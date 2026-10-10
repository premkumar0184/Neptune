#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Oil Paint & Fine Art Impasto Filter Plugin
===================================================================
Photoshop Reference:
- Topics.txt line 485: "Artistic and stylize filters - Oil Paint filter settings"
- Topics.txt line 451: "Apply filters from the filter gallery"
- Topics.txt line 452: "Filter Gallery overview"
- photoshop_docs.md Section 416 line 12058 (Filter > Stylize > Oil Paint:
  Creative effects, such as Oil Paint in the Stylize category)
- photoshop_docs.md Section 424 lines 16131 (Oil Paint filter settings:
  Stylization, Cleanliness, Scale, Bristle Detail, Lighting, Angle, Shine)

Key Architectural Features:
1. Painterly Brush Stroke Simulation:
   - Stylization (0.1 to 10.0): Controls brush stroke clustering radius and
     neighborhood grouping via Symmetric Nearest Neighbor filtering (gegl:snn-mean).
   - Cleanliness (0.0 to 10.0): Controls stroke edge fluidity, transitioning from
     raw, textured paint to smooth, flowing liquid oil glaze.
2. 3D Impasto Texture & Bristle Detailing:
   - Scale (0.1 to 10.0): Adjusts brush head width and thickness of the 3D impasto paint relief.
   - Bristle Detail (0.0 to 10.0): Controls micro-contrast grooves within the brush stroke flow.
3. Directional Surface Lighting & Specular Luster:
   - Lighting Toggle: Enables/disables directional surface lighting.
   - Light Angle (0.0° to 360.0°): Controls the incident angle of illumination across the impasto ridges.
   - Shine (0.0 to 5.0): Simulates wet oil paint gloss and specular luster.
4. Rich Oil Pigment Saturation:
   - Enhances pigment color vibrance and depth characteristic of physical oil paints.
5. Curated Fine-Art Presets:
   - Classic Impressionist Oil: Balanced stroke clustering with moderate impasto relief.
   - Thick Impasto Palette Knife: Heavy sculptural paint mounds and high specular luster.
   - Smooth Glaze Portrait: Renaissance liquid oil glaze with delicate soft sheen.
   - Expressionist Dynamic: Bold, energetic, broken brushstrokes with prominent bristle grooves.
   - Fine Canvas Detail: Small delicate micro-brushwork preserving high-frequency image details.
   - Custom: Full manual slider control.
6. Non-Destructive Adjustment Layering & Masks:
   - Creates an isolated adjustment layer duplicating the active drawable.
   - Attaches editable layer masks (Reveal All, Conceal All for selective painting, Selection).
   - Base layer source pixels underneath remain 100% mathematically untouched (0.000000 diff).
