# Current Task — Iteration 42

## Task
**Phase 40 — Non-Destructive Glowing Edges & Neon Stylize Filter Helper Plugin (`python-fu-glowing-edges`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 451: "Apply filters from the filter gallery", line 452: "Filter Gallery overview", line 484: "Apply texture and surface effects to filters", and `photoshop_docs.md` Section 416 lines 12128-12135 "Filter Gallery: Category: Stylize, Examples: Glowing Edges... Purpose: Stylization and edge effects"), Glowing Edges is one of the most iconic artistic stylize filters. It identifies high-contrast boundaries and transitions in an image and turns them into vibrant, luminous neon lines against a dark backdrop or superimposed over the composition. In Photoshop, users configure Edge Width (1-14), Edge Brightness (1-20), and Smoothness (1-15), and frequently blend the resulting neon outlines back onto the underlying artwork using Screen or Addition blend modes. Stock GIMP offers only low-level GEGL operations with no preset management, no neon color grading modes, no non-destructive adjustment layering, and no selective masking. Creating a dedicated native Python 3 helper plugin (`python-fu-glowing-edges`) provides full Photoshop Glowing Edges parity: Edge Width (1.0 to 15.0px), Edge Brightness (1.0 to 20.0), Smoothness pre-filtering (1.0 to 15.0), multiple neon color grading options (Full Spectral Neon, Electric Cyan, Hot Magenta, Laser Green, Golden Amber, Monochrome White), compositing blend modes (Screen, Addition, Soft Light, Normal), layer opacity (10% to 100%), curated presets (Classic Neon, Cyberpunk Cyan, Synthwave Magenta, Laser Wireframe, Architectural White, Custom), versatile layer masks (Reveal All, Conceal All, Selection), and 100% mathematical preservation of base layer source pixels underneath (`diff == 0.000000`).

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/glowing-edges/glowing-edges.py` (New plugin)
- `PhotoGIMP/scripts/verify_config.py` (Register `glowing-edges` in `REQUIRED_PLUGINS`, updating audit inventory to 34 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 35: `test_glowing_edges`, 11 assertions GE-01 through GE-11)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Glowing Edges & Neon Stylize entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 40 status and schedule Phase 41)
- `.ralph/PROGRESS.md` (Log Iteration 42 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 42 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/glowing-edges/` created with `glowing-edges.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure `python-fu-glowing-edges` registered in GIMP PDB under:
   - `<Image>/Filters/Artistic/Glowing Edges...`
   - `<Image>/Filters/Stylize/Glowing Edges...`
   - `<Image>/Layer/New Glowing Edges Layer...`
4. [x] Non-destructive adjustment layer created duplicating active drawable.
5. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 35):
   - Base layer pixels underneath remain 100% untouched (`diff == 0.000000`).
   - Classic Neon preset verified: High-contrast edge turned to luminous glow (1.0000 > 0.50) while flat areas remain dark (0.0000 < 0.10).
   - Cyberpunk Cyan preset verified: Electric cyan dominance (B=1.0000, G=0.9473 > R=0.1981).
   - Synthwave Magenta preset verified: Hot magenta dominance (R=1.0000, B=0.8469 > G=0.2502).
   - Laser Wireframe preset verified: Normal mode wireframe with laser green dominance (G=1.0000 > R=0.2502).
   - Architectural White preset verified: Monochrome neutral white edge contours (spread 0.0000 < 0.02).
   - Edge Brightness & Width scaling verified.
   - Screen blend mode verified: Luminous contours overlay smoothly while preserving flat base colors (R=1.0000).
   - Conceal-All black layer mask verified: Composite equals base layer (0.000000 diff) ready for brush painting.
   - Selection-aware mask verified: Glowing edges confined strictly to active selection (inside 1.00, outside 0.00).
   - Custom sliders with width, brightness, smoothness, tone, blend mode, and opacity verified.
6. [x] `verify_config.py` Section 6 passes with all 34 required plugins audited.
7. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all stages cleanly with exit code 0 (329/329 assertions passing in 35 test suites).

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `66676b8`
- Outer repository commit: `feat(ralph): complete iteration 42 - non-destructive glowing edges plugin`

