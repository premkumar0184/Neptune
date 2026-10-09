# Current Task — Iteration 71

## Task
**Phase 69 — Knockout Blending & Texture Cutout Effects Helper Plugin (`knockout-blending`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 120: "Create texture effects with Knockout"; `photoshop_docs.md` Section 124 lines 3684-3698: "Learn how to use the Knockout blending option to punch through layers and reveal underlying content for texture effects in photoeditor desktop", and Section 125 lines 3701-3730: "Set layer opacity and blending modes / Adjust fill opacity"):
1. **Knockout Blending**: Uses the active layer's silhouette shape to punch through intermediate layers underneath it, revealing underlying textures, images, or backgrounds:
   - **Shallow Knockout**: Punches through sibling layers inside the active layer's parent group down to the layer behind the group (or group backdrop).
   - **Deep Knockout**: Punches through all intermediate layers down to the base canvas/background layer.
2. **Fill Opacity Decoupling**: Adjusts the layer's own fill transparency (0% to 100%) independently from attached layer styles (strokes, bevels, drop shadows). At 0% fill opacity, the layer's fill color is invisible while its shape punches a hole through middle layers and its attached layer styles remain fully visible.
3. **Restoration / Clear Knockout**: Allows restoring intermediate layers and clearing knockout masks in one click.

Stock GIMP provides no built-in equivalent for Photoshop's Knockout blending options. Implementing `knockout-blending` brings complete Photoshop parity to Linux photo editing with `python-fu-knockout-blending` and `python-fu-clear-knockout`.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/knockout-blending/knockout-blending.py` (New plugin implementing `python-fu-knockout-blending` and `python-fu-clear-knockout`)
- `PhotoGIMP/scripts/verify_config.py` (Register `knockout-blending` in `REQUIRED_PLUGINS`, updating audit inventory to 63 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 64: `test_knockout_blending`, assertions KB-01 through KB-16)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Knockout Blending & Texture Cutout Effects Helper entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 69 status)
- `.ralph/PROGRESS.md` (Log Iteration 71 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 71 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/knockout-blending/` created with `knockout-blending.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] 2 PDB procedures registered in GIMP PDB:
   - `python-fu-knockout-blending` under `<Image>/Layer/Layer Style/Knockout Options...`, `<Image>/Layer/Blending Options/Knockout...`, and `<Image>/Filters/Retouching`
   - `python-fu-clear-knockout` under `<Image>/Layer/Layer Style/Clear Knockout`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 64):
   - KB-01: Procedure lookup and argument signatures verified across both procedures.
   - KB-02: Execution status verified (SUCCESS).
   - KB-03: Deep knockout punches transparency through all intermediate layers down to base canvas.
   - KB-04: Deep knockout reveals underlying base artwork through punched silhouette.
   - KB-05: Shallow knockout confines punch to layers inside parent group; leaves layers outside group untouched.
   - KB-06: Shallow knockout reveals group backdrop / under-group content.
   - KB-07: Fill Opacity decoupling: 0% fill opacity makes knockout shape fill transparent while punch remains active.
   - KB-08: Fill Opacity decoupling: partial fill opacity (e.g. 50%) blends knockout shape with underlying revealed content.
   - KB-09: Attached layer styles preservation: attached stroke / shadow layers remain visible while fill punches through.
   - KB-10: Feathering: edge feathering creates smooth anti-aliased cutout transitions.
   - KB-11: Inversion: invert toggle punches outside silhouette rather than inside.
   - KB-12: Curated presets: all 5 presets (`stencil-cutout`, `textured-text`, `soft-punch`, `glass-etched`, `translucent-knockout`) verified.
   - KB-13: Clear Knockout: restores punched intermediate layers cleanly.
   - KB-14: Graceful handling: single-layer / bottom-layer invocation handled gracefully as no-op SUCCESS.
   - KB-15: Single-step undo group encapsulation verified.
   - KB-16: Target and base layer artwork preserved with zero degradation (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 63 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement knockout blending and texture cutout effects helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 71 - knockout blending and texture cutout effects helper plugin`
