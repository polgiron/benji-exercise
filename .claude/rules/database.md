---
paths:
  - 'apps/api/app/**'
  - 'apps/dashboard/app/api/**'
---

# Database

SQLite through SQLAlchemy 2 (async, aiosqlite). The tables and the status machine are in
`docs/PLAN.md:29`: change the plan when the model changes.

- A persisted enum is stored as its snake_case string value, matching a Python `StrEnum`
  (`DeliveryStatus`) and, on the dashboard, a TS string enum with the `E` prefix
  (`EDeliveryStatus`) whose values are the same strings. Never store an enum's position.
- IDs are prefixed strings (`ep_`, `evt_`, `dlv_`, `att_`): generate them in one helper, never an
  autoincrement integer that leaks into the API.
- A guarantee the system relies on is a database constraint, not only a check in code: one delivery
  per (event, endpoint) is a `UNIQUE`, a re-submitted idempotency key is a `UNIQUE`. Prove it by
  writing the duplicate in a test and seeing it fail.
- Every change to a `deliveries` row bumps its `version` in the same statement — the dashboard drops
  any SSE update whose version is not newer.
- No migrations tool for this exercise: the schema is created on startup. Say so in the PR when a
  change needs the local `.db` file deleted.
