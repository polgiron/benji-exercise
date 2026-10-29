# Thread: Port Claude rules into benji-exercise

Claude Code project on claude.ai · "Benji exercise" · sub-thread · PR #4

## 🧑 User

can you bring all the claude rules I have from the parallel repo to this repo

## 🤖 Claude

I’ll find your other repo’s Claude rules and check with you which repo it is if that’s unclear.

Added `parallel-adventure/parallel` to this thread

- Find the Parallel repo and read its rules
- Adapt AGENTS.md, CLAUDE.md and .claude/rules to Nuxt + FastAPI
- Open the PR

I opened the PR with the rules from `Parallel-Adventure/parallel`: [polgiron/benji-exercise#4](https://github.com/polgiron/benji-exercise/pull/4). I took “the parallel repo” to mean that one.

It uses the same layout as Parallel: `AGENTS.md`, a `CLAUDE.md` that imports it, and path-scoped `.claude/rules/`. The general rules carry over as they are: the “done” levels, reading exit codes, proving a guard rail by breaking it, no `any`, the `E`/`I` naming, and only merging when you say so. I rewrote the React rules for Vue and shadcn-vue. I also replaced the Next.js and Supabase rules with `dashboard.md`, `database.md` and a new `api.md` for FastAPI.

Some things I pushed back on and left out:

- **The product rules** (adventures, NPCs, prompts, launchpad, `prll.fr`, feature flags).
- **OpenSpec and the `sandbox` branch**, which seem like too much process for a one-day take-home.
- **The ~50 skills.** Most are about Parallel itself. If you want any of the generic ones, like `grilling` or `prove-it`, tell me which.

One more thing: I accidentally committed a Node compile cache and wasn’t allowed to force-push. A second commit removes it, so squash-merge to keep `main` clean. I’m watching the PR.

## 🧑 User

ok squash merge it

## 🤖 Claude

I squash-merged [polgiron/benji-exercise#4](https://github.com/polgiron/benji-exercise/pull/4) into `main` as a single commit, so the stray cache commit isn’t in the history. The rules now apply to every new session on this repo.
