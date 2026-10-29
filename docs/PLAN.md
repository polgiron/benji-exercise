# Implementation plan — webhook notification system

Benji take-home. Budget: one working day. Runs locally, no external infrastructure.
Goal: a small, correct, well-tested vertical slice rather than a sprawling system.
Backend build order: [API_PLAN.md](API_PLAN.md).

## 1. Architecture at a glance

```
┌──────────── apps/dashboard (Nuxt, SPA) ────────────┐
│ UI components ── composables ── API layer (fetch)  │
│                  TanStack Vue Query cache  ◄── SSE │
└───────────────────────┬────────────────────▲───────┘
                  REST (JSON)           SSE /api/stream
┌───────────────────────▼────────────────────┴───────┐
│ apps/api (FastAPI + SQLite)                        │
│  routes ─► services (fan-out, replay) ─► SQLite    │
│  delivery worker (asyncio task in lifespan)        │
│     claims due rows ─► signs ─► POSTs ─► records   │
│  in-process event bus ─► SSE subscribers           │
│  /mock/* receivers (dev only: ok / fail / flaky…)  │
└────────────────────────────────────────────────────┘
```

Monorepo: Turborepo + pnpm. `apps/api` is a uv project whose `package.json` scripts
wrap `uv run …` so `pnpm dev` / `pnpm test` drive both apps. Shared packages: `@repo/ui`
(shadcn-vue components, design tokens, light/dark theme), `@repo/utils`, `@repo/eslint-config`,
`@repo/typescript-config`.

## 2. Data model (SQLite, SQLAlchemy 2 async + aiosqlite)

| table               | key columns                                                                                                                                                               | notes                                         |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| `endpoints`         | `id`, `url`, `event_types` (JSON), `secret`, `enabled`, `created_at`                                                                                                      | single implicit customer (multi-tenancy cut)  |
| `events`            | `id`, `type`, `payload` (JSON), `idempotency_key` **UNIQUE**, `payload_hash`, `created_at`                                                                                | dedup of re-submits                           |
| `deliveries`        | `id`, `event_id`, `endpoint_id`, `status`, `attempt_count`, `next_attempt_at`, `lease_expires_at`, `last_error`, `version`, timestamps; **UNIQUE(event_id, endpoint_id)** | one row = one (event, endpoint) pair, forever |
| `delivery_attempts` | `id`, `delivery_id`, `number`, `started_at`, `duration_ms`, `response_status`, `response_body` (truncated 2 KB), `error`, `trigger` (`auto` / `replay`)                   | append-only history                           |

Status machine: `pending → in_progress → succeeded | pending (retry scheduled) | failed`,
and `failed → pending` via Replay. `version` increments on every change (used by the UI, §6).

IDs are prefixed (`ep_`, `evt_`, `dlv_`, `att_`) for readability in logs and the UI.

## 3. Delivery pipeline

**Fan-out (transactional outbox).** `POST /api/events` inserts the event and one `deliveries`
row per _enabled_ endpoint subscribed to its type, in the same transaction. Nothing is sent
from the request path; if the process dies after commit, the worker still finds the rows.

**Worker.** One asyncio task started in FastAPI's lifespan. Every ~500 ms (or immediately when
woken by a new event) it:

1. Claims due work atomically (expired leases make crashed in-flight attempts recoverable):

   ```sql
   UPDATE deliveries
   SET status = 'in_progress', lease_expires_at = :now + 30s, version = version + 1
   WHERE id IN (
     SELECT id FROM deliveries
     WHERE (status = 'pending' AND next_attempt_at <= :now)
        OR (status = 'in_progress' AND lease_expires_at < :now)
     LIMIT 10
   )
   RETURNING *
   ```

2. Sends each claimed delivery concurrently (bounded semaphore) with `httpx.AsyncClient`,
   10 s timeout, signed headers (§4).
3. Records a `delivery_attempts` row and the outcome in one transaction, then publishes the
   new delivery state on the in-process bus.

**Retry policy — why this mechanism.** A DB-backed queue polled by an in-process worker gives
durability (state survives restarts), inspectability (every attempt is a row the UI reads) and
replay for free, with zero infrastructure. Redis/Celery/SQS would add moving parts the exercise
explicitly rules out. The claim query is written so the scale-out path is a drop-in change:
Postgres with `FOR UPDATE SKIP LOCKED` and N worker processes.

