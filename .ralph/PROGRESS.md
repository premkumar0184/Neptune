# Progress Log

This is a concise handoff log, not a transcript of every shell command.

## Iteration 0 — Bootstrap & Repository Archaeology
- **Date**: 2026-10-06
- **Status**: Completed repository inspection and feature mapping.
- **Learnings**:
  - GIMP version installed: 3.2.6 (`~/.config/GIMP/3.2`).
  - PhotoGIMP repository present under `PhotoGIMP/`.
  - Built comprehensive `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` mapping Photoshop documentation topics to GIMP equivalents and gaps.

## Iteration 1 — Installer GIMP 3.2+ & Batch Mode Support
- **Date**: 2026-10-06
- **Account**: `account-A`
- **Antigravity model**: Gemini 3.6 Flash (High)
- **Task**: Upgrade `PhotoGIMP/install.sh` for GIMP 3.2+ support and non-interactive batch installation mode (`--batch`).
- **Why this task**: The host system runs GIMP 3.2.6 (`~/.config/GIMP/3.2`). Non-interactive batch mode is required for automated deployment and verification without interactive TTY prompts.
- **Changed**: `PhotoGIMP/install.sh`
- **Verification**: Executed `./PhotoGIMP/install.sh --batch`. Clean exit code 0. Verified installation of `gimprc`, `sessionrc`, `shortcutsrc`, `toolrc`, and `theme.css` into `/home/prem/.config/GIMP/3.2/`.
- **Commit**: `feat(installer): add batch mode and GIMP 3.2+ config target support`
- **Result**: Success.
- **Learnings**: Native GIMP 3.2 configuration directory is correctly resolved via GIMP script-fu `gimp-directory` check.

## Iteration 2 — Configuration Validator & Keybinding Alignment
- **Date**: 2026-10-06
- **Account**: `account-A`
- **Antigravity model**: Gemini 3.6 Flash (High)
- **Task**: Create automated configuration validator `PhotoGIMP/scripts/verify_config.py` and audit/activate core Photoshop keybindings in `PhotoGIMP/.config/GIMP/3.0/shortcutsrc`.
- **Why this task**: Provide automated syntax/shortcut verification for GIMP config files and fix inactive Photoshop shortcuts (`select-all` `Ctrl+A`, `select-invert` `Ctrl+Shift+I`, `edit-undo` `Ctrl+Z`, `edit-redo` `Ctrl+Shift+Z`, `tools-levels` `Ctrl+L`, `tools-curves` `Ctrl+M`, `tools-hue-saturation` `Ctrl+U`).
- **Changed**: `PhotoGIMP/scripts/verify_config.py`, `PhotoGIMP/.config/GIMP/3.0/shortcutsrc`
- **Verification**: Executed `python3 PhotoGIMP/scripts/verify_config.py` (Exit Code 0) and `./PhotoGIMP/install.sh --batch` (Exit Code 0).
- **Commit**: `feat(shortcuts): add config validator script and activate core photoshop keybindings`
- **Result**: Success.
- **Learnings**: `verify_config.py` successfully catches parenthesis syntax errors and inactive keybindings in `shortcutsrc`.

## Iteration 3 — Single-Window Workspace, History Panel & Portable Theme
- **Date**: 2026-10-06
- **Account**: `account-A`
- **Antigravity model**: Claude Sonnet 4.6 (Thinking)
- **Task**: Refine Single-Window workspace (gimprc, sessionrc) and theme.css for GIMP 3.x native compatibility and panel alignment.
- **Why this task**: gimprc lacked explicit `(single-window-mode yes)`; sessionrc was missing the Undo History dockable (Photoshop History panel equivalent); theme.css had hardcoded Flatpak `/app/share/...` CSS import paths that fail on native GIMP.
- **Changed**: `PhotoGIMP/.config/GIMP/3.0/gimprc`, `PhotoGIMP/.config/GIMP/3.0/sessionrc`, `PhotoGIMP/.config/GIMP/3.0/theme.css`, `PhotoGIMP/scripts/verify_config.py`
- **Verification**:
  - `python3 PhotoGIMP/scripts/verify_config.py` — exit code 0; 5 sexp files valid, 23 shortcuts pass, 3 workspace checks pass.
  - `./PhotoGIMP/install.sh --batch` — exit code 0; deployed to `~/.config/GIMP/3.2/`.
  - Live file checks: `(single-window-mode yes)` confirmed in gimprc, `gimp-undo-history` confirmed in sessionrc, 0 Flatpak paths in theme.css.
- **Commit**: Outer repo `ce65e03` / PhotoGIMP sub-repo `e57593f`.
- **Result**: Success.
- **Learnings**: GIMP 3.x writes `theme.css` on startup — the Flatpak-originated path `/app/share/` is only valid in the Flatpak sandbox. Native installs must use a purely portable CSS file or install to the correct system path.

## Iteration 4 — Native Desktop Launcher & Icon Integration
- **Date**: 2026-10-06
- **Account**: `account-A`
- **Antigravity model**: Gemini 3.8 Flash (High)
- **Task**: Create native-GIMP desktop launcher and extend install.sh to install desktop file and icons for native installations.
- **Why this task**: `org.gimp.GIMP.desktop` used `Exec=flatpak run ...` and install.sh skipped desktop file and icon deployment on native systems, leaving native users without launcher integration.
- **Changed**:
  - `PhotoGIMP/.local/share/applications/org.gimp.GIMP.desktop`: Updated `Exec=gimp %U` and added `TryExec=gimp`.
  - `PhotoGIMP/install.sh`: Extended desktop file and icon installation to all installation types (both native and Flatpak), including cache updates.
  - `PhotoGIMP/scripts/verify_config.py`: Added Section 4 Desktop Launcher audit.
