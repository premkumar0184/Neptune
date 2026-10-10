# Current Task — Iteration 79

## Task
**Phase 77 — Perspective Crop & Keystone Rectification Helper Plugin (`perspective-crop`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 179: "Transform perspective while cropping"; `photoshop_docs.md` Section 183 lines 5345-5362: "Learn how to use the Perspective Crop tool in professional photoeditor to straighten images and correct distorted angles while cropping. Hold down the Crop tool in the Tools panel, then select the Perspective Crop tool. Draw a marquee around the object to straighten and crop. Adjust the corners of the marquee to match the edges of the object. Press Enter (Windows) or Return (macOS)"):
1. **Perspective Keystone Rectification**:
   - Objects captured at oblique camera angles (such as architecture, paintings, posters, whiteboards, documents, tilted horizons) suffer from projective keystone distortion where parallel lines converge and rectangular boundaries become trapezoids.
   - The Perspective Crop tool lets users place 4 arbitrary quadrilateral corner control points $(x_0, y_0)$ Top-Left, $(x_1, y_1)$ Top-Right, $(x_2, y_2)$ Bottom-Right, and $(x_3, y_3)$ Bottom-Left around the subject.
2. **Projective Homography Transformation**:
   - Computes the exact $3 \times 3$ projective homography transformation matrix mapping the distorted quadrilateral into an orthogonal planar rectangle $(0, 0) \to (W-1, H-1)$.
   - Solves the inverse mapping $M = H^{-1}$ using 8 linear boundary equations ($A m = b$) to eliminate keystone distortion.
3. **Resampling & Interpolation**:
   - High-fidelity backward mapping with bilinear interpolation resamples source pixels smoothly without holes, aliasing, or artifacts.
4. **Dimension & Aspect Ratio Control**:
   - Allows users to specify explicit output width & height, or auto-calculates dimensions from the quadrilateral's average edge lengths ($\text{Width} = \frac{\|P_1 - P_0\| + \|P_2 - P_3\|}{2}$, $\text{Height} = \frac{\|P_3 - P_0\| + \|P_2 - P_1\|}{2}$).
5. **Crop Modes (Non-Destructive Layer vs Whole Canvas Crop)**:
   - Output to a dedicated rectified layer `"<Layer Name> (Perspective Cropped)"` preserving original layers intact (`diff == 0.000000`), or resize/crop the document canvas to the rectified crop bounds.
6. **Auto Quad Helper (`python-fu-perspective-auto-quad`)**:
   - Computes default quadrilateral control points matching active selection bounds or layer geometry with optional margin or keystone presets.
7. **Undo Group Encapsulation**:
   - Full single-step undo group encapsulation and active undo stack maintenance.

Stock GIMP provides uniform crop (`gimp-image-crop`) and perspective transformation (`gimp-drawable-transform-perspective`), but lacks a dedicated Perspective Crop tool that unwarps arbitrary 4-point quadrilaterals directly into orthogonal rectified documents or cropped layers. Implementing `perspective-crop` brings complete Photoshop parity to Linux photo editing.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/perspective-crop/perspective-crop.py` (New plugin implementing 2 PDB procedures: `python-fu-perspective-crop` and `python-fu-perspective-auto-quad`)
- `PhotoGIMP/scripts/verify_config.py` (Register `perspective-crop` in `REQUIRED_PLUGINS`, updating audit inventory to 71 plugins)
- `PhotoGIMP/install.sh` (Batch deployment deploys all plug-ins to `~/.config/GIMP/3.2/plug-ins`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 72: `test_perspective_crop`, assertions PC-01 through PC-16)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Perspective Crop entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 77 status)
- `.ralph/PROGRESS.md` (Log Iteration 79 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 79 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/perspective-crop/` created with `perspective-crop.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] 2 PDB procedures registered in GIMP PDB:
   - `python-fu-perspective-crop` under `<Image>/Tools/Transform Tools/Perspective Crop...` and `<Image>/Image/Transform/Perspective Crop...`
   - `python-fu-perspective-auto-quad` under `<Image>/Tools/Transform Tools/Perspective Auto Quad...`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 72):
   - PC-01: Procedure signatures and argument audit across both procedures.
   - PC-02: Auto quad detection (`python-fu-perspective-auto-quad`) from layer / selection bounds.
   - PC-03: Planar keystone rectification: trapezoidal converging quad straightened into rectangular output.
   - PC-04: Dimensional fidelity: output width and height match requested dimensions exactly.
   - PC-05: Auto-calculated dimensions: output dimensions computed from average quad edge lengths when set to 0.
   - PC-06: Orthogonal corner alignment: 4 corners of subject quad mapped to exact boundary pixels of output.
   - PC-07: Parallel line restoration: vertical lines in skewed quadrilateral restored to true verticality (parallel to Y axis).
   - PC-08: Horizontal line restoration: horizontal lines in skewed quadrilateral restored to true horizontality (parallel to X axis).
   - PC-09: Centered feature fidelity: diagonal intersection / center coordinate preserved at output center.
   - PC-10: Resampling interpolation: smooth bilinear interpolation without pixel gaps or discontinuities.
   - PC-11: Non-destructive layer mode: outputs to `"<Name> (Perspective Cropped)"` without modifying source layer.
   - PC-12: Canvas crop mode: resizes canvas to rectified rectangle when `crop-canvas=True`.
   - PC-13: Alpha channel preservation: transparency outside cropped quad handled cleanly.
   - PC-14: Undo group encapsulation: single-step undo group across all operations.
   - PC-15: Active undo stack maintained throughout execution.
   - PC-16: Target & base canvas artwork preservation (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 71 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement perspective crop and keystone rectification helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 79 - perspective crop and keystone rectification helper plugin`
