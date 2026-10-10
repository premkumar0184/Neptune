#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# PhotoGIMP Layer Matting & Edge Defringe Suite Helper Plugin
# Complete Photoshop Parity for Layer > Matting (Defringe, Remove Black Matte, Remove White Matte, Color Decontaminate)
# (Topics.txt lines 225-227: "Fringe pixels around a selection", "Decrease the fringe on a selection", "Remove a matte from a selection";
#  photoshop_docs.md Section 229-231 lines 6459-6500)
#
# Features:
# 1. Defringe (python-fu-matting-defringe): Replaces semi-transparent fringe edge pixels with
#    interior pixel colors within configurable pixel width (1 to 200 px).
# 2. Remove Black Matte (python-fu-matting-remove-black-matte): Eliminates dark/black fringe contamination
#    from anti-aliased layer boundaries via inverse alpha premultiplication unmixing (C_true = C_fringe / alpha).
# 3. Remove White Matte (python-fu-matting-remove-white-matte): Eliminates light/white fringe contamination
#    from anti-aliased layer boundaries via inverse white blend unmixing (C_true = (C_fringe - (1 - alpha)) / alpha).
# 4. Color Decontaminate (python-fu-matting-color-decontaminate): Propagates core subject chrominance
#    outward into semi-transparent edge pixels while preserving original alpha gradient.
# 5. Non-Destructive Layer Mode ("<Name> (Matted)") vs In-Place Layer Patching.
# 6. Parasite Persistence (photogimp/matting): records matting operation and parameters.
# 7. Single-Step Undo Group Encapsulation & Active Undo Stack Preservation.

import sys
import json
import numpy as np
import gi

gi.require_version('Gimp', '3.0')
gi.require_version('Gegl', '0.4')
from gi.repository import Gimp, Gegl, GLib, Gio, GObject

PROC_DEFRINGE = "python-fu-matting-defringe"
PROC_REMOVE_BLACK_MATTE = "python-fu-matting-remove-black-matte"
PROC_REMOVE_WHITE_MATTE = "python-fu-matting-remove-white-matte"
PROC_COLOR_DECONTAMINATE = "python-fu-matting-color-decontaminate"
PARASITE_NAME = "photogimp/matting"


def layer_to_numpy(layer):
    """Extracts layer pixel GeglBuffer into RGBA float32 numpy array."""
    w = layer.get_width()
    h = layer.get_height()
    has_alpha = layer.has_alpha() if hasattr(layer, 'has_alpha') else False

    if not has_alpha:
        layer.add_alpha()

    buf = layer.get_buffer()
    rect = Gegl.Rectangle.new(0, 0, w, h)
    raw = buf.get(rect, 1.0, "RGBA float", Gegl.AbyssPolicy.CLAMP)
    arr = np.frombuffer(raw, dtype=np.float32).reshape((h, w, 4))
    return arr.copy()


def update_layer_from_numpy(layer, arr_rgba):
    """Writes RGBA float32 numpy array directly into layer buffer in-place."""
    h, w, _ = arr_rgba.shape
    buf = layer.get_buffer()
    rect = Gegl.Rectangle.new(0, 0, w, h)
    buf.set(rect, "RGBA float", arr_rgba.astype(np.float32).tobytes())
    buf.flush()
    layer.update(0, 0, w, h)


def numpy_to_layer(image, name, arr_rgba, pos_x=0, pos_y=0, parent=None, pos=0):
    """Creates a new layer from RGBA float32 array, inserted above reference position."""
    h, w, _ = arr_rgba.shape
    new_lyr = Gimp.Layer.new(
        image,
        name,
        w,
        h,
        Gimp.ImageType.RGBA_IMAGE,
        100.0,
        Gimp.LayerMode.NORMAL
    )
    image.insert_layer(new_lyr, parent, pos)
    new_lyr.set_offsets(pos_x, pos_y)

    buf = new_lyr.get_buffer()
    rect = Gegl.Rectangle.new(0, 0, w, h)
    buf.set(rect, "RGBA float", arr_rgba.astype(np.float32).tobytes())
    buf.flush()
    new_lyr.update(0, 0, w, h)
    return new_lyr


