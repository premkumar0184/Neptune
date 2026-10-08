# Current Task — Iteration 59

## Task
**Phase 57 — Channel Calculations & Two-Source Blending Helper Plugin (`python-fu-calculations`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 350: "Blend channels with Apply Image and Calculations", and `photoshop_docs.md` Section 340 lines 10050-10100: "Apply Image works with single and composite channels, while Calculations operates exclusively on single channels... choose first source image, layer, and channel... Invert... choose second source image, layer, and channel... Invert... blending mode... Opacity... Mask... For Result, specify whether to create a new document, add a new channel, or select the active image"), Calculations is one of Photoshop's most revered precision tools for digital artists, retouchers, and print professionals.

Stock GIMP provides individual channel menus and channel operations, but:
1. Lacks a unified two-source channel calculation dialog simulating Photoshop `Image > Calculations...`.
2. Lacks arbitrary single-channel selection from two independent sources (Red, Green, Blue, Alpha, Gray/Luminance).
3. Lacks independent Invert checkboxes for Source 1 and Source 2.
4. Lacks Photoshop's 11 core channel blending modes (Multiply, Screen, Overlay, Soft Light, Hard Light, Normal, Darken, Lighten, Difference, Subtract, Add) with Scale (1.0 to 2.0) and Offset (-255 to +255) calibration.
5. Lacks opacity modulation and optional mask channel integration.
6. Lacks Photoshop's 4 versatile destination outputs:
   - `New Channel`: saves the calculation result directly as a named alpha channel in the image channels list (essential for channel masking, hair extraction, and luminance selections).
   - `Selection`: loads the calculation result directly into the active marching-ants selection on the current canvas.
   - `New Layer`: inserts a grayscale / blended layer into the current layer stack.
   - `New Document`: generates a brand new document from the calculated channel.
7. Lacks curated presets for high-end masking and separation (Sky Matte Extract, Hair Silhouette, Contrast Luminance, Shadow Separation, Highlight Separation, Frequency Subtract, Frequency Add, Custom Math).

Implementing native GIMP 3.x Python 3 plugin `calculations` closes this gap with complete Photoshop parity:
1. `python-fu-calculations`:
   - Dual-Source Architecture:
     - `source1-layer-id`: Source 1 layer ID (0 for active layer).
     - `source1-channel`: Single channel choice (`gray`, `red`, `green`, `blue`, `alpha`).
     - `source1-invert`: Boolean invert for Source 1.
     - `source2-layer-id`: Source 2 layer ID (0 for active layer).
     - `source2-channel`: Single channel choice (`gray`, `red`, `green`, `blue`, `alpha`).
     - `source2-invert`: Boolean invert for Source 2.
   - Blending Mathematics:
     - `blend-mode`: Choice (`multiply`, `screen`, `overlay`, `soft-light`, `hard-light`, `normal`, `darken`, `lighten`, `difference`, `subtract`, `add`).
     - `opacity`: Blend strength (0.0% to 100.0%, default 100.0%).
     - `scale`: Factor for Add/Subtract modes (1.0 to 2.0, default 1.0).
     - `offset`: Value offset for Add/Subtract modes (-255.0 to 255.0, default 0.0).
   - Mask Options:
     - `mask-enabled`: Boolean toggle.
     - `mask-channel`: Mask channel choice (`gray`, `red`, `green`, `blue`, `alpha`).
     - `mask-invert`: Boolean invert for mask.
   - Destination Options:
     - `result-destination`: Choice (`new-channel`, `selection`, `new-layer`, `new-document`).
     - `channel-name`: Custom name for output channel/layer (default "Calculations").
   - Curated Presets:
     - `sky-matte-extract`: Red & Blue Inverted in Multiply (classic sky/cloud separation).
     - `hair-silhouette`: Green & Blue Inverted in Screen (fine edge/hair isolation).
     - `contrast-luminance`: Red & Green in Soft Light (dramatic skin/landscape contrast).
     - `shadow-separation`: Red Inverted & Blue Inverted in Multiply (deep shadow detail isolation).
     - `highlight-separation`: Red & Blue in Screen (specular highlight isolation).
     - `frequency-subtract`: Source 1 Gray & Source 2 Gray in Subtract (Scale 2.0, Offset 128.0).
     - `frequency-add`: Source 1 Gray & Source 2 Gray Inverted in Add (Scale 2.0, Offset 0.0).
     - `custom`: Full manual control.
   - Non-Destructive Operation:
     - Outputting to Channel, Selection, Layer, or Document leaves source pixels 100% untouched (`diff == 0.000000`).
   - Single-Step Undo Protection:
     - Encapsulated within `image.undo_group_start()` and `image.undo_group_end()`.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/calculations/calculations.py` (New plugin implementing `python-fu-calculations`)
- `PhotoGIMP/scripts/verify_config.py` (Register `calculations` in `REQUIRED_PLUGINS`, updating audit inventory to 51 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 52: `test_calculations`, assertions CALC-01 through CALC-16)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Calculations entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 57 status)
- `.ralph/PROGRESS.md` (Log Iteration 59 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 59 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/calculations/` created with `calculations.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure registered in GIMP PDB:
   - `python-fu-calculations` under `<Image>/Image/Calculations...`, `<Image>/Select/Calculations...`, `<Image>/Filters/Retouching`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 52):
   - CALC-01: Procedure lookup and argument signatures verified across all properties.
   - CALC-02: Execution status verified (PDB status SUCCESS).
   - CALC-03: Multiply blend mode math verified ($S_1 \cdot S_2$).
   - CALC-04: Screen blend mode math verified ($1 - (1 - S_1)(1 - S_2)$).
   - CALC-05: Difference blend mode math verified ($|S_1 - S_2|$).
   - CALC-06: Subtract blend mode math with Scale & Offset verified ($((S_1 - S_2) / \text{scale}) + (\text{offset} / 255)$).
   - CALC-07: Add blend mode math with Scale & Offset verified ($((S_1 + S_2) / \text{scale}) + (\text{offset} / 255)$).
   - CALC-08: Source 1 & Source 2 Invert toggles verified.
   - CALC-09: Single channel extraction verified (Red, Green, Blue, Alpha, Gray/Luminance).
   - CALC-10: Curated presets verified (sky-matte-extract, hair-silhouette, contrast-luminance, shadow-separation, frequency-subtract).
   - CALC-11: New Channel destination verified (channel added to image channels with correct pixel values).
   - CALC-12: Selection destination verified (active selection created matching calculation math).
   - CALC-13: New Layer destination verified (layer created in image stack matching calculation math).
   - CALC-14: New Document destination verified (new image created with correct dimensions and pixels).
   - CALC-15: Mask channel modulation verified.
   - CALC-16: Original image layers and base pixels 100% preserved (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 51 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement channel calculations and two-source blending helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 59 - channel calculations helper plugin`