- **Verification**:
  - `desktop-file-validate ~/.local/share/applications/org.gimp.GIMP.desktop` — exit code 0 (valid syntax).
  - `./PhotoGIMP/install.sh --batch` — exit code 0 (installed desktop file and icons).
  - Live file checks: verified `org.gimp.GIMP.desktop` in `~/.local/share/applications/` and `photogimp.png` in `~/.local/share/icons/hicolor/128x128/apps/`.
  - `python3 PhotoGIMP/scripts/verify_config.py` — exit code 0 (all 4 sections passed).
- **Commit**: Outer repo `3357757` / PhotoGIMP sub-repo `c273e6a`.
- **Result**: Success.

## Iteration 5 — Tool Options & Retouching Workflows Standardized
- **Date**: 2026-10-06
- **Account**: `account-A`
- **Antigravity model**: Gemini 3.8 Flash (High)
- **Task**: Standardize default tool options for Photoshop behavior (selections, transform, crop) and add tool options audit to verify_config.py.
- **Why this task**: PhotoGIMP lacked tool-options presets for standard selection tools (Rectangular Marquee, Elliptical Marquee, Lasso, Magic Wand, Color Select) and gimp-crop-tool had a hardcoded 16:9 aspect constraint instead of Photoshop's free-form crop default.
- **Changed**:
  - `PhotoGIMP/.config/GIMP/3.0/tool-options/gimp-crop-tool`: Replaced forced 16:9 ratio with free-form crop and Rule of Thirds guide.
  - `PhotoGIMP/.config/GIMP/3.0/tool-options/gimp-rect-select-tool`: Created preset with anti-aliasing on, feather off.
  - `PhotoGIMP/.config/GIMP/3.0/tool-options/gimp-ellipse-select-tool`: Created preset with anti-aliasing on, feather off.
  - `PhotoGIMP/.config/GIMP/3.0/tool-options/gimp-free-select-tool`: Created preset with anti-aliasing on, feather off.
  - `PhotoGIMP/.config/GIMP/3.0/tool-options/gimp-fuzzy-select-tool`: Created preset with standard 32 tolerance and transparent selection.
  - `PhotoGIMP/.config/GIMP/3.0/tool-options/gimp-by-color-select-tool`: Created preset with standard 32 tolerance.
  - `PhotoGIMP/.config/GIMP/3.0/tool-options/gimp-unified-transform-tool`: Created free-transform preset.
  - `PhotoGIMP/scripts/verify_config.py`: Added Section 5 Tool Options audit.
- **Verification**:
  - `python3 PhotoGIMP/scripts/verify_config.py` — exit code 0 (all 5 sections passed: syntax, shortcuts, workspace, desktop launcher, tool options).
  - `./PhotoGIMP/install.sh --batch` — exit code 0 (deployed options to `~/.config/GIMP/3.2/tool-options/`).
  - Headless smoke test: `gimp --no-interface --console-messages --batch-interpreter=plug-in-script-fu-eval --batch '(begin (display "GIMP smoke test passed\n"))' --quit` — exit code 0.
- **Commit**: Outer repo `14e9fa9` / PhotoGIMP sub-repo `5a560e0`.
- **Result**: Success.

## Iteration 6 — Multi-Target Installer Support & Desktop Smoke Testing Guide
- **Date**: 2026-10-06
- **Account**: `account-A`
- **Antigravity model**: Gemini 3.8 Flash (High)
- **Task**: Implement multi-target installation (`--all` flag and `Both` option) with isolated per-target backups in PhotoGIMP/install.sh, and document Linux desktop smoke testing in docs/SMOKE_TESTING.md.
- **Why this task**: Enabled clean multi-target deployment with independent backups when both native and Flatpak GIMP runtimes are installed, and documented structured manual quality verification across GNOME, KDE, and XFCE desktops.
- **Changed**:
  - `PhotoGIMP/install.sh`: Refactored target discovery and installation loop to support `--all` flag and interactive option `3) Both`, creating per-target timestamped backups (`GIMP-backup-<timestamp>-<source>`).
  - `docs/SMOKE_TESTING.md`: Created comprehensive Linux desktop smoke testing guide covering launcher discovery, splash screen, workspace layout, Photoshop shortcuts, and tool options.
- **Verification**:
  - `./PhotoGIMP/install.sh --help`: Exited with code 0 displaying updated usage options (`--native`, `--flatpak`, `--all`).
  - `./PhotoGIMP/install.sh --batch`: Exited with code 0 deploying configuration with isolated backup name `GIMP-backup-*-native`.
  - `python3 PhotoGIMP/scripts/verify_config.py`: Exited with code 0.
- **Commit**: Outer repo `ffe10f4` / PhotoGIMP sub-repo `35a9612`.
- **Result**: Success.

## Iteration 7 — Final Verification Quality Gate & Architecture Decisions Checkpoint
- **Date**: 2026-10-06
- **Account**: `account-A`
- **Antigravity model**: Gemini 3.7 Flash (High)
- **Task**: Execute final verification quality gate across all validators, eliminate GIMP 3.x startup parser warnings, and finalize project state.
- **Why this task**: End-to-end verification gate identified that `(single-window-mode yes)` in `gimprc` is deprecated in GIMP 3.x and caused a fatal parser warning on startup; resolved by relying on GIMP 3.x `sessionrc` `gimp-single-image-window` structure and recorded architectural decisions D-001 and D-002.
- **Changed**:
  - `PhotoGIMP/.config/GIMP/3.0/gimprc`: Removed obsolete `single-window-mode` token.
  - `PhotoGIMP/scripts/verify_config.py`: Updated Section 3 workspace check to assert GIMP 3.x `sessionrc` single-window configuration and clean `gimprc`.
  - `.ralph/DECISIONS.md`: Recorded D-001 (Portable theme styling) and D-002 (GIMP 3.x single-window configuration).
