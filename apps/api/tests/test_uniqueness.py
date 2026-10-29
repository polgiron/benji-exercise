"""Unique delivery: one event, one delivery per endpoint, however often it's submitted."""

import asyncio

from sqlalchemy import func, select

from app.models import Delivery, Event
from app.services.events import fan_out
from tests.conftest import sample


async def count(db, model):
    async with db.sessions() as s:
        return await s.scalar(select(func.count()).select_from(model))


async def test_same_key_twice_creates_one_event_and_no_new_deliveries(db, make_endpoint, fire):
    await make_endpoint()
    await make_endpoint()

    first = await fire(key="key-1")
    assert first.status_code == 201
    assert first.json()["deduplicated"] is False
    assert first.json()["delivery_count"] == 2

    second = await fire(key="key-1")
    assert second.status_code == 200
    assert second.json()["deduplicated"] is True
    assert second.json()["event"]["id"] == first.json()["event"]["id"]
    assert second.json()["delivery_count"] == 2

    assert await count(db, Event) == 1
    assert await count(db, Delivery) == 2


async def test_key_order_in_the_payload_does_not_matter(fire):
    payload = sample()
    await fire(payload=payload, key="key-1")
    r = await fire(payload=dict(reversed(payload.items())), key="key-1")
    assert r.json()["deduplicated"] is True


async def test_same_key_different_payload_is_rejected(db, fire):
    await fire(payload=sample(name="A"), key="key-1")
    r = await fire(payload=sample(name="B"), key="key-1")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "idempotency_key_reused"
    assert await count(db, Event) == 1


async def test_same_key_different_event_type_is_rejected(fire):
    await fire(event_type="campaign_updated", key="key-1")
    r = await fire(event_type="member_account_linked", key="key-1")
    assert r.status_code == 422


async def test_without_a_key_every_submit_is_a_new_event(db, fire):
    await fire()
    await fire()
    assert await count(db, Event) == 2


async def test_concurrent_submits_with_the_same_key(db, make_endpoint, fire):
    await make_endpoint()
    results = await asyncio.gather(*(fire(key="key-1") for _ in range(5)))
    assert sorted(r.status_code for r in results) == [200, 200, 200, 200, 201]
    assert await count(db, Event) == 1
    assert await count(db, Delivery) == 1


async def test_fan_out_twice_still_one_delivery_per_endpoint(db, make_endpoint, fire):
    await make_endpoint()
    await make_endpoint()
    event_id = (await fire()).json()["event"]["id"]

    async with db.sessions() as s:
        event = await s.get(Event, event_id)
        assert await fan_out(s, event) == []
        await s.commit()

    assert await count(db, Delivery) == 2
