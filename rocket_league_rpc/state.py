"""Pure defensive reducer; wall-clock sync belongs to state, not RPC timing."""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import logging
import json
import time

from .config import Config

log = logging.getLogger(__name__)


class Phase(str, Enum):
    MENU = 'MENU'
    COUNTDOWN = 'COUNTDOWN'
    PLAYING = 'PLAYING'
    GOAL_REPLAY = 'GOAL_REPLAY'
    PAUSED = 'PAUSED'
    OVERTIME = 'OVERTIME'
    ENDED = 'ENDED'
    REPLAY_VIEWER = 'REPLAY_VIEWER'
    TRAINING = 'TRAINING'


@dataclass(frozen=True)
class PlayerStats:
    name: str = ''
    primary_id: str = ''
    team: int | None = None
    score: int | None = None
    goals: int | None = None
    saves: int | None = None


@dataclass(frozen=True)
class MatchState:
    phase: Phase = Phase.MENU
    match_guid: str = ''
    arena: str = ''
    playlist_id: int | None = None
    blue_score: int = 0
    orange_score: int = 0
    time_remaining: int | None = None
    is_overtime: bool = False
    is_replay: bool = False
    winner_team: int | None = None
    local_team: int | None = None
    local_player_name: str = ''
    local_primary_id: str = ''
    clock_end: float | None = None
    # Presentation anchor only: Discord has no native paused timestamp.
    # Preserve the existing green countdown across a goal, then re-sync kickoff.
    goal_clock_end: float | None = None
    overtime_started_at: float | None = None
    last_round_started_at: float | None = None
    last_round_time_remaining: int | None = None
    overtime_round_confirmed: bool = False
    ended_at: float | None = None
    winner_name: str = ''
    players: tuple[PlayerStats, ...] = ()
    local_player_score: int | None = None
    local_player_goals: int | None = None
    local_player_saves: int | None = None


HANDLED_EVENTS = frozenset({
    'UpdateState','MatchCreated','MatchInitialized','CountdownBegin','RoundStarted',
    'ClockUpdatedSeconds','GoalScored','GoalReplayStart','GoalReplayWillEnd','GoalReplayEnd',
    'MatchPaused','MatchUnpaused','MatchEnded','PodiumStart','MatchDestroyed',
    'ReplayCreated','PlayerJoined','PlayerLeft',
})
RUNNING = (Phase.PLAYING, Phase.OVERTIME)


def normalize_event(message):
    """Official shape plus the JSON-string Data seen on real Windows TCP.

    Decode once only, after envelope framing; unknown events stay cheap.
    Raw transport logging happens before this compatibility normalization.
    """
    if not isinstance(message,dict) or not isinstance(message.get('Event'),str) or message['Event'] not in HANDLED_EVENTS:
        return message
    data = message.get('Data')
    if isinstance(data,str) and len(data) <= 2*1024*1024:
        try:
            decoded = json.loads(data)
            if isinstance(decoded,dict):
                return {**message,'Data':decoded}
        except (ValueError,RecursionError):
            pass
        log.debug('Unexpected encoded Data shape for %s',message.get('Event'))
    return message


def obj(value) -> dict:
    if isinstance(value, dict):
        return value
    log.debug('Expected object, received %s', type(value).__name__)
    return {}


def sequence(value) -> list:
    if isinstance(value, list):
        return value
    log.debug('Expected array, received %s', type(value).__name__)
    return []


def string(value, default='') -> str:
    if value is not None and not isinstance(value, str):
        log.debug('Expected string, received %s', type(value).__name__)
    return value if isinstance(value, str) else default


def integer(value, default=None):
    if value is not None and type(value) is not int:
        log.debug('Expected integer, received %s', type(value).__name__)
    return value if type(value) is int else default


def team(value) -> int | None:
    return value if type(value) is int and value in (0, 1) else None


def overtime_clock_start(state: MatchState, now: float, round_started: bool = False) -> float:
    """Single policy point: local elapsed clock, independent of TimeSeconds direction.

    Keep the first overtime RoundStarted anchor. If reconnecting without that event,
    use the first observed overtime packet; real elapsed overtime is then unknown.
    Change ONLY this function when real packets establish a better policy.
    """
    if not state.overtime_round_confirmed:
        if round_started:
            return now
        # bOvertime may arrive one tick AFTER the zero-clock kickoff.
        if state.last_round_time_remaining == 0 and state.last_round_started_at is not None:
            return state.last_round_started_at
    if state.overtime_started_at is not None:
        return state.overtime_started_at
    return now


