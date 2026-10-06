# Antigravity project rules

Follow `AGENTS.md` as the primary operating contract.

This is a long-running Ralph-style project. Persistent state lives under `.ralph/`.

Before implementing:
- read `.ralph/IMPLEMENTATION_PLAN.md`;
- read `.ralph/PROGRESS.md`;
- read `.ralph/RUN_STATE.json`;
- inspect the repository and Git state.

Do not treat chat history as durable memory.

Work in bounded iterations. Finish and verify one task before selecting another.

Never claim success without evidence from tests, build checks, static analysis, or documented manual verification.

After each completed iteration, update Ralph state and create a focused Git checkpoint when practical.

After an Antigravity account switch, assume no conversational memory from the previous account. Recover entirely from repository state and Git.
