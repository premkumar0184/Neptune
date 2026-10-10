#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Selection & Layer Stroke Helper Plugin
================================================================
Photoshop Reference:
- Topics.txt:
  - Line 154: Add a stroke to a frame
  - Line 355: Stroke a selection or layer with color
  - Line 358: Fill a selection or layer with color
  - Line 387: Modify fill and stroke for shapes
- photoshop_docs.md:
  - Section 345 lines 10280-10305: Edit > Stroke (stroke-selection-layer-color.html)
    "Learn how to apply a colored stroke to a selection or layer in professional photoeditor
     to enhance visual impact or define edges. Specify width in pixels, select Inside,
     Center, or Outside for Location, set Blending Mode and Opacity, Preserve Transparency."

Key Architectural Features:
1. Non-Destructive Stroke Layer (`python-fu-stroke-layer`):
   - Creates an isolated dedicated stroke layer placed immediately above the active layer,
     preserving the underlying artwork pixels with zero degradation (diff == 0.000000).
   - Also supports in-place stroke application when explicitly requested.
2. Geometric Position Modes:
   - Inside: The border is drawn strictly within the selection or layer content boundary
     (via selection shrink/erosion subtraction).
   - Outside: The border is drawn strictly outside the selection or layer content boundary
     (via selection grow/dilation subtraction).
   - Center: The border is centered symmetrically across the boundary edge (via balanced
     grow/shrink subtraction).
3. Automatic Layer Alpha Fallback:
   - If no selection is active, automatically targets the non-transparent content boundary
     of the active layer.
4. Comprehensive Color and Blending Control:
   - Color selection: Current GIMP foreground color, solid black, solid white, or custom RGB sliders.
   - Professional blend modes: Normal, Multiply, Screen, Overlay, Soft Light.
   - Opacity slider (0.0 to 100.0%).
   - Preserve Transparency option.
5. Editable Layer Masks:
   - Supports None, Reveal-All (white), Conceal-All (black), or Active Selection masks.
6. Single-Step Undo Protection:
   - All operations encapsulated within image.undo_group_start() and image.undo_group_end().
