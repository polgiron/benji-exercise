from collections.abc import AsyncIterator

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


@pytest.fixture
def fire(client):
    async def fire(event_type="campaign_updated", payload=None, key=None):
        headers = {"Idempotency-Key": key} if key else {}
        body = {"event_type": event_type, "payload": payload or {"campaign_id": "cmp_7"}}
        return await client.post("/api/events", json=body, headers=headers)

    return fire
