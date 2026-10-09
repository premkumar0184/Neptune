# Current Task — Iteration 69

## Task
**Phase 67 — Non-Destructive Stroke Layer Style Helper Plugin (`python-fu-stroke-style`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 107-118, 432: "Apply layer effects - Add layer styles", "Work with preset styles", "Layer style effects and options overview", and `photoshop_docs.md` Section 113-115 lines 3433-3500: "View and edit layer effects and styles using the Layer Style dialog in professional photoeditor... Stroke: Size, Position [Outside, Inside, Center], Blend Mode, Opacity, Overprint, Fill Type [Color, Gradient, Pattern]"), Stroke is a core layer style in professional graphic design, UI styling, icon fabrication, and typographic styling.

While Phase 54 introduced `stroke-layer` for `Edit > Stroke...` selection outlines, stock GIMP provides no built-in equivalent to Photoshop's dedicated Stroke Layer Style dialog. Specifically, it lacks:
- Native Photoshop Stroke Layer Style integration (`Layer > Layer Style > Stroke...`);
- Three distinct Fill Types: Solid Color, Gradient (Linear, Radial, Reflected with Angle & Scale), and Pattern (Checkerboard, Stripes, Mesh, Polka Dots, Carbon Fiber, Active Pattern with Scale);
- Geometric Position Modes: Outside (stroke dilates outward from silhouette), Inside (stroke insets strictly within layer silhouette), and Center (stroke is centered across the silhouette boundary);
- Dedicated non-destructive layer placement (Outside placed immediately beneath target layer or Inside placed above target layer, or in a grouped layer style container), leaving underlying target artwork 100% untouched (`diff == 0.000000`);
- Curated stroke style presets;
- Standard Photoshop blend modes and opacity scaling;
- Auto, None, Reveal-All, Conceal-All, and Active Selection layer mask integration;
- Single-step `Ctrl+Z` undo protection.

Implementing native GIMP 3.x Python 3 plugin `stroke-style` closes this gap with complete Photoshop parity.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/stroke-style/stroke-style.py` (New plugin implementing `python-fu-stroke-style`)
- `PhotoGIMP/scripts/verify_config.py` (Register `stroke-style` in `REQUIRED_PLUGINS`, updating audit inventory to 61 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 62: `test_stroke_style`, assertions STRK-01 through STRK-16)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Stroke Layer Style entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 67 status)
- `.ralph/PROGRESS.md` (Log Iteration 69 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 69 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/stroke-style/` created with `stroke-style.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure registered in GIMP PDB:
   - `python-fu-stroke-style` under `<Image>/Layer/Layer Style/Stroke...`, `<Image>/Filters/Light and Shadow/Stroke (Layer Style)...`, and `<Image>/Filters/Retouching`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 62):
   - STRK-01: Procedure lookup and argument signatures verified across all properties.
   - STRK-02: Execution status verified (PDB status SUCCESS).
   - STRK-03: Outside stroke geometry verified (stroke appears outside original silhouette; interior artwork untouched).
   - STRK-04: Inside stroke geometry verified (stroke is strictly confined within original silhouette; outside pixels alpha strictly 0.000).
   - STRK-05: Center stroke geometry verified (stroke straddles the silhouette boundary with both inside and outside expansion).
   - STRK-06: Size scaling verified (width 10px creates wider stroke band than width 3px).
   - STRK-07: Solid Color fill type & RGB fidelity verified (custom RGB swatch accurate).
   - STRK-08: Gradient fill type verified (linear and radial gradients rendered inside stroke band).
   - STRK-09: Pattern fill type verified (repeating pattern texture rendered inside stroke band).
   - STRK-10: Curated presets verified across all choices (e.g. classic black, white sticker, gold luxury, neon glow, etc.).
   - STRK-11: Blend modes validated (Normal, Multiply, Screen, Overlay, Soft Light, Darken, Lighten, Color).
   - STRK-12: Opacity modulation verified (opacity 50% scales stroke alpha).
   - STRK-13: Layer stack placement verified (outside stroke placed immediately beneath, inside stroke placed immediately above).
   - STRK-14: Auto layer mask attachment behavior verified (selection when active, none when empty).
   - STRK-15: Target layer artwork and base pixels 100% untouched (`diff == 0.000000`).
   - STRK-16: Single-step undo group encapsulation verified.
5. [x] `verify_config.py` Section 6 passes with all 61 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement non-destructive stroke layer style helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 69 - stroke layer style helper plugin`
