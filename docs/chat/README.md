# Chat trail

The sessions this repo was built in, exported as Markdown. How they fit together is in
[AI_USAGE.md](../AI_USAGE.md#how-it-went).

## Claude Code project on claude.ai — "Benji exercise"

The main thread coordinated the work and started one sub-thread per task. The API plan and build
(PR #3), the ported Claude rules (PR #4) and the dashboard plan and build happened in these threads.
Each file is the conversation as claude.ai shows it: messages on both sides, without the threads'
tool calls.

| Thread                                                                    | What came out of it         |
| ------------------------------------------------------------------------- | --------------------------- |
| [Main thread](project-0-main-thread.md)                                   | Handover, coordination, Q&A |
| ↳ [Plan the webhook API backend](project-1-plan-api-backend.md)           | API plan and build, PR #3   |
| ↳ [Port Claude rules into benji-exercise](project-2-port-claude-rules.md) | `.claude/rules/`, PR #4     |
| ↳ [Plan the webhook dashboard](project-3-plan-dashboard.md)               | `docs/DASHBOARD_PLAN.md`    |
| ↳ [Build the webhook dashboard](project-4-build-dashboard.md)             | Dashboard implementation    |
| ↳ [Brainstorm extra features](project-5-brainstorm-features.md)           | Ideas beyond the brief      |

## Claude Code sessions (desktop app)

Each file keeps what was said on both sides. The tool calls are folded into collapsible lists (the
command's description or the file touched), and their output is left out. Paths are made relative
to the repo, and images are noted but not included.

| Session                                                                              | When (UTC)                | User turns |
| ------------------------------------------------------------------------------------ | ------------------------- | ---------: |
| [Webhook notification system take-home](01-webhook-take-home.md)                     | 10-28 18:40 → 10-28 19:05 |          8 |
| [Dashboard UI requirements summary](02-dashboard-ui.md)                              | 10-28 19:06 → 10-29 06:50 |          8 |
| [Local dashboard and API setup](03-local-dashboard-api.md)                           | 10-29 08:56 → 10-29 10:02 |         12 |
| ↳ [Subagent: add deliveries activity endpoint](03-local-dashboard-api.subagent-1.md) |                           |            |
| [Exercise requirements review and testing](04-requirements-review.md)                | 10-29 09:06 → 10-29 10:18 |         11 |
| [Dashboard "how it works" page](05-how-it-works-page.md)                             | 10-29 10:06 → 10-29 10:32 |          3 |
| [Reviewer QOL improvements](06-reviewer-qol.md)                                      | 10-29 10:40 → 10-29 11:30 |         18 |
