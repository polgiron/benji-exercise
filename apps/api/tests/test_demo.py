from collections import Counter
from datetime import timedelta

import httpx
from sqlalchemy import func, select

from app.config import Settings
from app.event_types import validate_payload
from app.main import create_app
from app.models import Delivery, DeliveryAttempt, DeliveryStatus, Endpoint, Event, EventType


async def test_seed_replaces_everything_that_was_there(client, make_endpoint, fire, db):
    mine = await make_endpoint(url="https://example.com/mine")
    assert (await fire()).status_code == 201

    r = await client.post("/api/demo/seed")

    assert r.status_code == 200, r.text
    seeded = r.json()
    async with db.sessions() as s:
        assert await s.get(Endpoint, mine["id"]) is None
        assert await s.scalar(select(func.count()).select_from(Endpoint)) == seeded["endpoints"]
        assert await s.scalar(select(func.count()).select_from(Event)) == seeded["events"]
        assert await s.scalar(select(func.count()).select_from(Delivery)) == seeded["deliveries"]
        assert await s.scalar(select(func.count()).select_from(EventType)) == 3
    urls = [e["url"] for e in (await client.get("/api/endpoints")).json()]
    assert all(url.startswith("http://test/mock/") for url in urls)
    # Two endpoints on one URL would show each event twice under what looks like one receiver.
    assert len(set(urls)) == len(urls)


async def test_seeding_twice_does_not_add_up(client, db):
    first = (await client.post("/api/demo/seed")).json()
    second = (await client.post("/api/demo/seed")).json()

    assert (second["endpoints"], second["events"]) == (first["endpoints"], first["events"])
    async with db.sessions() as s:
        assert await s.scalar(select(func.count()).select_from(Delivery)) == second["deliveries"]


async def test_history_is_what_each_mock_would_have_answered(client, db, settings, clock):
    await client.post("/api/demo/seed")

    async with db.sessions() as s:
        deliveries = (await s.scalars(select(Delivery))).all()
        attempts = Counter((await s.scalars(select(DeliveryAttempt.delivery_id))).all())
    history = [d for d in deliveries if d.created_at < clock.now]
    live = [d for d in deliveries if d.created_at == clock.now]

    outcomes = {
        "Points ledger": (DeliveryStatus.succeeded, 3, None),
        "Partner bridge (down)": (DeliveryStatus.failed, settings.max_attempts, "HTTP 500"),
        "Legacy importer (retired)": (DeliveryStatus.failed, 1, "HTTP 400"),
        "Analytics export (paused)": (DeliveryStatus.failed, settings.max_attempts, "timeout"),
        "CRM sync": (DeliveryStatus.succeeded, 1, None),
    }
    for d in history:
        expected = outcomes.get(d.endpoint.description, (DeliveryStatus.succeeded, 1, None))
        assert (d.status, d.attempt_count, d.last_error) == expected, d.endpoint.description
        assert attempts[d.id] == d.attempt_count
        assert d.next_attempt_at is None  # settled: the worker has nothing to pick up
    # The live events wait for the worker; the paused endpoint gets none of them.
    assert live
    assert all(d.status == DeliveryStatus.pending for d in live)
    assert all(d.endpoint.enabled for d in live)


async def test_history_spans_the_month_weighted_to_today(client, db, clock):
    await client.post("/api/demo/seed")

    async with db.sessions() as s:
        created = (await s.scalars(select(Event.created_at))).all()
    assert min(created) >= clock.now - timedelta(days=30)
    assert any(at > clock.now - timedelta(days=1) for at in created)
    assert any(at < clock.now - timedelta(days=7) for at in created)
    recent = sum(at > clock.now - timedelta(days=7) for at in created)
    assert recent > len(created) * 7 / 30  # denser than a flat spread


async def test_every_seeded_payload_matches_its_schema(client, db):
    await client.post("/api/demo/seed")

    async with db.sessions() as s:
        types = {t.key: t for t in (await s.scalars(select(EventType))).all()}
        for event in (await s.scalars(select(Event))).all():
            validate_payload(types[event.event_type], event.payload)


async def test_seed_is_off_with_the_mock_receivers(tmp_path):
    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'off.db'}", mock_receivers=False
    )
    app = create_app(settings, run_worker=False)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            assert (await c.post("/api/demo/seed")).status_code == 404
