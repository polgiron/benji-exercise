# Benji — webhook notification system

Take-home for Benji's Senior Software Engineer role: customers register webhook endpoints,
events fan out to them with signed, retried, deduplicated, replayable deliveries, and a
dashboard shows every delivery live.

- **Design & trade-offs:** [docs/PLAN.md](docs/PLAN.md)
- **AI usage:** [docs/AI_USAGE.md](docs/AI_USAGE.md)

## Stack

| | |
|---|---|
| `apps/api` | FastAPI, SQLAlchemy 2 (async) + SQLite, httpx — managed with **uv** |
| `apps/dashboard` | Nuxt 4 (SPA), TanStack Vue Query, shadcn-vue, Tailwind 4 |
| `packages/utils` | shared TS helpers (`cn`, time formatting) |

Turborepo + pnpm drive both apps; the API's `package.json` scripts wrap `uv run …`.

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

## Other scripts

| command | does |
|---|---|
| `pnpm typecheck` | `nuxt typecheck` + `tsc` |
| `pnpm lint` | ruff (API) |
| `pnpm gen:api` | dumps FastAPI's OpenAPI schema and regenerates `apps/dashboard/app/api/schema.d.ts` |
