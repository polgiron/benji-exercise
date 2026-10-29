from collections.abc import Callable
from datetime import UTC, datetime

Clock = Callable[[], datetime]


def _system_now() -> datetime:
    return datetime.now(UTC)


_source: Clock = _system_now


def utcnow() -> datetime:
    """The one place the app reads the time, so tests can drive it (`set_clock`)."""
    return _source()


def set_clock(source: Clock | None) -> None:
    global _source
    _source = source or _system_now
