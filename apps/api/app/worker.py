"""Delivery worker: drains the deliveries table (the outbox).

One asyncio task in the API process. Each cycle it atomically claims due deliveries,
sends them concurrently, and records every attempt. State lives in SQLite, so a restart
loses nothing: pending rows are picked up again and expired leases are reclaimed.
"""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta

import httpx
from sqlalchemy import or_, select, update

from app.clock import Clock, utcnow
from app.config import Settings
from app.db import Database
from app.ids import new_id
from app.models import AttemptTrigger, Delivery, DeliveryAttempt, DeliveryStatus
from app.retry import Outcome, Result, classify_exception, classify_response, next_delay
from app.signing import signature_headers

log = logging.getLogger(__name__)

RESPONSE_BODY_LIMIT = 2048
USER_AGENT = "Benji-Webhooks/0.1"

OnChange = Callable[[list[str]], Awaitable[None]]


class DeliveryWorker:
    def __init__(
        self,
        db: Database,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
        clock: Clock = utcnow,
        rand: Callable[[], float] | None = None,
        on_change: OnChange | None = None,
    ) -> None:
        self.db = db
        self.settings = settings
        self.clock = clock
        self.rand = rand
        self.on_change = on_change
        self.client = httpx.AsyncClient(
            transport=transport,
            timeout=settings.http_timeout_seconds,
            follow_redirects=False,
        )
        self._wake = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._semaphore = asyncio.Semaphore(settings.worker_concurrency)

    # Lifecycle -----------------------------------------------------------------------

    def start(self) -> None:
        self._task = asyncio.create_task(self._run_forever(), name="delivery-worker")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.client.aclose()

    def wake(self) -> None:
        """Called after new work is committed so it's sent now, not at the next poll."""
        self._wake.set()

    async def _run_forever(self) -> None:
        while True:
            try:
                processed = await self.run_once()
            except Exception:
                log.exception("delivery worker cycle failed")
                processed = 0
            if processed == 0:
                try:
                    await asyncio.wait_for(self._wake.wait(), self.settings.worker_poll_seconds)
                except TimeoutError:
                    pass
                self._wake.clear()

    # One cycle -----------------------------------------------------------------------

    async def run_once(self) -> int:
        """Claim due deliveries, send them, record the results. Returns how many."""
        claimed = await self.claim_due()
        if not claimed:
            return 0
        await self._notify(claimed)
        await asyncio.gather(*(self._deliver_guarded(d) for d in claimed))
        await self._notify(claimed)
        return len(claimed)

    async def claim_due(self) -> list[str]:
        """pending → in_progress in a single UPDATE, so two workers can never claim the
        same delivery. An in_progress row whose lease expired (worker crashed mid-send)
        is claimable again."""
        now = self.clock()
        due = (
            select(Delivery.id)
            .where(
                or_(
                    (Delivery.status == DeliveryStatus.pending) & (Delivery.next_attempt_at <= now),
                    (Delivery.status == DeliveryStatus.in_progress)
                    & (Delivery.lease_expires_at < now),
                )
            )
            .order_by(Delivery.next_attempt_at)
            .limit(self.settings.worker_batch_size)
            .scalar_subquery()
        )
        stmt = (
            update(Delivery)
            .where(Delivery.id.in_(due))
            .values(
                status=DeliveryStatus.in_progress,
                lease_expires_at=now + timedelta(seconds=self.settings.lease_seconds),
                version=Delivery.version + 1,
                updated_at=now,
            )
            .returning(Delivery.id)
        )
        async with self.db.sessions() as session:
            ids = list((await session.scalars(stmt)).all())
            await session.commit()
        return ids

    async def _deliver_guarded(self, delivery_id: str) -> None:
        async with self._semaphore:
            try:
                await self.deliver(delivery_id)
            except Exception:
                # Leave it in_progress: the lease expires and it's retried.
                log.exception("delivery %s failed unexpectedly", delivery_id)

    async def deliver(self, delivery_id: str) -> None:
        # Read what we need, then close the session: no transaction stays open while we
        # wait on the receiver.
        async with self.db.sessions() as session:
            delivery = await session.get(Delivery, delivery_id)
            if delivery is None or delivery.status != DeliveryStatus.in_progress:
                return
            claimed_version = delivery.version
            endpoint, event = delivery.endpoint, delivery.event
            if not endpoint.enabled:
                self._finish(delivery, DeliveryStatus.failed, "endpoint_disabled")
                await session.commit()
                return

        started_at = self.clock()
        body = event.body.encode()
        headers = {
            "content-type": "application/json",
            "user-agent": USER_AGENT,
            **signature_headers(endpoint.secret, delivery_id, body, int(started_at.timestamp())),
        }
        start = time.perf_counter()
        response_body: str | None = None
        try:
            response = await self.client.post(endpoint.url, content=body, headers=headers)
            response_body = response.text[:RESPONSE_BODY_LIMIT]
            result = classify_response(response)
        except Exception as exc:  # any failure to get a response is retryable
            result = classify_exception(exc)
        duration_ms = round((time.perf_counter() - start) * 1000)

        await self._record(
            delivery_id, claimed_version, result, started_at, duration_ms, response_body
        )

    async def _record(
        self,
        delivery_id: str,
        claimed_version: int,
        result: Result,
        started_at: datetime,
        duration_ms: int,
        response_body: str | None,
    ) -> None:
        """Append the attempt and move the delivery to its next state, in one transaction."""
        async with self.db.sessions() as session:
            delivery = await session.get(Delivery, delivery_id)
            # Lost the lease meanwhile (the send outlived lease_seconds and another worker
            # reclaimed it)? Then that worker owns the row; don't overwrite its state.
            if delivery is None or delivery.version != claimed_version:
                log.warning("delivery %s: lease lost, discarding result", delivery_id)
                return

            delivery.attempt_count += 1
            delivery.series_attempts += 1
            session.add(
                DeliveryAttempt(
                    id=new_id("att"),
                    delivery_id=delivery.id,
                    number=delivery.attempt_count,
                    trigger=AttemptTrigger.replay if delivery.replay_count else AttemptTrigger.auto,
                    started_at=started_at,
                    duration_ms=duration_ms,
                    response_status=result.status_code,
                    response_body=response_body,
                    error=result.error,
                )
            )

            if result.outcome == Outcome.success:
                self._finish(delivery, DeliveryStatus.succeeded, None)
            elif (
                result.outcome == Outcome.retry
                and delivery.series_attempts < self.settings.max_attempts
            ):
                delay = next_delay(
                    delivery.series_attempts,
                    self.settings.retry_base_seconds,
                    self.settings.retry_cap_seconds,
                    result.retry_after,
                    self.rand,
                )
                delivery.status = DeliveryStatus.pending
                delivery.next_attempt_at = self.clock() + timedelta(seconds=delay)
                delivery.lease_expires_at = None
                delivery.last_error = result.error
                self._touch(delivery)
            else:
                self._finish(delivery, DeliveryStatus.failed, result.error)
            await session.commit()

    def _finish(self, delivery: Delivery, status: DeliveryStatus, error: str | None) -> None:
        delivery.status = status
        delivery.next_attempt_at = None
        delivery.lease_expires_at = None
        delivery.last_error = error
        self._touch(delivery)

    def _touch(self, delivery: Delivery) -> None:
        delivery.version += 1
        delivery.updated_at = self.clock()

    async def _notify(self, delivery_ids: list[str]) -> None:
        if self.on_change:
            await self.on_change(delivery_ids)
