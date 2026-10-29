from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clock import utcnow
from app.errors import ApiError, not_found
from app.ids import new_id
from app.models import Endpoint, EventType, Subscription
from app.schemas import EndpointCreate, EndpointUpdate
from app.signing import generate_secret


async def _check_event_types(session: AsyncSession, keys: list[str]) -> list[str]:
    unique = sorted(set(keys))
    known = set(await session.scalars(select(EventType.key).where(EventType.key.in_(unique))))
    unknown = [k for k in unique if k not in known]
    if unknown:
        raise ApiError(422, "unknown_event_type", f"Unknown event type: {', '.join(unknown)}")
    return unique


async def list_endpoints(session: AsyncSession) -> Sequence[Endpoint]:
    return (await session.scalars(select(Endpoint).order_by(Endpoint.created_at.desc()))).all()


async def get_endpoint(session: AsyncSession, endpoint_id: str) -> Endpoint:
    endpoint = await session.get(Endpoint, endpoint_id)
    if endpoint is None:
        raise not_found("Endpoint", endpoint_id)
    return endpoint


async def create_endpoint(session: AsyncSession, data: EndpointCreate) -> Endpoint:
    event_types = await _check_event_types(session, data.event_types)
    now = utcnow()
    endpoint = Endpoint(
        id=new_id("ep"),
        url=str(data.url),
        description=data.description,
        secret=generate_secret(),
        enabled=True,
        created_at=now,
        updated_at=now,
        subscriptions=[Subscription(event_type=k) for k in event_types],
    )
    session.add(endpoint)
    await session.commit()
    return endpoint


async def update_endpoint(
    session: AsyncSession, endpoint_id: str, data: EndpointUpdate
) -> Endpoint:
    endpoint = await get_endpoint(session, endpoint_id)
    if data.event_types is not None:
        event_types = await _check_event_types(session, data.event_types)
        endpoint.subscriptions = [Subscription(event_type=k) for k in event_types]
    if data.url is not None:
        endpoint.url = str(data.url)
    if "description" in data.model_fields_set:
        endpoint.description = data.description
    if data.enabled is not None:
        endpoint.enabled = data.enabled
    endpoint.updated_at = utcnow()
    await session.commit()
    await session.refresh(endpoint)
    return endpoint
