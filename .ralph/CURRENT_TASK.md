# Current Task — Iteration 58

## Task
**Phase 56 — Non-Destructive Drop Shadow Layer Style Helper Plugin (`python-fu-drop-shadow`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 107-118, 432: "Apply layer effects - Add layer styles", "Work with preset styles", "Layer style effects and options overview", "Add drop shadows to text", and `photoshop_docs.md` Section 113-115 lines 3433-3500: "View and edit layer effects and styles using the Layer Style dialog in professional photoeditor... Drop Shadow effect parameters: Blend Mode, Color, Opacity, Angle, Distance, Spread, Size, Noise, Layer Knocks Out Drop Shadow... Layer styles are non-destructive effects linked to layer contents..."), Drop Shadow is the most universally used Layer Style effect.

Stock GIMP provides only the destructive filter `gegl:drop-shadow`, which:
1. Lacks Photoshop Layer Style non-destructive architecture (a dedicated shadow layer placed immediately beneath the target layer, leaving the target layer and background 100% untouched `diff == 0.000000`).
2. Lacks Photoshop's light angle trigonometry ($\theta \in [-180^\circ, 180^\circ]$ where light from angle $\theta$ casts shadow in the opposite direction $\Delta x = -\text{distance} \cdot \cos(\theta)$, $\Delta y = \text{distance} \cdot \sin(\theta)$).
3. Lacks Spread parameter ($0\%$ to $100\%$, which expands the solid shadow matte before blurring).
4. Lacks "Layer Knocks Out Drop Shadow" option (cutting out the parent layer silhouette so semi-transparent layers are not muddied by the shadow underneath).
5. Lacks Noise/film grain in shadow.
6. Lacks curated presets (Default, Soft Drop, Hard Edge, Elevated Card, Neon Backlight, Vintage Sketch, Custom).
7. Lacks professional blend modes (Multiply, Normal, Darken, Color Burn, Linear Burn), opacity control, and editable layer mask integration.

Implementing native GIMP 3.x Python 3 plugin `drop-shadow` closes this gap with complete Photoshop parity:
1. `python-fu-drop-shadow`:
   - Geometric Controls:
     - `angle`: Light source angle (-180.0° to 180.0°, default 120.0°).
     - `distance`: Distance offset (0.0 to 200.0 px, default 10.0 px).
     - `spread`: Shadow matte expansion percentage (0.0% to 100.0%, default 0.0%).
     - `size`: Blur radius / softness (0.0 to 200.0 px, default 10.0 px).
     - `knockout`: Layer Knocks Out Drop Shadow boolean (default True).
     - `noise`: Film grain noise percentage (0.0% to 100.0%, default 0.0%).
   - Curated Presets:
     - `default`: Photoshop Standard (120°, 10px dist, 0% spread, 10px size, 75% opacity, Multiply, Black).
     - `soft-drop`: Soft ambient shadow (90°, 15px dist, 10% spread, 25px size, 50% opacity, Multiply).
     - `hard-edge`: Graphic cast shadow (135°, 12px dist, 80% spread, 4px size, 85% opacity, Multiply).
     - `elevated-card`: UI floating card elevation (90°, 20px dist, 5% spread, 30px size, 40% opacity, Multiply).
     - `neon-backlight`: Colorful glow / backlight (90°, 0px dist, 20% spread, 25px size, 90% opacity, Custom color).
     - `vintage-sketch`: Textured sketch shadow with noise (120°, 8px dist, 0% spread, 8px size, 25% noise, 80% opacity).
     - `custom`: Custom user sliders.
   - Shadow Color: Custom RGB sliders (default Black #000000).
   - Blend Modes: Multiply (`Gimp.LayerMode.MULTIPLY`), Normal, Darken, Color Burn, Linear Burn.
   - Opacity slider (0.0 to 100.0%).
   - Non-Destructive Layer Architecture:
     - Dedicated shadow layer positioned immediately beneath the target layer.
     - Preserves original target layer and base pixels 100% untouched (`diff == 0.000000`).
   - Layer Mask Integration: None, Reveal-All (white), Conceal-All (black), Active Selection.
   - Single-Step Undo Protection: Encapsulated within `image.undo_group_start()` and `image.undo_group_end()`.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/drop-shadow/drop-shadow.py` (New plugin implementing `python-fu-drop-shadow`)
- `PhotoGIMP/scripts/verify_config.py` (Register `drop-shadow` in `REQUIRED_PLUGINS`, updating audit inventory to 50 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 51: `test_drop_shadow`, assertions DS-01 through DS-15)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Drop Shadow Layer Style entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 56 status)
- `.ralph/PROGRESS.md` (Log Iteration 58 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 58 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/drop-shadow/` created with `drop-shadow.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure registered in GIMP PDB:
   - `python-fu-drop-shadow` under `<Image>/Layer/Layer Style/Drop Shadow...`, `<Image>/Filters/Light and Shadow/Drop Shadow (Layer Style)...`, `<Image>/Filters/Retouching`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 51):
   - DS-01: Procedure lookup and argument signatures verified across all properties.
   - DS-02: Execution status verified (PDB status SUCCESS).
   - DS-03: Light angle 120° trigonometry verified (shadow cast downward and rightward).
   - DS-04: Light angle 0° trigonometry verified (shadow cast leftward).
   - DS-05: Distance offset scaling verified (shadow center translates with distance).
   - DS-06: Size blur radius falloff verified (diffuse soft boundary).
   - DS-07: Spread expansion verified (spread increases solid core alpha radius).
   - DS-08: Layer Knocks Out Drop Shadow verified (parent layer interior cleared in shadow layer).
   - DS-09: Shadow custom color fidelity verified (custom RGB values in shadow layer).
   - DS-10: Curated presets verified (soft-drop, hard-edge, elevated-card, neon-backlight).
   - DS-11: Dedicated shadow layer inserted beneath target layer in stack.
   - DS-12: Blend modes (Multiply, Normal, Darken, Color Burn, Linear Burn) & 75% opacity validated.
   - DS-13: Conceal-All black layer mask and Reveal-All white layer mask verified.
   - DS-14: Shadow noise / graininess verified (variance > 0 when noise > 0).
   - DS-15: Target and base layer pixel preservation verified (original pixels 100% untouched with diff == 0.000000).
5. [x] `verify_config.py` Section 6 passes with all 50 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement non-destructive drop shadow layer style helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 58 - drop shadow layer style helper plugin`

