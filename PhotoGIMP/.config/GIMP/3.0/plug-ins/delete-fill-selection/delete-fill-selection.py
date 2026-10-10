#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# PhotoGIMP Delete and Fill Selection Helper Plugin
# Complete Photoshop Parity for Shift+Backspace / Right-Click "Delete and Fill Selection"
# (Topics.txt line 195: "Remove objects with Delete and Fill Selection";
#  photoshop_docs.md Section 199 lines 5841-5852)
#
# Features:
# 1. One-Click Object Removal (Shift+Backspace): eliminates selected elements and in-fills
#    with boundary synthesized content matching the surrounding background.
# 2. Boundary Dilation / Expansion (expand): swallows object perimeter halos and edge fringing.
# 3. Poisson/Laplace Harmonic Diffusion: solves harmonic gradient relaxation matching ambient illumination.
# 4. Ambient Texture Synthesis & Grain Injection: matches surrounding high-frequency noise.
# 5. Edge Feathering (feather): smooth alpha transition seamlessly blending with unaffected canvas.
# 6. Automatic Deselection Post-Fill (deselect): clears selection marquee for instant clean preview.
# 7. Non-Destructive Layer Mode ("<Name> (Object Removed)") vs In-Place Layer Patching.
# 8. Empty Selection Safety: handles empty selection gracefully without error.
# 9. Parasite Persistence (photogimp/delete-fill): records fill parameters and metadata.
# 10. Single-Step Undo Group Encapsulation & Active Undo Stack Preservation.

import sys
import math
import json
import numpy as np
import gi

gi.require_version('Gimp', '3.0')
gi.require_version('Gegl', '0.4')
from gi.repository import Gimp, Gegl, GLib, Gio, GObject

PROC_NAME_ONE_CLICK = "python-fu-delete-fill-selection"
PROC_NAME_OPTIONS = "python-fu-delete-fill-options"
PARASITE_NAME = "photogimp/delete-fill"


def layer_to_numpy(layer):
    """Extracts layer pixel GeglBuffer into RGBA float32 numpy array."""
    w = layer.get_width()
    h = layer.get_height()
    has_alpha = layer.has_alpha() if hasattr(layer, 'has_alpha') else False

    buf = layer.get_buffer()
    rect = Gegl.Rectangle.new(0, 0, w, h)
    fmt = "RGBA float" if has_alpha else "RGB float"
    raw = buf.get(rect, 1.0, fmt, Gegl.AbyssPolicy.CLAMP)

    if has_alpha:
        arr = np.frombuffer(raw, dtype=np.float32).reshape((h, w, 4))
    else:
        rgb = np.frombuffer(raw, dtype=np.float32).reshape((h, w, 3))
        alpha = np.ones((h, w, 1), dtype=np.float32)
        arr = np.concatenate([rgb, alpha], axis=2)

    return arr.astype(np.float32).copy()


def update_layer_from_numpy(layer, arr_rgba):
    """Writes RGBA float32 numpy array directly into layer buffer in-place."""
    h, w, _ = arr_rgba.shape
    buf = layer.get_buffer()
    rect = Gegl.Rectangle.new(0, 0, w, h)
    buf.set(rect, "RGBA float", arr_rgba.astype(np.float32).tobytes())
    buf.flush()
    layer.update(0, 0, w, h)


def numpy_to_layer(image, name, arr_rgba, pos_x=0, pos_y=0, parent=None, pos=0):
    """Creates a new RGBA layer from numpy array and inserts it into image."""
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


def extract_selection_mask(image, layer):
    """
    Extracts binary/greyscale selection mask aligned to the target layer's bounds.
    Returns (lh, lw) float32 array with values in [0.0, 1.0], or None if no selection.
    """
    if Gimp.Selection.is_empty(image):
        return None

    chan = Gimp.Selection.save(image)
    if not chan:
        return None

    cw = chan.get_width()
    ch = chan.get_height()
    cbuf = chan.get_buffer()
    crect = Gegl.Rectangle.new(0, 0, cw, ch)
    raw_mask = cbuf.get(crect, 1.0, "Y float", Gegl.AbyssPolicy.CLAMP)
    mask_doc = np.frombuffer(raw_mask, dtype=np.float32).reshape((ch, cw))
    image.remove_channel(chan)

    succ, ox, oy = layer.get_offsets() if hasattr(layer, 'get_offsets') else (True, 0, 0)
    lw = layer.get_width()
    lh = layer.get_height()

    layer_mask = np.zeros((lh, lw), dtype=np.float32)
    x_start = max(0, ox)
    x_end = min(cw, ox + lw)
    y_start = max(0, oy)
    y_end = min(ch, oy + lh)

    if x_end > x_start and y_end > y_start:
        layer_mask[y_start - oy: y_end - oy, x_start - ox: x_end - ox] = mask_doc[y_start:y_end, x_start:x_end]

    return layer_mask


