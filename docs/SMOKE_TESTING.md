# PhotoGIMP Linux Desktop Smoke Testing Guide

This document outlines manual smoke testing procedures to verify PhotoGIMP installation, desktop integration, Photoshop workspace alignment, shortcuts, and tool behaviors across standard Linux desktop environments (GNOME, KDE Plasma, XFCE).

---

## 1. Environment & Pre-requisites

- **Operating System**: Linux (Arch Linux, Ubuntu/Debian, Fedora)
- **GIMP Version**: GIMP 3.0+ or GIMP 3.2+
- **Desktop Environments**:
  - GNOME Shell (Wayland / X11)
  - KDE Plasma (Wayland / X11)
  - XFCE4 (X11)

---

## 2. Desktop Environment Integration Test

### Step 1: Application Launcher Presence
1. Open the application launcher (Super key on GNOME/KDE, Applications Menu on XFCE).
2. Search for `PhotoGIMP`.
3. **Expected Result**:
   - `PhotoGIMP` appears with the custom PhotoGIMP icon (not generic fallback gear/icon).
   - Category listed under Graphics / Image Editor.

### Step 2: Application Startup & Splash Screen
1. Launch `PhotoGIMP` from the application launcher.
2. **Expected Result**:
   - PhotoGIMP splash screen (`splash-screen-2025-v2.png`) displays during initialization.
   - GIMP launches into Single-Window Mode.

---

## 3. Workspace & Dockable Layout Smoke Test

### Step 1: Layout Inspection
1. Verify that the user interface layout matches the standard Photoshop workspace:
   - **Left**: Single vertical toolbox containing grouped tools.
   - **Right Top**: Dockable book with Tool Options, Brushes, Patterns, Gradients, and Fonts.
   - **Right Bottom**: Dockable book with Layers, Channels, Paths, and Undo History.
2. Confirm the dark theme styling is consistent across dockables and tool headers.

---

## 4. Photoshop Keyboard Shortcuts Smoke Test

Open an image (`File -> Open` or `Ctrl+O`) and verify primary hotkeys:

| Action | Photoshop Hotkey | Expected GIMP Behavior |
| :--- | :--- | :--- |
| **Move Tool** | `V` | Activates Move Tool (`gimp-tool-move`) |
| **Marquee Select** | `M` | Activates Rectangular / Elliptical Marquee (`gimp-tool-rect-select`) |
| **Lasso Tool** | `L` | Activates Freehand / Scissors Lasso (`gimp-tool-free-select`) |
| **Magic Wand** | `W` | Activates Fuzzy Select Tool (`gimp-tool-fuzzy-select`) |
| **Crop Tool** | `C` | Activates Crop Tool (`gimp-tool-crop`) |
| **Eyedropper** | `I` | Activates Color Picker Tool (`gimp-tool-color-picker`) |
| **Spot Healing** | `J` | Activates Heal Tool (`gimp-tool-heal`) |
| **Brush Tool** | `B` | Activates Paintbrush Tool (`gimp-tool-paintbrush`) |
| **Clone Stamp** | `S` | Activates Clone Tool (`gimp-tool-clone`) |
| **Eraser** | `E` | Activates Eraser Tool (`gimp-tool-eraser`) |
| **Paint Bucket** | `Shift+G` | Activates Bucket Fill Tool (`gimp-tool-bucket-fill`) |
| **Gradient** | `G` | Activates Gradient Tool (`gimp-tool-gradient`) |
| **Type Tool** | `T` | Activates Text Tool (`gimp-tool-text`) |
| **Zoom Tool** | `Z` | Activates Zoom Tool (`gimp-tool-zoom`) |
| **Select All** | `Ctrl+A` | Selects entire canvas boundary |
| **Deselect** | `Ctrl+D` | Clears active selection |
| **Invert Selection**| `Ctrl+Shift+I` | Inverts selection mask |
| **Duplicate Layer**| `Ctrl+J` | Duplicates active layer |
| **Free Transform** | `Ctrl+T` | Activates Unified Transform bounding box |
| **Levels Dialog** | `Ctrl+L` | Opens Color Levels adjustment window |
| **Curves Dialog** | `Ctrl+M` | Opens Color Curves adjustment window |
| **Hue/Saturation** | `Ctrl+U` | Opens Hue-Saturation adjustment window |
| **Fill FG Color** | `Alt+Backspace`| Fills selection or canvas with foreground color |
| **Fill BG Color** | `Ctrl+Backspace`| Fills selection or canvas with background color |
| **Undo** | `Ctrl+Z` | Undoes previous operation |
| **Redo** | `Ctrl+Shift+Z` | Redoes previous operation |

---

## 5. Tool Defaults Smoke Test

1. **Crop Tool**: Verify free-form crop behavior with Rule of Thirds guide overlay (no fixed 16:9 ratio lock).
2. **Magic Wand Tool**: Verify tolerance defaults to 32 with anti-aliasing enabled.
3. **Marquee & Lasso Tools**: Verify anti-aliasing is enabled by default with feathering set to 0.

---

## 6. Restoration & Rollback Test

1. Run `./PhotoGIMP/install.sh --help` to confirm CLI help usage.
2. Confirm timestamped backups are stored in `~/.config/GIMP/GIMP-backup-<timestamp>-<source>`.
3. To restore:
   ```bash
   cp -a ~/.config/GIMP/GIMP-backup-<timestamp>-<source>/<version>/. ~/.config/GIMP/<version>/
   ```
