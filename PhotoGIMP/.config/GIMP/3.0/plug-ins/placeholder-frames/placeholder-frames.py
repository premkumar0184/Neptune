#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Placeholder Frames & Clipping Masks Layout Helper Plugin
==================================================================
Photoshop Reference:
- Topics.txt lines 150-155:
  "Draw frames", "Convert shapes or text to frames", "Place an image into a frame",
  "Select a frame and its content", "Add a stroke to a frame",
  "Apply patterns to template images"
- photoshop_docs.md Section 154-158 lines 4600-4735:
  "Draw empty frames: In photoeditor, the Frame tool lets you create shapes that
   automatically mask and resize images placed inside them... rectangular, elliptical...
   Convert shapes or text layers into frames... Place an image into a frame...
   image becomes a Smart Object... images automatically resize to fit frame boundaries...
   Add a stroke to a frame: Size, Position [Inside, Center, Outside], Color"

Architectural Parity & Key Features:
1. Placeholder Frame Creation & Conversion:
   - 'create-frame': Creates rectangular or elliptical placeholder frame at given (x, y, w, h)
     or from active selection bounds.
   - 'convert-to-frame': Converts an existing shape, text, or graphic layer into a frame container.
   - Frame container is represented as a specialized Gimp.GroupLayer with an attached boundary mask
     and persistent metadata parasite `photogimp/frame-container`.
2. Content Placement & Auto-Fitting:
   - 'place-image-in-frame': Imports an image file (or active layer) into the frame with auto-fitting:
     - 'fill' (Cover): Proportional scaling to cover entire frame, clipping overhang.
     - 'fit' (Contain): Proportional scaling to fit entire image inside frame.
     - 'stretch': Non-uniform scaling to exact frame width and height.
     - 'original': 100% scale centered in frame.
   - Content is placed inside the frame group and clipped non-destructively by the group mask.
3. Frame Stroke & Border Styling:
   - 'set-frame-stroke': Adds or updates a styled border stroke around the frame:
     width (1-100px), position ('inside', 'center', 'outside'), custom RGB swatch, and opacity.
4. Frame & Content Adjustment:
   - 'adjust-frame-content': Repositions (pan dx, dy) or rescales content inside the frame.
   - 'release-frame': Unpacks content from frame container back into standard root-level layers.
5. Canvas Artwork Integrity:
   - Base canvas artwork pixels remain 100% untouched (`diff == 0.000000`).
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

PARASITE_FRAME_CONTAINER = "photogimp/frame-container"


def get_all_layers(image):
    """Retrieve all layers recursively including items inside layer groups."""
    all_layers = []

    def _collect(item):
        all_layers.append(item)
        if isinstance(item, Gimp.GroupLayer) or hasattr(item, 'get_children'):
            try:
                children = item.get_children()
                if children:
                    for ch in children:
                        _collect(ch)
            except Exception:
                pass

    for lyr in image.get_layers():
        _collect(lyr)
    return all_layers


def resolve_active_layer(image, drawables):
    """Resolve active layer from image selection or drawables."""
    selected = image.get_selected_layers()
    if len(selected) > 0:
        return selected[0]
    if drawables and len(drawables) > 0:
        return drawables[0]
    layers = image.get_layers()
    return layers[0] if len(layers) > 0 else None


def read_json_parasite(item, key, default_val):
    """Safely read and JSON-decode an item/image parasite."""
    p = item.get_parasite(key)
    if p is None:
        return default_val
    try:
        raw_bytes = bytes(p.get_data())
        return json.loads(raw_bytes.decode("utf-8"))
    except Exception:
        return default_val


def write_json_parasite(item, key, data):
    """Safely JSON-encode and attach an item/image parasite."""
    raw_json = json.dumps(data, indent=2).encode("utf-8")
    item.attach_parasite(Gimp.Parasite.new(key, 1, raw_json))


