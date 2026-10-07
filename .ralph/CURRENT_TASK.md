# Current Task — Iteration 49

## Task
**Phase 47 — Non-Destructive Lens Blur & Optical Depth of Field Helper Plugin (`python-fu-lens-blur`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 461: "Create depth of field with lens blur", line 465: "Use Blur Gallery depth-of-field effects", and `photoshop_docs.md` Section 425 lines 12355-12377: "Filter > Blur > Lens Blur: Customize settings in the Lens Blur dialog box: Depth Map Source [None, Transparency, Layer Mask], Blur Focal Distance, Iris [Radius to control blur strength, Blade Curvature], Specular Highlights [Increase Brightness to enhance highlights, Threshold to define bright areas], and Noise [Distribution Uniform or Gaussian, Monochromatic]"), Lens Blur is one of Photoshop's premier optical simulation filters. It simulates the physical characteristics of camera lens diaphragms, rendering circular/polygonal optical bokeh discs and bloom around specular highlights rather than simple Gaussian blurring.

Stock GIMP provides no built-in `Lens Blur` dialog or depth-of-field adjustment layer helper. Users must manually construct complex channel depth maps, run GEGL operations with manual parameters, and construct masks. Implementing native GIMP 3.x Python 3 plugin `python-fu-lens-blur` brings full Photoshop parity to Linux photo editing:
- Optical aperture defocus simulation via `gegl:lens-blur` (Iris radius, highlight boost factor, and specular threshold).
- Specular highlights blooming: bright highlights expand into luminous bokeh circles without burning out midtones.
- Depth Map simulation modes: Radial Gradient (portrait shallow DOF with sharp focal center), Linear Depth Gradient (planar street/landscape depth), Uniform Defocus, and Active Selection.
- Monochromatic film grain / sensor texture integration (`noise-amount` via `gegl:noise-rgb` correlated/independent=False).
- Curated photographic presets (Portrait Fast Prime f/1.4, Street Shallow DOF f/2.0, Macro Extreme Bokeh f/1.2, Dreamy Specular Bokeh, Uniform Defocus, Custom).
- Layer mask modes (Depth Map Mask, Conceal All, Reveal All, Selection).
- 100% Non-destructive invariance: Base layer pixels underneath remain 100% mathematically untouched (`diff == 0.000000`).

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/lens-blur/lens-blur.py` (New plugin)
- `PhotoGIMP/scripts/verify_config.py` (Register `lens-blur` in `REQUIRED_PLUGINS`, updating audit inventory to 41 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 42: `test_lens_blur`, assertions LB-01 through LB-11)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Lens Blur entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 47 status and schedule Phase 48)
- `.ralph/PROGRESS.md` (Log Iteration 49 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 49 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/lens-blur/` created with `lens-blur.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure `python-fu-lens-blur` registered in GIMP PDB under:
   - `<Image>/Filters/Blur/Lens Blur...`
   - `<Image>/Filters/Blur Gallery/Lens Blur...`
   - `<Image>/Filters/Retouching`
   - `<Image>/Layer`
4. [x] Non-destructive adjustment layer created duplicating active drawable with optical lens blur applied.
5. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 42):
   - LB-01: Procedure arguments verified (preset, radius, highlight-factor, highlight-threshold, depth-source, focal-distance, invert-depth, noise-amount, mask-mode, opacity).
   - LB-02: Execution status verified (PDB status SUCCESS).
   - LB-03: Layer mode, name & mask verified (`Lens Blur (Portrait Fast Prime f/1.4)` with NORMAL mode and mask attached).
   - LB-04: Aperture Bokeh Disc Formation verified (highlight point expanded into circular bokeh disc: disc area luminance 0.301 > 0.125).
   - LB-05: Specular Highlight Boost verified (highlight factor amplifies specular luminance: 0.880 > 0.136).
   - LB-06: Portrait Fast Prime f/1.4 preset verified (radial falloff preserves focal center sharp with background defocus: mask 0.00 at center, mask 1.00 at outer).
   - LB-07: Street Photography Shallow DOF preset verified (linear depth gradient verified: foreground mask 0.00, background mask 0.73).
   - LB-08: Dreamy Specular Bokeh preset verified (reveal-all bokeh highlights: mask 1.00).
   - LB-09: Monochromatic film grain noise verified (sensor texture added: variance 0.007453 > 0.0003, monochromatic RGB correlation verified).
   - LB-10: Conceal-All black layer mask verified (composite diff == 0.000000).
   - LB-11: Selection confinement & non-destructive preservation verified (effect confined to selection, base layer 100% untouched diff == 0.000000).
6. [x] `verify_config.py` Section 6 passes with all 41 required plugins audited.
7. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0 (413/413 tests passing in 37.99s).

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `42ba0f5` (`feat(plugins): implement non-destructive lens blur and optical depth of field helper plugin`)
- Outer repository commit: `feat(ralph): complete iteration 49 - non-destructive lens blur plugin`
