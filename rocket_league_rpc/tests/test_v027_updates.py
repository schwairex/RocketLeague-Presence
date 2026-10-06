import os
from pathlib import Path
import sys


def test_independent_restart_env_keeps_preferences_but_drops_frozen_parent():
    from rocket_league_rpc.updates import independent_restart_env
    env=independent_restart_env({'_PYI_APPLICATION_HOME_DIR':'deleted','_PYI_ARCHIVE_FILE':'old.exe',
      '_PYI_PARENT_PROCESS_LEVEL':'1','_MEIPASS2':'deleted','PYINSTALLER_RESET_ENVIRONMENT':'0',
      'RL_PRESENCE_LAUNCHER_PATH':'old.exe','RL_PRESENCE_LAUNCHER_PID':'15','PATH':'system','RL_RPC_UI_SMOKE_PATH':'fixture.json'})
    assert not any(key.startswith('_PYI_') for key in env)
    assert '_MEIPASS2' not in env and 'RL_PRESENCE_LAUNCHER_PID' not in env
    assert 'RL_PRESENCE_LAUNCHER_PATH' not in env and env['PYINSTALLER_RESET_ENVIRONMENT']=='1'
    assert env['PATH']=='system' and env['RL_RPC_UI_SMOKE_PATH']=='fixture.json'


def test_user_facing_executable_controls_config_location(monkeypatch,tmp_path):
    from rocket_league_rpc.config import app_directory, application_executable
    outer=tmp_path/'installed/rl-presence.exe';outer.parent.mkdir();outer.write_bytes(b'MZouter')
    core=tmp_path/'cache/core.exe';core.parent.mkdir();core.write_bytes(b'MZcore')
    monkeypatch.setattr(sys,'frozen',True,raising=False);monkeypatch.setattr(sys,'executable',str(core))
    monkeypatch.setenv('RL_PRESENCE_LAUNCHER_PATH',str(outer))
    assert application_executable()==outer.resolve() and app_directory()==outer.parent
    monkeypatch.setenv('RL_PRESENCE_LAUNCHER_PATH',str(tmp_path/'missing.exe'))
    assert application_executable()==core.resolve()


def test_helper_cleans_runtime_before_both_new_launch_and_rollback():
    from rocket_league_rpc.updates import HELPER
    restart=HELPER[HELPER.index('function Restart-App'):HELPER.index('$replaced =')]
    assert '_PYI_' in restart and '_MEIPASS2' in restart
    assert 'PYINSTALLER_RESET_ENVIRONMENT' in restart
    assert restart.index('PYINSTALLER_RESET_ENVIRONMENT') < restart.index('Start-Process')


def test_handoff_uses_clean_subprocess_environment(monkeypatch,tmp_path):
    from rocket_league_rpc import updates
    from rocket_league_rpc.updates import StagedUpdate
    import hashlib
    current=tmp_path/'rl-presence.exe';current.write_bytes(b'MZcurrent')
    new=tmp_path/'rl-presence-0.2.7.exe';new.write_bytes(b'MZupdated')
    calls=[]
    monkeypatch.setenv('_PYI_APPLICATION_HOME_DIR','missing')
    monkeypatch.setattr(updates.subprocess,'Popen',lambda *args,**kw:calls.append((args,kw)))
    updates.launch_handoff(current,StagedUpdate(new,hashlib.sha256(new.read_bytes()).hexdigest()),[])
    assert calls[0][1]['env']['PYINSTALLER_RESET_ENVIRONMENT']=='1'
    assert '_PYI_APPLICATION_HOME_DIR' not in calls[0][1]['env']
