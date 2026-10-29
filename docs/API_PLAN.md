# API build plan — `apps/api`

The design (data model, retry policy, signing, uniqueness, live view) lives in
[PLAN.md](PLAN.md). This doc is the build order for the backend: what goes where, in which
order, and which tests land with each step. Budget: ~3 hours.

## What we're building

A FastAPI service over SQLite that:

1. stores **endpoints** (URL + subscribed event types + a signing secret shown once);
2. accepts **events** with an `Idempotency-Key`, and in the same transaction fans them out
   into one **delivery** row per enabled, subscribed endpoint (transactional outbox);
3. runs an in-process **worker** that atomically claims due deliveries, signs and POSTs them,
   logs every **attempt**, and reschedules failures with exponential backoff + jitter until
   success or `failed`;
4. lets a failed delivery be **replayed** (same delivery row, same event id, attempts continue);
5. pushes every delivery state change over **SSE** so the dashboard stays live;
6. ships **mock receivers** (`ok`, `fail`, `flaky`, `slow`, `reject`) to demo and test each path.

## Module layout

```
app/
  main.py            app factory, lifespan (create tables, start/stop worker), routers, errors
  config.py          settings: db url, retry base/cap/max attempts, lease, timeouts, tolerance
  db.py              async engine + session; SQLite WAL + busy_timeout; create_all (no Alembic)
  models.py          Endpoint, Event, Delivery, DeliveryAttempt (+ unique constraints)
  schemas.py         Pydantic request/response models (source of the OpenAPI contract)
  ids.py             prefixed ids: ep_, evt_, dlv_, att_
  errors.py          ApiError + handlers → {"error": {"code", "message"}} for every failure
  event_types.py     catalogue + sample payloads
  signing.py         generate_secret(), sign(), verify()  — no FastAPI imports
  retry.py           pure policy: classify(response | exc) and next_delay(attempt, retry_after)
  clock.py           injectable now() so tests control time
  bus.py             in-process pub/sub (one asyncio.Queue per SSE subscriber)
  services/
    events.py        ingest(): idempotency + fan_out()
    deliveries.py    replay(), list/detail queries, summary serialisation
  worker.py          claim_due(), deliver(), run_once(), run_forever() with a wake event
  routes/            endpoints, event_types, events, deliveries, stream, mock
tests/
  conftest.py        tmp SQLite per test, app client, MockTransport + fake clock fixtures
  test_signing.py  test_retry.py  test_uniqueness.py  test_replay.py
  test_fanout.py   test_endpoints.py  test_stream.py
```

Rule of thumb: routes parse and return, services hold the logic, `worker` and `signing`
don't know about HTTP routing. That keeps the four graded behaviours testable without the app.

## Build steps

Each step is one commit and ends green (`uv run pytest`, `ruff`).

| #   | step                     | content                                                                                                                                         | tests                                                                    |
| --- | ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| 1   | Foundations              | config, db (WAL, `busy_timeout`), models + constraints, ids, error envelope (incl. validation errors), tmp-DB fixtures                           | constraint smoke test; error shape on a 404 and a 422                    |
| 2   | Signing                  | `whsec_` secret generation, `sign(secret, msg_id, ts, body)`, `verify(secret, headers, body, tolerance)` with `hmac.compare_digest`             | round-trip; tampered body, wrong secret, stale and future timestamp fail |
| 3   | Endpoints                | `GET/POST /api/endpoints`, `PATCH /{id}` (enabled, event types); secret only in the create response; URL + known event types validated          | secret absent from list; unknown event type → 422                        |
| 4   | Events + fan-out         | `GET /api/event-types`, `POST /api/events`; envelope body serialised **once** and stored, so every attempt sends identical bytes                | see Uniqueness below; only enabled + subscribed endpoints get rows       |
| 5   | Retry policy + worker    | `retry.py` pure functions; `worker.run_once(transport, clock)`: claim → send (semaphore, 10 s timeout) → record attempt + new state atomically   | see Retry below; `run_once` used directly, no sleeps                     |
| 6   | Deliveries API + replay  | `GET /api/deliveries?status=&endpoint_id=`, `GET /{id}` (payload + attempts), `POST /{id}/replay` (only from `failed`, else 409)                  | see Replay below                                                         |
| 7   | Live stream              | `bus.publish(delivery_summary)` after every transition; `GET /api/stream` as `text/event-stream`, heartbeat comment every 15 s                    | subscriber receives `pending → in_progress → succeeded` in order         |
| 8   | Mock receivers + wiring  | `/mock/{ok,fail,flaky,slow,reject}`; flaky fails N times per `webhook-id`; receivers verify the signature; worker started in lifespan            | end-to-end: create endpoint on `/mock/flaky` → fire → succeeded          |
| 9   | Contract + docs          | `pnpm gen:api` (OpenAPI → `schema.d.ts`), README API section, signature-verification snippet                                                     | —                                                                        |

