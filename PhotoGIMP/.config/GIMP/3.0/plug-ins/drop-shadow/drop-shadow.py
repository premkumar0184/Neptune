#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Drop Shadow Layer Style Helper Plugin
================================================================
Simulates Adobe Photoshop's non-destructive Drop Shadow layer style:
  - Photoshop Menu: Layer > Layer Style > Drop Shadow...
  - Photoshop Menu: Filters > Light and Shadow > Drop Shadow (Layer Style)...
  - Photoshop Docs: Section 113-115 lines 3433-3500 (Layer Style effects and options)
  - Topics.txt: Lines 107-118, 432

Photoshop Light Angle & Geometry:
  Light Angle θ ∈ [-180°, 180°]: Shadow is cast in the direction opposite to the light source:
    Δx = -distance * cos(radians(θ))
    Δy = distance * sin(radians(θ))
  - At 120° (Photoshop default): light from top-left, shadow cast to bottom-right (dx > 0, dy > 0).
  - At 90°: light straight from top, shadow cast straight down (dx = 0, dy > 0).
  - At 0°: light from 3 o'clock, shadow cast to left (dx < 0, dy = 0).
  - At 180°: light from 9 o'clock, shadow cast to right (dx > 0, dy = 0).

Spread & Size Control:
  - Spread (0% to 100%): Expands / thickens the solid shadow matte prior to blurring.
    Spread pixels = round((spread / 100.0) * size).
  - Size (0 to 200px): Blur radius / softness.
    Remaining blur = (1.0 - (spread / 100.0)) * size.

Layer Knocks Out Drop Shadow:
  - When enabled (default True), the source layer's silhouette is subtracted / cleared
    from the shadow layer, preventing the shadow from muddying semi-transparent pixels.

Film Grain Noise:
  - Adds uniform texture / noise (0% to 100%) to the shadow alpha.

Non-Destructive Layer Architecture:
  - Generates a dedicated shadow layer inserted immediately beneath the target layer.
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


PROC_NAME = "python-fu-drop-shadow"

BLEND_MODES = {
    "multiply": Gimp.LayerMode.MULTIPLY,
    "normal": Gimp.LayerMode.NORMAL,
    "darken": Gimp.LayerMode.DARKEN_ONLY,
    "burn": Gimp.LayerMode.BURN,
    "linear-burn": Gimp.LayerMode.LINEAR_BURN,
}

PRESETS = {
    "default": {
        "label": "Photoshop Standard",
        "angle": 120.0,
        "distance": 10.0,
        "spread": 0.0,
        "size": 10.0,
        "opacity": 75.0,
        "blend_mode": "multiply",
        "color_r": 0.0,
        "color_g": 0.0,
        "color_b": 0.0,
        "knockout": True,
        "noise": 0.0,
    },
    "soft-drop": {
        "label": "Soft Ambient",
        "angle": 90.0,
        "distance": 15.0,
        "spread": 10.0,
        "size": 25.0,
        "opacity": 50.0,
        "blend_mode": "multiply",
        "color_r": 0.0,
        "color_g": 0.0,
        "color_b": 0.0,
        "knockout": True,
        "noise": 0.0,
    },
    "hard-edge": {
        "label": "Hard Edge Graphic",
        "angle": 135.0,
        "distance": 12.0,
        "spread": 80.0,
        "size": 4.0,
        "opacity": 85.0,
        "blend_mode": "multiply",
        "color_r": 0.0,
        "color_g": 0.0,
        "color_b": 0.0,
        "knockout": True,
        "noise": 0.0,
    },
    "elevated-card": {
        "label": "Elevated UI Card",
        "angle": 90.0,
        "distance": 20.0,
        "spread": 5.0,
        "size": 30.0,
        "opacity": 40.0,
        "blend_mode": "multiply",
        "color_r": 0.0,
        "color_g": 0.0,
        "color_b": 0.0,
        "knockout": True,
        "noise": 0.0,
    },
    "neon-backlight": {
        "label": "Neon Cyan Backlight",
        "angle": 90.0,
        "distance": 0.0,
        "spread": 20.0,
        "size": 25.0,
        "opacity": 90.0,
        "blend_mode": "normal",
        "color_r": 0.0,
        "color_g": 0.9,
        "color_b": 1.0,
        "knockout": True,
        "noise": 0.0,
    },
    "vintage-sketch": {
        "label": "Vintage Grain Sketch",
        "angle": 120.0,
        "distance": 8.0,
        "spread": 0.0,
        "size": 8.0,
        "opacity": 80.0,
        "blend_mode": "multiply",
        "color_r": 0.1,
        "color_g": 0.1,
        "color_b": 0.1,
        "knockout": True,
        "noise": 25.0,
    },
    "custom": {
        "label": "Custom",
        "angle": 120.0,
        "distance": 10.0,
        "spread": 0.0,
        "size": 10.0,
        "opacity": 75.0,
        "blend_mode": "multiply",
        "color_r": 0.0,
        "color_g": 0.0,
        "color_b": 0.0,
        "knockout": True,
        "noise": 0.0,
    },
}


