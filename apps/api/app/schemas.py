from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class Model(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EventTypeOut(Model):
    key: str
    description: str
    payload_schema: dict[str, Any]
    sample_payload: dict[str, Any]


class EndpointCreate(BaseModel):
    url: AnyHttpUrl
    description: str | None = Field(default=None, max_length=500)
    event_types: list[str] = Field(min_length=1)


class EndpointUpdate(BaseModel):
    url: AnyHttpUrl | None = None
    description: str | None = Field(default=None, max_length=500)
    event_types: list[str] | None = Field(default=None, min_length=1)
    enabled: bool | None = None


class EndpointOut(Model):
    id: str
    url: str
    description: str | None
    event_types: list[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime


class EndpointCreated(EndpointOut):
    """Only returned by POST /api/endpoints: the one time the secret is shown."""

    secret: str


class EventCreate(BaseModel):
    event_type: str
    payload: dict[str, Any]


class EventOut(Model):
    id: str
    event_type: str
    payload: dict[str, Any]
    idempotency_key: str | None
    created_at: datetime


class EventPublished(BaseModel):
    """`deduplicated: true` means the Idempotency-Key was already used for this exact
    request: nothing new was created and `event` is the original."""

    deduplicated: bool
    event: EventOut
    delivery_count: int


class DeliverySummary(BaseModel):
    """What the deliveries table and the live stream carry. `version` only ever grows:
    clients drop an update whose version is not newer than what they have."""

    id: str
    event_id: str
    event_type: str
    endpoint_id: str
    endpoint_url: str
    status: str
    attempt_count: int
    series_attempts: int
    max_attempts: int
    replay_count: int
    next_attempt_at: datetime | None
    last_error: str | None
    version: int
    created_at: datetime
    updated_at: datetime


class AttemptOut(Model):
    id: str
    number: int
    trigger: str
    started_at: datetime
    duration_ms: int
    response_status: int | None
    response_body: str | None
    error: str | None


class DeliveryDetail(DeliverySummary):
    payload: dict[str, Any]
    attempts: list[AttemptOut]


class DeliveryStats(BaseModel):
    """Delivery counts by status; every status is present, 0 when there are none."""

    pending: int = 0
    in_progress: int = 0
    succeeded: int = 0
    failed: int = 0
    total: int = 0


class ActivityRange(StrEnum):
    last_24h = "24h"
    last_7d = "7d"
    last_30d = "30d"


class ActivityBucket(BaseModel):
    """Deliveries created in [start, start + bucket_seconds), split by their current status."""

    start: datetime
    total: int
    succeeded: int
    failed: int


class DeliveryActivity(BaseModel):
    """Every bucket of the range is present, oldest first; the last one contains now."""

    range: ActivityRange
    bucket_seconds: int
    buckets: list[ActivityBucket]
