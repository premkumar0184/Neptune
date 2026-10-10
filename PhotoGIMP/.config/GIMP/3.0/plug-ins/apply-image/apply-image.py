#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Apply Image & Channel Math Helper Plugin
==================================================================
Photoshop Reference:
- Topics.txt line 350: "HDR and channel manipulation - Blend channels with Apply Image and Calculations"
- photoshop_docs.md Section 340 lines 10050-10100:
  "Apply Image works with single and composite channels, while Calculations
   operates exclusively on single channels... choose source image, layer, and channel...
   blending modes [Multiply, Screen, Overlay, Soft Light, Add, Subtract...],
   Invert checkbox, Opacity slider, Scale, Offset, and Mask options."

Key Architectural Features:
1. Non-Destructive Adjustment Layer Workflow:
   - Duplicates the source layer into an isolated adjustment layer positioned directly
     above the target drawable. Base layer pixels underneath remain 100% mathematically
     untouched (diff == 0.000000).
2. Channel Extraction:
   - Composite RGB, Red, Green, Blue, Alpha, or Luminance channel isolation.
   - Clean monochrome extraction powered by GEGL mono-mixer (gegl:mono-mixer) avoiding
     private GLib enum issues.
3. Channel Inversion Support:
   - gegl:invert-linear accurately inverts source channel data for frequency separation,
     matte generation, and channel calculations.
4. Scale & Offset Calibration:
   - Implements Photoshop Apply Image math (Result = Source / Scale + Offset / 255.0)
     via GIMP PDB gimp-drawable-levels output range mapping.
5. 12 Photoshop-Standard Blend Modes:
   - Normal, Multiply, Screen, Overlay, Soft Light, Hard Light, Add (Addition),
     Subtract, Difference, Darken, Lighten, and Linear Light.
