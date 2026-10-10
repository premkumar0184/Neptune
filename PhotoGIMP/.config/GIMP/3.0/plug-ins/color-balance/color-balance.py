#!/usr/bin/env python3
"""
PhotoGIMP Non-Destructive Color Balance & Tonal Grading Helper Plugin for GIMP 3.x

Creates a dedicated non-destructive Color Balance adjustment layer duplicating
the target drawable and applying 3-way color grading across Shadows, Midtones,
and Highlights with Cyan-Red, Magenta-Green, and Yellow-Blue controls, luminosity
preservation, cinematic presets, and an attached reveal-all layer mask inspired
by Adobe Photoshop's Color Balance adjustment command.

Photoshop Equivalence:
- Topics.txt line 328: Apply Color Balance adjustment in Photoshop.
- Topics.txt line 100: Correct color balance with Color and vibrance.
- photoshop_docs.md Section 3072 & line 3216: Color Balance: Changes overall color cast.

Key Advantages over destructive color balance:
1. 100% Non-Destructive: Duplicates target layer into an isolated adjustment layer.
2. 3-Way Tonal Split: Independent color balancing for Shadows, Midtones, and Highlights.
3. Cinematic & Photographic Presets: Teal & Orange, Warm Sunset, Cool Moonlight,
   Vintage Cross-Process, and Custom tonal sliders.
4. Preserve Luminosity: Prevents brightness shifts during aggressive color grading.
5. Reveal-All Layer Mask: Attached automatically for selective brush painting.
6. Target Layer Invariance: Source image pixels underneath remain 100% untouched.
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
    "teal-orange": {
        "label": "Teal & Orange",
        "shadows": (-30.0, 0.0, 30.0),       # Cyan/Blue in shadows
        "midtones": (15.0, 0.0, -15.0),      # Warm midtones
        "highlights": (35.0, -5.0, -30.0),   # Golden Amber in highlights
    },
    "warm-sunset": {
        "label": "Warm Sunset",
        "shadows": (0.0, 0.0, -10.0),        # Slight warm shadows
        "midtones": (25.0, 5.0, -25.0),      # Rich warm midtones
        "highlights": (45.0, 0.0, -40.0),    # Vibrant golden highlights
    },
    "cool-night": {
        "label": "Cool Moonlight",
        "shadows": (-25.0, 0.0, 35.0),       # Deep blue/cyan shadows
        "midtones": (-15.0, 5.0, 25.0),      # Cool midtones
        "highlights": (-10.0, 0.0, 20.0),    # Silver blue highlights
    },
    "cross-process": {
        "label": "Vintage Cross-Process",
        "shadows": (15.0, -20.0, 20.0),      # Green/Blue shadows
        "midtones": (-10.0, 15.0, -15.0),    # Magenta/Yellow midtones
        "highlights": (25.0, 10.0, -35.0),   # Golden Green highlights
    },
    "custom": {
        "label": "Custom Tonal Sliders",
    },
}


def color_balance(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-color-balance"),
                "No valid image provided.",
                0
            )
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-color-balance')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    # Read configuration parameters
    preset = config.get_property('preset')
    custom_range = config.get_property('tonal-range')
    cyan_red = config.get_property('cyan-red')
    magenta_green = config.get_property('magenta-green')
    yellow_blue = config.get_property('yellow-blue')
    preserve_lum = config.get_property('preserve-luminosity')
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
                GLib.quark_from_string("gimp-color-balance"),
                "No valid target layer found.",
                0
            )
        )

    pdb = Gimp.get_pdb()
    cb_proc = pdb.lookup_procedure('gimp-drawable-color-balance')
    if cb_proc is None:
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-color-balance"),
                "Underlying procedure 'gimp-drawable-color-balance' not found in PDB.",
                0
            )
        )

    Gimp.context_push()
    image.undo_group_start()

    try:
        preset_info = PRESETS.get(preset, PRESETS["teal-orange"])
        label = preset_info.get("label", "Custom")
        layer_name = f"Color Balance ({label})"

        # Create non-destructive duplicate layer
        cb_layer = Gimp.Layer.new_from_drawable(target_layer, image)
        cb_layer.set_name(layer_name)
        cb_layer.set_opacity(max(10.0, min(100.0, float(opacity))))
        cb_layer.set_mode(Gimp.LayerMode.NORMAL)

        parent = target_layer.get_parent()
        pos = image.get_item_position(target_layer)
        image.insert_layer(cb_layer, parent, pos)

        # Helper to apply color balance to a specific transfer mode
        def apply_cb(mode, cr, mg, yb):
            if abs(cr) < 0.001 and abs(mg) < 0.001 and abs(yb) < 0.001:
                return
            c = cb_proc.create_config()
            c.set_property('drawable', cb_layer)
            c.set_property('transfer-mode', mode)
            c.set_property('preserve-lum', bool(preserve_lum))
            c.set_property('cyan-red', float(cr))
            c.set_property('magenta-green', float(mg))
            c.set_property('yellow-blue', float(yb))
            cb_proc.run(c)

        if preset in PRESETS and preset != "custom":
            p = PRESETS[preset]
            apply_cb(Gimp.TransferMode.SHADOWS, *p["shadows"])
            apply_cb(Gimp.TransferMode.MIDTONES, *p["midtones"])
            apply_cb(Gimp.TransferMode.HIGHLIGHTS, *p["highlights"])
        else:  # Custom sliders
            if custom_range == "shadows":
                apply_cb(Gimp.TransferMode.SHADOWS, cyan_red, magenta_green, yellow_blue)
            elif custom_range == "highlights":
                apply_cb(Gimp.TransferMode.HIGHLIGHTS, cyan_red, magenta_green, yellow_blue)
            else:  # "midtones" (default)
                apply_cb(Gimp.TransferMode.MIDTONES, cyan_red, magenta_green, yellow_blue)

        # Attach reveal-all layer mask if requested
        if add_mask:
            mask = cb_layer.create_mask(Gimp.AddMaskType.WHITE)
            cb_layer.add_mask(mask)

        # Set newly created layer as active
        image.set_selected_layers([cb_layer])

        Gimp.displays_flush()
        image.undo_group_end()
        Gimp.context_pop()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    except Exception as exc:
        image.undo_group_end()
        Gimp.context_pop()
        msg = "Color Balance layer creation failed: " + str(exc)
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-color-balance"),
                msg,
                0
            )
        )


class ColorBalancePlugin(Gimp.PlugIn):
    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-color-balance"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            color_balance,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        procedure.set_menu_label("Color _Balance...")
        procedure.set_documentation(
            "Changes overall color cast with non-destructive 3-way tonal grading",
            "Creates a dedicated non-destructive Color Balance adjustment layer duplicating the target drawable. "
            "Applies 3-way color grading across Shadows, Midtones, and Highlights with Cyan-Red, Magenta-Green, "
            "and Yellow-Blue controls, cinematic presets, and luminosity preservation inspired by Adobe Photoshop.",
            name
        )
        procedure.set_attribution("Antigravity Ralph / PhotoGIMP", "PhotoGIMP", "2026")

        procedure.add_menu_path("<Image>/Colors")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        # Preset Choice Argument
        preset_choice = Gimp.Choice.new()
        preset_choice.add(
            "teal-orange",
            0,
            "Teal & Orange (Cinematic Look)",
            "Teal shadows with warm golden amber midtones and highlights"
        )
        preset_choice.add(
            "warm-sunset",
            1,
            "Warm Sunset (Golden Glow)",
            "Rich warm golden tones across midtones and highlights"
        )
        preset_choice.add(
            "cool-night",
            2,
            "Cool Moonlight (Nocturnal Blue)",
            "Deep blue and cyan shadows with cool highlights"
        )
        preset_choice.add(
            "cross-process",
            3,
            "Vintage Cross-Process",
            "Creative retro split-toning with green shadows and magenta midtones"
        )
        preset_choice.add(
            "custom",
            4,
            "Custom Tonal Sliders",
            "Manually specify Cyan-Red, Magenta-Green, and Yellow-Blue sliders"
        )

        procedure.add_choice_argument(
            "preset",
            "_Preset",
            "Color grading preset style",
            preset_choice,
            "teal-orange",
            GObject.ParamFlags.READWRITE
        )

        # Tonal Range Choice (for custom mode)
        range_choice = Gimp.Choice.new()
        range_choice.add(
            "midtones",
            0,
            "Midtones",
            "Adjust color balance in midtones"
        )
        range_choice.add(
            "shadows",
            1,
            "Shadows",
            "Adjust color balance in shadows"
        )
        range_choice.add(
            "highlights",
            2,
            "Highlights",
            "Adjust color balance in highlights"
        )

        procedure.add_choice_argument(
            "tonal-range",
            "Tonal _Range",
            "Tonal range to apply custom color balance sliders",
            range_choice,
            "midtones",
            GObject.ParamFlags.READWRITE
        )

        # Cyan-Red Slider (-100 to +100)
        procedure.add_double_argument(
            "cyan-red",
            "_Cyan - Red",
            "Color balance shift between Cyan (-) and Red (+)",
            -100.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # Magenta-Green Slider (-100 to +100)
        procedure.add_double_argument(
            "magenta-green",
            "_Magenta - Green",
            "Color balance shift between Magenta (-) and Green (+)",
            -100.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # Yellow-Blue Slider (-100 to +100)
        procedure.add_double_argument(
            "yellow-blue",
            "_Yellow - Blue",
            "Color balance shift between Yellow (-) and Blue (+)",
            -100.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # Preserve Luminosity Toggle
        procedure.add_boolean_argument(
            "preserve-luminosity",
            "_Preserve Luminosity",
            "Preserve original brightness while shifting colors (Photoshop default)",
            True,
            GObject.ParamFlags.READWRITE
        )

        # Layer Opacity Slider (10% to 100%, default 100%)
        procedure.add_double_argument(
            "opacity",
            "Layer _Opacity",
            "Overall opacity of the Color Balance adjustment layer (10% to 100%)",
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


Gimp.main(ColorBalancePlugin.__gtype__, sys.argv)
