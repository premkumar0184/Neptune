# Current Task — Iteration 28

## Task
**Phase 26 — Non-Destructive Diffuse Glow & Dreamy Glamour Filter Helper Plugin**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 663: "Apply diffuse glow to images", and `photoshop_docs.md` Section 417 line 12131: "Distort: Diffuse Glow... renders an image as though it were viewed through a soft diffusion filter. The filter adds translucent white noise, with the glow fading from the center of a selection"), Diffuse Glow and Glamour Soft Focus are quintessential creative filters and portrait retouching techniques. Diffuse Glow softens skin imperfections, blooms specular highlights into radiant halos, and introduces delicate optical grain texture simulating classic camera diffusion glass filters (such as Pro-Mist, Fog, and Soft-FX filters). In stock GIMP, achieving this effect is purely destructive or requires tedious multi-step layer duplication, luminance threshold extraction, Gaussian blur, noise generation, and manual layer blending. Creating a dedicated non-destructive helper plugin provides an isolated adjustment layer duplicating the active drawable, offering authentic Photoshop controls (Glow Amount, Clear Amount threshold, Diffusion Radius, Graininess, Warmth tint), curated photographic presets (Dreamy Glamour Portrait, Ethereal Sunlight Bloom, Vintage Diffusion Glass, Golden Hour Warm Glow, Night Neon Radiance, Subtle Soft Focus, Custom Sliders), compositing blend mode options (Screen, Soft Light, Addition, Normal), layer opacity, an attached reveal-all layer mask, and 100% protection of underlying source pixels.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/diffuse-glow/diffuse-glow.py` (New plugin)
- `PhotoGIMP/scripts/verify_config.py` (Register `diffuse-glow` in `REQUIRED_PLUGINS`, updating count to 20)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 21: `test_diffuse_glow`)

## Acceptance Criteria
1. [x] Plugin file exists, has shebang, is executable (`chmod +x`), and passes bytecode compilation.
2. [x] PDB procedure `python-fu-diffuse-glow` registered in GIMP PDB under `<Image>/Filters/Light and Shadow/Diffuse Glow...`, `<Image>/Filters/Retouching/Diffuse Glow...`, `<Image>/Colors/Diffuse Glow...`, and `<Image>/Layer`.
3. [x] Dedicated non-destructive Diffuse Glow adjustment layer created duplicating active drawable.
4. [x] In headless GIMP tests:
   - Base layer pixels underneath remain 100% untouched (`diff == 0.000000`).
   - Highlight bloom diffusion verified: Bright highlight area triggers radiant bloom into surrounding dark areas (bloom spill delta +0.1741 > 0.08).
   - Clear Amount threshold verified: High clear threshold (80.0) leaves dark shadow tones protected (shadow 0.1590 vs base 0.1500, delta 0.0090 <= 0.03).
   - Graininess verified: Translucent organic noise texture added to glow layer (variance 0.000118 > 0.00005).
   - Golden Hour warm glow verified: Golden warmth shift (R=1.0000 > B=0.7991, warmth delta +0.2009) applied to the bloom layer.
   - Blend mode verified: Screen (mode 31), Soft Light (mode 45), Addition (mode 33), and Normal (mode 28) modes correctly applied.
   - Custom sliders and opacity verified (Opacity 85.0%, custom threshold/radius/strength).
   - Reveal-all layer mask attached and editable.
5. [x] `verify_config.py` Section 6 passes with all 20 required plugins verified.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all stages cleanly with exit code 0 (162/162 tests passing).

## Verification Evidence
```
Command: python3 tests/run_all_tests.py
Result:
Stage 1: Configuration & Plugin Inventory Audit (verify_config.py) -> PASSED (20/20 plugins audited)
Stage 2: Installer Non-Interactive Deployment Test (install.sh --batch) -> PASSED (20 plugins deployed)
Stage 3: Headless GIMP Plugin Suite Regression Verification (tests/gimp_e2e_suite.py) -> PASSED:
  [PASS] PDB-REG: 20/20 plugins registered including python-fu-diffuse-glow
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
  [PASS] DG-01: Execution status (SUCCESS)
  [PASS] DG-02: Layer mode & name (Diffuse Glow (Dreamy Glamour Portrait) (45))
  [PASS] DG-03: Layer mask attachment (Reveal-all mask attached)
  [PASS] DG-04: Highlight bloom diffusion (Screen mode (31) and radiant bloom spill (spill=0.4125 > interior=0.2384, delta +0.1741) verified)
  [PASS] DG-05: Clear amount threshold (High clear threshold (80.0%) protects shadow tones (shadow 0.1590 vs base 0.1500, delta 0.0090 <= 0.03) verified)
  [PASS] DG-06: Translucent diffusion graininess (Optical diffusion grain texture verified (variance 0.000118 > 0.00005))
  [PASS] DG-07: Golden hour warmth shift (Golden highlight bloom verified (R=1.0000 > B=0.7991, warmth delta +0.2009))
  [PASS] DG-08: Night neon radiance mode (Addition blend mode (33) and 90.0% opacity verified)
  [PASS] DG-09: Custom sliders & opacity (Opacity 85.0%, Normal blend mode (28) verified)
  [PASS] DG-10: Non-destructive layer preservation (Base pixels 100% untouched across all tonal zones (diff 0.000000))
Total Tests Executed: 162
Tests Passed        : 162
Tests Failed        : 0
Elapsed Time        : 8.45s
Exit Code           : 0
```

## Verification Commands
- `python3 -m py_compile PhotoGIMP/.config/GIMP/3.0/plug-ins/diffuse-glow/diffuse-glow.py`
- `python3 PhotoGIMP/scripts/verify_config.py`
- `bash PhotoGIMP/install.sh --batch`
- `gimp --no-interface --console-messages --batch-interpreter=python-fu-eval --batch "exec(open('tests/gimp_e2e_suite.py').read())" --quit`
- `python3 tests/run_all_tests.py`

## Expected Checkpoint
- Git commit in PhotoGIMP submodule (`b45b0c5`).
- Updated `.ralph/PROGRESS.md`, `.ralph/RUN_STATE.json`, `.ralph/IMPLEMENTATION_PLAN.md`, `.ralph/PHOTOSHOP_FEATURE_MATRIX.md`.
- Git commit in outer repository.
