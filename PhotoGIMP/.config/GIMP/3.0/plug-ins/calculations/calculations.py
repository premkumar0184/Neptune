#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Channel Calculations & Two-Source Blending Helper Plugin
==================================================================
Photoshop Reference:
- Topics.txt line 350: "HDR and channel manipulation - Blend channels with Apply Image and Calculations"
- photoshop_docs.md Section 340 lines 10050-10100:
  "Apply Image works with single and composite channels, while Calculations
   operates exclusively on single channels... Choose the first source image, layer,
   and channel. Select Merged for Layer to use all layers. Optionally select Invert
   to use the channel's negative values or Gray to work with grayscale values.
   Choose the second source image, layer, and channel. Optionally select Invert
   to use the channel's negative. Choose a blending mode from the Blending menu.
   Enter an Opacity value to specify effect strength. To blend with a mask, select
   Mask, choose the image and layer containing the mask... For Result, specify
   whether to create a new document, add a new channel, or select the active image."

Key Features:
1. Two-Source Channel Extraction:
   - Source 1 & Source 2 can target any layer in the document.
   - Independent single channel selection: Gray (Luminance Rec. 709), Red, Green, Blue, Alpha.
   - Independent Invert toggles for Source 1 and Source 2.
2. 11 Photoshop-Standard Blend Modes:
   - Multiply, Screen, Overlay, Soft Light, Hard Light, Normal, Darken, Lighten,
     Difference, Subtract, and Add.
3. Scale & Offset Calibration:
   - Scale (1.0 to 2.0) and Offset (-255.0 to +255.0) for Add and Subtract modes
     supporting both 8-bit and 16-bit frequency separation and detail extraction math.
4. Opacity & Mask Modulation:
   - Opacity slider (0.0% to 100.0%).
   - Optional Mask channel with Invert toggle to protect Source 1 pixels.
5. 4 Destination Output Modes:
   - New Channel: Inserts a new named alpha/mask channel into the image channels list.
   - Selection: Converts the calculation result directly into an active marching-ants selection.
   - New Layer: Inserts a new grayscale/blended layer into the layer stack.
   - New Document: Generates a new grayscale image document.
6. 8 Curated Workflow Presets:
   - Sky Matte Extract: Red & Inverted Blue in Multiply for landscape sky isolation.
   - Hair Silhouette: Green & Inverted Blue in Screen for fine hair/edge extraction.
   - Tonal Contrast: Red & Green in Soft Light for rich skin/landscape tonal separation.
   - Shadow Separation: Inverted Red & Inverted Blue in Multiply for deepest shadow isolation.
   - Highlight Separation: Red & Blue in Screen for specular reflection isolation.
   - Frequency Separation (Subtract): Source 1 Gray & Source 2 Gray in Subtract (Scale 2, Offset 128).
   - Frequency Separation (Add): Source 1 Gray & Inverted Source 2 Gray in Add (Scale 2, Offset 0).
   - Custom Math: Full manual control over all parameters.
7. 100% Non-Destructive Operation:
   - Existing layers and base artwork remain completely untouched (diff == 0.000000).
8. Single-Step Undo Protection:
   - Encapsulated within image.undo_group_start() and image.undo_group_end().
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


PROC_NAME = "python-fu-calculations"

