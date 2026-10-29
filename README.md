# Benji — webhook notification system

Take-home for Benji's Senior Software Engineer role: customers register webhook endpoints,
events fan out to them with signed, retried, deduplicated, replayable deliveries, and a
dashboard shows every delivery live.

- **Design & trade-offs:** [docs/PLAN.md](docs/PLAN.md)
- **AI usage:** [docs/AI_USAGE.md](docs/AI_USAGE.md)
- **What's built:** [below](#whats-built) · **Next steps:** [below](#next-steps)

## What's built

### API (`apps/api`)

- **Endpoints and subscriptions.** A customer registers a URL subscribed to one or more event
  types. It can switch off the whole endpoint or a single event type. The signing secret is
  returned once, at creation.
- **Strict event catalogue.** Three event types, each with a JSON Schema checked on ingestion and
  a sample payload.
- **Idempotent ingestion.** An `Idempotency-Key` stored under a `UNIQUE` constraint, with a hash
  of the request: the same key and body is deduplicated, the same key with another body is a
  `422`. The event and its deliveries are written in one transaction.
- **Reliable delivery.** A `deliveries` table worked by an in-process worker (outbox style, no
  queue to run). Each delivery is claimed atomically under a lease, retried with exponential
  backoff and jitter (`Retry-After` honoured) up to 5 attempts, and survives a restart because
  its state lives in the database.