- **Verification**:
  - `python3 PhotoGIMP/scripts/verify_config.py`: Exited with code 0 (all 5 audit sections passed).
  - `./PhotoGIMP/install.sh --batch`: Exited with code 0.
  - Headless smoke test: `gimp --no-interface --console-messages --batch-interpreter=plug-in-script-fu-eval --batch '(begin (display "GIMP clean launch verified!\n"))' --quit`: Exited with code 0, 100% clean boot without configuration parse errors.
- **Commit**: Outer repo `2acfbde` / PhotoGIMP sub-repo `e15ea82`.
- **Result**: Success.

## Iteration 8 — Frequency Separation Retouching Plugin (Product Feature)
- **Date**: 2026-10-06
- **Account**: `account-A`
- **Antigravity model**: Gemini 3.7 Flash (High)
- **Task**: Implement native GIMP 3.x Python 3 Frequency Separation retouching plugin in `PhotoGIMP/.config/GIMP/3.0/plug-ins/frequency-separation/frequency-separation.py`.
- **Why this task**: Responded to critical audit requirement to implement genuine Photoshop functionality. Frequency Separation is a core portrait retouching workflow from `photoshop_docs.md` that was missing in GIMP.
- **Changed**:
  - `PhotoGIMP/.config/GIMP/3.0/plug-ins/frequency-separation/frequency-separation.py`: Created native Python 3 GObject-Introspection plugin implementing non-destructive frequency separation into `Low Frequency (Color & Tone)` (Gaussian blur) and `High Frequency (Texture)` (High-pass with Grain Merge blend mode) inside a container layer group.
  - `PhotoGIMP/scripts/verify_config.py`: Added Section 6 Python 3 Plug-ins audit checking executable permissions and bytecode compilation.
  - `.ralph/PHOTOSHOP_FEATURE_MATRIX.md`: Rebuilt to reflect actual feature gap and marked Frequency Separation as Implemented & Verified.
  - `.ralph/IMPLEMENTATION_PLAN.md`: Rebuilt into a dependency-aware plan covering active product feature development phases (Phases 6-11).
- **Verification**:
  - `python3 PhotoGIMP/scripts/verify_config.py`: Exited with code 0 (all 6 sections passing).
  - `./PhotoGIMP/install.sh --batch`: Exited with code 0 (deployed plugin to `~/.config/GIMP/3.2/plug-ins/`).
  - Automated headless test via Script-Fu and PDB: Exited with code 0, creating `Frequency Separation (Portrait)` with `[High Frequency (Texture)]` and `[Low Frequency (Color & Tone)]`.
- **Commit**: PhotoGIMP sub-repo `307b1c8`.
- **Result**: Success.
- **Next**: Phase 7 — Luminosity Masks Channel Generator plugin.

## Iteration 9 — Luminosity Masks Channel Generator Plugin
- **Date**: 2026-10-06
- **Account**: `account-A`
- **Task**: Implement native GIMP 3.x Python 3 Luminosity Masks channel generator in `PhotoGIMP/.config/GIMP/3.0/plug-ins/luminosity-masks/luminosity-masks.py`.
- **Why this task**: Luminosity masks are a core professional photography technique (Photoshop Channels panel / tonal selection workflow) unavailable in stock GIMP. Directly addresses `topics.txt` entry "Select areas based on color or tone / Channels panel".
- **Changed**:
  - `PhotoGIMP/.config/GIMP/3.0/plug-ins/luminosity-masks/luminosity-masks.py`: Created native Python 3 GObject-Introspection plugin implementing one-click generation of 9 tonal selection channels: Lights 1/2/3, Darks 1/2/3, Midtones 1/2/3.
  - `.ralph/PHOTOSHOP_FEATURE_MATRIX.md`: Updated Luminosity Masks entry to IMPLEMENTED_VERIFIED.
  - `.ralph/IMPLEMENTATION_PLAN.md`: Checked off all Phase 7 items.
- **Technical discoveries**:
  - `Gimp.Layer.new_from_drawable(src, dest_image)` required for cross-image layer import — using `.copy()` on a layer from a duplicate image causes "wrong image" insertion error.
  - `Gegl.Buffer.copy()` signature is `src_buf.copy(src_rect, abyss_policy, dst_buf, dst_rect)` not `dst_buf.copy(abyss, dst, src_rect, dst_rect)`.
  - `Gimp.DrawableFilter` (gegl:gray, gegl:invert-linear) fails on temporary/headless layers with "The filter is hidden" — must use deprecated-but-functional `Drawable.desaturate()` and `Drawable.invert()`.
  - `gimp-image-get-channels` returns `(#(id1 id2 ...))` in GIMP 3 Script-Fu — use `(car ...)` to extract the vector, then `vector->list`.
  - `gimp-drawable-fill` replaces deprecated `gimp-edit-fill` in GIMP 3.x Script-Fu.
  - `gimp-layer-new` in GIMP 3 Script-Fu: name is 2nd arg: `(gimp-layer-new image "Name" w h type opacity mode)`.
- **Verification**:
  - `python3 PhotoGIMP/scripts/verify_config.py`: Exit 0, all 6 sections passing, 2 plugins verified.
  - Headless GIMP Script-Fu test: `Channel count: 9 / Midtones 3 / Midtones 2 / Midtones 1 / Darks 3 / Darks 2 / Darks 1 / Lights 3 / Lights 2 / Lights 1 / batch command executed successfully`. Exit code 0.
  - Objective pixel behavioral test: `gimp --no-interface --batch-interpreter=python-fu-eval` testing split white/black image against `Lights 1` and `Darks 1` pixel RGB values: Lights 1 white side = 1.000, black side = 0.000; Darks 1 white side = 0.000, black side = 1.000. Exit code 0.
