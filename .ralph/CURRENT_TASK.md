# Current Task — Iteration 57

## Task
**Phase 55 — Non-Destructive Exposure Adjustment Layer & Tonal Range Helper Plugin (`python-fu-exposure`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 93-96, 347: "Color adjustment and fill layers", "Adjustment and fill layers overview", "Work with adjustment layers", "Create adjustment layers", "Adjust HDR exposure and toning", and `photoshop_docs.md` Section 338 lines 9935-9985: "Apply Exposure adjustments or HDR Toning to control highlights, shadows, and midtones... Exposure adjustments work non-destructively through adjustment layers, preserving your original image data and allowing you to modify or remove adjustments at any time... Layer>New Adjustment Layer>Exposure. In the Adjustments panel, adjust the Exposure slider to modify the highlight end of the tonal scale with minimal effect on shadows. Adjust the Offset slider to darken shadows and midtones without significantly affecting highlights. Adjust the Gamma slider to modify midtone values using a power function..."), Exposure adjustments are a fundamental non-destructive adjustment layer workflow.

Photoshop calculates exposure using a three-parameter tone equation in linear color space:
$$I' = \left(\max\left(0, I \cdot 2^{\text{exposure}} + \text{offset}\right)\right)^{1 / \text{gamma}}$$
Where:
1. `exposure` (-5.0 to +5.0 EV stops, default 0.0): Scales linear intensity by power-of-two EV stops, expanding or compressing highlights with proportional impact.
2. `offset` (-0.5 to +0.5, default 0.0): Additive bias adjusting shadow and black-point levels.
3. `gamma` (0.01 to 9.99, default 1.0): Exponential midtone power curve correction where $\gamma > 1.0$ brightens midtones and $\gamma < 1.0$ darkens midtones.

Stock GIMP provides the basic interactive Exposure tool (`gimp-drawable-exposure` / `gegl:exposure`), but:
1. Lacks a dedicated "New Exposure Adjustment Layer" workflow dialog.
2. Does not implement Photoshop's non-destructive adjustment layer architecture where the active drawable is duplicated into a dedicated adjustment layer, leaving original source pixels 100% untouched (`diff == 0.000000`).
3. Lacks photographic exposure presets (Default / Reset, +1 Stop Overexposure, +2 Stops Overexposure, -1 Stop Underexposure, -2 Stops Underexposure, Shadow Boost / Lift, Highlight Recovery, High Dynamic Compression, Custom sliders).
4. Lacks professional blend modes (Normal, Luminosity, Multiply, Screen, Overlay, Soft Light), opacity scaling, and automatic editable layer mask attachment (Auto, None, Reveal-All, Conceal-All, Active Selection).

Implementing native GIMP 3.x Python 3 plugin `exposure` closes this gap with complete Photoshop parity:
1. `python-fu-exposure`:
   - Three Exposure Sliders:
     - `exposure`: EV stops (-5.0 to +5.0, default 0.0).
     - `offset`: Shadow level offset (-0.50 to +0.50, default 0.0).
     - `gamma`: Midtone power curve exponent (0.10 to 5.00, default 1.0).
   - Curated Photographic Presets:
     - `default`: Reset (EV 0.0, Offset 0.0, Gamma 1.0).
     - `plus-1-stop`: +1.0 EV stop brighten.
     - `plus-2-stops`: +2.0 EV stops high-key brighten.
     - `minus-1-stop`: -1.0 EV stop underexposure / highlight rescue.
     - `minus-2-stops`: -2.0 EV stops low-key underexposure.
     - `shadow-lift`: EV 0.0, Offset +0.10, Gamma 1.25.
     - `highlight-recovery`: EV -1.2, Offset 0.0, Gamma 1.35.
     - `dynamic-compression`: EV +0.6, Offset -0.08, Gamma 0.90.
     - `custom`: Custom user sliders.
   - Non-Destructive Workflow:
     - Duplicates active drawable into a dedicated adjustment layer named `[Exposure Adjustment]`.
     - Preserves original source pixels 100% untouched (`diff == 0.000000`).
   - Professional Blend Modes: Normal, Luminosity (`Gimp.LayerMode.LUMINANCE`), Multiply, Screen, Overlay, Soft Light.
   - Opacity slider (0.0 to 100.0%).
   - Layer Mask Options: `auto` (active selection if present, else none), `none`, `reveal-all` (white), `conceal-all` (black), `selection`.
   - Single-Step Undo Protection: Encapsulated within `image.undo_group_start()` and `image.undo_group_end()`.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/exposure/exposure.py` (New plugin implementing `python-fu-exposure`)
- `PhotoGIMP/scripts/verify_config.py` (Register `exposure` in `REQUIRED_PLUGINS`, updating audit inventory to 49 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 50: `test_exposure_adjustment`, assertions EXP-01 through EXP-14)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Exposure Adjustment Layer entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 55 status)
- `.ralph/PROGRESS.md` (Log Iteration 57 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 57 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/exposure/` created with `exposure.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure registered in GIMP PDB:
   - `python-fu-exposure` under `<Image>/Layer/New Adjustment Layer/Exposure...`, `<Image>/Image/Adjustments/Exposure...`, `<Image>/Filters/Retouching`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 50):
   - EXP-01: Procedure lookup and argument signatures verified across all properties.
   - EXP-02: Execution status verified (PDB status SUCCESS).
   - EXP-03: Exposure EV stops +1.0 scaling verified ($I' \approx 2 \cdot I$).
   - EXP-04: Exposure EV stops -1.0 scaling verified ($I' \approx 0.5 \cdot I$).
   - EXP-05: Offset shadow black point adjustment verified (dark pixels lifted/offset).
   - EXP-06: Gamma midtone curve response verified ($\gamma > 1.0$ brightens midtones).
   - EXP-07: Curated photographic presets verified (+1 stop, -1 stop, shadow lift, highlight recovery).
   - EXP-08: Non-destructive adjustment layer generated above active layer.
   - EXP-09: Blend modes and opacity verified (Luminosity, Multiply, Screen, Overlay, Soft Light & 75% opacity).
   - EXP-10: Conceal-All black layer mask verified (black mask attached, composite invariance).
   - EXP-11: Reveal-All white layer mask verified.
   - EXP-12: Active selection auto-mask confinement verified.
   - EXP-13: In-place mode verified (when requested on target drawable).
   - EXP-14: Base layer pixel preservation verified (original source pixels 100% untouched with diff == 0.000000).
5. [x] `verify_config.py` Section 6 passes with all 49 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement non-destructive exposure adjustment layer and tonal range helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 57 - exposure adjustment layer and tonal range helper plugin`