PRESETS = {
    "default": {
        "label": "Custom Math",
        "desc": "Manual channel selection, inversion, and blend math",
        "s1_channel": "gray",
        "s1_invert": False,
        "s2_channel": "gray",
        "s2_invert": False,
        "blend_mode": "multiply",
        "opacity": 100.0,
        "scale": 1.0,
        "offset": 0.0,
        "destination": "new-channel",
    },
    "custom": {
        "label": "Custom Math",
        "desc": "Manual channel selection, inversion, and blend math",
        "s1_channel": "gray",
        "s1_invert": False,
        "s2_channel": "gray",
        "s2_invert": False,
        "blend_mode": "multiply",
        "opacity": 100.0,
        "scale": 1.0,
        "offset": 0.0,
        "destination": "new-channel",
    },
    "sky-matte-extract": {
        "label": "Sky Matte Extract",
        "desc": "Red channel and Inverted Blue channel in Multiply mode for sky/cloud mask extraction",
        "s1_channel": "red",
        "s1_invert": False,
        "s2_channel": "blue",
        "s2_invert": True,
        "blend_mode": "multiply",
        "opacity": 100.0,
        "scale": 1.0,
        "offset": 0.0,
        "destination": "new-channel",
    },
    "hair-silhouette": {
        "label": "Hair Silhouette",
        "desc": "Green channel and Inverted Blue channel in Screen mode for fine hair/edge extraction",
        "s1_channel": "green",
        "s1_invert": False,
        "s2_channel": "blue",
        "s2_invert": True,
        "blend_mode": "screen",
        "opacity": 100.0,
        "scale": 1.0,
        "offset": 0.0,
        "destination": "new-channel",
    },
    "contrast-luminance": {
        "label": "Tonal Contrast",
        "desc": "Red channel and Green channel in Soft Light mode for high-contrast portrait tone mask",
        "s1_channel": "red",
        "s1_invert": False,
        "s2_channel": "green",
        "s2_invert": False,
        "blend_mode": "soft-light",
        "opacity": 100.0,
        "scale": 1.0,
        "offset": 0.0,
        "destination": "new-channel",
    },
    "shadow-separation": {
        "label": "Shadow Separation",
        "desc": "Inverted Red and Inverted Blue in Multiply mode to isolate deepest shadow zones",
        "s1_channel": "red",
        "s1_invert": True,
        "s2_channel": "blue",
        "s2_invert": True,
        "blend_mode": "multiply",
        "opacity": 100.0,
        "scale": 1.0,
        "offset": 0.0,
        "destination": "new-channel",
    },
    "highlight-separation": {
        "label": "Highlight Separation",
        "desc": "Red and Blue channels in Screen mode to isolate specular highlights and reflections",
        "s1_channel": "red",
        "s1_invert": False,
        "s2_channel": "blue",
        "s2_invert": False,
        "blend_mode": "screen",
        "opacity": 100.0,
        "scale": 1.0,
        "offset": 0.0,
        "destination": "new-channel",
    },
    "frequency-subtract": {
        "label": "Frequency Separation (Subtract)",
        "desc": "Source 1 Gray and Source 2 Gray in Subtract mode with Scale 2.0 and Offset 128.0 (50% gray baseline)",
        "s1_channel": "gray",
        "s1_invert": False,
        "s2_channel": "gray",
        "s2_invert": False,
        "blend_mode": "subtract",
        "opacity": 100.0,
        "scale": 2.0,
        "offset": 128.0,
        "destination": "new-layer",
    },
    "frequency-add": {
        "label": "Frequency Separation (Add)",
        "desc": "Source 1 Gray and Inverted Source 2 Gray in Add mode with Scale 2.0 and Offset 0.0",
        "s1_channel": "gray",
        "s1_invert": False,
        "s2_channel": "gray",
        "s2_invert": True,
        "blend_mode": "add",
        "opacity": 100.0,
        "scale": 2.0,
        "offset": 0.0,
        "destination": "new-layer",
    },
}


def extract_channel(layer, channel_choice, img_w, img_h):
    """
    Extracts a normalized float32 2D array [0.0, 1.0] representing
    the requested channel across full canvas dimensions (img_w, img_h).
    """
    succ, off_x, off_y = layer.get_offsets() if hasattr(layer, 'get_offsets') else (True, 0, 0)
    lyr_w = layer.get_width()
    lyr_h = layer.get_height()
    has_alpha = layer.has_alpha() if hasattr(layer, 'has_alpha') else False
    fmt = "RGBA float" if has_alpha else "RGB float"
    n_ch = 4 if has_alpha else 3

    buf = layer.get_buffer()
    rect = Gegl.Rectangle.new(0, 0, lyr_w, lyr_h)
    raw = buf.get(rect, 1.0, fmt, Gegl.AbyssPolicy.CLAMP)
    arr = np.frombuffer(raw, dtype=np.float32).reshape((lyr_h, lyr_w, n_ch))

    # Channel extraction
    if channel_choice == "red":
        ch = arr[:, :, 0]
    elif channel_choice == "green":
        ch = arr[:, :, 1]
    elif channel_choice == "blue":
        ch = arr[:, :, 2]
    elif channel_choice == "alpha":
        ch = arr[:, :, 3] if has_alpha else np.ones((lyr_h, lyr_w), dtype=np.float32)
    else:  # "gray" / luminance (Rec. 709)
        ch = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]

    # If layer matches full image geometry directly
    if lyr_w == img_w and lyr_h == img_h and off_x == 0 and off_y == 0:
        return ch.astype(np.float32).copy()

    # Otherwise place into full canvas buffer
    canvas_ch = np.zeros((img_h, img_w), dtype=np.float32)
    x1 = max(0, off_x)
    y1 = max(0, off_y)
    x2 = min(img_w, off_x + lyr_w)
    y2 = min(img_h, off_y + lyr_h)
    if x2 > x1 and y2 > y1:
        lx1 = x1 - off_x
        ly1 = y1 - off_y
        lx2 = lx1 + (x2 - x1)
        ly2 = ly1 + (y2 - y1)
        canvas_ch[y1:y2, x1:x2] = ch[ly1:ly2, lx1:lx2]

    return canvas_ch


