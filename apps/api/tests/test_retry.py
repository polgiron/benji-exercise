"""Reliable delivery: failures are retried with backoff until success or max attempts."""

import asyncio
from datetime import timedelta

import httpx

from app.models import DeliveryStatus
from app.retry import next_delay
from tests.helpers import attempts, only_delivery


async def setup(make_endpoint, fire):
    await make_endpoint()
    await fire()


async def test_fails_twice_then_succeeds(db, make_endpoint, fire, worker, receiver, clock):
    receiver.respond(500, 503, 200)
    await setup(make_endpoint, fire)

    await worker.run_once()
    d = await only_delivery(db)
    assert d.status == DeliveryStatus.pending
    assert d.last_error == "HTTP 500"
    first_delay = d.next_attempt_at - clock.now
    assert first_delay == timedelta(seconds=2)  # base, rand pinned to 1.0

    assert await worker.run_once() == 0  # not due yet: no early retry
    clock.advance(first_delay.total_seconds())
    await worker.run_once()
    d = await only_delivery(db)
    assert d.next_attempt_at - clock.now == timedelta(seconds=4)  # backoff doubles

    clock.advance(4)
    await worker.run_once()
    d = await only_delivery(db)
    assert d.status == DeliveryStatus.succeeded
    assert d.attempt_count == 3
    assert d.last_error is None
    assert [a.response_status for a in await attempts(db, d.id)] == [500, 503, 200]
    assert len(receiver.requests) == 3


async def test_always_failing_ends_failed_after_max_attempts(
    db, make_endpoint, fire, receiver, drain, settings
):
    receiver.respond(500)
    await setup(make_endpoint, fire)
    await drain()

    d = await only_delivery(db)
    assert d.status == DeliveryStatus.failed
    assert d.attempt_count == settings.max_attempts == 5
    assert d.next_attempt_at is None
    assert len(receiver.requests) == 5


async def test_timeouts_and_connection_errors_are_retried(db, make_endpoint, fire, receiver, drain):
    receiver.respond(httpx.ReadTimeout("slow"), httpx.ConnectError("refused"), 200)
    await setup(make_endpoint, fire)
    await drain()

    d = await only_delivery(db)
    assert d.status == DeliveryStatus.succeeded
    errors = [a.error for a in await attempts(db, d.id)]
    assert errors[0] == "timeout"
    assert errors[1].startswith("connection_error")
    assert errors[2] is None


async def test_4xx_is_terminal(db, make_endpoint, fire, receiver, drain):
    receiver.respond(400)
    await setup(make_endpoint, fire)
    await drain()

    d = await only_delivery(db)
    assert d.status == DeliveryStatus.failed
    assert d.attempt_count == 1
    assert d.last_error == "HTTP 400"


async def test_429_is_retried_and_retry_after_honoured(
    db, make_endpoint, fire, worker, receiver, clock
):
    receiver.respond(httpx.Response(429, headers={"Retry-After": "120"}), 200)
    await setup(make_endpoint, fire)
    await worker.run_once()

    d = await only_delivery(db)
    assert d.status == DeliveryStatus.pending
    assert d.next_attempt_at - clock.now == timedelta(seconds=120)


async def test_expired_lease_is_reclaimed(db, make_endpoint, fire, worker, clock, settings):
    await setup(make_endpoint, fire)
    # A worker claimed it, then crashed before recording anything.
    assert len(await worker.claim_due()) == 1
    assert await worker.claim_due() == []  # leased: nobody else can take it

    clock.advance(settings.lease_seconds + 1)
    await worker.run_once()
    assert (await only_delivery(db)).status == DeliveryStatus.succeeded


async def test_concurrent_cycles_send_once(db, make_endpoint, fire, worker, receiver):
    await setup(make_endpoint, fire)
    await asyncio.gather(*(worker.run_once() for _ in range(5)))
    assert len(receiver.requests) == 1
    assert (await only_delivery(db)).attempt_count == 1


async def test_disabled_endpoint_fails_pending_delivery(client, db, make_endpoint, fire, worker):
    ep = await make_endpoint()
    await fire()
    await client.patch(f"/api/endpoints/{ep['id']}", json={"enabled": False})
    await worker.run_once()

    d = await only_delivery(db)
    assert d.status == DeliveryStatus.failed
    assert d.last_error == "endpoint_disabled"


def test_backoff_is_capped_and_jittered():
    assert next_delay(10, base=2, cap=30, rand=lambda: 1.0) == 30
    assert next_delay(1, base=2, cap=30, rand=lambda: 0.0) == 1  # jitter floor is half
    assert next_delay(1, base=2, cap=30, retry_after=60, rand=lambda: 1.0) == 60
