import pytest
from dataclasses import replace


@pytest.mark.parametrize('phase', ['COUNTDOWN','GOAL_REPLAY','PAUSED','ENDED','REPLAY_VIEWER'])
def test_stopped_clock_never_sends_ticking_timestamps(phase):
    from rocket_league_rpc.state import MatchState, Phase
    from rocket_league_rpc.config import Config
    from rocket_league_rpc.presence import build_presence
    s = MatchState(phase=Phase[phase], arena='Stadium_P', playlist_id=2, time_remaining=62, clock_end=1062,
                   overtime_started_at=900, ended_at=1000)
    p = build_presence(s, Config(), now=1000)
    assert 'start' not in p and 'end' not in p
    if phase in ['COUNTDOWN','GOAL_REPLAY','PAUSED']:
        assert '1:02' not in p['state']


def test_running_overtime_results_expiry_and_privacy_toggles():
    from rocket_league_rpc.state import MatchState, Phase
    from rocket_league_rpc.config import Config
    from rocket_league_rpc.presence import build_presence
    s = MatchState(phase=Phase.PLAYING, arena='Stadium_P', playlist_id=11,
                   blue_score=3, orange_score=2, local_team=0,
                   time_remaining=62, clock_end=1062)
    p = build_presence(s, Config(), now=1000)
    assert p['details'] == 'Ranked 2v2 | Blue 3 - 2 Orange'
    assert p['state'] == 'DFH Stadium' and p['end'] == 1062
    p = build_presence(s, Config(show_score=False, show_map=False, show_mode=False), 1000)
    assert p['details'] == 'Rocket League' and 'DFH' not in str(p)
    p = build_presence(s, Config(show_perspective=True), 1000)
    assert 'You 3 - 2 Opp' in p['details']
    p = build_presence(replace(s, phase=Phase.OVERTIME, is_overtime=True, overtime_started_at=990), Config(), 1000)
    assert p['start'] == 990 and 'end' not in p and 'Overtime' in p['state']
    end = replace(s, phase=Phase.ENDED, winner_team=0, ended_at=1000)
    assert '(Win)' in build_presence(end, Config(), 1059)['details']
    assert build_presence(end, Config(), 1060)['state'] == 'In menus / Queueing'
    assert 'Blue wins' in build_presence(replace(end, local_team=None), Config(), 1000)['details']


def test_all_presence_strings_are_bounded_even_unknown_unicode_arena():
    from rocket_league_rpc.state import MatchState, Phase
    from rocket_league_rpc.config import Config
    from rocket_league_rpc.presence import build_presence
    for arena in ['x', '🚀'*300]:
        p = build_presence(MatchState(phase=Phase.PLAYING, arena=arena), Config(), 1000)
        assert all(2 <= len(v) <= 128 for v in p.values() if isinstance(v, str))