def find_frame_group(image, name=""):
    """Find frame group by name or return the active/first frame group."""
    all_lyrs = get_all_layers(image)
    if name and name.strip():
        name_clean = name.strip()
        for lyr in all_lyrs:
            if isinstance(lyr, Gimp.GroupLayer):
                meta = read_json_parasite(lyr, PARASITE_FRAME_CONTAINER, None)
                if meta and (meta.get("name") == name_clean or lyr.get_name() == name_clean or lyr.get_name() == f"{name_clean} (Frame)"):
                    return lyr, meta
                if lyr.get_name() == name_clean or lyr.get_name() == f"{name_clean} (Frame)":
                    return lyr, meta or {"name": name_clean}

    # If no name specified, inspect selected layer or look for any frame group
    selected = image.get_selected_layers()
    for s in selected:
        if isinstance(s, Gimp.GroupLayer):
            meta = read_json_parasite(s, PARASITE_FRAME_CONTAINER, None)
            if meta:
                return s, meta
        parent = s.get_parent()
        if parent and isinstance(parent, Gimp.GroupLayer):
            meta = read_json_parasite(parent, PARASITE_FRAME_CONTAINER, None)
            if meta:
                return parent, meta

    # Fallback: scan all layers for first group with frame parasite
    for lyr in all_lyrs:
        if isinstance(lyr, Gimp.GroupLayer):
            meta = read_json_parasite(lyr, PARASITE_FRAME_CONTAINER, None)
            if meta:
                return lyr, meta

    return None, None