- **Signed delivery.** [Standard Webhooks](https://www.standardwebhooks.com/) HMAC-SHA256 over
  the id, timestamp and raw body, re-signed on every attempt.
- **Replay** of failed deliveries, keeping the same `webhook-id` so receivers can dedupe.
- **Observable.** An attempt log per delivery (status code, duration, error, response excerpt),
  counts by status, activity over time, and an SSE stream of every state change.
- **Demo tooling.** Mock receivers that verify the signature (`ok`, `fail`, `reject`, `flaky`,
  `slow`), plus Seed and Reset.

### Dashboard (`apps/dashboard`)

- **Overview.** A getting-started guide until the first delivery, a deliveries-over-time chart,
  KPIs, a status breakdown, the latest deliveries live, and the endpoints.
- **Deliveries.** A live table with status, attempts, a next-retry countdown and filters kept in
  the URL. A row expands to its payload and attempt log, and failed rows can be replayed.
- **Endpoints.** A list with an enable switch and a create dialog that shows the secret once. An
  endpoint's page has a switch per event type, its stats and its deliveries.
- **Test panel** (toggled from the header, not part of the customer's UI). Fire an event with a
  payload and idempotency key and see whether it was deduplicated. It also lists the mock
  receivers and the stream's live/reconnecting state, and has Seed and Reset.
- **How it works.** An animated walk-through of a delivery and its retries, and of what the
  signature proves to the receiver.
- **Accuracy over time.** Stream updates are written into the Vue Query cache, and only a newer
  `version` of a delivery is applied. Lists are refetched after a reconnect.
- **Async UX.** Skeletons while loading, and empty states that suggest a next action. Buttons are
  disabled while their request runs. A failed action shows a toast, and a failed load shows the
  error in place with Try again. Light and dark themes.

### A five-minute tour

1. `pnpm dev`, open http://localhost:3000, then **Seed** in the test panel (header toggle).
2. **Deliveries**: watch the live events settle, expand a failed one and **Replay** it.
3. **Endpoints**: create one on `http://localhost:8000/mock/flaky?fail=2` and copy its secret.
4. In the test panel, fire an event of a type it subscribes to. On **Deliveries**, its delivery
   fails twice, then succeeds on the third attempt. Re-submit with the same key: it is reported
   as deduplicated, and no delivery is added.
5. **How it works** for the picture of what just happened.

## Stack

|                              |                                                                                           |
| ---------------------------- | ----------------------------------------------------------------------------------------- |
| `apps/api`                   | FastAPI, SQLAlchemy 2 (async) + SQLite, httpx — managed with **uv**                       |
| `apps/dashboard`             | Nuxt 4 (SPA), TanStack Vue Query, Tailwind 4                                              |
| `packages/ui`                | shadcn-vue components + shared styles: `variables.css` (tokens), `theme.css` (light/dark) |
| `packages/utils`             | shared TS helpers (time formatting)                                                       |
| `packages/eslint-config`     | flat ESLint configs: `base`, `vue`                                                        |
| `packages/typescript-config` | `base.json`, `vue-library.json`                                                           |

Turborepo + pnpm drive both apps; the API's `package.json` scripts wrap `uv run …`.

Add a shadcn-vue component from `packages/ui`: `pnpm dlx shadcn-vue@latest add <name>`, then
export it from `packages/ui/src/index.ts`. Apps import components from `@repo/ui` and styles
with `@import '@repo/ui/styles.css';`.

## Prerequisites

- Node ≥ 22 and pnpm 10 (`corepack enable`)
- [uv](https://docs.astral.sh/uv/) (`brew install uv`) — it installs Python 3.13 itself

## Run

```bash
pnpm install
pnpm dev
```

- API: http://localhost:8000 (OpenAPI docs at `/docs`)
- Dashboard: http://localhost:3000

Run one app only with `pnpm --filter @repo/api dev` or `pnpm --filter @repo/dashboard dev`.

## Test

```bash
pnpm test
```

Runs pytest for the API and Vitest for the dashboard and utils. API tests alone:
`cd apps/api && uv run pytest`.

### Where each guarantee is proved

The worker runs one cycle at a time with an injected HTTP transport and clock, so these tests
are deterministic and never sleep.

| guarantee      | tests (`apps/api/tests/`)                                                                                                                                                                                                                                                                                               |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Retry**      | `test_retry.py`: fails twice then succeeds; ends `failed` after max attempts; timeouts and connection errors retried; 4xx terminal; 429 `Retry-After` honoured; backoff capped and jittered; expired lease reclaimed                                                                                                    |
| **Uniqueness** | `test_uniqueness.py`: same key twice → one event, no new deliveries; key order doesn't matter; same key + other payload or type → 422; concurrent submits with one key; fan-out twice → one delivery per endpoint. `test_retry.py::test_concurrent_cycles_send_once`; the `UNIQUE` constraints in `test_foundations.py` |
| **Replay**     | `test_replay.py`: failed → replayed until it succeeds; a full new series of attempts; same event and `webhook-id`; succeeded or pending → 409; paused endpoint → 409                                                                                                                                                    |
| **Signing**    | `test_signing.py`: valid signature passes; tampered body, message id or timestamp, wrong secret, stale or future timestamp fail; the outgoing request verifies with the secret from creation; retries re-sign a fresh timestamp over the same id and body                                                               |
| **End to end** | `test_end_to_end.py`: the app with its `/mock/*` receivers — flaky succeeds on the 3rd attempt, reject is terminal, a bad signature is refused                                                                                                                                                                          |
| **Live view**  | `test_stream.py` (a delivery's lifecycle over SSE); dashboard `utils/delivery-cache.test.ts` (only a newer `version` applies, every cached list and detail patched)                                                                                                                                                     |

## API

Full design: [docs/PLAN.md](docs/PLAN.md) and [docs/API_PLAN.md](docs/API_PLAN.md). Interactive
docs at http://localhost:8000/docs.

| method     | path                          | purpose                                                             |
| ---------- | ----------------------------- | ------------------------------------------------------------------- |
| GET        | `/api/event-types`            | catalogue: description, JSON Schema, sample payload                 |
| GET / POST | `/api/endpoints`              | list / create (the signing secret is returned only here)            |
| GET, PATCH | `/api/endpoints/{id}`         | read / enable, disable, change URL or event types                   |
| POST       | `/api/events`                 | publish an event (`Idempotency-Key` header), fans out               |
| GET        | `/api/events`                 | incoming event history                                              |
| GET        | `/api/deliveries`             | list, filter by `status`, `endpoint_id`, `event_id`, `event_type`   |
| GET        | `/api/deliveries/stats`       | counts by status (`endpoint_id` filter optional)                    |
| GET        | `/api/deliveries/activity`    | deliveries per time bucket (`range`, `endpoint_id`)                 |
| GET        | `/api/deliveries/{id}`        | detail: payload + attempt log                                       |
| POST       | `/api/deliveries/{id}/replay` | re-queue a failed delivery                                          |
| GET        | `/api/stream`                 | SSE: `delivery.updated` after every delivery state change           |
| POST       | `/mock/{ok,fail,reject}`      | demo receivers (verify the signature, then answer)                  |
| POST       | `/mock/flaky?fail=N`          | fails the first N requests per message, then 200                    |
| POST       | `/mock/slow?seconds=S`        | answers after S seconds (default 15, past the 10 s timeout)         |
| POST       | `/api/demo/reset`             | **wipes** endpoints, events, deliveries (event types stay)          |
| POST       | `/api/demo/seed`              | **wipes** endpoints, events, deliveries; seeds a month of demo data |

Errors always look like `{"error": {"code": "...", "message": "..."}}`.

### Try it

For a filled dashboard, use **Seed** at the top of the test panel (or
`curl -X POST localhost:8000/api/demo/seed`): it deletes everything first, then writes six
endpoints on the mock receivers, a month of their deliveries, and a few live events. **Reset**
next to it only empties the database.

```bash
curl -s localhost:8000/api/endpoints -H 'content-type: application/json' \
  -d '{"url": "http://localhost:8000/mock/flaky?fail=2", "event_types": ["campaign_updated"]}'

curl -s localhost:8000/api/events -H 'content-type: application/json' -H 'Idempotency-Key: demo-1' \
  -d '{"event_type": "campaign_updated", "payload": {"campaign_id": "cmp_7", "name": "Double points",
       "status": "active", "starts_at": "2026-11-01T00:00:00Z"}}'

curl -sN localhost:8000/api/stream   # watch it go pending → in_progress → pending → … → succeeded
```

Run the second command again: same key, same body → `200 {"deduplicated": true}` and no new
delivery. Same key, different body → `422 idempotency_key_reused`.

### Delivery guarantees

- **At least once.** Only a 2xx is success. Timeouts, network errors, 408/425/429 and 5xx are
  retried with exponential backoff and jitter (`Retry-After` honoured), up to 5 attempts, then
  `failed`. Other 4xx are terminal. Failed deliveries can be replayed.
- **Once per endpoint.** `UNIQUE(event_id, endpoint_id)`, and each delivery is claimed
  atomically by one worker at a time. If we crash between the receiver's 200 and recording it,
  it is sent again: receivers dedupe on `webhook-id`, which never changes for a delivery.
- **No ordering guarantee.** Use the envelope's `created_at`.

### Verifying a webhook (receiver side)

Signatures follow [Standard Webhooks](https://www.standardwebhooks.com/), so any of its libraries
work. With ours (`apps/api/app/signing.py`, no dependencies beyond the standard library):

```python
from app.signing import InvalidSignature, verify

def handle(raw_body: bytes, headers, secret: str):
    try:
        verify(secret, headers, raw_body)  # raw bytes, before json.loads; 5-minute tolerance
    except InvalidSignature:
        return 401
    ...
```

### Configuration

Environment variables (prefix `BENJI_`, or `apps/api/.env`): `DATABASE_URL`,
`RETRY_BASE_SECONDS` (2), `RETRY_CAP_SECONDS` (30), `MAX_ATTEMPTS` (5), `HTTP_TIMEOUT_SECONDS`
(10), `LEASE_SECONDS` (30), `MOCK_RECEIVERS` (true). Delays are seconds so a demo settles in
under a minute. The SQLite file is `apps/api/benji.db`; delete it to start fresh.

## Other scripts

| command          | does                                                                                |
| ---------------- | ----------------------------------------------------------------------------------- |
| `pnpm typecheck` | `nuxt typecheck`, `vue-tsc` (ui), `tsc` (utils)                                     |
| `pnpm lint`      | ruff (API), ESLint (dashboard, ui, utils)                                           |
| `pnpm format`    | Prettier on everything but the API (ruff formats Python)                            |
| `pnpm gen:api`   | dumps FastAPI's OpenAPI schema and regenerates `apps/dashboard/app/api/schema.d.ts` |

## Next steps

What was cut to fit a day, and what comes next. The reasoning behind each cut is in
[docs/PLAN.md §10](docs/PLAN.md#10-scope-cuts-deliberate-and-next-steps).

**Before production**

Shortcuts this demo takes that a real system couldn't:

- **Auth.** Today anyone can call the API, and everything belongs to one customer. Each customer
  would get an API key and only see their own endpoints and deliveries.
- **Secret encryption.** Signing secrets sit in the database as plain text. They should be
  encrypted, and changing a secret should keep the old one working for a while.
- **Postgres and separate workers.** SQLite allows one write at a time, and the worker runs
  inside the API process. With Postgres, several worker processes can share the queue without
  picking the same delivery.
- **Durable stream.** Live updates aren't stored anywhere, so after a reconnect the dashboard
  refetches everything. A stored stream would let it resume where it stopped.
- **Pagination.** Lists stop at 500 rows. Pages would let you browse all of them.
- **Retention.** Payloads and attempt logs are kept forever. Old ones should be deleted after a
  set time.

**Product**

- **Auto-disable an endpoint after N consecutive failures** and tell the customer, plus **bulk
  replay** ("replay all failed for this endpoint"): break an endpoint, fix it, re-enable, replay.
- **"Send test event" on an endpoint's page**, as Stripe and Svix offer.
- **Event-type versioning**: ship a `v2` of one type, pin a version on each subscription, and
  down-convert the payload for subscribers still on `v1`. The catalogue already promises that
  removing, renaming or retyping a field needs a new version.
- **An Events page** grouping deliveries by event (`GET /api/events` exists), and editing an
  endpoint's URL from the dashboard (`PATCH` exists; it needs a confirm step).

**Quality**

- **End-to-end tests** with Playwright: create an endpoint → fire an event → see it succeed.
