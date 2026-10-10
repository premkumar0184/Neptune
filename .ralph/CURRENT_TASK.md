# Current Task — Iteration 78

## Task
**Phase 76 — Content-Aware Scale & Intelligent Seam Carving Helper Plugin (`content-aware-scale`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 163-164: "Preserve visual content when scaling images", "Specify content to protect when scaling"; `photoshop_docs.md` Section 167 lines 4919-4943: "Learn how to use Content-Aware Scale in photoeditor to resize images while protecting important details and proportions... Select Edit > Content-Aware Scale... In the Options bar: Reference Point Location, Scaling Percentage / Width and Height, Amount [control the ratio of content-aware scaling to normal scaling], Protect [alpha channel or selection], Protect Skin Tones [preserve regions with skin tones]"):
1. **Intelligent Seam Carving**:
   - Resizes images (width and height reduction or expansion) by finding and removing or duplicating paths of least resistance (low-energy seams) across the image.
   - Preserves high-energy foreground subjects (people, buildings, contrast edges) at their exact proportions and scale while carving or expanding low-energy background areas (sky, water, solid colors, smooth gradients).
2. **Skin Tone Protection (`protect-skin-tones`)**:
   - Detects human skin tones based on RGB and YCbCr chromaticity rules ($R > G > B$ with skin chrominance constraints).
   - Injects a high energy barrier over skin pixels so seams navigate around human faces, limbs, and portrait subjects.
3. **Selection / Channel Mask Protection (`protect-mask`)**:
   - Allows users to designate arbitrary regions (via active selection or channel) to protect with an infinite energy barrier ($W_{\text{protect}} = 10000.0$), ensuring zero seams cross the user-specified subject.
4. **Photoshop "Amount" Slider ($0\% \dots 100\%$)**:
   - Controls the ratio of content-aware scaling to normal scaling:
     - 100%: Pure Content-Aware Seam Carving.
     - 0%: Standard uniform scaling.
     - Intermediate values (e.g. 50%): Linear blend interpolation between uniform resampling and seam-carved retargeting.
5. **Reference Point Alignment & Canvas Management**:
   - Anchors the scaled layer at Center, Top-Left, Top, Top-Right, Left, Right, Bottom-Left, Bottom, or Bottom-Right.
   - Non-destructive mode: creates `"<Layer Name> (Content-Aware Scaled)"`, leaving original source layers 100% untouched (`diff == 0.000000`).
6. **Energy Map Visualization**:
   - `python-fu-content-aware-energy-map`: Renders the calculated gradient and skin energy map as an inspection layer.

Stock GIMP provides uniform scaling tools (`gimp-image-scale`, `gimp-drawable-transform-scale`) but lacks native Content-Aware Scale or Seam Carving in GIMP 3.0. Implementing `content-aware-scale` brings complete Photoshop parity to Linux photo editing.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/content-aware-scale/content-aware-scale.py` (New plugin implementing 2 PDB procedures: `python-fu-content-aware-scale` and `python-fu-content-aware-energy-map`)
- `PhotoGIMP/scripts/verify_config.py` (Register `content-aware-scale` in `REQUIRED_PLUGINS`, updating audit inventory to 70 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 71: `test_content_aware_scale`, assertions CAS-01 through CAS-16)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Content-Aware Scale entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 76 status)
- `.ralph/PROGRESS.md` (Log Iteration 78 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 78 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/content-aware-scale/` created with `content-aware-scale.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] 2 PDB procedures registered in GIMP PDB:
   - `python-fu-content-aware-scale` under `<Image>/Edit/Content-Aware Scale...`, `<Image>/Tools/Transform Tools/Content-Aware Scale...`, and `<Image>/Layer/Transform/Content-Aware Scale...`
   - `python-fu-content-aware-energy-map` under `<Image>/Filters/Enhance/Content-Aware Energy Map...` and `<Image>/Layer/Transform/Energy Map...`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 71):
   - CAS-01: Procedure signatures and argument audit across both procedures.
   - CAS-02: Seam removal (reducing width): low-energy background is carved while high-energy subject maintains 100% width.
   - CAS-03: Seam insertion (expanding width): low-energy background is expanded while high-energy subject maintains exact width.
   - CAS-04: Seam removal (reducing height): vertical dimension reduced with horizontal features preserved.
   - CAS-05: Seam insertion (expanding height): vertical dimension expanded with horizontal features preserved.
   - CAS-06: Skin tone protection (`protect-skin-tones=True`): skin tone detection elevates energy so seams bypass skin subject.
   - CAS-07: Skin tone protection disabled (`protect-skin-tones=False`): seams pass through when skin protection is off.
   - CAS-08: Protected selection mask: active selection receives energy penalty so seams strictly avoid selection.
   - CAS-09: Amount slider (100% vs 50% vs 0%): controls ratio of content-aware scaling to uniform scaling.
   - CAS-10: Simultaneous 2D retargeting (both width and height scaled).
   - CAS-11: Reference point positioning (Center, Top-Left, Bottom-Right) properly offsets the layer.
   - CAS-12: Non-destructive layer mode: creates `"<Layer Name> (Content-Aware Scaled)"` leaving source intact.
   - CAS-13: Energy map preview procedure (`python-fu-content-aware-energy-map`) outputs valid heatmap.
   - CAS-14: Single-step undo group encapsulation across operations.
   - CAS-15: Active undo stack maintained.
   - CAS-16: Target & base canvas artwork preservation (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 70 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement content-aware scale and intelligent seam carving helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 78 - content-aware scale and intelligent seam carving helper plugin`
