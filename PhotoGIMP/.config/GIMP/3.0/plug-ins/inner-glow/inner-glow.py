#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Inner Glow Layer Style Helper Plugin
==============================================================
Simulates Adobe Photoshop's non-destructive Inner Glow layer style:
  - Photoshop Menu: Layer > Layer Style > Inner Glow...
  - Photoshop Menu: Filters > Light and Shadow > Inner Glow (Layer Style)...
  - Photoshop Docs: Section 113-115 lines 3433-3500 (Layer Style effects and options)
  - Topics.txt: Lines 107-118, 432

Photoshop Inner Glow Architecture:
  1. Dual Radiance Source Modes:
     - 'edge': Glow originates from layer silhouette boundaries and radiates inward towards center.
     - 'center': Glow originates from interior core and radiates outward towards boundaries.
  2. Choke & Size Control:
     - Choke (0% to 100%): Contracts / thickens the solid glow matte boundary prior to blurring.
     - Size (0 to 200px): Halo blur radius falloff.
  3. Range Contour Control:
     - Range (1% to 100%, default 50%): Shapes opacity falloff contour curve (A' = A^(50/range)).
  4. Technique:
     - 'softer': Natural Gaussian blur falloff.
     - 'precise': Concentrated boundary radiance.
  5. Strict Boundary Clipping:
     - Glow is strictly clipped inside target layer silhouette (outside pixels are alpha == 0.000).
  6. Film Grain Noise:
     - Adds uniform texture / noise (0% to 100%) to the glow halo.
  7. Non-Destructive Layer Architecture:
     - Dedicated glow layer inserted directly above the target layer in the stack.
     - Leaves target layer and canvas pixels 100% untouched (diff == 0.000000).
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


PROC_NAME = "python-fu-inner-glow"

BLEND_MODES = {
    "screen": Gimp.LayerMode.SCREEN,
    "normal": Gimp.LayerMode.NORMAL,
    "lighten": Gimp.LayerMode.LIGHTEN_ONLY,
    "dodge": Gimp.LayerMode.DODGE,
    "addition": Gimp.LayerMode.ADDITION,
    "overlay": Gimp.LayerMode.OVERLAY,
    "multiply": Gimp.LayerMode.MULTIPLY,
}

PRESETS = {
    "default": {
        "label": "Photoshop Standard",
        "source": "edge",
        "technique": "softer",
        "choke": 0.0,
        "size": 10.0,
        "range": 50.0,
        "opacity": 75.0,
        "blend_mode": "screen",
        "color_r": 1.0,
        "color_g": 0.95,
        "color_b": 0.60,
        "noise": 0.0,
    },
    "neon-cyan": {
        "label": "Neon Edge Radiance",
        "source": "edge",
        "technique": "softer",
        "choke": 15.0,
        "size": 15.0,
        "range": 50.0,
        "opacity": 85.0,
        "blend_mode": "screen",
        "color_r": 0.0,
        "color_g": 0.95,
        "color_b": 1.0,
        "noise": 0.0,
    },
    "candlelight": {
        "label": "Candlelight Warmth",
        "source": "edge",
        "technique": "softer",
        "choke": 10.0,
        "size": 20.0,
        "range": 60.0,
        "opacity": 80.0,
        "blend_mode": "addition",
        "color_r": 1.0,
        "color_g": 0.75,
        "color_b": 0.20,
        "noise": 0.0,
    },
    "center-spotlight": {
        "label": "Center Spotlight",
        "source": "center",
        "technique": "softer",
        "choke": 0.0,
        "size": 25.0,
        "range": 50.0,
        "opacity": 85.0,
        "blend_mode": "screen",
        "color_r": 1.0,
        "color_g": 1.0,
        "color_b": 1.0,
        "noise": 0.0,
    },
    "cyberpunk-core": {
        "label": "Cyberpunk Core",
        "source": "center",
        "technique": "precise",
        "choke": 20.0,
        "size": 18.0,
        "range": 45.0,
        "opacity": 90.0,
        "blend_mode": "dodge",
        "color_r": 1.0,
        "color_g": 0.0,
        "color_b": 0.80,
        "noise": 0.0,
    },
    "subtle-rim": {
        "label": "Subtle Rim Inset",
        "source": "edge",
        "technique": "softer",
        "choke": 0.0,
        "size": 5.0,
        "range": 50.0,
        "opacity": 50.0,
        "blend_mode": "screen",
        "color_r": 1.0,
        "color_g": 1.0,
        "color_b": 0.90,
        "noise": 0.0,
    },
}


class InnerGlowPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return [PROC_NAME]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_inner_glow, None)
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        # Menu Registrations
        procedure.set_menu_label("Inner Glow (Layer Style)...")
        procedure.add_menu_path("<Image>/Layer/Layer Style")
        procedure.add_menu_path("<Image>/Filters/Light and Shadow")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        procedure.set_documentation(
            "Inner Glow (Layer Style)",
            "Generates a non-destructive inner glow layer style with Edge/Center source modes, Choke contraction, Size blur radius, Range contour modulation, blend modes, and opacity.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Presets Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add("default", 0, "Photoshop Standard", "Standard warm edge inner glow")
        preset_choice.add("neon-cyan", 1, "Neon Edge Radiance", "Vivid neon cyan edge glow with choke")
        preset_choice.add("candlelight", 2, "Candlelight Warmth", "Warm golden ambient edge glow")
        preset_choice.add("center-spotlight", 3, "Center Spotlight", "Interior center radial spotlight")
        preset_choice.add("cyberpunk-core", 4, "Cyberpunk Core", "Magenta concentrated center glow")
        preset_choice.add("subtle-rim", 5, "Subtle Rim Inset", "Delicate 5px rim highlight")
        preset_choice.add("custom", 6, "Custom Sliders", "Manual slider controls")

        procedure.add_choice_argument(
            "preset",
            "Preset",
            "Curated Inner Glow preset style",
            preset_choice,
            "default",
            GObject.ParamFlags.READWRITE
        )

        # 2. Source Choice
        source_choice = Gimp.Choice.new()
        source_choice.add("edge", 0, "Edge", "Radiates inward from layer boundaries towards center")
        source_choice.add("center", 1, "Center", "Radiates outward from interior core towards boundaries")

        procedure.add_choice_argument(
            "source",
            "Source",
            "Glow source (edge: inward from boundary, center: outward from core)",
            source_choice,
            "edge",
            GObject.ParamFlags.READWRITE
        )

        # 3. Technique Choice
        tech_choice = Gimp.Choice.new()
        tech_choice.add("softer", 0, "Softer", "Natural smooth Gaussian blur falloff")
        tech_choice.add("precise", 1, "Precise", "Concentrated boundary radiance")

        procedure.add_choice_argument(
            "technique",
            "Technique",
            "Falloff technique (softer, precise)",
            tech_choice,
            "softer",
            GObject.ParamFlags.READWRITE
        )

        # 4. Choke (0.0% to 100.0%)
        procedure.add_double_argument(
            "choke",
            "Choke (%)",
            "Contracts / thickens solid glow boundary prior to blur (0.0 to 100.0)",
            0.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 5. Size (0.0 to 200.0 px)
        procedure.add_double_argument(
            "size",
            "Size (px)",
            "Inner glow halo blur radius in pixels (0.0 to 200.0)",
            0.0,
            200.0,
            10.0,
            GObject.ParamFlags.READWRITE
        )

        # 6. Range (1.0% to 100.0%)
        procedure.add_double_argument(
            "range",
            "Range (%)",
            "Opacity falloff contour curve modulation (1.0 to 100.0, default 50.0)",
            1.0,
            100.0,
            50.0,
            GObject.ParamFlags.READWRITE
        )

        # 7. Opacity (0.0% to 100.0%)
        procedure.add_double_argument(
            "opacity",
            "Opacity (%)",
            "Inner glow layer opacity (0.0 to 100.0)",
            0.0,
            100.0,
            75.0,
            GObject.ParamFlags.READWRITE
        )

        # 8. Blend Mode
        mode_choice = Gimp.Choice.new()
        mode_choice.add("screen", 0, "Screen", "Screen lightening mode (default)")
        mode_choice.add("normal", 1, "Normal", "Normal standard blend")
        mode_choice.add("lighten", 2, "Lighten", "Lighten only mode")
        mode_choice.add("dodge", 3, "Color Dodge", "Vivid color dodge mode")
        mode_choice.add("addition", 4, "Linear Dodge (Add)", "Linear dodge / addition mode")
        mode_choice.add("overlay", 5, "Overlay", "Contrast overlay mode")
        mode_choice.add("multiply", 6, "Multiply", "Darkening multiply mode")

        procedure.add_choice_argument(
            "blend-mode",
            "Blend Mode",
            "Layer blend mode (screen, normal, lighten, dodge, addition, overlay, multiply)",
            mode_choice,
            "screen",
            GObject.ParamFlags.READWRITE
        )

        # 9-11. Glow Color RGB
        procedure.add_double_argument("glow-r", "Glow Red", "Inner glow Red channel (0.0 to 1.0)", 0.0, 1.0, 1.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("glow-g", "Glow Green", "Inner glow Green channel (0.0 to 1.0)", 0.0, 1.0, 0.95, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("glow-b", "Glow Blue", "Inner glow Blue channel (0.0 to 1.0)", 0.0, 1.0, 0.60, GObject.ParamFlags.READWRITE)

        # 12. Noise (0.0% to 100.0%)
        procedure.add_double_argument(
            "noise",
            "Noise (%)",
            "Film grain noise texture percentage (0.0 to 100.0)",
            0.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 13. Mask Type
        mask_choice = Gimp.Choice.new()
        mask_choice.add("auto", 0, "Auto (Selection or None)", "Attach selection mask if selection exists, else none")
        mask_choice.add("none", 1, "None", "No layer mask attached")
        mask_choice.add("reveal-all", 2, "Reveal All (White)", "Attach full white layer mask")
        mask_choice.add("conceal-all", 3, "Conceal All (Black)", "Attach full black layer mask for brush painting")
        mask_choice.add("selection", 4, "Selection", "Attach active selection mask")

        procedure.add_choice_argument(
            "mask-type",
            "Layer Mask",
            "Layer mask type (auto, none, reveal-all, conceal-all, selection)",
            mask_choice,
            "auto",
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run_inner_glow(self, procedure, run_mode, image, drawables, config, run_data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("python-fu-inner-glow")
            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        # Read configuration parameters
        preset = config.get_property("preset")
        source_val = config.get_property("source")
        tech_val = config.get_property("technique")
        choke_val = config.get_property("choke")
        size_val = config.get_property("size")
        range_val = config.get_property("range")
        opacity_val = config.get_property("opacity")
        bmode_str = config.get_property("blend-mode")
        gl_r = config.get_property("glow-r")
        gl_g = config.get_property("glow-g")
        gl_b = config.get_property("glow-b")
        noise_val = config.get_property("noise")
        mask_str = config.get_property("mask-type")

        # Resolve preset values
        if preset in PRESETS and preset not in ("default", "custom"):
            p = PRESETS[preset]
            final_source = p["source"]
            final_tech = p["technique"]
            final_choke = float(p["choke"])
            final_size = float(p["size"])
            final_range = float(p["range"])
            final_opacity = float(p["opacity"])
            final_bmode = p["blend_mode"]
            final_r = float(p["color_r"])
            final_g = float(p["color_g"])
            final_b = float(p["color_b"])
            final_noise = float(p["noise"])
            label = p["label"]
        else:
            final_source = source_val
            final_tech = tech_val
            final_choke = float(choke_val)
            final_size = float(size_val)
            final_range = float(range_val)
            final_opacity = float(opacity_val)
            final_bmode = bmode_str
            final_r = float(gl_r)
            final_g = float(gl_g)
            final_b = float(gl_b)
            final_noise = float(noise_val)
            label = "Photoshop Standard" if preset == "default" else "Custom"

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
                    GLib.quark_from_string("gimp-inner-glow"),
                    "No valid target layer found for inner glow effect.",
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

            # 2. Create dedicated inner glow layer
            glow_name = f"{target_layer.get_name()} (Inner Glow - {label})"
            blend_mode_enum = BLEND_MODES.get(final_bmode, Gimp.LayerMode.SCREEN)
            glow_layer = Gimp.Layer.new(
                image,
                glow_name,
                img_w,
                img_h,
                Gimp.ImageType.RGBA_IMAGE,
                max(0.0, min(100.0, final_opacity)),
                blend_mode_enum
            )

            # Insert immediately above target layer in stack
            parent = target_layer.get_parent()
            pos = image.get_item_position(target_layer)
            image.insert_layer(glow_layer, parent, pos)

            # 3. Generate Inner Glow field based on Source mode
            glow_color = Gegl.Color.new(f"rgb({final_r:.4f}, {final_g:.4f}, {final_b:.4f})")
            Gimp.context_set_foreground(glow_color)

            if final_source == "edge":
                # Edge source: glow originates at silhouette boundary and radiates inward
                image.select_item(Gimp.ChannelOps.REPLACE, target_layer)
                Gimp.Selection.invert(image)

                choke_px = int(round((final_choke / 100.0) * final_size))
                if choke_px > 0:
                    Gimp.Selection.grow(image, choke_px)

                glow_layer.edit_fill(Gimp.FillType.FOREGROUND)
                Gimp.Selection.none(image)

                rem_blur = max(0.5, (1.0 - (final_choke / 100.0)) * final_size)
                std_dev = (rem_blur / 3.0) if final_tech == "precise" else (rem_blur / 2.0)

                filt_blur = Gimp.DrawableFilter.new(glow_layer, "gegl:gaussian-blur", "")
                fcfg = filt_blur.get_config()
                fcfg.set_property("std-dev-x", std_dev)
                fcfg.set_property("std-dev-y", std_dev)
                glow_layer.append_filter(filt_blur)
                glow_layer.merge_filters()

                # Read glow buffer and scale boundary step response (0.5 -> 1.0)
                glow_buf = glow_layer.get_buffer()
                raw_glow = glow_buf.get(rect, 1.0, "RGBA float", Gegl.AbyssPolicy.NONE)
                arr_glow = np.frombuffer(raw_glow, dtype=np.float32).reshape((img_h, img_w, 4)).copy()
                glow_a = np.clip(arr_glow[:, :, 3] * 2.0, 0.0, 1.0)

            else:
                # Center source: glow originates from interior core and radiates outward towards edges
                image.select_item(Gimp.ChannelOps.REPLACE, target_layer)

                shrink_px = max(1, int(round((1.0 - (final_choke / 100.0)) * (final_size / 2.0))))
                Gimp.Selection.shrink(image, shrink_px)

                glow_layer.edit_fill(Gimp.FillType.FOREGROUND)
                Gimp.Selection.none(image)

                rem_blur = max(0.5, final_size)
                std_dev = (rem_blur / 3.0) if final_tech == "precise" else (rem_blur / 2.0)

                filt_blur = Gimp.DrawableFilter.new(glow_layer, "gegl:gaussian-blur", "")
                fcfg = filt_blur.get_config()
                fcfg.set_property("std-dev-x", std_dev)
                fcfg.set_property("std-dev-y", std_dev)
                glow_layer.append_filter(filt_blur)
                glow_layer.merge_filters()

                glow_buf = glow_layer.get_buffer()
                raw_glow = glow_buf.get(rect, 1.0, "RGBA float", Gegl.AbyssPolicy.NONE)
                arr_glow = np.frombuffer(raw_glow, dtype=np.float32).reshape((img_h, img_w, 4)).copy()
                glow_a = np.clip(arr_glow[:, :, 3], 0.0, 1.0)

            # 4. Range contour modulation
            mask_inner = glow_a > 0.001
            if abs(final_range - 50.0) > 1.0 and np.any(mask_inner):
                gamma_exp = 50.0 / max(1.0, final_range)
                glow_a[mask_inner] = np.power(np.clip(glow_a[mask_inner], 0.0, 1.0), gamma_exp)

            # 5. Film grain noise texture
            if final_noise > 0.0 and np.any(mask_inner):
                noise_factor = (final_noise / 100.0) * 0.40
                rng = np.random.RandomState(42)
                grain = (rng.rand(img_h, img_w).astype(np.float32) - 0.5) * noise_factor
                glow_a[mask_inner] = np.clip(glow_a[mask_inner] + grain[mask_inner], 0.0, 1.0)

            # 6. Strict Boundary Silhouette Clipping to Target Layer
            glow_a *= target_alpha

            # Ensure pure glow color fidelity on RGB channels
            arr_glow[:, :, 0] = final_r
            arr_glow[:, :, 1] = final_g
            arr_glow[:, :, 2] = final_b
            arr_glow[:, :, 3] = glow_a

            # Write processed buffer back
            glow_buf.set(rect, "RGBA float", arr_glow.tobytes())
            glow_buf.flush()
            glow_layer.update(0, 0, img_w, img_h)

            # 7. Layer Mask Attachment
            if mask_str == "auto":
                if has_orig_sel and orig_sel_channel is not None:
                    image.select_item(Gimp.ChannelOps.REPLACE, orig_sel_channel)
                    mask = glow_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    glow_layer.add_mask(mask)
            elif mask_str == "reveal-all":
                mask = glow_layer.create_mask(Gimp.AddMaskType.WHITE)
                glow_layer.add_mask(mask)
            elif mask_str == "conceal-all":
                mask = glow_layer.create_mask(Gimp.AddMaskType.BLACK)
                glow_layer.add_mask(mask)
            elif mask_str == "selection":
                if has_orig_sel and orig_sel_channel is not None:
                    image.select_item(Gimp.ChannelOps.REPLACE, orig_sel_channel)
                    mask = glow_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    glow_layer.add_mask(mask)

            # Restore original selection or clear
            if has_orig_sel and orig_sel_channel is not None:
                image.select_item(Gimp.ChannelOps.REPLACE, orig_sel_channel)
                image.remove_channel(orig_sel_channel)
            else:
                Gimp.Selection.none(image)

            # Set glow layer as active layer
            image.set_selected_layers([glow_layer])

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
                    GLib.quark_from_string("gimp-inner-glow"),
                    f"Inner glow generation failed: {str(e)}",
                    0
                )
            )


Gimp.main(InnerGlowPlugin.__gtype__, sys.argv)
