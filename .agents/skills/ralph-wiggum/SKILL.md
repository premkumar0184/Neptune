---
name: ralph-wiggum
description: >-
  Long-running autonomous implementation workflow for this project. Use when
  continuing project work across Antigravity sessions or account switches.
---

# Ralph Wiggum Workflow

Use this procedure for one bounded iteration.

## Recover
Read:
- `AGENTS.md`
- `.ralph/IMPLEMENTATION_PLAN.md`
- `.ralph/CURRENT_TASK.md`
- `.ralph/PROGRESS.md`
- `.ralph/RUN_STATE.json`
- `.ralph/DECISIONS.md`
- `.ralph/KNOWN_ISSUES.md`

Then run `git status` and inspect the latest relevant commit/diff.

## Select one task
Choose ONE task with clear acceptance criteria and a realistic verification path. Write it to `.ralph/CURRENT_TASK.md`.

## Implement
Inspect existing code first. Make small, reversible changes. Do not broaden scope.

## Verify
Run focused tests first, then broader checks when justified. Fix failures caused by the current change and rerun them.

## Checkpoint
Create a focused Git commit containing the verified task. Never commit secrets.

## Update state
Record what changed, verification evidence, commit hash, durable discoveries, and the exact next task.

Update all applicable `.ralph/` files.

## Stop
End after one bounded task.

## Account switch
Treat a new account/session as a fresh worker:
NEW SESSION → READ STATE → INSPECT GIT → VERIFY LAST CHECKPOINT → SELECT NEXT TASK → IMPLEMENT → VERIFY → CHECKPOINT → UPDATE STATE

Never depend on the previous account's conversation memory.
