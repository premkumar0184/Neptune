# Current Task — Iteration 77

## Task
**Phase 75 — Artboards & Multi-Canvas Layout Manager Plugin (`artboards`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 146-149: "Get started with artboards", "Artboard properties and behaviors", "Create artboard documents", "Add artboards to the current document"; `photoshop_docs.md` Section 150-153 lines 4498-4595: "Learn about artboards in professional photoeditor, their structure, benefits, and customization for multi-screen design... Artboards are special layer groups that clip the contents of any contained elements to their boundaries... act as individual canvases within a document... Create new artboards from presets (Desktop, Mobile, Social, Print)... Artboard from Layers... Artboard from Group... Duplicate Artboard... Export Artboards to Files"):
1. **Artboard Containerization**:
   - Specialized Gimp `GroupLayer` (`"<Name> (Artboard)"`) acting as an isolated canvas within the document.
   - Non-destructive boundary clipping: layer mask attached to the group layer clipping all children to the artboard's exact rectangle (`[x, y, width, height]`).
   - Persistent metadata parasite `photogimp/artboard` storing `{ "name": name, "x": x, "y": y, "width": w, "height": h, "background": bg, "preset": preset }`.
   - Optional artboard background layer (White, Black, Transparent, Custom Color) pinned at the base of the artboard group.
2. **Creation & Conversion**:
   - `python-fu-create-artboard`: Creates new artboard with specified geometry or industry standard presets (Desktop 1080p, Mobile iPhone, Android, Tablet iPad, Social Instagram Square, Story, Print A4).
   - `python-fu-artboard-from-layers`: Wraps selected layers into a new artboard with calculated bounding box.
   - `python-fu-artboard-from-group`: Converts an existing layer group into an artboard container with boundary mask and metadata.
3. **Duplication & Spatial Layout**:
   - `python-fu-duplicate-artboard`: Clones an existing artboard with all nested content placed adjacent in specified direction (`right`, `left`, `below`, `above`) with customizable margin spacing.
   - `python-fu-resize-artboard`: Modifies artboard dimensions (width, height) and updates mask and background accordingly.
4. **Multi-Artboard Batch Export**:
   - `python-fu-export-artboards`: Iterates through all artboards in the document and exports each artboard cropped to its exact canvas bounds as standalone PNG or JPEG files.
5. **Canvas Artwork Integrity & Undo Protection**:
   - Target and base canvas artwork pixels remain 100% untouched (`diff == 0.000000`).
   - Single-step undo group encapsulation across all operations.

Stock GIMP has no native multi-canvas or Artboards support. Implementing `artboards` provides complete Photoshop parity on Linux.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/artboards/artboards.py` (New plugin implementing 6 PDB procedures: `python-fu-create-artboard`, `python-fu-artboard-from-layers`, `python-fu-artboard-from-group`, `python-fu-duplicate-artboard`, `python-fu-resize-artboard`, `python-fu-export-artboards`)
- `PhotoGIMP/scripts/verify_config.py` (Register `artboards` in `REQUIRED_PLUGINS`, updating audit inventory to 69 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 70: `test_artboards`, assertions AB-01 through AB-18)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Artboards & Multi-Canvas Layout entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 75 status)
- `.ralph/PROGRESS.md` (Log Iteration 77 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 77 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/artboards/` created with `artboards.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] 6 PDB procedures registered in GIMP PDB:
   - `python-fu-create-artboard` under `<Image>/Layer/Artboards/New Artboard...` and `<Image>/Tools/Transform Tools/Artboard`
   - `python-fu-artboard-from-layers` under `<Image>/Layer/Artboards/Artboard from Layers...`
   - `python-fu-artboard-from-group` under `<Image>/Layer/Artboards/Artboard from Group...`
   - `python-fu-duplicate-artboard` under `<Image>/Layer/Artboards/Duplicate Artboard...`
   - `python-fu-resize-artboard` under `<Image>/Layer/Artboards/Artboard Options...`
   - `python-fu-export-artboards` under `<Image>/File/Export/Export Artboards to Files...` and `<Image>/Layer/Artboards/Export Artboards...`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 70):
   - AB-01: Procedure signatures and argument audit across all 6 procedures.
   - AB-02: Create artboard container with specified geometry and persistent parasite (`photogimp/artboard`).
   - AB-03: Create artboard from device presets (Mobile iPhone, Desktop 1080p, Social Square).
   - AB-04: Boundary clipping: content inside artboard is strictly clipped to artboard boundary (inside 1.00, outside 0.00).
   - AB-05: Artboard background fill layer (white, black, transparent).
   - AB-06: Artboard from layers converting selected layers into an artboard container.
   - AB-07: Artboard from group converting existing layer group into artboard container.
   - AB-08: Duplicate artboard placing clone adjacent to existing artboard with spacing.
   - AB-09: Resize artboard geometry (updating width, height, boundary mask, and background).
   - AB-10: Multi-artboard coexistence (5 artboards side-by-side in same document).
   - AB-11: Content movement within artboard preserving boundary frame.
   - AB-12: Export artboards to files: exports individual PNG files cropped to exact artboard bounds.
   - AB-13: Export artboards to files: exports JPEG format.
   - AB-14: Export artboards dimensions verification on exported files.
   - AB-15: Unclipped layer coexistence (layers outside artboards remain unclipped).
   - AB-16: Undo group encapsulation for all artboard operations.
   - AB-17: Active undo stack maintained.
   - AB-18: Target & base canvas artwork preservation (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 69 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement artboards and multi-canvas layout manager plugin`
- Outer repository commit: `feat(ralph): complete iteration 77 - artboards and multi-canvas layout manager plugin`
