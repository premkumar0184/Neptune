#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Tilt-Shift & Miniature Blur Helper Plugin
===================================================================
Photoshop Reference:
- Topics.txt line 460: "Blur and sharpen filters - Overview of adding blur to images"
- Topics.txt line 463: "Blur and sharpen filters - Adjust image sharpness and blur"
- Topics.txt line 465: "Blur and sharpen filters - Use Blur Gallery depth-of-field effects"
- photoshop_docs.md Section 424 lines 12334, 12343 (Filter > Blur Gallery > Tilt-Shift:
  Simulate camera effects such as Motion Blur or Tilt-Shift looks, selective focus planes)

Key Architectural Features:
1. Optical Tilt-Shift Depth of Field:
   - Simulates large-aperture view camera / tilt-shift lens movements.
   - Lens Blur optical bokeh with specular highlights or Gaussian defocus modes.
2. Linear Focus Band & Gradient Falloff Controls:
   - Configurable focal position (0% to 100% of canvas).
   - Clear focal band width (0% to 80%) where details remain 100% sharp.
   - Smooth progressive gradient feathering (5% to 50%) transitioning between in-focus
     and out-of-focus zones.
3. Dual Plane Orientations:
   - Horizontal plane for landscapes, cityscapes, and horizontal compositions.
   - Vertical plane for tall architecture, street corridors, and vertical subjects.
4. Miniature Model Saturation Boost:
   - Built-in saturation pop (0% to 50%) simulating the vivid enamel/plastic look of
     miniature toy models and diorama fakes.
5. Curated Photographic Presets:
   - Classic Miniature Model: Balanced diorama look with center focus and vivid saturation.
   - Toy City Diorama: Heavy optical defocus and vibrant toy colors for urban aerial shots.
   - Subtle Portrait Shallow DOF: Wide focus band with gentle background/foreground falloff.
   - Vertical Architecture Tilt: Vertical focal column for skyscrapers and towers.
   - Macro Miniature: Ultra-shallow depth of field with narrow focal plane and intense blur.
   - Custom: Full manual slider control.
6. Non-Destructive Layering & Editable Masks:
   - Creates an isolated adjustment layer duplicating the active drawable.
   - Attaches a bidirectional linear gradient layer mask that users can freely paint onto
     with black/white brushes to selectively keep tall objects or spires sharp.
   - Underlying base layer pixels remain 100% mathematically untouched (0.000000 diff).
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
    "miniature": {
        "label": "Classic Miniature Model",
        "desc": "Balanced miniature diorama with center focus and vivid saturation",
        "blur_type": "lens",
        "blur_radius": 30.0,
        "orientation": "horizontal",
        "focal_pos": 50.0,
        "focal_width": 15.0,
        "feather": 25.0,
        "sat_boost": 25.0,
        "opacity": 100.0,
    },
    "toy-city": {
        "label": "Toy City Diorama",
        "desc": "Heavy defocus with low-angle street perspective and vibrant toy colors",
        "blur_type": "lens",
        "blur_radius": 45.0,
        "orientation": "horizontal",
        "focal_pos": 65.0,
        "focal_width": 20.0,
        "feather": 20.0,
        "sat_boost": 35.0,
        "opacity": 100.0,
    },
    "portrait-dof": {
        "label": "Subtle Portrait Shallow DOF",
        "desc": "Gentle background and foreground defocus with natural skin tones",
        "blur_type": "lens",
        "blur_radius": 15.0,
        "orientation": "horizontal",
        "focal_pos": 45.0,
        "focal_width": 30.0,
        "feather": 30.0,
        "sat_boost": 5.0,
        "opacity": 90.0,
    },
    "vertical-tilt": {
        "label": "Vertical Architecture Tilt",
        "desc": "Vertical focal column for tall skyscrapers, towers, and street corridors",
        "blur_type": "lens",
        "blur_radius": 30.0,
        "orientation": "vertical",
        "focal_pos": 50.0,
        "focal_width": 20.0,
        "feather": 25.0,
        "sat_boost": 15.0,
        "opacity": 100.0,
    },
    "macro-tilt": {
        "label": "Macro Miniature",
        "desc": "Ultra-shallow depth of field with narrow focal plane and intense blur",
        "blur_type": "lens",
        "blur_radius": 50.0,
        "orientation": "horizontal",
        "focal_pos": 50.0,
        "focal_width": 10.0,
        "feather": 15.0,
        "sat_boost": 30.0,
        "opacity": 100.0,
    },
    "custom": {
        "label": "Custom Tilt-Shift",
        "desc": "Manual slider configuration",
        "blur_type": "lens",
        "blur_radius": 25.0,
        "orientation": "horizontal",
        "focal_pos": 50.0,
        "focal_width": 20.0,
        "feather": 25.0,
        "sat_boost": 20.0,
        "opacity": 100.0,
    },
}


