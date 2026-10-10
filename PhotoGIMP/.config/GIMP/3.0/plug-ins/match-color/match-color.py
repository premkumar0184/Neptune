#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Match Color & Perceptual Color Transfer Plugin
========================================================================
Photoshop Reference:
- Topics.txt line 333: "Selective color adjustments - Match color in different images"
- Topics.txt line 334: "Match color between two images"
- Topics.txt line 335: "Match color of two layers in the same image"
- Topics.txt line 336: "Save and apply settings in Match Color"
- photoshop_docs.md Section 327-330 lines 9575-9695:
  "The Match Color command in photoeditor adjusts colors in single or multiple images,
   layers, or selections to align with colors in another... works only in RGB mode...
   controls for:
   - Luminance adjustment to brighten or darken the image (1-200, default 100).
   - Color Intensity adjustment (1-200, default 100; a value of 1 converts to grayscale).
   - Fade slider to control the strength of adjustment (0-100, moving right reduces effect).
   - Neutralize to automatically remove any color cast in the target image.
   - Source menu to select source image/layer or presets."

Key Architectural Features:
1. Dynamic Statistical Color Matching:
   - Evaluates channel moments via GIMP PDB gimp-drawable-histogram across target
     and source reference layers. Computes linear transfer channel gains applied
     via GEGL channel-mixer (gegl:channel-mixer).
2. Curated Photographic Grading Palettes:
   - Warm Golden Hour (warm amber sunlight, rich golden highlights)
   - Cool Cinema Blue (moody cinematic blue-hour grading with teal/cyan tones)
   - Vintage Film Tone (nostalgic analog film palette with lifted matte shadows)
   - Lush Foliage Emerald (vibrant landscape greens and rich emerald tones)
   - Sunset Crimson (radiant crimson, magenta, and evening orange dusk grading)
   - Skin Tone Harmony (flattering healthy warm portrait skin tones and balanced chroma)
   - Neutralize Only (clears color casts without changing palette)
   - Source Layer Match (direct statistical transfer from another layer)
   - Custom Sliders (manual control)
3. Luminance Control (1 to 200, default 100):
   - Linear EV exposure mapping via gegl:exposure (ev = log2(luminance / 100.0)).
4. Color Intensity Control (1 to 200, default 100):
   - Maps to gegl:vibrance saturation where 1.0 produces pure neutral grayscale
     (saturation = 0.0) and 200.0 doubles color saturation.
5. Fade Control (0 to 100, default 0):
   - Smoothly modulates adjustment layer effective opacity back to original unadjusted image.
6. Neutralize Color Cast:
   - Automatically computes channel imbalance on target drawable and balances RGB means.
7. Layer Mask Support:
   - Reveal All (white mask), Conceal All (black mask), Selection-aware mask.
