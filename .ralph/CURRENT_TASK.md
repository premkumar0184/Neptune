# Current Task — Iteration 45

## Task
**Phase 43 — Non-Destructive HDR Toning & Tone Mapping Helper Plugin (`python-fu-hdr-toning`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 347: "HDR and channel manipulation - Adjust HDR exposure and toning", line 106: "Adjust image lighting with Light", line 269: "Adjust image shadows and highlights", and `photoshop_docs.md` Section 338 lines 9951-9985: "HDR Toning provides multiple tone-mapping methods including Local Adaptation, Equalize Histogram, Exposure and Gamma, and Highlight Compression. Each method offers different controls for managing contrast, exposure, and tonal range... Edge Glow, Tone and Detail, Color controls"), HDR Toning is one of Photoshop's premier color and dynamic range grading tools. It is used extensively by landscape, architectural, portrait, and commercial photographers to expand perceived dynamic range, recover shadow and highlight details, produce local contrast microcontrast halos (Edge Glow), and enhance color vibrance.

However, in Adobe Photoshop, `Image > Adjustments > HDR Toning...` has a notorious drawback: it is strictly destructive and forces all existing layers in the document to be flattened into a single image layer! Photographers have long requested a non-destructive HDR Toning adjustment layer.

Stock GIMP contains no integrated HDR Toning helper plugin. Creating native GIMP 3.x Python 3 plugin `python-fu-hdr-toning` achieves complete Photoshop parity with major workflow enhancements:
1. Tone Mapping Methods: Local Adaptation (Mantiuk 2006 tone mapping with contrast and detail scaling), Equalize Histogram (stretch contrast), Exposure & Gamma, Highlight Compression.
2. Edge Glow / Detail Microcontrast: Configurable Edge Glow Radius (1.0 to 100.0px) and Strength (0.0 to 5.0) via `gegl:unsharp-mask` producing the signature HDR halo and crisp structural acutance.
3. Exposure & Gamma Controls: Linear Exposure EV (-5.0 to +5.0 EV) and midtone Gamma curve (0.1 to 3.0 via `gimp-drawable-levels`).
4. Shadow & Highlight Recovery: Adaptive dynamic range compensation opening deep shadows and preventing highlight clipping.
5. Color Vibrance & Saturation: Dual-slider intelligent saturation control with full Monochrome HDR support (`saturation = -100.0`).
6. Curated Photographic Presets: Default Photorealistic, High Dynamic Vivid, Dramatic Monochrome, Architectural Crisp, Surreal Dreamy, Night Cityglow, Custom.
7. Flexible Layer Mask Modes: Reveal-All White Mask, Conceal-All Black Mask, Active Selection Mask.
8. 100% Non-Destructive Invariance: Duplicates target drawable into an isolated layer; base layer pixels underneath remain 100% mathematically untouched (`diff == 0.000000`).

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/hdr-toning/hdr-toning.py` (New plugin)
- `PhotoGIMP/scripts/verify_config.py` (Register `hdr-toning` in `REQUIRED_PLUGINS`, updating audit inventory to 37 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 38: `test_hdr_toning`, assertions HDR-01 through HDR-11)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add HDR Toning & Tone Mapping entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 43 status and schedule Phase 44)
- `.ralph/PROGRESS.md` (Log Iteration 45 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 45 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/hdr-toning/` created with `hdr-toning.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure `python-fu-hdr-toning` registered in GIMP PDB under:
   - `<Image>/Image/Adjustments/HDR Toning...`
   - `<Image>/Filters/Enhance/HDR Toning...`
   - `<Image>/Filters/Retouching`
   - `<Image>/Layer`
4. [x] Non-destructive adjustment layer created duplicating active drawable.
5. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 38):
   - Base layer pixels underneath remain 100% untouched (`diff == 0.000000`).
   - Default Photorealistic preset verified: dynamic range expansion and microcontrast boost.
   - High Dynamic Vivid preset verified: dramatic contrast and enriched saturation.
   - Dramatic Monochrome preset verified: exact neutral monochrome (`R == G == B`, spread `0.000000`).
   - Architectural Crisp preset verified: sharp edge glow and shadow detail lift.
   - Equalize Histogram method verified: histogram stretch across dynamic range.
   - Exposure & Gamma method verified: EV brightening and midtone power gamma shift.
   - Highlight Compression method verified: highlight peak compression and shadow lift.
   - Conceal-All black layer mask verified: composite equals base layer (`diff == 0.000000`).
   - Selection-aware mask verified: HDR toning confined strictly to active selection.
6. [x] `verify_config.py` Section 6 passes with all 37 required plugins audited.
7. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all stages cleanly with exit code 0 (365/365 tests passing).

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Expected Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement non-destructive hdr toning and tone mapping helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 45 - non-destructive hdr toning plugin`
