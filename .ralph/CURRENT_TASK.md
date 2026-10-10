# Current Task — Iteration 80

## Task
**Phase 78 — Straighten & Content-Aware Crop Fill Helper Plugin (`straighten-crop`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 177-178: "Straighten tilted photos", "Apply Content-Aware Fill while cropping images"; `photoshop_docs.md` Section 181 lines 5311-5327, Section 182 lines 5328-5342: "Learn how to use Content-Aware Fill in photoeditor to automatically fill empty spaces when cropping, rotating, straightening, or expanding images... Select the Straighten tool from the Options bar, then drag a line along an edge in the tilted image... Automatically calculates rotation angle and rotates the image to level the horizon..."):
1. **Horizon Leveling / Two-Point Straighten Tool**:
   - Allows users to measure the tilt of an image by specifying a baseline line between $(x_1, y_1)$ and $(x_2, y_2)$ along an edge that should be horizontal (horizon line, table surface) or vertical (building pillar, flagpole).
   - Computes $\theta = \text{atan2}(y_2 - y_1, x_2 - x_1)$ in degrees and automatically determines the required corrective leveling angle $\phi$ to make the baseline exactly parallel to the X or Y axis.
2. **Crop & Bounding Modes**:
   - Rotating an image introduces empty corner wedges. Photoshop provides 3 modes:
     a. `content-aware-fill`: Automatically fills empty corner wedges using Content-Aware Inpainting (sampling boundary pixels, texture synthesis, and smooth diffusion) so the image remains a full rectangular photograph with zero transparent wedges.
     b. `crop-inner` (Auto-Crop / Inner Fit): Computes the maximum inscribed orthogonal rectangle inside the rotated boundary maintaining aspect ratio, trimming away all transparent wedges.
     c. `expand-canvas`: Expands the document canvas to the outer bounding box ($W' = |W \cos\phi| + |H \sin\phi|$, $H' = |W \sin\phi| + |H \cos\phi|$).
3. **Resampling & Inverse Warping**:
   - High-fidelity backward rotation mapping with bilinear interpolation resamples source pixels smoothly without aliasing or artifacts.
4. **Non-Destructive vs Canvas Crop**:
   - Non-destructive mode outputs to `"<Layer Name> (Straightened)"`, preserving source layer and base canvas pixels 100% untouched (`diff == 0.000000`).
   - Canvas mode resizes and updates document canvas.
5. **Angle Measurement Helper (`python-fu-measure-straighten-angle`)**:
   - Calculates baseline angle $\theta$, computes corrective rotation angle $\phi$, and persists metadata in image parasite `photogimp/straighten-angle`.
6. **Undo Group Encapsulation**:
   - Single-step undo group encapsulation and active undo stack maintenance.

Stock GIMP provides uniform rotate (`gimp-drawable-transform-rotate`), but lacks an automated horizon leveling tool, automatic inner-inscribed crop calculation, or Content-Aware Fill for rotating/straightening empty corner wedges. Implementing `straighten-crop` brings complete Photoshop parity to Linux photo editing.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/straighten-crop/straighten-crop.py` (New plugin implementing 2 PDB procedures: `python-fu-straighten-crop` and `python-fu-measure-straighten-angle`)
- `PhotoGIMP/scripts/verify_config.py` (Register `straighten-crop` in `REQUIRED_PLUGINS`, updating audit inventory to 72 plugins)
- `PhotoGIMP/install.sh` (Batch deployment deploys all plug-ins to `~/.config/GIMP/3.2/plug-ins`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 73: `test_straighten_crop`, assertions SC-01 through SC-16)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Straighten & Content-Aware Crop Fill entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 78 status)
- `.ralph/PROGRESS.md` (Log Iteration 80 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 80 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/straighten-crop/` created with `straighten-crop.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] 2 PDB procedures registered in GIMP PDB:
   - `python-fu-straighten-crop` under `<Image>/Tools/Transform Tools/Straighten...` and `<Image>/Image/Transform/Straighten & Crop...`
   - `python-fu-measure-straighten-angle` under `<Image>/Tools/Transform Tools/Measure Straighten Angle...`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 73):
   - SC-01: Procedure signatures and argument audit across both procedures.
   - SC-02: Horizon baseline angle calculation (`python-fu-measure-straighten-angle`) and parasite persistence.
   - SC-03: Two-point leveling execution: tilted line rotated to true horizontal (slope == 0).
   - SC-04: Vertical baseline leveling: vertical tilt straightened to true verticality (slope == $\infty$).
   - SC-05: Explicit angle parameter rotation mode.
   - SC-06: Content-Aware Fill mode: empty corner wedges filled with boundary colors (alpha == 1.0 everywhere).
   - SC-07: Inscribed inner-crop mode (`crop-mode="crop-inner"`): trimmed to maximum rectangle without transparent pixels.
   - SC-08: Inscribed inner-crop aspect ratio fidelity: maintains source document aspect ratio.
   - SC-09: Expand canvas mode (`crop-mode="expand-canvas"`): expands to exact bounding box dimensions.
   - SC-10: Rotational center preservation: center of rotation accurately preserved.
   - SC-11: Bilinear resampling fidelity: smooth gradient interpolation without artifacts.
   - SC-12: Non-destructive layer mode: outputs to `"<Name> (Straightened)"` without modifying original.
   - SC-13: Canvas crop mode: resizes canvas to straightened dimensions when `crop-canvas=True`.
   - SC-14: Undo group encapsulation: single-step undo group across all operations.
   - SC-15: Active undo stack maintained throughout execution.
   - SC-16: Target & base canvas artwork preservation (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 72 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement straighten and content-aware crop fill helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 80 - straighten and content-aware crop fill helper plugin`
