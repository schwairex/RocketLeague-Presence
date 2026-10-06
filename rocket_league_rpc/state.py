"""Pure defensive reducer; wall-clock sync belongs to state, not RPC timing."""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import logging
import json
import time

from .config import Config
from .identity import IdentityCandidate, normalize_primary_id, normalize_name, resolve_candidates

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
    clock_stopped_at: float | None = None
    resume_phase: Phase | None = None
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
    identity_hints: tuple[IdentityCandidate, ...] = ()
    identity_source: str = ''
    identity_confidence: str = ''
    identity_validated: bool = False
    identity_votes: tuple[str, ...] = ()
    identity_last_target: str = ''
    identity_consecutive: int = 0
    identity_spectator_seen: bool = False
    identity_warnings: tuple[str, ...] = ()


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
    anchor = state.overtime_started_at
    if not state.overtime_round_confirmed:
        if round_started:
            return now
        # bOvertime may arrive one tick AFTER the zero-clock kickoff.
        if state.last_round_time_remaining == 0 and state.last_round_started_at is not None:
            anchor = state.last_round_started_at
    if anchor is not None:
        stopped = max(0, now-max(state.clock_stopped_at, anchor)) if state.clock_stopped_at is not None else 0
        return anchor + stopped
    return now


def stop_clock(state: MatchState, phase: Phase, now: float) -> MatchState:
    return replace(state, phase=phase, clock_end=None,
                   clock_stopped_at=state.clock_stopped_at if state.clock_stopped_at is not None else now)


def sync_clock(state: MatchState, now: float, force: bool = False, round_started: bool = False) -> MatchState:
    if state.phase not in RUNNING:
        if state.is_overtime and state.overtime_started_at is None:
            frozen_at = state.clock_stopped_at if state.clock_stopped_at is not None else now
            state = replace(state, overtime_started_at=overtime_clock_start(state, frozen_at))
        return replace(state, clock_end=None)
    if state.is_overtime:
        return replace(state, phase=Phase.OVERTIME, clock_end=None,
                       overtime_started_at=overtime_clock_start(state, now, round_started),
                       clock_stopped_at=None, resume_phase=None,
                       overtime_round_confirmed=state.overtime_round_confirmed or round_started or (
                           state.last_round_time_remaining == 0 and state.last_round_started_at is not None))
    end = state.clock_end
    if state.time_remaining is not None and (force or end is None or abs((end-now)-state.time_remaining) > 2):
        end = now + state.time_remaining
    round_anchor = state.last_round_started_at
    # Keep a zero-clock kickoff valid if bOvertime arrives only after unpause.
    if not round_started and state.last_round_time_remaining == 0 and round_anchor is not None and state.clock_stopped_at is not None:
        round_anchor += max(0, now-max(state.clock_stopped_at, round_anchor))
    return replace(state, phase=Phase.PLAYING, clock_end=end, clock_stopped_at=None,
                   resume_phase=None, last_round_started_at=round_anchor)


def clear_identity(state: MatchState) -> MatchState:
    return replace(state,local_team=None,local_player_name='',local_primary_id='',
                   local_player_score=None,local_player_goals=None,local_player_saves=None,
                   identity_source='',identity_confidence='',identity_validated=False)


def set_identity_hints(state: MatchState, candidates, reset: bool = False) -> MatchState:
    """Single injection point; discovery has no ownership of clocks or match phases."""
    hints = tuple(c for c in candidates if isinstance(c,IdentityCandidate)) if isinstance(candidates,(list,tuple)) else ()
    if hints == state.identity_hints and not reset:
        return state
    return replace(clear_identity(state),identity_hints=hints,identity_votes=(),
                   identity_last_target='',identity_consecutive=0)


def _warn_identity(state, key, message):
    if key not in state.identity_warnings:
        log.warning('%s',message)  # never include account identifiers in WARNING/INFO
        state = replace(state,identity_warnings=state.identity_warnings+(key,))
    return state


