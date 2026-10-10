# Ralph Mode for Antigravity

This repository is intended for repeated Antigravity iterations on the PhotoGIMP project.

## Initial instruction

Give Antigravity this objective:

> Act as the implementation worker for PhotoGIMP. Read `AGENTS.md` and the `.ralph/` state first. Inspect the repo before changing anything. Keep the current Photoshop-style feature suite intact, modernize the interface toward a PhotoCraft-inspired visual language, and execute exactly one small verified task. Update the Ralph state and checkpoint the work. Do not continue into a second unrelated task.

## After an account/session switch

Use:

> Continue the PhotoGIMP project from persistent repository state. Do not rely on previous conversation context. Read `AGENTS.md` and `.ralph/` state, inspect Git status and the latest verified work, then execute the next single bounded UI/config task for the PhotoGIMP shell while preserving the feature set, and checkpoint it.

## Iteration contract

READ → INSPECT → PLAN → IMPLEMENT → VERIFY → CHECKPOINT → UPDATE STATE → READ

The next iteration starts from disk/Git state, not conversation memory.

## Long-running goal

The project must remain recoverable across:
- different Antigravity sessions;
- different Antigravity accounts;
- interruptions;
- context resets.

## Final design objective

The active project is PhotoGIMP and the design target is a cleaner, more premium PhotoCraft-inspired UI. The feature set is the Photoshop-aligned GIMP capability already implemented in this repo; do not regress it while building the next UI refinement.
