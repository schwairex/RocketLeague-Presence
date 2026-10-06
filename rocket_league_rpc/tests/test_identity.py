from pathlib import Path
import pytest


def test_primary_id_and_unicode_name_normalization():
    from rocket_league_rpc.identity import normalize_primary_id, normalize_name
    assert normalize_primary_id(' STEAM|76561198000000000|2 ') == ('steam','76561198000000000')
    assert normalize_primary_id(None) is None
    assert normalize_primary_id('Steam|') is None
    assert normalize_name(' [CLAN]  Ｐｌａｙｅｒ\t NAME ') == 'player name'


@pytest.mark.parametrize('content,expected',[
    ('"users" { "76561198000000000" { "PersonaName" "One" "MostRecent" "1" } }', ('Steam|76561198000000000','One')),
    ('\ufeff"users"\r\n{ "76561198000000000" { "PersonaName" "First" "MostRecent" "0" } "76561198000000001" { "PersonaName" "Last" "MostRecent" "1" } }', ('Steam|76561198000000001','Last')),
    ('"users" { "76561198000000000" { "MostRecent" "1" ', None),
    ('"users" { "76561198000000000" { "MostRecent" "1" } "76561198000000001" { "MostRecent" "1" } }', None),
    ('"users" { "76561198000000000" { "PersonaName" "No flag" } }', None),
    ('garbage',None), ('',None)
])
def test_most_recent_vdf_is_unique_well_formed_and_not_first_user(content,expected):
    from rocket_league_rpc.identity import SteamProvider
    provider=SteamProvider(registry=lambda name:None, read_loginusers=lambda:content, steam_running=lambda:False)
    candidates=provider.candidates()
    assert [(c.primary_id_key,c.name_hint) for c in candidates] == ([] if expected is None else [expected])


def test_active_user_conversion_beats_recent_only_while_steam_runs():
    from rocket_league_rpc.identity import SteamProvider
    text='"users" { "76561197960265851" { "PersonaName" "Real Persona" } "76561198000000001" { "MostRecent" "1" } }'
    provider=SteamProvider(registry=lambda name:123 if name=='ActiveUser' else None,
                           read_loginusers=lambda:text,steam_running=lambda:True)
    candidate=provider.candidates()[0]
    assert (candidate.primary_id_key,candidate.name_hint,candidate.source)==('Steam|76561197960265851','Real Persona','steam_active')
    provider=SteamProvider(registry=lambda name:123,read_loginusers=lambda:text,steam_running=lambda:False)
    assert provider.candidates()[0].primary_id_key=='Steam|76561198000000001'


def test_missing_or_denied_steam_sources_never_raise():
    from rocket_league_rpc.identity import SteamProvider
    def denied(*args): raise PermissionError('fixture')
    assert SteamProvider(registry=denied,read_loginusers=denied,steam_running=lambda:True).candidates()==()


def test_epic_provider_only_consumes_sanitized_readable_snapshot():
    from rocket_league_rpc.identity import EpicCmdlineProvider
    from rocket_league_rpc.game_watcher import sanitize_launch_args
    data={'running':True,'readable':True,**sanitize_launch_args(['RL.exe','-epicuserid=abc123','-epicusername=Epic Persona','-AUTH_PASSWORD=forbidden'])}
    candidate=EpicCmdlineProvider(lambda:data).candidates()[0]
    assert (candidate.primary_id_key,candidate.name_hint,candidate.source)==('Epic|abc123','Epic Persona','epic_launch')
    assert EpicCmdlineProvider(lambda:{**data,'readable':False}).candidates()==()


def test_all_id_matches_precede_name_and_stale_candidate_does_not_block():
    from rocket_league_rpc.identity import IdentityCandidate as C, resolve_identity
    players=[{'Name':'Different in-game name','PrimaryId':'sTeAm|123|2','TeamNum':0},
             {'Name':'Persona','PrimaryId':'Epic|456|0','TeamNum':1}]
    candidates=[C('Steam|old','Persona','stale','high'),C('Steam|123','Persona','steam_active','high')]
    assert resolve_identity(candidates,players) is players[0]


def test_unique_names_cross_platform_and_duplicates_never_guess():
    from rocket_league_rpc.identity import IdentityCandidate as C, resolve_identity
    players=[{'Name':' [TAG]  Ｐlayer NAME','PrimaryId':'Epic|abc|0'},
             {'Name':'PS user','PrimaryId':'PS4|p|0'}, {'Name':'Xbox user','PrimaryId':'XboxOne|x|0'},
             {'Name':'Switch user','PrimaryId':'Switch|s|0'}]
    candidate=C('','player name','manual','medium')
    assert resolve_identity([candidate],players) is players[0]
    duplicate={'Name':'Player   Name','PrimaryId':'Steam|id|0'}
    assert resolve_identity([candidate],players+[duplicate]) is None
    assert resolve_identity([C('Steam|id','player name','steam_active','high')],players+[duplicate]) is duplicate


def test_malformed_players_and_candidates_are_cheap_and_safe():
    from rocket_league_rpc.identity import IdentityCandidate as C, resolve_identity
    assert resolve_identity([C('Steam|123','','steam_active','high')],[None,{},42,{'PrimaryId':[]}]) is None