"""

import math
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
    "classic-oil": {
        "label": "Classic Impressionist Oil",
        "desc": "Balanced painterly stroke clustering with moderate impasto relief and warm brush shine",
        "stylization": 4.0,
        "cleanliness": 5.0,
        "scale": 1.5,
        "bristle_detail": 3.0,
        "lighting": True,
        "light_angle": 60.0,
        "shine": 1.0,
        "opacity": 100.0,
    },
    "thick-impasto": {
        "label": "Thick Impasto Palette Knife",
        "desc": "Heavy textured strokes, high impasto relief mounds, and dramatic specular shine",
        "stylization": 6.5,
        "cleanliness": 3.0,
        "scale": 3.5,
        "bristle_detail": 6.0,
        "lighting": True,
        "light_angle": 45.0,
        "shine": 2.5,
        "opacity": 100.0,
    },
    "smooth-glaze": {
        "label": "Smooth Glaze Portrait",
        "desc": "Flowing blended oil glaze with fine brush contours and soft delicate luster",
        "stylization": 3.0,
        "cleanliness": 8.0,
        "scale": 1.0,
        "bristle_detail": 1.5,
        "lighting": True,
        "light_angle": 75.0,
        "shine": 0.8,
        "opacity": 100.0,
    },
    "expressionist": {
        "label": "Expressionist Dynamic",
        "desc": "Bold, vigorous, broken brushstrokes with prominent bristle grooves",
        "stylization": 8.0,
        "cleanliness": 1.5,
        "scale": 2.5,
        "bristle_detail": 8.0,
        "lighting": True,
        "light_angle": 30.0,
        "shine": 1.8,
        "opacity": 100.0,
    },
    "fine-canvas": {
        "label": "Fine Canvas Detail",
        "desc": "Delicate micro-brushwork preserving sharp fine details with subtle canvas sheen",
        "stylization": 2.0,
        "cleanliness": 6.0,
        "scale": 0.8,
        "bristle_detail": 4.0,
        "lighting": True,
        "light_angle": 60.0,
        "shine": 0.5,
        "opacity": 100.0,
    },
    "custom": {
        "label": "Custom Oil Paint",
        "desc": "Manual slider configuration",
        "stylization": 4.0,
        "cleanliness": 5.0,
        "scale": 1.5,
        "bristle_detail": 3.0,
        "lighting": True,
        "light_angle": 60.0,
        "shine": 1.0,
        "opacity": 100.0,
    },
}


class OilPaintPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-oil-paint"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, self.run, None
        )
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
        procedure.set_menu_label("Oil Paint...")
        procedure.add_menu_path("<Image>/Filters/Artistic")
        procedure.add_menu_path("<Image>/Filters/Stylize")
        procedure.add_menu_path("<Image>/Layer")

        procedure.set_documentation(
            "Non-Destructive Oil Paint & Fine Art Impasto Helper",
            "Transforms photographs into fine-art oil paintings with organic brush strokes, "
            "impasto surface relief, and directional lighting using non-destructive adjustment layers.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add("classic-oil", 0, "Classic Impressionist Oil", "Balanced painterly stroke clustering with warm brush shine")
        preset_choice.add("thick-impasto", 1, "Thick Impasto Palette Knife", "Heavy textured strokes, high impasto relief mounds, and high shine")
        preset_choice.add("smooth-glaze", 2, "Smooth Glaze Portrait", "Flowing blended oil glaze with fine brush contours")
        preset_choice.add("expressionist", 3, "Expressionist Dynamic", "Bold, vigorous brushstrokes with prominent bristle grooves")
        preset_choice.add("fine-canvas", 4, "Fine Canvas Detail", "Delicate micro-brushwork preserving fine image details")
        preset_choice.add("custom", 5, "Custom Oil Paint", "Manual slider configuration")

        procedure.add_choice_argument(
            "preset",
            "Artistic Preset",
            "Curated oil painting preset (classic-oil, thick-impasto, smooth-glaze, expressionist, fine-canvas, custom)",
            preset_choice,
            "classic-oil",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "stylization",
            "Stylization",
            "Controls painterly brush stroke clustering and grouping (0.1 to 10.0, default 4.0)",
            0.1,
            10.0,
            4.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "cleanliness",
            "Cleanliness",
            "Smoothness and fluidity of brush strokes (0.0 to 10.0, default 5.0)",
            0.0,
            10.0,
            5.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "scale",
            "Scale",
            "Brush head width and thickness of impasto relief (0.1 to 10.0, default 1.5)",
            0.1,
            10.0,
            1.5,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "bristle-detail",
            "Bristle Detail",
            "Micro-contrast grooves and bristle ridges within brush strokes (0.0 to 10.0, default 3.0)",
            0.0,
            10.0,
            3.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_boolean_argument(
            "lighting",
            "Lighting",
            "Enable directional surface lighting and paint luster (True / False)",
            True,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "light-angle",
            "Light Angle (°)",
            "Direction of the incident light source (0.0° to 360.0°, default 60.0°)",
            0.0,
            360.0,
            60.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "shine",
            "Shine",
            "Specular gloss and luster of wet oil paint (0.0 to 5.0, default 1.0)",
            0.0,
            5.0,
            1.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "opacity",
            "Layer Opacity (%)",
            "Overall opacity of the Oil Paint layer (10.0% to 100.0%, default 100.0%)",
            10.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # Mask Type Choice
        mask_choice = Gimp.Choice.new()
        mask_choice.add("reveal-all", 0, "Reveal All (White Mask)", "Full image oil painting effect")
        mask_choice.add("conceal-all", 1, "Conceal All (Black Mask)", "Effect hidden; brush in selective painterly areas")
        mask_choice.add("selection", 2, "Active Selection Mask", "Confines oil paint effect strictly to active selection")

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
            Gimp.ui_init("oil-paint.py")
            dialog = Gimp.ProcedureDialog.new(procedure, config, "Oil Paint Stylize")
            dialog.fill([
                "preset", "stylization", "cleanliness", "scale", "bristle-detail",
                "lighting", "light-angle", "shine", "opacity", "mask-type"
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
                    GLib.quark_from_string("gimp-oil-paint"),
                    "No target drawable found to apply Oil Paint effect.",
                    0
                )
            )

        preset_key = config.get_property("preset") or "classic-oil"
        if preset_key not in PRESETS:
            preset_key = "classic-oil"
        preset_cfg = PRESETS[preset_key]

        if preset_key == "custom":
            stylization_val = config.get_property("stylization")
            cleanliness_val = config.get_property("cleanliness")
            scale_val = config.get_property("scale")
            bristle_val = config.get_property("bristle-detail")
            lighting_val = config.get_property("lighting")
            angle_val = config.get_property("light-angle")
            shine_val = config.get_property("shine")
            opacity_val = config.get_property("opacity")
        else:
            stylization_val = preset_cfg["stylization"]
            cleanliness_val = preset_cfg["cleanliness"]
            scale_val = preset_cfg["scale"]
            bristle_val = preset_cfg["bristle_detail"]
            lighting_val = preset_cfg["lighting"]
            angle_val = preset_cfg["light_angle"]
            shine_val = preset_cfg["shine"]
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
            layer_name = f"Oil Paint ({preset_cfg['label']})"
            oil_layer = Gimp.Layer.new_from_drawable(target_drawable, image)
            oil_layer.set_name(layer_name)
            oil_layer.set_mode(Gimp.LayerMode.NORMAL)
            oil_layer.set_opacity(float(opacity_val))

            parent = target_drawable.get_parent()
            pos = image.get_item_position(target_drawable)
            image.insert_layer(oil_layer, parent, pos)

            # 2. Cleanliness Pre-pass (stroke fluidity & noise reduction)
            if float(cleanliness_val) > 1.0:
                smooth_radius = max(0.2, (float(cleanliness_val) - 1.0) * 0.25)
                filt_clean = Gimp.DrawableFilter.new(oil_layer, "gegl:gaussian-blur", "")
                c_clean = filt_clean.get_config()
                c_clean.set_property("std-dev-x", float(smooth_radius))
                c_clean.set_property("std-dev-y", float(smooth_radius))
                oil_layer.merge_filter(filt_clean)

            # 3. Painterly Brush Stroke Clustering via gegl:snn-mean
            snn_radius = max(1, min(30, int(round(float(stylization_val) * 1.8))))
            pairs = 2 if float(stylization_val) >= 3.0 else 1
            filt_snn = Gimp.DrawableFilter.new(oil_layer, "gegl:snn-mean", "")
            c_snn = filt_snn.get_config()
            c_snn.set_property("radius", int(snn_radius))
            c_snn.set_property("pairs", int(pairs))
            oil_layer.merge_filter(filt_snn)

            # 4. Rich Oil Pigment Saturation Boost
            filt_vib = Gimp.DrawableFilter.new(oil_layer, "gegl:vibrance", "")
            c_vib = filt_vib.get_config()
            c_vib.set_property("vibrance", 0.18)
            oil_layer.merge_filter(filt_vib)

            # 5. Directional Surface Relief & Bristle Detailing (if lighting enabled)
            if bool(lighting_val) and (float(shine_val) > 0.05 or float(bristle_val) > 0.5):
                rad = math.radians(float(angle_val))
                dx = math.cos(rad)
                dy = math.sin(rad)
                strength = (float(shine_val) * 0.35 + float(bristle_val) * 0.08) * (float(scale_val) * 0.35)
                strength = min(1.2, max(0.05, strength))

                filt_conv = Gimp.DrawableFilter.new(oil_layer, "gegl:convolution-matrix", "")
                c_conv = filt_conv.get_config()
                c_conv.set_property("b3", float(-dy * strength))
                c_conv.set_property("d3", float(dy * strength))
                c_conv.set_property("c2", float(-dx * strength))
                c_conv.set_property("c4", float(dx * strength))
                c_conv.set_property("c3", 1.0)
                c_conv.set_property("normalize", False)
                c_conv.set_property("divisor", 1.0)
                c_conv.set_property("offset", 0.0)
                oil_layer.merge_filter(filt_conv)

            # 6. Attach Layer Mask
            if mask_type == "conceal-all":
                mask = oil_layer.create_mask(Gimp.AddMaskType.BLACK)
                oil_layer.add_mask(mask)
            elif mask_type == "selection":
                if saved_sel_channel is not None:
                    image.select_item(Gimp.ChannelOps.REPLACE, saved_sel_channel)
                    mask = oil_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    oil_layer.add_mask(mask)
                    Gimp.Selection.none(image)
                else:
                    mask = oil_layer.create_mask(Gimp.AddMaskType.WHITE)
                    oil_layer.add_mask(mask)
            else:  # reveal-all
                mask = oil_layer.create_mask(Gimp.AddMaskType.WHITE)
                oil_layer.add_mask(mask)

            # Cleanup saved selection channel
            if saved_sel_channel is not None:
                image.remove_channel(saved_sel_channel)

            image.set_selected_layers([oil_layer])
            oil_layer.set_visible(True)

        except Exception as e:
            image.undo_group_end()
            Gimp.context_pop()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-oil-paint"),
                    f"Oil Paint effect failed: {str(e)}",
                    0
                )
            )

        image.undo_group_end()
        Gimp.context_pop()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(OilPaintPlugin.__gtype__, sys.argv)
