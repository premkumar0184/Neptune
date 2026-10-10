#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Iris Blur & Vignette Bokeh Filter Plugin
==================================================================
Photoshop Reference:
- Topics.txt line 465: "Use Blur Gallery depth-of-field effects"
- Topics.txt line 460: "Overview of adding blur to images"
- Topics.txt line 461: "Create depth of field with lens blur"
- Topics.txt line 659: "Blur image backgrounds"
- photoshop_docs.md Section 424 line 12334:
  "Blur Gallery: Interactive, on-canvas tools like Field Blur, Iris Blur,
   and Tilt-Shift that let you apply blur selectively and control it visually."
- photoshop_docs.md Section 425 lines 12355-12377:
  "Create depth of field with lens blur: Depth map, Iris shape, Specular Highlights bokeh"

Key Architectural Features:
1. Selective Elliptical Depth-of-Field:
   - Focal Center (x, y): Positionable center of focus (0.0 to 1.0).
   - In-Focus Subject Radius: Controlled focal ellipse where subject remains 100% pin-sharp.
   - Ellipse Proportion / Aspect Ratio: Adjusts oval geometry (e.g. vertical for portrait faces,
     wide horizontal for cinematic anamorphic compositions).
   - Rotation Angle: Rotates the elliptical focal plane (0° to 360°).
   - Transition Feather / Softness: Smooth progressive falloff between sharp subject and blurred periphery.
2. Optical Lens Defocus & Bokeh Highlights:
   - Optical Lens Blur (gegl:lens-blur) with adjustable aperture radius and specular highlight boost.
   - Gaussian Blur (gegl:gaussian-blur) for smooth digital defocus.
3. Curated Photographic Presets:
   - Portrait Face Isolation: Flattering vertical oval focal zone for portrait faces.
   - Macro Subject Pinpoint: Tight circular focal zone with deep lens defocus and rich bokeh.
   - Street Photography Candid: Asymmetrical focal point isolating off-center candid subjects.
   - Cinematic Anamorphic Oval: Wide horizontal elliptical focus simulating anamorphic depth-of-field.
   - Vignette Peripheral Softness: Expansive oval focus softening outer peripheral edges.
   - Custom Iris Blur: Full manual slider control.
4. Flexible Mask Modes:
   - Iris Depth Mask: Sharp subject center with progressive radial falloff to blurred background.
   - Inverted Depth Mask: Blurred center with sharp outer periphery.
   - Active Selection Mask: Confines blur strictly to user selection or background cutout.
   - Full Defocus Layer: Reveal-all white mask ready for custom brush painting.
5. Non-Destructive Adjustment Layering:
   - Duplicates active drawable into an isolated layer.
   - Base layer source pixels underneath remain 100% mathematically untouched (diff == 0.000000).