def detect_local(state: MatchState, players: list, game: dict, config: Config, count_vote=True):
    players = [p for p in players if isinstance(p,dict)]
    spectator_fields = {'Boost','Speed','bHasCar','bBoosting','bOnGround','bOnWall','bSupersonic'}
    spectator_seen = state.identity_spectator_seen or config.spectating or any(spectator_fields.intersection(p) for p in players)
    state = replace(state,identity_spectator_seen=spectator_seen)
    cached = (config.identity_mode == 'auto' and bool(config.learned_primary_id)
              and normalize_primary_id(config.player_primary_id) == normalize_primary_id(config.learned_primary_id))
    if cached and players and not any(normalize_primary_id(p.get('PrimaryId')) == normalize_primary_id(config.player_primary_id) for p in players):
        state = _warn_identity(state,'learned_cache','Identity learned_cache is absent in this match; checking current local sources.')
    manual = IdentityCandidate('' if cached else config.player_primary_id,config.player_name,'manual_override','high')
    resolution = resolve_candidates((manual,),players) if manual.primary_id_key or manual.name_hint else None
    if resolution is None and (manual.primary_id_key or manual.name_hint) and players:
        state = _warn_identity(state,'manual_override','Identity manual_override is absent or ambiguous in this match; checking other local sources.')
    if resolution is not None:
        # A learned ID matching a currently validated provider remains automatic.
        if config.identity_mode == 'auto':
            automatic = resolve_candidates(state.identity_hints,players)
            if automatic and automatic.player is resolution.player:
                resolution = automatic
    elif config.identity_mode == 'auto':
        for candidate in state.identity_hints:
            if candidate.primary_id_key and not any(normalize_primary_id(p.get('PrimaryId')) == normalize_primary_id(candidate.primary_id_key) for p in players) and players:
                state = _warn_identity(state,candidate.source,'Identity '+candidate.source+' is absent in this match; checking other local sources.')
        resolution = resolve_candidates(state.identity_hints,players)
        if resolution is None and cached:
            resolution = resolve_candidates((IdentityCandidate(config.player_primary_id,'','learned_cache','medium'),),players)
    selected = resolution.player if resolution else None
    source, confidence = (resolution.source,resolution.confidence) if resolution else ('','')
    validated = resolution is not None
    if selected and config.player_platform != 'auto':
        primary = normalize_primary_id(selected.get('PrimaryId'))
        if primary and primary[0] != config.player_platform:
            state = _warn_identity(state,'platform','Ignoring platform preference: the unique match-validated identity uses another platform.')
    # Target is only the viewed car. Vote conservatively, revoke on a view change,
    # and retain spectator evidence until the match is destroyed.
    target_player = None
    key = ''
    if not selected and config.identity_mode == 'auto' and not config.spectating and not spectator_seen and game.get('bHasTarget') is True:
        target = obj(game.get('Target'))
        target_name, target_team = normalize_name(target.get('Name')),team(target.get('TeamNum'))
        matches = [p for p in players if target_name and normalize_name(p.get('Name')) == target_name and team(p.get('TeamNum')) == target_team
                   and ('Shortcut' not in target or 'Shortcut' not in p or target['Shortcut'] == p['Shortcut'])]
        if len(matches) == 1:
            target_player = matches[0]
            primary = normalize_primary_id(target_player.get('PrimaryId'))
            key = repr(primary) if primary else repr((target_name,target_team))
    votes = (state.identity_votes+(key,))[-10:] if count_vote else state.identity_votes
    consecutive = (state.identity_consecutive+1 if key and key == state.identity_last_target else 1 if key else 0) if count_vote else state.identity_consecutive if key == state.identity_last_target else 0
    if target_player and consecutive >= 5 and votes.count(key)/len(votes) >= .8:
        selected,source,confidence = target_player,'target_vote','low'
    previous_source = state.identity_source
    state = replace(state,identity_votes=votes,identity_last_target=key if count_vote else state.identity_last_target,identity_consecutive=consecutive,
                    identity_source=source,identity_confidence=confidence,identity_validated=validated)
    if selected is None:
        return clear_identity(state),None,'',''
    primary_id = string(selected.get('PrimaryId'))
    if source != previous_source or primary_id != state.local_primary_id:
        log.info('Account identified: source=%s confidence=%s (identifier redacted)',source,confidence)
        log.debug('Account PrimaryId=%r',primary_id)
    return state,team(selected.get('TeamNum')),string(selected.get('Name')),primary_id


