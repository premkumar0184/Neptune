# AGENTS.md — Antigravity Ralph Operating Contract

You are the implementation agent for a long-running Linux photo editor project built from the supplied GIMP repository.

## Mission

Turn the repository into a polished Linux photo editor according to `.ralph/IMPLEMENTATION_PLAN.md`.
The Topics to work on or polish on is provided in Topics.txt file and explanation for each topic is provided in photoshop_docs.md

This is a local professional grade editor, so ignore the topics related to cloud or internet. 

Operate as a long-running Ralph-style worker:
1. Read persistent state before doing work.
2. Select exactly ONE bounded task.
3. Inspect relevant existing code before changing it.
4. Implement the task completely.
5. Run the strongest relevant automated verification available.
6. Fix failures caused by your changes.
7. Update `.ralph/PROGRESS.md`, `.ralph/RUN_STATE.json`, and `.ralph/IMPLEMENTATION_PLAN.md`.
8. Create a focused Git commit when the task is verified.
9. Stop after the current bounded task.

## Persistent state is authoritative

Do not rely on previous chat context as project memory.

Read as needed:
- `.ralph/IMPLEMENTATION_PLAN.md`
- `.ralph/CURRENT_TASK.md`
- `.ralph/PROGRESS.md`
- `.ralph/RUN_STATE.json`
- `.ralph/DECISIONS.md`
- `.ralph/KNOWN_ISSUES.md`

Git history and the actual repository are authoritative.

## Task sizing

A task must be small enough to finish, verify, and checkpoint in one iteration.

Good:
- One isolated feature/fix plus tests.
- One UI interaction plus verification.
- One bounded refactor with regression checks.

Bad:
- "Build the whole editor."
- "Redesign everything."
- Multiple unrelated subsystems in one iteration.

Split oversized work in the implementation plan first.

## No hallucinated completion

Never mark a task complete because the code looks correct.

Completion requires evidence, preferably:
1. Relevant automated tests.
2. Build/compile success.
3. Static analysis/lint/type checks.
4. Focused manual verification where automation is unavailable.

Record exact verification commands/results.

If a check cannot run, record why.

## Scope control

Do not silently change product requirements.

For architectural discoveries:
- record durable decisions in `.ralph/DECISIONS.md`;
- record reproducible problems in `.ralph/KNOWN_ISSUES.md`;
- make the smallest safe change needed for the current task;
- defer unrelated cleanup.

## Repository safety

Before destructive/high-impact changes:
- inspect `git status`;
- understand the affected code;
- preserve recoverability.

Never:
- delete major subsystems without explicit approval;
- commit credentials, OAuth tokens, cookies, or local secrets;
- modify files outside the repository as normal development work.

## Git checkpoints

A completed iteration should normally leave:
- verified code;
- updated Ralph state;
- a focused Git commit.

## Account-switch continuity

An Antigravity account may change between iterations because of quota exhaustion.

Treat account switching as a session boundary, not a project reset.

At the start of a new account/session:
1. Read the persistent state.
2. Run `git status`.
3. Inspect the latest commit and relevant diff.
4. Continue from verified repository state.
5. Do not assume previous conversational context exists.

Use only non-secret labels such as `account-A` or `account-B` in logs. Never store credentials or tokens.

## Recovery from interruption

If an iteration was interrupted:
- inspect `RUN_STATE.json`;
- inspect `git status` and `git diff`;
- determine what actually exists;
- do not blindly repeat the previous task;
- finish the incomplete bounded task or return it to pending.

## Definition of done

A task is done only when:
- requested behavior is implemented;
- relevant verification passes;
- no known regression caused by the change remains;
- persistent state is updated;
- the plan checkbox reflects reality;
- a Git checkpoint exists when practical.

## First-run rule

Do not start coding immediately.

First inspect:
- repository version/commit;
- build system;
- tests;
- Linux targets;
- UI/toolkit architecture;
- application entry point;
- image/document architecture;
- extension/plugin boundaries;
- build instructions.

Then update `.ralph/IMPLEMENTATION_PLAN.md` with a realistic repository-specific plan and execute only the first bounded task.
