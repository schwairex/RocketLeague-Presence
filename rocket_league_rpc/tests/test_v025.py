from dataclasses import replace
import json
import struct

import pytest

from rocket_league_rpc.config import Config
from rocket_league_rpc.presence import build_presence
from rocket_league_rpc.state import MatchState, Phase, reduce_event


def match(playlist=11):
    return MatchState(phase=Phase.PLAYING, arena='EuroStadium_Night_P',
        playlist_id=playlist, blue_score=5, orange_score=2, time_remaining=153,
        clock_end=1153, local_team=0, local_player_goals=1,
        local_player_saves=2, local_player_score=593)


def event(state, name, now, **data):
    return reduce_event(state, {'Event': name, 'Data': data}, Config(), now)


def test_ranked_requested_layout_and_rank_tooltip():
    cfg = Config()
    cfg.mode_ranks['doubles'] = {'tier': 'Diamond I', 'division': 4}
    payload = build_presence(match(), cfg, 1000)
    assert payload['name'] == 'Rocket League'
    assert payload['details'] == 'Ranked 2v2 • 🔵 5 - 2 🟠'
    assert payload['state'] == '⚽1  🧤2  ⭐593'
    assert payload['large_image'] == 'mannfield'
    assert payload['large_text'] == 'Mannfield (Night)'
    assert payload['small_image'] == 'diamond_1'
    assert payload['small_text'] == 'Diamond I Div IV'
    assert payload['end'] == 1153


@pytest.mark.parametrize('playlist', [1, 2, 3, 4])
def test_casual_only_map_artwork(playlist):
    payload = build_presence(match(playlist), Config(), 1000)
    assert payload['details'].startswith('Casual ')
    assert payload['state'] == '⚽1  🧤2  ⭐593'
    assert 'small_image' not in payload and 'small_text' not in payload
    assert payload['large_image'] == 'mannfield' and payload['end'] == 1153


def test_training_only_map_without_score_stats_or_rank():
    payload = build_presence(replace(match(), phase=Phase.TRAINING), Config(), 1000)
    assert payload['details'] == 'Training'
    assert payload['state'] == 'Mannfield (Night)'
    assert 'small_image' not in payload and 'small_text' not in payload
    assert payload['large_image'] == 'mannfield'
    assert 'start' not in payload and 'end' not in payload


@pytest.mark.parametrize('name', ['GoalScored', 'GoalReplayStart', 'MatchPaused', 'CountdownBegin'])
def test_clock_stops_without_native_timestamp_and_static_value_never_ticks(name):
    stopped = event(match(), name, 1000)
    first = build_presence(stopped, Config(), 1000)
    later = build_presence(stopped, Config(), 1025)
    assert first == later
    assert 'end' not in first and 'start' not in first
    assert first['state'] == '⚽1  🧤2  ⭐593'
    assert 'Kickoff' not in first.get('state','') and 'Goal replay' not in first.get('state','')


@pytest.mark.parametrize('skipped', [False, True])
def test_goal_score_snapshot_replay_countdown_then_fresh_kickoff(skipped):
    state = event(match(), 'GoalScored', 1000, GoalTime=127.5)
    # GoalTime is the previous round length, NOT the remaining game time.
    assert state.time_remaining == 153
    if not skipped:
        state = event(state, 'GoalReplayStart', 1001)
    state = event(state, 'UpdateState', 1002, Game={
        'TimeSeconds': 153, 'bReplay': not skipped,
        'Teams': [{'TeamNum': 0, 'Score': 6}, {'TeamNum': 1, 'Score': 2}]})
    assert build_presence(state, Config(), 1002)['details'].endswith('🔵 6 - 2 🟠')
    if not skipped:
        state = event(state, 'GoalReplayEnd', 1010)
    state = event(state, 'CountdownBegin', 1011)
    frozen = build_presence(state, Config(), 1013)
    assert '⏸' not in frozen.get('state','') and 'end' not in frozen
    state = event(state, 'RoundStarted', 1014)
    resumed = build_presence(state, Config(), 1014)
    assert resumed['end'] == 1167
    assert '⏸' not in resumed.get('state','') and '2:33' not in resumed.get('state','')


def test_snapshot_replay_without_goal_event_stops_the_clock():
    state = event(match(), 'UpdateState', 1000, Game={'bReplay': True, 'TimeSeconds': 153})
    payload = build_presence(state, Config(), 1010)
    assert 'end' not in payload and '⏸' not in payload.get('state','')


@pytest.mark.parametrize('before', [Phase.COUNTDOWN, Phase.GOAL_REPLAY])
def test_unpause_does_not_run_a_stopped_countdown_or_replay(before):
    state = replace(match(), phase=before, clock_end=None, is_replay=before==Phase.GOAL_REPLAY)
    state = event(state, 'MatchPaused', 1000)
    state = event(state, 'MatchUnpaused', 1010)
    assert state.phase == before
    assert 'end' not in build_presence(state, Config(), 1010)
    assert '⏸' not in build_presence(state, Config(), 1010).get('state','')


