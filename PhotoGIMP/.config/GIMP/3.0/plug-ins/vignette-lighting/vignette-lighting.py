#!/usr/bin/env python3
"""
PhotoGIMP Non-Destructive Vignette & Lens Lighting Plugin for GIMP 3.x

Creates a non-destructive radial vignette adjustment layer to subtly darken or brighten
image edges to draw focus to the subject in the center.

Photoshop Equivalence:
- topics.txt lines 106 & 661: Adjust image lighting with Light / Adjust lighting in images.
- photoshop_docs.md Section 271: Darken the edges of your image to bring focus to its center.

Key Advantages over stock GIMP destructiveness:
1. 100% Non-Destructive: Created as an isolated overlay layer above the active image.
2. Mathematically Identical Center: Uses 50% neutral gray (#808080) for 0.000000 center deviation in Soft Light & Overlay modes.
3. Live Opacity & Blend Tuning: Adjust layer opacity, blend mode, or toggle visibility at any time.
4. Selective Masking: Optionally attaches a reveal-all layer mask for selective brushing over subjects.
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


_NEUTRAL_GRAY_HEX = "#808080"
_DARK_VIGNETTE_HEX = "#000000"
_LIGHT_VIGNETTE_HEX = "#ffffff"


def vignette_lighting(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-vignette-lighting"),
                "No valid image provided.",
                0
            )
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-vignette-lighting')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    tone = config.get_property('tone')
    mode_str = config.get_property('mode')
    radius = config.get_property('radius')
    softness = config.get_property('softness')
    opacity = config.get_property('opacity')
    add_mask = config.get_property('add-mask')

    # Resolve layer blend mode and colors
    if mode_str == "overlay":
        layer_mode = Gimp.LayerMode.OVERLAY
        base_color = Gegl.Color.new(_NEUTRAL_GRAY_HEX)
    elif mode_str == "multiply":
        layer_mode = Gimp.LayerMode.MULTIPLY
        base_color = Gegl.Color.new("#ffffff")
    else:
        layer_mode = Gimp.LayerMode.SOFTLIGHT
        base_color = Gegl.Color.new(_NEUTRAL_GRAY_HEX)

    if tone == "light":
        vig_color = Gegl.Color.new(_LIGHT_VIGNETTE_HEX)
        layer_name = "Vignette (Highlight)"
    else:
        vig_color = Gegl.Color.new(_DARK_VIGNETTE_HEX)
        layer_name = "Vignette (Shadow)"

    Gimp.context_push()
    image.undo_group_start()

    try:
        width = image.get_width()
        height = image.get_height()

        vig_layer = Gimp.Layer.new(
            image,
            layer_name,
            width,
            height,
            Gimp.ImageType.RGBA_IMAGE,
            float(opacity),
            layer_mode
        )

        # Place above active drawable
        parent = None
        pos = 0
        selected = image.get_selected_drawables()
        if len(selected) > 0:
            parent = selected[0].get_parent()
            pos = image.get_item_position(selected[0])
        else:
            layers = image.get_layers()
            if len(layers) > 0:
                pos = 0

        image.insert_layer(vig_layer, parent, pos)

        # Fill with neutral identity base
        Gimp.context_set_foreground(base_color)
        vig_layer.edit_fill(Gimp.FillType.FOREGROUND)

        # Apply GEGL vignette radial gradient filter
        vignette_filter = Gimp.DrawableFilter.new(vig_layer, "gegl:vignette", "")
        f_config = vignette_filter.get_config()
        f_config.set_property("radius", float(radius))
        f_config.set_property("softness", float(softness))
        f_config.set_property("color", vig_color)
        f_config.set_property("shape", "circle")  # Circle / proportional ellipse
        vig_layer.merge_filter(vignette_filter)

        # Add optional reveal-all layer mask
        if add_mask:
            mask = vig_layer.create_mask(Gimp.AddMaskType.WHITE)
            vig_layer.add_mask(mask)

        # Select the new vignette layer as active
        image.set_selected_layers([vig_layer])
        vig_layer.set_visible(True)

        Gimp.displays_flush()
    finally:
        image.undo_group_end()
        Gimp.context_pop()

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


class VignetteLighting(Gimp.PlugIn):
    ## GimpPlugIn virtual methods ##
    def do_set_i18n(self, procname):
        return True, 'gimp30-python', None

    def do_query_procedures(self):
        return ['python-fu-vignette-lighting']

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            vignette_lighting,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_documentation(
            "Create a non-destructive radial vignette or lens lighting layer",
            "Creates a non-destructive overlay layer with radial vignette falloff, "
            "preserving 100% of center image details while subtly darkening or brightening edges.",
            name
        )
        procedure.set_menu_label("Vignette Lighting...")
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP Project", "2026")
        procedure.add_menu_path("<Image>/Filters/Light and Shadow")
        procedure.add_menu_path("<Image>/Layer")

        tone_choice = Gimp.Choice.new()
        tone_choice.add(
            "dark",
            0,
            "Dark Vignette (Shadow Falloff - Classic Focus on Subject)",
            "Darkens outer edges and corners to draw viewer attention to the bright center"
        )
        tone_choice.add(
            "light",
            1,
            "Light Vignette (Highlight / High-Key Focus)",
            "Softly brightens edges for high-key portraits and ethereal aesthetic"
        )
        procedure.add_choice_argument(
            "tone",
            "Vignette _Tone",
            "Vignette tone falloff style",
            tone_choice,
            "dark",
            GObject.ParamFlags.READWRITE
        )

        mode_choice = Gimp.Choice.new()
        mode_choice.add(
            "softlight",
            0,
            "Soft Light (Subtle / Natural - Recommended)",
            "Smooth, natural edge contrast without crushing deep shadow details"
        )
        mode_choice.add(
            "overlay",
            1,
            "Overlay (Dramatic / High Contrast)",
            "Punchy, pronounced edge darkening with vivid dynamic contrast"
        )
        mode_choice.add(
            "multiply",
            2,
            "Multiply (Deep Shadows)",
            "Direct multiplicative shadow darkening across the outer frame"
        )
        procedure.add_choice_argument(
            "mode",
            "Blend _Mode",
            "Layer blend mode for the vignette effect",
            mode_choice,
            "softlight",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "radius",
            "_Radius",
            "Coverage radius from center (proportional)",
            0.2,
            3.0,
            1.2,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "softness",
            "_Softness (Feather)",
            "Gradual falloff transition smoothness (0.1 sharp to 1.0 ultra soft)",
            0.1,
            1.0,
            0.8,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "opacity",
            "_Opacity",
            "Initial layer opacity percentage",
            10.0,
            100.0,
            80.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_boolean_argument(
            "add-mask",
            "Add Reveal-All Layer _Mask",
            "Attach a white layer mask for selective brushing over subjects",
            True,
            GObject.ParamFlags.READWRITE
        )

        return procedure


if __name__ == "__main__":
    Gimp.main(VignetteLighting.__gtype__, sys.argv)
