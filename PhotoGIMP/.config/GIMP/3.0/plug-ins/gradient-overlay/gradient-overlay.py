#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Gradient Overlay Layer Style Helper Plugin
====================================================================
Simulates Adobe Photoshop's non-destructive Gradient Overlay layer style:
  - Photoshop Menu: Layer > Layer Style > Gradient Overlay...
  - Photoshop Menu: Filters > Light and Shadow > Gradient Overlay (Layer Style)...
  - Photoshop Docs: Section 113-115 lines 3433-3500 (Layer Style effects and options)
  - Topics.txt: Lines 107-118, 432

Photoshop Gradient Overlay Architecture:
  1. 5 Photoshop Gradient Geometry Styles:
     - Linear: Directional gradient transition.
     - Radial: Concentric circular falloff from center.
     - Angle: Conical rotational sweep around center.
     - Reflected: Bilateral symmetric linear reflection radiating from center.
     - Diamond: Geometric diamond / rhomboid falloff.
  2. Geometric Controls:
     - Angle (-180.0° to 180.0°, default 90.0° vertical).
     - Scale (10.0% to 500.0%, default 100.0%).
     - Reverse: Flips gradient color progression.
     - Align with Layer: Centers geometry to target layer boundaries.
     - Dither: Anti-banding dithering toggle.
  3. Curated Presets:
     - Black-White, Foreground-Background, Vintage Sepia, Sunset Horizon,
       Cyberpunk Neon, Ocean Breeze, Golden Glow, and Custom Start/End RGB.
  4. Strict Boundary Silhouette Clipping:
     - Overlay pixels are strictly clipped to the target layer's silhouette:
       A_overlay(x, y) = A_gradient(x, y) * A_target(x, y).
       Outside pixels are strictly alpha == 0.000.
       Anti-aliased and semi-transparent edges in the target layer are matched exactly.
  5. Photoshop Blend Modes & Opacity:
     - Normal, Multiply, Screen, Overlay, Soft Light, Color (HSL Color), Darken, Lighten.
     - Opacity slider (0.0% to 100.0%, default 100.0%).
  6. Non-Destructive Layer Architecture:
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


PROC_NAME = "python-fu-gradient-overlay"

BLEND_MODES = {
    "normal": Gimp.LayerMode.NORMAL,
    "multiply": Gimp.LayerMode.MULTIPLY,
    "screen": Gimp.LayerMode.SCREEN,
    "overlay": Gimp.LayerMode.OVERLAY,
    "soft-light": Gimp.LayerMode.SOFTLIGHT,
    "color": Gimp.LayerMode.HSL_COLOR,
    "darken": Gimp.LayerMode.DARKEN_ONLY,
    "lighten": Gimp.LayerMode.LIGHTEN_ONLY,
}

GRADIENT_STYLES = {
    "linear": Gimp.GradientType.LINEAR,
    "radial": Gimp.GradientType.RADIAL,
    "angle": Gimp.GradientType.CONICAL_ASYMMETRIC,
    "reflected": Gimp.GradientType.BILINEAR,
    "diamond": Gimp.GradientType.SQUARE,
}

PRESETS = {
    "black-white": {
        "label": "Black to White",
        "start_r": 0.0, "start_g": 0.0, "start_b": 0.0,
        "end_r": 1.0, "end_g": 1.0, "end_b": 1.0,
    },
    "fg-to-bg": {
        "label": "Foreground to Background",
        "start_r": 0.0, "start_g": 0.0, "start_b": 0.0,
        "end_r": 1.0, "end_g": 1.0, "end_b": 1.0,
    },
    "vintage-sepia": {
        "label": "Vintage Sepia",
        "start_r": 0.169, "start_g": 0.114, "start_b": 0.047,
        "end_r": 0.965, "end_g": 0.898, "end_b": 0.773,
    },
    "sunset-horizon": {
        "label": "Sunset Horizon",
        "start_r": 0.753, "start_g": 0.224, "start_b": 0.169,
        "end_r": 0.953, "end_g": 0.612, "end_b": 0.071,
    },
    "cyberpunk-neon": {
        "label": "Cyberpunk Neon",
        "start_r": 1.000, "start_g": 0.000, "start_b": 0.498,
        "end_r": 0.000, "end_g": 0.941, "end_b": 1.000,
    },
    "ocean-breeze": {
        "label": "Ocean Breeze",
        "start_r": 0.102, "start_g": 0.212, "start_b": 0.365,
        "end_r": 0.220, "end_g": 0.698, "end_b": 0.675,
    },
    "golden-glow": {
        "label": "Golden Glow",
        "start_r": 0.718, "start_g": 0.475, "start_b": 0.122,
        "end_r": 0.965, "end_g": 0.878, "end_b": 0.369,
    },
}


class GradientOverlayPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return [PROC_NAME]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_gradient_overlay, None)
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        # Menu Registrations
        procedure.set_menu_label("Gradient Overlay (Layer Style)...")
        procedure.add_menu_path("<Image>/Layer/Layer Style")
        procedure.add_menu_path("<Image>/Filters/Light and Shadow")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        procedure.set_documentation(
            "Gradient Overlay (Layer Style)",
            "Renders a non-destructive multi-style gradient overlay clipped strictly to the target layer's silhouette.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add("black-white", 0, "Black to White", "Classic black to white gradient")
        preset_choice.add("fg-to-bg", 1, "Foreground to Background", "Active toolbox foreground to background")
        preset_choice.add("vintage-sepia", 2, "Vintage Sepia", "Warm antique sepia tones")
        preset_choice.add("sunset-horizon", 3, "Sunset Horizon", "Warm crimson to orange sunset")
        preset_choice.add("cyberpunk-neon", 4, "Cyberpunk Neon", "High energy pink to electric cyan")
        preset_choice.add("ocean-breeze", 5, "Ocean Breeze", "Deep blue to fresh aquamarine")
        preset_choice.add("golden-glow", 6, "Golden Glow", "Rich amber to pale yellow glow")
        preset_choice.add("custom", 7, "Custom Colors", "User-defined dual-tone RGB endpoints")

        procedure.add_choice_argument(
            "preset",
            "Preset",
            "Curated gradient color palette preset",
            preset_choice,
            "black-white",
            GObject.ParamFlags.READWRITE
        )

        # 2. Style Choice
        style_choice = Gimp.Choice.new()
        style_choice.add("linear", 0, "Linear", "Linear directional gradient")
        style_choice.add("radial", 1, "Radial", "Concentric circular radial gradient")
        style_choice.add("angle", 2, "Angle", "Conical 360-degree sweep gradient")
        style_choice.add("reflected", 3, "Reflected", "Bilateral symmetric reflected gradient")
        style_choice.add("diamond", 4, "Diamond", "Rhomboid diamond gradient falloff")

        procedure.add_choice_argument(
            "style",
            "Style",
            "Photoshop gradient geometry style",
            style_choice,
            "linear",
            GObject.ParamFlags.READWRITE
        )

        # 3. Angle (-180.0° to 180.0°)
        procedure.add_double_argument(
            "angle",
            "Angle (°)",
            "Gradient rotation angle in degrees (-180.0 to 180.0)",
            -180.0,
            180.0,
            90.0,
            GObject.ParamFlags.READWRITE
        )

        # 4. Scale (10.0% to 500.0%)
        procedure.add_double_argument(
            "scale",
            "Scale (%)",
            "Gradient spatial scale percentage (10.0 to 500.0)",
            10.0,
            500.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # 5. Reverse (boolean)
        procedure.add_boolean_argument(
            "reverse",
            "Reverse",
            "Reverse gradient color progression",
            False,
            GObject.ParamFlags.READWRITE
        )

        # 6. Align with Layer (boolean)
        procedure.add_boolean_argument(
            "align-layer",
            "Align with Layer",
            "Center gradient coordinates to target layer boundaries",
            True,
            GObject.ParamFlags.READWRITE
        )

        # 7. Dither (boolean)
        procedure.add_boolean_argument(
            "dither",
            "Dither",
            "Enable anti-banding dithering",
            True,
            GObject.ParamFlags.READWRITE
        )

        # 8. Blend Mode
        mode_choice = Gimp.Choice.new()
        mode_choice.add("normal", 0, "Normal", "Normal standard blend mode")
        mode_choice.add("multiply", 1, "Multiply", "Multiply darkening mode")
        mode_choice.add("screen", 2, "Screen", "Screen lightening mode")
        mode_choice.add("overlay", 3, "Overlay", "Overlay contrast mode")
        mode_choice.add("soft-light", 4, "Soft Light", "Soft light subtle tint mode")
        mode_choice.add("color", 5, "Color", "Color (HSL Color) chrominance tint mode")
        mode_choice.add("darken", 6, "Darken", "Darken only mode")
        mode_choice.add("lighten", 7, "Lighten", "Lighten only mode")

        procedure.add_choice_argument(
            "blend-mode",
            "Blend Mode",
            "Layer blending mode for the gradient overlay",
            mode_choice,
            "normal",
            GObject.ParamFlags.READWRITE
        )

        # 9. Opacity (0.0% to 100.0%)
        procedure.add_double_argument(
            "opacity",
            "Opacity (%)",
            "Gradient overlay layer opacity (0.0 to 100.0)",
            0.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # 10. Start Color RGB
        procedure.add_double_argument("start-r", "Start Red", "Custom start red (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("start-g", "Start Green", "Custom start green (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("start-b", "Start Blue", "Custom start blue (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)

        # 11. End Color RGB
        procedure.add_double_argument("end-r", "End Red", "Custom end red (0.0 to 1.0)", 0.0, 1.0, 1.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("end-g", "End Green", "Custom end green (0.0 to 1.0)", 0.0, 1.0, 1.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("end-b", "End Blue", "Custom end blue (0.0 to 1.0)", 0.0, 1.0, 1.0, GObject.ParamFlags.READWRITE)

        # 12. Mask Type
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

    def run_gradient_overlay(self, procedure, run_mode, image, drawables, config, data):
        # Interactive GUI dialog
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("python-fu-gradient-overlay")
            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        # Read configuration parameters
        preset = config.get_property("preset")
        style = config.get_property("style")
        angle_val = config.get_property("angle")
        scale_val = config.get_property("scale")
        reverse_val = config.get_property("reverse")
        align_layer = config.get_property("align-layer")
        dither_val = config.get_property("dither")
        bmode_str = config.get_property("blend-mode")
        opacity_val = config.get_property("opacity")
        start_r = config.get_property("start-r")
        start_g = config.get_property("start-g")
        start_b = config.get_property("start-b")
        end_r = config.get_property("end-r")
        end_g = config.get_property("end-g")
        end_b = config.get_property("end-b")
        mask_str = config.get_property("mask-type")

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
                    GLib.quark_from_string("gimp-gradient-overlay"),
                    "No valid target layer found for gradient overlay effect.",
                    0
                )
            )

        pdb = Gimp.get_pdb()
        grad_proc = pdb.lookup_procedure("gimp-drawable-edit-gradient-fill")
        if grad_proc is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-gradient-overlay"),
                    "Procedure gimp-drawable-edit-gradient-fill not found in PDB.",
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

            # 2. Configure gradient colors
            if preset in PRESETS and preset not in ("fg-to-bg", "custom"):
                p = PRESETS[preset]
                Gimp.context_set_gradient_fg_bg_rgb()
                Gimp.context_set_foreground(Gegl.Color.new(f"rgb({p['start_r']:.4f}, {p['start_g']:.4f}, {p['start_b']:.4f})"))
                Gimp.context_set_background(Gegl.Color.new(f"rgb({p['end_r']:.4f}, {p['end_g']:.4f}, {p['end_b']:.4f})"))
                label = p["label"]
            elif preset == "custom":
                Gimp.context_set_gradient_fg_bg_rgb()
                Gimp.context_set_foreground(Gegl.Color.new(f"rgb({start_r:.4f}, {start_g:.4f}, {start_b:.4f})"))
                Gimp.context_set_background(Gegl.Color.new(f"rgb({end_r:.4f}, {end_g:.4f}, {end_b:.4f})"))
                label = "Custom"
            else:  # fg-to-bg
                Gimp.context_set_gradient_fg_bg_rgb()
                label = "FG to BG"

            Gimp.context_set_gradient_reverse(reverse_val)

            # 3. Calculate geometry endpoints
            if align_layer:
                offs = target_layer.get_offsets()
                off_x, off_y = float(offs[-2]), float(offs[-1])
                lw = float(target_layer.get_width())
                lh = float(target_layer.get_height())
                cx = float(off_x) + lw * 0.5
                cy = float(off_y) + lh * 0.5
                D = 0.5 * max(lw, lh) * (max(10.0, min(500.0, scale_val)) / 100.0)
            else:
                cx = float(img_w) * 0.5
                cy = float(img_h) * 0.5
                D = 0.5 * max(float(img_w), float(img_h)) * (max(10.0, min(500.0, scale_val)) / 100.0)

            rad = math.radians(angle_val)
            dx = D * math.cos(rad)
            dy = -D * math.sin(rad)

            if style == "linear":
                x1 = cx - dx
                y1 = cy - dy
                x2 = cx + dx
                y2 = cy + dy
            else:
                x1 = cx
                y1 = cy
                x2 = cx + dx
                y2 = cy + dy

            # 4. Create dedicated gradient overlay layer
            overlay_name = f"{target_layer.get_name()} (Gradient Overlay - {style.capitalize()})"
            blend_mode_enum = BLEND_MODES.get(bmode_str, Gimp.LayerMode.NORMAL)
            overlay_layer = Gimp.Layer.new(
                image,
                overlay_name,
                img_w,
                img_h,
                Gimp.ImageType.RGBA_IMAGE,
                max(0.0, min(100.0, opacity_val)),
                blend_mode_enum
            )

            # Insert immediately above target layer in stack
            parent = target_layer.get_parent()
            pos = image.get_item_position(target_layer)
            image.insert_layer(overlay_layer, parent, pos)

            # 5. Render gradient onto overlay layer
            Gimp.Selection.none(image)
            gtype = GRADIENT_STYLES.get(style, Gimp.GradientType.LINEAR)
            cfg_grad = grad_proc.create_config()
            cfg_grad.set_property("drawable", overlay_layer)
            cfg_grad.set_property("gradient-type", gtype)
            cfg_grad.set_property("offset", 0.0)
            cfg_grad.set_property("supersample", False)
            cfg_grad.set_property("dither", dither_val)
            cfg_grad.set_property("x1", x1)
            cfg_grad.set_property("y1", y1)
            cfg_grad.set_property("x2", x2)
            cfg_grad.set_property("y2", y2)
            grad_proc.run(cfg_grad)

            # 6. Strictly clip gradient overlay to target layer's silhouette
            ol_buf = overlay_layer.get_buffer()
            raw_ol = ol_buf.get(rect, 1.0, "RGBA float", Gegl.AbyssPolicy.NONE)
            arr_ol = np.frombuffer(raw_ol, dtype=np.float32).reshape((img_h, img_w, 4)).copy()
            arr_ol[:, :, 3] *= target_alpha

            ol_buf.set(rect, "RGBA float", arr_ol.tobytes())
            ol_buf.flush()
            overlay_layer.update(0, 0, img_w, img_h)

            # 7. Layer Mask Attachment
            if mask_str == "auto":
                if has_orig_sel and orig_sel_channel is not None:
                    image.select_item(Gimp.ChannelOps.REPLACE, orig_sel_channel)
                    mask = overlay_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    overlay_layer.add_mask(mask)
            elif mask_str == "reveal-all":
                mask = overlay_layer.create_mask(Gimp.AddMaskType.WHITE)
                overlay_layer.add_mask(mask)
            elif mask_str == "conceal-all":
                mask = overlay_layer.create_mask(Gimp.AddMaskType.BLACK)
                overlay_layer.add_mask(mask)
            elif mask_str == "selection":
                if has_orig_sel and orig_sel_channel is not None:
                    image.select_item(Gimp.ChannelOps.REPLACE, orig_sel_channel)
                    mask = overlay_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    overlay_layer.add_mask(mask)

            # Restore original selection or clear
            if has_orig_sel and orig_sel_channel is not None:
                image.select_item(Gimp.ChannelOps.REPLACE, orig_sel_channel)
                image.remove_channel(orig_sel_channel)
            else:
                Gimp.Selection.none(image)

            # Set overlay layer as active layer
            image.set_selected_layers([overlay_layer])

            image.undo_group_end()
            Gimp.context_pop()
            Gimp.displays_flush()

            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as e:
            image.undo_group_end()
            Gimp.context_pop()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-gradient-overlay"),
                    f"Gradient overlay generation failed: {str(e)}",
                    0
                )
            )


Gimp.main(GradientOverlayPlugin.__gtype__, sys.argv)
