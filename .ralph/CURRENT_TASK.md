# Current Task — Iteration 83

## Task
**Phase 81 — Layer Matting & Edge Defringe Suite Helper Plugin (`layer-matting`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 225-227: "Fringe pixels around a selection", "Decrease the fringe on a selection", "Remove a matte from a selection"; `photoshop_docs.md` Section 229-231 lines 6459-6500: "Learn how fringe pixels affect selections and how to remove unwanted edges using photoeditor Matting for cleaner composites... Defringe: Replace fringe pixel colors with pixels farther inside the selection to create cleaner edges and smooth transitions... Remove Black Matte and Remove White Matte: Remove black or white matte edges from anti-aliased selections... Color Decontaminate: Replace background colors in fringe pixels with nearby thoroughly selected pixel colors..."):
1. **Defringe (`Layer > Matting > Defringe...`)**:
   - Replaces semi-transparent fringe edge pixels with interior pixel colors within a user-configurable pixel width (1 to 200 px).
   - Eliminates contrasting background color spill along anti-aliased object silhouettes.
2. **Remove Black Matte (`Layer > Matting > Remove Black Matte`)**:
   - Anti-aliased selections extracted from black or dark backgrounds blend background black into edge alpha: $C_{\text{fringe}} = \alpha C_{\text{true}} + (1 - \alpha) C_{\text{black}} = \alpha C_{\text{true}}$.
   - Mathematically recovers true unmixed foreground color: $C_{\text{restored}} = \text{clamp}(C_{\text{fringe}} / \alpha, 0.0, 1.0)$ for $\alpha > 0$.
   - Eliminates ugly dark/dirty halos around cutouts.
3. **Remove White Matte (`Layer > Matting > Remove White Matte`)**:
   - Anti-aliased selections extracted from white backgrounds blend white into edge alpha: $C_{\text{fringe}} = \alpha C_{\text{true}} + 1 - \alpha$.
   - Mathematically recovers true unmixed foreground color: $C_{\text{restored}} = \text{clamp}((C_{\text{fringe}} - (1 - \alpha)) / \alpha, 0.0, 1.0)$ for $\alpha > 0$.
   - Eliminates pale milky halos around cutout edges.
4. **Color Decontaminate (`Layer > Matting > Color Decontaminate...`)**:
   - Propagates interior core subject chrominance outward into semi-transparent boundary pixels ($0 < \alpha < 1.0$) while preserving the original alpha gradient.
   - Configurable radius (1 to 50 px) and amount percentage (0% to 100%).
5. **Non-Destructive vs In-Place Execution**:
   - In-place mode (`new_layer=False`) directly cleans fringe on the active layer.
   - Non-destructive mode (`new_layer=True`) creates dedicated layer `"<Layer Name> (Matted)"`, preserving original source layer and base canvas pixels 100% untouched (`diff == 0.000000`).
6. **Parasite Persistence (`photogimp/matting`)**:
   - Records matting operation and parameters in document parasite.
7. **Undo Group Encapsulation & Active Undo Stack Preservation**:
   - Wraps all operations in single-step undo groups with active undo stack maintained throughout.

Stock GIMP 3.x lacks a native `Layer > Matting` menu and provides no automated defringe, black matte removal, or white matte removal tools. Implementing `layer-matting` completes this essential compositing requirement.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/layer-matting/layer-matting.py` (New plugin implementing 4 PDB procedures: `python-fu-matting-defringe`, `python-fu-matting-remove-black-matte`, `python-fu-matting-remove-white-matte`, and `python-fu-matting-color-decontaminate`)
- `PhotoGIMP/scripts/verify_config.py` (Register `layer-matting` in `REQUIRED_PLUGINS`, updating audit inventory to 75 plugins)
- `PhotoGIMP/install.sh` (Batch deployment deploys all plug-ins to `~/.config/GIMP/3.2/plug-ins`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 76: `test_layer_matting`, assertions LM-01 through LM-16)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Layer Matting & Defringe entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 81 status)
- `.ralph/PROGRESS.md` (Log Iteration 83 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 83 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/layer-matting/` created with `layer-matting.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] 4 PDB procedures registered in GIMP PDB:
   - `python-fu-matting-defringe` under `<Image>/Layer/Matting/Defringe...`
   - `python-fu-matting-remove-black-matte` under `<Image>/Layer/Matting/Remove Black Matte`
   - `python-fu-matting-remove-white-matte` under `<Image>/Layer/Matting/Remove White Matte`
   - `python-fu-matting-color-decontaminate` under `<Image>/Layer/Matting/Color Decontaminate...`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 76):
   - LM-01: Procedure signatures and argument audit across all 4 procedures.
   - LM-02: Defringe execution replacing boundary fringe with interior core colors.
   - LM-03: Defringe width control (1 to 200 px) expanding replacement distance.
   - LM-04: Remove Black Matte execution: recovers true luminosity from dark fringe ($C / \alpha$).
   - LM-05: Remove Black Matte unmixing fidelity: dark fringe edge luminance boosted to true foreground level.
   - LM-06: Remove White Matte execution: unmixes white contamination ($[C - (1-\alpha)] / \alpha$).
   - LM-07: Remove White Matte unmixing fidelity: pale milky edge luminance restored to true vibrant level.
   - LM-08: Color Decontaminate execution: propagates interior core chrominance into edge alpha pixels.
   - LM-09: Color Decontaminate amount control: blends between original fringe and decontaminated color.
   - LM-10: Color Decontaminate radius control: limits propagation distance.
   - LM-11: Alpha channel preservation: original alpha geometry and transparency gradients preserved.
   - LM-12: In-place layer modification mode (`new_layer=False`).
   - LM-13: Non-destructive layer mode (`new_layer=True`): creates `"<Name> (Matted)"` preserving source layer.
   - LM-14: Parasite persistence and deserialization (`photogimp/matting`).
   - LM-15: Single-step undo group encapsulation and active undo stack maintenance.
   - LM-16: Target & base canvas artwork preservation outside layer bounds (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 75 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement layer matting and edge defringe suite plugin`
- Outer repository commit: `feat(ralph): complete iteration 83 - layer matting and edge defringe suite plugin`