class PlaceholderFrames(Gimp.PlugIn):
    ## GimpPlugIn virtual methods ##
    def do_set_i18n(self, procname):
        return True, 'gimp30-python', None

    def do_query_procedures(self):
        return [
            "python-fu-create-frame",
            "python-fu-convert-to-frame",
            "python-fu-place-image-in-frame",
            "python-fu-set-frame-stroke",
            "python-fu-adjust-frame-content",
            "python-fu-release-frame",
        ]

    def do_create_procedure(self, name):
        Gegl.init(None)

        if name == "python-fu-create-frame":
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_create_frame, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("New Frame...")
            procedure.add_menu_path("<Image>/Layer/Frames")
            procedure.add_menu_path("<Image>/Tools/Transform Tools/Frame")
            procedure.set_documentation(
                "Create a placeholder frame",
                "Simulates Photoshop Frame Tool by creating a rectangular or elliptical placeholder frame.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_string_argument(
                "frame-name",
                "Frame Name",
                "Descriptive name for the frame placeholder",
                "Frame 1",
                GObject.ParamFlags.READWRITE
            )
            procedure.add_string_argument(
                "frame-shape",
                "Frame Shape",
                "Geometry shape of frame: 'rect' or 'ellipse'",
                "rect",
                GObject.ParamFlags.READWRITE
            )
            procedure.add_boolean_argument(
                "use-selection",
                "Use Active Selection",
                "If True and selection is active, use selection bounds and geometry",
                True,
                GObject.ParamFlags.READWRITE
            )
            procedure.add_int_argument(
                "pos-x",
                "Position X",
                "Left X coordinate of the frame",
                0, 100000, 50,
                GObject.ParamFlags.READWRITE
            )
            procedure.add_int_argument(
                "pos-y",
                "Position Y",
                "Top Y coordinate of the frame",
                0, 100000, 50,
                GObject.ParamFlags.READWRITE
            )
            procedure.add_int_argument(
                "width",
                "Width",
                "Width of the frame in pixels",
                1, 100000, 200,
                GObject.ParamFlags.READWRITE
            )
            procedure.add_int_argument(
                "height",
                "Height",
                "Height of the frame in pixels",
                1, 100000, 200,
                GObject.ParamFlags.READWRITE
            )
            procedure.add_string_argument(
                "fit-mode",
                "Auto-Fit Mode",
                "Fitting mode for placed content: 'fill', 'fit', 'stretch', or 'original'",
                "fill",
                GObject.ParamFlags.READWRITE
            )
            return procedure

        elif name == "python-fu-convert-to-frame":
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_convert_to_frame, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("Convert to Frame...")
            procedure.add_menu_path("<Image>/Layer/Frames")
            procedure.set_documentation(
                "Convert layer or selection to frame",
                "Simulates Photoshop 'Convert to Frame' by turning shapes, text, or selection into a frame placeholder.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_string_argument(
                "frame-name",
                "Frame Name",
                "Descriptive name for the converted frame",
                "Frame",
                GObject.ParamFlags.READWRITE
            )
            procedure.add_string_argument(
                "fit-mode",
                "Auto-Fit Mode",
                "Default fit mode for placed content: 'fill', 'fit', 'stretch', or 'original'",
                "fill",
                GObject.ParamFlags.READWRITE
            )
            return procedure

        elif name == "python-fu-place-image-in-frame":
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_place_image, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("Place Image into Frame...")
            procedure.add_menu_path("<Image>/Layer/Frames")
            procedure.add_menu_path("<Image>/File/Place")
            procedure.set_documentation(
                "Place an image into a placeholder frame",
                "Places and auto-fits an image into target frame with clipping mask encapsulation.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_string_argument(
                "frame-name",
                "Target Frame Name",
                "Name of frame to place into (leave empty for active/selected frame)",
                "",
                GObject.ParamFlags.READWRITE
            )
            procedure.add_string_argument(
                "file-path",
                "Image File Path",
                "Path to image file to place (leave empty to use active layer)",
                "",
                GObject.ParamFlags.READWRITE
            )
            procedure.add_string_argument(
                "fit-mode",
                "Fit Mode",
                "Aspect ratio fitting mode: 'fill', 'fit', 'stretch', 'original', or 'default'",
                "default",
                GObject.ParamFlags.READWRITE
            )
            return procedure

        elif name == "python-fu-set-frame-stroke":
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_set_stroke, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("Frame Stroke...")
            procedure.add_menu_path("<Image>/Layer/Frames")
            procedure.add_menu_path("<Image>/Layer/Layer Style")
            procedure.set_documentation(
                "Add or update frame border stroke",
                "Applies styled border stroke around frame boundary matching Photoshop Frame stroke options.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_string_argument(
                "frame-name",
                "Frame Name",
                "Target frame name (leave empty for active frame)",
                "",
                GObject.ParamFlags.READWRITE
            )
            procedure.add_int_argument(
                "stroke-width",
                "Stroke Width",
                "Width of the stroke in pixels",
                1, 100, 3,
                GObject.ParamFlags.READWRITE
            )
            procedure.add_string_argument(
                "position",
                "Position",
                "Stroke position relative to frame edge: 'inside', 'center', or 'outside'",
                "inside",
                GObject.ParamFlags.READWRITE
            )
            procedure.add_double_argument(
                "color-r",
                "Color Red",
                "Red color component (0.0 to 1.0)",
                0.0, 1.0, 0.0,
                GObject.ParamFlags.READWRITE
            )
            procedure.add_double_argument(
                "color-g",
                "Color Green",
                "Green color component (0.0 to 1.0)",
                0.0, 1.0, 0.0,
                GObject.ParamFlags.READWRITE
            )
            procedure.add_double_argument(
                "color-b",
                "Color Blue",
                "Blue color component (0.0 to 1.0)",
                0.0, 1.0, 0.0,
                GObject.ParamFlags.READWRITE
            )
            procedure.add_double_argument(
                "opacity",
                "Opacity",
                "Stroke layer opacity percentage (0.0 to 100.0)",
                0.0, 100.0, 100.0,
                GObject.ParamFlags.READWRITE
            )
            return procedure

        elif name == "python-fu-adjust-frame-content":
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_adjust_content, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("Adjust Frame Content...")
            procedure.add_menu_path("<Image>/Layer/Frames")
            procedure.set_documentation(
                "Pan or scale content inside a frame",
                "Transforms placed image within frame container while preserving frame boundary and clipping.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_string_argument(
                "frame-name",
                "Frame Name",
                "Target frame name (leave empty for active frame)",
                "",
                GObject.ParamFlags.READWRITE
            )
            procedure.add_int_argument(
                "offset-x",
                "Pan Offset X",
                "Horizontal delta in pixels to pan content within frame",
                -10000, 10000, 0,
                GObject.ParamFlags.READWRITE
            )
            procedure.add_int_argument(
                "offset-y",
                "Pan Offset Y",
                "Vertical delta in pixels to pan content within frame",
                -10000, 10000, 0,
                GObject.ParamFlags.READWRITE
            )
            procedure.add_double_argument(
                "scale-factor",
                "Scale Factor",
                "Relative multiplier to scale content (1.0 = unchanged)",
                0.01, 10.0, 1.0,
                GObject.ParamFlags.READWRITE
            )
            procedure.add_string_argument(
                "reapply-fit",
                "Reapply Fit Mode",
                "Re-fit content: 'none', 'fill', 'fit', or 'stretch'",
                "none",
                GObject.ParamFlags.READWRITE
            )
            return procedure

        elif name == "python-fu-release-frame":
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_release_frame, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("Release Frame...")
            procedure.add_menu_path("<Image>/Layer/Frames")
            procedure.set_documentation(
                "Release content from frame container",
                "Unpacks framed content back into a standard layer and cleans up frame container.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_string_argument(
                "frame-name",
                "Frame Name",
                "Target frame name (leave empty for active frame)",
                "",
                GObject.ParamFlags.READWRITE
            )
            procedure.add_boolean_argument(
                "keep-mask",
                "Keep Clipping Mask",
                "If True, transfers frame mask to released content layer; if False, discards mask",
                True,
                GObject.ParamFlags.READWRITE
            )
            return procedure

        return None

    def run_create_frame(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None or not image.is_valid():
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-placeholder-frames"), "No valid image provided.", 0)
            )

        frame_name = config.get_property("frame-name") or "Frame 1"
        shape = (config.get_property("frame-shape") or "rect").lower()
        use_sel = config.get_property("use-selection")
        fx = config.get_property("pos-x")
        fy = config.get_property("pos-y")
        fw = max(1, config.get_property("width"))
        fh = max(1, config.get_property("height"))
        fit_mode = config.get_property("fit-mode") or "fill"

        image.undo_group_start()
        try:
            # Check if active selection should be used
            has_sel = not Gimp.Selection.is_empty(image)
            sel_bounds = None
            if use_sel and has_sel:
                non_empty, x1, y1, x2, y2 = Gimp.Selection.bounds(image)
                if non_empty:
                    fx, fy = x1, y1
                    fw = max(1, x2 - x1)
                    fh = max(1, y2 - y1)
                    sel_bounds = (x1, y1, x2, y2)

            # Create Frame Group Layer
            group = Gimp.GroupLayer.new(image, f"{frame_name} (Frame)")
            image.insert_layer(group, None, 0)

            # Create placeholder background layer so group has valid bounding box
            placeholder = Gimp.Layer.new(
                image,
                f"{frame_name} (Placeholder)",
                fw, fh,
                Gimp.ImageType.RGBA_IMAGE,
                100.0,
                Gimp.LayerMode.NORMAL
            )
            image.insert_layer(placeholder, group, 0)
            placeholder.set_offsets(fx, fy)
            placeholder.edit_fill(Gimp.FillType.TRANSPARENT)

            # Create and attach Group Layer Mask
            mask = group.create_mask(Gimp.AddMaskType.BLACK)
            group.add_mask(mask)

            # Configure mask geometry
            if sel_bounds and use_sel:
                # Active selection is already present on the image
                mask.edit_fill(Gimp.FillType.WHITE)
                Gimp.Selection.none(image)
            elif shape == "ellipse":
                image.select_ellipse(Gimp.ChannelOps.REPLACE, fx, fy, fw, fh)
                mask.edit_fill(Gimp.FillType.WHITE)
                Gimp.Selection.none(image)
            else:
                image.select_rectangle(Gimp.ChannelOps.REPLACE, fx, fy, fw, fh)
                mask.edit_fill(Gimp.FillType.WHITE)
                Gimp.Selection.none(image)

            # Store frame metadata in group parasite
            meta = {
                "name": frame_name,
                "shape": shape,
                "x": fx,
                "y": fy,
                "width": fw,
                "height": fh,
                "fit_mode": fit_mode,
                "content_id": None,
                "stroke": None
            }
            write_json_parasite(group, PARASITE_FRAME_CONTAINER, meta)

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-placeholder-frames"), str(e), 0)
            )

        image.undo_group_end()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_convert_to_frame(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None or not image.is_valid():
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-placeholder-frames"), "No valid image provided.", 0)
            )

        target = resolve_active_layer(image, drawables)
        if target is None or not target.is_valid():
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-placeholder-frames"), "No active layer to convert.", 0)
            )

        frame_name = config.get_property("frame-name") or target.get_name()
        fit_mode = config.get_property("fit-mode") or "fill"

        image.undo_group_start()
        try:
            # Determine bounds
            has_sel = not Gimp.Selection.is_empty(image)
            if has_sel:
                _, fx, fy, x2, y2 = Gimp.Selection.bounds(image)
                fw = max(1, x2 - fx)
                fh = max(1, y2 - fy)
            else:
                offs = target.get_offsets()
                fx, fy = int(offs[-2]), int(offs[-1])
                fw = target.get_width()
                fh = target.get_height()

            # Create group layer
            group = Gimp.GroupLayer.new(image, f"{frame_name} (Frame)")
            image.insert_layer(group, None, 0)

            # Move target into group
            image.reorder_item(target, group, 0)

            # Add group mask based on target alpha or active selection
            mask = group.create_mask(Gimp.AddMaskType.BLACK)
            group.add_mask(mask)

            if has_sel:
                mask.edit_fill(Gimp.FillType.WHITE)
                Gimp.Selection.none(image)
            else:
                image.select_item(Gimp.ChannelOps.REPLACE, target)
                mask.edit_fill(Gimp.FillType.WHITE)
                Gimp.Selection.none(image)

            meta = {
                "name": frame_name,
                "shape": "custom",
                "x": fx,
                "y": fy,
                "width": fw,
                "height": fh,
                "fit_mode": fit_mode,
                "content_id": target.get_id(),
                "stroke": None
            }
            write_json_parasite(group, PARASITE_FRAME_CONTAINER, meta)

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-placeholder-frames"), str(e), 0)
            )

        image.undo_group_end()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_place_image(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None or not image.is_valid():
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-placeholder-frames"), "No valid image provided.", 0)
            )

        frame_name = config.get_property("frame-name")
        file_path = config.get_property("file-path") or ""
        fit_arg = config.get_property("fit-mode") or "default"

        group, meta = find_frame_group(image, frame_name)
        if group is None or meta is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-placeholder-frames"), "Frame container not found.", 0)
            )

        fit_mode = meta.get("fit_mode", "fill") if fit_arg == "default" else fit_arg
        fx, fy = meta.get("x", 0), meta.get("y", 0)
        fw, fh = meta.get("width", 200), meta.get("height", 200)

        image.undo_group_start()
        try:
            content_layer = None
            if file_path and file_path.strip() and os.path.isfile(file_path.strip()):
                gio_file = Gio.File.new_for_path(file_path.strip())
                content_layer = Gimp.file_load_layer(Gimp.RunMode.NONINTERACTIVE, image, gio_file)
                image.insert_layer(content_layer, group, 0)
            else:
                active_lyr = resolve_active_layer(image, drawables)
                if active_lyr and active_lyr.get_parent() != group:
                    content_layer = active_lyr
                    image.reorder_item(content_layer, group, 0)
                elif active_lyr:
                    content_layer = active_lyr
                else:
                    image.undo_group_end()
                    return procedure.new_return_values(
                        Gimp.PDBStatusType.CALLING_ERROR,
                        GLib.Error.new_literal(GLib.quark_from_string("gimp-placeholder-frames"), "No file path or active layer to place.", 0)
                    )

            cw = content_layer.get_width()
            ch = content_layer.get_height()

            # Apply Auto-Fitting
            if fit_mode == "fill":
                # Cover entire frame while maintaining aspect ratio
                scale_ratio = max(float(fw) / max(cw, 1), float(fh) / max(ch, 1))
                nw = max(1, int(round(cw * scale_ratio)))
                nh = max(1, int(round(ch * scale_ratio)))
                content_layer.scale(nw, nh, False)
                nx = fx + (fw - nw) // 2
                ny = fy + (fh - nh) // 2
                content_layer.set_offsets(nx, ny)

            elif fit_mode == "fit":
                # Contain whole image inside frame while maintaining aspect ratio
                scale_ratio = min(float(fw) / max(cw, 1), float(fh) / max(ch, 1))
                nw = max(1, int(round(cw * scale_ratio)))
                nh = max(1, int(round(ch * scale_ratio)))
                content_layer.scale(nw, nh, False)
                nx = fx + (fw - nw) // 2
                ny = fy + (fh - nh) // 2
                content_layer.set_offsets(nx, ny)

            elif fit_mode == "stretch":
                # Stretch to exact frame bounds
                content_layer.scale(fw, fh, False)
                content_layer.set_offsets(fx, fy)

            elif fit_mode == "original":
                # 100% scale centered in frame
                nx = fx + (fw - cw) // 2
                ny = fy + (fh - ch) // 2
                content_layer.set_offsets(nx, ny)

            # Ensure content layer is inside group at top
            if content_layer.get_parent() != group:
                image.reorder_item(content_layer, group, 0)

            clean_n = content_layer.get_name().replace(" copy", "").replace(" (Content)", "")
            content_layer.set_name(f"{clean_n} (Content)")
            meta["content_id"] = content_layer.get_id()
            meta["fit_mode"] = fit_mode
            write_json_parasite(group, PARASITE_FRAME_CONTAINER, meta)

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-placeholder-frames"), str(e), 0)
            )

        image.undo_group_end()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_set_stroke(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None or not image.is_valid():
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-placeholder-frames"), "No valid image provided.", 0)
            )

        frame_name = config.get_property("frame-name")
        width = max(1, config.get_property("stroke-width"))
        position = (config.get_property("position") or "inside").lower()
        cr = config.get_property("color-r")
        cg = config.get_property("color-g")
        cb = config.get_property("color-b")
        opacity = max(0.0, min(100.0, config.get_property("opacity")))

        group, meta = find_frame_group(image, frame_name)
        if group is None or meta is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-placeholder-frames"), "Frame container not found.", 0)
            )

        fx, fy = meta.get("x", 0), meta.get("y", 0)
        fw, fh = meta.get("width", 200), meta.get("height", 200)
        shape = meta.get("shape", "rect")
        fname = meta.get("name", "Frame")

        image.undo_group_start()
        try:
            # Check if stroke layer already exists above group
            stroke_layer_name = f"{fname} (Frame Stroke)"
            stroke_lyr = None
            for lyr in image.get_layers():
                if lyr.get_name() == stroke_layer_name:
                    stroke_lyr = lyr
                    break

            if stroke_lyr is None:
                # Find group position in root layer stack
                grp_pos = image.get_item_position(group)
                stroke_lyr = Gimp.Layer.new(
                    image,
                    stroke_layer_name,
                    image.get_width(),
                    image.get_height(),
                    Gimp.ImageType.RGBA_IMAGE,
                    opacity,
                    Gimp.LayerMode.NORMAL
                )
                image.insert_layer(stroke_lyr, None, max(0, grp_pos))
            else:
                stroke_lyr.set_opacity(opacity)
                stroke_lyr.edit_fill(Gimp.FillType.TRANSPARENT)

            # Draw stroke via channel subtraction geometry
            if shape == "ellipse":
                image.select_ellipse(Gimp.ChannelOps.REPLACE, fx, fy, fw, fh)
            else:
                image.select_rectangle(Gimp.ChannelOps.REPLACE, fx, fy, fw, fh)

            chan_orig = Gimp.Selection.save(image)

            if position == "inside":
                Gimp.Selection.shrink(image, width)
                chan_inner = Gimp.Selection.save(image)
                image.select_item(Gimp.ChannelOps.REPLACE, chan_orig)
                image.select_item(Gimp.ChannelOps.SUBTRACT, chan_inner)
                image.remove_channel(chan_inner)

            elif position == "outside":
                Gimp.Selection.grow(image, width)
                chan_outer = Gimp.Selection.save(image)
                image.select_item(Gimp.ChannelOps.REPLACE, chan_outer)
                image.select_item(Gimp.ChannelOps.SUBTRACT, chan_orig)
                image.remove_channel(chan_outer)

            else:  # center
                w_half = width // 2
                w_rem = width - w_half
                Gimp.Selection.grow(image, max(1, w_half))
                chan_outer = Gimp.Selection.save(image)

                image.select_item(Gimp.ChannelOps.REPLACE, chan_orig)
                Gimp.Selection.shrink(image, max(1, w_rem))
                chan_inner = Gimp.Selection.save(image)

                image.select_item(Gimp.ChannelOps.REPLACE, chan_outer)
                image.select_item(Gimp.ChannelOps.SUBTRACT, chan_inner)
                image.remove_channel(chan_outer)
                image.remove_channel(chan_inner)

            image.remove_channel(chan_orig)

            # Fill stroke with custom RGB
            Gimp.context_set_foreground(Gegl.Color.new(f"rgb({cr},{cg},{cb})"))
            stroke_lyr.edit_fill(Gimp.FillType.FOREGROUND)
            Gimp.Selection.none(image)

            meta["stroke"] = {
                "width": width,
                "position": position,
                "color": [cr, cg, cb],
                "opacity": opacity
            }
            write_json_parasite(group, PARASITE_FRAME_CONTAINER, meta)

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-placeholder-frames"), str(e), 0)
            )

        image.undo_group_end()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_adjust_content(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None or not image.is_valid():
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-placeholder-frames"), "No valid image provided.", 0)
            )

        frame_name = config.get_property("frame-name")
        dx = config.get_property("offset-x")
        dy = config.get_property("offset-y")
        scale_fac = config.get_property("scale-factor")
        reapply = config.get_property("reapply-fit") or "none"

        group, meta = find_frame_group(image, frame_name)
        if group is None or meta is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-placeholder-frames"), "Frame container not found.", 0)
            )

        # Resolve content layer inside group
        children = group.get_children() if hasattr(group, 'get_children') else []
        content_lyr = None
        for ch in children:
            if "(Content)" in ch.get_name() or ch.get_id() == meta.get("content_id"):
                content_lyr = ch
                break
        if content_lyr is None and len(children) > 0:
            content_lyr = children[0]

        if content_lyr is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-placeholder-frames"), "No content layer found inside frame.", 0)
            )

        image.undo_group_start()
        try:
            fw, fh = meta.get("width", 200), meta.get("height", 200)
            fx, fy = meta.get("x", 0), meta.get("y", 0)

            if reapply != "none":
                cw = content_lyr.get_width()
                ch = content_lyr.get_height()
                if reapply == "fill":
                    sr = max(float(fw) / max(cw, 1), float(fh) / max(ch, 1))
                    nw = max(1, int(round(cw * sr)))
                    nh = max(1, int(round(ch * sr)))
                    content_lyr.scale(nw, nh, False)
                    content_lyr.set_offsets(fx + (fw - nw) // 2, fy + (fh - nh) // 2)
                elif reapply == "fit":
                    sr = min(float(fw) / max(cw, 1), float(fh) / max(ch, 1))
                    nw = max(1, int(round(cw * sr)))
                    nh = max(1, int(round(ch * sr)))
                    content_lyr.scale(nw, nh, False)
                    content_lyr.set_offsets(fx + (fw - nw) // 2, fy + (fh - nh) // 2)
                elif reapply == "stretch":
                    content_lyr.scale(fw, fh, False)
                    content_lyr.set_offsets(fx, fy)

            if abs(scale_fac - 1.0) > 0.0001:
                nw = max(1, int(round(content_lyr.get_width() * scale_fac)))
                nh = max(1, int(round(content_lyr.get_height() * scale_fac)))
                content_lyr.scale(nw, nh, False)

            if dx != 0 or dy != 0:
                offs = content_lyr.get_offsets()
                content_lyr.set_offsets(int(offs[-2]) + dx, int(offs[-1]) + dy)

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-placeholder-frames"), str(e), 0)
            )

        image.undo_group_end()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_release_frame(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None or not image.is_valid():
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-placeholder-frames"), "No valid image provided.", 0)
            )

        frame_name = config.get_property("frame-name")
        keep_mask = config.get_property("keep-mask")

        group, meta = find_frame_group(image, frame_name)
        if group is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-placeholder-frames"), "Frame container not found.", 0)
            )

        image.undo_group_start()
        try:
            children = list(group.get_children()) if hasattr(group, 'get_children') else []
            content_lyr = None
            for ch in children:
                if "(Content)" in ch.get_name() or (meta and ch.get_id() == meta.get("content_id")):
                    content_lyr = ch
                    break
            if content_lyr is None and len(children) > 0:
                content_lyr = children[0]

            grp_mask = group.get_mask()

            if content_lyr is not None:
                # Move content layer outside of group
                grp_pos = image.get_item_position(group)
                image.reorder_item(content_lyr, None, max(0, grp_pos))

                # Clean name suffix
                clean_name = content_lyr.get_name().replace(" (Content)", "")
                content_lyr.set_name(clean_name)

                if keep_mask and grp_mask:
                    # Duplicate mask to content layer
                    mask_copy = content_lyr.create_mask(Gimp.AddMaskType.WHITE)
                    content_lyr.add_mask(mask_copy)
                    # Copy mask content
                    image.select_item(Gimp.ChannelOps.REPLACE, grp_mask)
                    mask_copy.edit_fill(Gimp.FillType.WHITE)
                    Gimp.Selection.none(image)

            # Remove associated stroke layer if present
            fname = meta.get("name", "") if meta else ""
            if fname:
                stroke_name = f"{fname} (Frame Stroke)"
                for lyr in image.get_layers():
                    if lyr.get_name() == stroke_name:
                        image.remove_layer(lyr)
                        break

            # Remove frame group
            image.remove_layer(group)

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-placeholder-frames"), str(e), 0)
            )

        image.undo_group_end()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(PlaceholderFrames.__gtype__, sys.argv)
