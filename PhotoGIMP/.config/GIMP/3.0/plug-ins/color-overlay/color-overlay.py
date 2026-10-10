#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Color Overlay Layer Style Helper Plugin
=================================================================
Simulates Adobe Photoshop's non-destructive Color Overlay layer style:
  - Photoshop Menu: Layer > Layer Style > Color Overlay...
  - Photoshop Menu: Filters > Light and Shadow > Color Overlay (Layer Style)...
  - Photoshop Docs: Section 113-115 lines 3433-3500 (Layer Style effects and options)
  - Topics.txt: Lines 107-118, 432

Photoshop Color Overlay Architecture:
  1. Solid Color Swatch:
     - Fills layer content with a pure solid RGB color.
  2. Strict Boundary Silhouette Clipping:
     - Overlay pixels are strictly clipped to the target layer's silhouette:
       A_overlay(x, y) = A_target(x, y). Outside pixels are strictly alpha == 0.000.
       Anti-aliased and semi-transparent edges in the target layer are matched exactly.
  3. Photoshop Blend Modes:
     - Normal, Multiply, Screen, Overlay, Soft Light, Color (HSL Color), Darken, Lighten.
  4. Opacity Control:
     - Opacity slider (0.0% to 100.0%, default 100.0%).
  5. Curated Presets:
     - Standard Red, Warm Amber, Cool Cyan, Emerald Green, Royal Purple,
       Pure White, Deep Black, Monochrome Tint, and Custom Sliders.
  6. Non-Destructive Layer Architecture:
     - Dedicated overlay layer inserted directly above the target layer in the stack.
     - Target layer artwork and underlying canvas pixels remain 100% untouched (diff == 0.000000).
     - Single-step Ctrl+Z undo protection.
