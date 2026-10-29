from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.db.sessions() as session:
        yield session


Session = Annotated[AsyncSession, Depends(get_session)]


async def notify_changed(request: Request, delivery_ids: list[str]) -> None:
    """New or re-queued work was committed: wake the worker and tell live clients."""
    worker = getattr(request.app.state, "worker", None)
    if worker is not None:
        worker.wake()
    on_change = getattr(request.app.state, "on_delivery_change", None)
    if on_change is not None and delivery_ids:
        await on_change(delivery_ids)
