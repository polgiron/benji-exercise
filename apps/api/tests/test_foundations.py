from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.ids import new_id
from app.models import Delivery, DeliveryStatus, Endpoint, Event, EventType, Subscription


async def test_event_types_are_seeded(db):
    async with db.sessions() as s:
        keys = (await s.scalars(select(EventType.key))).all()
    assert set(keys) == {
        "reward_transaction_created",
        "campaign_updated",
        "member_account_linked",
    }


async def test_seed_is_idempotent(db):
    await db.create_all()
    async with db.sessions() as s:
        assert len((await s.scalars(select(EventType))).all()) == 3


def _now():
    return datetime.now(UTC)


async def _endpoint_and_event(s):
    now = _now()
    ep = Endpoint(id=new_id("ep"), url="http://x", secret="whsec_x", created_at=now, updated_at=now)
    ev = Event(
        id=new_id("evt"),
        event_type="campaign_updated",
        payload={},
        body="{}",
        request_hash="h",
        created_at=now,
    )
    s.add_all([ep, ev])
    await s.flush()
    return ep, ev


async def test_one_delivery_per_event_and_endpoint(db):
    async with db.sessions() as s:
        ep, ev = await _endpoint_and_event(s)
        for _ in range(2):
            s.add(
                Delivery(
                    id=new_id("dlv"),
                    event_id=ev.id,
                    endpoint_id=ep.id,
                    status=DeliveryStatus.pending,
                    created_at=_now(),
                    updated_at=_now(),
                )
            )
        with pytest.raises(IntegrityError):
            await s.flush()


async def test_subscription_requires_a_known_event_type(db):
    async with db.sessions() as s:
        ep, _ = await _endpoint_and_event(s)
        s.add(Subscription(endpoint_id=ep.id, event_type="nope"))
        with pytest.raises(IntegrityError):
            await s.flush()


async def test_datetimes_round_trip_as_utc(db):
    async with db.sessions() as s:
        ep, _ = await _endpoint_and_event(s)
        await s.commit()
    async with db.sessions() as s:
        loaded = await s.get(Endpoint, ep.id)
        assert loaded.created_at.tzinfo is UTC


async def test_unknown_route_uses_the_error_shape(client):
    r = await client.get("/api/nope")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"