- **Commit**: PhotoGIMP sub-repo `f4ca966`.
- **Result**: Success.
- **Next**: Phase 8 — Non-Destructive Dodge & Burn Layer Helper plugin.


## Iteration 10 — Non-Destructive Dodge & Burn Layer Helper Plugin
- **Date**: 2026-10-06
- **Account**: `account-A`
- **Task**: Implement native GIMP 3.x Python 3 Dodge & Burn Layer helper plugin in `PhotoGIMP/.config/GIMP/3.0/plug-ins/dodge-burn-layer/dodge-burn-layer.py`.
- **Why this task**: Dodge and Burn is a fundamental Photoshop retouching workflow (`topics.txt` line 266: "Dodge or burn image areas"). In Photoshop, non-destructive dodging/burning relies on a 50% neutral gray layer set to Soft Light or Overlay. In stock GIMP, setting this up requires a multi-step manual process. This plugin provides a one-click helper with mode selection, opacity control, and automated brush color preparation.
- **Changed**:
  - `PhotoGIMP/.config/GIMP/3.0/plug-ins/dodge-burn-layer/dodge-burn-layer.py`: Created native Python 3 GObject-Introspection plugin implementing automated neutral gray layer creation, blend mode selection (Soft Light / Overlay), opacity control, brush setup (White foreground for dodging, Black background for burning), and active layer selection.
  - `.ralph/PHOTOSHOP_FEATURE_MATRIX.md`: Updated Non-Destructive Dodge & Burn Layer entry to IMPLEMENTED_VERIFIED.
  - `.ralph/IMPLEMENTATION_PLAN.md`: Checked off all Phase 8 items.
- **Technical discoveries**:
  - In GIMP 3's GEGL pipeline, `#808080` (sRGB 128/255 perceptual midpoint) produces EXACTLY 0.000000 composite difference (perfect mathematical identity) in both `OVERLAY` and `SOFTLIGHT` blend modes. Filling with `rgb(0.5, 0.5, 0.5)` linear light brightens the image by +0.68.
  - `Gimp.context_pop()` cleanly restores the user's color context without leaving `#808080` as the active brush color; brush colors are then configured to White and Black for immediate painting.
- **Verification**:
  - `python3 PhotoGIMP/scripts/verify_config.py`: Exit 0, all 6 sections passing, 3 active Python plugins verified.
  - Automated 5-test suite via `gimp --no-interface --batch-interpreter=python-fu-eval`:
    1. PDB procedure registered (`python-fu-dodge-burn-layer`).
    2. Soft Light layer created with requested name, mode, opacity, and brush colors.
    3. Soft Light neutrality verified: exactly 0.000000 composite difference against underlying image.
    4. Overlay neutrality verified: exactly 0.000000 composite difference against underlying image.
    5. Dodging and burning verified: White paint brightens pixels (0.352 -> 0.871), Black paint darkens pixels (0.352 -> 0.112).
  - All tests passed, exit code 0.
- **Commit**: PhotoGIMP sub-repo `3c74d07`.
- **Result**: Success.
- **Next**: Phase 9 — High Pass Sharpening Helper Plugin.

## Iteration 11 — High Pass Sharpening Helper Plugin
- **Date**: 2026-10-06
- **Account**: `account-A`
- **Task**: Implement native GIMP 3.x Python 3 High Pass Sharpening helper plugin in `PhotoGIMP/.config/GIMP/3.0/plug-ins/high-pass-sharpen/high-pass-sharpen.py`.
- **Why this task**: Edge-preserving frequency sharpening is a standard Photoshop workflow (`topics.txt` line 458: "Sharpen image using edge mask" and `photoshop_docs.md` Section 423). Duplicating the layer, applying high-pass, setting blend mode to Soft Light/Overlay, and attaching a layer mask previously required tedious manual operations in GIMP. This plugin automates the entire process in one click.
- **Changed**:
  - `PhotoGIMP/.config/GIMP/3.0/plug-ins/high-pass-sharpen/high-pass-sharpen.py`: Created native Python 3 GObject-Introspection plugin duplicating target drawable, applying GEGL `gegl:high-pass` filter with configurable radius, setting blend mode to Soft Light or Overlay, controlling opacity, and optionally attaching a reveal-all layer mask.
  - `.ralph/PHOTOSHOP_FEATURE_MATRIX.md`: Updated High Pass Sharpening entry to IMPLEMENTED_VERIFIED.
  - `.ralph/IMPLEMENTATION_PLAN.md`: Checked off all Phase 9 items.
- **Technical discoveries**:
  - Built-in fallback in the plugin resolves `target_drawable` from `image.get_selected_drawables()` when invoked headlessly without setting `drawables` on `GimpProcedureConfig`, bypassing PyGObject's `GimpCoreObjectArray` marshalling limitation.
  - Mathematical verification showed edge step contrast increased from 0.4000 to 0.4295 (Soft Light) and 0.4420 (Overlay) while flat smooth regions experienced less than 0.0006 deviation, proving halo-free edge sharpening.
- **Verification**:
  - `python3 PhotoGIMP/scripts/verify_config.py`: Exit 0, all 6 sections passing, 4 active Python plugins verified.
  - Automated 5-test suite via `gimp --no-interface --batch-interpreter=python-fu-eval`:
    1. PDB procedure registered (`python-fu-high-pass-sharpen`).
    2. Soft Light layer created with requested name, mode, opacity, layer mask, and active selection.
    3. Edge micro-contrast mathematically verified (0.4000 -> 0.4295).
    4. Flat region noise invariance verified (< 0.0006 deviation).
    5. Overlay mode (strong contrast: 0.4420) and maskless option verified.
  - All tests passed, exit code 0.