class DropShadowPlugin(Gimp.PlugIn):
    def do_query_procedures(self):
        return [PROC_NAME]

    def do_set_i18n(self, procname):
        return False

    def do_create_procedure(self, name):
        if name != PROC_NAME:
            return None

        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            self.run_drop_shadow,
            None
        )
        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )
        procedure.set_menu_label("Drop Shadow (Layer Style)...")
        procedure.add_menu_path("<Image>/Layer/Layer Style")
        procedure.add_menu_path("<Image>/Filters/Light and Shadow")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        procedure.set_documentation(
            "Drop Shadow Layer Style (Non-Destructive)",
            "Simulates Photoshop Layer > Layer Style > Drop Shadow with light angle trigonometry, "
            "distance, spread matte expansion, size blur, knockout clipping, and noise grain.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Preset
        preset_choice = Gimp.Choice.new()
        preset_choice.add("default", 0, "Photoshop Standard", "Standard 120° drop shadow with 10px distance and blur")
        preset_choice.add("soft-drop", 1, "Soft Ambient", "Diffused ambient shadow with soft 25px blur")
        preset_choice.add("hard-edge", 2, "Hard Edge Graphic", "Graphic high-contrast cast shadow with 80% spread")
        preset_choice.add("elevated-card", 3, "Elevated UI Card", "Deep UI floating card elevation shadow")
        preset_choice.add("neon-backlight", 4, "Neon Cyan Backlight", "Radiant colored neon backlight glow")
        preset_choice.add("vintage-sketch", 5, "Vintage Grain Sketch", "Textured analog charcoal shadow with noise")
        preset_choice.add("custom", 6, "Custom Sliders", "Use manual sliders for all parameters")

        procedure.add_choice_argument(
            "preset",
            "Preset",
            "Curated drop shadow layer style preset or custom sliders",
            preset_choice,
            "default",
            GObject.ParamFlags.READWRITE
        )

        # 2. Angle (-180.0° to 180.0°)
        procedure.add_double_argument(
            "angle",
            "Angle (°)",
            "Light source angle in degrees (-180.0 to 180.0, default 120.0)",
            -180.0,
            180.0,
            120.0,
            GObject.ParamFlags.READWRITE
        )

        # 3. Distance (0.0 to 200.0 px)
        procedure.add_double_argument(
            "distance",
            "Distance (px)",
            "Offset distance in pixels (0.0 to 200.0, default 10.0)",
            0.0,
            200.0,
            10.0,
            GObject.ParamFlags.READWRITE
        )

        # 4. Spread (0.0% to 100.0%)
        procedure.add_double_argument(
            "spread",
            "Spread (%)",
            "Shadow matte boundary expansion percentage prior to blur (0.0 to 100.0, default 0.0)",
            0.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 5. Size (0.0 to 200.0 px)
        procedure.add_double_argument(
            "size",
            "Size (px)",
            "Gaussian blur radius / softness in pixels (0.0 to 200.0, default 10.0)",
            0.0,
            200.0,
            10.0,
            GObject.ParamFlags.READWRITE
        )

        # 6. Opacity (0.0% to 100.0%)
        procedure.add_double_argument(
            "opacity",
            "Opacity (%)",
            "Shadow layer opacity percentage (0.0 to 100.0, default 75.0)",
            0.0,
            100.0,
            75.0,
            GObject.ParamFlags.READWRITE
        )

        # 7. Blend Mode
        mode_choice = Gimp.Choice.new()
        mode_choice.add("multiply", 0, "Multiply", "Photoshop standard darkening shadow blend")
        mode_choice.add("normal", 1, "Normal", "Direct opaque shadow rendering")
        mode_choice.add("darken", 2, "Darken", "Darken only blend mode")
        mode_choice.add("burn", 3, "Color Burn", "High contrast color burn shadow")
        mode_choice.add("linear-burn", 4, "Linear Burn", "Intense linear burn shadow")

        procedure.add_choice_argument(
            "blend-mode",
            "Blend Mode",
            "Shadow layer blend mode (multiply, normal, darken, burn, linear-burn)",
            mode_choice,
            "multiply",
            GObject.ParamFlags.READWRITE
        )

        # 8-10. Shadow Color (RGB)
        procedure.add_double_argument("shadow-r", "Shadow Red", "Shadow color Red (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("shadow-g", "Shadow Green", "Shadow color Green (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("shadow-b", "Shadow Blue", "Shadow color Blue (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)

        # 11. Layer Knocks Out Drop Shadow
        procedure.add_boolean_argument(
            "knockout",
            "Layer Knocks Out Drop Shadow",
            "Cuts out target layer silhouette from shadow layer",
            True,
            GObject.ParamFlags.READWRITE
        )

        # 12. Noise (0.0% to 100.0%)
        procedure.add_double_argument(
            "noise",
            "Noise (%)",
            "Film grain texture noise in shadow (0.0 to 100.0, default 0.0)",
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
            "Layer mask attached to shadow layer (auto, none, reveal-all, conceal-all, selection)",
            mask_choice,
            "auto",
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run_drop_shadow(self, procedure, run_mode, image, drawables, config, run_data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("python-fu-drop-shadow")
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
        spread_val = config.get_property("spread")
        size_val = config.get_property("size")
        opacity_val = config.get_property("opacity")
        bmode_str = config.get_property("blend-mode")
        sh_r = config.get_property("shadow-r")
        sh_g = config.get_property("shadow-g")
        sh_b = config.get_property("shadow-b")
        knockout_val = config.get_property("knockout")
        noise_val = config.get_property("noise")
        mask_str = config.get_property("mask-type")

        # Resolve preset values
        if preset in PRESETS and preset not in ("default", "custom"):
            p = PRESETS[preset]
            final_angle = float(p["angle"])
            final_dist = float(p["distance"])
            final_spread = float(p["spread"])
            final_size = float(p["size"])
            final_opacity = float(p["opacity"])
            final_bmode = p["blend_mode"]
            final_r = float(p["color_r"])
            final_g = float(p["color_g"])
            final_b = float(p["color_b"])
            final_knockout = bool(p["knockout"])
            final_noise = float(p["noise"])
            label = p["label"]
        else:
            final_angle = float(angle_val)
            final_dist = float(dist_val)
            final_spread = float(spread_val)
            final_size = float(size_val)
            final_opacity = float(opacity_val)
            final_bmode = bmode_str
            final_r = float(sh_r)
            final_g = float(sh_g)
            final_b = float(sh_b)
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
                    GLib.quark_from_string("gimp-drop-shadow"),
                    "No valid target layer found for drop shadow effect.",
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
            # 1. Create dedicated shadow layer
            shadow_name = f"{target_layer.get_name()} (Drop Shadow - {label})"
            blend_mode_enum = BLEND_MODES.get(final_bmode, Gimp.LayerMode.MULTIPLY)
            shadow_layer = Gimp.Layer.new(
                image,
                shadow_name,
                img_w,
                img_h,
                Gimp.ImageType.RGBA_IMAGE,
                max(0.0, min(100.0, final_opacity)),
                blend_mode_enum
            )

            # Insert immediately beneath target layer in stack
            parent = target_layer.get_parent()
            pos = image.get_item_position(target_layer) + 1
            image.insert_layer(shadow_layer, parent, pos)

            # 2. Select target layer silhouette
            image.select_item(Gimp.ChannelOps.REPLACE, target_layer)

            # 3. Calculate spread expansion
            spread_px = int(round((final_spread / 100.0) * final_size))
            if spread_px > 0:
                Gimp.Selection.grow(image, spread_px)

            # 4. Calculate offset translation from light angle θ
            # Δx = -distance * cos(θ), Δy = distance * sin(θ)
            rad = math.radians(final_angle)
            dx = int(round(-final_dist * math.cos(rad)))
            dy = int(round(final_dist * math.sin(rad)))
            if dx != 0 or dy != 0:
                Gimp.Selection.translate(image, dx, dy)

            # 5. Fill shadow layer with shadow color
            shadow_color = Gegl.Color.new(f"rgb({final_r:.4f}, {final_g:.4f}, {final_b:.4f})")
            Gimp.context_set_foreground(shadow_color)
            shadow_layer.edit_fill(Gimp.FillType.FOREGROUND)
            Gimp.Selection.none(image)

            # 6. Apply gaussian blur for remaining size
            rem_blur = max(0.0, (1.0 - (final_spread / 100.0)) * final_size)
            if rem_blur > 0.1:
                filt_blur = Gimp.DrawableFilter.new(shadow_layer, "gegl:gaussian-blur", "")
                fcfg = filt_blur.get_config()
                fcfg.set_property("std-dev-x", rem_blur / 2.0)
                fcfg.set_property("std-dev-y", rem_blur / 2.0)
                shadow_layer.append_filter(filt_blur)
                shadow_layer.merge_filters()

            # 7. Layer Knocks Out Drop Shadow
            if final_knockout:
                image.select_item(Gimp.ChannelOps.REPLACE, target_layer)
                shadow_layer.edit_clear()
                Gimp.Selection.none(image)

            # 8. Film Grain Noise
            if final_noise > 0.0:
                noise_factor = (final_noise / 100.0) * 0.40
                buf = shadow_layer.get_buffer()
                rect = Gegl.Rectangle.new(0, 0, img_w, img_h)
                raw = buf.get(rect, 1.0, "RGBA float", Gegl.AbyssPolicy.NONE)
                arr = np.frombuffer(raw, dtype=np.float32).reshape((img_h, img_w, 4)).copy()

                alpha = arr[:, :, 3]
                mask_shadow = alpha > 0.005
                if np.any(mask_shadow):
                    rng = np.random.RandomState(42)
                    grain = (rng.rand(img_h, img_w).astype(np.float32) - 0.5) * noise_factor
                    arr[:, :, 3] = np.clip(alpha + grain * mask_shadow, 0.0, 1.0)
                    buf.set(rect, "RGBA float", arr.tobytes())
                    buf.flush()
                    shadow_layer.update(0, 0, img_w, img_h)

            # 9. Layer Mask Attachment
            if mask_str == "auto":
                if has_orig_sel and orig_sel_channel is not None:
                    image.select_item(Gimp.ChannelOps.REPLACE, orig_sel_channel)
                    mask = shadow_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    shadow_layer.add_mask(mask)
            elif mask_str == "reveal-all":
                mask = shadow_layer.create_mask(Gimp.AddMaskType.WHITE)
                shadow_layer.add_mask(mask)
            elif mask_str == "conceal-all":
                mask = shadow_layer.create_mask(Gimp.AddMaskType.BLACK)
                shadow_layer.add_mask(mask)
            elif mask_str == "selection":
                if has_orig_sel and orig_sel_channel is not None:
                    image.select_item(Gimp.ChannelOps.REPLACE, orig_sel_channel)
                    mask = shadow_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    shadow_layer.add_mask(mask)

            # 10. Restore original selection
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
            msg = "Drop shadow failed: " + str(exc)
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-drop-shadow"),
                    msg,
                    0
                )
            )


Gimp.main(DropShadowPlugin.__gtype__, sys.argv)
