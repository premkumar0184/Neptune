#!/usr/bin/env python3
"""
PhotoGIMP Non-Destructive Light & Tonal Range Helper Plugin for GIMP 3.x

Creates a dedicated non-destructive Light adjustment layer providing a unified
6-point photographic tonal control panel (Exposure, Contrast, Highlights, Shadows,
Whites, and Blacks) directly reproducing Adobe Photoshop's Light adjustment layer
and Camera Raw Basic panel.

Photoshop Equivalence:
- Topics.txt line 106: Adjust image lighting with Light.
- photoshop_docs.md Section 110 lines 3305-3348:
  "Learn how to fine-tune image lighting with Light adjustment layer in professional
   photoeditor on desktop. Use the Light adjustment layer to improve image lighting
   with precise controls for Exposure, Contrast, Highlights, Shadows, Whites, and Blacks.
   Adjust overall brightness and contrast, recover shadow detail, refine highlights,
   and control the brightest and darkest areas of your image.
   Edits made with Light are non-destructive. Modify settings, add layer masks to control
   where the effect is applied, and continue editing the layers below without permanently
   changing the original image.
   Controls:
   * Exposure: Brightens or darkens the image.
   * Contrast: Increases or decreases the difference between light and dark areas.
   * Highlights: Adjusts detail in lighter areas.
   * Shadows: Adjusts detail in darker areas.
   * Whites: Adjusts the brightest tones in the image.
   * Blacks: Adjusts the darkest tones in the image."

Key Advantages over stock destructive editing:
1. 100% Non-Destructive: Duplicates the active drawable into an isolated adjustment layer.
2. Unified 6-Point Darkroom Pipeline:
   - Exposure: Global linear EV stop scaling via GEGL gegl:exposure.
   - Contrast: Midtone S-curve contrast expansion/compression via GEGL gegl:brightness-contrast.
   - Highlights & Shadows: Local dynamic range recovery via GEGL gegl:shadows-highlights.
   - Whites & Blacks: Extreme tonal threshold clipping & matte adjustments via GEGL gegl:levels.
3. Curated Lighting Presets:
   - Brighten & Pop: Balanced exposure lift with punchy contrast, restored highlights, and open shadows.
   - Recover Backlit Subject: High dynamic range recovery lifting dark subjects while compressing skies.
   - Deep Contrast & Rich Darks: Dramatic, moody lighting with deep crushed blacks and punchy highlights.
   - Soft Low-Contrast Wash: Gentle matte look with lifted faded blacks and soft highlights.
   - High-Key Studio: Bright, luminous studio lighting with clean white highlights and open shadows.
   - Custom Sliders: Full independent control over all 6 tonal parameters.
4. Reveal-All Layer Mask: Attached automatically for selective brush painting.
5. Live Opacity Control: Adjust overall adjustment strength at any point in the workflow.
6. Target Layer Invariance: Source image pixels underneath remain 100% untouched.
"""

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
    "brighten-pop": {
        "label": "Brighten & Pop",
        "exposure": 0.35,
        "contrast": 20.0,
        "highlights": -15.0,
        "shadows": 25.0,
        "whites": 15.0,
        "blacks": -10.0,
    },
    "backlit-recovery": {
        "label": "Recover Backlit Subject",
        "exposure": 0.50,
        "contrast": -15.0,
        "highlights": -40.0,
        "shadows": 65.0,
        "whites": 5.0,
        "blacks": 10.0,
    },
    "deep-contrast": {
        "label": "Deep Contrast & Rich Darks",
        "exposure": -0.20,
        "contrast": 40.0,
        "highlights": 20.0,
        "shadows": -25.0,
        "whites": 25.0,
        "blacks": -35.0,
    },
    "soft-wash": {
        "label": "Soft Low-Contrast Wash",
        "exposure": 0.25,
        "contrast": -30.0,
        "highlights": -20.0,
        "shadows": 35.0,
        "whites": -15.0,
        "blacks": 30.0,
    },
    "high-key": {
        "label": "High-Key Studio",
        "exposure": 0.75,
        "contrast": -10.0,
        "highlights": -10.0,
        "shadows": 30.0,
        "whites": 40.0,
        "blacks": 15.0,
    },
    "custom": {
        "label": "Custom Light & Tone",
        "exposure": 0.0,
        "contrast": 0.0,
        "highlights": 0.0,
        "shadows": 0.0,
        "whites": 0.0,
        "blacks": 0.0,
    },
}


