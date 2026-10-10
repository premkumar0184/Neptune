# Current Task — Iteration 81

## Task
**Phase 79 — Free Transform & Repeat Transform (Transform Again) Helper Plugin (`transform-again`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 180-187: "Transformation options in Photoshop", "Rotate or flip images", "Adjust scale, rotation, and perspective", "Duplicate objects as you transform", "Apply transformations", "Move reference point for transformations", "Rotate objects"; `photoshop_docs.md` Section 184-189 lines 5365-5499: "In complex photoeditor designs, you often need duplicate objects in varying sizes, angles, or positions. Instead of replicating and transforming separately, use a shortcut to do both simultaneously... Press Ctrl+Alt+T to create a duplicate and enter Free Transform mode... Select Edit > Transform > Again to repeat a transformation... Shift+Ctrl+T / Shift+Ctrl+Alt+T... Move reference point for transformations: 9-point anchor or custom origin"):
1. **Free Transform with Duplicate (`Ctrl+Alt+T`)**:
   - Replicates active layer/object and simultaneously applies affine transformations (Scale, Rotation, Translation offset, Skew) while preserving original source layer intact (`diff == 0.000000`).
   - Supports 9-point reference point anchor positioning (Top-Left, Top, Top-Right, Left, Center, Right, Bottom-Left, Bottom, Bottom-Right) or arbitrary custom coordinate origin $(x_0, y_0)$.
2. **Transform Again (`Shift+Ctrl+T`)**:
   - Reapplies the exact remembered affine transformation parameters or composite matrix from the previous transform operation to the active layer directly in-place.
3. **Transform Again with Duplicate (`Shift+Ctrl+Alt+T`)**:
   - Replicates the active layer and applies the remembered transformation to the duplicate. When executed repeatedly (or with a `count` parameter), produces compounded geometric step-and-repeat arrays, radial bursts/starbursts, spiral cascades, and isometric progressions.
4. **Parasite Persistence (`photogimp/last-transform`)**:
   - Persists transformation parameters (`scale_x`, `scale_y`, `link_scale`, `angle`, `offset_x`, `offset_y`, `skew_x`, `skew_y`, `reference_point`, `custom_origin_x`, `custom_origin_y`, `interpolation`, `resize_mode`, `matrix`) in image parasite for cross-operation continuity.
5. **Undo Group Encapsulation**:
   - Encapsulates entire multi-step or looping operations in single-step undo groups with active undo stack maintenance.

GIMP 3.x has individual transform tools, but lacks automated duplicate-and-transform (`Ctrl+Alt+T`), repeat transform again (`Shift+Ctrl+T`), step-and-repeat arrays (`Shift+Ctrl+Alt+T`), and 9-point reference anchor positioning. Implementing `transform-again` closes this vital Photoshop workflow gap.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/transform-again/transform-again.py` (New plugin implementing 3 PDB procedures: `python-fu-free-transform-duplicate`, `python-fu-transform-again`, and `python-fu-transform-again-duplicate`)
- `PhotoGIMP/scripts/verify_config.py` (Register `transform-again` in `REQUIRED_PLUGINS`, updating audit inventory to 73 plugins)
- `PhotoGIMP/install.sh` (Batch deployment deploys all plug-ins to `~/.config/GIMP/3.2/plug-ins`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 74: `test_transform_again`, assertions TA-01 through TA-16)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Free Transform & Repeat Transform entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 79 status)
- `.ralph/PROGRESS.md` (Log Iteration 81 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 81 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/transform-again/` created with `transform-again.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] 3 PDB procedures registered in GIMP PDB:
   - `python-fu-free-transform-duplicate` under `<Image>/Edit/Free Transform with Duplicate...`, `<Image>/Layer/Transform/Free Transform with Duplicate...`, and `<Image>/Tools/Transform Tools/Free Transform with Duplicate...`
   - `python-fu-transform-again` under `<Image>/Edit/Transform/Again` and `<Image>/Layer/Transform/Transform Again`
   - `python-fu-transform-again-duplicate` under `<Image>/Edit/Transform/Again and Duplicate` and `<Image>/Layer/Transform/Transform Again and Duplicate`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 74):
   - TA-01: Procedure signatures and argument audit across all 3 procedures.
   - TA-02: Free Transform with Duplicate execution: creates duplicate layer preserving original intact.
   - TA-03: Center anchor rotation and scaling: transforms around center reference point.
   - TA-04: Top-Left anchor rotation: corner remains stationary while rest of layer rotates.
   - TA-05: 9-point reference anchor resolution across all positions (Top-Left, Top, Top-Right, Left, Center, Right, Bottom-Left, Bottom, Bottom-Right).
   - TA-06: Custom origin coordinate anchor positioning.
   - TA-07: In-place transformation mode (`duplicate_layer=False`): transforms target layer directly.
   - TA-08: Transform Again (`python-fu-transform-again`): reapplies remembered transformation parameters in-place.
   - TA-09: Transform Again with Duplicate (`python-fu-transform-again-duplicate`): duplicates and applies transform.
   - TA-10: Compounded step-and-repeat arrays (`count > 1`): generates cascading multi-layer transformations.
   - TA-11: Horizontal and vertical skewing fidelity.
   - TA-12: Parasite persistence and deserialization (`photogimp/last-transform`).
   - TA-13: Interpolation modes (Cubic, Linear, None).
   - TA-14: Undo group encapsulation: single-step undo group across single and multi-count transforms.
   - TA-15: Active undo stack maintained throughout execution.
   - TA-16: Target & base canvas artwork preservation (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 73 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement free transform with duplicate and transform again helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 81 - free transform with duplicate and transform again helper plugin`
