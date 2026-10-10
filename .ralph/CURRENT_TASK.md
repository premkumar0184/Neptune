# Current Task — Iteration 76

## Task
**Phase 74 — Image Stacks Statistical Blending Helper Plugin (`image-stacks`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` line 145: "Create and process image stacks"; `photoshop_docs.md` Section 149 lines 4440-4495: "Create and process image stacks... combine multiple images with similar framing into a Smart Object... apply stack modes processing options that analyze corresponding pixels across all layers to create a composite that eliminates noise, distortion, or unwanted objects... Mean for noise reduction or Median for object removal... File > Scripts > Statistics... File > Scripts > Load Files into Stack... Edit > Auto-Align Layers... Layer > Smart Objects > Stack Mode... Layer > Smart Objects > Rasterize"):
1. **Image Stack Containerization**:
   - Encapsulates source layers into a specialized Smart Object group layer (`"<Stack Name> (Image Stack)"`) with persistent metadata parasite (`photogimp/image-stack`).
   - Keeps source layers preserved non-destructively in a `"[Stack Sources]"` sub-group.
   - Maintains an active rendered composite layer (`"[Rendered Composite - <Mode>]"`) tagged with parasite (`photogimp/stack-composite`).
2. **Statistical Stack Modes**:
   - `mean`: Average pixel values across all layers -> noise reduction (improves SNR by $\sqrt{N}$).
   - `median`: Median pixel value across all layers -> moving object removal (removes tourists, vehicles, transients).
   - `maximum`: Lightest pixel values -> star trails, fireworks, light streaks.
   - `minimum`: Darkest pixel values -> shadow accumulation, dark composite.
   - `range`: Peak-to-peak difference (Max - Min) -> motion detection / difference map.
   - `stddev`: Standard deviation across layers -> noise / variability analysis.
   - `variance`: Variance across layers.
   - `sum`: Accumulated exposures (clipped to [0, 1]) -> long exposure simulation / astrophotography.
   - `entropy`: Information entropy of pixel distribution.
   - `skewness`: Asymmetry distribution metric.
   - `kurtosis`: Distribution peakedness metric.
   - `none`: Disables composite rendering, revealing top source layer (matching Photoshop behavior).
3. **Load Files into Stack (`python-fu-load-files-into-stack`)**:
   - Loads multiple image files from disk into separate layers of an image, optionally auto-aligning and converting to an image stack.
4. **Statistics Script (`python-fu-statistics-stack`)**:
   - Single-operation automated workflow mirroring Photoshop `File > Scripts > Statistics`: loads images from file list, aligns them, wraps them into a stack, and renders composite.
5. **Auto-Align Stack Layers (`python-fu-auto-align-stack`)**:
   - Automated registration of stack layers against reference layer minimizing pixel difference via phase correlation.
6. **Set Stack Mode & Dynamic Re-rendering (`python-fu-set-stack-mode`, `python-fu-render-image-stack`)**:
   - Non-destructive dynamic switching between statistical modes on existing stack containers without losing source layers.
7. **Rasterize Stack (`python-fu-rasterize-image-stack`)**:
   - Permanently bakes composite layer to regular raster layer, cleaning up container group (Photoshop `Layer > Smart Objects > Rasterize`).
8. **Canvas Artwork Integrity & Undo Protection**:
   - Target and base canvas artwork pixels remain 100% untouched (`diff == 0.000000`).
   - Single-step undo group encapsulation across all operations.

Stock GIMP provides no built-in equivalent for Photoshop's Image Stacks, Smart Object Stack Modes, or the Statistics script. Implementing `image-stacks` provides full Photoshop parity on Linux.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/image-stacks/image-stacks.py` (New plugin implementing 7 PDB procedures: `python-fu-create-image-stack`, `python-fu-set-stack-mode`, `python-fu-render-image-stack`, `python-fu-load-files-into-stack`, `python-fu-statistics-stack`, `python-fu-auto-align-stack`, `python-fu-rasterize-image-stack`)
- `PhotoGIMP/scripts/verify_config.py` (Register `image-stacks` in `REQUIRED_PLUGINS`, updating audit inventory to 68 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 69: `test_image_stacks`, assertions IS-01 through IS-18)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Image Stacks Statistical Blending entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 74 status)
- `.ralph/PROGRESS.md` (Log Iteration 76 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 76 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/image-stacks/` created with `image-stacks.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] 7 PDB procedures registered in GIMP PDB:
   - `python-fu-create-image-stack` under `<Image>/Layer/Smart Objects/Image Stack` and `<Image>/Layer/Image Stacks`
   - `python-fu-set-stack-mode` under `<Image>/Layer/Smart Objects/Stack Mode` and `<Image>/Layer/Image Stacks`
   - `python-fu-render-image-stack` under `<Image>/Layer/Image Stacks`
   - `python-fu-load-files-into-stack` under `<Image>/File/Scripts/Load Files into Stack` and `<Image>/Layer/Image Stacks`
   - `python-fu-statistics-stack` under `<Image>/File/Scripts/Statistics` and `<Image>/Layer/Image Stacks`
   - `python-fu-auto-align-stack` under `<Image>/Edit/Auto-Align Layers` and `<Image>/Layer/Image Stacks`
   - `python-fu-rasterize-image-stack` under `<Image>/Layer/Smart Objects/Rasterize Stack` and `<Image>/Layer/Image Stacks`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 69):
   - IS-01: Procedure signatures and argument audit across all 7 procedures.
   - IS-02: Create image stack container from layers with persistent parasite (`photogimp/image-stack`).
   - IS-03: Render stack with 'mean' mode (noise reduction math verified across layers).
   - IS-04: Render stack with 'median' mode (transient object / impulse removal verified).
   - IS-05: Render stack with 'maximum' mode (lightest pixel composite / star trails).
   - IS-06: Render stack with 'minimum' mode (darkest pixel composite).
   - IS-07: Render stack with 'range' mode (max - min difference math verified).
   - IS-08: Render stack with 'stddev' mode (standard deviation math verified).
   - IS-09: Render stack with 'sum' mode (exposure accumulation verified).
   - IS-10: Render stack with 'variance' mode (variance math verified).
   - IS-11: Render stack with 'none' mode (composite layer disabled, reveals top source layer).
   - IS-12: Dynamic stack mode switching ('mean' -> 'median' -> 'maximum') preserving source layers.
   - IS-13: Auto-align stack layers registering translated layers against reference layer.
   - IS-14: Load files into stack importing multiple image files into separate layers.
   - IS-15: One-shot Statistics pipeline executing load, align, stack, and render in single step.
   - IS-16: Rasterize stack converting stack Smart Object into standard raster layer.
   - IS-17: Single-step undo group encapsulation across operations.
   - IS-18: Target & base canvas artwork preservation (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 68 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement image stacks statistical blending helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 76 - image stacks statistical blending helper plugin`
