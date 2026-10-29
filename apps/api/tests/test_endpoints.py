from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Endpoint

NEW = {"url": "https://example.com/hook", "event_types": ["campaign_updated"]}


async def test_list_event_types(client):
    r = await client.get("/api/event-types")
    assert r.status_code == 200
    assert {t["key"] for t in r.json()} >= {"campaign_updated"}
    assert all("sample_payload" in t for t in r.json())


async def test_create_returns_the_secret_once(client):
    r = await client.post("/api/endpoints", json=NEW)
    assert r.status_code == 201
    created = r.json()
    assert created["secret"].startswith("whsec_")
    assert created["enabled"] is True
    assert created["event_types"] == ["campaign_updated"]

    listed = (await client.get("/api/endpoints")).json()
    assert [e["id"] for e in listed] == [created["id"]]
    assert "secret" not in listed[0]
    assert "secret" not in (await client.get(f"/api/endpoints/{created['id']}")).json()


async def test_event_types_are_deduplicated_and_sorted(client):
    body = NEW | {"event_types": ["member_account_linked", "campaign_updated", "campaign_updated"]}
    r = await client.post("/api/endpoints", json=body)
    assert r.json()["event_types"] == ["campaign_updated", "member_account_linked"]


async def test_unknown_event_type_is_rejected(client):
    r = await client.post("/api/endpoints", json=NEW | {"event_types": ["nope"]})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "unknown_event_type"


async def test_invalid_url_uses_the_error_shape(client):
    r = await client.post("/api/endpoints", json=NEW | {"url": "not a url"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"
    assert r.json()["error"]["message"].startswith("url:")


async def test_at_least_one_event_type(client):
    r = await client.post("/api/endpoints", json=NEW | {"event_types": []})
    assert r.status_code == 422


async def test_disable_and_change_event_types(client):
    ep = (await client.post("/api/endpoints", json=NEW)).json()
    r = await client.patch(
        f"/api/endpoints/{ep['id']}",
        json={"enabled": False, "event_types": ["member_account_linked"]},
    )
    assert r.status_code == 200
    assert r.json()["enabled"] is False
    assert r.json()["event_types"] == ["member_account_linked"]
    assert r.json()["url"] == NEW["url"]


async def test_update_unknown_endpoint(client):
    r = await client.patch("/api/endpoints/ep_nope", json={"enabled": False})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


async def test_a_url_already_taken_is_refused_on_create(client, db):
    assert (await client.post("/api/endpoints", json=NEW)).status_code == 201

    r = await client.post("/api/endpoints", json=NEW | {"event_types": ["member_account_linked"]})

    assert r.status_code == 409
    assert r.json()["error"]["code"] == "endpoint_url_taken"
    assert len((await client.get("/api/endpoints")).json()) == 1


async def test_a_url_already_taken_is_refused_on_update(client, make_endpoint):
    taken = await make_endpoint(url="https://example.com/taken")
    other = await make_endpoint(url="https://example.com/other")

    r = await client.patch(f"/api/endpoints/{other['id']}", json={"url": taken["url"]})

    assert r.status_code == 409
    assert r.json()["error"]["code"] == "endpoint_url_taken"
    assert (await client.get(f"/api/endpoints/{other['id']}")).json()["url"] == other["url"]
    # Keeping its own URL is not a conflict.
    r = await client.patch(f"/api/endpoints/{other['id']}", json={"url": other["url"]})
    assert r.status_code == 200


async def test_the_database_refuses_a_second_endpoint_on_a_url(db, make_endpoint):
    """The guarantee is the UNIQUE constraint, not the service: a write that skips the
    service is refused too."""
    taken = await make_endpoint(url="https://example.com/taken")
    now = datetime.now(UTC)
    async with db.sessions() as s:
        s.add(Endpoint(id="ep_dup", url=taken["url"], secret="x", created_at=now, updated_at=now))
        with pytest.raises(IntegrityError):
            await s.commit()
