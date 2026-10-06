# Photoshop Feature Matrix for GIMP / PhotoGIMP

This document is the authoritative mapping between Adobe Photoshop features (from `Topics.txt` and `photoshop_docs.md`) and their GIMP / PhotoGIMP equivalents, capabilities, gaps, and implementation status.

---

## 1. Workspace & Navigation

### Feature: Custom Workspace & Panel Layout
- **Source topic**: Get started - Workspace overview / Save custom workspaces / Rearrange document windows
- **Photoshop behavior**: Single-window dockable panels (Layers, Channels, Paths, History, Properties, Tools) with customizable layouts, toolbars, and saved workspace presets.
- **GIMP equivalent**: Single-Window Mode with GIMP dockables (`sessionrc`). PhotoGIMP provides a pre-configured `sessionrc` that replicates the standard Photoshop single-window workspace layout (Tools on left, Layers/Channels/Paths/History on right).
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/sessionrc`, `PhotoGIMP/.config/GIMP/3.0/gimprc`, GTK3 layout.
- **Current capability**: Single-window layout with dockable dialogs matching Photoshop UI structure.
- **Gap**: Minor layout quirks when migrating between GIMP 3.0 and GIMP 3.2 config directories; missing automated version path detection in installer for 3.2.
- **Dependencies**: GTK3, GIMP 3.x session manager.
- **Implementation priority**: High (Phase 1).
- **Verification strategy**: Verify `sessionrc` parsing, launch GIMP with configuration, inspect panel placement.
- **Status**: Implemented / Needs 3.2 compatibility polish.

---

### Feature: Keyboard Shortcuts (Photoshop Preset)
- **Source topic**: Get started - View keyboard shortcuts / Use spring-loaded shortcuts
- **Photoshop behavior**: Standard Photoshop hotkeys (V for Move, M for Marquee, L for Lasso, W for Magic Wand, B for Brush, E for Eraser, Ctrl+T for Free Transform, Ctrl+J for Duplicate Layer, Ctrl+Shift+I for Invert Selection, etc.).
- **GIMP equivalent**: GIMP keybinding system (`shortcutsrc`). PhotoGIMP provides a complete `shortcutsrc` file mapping Photoshop standard hotkeys to GIMP menu commands and tools.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/shortcutsrc`.
- **Current capability**: Mapped Photoshop shortcuts for primary tools and commands.
- **Gap**: Some shortcuts require updating for GIMP 3.2 menu command renames/paths.
- **Dependencies**: GIMP Action System.
- **Implementation priority**: High (Phase 1).
- **Verification strategy**: Validate `shortcutsrc` key action lines against GIMP 3.2 action definitions.
- **Status**: Implemented / Polish pending.

---

## 2. Selection Tools

### Feature: Rectangular & Elliptical Marquee Selections
- **Source topic**: Make selections - Make selections with the Marquee tools
- **Photoshop behavior**: Rectangular and Elliptical selection tools with feathering, anti-aliasing, fixed aspect ratio/size modes, add/subtract/intersect modes.
- **GIMP equivalent**: `gimp-tool-rect-select`, `gimp-tool-ellipse-select`.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/toolrc`, `tool-options/gimp-rect-select-tool`, `tool-options/gimp-ellipse-select-tool`.
- **Current capability**: Full support with feathering, aspect ratio constraints, and standard operation modes.
- **Gap**: Tool icons and default spring-loaded shortcuts in PhotoGIMP shortcut map.
- **Dependencies**: GIMP Core selection engine.
- **Implementation priority**: High (Phase 2).
- **Verification strategy**: Test selection creation, feathering, and shortcut triggers (M / Shift+M).
- **Status**: Equivalent.

---

### Feature: Lasso, Polygonal Lasso & Magnetic Lasso
- **Source topic**: Make selections - Isolate image areas with Lasso tools
- **Photoshop behavior**: Freehand Lasso, click-to-click Polygonal Lasso, and edge-snapping Magnetic Lasso.
- **GIMP equivalent**: Free Select Tool (`gimp-tool-free-select`) and Scissors Select Tool (`gimp-tool-iscissors`).
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/toolrc`.
- **Current capability**: Freehand, polygonal, and edge-detecting selection capabilities.
- **Gap**: Magnetic Lasso snapping parameters differ slightly from Photoshop default tension/frequency.
- **Dependencies**: GEGL contour detection.
- **Implementation priority**: Medium (Phase 2).
- **Verification strategy**: Verify tool activation with shortcut 'L'.
- **Status**: Equivalent.

