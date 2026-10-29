import asyncio
import signal
import threading
from collections.abc import Callable
from types import FrameType

EXIT_SIGNALS = (signal.SIGINT, signal.SIGTERM)


def on_exit_signal(callback: Callable[[], None]) -> Callable[[], None]:
    """Run `callback` on the event loop as soon as the server is told to stop; returns `restore`.

    uvicorn's graceful shutdown waits for every open connection before it runs the lifespan
    shutdown, and an SSE stream never ends on its own: without this, a stop (or a --reload)
    hangs for as long as a dashboard is open. The previous handler (uvicorn's) still runs:
    uvicorn installs its own with signal.signal precisely so it can be chained and restored.
    """
    if threading.current_thread() is not threading.main_thread():
        return lambda: None  # signals only reach the main thread (TestClient runs apps elsewhere)
    loop = asyncio.get_running_loop()
    previous = {sig: signal.getsignal(sig) for sig in EXIT_SIGNALS}

    def handle(sig: int, frame: FrameType | None) -> None:
        loop.call_soon_threadsafe(callback)  # not from inside a signal handler
        handler = previous[sig]
        if callable(handler):
            handler(sig, frame)

    for sig in EXIT_SIGNALS:
        signal.signal(sig, handle)

    def restore() -> None:
        for sig, handler in previous.items():
            signal.signal(sig, handler)

    return restore
