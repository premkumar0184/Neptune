# Task Protocol

## Before coding
- Read `AGENTS.md` and the relevant `.ralph/` state.
- Confirm the active project is PhotoGIMP, not the separate photocraft reference repository.
- Run `git status`.
- Inspect the existing implementation.
- Define acceptance criteria.
- Identify verification commands.

## Product objective
The active goal is to keep the existing Photoshop-style feature set intact while refining the PhotoGIMP UI toward a clean, premium PhotoCraft-inspired presentation.

## During coding
- Keep the change scoped.
- Preserve existing behavior outside the task.
- Prefer UI/config improvements that increase polish without breaking core features.
- Add/update tests when appropriate.
- Avoid unrelated formatting churn.

## Before completion
Run the strongest relevant checks and ask:
1. Does the requested behavior actually work?
2. Did the change introduce a regression?
3. Is the evidence sufficient?
4. Is the plan checkbox truthful?
5. Can a fresh session recover from the state?

## After completion
Update:
- `.ralph/CURRENT_TASK.md`
- `.ralph/PROGRESS.md`
- `.ralph/RUN_STATE.json`
- `.ralph/IMPLEMENTATION_PLAN.md`
- `.ralph/DECISIONS.md` when needed
- `.ralph/KNOWN_ISSUES.md` when needed

Then create a focused Git checkpoint when practical.

Finally STOP. The next iteration is a separate unit of work.
