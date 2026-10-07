# Current Task — Iteration 43

## Task
**Phase 41 — Non-Destructive Oil Paint & Fine Art Impasto Helper Plugin (`python-fu-oil-paint`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 485: "Artistic and stylize filters - Oil Paint filter settings", and `photoshop_docs.md` Section 416 line 12058: "Filter > Stylize > Oil Paint: Creative effects, such as Oil Paint in the Stylize category", and Section 424 line 16131: "Oil Paint filter settings"), the Oil Paint filter is one of the most distinctive artistic stylization tools. It transforms photographic pixels into textured fine-art oil paint with organic brush strokes, surface relief (impasto), and directional lighting luster. In Photoshop, users configure:
1. Brush settings:
   - Stylization (0.1 to 10.0): Controls stroke clustering and painterly neighborhood grouping.
   - Cleanliness (0.0 to 10.0): Controls stroke edge fluidity, transitioning from raw textured paint to smooth, liquid oil glaze.
   - Scale (0.1 to 10.0): Adjusts brush head width and thickness of the 3D impasto paint relief.
   - Bristle Detail (0.0 to 10.0): Adds micro-grooves and bristle streaks within the brush flow.
2. Lighting settings:
   - Lighting Toggle: Enables/disables directional surface relief lighting.
   - Light Angle (0.0° to 360.0°): Adjusts incident illumination angle.
   - Shine (0.0 to 5.0): Controls specular luster of wet oil paint.

Stock GIMP lacks a dedicated non-destructive Oil Paint tool that replicates Photoshop's workflow. Creating native Python 3 helper plugin `python-fu-oil-paint` provides full parity:
- Symmetric Nearest Neighbor stroke clustering (`gegl:snn-mean`) with radius and pairs.
- Cleanliness pre-smoothing pass (`gegl:gaussian-blur`).
- Rich pigment vibrance boost (`gegl:vibrance`).
- Directional surface relief and bristle detailing via 5x5 convolution matrix (`gegl:convolution-matrix`) with incident light angle and specular luster shine.
- Curated presets: Classic Impressionist Oil, Thick Impasto Palette Knife, Smooth Glaze Portrait, Expressionist Dynamic, Fine Canvas Detail, and Custom.
- Non-destructive adjustment layering with mask modes: Reveal All, Conceal All, and Selection.
- 100% mathematical preservation of base layer pixels underneath (`diff == 0.000000`).

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/oil-paint/oil-paint.py` (New plugin)
- `PhotoGIMP/scripts/verify_config.py` (Register `oil-paint` in `REQUIRED_PLUGINS`, updating inventory to 35 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 36: `test_oil_paint`, 11 assertions OP-01 through OP-11)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Oil Paint & Fine Art Impasto entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 41 status and schedule Phase 42)
- `.ralph/PROGRESS.md` (Log Iteration 43 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 43 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/oil-paint/` created with `oil-paint.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure `python-fu-oil-paint` registered in GIMP PDB under:
   - `<Image>/Filters/Artistic/Oil Paint...`
   - `<Image>/Filters/Stylize/Oil Paint...`
   - `<Image>/Layer`
4. [x] Non-destructive adjustment layer created duplicating active drawable.
5. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 36):
   - Base layer pixels underneath remain 100% untouched (`diff == 0.000000`).
   - Classic Impressionist Oil preset verified: stroke clustering variance reduction on high-frequency noise while preserving macro contrast.
   - Thick Impasto Palette Knife preset verified: high stylization and high specular shine relief (contrast 0.5906).
   - Smooth Glaze Portrait preset verified: fluid stroke pre-smoothing.
   - Expressionist Dynamic preset verified: bold brushwork with bristle relief.
   - Directional lighting response verified: varying light angle modifies directional impasto relief (delta 0.2318 across incident angles).
   - Conceal-All black layer mask verified: composite equals base layer (`diff == 0.000000`).
   - Selection-aware mask verified: oil paint confined strictly to active selection (inside 1.00, outside 0.00).
6. [x] `verify_config.py` Section 6 passes with all 35 required plugins audited.
7. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all stages cleanly with exit code 0 (341/341 assertions passing across 36 test suites).

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `d11c8d6`
- Outer repository commit: `feat(ralph): complete iteration 43 - non-destructive oil paint plugin`
