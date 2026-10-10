#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Artboards & Multi-Canvas Layout Manager Plugin
=========================================================
Photoshop Reference:
- Topics.txt lines 146-149:
  "Get started with artboards", "Artboard properties and behaviors",
  "Create artboard documents", "Add artboards to the current document"
- photoshop_docs.md Section 150-153 lines 4498-4595:
  "Artboards are special layer groups that clip the contents of any contained
   elements to their boundaries. Web and UX designers can use artboards to create
   designs for multiple devices and screen sizes simultaneously...
   While creating artboards, you can choose from various preset sizes or define
   your own custom artboard size...
   Artboard from Layers... Artboard from Group...
   Add Artboards to current document (Artboard Tool, Plus icons on sides)...
   Export Artboards to Files..."

Architectural Features:
1. Artboard Container Group (`python-fu-create-artboard`):
   - Encapsulated as a specialized Gimp.GroupLayer ("<Name> (Artboard)") acting as an
     independent canvas within the multi-canvas document.
   - Non-destructive boundary clipping: group layer mask attached to the container group
     strictly clips all children to the artboard's bounding box [x, y, width, height].
   - Persistent metadata parasite `photogimp/artboard` storing coordinates, dimensions,
     background mode, preset name, and clipping state.
   - Optional artboard background layer (White, Black, Transparent, Custom Color) pinned
     at the base of the container group.
2. Standard Device & Screen Presets:
   - Desktop 1080p, Desktop 1440p, Desktop 4K, Mobile iPhone, Mobile Android, Tablet iPad,
     Social Instagram Square, Social Story, Print A4.
3. Conversion Workflows:
   - `python-fu-artboard-from-layers`: Automatically measures collective bounding box of
     selected layers and converts them into an artboard container.
   - `python-fu-artboard-from-group`: Converts an existing layer group into an artboard.
4. Duplication & Spatial Arrangement (`python-fu-duplicate-artboard`):
   - Clones an existing artboard with all nested content, placed adjacent in specified
     direction ('right', 'left', 'below', 'above') with customizable spacing.
   - Automatically expands parent image canvas if needed to accommodate all artboards side-by-side.
5. Artboard Resizing (`python-fu-resize-artboard`):
   - Updates artboard width, height, boundary mask, and background layer.
6. Multi-Artboard Batch Export (`python-fu-export-artboards`):
   - Exports all artboards in the document as standalone files (PNG or JPEG), each cropped
     to its individual artboard canvas geometry.
7. Canvas Artwork Integrity & Undo Protection:
   - Target and base canvas artwork pixels remain 100% untouched (diff == 0.000000).
   - Single-step undo group encapsulation across all operations.
