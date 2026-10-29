# Benji — webhook notification system

When something happens at Benji (a member earns points, a campaign changes), a customer's own
systems want to know right away. This project tells them with a **webhook**: an HTTP request
sent to a URL the customer registered. It makes sure every webhook arrives, proves it really
came from Benji, never sends the same one twice, lets you resend the ones that failed, and
shows all of it live in a dashboard.

It is a take-home exercise for Benji's Senior Software Engineer role.

- **Why it is built this way:** [docs/PLAN.md](docs/PLAN.md)
- **How AI was used:** [docs/AI_USAGE.md](docs/AI_USAGE.md)

**Words used below**

- **Event:** something that happened, like "campaign updated", with its details as JSON.
- **Endpoint:** a URL a customer registered, with the kinds of event it wants to receive.
- **Delivery:** one event sent to one endpoint. One event becomes as many deliveries as there
  are endpoints that want it.
- **Attempt:** one try at sending a delivery. A delivery can take several.

## Run it

You need Node 22 or later with pnpm 10 (`corepack enable`), and
[uv](https://docs.astral.sh/uv/) (`brew install uv`), which installs Python by itself.

```bash
pnpm install
pnpm dev
```

- Dashboard: http://localhost:3000
- API: http://localhost:8000, with interactive docs at http://localhost:8000/docs

To run one app only: `pnpm --filter @repo/api dev` or `pnpm --filter @repo/dashboard dev`.

## What's built

### A five-minute tour

1. Run it, open http://localhost:3000, open the test panel from the header and click **Seed**.
   It fills the app with a month of example data.
2. **Deliveries**: watch the new events settle. Expand a failed one to see each attempt, then
   **Replay** it.
3. **Endpoints**: create one with the URL `http://localhost:8000/mock/flaky?fail=2`, a fake
   receiver that fails twice before it accepts. Copy the secret: it is shown only once.
4. In the test panel, send an event of a kind that endpoint wants. On **Deliveries**, its
   delivery fails twice, then succeeds on the third attempt. Send it again with the same key:
   the panel says it was a duplicate, and nothing new is sent.
5. **How it works** shows what just happened, step by step.

### The API (`apps/api`)

- **Endpoints.** A customer registers a URL and picks which kinds of event it wants. They can
  pause the whole endpoint or a single kind of event. At creation they get a secret key to check
  our signatures. It is shown only that once.
- **Three kinds of event**: reward transaction created, campaign updated, member account linked.
  Each has a strict format, and an event that doesn't match it is refused.
- **No duplicate events.** Whoever sends us an event attaches a key of their choice (the
  `Idempotency-Key` header). If the same event arrives again with the same key, say after a
  network glitch, we recognise it and send nothing new. The same key with different content is
  refused as an error.
- **Deliveries are never lost.** Each delivery is saved in the database before it is sent, and a
  loop running inside the API sends whatever is due. If the receiver is down or too slow, we try
  again later, waiting longer each time: up to 2 s, then 4 s, 8 s… and never more than 30 s. Each
  wait is cut by a random amount, so receivers that failed together aren't all retried at the
  same moment. After 5 attempts the delivery is marked failed. If the
  receiver asks us to wait a given time, we do. Restarting the API loses nothing.
- **Signed.** Every request carries a signature made from the endpoint's secret and the content,
  following the [Standard Webhooks](https://www.standardwebhooks.com/) spec. The receiver
  recomputes it to check that the request came from us, wasn't changed and is recent.
- **Replay.** A failed delivery can be sent again once the customer has fixed their server. It
  keeps the same id, so the receiver can tell it's the same message.
- **Everything is visible.** Each attempt is recorded: the response code, how long it took, the
  error, and the start of the response. There are counts by status, activity over time, and a
  live feed of every change that the dashboard listens to.
- **Demo tools.** Fake receivers inside the API check the signature, then answer: always OK,
  always an error, a refusal, fail the first N times, or too slow. **Seed** fills the database
  with example data and **Reset** empties it.

### The dashboard (`apps/dashboard`)

- **Overview.** A getting-started guide until the first delivery, a chart of deliveries over
  time, key numbers, a breakdown by status, the latest deliveries live, and the endpoints.
- **Deliveries.** A live table: status, attempts so far, a countdown to the next retry. Filters
  are kept in the URL, so a filtered view can be shared. A row opens to show the event's content
  and every attempt, and failed rows can be replayed.
- **Endpoints.** The list, with a switch to pause each one, and a form to create one that shows
  the secret once. Each endpoint has its own page with a switch per kind of event, its numbers
  and its deliveries.
- **Test panel.** Opened from the header, and not part of what a customer would see. Send an
  event with the content and key you choose, and see whether it was a duplicate. It also lists
  the fake receivers, shows whether the live feed is connected, and has Seed and Reset.
- **How it works.** An animated walk-through of a delivery and its retries, and of what the
  signature proves to the receiver.
- **Stays accurate.** Changes arrive live and update the screen in place. An update that arrives
  late never overwrites a newer one. If the live connection drops, the dashboard reloads
  everything once it's back.
- **Waiting and errors.** Placeholders while a page loads, and empty pages that say what to do
  next. Buttons are disabled while they work. A failed action shows a short message, and a page
  that fails to load says so with a **Try again** button. Light and dark themes.

## Tests

```bash
pnpm test
```

This runs the API tests (pytest) and the dashboard and utils tests (Vitest). API tests alone:
`cd apps/api && uv run pytest`.

The tests control the clock and fake the network, so they are fast and never wait. Where each
promise is checked (files in `apps/api/tests/` unless noted):

- **Retries** (`test_retry.py`): a receiver that fails twice then works. Giving up after the last
  attempt. Timeouts and lost connections are retried, refusals (4xx) are not. "Wait N seconds"
  answers are respected, and waits grow but stay capped. A delivery left half-sent by a crashed
  loop is picked up again.
- **No duplicates** (`test_uniqueness.py`): the same key twice makes one event. The same key with
  different content is refused. Two identical requests at the same moment make one event. An
  event never makes two deliveries for the same endpoint. Two sending loops running at once send
  a delivery only once (`test_retry.py::test_concurrent_cycles_send_once`).
- **Replay** (`test_replay.py`): a failed delivery is replayed until it succeeds, with a fresh set
  of attempts and the same id. A delivery that succeeded, is still pending, or whose endpoint is
  paused can't be replayed.
- **Signatures** (`test_signing.py`): a valid signature passes. Changed content, id or time, the
  wrong secret, or a time too old or in the future all fail. The requests we send verify with the
  secret given at creation, and each retry is signed again with a fresh time.
- **End to end** (`test_end_to_end.py`): the running app against its fake receivers.
- **Live view** (`test_stream.py`, and the dashboard's `utils/delivery-cache.test.ts`): a
  delivery's changes reach the live feed, and an older update never overwrites a newer one.

## Using the API

The full design is in [docs/PLAN.md](docs/PLAN.md) and [docs/API_PLAN.md](docs/API_PLAN.md).
You can try every call from http://localhost:8000/docs.

| call                               | what it does                                                                 |
| ---------------------------------- | ---------------------------------------------------------------------------- |
| `GET /api/event-types`             | The kinds of event, with their format and an example                         |
| `GET`, `POST /api/endpoints`       | List endpoints, or create one (the secret is only in this response)          |
| `GET`, `PATCH /api/endpoints/{id}` | Read one, pause or resume it, change its URL or its kinds of event           |
| `POST /api/events`                 | Send an event (with an `Idempotency-Key` header): one delivery per endpoint  |
| `GET /api/events`                  | Past events                                                                  |
| `GET /api/deliveries`              | Deliveries, filtered by `status`, `endpoint_id`, `event_id` or `event_type`  |
| `GET /api/deliveries/stats`        | How many deliveries are in each status                                       |
| `GET /api/deliveries/activity`     | Deliveries over time, for the chart                                          |
| `GET /api/deliveries/{id}`         | One delivery, with its content and every attempt                             |
| `POST /api/deliveries/{id}/replay` | Send a failed delivery again                                                 |
| `GET /api/stream`                  | The live feed: a message each time a delivery changes                        |
| `POST /mock/{ok,fail,reject}`      | Fake receivers: check the signature, then accept, error or refuse            |
| `POST /mock/flaky?fail=N`          | Fake receiver that fails the first N times for each message, then accepts    |
| `POST /mock/slow?seconds=S`        | Fake receiver that answers after S seconds (15 by default, past our timeout) |
| `POST /api/demo/reset`             | **Deletes** all endpoints, events and deliveries                             |
| `POST /api/demo/seed`              | **Deletes** everything, then adds a month of example data                    |

When something goes wrong, the answer always looks like
`{"error": {"code": "...", "message": "..."}}`.

### Try it from the terminal

```bash
# An endpoint on the receiver that fails twice
curl -s localhost:8000/api/endpoints -H 'content-type: application/json' \
  -d '{"url": "http://localhost:8000/mock/flaky?fail=2", "event_types": ["campaign_updated"]}'

# An event for it
curl -s localhost:8000/api/events -H 'content-type: application/json' -H 'Idempotency-Key: demo-1' \
  -d '{"event_type": "campaign_updated", "payload": {"campaign_id": "cmp_7", "name": "Double points",
       "status": "active", "starts_at": "2026-11-01T00:00:00Z"}}'

# The live feed: pending → in_progress → pending (waiting to retry) → … → succeeded
curl -sN localhost:8000/api/stream
```

Send the event again with the same key and content: the answer is
`200 {"deduplicated": true}`, and nothing new is sent. Same key, different content:
`422 idempotency_key_reused`.

### What a receiver can count on

- **Every webhook arrives at least once.** Only a 2xx answer counts as received. Timeouts,
  network errors, "busy" answers (408, 425, 429) and server errors (5xx) are retried, up to 5
  attempts. Any other 4xx means the receiver refused it, so we stop. Failed deliveries can be
  replayed.
- **Never twice, with one exception.** An event makes one delivery per endpoint, and only one
  sending loop works on a delivery at a time. But if we crash right after the receiver answered
  OK and before we saved that, it is sent again after the restart. Every message carries a
  `webhook-id` that never changes, so the receiver can skip one it has already handled.
- **Not in order.** Webhooks can arrive in any order. Use the `created_at` inside each message to
  sort them.

### Checking a webhook's signature (receiver side)

Any [Standard Webhooks](https://www.standardwebhooks.com/) library works. Ours is
`apps/api/app/signing.py` and only needs Python's standard library. Check the raw request body,
before turning it into JSON. A request more than 5 minutes old is refused, so a captured request
can't be sent again later by someone else.

```python
from app.signing import InvalidSignature, verify

def handle(raw_body: bytes, headers, secret: str):
    try:
        verify(secret, headers, raw_body)
    except InvalidSignature:
        return 401
    ...
```

### Settings

Set them as environment variables with a `BENJI_` prefix, or in `apps/api/.env`. The waits are
in seconds so a demo settles in under a minute. A real system would use minutes to hours.

| setting                | default                         | what it controls                                                 |
| ---------------------- | ------------------------------- | ---------------------------------------------------------------- |
| `DATABASE_URL`         | SQLite file `apps/api/benji.db` | The database. Delete the file to start fresh                     |
| `RETRY_BASE_SECONDS`   | 2                               | The first wait before a retry                                    |
| `RETRY_CAP_SECONDS`    | 30                              | The longest wait between retries                                 |
| `MAX_ATTEMPTS`         | 5                               | Attempts before a delivery is marked failed                      |
| `HTTP_TIMEOUT_SECONDS` | 10                              | How long we wait for a receiver to answer                        |
| `LEASE_SECONDS`        | 30                              | After this, a delivery stuck mid-send (crash) is picked up again |
| `MOCK_RECEIVERS`       | true                            | Turns the fake receivers and Seed on (off in a real deployment)  |

## Next steps

What was left out to fit in a day, and what would come next. The reasoning is in
[docs/PLAN.md §10](docs/PLAN.md#10-scope-cuts-deliberate-and-next-steps).

**Before production**

Shortcuts this demo takes that a real system couldn't:

- **Auth.** Today anyone can call the API, and everything belongs to one customer. Each customer
  would get an API key and only see their own endpoints and deliveries.
- **Secret encryption.** Signing secrets sit in the database as plain text. They should be
  encrypted, and changing a secret should keep the old one working for a while.
- **Postgres and separate workers.** SQLite allows one write at a time, and the sending loop runs
  inside the API process. With Postgres, several separate sending processes can share the work
  without picking the same delivery.
- **Durable live feed.** Live updates aren't stored anywhere, so after a reconnect the dashboard
  reloads everything. A stored feed would let it resume where it stopped.
- **Pagination.** Lists stop at 500 rows. Pages would let you browse all of them.
- **Retention.** Event contents and attempts are kept forever. Old ones should be deleted after a
  set time.

**Product**

- **Pause failing endpoints, resend in bulk.** After N failures in a row, pause the endpoint and
  tell the customer. Once it's fixed, resend all its failed deliveries in one click.
- **A "send a test event" button** on each endpoint's page, as Stripe and Svix have.
- **Versions of an event's format.** Today a format can only gain fields. To rename or remove
  one, we'd publish a version 2, let each endpoint pick its version, and convert messages for
  endpoints still on version 1.
- **An Events page** listing each event with its deliveries, and **changing an endpoint's URL**
  from the dashboard. The API already supports both.

**Quality**

- **Browser tests** (Playwright) that click through the app: create an endpoint, send an event,
  see it succeed.

## How the code is organised

One repository holds both apps and the code they share. pnpm and Turborepo run them together.

| folder                       | what's in it                                                                     |
| ---------------------------- | -------------------------------------------------------------------------------- |
| `apps/api`                   | The API: FastAPI, SQLAlchemy with SQLite, httpx. Python, managed with uv         |
| `apps/dashboard`             | The dashboard: Nuxt 4 (runs in the browser only), TanStack Vue Query, Tailwind 4 |
| `packages/ui`                | Shared UI components (shadcn-vue) and styles: colours, spacing, light and dark   |
| `packages/utils`             | Shared TypeScript helpers (time formatting)                                      |
| `packages/eslint-config`     | Shared lint rules                                                                |
| `packages/typescript-config` | Shared TypeScript settings                                                       |

To add a UI component, run `pnpm dlx shadcn-vue@latest add <name>` in `packages/ui`, then export
it from `packages/ui/src/index.ts`. Apps import components from `@repo/ui`, and styles with
`@import '@repo/ui/styles.css';`.

| command          | what it does                                                                              |
| ---------------- | ----------------------------------------------------------------------------------------- |
| `pnpm typecheck` | Checks types in the dashboard, ui and utils                                               |
| `pnpm lint`      | Lints everything: ruff for the API, ESLint for the rest                                   |
| `pnpm format`    | Formats everything but the API with Prettier (ruff formats Python)                        |
| `pnpm gen:api`   | Regenerates the dashboard's API types (`apps/dashboard/app/api/schema.d.ts`) from the API |
