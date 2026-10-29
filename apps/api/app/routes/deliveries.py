from typing import Annotated

from fastapi import APIRouter, Query, Request

from app.deps import Session, notify_changed
from app.models import DeliveryStatus
from app.schemas import DeliveryDetail, DeliverySummary
from app.services import deliveries as service

router = APIRouter(prefix="/api/deliveries", tags=["deliveries"])


@router.get("")
async def list_deliveries(
    request: Request,
    session: Session,
    status: DeliveryStatus | None = None,
    endpoint_id: str | None = None,
    event_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[DeliverySummary]:
    settings = request.app.state.settings
    rows = await service.list_deliveries(session, status, endpoint_id, event_id, limit)
    return [service.summarize(d, settings) for d in rows]


@router.get("/{delivery_id}")
async def get_delivery(delivery_id: str, request: Request, session: Session) -> DeliveryDetail:
    return await service.get_detail(session, delivery_id, request.app.state.settings)


@router.post("/{delivery_id}/replay")
async def replay_delivery(delivery_id: str, request: Request, session: Session) -> DeliverySummary:
    delivery = await service.replay(session, delivery_id)
    await notify_changed(request, [delivery.id])
    return service.summarize(delivery, request.app.state.settings)
