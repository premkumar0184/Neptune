# Current Task — Iteration 72

## Task
**Phase 70 — Smart Filters & Non-Destructive Filter Effects Helper Plugin (`smart-filters`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 454, 459: "Smart filters - Sharpening overview", "Apply and manage Smart Filters"; `photoshop_docs.md` Section 138 lines 4057-4066, Section 153 lines 4408-4434, Section 413-415 lines 12047-12115, Section 446 lines 13049-13056):
1. **Smart Filter Objects & Containers**:
   - In Photoshop, applying a filter to a Smart Object converts it into a non-destructive Smart Filter.
   - The original source content is preserved pristine without degradation so that repeated adjustments never accumulate quantization or blur artifacts.
2. **Non-Destructive Re-Editable Filter Passes**:
   - Supports popular filter types: Gaussian Blur, Smart Sharpen (unsharp mask), High Pass, Vignette, Noise Reduction, Diffuse Glow, Pixelize, and Oilify.
   - Presets include `soft-portrait-blur`, `crisp-unsharp-sharpen`, `high-pass-texture`, `vintage-vignette`, `subtle-denoise`, `dreamy-glow`, and `retro-pixel-art`.
   - Re-editing the filter re-computes the effect from the pristine original source pixels while preserving mask edits.
3. **Smart Filter Mask (`Filter Mask`)**:
   - A dedicated layer mask attached to the Smart Filter layer controls exactly where the filter effect is visible (white reveals filter effect, black conceals filter effect, gray provides soft transitions).
   - Filter mask is preserved intact across parameter adjustments.
4. **Rasterize & Clear Operations**:
   - `Rasterize Smart Filters`: Bakes the filter effect permanently into a standard raster layer (Photoshop `Layer > Rasterize > Smart Object`).
   - `Clear Smart Filters`: Discards the filter effect and mask, cleanly restoring the pristine original layer pixels (`diff == 0.000000`).

Stock GIMP has no built-in equivalent for Photoshop's non-destructive Smart Filters. Implementing `smart-filters` provides full Photoshop parity on Linux.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/smart-filters/smart-filters.py` (New plugin implementing 5 PDB procedures: `python-fu-convert-for-smart-filters`, `python-fu-apply-smart-filter`, `python-fu-edit-smart-filter`, `python-fu-rasterize-smart-filters`, `python-fu-clear-smart-filters`)
- `PhotoGIMP/scripts/verify_config.py` (Register `smart-filters` in `REQUIRED_PLUGINS`, updating audit inventory to 64 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 65: `test_smart_filters`, assertions SF-01 through SF-16)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Smart Filters & Non-Destructive Filter Effects Helper entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 70 status)
- `.ralph/PROGRESS.md` (Log Iteration 72 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 72 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/smart-filters/` created with `smart-filters.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] 5 PDB procedures registered in GIMP PDB:
   - `python-fu-convert-for-smart-filters` under `<Image>/Filters/Smart Filters` and `<Image>/Layer/Smart Objects`
   - `python-fu-apply-smart-filter` under `<Image>/Filters/Smart Filters`
   - `python-fu-edit-smart-filter` under `<Image>/Filters/Smart Filters`
   - `python-fu-rasterize-smart-filters` under `<Image>/Filters/Smart Filters` and `<Image>/Layer/Rasterize`
   - `python-fu-clear-smart-filters` under `<Image>/Filters/Smart Filters`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 65):
   - SF-01: Procedure signatures and argument audit across all 5 procedures.
   - SF-02: Convert for Smart Filters encapsulation (container group with hidden pristine source and active render layer).
   - SF-03: Apply Smart Filter (Gaussian blur) execution status SUCCESS and filter rendered on target.
   - SF-04: Smart Filter Mask attachment (mask attached and controls localized filter reveal/conceal).
   - SF-05: Non-destructive pristine source preservation (source pixels 100% identical to original artwork `diff == 0.000000`).
   - SF-06: Edit Smart Filter re-rendering (changing radius re-renders from source without degrading image quality).
   - SF-07: Filter mask preservation across edits (painted mask values preserved intact when filter is edited).
   - SF-08: Blend Mode & Opacity adjustments (Filter layer opacity and blend mode correctly assigned).
   - SF-09: Multiple filter types supported (`smart-sharpen`, `high-pass`, `vignette`, `diffuse-glow`, `pixelize`).
   - SF-10: Curated presets verified across all presets.
   - SF-11: Auto-conversion when applying smart filter directly to standard raster layer.
   - SF-12: Rasterize Smart Filters bakes filter down to standard raster layer and removes container.
   - SF-13: Clear Smart Filters discards filters and restores original pristine pixels (`diff == 0.000000`).
   - SF-14: Filter mask initialization options (`reveal-all`, `conceal-all`, `from-selection`).
   - SF-15: Single-step undo group encapsulation verified.
   - SF-16: Target & base canvas artwork preservation verification (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 64 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement smart filters and non-destructive filter effects helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 72 - smart filters and non-destructive filter effects helper plugin`
