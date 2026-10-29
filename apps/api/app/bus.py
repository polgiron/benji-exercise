"""In-process pub/sub feeding the SSE stream. No backlog: a client that was disconnected
refetches over REST on reconnect (the `ready` event tells it when)."""

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

log = logging.getLogger(__name__)

Message = tuple[str, dict[str, Any]]


class Bus:
    def __init__(self, queue_size: int = 1000) -> None:
        self._subscribers: set[asyncio.Queue[Message | None]] = set()
        self._queue_size = queue_size
        self._closed = False

    @asynccontextmanager
    async def subscribe(self) -> AsyncIterator[asyncio.Queue[Message | None]]:
        queue: asyncio.Queue[Message | None] = asyncio.Queue(self._queue_size)
        if self._closed:
            queue.put_nowait(None)
        self._subscribers.add(queue)
        try:
            yield queue
        finally:
            self._subscribers.discard(queue)

    def publish(self, event: str, data: dict[str, Any]) -> None:
        for queue in list(self._subscribers):
            try:
                queue.put_nowait((event, data))
            except asyncio.QueueFull:
                # Too slow to keep up: end its stream (None), it reconnects and refetches.
                log.warning("dropping a slow SSE subscriber")
                self._end(queue)

    def _end(self, queue: asyncio.Queue[Message | None]) -> None:
        self._subscribers.discard(queue)
        if queue.full():
            queue.get_nowait()
        queue.put_nowait(None)

    def close(self) -> None:
        """End every stream (None), now and for anyone subscribing after: the server is stopping."""
        self._closed = True
        for queue in list(self._subscribers):
            self._end(queue)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


def format_sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"
