from typing import Annotated

from fastapi import APIRouter, Header, Query, Request, Response

from app.deps import Session, notify_changed
from app.schemas import EventCreate, EventOut, EventPublished
from app.services import events as service

router = APIRouter(prefix="/api/events", tags=["events"])


@router.post(
    "",
    status_code=201,
    responses={200: {"model": EventPublished, "description": "Deduplicated re-submit"}},
)
async def publish_event(
    data: EventCreate,
    request: Request,
    session: Session,
    response: Response,
    idempotency_key: Annotated[str | None, Header(max_length=255)] = None,
) -> EventPublished:
    """Internal ingestion API: what Benji's services call when something happens.

    Send an `Idempotency-Key` per intended action and reuse it on retry: a re-submit
    returns 200 with `deduplicated: true` and creates nothing.
    """
    published = await service.publish_event(session, data.event_type, data.payload, idempotency_key)
    if published.deduplicated:
        response.status_code = 200
    else:
        await notify_changed(request, published.delivery_ids)
    return EventPublished(
        deduplicated=published.deduplicated,
        event=EventOut.model_validate(published.event),
        delivery_count=len(published.delivery_ids),
    )


@router.get("")
async def list_events(
    session: Session, limit: Annotated[int, Query(ge=1, le=500)] = 100
) -> list[EventOut]:
    return [EventOut.model_validate(e) for e in await service.list_events(session, limit)]
