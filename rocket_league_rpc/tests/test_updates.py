import hashlib
from pathlib import Path

import pytest

REPO = 'https://github.com/schwairex/RocketLeague-Presence'


def release(version='0.2.4', blob=b'MZ' + b'x' * 80):
    return {'tag_name': 'v' + version, 'name': 'RL Presence ' + version,
        'body': 'Yeni özellikler\n<script>bad()</script>', 'draft': False, 'prerelease': False,
        'published_at': '2026-10-05T12:00:00Z', 'html_url': REPO + '/releases/tag/v' + version,
        'assets': [{'name': 'rl-presence.exe', 'size': len(blob),
            'digest': 'sha256:' + hashlib.sha256(blob).hexdigest(),
            'browser_download_url': REPO + '/releases/download/v' + version + '/rl-presence.exe'}]}


def test_release_selection_versions_and_host_validation():
    from rocket_league_rpc.updates import parse_releases, version_tuple
    releases = parse_releases([release(), release('0.10.0'), {'tag_name': 'bad'}])
    assert releases[0].version == '0.10.0'
    assert version_tuple('0.10.0') > version_tuple('0.2.9')
    bad = release(); bad['assets'][0]['browser_download_url'] = 'https://example.com/rl-presence.exe'
    assert parse_releases([bad])[0].asset is None
    preview = release(); preview['prerelease'] = True
    assert parse_releases([preview]) == []
    assert parse_releases({}) == []


def test_verified_download_and_checksum_mismatch_removes_staging(tmp_path):
    from rocket_league_rpc.updates import GitHubReleases, parse_releases
    blob = b'MZ' + b'x' * 80
    client = GitHubReleases()
    client._download = lambda url, path, size, progress: path.write_bytes(blob)
    target = client.stage(parse_releases([release(blob=blob)])[0], tmp_path)
    assert target.path.read_bytes() == blob
    bad = release(blob=blob); bad['assets'][0]['digest'] = 'sha256:' + '0' * 64
    with pytest.raises(ValueError, match='SHA-256'):
        client.stage(parse_releases([bad])[0], tmp_path)
    assert not list(tmp_path.glob('*.part'))


def test_missing_checksum_and_non_executable_are_rejected(tmp_path):
    from rocket_league_rpc.updates import GitHubReleases, parse_releases
    data = release(); data['assets'][0].pop('digest')
    with pytest.raises(ValueError, match='SHA-256'):
        GitHubReleases().stage(parse_releases([data])[0], tmp_path)
    data = release(blob=b'not an executable')
    client = GitHubReleases()
    client._download = lambda url, path, size, progress: path.write_bytes(b'not an executable')
    with pytest.raises(ValueError, match='EXE'):
        client.stage(parse_releases([data])[0], tmp_path)


def test_helper_keeps_paths_out_of_powershell_code(tmp_path):
    from rocket_league_rpc.updates import prepare_handoff
    current = tmp_path / "a ' $(bad)" / 'rl-presence.exe'
    current.parent.mkdir(); current.write_bytes(b'old')
    staged = tmp_path / 'new.exe'; staged.write_bytes(b'new')
    script, manifest = prepare_handoff(current, staged, pid=99999, args=['--debug'],expected_sha256=hashlib.sha256(b'new').hexdigest())
    assert '$(bad)' not in script.read_text()
    import json
    data = json.loads(manifest.read_text())
    assert data['current'] == str(current.resolve()) and data['args'] == ['--debug']
    assert '-LiteralPath' in script.read_text() and 'backup' in script.read_text()


def test_update_manager_offline_does_not_call_relaunch(tmp_path):
    from rocket_league_rpc.updates import UpdateManager
    class Offline:
        def fetch(self): raise OSError('offline')
    called = []
    manager = UpdateManager(tmp_path, client=Offline(), on_ready=lambda p: called.append(p))
    manager.check(background=False)
    assert manager.snapshot()['status'] == 'error' and not called


def test_source_run_shows_release_without_replacing_python(tmp_path):
    from rocket_league_rpc.updates import UpdateManager, parse_releases
    class Client:
        def fetch(self): return parse_releases([release()])
        def stage(self, *args): raise AssertionError('source run must not update Python')
    manager = UpdateManager(tmp_path, client=Client(), frozen=False)
    manager.check(background=False)
    assert manager.snapshot()['status'] == 'available'
    assert manager.snapshot()['latest_version'] == '0.2.4'


