"""Bounded async pypresence IPC and one coalescing activity publisher."""
from __future__ import annotations

import asyncio
import copy
import json
import logging
import struct
import time

from pypresence import AioPresence
from pypresence.exceptions import DiscordError, DiscordNotFound, PipeClosed, ServerError
from pypresence.payloads import Payload
from pypresence.utils import get_ipc_path

log = logging.getLogger(__name__)
UNSET = object()


class DiscordClient(AioPresence):
    """Keep AioPresence activity building, but own framing and pipe lifetime.

    pypresence 4.6.2 uses read(), a character length for UTF-8 frames and a
    close() that closes its event loop. IPC can split frames and player/map
    text can contain Unicode. These boundary overrides make those cases safe.
    """
    def __init__(self, client_id: str):
        super().__init__(client_id, loop=asyncio.get_running_loop(),
                         connection_timeout=5, response_timeout=5)

    def send_data(self, op: int, payload: dict | Payload):
        data = payload.data if isinstance(payload, Payload) else payload
        wire = json.dumps(data, ensure_ascii=False).encode('utf-8')
        if self.sock_writer is None:
            raise PipeClosed()
        self.sock_writer.write(struct.pack('<II', op, len(wire)) + wire)

    async def read_output(self):
        if self.sock_reader is None:
            raise PipeClosed()
        try:
            header = await self.sock_reader.readexactly(8)
            op, length = struct.unpack('<II', header)
            if op == 2 or length > 1024*1024:
                raise PipeClosed()
            data = json.loads(await self.sock_reader.readexactly(length))
        except (asyncio.IncompleteReadError, ValueError, UnicodeError, struct.error) as exc:
            raise PipeClosed() from exc
        if not isinstance(data, dict):
            raise PipeClosed()
        if data.get('evt') == 'ERROR':
            details = data.get('data')
            raise ServerError(str(details.get('message', 'Discord RPC error') if isinstance(details,dict) else details))
        return data

    async def handshake(self):
        # Named-pipe discovery probes synchronously; do it outside the event loop.
        path = await asyncio.to_thread(get_ipc_path, self.pipe)
        if not path:
            raise DiscordNotFound()
        await self.create_reader_writer(path)
        self.send_data(0, {'v':1, 'client_id':self.client_id})
        data = await self.read_output()
        if 'code' in data:
            raise DiscordError(data['code'], data.get('message','Discord handshake failed'))

    async def close(self):
        # sock_writer is a transport on Windows and StreamWriter on Unix.
        writer, self.sock_writer = self.sock_writer, None
        self.sock_reader = None
        if writer is not None:
            writer.close()
            if hasattr(writer, 'wait_closed'):
                try:
                    await asyncio.wait_for(writer.wait_closed(), 2)
                except (OSError, TimeoutError):
                    pass

    def is_connected(self) -> bool:
        reader = self.sock_reader
        if reader is None or self.sock_writer is None or self.sock_writer.is_closing():
            return False
        # at_eof() waits for the buffer to be drained. A server CLOSE frame or
        # unsolicited event can remain buffered while the pipe has already
        # ended. CPython 3.11+ StreamReader stores that transport EOF in _eof;
        # check it independently of unread data, covered by a protocol test.
        if getattr(reader, '_eof', reader.at_eof()) or reader.exception() is not None:
            return False
        buffer = getattr(reader, '_buffer', b'')
        # A CLOSE control frame can also precede the transport EOF notification.
        return not (len(buffer) >= 8 and struct.unpack_from('<I', buffer)[0] == 2)


class PresencePublisher:
    """Latest payload wins. No activity write (including clear) beats 15 s.

    Failed writes also consume a window because Discord may have received
    them before its response pipe closed. Reconnection never resets this.
    Priority bypasses a longer configured interval, never the hard floor.
    """
    def __init__(self, factory, interval: float = 15, clock=time.monotonic):
        self.factory = factory
        self.interval = max(15.0, interval)
        self.clock = clock
        self.desired = None
        self.sent = UNSET
        self.last_attempt = float('-inf')
        self.retry_at = float('-inf')
        self.retry_delay = 3.0
        self.priority = False
        self.revision = 0
        self.client = None
        self.error = ''
        self.lock = asyncio.Lock()

    def offer(self, payload: dict | None, priority: bool = False):
        if payload != self.desired or priority:
            self.revision += 1
        self.desired = copy.deepcopy(payload)
        self.priority = self.priority or priority

    async def _disconnect(self):
        client, self.client = self.client, None
        self.sent = UNSET
        if client is not None:
            try:
                await asyncio.wait_for(client.close(), 3)
            except Exception:
                log.debug('Discord pipe cleanup failed', exc_info=True)

    async def pump(self) -> bool:
        async with self.lock:
            now = self.clock()
            if self.client is not None and hasattr(self.client, 'is_connected') and not self.client.is_connected():
                log.info('Discord IPC closed; reconnecting to resend current presence')
                await self._disconnect()
            floor = 15.0 if self.priority or self.desired is None else self.interval
            if now < self.retry_at or now-self.last_attempt < floor:
                return False
            if self.client is not None and self.desired == self.sent:
                self.priority = False
                return False
            # No game -> don't connect a new IPC session solely to clear it.
            if self.client is None and self.desired is None:
                return False
            try:
                if self.client is None:
                    self.client = self.factory()
                    await asyncio.wait_for(self.client.connect(), 6)
                    self.sent = UNSET
                    log.info('Discord RPC connected')
                # offer() may have changed while connect awaited; send latest.
                payload = copy.deepcopy(self.desired)
                revision = self.revision
                self.last_attempt = self.clock()
                if payload is None:
                    await asyncio.wait_for(self.client.clear(), 6)
                else:
                    await asyncio.wait_for(self.client.update(**payload), 6)
                self.sent = payload
                self.error = ''
                self.retry_delay = 3
                if self.revision == revision:
                    self.priority = False
                return True
            except asyncio.CancelledError:
                await self._disconnect()
                raise
            except Exception as exc:
                self.error = f'{type(exc).__name__}: {exc}'
                log.warning('Discord RPC unavailable: %s. Retrying in %.0fs.', exc, self.retry_delay)
                await self._disconnect()
                self.retry_at = self.clock() + self.retry_delay
                self.retry_delay = min(30.0, self.retry_delay*1.5)
                return False

    async def shutdown(self):
        async with self.lock:
            # Clear explicitly if eligible; otherwise closing the owning IPC
            # session removes its activity without another SET_ACTIVITY write.
            if self.client is not None and self.clock()-self.last_attempt >= 15:
                try:
                    self.last_attempt = self.clock()
                    await asyncio.wait_for(self.client.clear(), 3)
                except Exception:
                    log.debug('Discord shutdown clear failed', exc_info=True)
            await self._disconnect()
