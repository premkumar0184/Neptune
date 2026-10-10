---
name: ralph-wiggum
description: >-
  Long-running autonomous implementation workflow for the PhotoGIMP project. Use when
  continuing work across Antigravity sessions or account switches.
---

# Ralph Wiggum Workflow

Use this procedure for one bounded iteration on the PhotoGIMP repo.

## Recover
Read:
- `AGENTS.md`
- `GEMINI.md`
- `RALPH.md`
- `.ralph/IMPLEMENTATION_PLAN.md`
- `.ralph/CURRENT_TASK.md`
- `.ralph/PROGRESS.md`
- `.ralph/RUN_STATE.json`
- `.ralph/DECISIONS.md`
- `.ralph/KNOWN_ISSUES.md`
- `PhotoGIMP/README.md`

Then run `git status` and inspect the latest relevant commit/diff.

## Product direction
The active app is PhotoGIMP.
The photocraft folder is only a design reference for the premium UI direction.

The goal is to keep the Photoshop-style feature suite intact while refining the PhotoGIMP interface toward a cleaner, more modern PhotoCraft-inspired presentation.

## Select one task
Choose ONE task with clear acceptance criteria and a realistic verification path. Write it to `.ralph/CURRENT_TASK.md`.

## Implement
Inspect existing code and config first. Make small, reversible changes. Do not broaden scope. Prefer improvements to the PhotoGIMP shell and configuration layer without removing working features.

## Verify
Run focused config/tests first, then broader checks when justified. Fix failures caused by the current change and rerun them.

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
