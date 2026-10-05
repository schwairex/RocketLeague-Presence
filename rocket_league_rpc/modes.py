"""UNVERIFIED playlist table. Official docs do not enumerate IDs."""
import logging

log = logging.getLogger(__name__)
MODES = {
    1: 'Casual 1v1', 2: 'Casual 2v2', 3: 'Casual 3v3', 4: 'Casual 4v4',
    6: 'Private Match', 9: 'Free Play', 10: 'Ranked 1v1', 11: 'Ranked 2v2', 13: 'Ranked 3v3',
    20: 'Custom Training', 21: 'Training',
    27: 'Ranked Hoops', 28: 'Ranked Rumble', 29: 'Ranked Dropshot',
    30: 'Ranked Snow Day', 34: 'Tournament', 63: 'Ranked Heatseeker',
}
# ID 63: GrantJL/rl-lobby-ranks, lobby-ranks/types.h. Verify real API values
# after playlist changes; this table does not retrieve rank data.
RANKED_MODES = {'standard':(13,'Ranked 3v3'), 'doubles':(11,'Ranked 2v2'),
                'duel':(10,'Ranked 1v1'), 'heatseeker':(63,'Ranked Heatseeker'),
                'rumble':(28,'Ranked Rumble'), 'hoops':(27,'Ranked Hoops'),
                'snow_day':(30,'Ranked Snow Day'), 'dropshot':(29,'Ranked Dropshot')}
RANK_KEY_BY_PLAYLIST = {playlist:key for key,(playlist,_) in RANKED_MODES.items()}
_unknown: set[int] = set()


def lookup_mode(playlist_id) -> str:
    if type(playlist_id) is not int:
        return 'Rocket League'
    if playlist_id in MODES:
        return MODES[playlist_id]
    if playlist_id not in _unknown:
        _unknown.add(playlist_id)
        log.info('Unknown PlaylistId %s; add it to modes.py (UNVERIFIED table).', playlist_id)
    return f'Playlist {playlist_id}'
