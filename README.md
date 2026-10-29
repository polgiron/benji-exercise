# Benji — webhook notification system

Take-home for Benji's Senior Software Engineer role: customers register webhook endpoints,
events fan out to them with signed, retried, deduplicated, replayable deliveries, and a
dashboard shows every delivery live.

- **Design & trade-offs:** [docs/PLAN.md](docs/PLAN.md)
- **AI usage:** [docs/AI_USAGE.md](docs/AI_USAGE.md)

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
| POST       | `/api/demo/seed`              | **wipes** endpoints, events, deliveries; seeds a month of demo data |

Errors always look like `{"error": {"code": "...", "message": "..."}}`.

### Try it

For a filled dashboard, use **Reset and seed…** at the top of the test panel (or
`curl -X POST localhost:8000/api/demo/seed`): it deletes everything first, then writes six
endpoints on the mock receivers, a month of their deliveries, and a few live events.

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
