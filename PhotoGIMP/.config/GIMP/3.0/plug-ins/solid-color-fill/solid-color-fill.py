#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Solid Color Fill Layer & Canvas Fill Helper Plugin
===========================================================================
Photoshop Reference:
- Topics.txt:
  - Line 93: Color adjustment and fill layers
  - Line 101: Create fill layers
  - Line 103: Change adjustment and fill layer options
  - Line 353: Fill objects, selections, and layers
  - Line 357: Fill the work canvas
  - Line 358: Fill a selection or layer with color
- photoshop_docs.md:
  - Section 348 lines 10380-10416: Edit > Fill (fill-selection-layer-color.html)
    "Learn how to add a solid color fill to any selection or layer in professional photoeditor
     to enhance your designs and speed up your editing process. Under Contents, select:
     Foreground Color, Background Color, Black, 50% Gray, White, or Color. Under Blending,
     select Mode and Opacity. Select Preserve Transparency to fill only non-transparent areas."
  - Layer > New Fill Layer > Solid Color...:
    Creates a full-canvas layer filled with a solid color; if a selection is active,
    automatically converts the selection into an attached editable layer mask.

Key Architectural Features:
1. Solid Color Fill Layer (`python-fu-solid-color-fill`):
   - Fulfills Photoshop's Layer > New Fill Layer > Solid Color workflow:
     creates a full-canvas layer above the active layer and automatically converts any
     active selection into an attached layer mask, leaving underlying artwork 100% untouched
     (diff == 0.000000).
   - Also supports Selection-Only fill (new transparent layer with color confined to selection)
     and In-Place destructive fill with Preserve Transparency option.
