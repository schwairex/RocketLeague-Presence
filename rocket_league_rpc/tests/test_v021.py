import json
from dataclasses import replace

import pytest

from rocket_league_rpc.config import Config, load_config, save_config, validate_config
from rocket_league_rpc.presence import build_presence
from rocket_league_rpc.state import MatchState, Phase, reduce_event
from rocket_league_rpc.rpc import PresencePublisher
from .test_runtime import FakeDiscord


def test_identity_is_fixed_and_absent_from_config(tmp_path):
    cfg = validate_config({'client_id': '123', 'update_interval': 15})
    assert cfg.client_id == '802869954805760020'
    with pytest.raises(AttributeError):
        cfg.client_id = '456'
    path = tmp_path / 'config.json'
    assert save_config(cfg, path)
    assert 'client_id' not in json.loads(path.read_text())
    path.write_text('{"client_id":"123","update_interval":15}')
    migrated = load_config(path)
    assert migrated.client_id == cfg.client_id and migrated.update_interval == 1


def test_training_entry_has_no_incomplete_kickoff_card_or_stats():
    cfg = Config()
    state = MatchState()
    for name in ('MatchCreated', 'MatchInitialized', 'CountdownBegin'):
        state = reduce_event(state, {'Event': name, 'Data': {}}, cfg, 1000)
        payload = build_presence(state, cfg, 1000)
        assert '0 - 0' not in payload['details'] and 'Kickoff' not in payload['state']
    state = reduce_event(state, {'Event': 'UpdateState', 'Data': {
        'Game': {'PlaylistId': 9, 'Arena': 'Stadium_P', 'TimeSeconds': 0},
        'Players': []}}, cfg, 1000)
    state = replace(state, local_player_score=0, local_player_goals=0, local_player_saves=0)
    payload = build_presence(state, cfg, 1000)
    assert payload['details'] == 'Training' and payload['state'] == 'DFH Stadium'
    assert 'end' not in payload and 'start' not in payload


def test_game_timer_only_in_timestamp_and_goal_replay_text_omitted():
    state = MatchState(phase=Phase.PLAYING, arena='Stadium_P', playlist_id=2,
        blue_score=1, time_remaining=153, clock_end=1153,
        local_player_score=48, local_player_goals=0, local_player_saves=0)
    payload = build_presence(state, Config(), 1000)
    assert payload['state'] == 'DFH Stadium | P:48 G:0 S:0'
    assert payload['end'] - 1000 == 153
    assert build_presence(state, Config(), 1001) == payload
    replay = build_presence(replace(state, phase=Phase.GOAL_REPLAY), Config(), 1001)
    assert replay['state'] == payload['state'] and 'end' not in replay


async def test_immediate_phase_changes_and_rolling_budget_coalesce():
    now = [100.0]
    client = FakeDiscord(lambda: now[0])
    publisher = PresencePublisher(lambda: client, clock=lambda: now[0])
    for n in range(5):
        publisher.offer({'details': str(n)}, priority=True)
        assert await publisher.pump()
        now[0] += .1
    publisher.offer({'details': 'Goal'}, priority=True)
    assert not await publisher.pump()
    publisher.offer({'details': 'Training'}, priority=True)
    now[0] = 119.999
    assert not await publisher.pump()
    now[0] = 120
    assert await publisher.pump()
    assert client.operations[-1][2] == {'details': 'Training'}
    times = [op[1] for op in client.operations if op[0] == 'update']
    assert all(sum(t - 20 < x <= t for x in times) <= 5 for t in times)


async def test_training_wire_transition_never_publishes_incomplete_match():
    from rocket_league_rpc.main import Application
    now=[1000.0];client=FakeDiscord(lambda:now[0])
    app=Application(Config(),discord_factory=lambda:client,wall_clock=lambda:now[0],monotonic_clock=lambda:now[0])
    await app.set_running(True);await app.on_connection(True);await app.publisher.pump()
    for name in ('MatchCreated','MatchInitialized','CountdownBegin','RoundStarted'):
        now[0]+=.03
        await app.on_event({'Event':name,'Data':{}});await app.publisher.pump()
    now[0]+=.03
    await app.on_event({'Event':'UpdateState','Data':json.dumps({'Game':{'PlaylistId':9,'Arena':'Stadium_P','TimeSeconds':0},'Players':[]})})
    assert await app.publisher.pump()
    payloads=[op[2] for op in client.operations if op[0]=='update']
    assert [p['details'] for p in payloads]==['Rocket League','Training']
    assert payloads[-1]['state']=='DFH Stadium'


async def test_discord_clock_stays_synced_when_payload_waits_to_be_sent():
    now=[1000.0];client=FakeDiscord(lambda:now[0])
    pub=PresencePublisher(lambda:client,clock=lambda:now[0])
    state=MatchState(phase=Phase.PLAYING,arena='Stadium_P',playlist_id=2,time_remaining=153,clock_end=1153)
    for n in range(5):
        pub.offer({'details':str(n)},priority=True);await pub.pump()
    pub.offer(build_presence(state,Config(),1000),priority=True)
    now[0]=1020
    assert await pub.pump()
    assert client.operations[-1][2]['end']-now[0]==133