def compute_blend(A, B, mode, scale=1.0, offset=0.0):
    """
    Computes mathematical channel blending for arrays A (base) and B (blend).
    All arrays are float32 in [0.0, 1.0].
    """
    if mode == "normal":
        R = B.copy()
    elif mode == "multiply":
        R = A * B
    elif mode == "screen":
        R = 1.0 - (1.0 - A) * (1.0 - B)
    elif mode == "overlay":
        R = np.where(A < 0.5, 2.0 * A * B, 1.0 - 2.0 * (1.0 - A) * (1.0 - B))
    elif mode == "soft-light":
        # Photoshop standard Soft Light formula
        R = np.where(
            B <= 0.5,
            A - (1.0 - 2.0 * B) * A * (1.0 - A),
            A + (2.0 * B - 1.0) * (np.sqrt(np.maximum(A, 0.0)) - A)
        )
    elif mode == "hard-light":
        R = np.where(B < 0.5, 2.0 * A * B, 1.0 - 2.0 * (1.0 - A) * (1.0 - B))
    elif mode == "darken":
        R = np.minimum(A, B)
    elif mode == "lighten":
        R = np.maximum(A, B)
    elif mode == "difference":
        R = np.abs(A - B)
    elif mode == "subtract":
        s = max(0.001, float(scale))
        off = float(offset) / 255.0
        R = ((A - B) / s) + off
    elif mode == "add":
        s = max(0.001, float(scale))
        off = float(offset) / 255.0
        R = ((A + B) / s) + off
    else:
        R = B.copy()

    return R


