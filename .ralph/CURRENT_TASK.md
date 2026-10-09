# Current Task — Iteration 70

## Task
**Phase 68 — Global Lighting & Layer Style Effects Manager Plugin Suite (`python-fu-global-light`, `python-fu-scale-layer-effects`, `python-fu-copy-layer-style`, `python-fu-paste-layer-style`, `python-fu-clear-layer-style`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 111-120; `photoshop_docs.md` Section 116-121 lines 3550-3665: "Set a global lighting angle for all layers", "Scale layer effects", "Copy and paste layer styles", "Remove layer effects", "Display or hide layer styles"), layer styles are not isolated one-off effects; they form an integrated system managed collectively:
1. **Global Light** (`Layer > Layer Style > Global Light...`): Synchronizes directional lighting angle (-180° to 180°) and altitude (0° to 90°) across all directional effects in the document (Drop Shadow, Inner Shadow, Bevel & Emboss) to ensure visual coherence.
2. **Scale Layer Effects** (`Layer > Layer Style > Scale Effects...`): Proportionally rescales the size, distance, and blur radius (10% to 500%) across all attached layer style layers when scaling artwork or canvases.
3. **Copy & Paste Layer Styles** (`Layer > Layer Style > Copy Layer Style` / `Paste Layer Style`): Allows copying the full suite of layer styles from one layer and pasting them onto destination layers with automatic geometric adaptation.
4. **Clear Layer Style** (`Layer > Layer Style > Clear Layer Style`): One-click removal of all attached layer style layers/groups, leaving the underlying target artwork 100% untouched (`diff == 0.000000`).

Stock GIMP provides no built-in equivalents for managing layer style suites across layers. Implementing `layer-style-manager` completes the Photoshop layer style ecosystem in PhotoGIMP.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/layer-style-manager/layer-style-manager.py` (New plugin implementing all 5 PDB procedures)
- `PhotoGIMP/scripts/verify_config.py` (Register `layer-style-manager` with its 5 procedures in `REQUIRED_PLUGINS`, updating audit inventory to 62 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 63: `test_layer_style_manager`, assertions LSM-01 through LSM-16)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Global Lighting & Layer Style Manager entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 68 status)
- `.ralph/PROGRESS.md` (Log Iteration 70 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 70 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/layer-style-manager/` created with `layer-style-manager.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] 5 PDB procedures registered in GIMP PDB:
   - `python-fu-global-light` under `<Image>/Layer/Layer Style/Global Light...` and `<Image>/Filters/Light and Shadow`
   - `python-fu-scale-layer-effects` under `<Image>/Layer/Layer Style/Scale Effects...` and `<Image>/Filters/Light and Shadow`
   - `python-fu-copy-layer-style` under `<Image>/Layer/Layer Style/Copy Layer Style`
   - `python-fu-paste-layer-style` under `<Image>/Layer/Layer Style/Paste Layer Style`
   - `python-fu-clear-layer-style` under `<Image>/Layer/Layer Style/Clear Layer Style`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 63):
   - LSM-01: Procedure lookup and argument signatures verified across all 5 procedures.
   - LSM-02: Global Light sets and retrieves image parasite lighting angles.
   - LSM-03: Global Light updates directional parameters across attached style layers.
   - LSM-04: Scale Layer Effects scales size/distance properties proportionally (e.g. 200%).
   - LSM-05: Copy Layer Style serializes attached styles to clipboard parasite.
   - LSM-06: Paste Layer Style replicates copied styles onto destination layer.
   - LSM-07: Pasted style layers correctly positioned relative to destination layer.
   - LSM-08: Clear Layer Style removes all attached style layers from target layer.
   - LSM-09: Clear Layer Style leaves target layer artwork 100% untouched (`diff == 0.000000`).
   - LSM-10: Clear Layer Style leaves unrelated layers in stack untouched.
   - LSM-11: Scale Effects rescales multi-style compound layer stacks.
   - LSM-12: Global Light altitude modulation verified.
   - LSM-13: Style clipboard persists across active image operations.
   - LSM-14: Graceful handling of layers with no styles attached (no-op SUCCESS).
   - LSM-15: Single-step undo group encapsulation verified across operations.
   - LSM-16: Target and base layer artwork preserved with zero degradation (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 62 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement global lighting and layer style manager plugin suite`
- Outer repository commit: `feat(ralph): complete iteration 70 - global lighting and layer style manager plugin suite`
