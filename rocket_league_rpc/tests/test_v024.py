import pytest

from rocket_league_rpc.config import Config, RANK_TIERS
from rocket_league_rpc.modes import RANKED_MODES
from rocket_league_rpc.presence import build_presence
from rocket_league_rpc.state import MatchState, Phase


@pytest.mark.parametrize('key,mode', RANKED_MODES.items())
def test_current_mode_rank_is_artwork_and_tooltip_only(key, mode):
    cfg = Config()
    cfg.mode_ranks[key] = {'tier': 'Diamond I', 'division': 4}
    state = MatchState(phase=Phase.PLAYING, playlist_id=mode[0], arena='Stadium_P', local_team=0)
    payload = build_presence(state, cfg)
    assert payload['small_image'] == 'diamond_1'
    assert payload['small_text'] == 'Diamond I Div IV'
    assert 'Diamond' not in payload['details'] + payload.get('state','')
    assert payload['large_image'] == 'dfh_stadium'
    assert payload['large_text'] == 'DFH Stadium'


def test_all_rank_asset_keys_and_ssl_without_division():
    from rocket_league_rpc.ranks import RANK_ASSETS
    assert set(RANK_ASSETS) == set(RANK_TIERS)
    assert len(set(RANK_ASSETS.values())) == len(RANK_TIERS)
    cfg = Config()
    cfg.mode_ranks['duel'] = {'tier': 'Supersonic Legend', 'division': 4}
    payload = build_presence(MatchState(phase=Phase.ENDED, playlist_id=10), cfg)
    assert payload['small_image'] == 'supersonic_legend'
    assert payload['small_text'] == 'Supersonic Legend'


@pytest.mark.parametrize('phase,playlist,show_rank,tier', [(Phase.TRAINING, 11, True, 'Diamond I'), (Phase.PLAYING, 2, True, 'Diamond I'), (Phase.PLAYING, 11, False, 'Diamond I'), (Phase.PLAYING, 11, True, 'Unranked')])
def test_rank_fallback_omits_small_artwork(phase, playlist, show_rank, tier):
    cfg = Config(show_rank=show_rank)
    cfg.mode_ranks['doubles'] = {'tier': tier, 'division': 1}
    payload = build_presence(MatchState(phase=phase, playlist_id=playlist, local_team=1), cfg)
    assert 'small_image' not in payload
    assert 'small_text' not in payload


@pytest.mark.parametrize('point,expected', [((-499,-199),13),((100,-199),12),((699,-199),14),((-499,200),10),((699,200),11),((-499,499),16),((100,499),15),((699,499),17),((100,0),1),((-501,0),1)])
def test_native_resize_hit_test_all_edges_negative_monitor(point, expected):
    from rocket_league_rpc.window_chrome import resize_hit_test
    assert resize_hit_test(*point, (-500,-200,700,500), 8) == expected


def test_maximized_window_and_dpi_scaled_border():
    from rocket_league_rpc.window_chrome import resize_hit_test
    assert resize_hit_test(10,300,(0,0,1200,700),16) == 10
    assert resize_hit_test(10,300,(0,0,1200,700),16,maximized=True) == 1


def test_download_verifying_then_handoff(tmp_path, monkeypatch):
    from rocket_league_rpc.updates import UpdateManager, parse_releases
    monkeypatch.setattr('rocket_league_rpc.updates.__version__','0.2.6')
    from .test_updates import release
    states = []
    class Client:
        def fetch(self): return parse_releases([release()])
        def stage(self, release, folder, progress):
            progress(55);states.append(manager.snapshot())
            progress(100);states.append(manager.snapshot())
            return 'verified'
    monkeypatch.setattr('rocket_league_rpc.updates.time.sleep', lambda n: None)
    manager = UpdateManager(tmp_path, client=Client(), frozen=True,
        on_ready=lambda staged: states.append(manager.snapshot()))
    manager.check(background=False)
    assert [(s['status'],s['progress']) for s in states] == [('downloading',55),('verifying',100),('restarting',100)]


def test_network_progress_does_not_claim_verification_before_stream_closes(tmp_path):
    from rocket_league_rpc.updates import GitHubReleases
    class Stream:
        def __init__(self): self.chunks = iter([b'x'*996, b'x'*4, b''])
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self,n): return next(self.chunks)
    client=GitHubReleases();client._open=lambda url:Stream()
    progress=[]
    client._download('test',tmp_path/'download.part',1000,progress.append)
    assert progress == [99,99]
