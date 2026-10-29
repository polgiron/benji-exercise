from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def make_engine(url: str) -> AsyncEngine:
    engine = create_async_engine(url)

    @event.listens_for(engine.sync_engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _record) -> None:
        cursor = dbapi_conn.cursor()
        # WAL lets the dashboard read while the worker writes; busy_timeout waits for the
        # write lock instead of failing; foreign keys are off by default in SQLite.
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


class Database:
    def __init__(self, url: str) -> None:
        self.engine = make_engine(url)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_all(self) -> None:
        from app import models  # noqa: F401  (registers the tables)
        from app.event_types import seed_event_types

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with self.sessions() as session:
            await seed_event_types(session)

    async def dispose(self) -> None:
        await self.engine.dispose()
