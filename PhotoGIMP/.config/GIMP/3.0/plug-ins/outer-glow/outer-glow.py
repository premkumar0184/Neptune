#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Outer Glow Layer Style Helper Plugin
==============================================================
Simulates Adobe Photoshop's non-destructive Outer Glow layer style:
  - Photoshop Menu: Layer > Layer Style > Outer Glow...
  - Photoshop Menu: Filters > Light and Shadow > Outer Glow (Layer Style)...
  - Photoshop Docs: Section 113-115 lines 3433-3500 (Layer Style effects and options)
  - Topics.txt: Lines 107-118, 432

Photoshop Outer Glow Architecture:
  1. Omnidirectional Radiance:
     - Emanates outward equally in all directions from the layer silhouette boundary.
  2. Spread & Size Control:
     - Spread (0% to 100%): Expands / thickens the solid glow matte prior to blurring.
       Spread pixels = round((spread / 100.0) * size).
     - Size (0 to 200px): Blur radius / halo softness.
       Remaining blur = (1.0 - (spread / 100.0)) * size.
  3. Range Contour Control:
     - Range (1% to 100%, default 50%): Controls opacity falloff contour of the glow.
       Exponent = 50.0 / range. At range > 50%, glow retains brightness further out.
  4. Technique:
     - 'softer': Natural Gaussian blur falloff.
     - 'precise': Crisp concentrated edge radiance.
  5. Layer Knocks Out Glow:
     - When enabled (default True), the source layer's silhouette is subtracted / cleared
       from the glow layer, keeping solid parent pixels crisp and untinted.
  6. Film Grain Noise:
     - Adds uniform texture / noise (0% to 100%) to the glow halo.
  7. Non-Destructive Layer Architecture:
     - Dedicated glow layer inserted immediately beneath the target layer.
     - Leaves the target layer and background pixels 100% untouched (diff == 0.000000).
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


PROC_NAME = "python-fu-outer-glow"

BLEND_MODES = {
    "screen": Gimp.LayerMode.SCREEN,
    "normal": Gimp.LayerMode.NORMAL,
    "lighten": Gimp.LayerMode.LIGHTEN_ONLY,
    "dodge": Gimp.LayerMode.DODGE,
    "addition": Gimp.LayerMode.ADDITION,
}

PRESETS = {
    "default": {
        "label": "Photoshop Standard",
        "technique": "softer",
        "spread": 0.0,
        "size": 15.0,
        "range": 50.0,
        "opacity": 75.0,
        "blend_mode": "screen",
        "color_r": 1.0,
        "color_g": 0.95,
        "color_b": 0.60,
        "knockout": True,
        "noise": 0.0,
    },
    "neon-cyan": {
        "label": "Neon Cyan Halo",
        "technique": "softer",
        "spread": 10.0,
        "size": 25.0,
        "range": 50.0,
        "opacity": 85.0,
        "blend_mode": "screen",
        "color_r": 0.0,
        "color_g": 0.90,
        "color_b": 1.0,
        "knockout": True,
        "noise": 0.0,
    },
    "golden-radiance": {
        "label": "Golden Radiance",
        "technique": "softer",
        "spread": 15.0,
        "size": 20.0,
        "range": 55.0,
        "opacity": 80.0,
        "blend_mode": "dodge",
        "color_r": 1.0,
        "color_g": 0.80,
        "color_b": 0.20,
        "knockout": True,
        "noise": 0.0,
    },
    "ethereal-white": {
        "label": "Ethereal White",
        "technique": "softer",
        "spread": 5.0,
        "size": 30.0,
        "range": 50.0,
        "opacity": 70.0,
        "blend_mode": "screen",
        "color_r": 1.0,
        "color_g": 1.0,
        "color_b": 1.0,
        "knockout": True,
        "noise": 0.0,
    },
    "magical-magenta": {
        "label": "Magical Magenta",
        "technique": "softer",
        "spread": 10.0,
        "size": 20.0,
        "range": 50.0,
        "opacity": 80.0,
        "blend_mode": "screen",
        "color_r": 1.0,
        "color_g": 0.20,
        "color_b": 0.90,
        "knockout": True,
        "noise": 0.0,
    },
    "radioactive-green": {
        "label": "Radioactive Green",
        "technique": "softer",
        "spread": 20.0,
        "size": 25.0,
        "range": 60.0,
        "opacity": 85.0,
        "blend_mode": "screen",
        "color_r": 0.20,
        "color_g": 1.0,
        "color_b": 0.20,
        "knockout": True,
        "noise": 0.0,
    },
    "subtle-soft": {
        "label": "Subtle Soft",
        "technique": "softer",
        "spread": 0.0,
        "size": 10.0,
        "range": 50.0,
        "opacity": 50.0,
        "blend_mode": "screen",
        "color_r": 1.0,
        "color_g": 0.98,
        "color_b": 0.90,
        "knockout": True,
        "noise": 0.0,
    },
    "custom": {
        "label": "Custom Sliders",
        "technique": "softer",
        "spread": 0.0,
        "size": 15.0,
        "range": 50.0,
        "opacity": 75.0,
        "blend_mode": "screen",
        "color_r": 1.0,
        "color_g": 0.95,
        "color_b": 0.60,
        "knockout": True,
        "noise": 0.0,
    }
}


