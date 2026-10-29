# Thread: Brainstorm extra features

Claude Code project on claude.ai · "Benji exercise" · sub-thread

## 🧑 User

ok let's start a thread for simply brainstorming on this topic

## 🤖 Claude

Let’s start from your versioning idea and the four I suggested, and weigh what each would show against what it costs.

I’d push back a little on both sides. Versioning isn’t as heavy as it sounded if you keep it narrow: ship a `v2` of one type only (say a renamed field), add a version pinned on each subscription, and have fan-out down-convert the payload to v1 for old subscribers. That’s roughly half a day, and `apps/api/app/event_types.py:18` already promises “removing, renaming or retyping needs a new version (not built)”. So it fits the story. The catch is that it’s hard to show: the reviewer sees two nearly identical JSON blobs. It’s a design-maturity signal, not a demo moment.

Here’s how I’d rank the options on value per hour:

1. **“Send test event” button on an endpoint** (my addition). It takes about an hour, and every real webhook product has it (Stripe, Svix). It also makes your own demo smoother.
2. **Auto-disable after N consecutive failures, plus bulk replay.** Both already sit in the “next steps” of the scope-cuts table (`docs/PLAN.md:194`). Building them turns “we’d do this later” into “done”, and together they make one demo: break an endpoint, it gets disabled, you fix it, re-enable, replay everything.
3. **Versioning, scoped as above.** It’s worth it if you want to talk about API contracts in the interview. Otherwise a solid paragraph in the plan gets you most of the credit.
4. **Secret rotation.** It’s real ops value, but nothing visible happens in a demo. I’d leave it as a next step.

My pick is 1 and 2, with versioning written up as a design note. Do you see versioning as something Benji’s reviewers would care about specifically, or did it just feel like the most “senior” option?
