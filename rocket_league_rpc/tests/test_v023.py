import json
from dataclasses import asdict
from pathlib import Path

import pytest


@pytest.mark.parametrize('playlist,label',[(1,'Casual 1v1'),(2,'Casual 2v2'),(3,'Casual 3v3'),(4,'Casual 4v4'),(10,'Ranked 1v1'),(11,'Ranked 2v2'),(13,'Ranked 3v3'),(63,'Ranked Heatseeker')])
def test_size_mode_names(playlist,label):
    from rocket_league_rpc.modes import lookup_mode
    assert lookup_mode(playlist)==label


def test_per_mode_rank_validation_migration_and_presence(tmp_path):
    from rocket_league_rpc.config import validate_config,save_config,load_config
    from rocket_league_rpc.presence import build_presence
    from rocket_league_rpc.state import MatchState,Phase
    cfg=validate_config({'rank_tier':'Diamond II','rank_division':3})
    assert len(cfg.mode_ranks)==8
    assert all(v=={'tier':'Diamond II','division':3} for v in cfg.mode_ranks.values())
    data=asdict(cfg);data['mode_ranks']['doubles']={'tier':'Champion I','division':4}
    data['mode_ranks']['hoops']={'tier':'wrong','division':99}
    cfg=validate_config(data)
    assert cfg.mode_ranks['hoops']=={'tier':'Unranked','division':4}
    path=tmp_path/'config.json';assert save_config(cfg,path)
    cfg=load_config(path)
    for playlist,rank in [(11,'Champion I Div IV'),(10,'Diamond II Div III'),(13,'Diamond II Div III')]:
        state=MatchState(phase=Phase.PLAYING,arena='Stadium_P',playlist_id=playlist)
        assert rank == build_presence(state,cfg,1000)['small_text']
    assert 'Diamond' not in build_presence(MatchState(phase=Phase.PLAYING,arena='Park_P',playlist_id=2),cfg,1000)['details']


@pytest.mark.parametrize('arena,name,key',[('Paname_Dusk_P','Parc de Paris','parc_de_paris'),('CS_P','Champions Field','champions_field'),('Beach_P','Salty Shores','salty_shores'),('Mall_Day_P','Boostfield Mall','boostfield_mall'),('HoopsStadium_P','Dunk House','dunk_house'),('ShatterShot_P','Core 707','core_707'),('UF_Night_P','United Futura','united_futura')])
def test_expanded_maps(arena,name,key):
    from rocket_league_rpc.maps import lookup_map
    assert lookup_map(arena.lower())==(name,key)


def test_discovery_returns_steam_and_epic_and_patches_both(tmp_path):
    from rocket_league_rpc.installer import discover_installs, configure_installs
    steam=tmp_path/'Steam';one=steam/'steamapps/common/rocketleague';(one/'TAGame').mkdir(parents=True)
    two=tmp_path/'Epic/RocketLeague';(two/'TAGame').mkdir(parents=True)
    manifests=tmp_path/'manifests';manifests.mkdir()
    (manifests/'sugar.item').write_text(json.dumps({'AppName':'Sugar','InstallLocation':str(two)}))
    installs=discover_installs(roots=[steam],manifests=manifests)
    assert set(installs)=={one.resolve(),two.resolve()}
    results=configure_installs(installs)
    assert len(results)==2 and all(r['status']=='restart_required' for r in results)
    assert all(Path(r['ini']).exists() and Path(r['backup']).exists() for r in results)
    assert all(r['status']=='ready' for r in configure_installs(installs))


def test_process_executable_selects_active_install(tmp_path):
    from rocket_league_rpc.game_watcher import install_from_executable
    root=tmp_path/'Epic/RocketLeague';(root/'TAGame').mkdir(parents=True)
    assert install_from_executable(str(root/'Binaries/Win64/RocketLeague.exe'))==root.resolve()
    assert install_from_executable(str(root/'SomeOtherGame.exe')) is None


def test_update_loaded_callback_returns_none(caplog):
    from rocket_league_rpc.gui import startup_update_check
    from webview.event import Event
    class Updates:
        def check(self):return {'status':'checking'}
    assert startup_update_check(Updates()) is None
    event=Event(None,should_lock=True)
    event+=lambda:startup_update_check(Updates())
    event.set()
    assert 'unhashable' not in caplog.text


def test_report_uses_honest_app_user_agent_to_reach_cloudflare():
    from rocket_league_rpc.reports import ReportClient
    from .test_v022 import Response
    calls=[]
    def send(request,timeout):
        calls.append(request)
        assert request.get_header('User-agent').startswith('RL-Presence/')
        return Response(200)
    assert ReportClient(send).submit('valid title','long description')['status']=='sent'
    assert len(calls)==1


def test_setup_restart_remembered_across_app_restarts_and_game_relaunch(tmp_path,monkeypatch):
    from rocket_league_rpc import installer
    from rocket_league_rpc.config import Config
    import time
    path=tmp_path/'Steam/rocketleague';(path/'TAGame').mkdir(parents=True)
    monkeypatch.setattr(installer,'discover_installs',lambda **kwargs:[path])
    started=time.time()-100
    setup=installer.InstallationSetup()
    assert setup.check(Config(),True,path,started)['restart_required']
    # An idempotent repeat must still show the required restart.
    assert setup.check(Config(),True,path,started)['restart_required']
    assert installer.InstallationSetup().check(Config(),True,path,started)['restart_required']
    assert setup.check(Config(),True,path,time.time()+100)['status']=='ready'
    assert setup.check(Config(),False)['status']=='ready'


