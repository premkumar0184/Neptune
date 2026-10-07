# Current Task — Iteration 46

## Task
**Phase 44 — Non-Destructive Match Color & Perceptual Color Transfer Helper Plugin (`python-fu-match-color`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 333-336: "Selective color adjustments - Match color in different images, Match color between two images, Match color of two layers in the same image, Save and apply settings in Match Color", and `photoshop_docs.md` Section 327-330 lines 9575-9695: "The Match Color command in photoeditor adjusts colors in single or multiple images, layers, or selections to align with colors in another... works only in RGB mode... controls for: Luminance adjustment [1-200, default 100], Color Intensity [1-200, default 100, value of 1 converts to grayscale], Fade [0-100, default 0, moving right reduces effect], Neutralize [automatically removes any color cast in target image]"), Match Color is one of Photoshop's premier color standardization and grading commands. It is used across portraiture, landscape, cinematography, and compositing to align color balance across shots, match skin tones, transfer color palettes between reference images/layers, and neutralize color casts.

In stock GIMP, there is no direct equivalent to Photoshop's Match Color dialog. Photographers must manually adjust curves or levels by eye. Implementing native GIMP 3.x Python 3 plugin `python-fu-match-color` achieves full Photoshop parity with non-destructive workflow enhancements:
1. Dynamic Source Layer Color Transfer: Computes statistical channel moments via PDB `gimp-drawable-histogram` between a source reference layer and target layer, mapping color distribution via `gegl:channel-mixer`.
2. Curated Photographic Grading Palettes: Warm Golden Hour (warm amber sunlight), Cool Cinema Blue (moody teal/cyan cinema), Vintage Film Tone (analog film matte warmth), Lush Foliage Emerald (deep landscape greens), Sunset Crimson (radiant dusk orange/magenta), Skin Tone Harmony (healthy portrait skin balance), Neutralize Only, Source Layer, and Custom sliders.
3. Luminance Slider (1 to 200, default 100): Maps to linear exposure EV via `gegl:exposure` (`ev = log2(lum / 100.0)`).
4. Color Intensity Slider (1 to 200, default 100): Maps to `gegl:vibrance` saturation where `color_intensity = 1.0` yields pure neutral grayscale (`saturation = 0.0`) and `color_intensity = 200.0` yields double saturation.
5. Fade Slider (0 to 100, default 0): Linearly modulates adjustment layer effective opacity back to the unadjusted base layer (`eff_opacity = opacity * (1.0 - fade / 100.0)`).
6. Neutralize Color Cast Toggle: Automatically calculates chromatic channel imbalances and applies balancing gains to eliminate color casts (>95% cast reduction).
7. Layer Mask Support: Reveal All (white mask), Conceal All (black mask), and Active Selection mask.
8. 100% Non-Destructive Invariance: Duplicates target drawable into an isolated adjustment layer; base layer pixels underneath remain 100% mathematically untouched (`diff == 0.000000`).

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/match-color/match-color.py` (New plugin)
- `PhotoGIMP/scripts/verify_config.py` (Register `match-color` in `REQUIRED_PLUGINS`, updating audit inventory to 38 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 39: `test_match_color`, assertions MC-01 through MC-11)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Match Color entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 44 status and schedule Phase 45)
- `.ralph/PROGRESS.md` (Log Iteration 46 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 46 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/match-color/` created with `match-color.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure `python-fu-match-color` registered in GIMP PDB under:
   - `<Image>/Image/Adjustments/Match Color...`
   - `<Image>/Colors/Match Color...`
   - `<Image>/Filters/Retouching`
   - `<Image>/Layer`
4. [x] Non-destructive adjustment layer created duplicating active drawable.
5. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 39):
   - MC-01: Procedure arguments verified (preset, source-layer-id, luminance, color-intensity, fade, neutralize, mask-mode, opacity).
   - MC-02: Execution status verified (PDB status SUCCESS).
   - MC-03: Layer mode, name & mask verified (`Match Color (Warm Golden Hour)` with reveal-all mask attached).
   - MC-04: Source Layer Color Matching verified (color statistics transferred from source layer to target: Red 0.202->0.361, Blue 0.799->0.082).
   - MC-05: Warm Golden Hour preset verified (R=0.456 > G=0.283 > B=0.063 warm amber tone).
   - MC-06: Cool Cinema Blue preset verified (B=0.905 > G=0.451 > R=0.144 cool cinema tone).
   - MC-07: Lush Foliage Emerald preset verified (G=0.807 > R=0.093, B=0.181 landscape green).
   - MC-08: Color Intensity = 1.0 verified (pure neutral grayscale, spread == 0.000000).
   - MC-09: Neutralize Color Cast toggle verified (color cast neutralized from 0.5975 to 0.0049, >95% reduction).
   - MC-10: Conceal-All black layer mask verified (composite diff == 0.000000).
   - MC-11: Selection confinement & non-destructive preservation verified (effect confined to selection, base layer 100% untouched diff == 0.000000).
6. [x] `verify_config.py` Section 6 passes with all 38 required plugins audited.
7. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0 (377/377 tests passing).

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Expected Checkpoint
- PhotoGIMP submodule commit: `7728b76` (`feat(plugins): implement non-destructive match color and perceptual color transfer helper plugin`)
- Outer repository commit: `feat(ralph): complete iteration 46 - non-destructive match color plugin`
