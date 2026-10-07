# Current Task — Iteration 47

## Task
**Phase 45 — Non-Destructive Apply Image & Channel Math Helper Plugin (`python-fu-apply-image`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 350: "HDR and channel manipulation - Blend channels with Apply Image and Calculations", and `photoshop_docs.md` Section 340 lines 10050-10100: "Image > Apply Image and Image > Calculations: Blend channels with Apply Image and Calculations... choose source image, layer, and channel... blending modes [Multiply, Screen, Overlay, Soft Light, Add, Subtract...], Invert checkbox, Opacity slider, Scale, Offset, and Mask options"), Apply Image and Calculations are the foundation of high-end commercial retouching, digital darkroom composite math, and channel-based adjustments.

Retouchers and digital artists rely heavily on Apply Image for:
1. Frequency Separation:
   - 8-bit Frequency Separation texture extraction (Subtract blend mode, Scale 2, Offset 128).
   - 16-bit Frequency Separation texture extraction (Add blend mode, Invert True, Scale 2, Offset 0).
2. Channel Luminosity & Contrast Blending:
   - Blending the Green channel onto the composite using Soft Light for flattering skin contrast and tone without color casts.
   - Blending the Red channel onto the composite using Multiply for dramatic fine-art black & white landscape contrast.
3. Channel Matte & Alpha Extraction:
   - Blending high-contrast inverted channels using Screen or Overlay for hair and edge masking.
4. Channel Math & Calculations:
   - Combining any source channel (RGB, Red, Green, Blue, Alpha, Luminance) with full blending modes, opacity, scale, and offset.

Stock GIMP provides no built-in `Apply Image` or `Calculations` dialog, forcing users to manually duplicate channels, paste floats, adjust curves, and flatten. Implementing native GIMP 3.x Python 3 plugin `python-fu-apply-image` bridges this major professional gap with non-destructive layering:
- Source channel extraction (Composite RGB, Red, Green, Blue, Alpha, Luminance via `gegl:mono-mixer`).
- Channel inversion support (`gegl:invert-linear`).
- Precise scale & offset calibration via `gimp-drawable-levels`.
- 12 Photoshop-standard blend modes (Normal, Multiply, Screen, Overlay, Soft Light, Hard Light, Add, Subtract, Difference, Darken, Lighten, Linear Light).
- Curated retouching presets (8-bit Frequency Separation, 16-bit Frequency Separation, Green Channel Contrast, Red Channel Multiply, Blue Matte Extract, Luminosity Blend, Custom).
- Layer mask options (Reveal All, Conceal All, Active Selection).
- 100% Non-destructive invariance: Base layer pixels underneath remain 100% mathematically untouched (`diff == 0.000000`).

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/apply-image/apply-image.py` (New plugin)
- `PhotoGIMP/scripts/verify_config.py` (Register `apply-image` in `REQUIRED_PLUGINS`, updating audit inventory to 39 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 40: `test_apply_image`, assertions AI-01 through AI-11)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Apply Image entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 45 status and schedule Phase 46)
- `.ralph/PROGRESS.md` (Log Iteration 47 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 47 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/apply-image/` created with `apply-image.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure `python-fu-apply-image` registered in GIMP PDB under:
   - `<Image>/Image/Apply Image...`
   - `<Image>/Image/Calculations...`
   - `<Image>/Filters/Retouching`
   - `<Image>/Layer`
4. [x] Non-destructive adjustment layer created duplicating active drawable or source channel.
5. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 40):
   - AI-01: Procedure arguments verified (preset, source-layer-id, source-channel, invert, blend-mode, opacity, scale, offset, mask-mode).
   - AI-02: Execution status verified (PDB status SUCCESS).
   - AI-03: Layer mode, name & mask verified (`Apply Image (Frequency Separation (8-bit))` with `SUBTRACT` mode and reveal-all mask attached).
   - AI-04: Frequency Separation 8-bit preset verified (Subtract, Scale 2, Offset 128 neutral gray baseline #808080).
   - AI-05: Green Channel Contrast preset verified (Green channel isolated and blended via Soft Light).
   - AI-06: Red Channel Multiply preset verified (Red channel isolated and blended via Multiply).
   - AI-07: Invert flag verified (Source channel accurately inverted before blending).
   - AI-08: Blend modes verified (Screen, Overlay, Add, Difference, Linear Light).
   - AI-09: Scale and Offset calibration verified via levels math (Scale 4.0 & Offset 64.0 verified).
   - AI-10: Conceal-All black layer mask verified (composite diff == 0.000000).
   - AI-11: Selection confinement & non-destructive preservation verified (effect confined to selection, base layer 100% untouched diff == 0.000000).
6. [x] `verify_config.py` Section 6 passes with all 39 required plugins audited.
7. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0 (389/389 tests passing).

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `79a97b5` (`feat(plugins): implement non-destructive apply image and channel math helper plugin`)
- Outer repository commit: `feat(ralph): complete iteration 47 - non-destructive apply image plugin`
