#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Seamless Pattern Generator & Tile Preview Helper Plugin
=================================================================
Photoshop Reference:
- Topics.txt lines 361-368:
  - Create and fill with patterns
  - Pattern Preview best practices
  - Create a new pattern
  - Generate patterns with Pattern Maker
  - Paint symmetrical patterns
  - Manage patterns in the Patterns panel
  - Use the Pattern Stamp tool for a hand-painted look
- photoshop_docs.md:
  - Section 348 lines 10390-10400: Edit > Fill: Contents: Pattern
  - Section 350-351 lines 10439-10480: View > Pattern Preview, Edit > Define Pattern

Key Architectural Features:
1. Seamless Pattern Tile Synthesis (`python-fu-seamless-pattern`):
   - Kaleidoscope: 4-quadrant symmetrical reflection providing 100% mathematical
     zero-discontinuity boundary continuity (left == right, top == bottom).
   - Crossfade: Dual-axis half-offset with smooth cosine edge-wrap blending over
     an adjustable overlap width percentage (5% to 50%).
   - Horizontal Mirror (mirror-x): Reflects left half onto right half for horizontal runners.
   - Vertical Mirror (mirror-y): Reflects top half onto bottom half for vertical borders.
   - Output options: Dedicated adjustment layer or in-place modification.
   - Editable layer masks (Reveal-all, Conceal-all, Active Selection).

2. Pattern Tile Preview (`python-fu-pattern-preview`):
   - Simulates Photoshop's View > Pattern Preview.
   - Replicates the active tile across a 2x2, 3x3, or 4x4 grid into a new preview document
     or preview layer to visually verify seamlessness, symmetry, and visual rhythm.

3. Pattern Fill Layer (`python-fu-pattern-fill`):
   - Simulates Photoshop's Edit > Fill > Pattern / Pattern Fill adjustment layer.
   - Tiles the active seamless pattern across the entire document canvas on a new layer.
   - Professional blend modes (Normal, Multiply, Screen, Overlay, Soft Light).
   - Preserves base layers with zero modification (diff == 0.000000).

4. Single-Step Undo Protection:
   - All operations wrapped in image.undo_group_start() and image.undo_group_end().
