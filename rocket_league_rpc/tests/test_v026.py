from dataclasses import replace
import asyncio
import json
import struct

import pytest

from rocket_league_rpc.config import Config
from rocket_league_rpc.main import Application
from rocket_league_rpc.presence import build_presence
from rocket_league_rpc.state import MatchState, Phase, reduce_event
from .test_runtime import FakeDiscord
from .test_v025 import match


@pytest.mark.parametrize('playlist,mode', [(11,'Ranked 2v2'), (2,'Casual 2v2')])
def test_exact_three_line_layout_map_only_in_artwork_tooltip(playlist, mode):
    cfg = Config()
    cfg.mode_ranks['doubles'] = {'tier':'Diamond I','division':4}
    payload = build_presence(match(playlist), cfg, 1000)
    assert payload['name'] == 'Rocket League'
    assert payload['details'] == mode + ' • 🔵 5 - 2 🟠'
    assert payload['state'] == '⚽1  🧤2  ⭐593'
    assert payload['large_image'] == 'mannfield' and payload['large_text'] == 'Mannfield (Night)'
    assert payload['end'] == 1153
    if playlist == 11:
        assert payload['small_image'] == 'diamond_1' and payload['small_text'] == 'Diamond I Div IV'
    else:
        assert 'small_image' not in payload and 'small_text' not in payload


@pytest.mark.parametrize('phase', [Phase.COUNTDOWN,Phase.GOAL_REPLAY,Phase.PAUSED])
@pytest.mark.parametrize('overtime', [False,True])
def test_no_white_clock_map_or_phase_label_in_stopped_match_text(phase, overtime):
    state = replace(match(), phase=phase, clock_end=None, is_overtime=overtime,
        clock_stopped_at=1000, overtime_started_at=990)
    first = build_presence(state, Config(), 1000)
    assert first['state'] == '⚽1  🧤2  ⭐593'
    assert build_presence(state, Config(), 1020) == first
    assert 'start' not in first and 'end' not in first
    assert 'Mannfield' not in first['details'] + first['state']


def test_training_keeps_map_line_only_and_no_small_artwork_or_timer():
    payload = build_presence(replace(match(), phase=Phase.TRAINING), Config(), 1000)
    assert payload['details'] == 'Training' and payload['state'] == 'Mannfield (Night)'
    assert not {'small_image','small_text','start','end'}.intersection(payload)


def test_overtime_uses_only_stats_text_and_native_elapsed_timer():
    payload = build_presence(replace(match(), phase=Phase.OVERTIME, is_overtime=True,
        clock_end=None, overtime_started_at=990), Config(), 1000)
    assert payload['state'] == '⚽1  🧤2  ⭐593' and payload['start'] == 990


def test_zero_and_missing_stats_are_distinguished_without_guessing_an_opponent():
    zero = replace(match(), local_player_goals=0,local_player_saves=0,local_player_score=0)
    assert build_presence(zero, Config(), 1000)['state'] == '⚽0  🧤0  ⭐0'
    unknown = replace(zero,local_player_goals=None,local_player_saves=None,local_player_score=None)
    assert build_presence(unknown, Config(), 1000)['state'] == '⚽—  🧤—  ⭐—'
    partial = replace(zero,local_player_goals=None)
    assert build_presence(partial, Config(), 1000)['state'] == '⚽—  🧤0  ⭐0'


def test_hidden_player_stats_do_not_restore_map_clock_or_a_filler_line():
    payload = build_presence(match(), Config(show_player_stats=False), 1000)
    assert 'state' not in payload and payload['large_text'] == 'Mannfield (Night)'
    assert payload['end'] == 1153


def snapshot(score=593,goals=1,saves=2,players=True):
    return {'Event':'UpdateState','Data':{'MatchGuid':'v026-match','Players':[
        {'Name':'PlayerA','PrimaryId':'Steam|123|0','TeamNum':0,'Score':score,'Goals':goals,'Saves':saves},
        {'Name':'Opponent','PrimaryId':'Steam|456|0','TeamNum':1,'Score':999,'Goals':9,'Saves':9}
    ] if players else [],'Game':{'Arena':'EuroStadium_Night_P','PlaylistId':11,
        'TimeSeconds':153,'bOvertime':False,'bReplay':False,'bHasTarget':False,
        'Teams':[{'TeamNum':0,'Score':5},{'TeamNum':1,'Score':2}]}}}


def test_unmatched_identity_never_borrows_opponent_stats():
    state = reduce_event(MatchState(),snapshot(),Config(player_name='Missing'),1000)
    assert build_presence(state,Config(),1000)['state'] == '⚽—  🧤—  ⭐—'


