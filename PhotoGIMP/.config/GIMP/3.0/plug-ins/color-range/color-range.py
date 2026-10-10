#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Color Range Selection & Isolation Helper Plugin
=========================================================================
Photoshop Reference:
- Topics.txt line 202: "Select a Color Range in Photoshop"
- Topics.txt line 208: "Refine and modify selections - Refine your selection and mask"
- Topics.txt line 219: "Refine and soften selection edges"
- photoshop_docs.md Section 3111-3123 (Use Color Range to create a precise mask)
- photoshop_docs.md Section 6044-6062 (Select > Color Range: Skin Tones, Highlights, Midtones,
  Shadows, Reds, Yellows, Greens, Cyans, Blues, Magentas, Fuzziness)

Key Architectural Features:
1. Targeted Color Range Families:
   - Reds, Yellows, Greens, Cyans, Blues, Magentas: Primary and secondary spectral color ranges.
   - Highlights: Upper tonal luminance band (whites and bright specular tones).
   - Midtones: Medium neutral luminance band.
   - Shadows: Lower tonal luminance band (deep shadows and dark tones).
   - Skin Tones: Photographic portrait Caucasian, Mediterranean, and deeper melanin skin tones.
   - Sampled Colors: User-defined color from current foreground context.
2. Continuous Fuzziness Thresholding:
   - Fuzziness slider (0 to 100) calibrates sampling tolerance, mapping smoothly to GIMP's
     sampling threshold for subtle feathering and precision.
3. Edge Refinement:
   - Shift Edge (Shrink / Grow) from -50px to +50px.
   - Edge Feathering (Fade) from 0.0px to 50.0px for seamless gradient blending.
   - Invert selection toggle.
4. Flexible Output Modes:
   - New Layer with Mask: Isolated duplicate layer with attached layer mask, keeping the base layer
     underneath 100% untouched (0.000000 diff).
   - Selection Only: Sets active marching ants selection on the image canvas.
   - Channel Mask: Saves the selection into a new reusable Channel in the Channels dialog.
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


RANGE_PRESETS = {
    "reds": {
        "label": "Reds",
        "colors": [
            "rgb(1.0, 0.0, 0.0)",
            "rgb(0.85, 0.10, 0.10)",
        ],
        "default_fuzz": 35.0,
    },
    "yellows": {
        "label": "Yellows",
        "colors": [
            "rgb(1.0, 1.0, 0.0)",
            "rgb(0.90, 0.85, 0.10)",
        ],
        "default_fuzz": 35.0,
    },
    "greens": {
        "label": "Greens",
        "colors": [
            "rgb(0.0, 1.0, 0.0)",
            "rgb(0.10, 0.80, 0.10)",
        ],
        "default_fuzz": 35.0,
    },
    "cyans": {
        "label": "Cyans",
        "colors": [
            "rgb(0.0, 1.0, 1.0)",
            "rgb(0.10, 0.85, 0.85)",
        ],
        "default_fuzz": 35.0,
    },
    "blues": {
        "label": "Blues",
        "colors": [
            "rgb(0.0, 0.0, 1.0)",
            "rgb(0.10, 0.10, 0.85)",
        ],
        "default_fuzz": 35.0,
    },
    "magentas": {
        "label": "Magentas",
        "colors": [
            "rgb(1.0, 0.0, 1.0)",
            "rgb(0.85, 0.10, 0.85)",
        ],
        "default_fuzz": 35.0,
    },
    "highlights": {
        "label": "Highlights",
        "colors": [
            "rgb(1.0, 1.0, 1.0)",
            "rgb(0.92, 0.92, 0.92)",
        ],
        "default_fuzz": 45.0,
    },
    "shadows": {
        "label": "Shadows",
        "colors": [
            "rgb(0.0, 0.0, 0.0)",
            "rgb(0.08, 0.08, 0.08)",
        ],
        "default_fuzz": 45.0,
    },
    "midtones": {
        "label": "Midtones",
        "colors": [
            "rgb(0.50, 0.50, 0.50)",
            "rgb(0.40, 0.40, 0.40)",
            "rgb(0.60, 0.60, 0.60)",
        ],
        "default_fuzz": 40.0,
    },
    "skin-tones": {
        "label": "Skin Tones",
        "colors": [
            "rgb(0.80, 0.60, 0.50)",
            "rgb(0.65, 0.45, 0.35)",
            "rgb(0.88, 0.72, 0.60)",
        ],
        "default_fuzz": 40.0,
    },
    "sampled": {
        "label": "Sampled Colors",
        "colors": [],
        "default_fuzz": 30.0,
    },
}


class ColorRangePlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-color-range"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, self.run, None
        )
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
        procedure.set_menu_label("Color Range...")
        procedure.add_menu_path("<Image>/Select")
        procedure.add_menu_path("<Image>/Filters/Retouching")
        procedure.add_menu_path("<Image>/Layer")

        procedure.set_documentation(
            "Non-Destructive Color Range Selection & Isolation Helper",
            "Selects targeted spectral color families, highlights, midtones, shadows, or skin tones "
            "with continuous fuzziness tolerance and edge refinement, outputting to a non-destructive "
            "layer with mask, active selection, or channel.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # Color Range Choice
        range_choice = Gimp.Choice.new()
        range_choice.add("reds", 0, "Reds", "Select red hue tones")
        range_choice.add("yellows", 1, "Yellows", "Select yellow hue tones")
        range_choice.add("greens", 2, "Greens", "Select green hue tones")
        range_choice.add("cyans", 3, "Cyans", "Select cyan hue tones")
        range_choice.add("blues", 4, "Blues", "Select blue hue tones")
        range_choice.add("magentas", 5, "Magentas", "Select magenta hue tones")
        range_choice.add("highlights", 6, "Highlights", "Select upper luminance highlight tones")
        range_choice.add("midtones", 7, "Midtones", "Select neutral midtone luminance tones")
        range_choice.add("shadows", 8, "Shadows", "Select deep shadow luminance tones")
        range_choice.add("skin-tones", 9, "Skin Tones", "Select photographic portrait skin tones")
        range_choice.add("sampled", 10, "Sampled Colors", "Select colors matching current foreground context")

        procedure.add_choice_argument(
            "target-range",
            "Select Range",
            "Target color family or tonal range (reds, yellows, greens, cyans, blues, magentas, highlights, midtones, shadows, skin-tones, sampled)",
            range_choice,
            "reds",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "fuzziness",
            "Fuzziness",
            "Color sampling tolerance and falloff width (0.0 to 100.0, default 40.0)",
            0.0,
            100.0,
            40.0,
            GObject.ParamFlags.READWRITE
        )

        # Output Mode Choice
        out_choice = Gimp.Choice.new()
        out_choice.add(
            "new-layer-mask",
            0,
            "New Layer with Mask (Non-Destructive)",
            "Creates a duplicate layer with attached color mask, leaving base layer untouched"
        )
        out_choice.add(
            "selection-only",
            1,
            "Selection Only (Marching Ants)",
            "Sets the active selection on the canvas without altering layers"
        )
        out_choice.add(
            "channel-mask",
            2,
            "Save to Channel Mask",
            "Saves the color range selection to a reusable channel in the Channels panel"
        )

        procedure.add_choice_argument(
            "output-mode",
            "Output Mode",
            "Destination of the color range selection (new-layer-mask, selection-only, channel-mask)",
            out_choice,
            "new-layer-mask",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "feather-radius",
            "Feather Radius (px)",
            "Softness radius of the selection edge for smooth blending (0.0 to 50.0px)",
            0.0,
            50.0,
            1.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "shift-edge",
            "Shift Edge (px)",
            "Expand (+px) or contract (-px) the selection boundary (-50.0 to +50.0px)",
            -50.0,
            50.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_boolean_argument(
            "invert",
            "Invert Selection",
            "Inverts the final color range selection mask",
            False,
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run(self, procedure, run_mode, image, drawables, config, data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            Gimp.ui_init("color-range.py")
            dialog = Gimp.ProcedureDialog.new(procedure, config, "Color Range")
            dialog.fill(["target-range", "fuzziness", "output-mode", "feather-radius", "shift-edge", "invert"])
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
                    GLib.quark_from_string("gimp-color-range"),
                    "No target drawable found to apply color range.",
                    0
                )
            )

        range_key = config.get_property("target-range") or "reds"
        if range_key not in RANGE_PRESETS:
            range_key = "reds"
        range_cfg = RANGE_PRESETS[range_key]

        fuzziness_val = config.get_property("fuzziness")
        feather_val = config.get_property("feather-radius")
        shift_val = config.get_property("shift-edge")
        output_mode = config.get_property("output-mode") or "new-layer-mask"
        invert_flag = config.get_property("invert")

        # Map fuzziness (0-100) to GIMP sampling threshold (0.01 - 1.0)
        sample_threshold = min(1.0, max(0.01, (float(fuzziness_val) / 100.0) * 0.45 + 0.05))

        Gimp.context_push()
        image.undo_group_start()

        try:
            # Set sampling threshold
            Gimp.context_set_sample_threshold(sample_threshold)

            # Determine colors to sample
            if range_key == "sampled":
                fg_color = Gimp.context_get_foreground()
                color_list = [fg_color]
            else:
                color_list = [Gegl.Color.new(c_str) for c_str in range_cfg["colors"]]

            # Select colors across the target drawable
            first = True
            for color_obj in color_list:
                op = Gimp.ChannelOps.REPLACE if first else Gimp.ChannelOps.ADD
                image.select_color(op, target_drawable, color_obj)
                first = False

            # Invert toggle if requested
            if invert_flag:
                Gimp.Selection.invert(image)

            # Shift Edge (Grow / Shrink)
            if abs(float(shift_val)) >= 0.5:
                shift_int = int(round(float(shift_val)))
                if shift_int > 0:
                    Gimp.Selection.grow(image, shift_int)
                elif shift_int < 0:
                    Gimp.Selection.shrink(image, -shift_int)

            # Feather Edge
            if float(feather_val) > 0.05:
                Gimp.Selection.feather(image, float(feather_val))

            # Handle Output Mode
            if output_mode == "selection-only":
                # Leave marching ants active on canvas
                pass

            elif output_mode == "channel-mask":
                mask_channel = Gimp.Selection.save(image)
                mask_channel.set_name(f"Color Range Mask ({range_cfg['label']})")
                Gimp.Selection.none(image)

            elif output_mode == "new-layer-mask":
                layer_name = f"Color Range ({range_cfg['label']})"
                dup_layer = Gimp.Layer.new_from_drawable(target_drawable, image)
                dup_layer.set_name(layer_name)
                dup_layer.set_mode(Gimp.LayerMode.NORMAL)
                dup_layer.set_opacity(100.0)

                parent = target_drawable.get_parent()
                pos = image.get_item_position(target_drawable)
                image.insert_layer(dup_layer, parent, pos)

                mask = dup_layer.create_mask(Gimp.AddMaskType.SELECTION)
                dup_layer.add_mask(mask)
                Gimp.Selection.none(image)

        except Exception as e:
            image.undo_group_end()
            Gimp.context_pop()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-color-range"),
                    f"Color Range failed: {str(e)}",
                    0
                )
            )

        image.undo_group_end()
        Gimp.context_pop()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(ColorRangePlugin.__gtype__, sys.argv)