## Design details settled for the build

**Idempotency on the way in.** `Idempotency-Key` is optional; without it every submit is a new
event. With it: insert the event and catch `IntegrityError` on the UNIQUE column (never
check-then-insert), then load the existing row. Same `payload_hash` (sha256 of canonical JSON
of `type` + `payload`) → `200 {deduplicated: true, event}` and no new deliveries. Different
hash → `422 idempotency_key_reused` (client bug; matches the IETF Idempotency-Key draft).

**Uniqueness on the way out.** `fan_out(event)` uses `INSERT … ON CONFLICT (event_id,
endpoint_id) DO NOTHING`, so calling it twice is a no-op, and the worker's claim is a single
`UPDATE … WHERE id IN (SELECT … LIMIT n) RETURNING *` (atomic in SQLite ≥ 3.35). The send
happens outside any transaction; only the claim and the result recording are transactional.

**Each attempt is signed fresh.** The body bytes are fixed at event creation, the timestamp is
the attempt's own (so a retry 10 minutes later still passes a 5-minute tolerance), and the
message id stays the same across retries and replays so receivers can dedupe.

**Retry config.** Dev defaults: base 2 s, cap 30 s, 5 attempts, full jitter (so a demo fails
over in under a minute). Tests set jitter to 0 and drive a fake clock. Lease 30 s > HTTP
timeout 10 s, so an in-flight attempt is never reclaimed while it can still finish.

**Disabled endpoints.** Disabling doesn't delete pending deliveries; the worker marks them
`failed: endpoint_disabled` at claim time, and they can be replayed after re-enabling.

## Tests proving the four graded behaviours

- **Retry** — receiver `500, 500, 200` → 3 attempts, `succeeded`, delays grow; timeouts and
  connection errors retried; `429 Retry-After` honoured; always-500 → `failed` after 5;
  `400` → `failed` after 1 (terminal); an expired lease is reclaimed and re-sent.
- **Uniqueness** — same key + same body twice → one event, deliveries unchanged,
  `deduplicated: true`; same key + different body → 422; `fan_out` twice → still one row per
  endpoint; two concurrent `run_once()` → exactly one HTTP request; replay of a succeeded
  delivery → 409.
- **Replay** — always-fail until `failed` → flip the receiver to 200 → replay → `succeeded`;
  attempt numbers continue (6, 7…), the earlier attempts are kept, `trigger = replay`.
- **Signature** — unit cases from step 2, plus the actual outgoing request captured by the
  MockTransport verifies with the secret returned at endpoint creation.

## Cut from the API slice (see PLAN.md §10 for the full list)

No auth / multi-tenancy, no migrations tool (`create_all` on startup), no pagination beyond a
limit, no `GET /events?since=` catch-up, no secret rotation, no auto-disable of failing
endpoints. Each is a next step, not a hole: the schema already leaves room for them.