---

### Feature: Magic Wand & Quick Selection Tool
- **Source topic**: Make selections - Select areas by color with the Magic Wand tool / Quick Selection tool
- **Photoshop behavior**: Magic Wand selects contiguous/non-contiguous pixels by color tolerance. Quick Selection paints to select regions automatically based on edge detection.
- **GIMP equivalent**: Fuzzy Select Tool (`gimp-tool-fuzzy-select`) and Select by Color Tool (`gimp-tool-by-color-select`).
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/toolrc`, `tool-options/gimp-fuzzy-select-tool`.
- **Current capability**: Color tolerance selection, contiguous selection, feathering, draw-to-expand selection.
- **Gap**: Quick Selection brush-based selection algorithm differs from Photoshop's texture-aware brush selection; GIMP uses Paint Select tool in 3.0+.
- **Dependencies**: GIMP Paint Select tool.
- **Implementation priority**: Medium (Phase 2).
- **Verification strategy**: Test selection thresholds and shortcut mappings ('W').
- **Status**: Partially Equivalent.

---

## 3. Layer Architecture & Operations

### Feature: Layer Stack & Groups
- **Source topic**: Create and manage layers - Layers overview / Organize layers with layer groups
- **Photoshop behavior**: Hierarchical layer stack with layer folders/groups, visibility toggle, locking (pixels, position, transparency), opacity, and blending modes.
- **GIMP equivalent**: GIMP Layer Tree & Layer Groups (`gimp-layer-group`).
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/sessionrc` (Layers dockable).
- **Current capability**: Full group nesting, layer visibility, opacity, pixel/alpha lock, and layer reordering.
- **Gap**: Group blending modes (Pass Through) behavior aligned in GIMP 2.10/3.x.
- **Dependencies**: GIMP Core layer model.
- **Implementation priority**: High (Phase 3).
- **Verification strategy**: Verify group creation, layer drag-and-drop, and opacity control.
- **Status**: Equivalent.

---

### Feature: Blending Modes
- **Source topic**: Create and manage layers - Set layer opacity and blending modes
- **Photoshop behavior**: Normal, Dissolve, Darken, Multiply, Color Burn, Linear Burn, Darker Color, Lighten, Screen, Color Dodge, Linear Dodge (Add), Lighter Color, Overlay, Soft Light, Hard Light, Vivid Light, Linear Light, Pin Light, Hard Mix, Difference, Exclusion, Subtract, Divide, Hue, Saturation, Color, Luminosity.
- **GIMP equivalent**: GIMP Blending Modes (Normal, Dissolve, Multiply, Screen, Overlay, Darken, Lighten, Color Dodge, Color Burn, Hard Light, Soft Light, Difference, Addition, Subtract, Grain Extract, Grain Merge, Hue, Chroma, Color, Lightness, etc.).
- **GIMP source locations**: GEGL blend modes, GIMP core image stack.
- **Current capability**: GIMP 2.10/3.0+ supports linear and perceptual space blending modes matching Photoshop.
- **Gap**: UI naming discrepancies in mode dropdown mapped via PhotoGIMP localization where applicable.
- **Dependencies**: GEGL.
- **Implementation priority**: High (Phase 3).
- **Verification strategy**: Compare blended output between GIMP blend modes and Photoshop spec.
- **Status**: Equivalent.

---

