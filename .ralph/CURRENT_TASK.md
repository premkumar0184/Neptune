# Current Task — Iteration 82

## Task
**Phase 80 — Delete and Fill Selection Helper Plugin (`delete-fill-selection`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 195: "Remove objects with Delete and Fill Selection"; `photoshop_docs.md` Section 199 lines 5841-5852: "Learn how to remove unwanted objects from your image using the Delete and Fill Selection tool... Control+click or right-click the selected object. Then, select Delete and Fill Selection. photoeditor will automatically remove the selected object and fill the area with content that matches the surrounding image"):
1. **Delete and Fill Selection (`Shift+Backspace` / Right-click on selection)**:
   - Removes selected unwanted objects/elements with a single click or shortcut.
   - Synthesizes replacement background texture, colors, and tonal gradients sampled from surrounding unselected pixels (Content-Aware Inpainting).
   - Automatically deselects upon completion for an instant clean viewing experience.
2. **Advanced Inpainting & Infill Architecture**:
   - Boundary dilation/expansion (default 2px) to eliminate object edge halos and fringing.
   - Smooth harmonic Poisson/Laplace diffusion solving $\nabla^2 I = 0$ with boundary Dirichlet conditions to match ambient lighting gradients.
   - Texture synthesis & grain preservation from surrounding sampling radius to avoid artificial flat blurring.
   - Edge feathering (default 2px) for seamless alpha blending into the surrounding canvas.
3. **Delete and Fill Options Dialog (`python-fu-delete-fill-options`)**:
   - Allows fine-tuning sampling margin/radius, edge feathering, selection expansion, inpainting method, and non-destructive output mode.
4. **Non-Destructive vs In-Place Execution**:
   - In-place mode (`new_layer=False`) seamlessly patches active layer in a single undo step.
   - Non-destructive mode (`new_layer=True`) writes inpainted result to `"<Layer Name> (Object Removed)"`, preserving original source layer and base canvas pixels 100% untouched (`diff == 0.000000`).
5. **Parasite Persistence (`photogimp/delete-fill`)**:
   - Records metadata, bounding box coordinates, and fill parameters in document parasite.
6. **Undo Group Encapsulation & Active Undo Stack Preservation**:
   - Encapsulates entire multi-stage inpainting pipeline in single-step undo groups with active undo stack maintenance.

Stock GIMP 3.x only provides standard Clear (`Delete` key, leaving transparent holes or solid background color) and lacks a native one-click Content-Aware Delete and Fill Selection tool. Implementing `delete-fill-selection` fulfills this essential Photoshop workflow.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/delete-fill-selection/delete-fill-selection.py` (New plugin implementing 2 PDB procedures: `python-fu-delete-fill-selection` and `python-fu-delete-fill-options`)
- `PhotoGIMP/.config/GIMP/3.0/shortcutsrc` (Map `<Shift>BackSpace` to `python-fu-delete-fill-selection`)
- `PhotoGIMP/scripts/verify_config.py` (Register `delete-fill-selection` in `REQUIRED_PLUGINS`, updating audit inventory to 74 plugins)
- `PhotoGIMP/install.sh` (Batch deployment deploys all plug-ins to `~/.config/GIMP/3.2/plug-ins`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 75: `test_delete_fill_selection`, assertions DFS-01 through DFS-16)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Delete and Fill Selection entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 80 status)
- `.ralph/PROGRESS.md` (Log Iteration 82 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 82 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/delete-fill-selection/` created with `delete-fill-selection.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] 2 PDB procedures registered in GIMP PDB:
   - `python-fu-delete-fill-selection` under `<Image>/Edit/Delete and Fill Selection`, `<Image>/Select/Delete and Fill Selection`, and `<Image>/Layer/Delete and Fill Selection`
   - `python-fu-delete-fill-options` under `<Image>/Edit/Delete and Fill Options...` and `<Image>/Select/Delete and Fill Options...`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 75):
   - DFS-01: Procedure signatures and argument audit across both procedures.
   - DFS-02: One-click Delete and Fill Selection execution on active rectangular selection.
   - DFS-03: Complete object removal: selected red object replaced with ambient background color.
   - DFS-04: Seamless harmonic gradient continuation: luminance smoothly interpolated across filled region.
   - DFS-05: Boundary dilation / expansion: eliminates edge halos and perimeter artifacts.
   - DFS-06: Edge feathering radius control: smooth alpha transition at boundaries.
   - DFS-07: Sampling radius configuration: samples source textures within specified margin.
   - DFS-08: Automatic deselection post-fill: selection cleared upon completion for instant clean view.
   - DFS-09: Arbitrary polygon / elliptical selection support.
   - DFS-10: In-place layer modification mode (`new_layer=False`).
   - DFS-11: Non-destructive layer mode (`new_layer=True`): creates `"<Name> (Object Removed)"` preserving source layer.
   - DFS-12: Empty selection safety: returns clean execution status without crashing when selection is empty.
   - DFS-13: Parasite persistence and deserialization (`photogimp/delete-fill`).
   - DFS-14: Undo group encapsulation: single-step undo group across entire inpainting pipeline.
   - DFS-15: Active undo stack maintained throughout execution.
   - DFS-16: Target & base canvas artwork preservation outside selection bounds (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 74 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement delete and fill selection helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 82 - delete and fill selection helper plugin`
