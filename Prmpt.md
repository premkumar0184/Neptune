Continue the PhotoGIMP project with a clear mission: modernize the UI toward a PhotoCraft-inspired look while preserving the full Photoshop-style feature set already added to the repo.

IMPORTANT:
The active project is PhotoGIMP. The photocraft directory is a reference benchmark for visual direction, not the app being actively modified.

You are NOT allowed to declare the project complete merely because the plan is marked complete or because previous agents claimed success.

This is a fresh iteration. Recover the project entirely from the repository, Git history, and persistent state.

==================================================
1. RECOVER STATE
==================================================

Read:

- AGENTS.md
- GEMINI.md
- RALPH.md
- Topics.txt
- photoshop_docs.md
- PhotoGIMP/README.md
- .ralph/PHOTOSHOP_FEATURE_MATRIX.md
- .ralph/IMPLEMENTATION_PLAN.md
- .ralph/CURRENT_TASK.md
- .ralph/PROGRESS.md
- .ralph/RUN_STATE.json
- .ralph/DECISIONS.md
- .ralph/KNOWN_ISSUES.md

Then run:

git status
git log -15 --oneline
git diff
git branch --show-current

Inspect the latest relevant commits and verify what the previous iteration actually changed.
Do not trust the previous summary without checking the repository.

==================================================
2. VERIFY THE CURRENT STATE BEFORE NEW WORK
==================================================

Before implementing anything new, determine whether the repo is currently healthy.

Run the strongest applicable baseline checks:
- config validation scripts
- install/deploy checks
- automated tests
- relevant smoke checks
- GIMP compatibility checks for the edited files

If a previously implemented feature is broken, incomplete, or unverifiable, fix THAT before starting a new feature.

Never stack new work on top of an unverified broken state.

==================================================
3. WORK FROM THE RIGHT PRODUCT DEFINITION
==================================================

The product definition is:
- PhotoGIMP is the active app.
- PhotoCraft is the UI inspiration source for polish and structure.
- Photoshop-era functionality in the plans and matrices remains mandatory.

The objective is not to replace GIMP behavior with a new app. The objective is to keep the feature-rich PhotoGIMP workflow and make it visually closer to the premium, organized PhotoCraft design language.

For UI or shell work, inspect:
- `PhotoGIMP/.config/GIMP/3.0/gimprc`
- `PhotoGIMP/.config/GIMP/3.0/sessionrc`
- `PhotoGIMP/.config/GIMP/3.0/theme.css`
- `PhotoGIMP/.config/GIMP/3.0/shortcutsrc`
- `PhotoGIMP/.config/GIMP/3.0/tool-options/`
- `PhotoGIMP/install.sh`
- `PhotoGIMP/scripts/verify_config.py`

For feature work, use:
- `Topics.txt`
- `photoshop_docs.md`
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md`

==================================================
4. SELECT EXACTLY ONE BOUNDED TASK
==================================================

Choose ONE highest-priority incomplete or insufficiently verified task from the implementation plan.

It should be small enough to:
- implement;
- test;
- debug;
- and checkpoint
within this iteration.

If the task is too large, split it into smaller tasks before implementing.

Do not combine unrelated features.

Before coding, update:

.ralph/CURRENT_TASK.md

with:
- task
- rationale
- affected code
- acceptance criteria
- verification commands
- expected checkpoint

==================================================
5. IMPLEMENTATION
==================================================

Inspect the existing implementation first.

Then implement only the selected task.

Rules:

- prefer existing GIMP APIs and configuration patterns;
- avoid unnecessary rewrites;
- avoid speculative architecture;
- avoid unrelated cleanup;
- preserve existing functionality;
- maintain the Photoshop-like workflow and all custom plugins;
- apply PhotoCraft-inspired polish only where it improves the editor without breaking compatibility.

Do not create fake functionality whose UI exists but whose behavior is missing.

==================================================
6. VERIFICATION — THIS IS MANDATORY
==================================================

After implementation, verify the ACTUAL FEATURE.

Use the strongest available evidence, in this order:

1. automated behavioral tests
2. config validation scripts and install checks
3. build/compile or script validation
4. integration checks
5. focused manual verification

Do not stop at "the config changed" or "the script runs" when the real feature has observable behavior that can be tested.

For image-editing features, verify relevant output characteristics whenever possible.
For UI/config features, verify actual user-visible behavior and stability of the install/deployment path.

If verification fails:
- diagnose the failure;
- fix it;
- rerun verification.

Do not mark the task complete while known verification failures remain.

==================================================
7. CHECK FOR REGRESSIONS
==================================================

Before declaring success:

- inspect `git diff`
- run relevant existing tests
- ensure unrelated functionality was not broken
- ensure no debugging artifacts remain
- ensure no credentials/secrets were added

If the task exposed an unrelated issue, do not silently expand scope.
Record it in `.ralph/KNOWN_ISSUES.md`.

==================================================
8. UPDATE PERSISTENT STATE
==================================================

Update:

- .ralph/CURRENT_TASK.md
- .ralph/PROGRESS.md
- .ralph/RUN_STATE.json
- .ralph/IMPLEMENTATION_PLAN.md
- .ralph/PHOTOSHOP_FEATURE_MATRIX.md
- .ralph/DECISIONS.md if a durable decision was made
- .ralph/KNOWN_ISSUES.md if a reproducible issue was discovered

The feature matrix must reflect the TRUE verification state.

Do not change a feature to "complete" simply because implementation exists.

Record:
- what was changed;
- what was tested;
- exact verification commands;
- verification result;
- commit hash;
- important discoveries;
- the next recommended task.

==================================================
9. GIT CHECKPOINT
==================================================

Create a focused Git commit after verification.

The commit should describe the actual completed work.

==================================================
10. FINAL OBJECTIVE
==================================================

The working product is PhotoGIMP, and the desired direction is a PhotoCraft-inspired UI layered over the already-functional Photoshop-style feature set.

Do not let the project drift back into a generic GIMP-only customization task. Keep the feature power and upgrade the elegance.

Do not commit:
- credentials
- OAuth tokens
- cookies
- API keys
- machine-local secrets
- unrelated files

==================================================
11. ANTI-LAZINESS RULE
==================================================

You have unlimited future iterations.

Do NOT optimize for making the plan look completed.

Optimize for:
- correctness
- real feature behavior
- testability
- maintainability
- small reversible changes
- evidence

A feature that is partially implemented or insufficiently tested MUST remain
marked incomplete.

A large feature must be decomposed instead of falsely marked complete.

If you discover that previous iterations were too shallow, reopen their
feature status and correct the persistent state.

==================================================
12. STOP CONDITION
==================================================

After completing and verifying ONE bounded task:

- update persistent state;
- create the Git checkpoint;
- STOP.

Do not immediately start another task.

A future Antigravity session will continue from the repository state.

==================================================
13. PROJECT COMPLETION
==================================================

The entire project may ONLY be marked COMPLETE when:

- the Photoshop feature inventory has been systematically evaluated;
- implemented features have objective verification evidence;
- incomplete/blocked features are explicitly documented;
- required build/tests/quality gates pass;
- no critical known issue remains;
- the implementation plan matches the actual repository state.

Never mark the project complete merely because all current checkboxes happen
to be checked.
