#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Bevel & Emboss Layer Style Helper Plugin
==================================================================
Simulates Adobe Photoshop's non-destructive Bevel & Emboss layer style:
  - Photoshop Menu: Layer > Layer Style > Bevel & Emboss...
  - Photoshop Menu: Filters > Light and Shadow > Bevel and Emboss (Layer Style)...
  - Photoshop Docs: Section 113-115 lines 3433-3610 (Layer Style effects and options)
  - Topics.txt: Lines 107-118, 432

Photoshop Bevel & Emboss Architecture:
  1. Structure & Geometry:
     - Style:
       * Inner Bevel: Bevel ramp strictly inside target layer boundaries.
       * Outer Bevel: Bevel ramp strictly outside target layer boundaries.
       * Emboss: Bevel ramp straddling boundary seam across both inside and outside.
       * Pillow Emboss: Inverted boundary profile (concave ridge inside, convex outside).
     - Technique:
       * Smooth: Smooth continuous gradient slope falloff.
       * Chisel Hard: Sharp multi-faceted planar chisel ridges.
       * Chisel Soft: Chiseled slopes with gentle apex ridge softening.
     - Depth: Slope steepness multiplier (1.0% to 1000.0%, default 100.0%).
     - Direction:
       * Up (default): Convex / raised 3D surface relief.
       * Down: Concave / carved / recessed 3D surface relief.
     - Size: Width / radius of the bevel ramp (0.0 to 250.0px, default 5.0px).
     - Soften: Edge blur smoothing radius (0.0 to 16.0px, default 0.0px).
  2. Shading & Spherical Directional Illumination:
     - Angle: Azimuth light direction in degrees (-180.0° to 180.0°, default 120.0°).
     - Altitude: Elevation angle above the surface (0.0° to 90.0°, default 30.0°).
     - Surface Normal: Computed via central differences of height field H(x, y).
     - Directional Dot Product: dot = (-gx * lx - gy * ly) / ||N||.
       * Positive dot -> Highlight (facing incident light).
       * Negative dot -> Shadow (facing away from light).
       * Flat interior / exterior -> 0.0 (exact identity neutrality).
     - Gloss Contour:
       * Linear: Direct diffuse illumination response.
       * Curved: Non-linear specular luster curve enhancing metallic / gloss polish.
  3. Separate Highlight & Shadow Passes:
     - Highlight: Screen, Normal, Overlay, Soft Light, Linear Dodge (default Screen 75% white).
     - Shadow: Multiply, Normal, Darken, Color Burn, Linear Burn (default Multiply 75% black).
  4. Non-Destructive Container Architecture:
     - Dedicated container group "(Bevel & Emboss)" inserted immediately above target layer.
     - Contains independent Highlight and Shadow layers.
     - Target layer artwork and underlying canvas pixels remain 100% untouched (diff == 0.000000).
     - Single-step Ctrl+Z undo protection.
