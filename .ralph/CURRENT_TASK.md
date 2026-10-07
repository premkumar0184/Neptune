# Current Task — Iteration 51

## Task
**Phase 49 — Guide Layout & Compositional Alignment Helper Plugin (`python-fu-guide-layout`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 493-502: "Use grids and measurement guides: Alignment grids and guides, Overview of guides, grids, and smart guides, Create guides, Move guides, Edit guides, Remove guides", and `photoshop_docs.md` Section 450-454 lines 13150-13290: "View > New Guide Layout: Create guides in columns, rows, or margins", "View > Guides > Clear Guides"), compositional alignment guides are fundamental to professional photography, retouching, typography, and graphic layout.

Stock GIMP provides only primitive single-guide insertion (`Image > Guides > New Guide (by Orientation)...`), requiring users to manually calculate pixel coordinates for every third, golden ratio, gutter, and margin. There is no automated dialog in GIMP to generate structured compositional guide layouts or multi-column grids.

Implementing native GIMP 3.x Python 3 plugin `python-fu-guide-layout` (and companion `python-fu-clear-guides`) provides full Photoshop parity:
1. **Curated Compositional Presets**:
   - *Rule of Thirds* (3x3 grid dividing canvas at 33.33% and 66.67% horizontally and vertically).
   - *Golden Ratio / Phi Grid* (dividing canvas by $\phi \approx 1.618$ at 38.2% and 61.8% for classical artistic balance).
   - *Center Crosshairs* (50% horizontal and vertical guides for central symmetry and quadrant alignment).
   - *Safe Margins Frame* (outer boundary frame at 5% or 10% margins).
   - *Web 12-Column Grid* (12 columns with 16px gutters and 5% margins for responsive layout).
   - *Print Editorial 3x2 Grid* (3 columns, 2 rows with 12px gutters and margins).
   - *Custom Grid Layout* (arbitrary columns, rows, gutters in pixels, margins in percentages).
2. **Clear Existing Guides Option**:
   - Checkbox to remove all prior canvas guides before generating new layout (matching Photoshop's "Clear Existing Guides").
3. **Companion Clear Guides Procedure**:
   - `python-fu-clear-guides` for instant 1-click removal of all canvas guides (`View > Guides > Clear Guides`).
4. **Registration**:
   - Registered under `<Image>/View/Guides/New Guide Layout...`, `<Image>/Image/Guides/New Guide Layout...`, `<Image>/View/New Guide Layout...`, `<Image>/View/Guides/Clear Guides`, and `<Image>/View/Clear Guides`.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/guide-layout/guide-layout.py` (New plugin implementing `python-fu-guide-layout` and `python-fu-clear-guides`)
- `PhotoGIMP/scripts/verify_config.py` (Register `guide-layout` in `REQUIRED_PLUGINS`, updating audit inventory to 43 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 44: `test_guide_layout`, assertions GL-01 through GL-12)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Guide Layout entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 49 status and schedule Phase 50)
- `.ralph/PROGRESS.md` (Log Iteration 51 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 51 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/guide-layout/` created with `guide-layout.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedures registered in GIMP PDB:
   - `python-fu-guide-layout` under `<Image>/View/Guides/New Guide Layout...`, `<Image>/Image/Guides`, `<Image>/View`
   - `python-fu-clear-guides` under `<Image>/View/Guides/Clear Guides`, `<Image>/View/Clear Guides`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 44):
   - GL-01: Procedure arguments verified (preset, clear-existing, columns, rows, col-gutter, row-gutter, margin-top, margin-bottom, margin-left, margin-right).
   - GL-02: Execution status verified (PDB status SUCCESS).
   - GL-03: Rule of Thirds preset verified on 300x300 image (exact horizontal guides at y=100, y=200; vertical guides at x=100, x=200).
   - GL-04: Golden Ratio / Phi Grid preset verified on 1000x1000 image (guides at 382px and 618px horizontally and vertically).
   - GL-05: Center Crosshairs preset verified on 400x600 image (guides at x=200, y=300).
   - GL-06: Safe Margins preset verified on 200x200 image (margins at 5% = 10px, 95% = 190px).
   - GL-07: Custom multi-column grid with gutters verified (12 columns with 16px gutters generating 24 vertical guides).
   - GL-08: Custom multi-row grid with gutters verified (3 rows with 20px gutters generating 4 horizontal guides).
   - GL-09: Clear Existing Guides option verified (wipes old guides before generating new layout).
   - GL-10: Standalone `python-fu-clear-guides` procedure verified (removes all guides to 0).
   - GL-11: Asymmetrical margins verified (Top=30px, Bottom=240px, Left=15px, Right=255px on 300x300 canvas).
   - GL-12: Zero layer modification verified (guide creation leaves layer pixels 100% untouched, diff == 0.000000).
5. [x] `verify_config.py` Section 6 passes with all 43 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0 (439/439 tests passing in 40.71s).

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement guide layout and compositional alignment helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 51 - guide layout plugin`
