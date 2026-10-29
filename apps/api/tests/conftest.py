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
