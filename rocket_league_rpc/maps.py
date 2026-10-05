"""Best-effort Arena names; extend with real DEBUG packet values."""
import logging
import re

log = logging.getLogger(__name__)
# Asset keys are public configuration: README lists all unique keys.
MAPS = {
    'Stadium_P': ('DFH Stadium', 'dfh_stadium'),
    'Stadium_Day_P': ('DFH Stadium (Day)', 'dfh_stadium'),
    'Stadium_Foggy_P': ('DFH Stadium (Stormy)', 'dfh_stadium'),
    'Stadium_Winter_P': ('DFH Stadium (Snowy)', 'dfh_stadium'),
    'Park_P': ('Beckwith Park', 'beckwith_park'),
    'Park_Night_P': ('Beckwith Park (Midnight)', 'beckwith_park'),
    'Park_Rainy_P': ('Beckwith Park (Stormy)', 'beckwith_park'),
    'Utopia_Stadium': ('Utopia Coliseum', 'utopia_coliseum'),
    'UtopiaStadium_P': ('Utopia Coliseum', 'utopia_coliseum'),
    'UtopiaStadium_Dusk_P': ('Utopia Coliseum (Dusk)', 'utopia_coliseum'),
    'UtopiaStadium_Snow_P': ('Utopia Coliseum (Snowy)', 'utopia_coliseum'),
    'Wasteland_P': ('Wasteland', 'wasteland'),
    'Wasteland_Night_P': ('Wasteland (Night)', 'wasteland'),
    'NeoTokyo_P': ('Neo Tokyo', 'neo_tokyo'),
    'NeoTokyo_Standard_P': ('Neo Tokyo', 'neo_tokyo'),
    'TrainStation_P': ('Urban Central', 'urban_central'),
    'TrainStation_Dawn_P': ('Urban Central (Dawn)', 'urban_central'),
    'TrainStation_Night_P': ('Urban Central (Night)', 'urban_central'),
    'Underwater_P': ('Aquadome', 'aquadome'),
    'EuroStadium_P': ('Mannfield', 'mannfield'),
    'EuroStadium_Night_P': ('Mannfield (Night)', 'mannfield'),
    'EuroStadium_Rainy_P': ('Mannfield (Stormy)', 'mannfield'),
    'EuroStadium_Snow_P': ('Mannfield (Snowy)', 'mannfield'),
    'CHN_Stadium_P': ('Forbidden Temple', 'forbidden_temple'),
    'CHN_Stadium_Day_P': ('Forbidden Temple (Day)', 'forbidden_temple'),
    'Farm_P': ('Farmstead', 'farmstead'),
    'Farm_Night_P': ('Farmstead (Night)', 'farmstead'),
    'Stadium_Race_Day_P': ('DFH Stadium (Circuit)', 'dfh_stadium'),
    'Stadium_10A_P': ('DFH Stadium (Anniversary)', 'dfh_stadium'),
    'Park_Snowy_P': ('Beckwith Park (Snowy)', 'beckwith_park'),
    'Park_Bman_P': ('Beckwith Park (Gotham Night)', 'beckwith_park'),
    'UtopiaStadium_Lux_P': ('Utopia Coliseum (Gilded)', 'utopia_coliseum'),
    'Wasteland_GRS_P': ('Wasteland (Pitched)', 'wasteland'),
    'Wasteland_Art_P': ('Wasteland', 'wasteland'),
    'Wasteland_S_P': ('Wasteland', 'wasteland'),
    'Wasteland_Night_S_P': ('Wasteland (Night)', 'wasteland'),
    'NeoTokyo_Toon_P': ('Neo Tokyo (Comic)', 'neo_tokyo'),
    'NeoTokyo_Hax_P': ('Neo Tokyo (Hacked)', 'neo_tokyo'),
    'NeoTokyo_Hax_Signs_P': ('Neo Tokyo (Hacked)', 'neo_tokyo'),
    'NeoTokyo_Hax_Signs_Off_P': ('Neo Tokyo (Hacked)', 'neo_tokyo'),
    'NeoTokyo_Arcade_P': ('Neo Tokyo (Arcade)', 'neo_tokyo'),
    'Haunted_TrainStation_P': ('Urban Central (Haunted)', 'urban_central'),
    'Underwater_GRS_P': ('Aquadome (Shallows)', 'aquadome'),
    'EuroStadium_Dusk_P': ('Mannfield (Dusk)', 'mannfield'),
    'EuroStadium_SnowNight_P': ('Mannfield (Snowy)', 'mannfield'),
    'FNI_Stadium_P': ('Forbidden Temple (Fire and Ice)', 'forbidden_temple'),
    'Farm_HW_P': ('Farmstead (Spooky)', 'farmstead'),
    'Farm_GRS_P': ('Farmstead (Pitched)', 'farmstead'),
    'CS_P': ('Champions Field', 'champions_field'),
    'CS_Day_P': ('Champions Field (Day)', 'champions_field'),
    'CS_HW_P': ('Rivals Arena', 'rivals_arena'),
    'BB_P': ('Champions Field (NFL)', 'champions_field'),
    'Swoosh_P': ('Champions Field (Nike FC)', 'champions_field'),
    'ARC_Standard_P': ('Starbase ARC', 'starbase_arc'),
    'ARC_P': ('Arctagon', 'arctagon'),
    'ARC_Darc_P': ('Starbase ARC (Aftermath)', 'starbase_arc_aftermath'),
    'Beach_P': ('Salty Shores', 'salty_shores'),
    'Beach_Night_P': ('Salty Shores (Night)', 'salty_shores'),
    'Beach_Night_GRS_P': ('Salty Shores (Salty Fest)', 'salty_shores'),
    'HoopsStadium_P': ('Dunk House', 'dunk_house'),
    'HoopsStreet_P': ('The Block', 'the_block'),
    'HoopsStreet_Art_P': ('The Block', 'the_block'),
    'ShatterShot_P': ('Core 707', 'core_707'),
    'ThrowbackStadium_P': ('Throwback Stadium', 'throwback_stadium'),
    'ThrowbackHockey_P': ('Throwback Stadium (Snowy)', 'throwback_stadium'),
    'Music_P': ('Neon Fields', 'neon_fields'),
    'Outlaw_P': ('Deadeye Canyon', 'deadeye_canyon'),
    'Outlaw_Oasis_P': ('Deadeye Canyon (Oasis)', 'deadeye_canyon_oasis'),
    'Street_P': ('Sovereign Heights', 'sovereign_heights'),
    'FF_Dusk_P': ('Estadio Vida (Dusk)', 'estadio_vida'),
    'Woods_P': ('Drift Woods', 'drift_woods'),
    'Woods_Night_P': ('Drift Woods (Night)', 'drift_woods'),
    'Woods_Forest_P': ('Drift Woods (Forest)', 'drift_woods'),
    'UF_Day_P': ('Futura Garden', 'futura_garden'),
    # Inferred from the installed UF_Night_P package and Season 23 arena news.
    'UF_Night_P': ('United Futura', 'united_futura'),
    'Mall_Day_P': ('Boostfield Mall', 'boostfield_mall'),
    'Paname_Dusk_P': ('Parc de Paris', 'parc_de_paris'),
    'KO_Quadron_P': ('Quadron', 'quadron'),
    'KO_Calavera_P': ('Calavera', 'calavera'),
    'KO_Carbon_P': ('Carbon', 'carbon'),
    'Labs_4v4_Arena15_EuroStadium_Night_P': ('Mannfield (Quads)', 'mannfield'),
    'Labs_4v4_Arena15_Blackout_P': ('Midnight Metro (Quads)', 'midnight_metro'),
    'Labs_4v4_Arena15_Retro_P': ('Sunset Dunes (Quads)', 'sunset_dunes'),
}
# Rocket Labs layouts share one Discord artwork; their names remain distinct.
for _arena, _name in {
    'CirclePillars': 'Pillars', 'Cosmic': 'Cosmic', 'Cosmic_V4': 'Cosmic',
    'DoubleGoal': 'Double Goal', 'DoubleGoal_V2': 'Double Goal',
    'Octagon': 'Octagon', 'Octagon_02': 'Octagon', 'Octagon_Vent': 'Octagon (Vent)',
    'Underpass': 'Underpass', 'Underpass_v0': 'Underpass', 'Utopia': 'Utopia Retro',
    'Basin': 'Basin', 'Corridor': 'Corridor', 'Holyfield': 'Loophole',
    'Galleon': 'Galleon', 'Galleon_Mast': 'Galleon (Retro)',
    'PillarGlass': 'Hourglass', 'PillarHeat': 'Barricade', 'PillarWings': 'Colossus',
    'Holyfield_Space': 'Holyfield', 'Octagon_B2B_02': 'Roadblock',
}.items():
    MAPS[f'Labs_{_arena}_P'] = (_name, 'rocket_labs')
_normalized = {k.casefold(): v for k, v in MAPS.items()}
_families = sorted(((re.sub(r'_p$', '', k.casefold()), v) for k, v in MAPS.items()),
                   key=lambda item: len(item[0]), reverse=True)
_unknown: set[str] = set()


def lookup_map(arena) -> tuple[str, str]:
    if not isinstance(arena, str) or not arena.strip():
        return ('Rocket League', 'rl_logo')
    name = arena.strip()
    key = name.casefold()
    if key in _normalized:
        return _normalized[key]
    for family, value in _families:
        if key.startswith(family + '_'):
            return value
    if key not in _unknown:
        _unknown.add(key)
        log.info('Unknown Arena %r; add it to maps.py (best-effort table).', name)
    return (name, 'rl_logo')