def test_partial_permission_failure_does_not_block_other_install(tmp_path,monkeypatch):
    from rocket_league_rpc import installer
    from rocket_league_rpc.config import Config
    one,two=tmp_path/'steam',tmp_path/'epic'
    for path in (one,two):(path/'TAGame').mkdir(parents=True)
    original=installer.patch_stats_ini
    def patch(path,*args):
        if path==one:raise PermissionError('denied')
        return original(path,*args)
    monkeypatch.setattr(installer,'patch_stats_ini',patch)
    monkeypatch.setattr(installer,'discover_installs',lambda **kwargs:[one,two])
    result=installer.InstallationSetup().check(Config(),True,two)
    assert result['restart_required'] and result['status']=='restart_required'
    assert result['installs'][0]['status']=='permission_denied'
    assert Path(result['installs'][1]['ini']).exists()


@pytest.mark.asyncio
async def test_application_automatically_chooses_running_copy_and_keeps_preferences(tmp_path,monkeypatch):
    from rocket_league_rpc import main,installer
    from rocket_league_rpc.config import validate_config,load_config
    steam,epic=tmp_path/'steam',tmp_path/'epic'
    for path in (steam,epic):(path/'TAGame').mkdir(parents=True)
    monkeypatch.setattr(installer,'discover_installs',lambda **kwargs:[steam,epic])
    monkeypatch.setattr(main,'running_game_info',lambda:(epic,0))
    cfg=validate_config({'language':'en','mode_ranks':{'hoops':{'tier':'Gold II','division':2}}})
    app=main.Application(cfg,tmp_path/'config.json',auto_setup=True)
    await app.configure_game_installs()
    assert app.snapshot()['installation']['active_path']==str(epic.resolve())
    assert app.config.install_path==str(epic.resolve())
    assert load_config(tmp_path/'config.json').mode_ranks['hoops']['tier']=='Gold II'
    monkeypatch.setattr(main,'running_game_info',lambda:(steam,0))
    await app.configure_game_installs()
    assert app.config.install_path==str(steam.resolve())


def test_map_variants_and_longest_family_match():
    from rocket_league_rpc.maps import lookup_map
    assert lookup_map('OUTLAW_OASIS_FX_P')==('Deadeye Canyon (Oasis)','deadeye_canyon_oasis')
    assert lookup_map('Labs_Galleon_Mast_new_P')==('Galleon (Retro)','rocket_labs')
    assert lookup_map('Paname_Dusk_event_P')==('Parc de Paris','parc_de_paris')


def test_all_rank_modes_are_independent_and_invalid_config_never_crashes():
    from rocket_league_rpc.config import validate_config
    from rocket_league_rpc.modes import RANKED_MODES
    from rocket_league_rpc.presence import build_presence
    from rocket_league_rpc.state import MatchState,Phase
    cfg=validate_config({'mode_ranks':{key:{'tier':'Gold I','division':index%4+1} for index,key in enumerate(RANKED_MODES)}})
    for key,(playlist,_) in RANKED_MODES.items():
        assert ['I','II','III','IV'][cfg.mode_ranks[key]['division']-1] in build_presence(MatchState(phase=Phase.PLAYING,playlist_id=playlist),cfg)['small_text']
    for bad in (None,[],{'hoops':[]},{'hoops':{'tier':{},'division':None}}):
        assert len(validate_config({'mode_ranks':bad}).mode_ranks)==8


def test_first_run_and_malformed_config_have_complete_independent_rank_defaults(tmp_path):
    from rocket_league_rpc.config import Config,load_config
    path=tmp_path/'config.json'
    for cfg in (Config(),load_config(path)):
        assert len(cfg.mode_ranks)==8
        assert all(v=={'tier':'Unranked','division':1} for v in cfg.mode_ranks.values())
        cfg.mode_ranks['duel']['tier']='Gold I'
        assert cfg.mode_ranks['doubles']['tier']=='Unranked'
    path.write_text('{bad')
    assert len(load_config(path).mode_ranks)==8


@pytest.mark.asyncio
async def test_startup_detects_running_game_without_executable_access(tmp_path,monkeypatch):
    from rocket_league_rpc import main,installer
    from rocket_league_rpc.config import Config
    root=tmp_path/'Steam/rocketleague';(root/'TAGame').mkdir(parents=True)
    monkeypatch.setattr(installer,'discover_installs',lambda **kwargs:[root])
    monkeypatch.setattr(main,'running_game_info',lambda:(None,None))
    monkeypatch.setattr(main,'rocket_league_running',lambda:True)
    app=main.Application(Config(),auto_setup=True)
    result=await app.configure_game_installs()
    assert result['restart_required'] and result['status']=='restart_required'
    await app.set_running(False)
    assert not app.install_setup.pending
