import asyncio
import signal

from app.shutdown import on_exit_signal


async def test_exit_signal_runs_the_callback_and_the_previous_handler():
    calls: list[str] = []

    def previous(sig, frame):
        calls.append("previous")

    original = signal.signal(signal.SIGTERM, previous)
    try:
        restore = on_exit_signal(lambda: calls.append("callback"))
        signal.raise_signal(signal.SIGTERM)
        await asyncio.sleep(0)  # the callback is scheduled on the loop, not run in the handler
        assert calls == ["previous", "callback"]

        restore()
        assert signal.getsignal(signal.SIGTERM) is previous
    finally:
        signal.signal(signal.SIGTERM, original)
