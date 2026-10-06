import json
from dataclasses import replace
import logging
import pytest

from rocket_league_rpc.config import Config, validate_config
from rocket_league_rpc.identity import IdentityCandidate as C
from rocket_league_rpc.state import MatchState, reduce_event
from rocket_league_rpc.presence import build_presence


def packet(uid='123',name='Game Name',guid='one',score=593,**game):
    return {'Event':'UpdateState','Data':{'MatchGuid':guid,'Players':[
        {'Name':name,'PrimaryId':'Steam|'+uid+'|0','Shortcut':1,'TeamNum':0,'Score':score,'Goals':1,'Saves':2},
        {'Name':'Viewed Opponent','PrimaryId':'Epic|opponent|0','Shortcut':2,'TeamNum':1,'Score':999,'Goals':9,'Saves':9}],
        'Game':{'Arena':'EuroStadium_Night_P','PlaylistId':11,'TimeSeconds':153,'bOvertime':False,
                'bReplay':False,'bHasWinner':False,'Winner':'','bHasTarget':False,
                'Teams':[{'TeamNum':0,'Score':5},{'TeamNum':1,'Score':2}],**game}}}


def hints(state,*candidates):
    from rocket_league_rpc.state import set_identity_hints
    return set_identity_hints(state,candidates)


def test_schema_four_preserves_legacy_fields_as_optional_auto_hints():
    cfg=validate_config({'schema_version':3,'player_name':'Old Name','player_primary_id':'Steam|old|0','player_platform':'steam','update_interval':15})
    assert cfg.schema_version==4 and cfg.identity_mode=='auto'
    assert cfg.player_primary_id=='Steam|old|0' and cfg.player_name=='Old Name'
    assert cfg.update_interval==15  # schema 3 already allowed this user preference
    assert validate_config({'identity_mode':'manual'}).identity_mode=='manual'
    assert validate_config({'identity_mode':'bad'}).identity_mode=='auto'


def test_stale_saved_id_falls_through_to_auto_id_despite_different_names(caplog):
    cfg=Config(player_primary_id='Steam|old|0',player_name='Old Name',player_platform='epic')
    state=hints(MatchState(),C('Steam|123','Platform Persona','steam_active','high'))
    with caplog.at_level(logging.WARNING):
        state=reduce_event(state,packet(),cfg,1000)
        state=reduce_event(state,packet(score=600),cfg,1001)
    assert state.local_player_score==600 and state.local_primary_id=='Steam|123|0'
    assert state.identity_source=='steam_active' and state.identity_validated
    assert 'Steam|old' not in caplog.text and 'Steam|123' not in caplog.text
    assert sum('manual_override' in record.message for record in caplog.records)==1


def test_present_manual_identity_wins_over_auto_and_viewed_opponent():
    cfg=Config(player_name='Viewed Opponent')
    state=hints(MatchState(),C('Steam|123','','steam_active','high'))
    state=reduce_event(state,packet(bHasTarget=True,Target={'Name':'Game Name','TeamNum':0}),cfg,1000)
    assert state.local_primary_id=='Epic|opponent|0' and state.identity_source=='manual_override'
    assert state.local_player_score==999


def test_manual_mode_does_not_infer_when_override_is_missing():
    state=hints(MatchState(),C('Steam|123','','steam_active','high'))
    cfg=Config(identity_mode='manual',player_primary_id='Steam|old|0')
    for index in range(12): state=reduce_event(state,packet(bHasTarget=True,Target={'Name':'Game Name','TeamNum':0}),cfg,1000+index)
    assert state.local_team is None and not state.identity_source
    assert 'state' not in build_presence(state,cfg,1012)


def test_unique_normalized_manual_name_ignores_wrong_platform_preference(caplog):
    cfg=Config(player_name=' [TAG]  Ｇame   Name ',player_platform='epic')
    with caplog.at_level(logging.WARNING): state=reduce_event(MatchState(),packet(),cfg,1000)
    assert state.local_primary_id=='Steam|123|0'
    assert 'platform preference' in caplog.text.lower()


def test_duplicate_manual_name_does_not_choose_arbitrary_platform():
    message=packet();message['Data']['Players'][1]['Name']='Game Name'
    state=reduce_event(MatchState(),message,Config(player_name='Game Name',player_platform='steam'),1000)
    assert state.local_team is None and state.local_player_score is None


def test_target_requires_five_consecutive_votes_and_eighty_percent():
    cfg=Config();state=MatchState()
    for index in range(5): state=reduce_event(state,packet(bHasTarget=False),cfg,1000+index)
    for index in range(7):
        state=reduce_event(state,packet(bHasTarget=True,Target={'Name':'Game Name','TeamNum':0,'Shortcut':1}),cfg,1010+index)
        assert state.local_team is None
    state=reduce_event(state,packet(bHasTarget=True,Target={'Name':'Game Name','TeamNum':0,'Shortcut':1}),cfg,1017)
    assert state.local_team==0 and state.identity_confidence=='low' and not state.identity_validated