### Feature: Adjustment Layers & Fill Layers
- **Source topic**: Create and manage layers - Adjustment and fill layers overview
- **Photoshop behavior**: Non-destructive adjustment layers (Levels, Curves, Hue/Saturation, etc.) affecting all layers below in stack.
- **GIMP equivalent**: GEGL non-destructive filter attachments on layers / layer groups (GIMP 3.0+ non-destructive editing framework).
- **GIMP source locations**: GIMP 3.x non-destructive filter system.
- **Current capability**: Non-destructive GEGL filters on layers.
- **Gap**: Standalone dedicated adjustment layer creation dialog workflow mapped to GEGL layer filters.
- **Dependencies**: GEGL non-destructive graph.
- **Implementation priority**: Medium (Phase 3).
- **Verification strategy**: Add GEGL filter to layer group and modify parameters dynamically.
- **Status**: Partially Equivalent.

---

## 4. Painting & Editing Tools

### Feature: Brush Tool & Tool Presets
- **Source topic**: Set up toolbars and panels - Create tool presets / Paint and colorize - Brush tool
- **Photoshop behavior**: Customizable brushes with size, hardness, opacity, flow, smooth stroke (smoothing), brush dynamics (pressure sensitivity, tilt), brush presets library.
- **GIMP equivalent**: Paintbrush Tool (`gimp-tool-paintbrush`) with Dynamics engine and Tool Presets.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/toolrc`, `tool-options/gimp-paintbrush-tool`.
- **Current capability**: Pressure sensitivity, smooth stroke, flow, opacity, customizable brush tips.
- **Gap**: Brush preset naming and organizational layout in PhotoGIMP presets.
- **Dependencies**: GIMP Paint Core.
- **Implementation priority**: High (Phase 4).
- **Verification strategy**: Test brush drawing, size/hardness hotkeys ('[' and ']'), and 'B' shortcut.
- **Status**: Equivalent.

---

### Feature: Eraser, Spot Healing, Healing Brush & Clone Stamp
- **Source topic**: Retouch and repair - Spot Healing Brush / Healing Brush / Clone Stamp Tool
- **Photoshop behavior**:
  - Spot Healing: Automatic texture synthesis for spot removal.
  - Healing Brush: Sample source texture and blend color with destination lighting.
  - Clone Stamp: Exact pixel sampling from source coordinate to target.
- **GIMP equivalent**: Heal Tool (`gimp-tool-heal`) and Clone Tool (`gimp-tool-clone`).
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/toolrc`, `tool-options/gimp-heal-tool`, `tool-options/gimp-clone-tool`.
- **Current capability**: Healing brush (texture blending sample) and Clone stamp (Ctrl+click source sampling).
- **Gap**: Seamless content-aware single-click spot healing without sampling point setup (Resynthesizer / GEGL heal plugin).
- **Dependencies**: GIMP Heal engine.
- **Implementation priority**: High (Phase 5).
- **Verification strategy**: Test source setting with Ctrl+click and sample cloning/healing.
- **Status**: Mapped / Equivalent.

---

## 5. Transform Tools

### Feature: Free Transform & Unified Transform
- **Source topic**: Crop, resize, and transform - Transform images, shapes, and paths / Adjust scale, rotation, and perspective
- **Photoshop behavior**: Free Transform (Ctrl+T) supporting scaling, rotation, skewing, perspective distortion, shear, and reference point manipulation in a single bounding box.
- **GIMP equivalent**: Unified Transform Tool (`gimp-tool-unified-transform`).
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/shortcutsrc` (Ctrl+T mapped to `gimp-tool-unified-transform`), `tool-options/gimp-unified-transform-tool`.
- **Current capability**: All transform operations (scale, rotate, shear, perspective) combined into one interaction handle box.
- **Gap**: PhotoGIMP maps Ctrl+T to Unified Transform tool cleanly.
- **Dependencies**: GEGL Transform matrices.
- **Implementation priority**: High (Phase 6).
- **Verification strategy**: Trigger Ctrl+T, manipulate handles, confirm transformation application.
- **Status**: Equivalent.

---

### Feature: Crop Tool & Straighten
- **Source topic**: Crop, resize, and transform - Crop photos / Crop tool options / Straighten tilted photos
- **Photoshop behavior**: Non-destructive and destructive canvas crop with overlay grids (Rule of thirds, Golden ratio), aspect ratio lock, straighten horizon line tool, and Content-Aware Fill expansion.
- **GIMP equivalent**: Crop Tool (`gimp-tool-crop`).
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/toolrc`, `tool-options/gimp-crop-tool`.
- **Current capability**: Interactive canvas crop, aspect ratio presets, rule-of-thirds grid guides.
- **Gap**: Content-aware fill expansion on crop boundary expansion requires GEGL fill / resynthesizer.
- **Dependencies**: GIMP Core Crop.
- **Implementation priority**: Medium (Phase 6).
- **Verification strategy**: Test shortcut 'C', set aspect ratio, verify crop execution.
- **Status**: Equivalent.

