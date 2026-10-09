# Current Task — Iteration 64

## Task
**Phase 62 — Non-Destructive Color Overlay Layer Style Helper Plugin (`python-fu-color-overlay`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 107-118, 432: "Apply layer effects - Add layer styles", "Work with preset styles", "Layer style effects and options overview", and `photoshop_docs.md` Section 113-115 lines 3433-3500: "View and edit layer effects and styles using the Layer Style dialog in professional photoeditor... Color Overlay: Blend Mode, Color, Opacity"), Color Overlay represents one of the most fundamental layer styles, enabling non-destructive tinting, solid color fills, brand color application, and monochrome grading directly over layer content.

Stock GIMP provides bucket fill and flat color layers, but lacks a dedicated non-destructive Color Overlay layer style dialog, lacks automatic silhouette boundary alpha clipping to target layers ($A_{\text{overlay}}(x, y) = A_{\text{target}}(x, y)$), lacks Photoshop's standard blend modes (Normal, Multiply, Screen, Overlay, Soft Light, Color / HSL Color, Darken, Lighten), lacks curated color presets, and lacks dedicated overlay layer placement immediately above the target layer leaving underlying artwork 100% untouched (`diff == 0.000000`).

Implementing native GIMP 3.x Python 3 plugin `color-overlay` closes this gap with complete Photoshop parity:
1. `python-fu-color-overlay`:
   - Color & Presets:
     - `preset`: Choice (`default-red`, `warm-amber`, `cool-cyan`, `emerald-green`, `royal-purple`, `pure-white`, `deep-black`, `monochrome-tint`, `custom`).
     - `color-r`, `color-g`, `color-b`: Solid Color RGB (default red `[1.0, 0.0, 0.0]`).
   - Blending & Opacity:
     - `blend-mode`: Choice (`normal`, `multiply`, `screen`, `overlay`, `soft-light`, `color`, `darken`, `lighten`).
     - `opacity`: Percentage slider (0.0% to 100.0%, default 100.0%).
   - Layer Masking:
     - `mask-type`: Choice (`auto`, `none`, `reveal-all`, `conceal-all`, `selection`).
   - Non-Destructive Operation:
     - Dedicated overlay layer inserted directly above the target layer in stack.
     - Pixels strictly clipped to the target layer's silhouette (outside alpha strictly `0.000`, anti-aliased edge alphas matching target layer exactly).
     - Target layer artwork and underlying canvas 100% untouched (`diff == 0.000000`).
     - Single-step `Ctrl+Z` undo protection.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/color-overlay/color-overlay.py` (New plugin implementing `python-fu-color-overlay`)
- `PhotoGIMP/scripts/verify_config.py` (Register `color-overlay` in `REQUIRED_PLUGINS`, updating audit inventory to 56 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 57: `test_color_overlay`, assertions CO-01 through CO-15)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Color Overlay Layer Style entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 62 status)
- `.ralph/PROGRESS.md` (Log Iteration 64 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 64 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/color-overlay/` created with `color-overlay.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure registered in GIMP PDB:
   - `python-fu-color-overlay` under `<Image>/Layer/Layer Style/Color Overlay...`, `<Image>/Filters/Light and Shadow/Color Overlay (Layer Style)...`, and `<Image>/Filters/Retouching`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 57):
   - CO-01: Procedure lookup and argument signatures verified across all properties.
   - CO-02: Execution status verified (PDB status SUCCESS).
   - CO-03: Solid red color fidelity verified (interior pixels have exact target RGB `[1.0, 0.0, 0.0]`).
   - CO-04: Strict boundary silhouette clipping (pixels outside target layer silhouette are strictly alpha 0.000).
   - CO-05: Semi-transparent edge alpha preservation (feathered edge alpha matches target layer alpha).
   - CO-06: Custom RGB color swatch fidelity (e.g. emerald green `[0.0, 0.75, 0.35]`).
   - CO-07: Curated presets verified (`default-red`, `warm-amber`, `cool-cyan`, `emerald-green`, `royal-purple`, `pure-white`, `deep-black`, `monochrome-tint`).
   - CO-08: Layer stack placement verified (overlay layer inserted immediately above parent layer in stack).
   - CO-09: Blend modes validation (Normal, Multiply, Screen, Overlay, Soft Light, Color / HSL Color, Darken, Lighten).
   - CO-10: Opacity scaling validation (e.g. 50% opacity sets layer opacity to 50.0).
   - CO-11: Conceal-All black layer mask attachment verified.
   - CO-12: Reveal-All white layer mask attachment verified.
   - CO-13: Active selection to layer mask conversion verified.
   - CO-14: Auto layer mask attachment behavior verified (attaches selection mask when active and none when empty).
   - CO-15: Target and base layer artwork 100% untouched across all operations (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 56 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement non-destructive color overlay layer style helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 64 - color overlay layer style helper plugin`
