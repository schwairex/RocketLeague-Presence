import configparser
import json
import pytest


def test_config_default_malformed_backup_and_clamping(tmp_path):
    from rocket_league_rpc.config import Config, load_config
    path = tmp_path/'config.json'
    cfg = load_config(path)
    assert path.exists() and cfg.stats_port == 49123 and cfg.update_interval >= 1
    path.write_text('{broken', encoding='utf-8')
    assert load_config(path).stats_port == 49123
    assert list(tmp_path.glob('config.json*.bak'))
    path.write_text(json.dumps({'update_interval': 1, 'stats_port': 99999,
        'show_map': 'false', 'log_level': 'nonsense', 'stats_transport': 'UDP',
        'client_id': 123, 'stats_web_port': 49123}), encoding='utf-8')
    cfg = load_config(path)
    assert cfg.update_interval == 1 and cfg.stats_port == 49123
    assert cfg.show_map is False and cfg.log_level == 'INFO' and cfg.stats_transport == 'tcp'
    assert cfg.client_id == '802869954805760020' and cfg.stats_web_port != cfg.stats_port


@pytest.mark.parametrize('existing', ['TAStatsAPI.ini','DefaultStatsAPI.ini',None])
def test_ini_selection_backup_missing_file_and_idempotence(tmp_path, existing):
    from rocket_league_rpc.installer import patch_stats_ini
    folder = tmp_path/'TAGame'/'Config'
    folder.mkdir(parents=True)
    before = '[Other]\nKeepCase=unchanged\n'
    if existing:
        (folder/existing).write_text(before, encoding='utf-8')
    if existing == 'TAStatsAPI.ini':
        (folder/'DefaultStatsAPI.ini').write_text('fallback untouched', encoding='utf-8')
    result = patch_stats_ini(tmp_path, tcp_port=49123, web_port=49124)
    assert result.changed and result.path.name == (existing or 'DefaultStatsAPI.ini')
    ini = configparser.ConfigParser(interpolation=None)
    ini.optionxform = str
    ini.read(result.path, encoding='utf-8')
    section = ini['TAGame.MatchStatsExporter_TA']
    assert float(section['PacketSendRate']) == 30 and section['Port'] == '49123'
    assert section['WebPort'] == '49124'
    assert result.backup.read_text(encoding='utf-8') == (before if existing else '')
    after = result.path.read_bytes()
    assert not patch_stats_ini(tmp_path).changed
    assert result.path.read_bytes() == after
    if existing == 'TAStatsAPI.ini':
        assert (folder/'DefaultStatsAPI.ini').read_text() == 'fallback untouched'


def test_ini_preserves_enabled_rate_and_corrects_disabled_and_conflicting_ports(tmp_path):
    from rocket_league_rpc.installer import patch_stats_ini
    folder = tmp_path/'TAGame'/'Config'
    folder.mkdir(parents=True)
    path = folder/'TAStatsAPI.ini'
    path.write_text('[TAGame.MatchStatsExporter_TA]\nPacketSendRate=60\nPort=0\nWebPort=0\n')
    patch_stats_ini(tmp_path, tcp_port=50000, web_port=50001)
    assert 'PacketSendRate = 60' in path.read_text()
    assert 'Port = 50000' in path.read_text()
    with pytest.raises(ValueError):
        patch_stats_ini(tmp_path, tcp_port=50000, web_port=50000)


def test_maps_modes_unknown_fallback_and_logged_once(caplog):
    from rocket_league_rpc.maps import lookup_map
    from rocket_league_rpc.modes import lookup_mode
    caplog.set_level('INFO')
    assert lookup_map('stadium_p') == ('DFH Stadium','dfh_stadium')
    assert lookup_map('Stadium_Foggy_P')[1] == 'dfh_stadium'
    assert lookup_map('MysteryArena_123') == ('MysteryArena_123','rl_logo')
    lookup_map('MysteryArena_123')
    assert lookup_mode(987654) == 'Playlist 987654'
    lookup_mode(987654)
    assert len([r for r in caplog.records if 'Unknown' in r.message]) == 2
