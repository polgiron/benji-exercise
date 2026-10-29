---
paths:
  - 'apps/dashboard/**'
---

# Dashboard

### API layer

- Every call to the API goes through a typed function in `app/api/` built on `apiFetch` from
  `app/api/client.ts`. Components and composables never call `ofetch` / `$fetch` or write an API path
  themselves — add the function to `app/api/` first.
- Request and response types come from the generated `app/api/schema.d.ts`. Never hand-write a type
  the schema already has; if it is missing, the API's Pydantic model is what changes, then
  `pnpm gen:api`.
- Every failure reaches the UI as an `ApiError` (`code`, `message`, `status`). Show its `message`;
  branch on its `code`, never on the message text.

### Server state (TanStack Vue Query)

- Server state lives in the Vue Query cache, nowhere else — no Pinia, no copy in a `ref`.
- Query keys come from one factory per resource, never an inline array, so invalidation and the SSE
  merge hit the same key.
- Live updates from SSE are written into the cache with `setQueryData`, and only when the incoming
  `version` is newer than the cached one (`docs/PLAN.md:112`).

### Routing

File-based under `app/pages/`. Navigate with `<NuxtLink>` / `navigateTo`; the dashboard is an SPA
(`ssr: false`), so there is no server-only code path in it.
