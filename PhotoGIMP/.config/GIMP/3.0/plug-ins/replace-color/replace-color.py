#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Replace Color & Targeted Object Recoloring Helper Plugin
==================================================================================
Photoshop Reference:
- Topics.txt line 337: "Replace Object Colors by Applying a Hue or Saturation Adjustment"
- Topics.txt line 339: "Make selective color adjustments"
- photoshop_docs.md Section 331 lines 9698-9714:
  "Replace Object Colors by Applying a Hue or Saturation Adjustment:
   Learn more about replacing the color of selected objects in professional photoeditor
   using Hue/Saturation adjustment layers for flexible, non-destructive editing...
   move the Hue and Saturation sliders to replace the object's color...
   If original color tints the new one, select Colorize... set adjustment layer
   to Hue or Color blending mode... Paint on mask with black or white to refine affected area."

Key Architectural Features:
1. Non-Destructive Adjustment Layer Workflow:
   - Duplicates the target layer into an isolated adjustment layer positioned directly
     above the active drawable. Base layer pixels underneath remain 100% mathematically
     untouched (diff == 0.000000).
2. Perceptual Fuzziness Masking:
   - Samples target object color and calculates color selection with adjustable fuzziness
     tolerance and feather falloff, producing smooth, artifact-free boundary transitions.
3. Complete Color Transformation:
   - Relative Hue shift (-180° to +180°), Saturation shift (-100 to +100), and Lightness
     shift (-100 to +100) using native PDB procedure `gimp-drawable-hue-saturation`.
   - Dedicated Colorize mode using native PDB procedure `gimp-drawable-colorize-hsl`
     for recoloring neutral/grayscale elements or tinting uniformly.
4. Professional Compositing Blend Modes:
   - Color (HSL_COLOR, Photoshop standard preserving luminance detail), Hue (HSV_HUE),
     Normal, and Soft Light.
5. Flexible Layer Mask Modes:
   - Fuzziness Mask (feathered selection mask isolated to target color), Conceal All
     (black mask), Reveal All (white mask), and Active Selection.
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


TARGET_PRESETS = {
    "sampled-color": {
        "label": "Sampled Color",
        "desc": "Custom RGB sample color",
        "color": None,
    },
    "reds": {
        "label": "Reds",
        "desc": "Pure Red hue range (0° / 360°)",
        "color": (1.0, 0.0, 0.0),
    },
    "yellows": {
        "label": "Yellows",
        "desc": "Yellow hue range (60°)",
        "color": (1.0, 1.0, 0.0),
    },
    "greens": {
        "label": "Greens",
        "desc": "Green hue range (120°)",
        "color": (0.0, 1.0, 0.0),
    },
    "cyans": {
        "label": "Cyans",
        "desc": "Cyan hue range (180°)",
        "color": (0.0, 1.0, 1.0),
    },
    "blues": {
        "label": "Blues",
        "desc": "Blue hue range (240°)",
        "color": (0.0, 0.0, 1.0),
    },
    "magentas": {
        "label": "Magentas",
        "desc": "Magenta hue range (300°)",
        "color": (1.0, 0.0, 1.0),
    },
}

BLEND_MODES = {
    "color": Gimp.LayerMode.HSL_COLOR,
    "hue": Gimp.LayerMode.HSV_HUE,
    "normal": Gimp.LayerMode.NORMAL,
    "soft-light": Gimp.LayerMode.SOFTLIGHT,
}