def light_tone(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-light-tone"),
                "No valid image provided.",
                0
            )
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-light-tone')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    # Read configuration parameters
    preset = config.get_property('preset')
    exposure = config.get_property('exposure')
    contrast = config.get_property('contrast')
    highlights = config.get_property('highlights')
    shadows = config.get_property('shadows')
    whites = config.get_property('whites')
    blacks = config.get_property('blacks')
    opacity = config.get_property('opacity')
    add_mask = config.get_property('add-mask')

    # Apply preset values or custom values
    if preset != "custom" and preset in PRESETS:
        p_cfg = PRESETS[preset]
        exp_val = p_cfg["exposure"]
        con_val = p_cfg["contrast"]
        hl_val = p_cfg["highlights"]
        sh_val = p_cfg["shadows"]
        wh_val = p_cfg["whites"]
        bl_val = p_cfg["blacks"]
        layer_name = f"Light & Tone ({p_cfg['label']})"
    else:
        exp_val = float(exposure)
        con_val = float(contrast)
        hl_val = float(highlights)
        sh_val = float(shadows)
        wh_val = float(whites)
        bl_val = float(blacks)
        layer_name = "Light & Tone (Custom)"

    # Resolve target drawable
    target_drawable = None
    if drawables and len(drawables) > 0:
        target_drawable = drawables[0]
    else:
        selected = image.get_selected_drawables()
        if len(selected) > 0:
            target_drawable = selected[0]
        else:
            layers = image.get_layers()
            if len(layers) > 0:
                target_drawable = layers[0]

    if target_drawable is None:
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-light-tone"),
                "No target drawable found to apply light and tonal range adjustment.",
                0
            )
        )

    Gimp.context_push()
    image.undo_group_start()

    try:
        # Create non-destructive adjustment layer duplicating active target drawable
        light_layer = Gimp.Layer.new_from_drawable(target_drawable, image)
        light_layer.set_name(layer_name)
        light_layer.set_opacity(float(opacity))
        light_layer.set_mode(Gimp.LayerMode.NORMAL)

        # Insert immediately above target drawable
        parent = target_drawable.get_parent()
        pos = image.get_item_position(target_drawable)
        image.insert_layer(light_layer, parent, pos)

        # ----------------------------------------------------------------------
        # Stage 1: Exposure Adjustment (gegl:exposure)
        # ----------------------------------------------------------------------
        if abs(exp_val) > 0.001:
            f_exp = Gimp.DrawableFilter.new(light_layer, "gegl:exposure", "")
            c_exp = f_exp.get_config()
            c_exp.set_property("exposure", float(exp_val))
            light_layer.merge_filter(f_exp)

        # ----------------------------------------------------------------------
        # Stage 2: Contrast S-Curve Adjustment (gegl:brightness-contrast)
        # In GEGL, contrast default is 1.0 (identity).
        # ----------------------------------------------------------------------
        if abs(con_val) > 0.001:
            f_con = Gimp.DrawableFilter.new(light_layer, "gegl:brightness-contrast", "")
            c_con = f_con.get_config()
            contrast_mult = 1.0 + (float(con_val) / 100.0) * 0.5
            c_con.set_property("contrast", float(contrast_mult))
            light_layer.merge_filter(f_con)

        # ----------------------------------------------------------------------
        # Stage 3: Highlights & Shadows Recovery (gegl:shadows-highlights)
        # In GEGL shadows-highlights: positive shadows lifts darks,
        # and negative highlights compresses/recovers blown highlights.
        # ----------------------------------------------------------------------
        if abs(sh_val) > 0.001 or abs(hl_val) > 0.001:
            f_sh = Gimp.DrawableFilter.new(light_layer, "gegl:shadows-highlights", "")
            c_sh = f_sh.get_config()
            c_sh.set_property("shadows", float(sh_val))
            c_sh.set_property("highlights", -float(hl_val))
            c_sh.set_property("radius", 50.0)
            c_sh.set_property("compress", 50.0)
            light_layer.merge_filter(f_sh)

        # ----------------------------------------------------------------------
        # Stage 4: Whites & Blacks Thresholds (gegl:levels)
        # ----------------------------------------------------------------------
        if abs(wh_val) > 0.001 or abs(bl_val) > 0.001:
            in_low = 0.0
            in_high = 1.0
            out_low = 0.0
            out_high = 1.0

            # Whites: Positive shifts in-high down (brightening/clipping whites)
            # Negative pulls out-high down (compressing extreme whites)
            if wh_val > 0.0:
                in_high = max(0.5, 1.0 - (float(wh_val) / 100.0) * 0.20)
            elif wh_val < 0.0:
                out_high = max(0.5, 1.0 + (float(wh_val) / 100.0) * 0.20)

            # Blacks: Negative shifts in-low up (deepening/crushing deep blacks)
            # Positive lifts out-low up (producing soft/faded matte blacks)
            if bl_val < 0.0:
                in_low = min(0.5, (-float(bl_val) / 100.0) * 0.15)
            elif bl_val > 0.0:
                out_low = min(0.5, (float(bl_val) / 100.0) * 0.15)

            f_lev = Gimp.DrawableFilter.new(light_layer, "gegl:levels", "")
            c_lev = f_lev.get_config()
            c_lev.set_property("in-low", float(in_low))
            c_lev.set_property("in-high", float(in_high))
            c_lev.set_property("out-low", float(out_low))
            c_lev.set_property("out-high", float(out_high))
            light_layer.merge_filter(f_lev)

        # ----------------------------------------------------------------------
        # Stage 5: Reveal-All Layer Mask
        # ----------------------------------------------------------------------
        if add_mask:
            mask = light_layer.create_mask(Gimp.AddMaskType.WHITE)
            light_layer.add_mask(mask)

        # Set newly created adjustment layer as selected
        image.set_selected_layers([light_layer])
        Gimp.displays_flush()

    except Exception as e:
        image.undo_group_end()
        Gimp.context_pop()
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-light-tone"),
                f"Light and tone processing failed: {str(e)}",
                0
            )
        )

    image.undo_group_end()
    Gimp.context_pop()

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


