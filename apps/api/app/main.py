from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, settings
from app.db import Database
from app.errors import install_error_handlers


def create_app(config: Settings = settings) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        db = Database(config.database_url)
        await db.create_all()
        app.state.db = db
        # The delivery worker starts here.
        yield
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

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
