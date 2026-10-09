# Current Task — Iteration 73

## Task
**Phase 71 — Layer Comps & Composition Variations Manager Plugin (`layer-comps`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 138-141: "Create layer compositions", "Create and manage layer comps"; `photoshop_docs.md` Section 145 lines 4175-4268: "Create and manage layer comps - Capture multiple design variations in a single file using snapshots of layer visibility, position, and appearance"):
1. **Layer Comp Snapshots & Properties**:
   - In Photoshop, a Layer Comp captures a snapshot of the document's layer stack at a specific moment.
   - It records three independent layer properties:
     - **Visibility**: Showing or hiding layers (`layer.get_visible()`, `layer.set_visible()`).
     - **Position**: Spatial layout coordinates / offsets (`layer.get_offsets()`, `layer.set_offsets()`).
     - **Appearance**: Layer opacity and blend mode (`layer.get_opacity()`, `layer.get_mode()`).
   - Designers use Layer Comps to explore and present design variations (e.g. desktop vs mobile layouts, colorways, seasonal themes) within a single document without creating separate files.
2. **Layer Comp Management**:
   - `Create Layer Comp`: Creates a named comp with optional comments and selectable property recording flags (`record_visibility`, `record_position`, `record_appearance`).
   - `Apply Layer Comp`: Restores the recorded layer properties for all layers captured in the comp.
   - `Cycle Layer Comps`: Next / Previous navigation controls to cycle quickly through all comps.
   - `Update Layer Comp`: Re-records the current document state into an existing comp.
   - `Delete Layer Comp`: Deletes a specific comp or clears all comps (`__ALL__`).
   - `Warning Resilience`: Gracefully handles deleted or renamed layers by applying properties to remaining layers and logging warnings, matching Photoshop warning indicator behavior.
3. **Export Layer Comps to Files**:
   - Matches Photoshop `File > Export > Layer Comps To Files`.
   - Iterates through comps, renders each comp variation, and exports to PNG or JPEG in a target folder with `{prefix}_{comp_name}.{ext}` naming.
   - Restores the document's original state and active comp after export.
4. **Artwork Integrity**:
   - Base canvas artwork pixels remain 100% untouched (`diff == 0.000000`).
   - Persistent storage in standard GIMP image parasite `photogimp/layer-comps`.

Stock GIMP provides no built-in equivalent for Photoshop's Layer Comps panel and workflow. Implementing `layer-comps` provides full Photoshop parity on Linux.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/layer-comps/layer-comps.py` (New plugin implementing 6 PDB procedures: `python-fu-create-layer-comp`, `python-fu-apply-layer-comp`, `python-fu-cycle-layer-comp`, `python-fu-update-layer-comp`, `python-fu-delete-layer-comp`, `python-fu-export-layer-comps`)
- `PhotoGIMP/scripts/verify_config.py` (Register `layer-comps` in `REQUIRED_PLUGINS`, updating audit inventory to 65 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 66: `test_layer_comps`, assertions LC-01 through LC-16)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Layer Comps & Composition Variations Manager entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 71 status)
- `.ralph/PROGRESS.md` (Log Iteration 73 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 73 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/layer-comps/` created with `layer-comps.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] 6 PDB procedures registered in GIMP PDB:
   - `python-fu-create-layer-comp` under `<Image>/Layer/Layer Comps` and `<Image>/Window/Layer Comps`
   - `python-fu-apply-layer-comp` under `<Image>/Layer/Layer Comps`
   - `python-fu-cycle-layer-comp` under `<Image>/Layer/Layer Comps`
   - `python-fu-update-layer-comp` under `<Image>/Layer/Layer Comps`
   - `python-fu-delete-layer-comp` under `<Image>/Layer/Layer Comps`
   - `python-fu-export-layer-comps` under `<Image>/File/Export` and `<Image>/Layer/Layer Comps`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 66):
   - LC-01: Procedure signatures and argument audit across all 6 procedures.
   - LC-02: Create Layer Comp execution and persistent parasite storage (`photogimp/layer-comps` metadata and active comp set).
   - LC-03: Layer Visibility snapshot & restoration across multiple comps.
   - LC-04: Layer Position / Offsets snapshot & restoration.
   - LC-05: Layer Appearance (Opacity & Blend Mode) snapshot & restoration.
   - LC-06: Selective property recording: Visibility only (position & appearance untouched).
   - LC-07: Selective property recording: Position only (visibility & appearance untouched).
   - LC-08: Selective property recording: Appearance only (visibility & position untouched).
   - LC-09: Update Layer Comp with new layer properties.
   - LC-10: Cycle Layer Comps (Next / Previous) navigation.
   - LC-11: Delete Layer Comp (single deletion and clear all comps).
   - LC-12: Missing layer resilience (graceful handling of deleted layers with warning logging).
   - LC-13: Export Layer Comps to Files in PNG format (`{prefix}_{comp_name}.png`).
   - LC-14: Export Layer Comps to Files in JPEG format (`{prefix}_{comp_name}.jpg`).
   - LC-15: Export restores original document state and active comp.
   - LC-16: Target & base canvas artwork preservation verification (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 65 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement layer comps and composition variations manager plugin`
- Outer repository commit: `feat(ralph): complete iteration 73 - layer comps and composition variations manager plugin`
