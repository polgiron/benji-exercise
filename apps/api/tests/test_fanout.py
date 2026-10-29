import json

from sqlalchemy import select

from app.models import Delivery, DeliveryStatus, Event


async def deliveries(db):
    async with db.sessions() as s:
        return (await s.scalars(select(Delivery))).all()


async def test_only_enabled_subscribed_endpoints_get_a_delivery(client, db, make_endpoint, fire):
    subscribed = await make_endpoint(["campaign_updated", "member_account_linked"])
    await make_endpoint(["member_account_linked"])
    disabled = await make_endpoint(["campaign_updated"])
    await client.patch(f"/api/endpoints/{disabled['id']}", json={"enabled": False})

    r = await fire("campaign_updated")
    assert r.json()["delivery_count"] == 1

    [delivery] = await deliveries(db)
    assert delivery.endpoint_id == subscribed["id"]
    assert delivery.status == DeliveryStatus.pending
    assert delivery.next_attempt_at is not None


async def test_event_with_no_subscribers_is_still_recorded(client, fire):
    r = await fire()
    assert r.status_code == 201
    assert r.json()["delivery_count"] == 0
    assert len((await client.get("/api/events")).json()) == 1


async def test_unknown_event_type_is_rejected(fire):
    r = await fire("nope")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "unknown_event_type"


async def test_body_is_the_signed_envelope(db, fire):
    r = await fire(payload={"campaign_id": "cmp_7"})
    async with db.sessions() as s:
        event = await s.get(Event, r.json()["event"]["id"])
    envelope = json.loads(event.body)
    assert envelope["id"] == event.id
    assert envelope["type"] == "campaign_updated"
    assert envelope["data"] == {"campaign_id": "cmp_7"}
    assert envelope["created_at"].endswith("Z")


async def test_events_are_listed_newest_first(client, fire):
    first = (await fire()).json()["event"]["id"]
    second = (await fire()).json()["event"]["id"]
    assert [e["id"] for e in (await client.get("/api/events")).json()] == [second, first]
