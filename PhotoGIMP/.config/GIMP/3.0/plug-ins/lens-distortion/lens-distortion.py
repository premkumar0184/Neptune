#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Lens Distortion & Optical Perspective Correction Plugin
==================================================================================
Photoshop Reference:
- Topics.txt line 482: "Artistic and stylize filters - Correct lens distortion and perspective"
- Topics.txt line 483: "Artistic and stylize filters - Correct wide-angle lens distortion"
- photoshop_docs.md Section 424 lines 12650-12655 (Filter > Lens Correction:
  Barrel Distortion: Straighten lines that curve outward from the center;
  Pincushion Distortion: Adjust lines that bend inward toward the image center;
  Vignetting: Balance brightness across your entire image, lighten dark corners)

Key Architectural Features:
1. Geometric Optical Distortion Correction:
   - Barrel Distortion Correction: Negative displacement scaling factor pulls pixels inward/outward
     along spherical curves, straightening outward bowing in wide-angle horizons and architecture.
   - Pincushion Distortion Correction: Positive displacement factor unpinches inward bending in
     telephoto images.
   - Fisheye Defish: Aggressive rectilinear de-warping for ultra-wide action cam and fisheye lenses.
2. Directional Displacement Modes:
   - Radial mode: Complete symmetrical 360-degree optical lens distortion correction.
   - Horizontal mode: Planar horizontal correction for architectural columns, facades, and panoramic walls.
   - Vertical mode: Planar vertical perspective leveling for tall building verticals.
3. Spherical Curvature & Field of View Controls:
   - Curvature slider (0.1 to 2.0) sets the spherical cap apex angle.
   - Angle of view slider (0° to 180°) matches physical camera optics.
4. Integrated Optical Vignette Illumination Compensation:
   - Peripheral illumination slider (-100% to +100%) lightens dark optical corners or counteracts
     vignetting falloff while leaving central image exposure intact.
5. Curated Photographic Presets:
   - Wide-Angle Barrel Correction: Straightens outward curves with corner illumination lift.
   - Telephoto Pincushion Correction: Straightens inward pinching from telephoto optics.
   - Fisheye Defish / De-Barrel: High-strength rectilinear unbending for ultra-wide lenses.
   - Architectural Perspective Flatten: Planar horizontal straightening for building facades.
   - Creative Fisheye Warp: Artistic spherical bulge with peripheral vignette shading.
   - Custom: Full manual slider control.
6. Non-Destructive Adjustment Layering & Masks:
   - Creates an isolated adjustment layer duplicating the active drawable.
   - Attaches editable layer masks (Reveal All, Conceal All for selective edge brushing, Active Selection).
   - Base layer source pixels underneath remain 100% mathematically untouched (0.000000 diff).