6. Curated Retouching Presets:
   - Frequency Separation (8-bit): Subtract mode, Scale 2.0, Offset 128.0 (neutral #808080 baseline).
   - Frequency Separation (16-bit): Add mode, Invert True, Scale 2.0, Offset 0.0.
   - Green Channel Contrast: Green channel isolated in Soft Light for flattering portrait skin tones.
   - Red Channel Multiply: Red channel isolated in Multiply for dramatic landscape tonal depth.
   - Blue Matte Extract: Blue channel inverted in Screen mode for hair/sky matte extraction.
   - Luminosity Blend: Perceptual luminance isolated in Overlay for crisp tonal punch.
   - Custom Math: Full manual control over channel, inversion, blend mode, scale, and offset.
7. Layer Mask Support:
   - Reveal All (white mask), Conceal All (black mask), and Active Selection.
"""

import math
import os
import sys
import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib


PRESETS = {
    "frequency-separation-8bit": {
        "label": "Frequency Separation (8-bit)",
        "desc": "Subtract blend mode with Scale 2 and Offset 128 (neutral 50% gray baseline)",
        "channel": "rgb",
        "invert": False,
        "blend_mode": "subtract",
        "scale": 2.0,
        "offset": 128.0,
        "opacity": 100.0,
    },
    "frequency-separation-16bit": {
        "label": "Frequency Separation (16-bit)",
        "desc": "Add blend mode with Invert enabled, Scale 2 and Offset 0",
        "channel": "rgb",
        "invert": True,
        "blend_mode": "add",
        "scale": 2.0,
        "offset": 0.0,
        "opacity": 100.0,
    },
    "green-channel-contrast": {
        "label": "Green Channel Contrast",
        "desc": "Isolate Green channel with Soft Light blend mode for natural skin tone contrast",
        "channel": "green",
        "invert": False,
        "blend_mode": "soft-light",
        "scale": 1.0,
        "offset": 0.0,
        "opacity": 100.0,
    },
    "red-channel-multiply": {
        "label": "Red Channel Multiply",
        "desc": "Isolate Red channel with Multiply blend mode for dramatic landscape tonal depth",
        "channel": "red",
        "invert": False,
        "blend_mode": "multiply",
        "scale": 1.0,
        "offset": 0.0,
        "opacity": 100.0,
    },
    "blue-matte-extract": {
        "label": "Blue Matte Extract",
        "desc": "Isolate Blue channel with Invert enabled and Screen blend mode for matte/hair extraction",
        "channel": "blue",
        "invert": True,
        "blend_mode": "screen",
        "scale": 1.0,
        "offset": 0.0,
        "opacity": 100.0,
    },
    "luminosity-blend": {
        "label": "Luminosity Blend",
        "desc": "Isolate composite luminance with Overlay blend mode for crisp tonal punch",
        "channel": "luminance",
        "invert": False,
        "blend_mode": "overlay",
        "scale": 1.0,
        "offset": 0.0,
        "opacity": 100.0,
    },
    "custom": {
        "label": "Custom Math",
        "desc": "Custom channel, blending mode, invert, scale, and offset",
        "channel": "rgb",
        "invert": False,
        "blend_mode": "normal",
        "scale": 1.0,
        "offset": 0.0,
        "opacity": 100.0,
    },
}

BLEND_MODES = {
    "normal": Gimp.LayerMode.NORMAL,
    "multiply": Gimp.LayerMode.MULTIPLY,
    "screen": Gimp.LayerMode.SCREEN,
    "overlay": Gimp.LayerMode.OVERLAY,
    "soft-light": Gimp.LayerMode.SOFTLIGHT,
    "hard-light": Gimp.LayerMode.HARDLIGHT,
    "add": Gimp.LayerMode.ADDITION,
    "subtract": Gimp.LayerMode.SUBTRACT,
    "difference": Gimp.LayerMode.DIFFERENCE,
    "darken": Gimp.LayerMode.DARKEN_ONLY,
    "lighten": Gimp.LayerMode.LIGHTEN_ONLY,
    "linear-light": Gimp.LayerMode.LINEAR_LIGHT,
}


def apply_image_run(procedure, run_mode, image, drawables, config, data):
    if image is None:
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-apply-image"),
                "No valid image provided.",
                0
            )
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-apply-image')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    # Read configuration parameters
    preset = config.get_property('preset')
    source_layer_id = config.get_property('source-layer-id')
    source_channel = config.get_property('source-channel')
    invert = config.get_property('invert')
    blend_mode = config.get_property('blend-mode')
    opacity = config.get_property('opacity')
    scale = config.get_property('scale')
    offset = config.get_property('offset')
    mask_mode = config.get_property('mask-mode')

    # Resolve target layer
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
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-apply-image"),
                "No valid target layer found.",
                0
            )
        )

    # Resolve source layer
    src_layer = None
    if source_layer_id > 0:
        item = Gimp.Item.get_by_id(source_layer_id)
        if item and isinstance(item, Gimp.Layer):
            src_layer = item
    if src_layer is None:
        src_layer = target_layer

    # Resolve preset parameters vs custom overrides
    if preset in PRESETS and preset != "custom":
        p_info = PRESETS[preset]
        source_channel = p_info["channel"]
        invert = p_info["invert"]
        blend_mode = p_info["blend_mode"]
        scale = p_info["scale"]
        offset = p_info["offset"]
        layer_label = p_info["label"]
    else:
        layer_label = f"{source_channel.upper()} {blend_mode.replace('-', ' ').title()}"

    layer_name = f"Apply Image ({layer_label})"

    Gimp.context_push()
    image.undo_group_start()

    try:
        # Check active selection state
        has_selection = not Gimp.Selection.is_empty(image)
        saved_sel = None
        if has_selection:
            saved_sel = Gimp.Selection.save(image)
            Gimp.Selection.none(image)

        # Create non-destructive duplicate adjustment layer
        applied_layer = Gimp.Layer.new_from_drawable(src_layer, image)
        applied_layer.set_name(layer_name)

        # Set blending mode and opacity
        gimp_mode = BLEND_MODES.get(blend_mode, Gimp.LayerMode.NORMAL)
        applied_layer.set_mode(gimp_mode)
        applied_layer.set_opacity(max(0.0, min(100.0, float(opacity))))

        # Insert immediately above target layer
        parent = target_layer.get_parent()
        pos = image.get_item_position(target_layer)
        image.insert_layer(applied_layer, parent, pos)

        # Channel extraction
        if source_channel == "red":
            f_mono = Gimp.DrawableFilter.new(applied_layer, "gegl:mono-mixer", "")
            c_mono = f_mono.get_config()
            c_mono.set_property("red", 1.0)
            c_mono.set_property("green", 0.0)
            c_mono.set_property("blue", 0.0)
            c_mono.set_property("preserve-luminosity", False)
            applied_layer.merge_filter(f_mono)
        elif source_channel == "green":
            f_mono = Gimp.DrawableFilter.new(applied_layer, "gegl:mono-mixer", "")
            c_mono = f_mono.get_config()
            c_mono.set_property("red", 0.0)
            c_mono.set_property("green", 1.0)
            c_mono.set_property("blue", 0.0)
            c_mono.set_property("preserve-luminosity", False)
            applied_layer.merge_filter(f_mono)
        elif source_channel == "blue":
            f_mono = Gimp.DrawableFilter.new(applied_layer, "gegl:mono-mixer", "")
            c_mono = f_mono.get_config()
            c_mono.set_property("red", 0.0)
            c_mono.set_property("green", 0.0)
            c_mono.set_property("blue", 1.0)
            c_mono.set_property("preserve-luminosity", False)
            applied_layer.merge_filter(f_mono)
        elif source_channel == "luminance":
            f_mono = Gimp.DrawableFilter.new(applied_layer, "gegl:mono-mixer", "")
            c_mono = f_mono.get_config()
            c_mono.set_property("red", 0.2126)
            c_mono.set_property("green", 0.7152)
            c_mono.set_property("blue", 0.0722)
            c_mono.set_property("preserve-luminosity", False)
            applied_layer.merge_filter(f_mono)
        elif source_channel == "alpha":
            if src_layer.has_alpha():
                mask_alpha = src_layer.create_mask(Gimp.AddMaskType.ALPHA)
                w = applied_layer.get_width()
                h = applied_layer.get_height()
                rect = Gegl.Rectangle.new(0, 0, w, h)
                mask_alpha.get_buffer().copy(rect, Gegl.AbyssPolicy.CLAMP, applied_layer.get_buffer(), rect)
                applied_layer.get_buffer().flush()
                applied_layer.update(0, 0, w, h)
            else:
                Gimp.context_set_foreground(Gegl.Color.new("rgb(1.0, 1.0, 1.0)"))
                applied_layer.fill(Gimp.FillType.FOREGROUND)
        # If "rgb", composite color channels are preserved

        # Channel Inversion
        if invert:
            f_inv = Gimp.DrawableFilter.new(applied_layer, "gegl:invert-linear", "")
            applied_layer.merge_filter(f_inv)

        # Scale & Offset Math Calibration
        if abs(float(scale) - 1.0) > 1e-4 or abs(float(offset)) > 1e-4:
            p_levels = Gimp.get_pdb().lookup_procedure("gimp-drawable-levels")
            if p_levels:
                safe_scale = max(0.01, float(scale))
                low_out = max(0.0, min(1.0, float(offset) / 255.0))
                high_out = max(0.0, min(1.0, float(offset) / 255.0 + 1.0 / safe_scale))
                c_levels = p_levels.create_config()
                c_levels.set_property("drawable", applied_layer)
                c_levels.set_property("channel", Gimp.HistogramChannel.VALUE)
                c_levels.set_property("low-input", 0.0)
                c_levels.set_property("high-input", 1.0)
                c_levels.set_property("clamp-input", True)
                c_levels.set_property("gamma", 1.0)
                c_levels.set_property("low-output", low_out)
                c_levels.set_property("high-output", high_out)
                c_levels.set_property("clamp-output", True)
                p_levels.run(c_levels)

        # Attach Layer Mask
        if mask_mode == "conceal-all":
            mask = applied_layer.create_mask(Gimp.AddMaskType.BLACK)
            applied_layer.add_mask(mask)
        elif mask_mode == "selection":
            if has_selection and saved_sel is not None:
                image.select_item(Gimp.ChannelOps.REPLACE, saved_sel)
                mask = applied_layer.create_mask(Gimp.AddMaskType.SELECTION)
                applied_layer.add_mask(mask)
                image.remove_channel(saved_sel)
                saved_sel = None
                Gimp.Selection.none(image)
            else:
                mask = applied_layer.create_mask(Gimp.AddMaskType.WHITE)
                applied_layer.add_mask(mask)
        else:  # "reveal-all"
            mask = applied_layer.create_mask(Gimp.AddMaskType.WHITE)
            applied_layer.add_mask(mask)

        # Clean up temporary saved selection if not already done
        if saved_sel is not None:
            image.select_item(Gimp.ChannelOps.REPLACE, saved_sel)
            image.remove_channel(saved_sel)
            saved_sel = None

        image.set_selected_layers([applied_layer])
        image.undo_group_end()
        Gimp.context_pop()
        Gimp.displays_flush()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    except Exception as e:
        if saved_sel is not None:
            try:
                image.remove_channel(saved_sel)
            except Exception:
                pass
        image.undo_group_end()
        Gimp.context_pop()
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-apply-image"),
                f"Error applying image channel math: {str(e)}",
                0
            )
        )


class ApplyImagePlugin(Gimp.PlugIn):
    def do_query_procedures(self):
        return ["python-fu-apply-image"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, apply_image_run, None
        )
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
        procedure.set_menu_label("Apply Image...")
        procedure.add_menu_path("<Image>/Image")
        procedure.add_menu_path("<Image>/Image/Calculations...")
        procedure.add_menu_path("<Image>/Filters/Retouching")
        procedure.add_menu_path("<Image>/Layer")

        procedure.set_documentation(
            "Non-Destructive Apply Image & Channel Math Helper",
            "Simulates Photoshop Image > Apply Image and Image > Calculations with "
            "channel isolation (RGB, Red, Green, Blue, Alpha, Luminance), Invert, "
            "12 blending modes, Scale and Offset math, and layer masks on an isolated "
            "non-destructive adjustment layer.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add("frequency-separation-8bit", 0, "Frequency Separation (8-bit)", "Subtract blend mode with Scale 2 and Offset 128")
        preset_choice.add("frequency-separation-16bit", 1, "Frequency Separation (16-bit)", "Add blend mode with Invert enabled, Scale 2 and Offset 0")
        preset_choice.add("green-channel-contrast", 2, "Green Channel Contrast", "Isolate Green channel with Soft Light blend mode")
        preset_choice.add("red-channel-multiply", 3, "Red Channel Multiply", "Isolate Red channel with Multiply blend mode")
        preset_choice.add("blue-matte-extract", 4, "Blue Matte Extract", "Isolate Blue channel with Invert and Screen blend mode")
        preset_choice.add("luminosity-blend", 5, "Luminosity Blend", "Isolate composite luminance with Overlay blend mode")
        preset_choice.add("custom", 6, "Custom Math", "Custom channel, blending mode, invert, scale, and offset")

        procedure.add_choice_argument(
            "preset",
            "Preset",
            "Retouching or channel blend preset",
            preset_choice,
            "frequency-separation-8bit",
            GObject.ParamFlags.READWRITE
        )

        # 2. Source Layer ID (optional integer, -1 for auto / active layer)
        procedure.add_int_argument(
            "source-layer-id",
            "Source Layer ID",
            "ID of the reference source layer (-1 for active/target layer)",
            -1,
            1000000,
            -1,
            GObject.ParamFlags.READWRITE
        )

        # 3. Source Channel Choice
        chan_choice = Gimp.Choice.new()
        chan_choice.add("rgb", 0, "RGB / Composite", "Composite RGB color channels")
        chan_choice.add("red", 1, "Red Channel", "Red monochrome channel")
        chan_choice.add("green", 2, "Green Channel", "Green monochrome channel")
        chan_choice.add("blue", 3, "Blue Channel", "Blue monochrome channel")
        chan_choice.add("alpha", 4, "Alpha Channel", "Layer transparency / alpha channel")
        chan_choice.add("luminance", 5, "Luminance (Luma)", "Perceptual luminance (Rec. 709)")

        procedure.add_choice_argument(
            "source-channel",
            "Source Channel",
            "Channel to extract from source layer",
            chan_choice,
            "rgb",
            GObject.ParamFlags.READWRITE
        )

        # 4. Invert (Boolean, default False)
        procedure.add_boolean_argument(
            "invert",
            "Invert Channel",
            "Invert the source channel values before blending",
            False,
            GObject.ParamFlags.READWRITE
        )

        # 5. Blend Mode Choice
        blend_choice = Gimp.Choice.new()
        blend_choice.add("normal", 0, "Normal", "Standard normal layer blending")
        blend_choice.add("multiply", 1, "Multiply", "Multiplies channel values (darkening)")
        blend_choice.add("screen", 2, "Screen", "Screen blending (lightening)")
        blend_choice.add("overlay", 3, "Overlay", "Combines Multiply and Screen based on base brightness")
        blend_choice.add("soft-light", 4, "Soft Light", "Subtle contrast enhancement")
        blend_choice.add("hard-light", 5, "Hard Light", "Intense contrast enhancement")
        blend_choice.add("add", 6, "Add / Addition", "Adds channel pixel values together")
        blend_choice.add("subtract", 7, "Subtract", "Subtracts channel pixel values")
        blend_choice.add("difference", 8, "Difference", "Absolute subtraction difference")
        blend_choice.add("darken", 9, "Darken", "Selects darker pixel values")
        blend_choice.add("lighten", 10, "Lighten", "Selects lighter pixel values")
        blend_choice.add("linear-light", 11, "Linear Light", "Linear combination (dodging and burning)")

        procedure.add_choice_argument(
            "blend-mode",
            "Blending Mode",
            "Layer blending mode",
            blend_choice,
            "normal",
            GObject.ParamFlags.READWRITE
        )

        # 6. Opacity (0.0 to 100.0, default 100.0)
        procedure.add_double_argument(
            "opacity",
            "Layer Opacity (%)",
            "Overall opacity of the adjustment layer (0.0 to 100.0, default 100.0)",
            0.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # 7. Scale (1.0 to 10.0, default 1.0)
        procedure.add_double_argument(
            "scale",
            "Scale",
            "Scaling divisor for channel calculation (e.g. 2.0 for frequency separation)",
            1.0,
            10.0,
            1.0,
            GObject.ParamFlags.READWRITE
        )

        # 8. Offset (-255.0 to 255.0, default 0.0)
        procedure.add_double_argument(
            "offset",
            "Offset",
            "Brightness offset value added after scale (e.g. 128.0 for 8-bit frequency separation)",
            -255.0,
            255.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 9. Mask Mode Choice
        mask_choice = Gimp.Choice.new()
        mask_choice.add("reveal-all", 0, "Reveal All (White Mask)", "Full effect across entire layer")
        mask_choice.add("conceal-all", 1, "Conceal All (Black Mask)", "Fully concealed, paint in with brush")
        mask_choice.add("selection", 2, "Active Selection", "Confine effect strictly to active selection")

        procedure.add_choice_argument(
            "mask-mode",
            "Layer Mask Mode",
            "Type of layer mask attached to the adjustment layer",
            mask_choice,
            "reveal-all",
            GObject.ParamFlags.READWRITE
        )

        return procedure


Gimp.main(ApplyImagePlugin.__gtype__, sys.argv)
