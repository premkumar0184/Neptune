# Current Task — Iteration 63

## Task
**Phase 61 — Non-Destructive Inner Shadow Layer Style Helper Plugin (`python-fu-inner-shadow`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 107-118, 432: "Apply layer effects - Add layer styles", "Work with preset styles", "Layer style effects and options overview", and `photoshop_docs.md` Section 113-115 lines 3433-3500: "View and edit layer effects and styles using the Layer Style dialog in professional photoeditor... Inner Shadow: Blend Mode, Opacity, Noise, Color, Angle, Use Global Light, Distance, Choke, Size, Contour"), Inner Shadow represents the companion layer style to Drop Shadow and Inner Glow, casting directional shading inside the silhouette of a layer or selection to simulate depth, engraving, cutouts, and recessed surface bevels.

Stock GIMP lacks a dedicated Inner Shadow layer style dialog, lacks Photoshop's directional light angle trigonometry (-180° to 180°), lacks Distance translation offset inside the silhouette, lacks Choke boundary contraction prior to blurring, lacks Size blur radius falloff, lacks Contour range falloff curve shaping ($A' = A^{50/\text{range}}$), lacks film grain noise texture injection, and lacks dedicated shadow layer positioning clipped strictly inside the target layer's silhouette, leaving underlying artwork 100% untouched (`diff == 0.000000`).

Implementing native GIMP 3.x Python 3 plugin `inner-shadow` closes this gap with complete Photoshop parity:
1. `python-fu-inner-shadow`:
   - Geometry & Directional Light Controls:
     - `angle`: Light angle in degrees (-180.0° to 180.0°, default 120.0°). Light from angle $\theta$ casts shadow inward along $\Delta x = -\text{distance} \cdot \cos(\theta), \Delta y = \text{distance} \cdot \sin(\theta)$.
     - `distance`: Pixel translation offset (0.0 to 200.0px, default 5.0px).
     - `choke`: Percentage slider (0.0% to 100.0%, default 0.0%). Thickens solid shadow boundary prior to blur.
     - `size`: Halo blur radius in pixels (0.0 to 200.0px, default 5.0px).
     - `range`: Opacity falloff contour percentage (1.0% to 100.0%, default 50.0%).
   - Presets & Color Controls:
     - `preset`: Choice (`default`, `deep-carved`, `subtle-inset`, `soft-ambient`, `hard-edge`, `custom`).
     - `shadow-r`, `shadow-g`, `shadow-b`: Solid Shadow Color RGB (default black `[0.0, 0.0, 0.0]`).
     - `noise`: Film grain noise percentage (0.0% to 100.0%, default 0.0%).
   - Blending & Masking:
     - `blend-mode`: Choice (`multiply`, `normal`, `darken`, `burn`, `linear-burn`).
     - `opacity`: Percentage slider (0.0% to 100.0%, default 75.0%).
     - `mask-type`: Choice (`auto`, `none`, `reveal-all`, `conceal-all`, `selection`).
   - Non-Destructive Operation:
     - Dedicated shadow layer inserted directly above the target layer in the stack.
     - Shadow pixels clipped strictly within the target layer's silhouette (outside alpha strictly `0.000`).
     - Target layer artwork and underlying canvas 100% untouched (`diff == 0.000000`).
     - Single-step `Ctrl+Z` undo protection.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/inner-shadow/inner-shadow.py` (New plugin implementing `python-fu-inner-shadow`)
- `PhotoGIMP/scripts/verify_config.py` (Register `inner-shadow` in `REQUIRED_PLUGINS`, updating audit inventory to 55 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 56: `test_inner_shadow`, assertions IS-01 through IS-15)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Inner Shadow Layer Style entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 61 status)
- `.ralph/PROGRESS.md` (Log Iteration 63 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 63 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/inner-shadow/` created with `inner-shadow.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure registered in GIMP PDB:
   - `python-fu-inner-shadow` under `<Image>/Layer/Layer Style/Inner Shadow...`, `<Image>/Filters/Light and Shadow/Inner Shadow (Layer Style)...`, and `<Image>/Filters/Retouching`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 56):
   - IS-01: Procedure lookup and argument signatures verified across all 16 properties.
   - IS-02: Execution status verified (PDB status SUCCESS).
   - IS-03: Light angle 120° directional shadow cast verified (top-left inner edge alpha > bottom-right inner edge alpha).
   - IS-04: Light angle 0° directional shadow cast verified (left inner edge alpha > right inner edge alpha).
   - IS-05: Strict boundary silhouette clipping (pixels outside target layer silhouette are strictly alpha 0.000).
   - IS-06: Distance offset translation verified (distance 20px projects deeper into interior than distance 5px).
   - IS-07: Choke boundary expansion control verified (choke 50% retains higher edge density than choke 0%).
   - IS-08: Size halo radius control verified (larger size penetrates deeper with smoother gradient).
   - IS-09: Custom shadow RGB color fidelity verified (e.g. blue/sepia shadow).
   - IS-10: Curated presets verified (`deep-carved`, `subtle-inset`, `soft-ambient`, `hard-edge`).
   - IS-11: Layer stack placement verified (shadow layer inserted immediately above parent layer in stack).
   - IS-12: Blend modes & opacity validation (Multiply, Normal, Darken, Color Burn, Linear Burn & 75% opacity validated).
   - IS-13: Range contour falloff modulation verified (range 80% retains higher inner alpha than range 20%).
   - IS-14: Conceal-All black layer mask and noise texture variance verified.
   - IS-15: Target and base layer artwork 100% untouched across all operations (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 55 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement non-destructive inner shadow layer style helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 63 - inner shadow layer style helper plugin`
