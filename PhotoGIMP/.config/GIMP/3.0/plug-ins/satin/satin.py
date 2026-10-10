#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Satin Layer Style Helper Plugin
=========================================================
Simulates Adobe Photoshop's non-destructive Satin layer style:
  - Photoshop Menu: Layer > Layer Style > Satin...
  - Photoshop Menu: Filters > Light and Shadow > Satin (Layer Style)...
  - Photoshop Docs: Section 113-115 lines 3433-3500 (Layer Style effects and options)
  - Topics.txt: Lines 107-118, 432

Photoshop Satin Architecture:
  1. Dual-Directional Offset Trigonometry:
     Given lighting angle θ and offset distance d:
       Δx = int(round(d * cos(θ)))
       Δy = int(round(-d * sin(θ)))
     Dual shifted boundary copies:
       M1(x, y) = Atarget(x - Δx, y - Δy)
       M2(x, y) = Atarget(x + Δx, y + Δy)
     Interior difference fold:
       M_diff(x, y) = |M1(x, y) - M2(x, y)|
  2. Invert Option (Specular Sheen vs Matte Shadow):
     - Invert == True (Photoshop Default):
       M_satin = (1.0 - M_diff) * Atarget
       Produces interior silk sheen folds radiating from core to edges.
     - Invert == False:
       M_satin = M_diff * Atarget
       Produces deep recessed fabric shading wrinkles.
  3. Size Radius Gaussian Diffusion:
     Softens interior folds with Gaussian blur radius proportional to Size.
  4. Contour Power-Law Curve Falloff:
     Shapes opacity curve across surface:
       M_contour = M_satin ** (50.0 / Range)
  5. Film Grain Noise Texture:
     Injects subtle organic texture into satin sheen.
  6. Strict Boundary Silhouette Clipping:
     Overlay pixels are strictly clipped to the target layer's silhouette:
       A_overlay(x, y) = A_satin(x, y) * A_target(x, y).
       Outside pixels are strictly alpha == 0.000000.
       Anti-aliased and semi-transparent edges in the target layer are matched exactly.
  7. Photoshop Blend Modes & Opacity:
     - Multiply, Normal, Color Burn, Linear Burn, Darken, Soft Light, Overlay, Screen.
     - Opacity slider (0.0% to 100.0%, default 50.0%).
  8. Non-Destructive Layer Architecture:
     - Dedicated overlay layer inserted directly above the target layer in the stack.
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


PROC_NAME = "python-fu-satin"

BLEND_MODES = {
    "multiply": Gimp.LayerMode.MULTIPLY,
    "normal": Gimp.LayerMode.NORMAL,
    "color-burn": Gimp.LayerMode.BURN,
    "linear-burn": Gimp.LayerMode.LINEAR_BURN,
    "darken": Gimp.LayerMode.DARKEN_ONLY,
    "soft-light": Gimp.LayerMode.SOFTLIGHT,
    "overlay": Gimp.LayerMode.OVERLAY,
    "screen": Gimp.LayerMode.SCREEN,
}

PRESETS = {
    "deep-silk": {
        "label": "Deep Silk",
        "angle": 19.0,
        "dist": 11.0,
        "size": 14.0,
        "invert": True,
        "range": 50.0,
        "r": 0.0, "g": 0.0, "b": 0.0,
        "bmode": "multiply",
        "opacity": 50.0,
        "noise": 0.0,
    },
    "pearl-sheen": {
        "label": "Pearl Sheen",
        "angle": 120.0,
        "dist": 15.0,
        "size": 20.0,
        "invert": True,
        "range": 50.0,
        "r": 1.0, "g": 1.0, "b": 1.0,
        "bmode": "screen",
        "opacity": 65.0,
        "noise": 0.0,
    },
    "golden-folds": {
        "label": "Golden Folds",
        "angle": 45.0,
        "dist": 12.0,
        "size": 18.0,
        "invert": True,
        "range": 50.0,
        "r": 0.95, "g": 0.75, "b": 0.20,
        "bmode": "overlay",
        "opacity": 60.0,
        "noise": 0.0,
    },
    "velvet-depth": {
        "label": "Velvet Depth",
        "angle": -45.0,
        "dist": 16.0,
        "size": 22.0,
        "invert": False,
        "range": 50.0,
        "r": 0.50, "g": 0.05, "b": 0.10,
        "bmode": "multiply",
        "opacity": 70.0,
        "noise": 0.0,
    },
    "midnight-glow": {
        "label": "Midnight Glow",
        "angle": 90.0,
        "dist": 14.0,
        "size": 16.0,
        "invert": True,
        "range": 50.0,
        "r": 0.10, "g": 0.20, "b": 0.50,
        "bmode": "soft-light",
        "opacity": 60.0,
        "noise": 0.0,
    },
    "subtle-contour": {
        "label": "Subtle Contour",
        "angle": 30.0,
        "dist": 8.0,
        "size": 10.0,
        "invert": True,
        "range": 50.0,
        "r": 0.20, "g": 0.20, "b": 0.20,
        "bmode": "normal",
        "opacity": 35.0,
        "noise": 0.0,
    },
}


