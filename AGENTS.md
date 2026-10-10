# AGENTS.md — PhotoGIMP + PhotoCraft UI Modernization Contract

You are the implementation agent for the active project in this workspace: PhotoGIMP.

This repo contains two separate things, and only one is the real target:
- PhotoGIMP is the active app and the actual product being improved.
- PhotoCraft is only a design reference and inspiration source for the UI direction.

Do not treat the photocraft folder as the main app to modify. It exists as a visual/reference benchmark, not as the product under active development.

## Mission

Turn PhotoGIMP into a polished Linux photo editor that keeps all of the Photoshop-style capability already added while adopting a cleaner, more premium, PhotoCraft-like visual and interaction language.

The core goal is:
- preserve the full Photoshop-aligned feature set already implemented in PhotoGIMP;
- keep the GIMP 3.x native architecture and plugin model intact;
- modernize the UI shell, panel structure, theme, spacing, typography, and workspace behavior to feel closer to PhotoCraft;
- do not regress functionality while improving the visual experience.

Use `Topics.txt`, `photoshop_docs.md`, and `.ralph/IMPLEMENTATION_PLAN.md` as the feature authority.
Use PhotoCraft as the design authority for layout, visual polish, hierarchy, and overall UX tone.

## Product direction

PhotoGIMP is not a new editor from scratch. It is a GIMP-based photo workflow that should feel familiar to Photoshop users while looking more modern, professional, and coherent.

The target is a hybrid:
- Photoshop-like workflow and shortcuts remain the primary behavior;
- PhotoCraft-like UI language is the primary visual direction;
- all current plugin tools, custom menus, and productivity features stay working.

This is a local editor; ignore cloud/web-only concepts unless they are explicitly required for the local desktop experience.

## Operating rules

Operate as a long-running Ralph-style worker:
1. Read persistent state before doing work.
2. Select exactly ONE bounded task.
3. Inspect relevant existing code and config before changing it.
4. Implement the task completely.
5. Run the strongest relevant verification available.
6. Fix failures caused by your changes.
7. Update `.ralph/PROGRESS.md`, `.ralph/RUN_STATE.json`, and `.ralph/IMPLEMENTATION_PLAN.md`.
8. Create a focused Git commit when the task is verified.
9. Repeat from step 1.

## Required reading

Always read the current project state before starting a new iteration:
- `.ralph/IMPLEMENTATION_PLAN.md`
- `.ralph/CURRENT_TASK.md`
- `.ralph/PROGRESS.md`
- `.ralph/RUN_STATE.json`
- `.ralph/DECISIONS.md`
- `.ralph/KNOWN_ISSUES.md`
- `PhotoGIMP/README.md`
- relevant PhotoGIMP config under `PhotoGIMP/.config/GIMP/3.0/`

Git history and the repository are authoritative.

## Responsible scope

A task must be small enough to finish, verify, and checkpoint in one iteration.

Good examples:
- tune a single workspace layout or theme setting;
- improve one UI shell file while preserving configuration integrity;
- adjust one tool preset or panel arrangement without breaking plugin behavior;
- refactor the guidance or AI prompt files for a clearer product direction.

Bad examples:
- redesign the entire app in one pass;
- rewrite the whole project to PhotoCraft code instead of preserving GIMP;
- remove working features to chase aesthetics.

## UI target

When working on the interface, prioritize these goals in order:
1. preserve the current feature set;
2. keep the workflow familiar to Photoshop users;
3. make the app feel cleaner, darker, more structured, and more premium;
4. bring the overall visual language closer to PhotoCraft without breaking GIMP compatibility.

Relevant areas for UI work:
- `PhotoGIMP/.config/GIMP/3.0/theme.css`
- `PhotoGIMP/.config/GIMP/3.0/gimprc`
- `PhotoGIMP/.config/GIMP/3.0/sessionrc`
- `PhotoGIMP/.config/GIMP/3.0/shortcutsrc`
- `PhotoGIMP/.config/GIMP/3.0/tool-options/`
- `PhotoGIMP/.local/share/applications/`
- `PhotoGIMP/install.sh`
- `PhotoGIMP/scripts/verify_config.py`

## Verification rules

Never mark a task complete because it looks correct.

Completion requires evidence, preferably:
1. relevant tests or config validation;
2. successful install or config deployment;
3. static checks / validation scripts;
4. focused manual verification where automation is unavailable.

Record exact commands and results.

If a check cannot run, record why.

## Scope control

Do not silently change product requirements.

For architectural discoveries:
- record durable decisions in `.ralph/DECISIONS.md`;
- record reproducible problems in `.ralph/KNOWN_ISSUES.md`;
- make the smallest safe change needed for the current task;
- defer unrelated cleanup.

## Repository safety

Before destructive or high-impact changes:
- inspect `git status`;
- understand the affected files;
- preserve recoverability.

Never:
- delete major subsystems without explicit approval;
- commit credentials, OAuth tokens, cookies, or local secrets;
- modify files outside the repo as normal development work.

## Git checkpoints

A completed iteration should normally leave:
- verified code/configuration;
- updated Ralph state;
- a focused Git commit.

## Account-switch continuity

If the session/account changes, treat it as a fresh state boundary.

At the start of a new account/session:
1. read the persistent state;
2. run `git status`;
3. inspect the latest commit and relevant diff;
4. continue from the verified repository state;
5. do not assume previous conversational memory.

## Definition of done

A task is done only when:
- the requested behavior is implemented;
- the relevant verification passes;
- no known regression remains;
- the persistent state is updated;
- the plan reflects reality;
- a Git checkpoint exists when practical.

## Final direction

The product direction is clear:
- this is PhotoGIMP, not a new photocraft project;
- the feature set is the Photoshop-like suite already assembled;
- the UI should increasingly resemble the modern PhotoCraft aesthetic while retaining the full PhotoGIMP workflow and compatibility.

This project is a GIMP-based professional photo editor with a PhotoCraft-inspired interface, not a from-scratch rewrite.
