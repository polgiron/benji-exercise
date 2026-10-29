# Dashboard build plan — `apps/dashboard`

The design lives in [PLAN.md](PLAN.md) (live view: §6, dashboard: §8) and the API contract in
[API_PLAN.md](API_PLAN.md). This doc is the build order for the dashboard: what the screens are,
how the layers split, and which checks land with each step. Budget: ~3 hours.

## Two products on one screen

The dashboard is split in two, on purpose:

- **The customer dashboard** — what a Benji customer would really get: their endpoints, the event
  types each one is subscribed to, the deliveries we sent them, and Replay. Nothing in it exists
  only for the exercise.
- **The test panel** — the tools only we need to demo the system: fire an event, re-submit with the
  same idempotency key, the mock receiver URLs. In production Benji fires events and customers only
  receive them, so these tools have no place in the customer's UI.

The test panel is a full-height card on the right, visible on every page. (Open question for later:
make it collapsible if the deliveries table runs out of width.)

## Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│ Logo   Overview · Deliveries · Endpoints                       theme │
├───────────────────────────────────────────────────┬──────────────────┤
│                                                   │  TEST PANEL      │
│  page content                                     │                  │
│                                                   │  Fire event      │
│  Overview:                                        │  Re-submit       │
│   ┌ Deliveries ──────────┐ ┌ Endpoints ─────────┐ │  Mock receivers  │
│   │ 3 pending · 1 failed │ │ 2 enabled / 3      │ │                  │
│   │ latest 5, live       │ │ url + type chips   │ │                  │
│   │            View all →│ │         View all → │ │                  │
│   └──────────────────────┘ └────────────────────┘ │                  │
│                                                   │  ● live          │
└───────────────────────────────────────────────────┴──────────────────┘
```

## Screens

**Overview** (`/`) — two widget cards, each opening its page.

- _Deliveries card_: counts by status from `GET /api/deliveries/stats` (refetched on every SSE
  status change, so it is never computed from a limited list) and the latest 5 deliveries, live.
- _Endpoints card_: enabled / total, and each endpoint's URL with its event-type chips.

**Deliveries** (`/deliveries`) — the live table.

- Columns: event type, endpoint URL, status badge, attempts (`series_attempts/max_attempts`, plus
  a replay count when > 0), next retry countdown, updated time.
- Filters (status, endpoint) live in the URL query, so a filtered view is a link.
- A row expands (Collapsible) into the payload JSON and the attempt log: number, trigger
  (auto / replay), status code, duration, error, response excerpt.
- Replay on failed rows. `not_replayable` (409) shows as a toast; the row corrects itself from SSE.
- `endpoint_disabled` as `last_error` reads as "endpoint was disabled". Replay is disabled, with
  a tooltip, while the endpoint is paused (the API would refuse it) and comes back once it is
  enabled again.
- An empty result under a filter says so, with a "Clear filters" button.

**Endpoints** (`/endpoints`) and **Endpoint** (`/endpoints/[id]`)

- List: URL, description, event-type chips, an enabled switch.
- Create dialog: URL, description, event types (checkboxes from `GET /api/event-types`). On
  success the dialog swaps to the secret: copy button, "you won't see this again" warning.
- Endpoint page: two levels of control.
  - The endpoint switch pauses everything for that URL (the secret and the URL stay the same).
  - One switch per event type subscribes or unsubscribes it (`PATCH event_types`) — e.g. keep
    "points earned", stop "points removed". It only affects future events: deliveries already
    queued still go out.
  - Its deliveries below (the deliveries table filtered by `endpoint_id`) and its stats.

**Test panel** (all pages)

- _Fire event_: event-type select, JSON payload editor prefilled from `sample_payload`, the
  `payload_schema` shown on demand, an idempotency key. Result banner: "Created evt_…,
  N deliveries" or "Deduplicated — already received as evt_…, no new deliveries". `invalid_payload`
  shows the field the API names; `idempotency_key_reused` explains the key was used for a
  different payload.
- _Idempotency key_: one key per intended action. It is regenerated when the type or payload
  changes and after a new send; **Re-submit same key** resends the last request with its key, which
  is how the dedupe becomes visible.
- _Mock receivers_: the `/mock/*` URLs with what each does and a copy button, to paste into the
  create dialog.
- _Connection_: live / reconnecting dot for the SSE stream.

## Layers

```
app/
  api/            typed fetch functions on apiFetch — endpoints.ts, event-types.ts, events.ts,
                  deliveries.ts; types from schema.d.ts only
  composables/
    query-keys.ts            one key factory per resource
    use-endpoints.ts         list, detail, create, update (mutations invalidate)
    use-event-types.ts
    use-deliveries.ts        list(filters), detail, stats, replay
    use-fire-event.ts         mutation + idempotency-key state
    use-delivery-stream.ts    EventSource → cache (see below), connection state
    use-now.ts               one shared 1 s clock for countdowns
  utils/delivery-cache.ts    pure merge functions (no Vue) — the unit-tested part
  components/
    layout/      AppHeader, TestPanel
    overview/    DeliveriesCard, EndpointsCard
    deliveries/  DeliveriesTable, DeliveryRow, AttemptLog, DeliveryStatusBadge, RetryCountdown
    endpoints/   EndpointList, CreateEndpointDialog, SecretReveal, EventTypeSwitches
    test-panel/  FireEventForm, FireEventResult, MockReceivers, ConnectionStatus
    common/      LoadError (a failed load + "Try again", used by every view)
  pages/         index.vue, deliveries.vue, endpoints/index.vue, endpoints/[id].vue
```

Components render; composables own server state; `api/` owns HTTP. No Pinia: the only client
state is the open row, the filters (URL) and the test panel's form.

## Staying accurate over time

The SSE stream is an accelerator, REST is the source of truth.

- On `ready` (first connect and every reconnect) and on tab refocus: invalidate every active
  query, so anything missed while disconnected is refetched. The bus has no backlog. While the
  API is down the stream retries every 3 s, so its reconnect is also what clears the views
  stuck on "could not reach the API" — no separate polling.
- On `delivery.updated`:
  - patch the row in every cached deliveries list that holds it, and the detail if cached,
    **only if the incoming `version` is newer**;
  - if no cached list holds that id (a new delivery), invalidate the lists instead of guessing
    where it belongs under the current filters and sort; debounce so a fan-out to 5 endpoints
    is one refetch;
  - invalidate stats when the status changed.
- The countdown is derived from `next_attempt_at` and `useNow`, never pushed.
- The detail's attempt log refetches when its row's `attempt_count` grows (the summary doesn't
  carry attempts).
- The secret from the create response stays in the dialog's local state and never enters the
  query cache; the list is refetched, not patched from that response.

## Async UX

Skeletons while loading; empty states with the next action ("No endpoints yet — create one",
"No deliveries — fire an event from the test panel"); every mutation button disabled with a
spinner while in flight. Errors all come from the one `ApiError` shape, branching on `code`
only: a failed mutation is a toast; a failed load shows its message in place with a "Try again"
button (`common/load-error.vue`).

## Build steps

Starts once PR #3 (the API) is merged. Each step ends with `pnpm typecheck`, `pnpm lint`,
`pnpm test` green, and steps 3–6 are checked in a browser against the `/mock/*` receivers.

| #   | step                     | content                                                                       | checks                                                                        |
| --- | ------------------------ | ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| 1   | Layout                   | header + nav, test panel shell, overview / deliveries / endpoints pages       | pages route; both themes read                                                 |
| 2   | API layer + keys         | `api/*.ts`, key factory, query/mutation composables                           | Vitest: a function per route builds the right request; error mapping          |
| 3   | Endpoints                | list, create dialog + secret reveal, endpoint page with both switches         | browser: create → secret once → reload → secret gone; unsubscribe a type      |
| 4   | Fire event               | form, schema, key handling, result banner, mock receivers                     | browser: fire → N deliveries; re-submit → deduplicated; bad payload → field   |
| 5   | Deliveries + live stream | table, filters in URL, expandable row, replay, `useDeliveryStream`, countdown | Vitest on `delivery-cache.ts`; browser: flaky receiver goes live to succeeded |
| 6   | Overview + polish        | the two cards with stats, empty / loading / error states                      | browser: stop the API → reconnecting; restart → caught up without refresh     |

## Tests

- `delivery-cache.ts`: newer version applies, older or equal is dropped; patching a row present in
  two filtered lists; unknown id returns "invalidate"; detail updated alongside the list.
- `useFireEvent`: the key is kept on re-submit and regenerated on change.
- API layer: `toApiError` already covered; one test per error code path the UI branches on.

## Contract nits to raise with the API

- `DeliverySummary.status` and `AttemptOut.trigger` are typed `string` in the schema. Typing them
  as the Pydantic enums would generate unions, so the badge can switch exhaustively.

## Cut, and next steps

| cut                                 | next step                                      |
| ----------------------------------- | ---------------------------------------------- |
| Collapsible / responsive test panel | toggle in the header, sheet on narrow screens  |
| Events history page (`GET /events`) | an Events page grouping deliveries by event    |
| Pagination                          | cursor pagination once the API has it          |
| Editing an endpoint's URL           | `PATCH url` is there; needs a confirm UX       |
| Bulk replay                         | "replay all failed for this endpoint"          |
| e2e tests                           | Playwright: create endpoint → fire → succeeded |
