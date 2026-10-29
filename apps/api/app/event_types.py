from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.clock import utcnow
from app.errors import ApiError
from app.models import EventType

# The catalogue: the contract each event type's payload follows. Seeded into the
# event_types table at startup, so the table stays the single source of truth that
# subscriptions and events reference.
#
# Schemas are strict on ingestion (every field declared, additionalProperties: false), so
# nothing undocumented reaches customers. Customers are told adding a field is
# non-breaking; removing, renaming or retyping one needs a new version (not built).


def _object(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


_ID = {"type": "string", "minLength": 1}
_TIMESTAMP = {"type": "string", "format": "date-time"}

EVENT_TYPES: list[dict[str, Any]] = [
    {
        "key": "reward_transaction_created",
        "description": "A member earned or redeemed points.",
        "payload_schema": _object(
            {
                "transaction_id": _ID,
                "member_id": _ID,
                "kind": {"enum": ["earn", "redeem"]},
                "points": {"type": "integer", "minimum": 1},
                "reason": {"type": "string"},
                "occurred_at": _TIMESTAMP,
            },
            ["transaction_id", "member_id", "kind", "points", "occurred_at"],
        ),
        "sample_payload": {
            "transaction_id": "txn_123",
            "member_id": "mem_42",
            "kind": "earn",
            "points": 50,
            "reason": "purchase",
            "occurred_at": "2026-10-29T09:00:00Z",
        },
    },
    {
        "key": "campaign_updated",
        "description": "A campaign's rules, dates or status changed.",
        "payload_schema": _object(
            {
                "campaign_id": _ID,
                "name": {"type": "string", "minLength": 1},
                "status": {"enum": ["draft", "active", "paused", "ended"]},
                "points_multiplier": {"type": "number", "exclusiveMinimum": 0},
                "starts_at": _TIMESTAMP,
                "ends_at": {"type": ["string", "null"], "format": "date-time"},
            },
            ["campaign_id", "name", "status", "starts_at"],
        ),
        "sample_payload": {
            "campaign_id": "cmp_7",
            "name": "Double points weekend",
            "status": "active",
            "points_multiplier": 2,
            "starts_at": "2026-11-01T00:00:00Z",
            "ends_at": "2026-11-03T00:00:00Z",
        },
    },
    {
        "key": "member_account_linked",
        "description": "A member linked an external account.",
        "payload_schema": _object(
            {
                "member_id": _ID,
                "provider": {"type": "string", "minLength": 1},
                "external_account_id": _ID,
                "linked_at": _TIMESTAMP,
            },
            ["member_id", "provider", "external_account_id", "linked_at"],
        ),
        "sample_payload": {
            "member_id": "mem_42",
            "provider": "acme_bank",
            "external_account_id": "acc_981",
            "linked_at": "2026-10-29T09:00:00Z",
        },
    },
]


def validate_payload(event_type: EventType, payload: dict[str, Any]) -> None:
    validator = Draft202012Validator(
        event_type.payload_schema, format_checker=Draft202012Validator.FORMAT_CHECKER
    )
    error = best_match(validator.iter_errors(payload))
    if error is not None:
        where = "payload" + "".join(f"[{p!r}]" for p in error.absolute_path)
        raise ApiError(422, "invalid_payload", f"{where}: {error.message}")


async def seed_event_types(session: AsyncSession) -> None:
    """Upsert the catalogue: the code is the source, the table follows it."""
    now = utcnow()
    stmt = insert(EventType).values([{**t, "created_at": now} for t in EVENT_TYPES])
    stmt = stmt.on_conflict_do_update(
        index_elements=["key"],
        set_={
            "description": stmt.excluded.description,
            "payload_schema": stmt.excluded.payload_schema,
            "sample_payload": stmt.excluded.sample_payload,
        },
    )
    await session.execute(stmt)
    await session.commit()