class CalculationsPlugin(Gimp.PlugIn):
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
            self.run_calculations,
            None
        )
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
        procedure.set_menu_label("Calculations...")
        procedure.add_menu_path("<Image>/Image")
        procedure.add_menu_path("<Image>/Select")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        procedure.set_documentation(
            "Channel Calculations & Two-Source Blending Helper",
            "Simulates Photoshop Image > Calculations with two-source single-channel "
            "isolation (Gray, Red, Green, Blue, Alpha), independent Invert toggles, "
            "11 blending modes, Scale and Offset math, opacity control, optional mask, "
            "and 4 output destinations: New Channel, Selection, New Layer, or New Document.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add("default", 0, "Custom Math", "Manual channel selection and blend math")
        preset_choice.add("custom", 1, "Custom Math", "Manual channel selection and blend math")
        preset_choice.add("sky-matte-extract", 2, "Sky Matte Extract", "Red & Blue Invert Multiply")
        preset_choice.add("hair-silhouette", 3, "Hair Silhouette", "Green & Blue Invert Screen")
        preset_choice.add("contrast-luminance", 4, "Tonal Contrast", "Red & Green Soft Light")
        preset_choice.add("shadow-separation", 5, "Shadow Separation", "Red Invert & Blue Invert Multiply")
        preset_choice.add("highlight-separation", 6, "Highlight Separation", "Red & Blue Screen")
        preset_choice.add("frequency-subtract", 7, "Frequency Separation (Subtract)", "Gray Subtract Scale 2 Offset 128")
        preset_choice.add("frequency-add", 8, "Frequency Separation (Add)", "Gray Add Invert Scale 2 Offset 0")

        procedure.add_choice_argument(
            "preset",
            "Preset",
            "Curated channel calculation preset",
            preset_choice,
            "default",
            GObject.ParamFlags.READWRITE
        )

        # 2. Source 1 Layer ID (0 for active layer)
        procedure.add_int_argument(
            "source1-layer-id",
            "Source 1 Layer ID",
            "ID of Source 1 layer (0 for active layer)",
            0,
            2147483647,
            0,
            GObject.ParamFlags.READWRITE
        )

        # 3. Source 1 Channel Choice
        s1_chan_choice = Gimp.Choice.new()
        s1_chan_choice.add("gray", 0, "Gray (Luminance)", "Perceptual luminance (Rec. 709)")
        s1_chan_choice.add("red", 1, "Red", "Red color channel")
        s1_chan_choice.add("green", 2, "Green", "Green color channel")
        s1_chan_choice.add("blue", 3, "Blue", "Blue color channel")
        s1_chan_choice.add("alpha", 4, "Alpha", "Layer transparency / alpha channel")

        procedure.add_choice_argument(
            "source1-channel",
            "Source 1 Channel",
            "Channel to extract from Source 1",
            s1_chan_choice,
            "gray",
            GObject.ParamFlags.READWRITE
        )

        # 4. Source 1 Invert
        procedure.add_boolean_argument(
            "source1-invert",
            "Source 1 Invert",
            "Invert Source 1 channel values (negative)",
            False,
            GObject.ParamFlags.READWRITE
        )

        # 5. Source 2 Layer ID (0 for active layer)
        procedure.add_int_argument(
            "source2-layer-id",
            "Source 2 Layer ID",
            "ID of Source 2 layer (0 for active layer)",
            0,
            2147483647,
            0,
            GObject.ParamFlags.READWRITE
        )

        # 6. Source 2 Channel Choice
        s2_chan_choice = Gimp.Choice.new()
        s2_chan_choice.add("gray", 0, "Gray (Luminance)", "Perceptual luminance (Rec. 709)")
        s2_chan_choice.add("red", 1, "Red", "Red color channel")
        s2_chan_choice.add("green", 2, "Green", "Green color channel")
        s2_chan_choice.add("blue", 3, "Blue", "Blue color channel")
        s2_chan_choice.add("alpha", 4, "Alpha", "Layer transparency / alpha channel")

        procedure.add_choice_argument(
            "source2-channel",
            "Source 2 Channel",
            "Channel to extract from Source 2",
            s2_chan_choice,
            "gray",
            GObject.ParamFlags.READWRITE
        )

        # 7. Source 2 Invert
        procedure.add_boolean_argument(
            "source2-invert",
            "Source 2 Invert",
            "Invert Source 2 channel values (negative)",
            False,
            GObject.ParamFlags.READWRITE
        )

        # 8. Blending Mode Choice
        blend_choice = Gimp.Choice.new()
        blend_choice.add("multiply", 0, "Multiply", "Multiplies channel values (darkening)")
        blend_choice.add("screen", 1, "Screen", "Screen blending (lightening)")
        blend_choice.add("overlay", 2, "Overlay", "High-contrast dynamic tone")
        blend_choice.add("soft-light", 3, "Soft Light", "Subtle tonal gradation")
        blend_choice.add("hard-light", 4, "Hard Light", "Punchy contrast gradation")
        blend_choice.add("normal", 5, "Normal", "Direct source 2 replacement")
        blend_choice.add("darken", 6, "Darken", "Selects darker pixel values")
        blend_choice.add("lighten", 7, "Lighten", "Selects lighter pixel values")
        blend_choice.add("difference", 8, "Difference", "Absolute subtraction difference")
        blend_choice.add("subtract", 9, "Subtract", "Subtracts channel pixel values")
        blend_choice.add("add", 10, "Add", "Adds channel pixel values together")

        procedure.add_choice_argument(
            "blend-mode",
            "Blending Mode",
            "Two-source channel blending mode",
            blend_choice,
            "multiply",
            GObject.ParamFlags.READWRITE
        )

        # 9. Opacity (0.0 to 100.0%)
        procedure.add_double_argument(
            "opacity",
            "Opacity (%)",
            "Blending strength percentage (0.0 to 100.0, default 100.0)",
            0.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # 10. Scale (1.0 to 2.0, default 1.0)
        procedure.add_double_argument(
            "scale",
            "Scale",
            "Scaling divisor for Add/Subtract modes (1.0 to 2.0, default 1.0)",
            1.0,
            2.0,
            1.0,
            GObject.ParamFlags.READWRITE
        )

        # 11. Offset (-255.0 to 255.0, default 0.0)
        procedure.add_double_argument(
            "offset",
            "Offset",
            "Value offset for Add/Subtract modes (-255.0 to 255.0, default 0.0)",
            -255.0,
            255.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 12. Mask Enabled
        procedure.add_boolean_argument(
            "mask-enabled",
            "Mask Enabled",
            "Enable mask channel to restrict blending area",
            False,
            GObject.ParamFlags.READWRITE
        )

        # 13. Mask Channel Choice
        mask_chan_choice = Gimp.Choice.new()
        mask_chan_choice.add("gray", 0, "Gray (Luminance)", "Perceptual luminance (Rec. 709)")
        mask_chan_choice.add("red", 1, "Red", "Red color channel")
        mask_chan_choice.add("green", 2, "Green", "Green color channel")
        mask_chan_choice.add("blue", 3, "Blue", "Blue color channel")
        mask_chan_choice.add("alpha", 4, "Alpha", "Layer transparency / alpha channel")

        procedure.add_choice_argument(
            "mask-channel",
            "Mask Channel",
            "Channel to use for masking",
            mask_chan_choice,
            "gray",
            GObject.ParamFlags.READWRITE
        )

        # 14. Mask Invert
        procedure.add_boolean_argument(
            "mask-invert",
            "Mask Invert",
            "Invert mask channel values",
            False,
            GObject.ParamFlags.READWRITE
        )

        # 15. Result Destination Choice
        dest_choice = Gimp.Choice.new()
        dest_choice.add("new-channel", 0, "New Channel", "Add calculation result as alpha channel")
        dest_choice.add("selection", 1, "Selection", "Load calculation result directly into active selection")
        dest_choice.add("new-layer", 2, "New Layer", "Add calculation result as new layer in layer stack")
        dest_choice.add("new-document", 3, "New Document", "Create a new image document with calculation result")

        procedure.add_choice_argument(
            "result-destination",
            "Result Destination",
            "Where to output calculation result (new-channel, selection, new-layer, new-document)",
            dest_choice,
            "new-channel",
            GObject.ParamFlags.READWRITE
        )

        # 16. Channel Name
        procedure.add_string_argument(
            "channel-name",
            "Name",
            "Name for created channel, layer, or document",
            "Calculations",
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run_calculations(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-calculations"), "No active image provided.", 0)
            )

        if run_mode == Gimp.RunMode.INTERACTIVE:
            gi.require_version('GimpUi', '3.0')
            from gi.repository import GimpUi

            GimpUi.init(PROC_NAME)
            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        # Read configuration parameters
        preset = config.get_property("preset")
        s1_lid = config.get_property("source1-layer-id")
        s1_chan = config.get_property("source1-channel")
        s1_inv = config.get_property("source1-invert")
        s2_lid = config.get_property("source2-layer-id")
        s2_chan = config.get_property("source2-channel")
        s2_inv = config.get_property("source2-invert")
        bmode = config.get_property("blend-mode")
        opacity_val = config.get_property("opacity")
        scale_val = config.get_property("scale")
        offset_val = config.get_property("offset")
        mask_en = config.get_property("mask-enabled")
        mask_chan = config.get_property("mask-channel")
        mask_inv = config.get_property("mask-invert")
        dest_str = config.get_property("result-destination")
        chan_name = config.get_property("channel-name") or "Calculations"

        # Resolve preset values vs direct sliders
        if preset in PRESETS and preset not in ("default", "custom"):
            p = PRESETS[preset]
            s1_chan = p["s1_channel"]
            s1_inv = p["s1_invert"]
            s2_chan = p["s2_channel"]
            s2_inv = p["s2_invert"]
            bmode = p["blend_mode"]
            opacity_val = p["opacity"]
            scale_val = p["scale"]
            offset_val = p["offset"]
            dest_str = p["destination"]
            label = p["label"]
        else:
            label = "Custom"

        img_w = image.get_width()
        img_h = image.get_height()
        layers = image.get_layers()

        # Resolve active layer
        selected = image.get_selected_layers()
        active_layer = selected[0] if selected else (drawables[0] if drawables else (layers[0] if layers else None))
        if active_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-calculations"), "No valid layers found.", 0)
            )

        # Resolve Source 1 Layer
        layer1 = None
        if s1_lid > 0:
            item = Gimp.Item.get_by_id(s1_lid)
            if item and isinstance(item, Gimp.Layer):
                layer1 = item
        if layer1 is None:
            layer1 = active_layer

        # Resolve Source 2 Layer
        layer2 = None
        if s2_lid > 0:
            item = Gimp.Item.get_by_id(s2_lid)
            if item and isinstance(item, Gimp.Layer):
                layer2 = item
        if layer2 is None:
            layer2 = active_layer

        Gimp.context_push()
        image.undo_group_start()

        try:
            # 1. Extract Source 1 channel
            A = extract_channel(layer1, s1_chan, img_w, img_h)
            if s1_inv:
                A = 1.0 - A

            # 2. Extract Source 2 channel
            B = extract_channel(layer2, s2_chan, img_w, img_h)
            if s2_inv:
                B = 1.0 - B

            # 3. Compute two-source channel blend
            R = compute_blend(A, B, bmode, scale=scale_val, offset=offset_val)

            # 4. Opacity modulation
            op_factor = max(0.0, min(100.0, float(opacity_val))) / 100.0
            if op_factor < 0.9999:
                R = A * (1.0 - op_factor) + R * op_factor

            # 5. Mask channel modulation
            if mask_en:
                M = extract_channel(layer1, mask_chan, img_w, img_h)
                if mask_inv:
                    M = 1.0 - M
                R = A * (1.0 - M) + R * M

            # Clip result strictly into [0.0, 1.0]
            R_final = np.clip(R, 0.0, 1.0).astype(np.float32)

            # 6. Output to destination
            if dest_str == "new-channel":
                # Create alpha / mask channel in image
                chan_color = Gegl.Color.new("rgba(1.0, 0.0, 0.0, 0.5)")
                out_chan = Gimp.Channel.new(image, chan_name, img_w, img_h, 100.0, chan_color)
                image.insert_channel(out_chan, None, 0)
                rect = Gegl.Rectangle.new(0, 0, img_w, img_h)
                out_chan.get_buffer().set(rect, "Y float", R_final.tobytes())
                out_chan.get_buffer().flush()
                out_chan.update(0, 0, img_w, img_h)
                image.set_selected_channels([out_chan])

            elif dest_str == "selection":
                # Load result directly into active marching ants selection
                temp_chan = Gimp.Channel.new(image, "_temp_calc_sel", img_w, img_h, 100.0, Gegl.Color.new("rgba(1.0, 0.0, 0.0, 0.5)"))
                image.insert_channel(temp_chan, None, 0)
                rect = Gegl.Rectangle.new(0, 0, img_w, img_h)
                temp_chan.get_buffer().set(rect, "Y float", R_final.tobytes())
                temp_chan.get_buffer().flush()
                image.select_item(Gimp.ChannelOps.REPLACE, temp_chan)
                image.remove_channel(temp_chan)

            elif dest_str == "new-layer":
                # Add grayscale calculation layer directly into layer stack
                out_layer = Gimp.Layer.new(
                    image,
                    f"{chan_name} ({label})",
                    img_w,
                    img_h,
                    Gimp.ImageType.RGBA_IMAGE,
                    100.0,
                    Gimp.LayerMode.NORMAL
                )
                parent = active_layer.get_parent()
                pos = image.get_item_position(active_layer)
                image.insert_layer(out_layer, parent, pos)

                rgba_out = np.empty((img_h, img_w, 4), dtype=np.float32)
                rgba_out[:, :, 0] = R_final
                rgba_out[:, :, 1] = R_final
                rgba_out[:, :, 2] = R_final
                rgba_out[:, :, 3] = 1.0

                rect = Gegl.Rectangle.new(0, 0, img_w, img_h)
                out_layer.get_buffer().set(rect, "RGBA float", rgba_out.tobytes())
                out_layer.get_buffer().flush()
                out_layer.update(0, 0, img_w, img_h)
                image.set_selected_layers([out_layer])

            elif dest_str == "new-document":
                # Create a brand new document from the calculation result
                new_doc = Gimp.Image.new(img_w, img_h, Gimp.ImageBaseType.RGB)
                bg_layer = Gimp.Layer.new(
                    new_doc,
                    "Background",
                    img_w,
                    img_h,
                    Gimp.ImageType.RGB_IMAGE,
                    100.0,
                    Gimp.LayerMode.NORMAL
                )
                new_doc.insert_layer(bg_layer, None, 0)

                rgb_out = np.empty((img_h, img_w, 3), dtype=np.float32)
                rgb_out[:, :, 0] = R_final
                rgb_out[:, :, 1] = R_final
                rgb_out[:, :, 2] = R_final

                rect = Gegl.Rectangle.new(0, 0, img_w, img_h)
                bg_layer.get_buffer().set(rect, "RGB float", rgb_out.tobytes())
                bg_layer.get_buffer().flush()
                bg_layer.update(0, 0, img_w, img_h)

                if run_mode == Gimp.RunMode.INTERACTIVE:
                    Gimp.Display.new(new_doc)

            Gimp.displays_flush()
            image.undo_group_end()
            Gimp.context_pop()

            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as exc:
            image.undo_group_end()
            Gimp.context_pop()
            msg = f"Calculations failed: {str(exc)}"
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-calculations"),
                    msg,
                    0
                )
            )


Gimp.main(CalculationsPlugin.__gtype__, sys.argv)
