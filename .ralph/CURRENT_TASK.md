# Current Task — Iteration 54

## Task
**Phase 52 — Non-Destructive Selection & Layer Stroke Helper Plugin (`python-fu-stroke-layer`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 355: "Stroke a selection or layer with color", line 358: "Fill a selection or layer with color", line 387: "Modify fill and stroke for shapes", line 154: "Add a stroke to a frame", and `photoshop_docs.md` Section 345 lines 10280-10305: "Edit > Stroke: Learn how to apply a colored stroke to a selection or layer in professional photoeditor to enhance visual impact or define edges"), stroking a selection or layer boundary with a specified border width, positioning (Inside, Center, Outside), color, opacity, and blend mode is one of the most essential graphic design, illustration, and photo retouching operations.

Stock GIMP provides only `gimp-drawable-edit-stroke-selection`, which:
1. Destructively modifies the active layer pixels directly with no undoable non-destructive layer separation.
2. Lacks Photoshop's explicit Inside, Center, and Outside geometric boundary positioning options.
3. Fails when no selection is active instead of automatically falling back to stroking the active layer's alpha/content boundary.
4. Lacks integration with professional blend modes, custom opacity, and attached editable layer masks.

Implementing native GIMP 3.x Python 3 plugin `stroke-layer` closes this gap with complete Photoshop parity:
1. `python-fu-stroke-layer`:
   - Positioning Geometries:
     - `inside`: Stroke is placed strictly inside the selection/layer boundary (via selection erosion/shrink subtraction).
     - `outside`: Stroke is placed strictly outside the selection/layer boundary (via selection dilation/grow subtraction).
     - `center`: Stroke is centered symmetrically straddling the boundary edge (via balanced dilation and erosion subtraction).
   - Width control: Configurable from 1 to 100 pixels.
   - Color selection:
     - `foreground`: Uses current GIMP context foreground color (Photoshop default).
     - `black`: Solid black border.
     - `white`: Solid white border.
     - `custom`: Explicit RGB sliders (`custom-r`, `custom-g`, `custom-b` from 0.0 to 1.0).
   - Output options:
     - `new-layer`: Dedicated stroke layer preserving source artwork with zero pixel degradation (`diff == 0.000000`).
     - `in-place`: Legacy destructive direct layer painting.
   - Professional Blend Modes: Normal, Multiply, Screen, Overlay, Soft Light.
   - Editable Layer Masks: None, Reveal-All (white), Conceal-All (black), Selection.
   - Layer Alpha Fallback: If no selection is active, automatically targets the non-transparent content boundary of the active layer.
   - Single-Step Undo Protection: All operations encapsulated within `image.undo_group_start()` and `image.undo_group_end()`.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/stroke-layer/stroke-layer.py` (New plugin implementing `python-fu-stroke-layer`)
- `PhotoGIMP/scripts/verify_config.py` (Register `stroke-layer` in `REQUIRED_PLUGINS`, updating audit inventory to 46 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 47: `test_stroke_layer`, assertions SL-01 through SL-14)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Selection & Layer Stroke Helper entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 52 status and schedule Phase 53)
- `.ralph/PROGRESS.md` (Log Iteration 54 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 54 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/stroke-layer/` created with `stroke-layer.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure registered in GIMP PDB:
   - `python-fu-stroke-layer` under `<Image>/Edit/Stroke Selection (Non-Destructive)...`, `<Image>/Layer/Stroke Layer...`, `<Image>/Filters/Retouching`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 47):
   - SL-01: Procedure lookup and argument signatures verified across all properties.
   - SL-02: Execution status verified (PDB status SUCCESS).
   - SL-03: Inside stroke geometry verified (stroke pixels strictly inside boundary, center transparent, outside transparent).
   - SL-04: Outside stroke geometry verified (stroke pixels strictly outside boundary, interior transparent, exterior transparent).
   - SL-05: Center stroke geometry verified (stroke pixels symmetrically span boundary, interior and exterior beyond stroke transparent).
   - SL-06: Stroke width scaling verified (e.g. 8px width generates accurate 8px band).
   - SL-07: Custom RGB color application verified (accurate color assignment e.g. green `[0.0, 1.0, 0.0]`).
   - SL-08: Foreground color default application verified (accurate extraction from GIMP context foreground).
   - SL-09: Blend modes and opacity verified (Multiply, Screen, Overlay, Soft Light & 75% opacity validated).
   - SL-10: Layer alpha fallback when selection is empty verified (strokes layer content boundary).
   - SL-11: Conceal-All black layer mask verified (composite diff == 0.000000).
   - SL-12: Reveal-All white layer mask attachment verified.
   - SL-13: Active selection mask confinement verified.
   - SL-14: Base layer pixel preservation verified (original source pixels 100% untouched with diff == 0.000000).
5. [x] `verify_config.py` Section 6 passes with all 46 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement non-destructive selection and layer stroke helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 54 - selection and layer stroke helper plugin`