@pytest.mark.parametrize('field,value', [('score',594),('goals',2),('saves',3)])
async def test_personal_stat_change_publishes_without_four_second_coalescing(field,value):
    now = [1000.0]
    client = FakeDiscord(lambda:now[0])
    app = Application(Config(player_name='PlayerA',auto_learn_primary_id=False),
        discord_factory=lambda:client,wall_clock=lambda:now[0],monotonic_clock=lambda:now[0])
    await app.set_running(True)
    await app.on_connection(True)
    await app.on_event(snapshot())
    assert await app.publisher.pump()
    now[0] += .1
    await app.on_event(snapshot(**{field:value}))
    assert await app.publisher.pump()
    assert client.operations[-1][2] == app.current_payload()
    assert 'Mannfield' not in client.operations[-1][2]['state']
    await app.publisher.shutdown()


async def test_stat_burst_obeys_rolling_budget_and_sends_latest_after_window_opens():
    now = [1000.0]
    client = FakeDiscord(lambda:now[0])
    app = Application(Config(player_name='PlayerA',auto_learn_primary_id=False),
        discord_factory=lambda:client,wall_clock=lambda:now[0],monotonic_clock=lambda:now[0])
    await app.set_running(True)
    await app.on_connection(True)
    for n in range(5):
        now[0] = 1000 + n*.1
        await app.on_event(snapshot(score=593+n))
        assert await app.publisher.pump()
    now[0] = 1001
    await app.on_event(snapshot(score=650,goals=2,saves=3))
    assert not await app.publisher.pump()
    now[0] = 1019.999
    assert not await app.publisher.pump()
    now[0] = 1020
    assert await app.publisher.pump()
    assert client.operations[-1][2]['state'] == '⚽2  🧤3  ⭐650'
    assert sum(op[0]=='update' for op in client.operations) == 6
    assert not await app.publisher.pump()  # unchanged payload is never resent
    await app.publisher.shutdown()


async def test_actual_rpc_frame_has_exact_stats_and_clears_white_clock_and_small_assets():
    from rocket_league_rpc.rpc import DiscordClient
    client = DiscordClient(Config().client_id)
    frames = []
    class Writer:
        def write(self,data): frames.append(data)
    client.sock_writer = Writer()
    async def output(): return {'evt':'SET_ACTIVITY'}
    client.read_output = output
    cfg = Config()
    cfg.mode_ranks['doubles'] = {'tier':'Diamond I','division':4}
    await client.update(**build_presence(match(),cfg,1000))
    await client.update(**build_presence(replace(match(2),phase=Phase.GOAL_REPLAY),cfg,1001))
    first,second = [json.loads(frame[8:])['args']['activity'] for frame in frames]
    assert first['state'] == second['state'] == '⚽1  🧤2  ⭐593'
    assert first['assets']['large_text'] == 'Mannfield (Night)'
    assert first['assets']['small_image'] == 'diamond_1'
    assert first['timestamps']['end'] == 1153 and not second.get('timestamps')
    assert 'small_image' not in second['assets'] and 'small_text' not in second['assets']
    assert all(struct.unpack('<II',f[:8])[1] == len(f[8:]) for f in frames)


async def test_fragmented_tcp_player_stats_reach_publisher_without_waiting_four_seconds():
    from rocket_league_rpc.stats_client import StatsClient
    now=[1000.0]
    client=FakeDiscord(lambda:now[0])
    cfg=Config(player_name='PlayerA',auto_learn_primary_id=False)
    app=Application(cfg,discord_factory=lambda:client,wall_clock=lambda:now[0],monotonic_clock=lambda:now[0])
    await app.set_running(True)
    sent=[]
    async def receive(message):
        now[0]+=.1
        await app.on_event(message)
        sent.append(await app.publisher.pump())
    async def serve(reader,writer):
        wire=b''.join(json.dumps(p,ensure_ascii=False).encode('utf-8') for p in [snapshot(),snapshot(score=650,goals=2,saves=3)])
        try:
            for chunk in [wire[:7],wire[7:56],wire[56:]]:
                writer.write(chunk)
                await writer.drain()
                await asyncio.sleep(0)
        finally:
            writer.close()
            await writer.wait_closed()
    server=await asyncio.start_server(serve,'127.0.0.1',0)
    try:
        cfg.stats_port=server.sockets[0].getsockname()[1]
        await asyncio.wait_for(StatsClient(cfg,receive,app.on_connection).session(),5)
        assert sent == [True,True]
        updates=[op for op in client.operations if op[0]=='update']
        assert [op[2]['state'] for op in updates] == ['⚽1  🧤2  ⭐593','⚽2  🧤3  ⭐650']
    finally:
        server.close()
        await server.wait_closed()
        await app.publisher.shutdown()
