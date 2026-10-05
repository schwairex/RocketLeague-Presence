import asyncio
from dataclasses import replace
import pytest


class FakeDiscord:
    def __init__(self, clock):
        self.clock = clock
        self.operations = []
        self.fail_update = False
        self.closed = False

    async def connect(self):
        self.operations.append(('connect', self.clock(), None))

    async def update(self, **payload):
        self.operations.append(('update', self.clock(), payload.copy()))
        if self.fail_update:
            self.fail_update = False
            raise BrokenPipeError('Discord restarted')

    async def clear(self):
        self.operations.append(('clear', self.clock(), None))

    async def close(self):
        self.closed = True


async def test_normal_updates_coalesce_and_priority_skips_interval():
    from rocket_league_rpc.rpc import PresencePublisher
    now = [100.0]
    clock = lambda: now[0]
    client = FakeDiscord(clock)
    publisher = PresencePublisher(lambda:client, interval=1, clock=clock)
    publisher.offer({'details':'Menu'})
    assert await publisher.pump()
    publisher.offer({'details':'Score 1'})
    now[0] = 103.999
    assert not await publisher.pump()
    publisher.offer({'details':'Match finished'}, priority=True)
    now[0] = 104
    assert await publisher.pump()
    assert [op[2] for op in client.operations if op[0]=='update'] == [
        {'details':'Menu'}, {'details':'Match finished'}]
    now[0] = 200
    publisher.offer({'details':'Match finished'})
    assert not await publisher.pump()  # identical payload skipped


async def test_failed_send_reconnect_resends_current_without_resetting_window():
    from rocket_league_rpc.rpc import PresencePublisher
    now = [100.0]
    clock = lambda:now[0]
    clients = []
    def factory():
        client = FakeDiscord(clock)
        clients.append(client)
        return client
    publisher = PresencePublisher(factory, clock=clock)
    publisher.offer({'details':'Current match'})
    await publisher.pump()
    now[0] = 115
    clients[0].fail_update = True
    publisher.offer({'details':'Latest score'})
    assert not await publisher.pump()
    assert clients[0].closed
    now[0] = 117.999
    assert not await publisher.pump()
    now[0] = 119
    assert await publisher.pump()
    assert clients[-1].operations[-1][2] == {'details':'Latest score'}
    times = [op[1] for client in clients for op in client.operations if op[0]=='update']
    assert times == [100, 115, 119]
    await publisher.shutdown()
    assert clients[-1].closed


async def test_clear_is_immediate_and_game_restart_is_coalesced():
    from rocket_league_rpc.rpc import PresencePublisher
    now=[100.0]
    client=FakeDiscord(lambda:now[0])
    pub=PresencePublisher(lambda:client, clock=lambda:now[0])
    pub.offer({'details':'Match'})
    await pub.pump()
    pub.offer(None)
    now[0]=101
    assert await pub.pump()
    assert client.operations[-1][0]=='clear'
    pub.offer({'details':'Menus'})
    now[0]=104.999
    assert not await pub.pump()
    now[0]=105
    assert await pub.pump()
    assert client.operations[-1][2]=={'details':'Menus'}


async def test_supervisor_restarts_failed_task_and_stops_on_cancellation():
    from rocket_league_rpc.runtime import supervise
    stop=asyncio.Event()
    runs=[]
    async def fails_once():
        runs.append(True)
        if len(runs)==1:
            raise RuntimeError('transient')
        stop.set()
    await asyncio.wait_for(supervise('test', fails_once, stop, retry_delay=0), 1)
    assert len(runs)==2


def test_single_instance_guard_releases_for_next_run(tmp_path):
    from rocket_league_rpc.runtime import SingleInstance, AlreadyRunning
    lock=tmp_path/'app.lock'
    name='Local\\rpc-test-' + tmp_path.name
    with SingleInstance(lock,name):
        with pytest.raises(AlreadyRunning):
            with SingleInstance(lock,name):
                pass
    with SingleInstance(lock,name):
        pass


async def test_app_process_and_connection_gating_and_new_match_priority():
    from rocket_league_rpc.main import Application
    from rocket_league_rpc.config import Config
    from rocket_league_rpc.state import Phase
    from rocket_league_rpc.tests.test_state import update, event
    now=[1000.0]
    client=FakeDiscord(lambda:now[0])
    app=Application(Config(), discord_factory=lambda:client, wall_clock=lambda:now[0])
    assert app.current_payload() is None
    await app.set_running(True)
    assert app.current_payload()['state']=='In menus / Queueing'
    await app.on_connection(True)
    await app.on_event(update())
    assert app.state.phase==Phase.PLAYING
    assert 'Blue 2 - 1 Orange' in app.current_payload()['details']
    await app.on_connection(False)
    assert app.current_payload()['state']=='In menus / Queueing'
    await app.set_running(False)
    assert app.current_payload() is None and app.state.phase==Phase.MENU
    await app.set_running(True)
    assert app.current_payload()['state']=='In menus / Queueing'


def test_process_watcher_handles_disappearing_processes(monkeypatch):
    import psutil
    from rocket_league_rpc.game_watcher import rocket_league_running
    class Proc:
        def __init__(self, name): self.info={'name':name}
    monkeypatch.setattr(psutil, 'process_iter', lambda attrs: iter([Proc(None),Proc('RocketLeague.exe')]))
    assert rocket_league_running()
    monkeypatch.setattr(psutil, 'process_iter', lambda attrs:iter([Proc('notepad.exe')]))
    assert not rocket_league_running()
