from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    TypeDecorator,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class UTCDateTime(TypeDecorator[datetime]):
    """SQLite has no timezone type: store naive UTC, hand back aware UTC datetimes."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Any) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("naive datetime")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: Any) -> datetime | None:
        return value.replace(tzinfo=UTC) if value is not None else None


class DeliveryStatus(StrEnum):
    pending = "pending"
    in_progress = "in_progress"
    succeeded = "succeeded"
    failed = "failed"


class AttemptTrigger(StrEnum):
    auto = "auto"
    replay = "replay"


class EventType(Base):
    __tablename__ = "event_types"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    description: Mapped[str] = mapped_column(Text)
    # JSON Schema (draft 2020-12) every payload of this type must satisfy.
    payload_schema: Mapped[dict[str, Any]] = mapped_column(JSON)
    sample_payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)


class Endpoint(Base):
    """A customer's subscription: a URL plus the event types it wants."""

    __tablename__ = "endpoints"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    # Two endpoints on one URL would send that server every event twice.
    url: Mapped[str] = mapped_column(Text, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    secret: Mapped[str] = mapped_column(String(64))
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)

    subscriptions: Mapped[list["Subscription"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="Subscription.event_type"
    )

    @property
    def event_types(self) -> list[str]:
        return [s.event_type for s in self.subscriptions]


class Subscription(Base):
    """Link rows behind an endpoint's list of event types."""

    __tablename__ = "subscriptions"

    endpoint_id: Mapped[str] = mapped_column(
        ForeignKey("endpoints.id", ondelete="CASCADE"), primary_key=True
    )
    event_type: Mapped[str] = mapped_column(ForeignKey("event_types.key"), primary_key=True)


class Event(Base):
    """One accepted incoming call to POST /api/events."""

    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    event_type: Mapped[str] = mapped_column(ForeignKey("event_types.key"))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    # The exact envelope bytes we sign and send, fixed at creation so every retry and
    # replay sends identical content.
    body: Mapped[str] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), unique=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)


class Delivery(Base):
    """One (event, endpoint) pair, forever. The outbox row the worker drains."""

    __tablename__ = "deliveries"
    __table_args__ = (UniqueConstraint("event_id", "endpoint_id"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"))
    endpoint_id: Mapped[str] = mapped_column(ForeignKey("endpoints.id"), index=True)
    status: Mapped[DeliveryStatus] = mapped_column(String(16), index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    # Attempts since the last replay (or creation): what max_attempts is checked against.
    series_attempts: Mapped[int] = mapped_column(Integer, default=0)
    replay_count: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(UTCDateTime, index=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    last_error: Mapped[str | None] = mapped_column(Text)
    # Bumped on every change so the dashboard can drop out-of-order live updates.
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)

    event: Mapped[Event] = relationship(lazy="joined")
    endpoint: Mapped[Endpoint] = relationship(lazy="joined")


class DeliveryAttempt(Base):
    """One outgoing HTTP call. Append-only."""

    __tablename__ = "delivery_attempts"
    __table_args__ = (UniqueConstraint("delivery_id", "number"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    delivery_id: Mapped[str] = mapped_column(ForeignKey("deliveries.id"), index=True)
    number: Mapped[int] = mapped_column(Integer)
    trigger: Mapped[AttemptTrigger] = mapped_column(String(16))
    started_at: Mapped[datetime] = mapped_column(UTCDateTime)
    duration_ms: Mapped[int] = mapped_column(Integer)
    response_status: Mapped[int | None] = mapped_column(Integer)
    response_body: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