def test_relaunch_keeps_resolved_configuration_path(tmp_path):
    from rocket_league_rpc.updates import relaunch_args
    config = tmp_path / 'Türkçe yol' / 'config.json'
    for args in (['--debug','--config','relative/config.json'], ['--config=relative/config.json','--debug']):
        assert relaunch_args(args,config) == ['--debug','--config',str(config.resolve())]


def test_checksum_file_fallback(tmp_path):
    from rocket_league_rpc.updates import GitHubReleases, parse_releases
    blob = b'MZ' + b'x' * 80
    data = release(blob=blob); data['assets'][0].pop('digest')
    url = REPO + '/releases/download/v0.2.4/SHA256SUMS.txt'
    data['assets'].append({'name':'SHA256SUMS.txt','browser_download_url':url})
    client = GitHubReleases()
    client._read = lambda *args: (hashlib.sha256(blob).hexdigest()+'  rl-presence.exe\n').encode()
    client._download = lambda url,path,size,progress: path.write_bytes(blob)
    assert client.stage(parse_releases([data])[0],tmp_path).path.read_bytes() == blob


def test_frozen_update_notifies_stages_then_hands_off(tmp_path,monkeypatch):
    from rocket_league_rpc.updates import UpdateManager, parse_releases
    import rocket_league_rpc.updates as updates
    monkeypatch.setattr(updates.time,'sleep',lambda seconds: None)
    staged = tmp_path/'staged.exe'
    called=[]
    class Client:
        def fetch(self): return parse_releases([release()])
        def stage(self,release,folder,progress):
            assert manager.snapshot()['status']=='downloading'
            progress(50);assert manager.snapshot()['progress']==50
            return staged
    manager = UpdateManager(tmp_path,client=Client(),frozen=True,on_ready=called.append)
    manager.check(background=False)
    assert called==[staged] and manager.snapshot()['status']=='restarting'


def test_frozen_download_failure_keeps_rpc_and_config(tmp_path,monkeypatch):
    from rocket_league_rpc.updates import UpdateManager, parse_releases
    import rocket_league_rpc.updates as updates
    monkeypatch.setattr(updates.time,'sleep',lambda seconds: None)
    config = tmp_path/'config.json'; config.write_text('{"player_name":"PlayerA"}')
    called=[]
    class Client:
        def fetch(self): return parse_releases([release()])
        def stage(self,*args): raise OSError('download interrupted')
    manager = UpdateManager(tmp_path,client=Client(),frozen=True,on_ready=called.append)
    manager.check(background=False)
    assert not called and manager.snapshot()['status']=='error'
    assert config.read_text()=='{"player_name":"PlayerA"}'


def test_failed_release_does_not_auto_restart_loop(tmp_path,monkeypatch):
    from rocket_league_rpc.updates import UpdateManager, parse_releases
    import rocket_league_rpc.updates as updates
    import json
    monkeypatch.setattr(updates.time,'sleep',lambda seconds: None)
    folder=tmp_path/'.updates';folder.mkdir()
    (folder/'failed-release.json').write_text(json.dumps({'version':'0.2.4'}))
    called=[]
    class Client:
        def fetch(self): return parse_releases([release()])
        def stage(self,*args): return folder/'rl-presence-0.2.4.exe'
    for _ in range(2):
        manager=UpdateManager(tmp_path,client=Client(),frozen=True,on_ready=called.append)
        manager.check(background=False)
        assert manager.snapshot()['status']=='blocked'
    assert not called
    manager.check(background=False,retry_failed=True)
    assert len(called)==1


def test_verified_digest_survives_stage_to_handoff_and_detects_changed_file(tmp_path):
    from rocket_league_rpc.updates import GitHubReleases, parse_releases, prepare_handoff
    blob=b'MZ'+b'x'*80
    client=GitHubReleases();client._download=lambda url,path,size,progress:path.write_bytes(blob)
    staged=client.stage(parse_releases([release(blob=blob)])[0],tmp_path)
    staged.path.write_bytes(b'MZ'+b'y'*80)
    with pytest.raises(ValueError,match='SHA-256'):
        prepare_handoff(tmp_path/'rl-presence.exe',staged.path,999999,[],staged.sha256)
