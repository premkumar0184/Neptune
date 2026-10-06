# Implementation Plan — Linux Photo Editor (PhotoGIMP / GIMP 3.x)

Status: IN_PROGRESS

This file is the authoritative list of project work for transforming GIMP/PhotoGIMP into a seamless Photoshop-like editing experience.

## Product objective

Transform GIMP 3.x on Linux into a seamless Photoshop-like editing experience using the PhotoGIMP framework, custom configuration files (`gimprc`, `sessionrc`, `shortcutsrc`, `toolrc`, `theme.css`, `contextrc`), tool options, and desktop integration scripts.

---

## Phase 0 — Repository Archaeology & Baseline Analysis
- [x] Identify GIMP version (`GNU Image Manipulation Program version 3.2.6`).
- [x] Inspect PhotoGIMP repository structure and configuration assets (`PhotoGIMP/`).
- [x] Verify system GIMP installation (`/usr/bin/gimp`) and user config directory (`~/.config/GIMP/3.2`).
- [x] Build comprehensive Photoshop Feature Matrix (`.ralph/PHOTOSHOP_FEATURE_MATRIX.md`).
- [x] Initialize Git tracking and create baseline commit.

---

## Phase 1 — GIMP 3.2+ Installer Compatibility & Automated Deployment
- [x] Update `PhotoGIMP/install.sh` to detect and support GIMP 3.2+ configuration directory (`~/.config/GIMP/3.2/` alongside `3.0/`).
- [x] Add non-interactive installation flag (`--batch` / `-y` / `--yes`) to `PhotoGIMP/install.sh` for automated verification and CI environments.
- [ ] Ensure installer safely backs up and updates both native GIMP 3.x and Flatpak installations.
- [x] Verify installation against the live system GIMP 3.2.6 configuration directory.

---

## Phase 2 — Photoshop Keybinding Audit & Alignment
- [x] Audit `PhotoGIMP/.config/GIMP/3.0/shortcutsrc` for action path compatibility with GIMP 3.2 action names.
- [x] Map and activate missing Photoshop shortcuts (Select All `Ctrl+A`, Select Invert `Ctrl+Shift+I`, Deselect `Ctrl+D`, Layer Duplicate `Ctrl+J`, Free Transform `Ctrl+T`, Undo `Ctrl+Z`, Redo `Ctrl+Shift+Z`, Levels `Ctrl+L`, Curves `Ctrl+M`, Hue/Saturation `Ctrl+U`).
- [x] Create automated syntax and shortcut validator `PhotoGIMP/scripts/verify_config.py` to prevent broken keybindings.

---

## Phase 3 — Single-Window Workspace & Theme UI Polish
- [x] Inspect and refine `sessionrc` dockable layout for GIMP 3.2 (Layers, Channels, Paths, Undo History, Tool Options) — added gimp-undo-history; enforce single-window-mode yes in gimprc.
- [x] Polish `theme.css` to match dark Photoshop UI styling and ensure GTK3 theme compatibility — removed hardcoded Flatpak /app/ paths; added portable dark overrides.
- [x] Verify splash screen installation (`splashes/`) and desktop application launcher integration (`.local/share/applications/org.gimp.GIMP.desktop`) — enabled native desktop/icon install and validated launcher entry.

---

## Phase 4 — Tool Options & Retouching Workflows
- [x] Audit tool configuration (`toolrc` and `tool-options/`) for Brush, Eraser, Healing Brush, Clone Stamp, Marquee, Lasso, Wand, and Transform tools.
- [x] Standardize default tool options to match Photoshop default tool behaviors (free-form crop, anti-aliasing, 32 tolerance for wand, feathering defaults).

---

## Phase 5 — Verification & Automated Quality Gate
- [x] Build automated configuration verification script (`PhotoGIMP/scripts/verify_config.py`).
- [x] Run headless GIMP validation (`gimp --no-interface --batch ...`) with the installed PhotoGIMP configuration.
- [ ] Document manual smoke testing steps for Linux desktop DEs (GNOME/KDE/XFCE).

---

## Task Execution Guidelines

- Work on exactly ONE bounded task per iteration.
- Never mark a task complete without empirical verification evidence.
- Commit verified changes to Git after each iteration.