def dilate_binary_mask(mask, radius):
    """Dilates mask by radius pixels to expand selection and swallow border halos."""
    if radius <= 0:
        return mask.copy()

    dilated = (mask > 0.1).astype(np.float32)
    for _ in range(radius):
        pad = np.pad(dilated, 1, mode='constant', constant_values=0)
        dilated = np.maximum.reduce([
            dilated,
            pad[:-2, 1:-1], pad[2:, 1:-1], pad[1:-1, :-2], pad[1:-1, 2:],
            pad[:-2, :-2], pad[:-2, 2:], pad[2:, :-2], pad[2:, 2:]
        ])
    return dilated


def feather_mask_array(mask, radius):
    """Applies smooth feathering blur to mask."""
    if radius <= 0.1:
        return mask.copy()

    passes = max(1, int(round(radius)))
    feathered = mask.copy().astype(np.float32)
    for _ in range(passes):
        pad = np.pad(feathered, 1, mode='edge')
        feathered = (
            pad[:-2, :-2] + pad[:-2, 1:-1] + pad[:-2, 2:] +
            pad[1:-1, :-2] + pad[1:-1, 1:-1] + pad[1:-1, 2:] +
            pad[2:, :-2] + pad[2:, 1:-1] + pad[2:, 2:]
        ) / 9.0
    return np.clip(feathered, 0.0, 1.0)


def inpaint_selection(src_rgba, raw_mask, sampling_radius=16, expand=2, feather=2.0):
    """
    Seamless Content-Aware inpainting replacing masked pixels with surrounding texture & tone.
    """
    H, W, C = src_rgba.shape

    # 1. Expand mask to swallow object edges
    dilated_mask = dilate_binary_mask(raw_mask, expand)
    hole = (dilated_mask > 0.5)
    valid = ~hole

    if not np.any(hole) or not np.any(valid):
        return src_rgba.copy()

    filled = src_rgba.copy()

    # 2. Fast 2-pass Voronoi boundary projection
    idx_y, idx_x = np.meshgrid(np.arange(H), np.arange(W), indexing='ij')
    cy = np.where(valid, idx_y, -1)
    cx = np.where(valid, idx_x, -1)

    for y in range(H):
        for x in range(W):
            if cy[y, x] == -1:
                best_d = 1e9
                for dy, dx in [(-1, 0), (0, -1)]:
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
            for dy, dx in [(1, 0), (0, 1)]:
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and cy[ny, nx] != -1:
                    py, px = cy[ny, nx], cx[ny, nx]
                    d = (y - py) ** 2 + (x - px) ** 2
                    if d < best_d:
                        best_d = d
                        cy[y, x] = py
                        cx[y, x] = px

    filled[:, :, :3] = src_rgba[cy, cx, :3]

    # 3. Poisson / Jacobi harmonic diffusion: 15 relaxation steps
    for _ in range(15):
        pad = np.pad(filled, ((1, 1), (1, 1), (0, 0)), mode='edge')
        avg = 0.25 * (pad[:-2, 1:-1] + pad[2:, 1:-1] + pad[1:-1, :-2] + pad[1:-1, 2:])
        filled[hole] = avg[hole]

    # 4. Sampling boundary band texture variance synthesis
    margin_band = dilate_binary_mask(dilated_mask, sampling_radius)
    band_mask = (margin_band > 0.5) & valid

    if np.any(band_mask):
        band_pixels = src_rgba[band_mask, :3]
        std_rgb = np.std(band_pixels, axis=0)
        # If boundary has notable photographic grain, inject subtle synthetic noise
        if np.any(std_rgb > 0.005):
            noise = np.random.normal(0.0, np.clip(std_rgb * 0.35, 0.001, 0.04), size=(H, W, 3)).astype(np.float32)
            filled[hole, :3] = np.clip(filled[hole, :3] + noise[hole], 0.0, 1.0)

    # 5. Feathered edge blending
    feathered_mask = feather_mask_array(dilated_mask, feather)
    alpha_blend = feathered_mask[:, :, None]
    result = (1.0 - alpha_blend) * src_rgba + alpha_blend * filled
    result[:, :, 3] = src_rgba[:, :, 3]

    return result.astype(np.float32)


def resolve_target_layer(image, drawables):
    """Resolves active layer with fallback chain."""
    if drawables and len(drawables) > 0:
        return drawables[0]
    if hasattr(image, "get_selected_layers") and image.get_selected_layers():
        return image.get_selected_layers()[0]
    if hasattr(image, "get_selected_drawables") and image.get_selected_drawables():
        return image.get_selected_drawables()[0]
    if image.get_layers():
        return image.get_layers()[0]
    return None


