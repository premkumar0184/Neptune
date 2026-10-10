#!/usr/bin/env python3
"""
PhotoGIMP Non-Destructive Shadows & Highlights Recovery Plugin for GIMP 3.x

Creates a non-destructive tone recovery layer using local neighborhood tonal
analysis to correct backlit subjects, lift crushed shadows, and recover blown
highlights while preserving source pixel integrity.

Photoshop Equivalence:
- Topics.txt line 269: Adjust image shadows and highlights.
- photoshop_docs.md Section 273: Adjust image shadows and highlights in photoeditor.
  Apply Shadow/Highlight adjustments to correct backlighting and brighten dark areas
  by analyzing each pixel's surrounding area and adjusting tones locally rather than globally.

Key Advantages over stock destructive editing:
1. 100% Non-Destructive: Created as an isolated recovery layer above the active image.
2. Local Spatial Tonal Analysis: Powered by GEGL gegl:shadows-highlights.
3. Bidirectional Recovery: Independently lift shadows and compress/darken blown highlights.
4. Layer Mask Attached: Reveal-all white mask enables targeted brush-painting on subjects.
5. Live Opacity Control: Fine-tune the recovery intensity at any point in the workflow.
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


def shadow_highlight(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-shadow-highlight"),
                "No valid image provided.",
                0
            )
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-shadow-highlight')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    # Read configuration parameters
    shadows = config.get_property('shadows')
    highlights = config.get_property('highlights')
    radius = config.get_property('radius')
    compress = config.get_property('compress')
    opacity = config.get_property('opacity')
    add_mask = config.get_property('add-mask')

    # Resolve target drawable
    target_drawable = None
    if drawables and len(drawables) > 0:
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
                GLib.quark_from_string("gimp-shadow-highlight"),
                "No target drawable found to apply shadows and highlights recovery.",
                0
            )
        )

    Gimp.context_push()
    image.undo_group_start()

    try:
        # Create non-destructive recovery layer duplicating target
        recovery_layer = Gimp.Layer.new_from_drawable(target_drawable, image)
        recovery_layer.set_name("Shadows & Highlights (Recovery)")
        recovery_layer.set_opacity(float(opacity))
        recovery_layer.set_mode(Gimp.LayerMode.NORMAL)

        # Insert immediately above target drawable
        parent = target_drawable.get_parent()
        pos = image.get_item_position(target_drawable)
        image.insert_layer(recovery_layer, parent, pos)

        # Apply GEGL shadows-highlights filter
        # Note: In GEGL gegl:shadows-highlights, positive 'shadows' lifts shadows,
        # and negative 'highlights' compresses/darkens highlights.
        sh_filter = Gimp.DrawableFilter.new(recovery_layer, "gegl:shadows-highlights", "")
        f_config = sh_filter.get_config()
        f_config.set_property("shadows", float(shadows))
        f_config.set_property("highlights", -float(highlights))
        f_config.set_property("radius", float(radius))
        f_config.set_property("compress", float(compress))
        recovery_layer.merge_filter(sh_filter)

        # Attach optional reveal-all layer mask
        if add_mask:
            mask = recovery_layer.create_mask(Gimp.AddMaskType.WHITE)
            recovery_layer.add_mask(mask)

        # Select the recovery layer as active
        image.set_selected_layers([recovery_layer])
        recovery_layer.set_visible(True)

        Gimp.displays_flush()
    finally:
        image.undo_group_end()
        Gimp.context_pop()

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


class ShadowHighlight(Gimp.PlugIn):
    ## GimpPlugIn virtual methods ##
    def do_set_i18n(self, procname):
        return True, 'gimp30-python', None

    def do_query_procedures(self):
        return ['python-fu-shadow-highlight']

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            shadow_highlight,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_documentation(
            "Non-destructive shadows and highlights tonal recovery",
            "Creates a non-destructive tone recovery layer using local spatial analysis "
            "to brighten deep shadows and compress blown highlights without flattening midtones.",
            name
        )
        procedure.set_menu_label("Shadows and Highlights...")
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP Project", "2026")
        procedure.add_menu_path("<Image>/Colors")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        # Shadows Amount Slider (0 to 100%)
        procedure.add_double_argument(
            "shadows",
            "_Shadows Amount (Lighten)",
            "Amount of shadow brightening to apply (0.0 to 100.0%)",
            0.0,
            100.0,
            50.0,
            GObject.ParamFlags.READWRITE
        )

        # Highlights Amount Slider (0 to 100%)
        procedure.add_double_argument(
            "highlights",
            "_Highlights Amount (Darken / Recover)",
            "Amount of highlight compression/darkening to apply (0.0 to 100.0%)",
            0.0,
            100.0,
            50.0,
            GObject.ParamFlags.READWRITE
        )

        # Spatial Radius / Tonal Width
        procedure.add_double_argument(
            "radius",
            "Tonal _Radius (Spatial Width)",
            "Local spatial neighborhood radius in pixels for tone calculation",
            1.0,
            500.0,
            50.0,
            GObject.ParamFlags.READWRITE
        )

        # Midtone Compression
        procedure.add_double_argument(
            "compress",
            "Midtone _Compression",
            "Compress effect on shadows/highlights to protect midtones (0.0 to 100.0%)",
            0.0,
            100.0,
            20.0,
            GObject.ParamFlags.READWRITE
        )

        # Layer Opacity Slider
        procedure.add_double_argument(
            "opacity",
            "Layer _Opacity",
            "Overall opacity of the recovery layer (10.0 to 100.0%)",
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


Gimp.main(ShadowHighlight.__gtype__, sys.argv)
