# Current Task — Iteration 52

## Task
**Phase 50 — Frame Animation & Tweening Helper Plugin (`python-fu-frame-animation-setup`, `python-fu-create-tween`, `python-fu-pingpong-animation`, `python-fu-remove-animation-tags`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 512-523: "Create animation frames, Edit animation frames, Unify layer properties in animation frames, Copy frames with layer properties, Create frames using tweening, Manage layer visibility in animation frames, Specify a delay time in frame animations, Choose a frame disposal method, Specify looping in frame animations, Delete animations", and `photoshop_docs.md` Section 472-477 lines 13880-14010: "Window > Timeline: Create Frame Animation", "Create frames using tweening", "Specify a delay time in frame animations", "Choose a frame disposal method", "Specify looping in frame animations", "Delete animations"), timeline and frame animation controls are vital for creating web banners, UI animations, animated GIFs, sprite sheets, and cinematic motion graphics.

Stock GIMP's animation model uses layers as frames (from bottom to top) and parses animation metadata from layer name suffixes (e.g. `Layer (100ms) (replace)`). However, stock GIMP provides NO workflow dialogs to:
1. Batch set/update frame delay (in ms or standard FPS rates: 10, 12, 24, 30 fps) across layers without tedious manual layer renaming.
2. Batch configure frame disposal methods (`(replace)` for Photoshop Dispose vs `(combine)` for Photoshop Do Not Dispose).
3. Automatically generate smooth crossfade intermediate frames via **Tweening** between keyframes.
4. Automatically generate seamless **Ping-Pong bounce loops** by reversing intermediate frames.
5. Cleanly strip animation tags from layer names to return documents to static artwork.

Implementing native GIMP 3.x Python 3 plugin `frame-animation` provides complete Photoshop parity:
1. `python-fu-frame-animation-setup`:
   - Configures uniform frame timing with standard FPS presets (10 fps [100ms], 12 fps [83ms], 24 fps [42ms], 30 fps [33ms], 20 fps [50ms], 5 fps [200ms], 2 fps [500ms], or custom ms).
   - Configures frame disposal method (`replace`, `combine`, or preserve).
   - Allows targeting all layers or active layer only.
   - Allows reversing playback order.
2. `python-fu-create-tween`:
   - Interpolates intermediate frames between keyframes with mathematically linear opacity crossfading.
   - Allows tweening consecutive pairs across the entire stack or active pair only.
   - Configures number of tween frames to insert ($N=1\dots 50$), delay tag, and disposal mode.
   - Inserts generated composite tween layers at exact stack positions between keyframes.
3. `python-fu-pingpong-animation`:
   - Duplicates layers in reverse order (excluding turnaround endpoints) to produce seamless infinite loop playback without jump cuts.
4. `python-fu-remove-animation-tags`:
   - Cleans all `(\d+ms)` and `(combine|replace)` tags from layer names.
5. Menu Integration:
   - Registered under `<Image>/Filters/Animation/` and `<Image>/Image/Animation/`.
6. Undo Grouping:
   - Full 1-step `Ctrl+Z` undo protection for all batch operations.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/frame-animation/frame-animation.py` (New plugin implementing all 4 animation procedures)
- `PhotoGIMP/scripts/verify_config.py` (Register `frame-animation` in `REQUIRED_PLUGINS`, updating audit inventory to 44 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 45: `test_frame_animation`, assertions FA-01 through FA-14)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add Frame Animation & Tweening Helper entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 50 status)
- `.ralph/PROGRESS.md` (Log Iteration 52 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 52 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/frame-animation/` created with `frame-animation.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] PDB procedures registered in GIMP PDB:
   - `python-fu-frame-animation-setup` under `<Image>/Filters/Animation/Frame Animation Setup...`, `<Image>/Image/Animation`
   - `python-fu-create-tween` under `<Image>/Filters/Animation/Create Tween Frames...`, `<Image>/Image/Animation`
   - `python-fu-pingpong-animation` under `<Image>/Filters/Animation/Ping-Pong Loop...`, `<Image>/Image/Animation`
   - `python-fu-remove-animation-tags` under `<Image>/Filters/Animation/Remove Animation Tags`, `<Image>/Image/Animation`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 45):
   - FA-01: Procedure arguments verified across all 4 procedures.
   - FA-02: Execution status verified (PDB status SUCCESS).
   - FA-03: Frame Animation Setup 24 fps preset verified (`(42ms)` tag attached to all layers).
   - FA-04: Frame Animation Setup disposal method verified (`(replace)` tag attached to all layers).
   - FA-05: Frame Animation Setup `(combine)` mode verified (`(combine)` tag attached).
   - FA-06: Custom frame delay verified (e.g. `(175ms)` custom duration).
   - FA-07: Reverse layer order verified (inverts playback stack).
   - FA-08: Selected-layer-only targeting verified (only active layer tagged with 33ms, others untouched).
   - FA-09: Single-pair crossfade tweening verified (3 intermediate frames generated between Black and White layers, total 5 layers).
   - FA-10: Crossfade opacity interpolation verified (linear progression: 0.00 -> 0.250 -> 0.503 -> 0.753 -> 1.00).
   - FA-11: Full sequence consecutive-pair tweening verified across multiple keyframes (7 total frames).
   - FA-12: Ping-Pong loop generation verified (4-frame sequence [1, 2, 3, 4] expanded to 6-frame loop [1, 2, 3, 4, 3, 2]).
   - FA-13: Remove animation tags verified (all `(\d+ms)` and `(replace|combine)` tags cleanly removed from layer names).
   - FA-14: Base keyframe pixel preservation verified (original keyframe pixels 100% untouched: kf_a=0.000000, kf_b=1.000000).
5. [x] `verify_config.py` Section 6 passes with all 44 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0 (457/457 tests passing in 46.66s, all stages in 60.93s).

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement frame animation and tweening helper plugin` (`b70d02e`)
- Outer repository commit: `feat(ralph): complete iteration 52 - frame animation plugin`
