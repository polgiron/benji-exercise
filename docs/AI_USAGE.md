# AI usage

Built with Claude Code (desktop app) as a pair: I made the product and stack decisions, Claude
drafted, scaffolded and implemented under review.

## How it went

1. **Brief & stack** — read the exercise with Claude, chose the stack (FastAPI to match Benji's
   Python backend; Nuxt + Vue Query to match the frontend), and wrote a handover brief
   (below) to start the build session from.
2. **Plan** — Claude drafted [PLAN.md](PLAN.md) from the brief; I reviewed the design choices
   (outbox-style DB queue, Standard Webhooks signing, SSE + versioned cache merges).
3. **Scaffold** — Turborepo/pnpm monorepo, uv project, Nuxt + shadcn-vue, OpenAPI → TS types.
4. **API plan** — Claude drafted [API_PLAN.md](API_PLAN.md) (build order + tests per step); I
   challenged it in chat: endpoints vs subscriptions, why both an idempotency key and a request
   hash, provider vs receiver roles, and asked for a strict JSON Schema per event type.
5. **API implementation** — built step by step from that plan, each step committed with its
   tests green.
6. **Dashboard plan** — Claude drafted [DASHBOARD_PLAN.md](DASHBOARD_PLAN.md) and I reviewed it:
   the split between the customer dashboard and the test panel, the two levels of endpoint
   control, how the live view stays accurate.
7. **Dashboard implementation** — API layer and SSE cache merge first (unit-tested), then the
   layout and pages, then a pass to compose every surface from `@repo/ui` only.
8. **Review against the brief** — a separate Claude session checked each requirement of the
   exercise against the code, ran the checks, then ran the API and dashboard for real: an
   independent receiver verifying signatures, retries and replay against the `/mock/*`
   receivers, concurrent re-submits, an API restart mid-retry, and the dashboard in a browser.
   It found gaps (views stuck on an error after an API outage, no Retry, a misleading empty
   state under a filter, Replay offered on paused endpoints, docs behind the code); I chose
   the fixes, and they shipped in one PR.

## Handover brief that started the build session

> Senior fullstack take-home for Benji (B2B loyalty/rewards). Max one day of work, runs locally
> with no external infrastructure, delivered as a GitHub repo. AI use is expected — keep the
> chat trail.
>
> Stack: FastAPI + SQLite + uv; in-process background loop reading a `deliveries` table
> (outbox-style), no Redis/queue. Nuxt (`ssr: false`), TanStack Vue Query, SSE written into
> the query cache with `setQueryData`, no Pinia, plain typed fetch functions, shadcn-vue.
> Turborepo + pnpm monorepo. Bonus: generate the dashboard's TS types from FastAPI's OpenAPI.
>
> Next step: write the implementation plan first (it is a deliverable), then scaffold the
> monorepo.

## Chat trail

The session transcripts are exported to `docs/chat/` at the end of the work.
