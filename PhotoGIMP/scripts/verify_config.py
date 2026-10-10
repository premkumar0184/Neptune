#!/usr/bin/env python3
"""
PhotoGIMP Configuration Validator

Validates S-expression syntax and verifies key Photoshop shortcut action mappings
and workspace configuration in PhotoGIMP configuration files.
"""

import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTOGIMP_DIR = os.path.dirname(SCRIPT_DIR)
CONFIG_DIR = os.path.join(PHOTOGIMP_DIR, ".config", "GIMP", "3.0")

# Essential Photoshop shortcuts that must be ACTIVE in shortcutsrc
REQUIRED_SHORTCUTS = {
    "select-all": "<Primary>a",
    "select-none": "<Primary>d",
    "select-invert": "<Primary><Shift>i",
    "layers-duplicate": "<Primary>j",
    "tools-unified-transform": "<Primary>t",
    "edit-fill-fg": "<Alt>BackSpace",
    "edit-fill-bg": "<Primary>BackSpace",
    "edit-undo": "<Primary>z",
    "edit-redo": "<Primary><Shift>z",
    "tools-levels": "<Primary>l",
    "tools-curves": "<Primary>m",
    "tools-hue-saturation": "<Primary>u",
    "tools-paintbrush": "b",
    "tools-eraser": "e",
    "tools-move": "v",
    "tools-rect-select": "m",
    "tools-free-select": "l",
    "tools-fuzzy-select": "w",
    "tools-crop": "c",
    "tools-heal": "j",
    "tools-clone": "s",
    "tools-text": "t",
    "tools-zoom": "z",
}

