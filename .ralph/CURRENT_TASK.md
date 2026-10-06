# Current Task — Iteration 24

## Task
**Phase 22 — Non-Destructive Clarity & Dehaze Helper Plugin**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 104: "Adjust contrast with Clarity and Dehaze", `photoshop_docs.md` Section 108 lines 3260-3277: "Adjust midtone contrast and reduce haze non-destructively using the Clarity and dehaze adjustment layer in professional photoeditor"), Clarity enhances local midtone contrast and adds definition to textures without clipping highlights or shadows, while Dehaze cuts through atmospheric humidity, fog, and distance haze to restore deep contrast and rich color saturation. In stock GIMP, users lack a single non-destructive clarity/dehaze adjustment layer. Creating a dedicated helper plugin provides an isolated adjustment layer, wide-radius local contrast unsharp masking for clarity, contrast and brightness expansion with vibrance restoration for dehaze, authentic presets (Landscape, Mountain Haze, Soft Portrait, Mist/Fog, Architecture), custom sliders, opacity control, an attached reveal-all layer mask, and 100% protection of underlying source pixels.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/clarity-dehaze/clarity-dehaze.py` (New plugin)
- `PhotoGIMP/scripts/verify_config.py` (Register `clarity-dehaze` in `REQUIRED_PLUGINS`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 17: `test_clarity_dehaze`)

## Acceptance Criteria
1. [x] Plugin file exists, has shebang, is executable (`chmod +x`), and passes bytecode compilation.
2. [x] PDB procedure `python-fu-clarity-dehaze` registered in GIMP PDB under `<Image>/Colors`, `<Image>/Filters/Enhance`, and `<Image>/Filters/Retouching`.
3. [x] Dedicated non-destructive Clarity & Dehaze adjustment layer created above active drawable.
4. [x] In headless GIMP tests:
   - Midtone local contrast boost verified (Base contrast 0.202 -> Clarity 0.356, boost x1.76).
   - Atmospheric haze penetration verified (Base dark 0.301 -> Dehazed 0.153, deepened by delta 0.148).
   - Negative clarity softening verified (Boundary softened from 0.202 to 0.106).
   - Custom sliders verified with 85.0% opacity.
   - Reveal-all layer mask attached and editable.
   - Source layer pixels underneath remain 100% untouched (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 16 required plugins verified.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all stages cleanly with exit code 0 (121/121 tests passing).

## Verification Evidence
```
Command: python3 tests/run_all_tests.py
Result:
Stage 1: Configuration & Plugin Inventory Audit (verify_config.py) -> PASSED (16/16 plugins audited)
Stage 2: Installer Non-Interactive Deployment Test (install.sh --batch) -> PASSED (16 plugins deployed)
Stage 3: Headless GIMP Plugin Suite Regression Verification (tests/gimp_e2e_suite.py) -> PASSED:
  [PASS] PDB-REG: 16/16 plugins registered including python-fu-clarity-dehaze
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
  [PASS] CD-01: Execution status (SUCCESS)
  [PASS] CD-02: Layer mode & name (Clarity & Dehaze (Landscape: Crisp Punch & Dehaze) (28))
  [PASS] CD-03: Layer mask attachment (Reveal-all mask attached)
  [PASS] CD-04: Midtone local contrast boost (Base contrast 0.202 -> Clarity 0.356 (boost x1.76))
  [PASS] CD-05: Atmospheric haze penetration (Haze black level deepened: Base 0.301 -> Dehazed 0.153 (delta 0.148))
  [PASS] CD-06: Negative clarity softening (Boundary softened: Base 0.202 -> Softened 0.106)
  [PASS] CD-07: Custom sliders & opacity (Opacity 85.0%, custom Clarity +50.0 / Dehaze -20.0 verified)
  [PASS] CD-08: Non-destructive layer preservation (Base pixels 100% untouched (diff 0.000000))
Total Tests Executed: 121
Tests Passed        : 121
Tests Failed        : 0
Elapsed Time        : 6.19s
Exit Code           : 0
```

## Verification Commands
- `python3 -m py_compile PhotoGIMP/.config/GIMP/3.0/plug-ins/clarity-dehaze/clarity-dehaze.py`
- `python3 PhotoGIMP/scripts/verify_config.py`
- `bash PhotoGIMP/install.sh --batch`
- `gimp --no-interface --console-messages --batch-interpreter=python-fu-eval --batch "exec(open('tests/gimp_e2e_suite.py').read())" --quit`
- `python3 tests/run_all_tests.py`

## Expected Checkpoint
- Git commit in PhotoGIMP submodule (`5e22f15`).
- Updated `.ralph/PROGRESS.md`, `.ralph/RUN_STATE.json`, `.ralph/IMPLEMENTATION_PLAN.md`, `.ralph/PHOTOSHOP_FEATURE_MATRIX.md`.
- Git commit in outer repository.
