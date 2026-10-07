# Current Task — Iteration 39

## Task
**Phase 37 — Non-Destructive Smart Sharpen & Optical Deconvolution Helper Plugin (`python-fu-smart-sharpen`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 460: "Apply the Smart Sharpen filter", line 462: "Sharpen images", line 463: "Adjust image sharpness and blur", and `photoshop_docs.md` Section 424 lines 12217-12255 "Filter > Sharpen > Smart Sharpen"), professional photographers rely on Smart Sharpen rather than basic Unsharp Masking because it offers advanced blur-removal algorithms (Gaussian Blur, Lens Blur with reduced haloing, and Motion Blur), integrated noise reduction (`Reduce Noise` slider) to avoid amplifying digital sensor noise in smooth or shadow areas, and non-destructive layering. In stock GIMP, users only have destructive unsharp masking or manual high-pass blending, lacking automated noise suppression, multi-algorithm optical deconvolution modes, curated presets, and non-destructive adjustment layers with layer masks. Creating a dedicated native Python 3 helper plugin (`python-fu-smart-sharpen`) provides Photoshop Smart Sharpen parity: Amount (1% to 500%), Radius (0.1 to 50.0px), Reduce Noise (0% to 100%), three blur removal modes (Lens Blur, Gaussian Blur, Motion Blur), curated presets (Default Lens Blur, Microcontrast / Fine Detail, Maximum Acutance, Motion Blur Recovery, Portrait Texture, Custom), versatile layer masks (Reveal All, Conceal All for selective edge brushing, Active Selection), and 100% mathematical preservation of base layer source pixels underneath.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/smart-sharpen/smart-sharpen.py` (New plugin)
- `PhotoGIMP/scripts/verify_config.py` (Register `smart-sharpen` in `REQUIRED_PLUGINS`, updating audit inventory to 31 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 32: `test_smart_sharpen`, 11 assertions SSH-01 through SSH-11)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Smart Sharpen entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 37 status)
- `.ralph/PROGRESS.md` (Log Iteration 39 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 39 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/smart-sharpen/` created with `smart-sharpen.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure `python-fu-smart-sharpen` registered in GIMP PDB under:
   - `<Image>/Filters/Enhance/Smart Sharpen...`
   - `<Image>/Filters/Retouching/Smart Sharpen...`
   - `<Image>/Layer/New Smart Sharpen Layer...`
4. [x] Non-destructive adjustment layer created duplicating active drawable.
5. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 32):
   - Base layer pixels underneath remain 100% untouched (`diff == 0.000000`).
   - Default Lens Blur preset verified: Edge contrast increases significantly across high-frequency boundary (0.4006 -> 0.6000, +0.1995 boost).
   - Microcontrast preset verified: High acutance sharpening on fine details (contrast 0.6702, +0.2696 boost).
   - Heavy Deconvolution preset verified: Pronounced edge definition boost (contrast 0.8301, +0.4295 boost).
   - Gaussian Blur algorithm mode verified: Traditional unsharp frequency response (contrast 0.8217).
   - Motion Blur algorithm mode verified: Enhanced directional edge sharpening (contrast 0.9301).
   - Reduce Noise parameter verified: Suppresses noise amplification in smooth regions (flat deviation 0.00054 < 0.05).
   - Conceal-All black layer mask verified: Composite equals base layer (0.000000 diff) ready for brush painting.
   - Selection-aware mask verified: Sharpening applied strictly inside active selection, outside untouched.
   - Custom sliders with opacity, amount, radius, and noise reduction verified.
6. [x] `verify_config.py` Section 6 passes with all 31 required plugins audited.
7. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all stages cleanly with exit code 0 (293/293 assertions passing in 32 test suites).

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `46301bf`
- Outer repository commit: `dc3b820`