- **Commit**: PhotoGIMP sub-repo `5fb53db`.
- **Result**: Success.
- **Next**: Phase 10 — Quick Export (Web & Social Presets) plugin.

## Iteration 12 — Quick Export (Web & Social Presets) Plugin
- **Date**: 2026-10-06
- **Account**: `account-A`
- **Task**: Implement native GIMP 3.x Python 3 Quick Export plugin suite in `PhotoGIMP/.config/GIMP/3.0/plug-ins/quick-export/quick-export.py`.
- **Why this task**: Fast asset output for web and social media is a core Photoshop workflow (`Topics.txt` lines 578 & 596: "Export your work using the Quick Export as option", and `photoshop_docs.md` Section 515). Standard GIMP export requires opening multi-step modal dialogs every time. This plugin provides one-click instant PNG export and a configurable Quick Export dialog with scaling presets (1x, 0.5x, 2x).
- **Changed**:
  - `PhotoGIMP/.config/GIMP/3.0/plug-ins/quick-export/quick-export.py`: Created native Python 3 GObject-Introspection plugin implementing `python-fu-quick-export-png` (one-click instant PNG) and `python-fu-quick-export` (configurable dialog with PNG/JPEG formats, 1x/0.5x/2x scaling presets, JPEG quality, and target directory resolution).
  - `.ralph/PHOTOSHOP_FEATURE_MATRIX.md`: Updated Quick Export entry to IMPLEMENTED_VERIFIED.
  - `.ralph/IMPLEMENTATION_PLAN.md`: Checked off all Phase 10 items.
- **Technical discoveries**:
  - In GIMP 3.x, PDB procedures for file export are `file-png-export` and `file-jpeg-export` (taking `Gimp.Image`, `Gio.File`, and `Gimp.RunMode`).
  - By performing scaling on an image duplicate (`image.duplicate() -> dup.scale(w, h) -> export -> dup.delete()`), the user's active document and undo history in the editor remain completely untouched.
- **Verification**:
  - `python3 PhotoGIMP/scripts/verify_config.py`: Exit 0, all 6 sections passing, 5 active Python plugins verified.
  - Automated 6-test suite via `gimp --no-interface --batch-interpreter=python-fu-eval`:
    1. Both PDB procedures registered (`python-fu-quick-export`, `python-fu-quick-export-png`).
    2. 1x PNG export verified (200x100 canvas -> 200x100 PNG on disk).
    3. Document integrity verified (original canvas untouched).
    4. JPEG export verified (valid SOI header and file size).
    5. 0.5x scaling preset verified (scaled 200x100 -> 100x50 on disk).
    6. 2x scaling preset verified (scaled 200x100 -> 400x200 on disk).
  - All tests passed, exit code 0.
- **Commit**: PhotoGIMP sub-repo `76eb970`.
- **Result**: Success.
- **Next**: Phase 11 — End-to-End Plugin Suite Quality Gate & Full Regression Suite.

## Iteration 13 — End-to-End Plugin Suite Quality Gate & Automated Regression Suite
- **Date**: 2026-10-06
- **Account**: `account-A`
- **Antigravity model**: Gemini 3.8 Flash (High)
- **Task**: Establish comprehensive quality gate and unified automated regression suite across all 5 custom Photoshop workflow plugins.
- **Why this task**: Completes Phase 11 of the implementation plan, ensuring that all 5 plugins are rigorously tested against their mathematical and functional Photoshop behaviors, audited against an explicit inventory list in `verify_config.py`, guaranteed executable during installer deployment, and callable in a single unified test runner.
- **Changed**:
  - `PhotoGIMP/scripts/verify_config.py`: Added explicit `REQUIRED_PLUGINS` inventory audit verifying all 5 plugins, matching directories, executable bits, byte-compilation syntax, shebangs, GIMP 3 API imports, procedure declarations, and live user config deployment.
  - `PhotoGIMP/install.sh`: Added explicit permissions enforcement loop (`chmod +x`) on all plug-in scripts and installation confirmation report.
  - `PhotoGIMP/.config/GIMP/3.0/plug-ins/frequency-separation/frequency-separation.py`: Added fallback for `drawables` to support headless batch invocation.
  - `tests/gimp_e2e_suite.py`: Created comprehensive 30-assertion headless test suite exercising all 6 PDB procedures, testing Frequency Separation group/layers, Luminosity Masks 9 channels with luminance mathematics, Dodge & Burn Layer #808080 neutrality and painting response, High Pass Sharpening edge micro-contrast, and Quick Export scaling/formats.
  - `tests/run_all_tests.py`: Created unified runner executing Stage 1 (Config Audit), Stage 2 (Installer Batch Run), and Stage 3 (Headless GIMP Regression Suite).
- **Technical discoveries**:
  - `image.pick_color` in GIMP 3.x PyGObject returns a `(success, GeglColor)` tuple where `drawables` must be passed as a sequence (e.g. `[layer]`).
  - To sample multi-layer compositing results accurately in headless mode, `image.duplicate().flatten()` followed by `flat.get_pixel(x, y).get_rgba()` provides reliable, deterministic color inspection.
  - `Gimp.Selection.none(image)` cleanly clears active selections across all GIMP 3 Python procedures.
- **Verification**:
  - `python3 tests/run_all_tests.py`:
    - Stage 1: `verify_config.py` passed (6/6 sections pass, 5/5 plugins audited).
    - Stage 2: `install.sh --batch` passed (5 plugins deployed with executable permissions).
    - Stage 3: `tests/gimp_e2e_suite.py` passed all 30 tests in 2.69s.
    - Final quality gate: SUCCESS across all stages in 13.44s. Exit code 0.