def test_target_first_five_identical_packets_can_identify_but_switch_clears_stats():
    cfg=Config();state=MatchState()
    for index in range(4):
        state=reduce_event(state,packet(bHasTarget=True,Target={'Name':'Game Name','TeamNum':0}),cfg,1000+index)
        assert state.local_player_score is None
    state=reduce_event(state,packet(bHasTarget=True,Target={'Name':'Game Name','TeamNum':0}),cfg,1004)
    assert state.local_player_score==593
    state=reduce_event(state,packet(bHasTarget=True,Target={'Name':'Viewed Opponent','TeamNum':1}),cfg,1005)
    assert state.local_player_score is None and 'state' not in build_presence(state,cfg,1005)


@pytest.mark.parametrize('spectating',[True,False])
def test_spectator_evidence_is_sticky_and_never_allows_target_inference(spectating):
    cfg=Config(spectating=spectating);state=MatchState()
    first=packet(bHasTarget=True,Target={'Name':'Game Name','TeamNum':0})
    if not spectating: first['Data']['Players'][0]['Boost']=80
    state=reduce_event(state,first,cfg,1000)
    for index in range(10): state=reduce_event(state,packet(bHasTarget=True,Target={'Name':'Game Name','TeamNum':0}),cfg,1001+index)
    assert state.local_team is None and state.local_player_score is None


def test_new_match_resets_votes_and_stale_stats_but_preserves_injected_hints():
    cfg=Config();state=hints(MatchState(),C('Steam|123','','steam_active','high'))
    state=reduce_event(state,packet(),cfg,1000)
    assert state.local_player_score==593
    state=hints(state,C('Steam|456','','steam_active','high'))
    assert state.local_player_score is None
    state=reduce_event(state,packet(uid='456',name='Second Account',guid='two',score=77),cfg,1001)
    assert state.local_player_score==77 and state.local_player_name=='Second Account'


def test_unidentified_line_is_absent_and_known_zero_still_visible():
    state=reduce_event(MatchState(),packet(),Config(),1000)
    assert 'state' not in build_presence(state,Config(),1000)
    state=replace(state,local_player_score=0,local_player_goals=0,local_player_saves=0)
    assert build_presence(state,Config(),1000)['state']=='⚽0  🧤0  ⭐0'


def test_learned_cache_never_beats_current_account_when_both_are_in_lobby():
    cfg=validate_config({'player_primary_id':'Steam|123|0','learned_primary_id':'Steam|123|0'})
    state=hints(MatchState(),C('Steam|456','','steam_active','high'))
    message=packet(uid='456',name='Current Account',score=100)
    message['Data']['Players'].append({'Name':'Previous Account','PrimaryId':'Steam|123|0','TeamNum':1,'Score':900,'Goals':9,'Saves':9})
    state=reduce_event(state,message,cfg,1000)
    assert state.local_primary_id=='Steam|456|0' and state.local_player_score==100
    assert state.identity_source=='steam_active'


def test_explicit_spectator_setting_is_remembered_until_new_match():
    cfg=Config(spectating=True);state=MatchState()
    message=packet(bHasTarget=True,Target={'Name':'Game Name','TeamNum':0})
    state=reduce_event(state,message,cfg,1000);cfg.spectating=False
    for i in range(8):state=reduce_event(state,message,cfg,1001+i)
    assert state.local_player_score is None and state.identity_spectator_seen


@pytest.mark.asyncio
async def test_settings_save_is_not_an_additional_target_packet():
    from rocket_league_rpc.main import Application
    app=Application(Config(),identity_discovery=lambda:(),wall_clock=lambda:1000)
    await app.set_running(True);await app.on_connection(True)
    message=packet(bHasTarget=True,Target={'Name':'Game Name','TeamNum':0})
    for _ in range(4):await app.on_event(message)
    for i in range(5):await app.apply_config({'show_map':bool(i%2)})
    assert app.state.local_player_score is None and app.state.identity_consecutive==4
    await app.on_event(message)
    assert app.state.local_player_score==593


@pytest.mark.asyncio
async def test_runtime_rediscovers_on_start_and_new_match_relearns_atomically(tmp_path):
    from rocket_league_rpc.main import Application
    calls=[]
    def discover():
        calls.append(True)
        return (C('Steam|'+('123' if len(calls)<3 else '456'),'Persona','steam_active','high'),)
    path=tmp_path/'config.json'
    cfg=Config(player_primary_id='Steam|old|0')
    app=Application(cfg,config_path=path,identity_discovery=discover,wall_clock=lambda:1000)
    await app.set_running(True);await app.on_connection(True)
    await app.on_event({'Event':'MatchCreated','Data':{'MatchGuid':'one'}})
    await app.on_event(packet())
    assert len(calls)==2 and app.state.local_player_score==593
    assert json.loads(path.read_text())['player_primary_id']=='Steam|123|0'
    assert json.loads(path.read_text())['learned_primary_id']=='Steam|123|0'
    await app.on_event(packet(uid='456',name='Second Account',guid='two',score=77))
    assert len(calls)==3 and app.state.local_player_score==77
    assert json.loads(path.read_text())['player_primary_id']=='Steam|456|0'
    assert app.snapshot()['identity']['source']=='steam_active'
    assert not list(tmp_path.glob('*.tmp'))
    await app.apply_config({'player_primary_id':'Epic|user-override|0'})
    assert app.config.learned_primary_id==''


