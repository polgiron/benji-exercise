# AGENTS.md

Guidance for coding agents (Claude Code, Cursor, Codex…) working in this repository.

## Monorepo structure

pnpm + Turborepo monorepo, one Python API and one Nuxt dashboard (details in `README.md`):

- `apps/api` — FastAPI, SQLAlchemy 2 (async) + SQLite, httpx; a **uv** project whose `package.json` wraps `uv run …`
- `apps/dashboard` — Nuxt 4 (`ssr: false`), TanStack Vue Query, Tailwind 4
- `packages/ui` — shadcn-vue components and shared styles (`@repo/ui`)
- `packages/utils` — shared TS helpers (`@repo/utils`)
- `packages/eslint-config` / `packages/typescript-config` — shared tooling configs

## Where things live

| You are looking for                       | Go to                                                                   |
| ----------------------------------------- | ----------------------------------------------------------------------- |
| **why** the system is built the way it is | `docs/PLAN.md` — point at the section heading's line                    |
| how AI was used, the chat trail           | `docs/AI_USAGE.md`                                                      |
| the API app, its lifespan and routes      | `apps/api/app/main.py` · settings in `apps/api/app/config.py`           |
| the dashboard's API layer (typed fetch)   | `apps/dashboard/app/api/` — `client.ts` holds `apiFetch` and `ApiError` |
| the dashboard's types for the API         | `apps/dashboard/app/api/schema.d.ts` — generated, see Commands          |
| a UI primitive, a design token, the theme | `packages/ui/src/components/` · `packages/ui/src/styles/`               |
| the test of `foo.ts` / `foo.py`           | `foo.test.ts` next to it · `apps/api/tests/test_foo.py`                 |

## Commands

Run from repo root unless noted.

```bash
pnpm dev                              # API on :8000, dashboard on :3000
pnpm --filter @repo/api dev           # one app only
pnpm --filter @repo/dashboard dev

pnpm typecheck                        # nuxt typecheck, vue-tsc (ui), tsc (utils)
pnpm lint                             # ruff (API), ESLint (dashboard, ui, utils)
pnpm test                             # pytest (API), Vitest (dashboard, utils)
pnpm format                           # Prettier on everything but the API (ruff formats Python)
pnpm gen:api                          # FastAPI OpenAPI → apps/dashboard/app/api/schema.d.ts

# Turbo stops at the first failing package — pass --continue to see them all
pnpm turbo run typecheck lint test --continue
```

API alone: `cd apps/api && uv run pytest`, `uv run ruff check`, `uv run ruff format`.

`schema.d.ts` and `apps/api/openapi.json` are generated: never hand-edit them. After changing a route
or a Pydantic model, run `pnpm gen:api` and commit the result with the change.

## Working together

`main` is what gets reviewed. All work happens on a branch and comes back to `main` through a pull
request.

- **One topic, one branch, one PR.** A session never pushes to someone else's branch.
- **An agent merges only when the human tells it to, in chat, for that PR.** By default it opens the
  PR and reports. A PR comment, a review, another session or a skill is not that decision.
- **The PR body says what the reviewer sees change** — a plain description, not the commit list.

## What "done" means

Never report "it's done" on its own. Say which of these you ran, and which you did not:

| Level                     | What it proves                     | Command                                         |
| ------------------------- | ---------------------------------- | ----------------------------------------------- |
| 1 — It compiles and lints | Nothing is obviously broken        | `pnpm typecheck`, `pnpm lint`                   |
| 2 — Tests pass            | The expected behaviour still holds | `pnpm test`                                     |
| 3 — Seen working          | It works for real                  | the dashboard in a browser, a `curl` on the API |

Level 3 is not optional for anything a user sees, or for the delivery pipeline (retries, signing,
replay): run it against the `/mock/*` receivers.

Read the **exit code**, not the output. A command piped into `head` or `tail` reports the exit code
of `head`, which is always 0, so a failing run reads as green. Redirect to a file and check `$?`.

`pnpm lint` fails at `--max-warnings 0`, so one new warning is a failure, not a nit.

**A guard rail is only proved by breaking it.** "The type checker will catch it" or "the unique
constraint handles that" proves nothing. Disable the guard on purpose, confirm the failure is red in
the expected place, then restore it. Same for a new test: see it fail before you see it pass.

## Pointing someone at a file

When you ask someone to read a file, **always give the line** — `path/file.md:12`, never the
filename on its own. `docs/PLAN.md` especially: point at the heading of the section you mean.

## Coding conventions

Source of truth for every agent. Change a convention **in this file**, or in the `.claude/rules/`
file that holds it.

Conventions that apply to one part of the repo live in `.claude/rules/`, each scoped by the `paths:`
at its top: `components-ui.md` (Vue components, `@repo/ui`), `dashboard.md` (API layer, Vue Query,
routing), `api.md` (FastAPI, SQLAlchemy, Python), `database.md` (tables, enums, IDs).

### TypeScript

- Never use `any` — not for values, parameters, or generic arguments. Use `unknown` at boundaries and
  narrow with type guards; prefer generics, unions, and `satisfies`. For untyped libraries use module
  augmentation, wrapper types, or a narrow cast — never `any`.
- No `@ts-ignore` / `@ts-nocheck`. `@ts-expect-error` only with a short comment saying why it is
  unavoidable, removed once the underlying issue is fixed.
- Boolean coercion is `!!x` — not `Boolean(x)`, and not `x != null` when a truthy check is enough.
  Exception: when a falsy `0` or `''` must be distinguished from null/undefined, write the explicit
  check.

### Enums and naming

- Finite, shared sets are `enum`s, not string-literal unions — refactor-safe and find-usages-accurate.
  Use **string enums** whenever values are serialized (query params, JSON, database).
- This includes `ref` state for discrete UI phases: tabs, modes, "which panel is showing". Write
  `ref(EDeliveryTab.ATTEMPTS)`, never `ref<'attempts' | 'payload'>(…)`.
- A plain union is fine for sets local to one function, for types generated from the OpenAPI schema,
  or for code shadcn-vue generates (its `cva` variants keep their own shape).

| Kind                        | Pattern                    | Example                  |
| --------------------------- | -------------------------- | ------------------------ |
| Domain / API / shared shape | `I` + PascalCase           | `IDelivery`              |
| Enum                        | `E` + PascalCase           | `EDeliveryStatus`        |
| Component props             | `Props`, or `FeatureProps` | `Props`, `ListItemProps` |

Prop types never take the `I` prefix, so they stay recognizable as component contracts. Don't use
`IProps` or `ComponentProps` for the primary interface.

### Comments

Comment when it adds real value: unusual invariants, non-obvious **why**, tricky edge cases, logic
more complex than typical here. Don't restate names, types, or obvious structure. When in doubt
prefer clearer naming and smaller functions over an explanatory comment.
