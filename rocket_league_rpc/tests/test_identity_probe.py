import json
import psutil
from rocket_league_rpc import game_watcher


def test_probe_ignores_scalar_user_entries(monkeypatch,tmp_path):
    import sys
    from types import SimpleNamespace
    from contextlib import nullcontext
    from rocket_league_rpc.identity_probe import run_probe
    (tmp_path/'config').mkdir();(tmp_path/'config/loginusers.vdf').write_text('"users" { "76561198000000000" "not-an-object" }')
    registry=SimpleNamespace(HKEY_CURRENT_USER=1,OpenKey=lambda *args:nullcontext(1),
       QueryValueEx=lambda key,name:(123 if name=='ActiveUser' else str(tmp_path),1))
    monkeypatch.setitem(sys.modules,'winreg',registry)
    monkeypatch.setattr('psutil.process_iter',lambda *args:[])
    result=run_probe(base=tmp_path)
    assert result['steam']['users_count']==0 and result['read_only']


def test_sanitizer_discards_credentials_before_returning_launch_snapshot():
    args = ['RocketLeague.exe', '-epicusername=Safe Name', '-AUTH_PASSWORD=do-not-retain',
            '-AUTH_LOGIN', 'also-forbidden', '-exchangeCode=third-secret',
            '-epicuserid', 'abc123', '-access_token', 'fourth-secret', '-nomovie']
    result = game_watcher.sanitize_launch_args(args)
    wire = json.dumps(result)
    assert all(secret not in wire for secret in ('do-not-retain','also-forbidden','third-secret','fourth-secret'))
    assert result['epicusername'] == 'Safe Name' and result['epicuserid'] == 'abc123'
    assert result['argument_names'] == ['epicusername','epicuserid','nomovie']


def test_secret_parameter_cannot_be_used_as_an_identity_value():
    result = game_watcher.sanitize_launch_args(['RocketLeague.exe','-epicusername','-AUTH_PASSWORD=secret','-epicuserid=TOKEN:secret'])
    assert result['epicusername'] == result['epicuserid'] == ''
    assert 'secret' not in json.dumps(result)


def test_game_cmdline_snapshot_handles_access_denied_and_no_game():
    class Process:
        info = {'name':'RocketLeague.exe'}
        def cmdline(self): raise psutil.AccessDenied(123)
    denied = game_watcher.sanitized_game_cmdline(lambda fields: [Process()])
    assert denied['running'] and not denied['readable'] and denied['error']=='AccessDenied'
    assert game_watcher.sanitized_game_cmdline(lambda fields: [])['running'] is False


def test_probe_cli_does_not_load_config_or_start_application(monkeypatch,capsys):
    from rocket_league_rpc import main, identity_probe
    monkeypatch.setattr(identity_probe,'run_probe',lambda *args,**kw:{'read_only':True,'ids':'redacted'})
    def forbidden(*args,**kwargs): raise AssertionError('Probe must not write settings/logs or start the engine')
    monkeypatch.setattr(main,'load_config',forbidden)
    monkeypatch.setattr(main,'configure_logging',forbidden)
    assert main.cli(['--identity-probe']) == 0
    assert json.loads(capsys.readouterr().out)['read_only']