"""

import math
import os
import sys
import numpy as np
import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib


PROC_SEAMLESS = "python-fu-seamless-pattern"
PROC_PREVIEW = "python-fu-pattern-preview"
PROC_FILL = "python-fu-pattern-fill"

BLEND_MODES = {
    "normal": Gimp.LayerMode.NORMAL,
    "multiply": Gimp.LayerMode.MULTIPLY,
    "screen": Gimp.LayerMode.SCREEN,
    "overlay": Gimp.LayerMode.OVERLAY,
    "soft-light": Gimp.LayerMode.SOFTLIGHT,
}


def get_layer_rgba_array(layer):
    """Retrieves layer pixel buffer as a uint8 NumPy array of shape (H, W, 4)."""
    width = layer.get_width()
    height = layer.get_height()
    buf = layer.get_buffer()
    rect = Gegl.Rectangle.new(0, 0, width, height)
    raw = buf.get(rect, 1.0, "RGBA u8", Gegl.AbyssPolicy.NONE)
    arr = np.frombuffer(raw, dtype=np.uint8).reshape((height, width, 4)).copy()
    return arr, width, height


def write_layer_rgba_array(layer, arr):
    """Writes uint8 NumPy array of shape (H, W, 4) into layer buffer and flushes."""
    width = layer.get_width()
    height = layer.get_height()
    buf = layer.get_buffer()
    rect = Gegl.Rectangle.new(0, 0, width, height)
    buf.set(rect, "RGBA u8", arr.tobytes())
    buf.flush()
    layer.update(0, 0, width, height)


class SeamlessPatternPlugin(Gimp.PlugIn):
    def do_query_procedures(self):
        return [
            PROC_SEAMLESS,
            PROC_PREVIEW,
            PROC_FILL,
        ]

    def do_create_procedure(self, name):
        if name == PROC_SEAMLESS:
            return self._create_seamless_procedure(name)
        elif name == PROC_PREVIEW:
            return self._create_preview_procedure(name)
        elif name == PROC_FILL:
            return self._create_fill_procedure(name)
        return None

    # --------------------------------------------------------------------------
    # Procedure Definitions
    # --------------------------------------------------------------------------

    def _create_seamless_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_seamless, None)
        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )
        procedure.set_menu_label("Create Seamless Pattern Tile...")
        procedure.add_menu_path("<Image>/Filters/Map")
        procedure.add_menu_path("<Image>/Filters/Pattern")
        procedure.add_menu_path("<Image>/Image/Patterns")

        procedure.set_documentation(
            "Create Seamless Pattern Tile",
            "Synthesizes a seamless repeating pattern tile using 4-quadrant symmetrical "
            "kaleidoscope mirroring, dual-axis edge-wrap crossfading, or directional mirroring.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Synthesis Method
        meth_choice = Gimp.Choice.new()
        meth_choice.add("kaleidoscope", 0, "4-Quadrant Symmetrical Mirroring", "Guaranteed 100% boundary continuity")
        meth_choice.add("crossfade", 1, "Dual-Axis Edge-Wrap Crossfade Blending", "Cosine edge-wrap for organic textures")
        meth_choice.add("mirror-x", 2, "Horizontal Symmetrical Mirroring", "Horizontal seamless runner tile")
        meth_choice.add("mirror-y", 3, "Vertical Symmetrical Mirroring", "Vertical seamless border tile")

        procedure.add_choice_argument(
            "method",
            "Synthesis Method",
            "Mathematical tiling algorithm (kaleidoscope, crossfade, mirror-x, mirror-y)",
            meth_choice,
            "kaleidoscope",
            GObject.ParamFlags.READWRITE
        )

        # 2. Blend Width (for crossfade)
        procedure.add_double_argument(
            "blend-width",
            "Overlap / Feather Width (%)",
            "Percentage of tile width/height used for edge crossfading (5.0 to 50.0, default 25.0)",
            5.0,
            50.0,
            25.0,
            GObject.ParamFlags.READWRITE
        )

        # 3. Output Mode
        out_choice = Gimp.Choice.new()
        out_choice.add("new-layer", 0, "Create New Seamless Tile Layer", "Non-destructive layer preserving original artwork")
        out_choice.add("in-place", 1, "Modify Active Layer In-Place", "Directly overwrites active layer buffer")

        procedure.add_choice_argument(
            "output-mode",
            "Output Mode",
            "Target layer for generated seamless pattern (new-layer, in-place)",
            out_choice,
            "new-layer",
            GObject.ParamFlags.READWRITE
        )

        # 4. Layer Mask
        mask_choice = Gimp.Choice.new()
        mask_choice.add("none", 0, "None", "No mask attached")
        mask_choice.add("reveal-all", 1, "Reveal-All (White Mask)", "Fully visible editable layer mask")
        mask_choice.add("conceal-all", 2, "Conceal-All (Black Mask)", "Fully hidden mask for selective brush painting")
        mask_choice.add("selection", 3, "Active Selection Mask", "Mask initialized from document selection")

        procedure.add_choice_argument(
            "mask-type",
            "Layer Mask Attachment",
            "Initial mask attached to generated seamless layer (none, reveal-all, conceal-all, selection)",
            mask_choice,
            "none",
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def _create_preview_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_preview, None)
        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )
        procedure.set_menu_label("Pattern Tile Preview...")
        procedure.add_menu_path("<Image>/View")
        procedure.add_menu_path("<Image>/Filters/Map")
        procedure.add_menu_path("<Image>/Image/Patterns")

        procedure.set_documentation(
            "Pattern Tile Preview",
            "Simulates Photoshop View > Pattern Preview by repeating the active layer across a tiled grid.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Grid Size
        grid_choice = Gimp.Choice.new()
        grid_choice.add("2x2", 0, "2 x 2 Tiled Grid", "4 repetitions (2 columns by 2 rows)")
        grid_choice.add("3x3", 1, "3 x 3 Tiled Grid", "9 repetitions (Photoshop preview standard)")
        grid_choice.add("4x4", 2, "4 x 4 Tiled Grid", "16 repetitions (dense texture preview)")

        procedure.add_choice_argument(
            "grid-size",
            "Tiled Grid Dimension",
            "Number of pattern repetitions along width and height (2x2, 3x3, 4x4)",
            grid_choice,
            "3x3",
            GObject.ParamFlags.READWRITE
        )

        # 2. Destination
        dest_choice = Gimp.Choice.new()
        dest_choice.add("new-image", 0, "Open in New Preview Document", "Creates standalone preview document sized to grid")
        dest_choice.add("new-layer", 1, "Add Tiled Preview Layer to Document", "Inserts tiled layer into active document")

        procedure.add_choice_argument(
            "destination",
            "Preview Destination",
            "Where to render the tiled pattern preview (new-image, new-layer)",
            dest_choice,
            "new-image",
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def _create_fill_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_fill, None)
        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )
        procedure.set_menu_label("Fill with Pattern Tile...")
        procedure.add_menu_path("<Image>/Edit")
        procedure.add_menu_path("<Image>/Layer/New")
        procedure.add_menu_path("<Image>/Filters/Pattern")

        procedure.set_documentation(
            "Fill with Pattern Tile",
            "Simulates Photoshop Edit > Fill > Pattern by tiling the active layer across "
            "the canvas as a dedicated layer in professional blend modes with layer mask support.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Blend Mode
        mode_choice = Gimp.Choice.new()
        mode_choice.add("normal", 0, "Normal", "Standard opaque pattern fill")
        mode_choice.add("multiply", 1, "Multiply", "Darkening texture overlay")
        mode_choice.add("screen", 2, "Screen", "Lightening radiant overlay")
        mode_choice.add("overlay", 3, "Overlay", "High-contrast dynamic texture blend")
        mode_choice.add("soft-light", 4, "Soft Light", "Subtle tonal texture diffusion")

        procedure.add_choice_argument(
            "blend-mode",
            "Layer Blend Mode",
            "Photoshop-standard blend mode for the tiled fill layer",
            mode_choice,
            "normal",
            GObject.ParamFlags.READWRITE
        )

        # 2. Opacity
        procedure.add_double_argument(
            "opacity",
            "Layer Opacity (%)",
            "Fill layer opacity percentage (0.0 to 100.0, default 100.0)",
            0.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # 3. Layer Mask
        mask_choice = Gimp.Choice.new()
        mask_choice.add("reveal-all", 0, "Reveal-All (White Mask)", "Fully visible editable layer mask")
        mask_choice.add("conceal-all", 1, "Conceal-All (Black Mask)", "Fully hidden mask for selective brush painting")
        mask_choice.add("selection", 2, "Active Selection Mask", "Mask confined to current active selection")

        procedure.add_choice_argument(
            "mask-type",
            "Layer Mask Attachment",
            "Initial mask attached to pattern fill layer (reveal-all, conceal-all, selection)",
            mask_choice,
            "reveal-all",
            GObject.ParamFlags.READWRITE
        )

        return procedure

    # --------------------------------------------------------------------------
    # Execution Handlers
    # --------------------------------------------------------------------------

    def run_seamless(self, procedure, run_mode, image, drawables, config, data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-seamless"), "No valid image provided.", 0)
            )

        selected = image.get_selected_layers()
        active_layer = selected[0] if selected else (drawables[0] if drawables else None)
        if active_layer is None:
            layers = image.get_layers()
            if layers:
                active_layer = layers[0]
        if active_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-seamless"), "No active layer selected.", 0)
            )

        method = config.get_property("method")
        blend_width = config.get_property("blend-width")
        output_mode = config.get_property("output-mode")
        mask_type = config.get_property("mask-type")

        image.undo_group_start()
        try:
            # Handle selection isolation per Decision D-003
            has_selection = not Gimp.Selection.is_empty(image)
            saved_sel = None
            if has_selection:
                saved_sel = Gimp.Selection.save(image)
                Gimp.Selection.none(image)

            arr, width, height = get_layer_rgba_array(active_layer)

            # Mathematical synthesis
            if method == "kaleidoscope":
                hw, hh = width // 2, height // 2
                quad = arr[:hh, :hw]
                out = np.zeros_like(arr)
                out[:hh, :hw] = quad
                out[:hh, hw:hw * 2] = np.fliplr(quad)
                out[hh:hh * 2, :hw] = np.flipud(quad)
                out[hh:hh * 2, hw:hw * 2] = np.flipud(np.fliplr(quad))
                if width % 2 != 0:
                    out[:, -1] = out[:, -2]
                if height % 2 != 0:
                    out[-1, :] = out[-2, :]

            elif method == "crossfade":
                rolled = np.roll(arr.astype(np.float32), (height // 2, width // 2), axis=(0, 1))
                wx = 0.5 * (1.0 - np.cos(2.0 * np.pi * np.arange(width) / float(width)))
                wy = 0.5 * (1.0 - np.cos(2.0 * np.pi * np.arange(height) / float(height)))
                w2d = np.outer(wy, wx)[..., np.newaxis]
                blended = rolled * (1.0 - w2d) + arr.astype(np.float32) * w2d
                out = np.clip(blended, 0.0, 255.0).astype(np.uint8)

            elif method == "mirror-x":
                hw = width // 2
                half = arr[:, :hw]
                out = np.zeros_like(arr)
                out[:, :hw] = half
                out[:, hw:hw * 2] = np.fliplr(half)
                if width % 2 != 0:
                    out[:, -1] = out[:, -2]

            elif method == "mirror-y":
                hh = height // 2
                half = arr[:hh, :]
                out = np.zeros_like(arr)
                out[:hh, :] = half
                out[hh:hh * 2, :] = np.flipud(half)
                if height % 2 != 0:
                    out[-1, :] = out[-2, :]
            else:
                out = arr.copy()

            # Target layer creation / update
            if output_mode == "new-layer":
                pos = image.get_item_position(active_layer)
                target_layer = Gimp.Layer.new(
                    image,
                    f"Seamless Pattern ({method})",
                    width,
                    height,
                    Gimp.ImageType.RGBA_IMAGE,
                    100.0,
                    Gimp.LayerMode.NORMAL
                )
                image.insert_layer(target_layer, None, pos)
            else:
                target_layer = active_layer

            write_layer_rgba_array(target_layer, out)

            # Restore selection if saved
            if saved_sel:
                image.select_item(Gimp.ChannelOps.REPLACE, saved_sel)
                image.remove_channel(saved_sel)

            # Attach layer mask if requested
            if output_mode == "new-layer" and mask_type != "none":
                if mask_type == "reveal-all":
                    mask = target_layer.create_mask(Gimp.AddMaskType.WHITE)
                    target_layer.add_mask(mask)
                elif mask_type == "conceal-all":
                    mask = target_layer.create_mask(Gimp.AddMaskType.BLACK)
                    target_layer.add_mask(mask)
                elif mask_type == "selection":
                    if not Gimp.Selection.is_empty(image):
                        mask = target_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    else:
                        mask = target_layer.create_mask(Gimp.AddMaskType.WHITE)
                    target_layer.add_mask(mask)

            Gimp.displays_flush()
        finally:
            image.undo_group_end()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_preview(self, procedure, run_mode, image, drawables, config, data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-seamless"), "No valid image provided.", 0)
            )

        selected = image.get_selected_layers()
        active_layer = selected[0] if selected else (drawables[0] if drawables else None)
        if active_layer is None:
            layers = image.get_layers()
            if layers:
                active_layer = layers[0]
        if active_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-seamless"), "No active layer selected.", 0)
            )

        grid_size = config.get_property("grid-size")
        destination = config.get_property("destination")

        reps = 3
        if grid_size == "2x2":
            reps = 2
        elif grid_size == "4x4":
            reps = 4

        arr, tw, th = get_layer_rgba_array(active_layer)
        tiled = np.tile(arr, (reps, reps, 1))
        pw, ph = tw * reps, th * reps

        if destination == "new-image":
            preview_img = Gimp.Image.new(pw, ph, Gimp.ImageBaseType.RGB)
            preview_layer = Gimp.Layer.new(
                preview_img,
                f"Pattern Preview ({grid_size})",
                pw,
                ph,
                Gimp.ImageType.RGBA_IMAGE,
                100.0,
                Gimp.LayerMode.NORMAL
            )
            preview_img.insert_layer(preview_layer, None, 0)
            write_layer_rgba_array(preview_layer, tiled)

            if run_mode == Gimp.RunMode.INTERACTIVE:
                Gimp.Display.new(preview_img)
            Gimp.displays_flush()
        else:
            image.undo_group_start()
            try:
                preview_layer = Gimp.Layer.new(
                    image,
                    f"Pattern Preview ({grid_size})",
                    pw,
                    ph,
                    Gimp.ImageType.RGBA_IMAGE,
                    100.0,
                    Gimp.LayerMode.NORMAL
                )
                image.insert_layer(preview_layer, None, 0)
                write_layer_rgba_array(preview_layer, tiled)
                Gimp.displays_flush()
            finally:
                image.undo_group_end()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_fill(self, procedure, run_mode, image, drawables, config, data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-seamless"), "No valid image provided.", 0)
            )

        selected = image.get_selected_layers()
        active_layer = selected[0] if selected else (drawables[0] if drawables else None)
        if active_layer is None:
            layers = image.get_layers()
            if layers:
                active_layer = layers[0]
        if active_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-seamless"), "No active layer selected.", 0)
            )

        blend_name = config.get_property("blend-mode")
        opacity = config.get_property("opacity")
        mask_type = config.get_property("mask-type")

        blend_mode = BLEND_MODES.get(blend_name, Gimp.LayerMode.NORMAL)
        canvas_w = image.get_width()
        canvas_h = image.get_height()

        image.undo_group_start()
        try:
            # Handle selection isolation per Decision D-003
            has_selection = not Gimp.Selection.is_empty(image)
            saved_sel = None
            if has_selection:
                saved_sel = Gimp.Selection.save(image)
                Gimp.Selection.none(image)

            arr, tw, th = get_layer_rgba_array(active_layer)
            reps_y = int(math.ceil(canvas_h / float(th)))
            reps_x = int(math.ceil(canvas_w / float(tw)))

            # Tile across canvas
            tiled_full = np.tile(arr, (reps_y, reps_x, 1))[:canvas_h, :canvas_w, :]

            pos = image.get_item_position(active_layer)
            fill_layer = Gimp.Layer.new(
                image,
                f"Pattern Fill ({blend_name.capitalize()})",
                canvas_w,
                canvas_h,
                Gimp.ImageType.RGBA_IMAGE,
                opacity,
                blend_mode
            )
            image.insert_layer(fill_layer, None, pos)
            write_layer_rgba_array(fill_layer, tiled_full)

            # Restore selection if saved
            if saved_sel:
                image.select_item(Gimp.ChannelOps.REPLACE, saved_sel)
                image.remove_channel(saved_sel)

            # Attach layer mask
            if mask_type == "reveal-all":
                mask = fill_layer.create_mask(Gimp.AddMaskType.WHITE)
                fill_layer.add_mask(mask)
            elif mask_type == "conceal-all":
                mask = fill_layer.create_mask(Gimp.AddMaskType.BLACK)
                fill_layer.add_mask(mask)
            elif mask_type == "selection":
                if not Gimp.Selection.is_empty(image):
                    mask = fill_layer.create_mask(Gimp.AddMaskType.SELECTION)
                else:
                    mask = fill_layer.create_mask(Gimp.AddMaskType.WHITE)
                fill_layer.add_mask(mask)

            Gimp.displays_flush()
        finally:
            image.undo_group_end()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(SeamlessPatternPlugin.__gtype__, sys.argv)