"""

import os
import sys
import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib


PRESETS = {
    "wide-angle-barrel": {
        "label": "Wide-Angle Barrel Correction",
        "desc": "Straightens outward curving lines and brightens dark corners from wide-angle optics",
        "amount": -25.0,
        "curvature": 1.0,
        "angle_of_view": 60.0,
        "mode": "radial",
        "vignette": 20.0,
        "opacity": 100.0,
    },
    "telephoto-pincushion": {
        "label": "Telephoto Pincushion Correction",
        "desc": "Straightens inward pinching and distortion from telephoto lenses",
        "amount": 25.0,
        "curvature": 1.0,
        "angle_of_view": 30.0,
        "mode": "radial",
        "vignette": 0.0,
        "opacity": 100.0,
    },
    "fisheye-defish": {
        "label": "Fisheye Defish / De-Barrel",
        "desc": "Aggressive rectilinear unbending for ultra-wide action cam and fisheye optics",
        "amount": -60.0,
        "curvature": 1.0,
        "angle_of_view": 90.0,
        "mode": "radial",
        "vignette": 35.0,
        "opacity": 100.0,
    },
    "architectural-horizontal": {
        "label": "Architectural Perspective Flatten",
        "desc": "Horizontal planar straightening for structural columns and building facades",
        "amount": -20.0,
        "curvature": 0.8,
        "angle_of_view": 45.0,
        "mode": "horizontal",
        "vignette": 0.0,
        "opacity": 100.0,
    },
    "creative-fisheye": {
        "label": "Creative Fisheye Warp",
        "desc": "Artistic spherical bulge emphasizing central elements with vignette shading",
        "amount": 70.0,
        "curvature": 1.0,
        "angle_of_view": 90.0,
        "mode": "radial",
        "vignette": -25.0,
        "opacity": 100.0,
    },
    "custom": {
        "label": "Custom Lens Correction",
        "desc": "Manual slider configuration",
        "amount": -25.0,
        "curvature": 1.0,
        "angle_of_view": 60.0,
        "mode": "radial",
        "vignette": 0.0,
        "opacity": 100.0,
    },
}


class LensDistortionPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-lens-distortion"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, self.run, None
        )
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
        procedure.set_menu_label("Lens Distortion...")
        procedure.add_menu_path("<Image>/Filters/Distort")
        procedure.add_menu_path("<Image>/Filters/Retouching")
        procedure.add_menu_path("<Image>/Layer")

        procedure.set_documentation(
            "Non-Destructive Lens Distortion & Perspective Correction Helper",
            "Corrects optical barrel and pincushion distortions, straightens curved lines, "
            "and balances peripheral vignette illumination using non-destructive adjustment layers.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add("wide-angle-barrel", 0, "Wide-Angle Barrel Correction", "Straightens outward curving lines and brightens dark corners")
        preset_choice.add("telephoto-pincushion", 1, "Telephoto Pincushion Correction", "Straightens inward pinching and distortion")
        preset_choice.add("fisheye-defish", 2, "Fisheye Defish / De-Barrel", "Aggressive rectilinear unbending for fisheye lenses")
        preset_choice.add("architectural-horizontal", 3, "Architectural Perspective Flatten", "Horizontal planar straightening for building facades")
        preset_choice.add("creative-fisheye", 4, "Creative Fisheye Warp", "Artistic spherical bulge emphasizing central elements")
        preset_choice.add("custom", 5, "Custom Lens Correction", "Manual slider configuration")

        procedure.add_choice_argument(
            "preset",
            "Correction Preset",
            "Curated lens correction preset (wide-angle-barrel, telephoto-pincushion, fisheye-defish, architectural-horizontal, creative-fisheye, custom)",
            preset_choice,
            "wide-angle-barrel",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "amount",
            "Distortion Amount (%)",
            "Geometric distortion scaling: negative values correct barrel bowing, positive values correct pincushion pinching (-100.0% to 100.0%, default -25.0%)",
            -100.0,
            100.0,
            -25.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "curvature",
            "Spherical Curvature",
            "Curvature factor of the optical spherical cap (0.0 to 1.0, default 1.0)",
            0.0,
            1.0,
            1.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "angle-of-view",
            "Angle of View (°)",
            "Camera lens angle of view in degrees (0.0° to 180.0°, default 60.0°)",
            0.0,
            180.0,
            60.0,
            GObject.ParamFlags.READWRITE
        )

        # Mode Choice
        mode_choice = Gimp.Choice.new()
        mode_choice.add("radial", 0, "Radial (Full 360°)", "Full symmetrical circular optical correction")
        mode_choice.add("horizontal", 1, "Horizontal Only", "Planar horizontal correction (columns, facades)")
        mode_choice.add("vertical", 2, "Vertical Only", "Planar vertical correction (perspective leveling)")

        procedure.add_choice_argument(
            "mode",
            "Displacement Mode",
            "Direction of optical displacement (radial, horizontal, vertical)",
            mode_choice,
            "radial",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "vignette-compensation",
            "Vignette Illumination (%)",
            "Compensates for optical corner light falloff: positive lightens dark corners, negative darkens (-100.0% to 100.0%, default 0.0%)",
            -100.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "opacity",
            "Layer Opacity (%)",
            "Overall opacity of the Lens Correction layer (10.0% to 100.0%, default 100.0%)",
            10.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # Mask Type Choice
        mask_choice = Gimp.Choice.new()
        mask_choice.add("reveal-all", 0, "Reveal All (White Mask)", "Full image correction")
        mask_choice.add("conceal-all", 1, "Conceal All (Black Mask)", "Correction hidden; brush in selectively")
        mask_choice.add("selection", 2, "Active Selection Mask", "Confines correction strictly to active selection")

        procedure.add_choice_argument(
            "mask-type",
            "Layer Mask Mode",
            "Initial layer mask configuration (reveal-all, conceal-all, selection)",
            mask_choice,
            "reveal-all",
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run(self, procedure, run_mode, image, drawables, config, data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            Gimp.ui_init("lens-distortion.py")
            dialog = Gimp.ProcedureDialog.new(procedure, config, "Lens Distortion Correction")
            dialog.fill([
                "preset", "amount", "curvature", "angle-of-view",
                "mode", "vignette-compensation", "opacity", "mask-type"
            ])
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        # Resolve target drawable
        target_drawable = None
        selected_layers = image.get_selected_layers()
        if len(selected_layers) > 0:
            target_drawable = selected_layers[0]
        elif drawables and len(drawables) > 0:
            d = drawables[0]
            if hasattr(d, 'is_layer_mask') and d.is_layer_mask():
                target_drawable = image.get_layers()[0] if len(image.get_layers()) > 0 else None
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
                    GLib.quark_from_string("gimp-lens-distortion"),
                    "No target drawable found to apply Lens Distortion correction.",
                    0
                )
            )

        preset_key = config.get_property("preset") or "wide-angle-barrel"
        if preset_key not in PRESETS:
            preset_key = "wide-angle-barrel"
        preset_cfg = PRESETS[preset_key]

        if preset_key == "custom":
            amount_val = config.get_property("amount")
            curvature_val = config.get_property("curvature")
            angle_val = config.get_property("angle-of-view")
            mode_val = config.get_property("mode") or "radial"
            vignette_val = config.get_property("vignette-compensation")
            opacity_val = config.get_property("opacity")
        else:
            amount_val = preset_cfg["amount"]
            curvature_val = preset_cfg["curvature"]
            angle_val = preset_cfg["angle_of_view"]
            mode_val = preset_cfg["mode"]
            vignette_val = preset_cfg["vignette"]
            opacity_val = config.get_property("opacity")
            if opacity_val <= 0.0 or opacity_val > 100.0:
                opacity_val = preset_cfg["opacity"]

        mask_type = config.get_property("mask-type") or "reveal-all"

        Gimp.context_push()
        image.undo_group_start()

        saved_sel_channel = None
        try:
            # Check active selection (Decision D-003)
            has_user_selection = not Gimp.Selection.is_empty(image)
            if has_user_selection:
                saved_sel_channel = Gimp.Selection.save(image)
                Gimp.Selection.none(image)

            # 1. Duplicate active drawable into isolated adjustment layer
            layer_name = f"Lens Correction ({preset_cfg['label']})"
            lens_layer = Gimp.Layer.new_from_drawable(target_drawable, image)
            lens_layer.set_name(layer_name)
            lens_layer.set_mode(Gimp.LayerMode.NORMAL)
            lens_layer.set_opacity(float(opacity_val))

            parent = target_drawable.get_parent()
            pos = image.get_item_position(target_drawable)
            image.insert_layer(lens_layer, parent, pos)

            # 2. Apply optical geometric distortion via gegl:spherize
            filt_distort = Gimp.DrawableFilter.new(lens_layer, "gegl:spherize", "")
            c_distort = filt_distort.get_config()
            c_distort.set_property("amount", max(-1.0, min(1.0, float(amount_val) / 100.0)))
            c_distort.set_property("curvature", max(0.0, min(1.0, float(curvature_val))))
            c_distort.set_property("angle-of-view", max(0.0, min(180.0, float(angle_val))))
            c_distort.set_property("mode", str(mode_val))
            lens_layer.merge_filter(filt_distort)

            # 3. Apply peripheral vignette illumination compensation if requested
            if abs(float(vignette_val)) >= 1.0:
                alpha = min(0.60, abs(float(vignette_val)) / 100.0 * 0.45)
                if float(vignette_val) > 0.0:
                    col_str = f"rgba(1.0, 1.0, 1.0, {alpha:.3f})"
                else:
                    col_str = f"rgba(0.0, 0.0, 0.0, {alpha:.3f})"

                filt_vig = Gimp.DrawableFilter.new(lens_layer, "gegl:vignette", "")
                c_vig = filt_vig.get_config()
                c_vig.set_property("color", Gegl.Color.new(col_str))
                c_vig.set_property("radius", 1.25)
                c_vig.set_property("softness", 0.85)
                lens_layer.merge_filter(filt_vig)

            # 4. Attach Layer Mask
            if mask_type == "conceal-all":
                mask = lens_layer.create_mask(Gimp.AddMaskType.BLACK)
                lens_layer.add_mask(mask)
            elif mask_type == "selection":
                if saved_sel_channel is not None:
                    image.select_item(Gimp.ChannelOps.REPLACE, saved_sel_channel)
                    mask = lens_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    lens_layer.add_mask(mask)
                    Gimp.Selection.none(image)
                else:
                    mask = lens_layer.create_mask(Gimp.AddMaskType.WHITE)
                    lens_layer.add_mask(mask)
            else:  # reveal-all
                mask = lens_layer.create_mask(Gimp.AddMaskType.WHITE)
                lens_layer.add_mask(mask)

            # Cleanup saved selection channel
            if saved_sel_channel is not None:
                image.remove_channel(saved_sel_channel)

            image.set_selected_layers([lens_layer])
            lens_layer.set_visible(True)

        except Exception as e:
            image.undo_group_end()
            Gimp.context_pop()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-lens-distortion"),
                    f"Lens Distortion correction failed: {str(e)}",
                    0
                )
            )

        image.undo_group_end()
        Gimp.context_pop()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(LensDistortionPlugin.__gtype__, sys.argv)
