import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.clock import utcnow
from app.errors import ApiError
from app.ids import new_id
from app.models import Delivery, DeliveryStatus, Endpoint, Event, EventType, Subscription


@dataclass
class Published:
    event: Event
    deduplicated: bool
    delivery_ids: list[str]


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def request_hash(event_type: str, payload: dict[str, Any]) -> str:
    """Same request ⇔ same hash, whatever the key order or whitespace of the JSON."""
    return hashlib.sha256(_canonical({"type": event_type, "payload": payload}).encode()).hexdigest()


async def publish_event(
    session: AsyncSession,
    event_type: str,
    payload: dict[str, Any],
    idempotency_key: str | None = None,
) -> Published:
    """Accept an event and fan it out, atomically.

    This is what Benji's other services would call; POST /api/events wraps it. The event
    and its deliveries are written in one transaction (transactional outbox): nothing is
    sent from here, the worker picks the rows up.
    """
    if await session.get(EventType, event_type) is None:
        raise ApiError(422, "unknown_event_type", f"Unknown event type: {event_type}")

    digest = request_hash(event_type, payload)
    now = utcnow()
    event_id = new_id("evt")
    envelope = {
        "id": event_id,
        "type": event_type,
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "data": payload,
    }
    event = Event(
        id=event_id,
        event_type=event_type,
        payload=payload,
        body=_canonical(envelope),
        idempotency_key=idempotency_key,
        request_hash=digest,
        created_at=now,
    )
    session.add(event)
    try:
        # Let the UNIQUE constraint decide, never check-then-insert: two concurrent
        # submits with the same key can't both get through.
        await session.flush()
    except IntegrityError:
        await session.rollback()
        return await _deduplicate(session, idempotency_key, digest)

    delivery_ids = await fan_out(session, event)
    await session.commit()
    return Published(event=event, deduplicated=False, delivery_ids=delivery_ids)


async def _deduplicate(session: AsyncSession, key: str | None, digest: str) -> Published:
    existing = await session.scalar(select(Event).where(Event.idempotency_key == key))
    if existing is None:  # the conflict wasn't on the key; shouldn't happen
        raise ApiError(500, "internal_error", "Could not store the event")
    if existing.request_hash != digest:
        raise ApiError(
            422,
            "idempotency_key_reused",
            f"Idempotency-Key {key!r} was already used for a different request",
        )
    delivery_ids = (
        await session.scalars(select(Delivery.id).where(Delivery.event_id == existing.id))
    ).all()
    return Published(event=existing, deduplicated=True, delivery_ids=list(delivery_ids))


async def fan_out(session: AsyncSession, event: Event) -> list[str]:
    """Create one pending delivery per enabled endpoint subscribed to the event's type.

    Safe to run twice: UNIQUE(event_id, endpoint_id) + ON CONFLICT DO NOTHING. Returns the
    ids of the deliveries created by this call.
    """
    endpoint_ids = (
        await session.scalars(
            select(Endpoint.id)
            .join(Subscription)
            .where(Subscription.event_type == event.event_type, Endpoint.enabled.is_(True))
        )
    ).all()
    if not endpoint_ids:
        return []
    now = utcnow()
    rows = [
        {
            "id": new_id("dlv"),
            "event_id": event.id,
            "endpoint_id": endpoint_id,
            "status": DeliveryStatus.pending,
            "attempt_count": 0,
            "series_attempts": 0,
            "replay_count": 0,
            "next_attempt_at": now,
            "version": 1,
            "created_at": now,
            "updated_at": now,
        }
        for endpoint_id in endpoint_ids
    ]
    stmt = (
        insert(Delivery)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["event_id", "endpoint_id"])
        .returning(Delivery.id)
    )
    return list((await session.scalars(stmt)).all())


async def list_events(session: AsyncSession, limit: int = 100) -> Sequence[Event]:
    stmt = select(Event).order_by(Event.created_at.desc(), Event.id.desc()).limit(limit)
    return (await session.scalars(stmt)).all()
