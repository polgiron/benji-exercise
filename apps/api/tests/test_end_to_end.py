"""The whole loop through the real app: the worker delivers to the app's own /mock
receivers, which verify the signature like a customer would."""

import httpx
import pytest

from app.worker import DeliveryWorker


@pytest.fixture
async def e2e_worker(app, db, settings, clock):
    w = DeliveryWorker(
        db,
        settings,
        transport=httpx.ASGITransport(app=app),
        clock=clock,
        rand=lambda: 1.0,
        on_change=app.state.on_delivery_change,
    )
    yield w
    await w.stop()


async def run(worker, clock, cycles=10):
    for _ in range(cycles):
        await worker.run_once()
        clock.advance(3600)


async def deliver_to(client, make_endpoint, fire, worker, clock, url):
    await make_endpoint(url=url)
    await fire()
    await run(worker, clock)
    [d] = (await client.get("/api/deliveries")).json()
    return (await client.get(f"/api/deliveries/{d['id']}")).json()


async def test_flaky_receiver_succeeds_on_third_attempt(
    client, make_endpoint, fire, e2e_worker, clock
):
    d = await deliver_to(
        client, make_endpoint, fire, e2e_worker, clock, "http://test/mock/flaky?fail=2"
    )
    assert d["status"] == "succeeded"
    assert [a["response_status"] for a in d["attempts"]] == [503, 503, 200]


async def test_ok_receiver_accepts_our_signature(client, make_endpoint, fire, e2e_worker, clock):
    d = await deliver_to(client, make_endpoint, fire, e2e_worker, clock, "http://test/mock/ok")
    assert d["status"] == "succeeded"
    assert d["attempts"][0]["response_body"] == "received"


async def test_reject_receiver_is_terminal(client, make_endpoint, fire, e2e_worker, clock):
    d = await deliver_to(client, make_endpoint, fire, e2e_worker, clock, "http://test/mock/reject")
    assert d["status"] == "failed"
    assert len(d["attempts"]) == 1


async def test_mock_receiver_rejects_a_bad_signature(client, make_endpoint, fire, db):
    await make_endpoint(url="http://test/mock/ok")
    await fire()
    [d] = (await client.get("/api/deliveries")).json()
    r = await client.post(
        "/mock/ok",
        content=b"{}",
        headers={
            "webhook-id": d["id"],
            "webhook-timestamp": "1",
            "webhook-signature": "v1,AAAA",
        },
    )
    assert r.status_code == 401
