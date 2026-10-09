# Current Task — Iteration 68

## Task
**Phase 66 — Non-Destructive Bevel and Emboss Layer Style Helper Plugin (`python-fu-bevel-emboss`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 107-118, 432: "Apply layer effects - Add layer styles", "Work with preset styles", "Layer style effects and options overview", and `photoshop_docs.md` Section 113-115 lines 3433-3610: "View and edit layer effects and styles using the Layer Style dialog in professional photoeditor... Bevel & Emboss: Style [Inner Bevel, Outer Bevel, Emboss, Pillow Emboss], Technique [Smooth, Chisel Hard, Chisel Soft], Depth, Direction [Up, Down], Size, Soften, Shading Angle & Altitude, Highlight Mode/Opacity, Shadow Mode/Opacity"), Bevel and Emboss is the signature 3D surface relief layer style in professional graphic design, UI styling, icon fabrication, and typographic styling.

Stock GIMP provides no built-in equivalent to Photoshop's Bevel and Emboss layer style, lacks non-destructive 3D height-map normal shading, lacks multi-style support (Inner Bevel, Outer Bevel, Emboss, Pillow Emboss), lacks technique styling (Smooth, Chisel Hard, Chisel Soft), lacks directional up/down relief inversion, lacks directional light Angle (-180° to 180°) and Altitude (0° to 90°) spherical illumination, lacks independent Highlight (Screen) and Shadow (Multiply) compositing passes, and lacks dedicated non-destructive layer placement leaving underlying artwork 100% untouched (`diff == 0.000000`).

Implementing native GIMP 3.x Python 3 plugin `bevel-emboss` closes this gap with complete Photoshop parity:
1. `python-fu-bevel-emboss`:
   - Structure & Geometry:
     - `style`: Choice (`inner-bevel`, `outer-bevel`, `emboss`, `pillow-emboss`, default `inner-bevel`).
     - `technique`: Choice (`smooth`, `chisel-hard`, `chisel-soft`, default `smooth`).
     - `depth`: Percentage slider (1.0% to 1000.0%, default 100.0%).
     - `direction`: Choice (`up`, `down`, default `up`).
     - `size`: Radius distance in pixels (0.0 to 250.0px, default 5.0px).
     - `soften`: Edge blur smoothing in pixels (0.0 to 16.0px, default 0.0px).
   - Shading & Illumination:
     - `angle`: Azimuth lighting angle (-180.0° to 180.0°, default 120.0°).
     - `altitude`: Elevation lighting angle (0.0° to 90.0°, default 30.0°).
     - `gloss`: Contour response (`linear`, `curved`, default `linear`).
   - Highlight Controls:
     - `highlight-mode`: Choice (`screen`, `normal`, `overlay`, `soft-light`, `linear-dodge`, default `screen`).
     - `highlight-r`, `highlight-g`, `highlight-b`: Highlight color RGB (0.0 to 1.0, default 1.0, 1.0, 1.0).
     - `highlight-opacity`: Percentage slider (0.0% to 100.0%, default 75.0%).
   - Shadow Controls:
     - `shadow-mode`: Choice (`multiply`, `normal`, `darken`, `color-burn`, `linear-burn`, default `multiply`).
     - `shadow-r`, `shadow-g`, `shadow-b`: Shadow color RGB (0.0 to 1.0, default 0.0, 0.0, 0.0).
     - `shadow-opacity`: Percentage slider (0.0% to 100.0%, default 75.0%).
   - Presets:
     - `preset`: Choice (`classic-inner-bevel`, `hard-chisel-metal`, `deep-emboss`, `pillow-carved`, `soft-round-bevel`, `outer-rim`, `custom`).
   - Layer Masking:
     - `mask-type`: Choice (`auto`, `none`, `reveal-all`, `conceal-all`, `selection`).
   - Non-Destructive Architecture:
     - Dedicated container group `(Bevel & Emboss)` inserted immediately above target layer with independent `Highlight` and `Shadow` passes.
     - Strict silhouette clipping for Inner Bevel ($A_{\text{hl}}, A_{\text{sh}} \le A_{\text{target}}$).
     - Target layer artwork and underlying canvas pixels remain 100% untouched (`diff == 0.000000`).
     - Single-step `Ctrl+Z` undo protection.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/bevel-emboss/bevel-emboss.py` (New plugin implementing `python-fu-bevel-emboss`)
- `PhotoGIMP/scripts/verify_config.py` (Register `bevel-emboss` in `REQUIRED_PLUGINS`, updating audit inventory to 60 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 61: `test_bevel_emboss`, assertions BE-01 through BE-16)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Bevel & Emboss Layer Style entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 66 status)
- `.ralph/PROGRESS.md` (Log Iteration 68 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 68 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/bevel-emboss/` created with `bevel-emboss.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure registered in GIMP PDB:
   - `python-fu-bevel-emboss` under `<Image>/Layer/Layer Style/Bevel and Emboss...`, `<Image>/Filters/Light and Shadow/Bevel and Emboss (Layer Style)...`, and `<Image>/Filters/Retouching`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 61):
   - BE-01: Procedure lookup and argument signatures verified across all 20 properties.
   - BE-02: Execution status verified (PDB status SUCCESS).
   - BE-03: Directional lighting verified (top-left highlight > 0, bottom-right shadow > 0 at 120°).
   - BE-04: Flat interior neutrality (center flat alpha is 0.0 for both highlight and shadow).
   - BE-05: Strict boundary silhouette clipping for Inner Bevel (outside alpha strictly 0.000).
   - BE-06: Direction inversion verified (Direction Down swaps highlight and shadow positions).
   - BE-07: Light angle rotation verified (Angle 0° illuminates right edge with shadow on left).
   - BE-08: Light altitude modulation verified (Altitude 75° softens directional contrast vs Altitude 15°).
   - BE-09: Depth scaling verified (Depth 300% produces higher shading intensity than Depth 50%).
   - BE-10: Bevel styles verified (Inner Bevel, Outer Bevel, Emboss, Pillow Emboss).
   - BE-11: Bevel techniques verified (Smooth vs Chisel Hard edge sharpness).
   - BE-12: Custom highlight and shadow colors RGB fidelity verified.
   - BE-13: Curated presets verified across all choices.
   - BE-14: Layer stack placement and group container verified (Highlight Screen mode, Shadow Multiply mode).
   - BE-15: Auto layer mask attachment behavior verified.
   - BE-16: Target and base layer artwork 100% untouched across all operations (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 60 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement non-destructive bevel and emboss layer style helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 68 - bevel and emboss layer style helper plugin`
