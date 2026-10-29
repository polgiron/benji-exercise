from datetime import UTC, datetime
from itertools import pairwise

import pytest


async def test_list_and_filter(client, make_endpoint, fire, receiver, drain):
    ok = await make_endpoint(url="https://ok.example.com/")
    bad = await make_endpoint(url="https://bad.example.com/")
    receiver.respond(400)  # both fail; then fix one and replay it
    await fire()
    await drain()

    all_ = (await client.get("/api/deliveries")).json()
    assert len(all_) == 2
    assert {d["status"] for d in all_} == {"failed"}

    ok_delivery = (await client.get("/api/deliveries", params={"endpoint_id": ok["id"]})).json()
    assert [d["endpoint_url"] for d in ok_delivery] == ["https://ok.example.com/"]
    receiver.respond(200)
    await client.post(f"/api/deliveries/{ok_delivery[0]['id']}/replay")
    await drain()

    failed = (await client.get("/api/deliveries", params={"status": "failed"})).json()
    assert [d["endpoint_id"] for d in failed] == [bad["id"]]
    assert (await client.get("/api/deliveries", params={"status": "nope"})).status_code == 422


async def test_list_filters_by_event_type(client, make_endpoint, fire):
    await make_endpoint(event_types=("campaign_updated", "member_account_linked"))
    await fire("campaign_updated")
    await fire("member_account_linked")

    linked = (
        await client.get("/api/deliveries", params={"event_type": "member_account_linked"})
    ).json()
    assert [d["event_type"] for d in linked] == ["member_account_linked"]
    unknown = await client.get("/api/deliveries", params={"event_type": "nope"})
    assert unknown.json() == []


async def test_detail_has_payload_and_attempt_log(client, make_endpoint, fire, receiver, drain):
    await make_endpoint()
    receiver.respond(503, 200)
    payload = (await fire()).json()["event"]["payload"]
    await drain()

    [summary] = (await client.get("/api/deliveries")).json()
    assert summary["attempt_count"] == 2
    assert summary["max_attempts"] == 5
    assert summary["event_type"] == "campaign_updated"

    detail = (await client.get(f"/api/deliveries/{summary['id']}")).json()
    assert detail["payload"] == payload
    assert [a["response_status"] for a in detail["attempts"]] == [503, 200]
    assert detail["attempts"][0]["error"] == "HTTP 503"
    assert detail["attempts"][0]["response_body"] == "nope"


async def test_unknown_delivery(client):
    r = await client.get("/api/deliveries/dlv_nope")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


async def test_stats_count_by_status(client, make_endpoint, fire, worker, receiver):
    empty = (await client.get("/api/deliveries/stats")).json()
    assert empty == {"pending": 0, "in_progress": 0, "succeeded": 0, "failed": 0, "total": 0}

    ok = await make_endpoint(url="https://ok.example.com/")
    await make_endpoint(url="https://bad.example.com/")
    receiver.respond(200, 400)
    await fire()
    await worker.run_once()  # one succeeds, one is rejected
    await fire()  # two more, still pending

    stats = (await client.get("/api/deliveries/stats")).json()
    assert stats == {"pending": 2, "in_progress": 0, "succeeded": 1, "failed": 1, "total": 4}

    per_endpoint = (
        await client.get("/api/deliveries/stats", params={"endpoint_id": ok["id"]})
    ).json()
    assert per_endpoint["total"] == 2
    assert per_endpoint["pending"] == 1


NOW = datetime(2026, 1, 15, 13, 47, 12, tzinfo=UTC)


def at(iso: str) -> datetime:
    return datetime.fromisoformat(iso).replace(tzinfo=UTC)


def starts(activity) -> list[datetime]:
    return [datetime.fromisoformat(b["start"]) for b in activity["buckets"]]


@pytest.mark.parametrize(
    ("range_", "count", "bucket_seconds"),
    [("24h", 24, 3600), ("7d", 28, 6 * 3600), ("30d", 30, 86400)],
)
async def test_activity_is_zero_filled_and_aligned(client, clock, range_, count, bucket_seconds):
    clock.now = NOW
    activity = (await client.get("/api/deliveries/activity", params={"range": range_})).json()

    assert activity["range"] == range_
    assert activity["bucket_seconds"] == bucket_seconds
    assert len(activity["buckets"]) == count
    assert all((b["total"], b["succeeded"], b["failed"]) == (0, 0, 0) for b in activity["buckets"])
    times = starts(activity)
    assert all(t.timestamp() % bucket_seconds == 0 for t in times)
    assert all((b - a).total_seconds() == bucket_seconds for a, b in pairwise(times))
    assert times[-1].timestamp() <= NOW.timestamp() < times[-1].timestamp() + bucket_seconds


async def test_activity_defaults_to_7d(client, clock):
    clock.now = NOW
    activity = (await client.get("/api/deliveries/activity")).json()
    assert activity["range"] == "7d"
    assert len(activity["buckets"]) == 28
    assert starts(activity)[-1] == at("2026-01-15T12:00:00")


async def test_activity_counts_land_in_their_bucket(
    client, clock, make_endpoint, fire, worker, receiver
):
    await make_endpoint(url="https://ok.example.com/")
    await make_endpoint(url="https://bad.example.com/")
    receiver.respond(200, 400)
    clock.now = at("2026-01-15T10:30:00")
    await fire()
    await worker.run_once()  # one succeeds, one is rejected

    clock.now = at("2026-01-14T13:59:59")  # just before the 24h window
    await fire()
    clock.now = at("2026-01-14T14:00:00")  # exactly on the first 24h bucket's start
    await fire()
    clock.now = NOW
    await fire()  # two more, still pending

    day = (await client.get("/api/deliveries/activity", params={"range": "24h"})).json()
    counts = {
        datetime.fromisoformat(b["start"]): (b["total"], b["succeeded"], b["failed"])
        for b in day["buckets"]
        if b["total"]
    }
    assert counts == {
        at("2026-01-14T14:00:00"): (2, 0, 0),
        at("2026-01-15T10:00:00"): (2, 1, 1),
        at("2026-01-15T13:00:00"): (2, 0, 0),
    }

    week = (await client.get("/api/deliveries/activity", params={"range": "7d"})).json()
    counts = {
        datetime.fromisoformat(b["start"]): (b["total"], b["succeeded"], b["failed"])
        for b in week["buckets"]
        if b["total"]
    }
    assert counts == {
        at("2026-01-14T12:00:00"): (4, 0, 0),
        at("2026-01-15T06:00:00"): (2, 1, 1),
        at("2026-01-15T12:00:00"): (2, 0, 0),
    }


async def test_activity_filters_by_endpoint(client, clock, make_endpoint, fire):
    clock.now = NOW
    first = await make_endpoint(url="https://one.example.com/")
    await fire()
    await make_endpoint(url="https://two.example.com/")
    await fire()

    def total(activity) -> int:
        return sum(b["total"] for b in activity["buckets"])

    url = "/api/deliveries/activity"
    assert total((await client.get(url)).json()) == 3
    assert total((await client.get(url, params={"endpoint_id": first["id"]})).json()) == 2
    assert total((await client.get(url, params={"endpoint_id": "ep_nope"})).json()) == 0


async def test_activity_rejects_an_unknown_range(client):
    r = await client.get("/api/deliveries/activity", params={"range": "1y"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"
