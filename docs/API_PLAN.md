# API build plan — `apps/api`

The design (data model, retry policy, signing, uniqueness, live view) lives in
[PLAN.md](PLAN.md). This doc is the build order for the backend: what goes where, in which
order, and which tests land with each step. Budget: ~3 hours.

## What we're building, in detail

### Tables

One implicit customer for now (auth and multi-tenancy are cut), so "the user's" data is the
whole database. Every table that a customer would own gets a `customer_id` later.

1. **`event_types`** — the catalogue of events we can send. `key` (PK, e.g.
   `reward_transaction_created`, `campaign_updated`, `member_account_linked`), `description`,
   `payload_schema` (JSON Schema, the contract: strict, `additionalProperties: false`, every
   event is validated against it → `422 invalid_payload`), `sample_payload` (valid by test,
   prefills the dashboard's test form), `created_at`. Customers are told that adding a field
   is non-breaking; removing, renaming or retyping one needs a new version (not built). Seeded at startup
   (upserted from code), read-only through the API. Every other table references it by FK, so an
   unknown type can't be subscribed to or fired.
2. **`endpoints`** — the customer's subscriptions: a URL plus the event types it wants
   (an endpoint _is_ the subscription, as in Stripe). `id` (`ep_…`), `url`, `description`,
   `secret` (`whsec_…`, returned once at creation, never by a GET), `enabled`, `created_at`,
   `updated_at`.
3. **`subscriptions`** — not a separate concept, just the link rows behind an endpoint's
   list of event types (many-to-many): `endpoint_id` → endpoints, `event_type` → event_types,
   **PK(endpoint_id, event_type)**. Never exposed on its own: the API reads and writes
   `event_types: [...]` on the endpoint. Chosen over a JSON column so the FK enforces the
   catalogue and fan-out is one indexed join.
4. **`events`** — the history of incoming calls (`POST /api/events`), one row per accepted
   event. `id` (`evt_…`), `event_type` → event_types, `payload` (JSON), `body` (the exact
   envelope bytes we sign and send, `{id, type, created_at, data}`), `idempotency_key`
   **UNIQUE** (nullable), `request_hash` (sha256 of the canonical JSON of type + payload, to
   catch a key reused for a different request), `created_at`. `payload` is what the caller
   sent; `body` is what we send (signed, byte-identical on every retry). A re-submit with the same key adds no row; the response
   says `deduplicated: true` and points at the original event.
5. **`deliveries`** — one row per (event, endpoint) pair, created by fan-out in the same
   transaction as the event: the outbox. `id` (`dlv_…`), `event_id`, `endpoint_id`, `status`
   (`pending` / `in_progress` / `succeeded` / `failed`), `attempt_count`, `next_attempt_at`,
   `lease_expires_at`, `last_error`, `version` (bumped on every change, used by the live view),
   `created_at`, `updated_at`. **UNIQUE(event_id, endpoint_id)** is what makes "never delivered
   twice to the same endpoint" a database guarantee.
6. **`delivery_attempts`** — the history of outgoing calls, append-only. `id` (`att_…`),
   `delivery_id`, `number` (1, 2, 3… continuing across replays), `trigger` (`auto` / `replay`),
   `started_at`, `duration_ms`, `response_status`, `response_body` (first 2 KB), `error`
   (`timeout`, `connection_error`, …). This is what the dashboard's attempt log shows.

### Behaviour on top of the tables

7. **Signing** — every request carries `webhook-id` (stable across retries), `webhook-timestamp`
   and `webhook-signature` (HMAC-SHA256 over `id.timestamp.body`, Standard Webhooks). Signed
   fresh per attempt; a `verify()` helper ships for receivers.
8. **Delivery worker** — an asyncio task started with the app. It claims due deliveries
   atomically (`pending` → `in_progress` with a 30 s lease), POSTs them with a 10 s timeout,
   then records the attempt and the new status in one transaction.
9. **Retry policy** — 2xx = success; network errors, timeouts, 408, 429 (honouring
   `Retry-After`) and 5xx are retried with exponential backoff + full jitter; other 4xx are
   terminal. After 5 attempts → `failed`. Delays are seconds in dev so the demo is watchable.
10. **Replay** — `failed` → `pending` on the same delivery row, same event id; new attempts are
    appended with `trigger = replay`. Replaying anything else is a 409.
11. **Live stream** — `GET /api/stream` (SSE) pushes the delivery summary after every status
    change; the dashboard writes it into its query cache and refetches on reconnect.
12. **Mock receivers** — `/mock/ok`, `/fail`, `/flaky?fail=N`, `/slow`, `/reject`, which verify
    the signature like a real customer would. Used by the demo and the end-to-end test.
13. **One error shape** — `{"error": {"code", "message"}}` for every failure, validation
    included, so the dashboard has a single error path.

### API routes

| method     | path                          | purpose                                               |
| ---------- | ----------------------------- | ----------------------------------------------------- |
| GET        | `/api/event-types`            | the catalogue, with sample payloads                   |
| GET / POST | `/api/endpoints`              | list / create (create returns the secret once)        |
| PATCH      | `/api/endpoints/{id}`         | enable / disable, change subscribed event types       |
| POST       | `/api/events`                 | fire an event (`Idempotency-Key` header)              |
| GET        | `/api/events`                 | incoming call history, newest first                   |
| GET        | `/api/deliveries`             | list, filter by `status` / `endpoint_id` / `event_id` |
| GET        | `/api/deliveries/{id}`        | detail: payload + attempt log                         |
| POST       | `/api/deliveries/{id}/replay` | re-queue a failed delivery                            |
| GET        | `/api/stream`                 | SSE                                                   |

## Module layout

```
app/
  main.py            app factory, lifespan (create tables, start/stop worker), routers, errors
  config.py          settings: db url, retry base/cap/max attempts, lease, timeouts, tolerance
  db.py              async engine + session; SQLite WAL + busy_timeout; create_all (no Alembic)
  models.py          EventType, Endpoint, Subscription, Event, Delivery, DeliveryAttempt
  schemas.py         Pydantic request/response models (source of the OpenAPI contract)
  ids.py             prefixed ids: ep_, evt_, dlv_, att_
  errors.py          ApiError + handlers → {"error": {"code", "message"}} for every failure
  event_types.py     seed data for the event_types table (keys, descriptions, samples)
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

| #   | step                    | content                                                                                                                                         | tests                                                                    |
| --- | ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| 1   | Foundations             | config, db (WAL, `busy_timeout`, FKs on), models + constraints, event-type seed, ids, error envelope (incl. validation errors), tmp-DB fixtures | constraint smoke test; error shape on a 404 and a 422                    |
| 2   | Signing                 | `whsec_` secret generation, `sign(secret, msg_id, ts, body)`, `verify(secret, headers, body, tolerance)` with `hmac.compare_digest`             | round-trip; tampered body, wrong secret, stale and future timestamp fail |
| 3   | Endpoints               | `GET/POST /api/endpoints`, `PATCH /{id}` (enabled, event types); secret only in the create response; URL + known event types validated          | secret absent from list; unknown event type → 422                        |
| 4   | Events + fan-out        | `GET /api/event-types`, `POST` / `GET /api/events`; envelope body serialised **once** and stored, so every attempt sends identical bytes        | see Uniqueness below; only enabled + subscribed endpoints get rows       |
| 5   | Retry policy + worker   | `retry.py` pure functions; `worker.run_once(transport, clock)`: claim → send (semaphore, 10 s timeout) → record attempt + new state atomically  | see Retry below; `run_once` used directly, no sleeps                     |
| 6   | Deliveries API + replay | `GET /api/deliveries?status=&endpoint_id=`, `GET /{id}` (payload + attempts), `POST /{id}/replay` (only from `failed`, else 409)                | see Replay below                                                         |
| 7   | Live stream             | `bus.publish(delivery_summary)` after every transition; `GET /api/stream` as `text/event-stream`, heartbeat comment every 15 s                  | subscriber receives `pending → in_progress → succeeded` in order         |
| 8   | Mock receivers + wiring | `/mock/{ok,fail,flaky,slow,reject}`; flaky fails N times per `webhook-id`; receivers verify the signature; worker started in lifespan           | end-to-end: create endpoint on `/mock/flaky` → fire → succeeded          |
| 9   | Contract + docs         | `pnpm gen:api` (OpenAPI → `schema.d.ts`), README API section, signature-verification snippet                                                    | —                                                                        |

## Design details settled for the build

**Idempotency on the way in.** `Idempotency-Key` is optional; without it every submit is a new
event. With it: insert the event and catch `IntegrityError` on the UNIQUE column (never
check-then-insert), then load the existing row. Same `request_hash` (sha256 of canonical JSON
— sorted keys, no whitespace — of `type` + `payload`, so key order doesn't matter) →
`200 {deduplicated: true, event}` and no new deliveries. Different hash → `422 idempotency_key_reused` (client bug; matches the IETF Idempotency-Key draft).

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