def reduce_event(state: MatchState, message, config: Config, now: float | None = None, *, count_identity_vote=True) -> MatchState:
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
        return MatchState(identity_hints=state.identity_hints)
    if event == 'ReplayCreated':
        return MatchState(phase=Phase.REPLAY_VIEWER, is_replay=True, identity_hints=state.identity_hints,
                          match_guid=string(data.get('MatchGuid')))
    # Loaded history can emit normal match events; it remains history until leave.
    if state.phase == Phase.REPLAY_VIEWER:
        return state
    guid = string(data.get('MatchGuid'))
    if event in ('MatchCreated','MatchInitialized'):
        if state.phase == Phase.MENU or state.phase == Phase.ENDED or (guid and guid != state.match_guid):
            state = MatchState(match_guid=guid,identity_hints=state.identity_hints)
        return stop_clock(state, Phase.COUNTDOWN, now)
    if event == 'UpdateState':
        fresh = state.phase == Phase.MENU or (guid and guid != state.match_guid)
        if fresh:
            state = MatchState(phase=Phase.PLAYING, match_guid=guid,identity_hints=state.identity_hints)
        elif guid and not state.match_guid:
            state = replace(state, match_guid=guid)
        game = obj(data.get('Game'))
        players = sequence(data.get('Players', []))
        state, local_team, local_name, local_id = detect_local(state,players,game,config,count_identity_vote)
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
        if replay and phase in RUNNING:
            state = stop_clock(state, Phase.GOAL_REPLAY, now)
            phase = Phase.GOAL_REPLAY
        elif not replay and phase == Phase.GOAL_REPLAY:
            phase = Phase.COUNTDOWN  # skipped replay: wait for RoundStarted
        elif phase == Phase.PAUSED and state.resume_phase in RUNNING and replay:
            state = replace(state, resume_phase=Phase.GOAL_REPLAY)
        elif phase == Phase.PAUSED and state.resume_phase == Phase.GOAL_REPLAY and not replay:
            state = replace(state, resume_phase=Phase.COUNTDOWN)
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
        return replace(state, phase=Phase.ENDED, clock_end=None, clock_stopped_at=None, resume_phase=None,
                       winner_team=winner if winner is not None else state.winner_team,
                       ended_at=state.ended_at if state.ended_at is not None else now)
    if state.phase == Phase.ENDED:
        return state  # late replay/round events must not erase the result
    if event in ('GoalScored','GoalReplayStart'):
        if state.phase == Phase.PAUSED:
            return replace(state, resume_phase=Phase.GOAL_REPLAY, is_replay=True)
        return replace(stop_clock(state, Phase.GOAL_REPLAY, now), is_replay=True)
    if event in ('GoalReplayEnd','CountdownBegin'):
        if state.phase == Phase.PAUSED:
            return replace(state, resume_phase=Phase.COUNTDOWN, is_replay=False)
        return replace(stop_clock(state, Phase.COUNTDOWN, now), is_replay=False)
    if event == 'MatchPaused':
        if state.phase == Phase.PAUSED:
            return state
        return replace(stop_clock(state, Phase.PAUSED, now), resume_phase=state.phase)
    if event in ('RoundStarted','MatchUnpaused'):
        running_phase = Phase.OVERTIME if state.is_overtime else Phase.PLAYING
        if event == 'MatchUnpaused' and state.phase != Phase.PAUSED:
            return state
        phase = (state.resume_phase or running_phase) if event == 'MatchUnpaused' else running_phase
        if event == 'RoundStarted' and state.phase == Phase.PAUSED:
            return replace(state, resume_phase=running_phase, is_replay=False,
                           last_round_started_at=now, last_round_time_remaining=state.time_remaining)
        state = replace(state, phase=phase, resume_phase=None,
                        is_replay=phase == Phase.GOAL_REPLAY,
                        last_round_started_at=now if event == 'RoundStarted' else state.last_round_started_at,
                        last_round_time_remaining=state.time_remaining if event == 'RoundStarted' else state.last_round_time_remaining)
        return sync_clock(state, now, force=True, round_started=event == 'RoundStarted')
    if event == 'PlayerLeft':
        left_id = string(data.get('PrimaryId')).casefold()
        left_name = string(data.get('PlayerName')).casefold()
        if (left_id and left_id == state.local_primary_id.casefold()) or (left_name and left_name == state.local_player_name.casefold()):
            return clear_identity(state)
    if event == 'PlayerJoined':
        log.debug('PlayerJoined name=%r id=%r; team comes from UpdateState', data.get('PlayerName'), data.get('PrimaryId'))
    return state