def render_tilt_mask(mask, image, orientation, focal_pos, focal_width, feather):
    """
    Renders a bidirectional linear gradient tilt-shift mask onto the given layer mask:
    - Pure Black (0.0) in the central in-focus clear band (preserving base layer sharpness).
    - Smooth progressive grayscale ramp in the transition zones.
    - Pure White (1.0) in the outer defocus zones (revealing blurred layer).
    """
    pdb = Gimp.get_pdb()
    grad_proc = pdb.lookup_procedure("gimp-drawable-edit-gradient-fill")
    if grad_proc is None:
        return

    W = image.get_width()
    H = image.get_height()

    Gimp.context_set_background(Gegl.Color.new("white"))
    mask.edit_fill(Gimp.FillType.BACKGROUND)

    if orientation == "vertical":
        cx = W * (float(focal_pos) / 100.0)
        hw = W * (float(focal_width) / 100.0) * 0.5
        trans = max(1.0, W * (float(feather) / 100.0))
        x_left = max(0.0, cx - hw)
        x_right = min(float(W), cx + hw)
        x_l_trans = max(0.0, x_left - trans)
        x_r_trans = min(float(W), x_right + trans)

        if x_left > 0.0:
            image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, int(x_left), H)
            Gimp.context_set_foreground(Gegl.Color.new("black"))
            Gimp.context_set_background(Gegl.Color.new("white"))
            cfg = grad_proc.create_config()
            cfg.set_property("drawable", mask)
            cfg.set_property("gradient-type", Gimp.GradientType.LINEAR)
            cfg.set_property("x1", x_left)
            cfg.set_property("y1", H * 0.5)
            cfg.set_property("x2", x_l_trans)
            cfg.set_property("y2", H * 0.5)
            grad_proc.run(cfg)

        if x_right < float(W):
            image.select_rectangle(Gimp.ChannelOps.REPLACE, int(x_right), 0, W - int(x_right), H)
            Gimp.context_set_foreground(Gegl.Color.new("black"))
            Gimp.context_set_background(Gegl.Color.new("white"))
            cfg = grad_proc.create_config()
            cfg.set_property("drawable", mask)
            cfg.set_property("gradient-type", Gimp.GradientType.LINEAR)
            cfg.set_property("x1", x_right)
            cfg.set_property("y1", H * 0.5)
            cfg.set_property("x2", x_r_trans)
            cfg.set_property("y2", H * 0.5)
            grad_proc.run(cfg)

        if x_right > x_left:
            image.select_rectangle(Gimp.ChannelOps.REPLACE, int(x_left), 0, max(1, int(x_right - x_left)), H)
            Gimp.context_set_foreground(Gegl.Color.new("black"))
            mask.edit_fill(Gimp.FillType.FOREGROUND)

    else:  # horizontal
        cy = H * (float(focal_pos) / 100.0)
        hw = H * (float(focal_width) / 100.0) * 0.5
        trans = max(1.0, H * (float(feather) / 100.0))
        y_top = max(0.0, cy - hw)
        y_bot = min(float(H), cy + hw)
        y_t_trans = max(0.0, y_top - trans)
        y_b_trans = min(float(H), y_bot + trans)

        if y_top > 0.0:
            image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, W, int(y_top))
            Gimp.context_set_foreground(Gegl.Color.new("black"))
            Gimp.context_set_background(Gegl.Color.new("white"))
            cfg = grad_proc.create_config()
            cfg.set_property("drawable", mask)
            cfg.set_property("gradient-type", Gimp.GradientType.LINEAR)
            cfg.set_property("x1", W * 0.5)
            cfg.set_property("y1", y_top)
            cfg.set_property("x2", W * 0.5)
            cfg.set_property("y2", y_t_trans)
            grad_proc.run(cfg)

        if y_bot < float(H):
            image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, int(y_bot), W, H - int(y_bot))
            Gimp.context_set_foreground(Gegl.Color.new("black"))
            Gimp.context_set_background(Gegl.Color.new("white"))
            cfg = grad_proc.create_config()
            cfg.set_property("drawable", mask)
            cfg.set_property("gradient-type", Gimp.GradientType.LINEAR)
            cfg.set_property("x1", W * 0.5)
            cfg.set_property("y1", y_bot)
            cfg.set_property("x2", W * 0.5)
            cfg.set_property("y2", y_b_trans)
            grad_proc.run(cfg)

        if y_bot > y_top:
            image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, int(y_top), W, max(1, int(y_bot - y_top)))
            Gimp.context_set_foreground(Gegl.Color.new("black"))
            mask.edit_fill(Gimp.FillType.FOREGROUND)

    Gimp.Selection.none(image)


class TiltShiftPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-tilt-shift"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, self.run, None
        )
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
        procedure.set_menu_label("Tilt-Shift Blur...")
        procedure.add_menu_path("<Image>/Filters/Blur")
        procedure.add_menu_path("<Image>/Filters/Retouching")
        procedure.add_menu_path("<Image>/Layer")

        procedure.set_documentation(
            "Non-Destructive Tilt-Shift & Miniature Blur Helper",
            "Creates a non-destructive tilt-shift blur layer with configurable focal plane, "
            "optical lens bokeh, progressive gradient falloff, and miniature saturation boost.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add("miniature", 0, "Classic Miniature Model", "Balanced diorama look with center focus and vivid saturation")
        preset_choice.add("toy-city", 1, "Toy City Diorama", "Heavy defocus with low-angle street perspective and vibrant toy colors")
        preset_choice.add("portrait-dof", 2, "Subtle Portrait Shallow DOF", "Gentle background and foreground defocus with natural skin tones")
        preset_choice.add("vertical-tilt", 3, "Vertical Architecture Tilt", "Vertical focal column for tall skyscrapers, towers, and street corridors")
        preset_choice.add("macro-tilt", 4, "Macro Miniature", "Ultra-shallow depth of field with narrow focal plane and intense blur")
        preset_choice.add("custom", 5, "Custom Tilt-Shift", "Manual slider configuration")

        procedure.add_choice_argument(
            "preset",
            "Tilt-Shift Preset",
            "Curated tilt-shift preset (miniature, toy-city, portrait-dof, vertical-tilt, macro-tilt, custom)",
            preset_choice,
            "miniature",
            GObject.ParamFlags.READWRITE
        )

        # Blur Type Choice
        blur_choice = Gimp.Choice.new()
        blur_choice.add("lens", 0, "Lens Blur (Optical Bokeh)", "Simulates large-aperture camera lens optics with specular highlights")
        blur_choice.add("gaussian", 1, "Gaussian Blur (Soft Defocus)", "Smooth uniform Gaussian smoothing defocus")

        procedure.add_choice_argument(
            "blur-type",
            "Blur Method",
            "Optical lens blur vs Gaussian defocus",
            blur_choice,
            "lens",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "blur-radius",
            "Blur Radius (px)",
            "Sets the defocus blur radius in pixels (1.0 to 100.0px, default 25.0px)",
            1.0,
            100.0,
            25.0,
            GObject.ParamFlags.READWRITE
        )

        # Orientation Choice
        orient_choice = Gimp.Choice.new()
        orient_choice.add("horizontal", 0, "Horizontal Plane", "Horizontal in-focus band (landscapes, aerial views)")
        orient_choice.add("vertical", 1, "Vertical Plane", "Vertical in-focus band (architecture, towers, tall subjects)")

        procedure.add_choice_argument(
            "orientation",
            "Focus Plane Orientation",
            "Orientation of the in-focus band (horizontal, vertical)",
            orient_choice,
            "horizontal",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "focal-position",
            "Focal Plane Position (%)",
            "Center position of the in-focus band (0.0% to 100.0%, default 50.0%)",
            0.0,
            100.0,
            50.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "focal-width",
            "In-Focus Band Width (%)",
            "Width of the completely clear, sharp zone (0.0% to 80.0%, default 20.0%)",
            0.0,
            80.0,
            20.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "feather",
            "Transition Feather (%)",
            "Width of the gradient transition from sharp to blurred (5.0% to 50.0%, default 25.0%)",
            5.0,
            50.0,
            25.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "saturation-boost",
            "Miniature Saturation Boost (%)",
            "Boosts color saturation to heighten the vivid toy diorama illusion (0.0% to 50.0%, default 20.0%)",
            0.0,
            50.0,
            20.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "opacity",
            "Layer Opacity (%)",
            "Overall opacity of the Tilt-Shift blur layer (10.0% to 100.0%, default 100.0%)",
            10.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # Mask Type Choice
        mask_choice = Gimp.Choice.new()
        mask_choice.add("tilt-shift", 0, "Tilt-Shift Gradient Mask", "Automatic linear gradient mask with clear focus band")
        mask_choice.add("reveal-all", 1, "Reveal All (White Mask)", "Full image blurred; paint black to sharpen")
        mask_choice.add("conceal-all", 2, "Conceal All (Black Mask)", "Blur hidden; paint white to selectively add blur")

        procedure.add_choice_argument(
            "mask-type",
            "Layer Mask Mode",
            "Initial layer mask configuration (tilt-shift, reveal-all, conceal-all)",
            mask_choice,
            "tilt-shift",
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run(self, procedure, run_mode, image, drawables, config, data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            Gimp.ui_init("tilt-shift.py")
            dialog = Gimp.ProcedureDialog.new(procedure, config, "Tilt-Shift Blur")
            dialog.fill([
                "preset", "blur-type", "blur-radius", "orientation",
                "focal-position", "focal-width", "feather",
                "saturation-boost", "opacity", "mask-type"
            ])
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        # Resolve target drawable
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
                    GLib.quark_from_string("gimp-tilt-shift"),
                    "No target drawable found to apply Tilt-Shift Blur.",
                    0
                )
            )

        preset_key = config.get_property("preset") or "miniature"
        if preset_key not in PRESETS:
            preset_key = "miniature"
        preset_cfg = PRESETS[preset_key]

        if preset_key == "custom":
            blur_type = config.get_property("blur-type") or "lens"
            blur_radius = config.get_property("blur-radius")
            orientation = config.get_property("orientation") or "horizontal"
            focal_pos = config.get_property("focal-position")
            focal_width = config.get_property("focal-width")
            feather = config.get_property("feather")
            sat_boost = config.get_property("saturation-boost")
            opacity = config.get_property("opacity")
        else:
            blur_type = preset_cfg["blur_type"]
            blur_radius = preset_cfg["blur_radius"]
            orientation = preset_cfg["orientation"]
            focal_pos = preset_cfg["focal_pos"]
            focal_width = preset_cfg["focal_width"]
            feather = preset_cfg["feather"]
            sat_boost = preset_cfg["sat_boost"]
            opacity = config.get_property("opacity")
            if opacity <= 0.0 or opacity > 100.0:
                opacity = preset_cfg["opacity"]

        mask_type = config.get_property("mask-type") or "tilt-shift"

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
            layer_name = f"Tilt-Shift Blur ({preset_cfg['label']})"
            tilt_layer = Gimp.Layer.new_from_drawable(target_drawable, image)
            tilt_layer.set_name(layer_name)
            tilt_layer.set_mode(Gimp.LayerMode.NORMAL)
            tilt_layer.set_opacity(float(opacity))

            parent = target_drawable.get_parent()
            pos = image.get_item_position(target_drawable)
            image.insert_layer(tilt_layer, parent, pos)

            # 2. Apply optical blur operation
            if blur_type == "lens":
                filt_blur = Gimp.DrawableFilter.new(tilt_layer, "gegl:lens-blur", "")
                c_blur = filt_blur.get_config()
                c_blur.set_property("radius", float(blur_radius))
                c_blur.set_property("highlight-factor", 0.25)
                tilt_layer.merge_filter(filt_blur)
            else:
                filt_blur = Gimp.DrawableFilter.new(tilt_layer, "gegl:gaussian-blur", "")
                c_blur = filt_blur.get_config()
                c_blur.set_property("std-dev-x", float(blur_radius))
                c_blur.set_property("std-dev-y", float(blur_radius))
                tilt_layer.merge_filter(filt_blur)

            # 3. Apply miniature saturation boost if requested
            if float(sat_boost) > 0.0:
                filt_sat = Gimp.DrawableFilter.new(tilt_layer, "gegl:vibrance", "")
                c_sat = filt_sat.get_config()
                c_sat.set_property("saturation", float(sat_boost) / 100.0)
                tilt_layer.merge_filter(filt_sat)

            # 4. Attach Layer Mask
            if mask_type == "conceal-all":
                mask = tilt_layer.create_mask(Gimp.AddMaskType.BLACK)
                tilt_layer.add_mask(mask)
            elif mask_type == "reveal-all":
                mask = tilt_layer.create_mask(Gimp.AddMaskType.WHITE)
                tilt_layer.add_mask(mask)
            else:  # "tilt-shift"
                mask = tilt_layer.create_mask(Gimp.AddMaskType.WHITE)
                tilt_layer.add_mask(mask)
                render_tilt_mask(mask, image, orientation, focal_pos, focal_width, feather)

            # Cleanup / restore saved selection
            if saved_sel_channel is not None:
                image.select_item(Gimp.ChannelOps.REPLACE, saved_sel_channel)
                image.remove_channel(saved_sel_channel)

            image.set_selected_layers([tilt_layer])
            tilt_layer.set_visible(True)

        except Exception as e:
            image.undo_group_end()
            Gimp.context_pop()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-tilt-shift"),
                    f"Tilt-Shift Blur failed: {str(e)}",
                    0
                )
            )

        image.undo_group_end()
        Gimp.context_pop()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(TiltShiftPlugin.__gtype__, sys.argv)
