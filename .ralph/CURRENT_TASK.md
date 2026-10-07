# Current Task — Iteration 41

## Task
**Phase 39 — Non-Destructive Lens Distortion & Perspective Correction Helper Plugin (`python-fu-lens-distortion`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 482: "Correct lens distortion and perspective", line 483: "Correct wide-angle lens distortion", and `photoshop_docs.md` Section 424 lines 12650-12655 "Filter > Lens Correction: Barrel Distortion: Straighten lines that curve outward from the center... Pincushion Distortion: Adjust lines that bend inward toward the image center... Vignetting: Balance brightness across your entire image"), optical camera lenses inherently suffer from geometric distortions and peripheral illumination falloff. Wide-angle and zoom lenses produce convex outward "barrel" distortion that bends horizontal horizons and vertical architectural columns, telephoto lenses cause concave inward "pincushion" distortion that pinches compositions, and optical vignetting darkens image corners. In stock GIMP, users have no unified, non-destructive optical lens correction workflow; they must rely on manual transform grids or destructive filters with no presets, no lens-specific compensation parameters, and no non-destructive adjustment layering. Creating a dedicated native Python 3 helper plugin (`python-fu-lens-distortion`) brings full Photoshop Lens Correction parity: geometric distortion amount (-100% to +100% covering inverse barrel straightening and pincushion expansion), spherical curvature (0.0 to 1.0), camera angle of view (0° to 180°), displacement mode (radial, horizontal, vertical), peripheral vignette illumination compensation (-100% to +100%), curated presets (Wide-Angle Barrel Correction, Telephoto Pincushion Correction, Fisheye Defish, Architectural Perspective Flatten, Creative Fisheye Warp, Custom), versatile layer masks (Reveal All, Conceal All, Selection), and 100% mathematical preservation of base layer source pixels underneath (`diff == 0.000000`).

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/lens-distortion/lens-distortion.py` (New plugin)
- `PhotoGIMP/scripts/verify_config.py` (Register `lens-distortion` in `REQUIRED_PLUGINS`, updating audit inventory to 33 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 34: `test_lens_distortion`, 11 assertions LD-01 through LD-11)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Lens Distortion & Perspective Correction entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 39 status and schedule Phase 40)
- `.ralph/PROGRESS.md` (Log Iteration 41 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 41 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/lens-distortion/` created with `lens-distortion.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure `python-fu-lens-distortion` registered in GIMP PDB under:
   - `<Image>/Filters/Distort/Lens Distortion...`
   - `<Image>/Filters/Retouching/Lens Distortion...`
   - `<Image>/Layer/New Lens Correction Layer...`
4. [x] Non-destructive adjustment layer created duplicating active drawable.
5. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 34):
   - Base layer pixels underneath remain 100% untouched (`diff == 0.000000`).
   - Wide-Angle Barrel Correction preset verified: Negative displacement unbends outward curved lines (delta 0.2502) and brightens optical corner vignette (1.0000 > 0.5029).
   - Telephoto Pincushion Correction preset verified: Positive displacement unpinches inward curved lines.
   - Fisheye Defish preset verified: Strong rectilinear unbending with corner illumination lift (1.0000 > 0.5029).
   - Architectural Perspective Flatten preset verified: Planar horizontal straightening mode.
   - Creative Fisheye Warp preset verified: Convex spherical bulge with edge vignette shading (0.0000 < 0.5029).
   - Vignette illumination compensation verified: Lightens dark corners without altering image center (center delta 0.0000).
   - Conceal-All black layer mask verified: Composite equals base layer (0.000000 diff) ready for brush painting.
   - Selection-aware mask verified: Distortion confined strictly to active selection (inside 1.00, outside 0.00).
   - Custom sliders with amount, curvature, angle of view, mode, and opacity verified.
6. [x] `verify_config.py` Section 6 passes with all 33 required plugins audited.
7. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all stages cleanly with exit code 0 (317/317 assertions passing in 34 test suites).

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `b5792f8`
- Outer repository commit: `feat(ralph): complete iteration 41 - non-destructive lens distortion plugin`