def replace_color_run(procedure, run_mode, image, drawables, config, data):
    if image is None:
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-replace-color"),
                "No valid image provided.",
                0
            )
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-replace-color')
        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    # Read configuration parameters
    target_preset = config.get_property('target-preset')
    sample_r = config.get_property('sample-r')
    sample_g = config.get_property('sample-g')
    sample_b = config.get_property('sample-b')
    fuzziness = config.get_property('fuzziness')
    hue_shift = config.get_property('hue-shift')
    sat_shift = config.get_property('saturation-shift')
    light_shift = config.get_property('lightness-shift')
    colorize = config.get_property('colorize')
    blend_mode = config.get_property('blend-mode')
    mask_mode = config.get_property('mask-mode')
    opacity = config.get_property('opacity')

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
                GLib.quark_from_string("gimp-replace-color"),
                "No valid target layer found.",
                0
            )
        )

    # Resolve target sample color
    if target_preset in TARGET_PRESETS and TARGET_PRESETS[target_preset]["color"] is not None:
        cr, cg, cb = TARGET_PRESETS[target_preset]["color"]
        preset_label = TARGET_PRESETS[target_preset]["label"]
    else:
        cr, cg, cb = float(sample_r), float(sample_g), float(sample_b)
        preset_label = f"#{int(cr * 255):02X}{int(cg * 255):02X}{int(cb * 255):02X}"

    layer_name = f"Replace Color ({preset_label})"

    Gimp.context_push()
    image.undo_group_start()

    saved_user_sel = None
    try:
        # Save pre-existing user selection if any (Decision D-003)
        has_user_selection = not Gimp.Selection.is_empty(image)
        if has_user_selection:
            saved_user_sel = Gimp.Selection.save(image)
            Gimp.Selection.none(image)

        # Create non-destructive duplicate adjustment layer
        adj_layer = Gimp.Layer.new_from_drawable(target_layer, image)
        adj_layer.set_name(layer_name)

        # Set blend mode and opacity
        gimp_mode = BLEND_MODES.get(blend_mode, Gimp.LayerMode.HSL_COLOR)
        adj_layer.set_mode(gimp_mode)
        adj_layer.set_opacity(max(0.0, min(100.0, float(opacity))))

        # Insert immediately above target layer
        parent = target_layer.get_parent()
        pos = image.get_item_position(target_layer)
        image.insert_layer(adj_layer, parent, pos)

        # Apply color transformation
        if colorize:
            p_col = Gimp.get_pdb().lookup_procedure("gimp-drawable-colorize-hsl")
            if p_col:
                col_cfg = p_col.create_config()
                col_cfg.set_property("drawable", adj_layer)
                # Map hue shift (-180 to +180) to degrees (0 to 360)
                col_hue = float(hue_shift) % 360.0
                if col_hue < 0.0:
                    col_hue += 360.0
                # Saturation: default 50% shifted by sat_shift (-100 to +100)
                col_sat = max(0.0, min(100.0, 50.0 + float(sat_shift) * 0.5))
                col_light = max(-100.0, min(100.0, float(light_shift)))
                col_cfg.set_property("hue", col_hue)
                col_cfg.set_property("saturation", col_sat)
                col_cfg.set_property("lightness", col_light)
                p_col.run(col_cfg)
        else:
            # Hue-Saturation adjustment
            p_hs = Gimp.get_pdb().lookup_procedure("gimp-drawable-hue-saturation")
            if p_hs:
                hs_cfg = p_hs.create_config()
                hs_cfg.set_property("drawable", adj_layer)
                hs_cfg.set_property("hue-range", Gimp.HueRange.ALL)
                hs_cfg.set_property("hue-offset", float(hue_shift))
                hs_cfg.set_property("saturation", float(sat_shift))
                hs_cfg.set_property("lightness", float(light_shift))
                hs_cfg.set_property("overlap", 0.0)
                p_hs.run(hs_cfg)

        # Generate layer mask
        if mask_mode == "fuzziness":
            # Compute threshold and feather based on fuzziness (0 to 100)
            fuzz_val = max(0.0, min(100.0, float(fuzziness)))
            sample_threshold = max(0.01, min(1.0, (fuzz_val / 100.0) * 0.85))
            Gimp.context_set_sample_threshold(sample_threshold)

            target_gegl = Gegl.Color.new(f"rgb({cr:.4f}, {cg:.4f}, {cb:.4f})")
            image.select_color(Gimp.ChannelOps.REPLACE, target_layer, target_gegl)

            # Feather selection to create smooth perceptual gradient falloff
            feather_px = max(1.0, fuzz_val / 15.0)
            Gimp.Selection.feather(image, feather_px)

            # If the user already had an active selection, constrain to it
            if has_user_selection and saved_user_sel is not None:
                image.select_item(Gimp.ChannelOps.INTERSECT, saved_user_sel)

            mask = adj_layer.create_mask(Gimp.AddMaskType.SELECTION)
            adj_layer.add_mask(mask)
            Gimp.Selection.none(image)

        elif mask_mode == "conceal-all":
            mask = adj_layer.create_mask(Gimp.AddMaskType.BLACK)
            adj_layer.add_mask(mask)

        elif mask_mode == "selection":
            if has_user_selection and saved_user_sel is not None:
                image.select_item(Gimp.ChannelOps.REPLACE, saved_user_sel)
                mask = adj_layer.create_mask(Gimp.AddMaskType.SELECTION)
                adj_layer.add_mask(mask)
                Gimp.Selection.none(image)
            else:
                mask = adj_layer.create_mask(Gimp.AddMaskType.WHITE)
                adj_layer.add_mask(mask)

        else:  # "reveal-all"
            mask = adj_layer.create_mask(Gimp.AddMaskType.WHITE)
            adj_layer.add_mask(mask)

        # Clean up temporary user selection channel
        if saved_user_sel is not None:
            try:
                image.remove_channel(saved_user_sel)
                saved_user_sel = None
            except Exception:
                pass

        image.set_selected_layers([adj_layer])
        image.undo_group_end()
        Gimp.context_pop()
        Gimp.displays_flush()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    except Exception as e:
        if saved_user_sel is not None:
            try:
                image.remove_channel(saved_user_sel)
            except Exception:
                pass
        image.undo_group_end()
        Gimp.context_pop()
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-replace-color"),
                f"Replace Color failed: {str(e)}",
                0
            )
        )


