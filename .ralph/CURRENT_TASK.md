# Current Task — Iteration 25

## Task
**Phase 23 — Non-Destructive Film Grain & Analog Texture Helper Plugin**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 105: "Adjust texture with Grain", `photoshop_docs.md` Section 109 lines 3280-3300: "Add grain to your image non-destructively using the Grain adjustment layer in professional photoeditor"), the Grain adjustment layer non-destructively introduces organic silver halide texture, controls grain Amount, particle Size, and Roughness, and simulates authentic analog film looks (35mm, Medium Format, High-ISO Street, Vintage Color). In stock GIMP, users have to destructively apply noise filters directly to image pixels. Creating a dedicated non-destructive helper plugin provides an isolated neutral gray (`#808080`) overlay layer with Soft Light / Overlay blending, customizable Amount, Size, and Roughness, monochromatic silver halide vs color grain toggle, authentic analog presets, layer opacity, an attached reveal-all layer mask, and 100% protection of underlying source pixels.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/film-grain/film-grain.py` (New plugin)
- `PhotoGIMP/scripts/verify_config.py` (Register `film-grain` in `REQUIRED_PLUGINS`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 18: `test_film_grain`)

## Acceptance Criteria
1. [x] Plugin file exists, has shebang, is executable (`chmod +x`), and passes bytecode compilation.
2. [x] PDB procedure `python-fu-film-grain` registered in GIMP PDB under `<Image>/Filters/Noise`, `<Image>/Filters/Retouching`, and `<Image>/Layer`.
3. [x] Dedicated non-destructive Film Grain overlay layer created above active drawable with Soft Light / Overlay blend mode.
4. [x] In headless GIMP tests:
   - Base layer pixels underneath remain 100% untouched (`diff == 0.000000`).
   - Grain texture variance verified (0.007724 > 0.003 analog texture variance).
   - Monochromatic grain neutrality verified (R == G == B, max spread 0.000000).
   - Color grain mode verified (produces chromatic dye cloud spread 0.3906 > 0.01).
   - Overlay blend mode verified in Gritty Street preset (mode 23 / Overlay).
   - Custom sliders and opacity verified (Opacity 85.0%, custom Amount/Size/Roughness).
   - Reveal-all layer mask attached and editable.
5. [x] `verify_config.py` Section 6 passes with all 17 required plugins verified.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all stages cleanly with exit code 0 (131/131 tests passing).

## Verification Evidence
```
Command: python3 tests/run_all_tests.py
Result:
Stage 1: Configuration & Plugin Inventory Audit (verify_config.py) -> PASSED (17/17 plugins audited)
Stage 2: Installer Non-Interactive Deployment Test (install.sh --batch) -> PASSED (17 plugins deployed)
Stage 3: Headless GIMP Plugin Suite Regression Verification (tests/gimp_e2e_suite.py) -> PASSED:
  [PASS] PDB-REG: 17/17 plugins registered including python-fu-film-grain
  [PASS] FS-01 to FS-05: Frequency Separation (5 tests passed)
  [PASS] LM-01 to LM-04: Luminosity Masks (4 tests passed)
  [PASS] DB-01 to DB-05: Dodge & Burn Layer (5 tests passed)
  [PASS] HPS-01 to HPS-05: High Pass Sharpen (5 tests passed)
  [PASS] QE-01 to QE-05: Quick Export Suite (5 tests passed)
  [PASS] VL-01 to VL-06: Vignette & Lighting (6 tests passed)
  [PASS] DF-01 to DF-06: Depth Defocus (6 tests passed)
  [PASS] SH-01 to SH-06: Shadows & Highlights Recovery (6 tests passed)
  [PASS] BW-01 to BW-07: Black & White Conversion & Toning (7 tests passed)
  [PASS] PF-01 to PF-08: Photo Filter Optical Lens Effects (8 tests passed)
  [PASS] VIB-01 to VIB-07: Vibrance & Smart Saturation (7 tests passed)
  [PASS] CB-01 to CB-08: Color Balance & Tonal Grading (8 tests passed)
  [PASS] GM-01 to GM-09: Gradient Map & Cinematic Grading (9 tests passed)
  [PASS] CM-01 to CM-08: Channel Mixer & Infrared (8 tests passed)
  [PASS] CT-01 to CT-07: Color Temperature & White Balance (7 tests passed)
  [PASS] CD-01 to CD-08: Clarity & Dehaze (8 tests passed)
  [PASS] FG-01: Execution status (SUCCESS)
  [PASS] FG-02: Layer mode & name (Film Grain (35mm Classic Film Grain) (45))
  [PASS] FG-03: Layer mask attachment (Reveal-all mask attached)
  [PASS] FG-04: Grain texture variance (Analog silver halide variance: 0.007724 > 0.003)
  [PASS] FG-05: Monochromatic silver halide grain (Exact channel neutrality (R=G=B spread 0.000000))
  [PASS] FG-06: Vintage color dye clouds (Chromatic grain spread: 0.3906 > 0.01)
  [PASS] FG-07: Gritty street overlay blend (Punchy Overlay blend mode (23))
  [PASS] FG-08: Custom sliders & opacity (Opacity 85.0%, custom Amount 50.0% / Size 2 / Roughness 75.0% verified)
  [PASS] FG-09: Non-destructive layer preservation (Base pixels 100% untouched (diff 0.000000))
Total Tests Executed: 131
Tests Passed        : 131
Tests Failed        : 0
Elapsed Time        : 6.69s
Exit Code           : 0
```

## Verification Commands
- `python3 -m py_compile PhotoGIMP/.config/GIMP/3.0/plug-ins/film-grain/film-grain.py`
- `python3 PhotoGIMP/scripts/verify_config.py`
- `bash PhotoGIMP/install.sh --batch`
- `gimp --no-interface --console-messages --batch-interpreter=python-fu-eval --batch "exec(open('tests/gimp_e2e_suite.py').read())" --quit`
- `python3 tests/run_all_tests.py`

## Expected Checkpoint
- Git commit in PhotoGIMP submodule (`86f1d76`).
- Updated `.ralph/PROGRESS.md`, `.ralph/RUN_STATE.json`, `.ralph/IMPLEMENTATION_PLAN.md`, `.ralph/PHOTOSHOP_FEATURE_MATRIX.md`.
- Git commit in outer repository.
