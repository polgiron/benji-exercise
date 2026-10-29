import random

from fastapi import APIRouter, Request

from app.clock import utcnow
from app.deps import Session, notify_changed
from app.schemas import DemoReset, DemoSeeded
from app.services import demo as service

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.post("/reset")
async def reset_demo_data(session: Session) -> DemoReset:
    """Test-panel tool: **deletes every endpoint, event and delivery**. Event types stay."""
    deleted = await service.reset(session)
    return DemoReset(
        endpoints=deleted.endpoints, events=deleted.events, deliveries=deleted.deliveries
    )


@router.post("/seed")
async def seed_demo_data(request: Request, session: Session) -> DemoSeeded:
    """Test-panel tool: **deletes every endpoint, event and delivery**, then fills the
    database with demo endpoints on the `/mock/*` receivers and a month of deliveries."""
    seeded = await service.seed(
        session, str(request.base_url), request.app.state.settings, utcnow(), random.Random()
    )
    await notify_changed(request, seeded.live_delivery_ids)
    return DemoSeeded(
        endpoints=seeded.endpoints, events=seeded.events, deliveries=seeded.deliveries
    )
