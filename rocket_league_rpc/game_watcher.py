"""psutil process discovery (no process memory access)."""
import asyncio
import logging
import psutil
import re
from pathlib import Path

log = logging.getLogger(__name__)

_FORBIDDEN_ARGUMENT = re.compile(r'AUTH|PASSWORD|TOKEN|EXCHANGE|SECRET|CREDENTIAL', re.I)


def sanitize_launch_args(arguments):
    """Discard opaque/secret values at the process boundary; retain two identity fields only."""
    result = {'argument_names': [], 'epicusername': '', 'epicuserid': ''}
    if not isinstance(arguments, (list, tuple)):
        return result
    index = 1  # argv[0] is the executable, never an identity source
    while index < len(arguments):
        argument = arguments[index]
        index += 1
        if not isinstance(argument, str) or not argument.startswith('-'):
            continue
        # Inspect only the key first; never bind a forbidden argument's value.
        public_argument = argument.lstrip('-')
        equals = public_argument.find('=')
        separator = equals >= 0
        key = public_argument[:equals] if separator else public_argument
        if _FORBIDDEN_ARGUMENT.search(key):
            if not separator and index < len(arguments):
                following = arguments[index]
                # A following identity flag has no credential value to consume.
                if not isinstance(following, str) or not re.match(r'^-+epic(?:username|userid)(?:=|$)', following, re.I):
                    index += 1
            continue
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}', key):
            continue
        key = key.casefold()
        if key not in result['argument_names']:
            result['argument_names'].append(key)
        if key not in ('epicusername', 'epicuserid'):
            continue  # unknown argument values are never retained
        value = public_argument[equals+1:] if separator else ''
        if not separator and index < len(arguments):
            following = arguments[index]
            if isinstance(following, str) and not following.startswith('-'):
                value = following
                index += 1
        if isinstance(value, str) and len(value) <= 256 and not _FORBIDDEN_ARGUMENT.search(value):
            result[key] = value.strip().strip('"')
    return result


def sanitized_game_cmdline(process_iter=None):
    """Read only RocketLeague.exe; no raw cmdline escapes this function."""
    result = {'running': False, 'readable': False, 'error': '', **sanitize_launch_args([])}
    try:
        for process in (process_iter or psutil.process_iter)(['name']):
            try:
                if str(process.info.get('name', '')).casefold() != 'rocketleague.exe':
                    continue
                result['running'] = True
                result.update(sanitize_launch_args(process.cmdline()))
                result['readable'] = True
                return result
            except (psutil.Error, OSError) as exc:
                if result['running']:
                    result['error'] = type(exc).__name__
    except (psutil.Error, OSError) as exc:
        result['error'] = type(exc).__name__
    return result


def install_from_executable(executable):
    try:
        path=Path(executable)
        if path.name.casefold() != 'rocketleague.exe':return None
        for root in path.parents:
            if (root/'TAGame').is_dir():return root.resolve()
    except (OSError,TypeError,ValueError):pass
    return None


def running_game_info():
    try:
        for process in psutil.process_iter(['name','exe','create_time']):
            try:
                if str(process.info.get('name','')).casefold()=='rocketleague.exe':
                    root=install_from_executable(process.info.get('exe'))
                    if root:return root,process.info.get('create_time')
            except psutil.Error:continue
    except (psutil.Error,OSError):
        log.debug('Cannot read running game executable path',exc_info=True)
    return None,None


def running_install():
    return running_game_info()[0]


def rocket_league_running() -> bool:
    try:
        for process in psutil.process_iter(['name']):
            try:
                name = process.info.get('name')
                if isinstance(name, str) and name.casefold() == 'rocketleague.exe':
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except (psutil.Error, OSError):
        log.debug('Process scan unavailable', exc_info=True)
        raise  # supervisor retries without inventing a "game stopped" transition
    return False


async def watch_game(on_change, stop: asyncio.Event, detector=rocket_league_running):
    from .runtime import wait_or_stop
    previous = None
    while not stop.is_set():
        running = await asyncio.to_thread(detector)
        if running != previous:
            await on_change(running)
            previous = running
        await wait_or_stop(stop, 1)
