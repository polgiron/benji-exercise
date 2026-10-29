from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bus import Bus
from app.config import Settings, settings
from app.db import Database
from app.errors import install_error_handlers
from app.routes import deliveries, endpoints, event_types, events, mock, stream
from app.services.deliveries import summaries
from app.shutdown import on_exit_signal
from app.worker import DeliveryWorker


def create_app(
    config: Settings = settings,
    *,
    run_worker: bool = True,
    transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    """`run_worker=False` lets tests drive the worker by hand (`run_once`)."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        db = Database(config.database_url)
        await db.create_all()
        bus = Bus()

        async def on_delivery_change(delivery_ids: list[str]) -> None:
            if not bus.subscriber_count:
                return
            async with db.sessions() as session:
                for summary in await summaries(session, delivery_ids, config):
                    bus.publish("delivery.updated", summary.model_dump(mode="json"))

        worker = DeliveryWorker(db, config, transport=transport, on_change=on_delivery_change)
        app.state.db = db
        app.state.bus = bus
        app.state.on_delivery_change = on_delivery_change
        app.state.worker = worker
        if run_worker:
            worker.start()
        restore_signals = on_exit_signal(bus.close)
        yield
        restore_signals()
        await worker.stop()
        await db.dispose()

    app = FastAPI(title="Benji Webhooks API", version="0.1.0", lifespan=lifespan)
    app.state.settings = config
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_error_handlers(app)
    app.include_router(event_types.router)
    app.include_router(endpoints.router)
    app.include_router(events.router)
    app.include_router(deliveries.router)
    app.include_router(stream.router)
    if config.mock_receivers:
        app.include_router(mock.router)

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
