#!/usr/bin/env python3
"""
PhotoGIMP Non-Destructive Dodge & Burn Layer Plugin for GIMP 3.x

Creates a 50% neutral gray (#808080) overlay layer set to Soft Light or
Overlay blend mode for professional non-destructive dodging and burning.

In Photoshop and high-end digital retouching, painting directly on pixels is
destructive. Instead, retouchers create a neutral gray layer set to Soft Light
or Overlay:
  - #808080 is the identity color (0.000000 pixel difference) in Soft Light
    and Overlay blending modes, rendering it completely invisible initially.
  - Painting with White (#ffffff) or light tones dodges (brightens highlights/tones).
  - Painting with Black (#000000) or dark tones burns (darkens shadows/tones).
  - Painting with #808080 or using the Eraser restores original pixel values.

This plugin automates the setup in one click and prepares the active brush colors.
"""

import sys
import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib


# Exact 50% neutral gray for sRGB / GEGL perceptual-to-linear identity blending
_NEUTRAL_GRAY_HEX = "#808080"
_DODGE_WHITE_HEX = "#ffffff"
_BURN_BLACK_HEX = "#000000"


def dodge_burn_layer(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-dodge-burn-layer"),
                "No valid image provided.",
                0
            )
        )

    # Interactive dialog handling
    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-dodge-burn-layer')
        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    mode_choice = config.get_property('mode')
    layer_name = config.get_property('name')
    opacity = config.get_property('opacity')

    if not layer_name:
        layer_name = "Dodge & Burn (Neutral Gray)"

    # Map choice string to Gimp.LayerMode
    if mode_choice == "overlay":
        layer_mode = Gimp.LayerMode.OVERLAY
    else:
        layer_mode = Gimp.LayerMode.SOFTLIGHT

    Gimp.context_push()
    image.undo_group_start()

    try:
        width = image.get_width()
        height = image.get_height()

        # Create new layer with RGB type and requested mode/opacity
        new_layer = Gimp.Layer.new(
            image,
            layer_name,
            width,
            height,
            Gimp.ImageType.RGB_IMAGE,
            float(opacity),
            layer_mode
        )

        # Insert layer above active drawable if available, otherwise at root position 0
        parent = None
        pos = 0
        if len(drawables) > 0:
            parent = drawables[0].get_parent()
            pos = image.get_item_position(drawables[0])

        image.insert_layer(new_layer, parent, pos)

        # Fill with exact 50% neutral gray (#808080)
        Gimp.context_set_foreground(Gegl.Color.new(_NEUTRAL_GRAY_HEX))
        new_layer.edit_fill(Gimp.FillType.FOREGROUND)

        # Set the newly created layer as the active selected layer
        image.set_selected_layers([new_layer])

        Gimp.displays_flush()

    except Exception as exc:
        image.undo_group_end()
        Gimp.context_pop()
        msg = "Dodge & Burn Layer creation failed: " + str(exc)
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-dodge-burn-layer"),
                msg,
                0
            )
        )

    image.undo_group_end()
    Gimp.context_pop()

    # Convenience: configure active brush colors for immediate dodging and burning:
    # Foreground = Pure White (dodge / brighten), Background = Pure Black (burn / darken)
    Gimp.context_set_foreground(Gegl.Color.new(_DODGE_WHITE_HEX))
    Gimp.context_set_background(Gegl.Color.new(_BURN_BLACK_HEX))

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


class DodgeBurnLayer(Gimp.PlugIn):
    ## GimpPlugIn virtual methods ##
    def do_set_i18n(self, procname):
        return True, 'gimp30-python', None

    def do_query_procedures(self):
        return ['python-fu-dodge-burn-layer']

    def do_create_procedure(self, name):
        Gegl.init(None)

        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            dodge_burn_layer,
            None
        )
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES |
            Gimp.ProcedureSensitivityMask.NO_DRAWABLES
        )
        procedure.set_documentation(
            "Create Non-Destructive Dodge & Burn Layer",
            (
                "Creates a 50% neutral gray (#808080) layer set to Soft Light or "
                "Overlay blend mode. Paint with White (#ffffff) to dodge (brighten) "
                "or Black (#000000) to burn (darken) without altering original pixels."
            ),
            name
        )
        procedure.set_menu_label("New Dodge & Burn Layer...")
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP Project", "2026")
        procedure.add_menu_path("<Image>/Layer")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        # Blend mode selection: Soft Light (Subtle) or Overlay (High Contrast)
        mode_choice = Gimp.Choice.new()
        mode_choice.add(
            "softlight",
            0,
            "Soft Light (Subtle - Recommended for Portraits)",
            "Gentle, smooth tonal adjustments suitable for skin and portraits"
        )
        mode_choice.add(
            "overlay",
            1,
            "Overlay (High Contrast - Recommended for Landscapes)",
            "Pronounced contrast and dynamic tonal adjustments"
        )
        procedure.add_choice_argument(
            "mode",
            "Blend _Mode",
            "Blending mode for the dodge and burn overlay layer",
            mode_choice,
            "softlight",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_string_argument(
            "name",
            "Layer _Name",
            "Name for the new dodge and burn layer",
            "Dodge & Burn (Neutral Gray)",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "opacity",
            "_Opacity",
            "Initial opacity percentage for the dodge and burn layer",
            1.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        return procedure


if __name__ == "__main__":
    Gimp.main(DodgeBurnLayer.__gtype__, sys.argv)
