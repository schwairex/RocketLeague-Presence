"""Task recovery, portable single-instance lifetime and structured logs."""
from __future__ import annotations

import asyncio
import ctypes
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

log = logging.getLogger(__name__)


async def wait_or_stop(stop: asyncio.Event, seconds: float):
    try:
        await asyncio.wait_for(stop.wait(), seconds)
    except TimeoutError:
        pass


async def supervise(name, factory, stop: asyncio.Event, retry_delay: float = 3):
    delay = retry_delay
    while not stop.is_set():
        try:
            await factory()
            if not stop.is_set():
                log.warning('Task %s returned unexpectedly; restarting.', name)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception('Task %s failed; restarting in %.1fs.', name, delay)
        if not stop.is_set():
            await wait_or_stop(stop, delay)
            delay = min(30, delay*1.5)


class AlreadyRunning(RuntimeError):
    pass


class SingleInstance:
    def __init__(self, lock_path: Path, mutex_name: str = 'Local\\rocket-league-rpc-7b543a5e'):
        self.path = lock_path
        self.mutex_name = mutex_name
        self.handle = None
        self.file = None

    def __enter__(self):
        if sys.platform == 'win32':
            from ctypes import wintypes
            self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            self.kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
            self.kernel.CreateMutexW.restype = wintypes.HANDLE
            self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            self.kernel.CloseHandle.restype = wintypes.BOOL
            self.handle = self.kernel.CreateMutexW(None, False, self.mutex_name)
            if not self.handle:
                raise ctypes.WinError(ctypes.get_last_error())
            if ctypes.get_last_error() == 183:
                self.kernel.CloseHandle(self.handle)
                self.handle = None
                raise AlreadyRunning('rocket-league-rpc is already running in this Windows session.')
        else:
            import fcntl
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.file = self.path.open('a+b')
            try:
                fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                self.file.close()
                self.file = None
                raise AlreadyRunning('rocket-league-rpc is already running.') from exc
        return self

    def __exit__(self, *_):
        if self.handle is not None:
            self.kernel.CloseHandle(self.handle)
            self.handle = None
        if self.file is not None:
            self.file.close()
            self.file = None


class StructuredFormatter(logging.Formatter):
    def format(self, record):
        import json
        payload = {'time':self.formatTime(record, '%Y-%m-%dT%H:%M:%S'),
                   'level':record.levelname,'logger':record.name,'message':record.getMessage()}
        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(folder: Path, level: str = 'INFO', debug: bool = False, raw: bool = False):
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()
    root.setLevel(logging.DEBUG if debug else getattr(logging, level, logging.INFO))
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s %(levelname)-7s %(message)s', '%H:%M:%S'))
    root.addHandler(console)
    try:
        folder.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(folder/'app.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
        handler.setFormatter(StructuredFormatter())
        root.addHandler(handler)
    except OSError as exc:
        log.error('Cannot open rotating logs: %s. Console logging remains available.', exc)
    raw_logger = logging.getLogger('raw_packets')
    raw_logger.propagate = False
    raw_logger.setLevel(logging.DEBUG)
    for handler in raw_logger.handlers[:]:
        raw_logger.removeHandler(handler)
        handler.close()
    if raw:
        try:
            handler = RotatingFileHandler(folder/'raw_packets.log', maxBytes=10*1024*1024, backupCount=3, encoding='utf-8')
            handler.setFormatter(logging.Formatter('%(message)s'))
            raw_logger.addHandler(handler)
        except OSError as exc:
            log.error('Cannot open raw packet log: %s', exc)