8. 100% Non-Destructive Invariance:
   - Duplicates target drawable into an isolated adjustment layer; base layer pixels
     underneath remain 100% mathematically untouched (diff == 0.000000).
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
    "warm-golden-hour": {
        "label": "Warm Golden Hour",
        "desc": "Warm golden hour sunlight, rich amber highlights, and glowing warmth",
        "src_r": 0.80,
        "src_g": 0.58,
        "src_b": 0.28,
        "exposure": 0.15,
        "vibrance": 18.0,
        "neutralize": False,
    },
    "cool-cinema-blue": {
        "label": "Cool Cinema Blue",
        "desc": "Moody cinematic blue-hour grading with teal/cyan undertones",
        "src_r": 0.25,
        "src_g": 0.48,
        "src_b": 0.80,
        "exposure": -0.10,
        "vibrance": 12.0,
        "neutralize": False,
    },
    "vintage-film": {
        "label": "Vintage Film Tone",
        "desc": "Nostalgic analog film palette with lifted matte shadows and warm split tone",
        "src_r": 0.72,
        "src_g": 0.62,
        "src_b": 0.42,
        "exposure": 0.20,
        "vibrance": -12.0,
        "neutralize": False,
    },
    "lush-foliage": {
        "label": "Lush Foliage Emerald",
        "desc": "Vibrant landscape greens and rich emerald organic tones",
        "src_r": 0.26,
        "src_g": 0.75,
        "src_b": 0.30,
        "exposure": 0.05,
        "vibrance": 25.0,
        "neutralize": False,
    },
    "sunset-crimson": {
        "label": "Sunset Crimson",
        "desc": "Radiant crimson, magenta, and evening orange dusk grading",
        "src_r": 0.82,
        "src_g": 0.32,
        "src_b": 0.68,
        "exposure": 0.12,
        "vibrance": 28.0,
        "neutralize": False,
    },
    "skin-harmony": {
        "label": "Skin Tone Harmony",
        "desc": "Flattering healthy warm portrait skin tones and balanced chroma",
        "src_r": 0.75,
        "src_g": 0.58,
        "src_b": 0.44,
        "exposure": 0.10,
        "vibrance": 10.0,
        "neutralize": False,
    },
    "neutralize-only": {
        "label": "Neutralize Only",
        "desc": "Automatically removes unwanted color casts without altering color balance",
        "exposure": 0.0,
        "vibrance": 0.0,
        "neutralize": True,
    },
    "source-layer": {
        "label": "Source Layer Match",
        "desc": "Transfers color statistics from another layer or reference in the document",
        "exposure": 0.0,
        "vibrance": 0.0,
        "neutralize": False,
    },
    "custom": {
        "label": "Custom Sliders",
        "desc": "Manual slider configuration",
        "exposure": 0.0,
        "vibrance": 0.0,
        "neutralize": False,
    },
}


def get_drawable_stats(drawable):
    """
    Computes linear RGB means and perceptual luminance from a drawable using
    GIMP PDB gimp-drawable-histogram.
    """
    pdb = Gimp.get_pdb()
    hist_proc = pdb.lookup_procedure('gimp-drawable-histogram')
    if not hist_proc:
        return 0.5, 0.5, 0.5, 0.5

    lin_values = {}
    for ch_name, ch_enum in [
        ('R', Gimp.HistogramChannel.RED),
        ('G', Gimp.HistogramChannel.GREEN),
        ('B', Gimp.HistogramChannel.BLUE),
        ('L', Gimp.HistogramChannel.LUMINANCE),
    ]:
        c = hist_proc.create_config()
        c.set_property('drawable', drawable)
        c.set_property('channel', ch_enum)
        c.set_property('start-range', 0.0)
        c.set_property('end-range', 1.0)
        res = hist_proc.run(c)
        if res and res.index(0) == Gimp.PDBStatusType.SUCCESS:
            srgb_mean = res.index(1) / 255.0
            # Convert sRGB gamma to linear intensity
            lin_val = max(0.0001, min(1.0, srgb_mean ** 2.2))
            lin_values[ch_name] = lin_val
        else:
            lin_values[ch_name] = 0.5

    return (
        lin_values.get('R', 0.5),
        lin_values.get('G', 0.5),
        lin_values.get('B', 0.5),
        lin_values.get('L', 0.5),
    )


