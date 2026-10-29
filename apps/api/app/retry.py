"""Retry policy: which outcomes are retried, and how long to wait. Pure functions."""

import random
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

import httpx

MAX_RETRY_AFTER_SECONDS = 3600


class Outcome(StrEnum):
    success = "success"
    retry = "retry"  # transient: try again later
    terminal = "terminal"  # the receiver rejected it; retrying won't help (Replay can)


@dataclass(frozen=True)
class Result:
    outcome: Outcome
    status_code: int | None = None
    error: str | None = None
    retry_after: float | None = None


RETRYABLE_STATUSES = {408, 425, 429}


def classify_response(response: httpx.Response) -> Result:
    status = response.status_code
    if 200 <= status < 300:
        return Result(Outcome.success, status)
    error = f"HTTP {status}"
    if status in RETRYABLE_STATUSES or status >= 500:
        return Result(Outcome.retry, status, error, parse_retry_after(response))
    return Result(Outcome.terminal, status, error)


def classify_exception(exc: Exception) -> Result:
    if isinstance(exc, httpx.TimeoutException):
        return Result(Outcome.retry, error="timeout")
    if isinstance(exc, httpx.TransportError):
        return Result(Outcome.retry, error=f"connection_error: {exc}".rstrip(": "))
    return Result(Outcome.retry, error=f"error: {type(exc).__name__}")


def parse_retry_after(response: httpx.Response) -> float | None:
    """Seconds form only; the HTTP-date form is rare for webhooks and treated as absent."""
    value = response.headers.get("retry-after", "").strip()
    if not value.isdigit():
        return None
    return min(float(value), MAX_RETRY_AFTER_SECONDS)


def next_delay(
    attempt: int,
    base: float,
    cap: float,
    retry_after: float | None = None,
    rand: Callable[[], float] | None = None,
) -> float:
    """Exponential backoff with jitter: base * 2^(attempt-1), capped, then scaled by a
    random factor in [0.5, 1] so receivers that failed together don't get retried in sync.
    A Retry-After from the receiver is a floor."""
    rand = rand or random.random
    ceiling = min(cap, base * 2 ** (attempt - 1))
    delay = ceiling * (0.5 + 0.5 * rand())
    return max(delay, retry_after or 0.0)
