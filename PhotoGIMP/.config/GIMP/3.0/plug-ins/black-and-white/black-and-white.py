#!/usr/bin/env python3
"""
PhotoGIMP Professional Black & White Conversion & Tonal Toning Plugin for GIMP 3.x

Creates a non-destructive monochrome adjustment layer with custom color channel
luminance weighting (Red, Green, Blue) and photographic toning presets (Sepia tone)
inspired by Adobe Photoshop's Black & White adjustment command.

Photoshop Equivalence:
- Topics.txt line 341: Color effects and techniques - Convert a color image to black and white.
- Topics.txt line 668: Convert images to black and white.
- Topics.txt line 667: Desaturate image backgrounds to black and white.

Key Advantages over stock destructive grayscale:
1. 100% Non-Destructive: Duplicates the source drawable into an isolated monochrome layer.
2. Channel Luminance Control: Powered by GEGL gegl:mono-mixer for fine-tuned channel contribution.
3. Photographic Presets: Neutral, High Contrast, Infrared, Landscape, Portrait, and Custom.
4. Archival Photographic Toning: Integrated warm Sepia toning powered by GEGL gegl:sepia.
5. Selective Masking: Reveal-all layer mask attached for selective subject color pops.
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


PRESET_WEIGHTS = {
    "neutral": (0.333, 0.333, 0.333),
    "high-contrast": (0.60, 0.30, 0.10),
    "infrared": (0.80, 0.20, -0.10),
    "landscape": (0.20, 0.60, 0.20),
    "portrait": (0.45, 0.45, 0.10),
}


def black_and_white(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-black-and-white"),
                "No valid image provided.",
                0
            )
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-black-and-white')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    # Read configuration parameters
    preset = config.get_property('preset')
    custom_red = config.get_property('custom-red')
    custom_green = config.get_property('custom-green')
    custom_blue = config.get_property('custom-blue')
    preserve_lum = config.get_property('preserve-luminosity')
    tone = config.get_property('tone')
    opacity = config.get_property('opacity')
    add_mask = config.get_property('add-mask')

    # Resolve channel weights
    if preset in PRESET_WEIGHTS:
        w_red, w_green, w_blue = PRESET_WEIGHTS[preset]
    else:  # "custom"
        w_red = float(custom_red)
        w_green = float(custom_green)
        w_blue = float(custom_blue)

    # Resolve target layer (must be a Gimp.Layer, not a Gimp.LayerMask)
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
                GLib.quark_from_string("gimp-black-and-white"),
                "No target drawable found to apply black and white conversion.",
                0
            )
        )

    Gimp.context_push()
    image.undo_group_start()

    try:
        # Determine layer title
        preset_label = preset.replace("-", " ").title()
        if tone == "sepia":
            layer_title = f"Black & White ({preset_label} - Sepia)"
        else:
            layer_title = f"Black & White ({preset_label})"

        # Create non-destructive monochrome layer duplicating target
        mono_layer = Gimp.Layer.new_from_drawable(target_drawable, image)
        mono_layer.set_name(layer_title)
        mono_layer.set_opacity(float(opacity))
        mono_layer.set_mode(Gimp.LayerMode.NORMAL)

        # Insert immediately above target drawable
        parent = target_drawable.get_parent()
        pos = image.get_item_position(target_drawable)
        image.insert_layer(mono_layer, parent, pos)

        # Apply GEGL mono-mixer filter for channel weighting
        mixer_filter = Gimp.DrawableFilter.new(mono_layer, "gegl:mono-mixer", "")
        f_config = mixer_filter.get_config()
        f_config.set_property("red", float(w_red))
        f_config.set_property("green", float(w_green))
        f_config.set_property("blue", float(w_blue))
        f_config.set_property("preserve-luminosity", bool(preserve_lum))
        mono_layer.merge_filter(mixer_filter)

        # Apply optional photographic toning
        if tone == "sepia":
            sepia_filter = Gimp.DrawableFilter.new(mono_layer, "gegl:sepia", "")
            s_config = sepia_filter.get_config()
            s_config.set_property("scale", 0.75)
            s_config.set_property("srgb", True)
            mono_layer.merge_filter(sepia_filter)

        # Attach optional reveal-all layer mask
        if add_mask:
            mask = mono_layer.create_mask(Gimp.AddMaskType.WHITE)
            mono_layer.add_mask(mask)

        # Select the monochrome layer as active
        image.set_selected_layers([mono_layer])
        mono_layer.set_visible(True)

        Gimp.displays_flush()
    finally:
        image.undo_group_end()
        Gimp.context_pop()

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


class BlackAndWhite(Gimp.PlugIn):
    ## GimpPlugIn virtual methods ##
    def do_set_i18n(self, procname):
        return True, 'gimp30-python', None

    def do_query_procedures(self):
        return ['python-fu-black-and-white']

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            black_and_white,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_documentation(
            "Convert color image to black and white with channel weighting and toning",
            "Creates a non-destructive monochrome layer with custom Red/Green/Blue channel "
            "luminance contribution and optional warm Sepia photographic toning.",
            name
        )
        procedure.set_menu_label("Black and White...")
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP Project", "2026")
        procedure.add_menu_path("<Image>/Colors")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        # Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add(
            "neutral",
            0,
            "Neutral (Balanced Monochrome Luminance)",
            "Standard balanced black and white conversion"
        )
        preset_choice.add(
            "high-contrast",
            1,
            "High Contrast (Red Filter - Dramatic Skies)",
            "Simulates red camera filter: deepens blue skies and brightens warm tones"
        )
        preset_choice.add(
            "infrared",
            2,
            "Infrared (Glowing Foliage & Dark Skies)",
            "Simulates infrared photography with bright whites and moody darks"
        )
        preset_choice.add(
            "landscape",
            3,
            "Landscape (Green Filter - Lush Foliage)",
            "Simulates green camera filter: separates foliage tones in landscapes"
        )
        preset_choice.add(
            "portrait",
            4,
            "Portrait (Yellow / Orange Filter - Smooth Skin)",
            "Softens blemishes and provides flattering skin luminance"
        )
        preset_choice.add(
            "custom",
            5,
            "Custom Channel Weights",
            "Manually specify Red, Green, and Blue channel weights"
        )
        procedure.add_choice_argument(
            "preset",
            "_Monochrome Preset",
            "Black and white conversion style preset",
            preset_choice,
            "neutral",
            GObject.ParamFlags.READWRITE
        )

        # Custom Channel Weights (Sliders)
        procedure.add_double_argument(
            "custom-red",
            "Custom _Red Weight",
            "Red channel contribution to monochrome luminance (custom mode)",
            -1.0,
            2.0,
            0.333,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "custom-green",
            "Custom _Green Weight",
            "Green channel contribution to monochrome luminance (custom mode)",
            -1.0,
            2.0,
            0.333,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "custom-blue",
            "Custom _Blue Weight",
            "Blue channel contribution to monochrome luminance (custom mode)",
            -1.0,
            2.0,
            0.333,
            GObject.ParamFlags.READWRITE
        )

        # Preserve Luminosity Toggle
        procedure.add_boolean_argument(
            "preserve-luminosity",
            "_Preserve Luminosity",
            "Normalize channel weights to maintain overall perceived brightness",
            False,
            GObject.ParamFlags.READWRITE
        )

        # Photographic Toning Choice
        tone_choice = Gimp.Choice.new()
        tone_choice.add(
            "none",
            0,
            "None (Pure Neutral Monochrome)",
            "Pure grayscale monochrome without color tinting"
        )
        tone_choice.add(
            "sepia",
            1,
            "Sepia Tone (Warm Archival Photographic Tint)",
            "Applies classic warm sepia photographic toning"
        )
        procedure.add_choice_argument(
            "tone",
            "Photographic _Toning",
            "Color tinting style applied to monochrome output",
            tone_choice,
            "none",
            GObject.ParamFlags.READWRITE
        )

        # Opacity Slider
        procedure.add_double_argument(
            "opacity",
            "Layer _Opacity",
            "Overall opacity of the monochrome layer (10.0 to 100.0%)",
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


Gimp.main(BlackAndWhite.__gtype__, sys.argv)
