"""Read-only TCP/WebSocket transport and bounded incremental JSON framing."""
from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable

from .config import Config

log = logging.getLogger(__name__)
raw_log = logging.getLogger('raw_packets')


class JsonStreamParser:
    """Linear byte scan; UTF-8 decoding happens only for complete objects.

    A malformed balanced object is dropped. An unbalanced/unterminated object
    cannot be reliably reframed without a delimiter; reset at max_buffer.
    """
    def __init__(self, max_buffer: int = 2*1024*1024):
        self.max_buffer = max_buffer
        self.reset()

    def reset(self):
        self.buffer = bytearray()
        self.depth = 0
        self.in_string = False
        self.escaped = False

    def feed(self, data: bytes) -> list[dict]:
        result = []
        for byte in data:
            if not self.depth:
                if byte != 123:
                    continue
                self.depth = 1
                self.buffer.append(byte)
                continue
            self.buffer.append(byte)
            if len(self.buffer) > self.max_buffer:
                log.debug('Stats object exceeded buffer limit; dropping incomplete frame')
                self.reset()
                continue
            if self.in_string:
                if self.escaped:
                    self.escaped = False
                elif byte == 92:
                    self.escaped = True
                elif byte == 34:
                    self.in_string = False
            elif byte == 34:
                self.in_string = True
            elif byte == 123:
                self.depth += 1
            elif byte == 125:
                self.depth -= 1
                if not self.depth:
                    try:
                        value = json.loads(self.buffer.decode('utf-8'))
                        if isinstance(value, dict):
                            result.append(value)
                    except (ValueError, UnicodeError, RecursionError):
                        log.debug('Discarding malformed Stats JSON object')
                    self.reset()
        return result


class StatsClient:
    def __init__(self, config: Config, on_event: Callable[[dict], Awaitable[None]],
                 on_connection: Callable[[bool], Awaitable[None]] | None = None,
                 raw_packets: bool = False):
        self.config = config
        self.on_event = on_event
        self.on_connection = on_connection
        self.raw_packets = raw_packets

    async def _connection(self, connected: bool):
        if self.on_connection is not None:
            await self.on_connection(connected)

    async def _consume(self, parser: JsonStreamParser, chunk: bytes):
        for message in parser.feed(chunk):
            log.debug('Raw Stats event: %r', message.get('Event'))
            if self.raw_packets:
                raw_log.debug('%s', json.dumps(message, ensure_ascii=False))
            try:
                await self.on_event(message)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception('Stats event handler failed; continuing with the next packet')

    async def session(self):
        """One connection; outer runtime owns process gating and capped retry."""
        parser = JsonStreamParser()
        try:
            if self.config.stats_transport == 'websocket':
                from websockets.asyncio.client import connect
                async with connect(f'ws://{self.config.stats_host}:{self.config.stats_web_port}',
                                   open_timeout=5, max_size=2*1024*1024) as websocket:
                    await self._connection(True)
                    async for frame in websocket:
                        await self._consume(parser, frame.encode('utf-8') if isinstance(frame, str) else frame)
            else:
                reader, writer = await asyncio.wait_for(asyncio.open_connection(
                    self.config.stats_host, self.config.stats_port), timeout=5)
                try:
                    await self._connection(True)
                    while chunk := await reader.read(65536):
                        await self._consume(parser, chunk)
                finally:
                    writer.close()
                    try:
                        await asyncio.wait_for(writer.wait_closed(), timeout=2)
                    except (OSError, TimeoutError):
                        pass
        finally:
            await self._connection(False)
