# Photoshop Feature Matrix for Linux Photo Editor (GIMP 3.x / PhotoGIMP)

This document is the authoritative mapping between Adobe Photoshop features (from `Topics.txt` and `photoshop_docs.md`) and GIMP / PhotoGIMP equivalents, real capability gaps, and implementation status.

---

## 1. Professional Retouching & Workflow Extensions (Custom GIMP 3.x Plugins)

### Feature: Frequency Separation
- **Source topic**: Retouch and correct - Retouch and repair images / Frequency Separation
- **Photoshop behavior**: Splits an image into a Low Frequency layer (color and tone via Gaussian Blur) and a High Frequency layer (fine texture via High Pass or Subtract math with Linear Light blend mode). Allows independent retouching of skin blemishes/textures without altering skin tone, and blending colors without smoothing pores.
- **GIMP equivalent**: Implemented via custom Python 3 plugin `python-fu-frequency-separation` in `<Image>/Filters/Retouching/Frequency Separation...`.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/frequency-separation/frequency-separation.py`.
- **Current capability**: Automated one-click creation of `Frequency Separation` layer group containing `Low Frequency (Color & Tone)` (Gaussian blur) and `High Frequency (Texture)` (High-pass with Grain Merge blend mode).
- **Gap**: None.
- **Dependencies**: Python 3 (`gi.repository.Gimp`, `gi.repository.Gegl`).
- **Implementation priority**: High (Phase 6).
- **Verification strategy**: `verify_config.py` plugin check + automated headless GIMP test creating Low/High frequency layer group on test image and asserting layer structure.
- **Status**: Implemented & Verified (Iteration 8).

---

### Feature: Luminosity Masks Generator
- **Source topic**: Make selections - Select areas based on color or tone / Channels panel
- **Photoshop behavior**: Generates 9 precision channel masks (Lights 1-3, Darks 1-3, Midtones 1-3) based on pixel luminance, allowing targeted exposure and tonal adjustments without manual edge painting.
- **GIMP equivalent**: Implemented via custom Python 3 plugin `python-fu-luminosity-masks` in `<Image>/Select/Luminosity Masks...`.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/luminosity-masks/luminosity-masks.py`.
- **Current capability**: Automated one-click generation of all 9 tonal channels: Lights 1/2/3, Darks 1/2/3, Midtones 1/2/3. Each channel uses iterative GEGL buffer copy + selection-intersection narrowing for progressively focused tonal ranges.
- **Gap**: None.
- **Dependencies**: Python 3 (`gi.repository.Gimp`, `gi.repository.Gegl`), `Gimp.Layer.new_from_drawable`, `Gimp.Channel.combine_masks`.
- **Implementation priority**: High (Phase 7).
- **Verification strategy**: Headless GIMP test confirms 9 channels created with correct names and verifies pixel luminance mathematics on test splits (exit 0).
- **Verification evidence** (Iteration 9):
  1. Headless Script-Fu: `gimp --no-interface --batch '...' --quit` → `Channel count: 9 / Midtones 3 / Midtones 2 / Midtones 1 / Darks 3 / Darks 2 / Darks 1 / Lights 3 / Lights 2 / Lights 1 / batch command executed successfully` (exit code 0).
  2. Objective pixel behavioral assertion: `gimp --no-interface --batch-interpreter=python-fu-eval` sampled pixel RGB values on split white/black test canvas: `Lights 1` white side = 1.000, black side = 0.000; `Darks 1` white side = 0.000, black side = 1.000 (exit code 0).
- **Status**: IMPLEMENTED_VERIFIED (Iteration 9).

---

### Feature: Non-Destructive Dodge & Burn Layer
- **Source topic**: Retouch and correct - Dodge and burn image areas
- **Photoshop behavior**: Creates a 50% neutral gray layer in Overlay or Soft Light blend mode, allowing non-destructive exposure painting with black/white brush without directly modifying source pixels.
- **GIMP equivalent**: Implemented via custom Python 3 plugin `python-fu-dodge-burn-layer` in `<Image>/Layer/New Dodge & Burn Layer...` and `<Image>/Filters/Retouching/Dodge & Burn Layer...`.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/dodge-burn-layer/dodge-burn-layer.py`.
- **Current capability**: One-click creation of 50% neutral gray overlay layer with interactive dialog for blend mode choice (Soft Light subtle vs Overlay high contrast), layer name, and opacity; prepares White/Black brush colors and selects layer for immediate painting.
- **Gap**: None.
- **Dependencies**: Python 3 (`gi.repository.Gimp`, `gi.repository.Gegl`).
- **Implementation priority**: Medium (Phase 8).
- **Verification strategy**: Automated headless GIMP test verifying PDB registration, layer creation, neutral gray fill (`#808080`), 0.000000 composite difference (perfect neutrality), and pixel brightening/darkening when painting.
- **Verification evidence** (Iteration 10):
  1. `verify_config.py`: Section 6 passed with 3 active Python plugins.
  2. Objective pixel behavioral test: `gimp --no-interface --batch-interpreter=python-fu-eval`: Soft Light neutrality diff = 0.000000, Overlay neutrality diff = 0.000000; dodged luminance = 0.871 (base 0.352), burned luminance = 0.112 (base 0.352). Exit code 0.