def test_replay_end_while_paused_waits_for_unpause_then_kickoff():
    state = event(match(), 'GoalScored', 1000)
    state = event(state, 'MatchPaused', 1001)
    state = event(state, 'GoalReplayEnd', 1005)
    assert state.phase == Phase.PAUSED
    state = event(state, 'MatchUnpaused', 1006)
    assert state.phase == Phase.COUNTDOWN
    assert 'end' not in build_presence(state, Config(), 1006)
    state = event(state, 'RoundStarted', 1009)
    assert build_presence(state, Config(), 1009)['end'] == 1162


def test_overtime_pause_resumes_without_counting_stopped_seconds():
    state = replace(match(), phase=Phase.OVERTIME, is_overtime=True, clock_end=None,
        overtime_started_at=1000, overtime_round_confirmed=True, time_remaining=17)
    state = event(state, 'MatchPaused', 1017)
    frozen = build_presence(state, Config(), 1017)
    assert 'start' not in frozen and 'end' not in frozen
    assert state.clock_stopped_at-state.overtime_started_at == 17
    assert '⏸' not in frozen.get('state','')
    assert build_presence(state, Config(), 1050) == frozen
    state = event(state, 'MatchUnpaused', 1050)
    resumed = build_presence(state, Config(), 1050)
    assert resumed['start'] == 1033  # 17 seconds played; the 33-second pause is excluded


def test_first_overtime_flag_during_pause_keeps_zero_clock_kickoff_anchor():
    state = replace(match(), time_remaining=0)
    state = event(state, 'CountdownBegin', 1001)
    state = event(state, 'RoundStarted', 1004)
    state = event(state, 'MatchPaused', 1005)
    state = event(state, 'ClockUpdatedSeconds', 1006, TimeSeconds=1, bOvertime=True)
    frozen = build_presence(state, Config(), 1006)
    assert state.clock_stopped_at-state.overtime_started_at == 1
    assert '⏸' not in frozen.get('state','')
    assert build_presence(state, Config(), 1020) == frozen
    state = event(state, 'MatchUnpaused', 1020)
    assert build_presence(state, Config(), 1020)['start'] == 1019


def test_first_overtime_flag_after_unpause_excludes_prior_pause():
    state = replace(match(), time_remaining=0)
    state = event(state, 'CountdownBegin', 1001)
    state = event(state, 'RoundStarted', 1004)
    state = event(state, 'MatchPaused', 1005)
    state = event(state, 'MatchUnpaused', 1020)
    state = event(state, 'ClockUpdatedSeconds', 1021, TimeSeconds=2, bOvertime=True)
    assert build_presence(state, Config(), 1021)['start'] == 1019


@pytest.mark.parametrize('flag_while_paused', [False, True])
def test_paused_zero_time_round_never_creates_a_future_overtime_start(flag_while_paused):
    state = replace(match(), time_remaining=0)
    state = event(state, 'CountdownBegin', 1001)
    if flag_while_paused:
        state = event(state, 'ClockUpdatedSeconds', 1002, TimeSeconds=0, bOvertime=True)
    state = event(state, 'MatchPaused', 1003)
    state = event(state, 'RoundStarted', 1004)
    assert state.phase == Phase.PAUSED
    state = event(state, 'MatchUnpaused', 1020)
    if not flag_while_paused:
        state = event(state, 'ClockUpdatedSeconds', 1020, TimeSeconds=0, bOvertime=True)
    assert build_presence(state, Config(), 1020)['start'] == 1020


@pytest.mark.parametrize('cfg', [Config(show_rank=False), Config()])
def test_unselected_or_hidden_rank_has_no_team_badge(cfg):
    payload = build_presence(match(), cfg, 1000)
    assert 'small_image' not in payload and 'small_text' not in payload


def test_visibility_toggles_and_unknown_stats_are_preserved():
    state = replace(match(), local_player_goals=None, local_player_saves=None, local_player_score=None)
    payload = build_presence(state, Config(show_mode=False, show_score=False), 1000)
    assert payload['details'] == 'Rocket League' and 'state' not in payload
    stopped = event(match(), 'GoalScored', 1000)
    hidden = build_presence(stopped, Config(show_time=False, show_player_stats=False, show_map=False), 1000)
    assert '⏸' not in hidden.get('state','') and 'end' not in hidden and 'start' not in hidden
    assert '⚽' not in hidden.get('state','') and 'Mannfield' not in str(hidden)


async def test_rpc_wire_replaces_rank_and_ticking_timestamp_with_no_small_assets():
    from rocket_league_rpc.rpc import DiscordClient
    client = DiscordClient(Config().client_id)
    frames = []
    class Writer:
        def write(self, data): frames.append(data)
    client.sock_writer = Writer()
    async def output(): return {'evt': 'SET_ACTIVITY'}
    client.read_output = output
    cfg = Config()
    cfg.mode_ranks['doubles'] = {'tier': 'Diamond I', 'division': 4}
    await client.update(**build_presence(match(), cfg, 1000))
    await client.update(**build_presence(event(match(2), 'GoalScored', 1001), cfg, 1001))
    first, second = [json.loads(frame[8:])['args']['activity'] for frame in frames]
    assert first['assets']['small_image'] == 'diamond_1'
    assert first['timestamps']['end'] == 1153
    assert not second.get('timestamps')
    assert 'small_image' not in second['assets'] and 'small_text' not in second['assets']
    assert second['state'] == '⚽1  🧤2  ⭐593'
    assert all(struct.unpack('<II', frame[:8])[1] == len(frame[8:]) for frame in frames)
