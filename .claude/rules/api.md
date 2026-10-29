---
paths:
  - 'apps/api/**'
---

# API (FastAPI, Python)

### Python

- Fully typed: every function signature, every return. No bare `# type: ignore` — when one is
  unavoidable, name the code and say why on the same line.
- Finite, shared sets are `StrEnum`s, not bare strings or `Literal` unions, named in PascalCase
  without a prefix (`DeliveryStatus`). Their values are what goes on the wire and in the database.
- `ruff check` and `ruff format` own style; don't argue with them in review.
- Async all the way: SQLAlchemy async sessions and `httpx.AsyncClient`. Never a blocking call
  (`requests`, `time.sleep`, sync file or DB I/O) inside a route or the worker.

### Routes and schemas

- Request and response bodies are Pydantic models, declared on the route (`response_model` or the
  return annotation) so they reach the OpenAPI schema and, through `pnpm gen:api`, the dashboard.
- Errors leave the API as `{ "error": { "code", "message" } }` with the right status — the dashboard's
  `toApiError` depends on that shape. `code` is a stable snake_case identifier.
- Routes stay thin: they validate and call a service. Fan-out, replay and delivery logic live in
  services, so the worker and the routes share them.

### Tests

- pytest under `apps/api/tests/`, one `test_<module>.py` per module. Use the fixtures in
  `conftest.py`; a test never touches the dev database or the network outside the `/mock/*`
  receivers.
- Time and randomness (retry backoff, jitter, lease expiry) are injected, so a test controls them
  instead of sleeping.
