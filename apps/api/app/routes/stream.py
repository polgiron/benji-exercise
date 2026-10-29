import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.bus import Bus, format_sse

router = APIRouter(tags=["stream"])

HEARTBEAT_SECONDS = 15.0


async def event_stream(
    bus: Bus,
    is_disconnected: Callable[[], Awaitable[bool]],
    heartbeat: float = HEARTBEAT_SECONDS,
) -> AsyncIterator[str]:
    async with bus.subscribe() as queue:
        # Reconnect delay hint, then `ready`: the client refetches over REST from here,
        # which covers anything it missed while disconnected.
        yield "retry: 3000\n\n"
        yield format_sse("ready", {})
        while not await is_disconnected():
            try:
                message = await asyncio.wait_for(queue.get(), heartbeat)
            except TimeoutError:
                yield ": ping\n\n"  # keeps proxies from closing an idle connection
                continue
            if message is None:
                return
            yield format_sse(*message)


@router.get("/api/stream", response_class=StreamingResponse)
async def stream(request: Request) -> StreamingResponse:
    """Server-sent events: `delivery.updated` with a DeliverySummary after every change."""
    return StreamingResponse(
        event_stream(request.app.state.bus, request.is_disconnected),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