def sync_clock(state: MatchState, now: float, force: bool = False, round_started: bool = False) -> MatchState:
    if state.phase not in RUNNING:
        return replace(state, clock_end=None)
    if state.is_overtime:
        return replace(state, phase=Phase.OVERTIME, clock_end=None,
                       overtime_started_at=overtime_clock_start(state, now, round_started),
                       overtime_round_confirmed=state.overtime_round_confirmed or round_started or (
                           state.last_round_time_remaining == 0 and state.last_round_started_at is not None))
    end = state.clock_end
    if state.time_remaining is not None and (force or end is None or abs((end-now)-state.time_remaining) > 2):
        end = now + state.time_remaining
    return replace(state, phase=Phase.PLAYING, clock_end=end)


def detect_local(players: list, game: dict, config: Config) -> tuple[int | None, str, str]:
    candidates = [p for p in players if isinstance(p, dict)]
    primary = config.player_primary_id.casefold()
    name = config.player_name.casefold()
    selected = None
    if primary:
        selected = next((p for p in candidates if string(p.get('PrimaryId')).casefold() == primary), None)
    if selected is None and name:
        selected = next((p for p in candidates if string(p.get('Name')).casefold() == name and (
            config.player_platform == 'auto' or string(p.get('PrimaryId')).split('|')[0].casefold() == config.player_platform)), None)
    if selected is None and (primary or name):
        return None, '', ''  # configured identity must not be replaced by a viewed opponent
    spectator_fields = {'Boost','Speed','bHasCar','bBoosting','bOnGround','bOnWall','bSupersonic'}
    spectating = config.spectating or any(spectator_fields.intersection(p) for p in candidates)
    if selected is None and game.get('bHasTarget') is True and not spectating:
        target = obj(game.get('Target'))
        target_name = string(target.get('Name'))
        target_team = team(target.get('TeamNum'))
        if target_name and target_team is not None:
            selected = next((p for p in candidates if string(p.get('Name')).casefold() == target_name.casefold()
                             and team(p.get('TeamNum')) == target_team), target)
    if selected is None:
        return None, '', ''
    return team(selected.get('TeamNum')), string(selected.get('Name')), string(selected.get('PrimaryId'))