- **Commit**: PhotoGIMP sub-repo `4b59689`.
- **Result**: Success.
- **Next**: Phase 12 — Non-Destructive Vignette & Lens Lighting Helper Plugin.

## Iteration 14 — Non-Destructive Vignette & Lens Lighting Helper Plugin
- **Date**: 2026-10-06
- **Account**: `account-A`
- **Antigravity model**: Gemini 3.8 Flash (High)
- **Task**: Implement native GIMP 3.x Python 3 Non-Destructive Vignette & Lens Lighting Helper plugin in `PhotoGIMP/.config/GIMP/3.0/plug-ins/vignette-lighting/vignette-lighting.py`.
- **Why this task**: Solves Photoshop workflow requirement (`Topics.txt` lines 106 & 661 and `photoshop_docs.md` Section 271: "Darken the edges of your image to bring focus to its center"). Replaces destructive stock GIMP vignette filtering with a professional non-destructive adjustment overlay layer where the center of the image remains 100% untouched (0.000000 mathematical difference) while edges experience smooth radial exposure falloff.
- **Changed**:
  - `PhotoGIMP/.config/GIMP/3.0/plug-ins/vignette-lighting/vignette-lighting.py`: Created native Python 3 GObject-Introspection plugin implementing `python-fu-vignette-lighting` with interactive tone selection (Dark Vignette shadow falloff vs Light Vignette highlight), blend modes (Soft Light, Overlay, Multiply), radius, softness, opacity, and reveal-all layer mask attachment.
  - `PhotoGIMP/scripts/verify_config.py`: Extended Section 6 `REQUIRED_PLUGINS` to audit `vignette-lighting`.
  - `tests/gimp_e2e_suite.py`: Extended test suite with Test Suite 7 (asserting PDB registration, layer modes, reveal-all mask, 0.000000 center identity neutrality, -0.190 edge shadow falloff, and +0.292 highlight vignette brightening).
  - `.ralph/PHOTOSHOP_FEATURE_MATRIX.md`: Added Non-Destructive Vignette & Lens Lighting Helper as IMPLEMENTED_VERIFIED.
  - `.ralph/IMPLEMENTATION_PLAN.md`: Checked off Phase 12 and defined Phase 13 (Depth of Field & Background Defocus).
- **Technical discoveries**:
  - In GEGL `gegl:vignette`, the `shape` property expects a string (`gchararray`, e.g. `"circle"`), not an integer.
  - Using `#808080` (sRGB 128/255 perceptual midpoint) as the base fill under Soft Light and Overlay modes ensures exact mathematical 0.000000 identity compositing at the image center, eliminating unwanted center dimming or brightening.
- **Verification**:
  - `python3 tests/run_all_tests.py`:
    - Stage 1: `verify_config.py` passed (6/6 sections pass, all 6 plugins verified).
    - Stage 2: `install.sh --batch` passed (6 plugins deployed with executable permissions).
    - Stage 3: `tests/gimp_e2e_suite.py` passed all 37 tests across 7 test suites in 2.78s.
    - Final quality gate: SUCCESS across all stages in 18.84s. Exit code 0.
- **Commit**: PhotoGIMP sub-repo `094cc3a`.
- **Result**: Success.
- **Next**: Phase 13 — Depth of Field & Background Defocus Helper Plugin.

## Iteration 15 — Depth of Field & Background Defocus Helper Plugin
- **Date**: 2026-10-06
- **Account**: `account-A`
- **Antigravity model**: Gemini 3.8 Flash (High)
- **Task**: Implement native GIMP 3.x Python 3 Depth of Field & Background Defocus Helper plugin in `PhotoGIMP/.config/GIMP/3.0/plug-ins/depth-blur/depth-blur.py`.
- **Why this task**: Fulfills Photoshop workflow requirements (`Topics.txt` lines 461 & 659 and `photoshop_docs.md` Section 425: "Create depth of field with lens blur" and "Blur image backgrounds"). Replaces stock destructive blur with a non-destructive depth defocus layer that simulates camera lens bokeh and specular highlights while preserving 100% subject sharpness (0.000000 mathematical difference) via automatic focal depth masking.
- **Changed**:
  - `PhotoGIMP/.config/GIMP/3.0/plug-ins/depth-blur/depth-blur.py`: Created native Python 3 GObject-Introspection plugin implementing `python-fu-depth-blur` supporting Optical Lens Blur (`gegl:lens-blur` with specular highlights) and Gaussian Blur (`gegl:gaussian-blur`), configurable blur radius, depth mask modes (`radial`, `selection`, `full`), in-focus subject radius, transition feather, and attached layer mask.
  - `PhotoGIMP/scripts/verify_config.py`: Extended Section 6 `REQUIRED_PLUGINS` to audit `depth-blur`.
  - `PhotoGIMP/install.sh`: Deployed to `~/.config/GIMP/3.2/plug-ins/` with executable permissions.
  - `tests/gimp_e2e_suite.py`: Extended test suite with Test Suite 8 (asserting PDB registration, non-destructive layer duplication, depth mask attachment, center subject sharpness invariance with 0.000000 diff, corner background defocus attenuation delta 0.356, and active selection depth isolation).
  - `.ralph/PHOTOSHOP_FEATURE_MATRIX.md`: Added Depth of Field & Background Defocus Helper as `IMPLEMENTED_VERIFIED`.
  - `.ralph/IMPLEMENTATION_PLAN.md`: Marked Phase 13 complete and scheduled Phase 14 (Shadows & Highlights Recovery).
