from datetime import datetime
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