def apply_defringe(arr_rgba, width=1):
    """
    Replaces fringe edge pixels with interior core colors up to width distance.
    """
    H, W, _ = arr_rgba.shape
    out = arr_rgba.copy()
    rgb = out[:, :, :3]
    alpha = out[:, :, 3]

    core = (alpha >= 0.85)
    fringe = (alpha > 0.01) & (alpha < 0.85)

    if not np.any(core) or not np.any(fringe):
        return out

    idx_y, idx_x = np.meshgrid(np.arange(H), np.arange(W), indexing='ij')
    cy = np.where(core, idx_y, -1)
    cx = np.where(core, idx_x, -1)

    # 2-pass Voronoi projection from core
    for y in range(H):
        for x in range(W):
            if cy[y, x] == -1:
                best_d = 1e9
                for dy, dx in [(-1, 0), (0, -1), (-1, -1), (-1, 1)]:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and cy[ny, nx] != -1:
                        py, px = cy[ny, nx], cx[ny, nx]
                        d = (y - py) ** 2 + (x - px) ** 2
                        if d < best_d:
                            best_d = d
                            cy[y, x] = py
                            cx[y, x] = px

    for y in range(H - 1, -1, -1):
        for x in range(W - 1, -1, -1):
            cur_py, cur_px = cy[y, x], cx[y, x]
            best_d = (y - cur_py) ** 2 + (x - cur_px) ** 2 if cur_py != -1 else 1e9
            for dy, dx in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and cy[ny, nx] != -1:
                    py, px = cy[ny, nx], cx[ny, nx]
                    d = (y - py) ** 2 + (x - px) ** 2
                    if d < best_d:
                        best_d = d
                        cy[y, x] = py
                        cx[y, x] = px

    valid_core_match = (cy != -1) & (cx != -1)
    dist_sq = (idx_y - cy) ** 2 + (idx_x - cx) ** 2
    replace_mask = fringe & valid_core_match & (dist_sq <= width * width)

    if np.any(replace_mask):
        py_match = cy[replace_mask]
        px_match = cx[replace_mask]
        out[replace_mask, :3] = rgb[py_match, px_match]

    return out


def apply_remove_black_matte(arr_rgba):
    """
    Eliminates black matte fringing via inverse alpha premultiplication unmixing:
    C_true = clamp(C_fringe / alpha, 0.0, 1.0)
    """
    out = arr_rgba.copy()
    rgb = out[:, :, :3]
    alpha = out[:, :, 3]

    mask = (alpha > 0.01) & (alpha < 0.999)
    if np.any(mask):
        a_expanded = alpha[mask, np.newaxis]
        restored = rgb[mask] / a_expanded
        out[mask, :3] = np.clip(restored, 0.0, 1.0)

    return out


def apply_remove_white_matte(arr_rgba):
    """
    Eliminates white matte fringing via inverse white blend unmixing:
    C_true = clamp((C_fringe - (1 - alpha)) / alpha, 0.0, 1.0)
    """
    out = arr_rgba.copy()
    rgb = out[:, :, :3]
    alpha = out[:, :, 3]

    mask = (alpha > 0.01) & (alpha < 0.999)
    if np.any(mask):
        a_expanded = alpha[mask, np.newaxis]
        one_minus_a = 1.0 - a_expanded
        restored = (rgb[mask] - one_minus_a) / a_expanded
        out[mask, :3] = np.clip(restored, 0.0, 1.0)

    return out


