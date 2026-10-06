# Implementation Plan — Linux Photo Editor (GIMP 3.x / PhotoGIMP)

Status: IN_PROGRESS

This file is the authoritative roadmap of product-development work to transform GIMP 3.x on Linux into a professional, Photoshop-grade photo editing environment.

---

## Completed Baseline Phases (Configuration & Integration Overlay)

- [x] **Phase 0 — Repository Archaeology & Baseline Analysis**: Verified GIMP 3.2.6, PhotoGIMP assets, and initialized tracking.
- [x] **Phase 1 — GIMP 3.2+ Multi-Target Installer**: Non-interactive batch mode (`--batch`), multi-target deployment (`--all`), isolated runtime backups.
- [x] **Phase 2 — Photoshop Keybinding Alignment**: Active Photoshop shortcuts configured in `shortcutsrc` (`Ctrl+A`, `Ctrl+D`, `Ctrl+Shift+I`, `Ctrl+J`, `Ctrl+T`, `Ctrl+Z`, `Ctrl+Shift+Z`, `Ctrl+L`, `Ctrl+M`, `Ctrl+U`, `B`, `E`, `V`, `M`, `L`, `W`, `C`, `J`, `S`, `T`, `Z`).
- [x] **Phase 3 — Single-Window Workspace & Theme**: Configured `sessionrc` dockable layout with Undo History panel, clean GIMP 3.x `gimprc`, portable dark `theme.css`, native desktop launcher, and multi-resolution icons.
- [x] **Phase 4 — Tool Options & Retouching Defaults**: Standardized presets in `tool-options/` (free-form crop, anti-aliased selections, tolerance 32 for Magic Wand / Color Select).
- [x] **Phase 5 — Automated Configuration Quality Gate**: Built `verify_config.py` with 5 automated audit sections and documented manual testing in `docs/SMOKE_TESTING.md`.

---

## Active Product Development Phases (Photoshop Feature Extensions)

### Phase 6 — Frequency Separation Retouching Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `frequency-separation` (`python-fu-frequency-separation`) in `PhotoGIMP/.config/GIMP/3.0/plug-ins/frequency-separation/frequency-separation.py`.
- [x] Implement interactive dialog with Gaussian blur radius slider (default: 3.0px) and seamless layer reconstruction math.
- [x] Create grouped `Frequency Separation` folder with `Low Frequency` (color/tone) and `High Frequency` (texture/detail) layers.
- [x] Register under menu path `<Image>/Filters/Retouching/Frequency Separation...`.
- [x] Validate plugin syntax, registration, and execute automated headless GIMP test splitting a test image and verifying layer structure.

### Phase 7 — Luminosity Masks Channel Generator
- [ ] Implement native GIMP 3.x Python 3 plugin `luminosity-masks` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/luminosity-masks/luminosity_masks.py`.
- [ ] Automatically calculate 9 precision tonal channels: Lights (1, 2, 3), Darks (1, 2, 3), and Midtones (1, 2, 3).
- [ ] Register under menu path `<Image>/Select/Luminosity Masks...`.
- [ ] Validate channel generation on test image via headless GIMP test.

### Phase 8 — Non-Destructive Dodge & Burn Layer Helper
- [ ] Implement native GIMP 3.x Python 3 plugin `dodge-burn-layer` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/dodge-burn-layer/dodge_burn_layer.py`.
- [ ] Create 50% neutral gray overlay layer (`#808080`) set to Overlay or Soft Light blend mode.
- [ ] Register under menu path `<Image>/Layer/New Dodge & Burn Layer...`.
- [ ] Validate layer creation and properties via headless GIMP test.

### Phase 9 — High Pass Sharpening Helper
- [ ] Implement native GIMP 3.x Python 3 plugin `high-pass-sharpen` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/high-pass-sharpen/high_pass_sharpen.py`.
- [ ] Duplicate active layer, apply `gegl:high-pass` filter with configurable radius, and set blend mode to Soft Light / Overlay.
- [ ] Register under menu path `<Image>/Filters/Enhance/High Pass Sharpen...`.
- [ ] Validate sharpening layer generation via headless GIMP test.

### Phase 10 — Quick Export (Web & Social Presets)
- [ ] Implement native GIMP 3.x Python 3 plugin `quick-export` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/quick-export/quick_export.py`.
- [ ] Fast one-click export to PNG / JPEG in document directory with automatic scaling (1x, 2x, 0.5x).
- [ ] Register under menu path `<Image>/File/Quick Export as PNG...`.
- [ ] Validate exported image files via headless GIMP test.

### Phase 11 — End-to-End Plugin Suite Quality Gate
- [ ] Extend `PhotoGIMP/scripts/verify_config.py` with Section 6 Plugin Suite audit.
- [ ] Ensure `PhotoGIMP/install.sh` deploys all plugin directories to user config `plug-ins/` with executable permissions.
- [ ] Execute full headless GIMP test suite exercising all custom plugins.
