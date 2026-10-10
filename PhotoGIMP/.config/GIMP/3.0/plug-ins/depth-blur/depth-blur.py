#!/usr/bin/env python3
"""
PhotoGIMP Non-Destructive Depth of Field & Background Defocus Plugin for GIMP 3.x

Creates a non-destructive depth-of-field blur layer with optical lens bokeh
or Gaussian defocus, protected by a focal depth mask that keeps the subject
100% sharp while smoothly defocusing background elements.

Photoshop Equivalence:
- Topics.txt line 461: Blur and sharpen filters - Create depth of field with lens blur.
- Topics.txt line 465: Use Blur Gallery depth-of-field effects.
- Topics.txt line 659: Quick actions - Blur image backgrounds.
- photoshop_docs.md Section 425: Create depth of field with lens blur.

Key Features:
1. 100% Non-Destructive: Duplicates the source layer into an isolated blur layer.
2. Optical Lens Bokeh: Uses GEGL gegl:lens-blur with specular highlight enhancement.
3. Smooth Depth Masking: Automatically applies radial depth falloff mask, preserving
   the center subject with 0.000000 mathematical sharpness while blurring periphery.
4. Selection Aware: Respects active user selections to isolate complex subjects.
5. Live Brush Refinement: Layer mask remains attached and active for manual touch-ups.
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


def depth_blur(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-depth-blur"),
                "No valid image provided.",
                0
            )
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-depth-blur')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    # Read configuration parameters
    blur_type = config.get_property('blur-type')
    blur_radius = config.get_property('blur-radius')
    highlight_factor = config.get_property('highlight-factor')
    depth_source = config.get_property('depth-source')
    focal_radius = config.get_property('focal-radius')
    focal_softness = config.get_property('focal-softness')
    opacity = config.get_property('opacity')

    # Resolve active target drawable
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
                GLib.quark_from_string("gimp-depth-blur"),
                "No target drawable found to apply depth defocus.",
                0
            )
        )

    Gimp.context_push()
    image.undo_group_start()

    try:
        # Determine layer name
        blur_name = "Depth Defocus (Lens Bokeh)" if blur_type == "lens" else "Depth Defocus (Gaussian Blur)"

        # Duplicate the target layer for non-destructive workflow
        blur_layer = Gimp.Layer.new_from_drawable(target_drawable, image)
        blur_layer.set_name(blur_name)
        blur_layer.set_opacity(float(opacity))
        blur_layer.set_mode(Gimp.LayerMode.NORMAL)

        # Insert immediately above target drawable
        parent = target_drawable.get_parent()
        pos = image.get_item_position(target_drawable)
        image.insert_layer(blur_layer, parent, pos)

        # Apply blur operation to the duplicated layer
        if blur_type == "lens":
            blur_filter = Gimp.DrawableFilter.new(blur_layer, "gegl:lens-blur", "")
            f_config = blur_filter.get_config()
            f_config.set_property("radius", float(blur_radius))
            f_config.set_property("highlight-factor", float(highlight_factor))
            blur_layer.merge_filter(blur_filter)
        else:
            blur_filter = Gimp.DrawableFilter.new(blur_layer, "gegl:gaussian-blur", "")
            f_config = blur_filter.get_config()
            f_config.set_property("std-dev-x", float(blur_radius))
            f_config.set_property("std-dev-y", float(blur_radius))
            blur_layer.merge_filter(blur_filter)

        # Create depth mask to preserve in-focus subject
        if depth_source == "radial":
            # Black mask hides blur layer completely at center (sharp subject)
            mask = blur_layer.create_mask(Gimp.AddMaskType.BLACK)
            blur_layer.add_mask(mask)

            # Apply radial gradient falloff to white (reveals blur at edges)
            vignette_filter = Gimp.DrawableFilter.new(mask, "gegl:vignette", "")
            v_config = vignette_filter.get_config()
            v_config.set_property("radius", float(focal_radius))
            v_config.set_property("softness", float(focal_softness))
            v_config.set_property("shape", "circle")
            v_config.set_property("color", Gegl.Color.new("white"))
            mask.merge_filter(vignette_filter)

        elif depth_source == "selection":
            if not Gimp.Selection.is_empty(image):
                # Invert selection so background is selected (reveals blur on background)
                Gimp.Selection.invert(image)
                mask = blur_layer.create_mask(Gimp.AddMaskType.SELECTION)
                blur_layer.add_mask(mask)
                # Invert back to restore user's original selection
                Gimp.Selection.invert(image)
            else:
                # Fallback to radial if no active selection exists
                mask = blur_layer.create_mask(Gimp.AddMaskType.BLACK)
                blur_layer.add_mask(mask)
                vignette_filter = Gimp.DrawableFilter.new(mask, "gegl:vignette", "")
                v_config = vignette_filter.get_config()
                v_config.set_property("radius", float(focal_radius))
                v_config.set_property("softness", float(focal_softness))
                v_config.set_property("shape", "circle")
                v_config.set_property("color", Gegl.Color.new("white"))
                mask.merge_filter(vignette_filter)

        else:  # "full"
            # Reveal-all white mask allowing manual painting
            mask = blur_layer.create_mask(Gimp.AddMaskType.WHITE)
            blur_layer.add_mask(mask)

        # Set blur layer active with mask ready for brushing
        image.set_selected_layers([blur_layer])
        blur_layer.set_visible(True)

        Gimp.displays_flush()
    finally:
        image.undo_group_end()
        Gimp.context_pop()

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


class DepthBlur(Gimp.PlugIn):
    ## GimpPlugIn virtual methods ##
    def do_set_i18n(self, procname):
        return True, 'gimp30-python', None

    def do_query_procedures(self):
        return ['python-fu-depth-blur']

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            depth_blur,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_documentation(
            "Create non-destructive depth of field defocus and background blur",
            "Creates a non-destructive blur layer with optical lens bokeh or Gaussian defocus, "
            "with a focal depth mask preserving center subject sharpness while defocusing backgrounds.",
            name
        )
        procedure.set_menu_label("Depth Defocus (Lens Blur)...")
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP Project", "2026")
        procedure.add_menu_path("<Image>/Filters/Blur")

        # Blur Type Choice
        blur_choice = Gimp.Choice.new()
        blur_choice.add(
            "lens",
            0,
            "Lens Blur (Optical Bokeh & Specular Highlights)",
            "Simulates real camera lens optics with specular highlight bokeh"
        )
        blur_choice.add(
            "gaussian",
            1,
            "Gaussian Blur (Soft Defocus)",
            "Uniform Gaussian smoothing defocus"
        )
        procedure.add_choice_argument(
            "blur-type",
            "Blur _Type",
            "Optical lens blur vs Gaussian defocus",
            blur_choice,
            "lens",
            GObject.ParamFlags.READWRITE
        )

        # Blur Radius Slider
        procedure.add_double_argument(
            "blur-radius",
            "_Blur Radius / Strength",
            "Blur radius in pixels (defocus amount)",
            1.0,
            100.0,
            15.0,
            GObject.ParamFlags.READWRITE
        )

        # Specular Highlight Factor Slider
        procedure.add_double_argument(
            "highlight-factor",
            "_Specular Highlight Bokeh",
            "Highlight boost factor for lens bokeh (0.0 = none, 1.0 = maximum)",
            0.0,
            1.0,
            0.2,
            GObject.ParamFlags.READWRITE
        )

        # Depth Source Choice
        depth_choice = Gimp.Choice.new()
        depth_choice.add(
            "radial",
            0,
            "Radial Depth Mask (Sharp Center Subject / Blurred Edges)",
            "Gradually transitions from sharp center subject to blurred periphery"
        )
        depth_choice.add(
            "selection",
            1,
            "Active Selection (Protect Subject / Blur Background)",
            "Uses active selection boundary to isolate subject and blur background"
        )
        depth_choice.add(
            "full",
            2,
            "Full Defocus Layer (Reveal-All Mask for Manual Painting)",
            "Applies blur across entire layer with white mask for custom brushing"
        )
        procedure.add_choice_argument(
            "depth-source",
            "_Depth Mask Source",
            "Focal depth protection mask style",
            depth_choice,
            "radial",
            GObject.ParamFlags.READWRITE
        )

        # Focal Zone Radius Slider
        procedure.add_double_argument(
            "focal-radius",
            "In-Focus Subject _Radius",
            "Radius of sharp in-focus subject zone (radial mode)",
            0.1,
            3.0,
            0.8,
            GObject.ParamFlags.READWRITE
        )

        # Focal Zone Softness Slider
        procedure.add_double_argument(
            "focal-softness",
            "Depth Transition _Feather",
            "Softness / feathering of focal depth falloff",
            0.1,
            1.0,
            0.6,
            GObject.ParamFlags.READWRITE
        )

        # Layer Opacity Slider
        procedure.add_double_argument(
            "opacity",
            "Defocus Layer _Opacity",
            "Opacity of the defocus layer (10.0 to 100.0%)",
            10.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        return procedure


Gimp.main(DepthBlur.__gtype__, sys.argv)
