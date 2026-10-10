#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Smart Filters & Non-Destructive Filter Effects Helper Plugin
======================================================================
Photoshop Reference:
- Topics.txt:
  - Line 454: "Smart filters - Sharpening overview"
  - Line 459: "Apply and manage Smart Filters"
- photoshop_docs.md:
  - Section 138 lines 4057-4066: Convert back to layers / discard smart filters or rasterize
  - Section 153 lines 4408-4434: "Filters applied to Smart Objects become Smart Filters, which
    remain editable and can be masked, adjusted, or removed without affecting the underlying image."
  - Section 413 lines 12047-12059: "When applied to a Smart Object, some filters become Smart
    Filters, letting you edit or remove them later without permanently changing your image."
  - Section 446 lines 13049-13056: "Smart filter: Converts the layer to a Smart Object and applies
    the filter non-destructively as a Smart Filter."

Key Architectural Features:
1. Smart Object Containerization (`python-fu-convert-for-smart-filters`):
   - Encapsulates layer into a non-destructive Smart Object group container.
   - Stores a pristine copy of original pixels in a hidden Source Content layer tagged with
     the parasite "photogimp/smart-source".
   - Active rendering layer tagged with "photogimp/smart-render".
   - Stores metadata in group parasite "photogimp/smart-object".
2. Non-Destructive Filter Passes (`python-fu-apply-smart-filter`):
   - Applies GEGL filter operations (Gaussian Blur, Smart Sharpen, High Pass, Vignette,
     Noise Reduction/Median Blur, Diffuse Glow/Bloom, Pixelize) from pristine source pixels.
   - Decoupled Filter Opacity (0% to 100%) and Filter Blend Modes (Normal, Multiply, Screen,
     Overlay, Soft Light, Luminance).
   - Automatically initializes Smart Filter Mask (Reveal All, Conceal All, or Selection).
3. Re-Editable Filter Stacks (`python-fu-edit-smart-filter`):
   - Re-renders filter passes directly from pristine source content without accumulating
     generation or compression loss.
   - Automatically preserves user's painted Smart Filter mask intact across adjustments.
4. Permanent Baking (`python-fu-rasterize-smart-filters`):
   - Bakes smart filter rendering and applied mask down to a standard raster layer, matching
     Photoshop's "Layer > Rasterize > Smart Object".
5. Complete Restoration (`python-fu-clear-smart-filters`):
   - Discards all smart filter layers and masks, cleanly restoring pristine original layer
     pixels 100% intact (diff == 0.000000).
