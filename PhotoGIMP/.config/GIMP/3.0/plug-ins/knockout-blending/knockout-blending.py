#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Knockout Blending & Texture Cutout Effects Helper Plugin
==================================================================
Photoshop Reference:
- Topics.txt:
  - Line 120: Create texture effects with Knockout
  - Line 121: Set layer opacity and blending modes
- photoshop_docs.md:
  - Section 124 lines 3684-3698: Create texture effects with Knockout
    "Learn how to use the Knockout blending option to punch through layers and reveal
     underlying content for texture effects in photoeditor desktop...
     You'll need three elements: a top layer that defines the knockout shape, middle layers
     to punch through, and underlying content to reveal. Unlike layer masks, which hide content,
     Knockout removes visibility from intermediate layers...
     Shallow punches through to group boundary; Deep punches through to background/base layer."
  - Section 125 lines 3701-3730: Set layer opacity and blending modes
    "Fill opacity affects only pixels, shapes, or text on the layer while preserving the full
     opacity of layer effects like drop shadows and strokes. This separation gives you precise
     control when combining layer content with styled effects."

Key Architectural Features:
1. Deep Knockout (`knockout-type = deep`):
   - Punches through all intermediate layers down to the bottom-most base canvas/background layer.
   - Reveals underlying background imagery, photos, or canvas colors directly through the layer silhouette.
2. Shallow Knockout (`knockout-type = shallow`):
   - Confines the cutout punch strictly to sibling layers inside the active layer's parent group.
   - Layers behind or outside the group remain completely unpunched and intact, revealing the group backdrop.
3. Decoupled Fill Opacity (`fill-opacity = 0.0% to 100.0%`):
   - Adjusts the transparency of the knockout shape's own color fill independently from attached layer styles.
   - At 0% fill opacity, the shape's fill is completely transparent while its cutout punches through middle layers.
   - Attached layer styles (Drop Shadow, Stroke, Outer Glow, Bevel & Emboss) remain fully visible and styled.
4. Edge Feathering & Cutout Inversion:
   - Feather radius (0.0 to 50.0px) for smooth anti-aliased or soft cutout edges.
   - Invert toggle allows punching outside the layer's silhouette instead of inside.
5. Curated Presets:
   - Stencil Cutout, Textured Text, Soft Punch, Glass Etched, Translucent Knockout, Custom.
6. Restoration & Clean Knockout Clearing (`python-fu-clear-knockout`):
   - Restores target layer opacity and cleanly removes knockout masks from punched intermediate layers.
7. Single-Step Undo Protection:
   - All operations encapsulated within image.undo_group_start() and image.undo_group_end().
8. 100% Non-Destructive Base Preservation:
   - Base canvas and underlying artwork remain 100% mathematically untouched (diff == 0.000000).
