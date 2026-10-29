from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clock import utcnow
from app.config import Settings
from app.errors import ApiError, not_found
from app.models import Delivery, DeliveryAttempt, DeliveryStatus
from app.schemas import AttemptOut, DeliveryDetail, DeliveryStats, DeliverySummary


def summarize(delivery: Delivery, settings: Settings) -> DeliverySummary:
    return DeliverySummary(
        id=delivery.id,
        event_id=delivery.event_id,
        event_type=delivery.event.event_type,
        endpoint_id=delivery.endpoint_id,
        endpoint_url=delivery.endpoint.url,
        status=delivery.status,
        attempt_count=delivery.attempt_count,
        series_attempts=delivery.series_attempts,
        max_attempts=settings.max_attempts,
        replay_count=delivery.replay_count,
        next_attempt_at=delivery.next_attempt_at,
        last_error=delivery.last_error,
        version=delivery.version,
        created_at=delivery.created_at,
        updated_at=delivery.updated_at,
    )


async def list_deliveries(
    session: AsyncSession,
    status: DeliveryStatus | None = None,
    endpoint_id: str | None = None,
    event_id: str | None = None,
    limit: int = 100,
) -> Sequence[Delivery]:
    stmt = select(Delivery).order_by(Delivery.created_at.desc(), Delivery.id.desc()).limit(limit)
    if status:
        stmt = stmt.where(Delivery.status == status)
    if endpoint_id:
        stmt = stmt.where(Delivery.endpoint_id == endpoint_id)
    if event_id:
        stmt = stmt.where(Delivery.event_id == event_id)
    return (await session.scalars(stmt)).all()


async def stats(session: AsyncSession, endpoint_id: str | None = None) -> DeliveryStats:
    stmt = select(Delivery.status, func.count()).group_by(Delivery.status)
    if endpoint_id:
        stmt = stmt.where(Delivery.endpoint_id == endpoint_id)
    counts = {status: n for status, n in (await session.execute(stmt)).all()}
    return DeliveryStats(**counts, total=sum(counts.values()))


async def summaries(
    session: AsyncSession, delivery_ids: list[str], settings: Settings
) -> list[DeliverySummary]:
    rows = await session.scalars(select(Delivery).where(Delivery.id.in_(delivery_ids)))
    return [summarize(d, settings) for d in rows]


async def get_delivery(session: AsyncSession, delivery_id: str) -> Delivery:
    delivery = await session.get(Delivery, delivery_id)
    if delivery is None:
        raise not_found("Delivery", delivery_id)
    return delivery


async def get_detail(session: AsyncSession, delivery_id: str, settings: Settings) -> DeliveryDetail:
    delivery = await get_delivery(session, delivery_id)
    attempts = await session.scalars(
        select(DeliveryAttempt)
        .where(DeliveryAttempt.delivery_id == delivery_id)
        .order_by(DeliveryAttempt.number)
    )
    return DeliveryDetail(
        **summarize(delivery, settings).model_dump(),
        payload=delivery.event.payload,
        attempts=[AttemptOut.model_validate(a) for a in attempts],
    )


async def replay(session: AsyncSession, delivery_id: str) -> Delivery:
    """failed → pending on the same row: same event, same webhook-id, a new attempt series.

    Only from `failed`: a succeeded delivery is never sent again, and a pending or
    in-progress one is already going to be.
    """
    delivery = await get_delivery(session, delivery_id)
    if delivery.status != DeliveryStatus.failed:
        raise ApiError(
            409,
            "not_replayable",
            f"Only failed deliveries can be replayed (this one is {delivery.status})",
        )
    if not delivery.endpoint.enabled:
        raise ApiError(409, "endpoint_disabled", "Enable the endpoint before replaying")
    now = utcnow()
    delivery.status = DeliveryStatus.pending
    delivery.next_attempt_at = now
    delivery.series_attempts = 0
    delivery.replay_count += 1
    delivery.last_error = None
    delivery.version += 1
    delivery.updated_at = now
    await session.commit()
    return delivery
