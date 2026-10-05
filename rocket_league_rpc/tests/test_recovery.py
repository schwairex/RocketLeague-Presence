import asyncio
import json
import struct
import pytest


async def test_discord_adapter_frames_unicode_bytes_reads_partial_reply_and_keeps_loop_alive():
    from rocket_league_rpc.rpc import DiscordClient
    client=DiscordClient('123456789012345678')
    class Writer:
        def __init__(self): self.wire=b''; self.closed=False
        def write(self,data): self.wire+=data
        def close(self): self.closed=True
    writer=Writer()
    client.sock_writer=writer
    client.send_data(1, {'Name':'Çağrı 🚀'})
    op,length=struct.unpack('<II',writer.wire[:8])
    assert op==1 and length==len(writer.wire[8:])
    assert json.loads(writer.wire[8:])=={'Name':'Çağrı 🚀'}
    reader=asyncio.StreamReader()
    client.sock_reader=reader
    body=b'{"evt":"SET_ACTIVITY","data":{}}'
    wire=struct.pack('<II',1,len(body))+body
    task=asyncio.create_task(client.read_output())
    for byte in wire:
        reader.feed_data(bytes([byte]))
        await asyncio.sleep(0)
    assert (await task)['evt']=='SET_ACTIVITY'
    await client.close()
    assert writer.closed and not asyncio.get_running_loop().is_closed()


async def test_priority_offered_while_send_in_flight_keeps_hard_floor_instead_of_long_interval():
    from rocket_league_rpc.rpc import PresencePublisher
    from .test_runtime import FakeDiscord
    now=[100.0]
    began=asyncio.Event()
    finish=asyncio.Event()
    class SlowClient(FakeDiscord):
        async def update(self,**payload):
            await super().update(**payload)
            began.set()
            await finish.wait()
    client=SlowClient(lambda:now[0])
    pub=PresencePublisher(lambda:client,interval=60,clock=lambda:now[0])
    pub.offer({'details':'Playing'})
    task=asyncio.create_task(pub.pump())
    await began.wait()
    pub.offer({'details':'Match finished'},priority=True)
    finish.set()
    await task
    now[0]=115
    assert await pub.pump()
    assert client.operations[-1][2]=={'details':'Match finished'}


async def test_game_stop_start_race_does_not_kill_stats_loop(monkeypatch):
    from rocket_league_rpc.main import Application
    from rocket_league_rpc.config import Config
    import rocket_league_rpc.main as main
    app=Application(Config())
    entered=asyncio.Event()
    resumed=asyncio.Event()
    calls=[]
    async def session(self):
        calls.append(True)
        if len(calls)==1:
            entered.set()
        else:
            resumed.set()
        await asyncio.Event().wait()
    monkeypatch.setattr(main.StatsClient,'session',session)
    await app.set_running(True)
    task=asyncio.create_task(app.stats_loop())
    try:
        await asyncio.wait_for(entered.wait(),1)
        await app.set_running(False)
        await app.set_running(True)  # before the cancelled child resumes
        await asyncio.wait_for(resumed.wait(),1)
        assert not task.done()
    finally:
        app.stop.set()
        task.cancel()
        await asyncio.gather(task,return_exceptions=True)


async def test_websocket_transport_receives_same_envelopes():
    from websockets.asyncio.server import serve
    from rocket_league_rpc.config import Config
    from rocket_league_rpc.stats_client import StatsClient
    received=[]
    status=[]
    async def handler(socket):
        await socket.send('{"Event":"RoundStarted","Data":{}}')
    async def event(message): received.append(message)
    async def connection(connected): status.append(connected)
    async with serve(handler,'127.0.0.1',0) as server:
        cfg=Config(stats_transport='websocket',stats_web_port=server.sockets[0].getsockname()[1])
        await StatsClient(cfg,event,connection).session()
    assert received==[{'Event':'RoundStarted','Data':{}}] and status==[True,False]


def test_install_discovery_reads_vdf_and_epic_manifests(tmp_path):
    from rocket_league_rpc.installer import discover_install
    steam=tmp_path/'steam'
    extra=tmp_path/'library'
    (steam/'steamapps').mkdir(parents=True)
    (steam/'steamapps'/'libraryfolders.vdf').write_text('"libraryfolders" { "1" { "path" "'+str(extra).replace('\\','\\\\')+'" }}')
    install=extra/'steamapps'/'common'/'rocketleague'
    (install/'TAGame').mkdir(parents=True)
    assert discover_install([steam],tmp_path/'missing')==install
    epic=tmp_path/'epic'
    (epic/'TAGame').mkdir(parents=True)
    manifests=tmp_path/'manifests'
    manifests.mkdir()
    (manifests/'bad.item').write_text('[]')
    (manifests/'good.item').write_text(json.dumps({'AppName':'Sugar','DisplayName':'Rocket League','InstallLocation':str(epic)}))
    assert discover_install([],manifests)==epic