def reduce_event(state: MatchState, message, config: Config, now: float | None = None) -> MatchState:
    now = time.time() if now is None else now
    message = normalize_event(message)
    if not isinstance(message, dict) or not isinstance(message.get('Event'), str):
        log.debug('Unexpected Stats envelope shape: %s', type(message).__name__)
        return state
    event = message['Event']
    if event not in HANDLED_EVENTS:
        log.debug('Ignored Stats event %s', event)
        return state
    if not isinstance(message.get('Data'), dict):
        log.debug('Unexpected Data for %s', event)
        return state
    data = message['Data']
    if event == 'MatchDestroyed':
        return MatchState()
    if event == 'ReplayCreated':
        return MatchState(phase=Phase.REPLAY_VIEWER, is_replay=True,
                          match_guid=string(data.get('MatchGuid')))
    # Loaded history can emit normal match events; it remains history until leave.
    if state.phase == Phase.REPLAY_VIEWER:
        return state
    guid = string(data.get('MatchGuid'))
    if event in ('MatchCreated','MatchInitialized'):
        if state.phase == Phase.MENU or state.phase == Phase.ENDED or (guid and guid != state.match_guid):
            state = MatchState(match_guid=guid)
        return replace(state, phase=Phase.COUNTDOWN, clock_end=None)
    if event == 'UpdateState':
        fresh = state.phase == Phase.MENU or (guid and guid != state.match_guid)
        if fresh:
            state = MatchState(phase=Phase.PLAYING, match_guid=guid)
        elif guid and not state.match_guid:
            state = replace(state, match_guid=guid)
        game = obj(data.get('Game'))
        players = sequence(data.get('Players', []))
        local_team, local_name, local_id = detect_local(players, game, config)
        blue, orange = state.blue_score, state.orange_score
        for entry in sequence(game.get('Teams', [])):
            entry = obj(entry)
            score = integer(entry.get('Score'))
            if score is not None and score >= 0:
                if team(entry.get('TeamNum')) == 0:
                    blue = score
                elif team(entry.get('TeamNum')) == 1:
                    orange = score
        seconds = integer(game.get('TimeSeconds'), state.time_remaining)
        overtime = game.get('bOvertime') if type(game.get('bOvertime')) is bool else state.is_overtime
        replay = game.get('bReplay') if type(game.get('bReplay')) is bool else state.is_replay
        phase = state.phase
        goal_end = state.goal_clock_end
        if replay and phase in RUNNING:
            goal_end = state.clock_end if not state.is_overtime else None
            phase = Phase.GOAL_REPLAY
        elif not replay and phase == Phase.GOAL_REPLAY:
            phase = Phase.COUNTDOWN  # skipped replay: wait for RoundStarted
        winner = state.winner_team
        if game.get('bHasWinner') is True:
            winner_name = string(game.get('Winner')).casefold()
            for entry in sequence(game.get('Teams', [])):
                entry = obj(entry)
                if winner_name and string(entry.get('Name')).casefold() == winner_name:
                    winner = team(entry.get('TeamNum'))
            phase = Phase.ENDED
        playlist = integer(game.get('PlaylistId'), state.playlist_id)
        if playlist in (9, 20, 21) and phase != Phase.ENDED:
            phase = Phase.TRAINING  # best-effort unverified playlist table
        player_stats = tuple(PlayerStats(string(p.get('Name')), string(p.get('PrimaryId')),
            team(p.get('TeamNum')), integer(p.get('Score')), integer(p.get('Goals')),
            integer(p.get('Saves'))) for p in players if isinstance(p, dict))
        local = next((p for p in player_stats if (local_id and p.primary_id.casefold() == local_id.casefold())
                     or (not local_id and local_name and p.name.casefold() == local_name.casefold() and p.team == local_team)), None)
        state = replace(state, phase=phase, arena=string(game.get('Arena'), state.arena),
                        goal_clock_end=goal_end if phase in (Phase.GOAL_REPLAY, Phase.COUNTDOWN) else None,
                        playlist_id=playlist, players=player_stats,
                        winner_name=string(game.get('Winner'), state.winner_name),
                        local_player_score=local.score if local else None,
                        local_player_goals=local.goals if local else None,
                        local_player_saves=local.saves if local else None,
                        blue_score=blue, orange_score=orange, time_remaining=seconds,
                        is_overtime=overtime, is_replay=replay, winner_team=winner,
                        local_team=local_team, local_player_name=local_name, local_primary_id=local_id,
                        ended_at=(state.ended_at if state.ended_at is not None else now) if phase == Phase.ENDED else None)
        if overtime:
            log.debug('Overtime TimeSeconds sample=%r (UpdateState)', game.get('TimeSeconds'))
        return sync_clock(state, now, force=fresh)
    if state.phase in (Phase.MENU, Phase.TRAINING):
        return state
    if event == 'ClockUpdatedSeconds':
        seconds = integer(data.get('TimeSeconds'), state.time_remaining)
        overtime = data.get('bOvertime') if type(data.get('bOvertime')) is bool else state.is_overtime
        state = replace(state, time_remaining=seconds, is_overtime=overtime)
        if overtime:
            log.debug('Overtime TimeSeconds sample=%r (ClockUpdatedSeconds)', data.get('TimeSeconds'))
        return sync_clock(state, now)
    if event in ('MatchEnded','PodiumStart'):
        winner = team(data.get('WinnerTeamNum'))
        return replace(state, phase=Phase.ENDED, clock_end=None, goal_clock_end=None,
                       winner_team=winner if winner is not None else state.winner_team,
                       ended_at=state.ended_at if state.ended_at is not None else now)
    if state.phase == Phase.ENDED:
        return state  # late replay/round events must not erase the result
    if event in ('GoalScored','GoalReplayStart'):
        return replace(state, phase=Phase.GOAL_REPLAY, clock_end=None, is_replay=True,
                       goal_clock_end=state.goal_clock_end or (state.clock_end if not state.is_overtime else None))
    if event in ('GoalReplayEnd','CountdownBegin'):
        return replace(state, phase=Phase.COUNTDOWN, clock_end=None, is_replay=False)
    if event == 'MatchPaused':
        return replace(state, phase=Phase.PAUSED, clock_end=None, goal_clock_end=None)
    if event in ('RoundStarted','MatchUnpaused'):
        state = replace(state, phase=Phase.OVERTIME if state.is_overtime else Phase.PLAYING,
                        is_replay=False, goal_clock_end=None,
                        last_round_started_at=now if event == 'RoundStarted' else state.last_round_started_at,
                        last_round_time_remaining=state.time_remaining if event == 'RoundStarted' else state.last_round_time_remaining)
        return sync_clock(state, now, force=True, round_started=event == 'RoundStarted')
    if event == 'PlayerLeft':
        left_id = string(data.get('PrimaryId')).casefold()
        left_name = string(data.get('PlayerName')).casefold()
        if (left_id and left_id == state.local_primary_id.casefold()) or (left_name and left_name == state.local_player_name.casefold()):
            return replace(state, local_team=None, local_player_name='', local_primary_id='',
                           local_player_score=None,local_player_goals=None,local_player_saves=None)
    if event == 'PlayerJoined':
        log.debug('PlayerJoined name=%r id=%r; team comes from UpdateState', data.get('PlayerName'), data.get('PrimaryId'))
    return state
