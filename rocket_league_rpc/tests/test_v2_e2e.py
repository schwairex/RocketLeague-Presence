import asyncio
import pytest
from rocket_league_rpc.config import Config
from rocket_league_rpc.main import Application
from rocket_league_rpc.mock_stats_server import MockStatsServer
from rocket_league_rpc.stats_client import StatsClient
from rocket_league_rpc.state import Phase
from .test_runtime import FakeDiscord


@pytest.mark.parametrize('encoded',[False,True])
async def test_fragmented_mock_match_updates_all_stats_and_rpc_with_both_envelopes(encoded):
    now=[1000.0]
    client=FakeDiscord(lambda:now[0])
    phases=set();seen=[];payloads=[]
    async with MockStatsServer(port=0,delay=0,encoded_data=encoded) as server:
        app=Application(Config(stats_port=server.port,player_name='PlayerA',
                               rank_tier='Diamond II',rank_division=3),
                        discord_factory=lambda:client,wall_clock=lambda:now[0],monotonic_clock=lambda:now[0])
        await app.set_running(True)
        async def receive(packet):
            now[0]+=16  # virtual rate windows; real TCP fragmentation
            await app.on_event(packet)
            phases.add(app.state.phase)
            seen.append(app.snapshot()['match'])
            await app.publisher.pump()
            if app.current_payload():payloads.append(app.current_payload())
        transport=StatsClient(app.config,receive,app.on_connection)
        await transport.session()
        assert {Phase.COUNTDOWN,Phase.PLAYING,Phase.GOAL_REPLAY,Phase.PAUSED,Phase.OVERTIME,Phase.ENDED,Phase.MENU} <= phases
        live=next(m for m in seen if m['local_player_score']==200 and m['winner_name']=='Blue')
        assert live['arena']=='Stadium_P' and live['playlist_id']==11
        assert (live['blue_score'],live['orange_score'],live['local_player_goals'],live['local_player_saves'])==(2,1,2,1)
        assert any(p.get('small_text') == 'Diamond II Div III' and '⚽2' in p['state'] for p in payloads)
        assert any('Win' in p['details'] for p in payloads)
        writes=[op for op in client.operations if op[0] in ('update','clear')]
        assert all(b[1]-a[1]>=15 for a,b in zip(writes,writes[1:]))
        assert app.state.phase==Phase.MENU
        await app.publisher.shutdown()
