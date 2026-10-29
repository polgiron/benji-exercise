# Subagent: Add deliveries activity endpoint

Spawned by [Local dashboard and API setup](03-local-dashboard-api.md) · `general-purpose`

## 🧑 User · 2026-10-29 09:05 UTC

Add a time-series endpoint to the FastAPI app in  (a git worktree — work only there, don't cd elsewhere, don't commit, don't touch apps/dashboard except the generated schema file). Read AGENTS.md, CLAUDE.md, and .claude/rules/api.md + .claude/rules/database.md first; follow them.

Goal: the dashboard overview gets an "Activity" area chart of deliveries over time. Build exactly this contract (the frontend is being written against it in parallel):

GET /api/deliveries/activity?range=24h|7d|30d&endpoint_id=<optional>
- `range` is a StrEnum `ActivityRange` with values "24h", "7d", "30d"; default "7d".
- Response model `DeliveryActivity`: `{ range: ActivityRange, bucket_seconds: int, buckets: list[ActivityBucket] }`
- `ActivityBucket`: `{ start: datetime, total: int, succeeded: int, failed: int }` — counts of deliveries whose `created_at` falls in [start, start+bucket); `succeeded`/`failed` by the delivery's current status; `total` counts all statuses.
- Bucketing: 24h → 24 buckets of 1h; 7d → 28 buckets of 6h; 30d → 30 buckets of 1 day. Buckets aligned to UTC boundaries of their size, the last bucket is the one containing "now", every bucket is present (zero-filled), oldest first.
- Use the app's clock abstraction (apps/api/app/clock.py) for "now" so tests can pin time. Doing the bucketing in Python over a filtered query is fine (SQLite).
- Declare the route in apps/api/app/routes/deliveries.py BEFORE `/{delivery_id}` so it isn't shadowed; put the logic in apps/api/app/services/deliveries.py next to `stats`. Match the existing style there.

Tests in apps/api/tests (see the existing deliveries tests for fixtures): zero-filled shape for each range, counts landing in the right bucket, aligned starts, endpoint_id filter, invalid range → 422. Watch each new test fail before it passes (AGENTS.md "A guard rail is only proved by breaking it").

Then run from the repo root: `pnpm gen:api` (regenerates apps/api/openapi.json and apps/dashboard/app/api/schema.d.ts — never hand-edit those), `cd apps/api && uv run pytest -q`, `uv run ruff check`, `uv run ruff format --check`. Read exit codes, not piped output. The API dev server is already running on :8000 with --reload; finish with a `curl -s 'http://localhost:8000/api/deliveries/activity?range=24h'` to see it live.

Report back: the files changed, the final response shape (paste one curl output), and the exit codes of pytest / ruff / gen:api.

## 🤖 Claude · 2026-10-29 09:05 UTC

<details><summary>5 tool calls</summary>

- `Bash` — Read rules, clock, and list API files
- `Bash` — Read deliveries route, service, schemas, test fixtures
- `Bash` — Read schemas, deliveries tests, models
- `Bash` — Inspect UTCDateTime and clock usage in events
- `Bash` — Check error handler and parametrize usage

</details>

Writing the tests first, so they fail before the endpoint exists.

<details><summary>1 tool call</summary>

- `Bash` — Add activity tests and run them red

</details>

All 7 new tests red (the path is currently captured by `/{delivery_id}` → 404). Now the implementation.

<details><summary>1 tool call</summary>

- `Bash` — Implement schemas, service, route; rerun tests

</details>

Green. Now break the two guards on purpose: the route order, and the alignment.

<details><summary>1 tool call</summary>

- `Bash` — Mutate route order and alignment, confirm red, restore

</details>

Both mutations went red where expected and are restored. Now the full suite, ruff, and codegen.

<details><summary>3 tool calls</summary>

- `Bash` — Run ruff check on the API
- `Bash` — Show first ruff error
- `Bash` — Fix lint, format, run ruff and full pytest

</details>

Ruff reformatted only my test file. The untracked `packages/ui/src/components/empty/` and the `nuxt.config.ts` change aren't mine, so I'm leaving them alone. Next is codegen.

<details><summary>2 tool calls</summary>

- `Bash` — Regenerate OpenAPI and TS schema
- `Bash` — Check generated diff and curl live endpoint

</details>

The live 24h output is all zeros. To check that real data gets counted, I'll compare the 30d sums against `/stats`.

<details><summary>2 tool calls</summary>

- `Bash` — Compare activity with stats on live dev DB
- `SubagentHandback`

</details>
