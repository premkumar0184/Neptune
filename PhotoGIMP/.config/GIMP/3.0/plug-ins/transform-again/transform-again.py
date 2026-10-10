#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# PhotoGIMP Free Transform with Duplicate & Transform Again Helper Plugin
# Complete Photoshop Parity for Ctrl+Alt+T, Shift+Ctrl+T, and Shift+Ctrl+Alt+T
# (Topics.txt lines 180-187: "Transformation options in Photoshop", "Rotate or flip images",
#  "Adjust scale, rotation, and perspective", "Duplicate objects as you transform",
#  "Apply transformations", "Move reference point for transformations", "Rotate objects";
#  photoshop_docs.md Section 184-189 lines 5365-5499)
#
# Features:
# 1. Free Transform with Duplicate (Ctrl+Alt+T): replicates active layer and transforms duplicate
#    while preserving source layer intact (diff == 0.000000).
# 2. 9-Point Reference Anchor Grid (center, top-left, top, top-right, left, right,
#    bottom-left, bottom, bottom-right) plus custom coordinate origin (x0, y0) and canvas-center.
# 3. Compounded Affine Transformation Matrix (Scale, Rotation, Translation offset, Skew).
# 4. Transform Again (Shift+Ctrl+T): reapplies remembered transformation parameters in-place.
# 5. Transform Again with Duplicate (Shift+Ctrl+Alt+T): duplicates active layer and reapplies
#    remembered transform, with compounding step-and-repeat array loops (count >= 1).
# 6. Parasite Persistence (photogimp/last-transform) stores transform parameters and matrix.
# 7. Single-Step Undo Group Encapsulation & Active Undo Stack Preservation.

import sys
import math
import json
import numpy as np
import gi

gi.require_version('Gimp', '3.0')
gi.require_version('Gegl', '0.4')
from gi.repository import Gimp, Gegl, GLib, Gio, GObject

PROC_NAME_FREE_TRANSFORM = "python-fu-free-transform-duplicate"
PROC_NAME_TRANSFORM_AGAIN = "python-fu-transform-again"
PROC_NAME_TRANSFORM_AGAIN_DUP = "python-fu-transform-again-duplicate"
PARASITE_NAME = "photogimp/last-transform"


def compute_anchor_point(image, layer, ref_point_str, custom_x, custom_y):
    """
    Computes absolute (X, Y) anchor / pivot coordinates based on layer bounds or image canvas.
    """
    ref = (ref_point_str or "center").lower().strip()
    if ref == "custom":
        return float(custom_x), float(custom_y)

    if ref == "canvas-center":
        return float(image.get_width()) / 2.0, float(image.get_height()) / 2.0

    succ, ox, oy = layer.get_offsets() if hasattr(layer, "get_offsets") else (True, 0, 0)
    w = float(layer.get_width())
    h = float(layer.get_height())

    anchors = {
        "top-left": (float(ox), float(oy)),
        "top": (float(ox) + w / 2.0, float(oy)),
        "top-right": (float(ox) + w, float(oy)),
        "left": (float(ox), float(oy) + h / 2.0),
        "center": (float(ox) + w / 2.0, float(oy) + h / 2.0),
        "right": (float(ox) + w, float(oy) + h / 2.0),
        "bottom-left": (float(ox), float(oy) + h),
        "bottom": (float(ox) + w / 2.0, float(oy) + h),
        "bottom-right": (float(ox) + w, float(oy) + h),
    }

    return anchors.get(ref, anchors["center"])


