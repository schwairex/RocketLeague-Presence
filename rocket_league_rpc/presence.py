"""Discord payload formatting. No IO or rate-limit decisions here."""
import time

from .config import Config, ACTIVITIES
from .maps import lookup_map
from .modes import lookup_mode
from .state import MatchState, Phase, overtime_clock_start


def limit_text(value: str) -> str:
    value = ''.join(c for c in value if c.isprintable()).strip()
    return value[:128] if len(value) >= 2 else (value + ' ') if value else 'RL'


def rank_label(config: Config) -> str:
    if not config.show_rank or config.rank_tier == 'Unranked':
        return ''
    division = '' if config.rank_tier == 'Supersonic Legend' else f" Div {('I','II','III','IV')[config.rank_division-1]}"
    return config.rank_tier + division


def menu_presence(config: Config | None = None) -> dict:
    config = config or Config()
    return {'details': limit_text(' | '.join(filter(None, ['Rocket League', rank_label(config)]))),
            'state': ACTIVITIES.get(config.manual_activity, ACTIVITIES['auto']),
            'large_image': 'rl_logo', 'large_text': 'Rocket League'}


def build_presence(state: MatchState, config: Config, now: float | None = None) -> dict:
    now = time.time() if now is None else now
    if state.phase == Phase.MENU or (state.phase == Phase.ENDED and state.ended_at is not None and now-state.ended_at >= 60):
        return menu_presence(config)
    if state.phase == Phase.REPLAY_VIEWER:
        return {'details': 'Rocket League', 'state': 'Watching a replay',
                'large_image':'rl_logo', 'large_text':'Rocket League'}
    map_name, asset = lookup_map(state.arena)
    score = f'Blue {state.blue_score} - {state.orange_score} Orange'
    if config.show_perspective and state.local_team in (0, 1):
        ours, theirs = (state.blue_score, state.orange_score) if state.local_team == 0 else (state.orange_score, state.blue_score)
        score = f'You {ours} - {theirs} Opp'
    details = ' | '.join(filter(None, [lookup_mode(state.playlist_id) if config.show_mode else '', score if config.show_score else ''])) or 'Rocket League'
    if state.phase == Phase.TRAINING:
        details = 'Training'
    clock = '' if state.time_remaining is None else f'{max(0,state.time_remaining)//60}:{max(0,state.time_remaining)%60:02d} left'
    label = {Phase.COUNTDOWN:'Kickoff countdown', Phase.GOAL_REPLAY:'Goal replay',
             Phase.PAUSED:'Paused', Phase.ENDED:'Match finished'}.get(state.phase, '')
    if state.phase == Phase.OVERTIME:
        clock = 'Overtime'
    elif state.is_overtime and label:
        clock = 'Overtime'  # clock is static during pauses/replays even in OT
    if state.phase == Phase.ENDED:
        result = ''
        if state.winner_team in (0, 1):
            result = ('Win' if state.winner_team == state.local_team else 'Loss') if state.local_team in (0, 1) else ('Blue wins' if state.winner_team == 0 else 'Orange wins')
        details = 'Match finished' + (f': {score}' if config.show_score else '') + (f' ({result})' if result else '')
        clock = ''
    if not config.show_time or state.phase == Phase.TRAINING:
        clock = ''
    stats = ''
    if config.show_player_stats:
        stats = ' '.join(f'{key}:{value}' for key,value in (
            ('P',state.local_player_score), ('G',state.local_player_goals), ('S',state.local_player_saves)) if value is not None)
    details = ' | '.join(filter(None, [details, rank_label(config)]))
    status = ' | '.join(filter(None, [map_name if config.show_map else '', label, clock, stats])) or 'Playing Rocket League'
    payload = {'details':details, 'state':status,
               'large_image':asset if config.show_map else 'rl_logo',
               'large_text':map_name if config.show_map else 'Rocket League',
               'small_image': 'blue' if state.local_team == 0 else 'orange' if state.local_team == 1 else 'rl_logo',
               'small_text':'Team Blue' if state.local_team == 0 else 'Team Orange' if state.local_team == 1 else 'Blue vs Orange'}
    if config.show_time and state.phase == Phase.PLAYING and state.clock_end is not None and state.clock_end > now:
        payload['end'] = int(state.clock_end)
    elif config.show_time and state.phase == Phase.OVERTIME:
        payload['start'] = int(overtime_clock_start(state, now))
    return {k: limit_text(v) if isinstance(v, str) else v for k,v in payload.items()}