- **Status**: IMPLEMENTED_VERIFIED (Iteration 10).

---

### Feature: High Pass Sharpening Helper
- **Source topic**: Adjust image color and tone - Sharpening and noise reduction
- **Photoshop behavior**: High Pass filter applied to duplicate layer in Overlay/Soft Light mode to sharpen micro-contrast and edges without halo artifacts.
- **GIMP equivalent**: `gegl:high-pass` filter exists in GIMP 3.x, but requires manual layer duplicate, filter application, and blend mode switch.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/high-pass-sharpen/high_pass_sharpen.py`.
- **Current capability**: Manual GEGL filter application.
- **Gap**: Dedicated one-click sharpening layer setup with live radius slider.
- **Dependencies**: GEGL `gegl:high-pass`, Python 3.
- **Implementation priority**: Medium (Phase 9).
- **Verification strategy**: Headless GIMP test asserting sharpened layer creation.
- **Status**: Planned.

---

### Feature: Quick Export (Web & Social Formats)
- **Source topic**: Save and export images - Export images in multiple formats
- **Photoshop behavior**: Quick Export as PNG / JPEG / WebP with scaling presets (1x, 2x, 0.5x) and automatic metadata stripping.
- **GIMP equivalent**: Standard File -> Export As dialog requiring manual format and parameter selection every time.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/quick-export/quick_export.py`.
- **Current capability**: Standard GIMP file export dialogs.
- **Gap**: Fast one-click export to PNG/JPEG with automatic naming in document directory.
- **Dependencies**: Python 3 GIMP file export procedures (`gimp-file-save` / `file-png-save`).
- **Implementation priority**: Medium (Phase 10).
- **Verification strategy**: Headless GIMP test exporting test canvas to PNG/JPEG and verifying output file validity.
- **Status**: Planned.

---

## 2. Core Editing & Adjustment Infrastructure (Native GIMP 3.x Built-ins)

### Feature: Curves, Levels & Color Adjustments
- **Source topic**: Adjust image color and tone - Correct color balance
- **Photoshop behavior**: Levels (`Ctrl+L`), Curves (`Ctrl+M`), Hue/Saturation (`Ctrl+U`), Color Balance.
- **GIMP equivalent**: `gimp-curves-tool`, `gimp-levels-tool`, `gimp-hue-saturation-tool`, `gimp-color-balance-tool`.
- **Status**: Native equivalent; shortcuts mapped in PhotoGIMP `shortcutsrc`.

### Feature: Layer Masks & Blending Modes
- **Source topic**: Create and manage layers - Work with layer masks / Blend modes
- **Photoshop behavior**: Layer masks, clipping masks, standard blend modes (Multiply, Screen, Overlay, Soft Light, Linear Light, Color, Luminosity).
- **GIMP equivalent**: GIMP 3.x supports 38 GEGL layer blend modes and full layer mask support (white, black, alpha, selection).
- **Status**: Native equivalent.

### Feature: Selections & Quick Mask
- **Source topic**: Make selections - Select areas with selection tools / Quick Mask
- **Photoshop behavior**: Marquee (`M`), Lasso (`L`), Magic Wand (`W`), Quick Mask (`Q`).
- **GIMP equivalent**: Rect/Ellipse Select, Free Select, Fuzzy Select, Quick Mask toggle (`Shift+Q` / `Q`).
- **Status**: Native equivalent; tool options presets standardized in `tool-options/`.

---

## 3. Configuration & Desktop Integration Overlay

### Feature: Single-Window Photoshop Workspace & Theme
- **Photoshop behavior**: Single-window dockable layout with dark theme.
- **Status**: Configured via `sessionrc`, `gimprc`, `theme.css`, `install.sh`, and `verify_config.py`.
