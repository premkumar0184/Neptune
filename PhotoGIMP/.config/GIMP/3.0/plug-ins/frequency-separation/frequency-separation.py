#!/usr/bin/env python3
"""
PhotoGIMP Frequency Separation Plugin for GIMP 3.x

Splits the active layer into two frequency components:
1. Low Frequency: Contains color and broad tonal transitions (Gaussian blur).
2. High Frequency: Contains fine surface details, skin texture, and sharp edges (High-pass texture extraction).

Allows professional non-destructive skin retouching and texture editing.
"""

import sys
import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib


def frequency_separation(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(Gimp.PDBStatusType.CALLING_ERROR, GLib.Error())

    if len(drawables) == 0:
        selected = image.get_selected_drawables()
        if len(selected) > 0:
            drawables = selected
        else:
            layers = image.get_layers()
            if len(layers) > 0:
                drawables = [layers[0]]

    if len(drawables) == 0:
        return procedure.new_return_values(Gimp.PDBStatusType.CALLING_ERROR, GLib.Error())

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-frequency-separation')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    radius = config.get_property('radius')

    Gimp.context_push()
    image.undo_group_start()

    try:
        for drawable in drawables:
            parent = drawable.get_parent()
            pos = image.get_item_position(drawable)
            base_name = drawable.get_name()

            # 1. Create a container group for the frequency separation layers
            group_name = "Frequency Separation (" + base_name + ")"
            group = Gimp.GroupLayer.new(image, group_name)
            image.insert_layer(group, parent, pos)

            # 2. Create Low Frequency layer (color and tone)
            low_layer = drawable.copy()
            low_layer.set_name("Low Frequency (Color & Tone)")
            image.insert_layer(low_layer, group, 0)

            # Apply Gaussian Blur to the low frequency layer
            blur_filter = Gimp.DrawableFilter.new(low_layer, "gegl:gaussian-blur", "")
            blur_config = blur_filter.get_config()
            blur_config.set_property("std-dev-x", float(radius))
            blur_config.set_property("std-dev-y", float(radius))
            low_layer.merge_filter(blur_filter)

            # 3. Create High Frequency layer (texture and fine details)
            high_layer = drawable.copy()
            high_layer.set_name("High Frequency (Texture)")
            # Insert above low_layer inside the group
            image.insert_layer(high_layer, group, 0)

            # Apply High Pass filter to extract texture
            high_filter = Gimp.DrawableFilter.new(high_layer, "gegl:high-pass", "")
            high_config = high_filter.get_config()
            high_config.set_property("std-dev", float(radius))
            high_layer.merge_filter(high_filter)

            # Set High Frequency layer blending mode to Linear Light / Grain Merge for seamless reconstruction
            high_layer.set_mode(Gimp.LayerMode.GRAIN_MERGE)
            high_layer.set_visible(True)
            low_layer.set_visible(True)

        Gimp.displays_flush()
    finally:
        image.undo_group_end()
        Gimp.context_pop()

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


class FrequencySeparation(Gimp.PlugIn):
    ## GimpPlugIn virtual methods ##
    def do_set_i18n(self, procname):
        return True, 'gimp30-python', None

    def do_query_procedures(self):
        return ['python-fu-frequency-separation']

    def do_create_procedure(self, name):
        Gegl.init(None)

        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            frequency_separation,
            None
        )
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )
        procedure.set_documentation(
            "Frequency Separation for Skin & Texture Retouching",
            "Splits the active layer into Low Frequency (colors/tones) and High Frequency (textures/details) layers.",
            name
        )
        procedure.set_menu_label("Frequency Separation...")
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP Project", "2026")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        procedure.add_double_argument(
            "radius",
            "Blur _Radius",
            "Gaussian blur radius (sigma) for frequency separation",
            0.1,
            100.0,
            3.0,
            GObject.ParamFlags.READWRITE
        )

        return procedure


if __name__ == "__main__":
    Gimp.main(FrequencySeparation.__gtype__, sys.argv)
