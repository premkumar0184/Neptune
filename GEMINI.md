# Gemini project rules

Follow `AGENTS.md` as the primary operating contract.

This repository is the PhotoGIMP project. The active product is PhotoGIMP, not the separate photocraft directory.

## Product direction

PhotoGIMP already contains the Photoshop-like feature set, plugin suite, and workflow improvements. The goal is to modernize the interface toward the PhotoCraft visual language while preserving everything that already works.

Treat PhotoCraft as a visual/reference benchmark, not as the application being actively edited.

## Required workflow

Before implementing:
- read `.ralph/IMPLEMENTATION_PLAN.md`;
- read `.ralph/PROGRESS.md`;
- read `.ralph/RUN_STATE.json`;
- inspect the repository and Git state;
- confirm the active task remains within PhotoGIMP and its configuration/UI layer.

Do not treat chat history as durable memory.

Work in bounded iterations. Finish and verify one task before selecting another.

Never claim success without evidence from tests, config validation, build checks, or documented manual verification.

After each completed iteration, update Ralph state and create a focused Git checkpoint when practical.

After an Antigravity account switch, recover entirely from repository state and Git. Do not rely on previous conversation memory.

## UI objective

Focus on the PhotoGIMP shell and config layer:
- workspace layout
- theme and panel density
- tool arrangement and visual hierarchy
- app identity and desktop integration
- Photoshop-like ergonomics with a cleaner, more premium visual style

Keep feature parity intact. Do not remove or downgrade the existing Photoshop-style tools, plugins, or keyboard behavior while redesigning the UI.