class DeleteFillSelectionPlugin(Gimp.PlugIn):
    """Native GIMP 3.0 Delete and Fill Selection Plugin."""

    def do_query_procedures(self):
        return [
            PROC_NAME_ONE_CLICK,
            PROC_NAME_OPTIONS,
        ]

    def do_set_i18n(self, procname):
        return False

    def do_create_procedure(self, name):
        if name == PROC_NAME_ONE_CLICK:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_delete_fill_one_click, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES
            )
            procedure.set_menu_label("Delete and Fill Selection")
            procedure.add_menu_path("<Image>/Edit/Delete and Fill Selection")
            procedure.add_menu_path("<Image>/Select/Delete and Fill Selection")
            procedure.add_menu_path("<Image>/Layer/Delete and Fill Selection")
            procedure.set_documentation(
                "Delete and Fill Selection",
                "Removes selected objects and seamlessly fills with surrounding background pixels (Photoshop Shift+Backspace parity).",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")
            return procedure

        if name == PROC_NAME_OPTIONS:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_delete_fill_options, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES
            )
            procedure.set_menu_label("Delete and Fill Options...")
            procedure.add_menu_path("<Image>/Edit/Delete and Fill Options...")
            procedure.add_menu_path("<Image>/Select/Delete and Fill Options...")
            procedure.set_documentation(
                "Delete and Fill Options",
                "Configurable Content-Aware object removal and background fill with sampling control.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_int_argument("sampling-radius", "Sampling Margin", "Sampling radius in pixels (1 to 200)", 1, 200, 16, GObject.ParamFlags.READWRITE)
            procedure.add_double_argument("feather", "Edge Feathering", "Feather radius in pixels (0.0 to 50.0)", 0.0, 50.0, 2.0, GObject.ParamFlags.READWRITE)
            procedure.add_int_argument("expand", "Selection Expansion", "Expansion dilation in pixels (0 to 50)", 0, 50, 2, GObject.ParamFlags.READWRITE)
            procedure.add_string_argument("method", "Inpaint Method", "Method: boundary-synthesis, harmonic-inpaint", "boundary-synthesis", GObject.ParamFlags.READWRITE)
            procedure.add_boolean_argument("new-layer", "Non-Destructive Layer", "Create new layer instead of modifying in-place", False, GObject.ParamFlags.READWRITE)
            procedure.add_boolean_argument("deselect", "Deselect Post-Fill", "Automatically clear selection upon fill completion", True, GObject.ParamFlags.READWRITE)
            return procedure

        return None

    def execute_delete_fill(self, image, drawables, sampling_radius=16, feather=2.0, expand=2, new_layer=False, deselect=True):
        if image is None:
            return False, "No active image provided."

        target_layer = resolve_target_layer(image, drawables)
        if target_layer is None:
            return False, "No active layer found."

        if Gimp.Selection.is_empty(image):
            # Clean non-fatal return if no selection active
            return True, "No active selection to fill."

        succ, non_empty, x1, y1, x2, y2 = Gimp.Selection.bounds(image)
        if not non_empty:
            return True, "Selection is empty."

        mask = extract_selection_mask(image, target_layer)
        if mask is None or not np.any(mask > 0.05):
            return True, "No selection intersection with target layer."

        image.undo_group_start()
        try:
            src_rgba = layer_to_numpy(target_layer)
            inpainted = inpaint_selection(src_rgba, mask, sampling_radius=sampling_radius, expand=expand, feather=feather)

            parent = target_layer.get_parent()
            pos = target_layer.get_position() if hasattr(target_layer, 'get_position') else 0
            succ_o, ox, oy = target_layer.get_offsets() if hasattr(target_layer, 'get_offsets') else (True, 0, 0)

            if new_layer:
                lyr_name = f"{target_layer.get_name()} (Object Removed)"
                out_layer = numpy_to_layer(image, lyr_name, inpainted, ox, oy, parent, pos)
                image.set_selected_layers([out_layer])
            else:
                update_layer_from_numpy(target_layer, inpainted)
                image.set_selected_layers([target_layer])

            if deselect:
                Gimp.Selection.none(image)

            # Persist in parasite
            p_data = {
                "sampling_radius": sampling_radius,
                "feather": feather,
                "expand": expand,
                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                "new_layer": new_layer,
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

    def run_delete_fill_one_click(self, procedure, run_mode, image, drawables, config, run_data):
        success, msg = self.execute_delete_fill(
            image, drawables,
            sampling_radius=16,
            feather=2.0,
            expand=2,
            new_layer=False,
            deselect=True
        )
        if not success:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-dfs"), msg, 0)
            )
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_delete_fill_options(self, procedure, run_mode, image, drawables, config, run_data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            gi.require_version('GimpUi', '3.0')
            from gi.repository import GimpUi
            GimpUi.init(PROC_NAME_OPTIONS)
            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        sampling_radius = config.get_property("sampling-radius")
        feather = config.get_property("feather")
        expand = config.get_property("expand")
        new_layer = config.get_property("new-layer")
        deselect = config.get_property("deselect")

        success, msg = self.execute_delete_fill(
            image, drawables,
            sampling_radius=sampling_radius,
            feather=feather,
            expand=expand,
            new_layer=new_layer,
            deselect=deselect
        )
        if not success:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-dfs"), msg, 0)
            )
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(DeleteFillSelectionPlugin.__gtype__, sys.argv)
