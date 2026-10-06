# Ralph Mode for Antigravity

This repository is intended for repeated Antigravity iterations.

## Initial instruction

Give Antigravity this objective:

> Act as the implementation worker for this project. Read `AGENTS.md` and the entire `.ralph/` state first. Inspect the repository before changing anything. Build a realistic implementation plan for the Linux photo editor, then execute exactly one small verified task. Update the Ralph state and checkpoint the work. Do not continue into a second unrelated task.

## After an account/session switch

Use:

> Continue this project from persistent repository state. Do not rely on previous conversation context. Read `AGENTS.md` and `.ralph/` state, inspect Git status and the latest verified work, then execute the next single bounded task and checkpoint it.

## Iteration contract

READ → INSPECT → PLAN → IMPLEMENT → VERIFY → CHECKPOINT → UPDATE STATE → STOP

The next iteration starts from disk/Git state, not conversation memory.

## Long-running goal

The project must remain recoverable across:
- different Antigravity sessions;
- different Antigravity accounts;
- interruptions;
- context resets.
