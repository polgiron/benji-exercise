from sqlalchemy import select

from app.models import Delivery, DeliveryAttempt


async def only_delivery(db) -> Delivery:
    async with db.sessions() as s:
        [delivery] = (await s.scalars(select(Delivery))).all()
        return delivery


async def attempts(db, delivery_id: str) -> list[DeliveryAttempt]:
    async with db.sessions() as s:
        stmt = (
            select(DeliveryAttempt)
            .where(DeliveryAttempt.delivery_id == delivery_id)
            .order_by(DeliveryAttempt.number)
        )
        return list((await s.scalars(stmt)).all())
