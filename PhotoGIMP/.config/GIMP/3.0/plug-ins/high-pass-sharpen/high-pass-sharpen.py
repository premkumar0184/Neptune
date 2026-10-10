#!/usr/bin/env python3
"""
PhotoGIMP High Pass Sharpening Helper Plugin for GIMP 3.x

Implements the standard Photoshop high-pass frequency sharpening workflow:
  1. Duplicates the target layer.
  2. Applies the GEGL high-pass filter with a configurable radius (std-dev).
  3. Sets the blend mode to Soft Light (natural) or Overlay (crisp).
  4. Optionally attaches a reveal-all (White) layer mask for selective masking.

In Photoshop and professional photo retouching, High Pass sharpening is preferred
over unsharp mask because it isolates high-frequency edges and micro-contrast
without introducing noisy halos in flat regions like skies or skin.
"""

import sys
import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib


def high_pass_sharpen(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-high-pass-sharpen"),
                "No valid image provided.",
                0
            )
        )

    target_drawable = None
    if len(drawables) > 0:
        target_drawable = drawables[0]
    else:
        selected = image.get_selected_drawables()
        if len(selected) > 0:
            target_drawable = selected[0]
        else:
            layers = image.get_layers()
            if len(layers) > 0:
                target_drawable = layers[0]

    if target_drawable is None:
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-high-pass-sharpen"),
                "No active layer or drawable found to sharpen.",
                0
            )
        )

    # Interactive dialog handling
    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-high-pass-sharpen')
        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    radius = config.get_property('radius')
    mode_choice = config.get_property('mode')
    opacity = config.get_property('opacity')
    add_mask = config.get_property('add-mask')

    if mode_choice == "overlay":
        layer_mode = Gimp.LayerMode.OVERLAY
    else:
        layer_mode = Gimp.LayerMode.SOFTLIGHT

    Gimp.context_push()
    image.undo_group_start()

    try:
        base_name = target_drawable.get_name()
        parent = target_drawable.get_parent()
        pos = image.get_item_position(target_drawable)

        # 1. Duplicate target layer
        sharpen_layer = target_drawable.copy()
        sharpen_layer.set_name(f"High Pass Sharpen ({base_name})")
        image.insert_layer(sharpen_layer, parent, pos)

        # 2. Apply GEGL high-pass filter
        hp_filter = Gimp.DrawableFilter.new(sharpen_layer, "gegl:high-pass", "")
        hp_config = hp_filter.get_config()
        hp_config.set_property("std-dev", float(radius))
        sharpen_layer.merge_filter(hp_filter)

        # 3. Set blending mode and opacity
        sharpen_layer.set_mode(layer_mode)
        sharpen_layer.set_opacity(float(opacity))
        sharpen_layer.set_visible(True)

        # 4. Attach reveal-all layer mask if requested
        if add_mask:
            mask = sharpen_layer.create_mask(Gimp.AddMaskType.WHITE)
            sharpen_layer.add_mask(mask)

        # 5. Set as active layer
        image.set_selected_layers([sharpen_layer])

        Gimp.displays_flush()

    except Exception as exc:
        image.undo_group_end()
        Gimp.context_pop()
        msg = "High Pass Sharpen failed: " + str(exc)
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-high-pass-sharpen"),
                msg,
                0
            )
        )

    image.undo_group_end()
    Gimp.context_pop()

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


class HighPassSharpen(Gimp.PlugIn):
    ## GimpPlugIn virtual methods ##
    def do_set_i18n(self, procname):
        return True, 'gimp30-python', None

    def do_query_procedures(self):
        return ['python-fu-high-pass-sharpen']

    def do_create_procedure(self, name):
        Gegl.init(None)

        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            high_pass_sharpen,
            None
        )
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES |
            Gimp.ProcedureSensitivityMask.NO_DRAWABLES
        )
        procedure.set_documentation(
            "High Pass Sharpening (Edge-Preserving Frequency Sharpen)",
            (
                "Duplicates the active layer, applies GEGL high-pass filter to extract "
                "edge micro-contrast, and blends it using Soft Light or Overlay mode "
                "with an optional layer mask for non-destructive frequency sharpening."
            ),
            name
        )
        procedure.set_menu_label("High Pass Sharpen...")
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP Project", "2026")
        procedure.add_menu_path("<Image>/Filters/Enhance")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        procedure.add_double_argument(
            "radius",
            "_Filter Radius",
            "High Pass filter radius (std-dev) in pixels",
            0.5,
            50.0,
            2.5,
            GObject.ParamFlags.READWRITE
        )

        mode_choice = Gimp.Choice.new()
        mode_choice.add(
            "softlight",
            0,
            "Soft Light (Subtle / Natural - Default)",
            "Gentle sharpening ideal for portraits and natural textures"
        )
        mode_choice.add(
            "overlay",
            1,
            "Overlay (Crisp / Pronounced)",
            "Strong, crisp edge contrast ideal for architecture and landscapes"
        )
        procedure.add_choice_argument(
            "mode",
            "Blend _Mode",
            "Layer blend mode for sharpening composite",
            mode_choice,
            "softlight",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "opacity",
            "_Opacity",
            "Sharpening layer opacity percentage",
            1.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_boolean_argument(
            "add-mask",
            "Add Layer _Mask",
            "Attach a reveal-all (White) layer mask for selective painting",
            True,
            GObject.ParamFlags.READWRITE
        )

        return procedure


if __name__ == "__main__":
    Gimp.main(HighPassSharpen.__gtype__, sys.argv)
