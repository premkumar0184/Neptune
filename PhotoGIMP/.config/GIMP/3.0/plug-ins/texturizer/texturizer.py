#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Texturizer & Surface Canvas Helper Plugin
===================================================================
Photoshop Reference:
- Topics.txt line 481: "Apply texture and surface effects to filters"
- Topics.txt line 480: "Overview of adding blur to images"
- photoshop_docs.md Section 442 lines 12911-12930:
  "Filter > Texture > Texturizer / Filter Gallery: Canvas, Burlap, Brick, Sandstone
   with Scaling, Relief, Light Direction, and Invert"
- photoshop_docs.md Section 442 line 12915:
  "Texture and surface controls add realistic material qualities to filtered images,
   making them appear painted on canvas, brick, or other textured surfaces."

Key Architectural Features:
1. Native Tactile Heightmap Generation:
   - Canvas: Fine orthogonal warp-and-weft woven fabric grid with alternating thread undulating peaks.
   - Burlap: Coarse rustic jute weave with wider spacing, deeper inter-thread crevices, and fiber variation.
   - Brick: Staggered horizontal masonry courses with mortared bed joints and alternating vertical head joints.
   - Sandstone: Granular porous stone relief with stochastic micro-pits and mineral roughness.
   - Paper: Subtle organic cold-press watercolor paper grain.
2. Physical Directional Surface Lighting:
   - 8 directional lighting angles: Top, Top-Left, Left, Bottom-Left, Bottom, Bottom-Right, Right, Top-Right.
   - Surface gradient dot-product directional illumination: delta = Relief * (L . grad(H)).
3. Invert Texture Toggle:
   - Inverts ridges and valleys (reversing highlights and crevices).
4. Scaling and Relief Controls:
   - Scaling: 50% to 200% texture pattern magnification.
   - Relief: 1 to 50 depth intensity.
5. Curated Artistic Presets:
   - Fine Art Canvas: Classic gallery stretched canvas weave.
   - Rustic Burlap Weave: Coarse burlap/hessian rustic jute weave.
   - Weathered Brickwork: Architectural masonry course relief.
   - Sandstone Block Relief: Sedimentary porous sandstone blocks.
   - Watercolor Paper Grain: Cold-press handmade watercolor paper.
   - Custom: Full manual slider control.
6. 100% Non-Destructive Adjustment Layering:
   - Embosses texture onto neutral gray (128) in Soft Light or Overlay blend mode.
   - Base layer source pixels underneath remain 100% mathematically untouched (diff == 0.000000).
   - Editable layer mask attached for selective masking.
