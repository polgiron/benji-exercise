from fastapi import APIRouter
from sqlalchemy import select

from app.deps import Session
from app.models import EventType
from app.schemas import EventTypeOut

router = APIRouter(prefix="/api/event-types", tags=["event types"])


@router.get("")
async def list_event_types(session: Session) -> list[EventTypeOut]:
    rows = await session.scalars(select(EventType).order_by(EventType.key))
    return [EventTypeOut.model_validate(t) for t in rows]
