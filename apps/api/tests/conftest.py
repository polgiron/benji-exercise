from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
from fastapi import FastAPI

from app.config import Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(database_url=f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")


@pytest.fixture
async def app(settings) -> AsyncIterator[FastAPI]:
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        yield app


@pytest.fixture
def db(app):
    return app.state.db


@pytest.fixture
async def client(app) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def make_endpoint(client):
    async def make(event_types=("campaign_updated",), url="https://example.com/hook", **extra):
        body = {"url": url, "event_types": list(event_types), **extra}
        r = await client.post("/api/endpoints", json=body)
        assert r.status_code == 201, r.text
        return r.json()

    return make


def sample(event_type: str = "campaign_updated", **overrides):
    from app.event_types import EVENT_TYPES

    [t] = [t for t in EVENT_TYPES if t["key"] == event_type]
    return {**t["sample_payload"], **overrides}


@pytest.fixture
def fire(client):
    async def fire(event_type="campaign_updated", payload=None, key=None):
        headers = {"Idempotency-Key": key} if key else {}
        body = {"event_type": event_type, "payload": payload or sample(event_type)}
        return await client.post("/api/events", json=body, headers=headers)

    return fire


class FakeClock:
    def __init__(self) -> None:
        from datetime import UTC, datetime

        self.now = datetime(2026, 1, 1, tzinfo=UTC)

    def __call__(self):
        return self.now

    def advance(self, seconds: float) -> None:
        from datetime import timedelta

        self.now += timedelta(seconds=seconds)


class Receiver:
    """Scripted stand-in for a customer's server, plugged in as the worker's transport.

    `script` items are status codes or exceptions, consumed one per request; the last one
    repeats. Every request is kept for assertions.
    """

    def __init__(self, *script) -> None:
        self.script = list(script) or [200]
        self.requests: list[httpx.Request] = []

    def respond(self, *script) -> None:
        self.script = list(script)

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        step = self.script.pop(0) if len(self.script) > 1 else self.script[0]
        if isinstance(step, Exception):
            raise step
        if isinstance(step, httpx.Response):
            return step
        return httpx.Response(step, text="ok" if step < 400 else "nope")


@pytest.fixture
def clock() -> Iterator[FakeClock]:
    from app.clock import set_clock

    fake = FakeClock()
    set_clock(fake)
    yield fake
    set_clock(None)


@pytest.fixture
def receiver() -> Receiver:
    return Receiver(200)


@pytest.fixture
async def worker(db, settings, clock, receiver):
    from app.worker import DeliveryWorker

    w = DeliveryWorker(
        db, settings, transport=httpx.MockTransport(receiver), clock=clock, rand=lambda: 1.0
    )
    yield w
    await w.stop()


@pytest.fixture
def drain(worker, clock):
    """Run the worker until nothing is due, jumping the clock past each backoff."""

    async def drain(max_cycles: int = 50) -> None:
        for _ in range(max_cycles):
            if await worker.run_once() == 0:
                clock.advance(3600)
                if await worker.run_once() == 0:
                    return
        raise AssertionError("worker did not settle")

    return drain