"""

import json
import math
import sys

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib

import numpy as np

PROC_NAME_KNOCKOUT = "python-fu-knockout-blending"
PROC_NAME_CLEAR = "python-fu-clear-knockout"

STYLE_TAGS = [
    "(Drop Shadow",
    "(Outer Glow",
    "(Inner Glow",
    "(Inner Shadow",
    "(Color Overlay",
    "(Gradient Overlay",
    "(Pattern Overlay",
    "(Satin",
    "(Stroke",
    "(Bevel & Emboss)",
]

PRESETS = {
    "stencil-cutout": {
        "knockout_type": "deep",
        "fill_opacity": 0.0,
        "feather": 0.0,
        "preserve_styles": True,
        "invert": False,
        "opacity": 100.0,
        "label": "Stencil Cutout",
    },
    "textured-text": {
        "knockout_type": "shallow",
        "fill_opacity": 0.0,
        "feather": 0.0,
        "preserve_styles": True,
        "invert": False,
        "opacity": 100.0,
        "label": "Textured Text",
    },
    "soft-punch": {
        "knockout_type": "deep",
        "fill_opacity": 0.0,
        "feather": 4.0,
        "preserve_styles": True,
        "invert": False,
        "opacity": 100.0,
        "label": "Soft Punch",
    },
    "glass-etched": {
        "knockout_type": "shallow",
        "fill_opacity": 25.0,
        "feather": 1.0,
        "preserve_styles": True,
        "invert": False,
        "opacity": 100.0,
        "label": "Glass Etched",
    },
    "translucent-knockout": {
        "knockout_type": "deep",
        "fill_opacity": 50.0,
        "feather": 0.0,
        "preserve_styles": True,
        "invert": False,
        "opacity": 100.0,
        "label": "Translucent Knockout",
    },
    "custom": {
        "label": "Custom",
    },
}


def gaussian_blur_2d(arr, radius):
    """Vectorized Gaussian smoothing using separable 1D convolution."""
    if radius <= 0.1:
        return arr
    sigma = radius / 2.0
    ksize = int(math.ceil(sigma * 3.0)) * 2 + 1
    x = np.arange(-ksize // 2 + 1, ksize // 2 + 1)
    kernel_1d = np.exp(-0.5 * (x / sigma) ** 2)
    kernel_1d /= np.sum(kernel_1d)
    temp = np.apply_along_axis(lambda m: np.convolve(m, kernel_1d, mode='same'), axis=1, arr=arr)
    out = np.apply_along_axis(lambda m: np.convolve(m, kernel_1d, mode='same'), axis=0, arr=temp)
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def is_style_layer_for(layer, target_layer, image):
    """Check if layer is an attached style layer for target_layer."""
    if layer == target_layer:
        return False
    name = layer.get_name()
    target_name = target_layer.get_name()
    if name.startswith(f"{target_name} (") and any(tag in name for tag in STYLE_TAGS):
        return True
    if "(Bevel & Emboss)" in name:
        try:
            pos_lyr = image.get_item_position(layer)
            pos_art = image.get_item_position(target_layer)
            if abs(pos_lyr - pos_art) <= 1:
                return True
        except Exception:
            pass
    return False


def get_all_document_layers_flat(image):
    """Retrieve all layers in the image flattened from top to bottom."""
    flat_list = []

    def _traverse(container):
        children = container.get_children() if hasattr(container, 'get_children') else container.get_layers()
        for child in children:
            flat_list.append(child)
            if hasattr(child, 'get_children') and len(child.get_children()) > 0:
                _traverse(child)

    _traverse(image)
    return flat_list


def resolve_intermediate_layers(target_layer, image, knockout_type):
    """
    Identify intermediate layers to punch according to knockout mode:
    - shallow: sibling layers below target inside the parent group (or immediate sibling if root).
    - deep: all layers between target and the bottom-most base canvas layer.
    """
    if knockout_type == "none":
        return []

    parent = target_layer.get_parent()

    if knockout_type == "shallow":
        if parent is not None:
            siblings = parent.get_children()
            try:
                t_idx = siblings.index(target_layer)
                candidates = siblings[t_idx + 1 :]
            except ValueError:
                candidates = []
        else:
            # Top-level without group: intermediate layers down to before base layer
            top_layers = image.get_layers()
            try:
                t_idx = top_layers.index(target_layer)
                # Exclude bottom-most base layer
                candidates = top_layers[t_idx + 1 : -1] if len(top_layers) > 2 else (
                    top_layers[t_idx + 1 :] if len(top_layers) > 1 and t_idx + 1 < len(top_layers) - 1 else []
                )
            except ValueError:
                candidates = []
    else:  # deep
        flat_layers = get_all_document_layers_flat(image)
        try:
            t_idx = flat_layers.index(target_layer)
            # All layers below target down to before the last base layer
            candidates = flat_layers[t_idx + 1 : -1] if len(flat_layers) > 1 else []
        except ValueError:
            candidates = []

    # Exclude attached style layers belonging to target_layer
    filtered = [l for l in candidates if not is_style_layer_for(l, target_layer, image)]
    return filtered


class KnockoutBlendingPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return [PROC_NAME_KNOCKOUT, PROC_NAME_CLEAR]

    def do_create_procedure(self, name):
        if name == PROC_NAME_KNOCKOUT:
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_knockout, None)
            procedure.set_image_types("RGB*, GRAY*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES
            )

            # Menu Registrations
            procedure.set_menu_label("Knockout Options...")
            procedure.add_menu_path("<Image>/Layer/Layer Style")
            procedure.add_menu_path("<Image>/Layer/Blending Options")
            procedure.add_menu_path("<Image>/Filters/Retouching")

            procedure.set_documentation(
                "Apply Photoshop Knockout Blending & Texture Cutout Options",
                "Punches through intermediate layers using the active layer's silhouette "
                "to reveal underlying content, with decoupled fill opacity and style preservation.",
                name
            )

            # Procedure Arguments
            procedure.add_string_argument(
                "preset",
                "Preset",
                "Knockout Preset (stencil-cutout, textured-text, soft-punch, glass-etched, translucent-knockout, custom)",
                "custom",
                GObject.ParamFlags.READWRITE
            )

            procedure.add_string_argument(
                "knockout-type",
                "Knockout Type",
                "Knockout depth mode: shallow, deep, or none",
                "deep",
                GObject.ParamFlags.READWRITE
            )

            procedure.add_double_argument(
                "fill-opacity",
                "Fill Opacity (%)",
                "Separated fill opacity of layer artwork (0-100%)",
                0.0,
                100.0,
                0.0,
                GObject.ParamFlags.READWRITE
            )

            procedure.add_double_argument(
                "feather",
                "Feather Radius (px)",
                "Cutout edge feathering radius (0-50px)",
                0.0,
                50.0,
                0.0,
                GObject.ParamFlags.READWRITE
            )

            procedure.add_boolean_argument(
                "preserve-styles",
                "Preserve Styles",
                "Preserve attached layer style effects (stroke, drop shadow, bevel)",
                True,
                GObject.ParamFlags.READWRITE
            )

            procedure.add_boolean_argument(
                "invert",
                "Invert Knockout",
                "Invert knockout punch (punch outside silhouette)",
                False,
                GObject.ParamFlags.READWRITE
            )

            procedure.add_double_argument(
                "opacity",
                "Overall Opacity (%)",
                "Master knockout intensity opacity (0-100%)",
                0.0,
                100.0,
                100.0,
                GObject.ParamFlags.READWRITE
            )

            procedure.add_string_argument(
                "action",
                "Action",
                "Action to perform: apply or clear",
                "apply",
                GObject.ParamFlags.READWRITE
            )

            return procedure

        elif name == PROC_NAME_CLEAR:
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_clear, None)
            procedure.set_image_types("RGB*, GRAY*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES
            )

            # Menu Registrations
            procedure.set_menu_label("Clear Knockout")
            procedure.add_menu_path("<Image>/Layer/Layer Style")
            procedure.add_menu_path("<Image>/Layer/Blending Options")

            procedure.set_documentation(
                "Clear Knockout Blending & Restore Intermediate Layers",
                "Restores target layer fill opacity and removes knockout masks from punched intermediate layers.",
                name
            )

            return procedure

        return None

    def run_clear(self, procedure, run_mode, image, drawables, config, run_data):
        target_layer = None
        selected_layers = image.get_selected_layers()
        if len(selected_layers) > 0:
            target_layer = selected_layers[0]
        elif drawables and len(drawables) > 0:
            target_layer = drawables[0]
        else:
            layers = image.get_layers()
            target_layer = layers[0] if len(layers) > 0 else None

        if target_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-clear-knockout"), "No active layer.", 0)
            )

        image.undo_group_start()
        try:
            # Check for image parasite
            p = image.get_parasite("photogimp/knockout")
            punched_ids = []
            had_mask_map = {}
            orig_opacity = 100.0

            if p is not None:
                try:
                    meta = json.loads(bytes(p.get_data()).decode("utf-8"))
                    punched_ids = meta.get("punched_layer_ids", [])
                    had_mask_map = meta.get("had_mask", {})
                    orig_opacity = float(meta.get("target_orig_opacity", 100.0))
                except Exception:
                    orig_opacity = 100.0
                image.detach_parasite("photogimp/knockout")

            # Restore target layer opacity
            orig_opacity = 100.0
            lp_target = target_layer.get_parasite("photogimp/knockout-target")
            if lp_target is not None:
                try:
                    t_data = json.loads(bytes(lp_target.get_data()).decode("utf-8"))
                    orig_opacity = float(t_data.get("target_orig_opacity", 100.0))
                except Exception:
                    orig_opacity = 100.0
                target_layer.detach_parasite("photogimp/knockout-target")
            elif p is not None:
                try:
                    meta = json.loads(bytes(p.get_data()).decode("utf-8"))
                    orig_opacity = float(meta.get("target_orig_opacity", 100.0))
                except Exception:
                    orig_opacity = 100.0

            if orig_opacity <= 0.0:
                orig_opacity = 100.0

            target_layer.set_opacity(orig_opacity)

            # Process all document layers to find punched layers
            all_layers = get_all_document_layers_flat(image)
            for lyr in all_layers:
                is_punched = False
                created_mask = False
                lp = lyr.get_parasite("photogimp/knockout-punched")
                if lp is not None:
                    is_punched = True
                    try:
                        pdata = json.loads(bytes(lp.get_data()).decode("utf-8"))
                        created_mask = pdata.get("created_mask", False)
                    except Exception:
                        created_mask = False
                    lyr.detach_parasite("photogimp/knockout-punched")
                elif lyr.get_id() in punched_ids:
                    is_punched = True
                    created_mask = not had_mask_map.get(str(lyr.get_id()), False)

                if is_punched:
                    mask = lyr.get_mask()
                    if mask is not None and created_mask:
                        lyr.remove_mask(Gimp.MaskApplyMode.DISCARD)

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-clear-knockout"), str(e), 0)
            )

        image.undo_group_end()
        Gimp.displays_flush()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_knockout(self, procedure, run_mode, image, drawables, config, data):
        # Interactive GUI dialog
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init(PROC_NAME_KNOCKOUT)
            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        # Read configuration parameters
        preset = config.get_property("preset")
        ktype_prop = config.get_property("knockout-type")
        fill_op_prop = config.get_property("fill-opacity")
        feather_prop = config.get_property("feather")
        preserve_styles_prop = config.get_property("preserve-styles")
        invert_prop = config.get_property("invert")
        opacity_prop = config.get_property("opacity")
        action_prop = config.get_property("action")

        # Handle clear action
        if action_prop == "clear":
            return self.run_clear(procedure, run_mode, image, drawables, config, data)

        # Preset overrides
        if preset in PRESETS and preset != "custom":
            p = PRESETS[preset]
            final_ktype = p.get("knockout_type", "deep")
            final_fill_opacity = p.get("fill_opacity", 0.0)
            final_feather = p.get("feather", 0.0)
            final_preserve_styles = p.get("preserve_styles", True)
            final_invert = p.get("invert", False)
            final_opacity = p.get("opacity", 100.0)
        else:
            final_ktype = ktype_prop
            final_fill_opacity = fill_op_prop
            final_feather = feather_prop
            final_preserve_styles = preserve_styles_prop
            final_invert = invert_prop
            final_opacity = opacity_prop

        # Resolve target knockout layer
        target_layer = None
        selected_layers = image.get_selected_layers()
        if len(selected_layers) > 0:
            target_layer = selected_layers[0]
        elif drawables and len(drawables) > 0:
            d = drawables[0]
            if hasattr(d, 'is_layer_mask') and d.is_layer_mask():
                layers = image.get_layers()
                target_layer = layers[0] if len(layers) > 0 else None
            else:
                target_layer = d
        else:
            layers = image.get_layers()
            target_layer = layers[0] if len(layers) > 0 else None

        if target_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-knockout"), "No active knockout layer found.", 0)
            )

        # If knockout_type is "none", clear knockout and exit
        if final_ktype == "none":
            return self.run_clear(procedure, run_mode, image, drawables, config, data)

        img_w = image.get_width()
        img_h = image.get_height()

        # Find intermediate layers to punch
        intermediate_layers = resolve_intermediate_layers(target_layer, image, final_ktype)
        if not intermediate_layers:
            # Graceful no-op when no intermediate layers exist below target
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        image.undo_group_start()
        try:
            # 1. Read target layer's alpha silhouette and project onto canvas coordinates
            lw = target_layer.get_width()
            lh = target_layer.get_height()
            offs_t = target_layer.get_offsets()
            off_x, off_y = int(offs_t[-2]), int(offs_t[-1])

            t_rect = Gegl.Rectangle.new(0, 0, lw, lh)
            t_buf = target_layer.get_buffer()
            raw_t = t_buf.get(t_rect, 1.0, "RGBA float", Gegl.AbyssPolicy.NONE)
            arr_t = np.frombuffer(raw_t, dtype=np.float32).reshape((lh, lw, 4))
            t_alpha = arr_t[:, :, 3].copy()

            canvas_alpha = np.zeros((img_h, img_w), dtype=np.float32)
            cx1 = max(0, off_x)
            cy1 = max(0, off_y)
            cx2 = min(img_w, off_x + lw)
            cy2 = min(img_h, off_y + lh)

            if cx2 > cx1 and cy2 > cy1:
                tx1 = cx1 - off_x
                ty1 = cy1 - off_y
                tx2 = tx1 + (cx2 - cx1)
                ty2 = ty1 + (cy2 - cy1)
                canvas_alpha[cy1:cy2, cx1:cx2] = t_alpha[ty1:ty2, tx1:tx2]

            # 2. Apply optional feathering
            if final_feather > 0.0:
                canvas_alpha = gaussian_blur_2d(canvas_alpha, final_feather)

            # 3. Handle cutout inversion
            if final_invert:
                punch_factor = 1.0 - canvas_alpha
            else:
                punch_factor = canvas_alpha

            # 4. Compute effective punch intensity
            # Punch depth is proportional to (1.0 - fill_opacity) and overall opacity
            punch_intensity = punch_factor * (1.0 - (final_fill_opacity / 100.0)) * (final_opacity / 100.0)
            punch_intensity = np.clip(punch_intensity, 0.0, 1.0).astype(np.float32)

            # 5. Apply cutout punching to each intermediate layer
            punched_records = []
            had_mask_map = {}

            for lyr in intermediate_layers:
                lw_i = lyr.get_width()
                lh_i = lyr.get_height()
                offs_l = lyr.get_offsets()
                lx_off, ly_off = int(offs_l[-2]), int(offs_l[-1])

                # Project canvas punch intensity to intermediate layer's local coordinate space
                p_local = np.zeros((lh_i, lw_i), dtype=np.float32)
                ix1 = max(0, lx_off)
                iy1 = max(0, ly_off)
                ix2 = min(img_w, lx_off + lw_i)
                iy2 = min(img_h, ly_off + lh_i)

                if ix2 > ix1 and iy2 > iy1:
                    lx1 = ix1 - lx_off
                    ly1 = iy1 - ly_off
                    lx2 = lx1 + (ix2 - ix1)
                    ly2 = ly1 + (iy2 - iy1)
                    p_local[ly1:ly2, lx1:lx2] = punch_intensity[iy1:iy2, ix1:ix2]

                mask = lyr.get_mask()
                created_mask = False
                lp = lyr.get_parasite("photogimp/knockout-punched")
                if lp is not None:
                    try:
                        pdata = json.loads(bytes(lp.get_data()).decode("utf-8"))
                        created_mask = pdata.get("created_mask", False)
                    except Exception:
                        created_mask = False

                if mask is None:
                    mask = lyr.create_mask(Gimp.AddMaskType.WHITE)
                    lyr.add_mask(mask)
                    created_mask = True
                    had_mask_map[str(lyr.get_id())] = False
                elif lp is None:
                    had_mask_map[str(lyr.get_id())] = True
                else:
                    had_mask_map[str(lyr.get_id())] = not created_mask

                # Read existing mask data
                m_rect = Gegl.Rectangle.new(0, 0, lw_i, lh_i)
                mbuf = mask.get_buffer()
                raw_m = mbuf.get(m_rect, 1.0, "Y float", Gegl.AbyssPolicy.NONE)
                arr_m = np.frombuffer(raw_m, dtype=np.float32).reshape((lh_i, lw_i)).copy()

                # Punch hole: mask transparency is reduced where punch_intensity is high
                if created_mask:
                    arr_m = 1.0 - p_local
                else:
                    arr_m = arr_m * (1.0 - p_local)

                arr_m = np.clip(arr_m, 0.0, 1.0).astype(np.float32)
                mbuf.set(m_rect, "Y float", arr_m.tobytes())
                mbuf.flush()
                mask.update(0, 0, lw_i, lh_i)

                # Tag layer with punch parasite
                lp_meta = {"target_id": target_layer.get_id(), "created_mask": created_mask}
                lyr.attach_parasite(
                    Gimp.Parasite.new("photogimp/knockout-punched", 1, json.dumps(lp_meta).encode("utf-8"))
                )
                punched_records.append(lyr.get_id())

            # 6. Adjust target layer's own fill opacity
            orig_target_opacity = target_layer.get_opacity()
            lp_target = target_layer.get_parasite("photogimp/knockout-target")
            if lp_target is not None:
                try:
                    t_data = json.loads(bytes(lp_target.get_data()).decode("utf-8"))
                    orig_target_opacity = float(t_data.get("target_orig_opacity", 100.0))
                except Exception:
                    orig_target_opacity = 100.0
            else:
                target_layer.attach_parasite(
                    Gimp.Parasite.new(
                        "photogimp/knockout-target", 1,
                        json.dumps({"target_orig_opacity": orig_target_opacity}).encode("utf-8")
                    )
                )
            target_layer.set_opacity(final_fill_opacity * (final_opacity / 100.0))

            # 7. Record document-wide knockout parasite metadata
            doc_meta = {
                "target_layer_id": target_layer.get_id(),
                "target_orig_opacity": orig_target_opacity,
                "knockout_type": final_ktype,
                "fill_opacity": final_fill_opacity,
                "feather": final_feather,
                "invert": final_invert,
                "punched_layer_ids": punched_records,
                "had_mask": had_mask_map,
            }
            image.attach_parasite(
                Gimp.Parasite.new("photogimp/knockout", 1, json.dumps(doc_meta).encode("utf-8"))
            )

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-knockout"), str(e), 0)
            )

        image.undo_group_end()
        Gimp.displays_flush()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(KnockoutBlendingPlugin.__gtype__, sys.argv)