---

## 6. Color & Tonal Adjustments

### Feature: Levels & Curves
- **Source topic**: Adjust color and tone - Correct color balance / Curves / Levels
- **Photoshop behavior**: Channel-by-channel histogram editing (RGB, Red, Green, Blue) with input/output sliders, eyedropper sampling for black/white/gray points, and curve control points.
- **GIMP equivalent**: GIMP Levels Tool (`gimp-tool-levels`) and Curves Tool (`gimp-tool-curves`).
- **GIMP source locations**: GIMP GEGL operations, `shortcutsrc` (Ctrl+L for Levels, Ctrl+M for Curves).
- **Current capability**: Full 16/32-bit channel levels and curves adjustments with black/gray/white eyedroppers.
- **Gap**: Mapped in `shortcutsrc` (Ctrl+L and Ctrl+M).
- **Dependencies**: GEGL Color operations.
- **Implementation priority**: High (Phase 7).
- **Verification strategy**: Open Levels/Curves dialogs with Ctrl+L / Ctrl+M, modify curve, apply to image layer.
- **Status**: Equivalent.

---

### Feature: Hue/Saturation & Color Balance
- **Source topic**: Adjust color and tone - Hue/Saturation / Color Balance
- **Photoshop behavior**: Hue, Saturation, Lightness sliders with targeted color range selection (Master, Reds, Yellows, Greens, Cyans, Blues, Magentas). Color Balance with Shadows, Midtones, Highlights adjustments for Cyan/Red, Magenta/Green, Yellow/Blue.
- **GIMP equivalent**: GIMP Hue-Saturation Tool (`gimp-tool-hue-saturation`) and Color Balance Tool (`gimp-tool-color-balance`).
- **GIMP source locations**: GEGL color operations, `shortcutsrc` (Ctrl+U for Hue/Saturation, Ctrl+B for Color Balance).
- **Current capability**: Multi-channel hue/saturation adjustment, tonal range color balancing.
- **Gap**: PhotoGIMP shortcuts map Ctrl+U and Ctrl+B cleanly.
- **Dependencies**: GEGL.
- **Implementation priority**: High (Phase 7).
- **Verification strategy**: Test Ctrl+U and Ctrl+B shortcuts and tonal modifications.
- **Status**: Equivalent.

---

## 7. Linux UX & Packaging

### Feature: PhotoGIMP Linux Installer & GIMP 3.2 Compatibility
- **Source topic**: Get started - Desktop integration / Installation
- **Photoshop behavior**: Streamlined desktop entry, icon theme, splash screen, and single installer package.
- **GIMP equivalent**: `PhotoGIMP/install.sh` shell installer script and desktop integration assets (`.local/share/applications/org.gimp.GIMP.desktop`, `.local/share/icons/`).
- **GIMP source locations**: `PhotoGIMP/install.sh`, `PhotoGIMP/.config/GIMP/3.0/`, `PhotoGIMP/.local/`.
- **Current capability**: Installs PhotoGIMP configs to `~/.config/GIMP/3.0`.
- **Gap**: Arch Linux & current distributions ship GIMP 3.2.x, which uses `~/.config/GIMP/3.2/` instead of `~/.config/GIMP/3.0/`. The current `install.sh` only targets `3.0` and fails on GIMP 3.2 native installations without manual folder creation/linking.
- **Dependencies**: Bash, GIMP 3.x config layout.
- **Implementation priority**: High (Phase 1).
- **Verification strategy**: Run installer check against GIMP 3.2.6 installation, verify config directory targeting and successful installation.
- **Status**: High-priority gap / Fix required.
