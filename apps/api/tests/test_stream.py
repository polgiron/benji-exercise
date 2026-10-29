import asyncio
import json

from app.bus import Bus
from app.routes.stream import event_stream


def parse(chunk: str):
    lines = dict(line.split(": ", 1) for line in chunk.strip().splitlines() if ": " in line)
    return lines.get("event"), json.loads(lines["data"]) if "data" in lines else None


async def collect(app, until):
    """Subscribe like a browser would and gather `delivery.updated` messages."""
    disconnected = asyncio.Event()
    received = []

    async def is_disconnected():
        return disconnected.is_set()

    async def read():
        async for chunk in event_stream(app.state.bus, is_disconnected, heartbeat=0.05):
            event, data = parse(chunk)
            if event == "delivery.updated":
                received.append(data)
                if until(received):
                    return

    task = asyncio.create_task(read())
    return task, received, disconnected


async def test_stream_follows_a_delivery_through_its_lifecycle(
    app, make_endpoint, fire, worker, receiver, clock
):
    receiver.respond(500, 200)
    await make_endpoint()
    task, received, _ = await collect(app, until=lambda r: r[-1]["status"] == "succeeded")
    await asyncio.sleep(0)  # let it subscribe

    await fire()
    await worker.run_once()
    clock.advance(60)
    await worker.run_once()
    await asyncio.wait_for(task, 2)

    assert [m["status"] for m in received] == [
        "pending",  # created by fan-out
        "in_progress",
        "pending",  # retry scheduled
        "in_progress",
        "succeeded",
    ]
    versions = [m["version"] for m in received]
    assert versions == sorted(versions) and len(set(versions)) == len(versions)
    assert received[2]["last_error"] == "HTTP 500"
    assert received[2]["next_attempt_at"] is not None


async def test_stream_starts_with_ready_and_sends_heartbeats():
    bus = Bus()
    stop = asyncio.Event()

    async def is_disconnected():
        return stop.is_set()

    chunks = []
    async for chunk in event_stream(bus, is_disconnected, heartbeat=0.01):
        chunks.append(chunk)
        if chunk.startswith(": ping"):
            stop.set()
    assert chunks[0].startswith("retry:")
    assert parse(chunks[1])[0] == "ready"
    assert bus.subscriber_count == 0  # unsubscribed on disconnect


async def test_slow_subscriber_is_dropped_not_blocking():
    bus = Bus(queue_size=2)
    async with bus.subscribe() as queue:
        for i in range(5):
            bus.publish("delivery.updated", {"i": i})
        assert bus.subscriber_count == 0
        assert queue.get_nowait() == ("delivery.updated", {"i": 1})
        assert queue.get_nowait() is None  # end of stream: reconnect and refetch
