import pytest


def update(guid='match-1', remaining=300, overtime=False, **game):
    return {'Event': 'UpdateState', 'Data': {
        'MatchGuid': guid,
        'Players': [{'Name': 'Çağrı', 'PrimaryId': 'Epic|456|0', 'TeamNum': 0}],
        'Game': {'Teams': [{'TeamNum': 0, 'Name': 'Blue', 'Score': 2},
                           {'TeamNum': 1, 'Name': 'Orange', 'Score': 1}],
                 'PlaylistId': 11, 'Arena': 'Stadium_P', 'TimeSeconds': remaining,
                 'bOvertime': overtime, 'bReplay': False, 'bHasWinner': False,
                 'Winner': '', 'bHasTarget': True,
                 'Target': {'Name': 'Çağrı', 'Shortcut': 1, 'TeamNum': 0}, **game}}}


def event(name, **data):
    return {'Event': name, 'Data': data}


def test_full_lifecycle_and_result():
    from rocket_league_rpc.state import MatchState, Phase, reduce_event
    from rocket_league_rpc.config import Config
    s = MatchState()
    cfg = Config(player_name='çağrı')
    for name in ['MatchCreated', 'MatchInitialized', 'CountdownBegin']:
        s = reduce_event(s, event(name, MatchGuid='match-1'), cfg, now=1000)
        assert s.phase == Phase.COUNTDOWN
    s = reduce_event(s, update(), cfg, now=1000)
    assert (s.blue_score, s.orange_score, s.local_team) == (2, 1, 0)
    assert s.local_primary_id == 'Epic|456|0'
    s = reduce_event(s, event('RoundStarted'), cfg, now=1001)
    assert s.phase == Phase.PLAYING and s.clock_end == 1301
    s = reduce_event(s, event('GoalScored', Scorer={'TeamNum': 0}), cfg, now=1100)
    assert s.phase == Phase.GOAL_REPLAY  # stop the timer immediately on a goal
    s = reduce_event(s, event('GoalReplayStart'), cfg, now=1101)
    assert s.phase == Phase.GOAL_REPLAY
    s = reduce_event(s, event('GoalReplayWillEnd'), cfg, now=1102)
    assert s.phase == Phase.GOAL_REPLAY
    s = reduce_event(s, event('GoalReplayEnd'), cfg, now=1103)
    assert s.phase == Phase.COUNTDOWN
    s = reduce_event(s, event('RoundStarted'), cfg, now=1104)
    s = reduce_event(s, event('MatchPaused'), cfg, now=1105)
    assert s.phase == Phase.PAUSED
    s = reduce_event(s, event('MatchUnpaused'), cfg, now=1106)
    assert s.phase == Phase.PLAYING
    s = reduce_event(s, event('MatchEnded', WinnerTeamNum=0), cfg, now=1400)
    assert s.phase == Phase.ENDED and s.winner_team == 0 and s.ended_at == 1400
    s = reduce_event(s, event('PodiumStart'), cfg, now=1401)
    assert s.ended_at == 1400
    assert reduce_event(s, event('MatchDestroyed'), cfg, now=1410).phase == Phase.MENU


def test_overtime_clock_and_resync_threshold():
    from rocket_league_rpc.state import MatchState, Phase, reduce_event
    from rocket_league_rpc.config import Config
    cfg = Config()
    s = reduce_event(MatchState(), update(remaining=120), cfg, now=1000)
    assert s.clock_end == 1120
    s = reduce_event(s, event('ClockUpdatedSeconds', TimeSeconds=111), cfg, now=1010)
    assert s.clock_end == 1120  # deviation 1
    s = reduce_event(s, event('ClockUpdatedSeconds', TimeSeconds=112), cfg, now=1010)
    assert s.clock_end == 1120  # exactly 2 does not resync
    s = reduce_event(s, event('ClockUpdatedSeconds', TimeSeconds=113), cfg, now=1010)
    assert s.clock_end == 1123
    s = reduce_event(s, event('CountdownBegin'), cfg, now=1120)
    s = reduce_event(s, event('ClockUpdatedSeconds', TimeSeconds=0, bOvertime=True), cfg, now=1121)
    assert s.phase == Phase.COUNTDOWN and s.clock_end is None
    s = reduce_event(s, event('RoundStarted'), cfg, now=1124)
    assert s.phase == Phase.OVERTIME and s.overtime_started_at == 1124
    s = reduce_event(s, event('ClockUpdatedSeconds', TimeSeconds=7, bOvertime=True), cfg, now=1131)
    assert s.overtime_started_at == 1124 and s.clock_end is None


