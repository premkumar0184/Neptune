# Task Protocol

## Before coding
- Read `AGENTS.md`.
- Read the relevant `.ralph/` state.
- Run `git status`.
- Inspect the existing implementation.
- Define acceptance criteria.
- Identify verification commands.

## During coding
- Keep the change scoped.
- Preserve existing behavior outside the task.
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