def shift_2d(arr, dy, dx):
    """Vectorized integer 2D translation without external dependencies."""
    h, w = arr.shape
    res = np.zeros_like(arr)
    if dy > 0:
        sy1, sy2 = 0, h - dy
        dy1, dy2 = dy, h
    elif dy < 0:
        sy1, sy2 = -dy, h
        dy1, dy2 = 0, h + dy
    else:
        sy1, sy2 = 0, h
        dy1, dy2 = 0, h

    if dx > 0:
        sx1, sx2 = 0, w - dx
        dx1, dx2 = dx, w
    elif dx < 0:
        sx1, sx2 = -dx, w
        dx1, dx2 = 0, w + dx
    else:
        sx1, sx2 = 0, w
        dx1, dx2 = 0, w

    if sy2 > sy1 and sx2 > sx1:
        res[dy1:dy2, dx1:dx2] = arr[sy1:sy2, sx1:sx2]
    return res


class SatinPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return [PROC_NAME]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_satin, None)
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        # Menu Registrations
        procedure.set_menu_label("Satin (Layer Style)...")
        procedure.add_menu_path("<Image>/Layer/Layer Style")
        procedure.add_menu_path("<Image>/Filters/Light and Shadow")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        procedure.set_documentation(
            "Satin (Layer Style)",
            "Renders a non-destructive satin/silk sheen layer style clipped strictly to the target layer's silhouette.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add("deep-silk", 0, "Deep Silk (Classic)", "Classic black silk multiply interior shading")
        preset_choice.add("pearl-sheen", 1, "Pearl Sheen", "Luminous white silk specular highlight")
        preset_choice.add("golden-folds", 2, "Golden Folds", "Warm golden fabric overlay sheen")
        preset_choice.add("velvet-depth", 3, "Velvet Depth", "Rich dark crimson non-inverted fabric folds")
        preset_choice.add("midnight-glow", 4, "Midnight Glow", "Deep cobalt soft diffused sheen")
        preset_choice.add("subtle-contour", 5, "Subtle Contour", "Soft low-contrast edge contours")
        preset_choice.add("custom", 6, "Custom Sliders", "Manual adjustment of all satin parameters")

        procedure.add_choice_argument(
            "preset",
            "Preset",
            "Satin style preset or manual custom sliders",
            preset_choice,
            "deep-silk",
            GObject.ParamFlags.READWRITE
        )

        # 2. Angle (-180.0° to 180.0°)
        procedure.add_double_argument(
            "angle",
            "Angle (°)",
            "Directional lighting angle (-180.0 to 180.0, default 19.0)",
            -180.0,
            180.0,
            19.0,
            GObject.ParamFlags.READWRITE
        )

        # 3. Distance (0.0 to 200.0px)
        procedure.add_double_argument(
            "distance",
            "Distance (px)",
            "Dual offset translation distance (0.0 to 200.0, default 11.0)",
            0.0,
            200.0,
            11.0,
            GObject.ParamFlags.READWRITE
        )

        # 4. Size (0.0 to 200.0px)
        procedure.add_double_argument(
            "size",
            "Size (px)",
            "Blur radius / softness diffusion (0.0 to 200.0, default 14.0)",
            0.0,
            200.0,
            14.0,
            GObject.ParamFlags.READWRITE
        )

        # 5. Invert Toggle
        procedure.add_boolean_argument(
            "invert",
            "Invert",
            "Invert specular sheen vs matte shadow folds (default True)",
            True,
            GObject.ParamFlags.READWRITE
        )

        # 6. Range / Contour (1.0% to 100.0%)
        procedure.add_double_argument(
            "range",
            "Range / Contour (%)",
            "Contour falloff curve shaping (1.0 to 100.0, default 50.0)",
            1.0,
            100.0,
            50.0,
            GObject.ParamFlags.READWRITE
        )

        # 7-9. Satin Solid Color RGB (0.0 to 1.0)
        procedure.add_double_argument("satin-r", "Satin Red", "Custom color red (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("satin-g", "Satin Green", "Custom color green (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("satin-b", "Satin Blue", "Custom color blue (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)

        # 10. Blend Mode
        mode_choice = Gimp.Choice.new()
        mode_choice.add("multiply", 0, "Multiply", "Standard dark shading mode")
        mode_choice.add("normal", 1, "Normal", "Direct alpha blending")
        mode_choice.add("color-burn", 2, "Color Burn", "High-contrast saturated darks")
        mode_choice.add("linear-burn", 3, "Linear Burn", "Deep subtractive shading")
        mode_choice.add("darken", 4, "Darken", "Darken only mode")
        mode_choice.add("soft-light", 5, "Soft Light", "Subtle diffused lighting")
        mode_choice.add("overlay", 6, "Overlay", "High-contrast specular folds")
        mode_choice.add("screen", 7, "Screen", "Luminous highlight sheen")

        procedure.add_choice_argument(
            "blend-mode",
            "Blend Mode",
            "Layer blending mode for the satin overlay",
            mode_choice,
            "multiply",
            GObject.ParamFlags.READWRITE
        )

        # 11. Opacity (0.0% to 100.0%)
        procedure.add_double_argument(
            "opacity",
            "Opacity (%)",
            "Satin layer opacity (0.0 to 100.0, default 50.0)",
            0.0,
            100.0,
            50.0,
            GObject.ParamFlags.READWRITE
        )

        # 12. Noise (0.0% to 100.0%)
        procedure.add_double_argument(
            "noise",
            "Noise (%)",
            "Film grain noise texture percentage (0.0 to 100.0, default 0.0)",
            0.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 13. Layer Mask
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

    def run_satin(self, procedure, run_mode, image, drawables, config, data):
        # Interactive GUI dialog
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("python-fu-satin")
            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        # Read configuration parameters
        preset = config.get_property("preset")
        angle_val = config.get_property("angle")
        dist_val = config.get_property("distance")
        size_val = config.get_property("size")
        invert_val = config.get_property("invert")
        range_val = config.get_property("range")
        satin_r = config.get_property("satin-r")
        satin_g = config.get_property("satin-g")
        satin_b = config.get_property("satin-b")
        bmode_str = config.get_property("blend-mode")
        opacity_val = config.get_property("opacity")
        noise_val = config.get_property("noise")
        mask_str = config.get_property("mask-type")

        # Preset overrides
        if preset in PRESETS and preset != "custom":
            p = PRESETS[preset]
            final_angle = p["angle"]
            final_dist = p["dist"]
            final_size = p["size"]
            final_invert = p["invert"]
            final_range = p["range"]
            final_r = p["r"]
            final_g = p["g"]
            final_b = p["b"]
            final_bmode = p["bmode"]
            final_opacity = p["opacity"]
            final_noise = p["noise"]
            label = p["label"]
        else:
            final_angle = angle_val
            final_dist = dist_val
            final_size = size_val
            final_invert = invert_val
            final_range = range_val
            final_r = satin_r
            final_g = satin_g
            final_b = satin_b
            final_bmode = bmode_str
            final_opacity = opacity_val
            final_noise = noise_val
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
                    GLib.quark_from_string("gimp-satin"),
                    "No valid target layer found for satin effect.",
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
            # 1. Read target layer's alpha matte for strict silhouette clipping
            rect = Gegl.Rectangle.new(0, 0, img_w, img_h)
            target_buf = target_layer.get_buffer()
            raw_target = target_buf.get(rect, 1.0, "RGBA float", Gegl.AbyssPolicy.NONE)
            arr_target = np.frombuffer(raw_target, dtype=np.float32).reshape((img_h, img_w, 4))
            target_alpha = arr_target[:, :, 3].copy()

            # 2. Dual-directional offset trigonometry
            rad = math.radians(final_angle)
            dx = int(round(final_dist * math.cos(rad)))
            dy = int(round(-final_dist * math.sin(rad)))

            m1 = shift_2d(target_alpha, dy, dx)
            m2 = shift_2d(target_alpha, -dy, -dx)
            diff = np.abs(m1 - m2)

            if final_invert:
                satin_m = (1.0 - diff) * target_alpha
            else:
                satin_m = diff * target_alpha

            # 3. Contour curve shaping
            gamma = 50.0 / max(1.0, float(final_range))
            satin_m = np.power(np.clip(satin_m, 0.0, 1.0), gamma)

            # 4. Create dedicated satin overlay layer
            satin_name = f"{target_layer.get_name()} (Satin - {label})"
            blend_mode_enum = BLEND_MODES.get(final_bmode, Gimp.LayerMode.MULTIPLY)
            satin_layer = Gimp.Layer.new(
                image,
                satin_name,
                img_w,
                img_h,
                Gimp.ImageType.RGBA_IMAGE,
                max(0.0, min(100.0, final_opacity)),
                blend_mode_enum
            )

            # Insert immediately above target layer in stack
            parent = target_layer.get_parent()
            pos = image.get_item_position(target_layer)
            image.insert_layer(satin_layer, parent, pos)

            # 5. Populate initial satin pixels
            s_arr = np.zeros((img_h, img_w, 4), dtype=np.float32)
            s_arr[:, :, 0] = final_r
            s_arr[:, :, 1] = final_g
            s_arr[:, :, 2] = final_b
            s_arr[:, :, 3] = satin_m

            s_buf = satin_layer.get_buffer()
            s_buf.set(rect, "RGBA float", s_arr.tobytes())
            s_buf.flush()
            satin_layer.update(0, 0, img_w, img_h)

            # 6. Apply Gaussian blur diffusion for Size
            blur_radius = max(0.1, float(final_size))
            filt = Gimp.DrawableFilter.new(satin_layer, "gegl:gaussian-blur", "")
            fcfg = filt.get_config()
            fcfg.set_property("std-dev-x", blur_radius / 2.0)
            fcfg.set_property("std-dev-y", blur_radius / 2.0)
            satin_layer.append_filter(filt)
            satin_layer.merge_filters()

            # 7. Strictly clip blurred pixels to target layer's silhouette
            s_buf = satin_layer.get_buffer()
            res_raw = s_buf.get(rect, 1.0, "RGBA float", Gegl.AbyssPolicy.NONE)
            res_arr = np.frombuffer(res_raw, dtype=np.float32).reshape((img_h, img_w, 4)).copy()
            res_arr[:, :, 3] *= target_alpha

            # 8. Optional film grain noise injection
            if final_noise > 0.0:
                noise_field = np.random.normal(0.0, (final_noise / 100.0) * 0.15, (img_h, img_w)).astype(np.float32)
                res_arr[:, :, 3] = np.clip(res_arr[:, :, 3] + noise_field * (target_alpha > 0.01), 0.0, 1.0) * target_alpha

            s_buf.set(rect, "RGBA float", res_arr.tobytes())
            s_buf.flush()
            satin_layer.update(0, 0, img_w, img_h)

            # 9. Layer Mask Attachment
            if mask_str == "auto":
                if has_orig_sel and orig_sel_channel is not None:
                    image.select_item(Gimp.ChannelOps.REPLACE, orig_sel_channel)
                    mask = satin_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    satin_layer.add_mask(mask)
            elif mask_str == "reveal-all":
                mask = satin_layer.create_mask(Gimp.AddMaskType.WHITE)
                satin_layer.add_mask(mask)
            elif mask_str == "conceal-all":
                mask = satin_layer.create_mask(Gimp.AddMaskType.BLACK)
                satin_layer.add_mask(mask)
            elif mask_str == "selection":
                if has_orig_sel and orig_sel_channel is not None:
                    image.select_item(Gimp.ChannelOps.REPLACE, orig_sel_channel)
                    mask = satin_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    satin_layer.add_mask(mask)

            # Restore original selection or clear
            if has_orig_sel and orig_sel_channel is not None:
                image.select_item(Gimp.ChannelOps.REPLACE, orig_sel_channel)
                image.remove_channel(orig_sel_channel)
            else:
                Gimp.Selection.none(image)

            # Set overlay layer as active layer
            image.set_selected_layers([satin_layer])

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
                    GLib.quark_from_string("gimp-satin"),
                    f"Satin generation failed: {str(e)}",
                    0
                )
            )


Gimp.main(SatinPlugin.__gtype__, sys.argv)
