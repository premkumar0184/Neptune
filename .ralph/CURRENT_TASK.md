# Current Task — Iteration 30

## Task
**Phase 28 — Non-Destructive Selective Color & Background Desaturation Helper Plugin**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 667: "Desaturate image backgrounds to black and white", line 333: "Selective color adjustments", line 339: "Make selective color adjustments", and `photoshop_docs.md` Section 331 lines 9698-9712 and Section 107 lines 3233-3240), isolating a focal subject in vibrant full color while desaturating or converting surrounding background elements into classic monochrome or stylized toning is a standard high-end photographic workflow. Photoshop provides Quick Actions ("Desaturate image backgrounds to black and white") and Hue/Saturation adjustment layers with selection masks to achieve this non-destructively. In stock GIMP, achieving this effect requires laborious manual steps: duplicating the layer, running destructive desaturation, adding a layer mask, inverting selections, manually painting gradients, or risking harsh edge clipping. Creating a dedicated native Python 3 helper plugin (`python-fu-selective-color-pop`) provides an isolated adjustment layer duplicating the active drawable, applying high-performance GEGL monochrome mixing (`gegl:mono-mixer`), saturation scaling (`gegl:saturation`), or photographic sepia toning (`gegl:sepia`), intelligent focal depth masking (radial gradient falloff with configurable radius and edge softness, active selection subject masking, or manual brush masking), creative inverted mask option (monochrome subject on colored background), curated presets (Classic B&W Background, Dramatic High-Contrast B&W, Muted Pastel Desaturated, Vintage Sepia Toned, Cool Monochrome Noir, Custom Sliders), layer opacity control, and 100% protection of underlying source pixels.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/selective-color-pop/selective-color-pop.py` (New plugin)
- `PhotoGIMP/scripts/verify_config.py` (Register `selective-color-pop` in `REQUIRED_PLUGINS`, updating count to 22)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 23: `test_selective_color_pop`)

## Acceptance Criteria
1. [x] Plugin file exists, has shebang, is executable (`chmod +x`), and passes bytecode compilation.
2. [x] PDB procedure `python-fu-selective-color-pop` registered in GIMP PDB under `<Image>/Colors/Selective Color Pop...`, `<Image>/Filters/Retouching/Selective Color Pop...`, and `<Image>/Layer`.
3. [x] Dedicated non-destructive Selective Color adjustment layer created duplicating active drawable.
4. [x] In headless GIMP tests:
   - Base layer pixels underneath remain 100% untouched (`diff == 0.000000`).
   - Radial focal mask verified: Center subject remains 100% in original color (`diff == 0.000000`), while peripheral background is converted to pure monochrome (R=G=B, difference == 0.000000).
   - Selection-aware mask verified: Active subject selection protects subject color and desaturates background.
   - Invert mask option verified: Subject converted to monochrome while background remains in full color.
   - Muted pastel preset verified: Background saturation is reduced (chroma reduced by 75.4%) while subject color is preserved.
   - Vintage sepia preset verified: Background is sepia-toned (R > G > B) while subject remains in full color.
   - Custom sliders with custom channel weighting and layer opacity (80.0%) verified.
5. [x] `verify_config.py` Section 6 passes with all 22 required plugins verified.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all stages cleanly with exit code 0 (185/185 tests passing).

## Verification Evidence
```
Command: python3 tests/run_all_tests.py
Result:
Stage 1: Configuration & Plugin Inventory Audit (verify_config.py) -> PASSED (22/22 plugins audited)
Stage 2: Installer Non-Interactive Deployment Test (install.sh --batch) -> PASSED (22 plugins deployed)
Stage 3: Headless GIMP Plugin Suite Regression Verification (tests/gimp_e2e_suite.py) -> PASSED:
  [PASS] PDB-REG: 22/22 plugins registered including python-fu-selective-color-pop
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
  [PASS] FG-01 to FG-09: Film Grain & Analog Texture (9 tests passed)
  [PASS] LT-01 to LT-09: Light & Tonal Range (9 tests passed)
  [PASS] DT-01 to DT-09: Duotone & Tritone Print Effect (9 tests passed)
  [PASS] DG-01 to DG-10: Diffuse Glow & Glamour Filter (10 tests passed)
  [PASS] SS-01 to SS-10: Skin Smoothing & Portrait Retouching (10 tests passed)
  [PASS] SCP-01: Execution status (SUCCESS)
  [PASS] SCP-02: Layer mode & name (Selective Color Pop (Classic B&W Background) (28))
  [PASS] SCP-03: Layer mask attachment (Attached radial focal mask)
  [PASS] SCP-04: Subject full color preservation (Center subject 100% full color (diff 0.000000))
  [PASS] SCP-05: Peripheral background monochrome conversion (Edge exact monochrome: R=G=B=0.3968 (spread 0.000000))
  [PASS] SCP-06: Selection-aware subject mask (Inside full color (diff 0.000000), Outside pure monochrome (spread 0.000000))
  [PASS] SCP-07: Invert effect option (Center monochrome (spread 0.000000), Edge full color (diff 0.000000))
  [PASS] SCP-08: Muted pastel preset (Center full color, Background chroma muted 0.695 -> 0.171 (-75.4%))
  [PASS] SCP-09: Vintage sepia toning preset (Background warm archival sepia (R=0.665 > G=0.546 > B=0.356))
  [PASS] SCP-10: Custom sliders & opacity (Opacity 80.0%, Normal blend mode (28) verified)
  [PASS] SCP-11: Non-destructive layer preservation (Base pixels 100% untouched across all tonal zones (diff 0.000000))
Total Tests Executed: 185
Tests Passed        : 185
Tests Failed        : 0
Elapsed Time        : 9.47s
Exit Code           : 0
```

## Verification Commands
- `python3 -m py_compile PhotoGIMP/.config/GIMP/3.0/plug-ins/selective-color-pop/selective-color-pop.py`
- `python3 PhotoGIMP/scripts/verify_config.py`
- `bash PhotoGIMP/install.sh --batch`
- `gimp --no-interface --console-messages --batch-interpreter=python-fu-eval --batch "exec(open('tests/gimp_e2e_suite.py').read())" --quit`
- `python3 tests/run_all_tests.py`

## Expected Checkpoint
- Git commit in PhotoGIMP submodule.
- Updated `.ralph/PROGRESS.md`, `.ralph/RUN_STATE.json`, `.ralph/IMPLEMENTATION_PLAN.md`, `.ralph/PHOTOSHOP_FEATURE_MATRIX.md`.
- Git commit in outer repository.
