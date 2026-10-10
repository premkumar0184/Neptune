#!/usr/bin/env python3
"""
PhotoGIMP Photo Filter Optical Warming & Cooling Helper Plugin for GIMP 3.x

Creates a non-destructive optical lens filter adjustment layer simulating Kodak Wratten
and colored camera glass filters (Warming 85/81, Cooling 80/82, Deep Red, Orange, Amber,
Emerald, Cyan, Deep Blue, etc.) with configurable density, luminosity preservation,
and an attached reveal-all layer mask inspired by Adobe Photoshop's Photo Filter command.

Photoshop Equivalence:
- Topics.txt line 93/94: Color adjustment and fill layers - Work with adjustment layers.
- photoshop_docs.md line 3074 & 3218: Photo Filter: Applies warming/cooling lens effects.
- Topics.txt line 328/332: Adjust color and tone / Color corrections.

Key Advantages over destructive color adjustments:
1. 100% Non-Destructive: Created as an isolated adjustment layer above the target layer.
2. Authentic Optical Presets: Kodak Wratten 85 (warming), 81 (warm gold), 80 (cooling blue),
   82 (light cooling), Sepia, Amber, Deep Red, Deep Blue, Emerald, etc.
3. Density Control: Adjustable from 1% to 100% (default 25%, matching Photoshop).
4. Preserve Luminosity: When enabled, uses LCH Color mode to maintain perceptual lightness;
   when disabled, uses Soft Light mode to simulate physical filter light absorption.
5. Reveal-All Layer Mask: Automatically attached for selective brushing on subjects/faces.
6. Target Layer Preservation: Source layer pixels remain 100% untouched.
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
    # Authentic optical lens filter RGB values (sRGB linear/perceptual)
    "warming-85": (0.925, 0.541, 0.000, "Warming Filter (85)"),
    "warming-81": (0.933, 0.725, 0.180, "Warming Filter (81)"),
    "cooling-80": (0.000, 0.239, 0.647, "Cooling Filter (80)"),
    "cooling-82": (0.000, 0.451, 0.745, "Cooling Filter (82)"),
    "red": (0.918, 0.114, 0.141, "Red Filter"),
    "orange": (0.945, 0.353, 0.141, "Orange Filter"),
    "yellow": (1.000, 0.949, 0.000, "Yellow Filter"),
    "green": (0.000, 0.651, 0.318, "Green Filter"),
    "cyan": (0.000, 0.682, 0.937, "Cyan Filter"),
    "blue": (0.180, 0.192, 0.573, "Blue Filter"),
    "magenta": (0.925, 0.000, 0.549, "Magenta Filter"),
    "sepia": (0.639, 0.384, 0.035, "Sepia Tone Filter"),
    "deep-red": (0.745, 0.118, 0.176, "Deep Red Filter"),
    "deep-blue": (0.106, 0.078, 0.392, "Deep Blue Filter"),
    "deep-emerald": (0.000, 0.408, 0.216, "Deep Emerald Filter"),
    "amber": (1.000, 0.780, 0.000, "Amber Filter"),
}


def photo_filter(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-photo-filter"),
                "No valid image provided.",
                0
            )
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-photo-filter')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    # Read configuration parameters
    preset = config.get_property('preset')
    density = config.get_property('density')
    preserve_lum = config.get_property('preserve-luminosity')
    add_mask = config.get_property('add-mask')
    custom_red = config.get_property('custom-red')
    custom_green = config.get_property('custom-green')
    custom_blue = config.get_property('custom-blue')

    # Resolve optical filter color and display name
    if preset in PRESETS:
        r, g, b, label = PRESETS[preset]
    else:  # "custom"
        r = max(0.0, min(1.0, float(custom_red)))
        g = max(0.0, min(1.0, float(custom_green)))
        b = max(0.0, min(1.0, float(custom_blue)))
        label = "Custom Color"

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

    # Determine blend mode based on Preserve Luminosity
    # When preserving luminosity, LCH Color preserves perceived lightness and alters chroma/hue.
    # When unchecked, Soft Light simulates real optical filter light absorption.
    layer_mode = Gimp.LayerMode.LCH_COLOR if preserve_lum else Gimp.LayerMode.SOFTLIGHT

    Gimp.context_push()
    image.undo_group_start()

    try:
        width = image.get_width()
        height = image.get_height()
        density_val = max(1.0, min(100.0, float(density)))
        layer_name = f"Photo Filter ({label}, {int(round(density_val))}%)"

        # Create the dedicated non-destructive filter layer
        filter_layer = Gimp.Layer.new(
            image,
            layer_name,
            width,
            height,
            Gimp.ImageType.RGBA_IMAGE,
            density_val,
            layer_mode
        )

        parent = target_layer.get_parent() if target_layer else None
        pos = image.get_item_position(target_layer) if target_layer else 0

        # Insert above target layer
        image.insert_layer(filter_layer, parent, pos)

        # Fill filter layer with the optical lens color
        gegl_color = Gegl.Color.new(f"rgb({r:.4f}, {g:.4f}, {b:.4f})")
        Gimp.context_set_foreground(gegl_color)
        filter_layer.edit_fill(Gimp.FillType.FOREGROUND)

        # Attach reveal-all layer mask for selective brush painting
        if add_mask:
            mask = filter_layer.create_mask(Gimp.AddMaskType.WHITE)
            filter_layer.add_mask(mask)

        # Set newly created filter layer as active selection
        image.set_selected_layers([filter_layer])

        Gimp.displays_flush()
        image.undo_group_end()
        Gimp.context_pop()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    except Exception as exc:
        image.undo_group_end()
        Gimp.context_pop()
        msg = "Photo Filter creation failed: " + str(exc)
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-photo-filter"),
                msg,
                0
            )
        )


class PhotoFilter(Gimp.PlugIn):
    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-photo-filter"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            photo_filter,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        procedure.set_menu_label("Photo _Filter...")
        procedure.set_documentation(
            "Applies non-destructive warming, cooling, and colored optical lens filter effects",
            "Creates a dedicated non-destructive photo filter layer simulating optical camera lens filters "
            "(Kodak Wratten 85/81 warming, 80/82 cooling, color contrast filters) with density and luminosity "
            "controls inspired by Adobe Photoshop.",
            name
        )
        procedure.set_attribution("Antigravity Ralph / PhotoGIMP", "PhotoGIMP", "2026")

        procedure.add_menu_path("<Image>/Colors")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        # Optical Filter Presets Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add(
            "warming-85",
            0,
            "Warming Filter (85) - Kodak Amber",
            "Standard warming filter: adds rich amber warmth to portraits and landscapes"
        )
        preset_choice.add(
            "warming-81",
            1,
            "Warming Filter (81) - Warm Gold",
            "Light warming filter: adds subtle golden glow to cool scenes"
        )
        preset_choice.add(
            "cooling-80",
            2,
            "Cooling Filter (80) - Deep Blue",
            "Strong cooling filter: cools warm tungsten casts and adds twilight atmosphere"
        )
        preset_choice.add(
            "cooling-82",
            3,
            "Cooling Filter (82) - Light Blue",
            "Subtle cooling filter: gently cools overly warm sunlight"
        )
        preset_choice.add(
            "red",
            4,
            "Red Filter",
            "High contrast red filter for dramatic mood and warmth"
        )
        preset_choice.add(
            "orange",
            5,
            "Orange Filter",
            "Vibrant sunset orange optical tint"
        )
        preset_choice.add(
            "yellow",
            6,
            "Yellow Filter",
            "Brightening yellow daylight optical tint"
        )
        preset_choice.add(
            "green",
            7,
            "Green Filter",
            "Foliage and nature enhancement green filter"
        )
        preset_choice.add(
            "cyan",
            8,
            "Cyan Filter",
            "Cool ocean and sky cyan filter"
        )
        preset_choice.add(
            "blue",
            9,
            "Blue Filter",
            "Deep royal blue atmospheric filter"
        )
        preset_choice.add(
            "magenta",
            10,
            "Magenta Filter",
            "Vibrant theatrical magenta filter"
        )
        preset_choice.add(
            "sepia",
            11,
            "Sepia Tone Filter",
            "Classic warm antique photographic sepia tint"
        )
        preset_choice.add(
            "deep-red",
            12,
            "Deep Red Filter",
            "Dramatic deep ruby red filter"
        )
        preset_choice.add(
            "deep-blue",
            13,
            "Deep Blue Filter",
            "Moody nocturnal deep blue filter"
        )
        preset_choice.add(
            "deep-emerald",
            14,
            "Deep Emerald Filter",
            "Rich deep forest emerald filter"
        )
        preset_choice.add(
            "amber",
            15,
            "Amber Filter",
            "Golden amber photographic warming filter"
        )
        preset_choice.add(
            "custom",
            16,
            "Custom Color",
            "Manually specify custom RGB filter color"
        )

        procedure.add_choice_argument(
            "preset",
            "_Filter Preset",
            "Optical lens filter preset or custom color",
            preset_choice,
            "warming-85",
            GObject.ParamFlags.READWRITE
        )

        # Density Slider (1.0% to 100.0%, default 25.0%)
        procedure.add_double_argument(
            "density",
            "_Density (%)",
            "Amount of optical filter color applied to the image (1% to 100%)",
            1.0,
            100.0,
            25.0,
            GObject.ParamFlags.READWRITE
        )

        # Preserve Luminosity Toggle
        procedure.add_boolean_argument(
            "preserve-luminosity",
            "_Preserve Luminosity",
            "Preserve original image lightness while tinting color (Photoshop default)",
            True,
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

        # Custom Color Sliders
        procedure.add_double_argument(
            "custom-red",
            "Custom _Red",
            "Custom filter red channel intensity (0.0 to 1.0)",
            0.0,
            1.0,
            0.925,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "custom-green",
            "Custom _Green",
            "Custom filter green channel intensity (0.0 to 1.0)",
            0.0,
            1.0,
            0.541,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "custom-blue",
            "Custom _Blue",
            "Custom filter blue channel intensity (0.0 to 1.0)",
            0.0,
            1.0,
            0.000,
            GObject.ParamFlags.READWRITE
        )

        return procedure


Gimp.main(PhotoFilter.__gtype__, sys.argv)
