# Current Task — Iteration 62

## Task
**Phase 60 — Non-Destructive Inner Glow Layer Style Helper Plugin (`python-fu-inner-glow`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 107-118, 432: "Apply layer effects - Add layer styles", "Work with preset styles", "Layer style effects and options overview", and `photoshop_docs.md` Section 113-115 lines 3433-3500: "View and edit layer effects and styles using the Layer Style dialog in professional photoeditor... Inner Glow: Blend Mode, Opacity, Noise, Color/Gradient, Technique (Softer/Precise), Source (Center/Edge), Choke, Size, Contour, Range, Jitter"), Inner Glow represents the companion layer style to Outer Glow and Drop Shadow.

Stock GIMP lacks a dedicated Inner Glow layer style dialog, lacks Photoshop's dual radiance source modes (Edge vs Center), lacks Choke boundary contraction prior to blurring, lacks Size blur radius falloff, lacks Range contour curve modulation ($A' = A^{50/\text{range}}$), lacks Technique selection (`softer` vs `precise`), lacks film grain noise texture injection, and lacks dedicated glow layer positioning clipped strictly inside the target layer's silhouette, leaving underlying artwork 100% untouched (`diff == 0.000000`).

Implementing native GIMP 3.x Python 3 plugin `inner-glow` closes this gap with complete Photoshop parity:
1. `python-fu-inner-glow`:
   - Geometry & Source Modes:
     - `source`: Choice (`edge` inward from silhouette boundaries, `center` outward from interior core).
     - `technique`: Choice (`softer` Gaussian blur, `precise` concentrated boundary).
     - `choke`: Percentage slider (0.0% to 100.0%, default 0.0%).
     - `size`: Halo blur radius in pixels (0.0 to 200.0px, default 10.0px).
     - `range`: Opacity falloff contour percentage (1.0% to 100.0%, default 50.0%).
   - Presets & Color Controls:
     - `preset`: Choice (`default`, `neon-cyan`, `candlelight`, `center-spotlight`, `cyberpunk-core`, `subtle-rim`, `custom`).
     - `glow-r`, `glow-g`, `glow-b`: Solid Glow Color RGB (default warm yellow `[1.0, 0.95, 0.60]`).
     - `noise`: Film grain noise percentage (0.0% to 100.0%, default 0.0%).
   - Blending & Masking:
     - `blend-mode`: Choice (`screen`, `normal`, `lighten`, `dodge`, `addition`, `overlay`, `multiply`).
     - `opacity`: Percentage slider (0.0% to 100.0%, default 75.0%).
     - `mask-type`: Choice (`auto`, `none`, `reveal-all`, `conceal-all`, `selection`).
   - Non-Destructive Operation:
     - Dedicated glow layer inserted directly above the target layer in the stack.
     - Glow pixels clipped strictly within the target layer's silhouette (outside alpha strictly `0.000`).
     - Target layer artwork and underlying canvas 100% untouched (`diff == 0.000000`).
     - Single-step `Ctrl+Z` undo protection.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/inner-glow/inner-glow.py` (New plugin implementing `python-fu-inner-glow`)
- `PhotoGIMP/scripts/verify_config.py` (Register `inner-glow` in `REQUIRED_PLUGINS`, updating audit inventory to 54 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 55: `test_inner_glow`, assertions IG-01 through IG-15)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Inner Glow Layer Style entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 60 status)
- `.ralph/PROGRESS.md` (Log Iteration 62 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 62 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/inner-glow/` created with `inner-glow.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure registered in GIMP PDB:
   - `python-fu-inner-glow` under `<Image>/Layer/Layer Style/Inner Glow...`, `<Image>/Filters/Light and Shadow/Inner Glow (Layer Style)...`, and `<Image>/Filters/Retouching`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 55):
   - IG-01: Procedure lookup and argument signatures verified across all 16 properties.
   - IG-02: Execution status verified (PDB status SUCCESS).
   - IG-03: Edge source inward radiance verified (edge pixel alpha > interior pixel alpha).
   - IG-04: Center source outward radiance verified (interior core alpha > edge pixel alpha).
   - IG-05: Strict boundary silhouette clipping (pixels outside target layer silhouette are strictly alpha 0.000).
   - IG-06: Choke boundary expansion control verified (choke 50% retains higher edge density than choke 0%).
   - IG-07: Size halo radius control verified (larger size penetrates deeper into the interior).
   - IG-08: Technique selection verified (`softer` vs `precise`).
   - IG-09: Custom glow RGB color fidelity verified.
   - IG-10: Curated presets verified (Neon-cyan, candlelight, center-spotlight, cyberpunk-core, subtle-rim).
   - IG-11: Layer stack placement verified (glow layer inserted immediately above parent layer in stack).
   - IG-12: Blend modes & opacity validation (Screen, Normal, Lighten, Dodge, Addition, Overlay, Multiply & 75% opacity validated).
   - IG-13: Range contour falloff modulation verified (range 80% retains higher inner alpha than range 20%).
   - IG-14: Conceal-All black layer mask and noise texture variance verified.
   - IG-15: Target and base layer artwork 100% untouched across all operations (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 54 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement non-destructive inner glow layer style helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 62 - inner glow layer style helper plugin`
