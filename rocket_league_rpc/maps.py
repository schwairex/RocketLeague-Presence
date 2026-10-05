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
}
_normalized = {k.casefold(): v for k, v in MAPS.items()}
_families = {re.sub(r'_p$', '', k.casefold()): v for k, v in MAPS.items()
             if k in ('Stadium_P','Park_P','Utopia_Stadium','UtopiaStadium_P','Wasteland_P',
                      'NeoTokyo_P','TrainStation_P','Underwater_P','EuroStadium_P','CHN_Stadium_P','Farm_P')}
_unknown: set[str] = set()


def lookup_map(arena) -> tuple[str, str]:
    if not isinstance(arena, str) or not arena.strip():
        return ('Rocket League', 'rl_logo')
    name = arena.strip()
    key = name.casefold()
    if key in _normalized:
        return _normalized[key]
    for family, value in _families.items():
        if key.startswith(family + '_'):
            return value
    if key not in _unknown:
        _unknown.add(key)
        log.info('Unknown Arena %r; add it to maps.py (best-effort table).', name)
    return (name, 'rl_logo')