# Required Python 3 plugins extending GIMP 3.x with Photoshop workflows
REQUIRED_PLUGINS = {
    "frequency-separation": {
        "file": "frequency-separation.py",
        "procedures": ["python-fu-frequency-separation"],
        "description": "Frequency Separation (Texture & Color split)",
        "menu_prefix": "<Image>/Filters/Retouching",
    },
    "luminosity-masks": {
        "file": "luminosity-masks.py",
        "procedures": ["python-fu-luminosity-masks"],
        "description": "Luminosity Masks (9 tonal channels)",
        "menu_prefix": "<Image>/Select",
    },
    "dodge-burn-layer": {
        "file": "dodge-burn-layer.py",
        "procedures": ["python-fu-dodge-burn-layer"],
        "description": "Non-Destructive Dodge & Burn Layer (#808080 neutral gray)",
        "menu_prefix": "<Image>/Layer",
    },
    "high-pass-sharpen": {
        "file": "high-pass-sharpen.py",
        "procedures": ["python-fu-high-pass-sharpen"],
        "description": "High Pass Sharpening Helper (edge micro-contrast)",
        "menu_prefix": "<Image>/Filters",
    },
    "quick-export": {
        "file": "quick-export.py",
        "procedures": ["python-fu-quick-export", "python-fu-quick-export-png"],
        "description": "Quick Export Suite (1x/0.5x/2x PNG & JPEG)",
        "menu_prefix": "<Image>/File",
    },
    "vignette-lighting": {
        "file": "vignette-lighting.py",
        "procedures": ["python-fu-vignette-lighting"],
        "description": "Non-Destructive Vignette & Lens Lighting Layer",
        "menu_prefix": "<Image>/Filters/Light and Shadow",
    },
    "depth-blur": {
        "file": "depth-blur.py",
        "procedures": ["python-fu-depth-blur"],
        "description": "Depth of Field & Background Defocus Helper",
        "menu_prefix": "<Image>/Filters/Blur",
    },
    "shadow-highlight": {
        "file": "shadow-highlight.py",
        "procedures": ["python-fu-shadow-highlight"],
        "description": "Non-Destructive Shadows & Highlights Recovery",
        "menu_prefix": "<Image>/Colors",
    },
    "black-and-white": {
        "file": "black-and-white.py",
        "procedures": ["python-fu-black-and-white"],
        "description": "Professional Black & White Conversion & Toning",
        "menu_prefix": "<Image>/Colors",
    },
    "photo-filter": {
        "file": "photo-filter.py",
        "procedures": ["python-fu-photo-filter"],
        "description": "Photo Filter Optical Warming & Cooling Helper",
        "menu_prefix": "<Image>/Colors",
    },
    "vibrance": {
        "file": "vibrance.py",
        "procedures": ["python-fu-vibrance"],
        "description": "Non-Destructive Vibrance & Smart Saturation Helper",
        "menu_prefix": "<Image>/Colors",
    },
    "color-balance": {
        "file": "color-balance.py",
        "procedures": ["python-fu-color-balance"],
        "description": "Non-Destructive Color Balance & Tonal Grading Helper",
        "menu_prefix": "<Image>/Colors",
    },
    "gradient-map": {
        "file": "gradient-map.py",
        "procedures": ["python-fu-gradient-map"],
        "description": "Non-Destructive Gradient Map & Cinematic Color Grading Helper",
        "menu_prefix": "<Image>/Colors",
    },
    "channel-mixer": {
        "file": "channel-mixer.py",
        "procedures": ["python-fu-channel-mixer"],
        "description": "Non-Destructive Channel Mixer & Monochrome Infrared Helper",
        "menu_prefix": "<Image>/Colors",
    },
    "color-temperature": {
        "file": "color-temperature.py",
        "procedures": ["python-fu-color-temperature"],
        "description": "Non-Destructive Color Temperature & White Balance Helper",
        "menu_prefix": "<Image>/Colors",
    },
    "clarity-dehaze": {
        "file": "clarity-dehaze.py",
        "procedures": ["python-fu-clarity-dehaze"],
        "description": "Non-Destructive Clarity & Dehaze Helper",
        "menu_prefix": "<Image>/Colors",
    },
    "film-grain": {
        "file": "film-grain.py",
        "procedures": ["python-fu-film-grain"],
        "description": "Non-Destructive Film Grain & Analog Texture Helper",
        "menu_prefix": "<Image>/Filters/Noise",
    },
    "light-tone": {
        "file": "light-tone.py",
        "procedures": ["python-fu-light-tone"],
        "description": "Non-Destructive Light & Tonal Range Helper",
        "menu_prefix": "<Image>/Colors",
    },
    "duotone-effect": {
        "file": "duotone-effect.py",
        "procedures": ["python-fu-duotone-effect"],
        "description": "Non-Destructive Duotone & Tritone Print Effect Helper",
        "menu_prefix": "<Image>/Colors",
    },
    "diffuse-glow": {
        "file": "diffuse-glow.py",
        "procedures": ["python-fu-diffuse-glow"],
        "description": "Non-Destructive Diffuse Glow & Glamour Filter Helper",
        "menu_prefix": "<Image>/Filters/Light and Shadow",
    },
    "skin-smoothing": {
        "file": "skin-smoothing.py",
        "procedures": ["python-fu-skin-smoothing"],
        "description": "Non-Destructive Skin Smoothing & Portrait Beauty Retouching Helper",
        "menu_prefix": "<Image>/Filters/Retouching",
    },
    "selective-color-pop": {
        "file": "selective-color-pop.py",
        "procedures": ["python-fu-selective-color-pop"],
        "description": "Non-Destructive Selective Color & Background Desaturation Helper",
        "menu_prefix": "<Image>/Colors",
    },
    "photo-colorize": {
        "file": "photo-colorize.py",
        "procedures": ["python-fu-photo-colorize"],
        "description": "Non-Destructive Vintage Photo Restoration & Colorization Helper",
        "menu_prefix": "<Image>/Colors",
    },
    "jpeg-artifact-removal": {
        "file": "jpeg-artifact-removal.py",
        "procedures": ["python-fu-jpeg-artifact-removal"],
        "description": "Non-Destructive JPEG Artifacts Removal & Deblocking Helper",
        "menu_prefix": "<Image>/Filters/Enhance",
    },
    "charcoal-filter": {
        "file": "charcoal-filter.py",
        "procedures": ["python-fu-charcoal-filter"],
        "description": "Non-Destructive Charcoal & Fine-Art Sketch Helper",
        "menu_prefix": "<Image>/Filters/Artistic",
    },
    "woodcut-filter": {
        "file": "woodcut-filter.py",
        "procedures": ["python-fu-woodcut-filter"],
        "description": "Non-Destructive Woodcut & Linocut Printmaking Helper",
        "menu_prefix": "<Image>/Filters/Artistic",
    },
    "swirling-sky": {
        "file": "swirling-sky.py",
        "procedures": ["python-fu-swirling-sky"],
        "description": "Non-Destructive Swirling Night Sky & Twirl Distortion Helper",
        "menu_prefix": "<Image>/Filters/Distort",
    },
    "sky-replacement": {
        "file": "sky-replacement.py",
        "procedures": ["python-fu-sky-replacement"],
        "description": "Non-Destructive Sky Selection & Replacement Helper",
        "menu_prefix": "<Image>/Edit",
    },
    "select-subject": {
        "file": "select-subject.py",
        "procedures": ["python-fu-select-subject"],
        "description": "Non-Destructive Select Subject & Foreground Isolation Helper",
        "menu_prefix": "<Image>/Select",
    },
    "color-range": {
        "file": "color-range.py",
        "procedures": ["python-fu-color-range"],
        "description": "Non-Destructive Color Range Selection & Isolation Helper",
        "menu_prefix": "<Image>/Select",
    },
    "smart-sharpen": {
        "file": "smart-sharpen.py",
        "procedures": ["python-fu-smart-sharpen"],
        "description": "Non-Destructive Smart Sharpen & Optical Deconvolution Helper",
        "menu_prefix": "<Image>/Filters/Enhance",
    },
    "tilt-shift": {
        "file": "tilt-shift.py",
        "procedures": ["python-fu-tilt-shift"],
        "description": "Non-Destructive Tilt-Shift & Miniature Blur Helper",
        "menu_prefix": "<Image>/Filters/Blur",
    },
    "lens-distortion": {
        "file": "lens-distortion.py",
        "procedures": ["python-fu-lens-distortion"],
        "description": "Non-Destructive Lens Distortion & Perspective Correction Helper",
        "menu_prefix": "<Image>/Filters/Distort",
    },
    "glowing-edges": {
        "file": "glowing-edges.py",
        "procedures": ["python-fu-glowing-edges"],
        "description": "Non-Destructive Glowing Edges & Neon Stylize Filter Helper",
        "menu_prefix": "<Image>/Filters/Artistic",
    },
    "oil-paint": {
        "file": "oil-paint.py",
        "procedures": ["python-fu-oil-paint"],
        "description": "Non-Destructive Oil Paint & Fine Art Impasto Helper",
        "menu_prefix": "<Image>/Filters/Artistic",
    },
    "iris-blur": {
        "file": "iris-blur.py",
        "procedures": ["python-fu-iris-blur"],
        "description": "Non-Destructive Iris Blur & Vignette Bokeh Helper",
        "menu_prefix": "<Image>/Filters/Blur",
    },
    "hdr-toning": {
        "file": "hdr-toning.py",
        "procedures": ["python-fu-hdr-toning"],
        "description": "Non-Destructive HDR Toning & Tone Mapping Helper",
        "menu_prefix": "<Image>/Image/Adjustments",
    },
    "match-color": {
        "file": "match-color.py",
        "procedures": ["python-fu-match-color"],
        "description": "Non-Destructive Match Color & Perceptual Color Transfer Helper",
        "menu_prefix": "<Image>/Image/Adjustments",
    },
    "apply-image": {
        "file": "apply-image.py",
        "procedures": ["python-fu-apply-image"],
        "description": "Non-Destructive Apply Image & Channel Math Helper",
        "menu_prefix": "<Image>/Image",
    },
    "replace-color": {
        "file": "replace-color.py",
        "procedures": ["python-fu-replace-color"],
        "description": "Non-Destructive Replace Color & Targeted Object Recoloring Helper",
        "menu_prefix": "<Image>/Image/Adjustments",
    },
    "lens-blur": {
        "file": "lens-blur.py",
        "procedures": ["python-fu-lens-blur"],
        "description": "Non-Destructive Lens Blur & Optical Depth of Field Helper",
        "menu_prefix": "<Image>/Filters/Blur",
    },
    "texturizer": {
        "file": "texturizer.py",
        "procedures": ["python-fu-texturizer"],
        "description": "Non-Destructive Texturizer & Surface Canvas Helper",
        "menu_prefix": "<Image>/Filters/Artistic",
    },
    "guide-layout": {
        "file": "guide-layout.py",
        "procedures": ["python-fu-guide-layout", "python-fu-clear-guides"],
        "description": "Guide Layout & Compositional Alignment Helper",
        "menu_prefix": "<Image>/View",
    },
    "frame-animation": {
        "file": "frame-animation.py",
        "procedures": [
            "python-fu-frame-animation-setup",
            "python-fu-create-tween",
            "python-fu-pingpong-animation",
            "python-fu-remove-animation-tags",
        ],
        "description": "Frame Animation & Tweening Helper",
        "menu_prefix": "<Image>/Filters/Animation",
    },
    "seamless-pattern": {
        "file": "seamless-pattern.py",
        "procedures": [
            "python-fu-seamless-pattern",
            "python-fu-pattern-preview",
            "python-fu-pattern-fill",
        ],
        "description": "Seamless Pattern Generator & Tile Preview Helper",
        "menu_prefix": "<Image>/Filters/Map",
    },
    "stroke-layer": {
        "file": "stroke-layer.py",
        "procedures": [
            "python-fu-stroke-layer",
        ],
        "description": "Selection & Layer Stroke Helper",
        "menu_prefix": "<Image>/Edit",
    },
    "solid-color-fill": {
        "file": "solid-color-fill.py",
        "procedures": [
            "python-fu-solid-color-fill",
        ],
        "description": "Solid Color Fill Layer & Canvas Fill Helper",
        "menu_prefix": "<Image>/Layer",
    },
    "gradient-fill": {
        "file": "gradient-fill.py",
        "procedures": [
            "python-fu-gradient-fill",
        ],
        "description": "Gradient Fill Layer & Multi-Style Gradient Helper",
        "menu_prefix": "<Image>/Layer",
    },
    "exposure": {
        "file": "exposure.py",
        "procedures": [
            "python-fu-exposure",
        ],
        "description": "Exposure Adjustment Layer & Tonal Range Helper",
        "menu_prefix": "<Image>/Layer",
    },
    "drop-shadow": {
        "file": "drop-shadow.py",
        "procedures": [
            "python-fu-drop-shadow",
        ],
        "description": "Drop Shadow Layer Style Helper",
        "menu_prefix": "<Image>/Layer",
    },
    "calculations": {
        "file": "calculations.py",
        "procedures": [
            "python-fu-calculations",
        ],
        "description": "Channel Calculations & Two-Source Blending Helper",
        "menu_prefix": "<Image>/Image",
    },
    "outer-glow": {
        "file": "outer-glow.py",
        "procedures": [
            "python-fu-outer-glow",
        ],
        "description": "Outer Glow Layer Style Helper",
        "menu_prefix": "<Image>/Layer",
    },
    "pattern-fill": {
        "file": "pattern-fill.py",
        "procedures": [
            "python-fu-pattern-fill-layer",
        ],
        "description": "Pattern Fill Layer & Pattern Overlay Helper",
        "menu_prefix": "<Image>/Layer",
    },
    "inner-glow": {
        "file": "inner-glow.py",
        "procedures": [
            "python-fu-inner-glow",
        ],
        "description": "Inner Glow Layer Style Helper",
        "menu_prefix": "<Image>/Layer",
    },
    "inner-shadow": {
        "file": "inner-shadow.py",
        "procedures": [
            "python-fu-inner-shadow",
        ],
        "description": "Inner Shadow Layer Style Helper",
        "menu_prefix": "<Image>/Layer",
    },
    "color-overlay": {
        "file": "color-overlay.py",
        "procedures": [
            "python-fu-color-overlay",
        ],
        "description": "Color Overlay Layer Style Helper",
        "menu_prefix": "<Image>/Layer",
    },
    "gradient-overlay": {
        "file": "gradient-overlay.py",
        "procedures": [
            "python-fu-gradient-overlay",
        ],
        "description": "Gradient Overlay Layer Style Helper",
        "menu_prefix": "<Image>/Layer",
    },
    "pattern-overlay": {
        "file": "pattern-overlay.py",
        "procedures": [
            "python-fu-pattern-overlay",
        ],
        "description": "Pattern Overlay Layer Style Helper",
        "menu_prefix": "<Image>/Layer",
    },
    "satin": {
        "file": "satin.py",
        "procedures": [
            "python-fu-satin",
        ],
        "description": "Satin Layer Style Helper",
        "menu_prefix": "<Image>/Layer",
    },
    "bevel-emboss": {
        "file": "bevel-emboss.py",
        "procedures": [
            "python-fu-bevel-emboss",
        ],
        "description": "Bevel & Emboss Layer Style Helper",
        "menu_prefix": "<Image>/Layer",
    },
    "stroke-style": {
        "file": "stroke-style.py",
        "procedures": [
            "python-fu-stroke-style",
        ],
        "description": "Stroke Layer Style Helper",
        "menu_prefix": "<Image>/Layer",
    },
    "layer-style-manager": {
        "file": "layer-style-manager.py",
        "procedures": [
            "python-fu-global-light",
            "python-fu-scale-layer-effects",
            "python-fu-copy-layer-style",
            "python-fu-paste-layer-style",
            "python-fu-clear-layer-style",
        ],
        "description": "Global Lighting & Layer Style Manager Suite",
        "menu_prefix": "<Image>/Layer",
    },
    "knockout-blending": {
        "file": "knockout-blending.py",
        "procedures": [
            "python-fu-knockout-blending",
            "python-fu-clear-knockout",
        ],
        "description": "Knockout Blending & Texture Cutout Effects Helper",
        "menu_prefix": "<Image>/Layer",
    },
    "smart-filters": {
        "file": "smart-filters.py",
        "procedures": [
            "python-fu-convert-for-smart-filters",
            "python-fu-apply-smart-filter",
            "python-fu-edit-smart-filter",
            "python-fu-rasterize-smart-filters",
            "python-fu-clear-smart-filters",
        ],
        "description": "Smart Filters & Non-Destructive Filter Effects Helper",
        "menu_prefix": "<Image>/Filters",
    },
    "layer-comps": {
        "file": "layer-comps.py",
        "procedures": [
            "python-fu-create-layer-comp",
            "python-fu-apply-layer-comp",
            "python-fu-cycle-layer-comp",
            "python-fu-update-layer-comp",
            "python-fu-delete-layer-comp",
            "python-fu-export-layer-comps",
        ],
        "description": "Layer Comps & Composition Variations Manager",
        "menu_prefix": "<Image>/Layer",
    },
    "history-log": {
        "file": "history-log.py",
        "procedures": [
            "python-fu-set-history-log-prefs",
            "python-fu-record-history-entry",
            "python-fu-view-history-log",
            "python-fu-create-snapshot",
            "python-fu-apply-snapshot",
            "python-fu-new-document-from-snapshot",
            "python-fu-delete-snapshot",
        ],
        "description": "History States & Edit Session Audit Log",
        "menu_prefix": "<Image>/Edit",
    },
    "placeholder-frames": {
        "file": "placeholder-frames.py",
        "procedures": [
            "python-fu-create-frame",
            "python-fu-convert-to-frame",
            "python-fu-place-image-in-frame",
            "python-fu-set-frame-stroke",
            "python-fu-adjust-frame-content",
            "python-fu-release-frame",
        ],
        "description": "Placeholder Frames & Clipping Masks Layout Helper",
        "menu_prefix": "<Image>/Layer",
    },
    "image-stacks": {
        "file": "image-stacks.py",
        "procedures": [
            "python-fu-create-image-stack",
            "python-fu-set-stack-mode",
            "python-fu-render-image-stack",
            "python-fu-load-files-into-stack",
            "python-fu-statistics-stack",
            "python-fu-auto-align-stack",
            "python-fu-rasterize-image-stack",
        ],
        "description": "Image Stacks & Statistical Blending Helper",
        "menu_prefix": "<Image>/Layer",
    },
    "artboards": {
        "file": "artboards.py",
        "procedures": [
            "python-fu-create-artboard",
            "python-fu-artboard-from-layers",
            "python-fu-artboard-from-group",
            "python-fu-duplicate-artboard",
            "python-fu-resize-artboard",
            "python-fu-export-artboards",
        ],
        "description": "Artboards & Multi-Canvas Layout Manager",
        "menu_prefix": "<Image>/Layer",
    },
    "content-aware-scale": {
        "file": "content-aware-scale.py",
        "procedures": [
            "python-fu-content-aware-scale",
            "python-fu-content-aware-energy-map",
        ],
        "description": "Content-Aware Scale & Intelligent Seam Carving Helper",
        "menu_prefix": "<Image>/Edit",
    },
    "perspective-crop": {
        "file": "perspective-crop.py",
        "procedures": [
            "python-fu-perspective-crop",
            "python-fu-perspective-auto-quad",
        ],
        "description": "Perspective Crop & Keystone Rectification Helper",
        "menu_prefix": "<Image>/Tools/Transform Tools",
    },
    "straighten-crop": {
        "file": "straighten-crop.py",
        "procedures": [
            "python-fu-straighten-crop",
            "python-fu-measure-straighten-angle",
        ],
        "description": "Straighten & Content-Aware Crop Fill Helper",
        "menu_prefix": "<Image>/Tools/Transform Tools",
    },
    "transform-again": {
        "file": "transform-again.py",
        "procedures": [
            "python-fu-free-transform-duplicate",
            "python-fu-transform-again",
            "python-fu-transform-again-duplicate",
        ],
        "description": "Free Transform with Duplicate & Transform Again Suite",
        "menu_prefix": "<Image>/Edit",
    },
    "delete-fill-selection": {
        "file": "delete-fill-selection.py",
        "procedures": [
            "python-fu-delete-fill-selection",
            "python-fu-delete-fill-options",
        ],
        "description": "Delete and Fill Selection (Content-Aware Object Removal)",
        "menu_prefix": "<Image>/Edit",
    },
    "layer-matting": {
        "file": "layer-matting.py",
        "procedures": [
            "python-fu-matting-defringe",
            "python-fu-matting-remove-black-matte",
            "python-fu-matting-remove-white-matte",
            "python-fu-matting-color-decontaminate",
        ],
        "description": "Layer Matting & Edge Defringe Suite Helper",
        "menu_prefix": "<Image>/Layer/Matting",
    },
}




