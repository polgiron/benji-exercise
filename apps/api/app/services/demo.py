"""Demo data: wipe the customer-side tables, then fill them with a month of history.

The history is written straight to the tables, as the worker would have left it had it
delivered each event to the endpoint's `/mock/*` receiver: same attempt counts, statuses,
errors and backoff gaps. Writing it through the worker would take real time and put every
row at "now", leaving the 7- and 30-day charts empty.
"""

import random
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import delete, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.ids import new_id
from app.models import (
    AttemptTrigger,
    Delivery,
    DeliveryAttempt,
    DeliveryStatus,
    Endpoint,
    Event,
    Subscription,
)
from app.retry import next_delay
from app.services.events import new_event, publish_event
from app.signing import generate_secret

HISTORY_DAYS = 30
HISTORY_EVENTS = 400


@dataclass(frozen=True)
class Answer:
    """One reply of a mock receiver, as the worker would record it."""

    status: int | None
    body: str | None
    error: str | None
    duration_ms: tuple[int, int]


OK = Answer(200, "received", None, (40, 260))
UNAVAILABLE = Answer(503, "flaky failure", "HTTP 503", (30, 120))
ERROR = Answer(500, "internal error", "HTTP 500", (30, 150))
REJECTED = Answer(400, "bad request", "HTTP 400", (20, 90))
TIMEOUT = Answer(None, None, "timeout", (10_000, 10_050))


@dataclass(frozen=True)
class DemoEndpoint:
    path: str
    description: str
    event_types: tuple[str, ...]
    # What the receiver answers, attempt after attempt, given max_attempts.
    answers: Callable[[int], list[Answer]]
    enabled: bool = True
    # Days ago it started and stopped getting events: the failing ones get a short window,
    # so the demo reads like a healthy system with a few incidents, not a broken one.
    active_days: tuple[float, float] = (HISTORY_DAYS, 0)


DEMO_ENDPOINTS = [
    DemoEndpoint(
        "ok",
        "CRM sync",
        ("campaign_updated", "member_account_linked", "reward_transaction_created"),
        lambda _: [OK],
    ),
    DemoEndpoint(
        "flaky?fail=2",
        "Points ledger",
        ("reward_transaction_created",),
        lambda n: ([UNAVAILABLE] * 2 + [OK])[:n],
    ),
    # A real customer's servers each have their own URL; the query only tells the two
    # /mock/ok endpoints apart (the receiver ignores it).
    DemoEndpoint(
        "ok?receiver=campaign-mirror", "Campaign mirror", ("campaign_updated",), lambda _: [OK]
    ),
    DemoEndpoint(
        "fail",
        "Partner bridge (down)",
        ("member_account_linked",),
        lambda n: [ERROR] * n,
        active_days=(2, 0),
    ),
    DemoEndpoint(
        "reject",
        "Legacy importer (retired)",
        ("reward_transaction_created",),
        lambda _: [REJECTED],
        enabled=False,
        active_days=(HISTORY_DAYS, 26),
    ),
    DemoEndpoint(
        "slow?seconds=15",
        "Analytics export (paused)",
        ("campaign_updated",),
        lambda n: [TIMEOUT] * n,
        enabled=False,
        active_days=(12, 9),
    ),
]

# How often each type happens: points move far more often than campaigns change.
EVENT_MIX = {
    "reward_transaction_created": 0.6,
    "member_account_linked": 0.25,
    "campaign_updated": 0.15,
}

CAMPAIGNS = ["Double points weekend", "Spring sale", "Birthday bonus", "Refer a friend"]
PROVIDERS = ["acme_bank", "shopify", "stripe", "square"]
REASONS = ["purchase", "referral", "review", "birthday"]


@dataclass(frozen=True)
class Seeded:
    endpoints: int
    events: int
    deliveries: int
    # The few events fired for real at the end, for the worker to deliver live.
    live_delivery_ids: list[str]


