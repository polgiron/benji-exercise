# CLAUDE.md

@AGENTS.md

## Claude Code only

- Domain rules load on their own from `.claude/rules/` when you open a matching file.
- Run checks quietly, then read the exit code, not the log:
  - `pnpm turbo run typecheck lint test --output-logs=errors-only --continue`
  - one Vitest package: `pnpm --filter @repo/dashboard exec vitest run --reporter=dot`
  - the API: `cd apps/api && uv run pytest -q`
- Don't read a file again that you already read in this session: keep the useful range in mind.
- `docs/PLAN.md` is long: grep for the section, read around its line — don't read the whole file.