def test_ini_disabled_rate_and_permission_error_are_safe(tmp_path,monkeypatch,caplog):
    from rocket_league_rpc.config import Config
    from rocket_league_rpc.installer import patch_stats_ini,setup_install
    import rocket_league_rpc.installer as installer
    path=tmp_path/'TAGame'/'Config'/'DefaultStatsAPI.ini'
    path.parent.mkdir(parents=True)
    path.write_text('[TAGame.MatchStatsExporter_TA]\nPacketSendRate=0\nPort=49123\nWebPort=49124\n')
    patch_stats_ini(tmp_path)
    assert 'PacketSendRate = 30' in path.read_text()
    def forbidden(*args,**kwargs): raise PermissionError('denied')
    monkeypatch.setattr(installer,'patch_stats_ini',forbidden)
    assert setup_install(Config(install_path=str(tmp_path)),tmp_path/'config.json',True) is None
    assert 'administrator' in caplog.text


def test_ini_malformed_original_not_overwritten(tmp_path):
    from rocket_league_rpc.installer import patch_stats_ini
    path=tmp_path/'TAGame'/'Config'/'TAStatsAPI.ini'
    path.parent.mkdir(parents=True)
    path.write_text('no section header\nPort=0\n')
    with pytest.raises(ValueError,match='original untouched'):
        patch_stats_ini(tmp_path)
    assert path.read_text()=='no section header\nPort=0\n'


def test_config_nonstandard_nan_and_null_root_regenerate(tmp_path):
    from rocket_league_rpc.config import load_config
    path=tmp_path/'config.json'
    path.write_text('{"update_interval":NaN}')
    assert load_config(path).update_interval==15
    path.write_text('null')
    assert load_config(path).stats_port==49123
    assert list(tmp_path.glob('*.bak'))


def test_huge_integer_update_interval_clamps_without_overflow(tmp_path):
    from rocket_league_rpc.config import load_config
    path=tmp_path/'config.json'
    path.write_text(json.dumps({'update_interval':10**1000}))
    assert load_config(path).update_interval==3600


async def test_buffered_discord_close_detected_when_payload_unchanged():
    from rocket_league_rpc.rpc import DiscordClient,PresencePublisher
    client=DiscordClient('123456789012345678')
    reader=asyncio.StreamReader()
    reader.feed_data(struct.pack('<II',2,2)+b'{}')
    protocol=asyncio.StreamReaderProtocol(reader)
    protocol.eof_received()
    class Writer:
        def is_closing(self): return False
        def close(self): pass
    client.sock_reader=reader
    client.sock_writer=Writer()
    assert not client.is_connected()
    from .test_runtime import FakeDiscord
    replacement=FakeDiscord(lambda:115)
    publisher=PresencePublisher(lambda:replacement,clock=lambda:115)
    publisher.client=client
    publisher.offer({'details':'Unchanged'})
    publisher.sent={'details':'Unchanged'}
    publisher.last_attempt=100
    assert await publisher.pump()
    assert replacement.operations[-1][2]=={'details':'Unchanged'}


def test_config_lone_unicode_surrogate_never_crashes_persistence(tmp_path):
    from rocket_league_rpc.config import load_config
    path=tmp_path/'config.json'
    path.write_text(r'{"player_name":"\ud800","install_path":"\ud800"}')
    cfg=load_config(path)
    assert cfg.player_name=='' and cfg.install_path==''
    assert json.loads(path.read_text())['player_name']==''


async def test_full_supervised_application_exits_after_mock_match(monkeypatch):
    from rocket_league_rpc.main import Application
    from rocket_league_rpc.config import Config
    from rocket_league_rpc.mock_stats_server import MockStatsServer
    from .test_runtime import FakeDiscord
    import time
    discord=FakeDiscord(time.monotonic)
    async with MockStatsServer(port=0,delay=0) as server:
        app=Application(Config(stats_port=server.port),discord_factory=lambda:discord,mock_game=True)
        original=app.on_event
        async def on_event(message):
            await original(message)
            if message.get('Event')=='MatchDestroyed': app.stop.set()
        app.on_event=on_event
        await asyncio.wait_for(app.run(),5)
    assert app.stop.is_set() and discord.closed
