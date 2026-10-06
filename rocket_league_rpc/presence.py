"""Discord payload formatting. No IO or rate-limit decisions here."""
import time

from .config import Config, ACTIVITIES
from .maps import lookup_map
from .ranks import RANK_ASSETS
from .modes import lookup_mode, RANK_KEY_BY_PLAYLIST
from .state import MatchState, Phase, overtime_clock_start


def limit_text(value: str) -> str:
    value = ''.join(c for c in value if c.isprintable()).strip()
    return value[:128] if len(value) >= 2 else (value + ' ') if value else 'RL'


def rank_label(config: Config, playlist_id=None) -> str:
    key = RANK_KEY_BY_PLAYLIST.get(playlist_id) if type(playlist_id) is int else None
    if not config.show_rank or key is None:
        return ''
    rank = config.mode_ranks.get(key, {'tier':config.rank_tier,'division':config.rank_division})
    tier = rank['tier']
    if tier == 'Unranked':return ''
    division = '' if tier == 'Supersonic Legend' else f" Div {('I','II','III','IV')[rank['division']-1]}"
    return tier + division


def menu_presence(config: Config | None = None) -> dict:
    config = config or Config()
    return {'name': 'Rocket League', 'details': 'Rocket League',
            'state': ACTIVITIES.get(config.manual_activity, ACTIVITIES['auto']),
            'large_image': 'rl_logo', 'large_text': 'Rocket League'}


def build_presence(state: MatchState, config: Config, now: float | None = None) -> dict:
    now = time.time() if now is None else now
    if state.phase == Phase.MENU or (state.phase == Phase.ENDED and state.ended_at is not None and now-state.ended_at >= 60):
        return menu_presence(config)
    if state.phase == Phase.REPLAY_VIEWER:
        return {'name': 'Rocket League', 'details': 'Rocket League', 'state': 'Watching a replay',
                'large_image':'rl_logo', 'large_text':'Rocket League'}
    if state.phase in (Phase.COUNTDOWN, Phase.PLAYING) and state.playlist_id is None and not state.arena:
        # Lifecycle events precede the first authoritative mode/map snapshot.
        # Do not flash a fake 0-0 kickoff card when entering free play.
        return menu_presence(config)
    map_name, asset = lookup_map(state.arena)
    score = f'🔵 {state.blue_score} - {state.orange_score} 🟠'
    if config.show_perspective and state.local_team in (0, 1):
        ours, theirs = (state.blue_score, state.orange_score) if state.local_team == 0 else (state.orange_score, state.blue_score)
        own_icon, opponent_icon = ('🔵', '🟠') if state.local_team == 0 else ('🟠', '🔵')
        score = f'{own_icon} You {ours} - {theirs} Opp {opponent_icon}'
    details = ' • '.join(filter(None, [lookup_mode(state.playlist_id) if config.show_mode else '', score if config.show_score else ''])) or 'Rocket League'
    if state.phase == Phase.TRAINING:
        details = 'Training'
    if state.phase == Phase.ENDED:
        result = ''
        if state.winner_team in (0, 1):
            result = ('Win' if state.winner_team == state.local_team else 'Loss') if state.local_team in (0, 1) else ('Blue wins' if state.winner_team == 0 else 'Orange wins')
        details = 'Match finished' + (f': {score}' if config.show_score else '') + (f' ({result})' if result else '')
    stats = ''
    if config.show_player_stats and state.phase != Phase.TRAINING and any(value is not None for value in (
            state.local_player_goals,state.local_player_saves,state.local_player_score)):
        # Missing identity/API fields are unknown, never guessed zero/opponent stats.
        stats = '  '.join(f'{key}{value if value is not None else "—"}' for key,value in (
            ('⚽',state.local_player_goals), ('🧤',state.local_player_saves), ('⭐',state.local_player_score)))
    status = (map_name if config.show_map else '') if state.phase == Phase.TRAINING else stats
    payload = {'name':'Rocket League', 'details':details,
               'large_image':asset if config.show_map else 'rl_logo',
               'large_text':map_name if config.show_map else 'Rocket League'}
    if status:
        payload['state'] = status
    rank = rank_label(config, state.playlist_id) if state.phase != Phase.TRAINING else ''
    if rank:
        key = RANK_KEY_BY_PLAYLIST[state.playlist_id]
        tier = config.mode_ranks.get(key, {'tier':config.rank_tier})['tier']
        payload.update(small_image=RANK_ASSETS[tier], small_text=rank)
    if config.show_time and state.phase == Phase.PLAYING and state.clock_end is not None and state.clock_end > now:
        payload['end'] = int(state.clock_end)
    elif config.show_time and state.phase == Phase.OVERTIME:
        payload['start'] = int(overtime_clock_start(state, now))
    return {k: limit_text(v) if isinstance(v, str) else v for k,v in payload.items()}