"""

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


PROC_NAME = "python-fu-color-overlay"

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

PRESETS = {
    "default-red": {
        "label": "Standard Red",
        "color_r": 1.0,
        "color_g": 0.0,
        "color_b": 0.0,
        "blend_mode": "normal",
        "opacity": 100.0,
    },
    "warm-amber": {
        "label": "Warm Amber",
        "color_r": 1.0,
        "color_g": 0.65,
        "color_b": 0.0,
        "blend_mode": "multiply",
        "opacity": 75.0,
    },
    "cool-cyan": {
        "label": "Cool Cyan",
        "color_r": 0.0,
        "color_g": 0.8,
        "color_b": 1.0,
        "blend_mode": "screen",
        "opacity": 80.0,
    },
    "emerald-green": {
        "label": "Emerald Green",
        "color_r": 0.0,
        "color_g": 0.75,
        "color_b": 0.35,
        "blend_mode": "overlay",
        "opacity": 85.0,
    },
    "royal-purple": {
        "label": "Royal Purple",
        "color_r": 0.55,
        "color_g": 0.15,
        "color_b": 0.85,
        "blend_mode": "soft-light",
        "opacity": 80.0,
    },
    "pure-white": {
        "label": "Pure White",
        "color_r": 1.0,
        "color_g": 1.0,
        "color_b": 1.0,
        "blend_mode": "screen",
        "opacity": 100.0,
    },
    "deep-black": {
        "label": "Deep Black",
        "color_r": 0.0,
        "color_g": 0.0,
        "color_b": 0.0,
        "blend_mode": "multiply",
        "opacity": 100.0,
    },
    "monochrome-tint": {
        "label": "Monochrome Tint",
        "color_r": 0.25,
        "color_g": 0.45,
        "color_b": 0.65,
        "blend_mode": "color",
        "opacity": 100.0,
    },
}


class ColorOverlayPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return [PROC_NAME]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_color_overlay, None)
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        # Menu Registrations
        procedure.set_menu_label("Color Overlay (Layer Style)...")
        procedure.add_menu_path("<Image>/Layer/Layer Style")
        procedure.add_menu_path("<Image>/Filters/Light and Shadow")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        procedure.set_documentation(
            "Color Overlay (Layer Style)",
            "Fills the layer content with a non-destructive solid color overlay clipped strictly to the target layer's silhouette.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Presets Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add("default-red", 0, "Standard Red", "Photoshop standard red color overlay")
        preset_choice.add("warm-amber", 1, "Warm Amber", "Warm golden amber tint")
        preset_choice.add("cool-cyan", 2, "Cool Cyan", "Cool cyan backlight overlay")
        preset_choice.add("emerald-green", 3, "Emerald Green", "Lush emerald overlay")
        preset_choice.add("royal-purple", 4, "Royal Purple", "Royal purple mood overlay")
        preset_choice.add("pure-white", 5, "Pure White", "Pure white screen highlight overlay")
        preset_choice.add("deep-black", 6, "Deep Black", "Deep black multiply shade overlay")
        preset_choice.add("monochrome-tint", 7, "Monochrome Tint", "Monochrome color tint overlay")
        preset_choice.add("custom", 8, "Custom Sliders", "Manual slider controls")

        procedure.add_choice_argument(
            "preset",
            "Preset",
            "Curated Color Overlay preset style",
            preset_choice,
            "default-red",
            GObject.ParamFlags.READWRITE
        )

        # 2. Color R (0.0 to 1.0)
        procedure.add_double_argument(
            "color-r",
            "Color Red",
            "Solid overlay red component (0.0 to 1.0)",
            0.0,
            1.0,
            1.0,
            GObject.ParamFlags.READWRITE
        )

        # 3. Color G (0.0 to 1.0)
        procedure.add_double_argument(
            "color-g",
            "Color Green",
            "Solid overlay green component (0.0 to 1.0)",
            0.0,
            1.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 4. Color B (0.0 to 1.0)
        procedure.add_double_argument(
            "color-b",
            "Color Blue",
            "Solid overlay blue component (0.0 to 1.0)",
            0.0,
            1.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 5. Blend Mode
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
            "Layer blending mode for the color overlay",
            mode_choice,
            "normal",
            GObject.ParamFlags.READWRITE
        )

        # 6. Opacity (0.0% to 100.0%)
        procedure.add_double_argument(
            "opacity",
            "Opacity (%)",
            "Color overlay layer opacity (0.0 to 100.0)",
            0.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # 7. Mask Type
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

    def run_color_overlay(self, procedure, run_mode, image, drawables, config, data):
        # Interactive GUI dialog
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("python-fu-color-overlay")
            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        # Read configuration parameters
        preset = config.get_property("preset")
        col_r = config.get_property("color-r")
        col_g = config.get_property("color-g")
        col_b = config.get_property("color-b")
        bmode_str = config.get_property("blend-mode")
        opacity_val = config.get_property("opacity")
        mask_str = config.get_property("mask-type")

        # Resolve preset values
        if preset in PRESETS and preset not in ("default-red", "custom"):
            p = PRESETS[preset]
            final_r = float(p["color_r"])
            final_g = float(p["color_g"])
            final_b = float(p["color_b"])
            final_bmode = p["blend_mode"]
            final_opacity = float(p["opacity"])
            label = p["label"]
        elif preset == "default-red":
            final_r = 1.0
            final_g = 0.0
            final_b = 0.0
            final_bmode = bmode_str if bmode_str != "normal" else "normal"
            final_opacity = float(opacity_val)
            label = "Standard Red"
        else:
            final_r = float(col_r)
            final_g = float(col_g)
            final_b = float(col_b)
            final_bmode = bmode_str
            final_opacity = float(opacity_val)
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
                    GLib.quark_from_string("gimp-color-overlay"),
                    "No valid target layer found for color overlay effect.",
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

            # 2. Create dedicated color overlay layer
            overlay_name = f"{target_layer.get_name()} (Color Overlay - {label})"
            blend_mode_enum = BLEND_MODES.get(final_bmode, Gimp.LayerMode.NORMAL)
            overlay_layer = Gimp.Layer.new(
                image,
                overlay_name,
                img_w,
                img_h,
                Gimp.ImageType.RGBA_IMAGE,
                max(0.0, min(100.0, final_opacity)),
                blend_mode_enum
            )

            # Insert immediately above target layer in stack
            parent = target_layer.get_parent()
            pos = image.get_item_position(target_layer)
            image.insert_layer(overlay_layer, parent, pos)

            # 3. Construct overlay buffer clipped strictly to target silhouette
            arr_overlay = np.zeros((img_h, img_w, 4), dtype=np.float32)
            arr_overlay[:, :, 0] = final_r
            arr_overlay[:, :, 1] = final_g
            arr_overlay[:, :, 2] = final_b
            arr_overlay[:, :, 3] = target_alpha

            ol_buf = overlay_layer.get_buffer()
            ol_buf.set(rect, "RGBA float", arr_overlay.tobytes())
            ol_buf.flush()
            overlay_layer.update(0, 0, img_w, img_h)

            # 4. Layer Mask Attachment
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
                    GLib.quark_from_string("gimp-color-overlay"),
                    f"Color overlay generation failed: {str(e)}",
                    0
                )
            )


Gimp.main(ColorOverlayPlugin.__gtype__, sys.argv)
