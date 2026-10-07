# Current Task — Iteration 48

## Task
**Phase 46 — Non-Destructive Replace Color & Targeted Object Recoloring Helper Plugin (`python-fu-replace-color`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 337: "Replace Object Colors by Applying a Hue or Saturation Adjustment", line 339: "Make selective color adjustments", and `photoshop_docs.md` Section 331 lines 9698-9714: "Replace Object Colors by Applying a Hue or Saturation Adjustment: Learn more about replacing the color of selected objects in professional photoeditor using Hue/Saturation adjustment layers for flexible, non-destructive editing... move the Hue and Saturation sliders to replace the object's color... If original color tints the new one, select Colorize... set adjustment layer to Hue blending mode... Paint on mask with black or white to refine affected area"), replacing colors of specific objects (such as garments, automotive paints, packaging, flowers, eyes, and interior decor) is one of the most frequent professional editing operations.

Photoshop's classic `Image > Adjustments > Replace Color...` allows retouchers to:
1. Sample a target object color (or pick standard hue ranges: Reds, Yellows, Greens, Cyans, Blues, Magentas).
2. Adjust Fuzziness (tolerance threshold controlling mask softness and gradient falloff around the target color).
3. Transform the replacement: Hue (-180° to +180°), Saturation (-100 to +100), and Lightness (-100 to +100), with an optional Colorize toggle.
4. Output to a non-destructive adjustment layer with a fuzziness-weighted layer mask so users can paint in or out any areas.

Stock GIMP provides no built-in `Replace Color` adjustment dialog. Users are forced to manually invoke `Select by Color`, feather the selection, create a layer mask, duplicate the layer, run Colorize/Hue-Chroma, and adjust blend modes. Implementing native GIMP 3.x Python 3 plugin `python-fu-replace-color` brings this complete workflow into a single non-destructive helper:
- Target color sampling (RGB) or standard presets (Reds, Yellows, Greens, Cyans, Blues, Magentas, Custom).
- Perceptual Fuzziness mask calculation: Euclidean color distance in RGB/HSV space with smooth Hermite/cosine falloff generating a feathered alpha mask.
- Non-destructive adjustment layer duplicating the target drawable and applying native PDB `gimp-drawable-hue-saturation` for hue shift, saturation, and lightness adjustments.
- Dedicated Colorize mode using native PDB `gimp-drawable-colorize-hsl` for tinting low-saturation or neutral elements.
- Layer blend modes (Color via `HSL_COLOR`, Hue via `HSV_HUE`, Normal, Soft Light) and opacity.
- Layer mask options (Fuzziness Mask, Conceal All, Reveal All, Selection).
- 100% Non-destructive invariance: Base layer pixels underneath remain 100% mathematically untouched (`diff == 0.000000`).

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/replace-color/replace-color.py` (New plugin)
- `PhotoGIMP/scripts/verify_config.py` (Register `replace-color` in `REQUIRED_PLUGINS`, updating audit inventory to 40 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 41: `test_replace_color`, assertions RC-01 through RC-11)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Replace Color entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 46 status and schedule Phase 47)
- `.ralph/PROGRESS.md` (Log Iteration 48 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 48 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/replace-color/` created with `replace-color.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure `python-fu-replace-color` registered in GIMP PDB under:
   - `<Image>/Image/Adjustments/Replace Color...`
   - `<Image>/Colors/Replace Color...`
   - `<Image>/Filters/Retouching`
   - `<Image>/Layer`
4. [x] Non-destructive adjustment layer created duplicating active drawable with targeted color replaced.
5. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 41):
   - RC-01: Procedure arguments verified (target-preset, sample-r, sample-g, sample-b, fuzziness, hue-shift, saturation-shift, lightness-shift, colorize, blend-mode, mask-mode, opacity).
   - RC-02: Execution status verified (PDB status SUCCESS).
   - RC-03: Layer mode, name & mask verified (`Replace Color (Reds)` with HSL_COLOR mode and mask attached).
   - RC-04: Target Color Hue Shift verified (Red shifted by +120° to Green: R=0.000, G=1.000, B=0.000).
   - RC-05: Fuzziness Mask falloff verified (Mask isolates targeted reds [mask=1.00] and excludes distant blues [mask=0.00]).
   - RC-06: Colorize mode verified (Neutral gray uniformly tinted to green hue: G=0.947 > R=0.056, B=0.056).
   - RC-07: Saturation shift verified (Saturation -100 desaturated red target to neutral monochrome, spread 0.000000).
   - RC-08: Lightness shift verified (Lightness +50 lifted luminance: G=0.216, B=0.216 > 0.0).
   - RC-09: Blend modes verified (Color, Hue, Normal, Soft Light validated).
   - RC-10: Conceal-All black layer mask verified (Effect 100% concealed by black mask, composite diff == 0.000000).
   - RC-11: Selection confinement & non-destructive preservation verified (Mask [in=1.00, out=0.00], base layer 100% untouched diff == 0.000000).
6. [x] `verify_config.py` Section 6 passes with all 40 required plugins audited.
7. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0 (401/401 tests passing).

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `ea002c5` (`feat(plugins): implement non-destructive replace color and object recoloring helper plugin`)
- Outer repository commit: `feat(ralph): complete iteration 48 - non-destructive replace color plugin`
