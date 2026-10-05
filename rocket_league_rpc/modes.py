"""UNVERIFIED playlist table. Official docs do not enumerate IDs."""
import logging

log = logging.getLogger(__name__)
MODES = {
    1: 'Casual Duel', 2: 'Casual Doubles', 3: 'Casual Standard', 4: 'Casual Chaos',
    6: 'Private Match', 9: 'Free Play', 10: 'Ranked Duel', 11: 'Ranked Doubles', 13: 'Ranked Standard',
    20: 'Custom Training', 21: 'Training',
    27: 'Ranked Hoops', 28: 'Ranked Rumble', 29: 'Ranked Dropshot',
    30: 'Ranked Snow Day', 34: 'Tournament',
}
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