class OuterGlowPlugin(Gimp.PlugIn):

    def do_query_procedures(self):
        return [PROC_NAME]

    def do_set_i18n(self, procname):
        return False

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            self.run_outer_glow,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        procedure.set_menu_label("Outer Glow (Layer Style)...")
        procedure.add_menu_path("<Image>/Layer/Layer Style")
        procedure.add_menu_path("<Image>/Filters/Light and Shadow")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        procedure.set_documentation(
            "Non-destructive Outer Glow layer style helper with spread, size, contour range, knockout, and presets",
            "Creates a dedicated non-destructive outer glow layer positioned immediately beneath the target layer.",
            PROC_NAME
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Preset
        preset_choice = Gimp.Choice.new()
        preset_choice.add("default", 0, "Photoshop Standard", "Standard warm 15px outer glow with screen blend")
        preset_choice.add("neon-cyan", 1, "Neon Cyan Halo", "Cyberpunk neon cyan halo with 25px radius")
        preset_choice.add("golden-radiance", 2, "Golden Radiance", "Rich warm gold radiance with color dodge blend")
        preset_choice.add("ethereal-white", 3, "Ethereal White", "Pure mystic white halo with 30px soft diffusion")
        preset_choice.add("magical-magenta", 4, "Magical Magenta", "Vibrant neon magenta halo with 20px radius")
        preset_choice.add("radioactive-green", 5, "Radioactive Green", "Acid green hazard glow with 20% spread")
        preset_choice.add("subtle-soft", 6, "Subtle Soft", "Delicate ambient rim light with 10px radius")
        preset_choice.add("custom", 7, "Custom Sliders", "Use manual sliders for all parameters")

        procedure.add_choice_argument(
            "preset",
            "Preset",
            "Curated outer glow layer style preset or custom sliders",
            preset_choice,
            "default",
            GObject.ParamFlags.READWRITE
        )

        # 2. Technique
        tech_choice = Gimp.Choice.new()
        tech_choice.add("softer", 0, "Softer", "Natural smooth Gaussian blur falloff")
        tech_choice.add("precise", 1, "Precise", "Concentrated crisp rim glow")

        procedure.add_choice_argument(
            "technique",
            "Technique",
            "Glow softening algorithm (softer, precise)",
            tech_choice,
            "softer",
            GObject.ParamFlags.READWRITE
        )

        # 3. Spread (0.0% to 100.0%)
        procedure.add_double_argument(
            "spread",
            "Spread (%)",
            "Glow matte boundary expansion percentage prior to blur (0.0 to 100.0, default 0.0)",
            0.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 4. Size (0.0 to 200.0 px)
        procedure.add_double_argument(
            "size",
            "Size (px)",
            "Glow blur radius / softness in pixels (0.0 to 200.0, default 15.0)",
            0.0,
            200.0,
            15.0,
            GObject.ParamFlags.READWRITE
        )

        # 5. Range (1.0% to 100.0%)
        procedure.add_double_argument(
            "range",
            "Range (%)",
            "Contour opacity falloff curve (1.0 to 100.0, default 50.0)",
            1.0,
            100.0,
            50.0,
            GObject.ParamFlags.READWRITE
        )

        # 6. Opacity (0.0% to 100.0%)
        procedure.add_double_argument(
            "opacity",
            "Opacity (%)",
            "Glow layer opacity percentage (0.0 to 100.0, default 75.0)",
            0.0,
            100.0,
            75.0,
            GObject.ParamFlags.READWRITE
        )

        # 7. Blend Mode
        mode_choice = Gimp.Choice.new()
        mode_choice.add("screen", 0, "Screen", "Photoshop standard glowing screen blend")
        mode_choice.add("normal", 1, "Normal", "Direct opaque glow rendering")
        mode_choice.add("lighten", 2, "Lighten", "Lighten only blend mode")
        mode_choice.add("dodge", 3, "Color Dodge", "Intense glowing color dodge blend")
        mode_choice.add("addition", 4, "Linear Dodge (Add)", "Hyper-bright additive glow blend")

        procedure.add_choice_argument(
            "blend-mode",
            "Blend Mode",
            "Glow layer blend mode (screen, normal, lighten, dodge, addition)",
            mode_choice,
            "screen",
            GObject.ParamFlags.READWRITE
        )

        # 8-10. Glow Color (RGB)
        procedure.add_double_argument("glow-r", "Glow Red", "Glow color Red (0.0 to 1.0)", 0.0, 1.0, 1.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("glow-g", "Glow Green", "Glow color Green (0.0 to 1.0)", 0.0, 1.0, 0.95, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("glow-b", "Glow Blue", "Glow color Blue (0.0 to 1.0)", 0.0, 1.0, 0.60, GObject.ParamFlags.READWRITE)

        # 11. Layer Knocks Out Outer Glow
        procedure.add_boolean_argument(
            "knockout",
            "Layer Knocks Out Outer Glow",
            "Cuts out target layer silhouette from glow layer",
            True,
            GObject.ParamFlags.READWRITE
        )

        # 12. Noise (0.0% to 100.0%)
        procedure.add_double_argument(
            "noise",
            "Noise (%)",
            "Film grain texture noise in glow (0.0 to 100.0, default 0.0)",
            0.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 13. Layer Mask Type
        mask_choice = Gimp.Choice.new()
        mask_choice.add("auto", 0, "Auto (Selection Mask if selected)", "Selection mask if active, else no mask")
        mask_choice.add("none", 1, "None", "No layer mask attached")
        mask_choice.add("reveal-all", 2, "Reveal-All (White)", "White editable mask")
        mask_choice.add("conceal-all", 3, "Conceal-All (Black)", "Black mask for selective brush painting")
        mask_choice.add("selection", 4, "Active Selection", "Convert active selection into editable mask")

        procedure.add_choice_argument(
            "mask-type",
            "Layer Mask",
            "Layer mask attached to glow layer (auto, none, reveal-all, conceal-all, selection)",
            mask_choice,
            "auto",
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run_outer_glow(self, procedure, run_mode, image, drawables, config, run_data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("python-fu-outer-glow")
            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        # Read configuration parameters
        preset = config.get_property("preset")
        tech_val = config.get_property("technique")
        spread_val = config.get_property("spread")
        size_val = config.get_property("size")
        range_val = config.get_property("range")
        opacity_val = config.get_property("opacity")
        bmode_str = config.get_property("blend-mode")
        gl_r = config.get_property("glow-r")
        gl_g = config.get_property("glow-g")
        gl_b = config.get_property("glow-b")
        knockout_val = config.get_property("knockout")
        noise_val = config.get_property("noise")
        mask_str = config.get_property("mask-type")

        # Resolve preset values
        if preset in PRESETS and preset not in ("default", "custom"):
            p = PRESETS[preset]
            final_tech = p["technique"]
            final_spread = float(p["spread"])
            final_size = float(p["size"])
            final_range = float(p["range"])
            final_opacity = float(p["opacity"])
            final_bmode = p["blend_mode"]
            final_r = float(p["color_r"])
            final_g = float(p["color_g"])
            final_b = float(p["color_b"])
            final_knockout = bool(p["knockout"])
            final_noise = float(p["noise"])
            label = p["label"]
        else:
            final_tech = tech_val
            final_spread = float(spread_val)
            final_size = float(size_val)
            final_range = float(range_val)
            final_opacity = float(opacity_val)
            final_bmode = bmode_str
            final_r = float(gl_r)
            final_g = float(gl_g)
            final_b = float(gl_b)
            final_knockout = bool(knockout_val)
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
                    GLib.quark_from_string("gimp-outer-glow"),
                    "No valid target layer found for outer glow effect.",
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
            # 1. Create dedicated glow layer
            glow_name = f"{target_layer.get_name()} (Outer Glow - {label})"
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

            # Insert immediately beneath target layer in stack
            parent = target_layer.get_parent()
            pos = image.get_item_position(target_layer) + 1
            image.insert_layer(glow_layer, parent, pos)

            # 2. Select target layer silhouette
            image.select_item(Gimp.ChannelOps.REPLACE, target_layer)

            # 3. Calculate spread expansion (grows solid matte boundary outward)
            spread_px = int(round((final_spread / 100.0) * final_size))
            if spread_px > 0:
                Gimp.Selection.grow(image, spread_px)

            # 4. Fill glow layer with glow color
            glow_color = Gegl.Color.new(f"rgb({final_r:.4f}, {final_g:.4f}, {final_b:.4f})")
            Gimp.context_set_foreground(glow_color)
            glow_layer.edit_fill(Gimp.FillType.FOREGROUND)
            Gimp.Selection.none(image)

            # 5. Apply blur for remaining size
            rem_blur = max(0.0, (1.0 - (final_spread / 100.0)) * final_size)
            if rem_blur > 0.1:
                std_dev = (rem_blur / 3.0) if final_tech == "precise" else (rem_blur / 2.0)
                filt_blur = Gimp.DrawableFilter.new(glow_layer, "gegl:gaussian-blur", "")
                fcfg = filt_blur.get_config()
                fcfg.set_property("std-dev-x", std_dev)
                fcfg.set_property("std-dev-y", std_dev)
                glow_layer.append_filter(filt_blur)
                glow_layer.merge_filters()

            # 6. Range contour modulation & Noise processing via GeglBuffer
            needs_buf_mod = (abs(final_range - 50.0) > 1.0) or (final_noise > 0.0)
            if needs_buf_mod:
                buf = glow_layer.get_buffer()
                rect = Gegl.Rectangle.new(0, 0, img_w, img_h)
                raw = buf.get(rect, 1.0, "RGBA float", Gegl.AbyssPolicy.NONE)
                arr = np.frombuffer(raw, dtype=np.float32).reshape((img_h, img_w, 4)).copy()

                alpha = arr[:, :, 3]
                mask_glow = alpha > 0.001

                # Range contour modulation: power curve reshaping alpha decay
                if abs(final_range - 50.0) > 1.0 and np.any(mask_glow):
                    # Range in [1, 100]: at 50 -> exp 1.0. At 75 -> exp 0.667. At 25 -> exp 2.0
                    gamma_exp = 50.0 / max(1.0, final_range)
                    alpha[mask_glow] = np.power(np.clip(alpha[mask_glow], 0.0, 1.0), gamma_exp)

                # Film grain noise
                if final_noise > 0.0 and np.any(mask_glow):
                    noise_factor = (final_noise / 100.0) * 0.40
                    rng = np.random.RandomState(42)
                    grain = (rng.rand(img_h, img_w).astype(np.float32) - 0.5) * noise_factor
                    alpha[mask_glow] = np.clip(alpha[mask_glow] + grain[mask_glow], 0.0, 1.0)

                arr[:, :, 3] = alpha
                buf.set(rect, "RGBA float", arr.tobytes())
                buf.flush()
                glow_layer.update(0, 0, img_w, img_h)

            # 7. Layer Knocks Out Outer Glow
            if final_knockout:
                image.select_item(Gimp.ChannelOps.REPLACE, target_layer)
                glow_layer.edit_clear()
                Gimp.Selection.none(image)

            # 8. Layer Mask Attachment
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

            # 9. Restore original selection
            if has_orig_sel and orig_sel_channel is not None:
                image.select_item(Gimp.ChannelOps.REPLACE, orig_sel_channel)
                image.remove_channel(orig_sel_channel)
            else:
                Gimp.Selection.none(image)

            # Keep target layer selected
            image.set_selected_layers([target_layer])

            Gimp.displays_flush()
            image.undo_group_end()
            Gimp.context_pop()

            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as exc:
            if has_orig_sel and orig_sel_channel is not None:
                try:
                    image.remove_channel(orig_sel_channel)
                except Exception:
                    pass
            image.undo_group_end()
            Gimp.context_pop()
            msg = "Outer glow failed: " + str(exc)
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-outer-glow"),
                    msg,
                    0
                )
            )


Gimp.main(OuterGlowPlugin.__gtype__, sys.argv)
