import asyncio

from .test_runtime import FakeDiscord


async def test_fragmented_mock_match_through_real_tcp_reducer_and_publisher():
    from rocket_league_rpc.config import Config
    from rocket_league_rpc.main import Application
    from rocket_league_rpc.stats_client import StatsClient
    from rocket_league_rpc.mock_stats_server import MockStatsServer
    from rocket_league_rpc.state import Phase
    # Logical wall/monotonic clocks advance 15 s per packet: test the actual
    # production 15 s limiter without a several-minute wall-clock test.
    now=[1000.0]
    discord=FakeDiscord(lambda:now[0])
    cfg=Config(player_name='PlayerA')
    app=Application(cfg, discord_factory=lambda:discord,
                    wall_clock=lambda:now[0], monotonic_clock=lambda:now[0])
    await app.set_running(True)
    observed=[]
    names=[]
    async def receive(message):
        now[0]+=15
        names.append(message['Event'])
        await app.on_event(message)
        observed.append(app.state.phase)
        await app.publisher.pump()
    async with MockStatsServer(port=0, delay=0) as server:
        cfg.stats_port=server.port
        stats=StatsClient(cfg, receive, app.on_connection)
        await asyncio.wait_for(stats.session(), timeout=5)
    assert names[0]=='MatchCreated' and names[-1]=='MatchDestroyed'
    assert {Phase.COUNTDOWN,Phase.PLAYING,Phase.GOAL_REPLAY,Phase.OVERTIME,Phase.ENDED,Phase.MENU}.issubset(observed)
    updates=[op for op in discord.operations if op[0]=='update']
    assert all(b[1]-a[1]>=15 for a,b in zip(updates,updates[1:]))
    assert any('(Win)' in op[2]['details'] for op in updates)
    assert any('Overtime' in op[2]['state'] and 'start' in op[2] for op in updates)
    assert all('end' not in op[2] for op in updates if 'Goal replay' in op[2]['state'] or 'Kickoff countdown' in op[2]['state'])
    assert app.state.phase==Phase.MENU
    await app.publisher.shutdown()
    assert discord.closed