def test_overtime_flag_before_countdown_uses_first_overtime_round_not_regulation_round():
    from rocket_league_rpc.state import MatchState, reduce_event
    from rocket_league_rpc.config import Config
    cfg=Config()
    s=reduce_event(MatchState(),update(remaining=1),cfg,1000)
    s=reduce_event(s,event('RoundStarted'),cfg,1000)
    s=reduce_event(s,event('ClockUpdatedSeconds',TimeSeconds=0,bOvertime=True),cfg,1001)
    s=reduce_event(s,event('CountdownBegin'),cfg,1002)
    s=reduce_event(s,event('RoundStarted'),cfg,1005)
    assert s.overtime_started_at==1005
    s=reduce_event(s,event('ClockUpdatedSeconds',TimeSeconds=3,bOvertime=True),cfg,1008)
    assert s.overtime_started_at==1005


def test_overtime_flag_just_after_zero_clock_round_uses_that_round():
    from rocket_league_rpc.state import MatchState,reduce_event
    from rocket_league_rpc.config import Config
    cfg=Config()
    s=reduce_event(MatchState(),update(remaining=0),cfg,1000)
    s=reduce_event(s,event('CountdownBegin'),cfg,1001)
    s=reduce_event(s,event('RoundStarted'),cfg,1004)
    s=reduce_event(s,event('ClockUpdatedSeconds',TimeSeconds=1,bOvertime=True),cfg,1005)
    assert s.overtime_started_at==1004


def test_replay_viewer_stays_history_through_live_shaped_events_and_updates():
    from rocket_league_rpc.state import MatchState, Phase, reduce_event
    from rocket_league_rpc.config import Config
    cfg = Config()
    s = reduce_event(MatchState(), event('ReplayCreated', FileName='test', Date='2026-06-05'), cfg, 1000)
    for msg in [update(), event('MatchInitialized'), event('RoundStarted'), event('GoalReplayStart'),
                event('MatchEnded', WinnerTeamNum=0), event('MatchCreated')]:
        s = reduce_event(s, msg, cfg, 1001)
        assert s.phase == Phase.REPLAY_VIEWER
    assert reduce_event(s, event('MatchDestroyed'), cfg, 1002).phase == Phase.MENU


def test_new_guid_resets_and_offline_empty_guid_is_one_match():
    from rocket_league_rpc.state import MatchState, reduce_event, Phase
    from rocket_league_rpc.config import Config
    cfg = Config()
    s = reduce_event(MatchState(), update(guid=''), cfg, 1000)
    s = reduce_event(s, event('MatchPaused'), cfg, 1001)
    s = reduce_event(s, update(guid=''), cfg, 1002)
    assert s.phase == Phase.PAUSED
    s = reduce_event(s, update(guid='new'), cfg, 1003)
    assert s.phase == Phase.PLAYING and s.match_guid == 'new'
    assert reduce_event(s, event('MatchDestroyed'), cfg, 1004).phase == Phase.MENU


def test_configured_identity_beats_target_and_spectating_disables_inference():
    from rocket_league_rpc.state import MatchState, reduce_event
    from rocket_league_rpc.config import Config
    msg = update()
    msg['Data']['Players'].append({'Name': 'Other', 'PrimaryId': 'Steam|123|0', 'TeamNum': 1})
    s = reduce_event(MatchState(), msg, Config(player_primary_id='steam|123|0'), 1000)
    assert s.local_team == 1 and s.local_player_name == 'Other'
    assert reduce_event(MatchState(), msg, Config(spectating=True), 1000).local_team is None
    msg['Data']['Players'][0]['Boost'] = 50
    assert reduce_event(MatchState(), msg, Config(), 1000).local_team is None
    assert reduce_event(MatchState(), msg, Config(player_name='missing'), 1000).local_team is None


@pytest.mark.parametrize('msg', [None, [], {}, {'Event': []}, {'Event':'UpdateState','Data': []},
    {'Event':'UpdateState','Data': {'Players':[None,4,{}], 'Game': {'Teams': [None], 'TimeSeconds': 'bad', 'Arena': []}}},
    {'Event': 'BallHit', 'Data': {'whatever': []}}])
def test_malformed_fields_never_crash(msg):
    from rocket_league_rpc.state import MatchState, reduce_event
    from rocket_league_rpc.config import Config
    assert isinstance(reduce_event(MatchState(), msg, Config(), 1000), MatchState)
