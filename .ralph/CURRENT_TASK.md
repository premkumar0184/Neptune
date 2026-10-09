# Current Task — Iteration 75

## Task
**Phase 73 — Placeholder Frames & Clipping Masks Layout Helper Plugin (`placeholder-frames`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 150-155: "Draw frames", "Convert shapes or text to frames", "Place an image into a frame", "Select a frame and its content", "Add a stroke to a frame", "Apply patterns to template images"; `photoshop_docs.md` Section 154-158 lines 4600-4735: "Draw empty frames: In photoeditor, the Frame tool lets you create shapes that automatically mask and resize images placed inside them... rectangular, elliptical... Convert shapes or text layers into frames... Place an image into a frame... image becomes a Smart Object... images automatically resize to fit frame boundaries... Add a stroke to a frame: Size, Position [Inside, Center, Outside], Color"):
1. **Placeholder Frame Creation & Conversion**:
   - `Create Frame`: Creates rectangular or elliptical placeholder frames at specified coordinates or from active selection.
   - `Convert to Frame`: Converts existing shape, text, or graphic layer into a frame placeholder.
   - Frame is encapsulated as a specialized `GroupLayer` (`"<Name> (Frame)"`) with persistent metadata parasite (`photogimp/frame-container`) and a high-precision boundary mask.
2. **Placing & Auto-Fitting Content**:
   - `Place Image into Frame`: Inserts image (from file path or active layer) into frame container with automatic aspect-ratio fitting:
     - `Fill` (Cover): Scales content proportionally to fully cover frame area, clipping overhang.
     - `Fit` (Contain): Scales content proportionally to fit entirely inside frame, preserving full content.
     - `Stretch`: Non-uniform scaling to exact frame width and height.
     - `Original`: 100% scale centered in frame.
   - All content is clipped non-destructively by the frame mask.
3. **Frame Stroke & Border Styling**:
   - `Set Frame Stroke`: Adds or updates a styled border stroke around the frame: width (1-100px), position (`inside`, `center`, `outside`), custom RGB color, and opacity.
4. **Frame & Content Adjustment**:
   - `Adjust Frame Content`: Repositions (pan dx, dy) or rescales content inside the frame while keeping frame boundary and clipping fixed.
   - `Release Frame`: Unpacks content from frame container back into standard root-level layers.
5. **Canvas Artwork Integrity**:
   - Base canvas artwork pixels remain 100% untouched (`diff == 0.000000`).
   - Single-step undo group encapsulation across all operations.

Stock GIMP provides no built-in equivalent for Photoshop's Frame Tool, placeholder frames, automatic aspect-ratio fitting, or frame stroke integration. Implementing `placeholder-frames` provides full Photoshop parity on Linux.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/placeholder-frames/placeholder-frames.py` (New plugin implementing 6 PDB procedures: `python-fu-create-frame`, `python-fu-convert-to-frame`, `python-fu-place-image-in-frame`, `python-fu-set-frame-stroke`, `python-fu-adjust-frame-content`, `python-fu-release-frame`)
- `PhotoGIMP/scripts/verify_config.py` (Register `placeholder-frames` in `REQUIRED_PLUGINS`, updating audit inventory to 67 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 68: `test_placeholder_frames`, assertions PF-01 through PF-16)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Placeholder Frames & Clipping Masks Layout Helper entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 73 status)
- `.ralph/PROGRESS.md` (Log Iteration 75 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 75 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/placeholder-frames/` created with `placeholder-frames.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] 6 PDB procedures registered in GIMP PDB:
   - `python-fu-create-frame` under `<Image>/Layer/Frames` and `<Image>/Tools/Transform Tools/Frame`
   - `python-fu-convert-to-frame` under `<Image>/Layer/Frames`
   - `python-fu-place-image-in-frame` under `<Image>/Layer/Frames` and `<Image>/File/Place`
   - `python-fu-set-frame-stroke` under `<Image>/Layer/Frames` and `<Image>/Layer/Layer Style`
   - `python-fu-adjust-frame-content` under `<Image>/Layer/Frames`
   - `python-fu-release-frame` under `<Image>/Layer/Frames`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 68):
   - PF-01: Procedure signatures and argument audit across all 6 procedures.
   - PF-02: Create rectangular frame with specified geometry and persistent parasite (`photogimp/frame-container`).
   - PF-03: Create elliptical frame with oval mask geometry.
   - PF-04: Convert existing layer / shape / selection into frame placeholder.
   - PF-05: Place image into frame with 'fill' (cover) auto-fitting and aspect ratio preservation.
   - PF-06: Place image into frame with 'fit' (contain) auto-fitting.
   - PF-07: Place image into frame with 'stretch' auto-fitting.
   - PF-08: Clipping mask confinement: content outside frame boundary is strictly clipped (alpha 0.000).
   - PF-09: Frame stroke addition (inside position, custom RGB color).
   - PF-10: Frame stroke addition (outside position).
   - PF-11: Frame stroke addition (center position).
   - PF-12: Adjust frame content: pan offset dx, dy inside frame while keeping mask fixed.
   - PF-13: Adjust frame content: content scale factor update.
   - PF-14: Release frame: content unpacked to standard layer and frame container cleaned up.
   - PF-15: Undo group encapsulation for frame operations.
   - PF-16: Target & base canvas artwork preservation (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 67 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement placeholder frames and clipping masks layout helper plugin`
- Outer repository commit: `feat(ralph): complete iteration 75 - placeholder frames and clipping masks layout helper plugin`

