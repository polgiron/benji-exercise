import json

import pytest
from sqlalchemy import select

from app.event_types import EVENT_TYPES
from app.models import Delivery, DeliveryStatus, Event
from tests.conftest import sample


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
    r = await fire("nope", payload={"x": 1})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "unknown_event_type"


async def test_body_is_the_signed_envelope(db, fire):
    r = await fire()
    async with db.sessions() as s:
        event = await s.get(Event, r.json()["event"]["id"])
    envelope = json.loads(event.body)
    assert envelope["id"] == event.id
    assert envelope["type"] == "campaign_updated"
    assert envelope["data"] == sample()
    assert envelope["created_at"].endswith("Z")


async def test_events_are_listed_newest_first(client, fire):
    first = (await fire()).json()["event"]["id"]
    second = (await fire()).json()["event"]["id"]
    assert [e["id"] for e in (await client.get("/api/events")).json()] == [second, first]


async def test_every_sample_payload_matches_its_schema():
    from jsonschema import Draft202012Validator

    for t in EVENT_TYPES:
        validator = Draft202012Validator(
            t["payload_schema"], format_checker=Draft202012Validator.FORMAT_CHECKER
        )
        assert not list(validator.iter_errors(t["sample_payload"])), t["key"]


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (sample(points_multiplier="2"), "payload['points_multiplier']"),
        (sample(status="live"), "payload['status']"),
        (sample(starts_at="tomorrow"), "payload['starts_at']"),
        (sample(extra=1), "payload: Additional properties"),
        ({"campaign_id": "cmp_7"}, "is a required property"),
    ],
)
async def test_payload_must_match_the_event_type_schema(db, fire, payload, message):
    r = await fire(payload=payload)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_payload"
    assert message in r.json()["error"]["message"]
    async with db.sessions() as s:
        assert (await s.scalars(select(Event))).all() == []


async def test_event_types_expose_their_schema(client):
    [t] = [
        t for t in (await client.get("/api/event-types")).json() if t["key"] == "campaign_updated"
    ]
    assert t["payload_schema"]["additionalProperties"] is False