def _iso(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


def _payload(event_type: str, at: datetime, n: int, rng: random.Random) -> dict[str, Any]:
    member = f"mem_{rng.randint(1, 120)}"
    if event_type == "reward_transaction_created":
        kind = "redeem" if rng.random() < 0.2 else "earn"
        return {
            "transaction_id": f"txn_{n}",
            "member_id": member,
            "kind": kind,
            "points": rng.choice([10, 25, 50, 100, 250]),
            "reason": "redemption" if kind == "redeem" else rng.choice(REASONS),
            "occurred_at": _iso(at),
        }
    if event_type == "member_account_linked":
        return {
            "member_id": member,
            "provider": rng.choice(PROVIDERS),
            "external_account_id": f"acc_{rng.randint(100, 999)}",
            "linked_at": _iso(at),
        }
    starts = at + timedelta(days=rng.randint(1, 7))
    return {
        "campaign_id": f"cmp_{rng.randint(1, 12)}",
        "name": rng.choice(CAMPAIGNS),
        "status": rng.choice(["draft", "active", "active", "paused", "ended"]),
        "points_multiplier": rng.choice([1.5, 2, 3]),
        "starts_at": _iso(starts),
        "ends_at": _iso(starts + timedelta(days=rng.randint(2, 14))),
    }


async def reset(session: AsyncSession) -> None:
    """Delete every endpoint, event, delivery and attempt. The event-type catalogue stays."""
    for table in (DeliveryAttempt, Delivery, Event, Subscription, Endpoint):
        await session.execute(delete(table))


async def seed(
    session: AsyncSession,
    base_url: str,
    settings: Settings,
    now: datetime,
    rng: random.Random,
) -> Seeded:
    """Reset, then write the demo endpoints and a month of their delivery history, in one
    transaction. Then publish one event of each type for real, so the worker has live
    deliveries to work through (and retry) as the dashboard opens."""
    await reset(session)

    endpoints = [
        (
            demo,
            Endpoint(
                id=new_id("ep"),
                url=f"{base_url.rstrip('/')}/mock/{demo.path}",
                description=demo.description,
                secret=generate_secret(),
                enabled=demo.enabled,
                created_at=now - timedelta(days=demo.active_days[0], hours=1),
                updated_at=now - timedelta(days=demo.active_days[1]),
                subscriptions=[Subscription(event_type=t) for t in demo.event_types],
            ),
        )
        for demo in DEMO_ENDPOINTS
    ]
    session.add_all(endpoint for _, endpoint in endpoints)

    # A power of a uniform draw weights the history towards today, like a growing product.
    moments = sorted(
        now - timedelta(days=HISTORY_DAYS) * rng.random() ** 1.5 for _ in range(HISTORY_EVENTS)
    )
    events: list[Event] = []
    deliveries: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    for n, at in enumerate(moments, start=1):
        event_type = rng.choices(list(EVENT_MIX), weights=list(EVENT_MIX.values()))[0]
        event = new_event(event_type, _payload(event_type, at, n, rng), at)
        events.append(event)
        days_ago = (now - at) / timedelta(days=1)
        for demo, endpoint in endpoints:
            start, end = demo.active_days
            if event_type in demo.event_types and end <= days_ago < start:
                delivery, rows = _history(event, endpoint, demo, settings, rng)
                deliveries.append(delivery)
                attempts.extend(rows)

    session.add_all(events)
    await session.flush()
    await session.execute(insert(Delivery), deliveries)
    await session.execute(insert(DeliveryAttempt), attempts)
    await session.commit()

    live: list[str] = []
    for n, event_type in enumerate(EVENT_MIX, start=len(events) + 1):
        published = await publish_event(session, event_type, _payload(event_type, now, n, rng))
        live.extend(published.delivery_ids)
    return Seeded(
        endpoints=len(endpoints),
        events=len(events) + len(EVENT_MIX),
        deliveries=len(deliveries) + len(live),
        live_delivery_ids=live,
    )


def _history(
    event: Event,
    endpoint: Endpoint,
    demo: DemoEndpoint,
    settings: Settings,
    rng: random.Random,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """The delivery row and attempts the worker would have written for this pair."""
    delivery_id = new_id("dlv")
    script = demo.answers(settings.max_attempts)
    attempts: list[dict[str, Any]] = []
    at = event.created_at + timedelta(milliseconds=rng.randint(5, 80))
    for number, answer in enumerate(script, start=1):
        duration = rng.randint(*answer.duration_ms)
        attempts.append(
            {
                "id": new_id("att"),
                "delivery_id": delivery_id,
                "number": number,
                "trigger": AttemptTrigger.auto,
                "started_at": at,
                "duration_ms": duration,
                "response_status": answer.status,
                "response_body": answer.body,
                "error": answer.error,
            }
        )
        at += timedelta(milliseconds=duration)
        if number < len(script):
            delay = next_delay(
                number, settings.retry_base_seconds, settings.retry_cap_seconds, rand=rng.random
            )
            at += timedelta(seconds=delay)

    last = script[-1]
    delivery = {
        "id": delivery_id,
        "event_id": event.id,
        "endpoint_id": endpoint.id,
        "status": DeliveryStatus.succeeded if last is OK else DeliveryStatus.failed,
        "attempt_count": len(script),
        "series_attempts": len(script),
        "replay_count": 0,
        "next_attempt_at": None,
        "lease_expires_at": None,
        "last_error": last.error,
        # One bump to claim each attempt, one to record it.
        "version": 1 + 2 * len(script),
        "created_at": event.created_at,
        "updated_at": at,
    }
    return delivery, attempts
