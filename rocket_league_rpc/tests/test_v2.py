from dataclasses import replace
import asyncio
import json
import pytest

from .test_state import update,event


def test_update_state_retains_all_requested_player_stats_without_assuming_local_identity():
    from rocket_league_rpc.config import Config
    from rocket_league_rpc.state import MatchState,reduce_event
    msg=update()
    msg['Data']['Players'][0].update(Score=420,Goals=2,Saves=3)
    msg['Data']['Players'].append({'Name':'Other','PrimaryId':'Steam|123|0','TeamNum':1,'Score':250,'Goals':1,'Saves':4})
    s=reduce_event(MatchState(),msg,Config(player_name='Çağrı'),1000)
    assert (s.local_player_score,s.local_player_goals,s.local_player_saves)==(420,2,3)
    assert len(s.players)==2 and s.players[1].saves==4
    unknown=reduce_event(MatchState(),msg,Config(player_name='missing'),1000)
    assert unknown.local_player_score is None
    msg['Data']['Game'].update(bHasWinner=True,Winner='Blue')
    assert reduce_event(s,msg,Config(),1001).winner_name=='Blue'


def test_presence_includes_rank_division_and_local_player_stats():
    from rocket_league_rpc.config import Config
    from rocket_league_rpc.state import MatchState,Phase
    from rocket_league_rpc.presence import build_presence
    cfg=Config(rank_tier='Diamond II',rank_division=3,show_rank=True,show_player_stats=True)
    s=MatchState(phase=Phase.PLAYING,arena='Stadium_P',playlist_id=11,blue_score=2,orange_score=1,
                 time_remaining=222,clock_end=1222,local_team=0,
                 local_player_score=420,local_player_goals=2,local_player_saves=3)
    p=build_presence(s,cfg,1000)
    assert p['small_image'] == 'diamond_2' and p['small_text'] == 'Diamond II Div III'
    assert '420' in p['state'] and 'G:2' in p['state'] and 'S:3' in p['state']
    assert p['end']==1222 and p['large_image']=='dfh_stadium'
    p=build_presence(s,replace(cfg,show_time=False),1000)
    assert 'end' not in p and '3:42' not in p['state']
    p=build_presence(s,replace(cfg,show_player_stats=False,show_rank=False),1000)
    assert 'Diamond' not in str(p) and '420' not in str(p)


@pytest.mark.parametrize('activity,label',[('main_menu','Main menu'),('menu','In menus'),('queue','Queueing'),
    ('shop','Item shop'),('training','Free play'),('custom_training','Custom training'),('garage','Garage')])
def test_manual_activity_is_visible_but_never_overrides_live_match(activity,label):
    from rocket_league_rpc.config import Config
    from rocket_league_rpc.state import MatchState,Phase
    from rocket_league_rpc.presence import build_presence
    cfg=Config(manual_activity=activity)
    assert label in build_presence(MatchState(),cfg,1000)['state']
    live=MatchState(phase=Phase.PLAYING,arena='Stadium_P',playlist_id=11)
    assert label not in build_presence(live,cfg,1000)['state']


def test_rank_validation_and_new_config_fields_survive_save_load(tmp_path):
    from rocket_league_rpc.config import load_config,save_config,Config
    path=tmp_path/'config.json'
    path.write_text(json.dumps({'rank_tier':'nonsense','rank_division':90,'manual_activity':'oops',
                               'show_time':False,'show_rank':True,'show_player_stats':True,'player_platform':'epic'}))
    cfg=load_config(path)
    assert cfg.rank_tier=='Unranked' and cfg.rank_division==4 and cfg.manual_activity=='auto'
    assert cfg.player_platform=='epic' and not cfg.show_time
    cfg.rank_tier='Champion I'
    assert save_config(cfg,path)
    assert load_config(path).rank_tier=='Champion I'


def test_training_playlist_has_training_presence_without_match_countdown():
    from rocket_league_rpc.config import Config
    from rocket_league_rpc.state import MatchState,reduce_event,Phase
    from rocket_league_rpc.presence import build_presence
    msg=update(remaining=0,PlaylistId=9)
    s=reduce_event(MatchState(),msg,Config(),1000)
    assert s.phase==Phase.TRAINING
    p=build_presence(s,Config(),1000)
    assert 'Training' in p['details'] and 'end' not in p and 'start' not in p