@pytest.mark.asyncio
async def test_low_confidence_target_is_never_persisted(tmp_path):
    from rocket_league_rpc.main import Application
    path=tmp_path/'config.json'
    app=Application(Config(),config_path=path,identity_discovery=lambda:(),wall_clock=lambda:1000)
    await app.set_running(True);await app.on_connection(True)
    for _ in range(5): await app.on_event(packet(bHasTarget=True,Target={'Name':'Game Name','TeamNum':0}))
    assert app.state.local_player_score==593 and app.config.player_primary_id=='' and not path.exists()


@pytest.mark.asyncio
async def test_no_manual_fields_tcp_e2e_and_coalesced_budget():
    import asyncio
    from rocket_league_rpc.main import Application
    from rocket_league_rpc.stats_client import StatsClient
    writes=[];logical=[0.0]
    class Discord:
        async def connect(self): pass
        async def update(self,**payload): writes.append((logical[0],payload))
        async def clear(self): pass
        async def close(self): pass
    received=asyncio.Event();finish=asyncio.Event()
    async def handler(reader,writer):
        wire=b''.join(json.dumps(packet(score=600+i)).encode('utf-8') for i in range(9))
        for position in range(0,len(wire),137):
            writer.write(wire[position:position+137]);await writer.drain()
        await finish.wait();writer.close();await writer.wait_closed()
    server=await asyncio.start_server(handler,'127.0.0.1',0)
    cfg=Config(stats_port=server.sockets[0].getsockname()[1],auto_learn_primary_id=False)
    app=Application(cfg,discord_factory=Discord,wall_clock=lambda:1000,monotonic_clock=lambda:logical[0],
                    identity_discovery=lambda:(C('Steam|123','Different Persona','steam_active','high'),))
    await app.set_running(True)
    packets=[]
    async def on_event(message):
        logical[0]+=.1;await app.on_event(message);packets.append(app.state.local_player_score)
        await app.publisher.pump()
        if len(packets)==9: received.set()
    client=StatsClient(cfg,on_event,app.on_connection)
    session=asyncio.create_task(client.session())
    try:
        await asyncio.wait_for(received.wait(),3)
        assert packets==list(range(600,609)) and len(writes)==5
        assert writes[0][1]['state']=='⚽1  🧤2  ⭐600'
        logical[0]=20.1;await app.publisher.pump()
        assert writes[-1][1]['state']=='⚽1  🧤2  ⭐608' and len(writes)==6
    finally:
        finish.set();await asyncio.wait_for(session,3)
        server.close();await server.wait_closed();await app.publisher.shutdown()


@pytest.mark.parametrize('identified',[True,False])
@pytest.mark.asyncio
async def test_mock_stats_server_needs_no_manual_identity_and_omits_unresolved_line(identified,monkeypatch):
    import asyncio
    from rocket_league_rpc.main import Application
    from rocket_league_rpc import mock_stats_server as mock
    from rocket_league_rpc.stats_client import StatsClient
    now=[1000.0];writes=[];seen=[]
    class Discord:
        async def connect(self):pass
        async def update(self,**payload):writes.append((now[0],payload))
        async def clear(self):pass
        async def close(self):pass
    messages=[]
    for i in range(9):
        message=mock.update_packet(300-i)
        message['Data']['Game']['bHasTarget']=False
        message['Data']['Players'][0].update(Score=600+i,Goals=1,Saves=2)
        messages.append(message)
    monkeypatch.setattr(mock,'simulated_match',lambda:messages)
    async with mock.MockStatsServer(port=0,delay=0,encoded_data=True) as server:
        app=Application(Config(stats_port=server.port,auto_learn_primary_id=False),
            discord_factory=Discord,wall_clock=lambda:now[0],monotonic_clock=lambda:now[0],
            identity_discovery=lambda:(C('Steam|123' if identified else 'Steam|absent','Different platform name','steam_active','high'),))
        await app.set_running(True)
        async def receive(message):
            now[0]+=.1;await app.on_event(message)
            seen.append(app.current_payload());await app.publisher.pump()
        await asyncio.wait_for(StatsClient(app.config,receive,app.on_connection).session(),3)
        assert len(seen)==9
        if identified:
            assert [p['state'] for p in seen]==[f'⚽1  🧤2  ⭐{600+i}' for i in range(9)]
        else:
            assert all('state' not in p and '—' not in str(p) for p in seen)
        assert len(writes)<=5 and app.config.player_name==app.config.player_primary_id==''
        await app.publisher.shutdown()