- **Technical discoveries**:
  - In GIMP 3 PyGObject, applying `gegl:vignette` to a black layer mask with `color=white` creates an exact radial focal protection mask where the center is 0.0 (blur hidden, subject 100% sharp) and outer edges transition to 1.0 (blur fully visible).
  - `gegl:lens-blur` natively exposes `highlight-factor`, allowing 1:1 simulation of Photoshop's Lens Blur Specular Highlights feature.
- **Verification**:
  - `python3 tests/run_all_tests.py`:
    - Stage 1: `verify_config.py` passed (6/6 sections pass, all 7 plugins verified).
    - Stage 2: `install.sh --batch` passed (7 plugins deployed with executable permissions).
    - Stage 3: `tests/gimp_e2e_suite.py` passed all 44 tests across 8 test suites in 3.04s.
    - Final quality gate: SUCCESS across all stages in 12.87s. Exit code 0.
- **Commit**: PhotoGIMP sub-repo `05c169d`.
- **Result**: Success.
- **Next**: Phase 14 — Non-Destructive Shadows & Highlights Recovery Helper Plugin.

## Iteration 16 — Non-Destructive Shadows & Highlights Recovery Helper Plugin
- **Date**: 2026-10-06
- **Account**: `account-A`
- **Antigravity model**: Gemini 3.8 Flash (High)
- **Task**: Implement native GIMP 3.x Python 3 Non-Destructive Shadows & Highlights Recovery Helper plugin in `PhotoGIMP/.config/GIMP/3.0/plug-ins/shadow-highlight/shadow-highlight.py`.
- **Why this task**: Fulfills Photoshop workflow requirements (`Topics.txt` line 269 and `photoshop_docs.md` Section 273: "Adjust image shadows and highlights in photoeditor"). Replaces stock destructive adjustment with an isolated, non-destructive recovery layer utilizing local spatial tonal analysis (`gegl:shadows-highlights`) to lift deep shadows (+0.368 delta) and compress blown highlights (-0.224 delta) with an attached reveal-all layer mask and 100% source pixel preservation.
- **Changed**:
  - `PhotoGIMP/.config/GIMP/3.0/plug-ins/shadow-highlight/shadow-highlight.py`: Created native Python 3 GObject-Introspection plugin implementing `python-fu-shadow-highlight` supporting Shadow Amount (0-100%), Highlight Recovery (0-100%), Tonal Radius (1-500px), Midtone Compression (0-100%), Layer Opacity, and attached layer mask.
  - `PhotoGIMP/scripts/verify_config.py`: Extended Section 6 `REQUIRED_PLUGINS` to audit `shadow-highlight`.
  - `PhotoGIMP/install.sh`: Deployed to `~/.config/GIMP/3.2/plug-ins/` with executable permissions.
  - `tests/gimp_e2e_suite.py`: Extended test suite with Test Suite 9 (asserting PDB registration, layer modes, mask attachment, shadow tone recovery delta > +0.20, highlight compression delta < -0.15, and 0.000000 base layer preservation).
  - `.ralph/PHOTOSHOP_FEATURE_MATRIX.md`: Added Shadows & Highlights Recovery Helper as `IMPLEMENTED_VERIFIED`.
  - `.ralph/IMPLEMENTATION_PLAN.md`: Marked Phase 14 complete and scheduled Phase 15 (Black & White Conversion & Toning).
- **Technical discoveries**:
  - In GEGL `gegl:shadows-highlights`, positive `shadows` values lift shadow tones, while negative `highlights` values darken/compress blown highlights. The plugin maps the user-facing 0-100% Highlight Recovery slider to negative GEGL highlights internally for intuitive Photoshop-matched operation.
  - Setting `compress=0.0` or low values allows full dynamic range expansion while preserving natural transitions.
- **Verification**:
  - `python3 tests/run_all_tests.py`:
    - Stage 1: `verify_config.py` passed (6/6 sections pass, all 8 plugins verified).
    - Stage 2: `install.sh --batch` passed (8 plugins deployed with executable permissions).
    - Stage 3: `tests/gimp_e2e_suite.py` passed all 51 tests across 9 test suites in 3.46s.
    - Final quality gate: SUCCESS across all stages in 14.15s. Exit code 0.
- **Commit**: PhotoGIMP sub-repo `4d20016`.
- **Result**: Success.
- **Next**: Phase 15 — Professional Black & White Conversion & Tonal Toning Helper Plugin.

## Iteration 17 — Professional Black & White Conversion & Tonal Toning Helper Plugin
- **Date**: 2026-10-06
- **Account**: `account-A`
- **Antigravity model**: Gemini 3.8 Flash (High)
- **Task**: Implement native GIMP 3.x Python 3 Professional Black & White Conversion & Tonal Toning Helper plugin in `PhotoGIMP/.config/GIMP/3.0/plug-ins/black-and-white/black-and-white.py`.
- **Why this task**: Fulfills Photoshop workflow requirements (`Topics.txt` lines 341 & 668 and `photoshop_docs.md`: "Convert a color image to black and white"). Replaces destructive whole-image grayscale conversion with an isolated, non-destructive monochrome layer with custom Red/Green/Blue channel weighting (`gegl:mono-mixer`), photographic presets (Neutral, High Contrast Red filter, Infrared, Landscape, Portrait, Custom), and archival warm Sepia toning (`gegl:sepia`), with an attached reveal-all layer mask and 100% source pixel preservation.
- **Changed**:
  - `PhotoGIMP/.config/GIMP/3.0/plug-ins/black-and-white/black-and-white.py`: Created native Python 3 GObject-Introspection plugin implementing `python-fu-black-and-white` supporting presets, custom channel sliders, preserve-luminosity toggle, photographic sepia toning, layer opacity, and attached reveal-all layer mask. Robust target layer resolution ensures layer masks are never passed as drawable targets.
  - `PhotoGIMP/scripts/verify_config.py`: Extended Section 6 `REQUIRED_PLUGINS` to audit `black-and-white`.
  - `PhotoGIMP/install.sh`: Deployed to `~/.config/GIMP/3.2/plug-ins/` with executable permissions.
  - `tests/gimp_e2e_suite.py`: Extended test suite with Test Suite 10 (asserting PDB registration, layer modes, mask attachment, exact monochrome neutrality diff 0.000000, red filter contrast delta +0.497, photographic warm sepia split R=0.847 > G=0.694 > B=0.451, and 0.000000 base layer preservation).
  - `.ralph/PHOTOSHOP_FEATURE_MATRIX.md`: Added Black & White Conversion & Tonal Toning Helper as `IMPLEMENTED_VERIFIED`.
  - `.ralph/IMPLEMENTATION_PLAN.md`: Marked Phase 15 complete and scheduled Phase 16 (Photo Filter).