def validate_sexp_file(filepath):
    """Check parenthesis matching and basic syntax of an S-expression file."""
    if not os.path.isfile(filepath):
        return False, "File not found: {}".format(filepath)

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    depth = 0
    in_string = False
    escape = False
    line_no = 1

    for char in content:
        if char == "\n":
            line_no += 1
            escape = False
            continue

        if escape:
            escape = False
            continue

        if char == "\\" and in_string:
            escape = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if not in_string:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth < 0:
                    return False, "Unmatched closing parenthesis at line {} in {}".format(
                        line_no, os.path.basename(filepath))

    if depth != 0:
        return False, "Unclosed parenthesis (depth={}) in {}".format(depth, os.path.basename(filepath))

    return True, "Valid S-expression ({} lines)".format(line_no)


def parse_active_shortcuts(shortcutsrc_path):
    """Extract active (action "name" "key") entries from shortcutsrc."""
    active_shortcuts = {}
    with open(shortcutsrc_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line_str = line.strip()
            if line_str.startswith("#"):
                continue  # skip commented/inactive lines

            # Match (action "name" "shortcut") or (action "name")
            match = re.match(r'^\(\s*action\s+"([^"]+)"(?:\s+"([^"]+)")?\s*\)', line_str)
            if match:
                action_name = match.group(1)
                shortcut_key = match.group(2) if match.group(2) else ""
                active_shortcuts[action_name] = shortcut_key

    return active_shortcuts


def check_sessionrc_single_window(sessionrc_path):
    """Verify single-window-mode in GIMP 3.x sessionrc (gimp-single-image-window with open-on-exit)."""
    with open(sessionrc_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    if 'factory-entry "gimp-single-image-window"' in content and '(open-on-exit)' in content:
        return True, "sessionrc: (factory-entry \"gimp-single-image-window\") with (open-on-exit) is set"
    return False, "sessionrc: gimp-single-image-window open-on-exit missing -- single-window mode not configured"


def check_gimprc_clean(gimprc_path):
    """Verify gimprc does not contain obsolete GIMP 2.x tokens that cause fatal parse errors in GIMP 3.x."""
    with open(gimprc_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    if re.search(r'\(\s*single-window-mode', content):
        return False, "gimprc: Contains obsolete (single-window-mode) token -- causes GIMP 3.x fatal parse error"
    return True, "gimprc: Clean of obsolete tokens"


def check_sessionrc_undo_history(sessionrc_path):
    """Verify gimp-undo-history dockable is present in sessionrc."""
    with open(sessionrc_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    if "gimp-undo-history" in content:
        return True, "sessionrc: gimp-undo-history (History panel) dockable is present"
    return False, "sessionrc: gimp-undo-history dockable is missing -- Photoshop History panel not configured"


def check_theme_no_flatpak_paths(theme_path):
    """Verify theme.css has no hardcoded Flatpak /app/ paths."""
    with open(theme_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    flatpak_paths = re.findall(r'file:///app/', content)
    if not flatpak_paths:
        return True, "theme.css: No hardcoded Flatpak /app/ paths found"
    return False, "theme.css: Contains {} hardcoded Flatpak path(s) -- breaks native GIMP installs".format(
        len(flatpak_paths))


def check_theme_photocraft_tokens(theme_path):
    """Verify theme.css incorporates PhotoCraft Pro design tokens (Spectrum Dark, Blue accent, Pill buttons, precision sliders)."""
    with open(theme_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    required_elements = [
        ("@define-color fg-color", "foreground color token"),
        ("@define-color bg-color", "background color token"),
        ("@define-color selected-color", "selected highlight token"),
        ("#378ef0", "PhotoCraft Spectrum blue accent"),
        ("notebook header tabs tab", "modern tab strip styling"),
        ("button.suggested-action", "pill action button styling"),
        ("scale contents trough", "precision slider styling"),
    ]
    missing = [desc for pattern, desc in required_elements if pattern not in content]
    if not missing:
        return True, "theme.css: PhotoCraft Pro design tokens and modern styling verified"
    return False, "theme.css: Missing PhotoCraft design tokens: {}".format(", ".join(missing))


def main():
    print("PhotoGIMP Configuration Audit and Syntax Verification")
    print("======================================================")

    if not os.path.isdir(CONFIG_DIR):
        print("ERROR: Config directory not found: {}".format(CONFIG_DIR))
        sys.exit(1)

    config_files = ["gimprc", "sessionrc", "shortcutsrc", "toolrc", "contextrc"]
    errors = []

    # Section 1: S-expression syntax validation
    print("\n1. Syntax Validation:")
    for cfg in config_files:
        path = os.path.join(CONFIG_DIR, cfg)
        ok, msg = validate_sexp_file(path)
        status = "PASS" if ok else "FAIL"
        print("  [{}] {}: {}".format(status, cfg, msg))
        if not ok:
            errors.append(msg)

    # Section 2: Active Photoshop shortcut audit
    print("\n2. Active Photoshop Shortcut Audit:")
    shortcutsrc_path = os.path.join(CONFIG_DIR, "shortcutsrc")
    active_shortcuts = parse_active_shortcuts(shortcutsrc_path)

    missing_or_mismatched = []
    for action, expected_key in REQUIRED_SHORTCUTS.items():
        if action not in active_shortcuts:
            missing_or_mismatched.append(
                "Action '{}' is missing or commented out in shortcutsrc".format(action))
        elif active_shortcuts[action] != expected_key:
            actual_key = active_shortcuts[action]
            missing_or_mismatched.append(
                "Action '{}' mapped to '{}', expected '{}'".format(action, actual_key, expected_key))
        else:
            print("  [PASS] {} -> '{}'".format(action, expected_key))

    if missing_or_mismatched:
        print("\nShortcut Mismatches Found:")
        for item in missing_or_mismatched:
            print("  [FAIL] {}".format(item))
        errors.extend(missing_or_mismatched)
    else:
        print("\n  All required Photoshop shortcuts are active and correctly mapped!")

    # Section 3: Workspace configuration audit
    print("\n3. Workspace Configuration Audit:")

    workspace_checks = [
        (check_sessionrc_single_window, os.path.join(CONFIG_DIR, "sessionrc")),
        (check_gimprc_clean, os.path.join(CONFIG_DIR, "gimprc")),
        (check_sessionrc_undo_history, os.path.join(CONFIG_DIR, "sessionrc")),
        (check_theme_no_flatpak_paths, os.path.join(CONFIG_DIR, "theme.css")),
        (check_theme_photocraft_tokens, os.path.join(CONFIG_DIR, "theme.css")),
    ]

    for check_fn, path in workspace_checks:
        ok, msg = check_fn(path)
        status = "PASS" if ok else "FAIL"
        print("  [{}] {}".format(status, msg))
        if not ok:
            errors.append(msg)

    # Section 4: Desktop launcher audit
    print("\n4. Desktop Launcher Audit:")

    desktop_src = os.path.join(PHOTOGIMP_DIR, ".local", "share", "applications", "org.gimp.GIMP.desktop")
    if not os.path.isfile(desktop_src):
        msg = "Desktop file not found: {}".format(desktop_src)
        print("  [FAIL] {}".format(msg))
        errors.append(msg)
    else:
        with open(desktop_src, "r", encoding="utf-8", errors="replace") as f:
            desktop_content = f.read()

        # Check Exec does not use Flatpak-only invocation
        flatpak_exec = re.search(r'^Exec\s*=.*flatpak\s+run', desktop_content, re.MULTILINE)
        if flatpak_exec:
            msg = "desktop file Exec line still uses 'flatpak run' -- will not work on native GIMP"
            print("  [FAIL] {}".format(msg))
            errors.append(msg)
        else:
            exec_line = re.search(r'^Exec\s*=(.+)$', desktop_content, re.MULTILINE)
            exec_val = exec_line.group(1).strip() if exec_line else "(not found)"
            print("  [PASS] desktop file Exec is native-compatible: {}".format(exec_val))

        # Check TryExec is present for native validation
        if re.search(r'^TryExec\s*=', desktop_content, re.MULTILINE):
            print("  [PASS] desktop file has TryExec field")
        else:
            msg = "desktop file is missing TryExec -- launchers cannot validate binary availability"
            print("  [WARN] {}".format(msg))
            # Not a hard failure — just a warning

    # Check icon assets exist
    icons_src = os.path.join(PHOTOGIMP_DIR, ".local", "share", "icons")
    if os.path.isdir(icons_src):
        icon_count = sum(1 for _ in __import__('pathlib').Path(icons_src).rglob('*.png'))
        print("  [PASS] Icon assets present ({} PNG files in .local/share/icons/)".format(icon_count))
    else:
        msg = "Icon assets directory missing: {}".format(icons_src)
        print("  [FAIL] {}".format(msg))
        errors.append(msg)

    # Section 5: Tool Options Audit
    print("\n5. Tool Options Audit:")
    tool_opts_dir = os.path.join(CONFIG_DIR, "tool-options")
    if not os.path.isdir(tool_opts_dir):
        msg = "tool-options directory not found: {}".format(tool_opts_dir)
        print("  [FAIL] {}".format(msg))
        errors.append(msg)
    else:
        required_tool_options = [
            "gimp-rect-select-tool",
            "gimp-ellipse-select-tool",
            "gimp-free-select-tool",
            "gimp-fuzzy-select-tool",
            "gimp-by-color-select-tool",
            "gimp-crop-tool",
            "gimp-unified-transform-tool",
            "gimp-paintbrush-tool",
            "gimp-heal-tool",
            "gimp-clone-tool",
        ]
        tool_opt_errors = []
        for opt_file in os.listdir(tool_opts_dir):
            opt_path = os.path.join(tool_opts_dir, opt_file)
            if os.path.isfile(opt_path):
                ok, msg = validate_sexp_file(opt_path)
                if not ok:
                    tool_opt_errors.append("{}: {}".format(opt_file, msg))

        if tool_opt_errors:
            for toe in tool_opt_errors:
                print("  [FAIL] Syntax error in tool-options: {}".format(toe))
            errors.extend(tool_opt_errors)
        else:
            print("  [PASS] All {} files in tool-options have valid S-expression syntax".format(
                len(os.listdir(tool_opts_dir))))

        # Verify key selection tools are present
        missing_opts = [to for to in required_tool_options if not os.path.isfile(os.path.join(tool_opts_dir, to))]
        if missing_opts:
            msg = "Missing required tool options: {}".format(", ".join(missing_opts))
            print("  [FAIL] {}".format(msg))
            errors.append(msg)
        else:
            print("  [PASS] All required selection and retouching tool options exist")

        # Verify crop tool does not have hardcoded 1080/1920 aspect ratio
        crop_path = os.path.join(tool_opts_dir, "gimp-crop-tool")
        if os.path.isfile(crop_path):
            with open(crop_path, "r", encoding="utf-8", errors="replace") as f:
                crop_content = f.read()
            if "1080" in crop_content or "1920" in crop_content:
                msg = "gimp-crop-tool contains hardcoded 1080/1920 aspect ratio constraint"
                print("  [FAIL] {}".format(msg))
                errors.append(msg)
            else:
                print("  [PASS] gimp-crop-tool configured for free-form crop without forced aspect ratio")

        # Verify fuzzy select has standard tolerance 32
        fuzzy_path = os.path.join(tool_opts_dir, "gimp-fuzzy-select-tool")
        if os.path.isfile(fuzzy_path):
            with open(fuzzy_path, "r", encoding="utf-8", errors="replace") as f:
                fuzzy_content = f.read()
            if re.search(r'\(threshold\s+32(?:\.0)?\)', fuzzy_content):
                print("  [PASS] gimp-fuzzy-select-tool has Photoshop standard tolerance (threshold 32)")
            else:
                msg = "gimp-fuzzy-select-tool missing standard threshold 32"
                print("  [FAIL] {}".format(msg))
                errors.append(msg)

    # Section 6: Python 3 Plug-ins Audit
    print("\n6. Python 3 Plug-ins Audit:")
    plugins_dir = os.path.join(CONFIG_DIR, "plug-ins")
    if not os.path.isdir(plugins_dir):
        msg = "plug-ins directory missing: {}".format(plugins_dir)
        print("  [FAIL] {}".format(msg))
        errors.append(msg)
    else:
        import py_compile
        verified_plugins = 0

        # Audit each required plugin
        for plugin_name, info in REQUIRED_PLUGINS.items():
            plugin_subdir = os.path.join(plugins_dir, plugin_name)
            script_path = os.path.join(plugin_subdir, info["file"])

            if not os.path.isdir(plugin_subdir):
                msg = "Missing plugin subdirectory: plug-ins/{}".format(plugin_name)
                print("  [FAIL] {}".format(msg))
                errors.append(msg)
                continue

            if not os.path.isfile(script_path):
                msg = "Missing plugin script: plug-ins/{}/{}".format(plugin_name, info["file"])
                print("  [FAIL] {}".format(msg))
                errors.append(msg)
                continue

            # Check executable mode
            if not os.access(script_path, os.X_OK):
                msg = "Plugin is not executable: plug-ins/{}/{}".format(plugin_name, info["file"])
                print("  [FAIL] {}".format(msg))
                errors.append(msg)
                continue

            # Check Python compilation syntax
            try:
                py_compile.compile(script_path, doraise=True)
            except Exception as e:
                msg = "Syntax error in plug-ins/{}/{}: {}".format(plugin_name, info["file"], e)
                print("  [FAIL] {}".format(msg))
                errors.append(msg)
                continue

            # Check script contents for GIMP 3 API, procedure registrations, and shebang
            with open(script_path, "r", encoding="utf-8", errors="replace") as pf:
                script_body = pf.read()

            if not (script_body.startswith("#!/usr/bin/env python3") or script_body.startswith("#!/usr/bin/python3")):
                msg = "Plugin missing python3 shebang: plug-ins/{}/{}".format(plugin_name, info["file"])
                print("  [FAIL] {}".format(msg))
                errors.append(msg)
                continue

            if "gi.require_version('Gimp', '3.0')" not in script_body and 'gi.require_version("Gimp", "3.0")' not in script_body:
                msg = "Plugin missing Gimp 3.0 require_version: plug-ins/{}/{}".format(plugin_name, info["file"])
                print("  [FAIL] {}".format(msg))
                errors.append(msg)
                continue

            missing_procs = [p for p in info["procedures"] if p not in script_body]
            if missing_procs:
                msg = "Plugin {} missing procedure declarations: {}".format(plugin_name, ", ".join(missing_procs))
                print("  [FAIL] {}".format(msg))
                errors.append(msg)
                continue

            verified_plugins += 1
            print("  [PASS] {} ({} procedures: {})".format(
                plugin_name, len(info["procedures"]), ", ".join(info["procedures"])))

        # Also verify live user configuration directory (~/.config/GIMP/3.2/plug-ins) if present
        user_gimp_dir = os.path.expanduser("~/.config/GIMP/3.2/plug-ins")
        if os.path.isdir(user_gimp_dir):
            user_verified = 0
            for plugin_name, info in REQUIRED_PLUGINS.items():
                user_script = os.path.join(user_gimp_dir, plugin_name, info["file"])
                if os.path.isfile(user_script) and os.access(user_script, os.X_OK):
                    user_verified += 1
            print("  [PASS] Live user config ({}) has {}/{} required plugins deployed & executable".format(
                user_gimp_dir, user_verified, len(REQUIRED_PLUGINS)))
            if user_verified < len(REQUIRED_PLUGINS):
                msg = "Live config has only {}/{} required plugins installed".format(user_verified, len(REQUIRED_PLUGINS))
                print("  [FAIL] {}".format(msg))
                errors.append(msg)

        if verified_plugins == len(REQUIRED_PLUGINS):
            print("  [PASS] All {} required Photoshop workflow plugins verified!".format(len(REQUIRED_PLUGINS)))
        else:
            msg = "Expected {} plugins, but only {} passed verification".format(len(REQUIRED_PLUGINS), verified_plugins)
            print("  [FAIL] {}".format(msg))
            errors.append(msg)

    # Final result
    if errors:
        print("\nVerification FAILED with {} error(s).".format(len(errors)))
        sys.exit(1)
    else:
        print("\nVerification PASSED cleanly.")
        sys.exit(0)


if __name__ == "__main__":
    main()