"""

import os
import sys
import numpy as np
import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib


PRESETS = {
    "fine-art-canvas": {
        "label": "Fine Art Canvas",
        "desc": "Fine woven canvas fabric with subtle warp-and-weft relief",
        "texture": "canvas",
        "scaling": 100.0,
        "relief": 10.0,
        "light_dir": "top-left",
        "invert": False,
        "blend_mode": "soft-light",
        "mask_mode": "reveal-all",
        "opacity": 85.0,
    },
    "rustic-burlap": {
        "label": "Rustic Burlap Weave",
        "desc": "Coarse rustic jute fabric with deep weave grooves and tactile relief",
        "texture": "burlap",
        "scaling": 120.0,
        "relief": 18.0,
        "light_dir": "top-left",
        "invert": False,
        "blend_mode": "overlay",
        "mask_mode": "reveal-all",
        "opacity": 90.0,
    },
    "weathered-brick": {
        "label": "Weathered Brickwork",
        "desc": "Staggered masonry brickwork with pillowed faces and mortared joints",
        "texture": "brick",
        "scaling": 100.0,
        "relief": 25.0,
        "light_dir": "top-left",
        "invert": False,
        "blend_mode": "soft-light",
        "mask_mode": "reveal-all",
        "opacity": 90.0,
    },
    "sandstone-block": {
        "label": "Sandstone Block Relief",
        "desc": "Sedimentary porous stone texture with granular mineral pitting",
        "texture": "sandstone",
        "scaling": 100.0,
        "relief": 15.0,
        "light_dir": "top",
        "invert": False,
        "blend_mode": "soft-light",
        "mask_mode": "reveal-all",
        "opacity": 80.0,
    },
    "watercolor-paper": {
        "label": "Watercolor Paper Grain",
        "desc": "Cold-press watercolor paper with soft organic pulp texture",
        "texture": "paper",
        "scaling": 80.0,
        "relief": 6.0,
        "light_dir": "top-left",
        "invert": False,
        "blend_mode": "soft-light",
        "mask_mode": "reveal-all",
        "opacity": 65.0,
    },
    "custom": {
        "label": "Custom Texturizer",
        "desc": "Manual slider configuration for custom surface texture",
        "texture": "canvas",
        "scaling": 100.0,
        "relief": 10.0,
        "light_dir": "top-left",
        "invert": False,
        "blend_mode": "soft-light",
        "mask_mode": "reveal-all",
        "opacity": 85.0,
    },
}

LIGHT_VECTORS = {
    "top": (0.0, -1.0),
    "top-left": (-0.70710678, -0.70710678),
    "left": (-1.0, 0.0),
    "bottom-left": (-0.70710678, 0.70710678),
    "bottom": (0.0, 1.0),
    "bottom-right": (0.70710678, 0.70710678),
    "right": (1.0, 0.0),
    "top-right": (0.70710678, -0.70710678),
}

BLEND_MODES = {
    "soft-light": Gimp.LayerMode.SOFTLIGHT,
    "overlay": Gimp.LayerMode.OVERLAY,
    "hard-light": Gimp.LayerMode.HARDLIGHT,
    "multiply": Gimp.LayerMode.MULTIPLY,
}


def generate_texture_heightmap(texture_type, W, H, scaling_pct):
    """Generates continuous 2D heightmap array for specified material texture."""
    scale = max(0.2, float(scaling_pct) / 100.0)
    x = np.arange(W, dtype=np.float32)
    y = np.arange(H, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)

    if texture_type == "canvas":
        # Fine orthogonal canvas warp-and-weft weave
        period = max(4.0, 8.0 * scale)
        H_map = (np.sin(2.0 * np.pi * xx / period) * np.cos(2.0 * np.pi * yy / period) +
                 0.35 * np.cos(4.0 * np.pi * xx / period) - 0.35 * np.sin(4.0 * np.pi * yy / period))

    elif texture_type == "burlap":
        # Coarse rustic jute weave: alternating over-and-under thick yarns with fiber crevices
        period = max(8.0, 14.0 * scale)
        yarn_x = np.sin(2.0 * np.pi * xx / period)
        yarn_y = np.cos(2.0 * np.pi * yy / period)
        weave = np.where(np.sin(np.pi * xx / period) * np.sin(np.pi * yy / period) > 0, yarn_x, yarn_y)
        gaps = np.abs(np.sin(2.0 * np.pi * xx / period)) * np.abs(np.sin(2.0 * np.pi * yy / period))
        H_map = weave + 0.5 * gaps

    elif texture_type == "brick":
        # Staggered brick masonry courses
        brick_h = max(8.0, 16.0 * scale)
        brick_w = max(16.0, 36.0 * scale)
        mortar_thick = max(1.5, 2.0 * scale)

        course_idx = np.floor(yy / brick_h).astype(np.int32)
        y_in_course = yy % brick_h
        x_stagger = np.where((course_idx % 2) == 1, xx + brick_w * 0.5, xx)
        x_in_brick = x_stagger % brick_w

        dist_y = np.minimum(y_in_course, brick_h - y_in_course)
        dist_x = np.minimum(x_in_brick, brick_w - x_in_brick)

        mortar_y = np.clip(dist_y / mortar_thick, 0.0, 1.0)
        mortar_x = np.clip(dist_x / mortar_thick, 0.0, 1.0)
        mortar = np.minimum(mortar_y, mortar_x)

        dome = np.sin(np.pi * (y_in_course / brick_h)) * np.sin(np.pi * (x_in_brick / brick_w))
        H_map = mortar * (0.3 + 0.7 * dome)

    elif texture_type == "sandstone":
        # Granular sedimentary stone with multi-scale mineral pitting
        freqs = [0.08 / scale, 0.17 / scale, 0.35 / scale, 0.70 / scale]
        weights = [0.45, 0.30, 0.15, 0.10]
        H_map = np.zeros_like(xx)
        for f, w in zip(freqs, weights):
            H_map += w * (np.sin(xx * f * 2.3 + yy * f * 1.7) * np.cos(xx * f * 1.9 - yy * f * 2.5) +
                          np.sin(xx * f * 3.1 - yy * f * 0.8) * np.sin(yy * f * 3.7 + xx * f * 1.1))

    elif texture_type == "paper":
        # Soft cold-press watercolor paper grain
        freqs = [0.05 / scale, 0.12 / scale, 0.25 / scale]
        weights = [0.55, 0.30, 0.15]
        H_map = np.zeros_like(xx)
        for f, w in zip(freqs, weights):
            H_map += w * (np.sin(xx * f * 1.5 + yy * f * 2.1) * np.cos(xx * f * 2.7 - yy * f * 1.4))

    else:
        # Fallback fine canvas
        period = max(4.0, 8.0 * scale)
        H_map = np.sin(2.0 * np.pi * xx / period) * np.cos(2.0 * np.pi * yy / period)

    return H_map


def generate_surface_shading(H_map, light_dir_name, relief_val, invert):
    """Calculates directional shading and embosses onto neutral gray (128)."""
    lx, ly = LIGHT_VECTORS.get(light_dir_name, (-0.70710678, -0.70710678))
    gx, gy = np.gradient(H_map)

    # Scaling factor for realistic surface depth
    factor = float(relief_val) / 18.0
    shade = (gx * lx + gy * ly) * factor

    if invert:
        shade = -shade

    shade = np.clip(shade, -1.0, 1.0)
    gray = np.clip(128.0 + shade * 127.0, 0, 255).astype(np.uint8)
    return gray


class TexturizerPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-texturizer"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, self.run, None
        )
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
        procedure.set_menu_label("Texturizer...")
        procedure.add_menu_path("<Image>/Filters/Artistic")
        procedure.add_menu_path("<Image>/Filters/Texture")
        procedure.add_menu_path("<Image>/Filters/Retouching")
        procedure.add_menu_path("<Image>/Layer")

        procedure.set_documentation(
            "Non-Destructive Texturizer & Surface Canvas Helper",
            "Simulates tactile canvas, burlap, brick, sandstone, and fine paper surface textures "
            "with physical directional lighting, scaling, relief depth, and editable layer masks.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add("fine-art-canvas", 0, "Fine Art Canvas", "Fine woven canvas fabric with subtle warp-and-weft relief")
        preset_choice.add("rustic-burlap", 1, "Rustic Burlap Weave", "Coarse rustic jute fabric with deep weave grooves")
        preset_choice.add("weathered-brick", 2, "Weathered Brickwork", "Staggered masonry brickwork with pillowed faces and mortar joints")
        preset_choice.add("sandstone-block", 3, "Sandstone Block Relief", "Sedimentary porous stone texture with granular mineral pitting")
        preset_choice.add("watercolor-paper", 4, "Watercolor Paper Grain", "Cold-press watercolor paper with soft organic pulp texture")
        preset_choice.add("custom", 5, "Custom Texturizer", "Manual slider configuration for custom surface texture")

        procedure.add_choice_argument(
            "preset",
            "Surface Preset",
            "Curated surface texture preset (fine-art-canvas, rustic-burlap, weathered-brick, sandstone-block, watercolor-paper, custom)",
            preset_choice,
            "fine-art-canvas",
            GObject.ParamFlags.READWRITE
        )

        # 2. Texture Choice
        tex_choice = Gimp.Choice.new()
        tex_choice.add("canvas", 0, "Canvas", "Woven artist canvas fabric grid")
        tex_choice.add("burlap", 1, "Burlap", "Coarse rustic jute weave with deep crevices")
        tex_choice.add("brick", 2, "Brick", "Staggered masonry courses with mortar joints")
        tex_choice.add("sandstone", 3, "Sandstone", "Granular sedimentary stone pitting")
        tex_choice.add("paper", 4, "Paper", "Cold-press watercolor paper grain")

        procedure.add_choice_argument(
            "texture",
            "Texture Pattern",
            "Physical material surface texture (canvas, burlap, brick, sandstone, paper)",
            tex_choice,
            "canvas",
            GObject.ParamFlags.READWRITE
        )

        # 3. Scaling
        procedure.add_double_argument(
            "scaling",
            "Texture Scaling",
            "Texture pattern scale percentage (50.0 to 200.0, default 100.0)",
            50.0,
            200.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # 4. Relief Depth
        procedure.add_double_argument(
            "relief",
            "Relief Depth",
            "Surface relief embossing depth (1.0 to 50.0, default 10.0)",
            1.0,
            50.0,
            10.0,
            GObject.ParamFlags.READWRITE
        )

        # 5. Light Direction Choice
        light_choice = Gimp.Choice.new()
        light_choice.add("top", 0, "Top", "Directional light from top")
        light_choice.add("top-left", 1, "Top-Left", "Directional light from top-left (Photoshop standard)")
        light_choice.add("left", 2, "Left", "Directional light from left")
        light_choice.add("bottom-left", 3, "Bottom-Left", "Directional light from bottom-left")
        light_choice.add("bottom", 4, "Bottom", "Directional light from bottom")
        light_choice.add("bottom-right", 5, "Bottom-Right", "Directional light from bottom-right")
        light_choice.add("right", 6, "Right", "Directional light from right")
        light_choice.add("top-right", 7, "Top-Right", "Directional light from top-right")

        procedure.add_choice_argument(
            "light-dir",
            "Light Direction",
            "Direction of illuminating light source (top, top-left, left, bottom-left, bottom, bottom-right, right, top-right)",
            light_choice,
            "top-left",
            GObject.ParamFlags.READWRITE
        )

        # 6. Invert Texture
        procedure.add_boolean_argument(
            "invert",
            "Invert Texture",
            "Inverts ridges and crevices reversing surface highlights and shadows (default False)",
            False,
            GObject.ParamFlags.READWRITE
        )

        # 7. Blend Mode Choice
        blend_choice = Gimp.Choice.new()
        blend_choice.add("soft-light", 0, "Soft Light", "Natural photo texture blending (recommended)")
        blend_choice.add("overlay", 1, "Overlay", "High-contrast tactile texture blending")
        blend_choice.add("hard-light", 2, "Hard Light", "Dramatic surface relief embossing")
        blend_choice.add("multiply", 3, "Multiply", "Dark ink / handmade paper texture")

        procedure.add_choice_argument(
            "blend-mode",
            "Blend Mode",
            "Layer blend mode for texture embossing (soft-light, overlay, hard-light, multiply)",
            blend_choice,
            "soft-light",
            GObject.ParamFlags.READWRITE
        )

        # 8. Mask Mode Choice
        mask_choice = Gimp.Choice.new()
        mask_choice.add("reveal-all", 0, "Reveal All (White Mask)", "Attach full reveal-all white mask")
        mask_choice.add("conceal-all", 1, "Conceal All (Black Mask)", "Attach black mask for selective brush painting")
        mask_choice.add("selection", 2, "Active Selection Mask", "Confine texture strictly to active selection")

        procedure.add_choice_argument(
            "mask-mode",
            "Layer Mask Mode",
            "Adjustment layer mask configuration (reveal-all, conceal-all, selection)",
            mask_choice,
            "reveal-all",
            GObject.ParamFlags.READWRITE
        )

        # 9. Opacity
        procedure.add_double_argument(
            "opacity",
            "Layer Opacity",
            "Adjustment layer opacity percentage (0.0 to 100.0, default 85.0)",
            0.0,
            100.0,
            85.0,
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run(self, procedure, run_mode, image, drawables, config, data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-texturizer"),
                    "No valid image provided.",
                    0
                )
            )

        if run_mode == Gimp.RunMode.INTERACTIVE:
            Gimp.ui_init("texturizer.py")
            dialog = Gimp.ProcedureDialog.new(procedure, config, "Texturizer & Surface Controls")
            dialog.fill([
                "preset", "texture", "scaling", "relief",
                "light-dir", "invert", "blend-mode", "mask-mode", "opacity"
            ])
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        # Resolve target drawable safely
        target_drawable = None
        selected_layers = image.get_selected_layers()
        if len(selected_layers) > 0:
            target_drawable = selected_layers[0]
        elif drawables and len(drawables) > 0:
            d = drawables[0]
            if hasattr(d, 'is_layer_mask') and d.is_layer_mask():
                layers = image.get_layers()
                target_drawable = layers[0] if len(layers) > 0 else None
            else:
                target_drawable = d
        else:
            layers = image.get_layers()
            if len(layers) > 0:
                target_drawable = layers[0]

        if target_drawable is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-texturizer"),
                    "No target drawable found to apply Texturizer.",
                    0
                )
            )

        preset_key = config.get_property("preset") or "fine-art-canvas"
        if preset_key not in PRESETS:
            preset_key = "fine-art-canvas"
        preset_cfg = PRESETS[preset_key]

        if preset_key == "custom":
            texture_val = config.get_property("texture") or "canvas"
            scaling_val = config.get_property("scaling")
            relief_val = config.get_property("relief")
            light_dir_val = config.get_property("light-dir") or "top-left"
            invert_val = config.get_property("invert")
            blend_mode_val = config.get_property("blend-mode") or "soft-light"
            mask_mode_val = config.get_property("mask-mode") or "reveal-all"
            opacity_val = config.get_property("opacity")
        else:
            texture_val = preset_cfg["texture"]
            scaling_val = preset_cfg["scaling"]
            relief_val = preset_cfg["relief"]
            light_dir_val = preset_cfg["light_dir"]
            invert_val = preset_cfg["invert"]
            blend_mode_val = preset_cfg["blend_mode"]
            # Allow explicit mask-mode override even with preset
            mask_mode_arg = config.get_property("mask-mode")
            mask_mode_val = mask_mode_arg if mask_mode_arg else preset_cfg["mask_mode"]
            opacity_val = preset_cfg["opacity"]

        image.undo_group_start()
        saved_sel_channel = None
        try:
            # Check active selection (Decision D-003)
            has_user_selection = not Gimp.Selection.is_empty(image)
            if has_user_selection:
                saved_sel_channel = Gimp.Selection.save(image)
                Gimp.Selection.none(image)

            W = image.get_width()
            H = image.get_height()

            # 1. Generate surface heightmap
            H_map = generate_texture_heightmap(texture_val, W, H, scaling_val)

            # 2. Calculate directional surface shading and emboss onto neutral gray (128)
            gray = generate_surface_shading(H_map, light_dir_val, relief_val, invert_val)

            # 3. Create dedicated non-destructive Texturizer layer
            blend_enum = BLEND_MODES.get(blend_mode_val, Gimp.LayerMode.SOFTLIGHT)
            layer_name = f"Texturizer ({preset_cfg['label']})"
            tex_layer = Gimp.Layer.new(
                image,
                layer_name,
                W,
                H,
                Gimp.ImageType.RGBA_IMAGE,
                opacity_val,
                blend_enum
            )

            # Insert above target drawable
            parent = target_drawable.get_parent()
            pos = image.get_item_position(target_drawable)
            image.insert_layer(tex_layer, parent, pos)

            # 4. Populate pixel buffer with RGBA neutral gray emboss data
            rgba = np.empty((H, W, 4), dtype=np.uint8)
            rgba[:, :, 0] = gray
            rgba[:, :, 1] = gray
            rgba[:, :, 2] = gray
            rgba[:, :, 3] = 255

            buf = tex_layer.get_buffer()
            buf.set(Gegl.Rectangle.new(0, 0, W, H), "RGBA u8", rgba.tobytes())
            buf.flush()
            tex_layer.update(0, 0, W, H)

            # 5. Attach editable layer mask
            if mask_mode_val == "conceal-all":
                mask = tex_layer.create_mask(Gimp.AddMaskType.BLACK)
                tex_layer.add_mask(mask)
            elif mask_mode_val == "selection":
                if saved_sel_channel is not None:
                    image.select_item(Gimp.ChannelOps.REPLACE, saved_sel_channel)
                    mask = tex_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    tex_layer.add_mask(mask)
                    Gimp.Selection.none(image)
                else:
                    mask = tex_layer.create_mask(Gimp.AddMaskType.WHITE)
                    tex_layer.add_mask(mask)
            else:  # reveal-all
                mask = tex_layer.create_mask(Gimp.AddMaskType.WHITE)
                tex_layer.add_mask(mask)

            # Cleanup saved selection channel
            if saved_sel_channel is not None:
                image.remove_channel(saved_sel_channel)
                saved_sel_channel = None

            image.set_selected_layers([tex_layer])
            Gimp.displays_flush()

            image.undo_group_end()
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as err:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-texturizer"),
                    f"Texturizer execution failed: {str(err)}",
                    0
                )
            )


if __name__ == "__main__":
    Gimp.main(TexturizerPlugin.__gtype__, sys.argv)