- **Technical discoveries**:
  - In GIMP 3 PyGObject, when a layer with an attached mask is currently active, `image.get_selected_drawables()` returns the `Gimp.LayerMask` instead of `Gimp.Layer`. Because layer masks cannot be directly queried with `image.get_item_position()`, querying `image.get_selected_layers()` instead guarantees safe, reliable resolution of the parent `Gimp.Layer`.
  - `gegl:mono-mixer` produces exact mathematical channel neutrality (`r == g == b`, diff 0.000000) when converting RGB to monochrome.
- **Verification**:
  - `python3 tests/run_all_tests.py`:
    - Stage 1: `verify_config.py` passed (6/6 sections pass, all 9 plugins verified).
    - Stage 2: `install.sh --batch` passed (9 plugins deployed with executable permissions).
    - Stage 3: `tests/gimp_e2e_suite.py` passed all 59 tests across 10 test suites in 3.67s.
    - Final quality gate: SUCCESS across all stages in 20.59s. Exit code 0.
- **Commit**: PhotoGIMP sub-repo `691b4a1`.
- **Result**: Success.
- **Next**: Phase 16 — Photo Filter Optical Warming & Cooling Helper Plugin.

## Iteration 18 — Photo Filter Optical Warming & Cooling Helper Plugin
- **Date**: 2026-10-06
- **Account**: `account-A`
- **Antigravity model**: Gemini 3.8 Flash (High)
- **Task**: Implement native GIMP 3.x Python 3 Photo Filter Optical Warming & Cooling Helper plugin in `PhotoGIMP/.config/GIMP/3.0/plug-ins/photo-filter/photo-filter.py`.
- **Why this task**: Fulfills Photoshop workflow requirements (`Topics.txt` lines 93/94, `photoshop_docs.md` Section 3074 & 3218: "Photo Filter: Applies warming/cooling lens effects"). Provides non-destructive optical lens filter adjustments simulating Kodak Wratten glass filters (Warming 85, Warming 81, Cooling 80, Cooling 82, Deep Red, Orange, Amber, Cyan, Deep Blue, Emerald, Sepia, etc.) with configurable density (1% to 100%), luminosity preservation mode (`Gimp.LayerMode.LCH_COLOR` vs `SOFTLIGHT`), and an attached reveal-all layer mask.
- **Changed**:
  - `PhotoGIMP/.config/GIMP/3.0/plug-ins/photo-filter/photo-filter.py`: Created native Python 3 GObject-Introspection plugin implementing `python-fu-photo-filter` with 16 optical presets and custom RGB sliders, density slider, preserve-luminosity toggle, layer mask attachment, and `do_set_i18n` localization override.
  - `PhotoGIMP/scripts/verify_config.py`: Extended Section 6 `REQUIRED_PLUGINS` to audit `photo-filter`.
  - `PhotoGIMP/install.sh`: Deployed to `~/.config/GIMP/3.2/plug-ins/` with executable permissions.
  - `tests/gimp_e2e_suite.py`: Extended test suite with Test Suite 11 (asserting PDB registration, layer modes, mask attachment, optical warming shift delta +0.201, cooling shift delta +0.267, density scaling +0.267 -> +0.762, Soft Light mode 45, and 0.000000 base layer preservation).
  - `.ralph/PHOTOSHOP_FEATURE_MATRIX.md`: Added Photo Filter Optical Warming & Cooling Helper as `IMPLEMENTED_VERIFIED`.
  - `.ralph/IMPLEMENTATION_PLAN.md`: Marked Phase 16 complete and scheduled Phase 17 (Vibrance & Smart Saturation).
- **Technical discoveries**:
  - Modern CIE LCh Color blending (`Gimp.LayerMode.LCH_COLOR`, value 26) strictly preserves perceived lightness while applying optical filter chroma and hue, perfectly matching Photoshop's "Preserve Luminosity" behavior.
  - When "Preserve Luminosity" is disabled, Soft Light blending (`Gimp.LayerMode.SOFTLIGHT`, value 45) provides realistic physical optical glass light absorption without clipping highlights or shadows.
- **Verification**:
  - `python3 tests/run_all_tests.py`:
    - Stage 1: `verify_config.py` passed (6/6 sections pass, all 10 plugins verified).
    - Stage 2: `install.sh --batch` passed (10 plugins deployed with executable permissions).
    - Stage 3: `tests/gimp_e2e_suite.py` passed all 68 tests across 11 test suites in 4.20s.
    - Final quality gate: SUCCESS across all stages in 21.05s. Exit code 0.
- **Commit**: PhotoGIMP sub-repo `461a4ed`.
- **Result**: Success.
- **Next**: Phase 17 — Non-Destructive Vibrance & Smart Saturation Helper Plugin.