class ReplaceColorPlugin(Gimp.PlugIn):
    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-replace-color"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, replace_color_run, None
        )
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
        procedure.set_menu_label("Replace Color...")
        procedure.add_menu_path("<Image>/Image/Adjustments")
        procedure.add_menu_path("<Image>/Colors")
        procedure.add_menu_path("<Image>/Filters/Retouching")
        procedure.add_menu_path("<Image>/Layer")

        procedure.set_documentation(
            "Non-Destructive Replace Color & Targeted Object Recoloring Helper",
            "Simulates Photoshop Image > Adjustments > Replace Color with sampled "
            "color target selection, fuzziness tolerance mask, Hue/Saturation/Lightness "
            "transformation, Colorize mode, and non-destructive adjustment layer output.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Target Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add("sampled-color", 0, "Sampled Color", "Sample custom RGB color via sliders")
        preset_choice.add("reds", 1, "Reds", "Target pure Red color range")
        preset_choice.add("yellows", 2, "Yellows", "Target Yellow color range")
        preset_choice.add("greens", 3, "Greens", "Target Green color range")
        preset_choice.add("cyans", 4, "Cyans", "Target Cyan color range")
        preset_choice.add("blues", 5, "Blues", "Target Blue color range")
        preset_choice.add("magentas", 6, "Magentas", "Target Magenta color range")

        procedure.add_choice_argument(
            "target-preset",
            "Target Preset",
            "Sampled color or standard color range preset",
            preset_choice,
            "reds",
            GObject.ParamFlags.READWRITE
        )

        # 2. Sample Red (0.0 to 1.0, default 1.0)
        procedure.add_double_argument(
            "sample-r",
            "Sample Red",
            "Target sampled red color component (0.0 to 1.0)",
            0.0,
            1.0,
            1.0,
            GObject.ParamFlags.READWRITE
        )

        # 3. Sample Green (0.0 to 1.0, default 0.0)
        procedure.add_double_argument(
            "sample-g",
            "Sample Green",
            "Target sampled green color component (0.0 to 1.0)",
            0.0,
            1.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 4. Sample Blue (0.0 to 1.0, default 0.0)
        procedure.add_double_argument(
            "sample-b",
            "Sample Blue",
            "Target sampled blue color component (0.0 to 1.0)",
            0.0,
            1.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 5. Fuzziness (0.0 to 100.0, default 40.0)
        procedure.add_double_argument(
            "fuzziness",
            "Fuzziness Tolerance",
            "Tolerance threshold and feather falloff around sampled color (0 to 100)",
            0.0,
            100.0,
            40.0,
            GObject.ParamFlags.READWRITE
        )

        # 6. Hue Shift (-180.0 to +180.0, default 0.0)
        procedure.add_double_argument(
            "hue-shift",
            "Hue Shift",
            "Hue angle rotation in degrees (-180.0 to +180.0)",
            -180.0,
            180.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 7. Saturation Shift (-100.0 to +100.0, default 0.0)
        procedure.add_double_argument(
            "saturation-shift",
            "Saturation Shift",
            "Saturation adjustment (-100.0 to +100.0)",
            -100.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 8. Lightness Shift (-100.0 to +100.0, default 0.0)
        procedure.add_double_argument(
            "lightness-shift",
            "Lightness Shift",
            "Brightness / Lightness adjustment (-100.0 to +100.0)",
            -100.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 9. Colorize Toggle (default False)
        procedure.add_boolean_argument(
            "colorize",
            "Colorize",
            "Uniformly tint target area to specified replacement hue",
            False,
            GObject.ParamFlags.READWRITE
        )

        # 10. Blend Mode Choice
        blend_choice = Gimp.Choice.new()
        blend_choice.add("color", 0, "Color (HSL Color)", "Replaces color while preserving luminance detail")
        blend_choice.add("hue", 1, "Hue (HSV Hue)", "Replaces hue while preserving saturation and luminance")
        blend_choice.add("normal", 2, "Normal", "Direct normal pixel replacement")
        blend_choice.add("soft-light", 3, "Soft Light", "Subtle photographic color blend")

        procedure.add_choice_argument(
            "blend-mode",
            "Blend Mode",
            "Layer blend mode for recoloring",
            blend_choice,
            "color",
            GObject.ParamFlags.READWRITE
        )

        # 11. Mask Mode Choice
        mask_choice = Gimp.Choice.new()
        mask_choice.add("fuzziness", 0, "Fuzziness Mask", "Feathered selection mask isolating sampled color")
        mask_choice.add("conceal-all", 1, "Conceal All (Black Mask)", "Fully concealed, paint in with brush")
        mask_choice.add("reveal-all", 2, "Reveal All (White Mask)", "Full effect across layer")
        mask_choice.add("selection", 3, "Active Selection", "Confine effect strictly to active selection")

        procedure.add_choice_argument(
            "mask-mode",
            "Layer Mask Mode",
            "Type of layer mask attached to the adjustment layer",
            mask_choice,
            "fuzziness",
            GObject.ParamFlags.READWRITE
        )

        # 12. Opacity (0.0 to 100.0, default 100.0)
        procedure.add_double_argument(
            "opacity",
            "Opacity (%)",
            "Overall opacity of recoloring adjustment layer (0.0 to 100.0)",
            0.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        return procedure


Gimp.main(ReplaceColorPlugin.__gtype__, sys.argv)
