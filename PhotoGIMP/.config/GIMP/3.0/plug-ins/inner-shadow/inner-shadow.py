#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Inner Shadow Layer Style Helper Plugin
================================================================
Simulates Adobe Photoshop's non-destructive Inner Shadow layer style:
  - Photoshop Menu: Layer > Layer Style > Inner Shadow...
  - Photoshop Menu: Filters > Light and Shadow > Inner Shadow (Layer Style)...
  - Photoshop Docs: Section 113-115 lines 3433-3500 (Layer Style effects and options)
  - Topics.txt: Lines 107-118, 432

Photoshop Inner Shadow Architecture:
  1. Directional Light Angle Trigonometry:
     - Angle (-180° to 180°, default 120°): Light from angle θ casts shadow inward
       along Δx = -distance * cos(θ), Δy = distance * sin(θ).
  2. Distance Offset Translation:
     - Distance (0 to 200px, default 5px): Pixel offset of the inner shadow matte.
  3. Choke & Size Control:
     - Choke (0% to 100%, default 0%): Contracts the matte prior to blur.
     - Size (0 to 200px, default 5px): Halo blur radius in pixels.
  4. Range Contour Curve Control:
     - Range (1% to 100%, default 50%): Shapes opacity falloff contour (A' = A^(50/range)).
  5. Strict Boundary Silhouette Clipping:
     - Shadow is strictly clipped inside target layer silhouette (outside pixels alpha == 0.000).
  6. Film Grain Noise:
     - Adds uniform texture / noise (0% to 100%) to the inner shadow halo.
  7. Non-Destructive Layer Architecture:
     - Dedicated shadow layer inserted directly above the target layer in the stack.
     - Leaves target layer artwork and canvas pixels 100% untouched (diff == 0.000000).
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


PROC_NAME = "python-fu-inner-shadow"

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
        "distance": 5.0,
        "choke": 0.0,
        "size": 5.0,
        "range": 50.0,
        "opacity": 75.0,
        "blend_mode": "multiply",
        "color_r": 0.0,
        "color_g": 0.0,
        "color_b": 0.0,
        "noise": 0.0,
    },
    "deep-carved": {
        "label": "Deep Carved Inset",
        "angle": 120.0,
        "distance": 15.0,
        "choke": 20.0,
        "size": 15.0,
        "range": 60.0,
        "opacity": 85.0,
        "blend_mode": "multiply",
        "color_r": 0.0,
        "color_g": 0.0,
        "color_b": 0.0,
        "noise": 0.0,
    },
    "subtle-inset": {
        "label": "Subtle Inset Bevel",
        "angle": 90.0,
        "distance": 3.0,
        "choke": 0.0,
        "size": 4.0,
        "range": 50.0,
        "opacity": 50.0,
        "blend_mode": "multiply",
        "color_r": 0.0,
        "color_g": 0.0,
        "color_b": 0.0,
        "noise": 0.0,
    },
    "soft-ambient": {
        "label": "Soft Ambient Inset",
        "angle": 120.0,
        "distance": 8.0,
        "choke": 0.0,
        "size": 20.0,
        "range": 50.0,
        "opacity": 60.0,
        "blend_mode": "multiply",
        "color_r": 0.0,
        "color_g": 0.0,
        "color_b": 0.0,
        "noise": 0.0,
    },
    "hard-edge": {
        "label": "Hard Edge Cutout",
        "angle": 135.0,
        "distance": 6.0,
        "choke": 80.0,
        "size": 6.0,
        "range": 50.0,
        "opacity": 90.0,
        "blend_mode": "normal",
        "color_r": 0.0,
        "color_g": 0.0,
        "color_b": 0.0,
        "noise": 0.0,
    },
}


class InnerShadowPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return [PROC_NAME]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_inner_shadow, None)
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        # Menu Registrations
        procedure.set_menu_label("Inner Shadow (Layer Style)...")
        procedure.add_menu_path("<Image>/Layer/Layer Style")
        procedure.add_menu_path("<Image>/Filters/Light and Shadow")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        procedure.set_documentation(
            "Inner Shadow (Layer Style)",
            "Generates a non-destructive inner shadow layer style with directional light angle, distance offset, choke contraction, blur size, blend modes, and opacity.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Presets Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add("default", 0, "Photoshop Standard", "Standard 120° directional inner shadow")
        preset_choice.add("deep-carved", 1, "Deep Carved Inset", "Strong recessed relief shadow")
        preset_choice.add("subtle-inset", 2, "Subtle Inset Bevel", "Delicate 90° vertical bevel inset")
        preset_choice.add("soft-ambient", 3, "Soft Ambient Inset", "Wide soft ambient interior shading")
        preset_choice.add("hard-edge", 4, "Hard Edge Cutout", "Choked hard-edge graphic cutout shadow")
        preset_choice.add("custom", 5, "Custom Sliders", "Manual slider controls")

        procedure.add_choice_argument(
            "preset",
            "Preset",
            "Curated Inner Shadow preset style",
            preset_choice,
            "default",
            GObject.ParamFlags.READWRITE
        )

        # 2. Angle (-180.0° to 180.0°)
        procedure.add_double_argument(
            "angle",
            "Angle (°)",
            "Directional light angle in degrees (-180.0 to 180.0)",
            -180.0,
            180.0,
            120.0,
            GObject.ParamFlags.READWRITE
        )

        # 3. Distance (0.0 to 200.0 px)
        procedure.add_double_argument(
            "distance",
            "Distance (px)",
            "Offset distance of inner shadow in pixels (0.0 to 200.0)",
            0.0,
            200.0,
            5.0,
            GObject.ParamFlags.READWRITE
        )

        # 4. Choke (0.0% to 100.0%)
        procedure.add_double_argument(
            "choke",
            "Choke (%)",
            "Contracts / thickens solid shadow boundary prior to blur (0.0 to 100.0)",
            0.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 5. Size (0.0 to 200.0 px)
        procedure.add_double_argument(
            "size",
            "Size (px)",
            "Inner shadow halo blur radius in pixels (0.0 to 200.0)",
            0.0,
            200.0,
            5.0,
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
            "Inner shadow layer opacity (0.0 to 100.0)",
            0.0,
            100.0,
            75.0,
            GObject.ParamFlags.READWRITE
        )

        # 8. Blend Mode
        mode_choice = Gimp.Choice.new()
        mode_choice.add("multiply", 0, "Multiply", "Multiply darkening mode (default)")
        mode_choice.add("normal", 1, "Normal", "Normal standard blend")
        mode_choice.add("darken", 2, "Darken", "Darken only mode")
        mode_choice.add("burn", 3, "Color Burn", "Color burn contrast mode")
        mode_choice.add("linear-burn", 4, "Linear Burn", "Linear burn deep shadow mode")

        procedure.add_choice_argument(
            "blend-mode",
            "Blend Mode",
            "Layer blend mode (multiply, normal, darken, burn, linear-burn)",
            mode_choice,
            "multiply",
            GObject.ParamFlags.READWRITE
        )

        # 9-11. Shadow Color RGB
        procedure.add_double_argument("shadow-r", "Shadow Red", "Inner shadow Red channel (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("shadow-g", "Shadow Green", "Inner shadow Green channel (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("shadow-b", "Shadow Blue", "Inner shadow Blue channel (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)

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

    def run_inner_shadow(self, procedure, run_mode, image, drawables, config, run_data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("python-fu-inner-shadow")
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
        choke_val = config.get_property("choke")
        size_val = config.get_property("size")
        range_val = config.get_property("range")
        opacity_val = config.get_property("opacity")
        bmode_str = config.get_property("blend-mode")
        sh_r = config.get_property("shadow-r")
        sh_g = config.get_property("shadow-g")
        sh_b = config.get_property("shadow-b")
        noise_val = config.get_property("noise")
        mask_str = config.get_property("mask-type")

        # Resolve preset values
        if preset in PRESETS and preset not in ("default", "custom"):
            p = PRESETS[preset]
            final_angle = float(p["angle"])
            final_dist = float(p["distance"])
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
            final_angle = float(angle_val)
            final_dist = float(dist_val)
            final_choke = float(choke_val)
            final_size = float(size_val)
            final_range = float(range_val)
            final_opacity = float(opacity_val)
            final_bmode = bmode_str
            final_r = float(sh_r)
            final_g = float(sh_g)
            final_b = float(sh_b)
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
                    GLib.quark_from_string("gimp-inner-shadow"),
                    "No valid target layer found for inner shadow effect.",
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

            # 2. Create dedicated inner shadow layer
            shadow_name = f"{target_layer.get_name()} (Inner Shadow - {label})"
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

            # Insert immediately above target layer in stack
            parent = target_layer.get_parent()
            pos = image.get_item_position(target_layer)
            image.insert_layer(shadow_layer, parent, pos)

            # 3. Generate Inner Shadow field
            # Directional translation offsets from light angle θ:
            # Δx = -distance * cos(θ), Δy = distance * sin(θ)
            rad = math.radians(final_angle)
            dx = int(round(-final_dist * math.cos(rad)))
            dy = int(round(final_dist * math.sin(rad)))

            # Select target layer silhouette and invert to get exterior
            image.select_item(Gimp.ChannelOps.REPLACE, target_layer)
            Gimp.Selection.invert(image)

            # Choke expansion contracts the matte boundary
            choke_px = int(round((final_choke / 100.0) * final_size))
            if choke_px > 0:
                Gimp.Selection.grow(image, choke_px)

            # Directional translation
            if dx != 0 or dy != 0:
                Gimp.Selection.translate(image, dx, dy)

            # Fill shadow layer with shadow color
            shadow_color = Gegl.Color.new(f"rgb({final_r:.4f}, {final_g:.4f}, {final_b:.4f})")
            Gimp.context_set_foreground(shadow_color)
            shadow_layer.edit_fill(Gimp.FillType.FOREGROUND)
            Gimp.Selection.none(image)

            # Gaussian blur for size radius falloff
            rem_blur = max(0.5, (1.0 - (final_choke / 100.0)) * final_size)
            filt_blur = Gimp.DrawableFilter.new(shadow_layer, "gegl:gaussian-blur", "")
            fcfg = filt_blur.get_config()
            fcfg.set_property("std-dev-x", rem_blur / 2.0)
            fcfg.set_property("std-dev-y", rem_blur / 2.0)
            shadow_layer.append_filter(filt_blur)
            shadow_layer.merge_filters()

            # Read shadow buffer
            sh_buf = shadow_layer.get_buffer()
            raw_sh = sh_buf.get(rect, 1.0, "RGBA float", Gegl.AbyssPolicy.NONE)
            arr_sh = np.frombuffer(raw_sh, dtype=np.float32).reshape((img_h, img_w, 4)).copy()
            sh_a = np.clip(arr_sh[:, :, 3], 0.0, 1.0)

            # If distance == 0, scale boundary step edge response (0.5 -> 1.0)
            if final_dist < 0.1:
                sh_a = np.clip(sh_a * 2.0, 0.0, 1.0)

            # 4. Range contour modulation
            mask_inner = sh_a > 0.001
            if abs(final_range - 50.0) > 1.0 and np.any(mask_inner):
                gamma_exp = 50.0 / max(1.0, final_range)
                sh_a[mask_inner] = np.power(np.clip(sh_a[mask_inner], 0.0, 1.0), gamma_exp)

            # 5. Film grain noise texture
            if final_noise > 0.0 and np.any(mask_inner):
                noise_factor = (final_noise / 100.0) * 0.40
                rng = np.random.RandomState(42)
                grain = (rng.rand(img_h, img_w).astype(np.float32) - 0.5) * noise_factor
                sh_a[mask_inner] = np.clip(sh_a[mask_inner] + grain[mask_inner], 0.0, 1.0)

            # 6. Strict Boundary Silhouette Clipping to Target Layer
            sh_a *= target_alpha

            # Ensure pure shadow color fidelity on RGB channels
            arr_sh[:, :, 0] = final_r
            arr_sh[:, :, 1] = final_g
            arr_sh[:, :, 2] = final_b
            arr_sh[:, :, 3] = sh_a

            # Write processed buffer back
            sh_buf.set(rect, "RGBA float", arr_sh.tobytes())
            sh_buf.flush()
            shadow_layer.update(0, 0, img_w, img_h)

            # 7. Layer Mask Attachment
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

            # Restore original selection or clear
            if has_orig_sel and orig_sel_channel is not None:
                image.select_item(Gimp.ChannelOps.REPLACE, orig_sel_channel)
                image.remove_channel(orig_sel_channel)
            else:
                Gimp.Selection.none(image)

            # Set shadow layer as active layer
            image.set_selected_layers([shadow_layer])

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
                    GLib.quark_from_string("gimp-inner-shadow"),
                    f"Inner shadow generation failed: {str(e)}",
                    0
                )
            )


Gimp.main(InnerShadowPlugin.__gtype__, sys.argv)