"""

import math
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
    "portrait-face": {
        "label": "Portrait Face Isolation",
        "desc": "Flattering vertical oval focal zone for portrait faces with gentle feather falloff",
        "center_x": 0.50,
        "center_y": 0.40,
        "radius": 0.45,
        "proportion": 1.0,
        "squeeze": -0.25,
        "softness": 0.60,
        "rotation": 0.0,
        "blur_type": "lens",
        "blur_radius": 25.0,
        "highlight_factor": 0.25,
        "opacity": 100.0,
    },
    "macro-subject": {
        "label": "Macro Subject Pinpoint",
        "desc": "Tight circular focal zone with deep lens defocus and rich specular bokeh highlights",
        "center_x": 0.50,
        "center_y": 0.50,
        "radius": 0.25,
        "proportion": 1.0,
        "squeeze": 0.0,
        "softness": 0.50,
        "rotation": 0.0,
        "blur_type": "lens",
        "blur_radius": 45.0,
        "highlight_factor": 0.50,
        "opacity": 100.0,
    },
    "street-candid": {
        "label": "Street Photography Candid",
        "desc": "Asymmetrical focal center isolating an off-center subject within a busy street composition",
        "center_x": 0.35,
        "center_y": 0.45,
        "radius": 0.30,
        "proportion": 1.0,
        "squeeze": -0.10,
        "softness": 0.55,
        "rotation": 15.0,
        "blur_type": "lens",
        "blur_radius": 30.0,
        "highlight_factor": 0.20,
        "opacity": 100.0,
    },
    "cinematic-anamorphic": {
        "label": "Cinematic Anamorphic Oval",
        "desc": "Wide horizontal elliptical focus zone simulating anamorphic lens depth-of-field",
        "center_x": 0.50,
        "center_y": 0.50,
        "radius": 0.60,
        "proportion": 1.0,
        "squeeze": 0.60,
        "softness": 0.70,
        "rotation": 0.0,
        "blur_type": "lens",
        "blur_radius": 35.0,
        "highlight_factor": 0.30,
        "opacity": 100.0,
    },
    "vignette-defocus": {
        "label": "Vignette Peripheral Softness",
        "desc": "Expansive oval focus zone softening only outer peripheral edges with subtle blur",
        "center_x": 0.50,
        "center_y": 0.50,
        "radius": 0.80,
        "proportion": 1.0,
        "squeeze": 0.20,
        "softness": 0.80,
        "rotation": 0.0,
        "blur_type": "gaussian",
        "blur_radius": 15.0,
        "highlight_factor": 0.0,
        "opacity": 100.0,
    },
    "custom": {
        "label": "Custom Iris Blur",
        "desc": "Manual slider configuration",
        "center_x": 0.50,
        "center_y": 0.50,
        "radius": 0.45,
        "proportion": 1.0,
        "squeeze": 0.0,
        "softness": 0.60,
        "rotation": 0.0,
        "blur_type": "lens",
        "blur_radius": 25.0,
        "highlight_factor": 0.25,
        "opacity": 100.0,
    },
}


class IrisBlurPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-iris-blur"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, self.run, None
        )
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
        procedure.set_menu_label("Iris Blur...")
        procedure.add_menu_path("<Image>/Filters/Blur")
        procedure.add_menu_path("<Image>/Filters/Blur Gallery")
        procedure.add_menu_path("<Image>/Filters/Retouching")
        procedure.add_menu_path("<Image>/Layer")

        procedure.set_documentation(
            "Non-Destructive Iris Blur & Vignette Bokeh Helper",
            "Simulates optical Blur Gallery iris depth-of-field with an elliptical focal region, "
            "progressive gradient falloff, and lens bokeh highlights on an isolated adjustment layer.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add("portrait-face", 0, "Portrait Face Isolation", "Vertical oval focal zone for portrait faces")
        preset_choice.add("macro-subject", 1, "Macro Subject Pinpoint", "Tight circular focus with deep lens bokeh")
        preset_choice.add("street-candid", 2, "Street Photography Candid", "Asymmetrical focal center for off-center subjects")
        preset_choice.add("cinematic-anamorphic", 3, "Cinematic Anamorphic Oval", "Wide horizontal ellipse simulating anamorphic lens")
        preset_choice.add("vignette-defocus", 4, "Vignette Peripheral Softness", "Expansive oval focus softening outer edges")
        preset_choice.add("custom", 5, "Custom Iris Blur", "Manual slider configuration")

        procedure.add_choice_argument(
            "preset",
            "Photographic Preset",
            "Curated Iris Blur preset (portrait-face, macro-subject, street-candid, cinematic-anamorphic, vignette-defocus, custom)",
            preset_choice,
            "portrait-face",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "center-x",
            "Focal Center X (0.0-1.0)",
            "Horizontal center position of the elliptical in-focus zone (0.0 to 1.0, default 0.50)",
            0.0,
            1.0,
            0.50,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "center-y",
            "Focal Center Y (0.0-1.0)",
            "Vertical center position of the elliptical in-focus zone (0.0 to 1.0, default 0.50)",
            0.0,
            1.0,
            0.50,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "focal-radius",
            "In-Focus Subject Radius",
            "Radius of the sharp in-focus subject ellipse (0.05 to 2.0, default 0.45)",
            0.05,
            2.0,
            0.45,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "proportion",
            "Ellipse Proportion (0.0-1.0)",
            "Aspect ratio proportion of the focus ellipse (0.0 to 1.0, default 1.0)",
            0.0,
            1.0,
            1.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "squeeze",
            "Ellipse Squeeze / Stretch (-1.0 to 1.0)",
            "Horizontal (>0.0) vs vertical (<0.0) oval stretch (-1.0 to 1.0, default 0.0)",
            -1.0,
            1.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "softness",
            "Transition Feather / Softness",
            "Feather falloff gradient width from sharp subject to blurred periphery (0.05 to 1.0, default 0.60)",
            0.05,
            1.0,
            0.60,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "rotation",
            "Rotation Angle (°)",
            "Orientation angle of the focus ellipse (0.0° to 360.0°, default 0.0°)",
            0.0,
            360.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # Blur Type Choice
        blur_type_choice = Gimp.Choice.new()
        blur_type_choice.add("lens", 0, "Optical Lens Blur (Bokeh)", "Simulates physical camera aperture defocus with bokeh highlights")
        blur_type_choice.add("gaussian", 1, "Gaussian Blur", "Smooth digital defocus softening")

        procedure.add_choice_argument(
            "blur-type",
            "Optical Blur Type",
            "Defocus algorithm (lens = optical aperture bokeh, gaussian = smooth digital blur)",
            blur_type_choice,
            "lens",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "blur-radius",
            "Blur Strength / Radius (px)",
            "Optical defocus blur radius in pixels (1.0 to 100.0, default 25.0)",
            1.0,
            100.0,
            25.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "highlight-factor",
            "Specular Bokeh Highlights",
            "Highlight boost factor for out-of-focus lens bokeh (0.0 to 1.0, default 0.25)",
            0.0,
            1.0,
            0.25,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "opacity",
            "Layer Opacity (%)",
            "Overall opacity of the Iris Blur adjustment layer (10.0% to 100.0%, default 100.0%)",
            10.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # Mask Mode Choice
        mask_choice = Gimp.Choice.new()
        mask_choice.add("iris-depth", 0, "Iris Depth Mask (Sharp Subject / Blurred Edges)", "Preserves center subject sharp and blurs background")
        mask_choice.add("invert-depth", 1, "Inverted Depth Mask (Blurred Center / Sharp Edges)", "Blurs center subject and keeps background sharp")
        mask_choice.add("selection", 2, "Active Selection Mask", "Confines blur strictly to selection / background cutout")
        mask_choice.add("full", 3, "Full Defocus Layer (Reveal-All Mask)", "Applies blur across full layer with white mask for custom brushing")

        procedure.add_choice_argument(
            "mask-mode",
            "Focal Mask Mode",
            "Initial layer mask configuration (iris-depth, invert-depth, selection, full)",
            mask_choice,
            "iris-depth",
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run(self, procedure, run_mode, image, drawables, config, data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            Gimp.ui_init("iris-blur.py")
            dialog = Gimp.ProcedureDialog.new(procedure, config, "Iris Blur Depth-of-Field")
            dialog.fill([
                "preset", "center-x", "center-y", "focal-radius", "proportion",
                "squeeze", "softness", "rotation", "blur-type", "blur-radius",
                "highlight-factor", "opacity", "mask-mode"
            ])
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        # Resolve target drawable safely
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
                    GLib.quark_from_string("gimp-iris-blur"),
                    "No target drawable found to apply Iris Blur.",
                    0
                )
            )

        preset_key = config.get_property("preset") or "portrait-face"
        if preset_key not in PRESETS:
            preset_key = "portrait-face"
        preset_cfg = PRESETS[preset_key]

        if preset_key == "custom":
            cx_val = config.get_property("center-x")
            cy_val = config.get_property("center-y")
            radius_val = config.get_property("focal-radius")
            prop_val = max(0.0, min(1.0, config.get_property("proportion")))
            squeeze_val = max(-1.0, min(1.0, config.get_property("squeeze")))
            soft_val = config.get_property("softness")
            rot_val = config.get_property("rotation")
            blur_type_val = config.get_property("blur-type") or "lens"
            blur_rad_val = config.get_property("blur-radius")
            highlight_val = config.get_property("highlight-factor")
            opacity_val = config.get_property("opacity")
        else:
            cx_val = preset_cfg["center_x"]
            cy_val = preset_cfg["center_y"]
            radius_val = preset_cfg["radius"]
            prop_val = max(0.0, min(1.0, preset_cfg.get("proportion", 1.0)))
            squeeze_val = max(-1.0, min(1.0, preset_cfg.get("squeeze", 0.0)))
            soft_val = preset_cfg["softness"]
            rot_val = preset_cfg["rotation"]
            blur_type_val = preset_cfg["blur_type"]
            blur_rad_val = preset_cfg["blur_radius"]
            highlight_val = preset_cfg["highlight_factor"]
            opacity_val = config.get_property("opacity")
            if opacity_val <= 0.0 or opacity_val > 100.0:
                opacity_val = preset_cfg["opacity"]

        mask_mode = config.get_property("mask-mode") or "iris-depth"

        Gimp.context_push()
        image.undo_group_start()

        saved_sel_channel = None
        try:
            # Check active selection (Decision D-003)
            has_user_selection = not Gimp.Selection.is_empty(image)
            if has_user_selection:
                saved_sel_channel = Gimp.Selection.save(image)
                Gimp.Selection.none(image)

            # 1. Duplicate active drawable into isolated adjustment layer
            layer_name = f"Iris Blur ({preset_cfg['label']})"
            blur_layer = Gimp.Layer.new_from_drawable(target_drawable, image)
            blur_layer.set_name(layer_name)
            blur_layer.set_mode(Gimp.LayerMode.NORMAL)
            blur_layer.set_opacity(float(opacity_val))

            parent = target_drawable.get_parent()
            pos = image.get_item_position(target_drawable)
            image.insert_layer(blur_layer, parent, pos)

            # 2. Apply optical defocus blur to duplicate layer
            if blur_type_val == "gaussian":
                filt_blur = Gimp.DrawableFilter.new(blur_layer, "gegl:gaussian-blur", "")
                c_blur = filt_blur.get_config()
                c_blur.set_property("std-dev-x", float(blur_rad_val))
                c_blur.set_property("std-dev-y", float(blur_rad_val))
                blur_layer.merge_filter(filt_blur)
            else:  # "lens"
                filt_blur = Gimp.DrawableFilter.new(blur_layer, "gegl:lens-blur", "")
                c_blur = filt_blur.get_config()
                c_blur.set_property("radius", float(blur_rad_val))
                c_blur.set_property("highlight-factor", float(highlight_val))
                blur_layer.merge_filter(filt_blur)

            # 3. Create and attach focal depth layer mask
            if mask_mode == "iris-depth":
                # Black mask hides blur layer completely at center (sharp subject)
                mask = blur_layer.create_mask(Gimp.AddMaskType.BLACK)
                blur_layer.add_mask(mask)

                # Vignette radial falloff reveals blur on outer background
                filt_vig = Gimp.DrawableFilter.new(mask, "gegl:vignette", "")
                c_vig = filt_vig.get_config()
                c_vig.set_property("shape", "circle")
                c_vig.set_property("color", Gegl.Color.new("white"))
                c_vig.set_property("x", float(cx_val))
                c_vig.set_property("y", float(cy_val))
                c_vig.set_property("radius", float(radius_val))
                c_vig.set_property("proportion", float(prop_val))
                c_vig.set_property("squeeze", float(squeeze_val))
                c_vig.set_property("softness", float(soft_val))
                c_vig.set_property("rotation", float(rot_val))
                mask.merge_filter(filt_vig)

            elif mask_mode == "invert-depth":
                # White mask reveals blur at center; black vignette protects periphery
                mask = blur_layer.create_mask(Gimp.AddMaskType.WHITE)
                blur_layer.add_mask(mask)

                filt_vig = Gimp.DrawableFilter.new(mask, "gegl:vignette", "")
                c_vig = filt_vig.get_config()
                c_vig.set_property("shape", "circle")
                c_vig.set_property("color", Gegl.Color.new("black"))
                c_vig.set_property("x", float(cx_val))
                c_vig.set_property("y", float(cy_val))
                c_vig.set_property("radius", float(radius_val))
                c_vig.set_property("proportion", float(prop_val))
                c_vig.set_property("squeeze", float(squeeze_val))
                c_vig.set_property("softness", float(soft_val))
                c_vig.set_property("rotation", float(rot_val))
                mask.merge_filter(filt_vig)

            elif mask_mode == "selection":
                if saved_sel_channel is not None:
                    # Invert user selection so blur is revealed on background
                    image.select_item(Gimp.ChannelOps.REPLACE, saved_sel_channel)
                    Gimp.Selection.invert(image)
                    mask = blur_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    blur_layer.add_mask(mask)
                    Gimp.Selection.none(image)
                else:
                    mask = blur_layer.create_mask(Gimp.AddMaskType.WHITE)
                    blur_layer.add_mask(mask)

            else:  # "full"
                mask = blur_layer.create_mask(Gimp.AddMaskType.WHITE)
                blur_layer.add_mask(mask)

            # Cleanup saved selection channel
            if saved_sel_channel is not None:
                image.remove_channel(saved_sel_channel)

            image.set_selected_layers([blur_layer])
            blur_layer.set_visible(True)

        except Exception as e:
            image.undo_group_end()
            Gimp.context_pop()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-iris-blur"),
                    f"Iris Blur failed: {str(e)}",
                    0
                )
            )

        image.undo_group_end()
        Gimp.context_pop()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(IrisBlurPlugin.__gtype__, sys.argv)