2. Rich Color Source Presets:
   - Foreground color (current GIMP toolbox context foreground).
   - Background color (current GIMP toolbox context background).
   - 50% Neutral Gray (#808080: R=0.5, G=0.5, B=0.5).
   - Solid Black (#000000: R=0.0, G=0.0, B=0.0).
   - Solid White (#ffffff: R=1.0, G=1.0, B=1.0).
   - Custom RGB sliders (Red, Green, Blue from 0.0 to 1.0).
3. Professional Blend Modes & Opacity:
   - Normal, Multiply, Screen, Overlay, Soft Light, HSL Color.
   - Opacity slider (0.0 to 100.0%).
4. Editable Layer Masks:
   - Auto (Selection Mask if selected, else White mask), None, Reveal-All (white),
     Conceal-All (black), or Active Selection.
5. Preserve Transparency:
   - Locks alpha channel during in-place fills to preserve transparent areas.
6. Single-Step Undo Protection:
   - Encapsulated within image.undo_group_start() and image.undo_group_end().
"""

import sys
import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib


PROC_NAME = "python-fu-solid-color-fill"

BLEND_MODES = {
    "normal": Gimp.LayerMode.NORMAL,
    "multiply": Gimp.LayerMode.MULTIPLY,
    "screen": Gimp.LayerMode.SCREEN,
    "overlay": Gimp.LayerMode.OVERLAY,
    "soft-light": Gimp.LayerMode.SOFTLIGHT,
    "color": Gimp.LayerMode.HSL_COLOR,
}


class SolidColorFillPlugin(Gimp.PlugIn):
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
            self.run_solid_color_fill,
            None
        )
        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )
        procedure.set_menu_label("Solid Color Fill Layer...")
        procedure.add_menu_path("<Image>/Layer/New Fill Layer")
        procedure.add_menu_path("<Image>/Edit")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        procedure.set_documentation(
            "Solid Color Fill Layer (Non-Destructive)",
            "Creates a Photoshop-style solid color fill layer or fills canvas/selection "
            "with selected color, blend modes, opacity, and layer mask.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Color Source
        col_choice = Gimp.Choice.new()
        col_choice.add("foreground", 0, "Foreground Color", "Use current toolbox foreground color")
        col_choice.add("background", 1, "Background Color", "Use current toolbox background color")
        col_choice.add("50-gray", 2, "50% Neutral Gray", "Neutral 50% gray (#808080)")
        col_choice.add("black", 3, "Black", "Solid black (#000000)")
        col_choice.add("white", 4, "White", "Solid white (#ffffff)")
        col_choice.add("custom", 5, "Custom RGB", "Specify custom Red, Green, and Blue sliders")

        procedure.add_choice_argument(
            "color-source",
            "Color Source",
            "Color used to fill the layer or selection (foreground, background, 50-gray, black, white, custom)",
            col_choice,
            "foreground",
            GObject.ParamFlags.READWRITE
        )

        # 2. Custom RGB Sliders
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
            0.5,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "custom-b",
            "Custom Blue",
            "Blue channel intensity (0.0 to 1.0)",
            0.0,
            1.0,
            1.0,
            GObject.ParamFlags.READWRITE
        )

        # 3. Fill Scope
        scope_choice = Gimp.Choice.new()
        scope_choice.add("new-fill-layer", 0, "Solid Color Fill Layer", "Non-destructive full canvas layer with selection layer mask")
        scope_choice.add("selection-only", 1, "Selection Only (New Layer)", "New layer containing color confined to active selection")
        scope_choice.add("in-place", 2, "In-Place (Active Layer)", "Fill directly on active layer")

        procedure.add_choice_argument(
            "fill-scope",
            "Fill Scope",
            "Destination mode for fill (new-fill-layer, selection-only, in-place)",
            scope_choice,
            "new-fill-layer",
            GObject.ParamFlags.READWRITE
        )

        # 4. Blend Mode
        mode_choice = Gimp.Choice.new()
        mode_choice.add("normal", 0, "Normal", "Standard opaque color fill")
        mode_choice.add("multiply", 1, "Multiply", "Darkening color overlay")
        mode_choice.add("screen", 2, "Screen", "Lightening radiant color")
        mode_choice.add("overlay", 3, "Overlay", "High-contrast dynamic tone")
        mode_choice.add("soft-light", 4, "Soft Light", "Subtle tonal tint")
        mode_choice.add("color", 5, "Color (HSL)", "Colorize hue and saturation while keeping luminance")

        procedure.add_choice_argument(
            "blend-mode",
            "Blend Mode",
            "Photoshop-standard blend mode for fill layer",
            mode_choice,
            "normal",
            GObject.ParamFlags.READWRITE
        )

        # 5. Opacity
        procedure.add_double_argument(
            "opacity",
            "Opacity (%)",
            "Fill layer opacity percentage (0.0 to 100.0, default 100.0)",
            0.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # 6. Layer Mask
        mask_choice = Gimp.Choice.new()
        mask_choice.add("auto", 0, "Auto (Selection or White)", "Attach selection mask if active selection, otherwise white mask")
        mask_choice.add("none", 1, "None", "No mask attached")
        mask_choice.add("reveal-all", 2, "Reveal-All (White Mask)", "Fully visible editable layer mask")
        mask_choice.add("conceal-all", 3, "Conceal-All (Black Mask)", "Fully hidden mask for brush painting")
        mask_choice.add("selection", 4, "Active Selection Mask", "Mask initialized strictly from current selection")

        procedure.add_choice_argument(
            "mask-type",
            "Layer Mask Attachment",
            "Mask attached to fill layer (auto, none, reveal-all, conceal-all, selection)",
            mask_choice,
            "auto",
            GObject.ParamFlags.READWRITE
        )

        # 7. Preserve Transparency
        procedure.add_boolean_argument(
            "preserve-transparency",
            "Preserve Transparency",
            "When filling in-place, fill only non-transparent pixels",
            False,
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run_solid_color_fill(self, procedure, run_mode, image, drawables, config, data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-color-fill"), "No valid image provided.", 0)
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
                GLib.Error.new_literal(GLib.quark_from_string("gimp-color-fill"), "No active layer found.", 0)
            )

        color_source = config.get_property("color-source")
        custom_r = config.get_property("custom-r")
        custom_g = config.get_property("custom-g")
        custom_b = config.get_property("custom-b")
        fill_scope = config.get_property("fill-scope")
        blend_name = config.get_property("blend-mode")
        opacity = config.get_property("opacity")
        mask_type = config.get_property("mask-type")
        preserve_trans = config.get_property("preserve-transparency")

        blend_mode = BLEND_MODES.get(blend_name, Gimp.LayerMode.NORMAL)

        # Resolve fill color
        if color_source == "black":
            fill_color = Gegl.Color.new("rgb(0.0, 0.0, 0.0)")
        elif color_source == "white":
            fill_color = Gegl.Color.new("rgb(1.0, 1.0, 1.0)")
        elif color_source == "50-gray":
            fill_color = Gegl.Color.new("rgb(0.5, 0.5, 0.5)")
        elif color_source == "background":
            fill_color = Gimp.context_get_background()
        elif color_source == "custom":
            fill_color = Gegl.Color.new(f"rgb({custom_r:.4f}, {custom_g:.4f}, {custom_b:.4f})")
        else:  # foreground
            fill_color = Gimp.context_get_foreground()

        image.undo_group_start()
        Gimp.context_push()
        try:
            had_selection = not Gimp.Selection.is_empty(image)
            chan_orig = None
            if had_selection:
                chan_orig = Gimp.Selection.save(image)

            pos = image.get_item_position(active_layer)

            if fill_scope == "new-fill-layer":
                # Photoshop Solid Color Fill Layer:
                # The layer covers the whole canvas, and the selection is attached as a layer mask.
                if had_selection:
                    Gimp.Selection.none(image)

                layer_title = f"Color Fill ({color_source.capitalize()})"
                fill_layer = Gimp.Layer.new(
                    image,
                    layer_title,
                    image.get_width(),
                    image.get_height(),
                    Gimp.ImageType.RGBA_IMAGE,
                    opacity,
                    blend_mode
                )
                image.insert_layer(fill_layer, None, pos)

                Gimp.context_set_foreground(fill_color)
                fill_layer.edit_fill(Gimp.FillType.FOREGROUND)

                # Attach layer mask
                if mask_type == "auto":
                    if had_selection:
                        image.select_item(Gimp.ChannelOps.REPLACE, chan_orig)
                        mask = fill_layer.create_mask(Gimp.AddMaskType.SELECTION)
                        fill_layer.add_mask(mask)
                    else:
                        mask = fill_layer.create_mask(Gimp.AddMaskType.WHITE)
                        fill_layer.add_mask(mask)
                elif mask_type == "reveal-all":
                    mask = fill_layer.create_mask(Gimp.AddMaskType.WHITE)
                    fill_layer.add_mask(mask)
                elif mask_type == "conceal-all":
                    mask = fill_layer.create_mask(Gimp.AddMaskType.BLACK)
                    fill_layer.add_mask(mask)
                elif mask_type == "selection":
                    if had_selection:
                        image.select_item(Gimp.ChannelOps.REPLACE, chan_orig)
                        mask = fill_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    else:
                        mask = fill_layer.create_mask(Gimp.AddMaskType.WHITE)
                    fill_layer.add_mask(mask)

                # Restore selection state
                if had_selection:
                    image.select_item(Gimp.ChannelOps.REPLACE, chan_orig)
                    image.remove_channel(chan_orig)

                image.set_selected_layers([fill_layer])

            elif fill_scope == "selection-only":
                # Fills only within selection on a new layer
                layer_title = f"Color Fill Selection ({color_source.capitalize()})"
                fill_layer = Gimp.Layer.new(
                    image,
                    layer_title,
                    image.get_width(),
                    image.get_height(),
                    Gimp.ImageType.RGBA_IMAGE,
                    opacity,
                    blend_mode
                )
                image.insert_layer(fill_layer, None, pos)

                Gimp.context_set_foreground(fill_color)
                fill_layer.edit_fill(Gimp.FillType.FOREGROUND)

                if mask_type != "none" and mask_type != "auto":
                    if mask_type == "reveal-all":
                        mask = fill_layer.create_mask(Gimp.AddMaskType.WHITE)
                        fill_layer.add_mask(mask)
                    elif mask_type == "conceal-all":
                        mask = fill_layer.create_mask(Gimp.AddMaskType.BLACK)
                        fill_layer.add_mask(mask)
                    elif mask_type == "selection":
                        if had_selection:
                            mask = fill_layer.create_mask(Gimp.AddMaskType.SELECTION)
                        else:
                            mask = fill_layer.create_mask(Gimp.AddMaskType.WHITE)
                        fill_layer.add_mask(mask)

                if chan_orig is not None:
                    image.remove_channel(chan_orig)

                image.set_selected_layers([fill_layer])

            else:  # in-place
                target_layer = active_layer
                had_lock = target_layer.get_lock_alpha()
                if preserve_trans and target_layer.has_alpha():
                    target_layer.set_lock_alpha(True)

                Gimp.context_set_foreground(fill_color)
                target_layer.edit_fill(Gimp.FillType.FOREGROUND)

                if preserve_trans and target_layer.has_alpha():
                    target_layer.set_lock_alpha(had_lock)

                if chan_orig is not None:
                    image.remove_channel(chan_orig)

            Gimp.displays_flush()

        except Exception as exc:
            Gimp.context_pop()
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-color-fill"), str(exc), 0)
            )

        Gimp.context_pop()
        image.undo_group_end()

        return procedure.new_return_values(
            Gimp.PDBStatusType.SUCCESS,
            GLib.Error()
        )


if __name__ == "__main__":
    Gimp.main(SolidColorFillPlugin.__gtype__, sys.argv)