async def test_telemetry_distinguishes_connection_without_packets_and_reports_errors():
    from rocket_league_rpc.main import Application
    from rocket_league_rpc.config import Config
    app=Application(Config(),wall_clock=lambda:1000)
    await app.set_running(True)
    await app.on_connection(True)
    snap=app.snapshot()
    assert snap['stats']['connected'] and snap['stats']['last_event'] is None
    assert snap['stats']['status']=='awaiting_data'
    await app.on_event(update())
    snap=app.snapshot()
    assert snap['stats']['last_event']=='UpdateState' and snap['stats']['status']=='live'
    assert snap['match']['arena']=='Stadium_P'
    await app.on_stats_error(ConnectionRefusedError('refused'))
    await app.on_connection(False)
    assert 'refused' in app.snapshot()['stats']['error']


async def test_hot_reload_identity_reduces_last_snapshot_and_transport_restarts(tmp_path):
    from rocket_league_rpc.main import Application
    from rocket_league_rpc.config import Config
    app=Application(Config(player_name='missing'),config_path=tmp_path/'config.json',wall_clock=lambda:1000)
    await app.set_running(True)
    await app.on_connection(True)
    msg=update()
    msg['Data']['Players'][0].update(Score=420,Goals=2,Saves=3)
    await app.on_event(msg)
    assert app.state.local_team is None
    await app.apply_config({'player_name':'Çağrı','mode_ranks':{
        **app.config.mode_ranks,'doubles':{'tier':'Diamond II','division':2}}})
    assert app.state.local_team==0 and app.state.local_player_score==420
    assert app.current_payload()['small_image'] == 'diamond_2'
    assert json.loads((tmp_path/'config.json').read_text(encoding='utf-8'))['player_name']=='Çağrı'


async def test_ui_snapshot_never_contains_fake_live_statistics():
    from rocket_league_rpc.main import Application
    from rocket_league_rpc.config import Config
    app=Application(Config())
    snap=app.snapshot()
    assert not snap['game_running'] and snap['match']['players']==[]
    assert snap['discord']['sent_payload'] is None


async def test_saving_settings_does_not_resume_goal_replay_or_resync_a_stale_clock(tmp_path):
    from rocket_league_rpc.main import Application
    from rocket_league_rpc.config import Config
    from rocket_league_rpc.state import Phase
    now=[1000]
    app=Application(Config(),tmp_path/'config.json',wall_clock=lambda:now[0])
    await app.set_running(True)
    await app.on_connection(True)
    await app.on_event(update())
    clock=app.state.clock_end
    now[0]+=10
    await app.apply_config({'show_map':False})
    assert app.state.clock_end==clock
    await app.on_event(event('GoalReplayStart'))
    await app.apply_config({'show_map':True})
    assert app.state.phase==Phase.GOAL_REPLAY and app.state.clock_end is None


def test_training_round_events_do_not_become_a_live_match():
    from rocket_league_rpc.config import Config
    from rocket_league_rpc.state import MatchState,Phase,reduce_event
    s=reduce_event(MatchState(),update(PlaylistId=9),Config(),1000)
    for name in ('CountdownBegin','RoundStarted','GoalScored','GoalReplayEnd'):
        s=reduce_event(s,event(name),Config(),1001)
        assert s.phase==Phase.TRAINING and s.clock_end is None


async def test_real_tcp_data_string_format_is_decoded_before_reducer_and_telemetry():
    from rocket_league_rpc.main import Application
    from rocket_league_rpc.config import Config
    from rocket_league_rpc.state import Phase
    app=Application(Config(player_name='Çağrı'),wall_clock=lambda:1000)
    await app.set_running(True)
    await app.on_connection(True)
    packet=update(PlaylistId=9)
    packet['Data']['Players'][0].update(Score=420,Goals=2,Saves=3)
    packet['Data']=json.dumps(packet['Data'],ensure_ascii=False)
    await app.on_event(packet)
    assert app.state.phase==Phase.TRAINING and app.state.arena=='Stadium_P'
    assert app.state.local_player_score==420
    assert app.snapshot()['stats']['status']=='live'
    await app.apply_config({'rank_tier':'Diamond I'})
    assert app.state.local_player_goals==2


@pytest.mark.parametrize('data',['not json','[]','null','42','"nested string"','['*1500])
def test_invalid_encoded_data_never_crashes_or_creates_fake_match(data):
    from rocket_league_rpc.state import reduce_event,MatchState
    from rocket_league_rpc.config import Config
    assert reduce_event(MatchState(),{'Event':'UpdateState','Data':data},Config(),1000)==MatchState()


@pytest.mark.parametrize('name',[[],{},None,42,True])
def test_normalizer_rejects_non_string_event_names_cheaply(name):
    from rocket_league_rpc.state import reduce_event,MatchState
    from rocket_league_rpc.config import Config
    assert reduce_event(MatchState(),{'Event':name,'Data':'{}'},Config(),1000)==MatchState()
