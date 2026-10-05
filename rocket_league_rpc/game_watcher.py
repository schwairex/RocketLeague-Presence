"""psutil process discovery (no process memory access)."""
import asyncio
import logging
import psutil
from pathlib import Path

log = logging.getLogger(__name__)


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
