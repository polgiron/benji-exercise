"""Replayable failures: a failed delivery can be re-run, with its history kept."""

from app.models import DeliveryStatus
from tests.helpers import attempts, only_delivery


async def failed_delivery(make_endpoint, fire, receiver, drain, db):
    await make_endpoint()
    await fire()
    receiver.respond(500)
    await drain()
    d = await only_delivery(db)
    assert d.status == DeliveryStatus.failed
    return d


async def test_replay_failed_delivery_until_it_succeeds(
    client, db, make_endpoint, fire, receiver, drain, settings
):
    d = await failed_delivery(make_endpoint, fire, receiver, drain, db)
    receiver.respond(200)  # the customer fixed their server

    r = await client.post(f"/api/deliveries/{d.id}/replay")
    assert r.status_code == 200
    assert r.json()["status"] == "pending"
    assert r.json()["version"] > d.version
    await drain()

    d = await only_delivery(db)
    assert d.status == DeliveryStatus.succeeded
    history = await attempts(db, d.id)
    n = settings.max_attempts
    assert [a.number for a in history] == list(range(1, n + 2))  # numbering continues
    assert [a.trigger for a in history] == ["auto"] * n + ["replay"]
    assert [a.response_status for a in history] == [500] * n + [200]


async def test_replay_gets_a_full_new_series_of_attempts(
    client, db, make_endpoint, fire, receiver, drain, settings
):
    d = await failed_delivery(make_endpoint, fire, receiver, drain, db)
    await client.post(f"/api/deliveries/{d.id}/replay")
    await drain()  # still failing

    d = await only_delivery(db)
    assert d.status == DeliveryStatus.failed
    assert d.attempt_count == 2 * settings.max_attempts


async def test_replay_keeps_the_same_event_and_message_id(
    client, db, make_endpoint, fire, receiver, drain
):
    d = await failed_delivery(make_endpoint, fire, receiver, drain, db)
    receiver.respond(200)
    await client.post(f"/api/deliveries/{d.id}/replay")
    await drain()

    ids = {r.headers["webhook-id"] for r in receiver.requests}
    bodies = {r.content for r in receiver.requests}
    assert ids == {d.id}
    assert len(bodies) == 1


async def test_succeeded_delivery_cannot_be_replayed(client, db, make_endpoint, fire, drain):
    await make_endpoint()
    await fire()
    await drain()
    d = await only_delivery(db)

    r = await client.post(f"/api/deliveries/{d.id}/replay")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "not_replayable"


async def test_pending_delivery_cannot_be_replayed(client, db, make_endpoint, fire):
    await make_endpoint()
    await fire()
    d = await only_delivery(db)
    r = await client.post(f"/api/deliveries/{d.id}/replay")
    assert r.status_code == 409


async def test_replay_needs_the_endpoint_enabled(client, db, make_endpoint, fire, worker):
    ep = await make_endpoint()
    await fire()
    await client.patch(f"/api/endpoints/{ep['id']}", json={"enabled": False})
    await worker.run_once()
    d = await only_delivery(db)

    r = await client.post(f"/api/deliveries/{d.id}/replay")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "endpoint_disabled"

    await client.patch(f"/api/endpoints/{ep['id']}", json={"enabled": True})
    assert (await client.post(f"/api/deliveries/{d.id}/replay")).status_code == 200


async def test_replay_unknown_delivery(client):
    assert (await client.post("/api/deliveries/dlv_nope/replay")).status_code == 404
