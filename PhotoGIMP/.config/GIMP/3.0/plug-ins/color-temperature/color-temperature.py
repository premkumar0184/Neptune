#!/usr/bin/env python3
"""
PhotoGIMP Non-Destructive Color Temperature & White Balance Helper Plugin for GIMP 3.x

Creates a dedicated non-destructive Color Temperature adjustment layer duplicating
the target drawable and applying GEGL `gegl:color-temperature` to correct white balance,
warm up golden hour/sunset scenes, or cool down nocturnal/shade scenes using authentic
physical Kelvin blackbody radiation values inspired by Adobe Photoshop's Color & Vibrance
and Camera Raw White Balance commands.

Photoshop Equivalence:
- Topics.txt line 100: Correct color balance with Color and vibrance.
- photoshop_docs.md Section 104 line 3184 & 3192: Adjust Temperature, Tint, Vibrance, Saturation and fix White Balance to achieve balanced and natural-looking colors.
- photoshop_docs.md line 3192: Temperature: Adjusts the warmth or coolness of the colors.

Key Advantages over destructive color adjustments:
1. 100% Non-Destructive: Duplicates target layer into an isolated adjustment layer.
2. Authentic Physical Kelvin Presets:
   - Warming: Golden Hour / Sunset (6500K -> 9000K, rich amber warmth)
   - Warming: Tungsten Indoor Glow (5500K -> 7500K, warm interior illumination)
   - Cooling: Shade / Blue Hour (6500K -> 4800K, crisp alpine/shade coolness)
   - Cooling: Nocturnal Moonlight (6500K -> 3800K, deep midnight blue tone)
   - Candlelight Glow (5500K -> 10500K, fiery deep warmth)
   - Daylight Normalization (4000K -> 5500K, neutral daylight white balance)
   - Custom Kelvin Temperatures (independent Original and Intended Kelvin sliders)
3. Reveal-All Layer Mask: Attached automatically for selective brush painting on subjects/faces.
4. Target Layer Invariance: Source image pixels underneath remain 100% untouched.
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
    "warm-sunset": {
        "label": "Warming: Golden Hour (Sunset Glow)",
        "orig": 6500.0,
        "intended": 9000.0,
    },
    "warm-tungsten": {
        "label": "Warming: Tungsten (Warm Indoor Glow)",
        "orig": 5500.0,
        "intended": 7500.0,
    },
    "cool-shade": {
        "label": "Cooling: Shade / Blue Hour",
        "orig": 6500.0,
        "intended": 4800.0,
    },
    "cool-night": {
        "label": "Cooling: Nocturnal Moonlight",
        "orig": 6500.0,
        "intended": 3800.0,
    },
    "candlelight": {
        "label": "Candlelight Glow (Deep Fiery Amber)",
        "orig": 5500.0,
        "intended": 10500.0,
    },
    "daylight-correct": {
        "label": "Daylight Normalization (4000K -> 5500K)",
        "orig": 4000.0,
        "intended": 5500.0,
    },
    "custom": {
        "label": "Custom Kelvin Temperature",
    },
}


def color_temperature(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-color-temperature"),
                "No valid image provided.",
                0
            )
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-color-temperature')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    # Read configuration parameters
    preset = config.get_property('preset')
    orig_temp = config.get_property('original-temperature')
    intended_temp = config.get_property('intended-temperature')
    opacity = config.get_property('opacity')
    add_mask = config.get_property('add-mask')

    # Resolve target layer (must be a Gimp.Layer, not a Gimp.LayerMask)
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
                GLib.quark_from_string("gimp-color-temperature"),
                "No valid target layer found.",
                0
            )
        )

    Gimp.context_push()
    image.undo_group_start()

    try:
        preset_info = PRESETS.get(preset, PRESETS["warm-sunset"])
        label = preset_info.get("label", "Custom")
        layer_name = f"Color Temperature ({label})"

        # Create non-destructive duplicate layer
        ct_layer = Gimp.Layer.new_from_drawable(target_layer, image)
        ct_layer.set_name(layer_name)
        ct_layer.set_opacity(max(10.0, min(100.0, float(opacity))))
        ct_layer.set_mode(Gimp.LayerMode.NORMAL)

        parent = target_layer.get_parent()
        pos = image.get_item_position(target_layer)
        image.insert_layer(ct_layer, parent, pos)

        # Resolve temperatures in Kelvin
        if preset in PRESETS and preset != "custom":
            p = PRESETS[preset]
            orig_k = p["orig"]
            intended_k = p["intended"]
        else:
            orig_k = max(1000.0, min(12000.0, float(orig_temp)))
            intended_k = max(1000.0, min(12000.0, float(intended_temp)))

        # Apply GEGL color-temperature filter
        filt = Gimp.DrawableFilter.new(ct_layer, "gegl:color-temperature", "")
        filt_config = filt.get_config()
        filt_config.set_property("original-temperature", float(orig_k))
        filt_config.set_property("intended-temperature", float(intended_k))

        ct_layer.append_filter(filt)
        ct_layer.merge_filters()

        # Attach reveal-all layer mask if requested
        if add_mask:
            mask = ct_layer.create_mask(Gimp.AddMaskType.WHITE)
            ct_layer.add_mask(mask)

        # Set newly created layer as active
        image.set_selected_layers([ct_layer])

        Gimp.displays_flush()
        image.undo_group_end()
        Gimp.context_pop()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    except Exception as exc:
        image.undo_group_end()
        Gimp.context_pop()
        msg = "Color Temperature layer creation failed: " + str(exc)
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-color-temperature"),
                msg,
                0
            )
        )


class ColorTemperaturePlugin(Gimp.PlugIn):
    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-color-temperature"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            color_temperature,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        procedure.set_menu_label("Color _Temperature...")
        procedure.set_documentation(
            "Corrects white balance and adjusts Kelvin temperature warmly or coolly",
            "Creates a dedicated non-destructive Color Temperature adjustment layer duplicating the target drawable. "
            "Applies GEGL color-temperature to correct camera white balance and adjust ambient lighting temperature "
            "between warm golden hour amber and cool shade/moonlight inspired by Adobe Photoshop.",
            name
        )
        procedure.set_attribution("Antigravity Ralph / PhotoGIMP", "PhotoGIMP", "2026")

        procedure.add_menu_path("<Image>/Colors")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        # Preset Choice Argument
        preset_choice = Gimp.Choice.new()
        preset_choice.add(
            "warm-sunset",
            0,
            "Warming: Golden Hour (Sunset Glow)",
            "Rich warm golden hour sunset glow (6500K -> 9000K)"
        )
        preset_choice.add(
            "warm-tungsten",
            1,
            "Warming: Tungsten (Warm Indoor Glow)",
            "Warm interior tungsten lighting glow (5500K -> 7500K)"
        )
        preset_choice.add(
            "cool-shade",
            2,
            "Cooling: Shade / Blue Hour",
            "Crisp cool outdoor shade and blue hour tint (6500K -> 4800K)"
        )
        preset_choice.add(
            "cool-night",
            3,
            "Cooling: Nocturnal Moonlight",
            "Deep cool nocturnal moonlight tone (6500K -> 3800K)"
        )
        preset_choice.add(
            "candlelight",
            4,
            "Candlelight Glow (Deep Fiery Amber)",
            "Intense fiery amber candlelight illumination (5500K -> 10500K)"
        )
        preset_choice.add(
            "daylight-correct",
            5,
            "Daylight Normalization (4000K -> 5500K)",
            "Neutral daylight white balance correction from indoor light"
        )
        preset_choice.add(
            "custom",
            6,
            "Custom Kelvin Temperature",
            "Manually adjust original and intended Kelvin temperature sliders"
        )

        procedure.add_choice_argument(
            "preset",
            "_Preset",
            "White balance and temperature preset style",
            preset_choice,
            "warm-sunset",
            GObject.ParamFlags.READWRITE
        )

        # Original Temperature Slider (1000K to 12000K, default 6500K)
        procedure.add_double_argument(
            "original-temperature",
            "_Original Temperature (K)",
            "Estimated temperature of the light source in Kelvin the image was taken with",
            1000.0,
            12000.0,
            6500.0,
            GObject.ParamFlags.READWRITE
        )

        # Intended Temperature Slider (1000K to 12000K, default 6500K)
        procedure.add_double_argument(
            "intended-temperature",
            "_Intended Temperature (K)",
            "Corrected target temperature of the light source in Kelvin",
            1000.0,
            12000.0,
            6500.0,
            GObject.ParamFlags.READWRITE
        )

        # Layer Opacity Slider (10% to 100%, default 100%)
        procedure.add_double_argument(
            "opacity",
            "Layer _Opacity (%)",
            "Overall opacity of the Color Temperature adjustment layer (10% to 100%)",
            10.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # Reveal-All Layer Mask Option
        procedure.add_boolean_argument(
            "add-mask",
            "_Attach Layer Mask",
            "Attach a reveal-all white layer mask for selective brush painting",
            True,
            GObject.ParamFlags.READWRITE
        )

        return procedure


Gimp.main(ColorTemperaturePlugin.__gtype__, sys.argv)
