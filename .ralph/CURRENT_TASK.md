# Current Task — Iteration 50

## Task
**Phase 48 — Non-Destructive Texturizer & Surface Canvas Helper Plugin (`python-fu-texturizer`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 481: "Apply texture and surface effects to filters" and `photoshop_docs.md` Section 442 lines 12911-12930: "Filter > Texture > Texturizer / Filter Gallery: Canvas, Burlap, Brick, Sandstone with Scaling, Relief, Light Direction, and Invert"), the Texturizer filter is one of Photoshop's signature artistic and physical surface simulation tools. It gives digital paintings and photographs the physical, tactile look of being painted or printed on textured materials such as woven canvas, coarse burlap, architectural brick masonry, sandstone, or cold-press paper.

Stock GIMP provides no non-destructive Texturizer filter or adjustment layer helper with native Photoshop texture presets (Canvas, Burlap, Brick, Sandstone) and directional relief lighting. Users must manually construct complex heightmaps, run GEGL bump-map filters, set layer blend modes, and construct masks manually.

Implementing native GIMP 3.x Python 3 plugin `python-fu-texturizer` brings full Photoshop parity to Linux photo editing:
- Mathematical heightmap generation for classic tactile surfaces:
  1. **Canvas**: Fine orthogonal warp-and-weft woven fabric grid with alternating thread undulating peaks.
  2. **Burlap**: Coarse rustic jute weave with wider spacing, deeper inter-thread crevices, and fibrous variation.
  3. **Brick**: Staggered horizontal masonry courses with mortared bed joints and alternating vertical head joints.
  4. **Sandstone**: Granular porous stone relief with stochastic micro-pits and mineral roughness.
  5. **Paper**: Subtle organic cold-press watercolor paper grain.
- Physical directional surface lighting:
  - 8 directional lighting angles: Top ($\theta=90^\circ$), Top-Left ($135^\circ$), Left ($180^\circ$), Bottom-Left ($225^\circ$), Bottom ($270^\circ$), Bottom-Right ($315^\circ$), Right ($0^\circ$), Top-Right ($45^\circ$).
  - Surface gradient $\nabla H = (\frac{\partial H}{\partial x}, \frac{\partial H}{\partial y})$ dot-product directional illumination: $\Delta = \text{Relief} \cdot (\vec{L} \cdot \nabla H)$.
- Invert Texture toggle: Inverts ridges and valleys (reversing highlights and shadows).
- Scaling control: 50% to 200% texture scale magnification.
- Relief control: 1 to 50 depth intensity.
- Curated presets:
  - *Fine Art Canvas* (Canvas, Scaling 100%, Relief 10, Top-Left light, Soft Light 85%)
  - *Rustic Burlap Weave* (Burlap, Scaling 120%, Relief 18, Top-Left light, Overlay 90%)
  - *Weathered Brickwork* (Brick, Scaling 100%, Relief 25, Top-Left light, Soft Light 90%)
  - *Sandstone Block Relief* (Sandstone, Scaling 100%, Relief 15, Top light, Soft Light 80%)
  - *Watercolor Paper Grain* (Paper, Scaling 80%, Relief 6, Top-Left light, Soft Light 65%)
  - *Custom* (Full manual control)
- Non-destructive neutral gray (128) emboss layer in Soft Light / Overlay mode: Base image colors and hues remain 100% untouched underneath (`diff == 0.000000`), with an editable layer mask attached.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/texturizer/texturizer.py` (New plugin)
- `PhotoGIMP/scripts/verify_config.py` (Register `texturizer` in `REQUIRED_PLUGINS`, updating audit inventory to 42 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 43: `test_texturizer`, assertions TX-01 through TX-11)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Texturizer entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 48 status and schedule Phase 49)
- `.ralph/PROGRESS.md` (Log Iteration 50 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 50 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/texturizer/` created with `texturizer.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedure `python-fu-texturizer` registered in GIMP PDB under:
   - `<Image>/Filters/Artistic/Texturizer...`
   - `<Image>/Filters/Texture/Texturizer...`
   - `<Image>/Filters/Retouching`
   - `<Image>/Layer`
4. [x] Non-destructive adjustment layer created duplicating active drawable with textured emboss applied in Soft Light/Overlay mode.
5. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 43):
   - TX-01: Procedure arguments verified (preset, texture, scaling, relief, light-dir, invert, blend-mode, mask-mode, opacity).
   - TX-02: Execution status verified (PDB status SUCCESS).
   - TX-03: Layer mode, name & mask verified (`Texturizer (Fine Art Canvas)` with SOFTLIGHT mode and mask attached).
   - TX-04: Fine Art Canvas weave texture variance verified (surface relief variance 0.014020 > 0.001).
   - TX-05: Relief depth scaling verified (relief 25 variance 0.06346 > relief 5 variance 0.00288).
   - TX-06: Directional lighting angle response verified (Top-Left vs Bottom-Right phase reversal).
   - TX-07: Invert texture toggle verified (reverses highlights and shadows).
   - TX-08: Weathered Brickwork preset verified (staggered masonry courses pattern rendered, variance 0.00480 > 0.0003).
   - TX-09: Rustic Burlap Weave preset verified (coarse weave rendered with high relief in OVERLAY mode, variance 0.02269 > 0.001).
   - TX-10: Conceal-All black layer mask verified (composite diff == 0.000000).
   - TX-11: Selection confinement & non-destructive preservation verified (effect confined to selection [in=1.00, out=0.00], base layer 100% untouched diff == 0.000000).
6. [x] `verify_config.py` Section 6 passes with all 42 required plugins audited.
7. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0 (425/425 tests passing in 38.56s).

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement non-destructive texturizer and surface canvas helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 50 - non-destructive texturizer plugin`