class LightTonePlugin(Gimp.PlugIn):
    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-light-tone"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            light_tone,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        procedure.set_menu_label("Light and _Tone...")
        procedure.set_documentation(
            "Creates a non-destructive Light adjustment layer with 6-point tonal controls",
            "Creates a dedicated non-destructive Light adjustment layer duplicating active drawable. "
            "Provides unified 6-point photographic tonal controls for Exposure (EV), Contrast, Highlights, "
            "Shadows, Whites, and Blacks directly reproducing Adobe Photoshop's Light adjustment layer "
            "and Camera Raw Basic panel.",
            name
        )
        procedure.set_attribution("Antigravity Ralph / PhotoGIMP", "PhotoGIMP", "2026")

        procedure.add_menu_path("<Image>/Colors")
        procedure.add_menu_path("<Image>/Filters/Retouching")
        procedure.add_menu_path("<Image>/Layer")

        # Preset Choice Argument
        preset_choice = Gimp.Choice.new()
        preset_choice.add(
            "brighten-pop",
            0,
            "Brighten & Pop",
            "Balanced exposure lift with punchy contrast, restored highlights, and open shadows"
        )
        preset_choice.add(
            "backlit-recovery",
            1,
            "Recover Backlit Subject",
            "High dynamic range recovery lifting dark subjects while compressing skies"
        )
        preset_choice.add(
            "deep-contrast",
            2,
            "Deep Contrast & Rich Darks",
            "Dramatic, moody lighting with deep crushed blacks and punchy highlights"
        )
        preset_choice.add(
            "soft-wash",
            3,
            "Soft Low-Contrast Wash",
            "Gentle matte look with lifted faded blacks and soft highlights"
        )
        preset_choice.add(
            "high-key",
            4,
            "High-Key Studio",
            "Bright, luminous studio lighting with clean white highlights and open shadows"
        )
        preset_choice.add(
            "custom",
            5,
            "Custom Light & Tone",
            "Manually adjust Exposure, Contrast, Highlights, Shadows, Whites, and Blacks sliders"
        )

        procedure.add_choice_argument(
            "preset",
            "_Preset",
            "Photographic lighting preset look",
            preset_choice,
            "brighten-pop",
            GObject.ParamFlags.READWRITE
        )

        # Exposure Slider (-5.0 to +5.0 EV, default 0.0)
        procedure.add_double_argument(
            "exposure",
            "_Exposure (EV)",
            "Overall image exposure brightness in EV stops (-5.0 to +5.0 EV)",
            -5.0,
            5.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # Contrast Slider (-100% to +100%, default 0.0)
        procedure.add_double_argument(
            "contrast",
            "_Contrast (%)",
            "Midtone S-curve contrast (-100% to +100%)",
            -100.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # Highlights Slider (-100% to +100%, default 0.0)
        procedure.add_double_argument(
            "highlights",
            "_Highlights (%)",
            "Detail in lighter areas; negative compresses blown highlights, positive boosts (-100% to +100%)",
            -100.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # Shadows Slider (-100% to +100%, default 0.0)
        procedure.add_double_argument(
            "shadows",
            "_Shadows (%)",
            "Detail in darker areas; positive lifts shadows, negative deepens (-100% to +100%)",
            -100.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # Whites Slider (-100% to +100%, default 0.0)
        procedure.add_double_argument(
            "whites",
            "_Whites (%)",
            "Threshold for extreme specular highlights and white point (-100% to +100%)",
            -100.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # Blacks Slider (-100% to +100%, default 0.0)
        procedure.add_double_argument(
            "blacks",
            "_Blacks (%)",
            "Threshold for extreme shadows and deep black point (-100% to +100%)",
            -100.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # Layer Opacity Slider (10% to 100%, default 100%)
        procedure.add_double_argument(
            "opacity",
            "Layer _Opacity (%)",
            "Overall opacity of the Light & Tone adjustment layer (10% to 100%)",
            10.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # Reveal-All Layer Mask Option
        procedure.add_boolean_argument(
            "add-mask",
            "_Attach Layer Mask",
            "Attach a reveal-all white layer mask for selective brush painting",
            True,
            GObject.ParamFlags.READWRITE
        )

        return procedure


Gimp.main(LightTonePlugin.__gtype__, sys.argv)