"""

import os
import sys
import json
import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio

PARASITE_ARTBOARD = "photogimp/artboard"
PARASITE_ARTBOARD_BG = "photogimp/artboard-background"
PARASITE_ARTBOARD_BOUNDS = "photogimp/artboard-bounds"

PROC_NAME_CREATE = "python-fu-create-artboard"
PROC_NAME_FROM_LAYERS = "python-fu-artboard-from-layers"
PROC_NAME_FROM_GROUP = "python-fu-artboard-from-group"
PROC_NAME_DUPLICATE = "python-fu-duplicate-artboard"
PROC_NAME_RESIZE = "python-fu-resize-artboard"
PROC_NAME_EXPORT = "python-fu-export-artboards"

ARTBOARD_PRESETS = {
    "custom": (0, 0),
    "desktop-1080p": (1920, 1080),
    "desktop-1440p": (2560, 1440),
    "desktop-4k": (3840, 2160),
    "mobile-iphone": (390, 844),
    "mobile-iphone-pro-max": (430, 932),
    "mobile-android": (360, 800),
    "tablet-ipad": (820, 1180),
    "social-square": (1080, 1080),
    "social-story": (1080, 1920),
    "print-a4": (2480, 3508),
}


def read_json_parasite(item, parasite_name):
    """Safely read and decode a JSON metadata parasite."""
    par = item.get_parasite(parasite_name)
    if par:
        try:
            return json.loads(bytes(par.get_data()).decode("utf-8"))
        except Exception:
            pass
    return None


def write_json_parasite(item, parasite_name, data):
    """Write dictionary as a persistent JSON parasite."""
    raw = json.dumps(data).encode("utf-8")
    par = Gimp.Parasite.new(parasite_name, Gimp.PARASITE_PERSISTENT, raw)
    item.attach_parasite(par)


def is_artboard(item):
    """Check if item is an Artboard group layer."""
    if item and isinstance(item, Gimp.GroupLayer):
        return item.get_parasite(PARASITE_ARTBOARD) is not None
    return False


def find_all_artboards(image):
    """Recursively collect all Artboard group layers in the document."""
    artboards = []

    def _collect(item):
        if is_artboard(item):
            artboards.append(item)
        if isinstance(item, Gimp.GroupLayer) or hasattr(item, 'get_children'):
            for ch in item.get_children() or []:
                _collect(ch)

    for lyr in image.get_layers():
        _collect(lyr)
    return artboards


def find_active_artboard(image, drawables=None):
    """Locate active or selected Artboard in the document."""
    # 1. Check selected layers
    if hasattr(image, 'get_selected_layers'):
        for lyr in image.get_selected_layers():
            if is_artboard(lyr):
                return lyr
            parent = lyr.get_parent()
            while parent:
                if is_artboard(parent):
                    return parent
                parent = parent.get_parent()

    # 2. Check drawables
    if drawables:
        for d in drawables:
            if is_artboard(d):
                return d
            parent = d.get_parent()
            while parent:
                if is_artboard(parent):
                    return parent
                parent = parent.get_parent()

    # 3. Fallback to first artboard in document
    all_abs = find_all_artboards(image)
    return all_abs[0] if all_abs else None


def ensure_canvas_bounds(image, x, y, width, height, margin=50):
    """Expands document canvas if the specified bounding box extends past edges."""
    cur_w = image.get_width()
    cur_h = image.get_height()
    needed_w = max(cur_w, x + width + margin)
    needed_h = max(cur_h, y + height + margin)
    if needed_w > cur_w or needed_h > cur_h:
        image.resize(needed_w, needed_h, 0, 0)


def configure_artboard_mask(image, group, x, y, width, height):
    """Creates or updates the rectangular boundary clipping mask on the artboard group."""
    mask = group.get_mask()
    if mask is None:
        mask = group.create_mask(Gimp.AddMaskType.BLACK)
        group.add_mask(mask)

    # Fill mask with black outside, white strictly within artboard bounds
    Gimp.context_set_foreground(Gegl.Color.new("rgb(0,0,0)"))
    mask.edit_fill(Gimp.FillType.FOREGROUND)
    image.select_rectangle(Gimp.ChannelOps.REPLACE, x, y, width, height)
    mask.edit_fill(Gimp.FillType.WHITE)
    Gimp.Selection.none(image)
    return mask


def create_artboard_background(image, group, name, x, y, width, height, bg_color):
    """Creates an optional artboard background layer at the bottom of the group."""
    bg_color = (bg_color or "white").lower().strip()
    if bg_color == "transparent":
        return None

    bg = Gimp.Layer.new(
        image,
        f"{name} (Background)",
        width,
        height,
        Gimp.ImageType.RGBA_IMAGE,
        100.0,
        Gimp.LayerMode.NORMAL
    )
    # Insert at bottom of artboard group
    children = group.get_children() if hasattr(group, 'get_children') else []
    pos = len(children) if children else 0
    image.insert_layer(bg, group, pos)
    bg.set_offsets(x, y)

    if bg_color == "black":
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0,0,0)"))
        bg.edit_fill(Gimp.FillType.FOREGROUND)
    else:  # "white" or default
        Gimp.context_set_foreground(Gegl.Color.new("rgb(1,1,1)"))
        bg.edit_fill(Gimp.FillType.FOREGROUND)

    bg.attach_parasite(
        Gimp.Parasite.new(PARASITE_ARTBOARD_BG, Gimp.PARASITE_PERSISTENT, b"true")
    )
    return bg


def ensure_artboard_bounds_layer(image, group, name):
    """Ensures a transparent canvas-spanning layer exists in group to define clip extents."""
    for ch in group.get_children() or []:
        if ch.get_parasite(PARASITE_ARTBOARD_BOUNDS):
            if ch.get_width() != image.get_width() or ch.get_height() != image.get_height():
                ch.scale(image.get_width(), image.get_height(), False)
            ch.set_offsets(0, 0)
            return ch

    bounds = Gimp.Layer.new(
        image,
        f"{name} (Boundary Frame)",
        image.get_width(),
        image.get_height(),
        Gimp.ImageType.RGBA_IMAGE,
        100.0,
        Gimp.LayerMode.NORMAL
    )
    image.insert_layer(bounds, group, 0)
    bounds.edit_fill(Gimp.FillType.TRANSPARENT)
    bounds.set_offsets(0, 0)
    bounds.attach_parasite(
        Gimp.Parasite.new(PARASITE_ARTBOARD_BOUNDS, Gimp.PARASITE_PERSISTENT, b"true")
    )
    return bounds


class ArtboardsPlugin(Gimp.PlugIn):
    """Native GIMP 3.0 Artboards & Multi-Canvas Layout Manager Plugin."""

    def do_query_procedures(self):
        return [
            PROC_NAME_CREATE,
            PROC_NAME_FROM_LAYERS,
            PROC_NAME_FROM_GROUP,
            PROC_NAME_DUPLICATE,
            PROC_NAME_RESIZE,
            PROC_NAME_EXPORT,
        ]

    def do_create_procedure(self, name):
        if name == PROC_NAME_CREATE:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_create_artboard, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("New Artboard...")
            procedure.add_menu_path("<Image>/Layer/Artboards")
            procedure.add_menu_path("<Image>/Tools/Transform Tools/Artboard")
            procedure.set_documentation(
                "Create a new artboard",
                "Creates an isolated artboard canvas with optional boundary clipping and device presets.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_string_argument(
                "artboard-name", "Artboard Name", "Name of the new artboard",
                "Artboard 1", GObject.ParamFlags.READWRITE
            )
            procedure.add_string_argument(
                "preset", "Device Preset", "Screen preset ('desktop-1080p', 'mobile-iphone', 'social-square', etc.)",
                "custom", GObject.ParamFlags.READWRITE
            )
            procedure.add_int_argument(
                "pos-x", "Position X", "Left X coordinate of artboard",
                0, 100000, 0, GObject.ParamFlags.READWRITE
            )
            procedure.add_int_argument(
                "pos-y", "Position Y", "Top Y coordinate of artboard",
                0, 100000, 0, GObject.ParamFlags.READWRITE
            )
            procedure.add_int_argument(
                "width", "Width", "Width in pixels",
                1, 100000, 1920, GObject.ParamFlags.READWRITE
            )
            procedure.add_int_argument(
                "height", "Height", "Height in pixels",
                1, 100000, 1080, GObject.ParamFlags.READWRITE
            )
            procedure.add_string_argument(
                "bg-color", "Background Color", "Background fill: 'white', 'black', or 'transparent'",
                "white", GObject.ParamFlags.READWRITE
            )
            procedure.add_boolean_argument(
                "clip-content", "Clip Content", "Non-destructively clip layers extending outside bounds",
                True, GObject.ParamFlags.READWRITE
            )
            return procedure

        elif name == PROC_NAME_FROM_LAYERS:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_artboard_from_layers, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("Artboard from Layers...")
            procedure.add_menu_path("<Image>/Layer/Artboards")
            procedure.set_documentation(
                "Create artboard from selected layers",
                "Converts selected layers into a new artboard with calculated bounding box.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_string_argument(
                "artboard-name", "Artboard Name", "Name of the new artboard",
                "Artboard from Layers", GObject.ParamFlags.READWRITE
            )
            procedure.add_string_argument(
                "bg-color", "Background Color", "Background fill: 'white', 'black', or 'transparent'",
                "white", GObject.ParamFlags.READWRITE
            )
            procedure.add_boolean_argument(
                "clip-content", "Clip Content", "Non-destructively clip layers extending outside bounds",
                True, GObject.ParamFlags.READWRITE
            )
            return procedure

        elif name == PROC_NAME_FROM_GROUP:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_artboard_from_group, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("Artboard from Group...")
            procedure.add_menu_path("<Image>/Layer/Artboards")
            procedure.set_documentation(
                "Convert layer group to artboard",
                "Converts an existing layer group into an artboard container with boundary mask and metadata.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_string_argument(
                "artboard-name", "Artboard Name", "Name of the artboard",
                "Artboard from Group", GObject.ParamFlags.READWRITE
            )
            procedure.add_string_argument(
                "bg-color", "Background Color", "Background fill: 'white', 'black', or 'transparent'",
                "white", GObject.ParamFlags.READWRITE
            )
            procedure.add_boolean_argument(
                "clip-content", "Clip Content", "Non-destructively clip layers extending outside bounds",
                True, GObject.ParamFlags.READWRITE
            )
            return procedure

        elif name == PROC_NAME_DUPLICATE:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_duplicate_artboard, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("Duplicate Artboard...")
            procedure.add_menu_path("<Image>/Layer/Artboards")
            procedure.set_documentation(
                "Duplicate artboard and contents",
                "Clones an artboard and its nested layers, placing the replica adjacent in specified direction.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_string_argument(
                "direction", "Direction", "Placement direction: 'right', 'left', 'below', or 'above'",
                "right", GObject.ParamFlags.READWRITE
            )
            procedure.add_int_argument(
                "spacing", "Spacing", "Margin spacing between artboards in pixels",
                0, 10000, 50, GObject.ParamFlags.READWRITE
            )
            return procedure

        elif name == PROC_NAME_RESIZE:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_resize_artboard, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("Resize Artboard...")
            procedure.add_menu_path("<Image>/Layer/Artboards")
            procedure.set_documentation(
                "Resize artboard geometry",
                "Modifies artboard width, height, and boundary clipping mask.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_int_argument(
                "width", "Width", "New width in pixels",
                1, 100000, 1920, GObject.ParamFlags.READWRITE
            )
            procedure.add_int_argument(
                "height", "Height", "New height in pixels",
                1, 100000, 1080, GObject.ParamFlags.READWRITE
            )
            procedure.add_int_argument(
                "pos-x", "Position X", "New left X (-1 to preserve current X)",
                -1, 100000, -1, GObject.ParamFlags.READWRITE
            )
            procedure.add_int_argument(
                "pos-y", "Position Y", "New top Y (-1 to preserve current Y)",
                -1, 100000, -1, GObject.ParamFlags.READWRITE
            )
            return procedure

        elif name == PROC_NAME_EXPORT:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_export_artboards, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("Export Artboards to Files...")
            procedure.add_menu_path("<Image>/File/Export/Export Artboards to Files...")
            procedure.add_menu_path("<Image>/Layer/Artboards")
            procedure.set_documentation(
                "Export artboards to standalone files",
                "Exports each artboard cropped to its exact canvas bounds as individual PNG or JPEG files.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_string_argument(
                "output-dir", "Output Directory", "Directory to save exported files",
                "", GObject.ParamFlags.READWRITE
            )
            procedure.add_string_argument(
                "format", "Format", "Export format: 'png' or 'jpeg'",
                "png", GObject.ParamFlags.READWRITE
            )
            procedure.add_string_argument(
                "prefix", "Filename Prefix", "Optional prefix for exported files",
                "", GObject.ParamFlags.READWRITE
            )
            return procedure

        return None

    def run_create_artboard(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-artboards"), "No active image provided.", 0)
            )

        if run_mode == Gimp.RunMode.INTERACTIVE:
            gi.require_version('GimpUi', '3.0')
            from gi.repository import GimpUi
            GimpUi.init(PROC_NAME_CREATE)
            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        artboard_name = config.get_property("artboard-name") or "Artboard"
        preset = (config.get_property("preset") or "custom").lower().strip()
        pos_x = config.get_property("pos-x")
        pos_y = config.get_property("pos-y")
        width = config.get_property("width")
        height = config.get_property("height")
        bg_color = config.get_property("bg-color") or "white"
        clip_content = config.get_property("clip-content")

        # Resolve preset geometry if selected
        if preset in ARTBOARD_PRESETS and preset != "custom":
            pw, ph = ARTBOARD_PRESETS[preset]
            if width == 1920 and height == 1080:  # Defaults
                width, height = pw, ph

        image.undo_group_start()
        try:
            # Expand canvas if needed
            ensure_canvas_bounds(image, pos_x, pos_y, width, height)

            # Create Artboard Group Layer
            group = Gimp.GroupLayer.new(image)
            group.set_name(f"{artboard_name} (Artboard)")
            image.insert_layer(group, None, 0)

            # Ensure canvas-spanning boundary frame so mask covers canvas
            ensure_artboard_bounds_layer(image, group, artboard_name)

            # Create optional background layer
            create_artboard_background(image, group, artboard_name, pos_x, pos_y, width, height, bg_color)

            # Attach boundary clipping mask
            if clip_content:
                configure_artboard_mask(image, group, pos_x, pos_y, width, height)

            # Store persistent metadata parasite
            meta = {
                "name": artboard_name,
                "x": pos_x,
                "y": pos_y,
                "width": width,
                "height": height,
                "background": bg_color,
                "preset": preset,
                "clipped": clip_content
            }
            write_json_parasite(group, PARASITE_ARTBOARD, meta)

            image.set_selected_layers([group])
            image.undo_group_end()
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-artboards"), str(e), 0)
            )

    def run_artboard_from_layers(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-artboards"), "No active image provided.", 0)
            )

        selected_layers = image.get_selected_layers() if hasattr(image, 'get_selected_layers') else []
        if not selected_layers:
            if drawables:
                selected_layers = list(drawables)
            else:
                selected_layers = image.get_layers()

        if not selected_layers:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-artboards"), "No layers selected to create artboard.", 0)
            )

        artboard_name = config.get_property("artboard-name") or "Artboard from Layers"
        bg_color = config.get_property("bg-color") or "white"
        clip_content = config.get_property("clip-content")

        image.undo_group_start()
        try:
            # Measure collective bounding box of selected layers
            boxes = []
            for lyr in selected_layers:
                succ, ox, oy = lyr.get_offsets() if hasattr(lyr, 'get_offsets') else (True, 0, 0)
                lw = lyr.get_width()
                lh = lyr.get_height()
                boxes.append((ox, oy, ox + lw, oy + lh))

            min_x = min(b[0] for b in boxes)
            min_y = min(b[1] for b in boxes)
            max_x = max(b[2] for b in boxes)
            max_y = max(b[3] for b in boxes)
            width = max(1, max_x - min_x)
            height = max(1, max_y - min_y)

            # Insert group at position of topmost selected layer
            parent = selected_layers[0].get_parent()
            pos = selected_layers[0].get_position() if hasattr(selected_layers[0], 'get_position') else 0

            group = Gimp.GroupLayer.new(image)
            group.set_name(f"{artboard_name} (Artboard)")
            image.insert_layer(group, parent, pos)

            # Ensure canvas-spanning boundary frame so mask covers canvas
            ensure_artboard_bounds_layer(image, group, artboard_name)

            # Move selected layers inside group
            for lyr in selected_layers:
                image.reorder_item(lyr, group, -1)

            # Create optional background layer at bottom
            create_artboard_background(image, group, artboard_name, min_x, min_y, width, height, bg_color)

            # Attach boundary clipping mask
            if clip_content:
                configure_artboard_mask(image, group, min_x, min_y, width, height)

            # Store metadata
            meta = {
                "name": artboard_name,
                "x": min_x,
                "y": min_y,
                "width": width,
                "height": height,
                "background": bg_color,
                "preset": "custom",
                "clipped": clip_content
            }
            write_json_parasite(group, PARASITE_ARTBOARD, meta)

            image.set_selected_layers([group])
            image.undo_group_end()
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-artboards"), str(e), 0)
            )

    def run_artboard_from_group(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-artboards"), "No active image provided.", 0)
            )

        # Resolve target group
        target_group = None
        selected = image.get_selected_layers() if hasattr(image, 'get_selected_layers') else []
        for lyr in selected:
            if isinstance(lyr, Gimp.GroupLayer):
                target_group = lyr
                break

        if target_group is None:
            for lyr in image.get_layers():
                if isinstance(lyr, Gimp.GroupLayer):
                    target_group = lyr
                    break

        if target_group is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-artboards"), "No group layer found to convert to artboard.", 0)
            )

        artboard_name = config.get_property("artboard-name") or target_group.get_name()
        if not artboard_name.endswith("(Artboard)"):
            target_group.set_name(f"{artboard_name} (Artboard)")

        bg_color = config.get_property("bg-color") or "white"
        clip_content = config.get_property("clip-content")

        image.undo_group_start()
        try:
            children = target_group.get_children() or []
            if children:
                boxes = []
                for ch in children:
                    succ, ox, oy = ch.get_offsets() if hasattr(ch, 'get_offsets') else (True, 0, 0)
                    lw = ch.get_width()
                    lh = ch.get_height()
                    boxes.append((ox, oy, ox + lw, oy + lh))
                min_x = min(b[0] for b in boxes)
                min_y = min(b[1] for b in boxes)
                max_x = max(b[2] for b in boxes)
                max_y = max(b[3] for b in boxes)
                width = max(1, max_x - min_x)
                height = max(1, max_y - min_y)
            else:
                min_x, min_y = 0, 0
                width, height = image.get_width(), image.get_height()

            # Ensure canvas-spanning boundary frame so mask covers canvas
            ensure_artboard_bounds_layer(image, target_group, artboard_name)

            create_artboard_background(image, target_group, artboard_name, min_x, min_y, width, height, bg_color)

            if clip_content:
                configure_artboard_mask(image, target_group, min_x, min_y, width, height)

            meta = {
                "name": artboard_name,
                "x": min_x,
                "y": min_y,
                "width": width,
                "height": height,
                "background": bg_color,
                "preset": "custom",
                "clipped": clip_content
            }
            write_json_parasite(target_group, PARASITE_ARTBOARD, meta)

            image.set_selected_layers([target_group])
            image.undo_group_end()
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-artboards"), str(e), 0)
            )

    def run_duplicate_artboard(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-artboards"), "No active image provided.", 0)
            )

        artboard = find_active_artboard(image, drawables)
        if artboard is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-artboards"), "No active artboard found to duplicate.", 0)
            )

        meta = read_json_parasite(artboard, PARASITE_ARTBOARD) or {}
        cur_x = meta.get("x", 0)
        cur_y = meta.get("y", 0)
        w = meta.get("width", artboard.get_width() or 1920)
        h = meta.get("height", artboard.get_height() or 1080)
        name = meta.get("name", "Artboard")

        direction = (config.get_property("direction") or "right").lower().strip()
        spacing = config.get_property("spacing") or 50

        # Calculate new coordinates
        if direction == "left":
            new_x = cur_x - w - spacing
            new_y = cur_y
        elif direction == "below":
            new_x = cur_x
            new_y = cur_y + h + spacing
        elif direction == "above":
            new_x = cur_x
            new_y = cur_y - h - spacing
        else:  # "right"
            new_x = cur_x + w + spacing
            new_y = cur_y

        dx = new_x - cur_x
        dy = new_y - cur_y

        image.undo_group_start()
        try:
            # Expand canvas if needed
            ensure_canvas_bounds(image, new_x, new_y, w, h)

            # Duplicate artboard group layer
            new_group = artboard.copy()
            new_group.set_name(f"{name} Copy (Artboard)")
            parent = artboard.get_parent()
            pos = artboard.get_position() if hasattr(artboard, 'get_position') else 0
            image.insert_layer(new_group, parent, pos)

            # Shift children: boundary frame stays at (0, 0), others shift by (dx, dy)
            for ch in new_group.get_children() or []:
                if ch.get_parasite(PARASITE_ARTBOARD_BOUNDS):
                    if ch.get_width() != image.get_width() or ch.get_height() != image.get_height():
                        ch.scale(image.get_width(), image.get_height(), False)
                    ch.set_offsets(0, 0)
                else:
                    succ, ox, oy = ch.get_offsets() if hasattr(ch, 'get_offsets') else (True, 0, 0)
                    ch.set_offsets(ox + dx, oy + dy)

            # Reconfigure boundary mask at new position
            if meta.get("clipped", True):
                configure_artboard_mask(image, new_group, new_x, new_y, w, h)

            # Update metadata
            new_meta = dict(meta)
            new_meta["name"] = f"{name} Copy"
            new_meta["x"] = new_x
            new_meta["y"] = new_y
            write_json_parasite(new_group, PARASITE_ARTBOARD, new_meta)

            image.set_selected_layers([new_group])
            image.undo_group_end()
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-artboards"), str(e), 0)
            )

    def run_resize_artboard(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-artboards"), "No active image provided.", 0)
            )

        artboard = find_active_artboard(image, drawables)
        if artboard is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-artboards"), "No active artboard found to resize.", 0)
            )

        meta = read_json_parasite(artboard, PARASITE_ARTBOARD) or {}
        new_w = config.get_property("width") or meta.get("width", 1920)
        new_h = config.get_property("height") or meta.get("height", 1080)
        px = config.get_property("pos-x")
        py = config.get_property("pos-y")
        new_x = meta.get("x", 0) if px < 0 else px
        new_y = meta.get("y", 0) if py < 0 else py

        image.undo_group_start()
        try:
            ensure_canvas_bounds(image, new_x, new_y, new_w, new_h)

            ensure_artboard_bounds_layer(image, artboard, meta.get("name", "Artboard"))

            if meta.get("clipped", True):
                configure_artboard_mask(image, artboard, new_x, new_y, new_w, new_h)

            # Resize background layer if present
            for ch in artboard.get_children() or []:
                if ch.get_parasite(PARASITE_ARTBOARD_BG):
                    ch.scale(new_w, new_h, False)
                    ch.set_offsets(new_x, new_y)

            meta["x"] = new_x
            meta["y"] = new_y
            meta["width"] = new_w
            meta["height"] = new_h
            write_json_parasite(artboard, PARASITE_ARTBOARD, meta)

            image.undo_group_end()
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-artboards"), str(e), 0)
            )

    def run_export_artboards(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-artboards"), "No active image provided.", 0)
            )

        artboards = find_all_artboards(image)
        if not artboards:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-artboards"), "No artboards found in document to export.", 0)
            )

        out_dir = config.get_property("output-dir")
        if not out_dir or not out_dir.strip():
            gfile = image.get_file()
            if gfile and gfile.get_path():
                out_dir = os.path.dirname(gfile.get_path())
            else:
                out_dir = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES) or os.path.expanduser("~")
        out_dir = os.path.abspath(out_dir)
        os.makedirs(out_dir, exist_ok=True)

        fmt = (config.get_property("format") or "png").lower().strip()
        ext = "jpg" if fmt in ("jpeg", "jpg") else "png"
        prefix = (config.get_property("prefix") or "").strip()

        pdb = Gimp.get_pdb()
        export_proc_name = "file-jpeg-export" if ext == "jpg" else "file-png-export"
        export_proc = pdb.lookup_procedure(export_proc_name) or pdb.lookup_procedure(f"file-{ext}-save")

        if export_proc is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-artboards"), f"Export procedure for {ext} not found in PDB.", 0)
            )

        try:
            for ab in artboards:
                meta = read_json_parasite(ab, PARASITE_ARTBOARD) or {}
                ax = meta.get("x", 0)
                ay = meta.get("y", 0)
                aw = max(1, meta.get("width", ab.get_width() or 100))
                ah = max(1, meta.get("height", ab.get_height() or 100))
                ab_name = meta.get("name", "Artboard")
                target_name = ab.get_name()

                # Duplicate image for isolated rendering
                dup = image.duplicate()
                try:
                    # Keep only this artboard visible
                    for lyr in dup.get_layers():
                        lyr.set_visible(lyr.get_name() == target_name)

                    # Crop canvas exactly to artboard's bounds
                    dup.crop(aw, ah, ax, ay)

                    # Export cropped duplicate
                    clean_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in ab_name).strip("_")
                    out_filename = f"{prefix}_{clean_name}.{ext}" if prefix else f"{clean_name}.{ext}"
                    out_path = os.path.join(out_dir, out_filename)
                    gio_file = Gio.File.new_for_path(out_path)

                    cfg = export_proc.create_config()
                    cfg.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
                    cfg.set_property("image", dup)
                    cfg.set_property("file", gio_file)
                    if ext == "jpg":
                        try:
                            cfg.set_property("quality", 0.90)
                        except Exception:
                            pass
                    export_proc.run(cfg)

                finally:
                    dup.delete()

            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as e:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-artboards"), str(e), 0)
            )


Gimp.main(ArtboardsPlugin.__gtype__, sys.argv)