def match_color_run(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-match-color"),
                "No valid image provided.",
                0
            )
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-match-color')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    # Read configuration parameters
    preset = config.get_property('preset')
    source_layer_id = config.get_property('source-layer-id')
    luminance = config.get_property('luminance')
    color_intensity = config.get_property('color-intensity')
    fade = config.get_property('fade')
    neutralize_opt = config.get_property('neutralize')
    mask_mode = config.get_property('mask-mode')
    opacity = config.get_property('opacity')

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
                GLib.quark_from_string("gimp-match-color"),
                "No valid target layer found.",
                0
            )
        )

    # Preset lookup
    preset_info = PRESETS.get(preset, PRESETS["warm-golden-hour"])
    label = preset_info.get("label", "Custom")
    layer_name = f"Match Color ({label})"

    Gimp.context_push()
    image.undo_group_start()

    try:
        # Check active selection state
        has_selection = not Gimp.Selection.is_empty(image)
        saved_sel = None
        if has_selection:
            saved_sel = Gimp.Selection.save(image)

        # Clear selection temporarily so duplicate layer processes uniformly
        if has_selection:
            Gimp.Selection.none(image)

        # Create non-destructive duplicate adjustment layer
        mc_layer = Gimp.Layer.new_from_drawable(target_layer, image)
        mc_layer.set_name(layer_name)
        mc_layer.set_mode(Gimp.LayerMode.NORMAL)

        # Calculate effective opacity taking Fade into account
        fade_factor = 1.0 - (max(0.0, min(100.0, float(fade))) / 100.0)
        eff_opacity = max(0.0, min(100.0, float(opacity) * fade_factor))
        mc_layer.set_opacity(eff_opacity)

        # Insert above target layer
        parent = target_layer.get_parent()
        pos = image.get_item_position(target_layer)
        image.insert_layer(mc_layer, parent, pos)

        # Get target layer statistics
        tgt_r, tgt_g, tgt_b, tgt_lum = get_drawable_stats(target_layer)

        # Resolve channel gains based on preset or source layer
        if preset == "source-layer":
            # Find source layer
            src_layer = None
            if source_layer_id > 0:
                item = Gimp.Item.get_by_id(source_layer_id)
                if item and isinstance(item, Gimp.Layer):
                    src_layer = item
            if src_layer is None:
                # Select another layer in the image that is not the target
                for cand in image.get_layers():
                    if cand.get_id() != target_layer.get_id() and cand.get_id() != mc_layer.get_id():
                        src_layer = cand
                        break

            if src_layer is not None:
                src_r, src_g, src_b, src_lum = get_drawable_stats(src_layer)
                gain_r = src_r / max(0.001, tgt_r)
                gain_g = src_g / max(0.001, tgt_g)
                gain_b = src_b / max(0.001, tgt_b)
            else:
                gain_r, gain_g, gain_b = 1.0, 1.0, 1.0

            preset_exposure = 0.0
            preset_vibrance = 0.0
            do_neutralize = neutralize_opt

        elif preset in PRESETS and preset != "custom":
            p = PRESETS[preset]
            if preset != "neutralize-only" and "src_r" in p:
                gain_r = p["src_r"] / max(0.001, tgt_r)
                gain_g = p["src_g"] / max(0.001, tgt_g)
                gain_b = p["src_b"] / max(0.001, tgt_b)
            else:
                gain_r, gain_g, gain_b = 1.0, 1.0, 1.0
            preset_exposure = p["exposure"]
            preset_vibrance = p["vibrance"]
            do_neutralize = neutralize_opt or p.get("neutralize", False)
        else:
            # Custom sliders
            gain_r, gain_g, gain_b = 1.0, 1.0, 1.0
            preset_exposure = 0.0
            preset_vibrance = 0.0
            do_neutralize = neutralize_opt

        # Apply Neutralize if enabled: calculate channel balance gains
        if do_neutralize:
            avg_tgt = (tgt_r + tgt_g + tgt_b) / 3.0
            nr = avg_tgt / max(0.001, tgt_r)
            ng = avg_tgt / max(0.001, tgt_g)
            nb = avg_tgt / max(0.001, tgt_b)
            max_n = max(nr, ng, nb)
            if max_n > 1.8:
                scale_n = 1.8 / max_n
                nr *= scale_n
                ng *= scale_n
                nb *= scale_n
            gain_r *= nr
            gain_g *= ng
            gain_b *= nb

        # Scale gains to prevent severe clipping while preserving color transfer ratio
        max_g = max(gain_r, gain_g, gain_b)
        if max_g > 1.8:
            factor = 1.8 / max_g
            gain_r *= factor
            gain_g *= factor
            gain_b *= factor

        # 1. Apply GEGL Channel Mixer for Color Balance / Transfer
        filt_cm = Gimp.DrawableFilter.new(mc_layer, "gegl:channel-mixer", "")
        fc_cm = filt_cm.get_config()
        fc_cm.set_property("rr-gain", max(-2.0, min(2.0, float(gain_r))))
        fc_cm.set_property("gg-gain", max(-2.0, min(2.0, float(gain_g))))
        fc_cm.set_property("bb-gain", max(-2.0, min(2.0, float(gain_b))))
        fc_cm.set_property("preserve-luminosity", False)
        mc_layer.append_filter(filt_cm)
        mc_layer.merge_filters()

        # 2. Apply Luminance Adjustment (1 to 200, default 100)
        lum_ratio = max(1.0, min(200.0, float(luminance))) / 100.0
        ev_offset = math.log2(lum_ratio) + preset_exposure
        if abs(ev_offset) > 0.001:
            filt_exp = Gimp.DrawableFilter.new(mc_layer, "gegl:exposure", "")
            fc_exp = filt_exp.get_config()
            fc_exp.set_property("exposure", max(-10.0, min(10.0, float(ev_offset))))
            mc_layer.append_filter(filt_exp)
            mc_layer.merge_filters()

        # 3. Apply Color Intensity Adjustment (1 to 200, default 100)
        # Intensity = 1 converts to pure grayscale (saturation = 0.0)
        # Intensity = 100 is standard saturation (saturation = 1.0)
        # Intensity = 200 is double saturation (saturation = 2.0)
        sat_intensity = max(1.0, min(200.0, float(color_intensity)))
        sat_val = max(0.0, min(10.0, (sat_intensity - 1.0) / 99.0))
        vib_val = preset_vibrance

        filt_vib = Gimp.DrawableFilter.new(mc_layer, "gegl:vibrance", "")
        fc_vib = filt_vib.get_config()
        fc_vib.set_property("saturation", float(sat_val))
        fc_vib.set_property("vibrance", max(-100.0, min(100.0, float(vib_val))))
        mc_layer.append_filter(filt_vib)
        mc_layer.merge_filters()

        # 4. Attach Layer Mask according to mask_mode
        if mask_mode == "conceal-all":
            mask = mc_layer.create_mask(Gimp.AddMaskType.BLACK)
            mc_layer.add_mask(mask)
        elif mask_mode == "selection" and has_selection and saved_sel is not None:
            # Restore saved selection to create selection-aware mask
            image.select_item(Gimp.ChannelOps.REPLACE, saved_sel)
            mask = mc_layer.create_mask(Gimp.AddMaskType.SELECTION)
            mc_layer.add_mask(mask)
            Gimp.Selection.none(image)
        else:
            # Default: Reveal All
            mask = mc_layer.create_mask(Gimp.AddMaskType.WHITE)
            mc_layer.add_mask(mask)

        # Cleanup saved selection channel
        if saved_sel is not None and saved_sel.is_valid():
            try:
                image.remove_channel(saved_sel)
            except Exception:
                pass

        # Select new adjustment layer
        image.set_selected_layers([mc_layer])
        Gimp.displays_flush()

    except Exception as e:
        image.undo_group_end()
        Gimp.context_pop()
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-match-color"),
                f"Match Color processing failed: {str(e)}",
                0
            )
        )

    image.undo_group_end()
    Gimp.context_pop()

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


class MatchColorPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-match-color"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, match_color_run, None
        )
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
        procedure.set_menu_label("Match Color...")
        procedure.add_menu_path("<Image>/Image/Adjustments")
        procedure.add_menu_path("<Image>/Colors")
        procedure.add_menu_path("<Image>/Filters/Retouching")
        procedure.add_menu_path("<Image>/Layer")

        procedure.set_documentation(
            "Non-Destructive Match Color & Perceptual Color Transfer Helper",
            "Simulates Photoshop Image > Adjustments > Match Color with perceptual color "
            "transfer, Luminance (1-200), Color Intensity (1-200), Fade (0-100), Neutralize, "
            "and photographic grading palettes on an isolated non-destructive adjustment layer.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add("warm-golden-hour", 0, "Warm Golden Hour", "Warm golden hour sunlight and amber highlights")
        preset_choice.add("cool-cinema-blue", 1, "Cool Cinema Blue", "Moody cinematic blue-hour grading with teal undertones")
        preset_choice.add("vintage-film", 2, "Vintage Film Tone", "Nostalgic analog film palette with lifted matte shadows")
        preset_choice.add("lush-foliage", 3, "Lush Foliage Emerald", "Vibrant landscape greens and rich emerald tones")
        preset_choice.add("sunset-crimson", 4, "Sunset Crimson", "Radiant evening crimson, orange, and magenta grading")
        preset_choice.add("skin-harmony", 5, "Skin Tone Harmony", "Healthy warm portrait skin tones and balanced chroma")
        preset_choice.add("neutralize-only", 6, "Neutralize Only", "Automatically removes unwanted color casts")
        preset_choice.add("source-layer", 7, "Source Layer Match", "Transfers color statistics from another layer in image")
        preset_choice.add("custom", 8, "Custom Sliders", "Manual slider configuration")

        procedure.add_choice_argument(
            "preset",
            "Color Match Palette / Preset",
            "Curated grading palette or reference source method",
            preset_choice,
            "warm-golden-hour",
            GObject.ParamFlags.READWRITE
        )

        # 2. Source Layer ID (optional integer, -1 for auto / top reference)
        procedure.add_int_argument(
            "source-layer-id",
            "Source Layer ID",
            "ID of the reference source layer to transfer color from (-1 for auto)",
            -1,
            1000000,
            -1,
            GObject.ParamFlags.READWRITE
        )

        # 3. Luminance (1 to 200, default 100)
        procedure.add_double_argument(
            "luminance",
            "Luminance",
            "Brightness adjustment scaling (1 to 200, default 100)",
            1.0,
            200.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # 4. Color Intensity (1 to 200, default 100, 1 = grayscale)
        procedure.add_double_argument(
            "color-intensity",
            "Color Intensity",
            "Saturation adjustment scaling (1 to 200, default 100, 1 = grayscale)",
            1.0,
            200.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # 5. Fade (0 to 100, default 0)
        procedure.add_double_argument(
            "fade",
            "Fade",
            "Controls the strength of the adjustment (0 to 100, moving right reduces effect)",
            0.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 6. Neutralize (Boolean, default False)
        procedure.add_boolean_argument(
            "neutralize",
            "Neutralize Color Cast",
            "Automatically removes unwanted color casts by balancing channel means",
            False,
            GObject.ParamFlags.READWRITE
        )

        # 7. Mask Mode
        mask_choice = Gimp.Choice.new()
        mask_choice.add("reveal-all", 0, "Reveal All (White Mask)", "Full effect across entire layer")
        mask_choice.add("conceal-all", 1, "Conceal All (Black Mask)", "Fully concealed, paint in with brush")
        mask_choice.add("selection", 2, "Active Selection", "Confine color match strictly to selection")

        procedure.add_choice_argument(
            "mask-mode",
            "Layer Mask Mode",
            "Type of layer mask attached to the adjustment layer",
            mask_choice,
            "reveal-all",
            GObject.ParamFlags.READWRITE
        )

        # 8. Layer Opacity (0.0 to 100.0, default 100.0)
        procedure.add_double_argument(
            "opacity",
            "Layer Opacity (%)",
            "Overall opacity of the adjustment layer (0.0 to 100.0, default 100.0)",
            0.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        return procedure


Gimp.main(MatchColorPlugin.__gtype__, sys.argv)