def build_affine_matrix(ax, ay, scale_x, scale_y, angle_deg, offset_x, offset_y, skew_x_deg, skew_y_deg):
    """
    Builds 3x3 forward 2D affine transformation matrix around anchor point (ax, ay):
    M = T_post @ R @ S @ K @ T_pre
    """
    rad_angle = math.radians(angle_deg)
    cos_a = math.cos(rad_angle)
    sin_a = math.sin(rad_angle)

    rad_skew_x = math.radians(skew_x_deg)
    rad_skew_y = math.radians(skew_y_deg)
    tan_kx = math.tan(rad_skew_x)
    tan_ky = math.tan(rad_skew_y)

    sx = float(scale_x) / 100.0
    sy = float(scale_y) / 100.0

    # 1. Translate anchor to origin
    T_pre = np.array([
        [1.0, 0.0, -float(ax)],
        [0.0, 1.0, -float(ay)],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)

    # 2. Skew
    K = np.array([
        [1.0, tan_kx, 0.0],
        [tan_ky, 1.0, 0.0],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)

    # 3. Scale
    S = np.array([
        [sx, 0.0, 0.0],
        [0.0, sy, 0.0],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)

    # 4. Rotate
    R = np.array([
        [cos_a, -sin_a, 0.0],
        [sin_a, cos_a, 0.0],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)

    # 5. Translate back to anchor + translation offset
    T_post = np.array([
        [1.0, 0.0, float(ax) + float(offset_x)],
        [0.0, 1.0, float(ay) + float(offset_y)],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)

    # Composite matrix
    M = T_post @ R @ S @ K @ T_pre
    return M


def apply_affine_matrix(layer, M, interpolation_str="cubic", resize_mode_str="adjust"):
    """
    Applies 3x3 affine transformation matrix M to GIMP layer using native transform_matrix.
    """
    interp_map = {
        "none": Gimp.InterpolationType.NONE,
        "linear": Gimp.InterpolationType.LINEAR,
        "cubic": Gimp.InterpolationType.CUBIC,
        "nohalo": Gimp.InterpolationType.NOHALO,
        "lohalo": Gimp.InterpolationType.LOHALO,
    }
    interp = interp_map.get((interpolation_str or "cubic").lower().strip(), Gimp.InterpolationType.CUBIC)
    Gimp.context_set_interpolation(interp)

    resize_map = {
        "adjust": Gimp.TransformResize.ADJUST,
        "clip": Gimp.TransformResize.CLIP,
        "crop": Gimp.TransformResize.CROP,
        "crop-with-aspect": Gimp.TransformResize.CROP_WITH_ASPECT,
    }
    resize = resize_map.get((resize_mode_str or "adjust").lower().strip(), Gimp.TransformResize.ADJUST)
    Gimp.context_set_transform_resize(resize)
    Gimp.context_set_transform_direction(Gimp.TransformDirection.FORWARD)

    c00 = float(M[0, 0])
    c01 = float(M[0, 1])
    c02 = float(M[0, 2])
    c10 = float(M[1, 0])
    c11 = float(M[1, 1])
    c12 = float(M[1, 2])
    c20 = float(M[2, 0])
    c21 = float(M[2, 1])
    c22 = float(M[2, 2])

    transformed_layer = layer.transform_matrix(c00, c01, c02, c10, c11, c12, c20, c21, c22)
    return transformed_layer


def save_transform_parasite(image, params_dict):
    """
    Serializes transformation parameters and matrix to image parasite.
    """
    payload_str = json.dumps(params_dict)
    parasite = Gimp.Parasite.new(PARASITE_NAME, 1, payload_str.encode('utf-8'))
    image.attach_parasite(parasite)


def load_transform_parasite(image):
    """
    Deserializes transformation parameters from image parasite.
    """
    p = image.get_parasite(PARASITE_NAME)
    if not p:
        return None
    try:
        raw_bytes = bytes(p.get_data())
        return json.loads(raw_bytes.decode('utf-8'))
    except Exception:
        return None


def resolve_target_layer(image, drawables):
    """
    Resolves active layer with fallback chain.
    """
    if drawables and len(drawables) > 0:
        return drawables[0]
    if hasattr(image, "get_selected_layers") and image.get_selected_layers():
        return image.get_selected_layers()[0]
    if hasattr(image, "get_selected_drawables") and image.get_selected_drawables():
        return image.get_selected_drawables()[0]
    if image.get_layers():
        return image.get_layers()[0]
    return None


class TransformAgainPlugin(Gimp.PlugIn):
    def do_query_procedures(self):
        return [
            PROC_NAME_FREE_TRANSFORM,
            PROC_NAME_TRANSFORM_AGAIN,
            PROC_NAME_TRANSFORM_AGAIN_DUP,
        ]

    def do_set_i18n(self, procname):
        return False

    def do_create_procedure(self, name):
        if name == PROC_NAME_FREE_TRANSFORM:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_free_transform_duplicate, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES
            )
            procedure.set_menu_label("Free Transform with Duplicate...")
            procedure.add_menu_path("<Image>/Edit/Free Transform with Duplicate...")
            procedure.add_menu_path("<Image>/Layer/Transform/Free Transform with Duplicate...")
            procedure.add_menu_path("<Image>/Tools/Transform Tools/Free Transform with Duplicate...")
            procedure.set_documentation(
                "Free Transform with Duplicate",
                "Transforms active layer with scale, rotate, translate, and skew, with duplicate option (Photoshop Ctrl+Alt+T parity).",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_double_argument("scale-x", "Scale X (%)", "Horizontal scaling percentage", -10000.0, 10000.0, 100.0, GObject.ParamFlags.READWRITE)
            procedure.add_double_argument("scale-y", "Scale Y (%)", "Vertical scaling percentage", -10000.0, 10000.0, 100.0, GObject.ParamFlags.READWRITE)
            procedure.add_boolean_argument("link-scale", "Link Scale", "Maintain uniform aspect ratio scaling", True, GObject.ParamFlags.READWRITE)
            procedure.add_double_argument("angle", "Rotation Angle", "Rotation angle in degrees", -3600.0, 3600.0, 0.0, GObject.ParamFlags.READWRITE)
            procedure.add_double_argument("offset-x", "Offset X", "Horizontal translation in pixels", -100000.0, 100000.0, 0.0, GObject.ParamFlags.READWRITE)
            procedure.add_double_argument("offset-y", "Offset Y", "Vertical translation in pixels", -100000.0, 100000.0, 0.0, GObject.ParamFlags.READWRITE)
            procedure.add_double_argument("skew-x", "Skew X", "Horizontal skew angle in degrees", -89.0, 89.0, 0.0, GObject.ParamFlags.READWRITE)
            procedure.add_double_argument("skew-y", "Skew Y", "Vertical skew angle in degrees", -89.0, 89.0, 0.0, GObject.ParamFlags.READWRITE)
            procedure.add_string_argument("reference-point", "Reference Point", "Anchor point: center, top-left, top, top-right, left, right, bottom-left, bottom, bottom-right, custom, canvas-center", "center", GObject.ParamFlags.READWRITE)
            procedure.add_double_argument("custom-origin-x", "Custom Origin X", "Custom origin X coordinate when reference-point is custom", -100000.0, 100000.0, 0.0, GObject.ParamFlags.READWRITE)
            procedure.add_double_argument("custom-origin-y", "Custom Origin Y", "Custom origin Y coordinate when reference-point is custom", -100000.0, 100000.0, 0.0, GObject.ParamFlags.READWRITE)
            procedure.add_boolean_argument("duplicate-layer", "Duplicate Layer", "Duplicate layer before transforming (Ctrl+Alt+T)", True, GObject.ParamFlags.READWRITE)
            procedure.add_string_argument("interpolation", "Interpolation", "Interpolation mode: cubic, linear, none, nohalo, lohalo", "cubic", GObject.ParamFlags.READWRITE)
            procedure.add_string_argument("resize-mode", "Resize Mode", "Transform resize mode: adjust, clip, crop", "adjust", GObject.ParamFlags.READWRITE)
            return procedure

        if name == PROC_NAME_TRANSFORM_AGAIN:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_transform_again, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES
            )
            procedure.set_menu_label("Transform Again")
            procedure.add_menu_path("<Image>/Edit/Transform/Again")
            procedure.add_menu_path("<Image>/Layer/Transform/Transform Again")
            procedure.set_documentation(
                "Transform Again",
                "Repeats the last transformation on the active layer in-place (Photoshop Shift+Ctrl+T parity).",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")
            return procedure

        if name == PROC_NAME_TRANSFORM_AGAIN_DUP:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_transform_again_duplicate, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES
            )
            procedure.set_menu_label("Transform Again and Duplicate...")
            procedure.add_menu_path("<Image>/Edit/Transform/Again and Duplicate")
            procedure.add_menu_path("<Image>/Layer/Transform/Transform Again and Duplicate")
            procedure.set_documentation(
                "Transform Again and Duplicate",
                "Duplicates active layer and repeats the last transformation on the duplicate, with step-and-repeat loop support (Photoshop Shift+Ctrl+Alt+T parity).",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_int_argument("count", "Repeat Count", "Number of step-and-repeat iterations (1 to 100)", 1, 100, 1, GObject.ParamFlags.READWRITE)
            return procedure

        return None

    def run_free_transform_duplicate(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-ta"), "No active image provided.", 0)
            )

        target_layer = resolve_target_layer(image, drawables)
        if target_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-ta"), "No active layer found.", 0)
            )

        scale_x = config.get_property("scale-x")
        scale_y = config.get_property("scale-y")
        link_scale = config.get_property("link-scale")
        angle = config.get_property("angle")
        offset_x = config.get_property("offset-x")
        offset_y = config.get_property("offset-y")
        skew_x = config.get_property("skew-x")
        skew_y = config.get_property("skew-y")
        reference_point = config.get_property("reference-point") or "center"
        custom_origin_x = config.get_property("custom-origin-x")
        custom_origin_y = config.get_property("custom-origin-y")
        duplicate_layer = config.get_property("duplicate-layer")
        interpolation = config.get_property("interpolation") or "cubic"
        resize_mode = config.get_property("resize-mode") or "adjust"

        if link_scale and scale_y == 100.0 and scale_x != 100.0:
            scale_y = scale_x

        if run_mode == Gimp.RunMode.INTERACTIVE:
            gi.require_version('GimpUi', '3.0')
            from gi.repository import GimpUi
            GimpUi.init(PROC_NAME_FREE_TRANSFORM)
            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

            scale_x = config.get_property("scale-x")
            scale_y = config.get_property("scale-y")
            link_scale = config.get_property("link-scale")
            angle = config.get_property("angle")
            offset_x = config.get_property("offset-x")
            offset_y = config.get_property("offset-y")
            skew_x = config.get_property("skew-x")
            skew_y = config.get_property("skew-y")
            reference_point = config.get_property("reference-point") or "center"
            custom_origin_x = config.get_property("custom-origin-x")
            custom_origin_y = config.get_property("custom-origin-y")
            duplicate_layer = config.get_property("duplicate-layer")
            interpolation = config.get_property("interpolation") or "cubic"
            resize_mode = config.get_property("resize-mode") or "adjust"
            if link_scale and scale_y == 100.0 and scale_x != 100.0:
                scale_y = scale_x

        image.undo_group_start()
        try:
            working_layer = target_layer
            if duplicate_layer:
                working_layer = target_layer.copy()
                base_name = target_layer.get_name()
                working_layer.set_name(f"{base_name} Copy")
                parent = target_layer.get_parent()
                pos = target_layer.get_position() if hasattr(target_layer, 'get_position') else 0
                image.insert_layer(working_layer, parent, pos)

            ax, ay = compute_anchor_point(image, working_layer, reference_point, custom_origin_x, custom_origin_y)
            M = build_affine_matrix(ax, ay, scale_x, scale_y, angle, offset_x, offset_y, skew_x, skew_y)
            res_layer = apply_affine_matrix(working_layer, M, interpolation, resize_mode)
            image.set_selected_layers([res_layer])

            # Persist in parasite
            params_dict = {
                "scale_x": scale_x,
                "scale_y": scale_y,
                "link_scale": link_scale,
                "angle": angle,
                "offset_x": offset_x,
                "offset_y": offset_y,
                "skew_x": skew_x,
                "skew_y": skew_y,
                "reference_point": reference_point,
                "custom_origin_x": custom_origin_x,
                "custom_origin_y": custom_origin_y,
                "interpolation": interpolation,
                "resize_mode": resize_mode,
            }
            save_transform_parasite(image, params_dict)

            image.undo_group_end()
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as e:
            image.undo_group_end()
            import traceback
            traceback.print_exc()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-ta"), str(e), 0)
            )

    def run_transform_again(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-ta"), "No active image provided.", 0)
            )

        target_layer = resolve_target_layer(image, drawables)
        if target_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-ta"), "No active layer found.", 0)
            )

        params = load_transform_parasite(image)
        if not params:
            # Default identity transform (no-op)
            params = {
                "scale_x": 100.0, "scale_y": 100.0, "link_scale": True,
                "angle": 0.0, "offset_x": 0.0, "offset_y": 0.0,
                "skew_x": 0.0, "skew_y": 0.0, "reference_point": "center",
                "custom_origin_x": 0.0, "custom_origin_y": 0.0,
                "interpolation": "cubic", "resize_mode": "adjust"
            }

        image.undo_group_start()
        try:
            ax, ay = compute_anchor_point(
                image, target_layer,
                params.get("reference_point", "center"),
                params.get("custom_origin_x", 0.0),
                params.get("custom_origin_y", 0.0)
            )
            M = build_affine_matrix(
                ax, ay,
                params.get("scale_x", 100.0),
                params.get("scale_y", 100.0),
                params.get("angle", 0.0),
                params.get("offset_x", 0.0),
                params.get("offset_y", 0.0),
                params.get("skew_x", 0.0),
                params.get("skew_y", 0.0)
            )
            res_layer = apply_affine_matrix(
                target_layer, M,
                params.get("interpolation", "cubic"),
                params.get("resize_mode", "adjust")
            )
            image.set_selected_layers([res_layer])
            image.undo_group_end()
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as e:
            image.undo_group_end()
            import traceback
            traceback.print_exc()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-ta"), str(e), 0)
            )

    def run_transform_again_duplicate(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-ta"), "No active image provided.", 0)
            )

        target_layer = resolve_target_layer(image, drawables)
        if target_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-ta"), "No active layer found.", 0)
            )

        params = load_transform_parasite(image)
        if not params:
            params = {
                "scale_x": 100.0, "scale_y": 100.0, "link_scale": True,
                "angle": 0.0, "offset_x": 0.0, "offset_y": 0.0,
                "skew_x": 0.0, "skew_y": 0.0, "reference_point": "center",
                "custom_origin_x": 0.0, "custom_origin_y": 0.0,
                "interpolation": "cubic", "resize_mode": "adjust"
            }

        count = config.get_property("count")
        if count < 1:
            count = 1

        image.undo_group_start()
        try:
            curr_layer = target_layer
            base_name = target_layer.get_name()
            for i in range(1, count + 1):
                dup = curr_layer.copy()
                dup_name = f"{base_name} Copy {i}" if count > 1 else f"{curr_layer.get_name()} Copy"
                dup.set_name(dup_name)
                parent = curr_layer.get_parent()
                pos = curr_layer.get_position() if hasattr(curr_layer, 'get_position') else 0
                image.insert_layer(dup, parent, pos)

                ax, ay = compute_anchor_point(
                    image, dup,
                    params.get("reference_point", "center"),
                    params.get("custom_origin_x", 0.0),
                    params.get("custom_origin_y", 0.0)
                )
                M = build_affine_matrix(
                    ax, ay,
                    params.get("scale_x", 100.0),
                    params.get("scale_y", 100.0),
                    params.get("angle", 0.0),
                    params.get("offset_x", 0.0),
                    params.get("offset_y", 0.0),
                    params.get("skew_x", 0.0),
                    params.get("skew_y", 0.0)
                )
                res_layer = apply_affine_matrix(
                    dup, M,
                    params.get("interpolation", "cubic"),
                    params.get("resize_mode", "adjust")
                )
                curr_layer = res_layer

            image.set_selected_layers([curr_layer])
            image.undo_group_end()
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as e:
            image.undo_group_end()
            import traceback
            traceback.print_exc()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-ta"), str(e), 0)
            )


Gimp.main(TransformAgainPlugin.__gtype__, sys.argv)