"""

import json
import os
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


PROC_NAME_CONVERT = "python-fu-convert-for-smart-filters"
PROC_NAME_APPLY = "python-fu-apply-smart-filter"
PROC_NAME_EDIT = "python-fu-edit-smart-filter"
PROC_NAME_RASTERIZE = "python-fu-rasterize-smart-filters"
PROC_NAME_CLEAR = "python-fu-clear-smart-filters"

PARASITE_SMART_OBJ = "photogimp/smart-object"
PARASITE_SMART_SRC = "photogimp/smart-source"
PARASITE_SMART_RND = "photogimp/smart-render"


FILTER_PRESETS = {
    "soft-portrait-blur": {
        "label": "Soft Portrait Blur",
        "filter_type": "gaussian-blur",
        "radius": 4.0,
        "amount": 100.0,
        "opacity": 80.0,
        "blend_mode": "normal",
    },
    "dreamy-glow": {
        "label": "Dreamy Diffuse Glow",
        "filter_type": "diffuse-glow",
        "radius": 10.0,
        "amount": 75.0,
        "opacity": 80.0,
        "blend_mode": "screen",
    },
    "crisp-unsharp-sharpen": {
        "label": "Crisp Smart Sharpen",
        "filter_type": "smart-sharpen",
        "radius": 1.5,
        "amount": 150.0,
        "opacity": 100.0,
        "blend_mode": "normal",
    },
    "high-pass-texture": {
        "label": "High Pass Microcontrast",
        "filter_type": "high-pass",
        "radius": 3.0,
        "amount": 100.0,
        "opacity": 60.0,
        "blend_mode": "overlay",
    },
    "vintage-vignette": {
        "label": "Vintage Lens Vignette",
        "filter_type": "vignette",
        "radius": 1.2,
        "amount": 70.0,
        "opacity": 85.0,
        "blend_mode": "multiply",
    },
    "subtle-denoise": {
        "label": "Subtle Surface Denoise",
        "filter_type": "noise-reduction",
        "radius": 2.0,
        "amount": 50.0,
        "opacity": 90.0,
        "blend_mode": "normal",
    },
    "retro-pixel-art": {
        "label": "Retro Pixelize Mosaic",
        "filter_type": "pixelize",
        "radius": 8.0,
        "amount": 100.0,
        "opacity": 100.0,
        "blend_mode": "normal",
    },
    "custom": {
        "label": "Custom Filter",
        "filter_type": "gaussian-blur",
        "radius": 5.0,
        "amount": 100.0,
        "opacity": 100.0,
        "blend_mode": "normal",
    },
}

BLEND_MODES = {
    "normal": Gimp.LayerMode.NORMAL,
    "multiply": Gimp.LayerMode.MULTIPLY,
    "screen": Gimp.LayerMode.SCREEN,
    "overlay": Gimp.LayerMode.OVERLAY,
    "soft-light": Gimp.LayerMode.SOFTLIGHT,
    "luminance": Gimp.LayerMode.LUMINANCE,
}


def resolve_target_layer(image, drawables):
    """Resolve the active selected layer."""
    selected_layers = image.get_selected_layers()
    if len(selected_layers) > 0:
        return selected_layers[0]
    elif drawables and len(drawables) > 0:
        return drawables[0]
    layers = image.get_layers()
    return layers[0] if len(layers) > 0 else None


def resolve_smart_container(image, target_layer):
    """
    Locates the smart object container group, pristine source layer, and active render layer.
    Returns (group, source_layer, render_layer) or (None, None, None).
    """
    if target_layer is None:
        return None, None, None

    # Case 1: Target layer is the smart group container
    if hasattr(target_layer, 'get_children') and target_layer.get_parasite(PARASITE_SMART_OBJ) is not None:
        grp = target_layer
        children = grp.get_children()
        src = None
        rnd = None
        for c in children:
            if "(Smart Filter)" in c.get_name():
                rnd = c
            elif "(Source Content)" in c.get_name():
                src = c
            elif c.get_parasite(PARASITE_SMART_RND) is not None:
                rnd = c
            elif c.get_parasite(PARASITE_SMART_SRC) is not None:
                src = c
        if src is not None and rnd is not None:
            return grp, src, rnd

    # Case 2: Target layer is inside the smart group container
    parent = target_layer.get_parent()
    if parent is not None and parent.get_parasite(PARASITE_SMART_OBJ) is not None:
        children = parent.get_children()
        src = None
        rnd = None
        for c in children:
            if "(Smart Filter)" in c.get_name():
                rnd = c
            elif "(Source Content)" in c.get_name():
                src = c
            elif c.get_parasite(PARASITE_SMART_RND) is not None:
                rnd = c
            elif c.get_parasite(PARASITE_SMART_SRC) is not None:
                src = c
        if src is not None and rnd is not None:
            return parent, src, rnd

    # Case 3: Target layer has smart render or smart source parasite
    if target_layer.get_parasite(PARASITE_SMART_RND) is not None or target_layer.get_parasite(PARASITE_SMART_SRC) is not None:
        if parent is not None:
            return resolve_smart_container(image, parent)

    return None, None, None


def execute_convert_for_smart_filters(image, target_layer):
    """Converts a standard layer into a non-destructive Smart Object container."""
    # Check if already a smart container
    grp, src, rnd = resolve_smart_container(image, target_layer)
    if grp is not None:
        return grp, src, rnd

    parent = target_layer.get_parent()
    pos = image.get_item_position(target_layer)
    base_name = target_layer.get_name()

    # Create Smart Object Group
    grp = Gimp.GroupLayer.new(image, f"{base_name} (Smart Object)")
    image.insert_layer(grp, parent, pos)

    # Create Pristine Source Layer
    src = Gimp.Layer.new_from_drawable(target_layer, image)
    src.set_name(f"{base_name} (Source Content)")
    src.set_visible(False)
    for p in [PARASITE_SMART_RND, PARASITE_SMART_OBJ]:
        try:
            src.detach_parasite(p)
        except Exception:
            pass
    image.insert_layer(src, grp, 0)
    src.attach_parasite(Gimp.Parasite.new(PARASITE_SMART_SRC, 1, json.dumps({"base_name": base_name}).encode("utf-8")))

    # Create Render Layer
    rnd = Gimp.Layer.new_from_drawable(target_layer, image)
    rnd.set_name(f"{base_name} (Smart Filter)")
    rnd.set_visible(True)
    for p in [PARASITE_SMART_SRC, PARASITE_SMART_OBJ]:
        try:
            rnd.detach_parasite(p)
        except Exception:
            pass
    image.insert_layer(rnd, grp, 0)
    rnd.attach_parasite(Gimp.Parasite.new(PARASITE_SMART_RND, 1, json.dumps({"base_name": base_name}).encode("utf-8")))

    # Attach Smart Filter Mask (Reveal All / White by default)
    mask = rnd.create_mask(Gimp.AddMaskType.WHITE)
    rnd.add_mask(mask)

    # Attach Container Metadata Parasite
    meta = {
        "base_name": base_name,
        "source_id": src.get_id(),
        "render_id": rnd.get_id(),
        "filter_type": "none",
        "radius": 0.0,
        "amount": 100.0,
        "opacity": 100.0,
        "blend_mode": "normal",
        "preset": "custom",
    }
    grp.attach_parasite(Gimp.Parasite.new(PARASITE_SMART_OBJ, 1, json.dumps(meta).encode("utf-8")))

    # Remove original layer
    image.remove_layer(target_layer)
    image.set_selected_layers([rnd])

    return grp, src, rnd


def render_smart_filter_effect(image, src_layer, rnd_layer, filter_type, radius, amount, opacity, blend_mode):
    """
    Copies pristine pixels from src_layer to rnd_layer and applies the GEGL filter operation.
    Preserves any existing layer mask attached to rnd_layer.
    """
    lw = src_layer.get_width()
    lh = src_layer.get_height()
    rect = Gegl.Rectangle.new(0, 0, lw, lh)

    # 1. Reset render layer buffer with pristine original source pixels
    src_buf = src_layer.get_buffer()
    rnd_buf = rnd_layer.get_buffer()
    raw_pixels = src_buf.get(rect, 1.0, "RGBA float", Gegl.AbyssPolicy.NONE)
    rnd_buf.set(rect, "RGBA float", raw_pixels)
    rnd_buf.flush()

    # 2. Apply requested GEGL filter
    if filter_type == "gaussian-blur":
        filt = Gimp.DrawableFilter.new(rnd_layer, "gegl:gaussian-blur", "")
        cfg = filt.get_config()
        r = max(0.1, float(radius))
        cfg.set_property("std-dev-x", r)
        cfg.set_property("std-dev-y", r)
        rnd_layer.append_filter(filt)
        rnd_layer.merge_filters()

    elif filter_type == "smart-sharpen":
        filt = Gimp.DrawableFilter.new(rnd_layer, "gegl:unsharp-mask", "")
        cfg = filt.get_config()
        r = max(0.1, float(radius))
        scale = (float(amount) / 100.0) * 1.5
        cfg.set_property("std-dev", r)
        cfg.set_property("scale", scale)
        cfg.set_property("threshold", 0.005)
        rnd_layer.append_filter(filt)
        rnd_layer.merge_filters()

    elif filter_type == "high-pass":
        filt = Gimp.DrawableFilter.new(rnd_layer, "gegl:high-pass", "")
        cfg = filt.get_config()
        r = max(0.1, float(radius))
        contrast = max(0.1, float(amount) / 100.0)
        cfg.set_property("std-dev", r)
        cfg.set_property("contrast", contrast)
        rnd_layer.append_filter(filt)
        rnd_layer.merge_filters()

    elif filter_type == "vignette":
        filt = Gimp.DrawableFilter.new(rnd_layer, "gegl:vignette", "")
        cfg = filt.get_config()
        r = max(0.1, float(radius) / 5.0)
        soft = max(0.01, float(amount) / 100.0)
        cfg.set_property("radius", r)
        cfg.set_property("softness", soft)
        rnd_layer.append_filter(filt)
        rnd_layer.merge_filters()

    elif filter_type == "noise-reduction" or filter_type == "median-blur":
        filt = Gimp.DrawableFilter.new(rnd_layer, "gegl:median-blur", "")
        cfg = filt.get_config()
        r = max(1, int(radius))
        cfg.set_property("radius", r)
        rnd_layer.append_filter(filt)
        rnd_layer.merge_filters()

    elif filter_type == "diffuse-glow":
        filt = Gimp.DrawableFilter.new(rnd_layer, "gegl:bloom", "")
        cfg = filt.get_config()
        r = max(0.5, float(radius))
        strength = max(0.1, float(amount) / 100.0)
        cfg.set_property("radius", r)
        cfg.set_property("strength", strength)
        cfg.set_property("threshold", 0.4)
        rnd_layer.append_filter(filt)
        rnd_layer.merge_filters()

    elif filter_type == "pixelize":
        filt = Gimp.DrawableFilter.new(rnd_layer, "gegl:pixelize", "")
        cfg = filt.get_config()
        sz = max(2, int(radius))
        cfg.set_property("size-x", sz)
        cfg.set_property("size-y", sz)
        rnd_layer.append_filter(filt)
        rnd_layer.merge_filters()

    # 3. Apply Opacity and Layer Mode
    rnd_layer.set_opacity(max(0.0, min(100.0, float(opacity))))
    gmode = BLEND_MODES.get(blend_mode.lower(), Gimp.LayerMode.NORMAL)
    rnd_layer.set_mode(gmode)
    Gimp.displays_flush()


class SmartFiltersPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return [
            PROC_NAME_CONVERT,
            PROC_NAME_APPLY,
            PROC_NAME_EDIT,
            PROC_NAME_RASTERIZE,
            PROC_NAME_CLEAR,
        ]

    def do_create_procedure(self, name):
        if name == PROC_NAME_CONVERT:
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_convert, None)
            procedure.set_image_types("RGB*, GRAY*")
            procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE | Gimp.ProcedureSensitivityMask.DRAWABLES)
            procedure.set_menu_label("Convert for Smart Filters")
            procedure.add_menu_path("<Image>/Filters/Smart Filters")
            procedure.add_menu_path("<Image>/Layer/Smart Objects")
            procedure.set_documentation(
                "Convert Layer for Smart Filters",
                "Encapsulates active layer into a non-destructive Smart Object container.",
                name
            )
            return procedure

        elif name == PROC_NAME_APPLY:
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_apply, None)
            procedure.set_image_types("RGB*, GRAY*")
            procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE | Gimp.ProcedureSensitivityMask.DRAWABLES)
            procedure.set_menu_label("Apply Smart Filter...")
            procedure.add_menu_path("<Image>/Filters/Smart Filters")
            procedure.set_documentation(
                "Apply Non-Destructive Smart Filter",
                "Applies a re-editable filter effect with attached Smart Filter mask.",
                name
            )

            # Properties
            procedure.add_string_argument("preset", "Preset", "Preset name", "custom", GObject.ParamFlags.READWRITE)
            procedure.add_string_argument("filter-type", "Filter Type", "Type of filter to apply", "gaussian-blur", GObject.ParamFlags.READWRITE)
            procedure.add_double_argument("radius", "Radius / Size", "Filter radius or element size", 0.1, 200.0, 5.0, GObject.ParamFlags.READWRITE)
            procedure.add_double_argument("amount", "Amount / Strength", "Filter strength percentage", 0.0, 500.0, 100.0, GObject.ParamFlags.READWRITE)
            procedure.add_double_argument("opacity", "Filter Opacity", "Filter layer opacity percentage", 0.0, 100.0, 100.0, GObject.ParamFlags.READWRITE)
            procedure.add_string_argument("blend-mode", "Blend Mode", "Layer blend mode", "normal", GObject.ParamFlags.READWRITE)
            procedure.add_string_argument("mask-type", "Mask Initialization", "Filter mask initialization type", "reveal-all", GObject.ParamFlags.READWRITE)
            return procedure

        elif name == PROC_NAME_EDIT:
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_edit, None)
            procedure.set_image_types("RGB*, GRAY*")
            procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE | Gimp.ProcedureSensitivityMask.DRAWABLES)
            procedure.set_menu_label("Edit Smart Filter...")
            procedure.add_menu_path("<Image>/Filters/Smart Filters")
            procedure.set_documentation(
                "Edit Smart Filter Settings",
                "Re-adjusts filter parameters, re-rendering cleanly from pristine source pixels.",
                name
            )

            procedure.add_string_argument("preset", "Preset", "Preset name", "custom", GObject.ParamFlags.READWRITE)
            procedure.add_string_argument("filter-type", "Filter Type", "Type of filter to apply", "gaussian-blur", GObject.ParamFlags.READWRITE)
            procedure.add_double_argument("radius", "Radius / Size", "Filter radius or element size", 0.1, 200.0, 5.0, GObject.ParamFlags.READWRITE)
            procedure.add_double_argument("amount", "Amount / Strength", "Filter strength percentage", 0.0, 500.0, 100.0, GObject.ParamFlags.READWRITE)
            procedure.add_double_argument("opacity", "Filter Opacity", "Filter layer opacity percentage", 0.0, 100.0, 100.0, GObject.ParamFlags.READWRITE)
            procedure.add_string_argument("blend-mode", "Blend Mode", "Layer blend mode", "normal", GObject.ParamFlags.READWRITE)
            return procedure

        elif name == PROC_NAME_RASTERIZE:
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_rasterize, None)
            procedure.set_image_types("RGB*, GRAY*")
            procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE | Gimp.ProcedureSensitivityMask.DRAWABLES)
            procedure.set_menu_label("Rasterize Smart Filters")
            procedure.add_menu_path("<Image>/Filters/Smart Filters")
            procedure.add_menu_path("<Image>/Layer/Rasterize")
            procedure.set_documentation(
                "Rasterize Smart Filters",
                "Permanently bakes smart filters and mask into a standard raster layer.",
                name
            )
            return procedure

        elif name == PROC_NAME_CLEAR:
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_clear, None)
            procedure.set_image_types("RGB*, GRAY*")
            procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE | Gimp.ProcedureSensitivityMask.DRAWABLES)
            procedure.set_menu_label("Clear Smart Filters")
            procedure.add_menu_path("<Image>/Filters/Smart Filters")
            procedure.set_documentation(
                "Clear Smart Filters",
                "Removes smart filters and restores pristine source layer untouched.",
                name
            )
            return procedure

        return None

    def run_convert(self, procedure, run_mode, image, drawables, config, data):
        target_layer = resolve_target_layer(image, drawables)
        if target_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-smart-filters"), "No active layer.", 0)
            )

        image.undo_group_start()
        try:
            execute_convert_for_smart_filters(image, target_layer)
        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-smart-filters"), str(e), 0)
            )

        image.undo_group_end()
        Gimp.displays_flush()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_apply(self, procedure, run_mode, image, drawables, config, data):
        target_layer = resolve_target_layer(image, drawables)
        if target_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-smart-filters"), "No active layer.", 0)
            )

        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init(PROC_NAME_APPLY)
            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        preset = config.get_property("preset") or "custom"
        filter_type = config.get_property("filter-type") or "gaussian-blur"
        radius = config.get_property("radius")
        amount = config.get_property("amount")
        opacity = config.get_property("opacity")
        blend_mode = config.get_property("blend-mode") or "normal"
        mask_type = config.get_property("mask-type") or "reveal-all"

        if preset in FILTER_PRESETS and preset != "custom":
            p = FILTER_PRESETS[preset]
            filter_type = p.get("filter_type", filter_type)
            radius = p.get("radius", radius)
            amount = p.get("amount", amount)
            opacity = p.get("opacity", opacity)
            blend_mode = p.get("blend_mode", blend_mode)

        image.undo_group_start()
        try:
            grp, src, rnd = resolve_smart_container(image, target_layer)
            if grp is None:
                grp, src, rnd = execute_convert_for_smart_filters(image, target_layer)

            # Mask initialization if not already present
            if rnd.get_mask() is None:
                if mask_type == "conceal-all":
                    mask = rnd.create_mask(Gimp.AddMaskType.BLACK)
                elif mask_type == "from-selection":
                    if not Gimp.Selection.is_empty(image):
                        mask = rnd.create_mask(Gimp.AddMaskType.SELECTION)
                    else:
                        mask = rnd.create_mask(Gimp.AddMaskType.WHITE)
                else:  # reveal-all
                    mask = rnd.create_mask(Gimp.AddMaskType.WHITE)
                rnd.add_mask(mask)

            # Render filter effect from pristine source
            render_smart_filter_effect(image, src, rnd, filter_type, radius, amount, opacity, blend_mode)

            # Update container metadata
            p = grp.get_parasite(PARASITE_SMART_OBJ)
            base_name = grp.get_name().replace(" (Smart Object)", "")
            meta = {
                "base_name": base_name,
                "source_id": src.get_id(),
                "render_id": rnd.get_id(),
                "filter_type": filter_type,
                "radius": radius,
                "amount": amount,
                "opacity": opacity,
                "blend_mode": blend_mode,
                "preset": preset,
            }
            grp.attach_parasite(Gimp.Parasite.new(PARASITE_SMART_OBJ, 1, json.dumps(meta).encode("utf-8")))

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-smart-filters"), str(e), 0)
            )

        image.undo_group_end()
        Gimp.displays_flush()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_edit(self, procedure, run_mode, image, drawables, config, data):
        target_layer = resolve_target_layer(image, drawables)
        if target_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-smart-filters"), "No active layer.", 0)
            )

        grp, src, rnd = resolve_smart_container(image, target_layer)
        if grp is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-smart-filters"), "Selected layer is not a Smart Object.", 0)
            )

        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init(PROC_NAME_EDIT)
            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        preset = config.get_property("preset") or "custom"
        filter_type = config.get_property("filter-type") or "gaussian-blur"
        radius = config.get_property("radius")
        amount = config.get_property("amount")
        opacity = config.get_property("opacity")
        blend_mode = config.get_property("blend-mode") or "normal"

        if preset in FILTER_PRESETS and preset != "custom":
            p = FILTER_PRESETS[preset]
            filter_type = p.get("filter_type", filter_type)
            radius = p.get("radius", radius)
            amount = p.get("amount", amount)
            opacity = p.get("opacity", opacity)
            blend_mode = p.get("blend_mode", blend_mode)

        image.undo_group_start()
        try:
            # Re-render from pristine source (existing mask preserved)
            render_smart_filter_effect(image, src, rnd, filter_type, radius, amount, opacity, blend_mode)

            # Update parasite
            base_name = grp.get_name().replace(" (Smart Object)", "")
            meta = {
                "base_name": base_name,
                "source_id": src.get_id(),
                "render_id": rnd.get_id(),
                "filter_type": filter_type,
                "radius": radius,
                "amount": amount,
                "opacity": opacity,
                "blend_mode": blend_mode,
                "preset": preset,
            }
            grp.attach_parasite(Gimp.Parasite.new(PARASITE_SMART_OBJ, 1, json.dumps(meta).encode("utf-8")))

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-smart-filters"), str(e), 0)
            )

        image.undo_group_end()
        Gimp.displays_flush()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_rasterize(self, procedure, run_mode, image, drawables, config, data):
        target_layer = resolve_target_layer(image, drawables)
        if target_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-smart-filters"), "No active layer.", 0)
            )

        grp, src, rnd = resolve_smart_container(image, target_layer)
        if grp is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-smart-filters"), "Selected layer is not a Smart Object.", 0)
            )

        image.undo_group_start()
        try:
            base_name = grp.get_name().replace(" (Smart Object)", "")
            parent = grp.get_parent()
            pos = image.get_item_position(grp)

            # If render layer has a mask, apply it
            m = rnd.get_mask()
            if m is not None:
                rnd.remove_mask(Gimp.MaskApplyMode.APPLY)

            # Duplicate render layer to top-level
            baked = Gimp.Layer.new_from_drawable(rnd, image)
            baked.set_name(base_name)
            baked.set_opacity(rnd.get_opacity())
            baked.set_mode(rnd.get_mode())
            for p in [PARASITE_SMART_SRC, PARASITE_SMART_RND, PARASITE_SMART_OBJ]:
                try:
                    baked.detach_parasite(p)
                except Exception:
                    pass
            image.insert_layer(baked, parent, pos)

            # Remove smart object group container
            image.remove_layer(grp)
            image.set_selected_layers([baked])

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-smart-filters"), str(e), 0)
            )

        image.undo_group_end()
        Gimp.displays_flush()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_clear(self, procedure, run_mode, image, drawables, config, data):
        target_layer = resolve_target_layer(image, drawables)
        if target_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-smart-filters"), "No active layer.", 0)
            )

        grp, src, rnd = resolve_smart_container(image, target_layer)
        if grp is None:
            # Graceful no-op if not a Smart Object
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        image.undo_group_start()
        try:
            base_name = grp.get_name().replace(" (Smart Object)", "")
            parent = grp.get_parent()
            pos = image.get_item_position(grp)

            # Restore pristine source layer to original position
            restored = Gimp.Layer.new_from_drawable(src, image)
            restored.set_name(base_name)
            restored.set_visible(True)
            restored.set_opacity(100.0)
            restored.set_mode(Gimp.LayerMode.NORMAL)
            for p in [PARASITE_SMART_SRC, PARASITE_SMART_RND, PARASITE_SMART_OBJ]:
                try:
                    restored.detach_parasite(p)
                except Exception:
                    pass
            image.insert_layer(restored, parent, pos)

            # Remove smart object container
            image.remove_layer(grp)
            image.set_selected_layers([restored])

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-smart-filters"), str(e), 0)
            )

        image.undo_group_end()
        Gimp.displays_flush()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(SmartFiltersPlugin.__gtype__, sys.argv)