- Retryable: network errors, timeouts, `408`, `429` (honouring `Retry-After`), `5xx`.
- Terminal: other `4xx` — the receiver explicitly rejected the request; retrying will not
  help, but Replay can once they fix it.
- Backoff: exponential with full jitter, `base * 2^(n-1)`, capped; max 5 attempts, then
  `failed`. Base/cap are config: seconds in dev so the demo is watchable, minutes→hours in prod.
- Endpoint disabled while a delivery is pending → marked `failed` ("endpoint disabled") at
  claim time; replayable after re-enabling.

## 4. Authenticated delivery

Follows the [Standard Webhooks](https://www.standardwebhooks.com/) scheme so recipients can use
off-the-shelf verifiers:

- Secret: `whsec_` + 32 random bytes (base64), generated at endpoint creation, returned
  **only** in the create response; never by any GET.
- Headers: `webhook-id` (delivery id — stable across retries), `webhook-timestamp` (unix s),
  `webhook-signature: v1,<base64(HMAC-SHA256(secret, "{id}.{timestamp}.{raw_body}"))>`.
- The timestamp is signed, so receivers reject stale messages (5 min tolerance) → no replay
  attacks. Verification uses constant-time comparison.
- `app/signing.py` exposes `sign()` and `verify()`; the mock receivers verify with it, which
  doubles as the reference snippet in the README.

## 5. Uniqueness guarantees (and their honest limit)

1. **Event dedup**: `Idempotency-Key` header on `POST /api/events` (UNIQUE column). A re-submit
   returns `200 {deduplicated: true, event}` instead of `201`; same key + different payload →
   `422` (client bug, as in the IETF Idempotency-Key draft). The dashboard shows the deduplicated result explicitly.
2. **One delivery row per (event, endpoint)**: DB unique constraint — can't be bypassed by bugs.
3. **No concurrent sends**: the atomic claim means a delivery is held by one worker at a time.
4. **Never re-sent after success**: Replay is only allowed from `failed` (`409` otherwise);
   it reuses the same delivery row, appending attempts.
5. **Residual case**: HTTP can't give exactly-once. If we crash after the receiver got the
   request but before recording it, the lease expires and we retry → receiver sees it twice.
   That's why `webhook-id` is stable: receivers dedupe on it. Documented, not hidden.

## 6. Live delivery view

- `GET /api/stream` (SSE) pushes `delivery.updated` with the full delivery summary after
  every state change (created, claimed, attempt recorded, replayed). Simple, one-way,
  auto-reconnecting, no extra dependency — WebSockets would be overkill.
- The client writes these into TanStack Query's cache via `setQueryData` (list and detail),
  so every view of a delivery updates together.
- **Staying accurate over time** (the hard part):
  - updates carry `version`; the cache only applies an update with a higher version
    (out-of-order or stale messages can't regress a row);
  - REST is the source of truth, SSE is an accelerator: on (re)connect and on tab refocus,
    the deliveries queries are invalidated and refetched, covering anything missed while
    disconnected (the in-memory bus has no backlog);
  - "next retry in Xs" is derived from `next_attempt_at` with a ticking clock, not pushed.
- A connection indicator shows live / reconnecting.

## 7. API surface

| method     | path                                   | purpose                                         |
| ---------- | -------------------------------------- | ----------------------------------------------- |
| GET        | `/api/event-types`                     | catalogue (+ sample payloads for the test form) |
| GET / POST | `/api/endpoints`                       | list / create (create returns the secret once)  |
| PATCH      | `/api/endpoints/{id}`                  | enable / disable                                |
| POST       | `/api/events`                          | fire event (`Idempotency-Key` header)           |
| GET        | `/api/deliveries?status=&endpoint_id=` | list, newest first                              |
| GET        | `/api/deliveries/{id}`                 | detail: payload + attempts                      |
| POST       | `/api/deliveries/{id}/replay`          | failed → pending                                |
| GET        | `/api/stream`                          | SSE                                             |
| POST       | `/mock/{ok,fail,flaky,slow,reject}`    | dev receivers for demoing every path            |

Errors share one shape: `{"error": {"code": "...", "message": "..."}}` (exception handlers
also wrap validation errors), so the dashboard has one error path.

## 8. Dashboard

Nuxt with `ssr: false`, Tailwind, components from `@repo/ui` (shadcn-vue). Layers kept apart:

- `app/api/` — typed fetch functions only (types generated from FastAPI's OpenAPI schema with
  `openapi-typescript`: one contract, `pnpm gen:api`).
- `app/composables/` — Vue Query hooks (`useDeliveries`, `useReplayDelivery`, …) and
  `useDeliveryStream` (SSE → cache). Query keys centralised in one factory.
- `app/components/`, `app/pages/` — render only. Client-only UI state (expanded row, status
  filter) lives in components or the URL query. No Pinia.

Screens:

- **Deliveries** (home): live table — event type, endpoint, status badge, attempts
  (`2/5`), next retry countdown, updated time; status filter in the URL; expandable row with
  payload JSON and attempt log (status code, duration, error, response excerpt); Replay on
  failed rows.
- **Endpoints**: list with event-type chips and an enable/disable switch; create dialog
  (URL + event types multi-select, mock-receiver presets) that reveals the secret once with a
  copy button and a "you won't see this again" warning.
- **Fire test event** (sheet available everywhere): type select, JSON payload editor
  prefilled from the sample, idempotency key (auto-generated, with "re-submit same key");
  result banner: "created, N deliveries" vs "deduplicated — already received as evt_…".
- Async UX: skeletons for loading, empty states with a next action, buttons disabled and
  spinning while their mutation is in flight, toasts for errors from the single error shape.

## 9. Testing

Backend (pytest + pytest-asyncio, in-memory/tmp SQLite, httpx `ASGITransport`). The worker
takes an injectable HTTP transport and clock, and exposes `run_once()`, so tests are
deterministic and never sleep.

- **Signature**: sign/verify round-trip; tampered body, wrong secret, stale timestamp fail;
  an actual outgoing request verifies with the endpoint's secret from creation.
- **Retry**: 500 → `pending` with backoff and attempt recorded → 200 → `succeeded`;
  timeouts/connection errors retried; `429 Retry-After` honoured; max attempts → `failed`;
  `400` terminal; expired lease reclaimed.
- **Uniqueness**: same idempotency key twice → one event, one delivery per endpoint,
  `deduplicated: true`; different payload same key → 422; unique constraint rejects a duplicate
  delivery insert; two concurrent `run_once()` send once; replay of a succeeded delivery → 409.
- **Replay**: failed → replay → delivered; attempt history preserved and numbering continues.
- **Fan-out**: only enabled, subscribed endpoints get deliveries.

Frontend (Vitest): the SSE cache-merge logic (version ordering, list + detail updates) and
the error normalisation in the API layer — the parts with real logic.

## 10. Scope cuts (deliberate) and next steps

| cut                                          | why OK for now                   | next step                                                        |
| -------------------------------------------- | -------------------------------- | ---------------------------------------------------------------- |
| Auth & multi-tenancy                         | one implicit customer            | API keys → `customer_id` on every table                          |
| Secrets stored in plaintext                  | local demo                       | encrypt at rest (KMS), rotation with overlap (two valid secrets) |
| SQLite + single in-process worker            | no infra allowed                 | Postgres + `SKIP LOCKED`, separate worker processes              |
| In-memory SSE bus, no backlog                | refetch-on-reconnect covers gaps | Postgres `LISTEN/NOTIFY` or Redis pub/sub; `Last-Event-ID`       |
| No pagination beyond a limit                 | demo volumes                     | cursor pagination on `(created_at, id)`                          |
| No per-endpoint rate limit / circuit breaker | —                                | auto-disable after N consecutive failures, notify customer       |
| No e2e tests                                 | time                             | Playwright: create endpoint → fire → see succeeded               |
| No retention                                 | —                                | TTL on attempts/payloads                                         |
| Bulk replay                                  | —                                | "replay all failed for endpoint"                                 |

## 11. Day plan

| slot      | work                                                                                    |
| --------- | --------------------------------------------------------------------------------------- |
| 0:00–0:45 | plan (this doc), monorepo scaffold, tooling                                             |
| 0:45–3:30 | API: models, fan-out, worker, signing, replay, SSE, mock receivers — with tests as I go |
| 3:30–6:30 | dashboard: API layer + type gen, endpoints, fire event, live deliveries                 |
| 6:30–7:30 | polish async states, README, AI-usage note, final test pass                             |

## 12. AI usage

Planned and built with Claude Code; the handover brief, this plan and the chat trail are
kept in `docs/` (see `docs/AI_USAGE.md`).
