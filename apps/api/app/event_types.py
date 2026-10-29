from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.clock import utcnow
from app.models import EventType

# The catalogue. Seeded into the event_types table at startup (insert-if-missing), so the
# table stays the single source of truth that subscriptions and events reference.
EVENT_TYPES: list[dict] = [
    {
        "key": "reward_transaction_created",
        "description": "A member earned or redeemed points.",
        "sample_payload": {
            "transaction_id": "txn_123",
            "member_id": "mem_42",
            "points": 50,
            "kind": "earn",
        },
    },
    {
        "key": "campaign_updated",
        "description": "A campaign's rules, dates or status changed.",
        "sample_payload": {"campaign_id": "cmp_7", "status": "active", "multiplier": 2},
    },
    {
        "key": "member_account_linked",
        "description": "A member linked an external account.",
        "sample_payload": {"member_id": "mem_42", "provider": "acme_bank"},
    },
]


async def seed_event_types(session: AsyncSession) -> None:
    now = utcnow()
    stmt = insert(EventType).values([{**t, "created_at": now} for t in EVENT_TYPES])
    await session.execute(stmt.on_conflict_do_nothing(index_elements=["key"]))
    await session.commit()
