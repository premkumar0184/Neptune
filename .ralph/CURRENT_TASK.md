# Current Task — Iteration 60

## Task
**Phase 58 — Non-Destructive Outer Glow Layer Style Helper Plugin (`python-fu-outer-glow`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 107-118, 432: "Apply layer effects - Add layer styles", "Work with preset styles", "Layer style effects and options overview", and `photoshop_docs.md` Section 113-115 lines 3433-3500: "View and edit layer effects and styles using the Layer Style dialog in professional photoeditor... Outer Glow effect parameters: Blend Mode, Color, Opacity, Noise, Technique, Spread, Size, Range..."), Outer Glow is one of Photoshop's most essential non-destructive layer effects, universally used in graphic design, icon creation, typography, and photo retouching to create ambient rim lighting, neon signage halos, and ethereal specular backlights.

Stock GIMP provides no dedicated Outer Glow layer style. Users are forced to manually duplicate layers, lock alpha, fill with color, feather or grow selections, apply Gaussian blur, reposition in the stack, and clear the original silhouette manually. This manual procedure is destructive, tedious, and lacks Photoshop's integrated controls:
1. Lacks dedicated Outer Glow layer style dialog simulating Photoshop `Layer > Layer Style > Outer Glow...`.
2. Lacks Photoshop's 5 core glow blend modes: Screen (Photoshop default), Normal, Lighten, Color Dodge, and Linear Dodge (Add).
3. Lacks Spread parameter (expanding the solid alpha matte prior to blurring to control glow density and falloff hardness).
4. Lacks Size parameter (Gaussian blur radius and glow halo spread).
5. Lacks Range contour falloff parameter (power-curve / gamma shaping the alpha decay from edge to perimeter).
6. Lacks Technique selection (`softer` standard Gaussian blur vs `precise` sharp rim glow).
7. Lacks Layer Knocks Out Glow silhouette clipping (cutting out the parent silhouette so glow radiates strictly outward from the edges and leaves parent pixels clean).
8. Lacks film grain texture noise injection.
9. Lacks curated photographic and graphic style presets (Photoshop Standard Warm Glow, Neon Cyan Halo, Golden Radiance, Ethereal White, Magical Magenta, Radioactive Green, Subtle Soft Edge, Custom Sliders).
10. Lacks dedicated glow layer positioning immediately beneath the parent layer, leaving parent artwork 100% untouched (`diff == 0.000000`).

Implementing native GIMP 3.x Python 3 plugin `outer-glow` closes this gap with complete Photoshop parity:
1. `python-fu-outer-glow`:
   - Geometric & Softness Controls:
     - `spread`: Matte boundary expansion (0.0% to 100.0%, default 0.0%).
     - `size`: Blur radius / halo softness in pixels (0.0 to 200.0 px, default 15.0 px).
     - `range`: Glow falloff contour control (1.0% to 100.0%, default 50.0%).
     - `technique`: Glow technique choice (`softer`, `precise`).
     - `knockout`: Boolean silhouette clipping (default True).
     - `noise`: Film grain texture injection (0.0% to 100.0%, default 0.0%).
   - Color & Appearance:
     - `glow-r`, `glow-g`, `glow-b`: Custom RGB color channels (default warm yellow `[1.0, 0.95, 0.6]`).
     - `opacity`: Glow layer opacity (0.0% to 100.0%, default 75.0%).
     - `blend-mode`: Choice (`screen`, `normal`, `lighten`, `dodge`, `addition`).
   - Curated Presets:
     - `default`: Photoshop Standard Warm Glow.
     - `neon-cyan`: Cyberpunk Neon Cyan Halo.
     - `golden-radiance`: Rich Warm Gold Radiance.
     - `ethereal-white`: Pure Mystic White Halo.
     - `magical-magenta`: Neon Magenta Glow.
     - `radioactive-green`: Acid Green Hazard Glow.
     - `subtle-soft`: Subtle Ambient Edge Light.
     - `custom`: Manual sliders.
   - Non-Destructive Layer Architecture:
     - Dedicated glow layer placed immediately below target layer in layer stack.
     - Parent and base layer artwork preserved 100% (`diff == 0.000000`).
     - Editable layer mask support (auto, none, reveal-all, conceal-all, selection).
     - Single-step `Ctrl+Z` undo protection.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/outer-glow/outer-glow.py` (New plugin implementing `python-fu-outer-glow`)
- `PhotoGIMP/scripts/verify_config.py` (Register `outer-glow` in `REQUIRED_PLUGINS`, updating audit inventory to 52 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 53: `test_outer_glow`, assertions OG-01 through OG-15)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Outer Glow entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 58 status)
- `.ralph/PROGRESS.md` (Log Iteration 60 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 60 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/outer-glow/` created with `outer-glow.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure registered in GIMP PDB:
   - `python-fu-outer-glow` under `<Image>/Layer/Layer Style/Outer Glow...`, `<Image>/Filters/Light and Shadow/Outer Glow (Layer Style)...`, and `<Image>/Filters/Retouching`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 53):
   - OG-01: Procedure lookup and argument signatures verified across all properties.
   - OG-02: Execution status verified (PDB status SUCCESS).
   - OG-03: Outer glow omnidirectional radial falloff verified (glow expands equally outward in all 4 cardinal directions).
   - OG-04: Distance falloff verified (alpha closer to parent layer boundary > alpha further away).
   - OG-05: Spread expansion control verified (spread thickens solid core alpha prior to blur).
   - OG-06: Size halo radius control verified (larger size diffuses glow further outward).
   - OG-07: Silhouette knockout clipping verified (target layer silhouette cleared from glow layer).
   - OG-08: Custom glow RGB color fidelity verified.
   - OG-09: Curated presets verified (neon-cyan, golden-radiance, ethereal-white, magical-magenta, radioactive-green, subtle-soft).
   - OG-10: Dedicated glow layer stack placement beneath parent layer verified.
   - OG-11: Blend modes & opacity verified (Screen, Normal, Lighten, Color Dodge, Linear Dodge / Addition & 75% opacity).
   - OG-12: Range contour falloff modulation verified.
   - OG-13: Conceal-All black layer mask attachment verified.
   - OG-14: Film grain noise texture variance verified.
   - OG-15: Target & base layer pixels 100% untouched (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 52 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement non-destructive outer glow layer style helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 60 - outer glow layer style helper plugin`
