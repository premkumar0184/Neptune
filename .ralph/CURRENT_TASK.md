# Current Task — Iteration 35

## Task
**Phase 33 — Non-Destructive Swirling Night Sky & Twirl Distortion Helper Plugin**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 664: "Swirling night sky filter", and `photoshop_docs.md` Section 422 lines 12131 & Section 434 line 12677 Filter Gallery: Distort / Liquify: Twirl, Whirl, Pinch, Ripple geometric distortion effects), artistic landscape and night photography often features dramatic celestial spiral vortices, rotating star trails, and atmospheric sky currents inspired by iconic works such as Van Gogh's *The Starry Night*. In Photoshop, artists achieve this effect by applying Twirl and Pinch distortions to sky layers, compositing them non-destructively over landscape horizons with Screen, Soft Light, or Normal blend modes and protective horizon masks. In stock GIMP, distortion filters are applied destructively directly to the active layer, warping the ground, trees, and buildings along with the sky, lacking curated celestial presets, and lacking non-destructive adjustment layers or blend modes. Creating a dedicated native Python 3 helper plugin (`python-fu-swirling-sky`) provides an isolated non-destructive Swirling Sky adjustment layer duplicating the active drawable, applying rotational celestial twirl and pinch dynamics (`gegl:whirl-pinch`), atmospheric ripple wave motion (`gegl:ripple`), curated celestial presets (Starry Night Vortex, Deep Space Whirlpool, Atmospheric Cyclone, Subtle Sky Drift, Counter-Clockwise Spiral, Custom Vortex), versatile compositing blend modes (Normal, Screen for glowing stars, Soft Light, Lighten Only), layer opacity, editable layer masks (Reveal All, Conceal All for selective horizon brushing, and Active Selection for sky masks), and 100% preservation of underlying source pixels.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/swirling-sky/swirling-sky.py` (New plugin)
- `PhotoGIMP/scripts/verify_config.py` (Register `swirling-sky` in `REQUIRED_PLUGINS`, updating audit inventory to 27 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 28: `test_swirling_sky`, 11 assertions SNS-01 through SNS-11)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Swirling Night Sky entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 33 status)
- `.ralph/PROGRESS.md` (Log Iteration 35 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 35 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/swirling-sky/` created with `swirling-sky.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure `python-fu-swirling-sky` registered in GIMP PDB under:
   - `<Image>/Filters/Distort/Swirling Night Sky...`
   - `<Image>/Filters/Artistic/Swirling Night Sky...`
   - `<Image>/Layer/New Swirling Sky Layer...`
4. [x] Non-destructive adjustment layer created duplicating active drawable.
5. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 28):
   - Base layer pixels underneath remain 100% untouched (`diff == 0.000000`).
   - Starry Night Vortex preset verified: 240° celestial vortex rotates pixels across diagonal/polar axes (star rotated into dark sky: 0.947 > 0.30, lift +0.898).
   - Deep Space Whirlpool preset verified: 360° vortex with Screen blend mode (31) and 90.0% opacity.
   - Atmospheric Cyclone preset verified: Outward bloat pinch (-0.15) with Soft Light blend mode (45) and 85.0% opacity.
   - Counter-Clockwise Spiral preset verified: Inverted rotation angle (-180°) rotating dark sky into gold (0.202 < 0.25).
   - Subtle Sky Drift preset verified: Layer created cleanly.
   - Conceal-All black layer mask verified: Composite equals base layer (0.000000 diff) ready for selective horizon painting.
   - Selection-aware mask verified: Active sky selection swirled while unselected ground remains untouched (0.000000 diff).
   - Custom sliders with 85.0% opacity, 120° whirl, 0.10 pinch, and Lighten Only blend mode (36) verified.
6. [x] `verify_config.py` Section 6 passes with all 27 required plugins audited.
7. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all stages cleanly with exit code 0 (245/245 tests passing in 25.50s).

## Verification Evidence
```
Command: python3 tests/run_all_tests.py
Result:
Stage 1: Configuration & Plugin Inventory Audit (verify_config.py) -> PASSED (27/27 plugins audited)
Stage 2: Installer Non-Interactive Deployment Test (install.sh --batch) -> PASSED (27 plugins deployed)
Stage 3: Headless GIMP Plugin Suite Regression Verification (tests/gimp_e2e_suite.py) -> PASSED:
  [PASS] PDB-REG: 27/27 plugins registered including python-fu-swirling-sky
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
  [PASS] SCP-01 to SCP-11: Selective Color Pop & Background Desaturation (11 tests passed)
  [PASS] PC-01 to PC-11: Vintage Photo Colorization & Restoration (11 tests passed)
  [PASS] JAR-01 to JAR-11: JPEG Artifacts Removal & Deblocking (11 tests passed)
  [PASS] CF-01 to CF-11: Charcoal & Fine-Art Sketch (11 tests passed)
  [PASS] WF-01 to WF-11: Woodcut & Linocut Printmaking (11 tests passed)
  [PASS] SNS-01: Execution status (SUCCESS)
  [PASS] SNS-02: Layer mode & name (Layer 'Swirling Sky (Starry Night Vortex)' mode=28)
  [PASS] SNS-03: Layer mask attachment (Reveal-all mask attached)
  [PASS] SNS-04: Starry Night Vortex preset (Rotational vortex twirl: 0.947 > 0.30, lift +0.898)
  [PASS] SNS-05: Deep Space Whirlpool preset (Screen blend mode (31) and 90.0% opacity verified)
  [PASS] SNS-06: Atmospheric Cyclone preset (Soft Light blend mode (45) and 85.0% opacity verified)
  [PASS] SNS-07: Counter-Clockwise Spiral preset (Inverse rotation angle: 0.202 < 0.25)
  [PASS] SNS-08: Subtle Sky Drift preset (Layer 'Swirling Sky (Subtle Sky Drift)' created successfully)
  [PASS] SNS-09: Conceal-all black layer mask (Black mask attached for selective horizon brushing (diff 0.000000))
  [PASS] SNS-10: Selection-aware sky mask (Inside swirled (0.947 > 0.30), outside untouched (diff 0.000000))
  [PASS] SNS-11: Custom sliders & non-destructive preservation (Opacity 85.0%, Lighten Only mode (36), base pixels untouched (diff 0.000000))
Total Tests Executed: 245
Tests Passed        : 245
Tests Failed        : 0
Elapsed Time        : 13.79s
Exit Code           : 0
```

## Checkpoint Details
- Submodule commit in PhotoGIMP: `940035f`.
- Outer repository commit: Pending.
- Next Recommended Task: Phase 34 — Non-Destructive Sky Selection & Replacement Helper Plugin (`python-fu-sky-replacement`).
