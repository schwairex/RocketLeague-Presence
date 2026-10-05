"""psutil process discovery (no process memory access)."""
import asyncio
import logging
import psutil

log = logging.getLogger(__name__)


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
