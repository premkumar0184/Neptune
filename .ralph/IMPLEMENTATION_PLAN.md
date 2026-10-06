# Implementation Plan — Linux Photo Editor

Status: BOOTSTRAP_PENDING

This file is the authoritative list of project work.

## Product objective

Create a polished Linux photo editor from the supplied GIMP repository while preserving useful existing capabilities.

Do not invent major product requirements. Derive the concrete plan from:
1. the supplied repository;
2. explicit user requirements;
3. technical constraints discovered during inspection.

## Phase 0 — Repository archaeology

- [ ] Identify repository version/commit and current Git state.
- [ ] Identify build system and supported build procedure.
- [ ] Identify test suites and strongest practical verification commands.
- [ ] Map application entry point and major UI/toolkit components.
- [ ] Map image/document data structures and core editing pipeline.
- [ ] Identify plugin/extension interfaces.
- [ ] Build the unmodified repository, or document the exact blocker.
- [ ] Record architecture findings in `.ralph/DECISIONS.md`.

## Phase 1 — Product foundation

- [ ] Define target Linux UX and supported desktop environments.
- [ ] Define initial product feature set from the user's brief.
- [ ] Define window/layout/navigation behavior.
- [ ] Define document lifecycle: create/open/save/export/close/recovery.
- [ ] Define explicit non-goals to prevent scope growth.

## Phase 2 — Core editing experience

- [ ] Reliable image import/display.
- [ ] Required selections/transforms.
- [ ] Required layers/layer operations.
- [ ] Undo/redo.
- [ ] Required photo adjustments.
- [ ] Focused regression tests for modified behavior.

## Phase 3 — Linux application UX

- [ ] Startup/shutdown.
- [ ] File dialogs/recent documents.
- [ ] Keyboard shortcuts.
- [ ] HiDPI/scaling.
- [ ] Theme behavior if required.
- [ ] Packaging/distribution.
- [ ] Desktop integration.

## Phase 4 — Reliability/performance

- [ ] Measure startup bottlenecks.
- [ ] Measure expensive image operations.
- [ ] Verify memory behavior with large images.
- [ ] Verify undo/redo under realistic workloads.
- [ ] Add regression coverage for discovered failures.
- [ ] Do not optimize without measurements.

## Phase 5 — Quality gate

- [ ] Full build succeeds.
- [ ] Relevant automated tests pass.
- [ ] Static checks pass where available.
- [ ] Basic manual smoke test documented.
- [ ] No release-blocking issue remains.
- [ ] Final Git state is clean or intentionally documented.

## Planning rules

- Split tasks that cannot be implemented and verified in one iteration.
- Keep tasks ordered by dependency.
- Never check a box without evidence.
- Update the plan when new verified information changes the order or scope.