def apply_color_decontaminate(arr_rgba, amount=100.0, radius=5):
    """
    Propagates interior core chrominance into edge alpha pixels while preserving alpha gradient.
    """
    H, W, _ = arr_rgba.shape
    out = arr_rgba.copy()
    rgb = out[:, :, :3]
    alpha = out[:, :, 3]

    factor = np.clip(amount / 100.0, 0.0, 1.0)
    if factor <= 0.001:
        return out

    core = (alpha >= 0.95)
    fringe = (alpha > 0.01) & (alpha < 0.95)

    if not np.any(core) or not np.any(fringe):
        return out

    idx_y, idx_x = np.meshgrid(np.arange(H), np.arange(W), indexing='ij')
    cy = np.where(core, idx_y, -1)
    cx = np.where(core, idx_x, -1)

    for y in range(H):
        for x in range(W):
            if cy[y, x] == -1:
                best_d = 1e9
                for dy, dx in [(-1, 0), (0, -1), (-1, -1), (-1, 1)]:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and cy[ny, nx] != -1:
                        py, px = cy[ny, nx], cx[ny, nx]
                        d = (y - py) ** 2 + (x - px) ** 2
                        if d < best_d:
                            best_d = d
                            cy[y, x] = py
                            cx[y, x] = px

    for y in range(H - 1, -1, -1):
        for x in range(W - 1, -1, -1):
            cur_py, cur_px = cy[y, x], cx[y, x]
            best_d = (y - cur_py) ** 2 + (x - cur_px) ** 2 if cur_py != -1 else 1e9
            for dy, dx in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and cy[ny, nx] != -1:
                    py, px = cy[ny, nx], cx[ny, nx]
                    d = (y - py) ** 2 + (x - px) ** 2
                    if d < best_d:
                        best_d = d
                        cy[y, x] = py
                        cx[y, x] = px

    valid_core_match = (cy != -1) & (cx != -1)
    dist_sq = (idx_y - cy) ** 2 + (idx_x - cx) ** 2
    decontam_mask = fringe & valid_core_match & (dist_sq <= radius * radius)

    if np.any(decontam_mask):
        py_match = cy[decontam_mask]
        px_match = cx[decontam_mask]
        decontam_rgb = rgb[py_match, px_match]
        orig_rgb = rgb[decontam_mask]
        out[decontam_mask, :3] = (1.0 - factor) * orig_rgb + factor * decontam_rgb

    return out


def resolve_target_layer(image, drawables):
    """Resolves target layer from drawables list or active image layer."""
    if drawables and len(drawables) > 0 and isinstance(drawables[0], Gimp.Layer):
        return drawables[0]
    sel = image.get_selected_layers()
    if sel and len(sel) > 0:
        return sel[0]
    layers = image.get_layers()
    if layers and len(layers) > 0:
        return layers[0]
    return None


class LayerMattingPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return [
            PROC_DEFRINGE,
            PROC_REMOVE_BLACK_MATTE,
            PROC_REMOVE_WHITE_MATTE,
            PROC_COLOR_DECONTAMINATE
        ]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            self.run,
            None
        )
        procedure.set_image_types("RGBA, RGB")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        if name == PROC_DEFRINGE:
            procedure.set_menu_label("Defringe...")
            procedure.add_menu_path("<Image>/Layer/Matting")
            procedure.add_menu_path("<Image>/Filters/Edge-Detect")
            procedure.set_documentation(
                "Defringe layer edges",
                "Replaces semi-transparent fringe edge pixels with interior core colors within specified width",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")
            procedure.add_int_argument("width", "Width", "Fringe replacement width in pixels (1 to 200)", 1, 200, 1, GObject.ParamFlags.READWRITE)
            procedure.add_boolean_argument("new-layer", "Non-Destructive Layer", "Create new layer instead of modifying in-place", False, GObject.ParamFlags.READWRITE)
            return procedure

        elif name == PROC_REMOVE_BLACK_MATTE:
            procedure.set_menu_label("Remove Black Matte")
            procedure.add_menu_path("<Image>/Layer/Matting")
            procedure.set_documentation(
                "Remove black matte fringing",
                "Eliminates black matte fringing around anti-aliased layer boundaries",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")
            procedure.add_boolean_argument("new-layer", "Non-Destructive Layer", "Create new layer instead of modifying in-place", False, GObject.ParamFlags.READWRITE)
            return procedure

        elif name == PROC_REMOVE_WHITE_MATTE:
            procedure.set_menu_label("Remove White Matte")
            procedure.add_menu_path("<Image>/Layer/Matting")
            procedure.set_documentation(
                "Remove white matte fringing",
                "Eliminates white matte fringing around anti-aliased layer boundaries",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")
            procedure.add_boolean_argument("new-layer", "Non-Destructive Layer", "Create new layer instead of modifying in-place", False, GObject.ParamFlags.READWRITE)
            return procedure

        elif name == PROC_COLOR_DECONTAMINATE:
            procedure.set_menu_label("Color Decontaminate...")
            procedure.add_menu_path("<Image>/Layer/Matting")
            procedure.add_menu_path("<Image>/Select/Matting")
            procedure.set_documentation(
                "Decontaminate edge color bleed",
                "Propagates interior core subject colors outward into semi-transparent edge pixels to neutralize background color bleed",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")
            procedure.add_double_argument("amount", "Amount", "Decontamination intensity percentage (0.0 to 100.0%)", 0.0, 100.0, 100.0, GObject.ParamFlags.READWRITE)
            procedure.add_int_argument("radius", "Radius", "Decontamination radius in pixels (1 to 50)", 1, 50, 5, GObject.ParamFlags.READWRITE)
            procedure.add_boolean_argument("new-layer", "Non-Destructive Layer", "Create new layer instead of modifying in-place", False, GObject.ParamFlags.READWRITE)
            return procedure

        return None

    def execute_matting(self, proc_name, image, drawables, width=1, amount=100.0, radius=5, new_layer=False):
        if image is None:
            return False, "No active image provided."

        target_layer = resolve_target_layer(image, drawables)
        if target_layer is None:
            return False, "No active layer found."

        image.undo_group_start()
        try:
            src_rgba = layer_to_numpy(target_layer)

            if proc_name == PROC_DEFRINGE:
                matted = apply_defringe(src_rgba, width=width)
                suffix = "Defringed"
            elif proc_name == PROC_REMOVE_BLACK_MATTE:
                matted = apply_remove_black_matte(src_rgba)
                suffix = "Black Matte Removed"
            elif proc_name == PROC_REMOVE_WHITE_MATTE:
                matted = apply_remove_white_matte(src_rgba)
                suffix = "White Matte Removed"
            elif proc_name == PROC_COLOR_DECONTAMINATE:
                matted = apply_color_decontaminate(src_rgba, amount=amount, radius=radius)
                suffix = "Decontaminated"
            else:
                image.undo_group_end()
                return False, f"Unknown procedure {proc_name}"

            parent = target_layer.get_parent()
            pos = target_layer.get_position() if hasattr(target_layer, 'get_position') else 0
            succ_o, ox, oy = target_layer.get_offsets() if hasattr(target_layer, 'get_offsets') else (True, 0, 0)

            if new_layer:
                lyr_name = f"{target_layer.get_name()} ({suffix})"
                out_layer = numpy_to_layer(image, lyr_name, matted, ox, oy, parent, pos)
                image.set_selected_layers([out_layer])
            else:
                update_layer_from_numpy(target_layer, matted)
                image.set_selected_layers([target_layer])

            # Persist in parasite
            p_data = {
                "procedure": proc_name,
                "width": width,
                "amount": amount,
                "radius": radius,
                "new_layer": new_layer,
                "target_layer": target_layer.get_name()
            }
            p = Gimp.Parasite.new(PARASITE_NAME, 1, json.dumps(p_data).encode('utf-8'))
            image.attach_parasite(p)

            image.undo_group_end()
            return True, "Success"

        except Exception as e:
            image.undo_group_end()
            import traceback
            traceback.print_exc()
            return False, str(e)

    def run(self, procedure, run_mode, image, drawables, config, run_data):
        proc_name = procedure.get_name()

        width = 1
        amount = 100.0
        radius = 5
        new_layer = False

        if proc_name == PROC_DEFRINGE:
            width = config.get_property("width")
            new_layer = config.get_property("new-layer")
        elif proc_name == PROC_REMOVE_BLACK_MATTE:
            new_layer = config.get_property("new-layer")
        elif proc_name == PROC_REMOVE_WHITE_MATTE:
            new_layer = config.get_property("new-layer")
        elif proc_name == PROC_COLOR_DECONTAMINATE:
            amount = config.get_property("amount")
            radius = config.get_property("radius")
            new_layer = config.get_property("new-layer")

        success, msg = self.execute_matting(
            proc_name,
            image,
            drawables,
            width=width,
            amount=amount,
            radius=radius,
            new_layer=new_layer
        )

        if not success:
            err = GLib.Error.new_literal(GLib.quark_from_string("layer-matting-error"), 1, msg)
            return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, err)

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(LayerMattingPlugin.__gtype__, sys.argv)