"""

import math
import sys
import numpy as np
import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
from gi.repository import GLib


PROC_NAME = "python-fu-bevel-emboss"

HL_BLEND_MODES = {
    "screen": Gimp.LayerMode.SCREEN,
    "normal": Gimp.LayerMode.NORMAL,
    "overlay": Gimp.LayerMode.OVERLAY,
    "soft-light": Gimp.LayerMode.SOFTLIGHT,
    "linear-dodge": Gimp.LayerMode.ADDITION,
}

SH_BLEND_MODES = {
    "multiply": Gimp.LayerMode.MULTIPLY,
    "normal": Gimp.LayerMode.NORMAL,
    "darken": Gimp.LayerMode.DARKEN_ONLY,
    "color-burn": Gimp.LayerMode.BURN,
    "linear-burn": Gimp.LayerMode.LINEAR_BURN,
}

PRESETS = {
    "classic-inner-bevel": {
        "label": "Classic Inner Bevel",
        "style": "inner-bevel",
        "technique": "smooth",
        "depth": 100.0,
        "direction": "up",
        "size": 5.0,
        "soften": 0.0,
        "angle": 120.0,
        "altitude": 30.0,
        "gloss": "linear",
        "hl_mode": "screen", "hl_r": 1.0, "hl_g": 1.0, "hl_b": 1.0, "hl_op": 75.0,
        "sh_mode": "multiply", "sh_r": 0.0, "sh_g": 0.0, "sh_b": 0.0, "sh_op": 75.0,
    },
    "hard-chisel-metal": {
        "label": "Hard Chisel Metal",
        "style": "inner-bevel",
        "technique": "chisel-hard",
        "depth": 250.0,
        "direction": "up",
        "size": 8.0,
        "soften": 0.0,
        "angle": 135.0,
        "altitude": 30.0,
        "gloss": "curved",
        "hl_mode": "screen", "hl_r": 1.0, "hl_g": 1.0, "hl_b": 1.0, "hl_op": 85.0,
        "sh_mode": "multiply", "sh_r": 0.1, "sh_g": 0.1, "sh_b": 0.1, "sh_op": 80.0,
    },
    "deep-emboss": {
        "label": "Deep Emboss",
        "style": "emboss",
        "technique": "smooth",
        "depth": 150.0,
        "direction": "up",
        "size": 6.0,
        "soften": 0.0,
        "angle": 120.0,
        "altitude": 30.0,
        "gloss": "linear",
        "hl_mode": "screen", "hl_r": 1.0, "hl_g": 1.0, "hl_b": 1.0, "hl_op": 75.0,
        "sh_mode": "multiply", "sh_r": 0.0, "sh_g": 0.0, "sh_b": 0.0, "sh_op": 75.0,
    },
    "pillow-carved": {
        "label": "Pillow Carved",
        "style": "pillow-emboss",
        "technique": "smooth",
        "depth": 120.0,
        "direction": "down",
        "size": 6.0,
        "soften": 1.0,
        "angle": 120.0,
        "altitude": 30.0,
        "gloss": "linear",
        "hl_mode": "screen", "hl_r": 1.0, "hl_g": 1.0, "hl_b": 1.0, "hl_op": 70.0,
        "sh_mode": "multiply", "sh_r": 0.0, "sh_g": 0.0, "sh_b": 0.0, "sh_op": 75.0,
    },
    "soft-round-bevel": {
        "label": "Soft Round Bevel",
        "style": "inner-bevel",
        "technique": "smooth",
        "depth": 80.0,
        "direction": "up",
        "size": 12.0,
        "soften": 4.0,
        "angle": 90.0,
        "altitude": 45.0,
        "gloss": "linear",
        "hl_mode": "screen", "hl_r": 1.0, "hl_g": 1.0, "hl_b": 1.0, "hl_op": 65.0,
        "sh_mode": "multiply", "sh_r": 0.0, "sh_g": 0.0, "sh_b": 0.0, "sh_op": 65.0,
    },
    "outer-rim": {
        "label": "Outer Rim",
        "style": "outer-bevel",
        "technique": "smooth",
        "depth": 150.0,
        "direction": "up",
        "size": 8.0,
        "soften": 0.0,
        "angle": 120.0,
        "altitude": 30.0,
        "gloss": "linear",
        "hl_mode": "screen", "hl_r": 1.0, "hl_g": 1.0, "hl_b": 1.0, "hl_op": 75.0,
        "sh_mode": "multiply", "sh_r": 0.0, "sh_g": 0.0, "sh_b": 0.0, "sh_op": 75.0,
    },
}


def gaussian_blur_2d(arr, sigma):
    """Vectorized separable 1D Gaussian convolution in pure NumPy."""
    if sigma <= 0.2:
        return arr.copy()
    radius = int(math.ceil(2.5 * sigma))
    x = np.arange(-radius, radius + 1)
    k = np.exp(-0.5 * (x / sigma) ** 2)
    k /= k.sum()

    h, w = arr.shape
    res = np.zeros_like(arr)
    for y in range(h):
        res[y] = np.convolve(arr[y], k, mode='same')
    for x_i in range(w):
        res[:, x_i] = np.convolve(res[:, x_i], k, mode='same')
    return res


def compute_bevel_fields(alpha, style="inner-bevel", technique="smooth",
                         depth=100.0, direction="up", size=5.0, soften=0.0,
                         angle=120.0, altitude=30.0, gloss="linear"):
    """
    Computes separate Highlight and Shadow alpha intensity fields [0.0, 1.0]
    using spherical normal shading based on the target alpha profile.
    """
    h, w = alpha.shape
    sigma = max(0.4, float(size) / 2.0)
    a_blur = gaussian_blur_2d(alpha, sigma)

    # 1. Height map profile based on Bevel Style
    if style == "inner-bevel":
        h_map = a_blur * alpha
    elif style == "outer-bevel":
        h_map = a_blur * (1.0 - alpha)
    elif style == "pillow-emboss":
        h_map = (1.0 - a_blur) * alpha + a_blur * (1.0 - alpha)
    else:  # emboss
        h_map = a_blur

    # 2. Surface normal gradient calculation
    dy, dx = np.gradient(h_map)

    # 3. Technique modulation (Chisel Hard / Chisel Soft)
    if technique == "chisel-hard":
        dx = np.sign(dx) * np.clip(np.abs(dx) * 2.5, 0.0, 1.0)
        dy = np.sign(dy) * np.clip(np.abs(dy) * 2.5, 0.0, 1.0)
    elif technique == "chisel-soft":
        dx = gaussian_blur_2d(np.sign(dx) * np.clip(np.abs(dx) * 2.0, 0.0, 1.0), 1.0)
        dy = gaussian_blur_2d(np.sign(dy) * np.clip(np.abs(dy) * 2.0, 0.0, 1.0), 1.0)

    # 4. Spherical light projection
    rad_ang = math.radians(float(angle))
    rad_alt = math.radians(float(altitude))

    dir_mult = 1.0 if direction == "up" else -1.0
    lx = dir_mult * math.cos(rad_alt) * math.cos(rad_ang)
    ly = dir_mult * (-math.cos(rad_alt) * math.sin(rad_ang))

    # 5. Depth scaling
    d_scale = (float(depth) / 100.0) * 10.0
    gx = dx * d_scale
    gy = dy * d_scale

    norm = np.sqrt(gx**2 + gy**2 + 1.0)
    directional = (-gx * lx - gy * ly) / norm

    gain = 2.0
    hl = np.clip(directional * gain, 0.0, 1.0)
    sh = np.clip(-directional * gain, 0.0, 1.0)

    # 6. Gloss contour curve modulation
    if gloss == "curved":
        hl = np.clip(np.power(hl, 1.4) * 1.2, 0.0, 1.0)
        sh = np.clip(np.power(sh, 1.2) * 1.1, 0.0, 1.0)

    # 7. Soften blur radius
    if soften > 0.0:
        hl = gaussian_blur_2d(hl, float(soften))
        sh = gaussian_blur_2d(sh, float(soften))

    # 8. Boundary silhouette clipping
    if style == "inner-bevel":
        hl *= alpha
        sh *= alpha
    elif style == "outer-bevel":
        hl *= (1.0 - alpha)
        sh *= (1.0 - alpha)

    return hl.astype(np.float32), sh.astype(np.float32)


class BevelEmbossPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return [PROC_NAME]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_bevel_emboss, None)
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        # Menu Registrations
        procedure.set_menu_label("Bevel and Emboss (Layer Style)...")
        procedure.add_menu_path("<Image>/Layer/Layer Style")
        procedure.add_menu_path("<Image>/Filters/Light and Shadow")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        procedure.set_documentation(
            "Bevel and Emboss (Layer Style)",
            "Renders a non-destructive 3D Bevel and Emboss surface relief layer style with separate Highlight and Shadow passes.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add("classic-inner-bevel", 0, "Classic Inner Bevel", "Smooth raised interior bevel with standard lighting")
        preset_choice.add("hard-chisel-metal", 1, "Hard Chisel Metal", "Sharp planar chisel ridges with high depth and curved gloss")
        preset_choice.add("deep-emboss", 2, "Deep Emboss", "Boundary straddling 3D relief embossed on both sides")
        preset_choice.add("pillow-carved", 3, "Pillow Carved", "Sunken concave boundary pillow groove")
        preset_choice.add("soft-round-bevel", 4, "Soft Round Bevel", "Smooth rounded bevel with softened edges")
        preset_choice.add("outer-rim", 5, "Outer Rim", "Exterior raised rim bevel surrounding layer perimeter")
        preset_choice.add("custom", 6, "Custom Sliders", "Manual adjustment of all bevel and emboss parameters")

        procedure.add_choice_argument(
            "preset",
            "Preset",
            "Bevel and Emboss style preset or manual custom sliders",
            preset_choice,
            "classic-inner-bevel",
            GObject.ParamFlags.READWRITE
        )

        # 2. Style Choice
        style_choice = Gimp.Choice.new()
        style_choice.add("inner-bevel", 0, "Inner Bevel", "Ramp strictly inside target layer boundaries")
        style_choice.add("outer-bevel", 1, "Outer Bevel", "Ramp strictly outside target layer boundaries")
        style_choice.add("emboss", 2, "Emboss", "Ramp straddles boundary seam across both inside and outside")
        style_choice.add("pillow-emboss", 3, "Pillow Emboss", "Inverted boundary profile with sunken groove")

        procedure.add_choice_argument(
            "style",
            "Style",
            "Bevel structure style",
            style_choice,
            "inner-bevel",
            GObject.ParamFlags.READWRITE
        )

        # 3. Technique Choice
        tech_choice = Gimp.Choice.new()
        tech_choice.add("smooth", 0, "Smooth", "Continuous smooth gradient slope")
        tech_choice.add("chisel-hard", 1, "Chisel Hard", "Sharp multi-faceted planar chisel ridges")
        tech_choice.add("chisel-soft", 2, "Chisel Soft", "Chiseled slopes with gentle apex softening")

        procedure.add_choice_argument(
            "technique",
            "Technique",
            "Bevel edge carving technique",
            tech_choice,
            "smooth",
            GObject.ParamFlags.READWRITE
        )

        # 4. Depth (1.0% to 1000.0%)
        procedure.add_double_argument(
            "depth",
            "Depth (%)",
            "Height map slope steepness multiplier (1.0 to 1000.0, default 100.0)",
            1.0,
            1000.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # 5. Direction Choice (Up / Down)
        dir_choice = Gimp.Choice.new()
        dir_choice.add("up", 0, "Up", "Convex / raised 3D surface relief")
        dir_choice.add("down", 1, "Down", "Concave / carved / sunken 3D surface relief")

        procedure.add_choice_argument(
            "direction",
            "Direction",
            "Relief direction (Up or Down)",
            dir_choice,
            "up",
            GObject.ParamFlags.READWRITE
        )

        # 6. Size (0.0 to 250.0px)
        procedure.add_double_argument(
            "size",
            "Size (px)",
            "Bevel ramp width / radius (0.0 to 250.0, default 5.0)",
            0.0,
            250.0,
            5.0,
            GObject.ParamFlags.READWRITE
        )

        # 7. Soften (0.0 to 16.0px)
        procedure.add_double_argument(
            "soften",
            "Soften (px)",
            "Bevel edge smoothing blur radius (0.0 to 16.0, default 0.0)",
            0.0,
            16.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 8. Angle (-180.0° to 180.0°)
        procedure.add_double_argument(
            "angle",
            "Angle (°)",
            "Azimuth lighting angle (-180.0 to 180.0, default 120.0)",
            -180.0,
            180.0,
            120.0,
            GObject.ParamFlags.READWRITE
        )

        # 9. Altitude (0.0° to 90.0°)
        procedure.add_double_argument(
            "altitude",
            "Altitude (°)",
            "Elevation lighting angle (0.0 to 90.0, default 30.0)",
            0.0,
            90.0,
            30.0,
            GObject.ParamFlags.READWRITE
        )

        # 10. Gloss Contour Choice
        gloss_choice = Gimp.Choice.new()
        gloss_choice.add("linear", 0, "Linear", "Standard diffuse lighting response")
        gloss_choice.add("curved", 1, "Curved", "Enhanced specular luster for glossy/metal surfaces")

        procedure.add_choice_argument(
            "gloss",
            "Gloss Contour",
            "Gloss contour response curve",
            gloss_choice,
            "linear",
            GObject.ParamFlags.READWRITE
        )

        # 11. Highlight Mode Choice
        hl_mode_choice = Gimp.Choice.new()
        hl_mode_choice.add("screen", 0, "Screen", "Standard luminous highlight blending")
        hl_mode_choice.add("normal", 1, "Normal", "Direct alpha blending")
        hl_mode_choice.add("overlay", 2, "Overlay", "Contrast highlight blending")
        hl_mode_choice.add("soft-light", 3, "Soft Light", "Diffused soft highlight blending")
        hl_mode_choice.add("linear-dodge", 4, "Linear Dodge (Add)", "Additive intense specular blending")

        procedure.add_choice_argument(
            "highlight-mode",
            "Highlight Mode",
            "Blending mode for the highlight pass",
            hl_mode_choice,
            "screen",
            GObject.ParamFlags.READWRITE
        )

        # 12-14. Highlight Solid Color RGB (0.0 to 1.0)
        procedure.add_double_argument("highlight-r", "Highlight Red", "Highlight color red (0.0 to 1.0)", 0.0, 1.0, 1.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("highlight-g", "Highlight Green", "Highlight color green (0.0 to 1.0)", 0.0, 1.0, 1.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("highlight-b", "Highlight Blue", "Highlight color blue (0.0 to 1.0)", 0.0, 1.0, 1.0, GObject.ParamFlags.READWRITE)

        # 15. Highlight Opacity (0.0% to 100.0%)
        procedure.add_double_argument(
            "highlight-opacity",
            "Highlight Opacity (%)",
            "Highlight layer opacity (0.0 to 100.0, default 75.0)",
            0.0,
            100.0,
            75.0,
            GObject.ParamFlags.READWRITE
        )

        # 16. Shadow Mode Choice
        sh_mode_choice = Gimp.Choice.new()
        sh_mode_choice.add("multiply", 0, "Multiply", "Standard shadow shading mode")
        sh_mode_choice.add("normal", 1, "Normal", "Direct alpha blending")
        sh_mode_choice.add("darken", 2, "Darken", "Darken only mode")
        sh_mode_choice.add("color-burn", 3, "Color Burn", "High-contrast saturated darks")
        sh_mode_choice.add("linear-burn", 4, "Linear Burn", "Deep subtractive darks")

        procedure.add_choice_argument(
            "shadow-mode",
            "Shadow Mode",
            "Blending mode for the shadow pass",
            sh_mode_choice,
            "multiply",
            GObject.ParamFlags.READWRITE
        )

        # 17-19. Shadow Solid Color RGB (0.0 to 1.0)
        procedure.add_double_argument("shadow-r", "Shadow Red", "Shadow color red (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("shadow-g", "Shadow Green", "Shadow color green (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("shadow-b", "Shadow Blue", "Shadow color blue (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)

        # 20. Shadow Opacity (0.0% to 100.0%)
        procedure.add_double_argument(
            "shadow-opacity",
            "Shadow Opacity (%)",
            "Shadow layer opacity (0.0 to 100.0, default 75.0)",
            0.0,
            100.0,
            75.0,
            GObject.ParamFlags.READWRITE
        )

        # 21. Layer Mask
        mask_choice = Gimp.Choice.new()
        mask_choice.add("auto", 0, "Auto (Selection or None)", "Convert active selection to mask if active; else none")
        mask_choice.add("none", 1, "None", "No layer mask attached")
        mask_choice.add("reveal-all", 2, "Reveal All (White)", "Attach white mask allowing brush concealment")
        mask_choice.add("conceal-all", 3, "Conceal All (Black)", "Attach black mask allowing selective brush reveal")
        mask_choice.add("selection", 4, "From Selection", "Convert active selection boundary to mask")

        procedure.add_choice_argument(
            "mask-type",
            "Layer Mask",
            "Layer mask attachment option",
            mask_choice,
            "auto",
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run_bevel_emboss(self, procedure, run_mode, image, drawables, config, data):
        # Interactive GUI dialog
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("python-fu-bevel-emboss")
            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        # Read configuration parameters
        preset = config.get_property("preset")
        style_prop = config.get_property("style")
        tech_prop = config.get_property("technique")
        depth_prop = config.get_property("depth")
        dir_prop = config.get_property("direction")
        size_prop = config.get_property("size")
        soften_prop = config.get_property("soften")
        angle_prop = config.get_property("angle")
        alt_prop = config.get_property("altitude")
        gloss_prop = config.get_property("gloss")

        hl_mode_prop = config.get_property("highlight-mode")
        hl_r_prop = config.get_property("highlight-r")
        hl_g_prop = config.get_property("highlight-g")
        hl_b_prop = config.get_property("highlight-b")
        hl_op_prop = config.get_property("highlight-opacity")

        sh_mode_prop = config.get_property("shadow-mode")
        sh_r_prop = config.get_property("shadow-r")
        sh_g_prop = config.get_property("shadow-g")
        sh_b_prop = config.get_property("shadow-b")
        sh_op_prop = config.get_property("shadow-opacity")

        mask_str = config.get_property("mask-type")

        # Preset overrides
        if preset in PRESETS and preset != "custom":
            p = PRESETS[preset]
            final_style = p["style"]
            final_tech = p["technique"]
            final_depth = p["depth"]
            final_dir = p["direction"]
            final_size = p["size"]
            final_soften = p["soften"]
            final_angle = p["angle"]
            final_alt = p["altitude"]
            final_gloss = p["gloss"]
            final_hl_mode = p["hl_mode"]
            final_hl_r = p["hl_r"]
            final_hl_g = p["hl_g"]
            final_hl_b = p["hl_b"]
            final_hl_op = p["hl_op"]
            final_sh_mode = p["sh_mode"]
            final_sh_r = p["sh_r"]
            final_sh_g = p["sh_g"]
            final_sh_b = p["sh_b"]
            final_sh_op = p["sh_op"]
            label = p["label"]
        else:
            final_style = style_prop
            final_tech = tech_prop
            final_depth = depth_prop
            final_dir = dir_prop
            final_size = size_prop
            final_soften = soften_prop
            final_angle = angle_prop
            final_alt = alt_prop
            final_gloss = gloss_prop
            final_hl_mode = hl_mode_prop
            final_hl_r = hl_r_prop
            final_hl_g = hl_g_prop
            final_hl_b = hl_b_prop
            final_hl_op = hl_op_prop
            final_sh_mode = sh_mode_prop
            final_sh_r = sh_r_prop
            final_sh_g = sh_g_prop
            final_sh_b = sh_b_prop
            final_sh_op = sh_op_prop
            label = "Custom"

        # Resolve target layer
        target_layer = None
        selected_layers = image.get_selected_layers()
        if len(selected_layers) > 0:
            target_layer = selected_layers[0]
        elif drawables and len(drawables) > 0:
            d = drawables[0]
            if hasattr(d, 'is_layer_mask') and d.is_layer_mask():
                layers = image.get_layers()
                target_layer = layers[0] if len(layers) > 0 else None
            else:
                target_layer = d
        else:
            layers = image.get_layers()
            target_layer = layers[0] if len(layers) > 0 else None

        if target_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-bevel-emboss"),
                    "No valid target layer found for bevel effect.",
                    0
                )
            )

        # Canvas dimensions
        img_w = image.get_width()
        img_h = image.get_height()

        Gimp.context_push()
        image.undo_group_start()

        # Save active selection if any
        has_orig_sel = not Gimp.Selection.is_empty(image)
        orig_sel_channel = Gimp.Selection.save(image) if has_orig_sel else None

        try:
            # 1. Read target layer's alpha matte
            rect = Gegl.Rectangle.new(0, 0, img_w, img_h)
            target_buf = target_layer.get_buffer()
            raw_target = target_buf.get(rect, 1.0, "RGBA float", Gegl.AbyssPolicy.NONE)
            arr_target = np.frombuffer(raw_target, dtype=np.float32).reshape((img_h, img_w, 4))
            target_alpha = arr_target[:, :, 3].copy()

            # 2. Compute 3D Highlight and Shadow shading fields
            hl_field, sh_field = compute_bevel_fields(
                target_alpha,
                style=final_style,
                technique=final_tech,
                depth=final_depth,
                direction=final_dir,
                size=final_size,
                soften=final_soften,
                angle=final_angle,
                altitude=final_alt,
                gloss=final_gloss
            )

            # 3. Create dedicated container Group Layer
            group_name = f"{target_layer.get_name()} (Bevel & Emboss - {label})"
            bev_group = Gimp.GroupLayer.new(image)
            bev_group.set_name(group_name)

            parent = target_layer.get_parent()
            pos = image.get_item_position(target_layer)
            image.insert_layer(bev_group, parent, pos)

            # 4. Create Highlight layer inside group
            hl_layer_name = f"{target_layer.get_name()} (Bevel Highlight)"
            hl_mode_enum = HL_BLEND_MODES.get(final_hl_mode, Gimp.LayerMode.SCREEN)
            hl_layer = Gimp.Layer.new(
                image,
                hl_layer_name,
                img_w,
                img_h,
                Gimp.ImageType.RGBA_IMAGE,
                max(0.0, min(100.0, float(final_hl_op))),
                hl_mode_enum
            )
            image.insert_layer(hl_layer, bev_group, 0)

            # Populate highlight pixels
            hl_arr = np.zeros((img_h, img_w, 4), dtype=np.float32)
            hl_arr[:, :, 0] = final_hl_r
            hl_arr[:, :, 1] = final_hl_g
            hl_arr[:, :, 2] = final_hl_b
            hl_arr[:, :, 3] = hl_field

            hl_buf = hl_layer.get_buffer()
            hl_buf.set(rect, "RGBA float", hl_arr.tobytes())
            hl_buf.flush()
            hl_layer.update(0, 0, img_w, img_h)

            # 5. Create Shadow layer inside group (inserted below highlight)
            sh_layer_name = f"{target_layer.get_name()} (Bevel Shadow)"
            sh_mode_enum = SH_BLEND_MODES.get(final_sh_mode, Gimp.LayerMode.MULTIPLY)
            sh_layer = Gimp.Layer.new(
                image,
                sh_layer_name,
                img_w,
                img_h,
                Gimp.ImageType.RGBA_IMAGE,
                max(0.0, min(100.0, float(final_sh_op))),
                sh_mode_enum
            )
            image.insert_layer(sh_layer, bev_group, 1)

            # Populate shadow pixels
            sh_arr = np.zeros((img_h, img_w, 4), dtype=np.float32)
            sh_arr[:, :, 0] = final_sh_r
            sh_arr[:, :, 1] = final_sh_g
            sh_arr[:, :, 2] = final_sh_b
            sh_arr[:, :, 3] = sh_field

            sh_buf = sh_layer.get_buffer()
            sh_buf.set(rect, "RGBA float", sh_arr.tobytes())
            sh_buf.flush()
            sh_layer.update(0, 0, img_w, img_h)

            # 6. Layer Mask Attachment on container group
            if mask_str == "auto":
                if has_orig_sel and orig_sel_channel is not None:
                    image.select_item(Gimp.ChannelOps.REPLACE, orig_sel_channel)
                    mask = bev_group.create_mask(Gimp.AddMaskType.SELECTION)
                    bev_group.add_mask(mask)
            elif mask_str == "reveal-all":
                mask = bev_group.create_mask(Gimp.AddMaskType.WHITE)
                bev_group.add_mask(mask)
            elif mask_str == "conceal-all":
                mask = bev_group.create_mask(Gimp.AddMaskType.BLACK)
                bev_group.add_mask(mask)
            elif mask_str == "selection":
                if has_orig_sel and orig_sel_channel is not None:
                    image.select_item(Gimp.ChannelOps.REPLACE, orig_sel_channel)
                    mask = bev_group.create_mask(Gimp.AddMaskType.SELECTION)
                    bev_group.add_mask(mask)

            # Restore original selection or clear
            if has_orig_sel and orig_sel_channel is not None:
                image.select_item(Gimp.ChannelOps.REPLACE, orig_sel_channel)
                image.remove_channel(orig_sel_channel)
            else:
                Gimp.Selection.none(image)

            # Set group layer as active layer
            image.set_selected_layers([bev_group])

            image.undo_group_end()
            Gimp.context_pop()
            Gimp.displays_flush()

            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as e:
            if has_orig_sel and orig_sel_channel is not None:
                try:
                    image.remove_channel(orig_sel_channel)
                except Exception:
                    pass
            image.undo_group_end()
            Gimp.context_pop()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-bevel-emboss"),
                    f"Bevel & Emboss generation failed: {str(e)}",
                    0
                )
            )


Gimp.main(BevelEmbossPlugin.__gtype__, sys.argv)