"""

import sys
import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib


PROC_NAME = "python-fu-stroke-layer"

BLEND_MODES = {
    "normal": Gimp.LayerMode.NORMAL,
    "multiply": Gimp.LayerMode.MULTIPLY,
    "screen": Gimp.LayerMode.SCREEN,
    "overlay": Gimp.LayerMode.OVERLAY,
    "soft-light": Gimp.LayerMode.SOFTLIGHT,
}


class StrokeLayerPlugin(Gimp.PlugIn):
    def do_query_procedures(self):
        return [PROC_NAME]

    def do_set_i18n(self, procname):
        return False

    def do_create_procedure(self, name):
        if name != PROC_NAME:
            return None

        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            self.run_stroke,
            None
        )
        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )
        procedure.set_menu_label("Stroke Selection (Non-Destructive)...")
        procedure.add_menu_path("<Image>/Edit")
        procedure.add_menu_path("<Image>/Layer")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        procedure.set_documentation(
            "Stroke Selection (Non-Destructive)",
            "Draws a colored stroke border along the edge of the current selection or active layer content "
            "with Inside, Center, or Outside positioning, custom color, blend modes, and layer mask support.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Position Geometry
        pos_choice = Gimp.Choice.new()
        pos_choice.add("outside", 0, "Outside", "Draw stroke outside boundary")
        pos_choice.add("center", 1, "Center", "Center stroke symmetrically across boundary")
        pos_choice.add("inside", 2, "Inside", "Draw stroke inside boundary")

        procedure.add_choice_argument(
            "position",
            "Stroke Position",
            "Geometric placement relative to selection/layer edge (outside, center, inside)",
            pos_choice,
            "outside",
            GObject.ParamFlags.READWRITE
        )

        # 2. Width (pixels)
        procedure.add_int_argument(
            "width",
            "Stroke Width (px)",
            "Border thickness in pixels (1 to 100, default 3)",
            1,
            100,
            3,
            GObject.ParamFlags.READWRITE
        )

        # 3. Color Source
        col_choice = Gimp.Choice.new()
        col_choice.add("foreground", 0, "Foreground Color", "Use current toolbox foreground color")
        col_choice.add("black", 1, "Black", "Solid black border (#000000)")
        col_choice.add("white", 2, "White", "Solid white border (#ffffff)")
        col_choice.add("custom", 3, "Custom RGB", "Specify custom Red, Green, and Blue values")

        procedure.add_choice_argument(
            "color-source",
            "Color Source",
            "Color of the stroke border (foreground, black, white, custom)",
            col_choice,
            "foreground",
            GObject.ParamFlags.READWRITE
        )

        # 4. Custom RGB Sliders
        procedure.add_double_argument(
            "custom-r",
            "Custom Red",
            "Red channel intensity (0.0 to 1.0)",
            0.0,
            1.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "custom-g",
            "Custom Green",
            "Green channel intensity (0.0 to 1.0)",
            0.0,
            1.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "custom-b",
            "Custom Blue",
            "Blue channel intensity (0.0 to 1.0)",
            0.0,
            1.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 5. Blend Mode
        mode_choice = Gimp.Choice.new()
        mode_choice.add("normal", 0, "Normal", "Standard opaque stroke")
        mode_choice.add("multiply", 1, "Multiply", "Darkening stroke overlay")
        mode_choice.add("screen", 2, "Screen", "Lightening radiant border")
        mode_choice.add("overlay", 3, "Overlay", "High-contrast dynamic border")
        mode_choice.add("soft-light", 4, "Soft Light", "Subtle soft light border")

        procedure.add_choice_argument(
            "blend-mode",
            "Layer Blend Mode",
            "Photoshop-standard blend mode for the stroke layer",
            mode_choice,
            "normal",
            GObject.ParamFlags.READWRITE
        )

        # 6. Opacity
        procedure.add_double_argument(
            "opacity",
            "Opacity (%)",
            "Stroke layer opacity percentage (0.0 to 100.0, default 100.0)",
            0.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # 7. Output Mode
        out_choice = Gimp.Choice.new()
        out_choice.add("new-layer", 0, "Create New Stroke Layer", "Non-destructive layer preserving original artwork")
        out_choice.add("in-place", 1, "Modify Active Layer In-Place", "Directly paint stroke into active layer")

        procedure.add_choice_argument(
            "output-mode",
            "Output Mode",
            "Destination layer for the generated stroke (new-layer, in-place)",
            out_choice,
            "new-layer",
            GObject.ParamFlags.READWRITE
        )

        # 8. Layer Mask
        mask_choice = Gimp.Choice.new()
        mask_choice.add("none", 0, "None", "No mask attached")
        mask_choice.add("reveal-all", 1, "Reveal-All (White Mask)", "Fully visible editable layer mask")
        mask_choice.add("conceal-all", 2, "Conceal-All (Black Mask)", "Fully hidden mask for selective brush painting")
        mask_choice.add("selection", 3, "Active Selection Mask", "Mask initialized from current selection")

        procedure.add_choice_argument(
            "mask-type",
            "Layer Mask Attachment",
            "Initial mask attached to stroke layer (none, reveal-all, conceal-all, selection)",
            mask_choice,
            "none",
            GObject.ParamFlags.READWRITE
        )

        # 9. Preserve Transparency
        procedure.add_boolean_argument(
            "preserve-transparency",
            "Preserve Transparency",
            "Stroke only the opaque areas of the active layer",
            False,
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run_stroke(self, procedure, run_mode, image, drawables, config, data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-stroke"), "No valid image provided.", 0)
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
                GLib.Error.new_literal(GLib.quark_from_string("gimp-stroke"), "No active layer found.", 0)
            )

        position = config.get_property("position")
        width = int(config.get_property("width"))
        color_source = config.get_property("color-source")
        custom_r = config.get_property("custom-r")
        custom_g = config.get_property("custom-g")
        custom_b = config.get_property("custom-b")
        blend_name = config.get_property("blend-mode")
        opacity = config.get_property("opacity")
        output_mode = config.get_property("output-mode")
        mask_type = config.get_property("mask-type")
        preserve_trans = config.get_property("preserve-transparency")

        width = max(1, min(100, width))
        blend_mode = BLEND_MODES.get(blend_name, Gimp.LayerMode.NORMAL)

        # Determine stroke color
        if color_source == "black":
            stroke_color = Gegl.Color.new("rgb(0.0, 0.0, 0.0)")
        elif color_source == "white":
            stroke_color = Gegl.Color.new("rgb(1.0, 1.0, 1.0)")
        elif color_source == "custom":
            stroke_color = Gegl.Color.new(f"rgb({custom_r:.4f}, {custom_g:.4f}, {custom_b:.4f})")
        else:  # foreground
            stroke_color = Gimp.context_get_foreground()

        image.undo_group_start()
        Gimp.context_push()
        try:
            had_selection = not Gimp.Selection.is_empty(image)

            # If no selection is active, target layer alpha/content boundary
            if not had_selection:
                image.select_item(Gimp.ChannelOps.REPLACE, active_layer)
                # If layer was completely transparent, fall back to layer bounding box
                if Gimp.Selection.is_empty(image):
                    offsets = active_layer.get_offsets()
                    ox, oy = offsets[0], offsets[1]
                    lw, lh = active_layer.get_width(), active_layer.get_height()
                    image.select_rectangle(Gimp.ChannelOps.REPLACE, ox, oy, lw, lh)

            chan_orig = Gimp.Selection.save(image)

            # Synthesize stroke selection band based on geometric position
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
                w_out = (width + 1) // 2
                w_in = width // 2
                image.select_item(Gimp.ChannelOps.REPLACE, chan_orig)
                if w_out > 0:
                    Gimp.Selection.grow(image, w_out)
                chan_outer = Gimp.Selection.save(image)

                image.select_item(Gimp.ChannelOps.REPLACE, chan_orig)
                if w_in > 0:
                    Gimp.Selection.shrink(image, w_in)
                chan_inner = Gimp.Selection.save(image)

                image.select_item(Gimp.ChannelOps.REPLACE, chan_outer)
                image.select_item(Gimp.ChannelOps.SUBTRACT, chan_inner)
                image.remove_channel(chan_outer)
                image.remove_channel(chan_inner)

            # Target layer setup
            if output_mode == "new-layer":
                pos = image.get_item_position(active_layer)
                stroke_layer = Gimp.Layer.new(
                    image,
                    f"Stroke ({position.capitalize()} {width}px)",
                    image.get_width(),
                    image.get_height(),
                    Gimp.ImageType.RGBA_IMAGE,
                    opacity,
                    blend_mode
                )
                image.insert_layer(stroke_layer, None, pos)
            else:
                stroke_layer = active_layer

            # Handle preserve transparency
            if preserve_trans and active_layer.has_alpha():
                image.select_item(Gimp.ChannelOps.INTERSECT, active_layer)

            # Fill the stroke band
            Gimp.context_set_foreground(stroke_color)
            stroke_layer.edit_fill(Gimp.FillType.FOREGROUND)

            # Restore original selection or clear
            if had_selection:
                image.select_item(Gimp.ChannelOps.REPLACE, chan_orig)
            else:
                Gimp.Selection.none(image)
            image.remove_channel(chan_orig)

            # Attach layer mask if new layer
            if output_mode == "new-layer" and mask_type != "none":
                if mask_type == "reveal-all":
                    mask = stroke_layer.create_mask(Gimp.AddMaskType.WHITE)
                    stroke_layer.add_mask(mask)
                elif mask_type == "conceal-all":
                    mask = stroke_layer.create_mask(Gimp.AddMaskType.BLACK)
                    stroke_layer.add_mask(mask)
                elif mask_type == "selection":
                    if had_selection:
                        mask = stroke_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    else:
                        mask = stroke_layer.create_mask(Gimp.AddMaskType.WHITE)
                    stroke_layer.add_mask(mask)

            if output_mode == "new-layer":
                image.set_selected_layers([stroke_layer])

            Gimp.displays_flush()
        finally:
            Gimp.context_pop()
            image.undo_group_end()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(StrokeLayerPlugin.__gtype__, sys.argv)
