# Current Task — Iteration 44

## Task
**Phase 42 — Non-Destructive Iris Blur & Vignette Bokeh Helper Plugin (`python-fu-iris-blur`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 465: "Use Blur Gallery depth-of-field effects", line 460: "Overview of adding blur to images", line 461: "Create depth of field with lens blur", line 659: "Blur image backgrounds", and `photoshop_docs.md` Section 424 line 12334: "Blur Gallery: Interactive, on-canvas tools like Field Blur, Iris Blur, and Tilt-Shift that let you apply blur selectively and control it visually"), Iris Blur is one of the premier Blur Gallery tools. While Tilt-Shift provides linear planar focus, Iris Blur provides selective shallow depth of field around an elliptical focal subject (such as portrait faces, macro flowers, food, product isolation, or candid street subjects).
In Photoshop, users configure:
1. Focal Center: normalized `(x, y)` coordinates of the in-focus subject.
2. In-Focus Subject Radius: elliptical focus region where the subject remains 100% pin-sharp (`diff == 0.000000`).
3. Ellipse Proportion / Aspect Ratio: ratio between horizontal and vertical axes to fit face shapes or wide compositions.
4. Rotation Angle: orientation of the elliptical focus plane (0° to 360°).
5. Transition Feather / Softness: progressive gradient falloff from 100% sharp to 100% out-of-focus background.
6. Optical Blur Type: Lens Blur (optical aperture bokeh with specular highlight factor) vs Gaussian Blur (smooth digital defocus).
7. Optical Blur Radius (1.0 to 100.0px).
8. Optical Bokeh Specular Highlights (0.0 to 1.0 boost factor).
9. Curated photographic presets (Portrait Face Isolation, Macro Subject Pinpoint, Street Photography Candid, Cinematic Anamorphic Oval, Vignette Peripheral Softness, Custom sliders).
10. Layer Mask Modes (Iris Depth Mask, Inverted Depth Mask, Active Selection Mask, Full Reveal-All Mask).
11. 100% mathematical preservation of base layer pixels underneath (`diff == 0.000000`).

Stock GIMP provides no Blur Gallery Iris Blur tool. Creating native Python 3 helper plugin `python-fu-iris-blur` establishes complete Photoshop Blur Gallery parity.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/iris-blur/iris-blur.py` (New plugin)
- `PhotoGIMP/scripts/verify_config.py` (Register `iris-blur` in `REQUIRED_PLUGINS`, updating audit inventory to 36 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 37: `test_iris_blur`, 11 assertions IB-01 through IB-11)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Iris Blur & Vignette Bokeh entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 42 status and schedule Phase 43)
- `.ralph/PROGRESS.md` (Log Iteration 44 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 44 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/iris-blur/` created with `iris-blur.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure `python-fu-iris-blur` registered in GIMP PDB under:
   - `<Image>/Filters/Blur/Iris Blur...`
   - `<Image>/Filters/Blur Gallery/Iris Blur...`
   - `<Image>/Filters/Retouching`
   - `<Image>/Layer`
4. [x] Non-destructive adjustment layer created duplicating active drawable.
5. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 37):
   - Base layer pixels underneath remain 100% untouched (`diff == 0.000000`).
   - Inner focal subject center remains 100% pin-sharp (`diff == 0.000000`).
   - Outer background displays significant optical defocus blur bleed (`diff > 0.05`).
   - Portrait Face Isolation preset verified: vertical oval aspect ratio with gentle falloff.
   - Macro Subject Pinpoint preset verified: tight circular focal zone with heavy lens blur and bokeh highlights.
   - Street Photography Candid preset verified: offset focal center `(x=0.35, y=0.45)` isolating off-center subject.
   - Cinematic Anamorphic Oval preset verified: wide horizontal proportion (`mask_h < mask_v`).
   - Gaussian Blur algorithm mode verified: smooth digital defocus.
   - Inverted depth mask mode verified: blurred center with sharp outer periphery.
   - Conceal-All black layer mask verified: composite equals base layer (`diff == 0.000000`).
   - Selection-aware mask verified: iris blur confined strictly to active selection.
6. [x] `verify_config.py` Section 6 passes with all 36 required plugins audited.
7. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all stages cleanly with exit code 0 (353/353 tests passing).

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Expected Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement non-destructive iris blur and vignette bokeh plugin`
- Outer repository commit: `feat(ralph): complete iteration 44 - non-destructive iris blur plugin`
