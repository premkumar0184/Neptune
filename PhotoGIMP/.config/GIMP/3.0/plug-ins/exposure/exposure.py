#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Exposure Adjustment Layer & Tonal Range Helper Plugin
================================================================================
Simulates Adobe Photoshop's non-destructive Exposure adjustment layer:
  - Photoshop Menu: Layer > New Adjustment Layer > Exposure...
  - Photoshop Menu: Image > Adjustments > Exposure...
  - Photoshop Docs: Section 338 lines 9935-9985 (adjust-hdr-exposure-and-toning.html)
  - Topics.txt: Lines 93-96, 347

Photoshop Linear Color Space Exposure Tone Equation:
  I' = ((I * 2^exposure) + offset) ** (1.0 / gamma)

Controls & Parity:
1. Three Photographic Parameters:
   - Exposure: -5.0 to +5.0 EV stops (default 0.0). Power-of-two intensity scaling
     affecting the highlight end of the tonal scale with minimal impact on deep blacks.
   - Offset: -0.50 to +0.50 (default 0.0). Additive offset shifting shadow and black-point levels.
   - Gamma: 0.10 to 5.00 (default 1.0). Power-curve midtone contrast correction.
2. Curated Photographic Presets:
   - Default / Reset (EV 0.0, Offset 0.0, Gamma 1.0)
   - +1 Stop Overexposure (EV 1.0, Offset 0.0, Gamma 1.0)
   - +2 Stops Overexposure (EV 2.0, Offset 0.0, Gamma 1.0)
   - -1 Stop Underexposure (EV -1.0, Offset 0.0, Gamma 1.0)
   - -2 Stops Underexposure (EV -2.0, Offset 0.0, Gamma 1.0)
   - Shadow Lift (EV 0.0, Offset +0.10, Gamma 1.25)
   - Highlight Recovery (EV -1.20, Offset 0.0, Gamma 1.35)
   - Dynamic Compression (EV +0.60, Offset -0.08, Gamma 0.90)
   - Custom sliders
3. Non-Destructive Layer Architecture:
   - New Adjustment Layer (default): Duplicates active drawable into a dedicated adjustment layer,
     leaving underlying artwork 100% untouched (diff == 0.000000).
   - In-Place: Direct active layer buffer transformation.
4. Professional Blend Modes & Opacity:
   - Normal, Luminosity (Luminance), Multiply, Screen, Overlay, Soft Light.
   - Opacity slider (0.0 to 100.0%).
5. Layer Mask Integration:
   - Auto (selection mask if active, else none), None, Reveal-All (white),
     Conceal-All (black), Active Selection.
6. Single-Step Undo Protection:
   - Encapsulated within image.undo_group_start() and image.undo_group_end().
"""

import sys
import numpy as np
import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
from gi.repository import GLib


PROC_NAME = "python-fu-exposure"

BLEND_MODES = {
    "normal": Gimp.LayerMode.NORMAL,
    "luminosity": Gimp.LayerMode.LUMINANCE,
    "multiply": Gimp.LayerMode.MULTIPLY,
    "screen": Gimp.LayerMode.SCREEN,
    "overlay": Gimp.LayerMode.OVERLAY,
    "soft-light": Gimp.LayerMode.SOFTLIGHT,
}

PRESETS = {
    "default": {
        "label": "Default Reset",
        "exposure": 0.0,
        "offset": 0.0,
        "gamma": 1.0,
    },
    "plus-1-stop": {
        "label": "+1 Stop Overexposure",
        "exposure": 1.0,
        "offset": 0.0,
        "gamma": 1.0,
    },
    "plus-2-stops": {
        "label": "+2 Stops Overexposure",
        "exposure": 2.0,
        "offset": 0.0,
        "gamma": 1.0,
    },
    "minus-1-stop": {
        "label": "-1 Stop Underexposure",
        "exposure": -1.0,
        "offset": 0.0,
        "gamma": 1.0,
    },
    "minus-2-stops": {
        "label": "-2 Stops Underexposure",
        "exposure": -2.0,
        "offset": 0.0,
        "gamma": 1.0,
    },
    "shadow-lift": {
        "label": "Shadow Lift",
        "exposure": 0.0,
        "offset": 0.10,
        "gamma": 1.25,
    },
    "highlight-recovery": {
        "label": "Highlight Recovery",
        "exposure": -1.20,
        "offset": 0.0,
        "gamma": 1.35,
    },
    "dynamic-compression": {
        "label": "Dynamic Compression",
        "exposure": 0.60,
        "offset": -0.08,
        "gamma": 0.90,
    },
    "custom": {
        "label": "Custom",
        "exposure": 0.0,
        "offset": 0.0,
        "gamma": 1.0,
    },
}


def apply_exposure_transformation(layer, image, exposure_val, offset_val, gamma_val, respect_selection=False):
    """Applies Photoshop exposure equation to layer buffer with float precision."""
    width = layer.get_width()
    height = layer.get_height()
    buf = layer.get_buffer()
    rect = Gegl.Rectangle.new(0, 0, width, height)
    raw = buf.get(rect, 1.0, "RGBA float", Gegl.AbyssPolicy.NONE)
    arr = np.frombuffer(raw, dtype=np.float32).reshape((height, width, 4)).copy()

    # RGB channels
    rgb = arr[:, :, :3]
    ev_scale = float(2.0 ** float(exposure_val))
    off = float(offset_val)
    gam = float(max(0.01, float(gamma_val)))
    inv_gamma = 1.0 / gam

    # Photoshop formula: I' = ((I * 2^EV) + offset) ** (1/gamma)
    scaled = np.maximum(0.0, rgb * ev_scale + off)
    if abs(gam - 1.0) > 1e-4:
        scaled = np.power(scaled, inv_gamma)
    new_rgb = np.clip(scaled, 0.0, 1.0)

    if respect_selection and not Gimp.Selection.is_empty(image):
        sel = image.get_selection()
        sel_buf = sel.get_buffer()
        succ, off_x, off_y = layer.get_offsets()
        rect_sel = Gegl.Rectangle.new(off_x, off_y, width, height)
        sel_raw = sel_buf.get(rect_sel, 1.0, "Y float", Gegl.AbyssPolicy.NONE)
        sel_mask = np.frombuffer(sel_raw, dtype=np.float32).reshape((height, width, 1))
        arr[:, :, :3] = np.clip(rgb * (1.0 - sel_mask) + new_rgb * sel_mask, 0.0, 1.0)
    else:
        arr[:, :, :3] = new_rgb

    buf.set(rect, "RGBA float", arr.tobytes())
    buf.flush()
    layer.update(0, 0, width, height)


class ExposurePlugin(Gimp.PlugIn):
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
            self.run_exposure,
            None
        )
        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )
        procedure.set_menu_label("Exposure...")
        procedure.add_menu_path("<Image>/Layer/New Adjustment Layer")
        procedure.add_menu_path("<Image>/Image/Adjustments")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        procedure.set_documentation(
            "Exposure Adjustment Layer (Non-Destructive)",
            "Simulates Photoshop Layer > New Adjustment Layer > Exposure and Image > Adjustments > Exposure "
            "with linear EV exposure stops, shadow offset, and midtone gamma power curve.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Preset
        preset_choice = Gimp.Choice.new()
        preset_choice.add("default", 0, "Default (Reset)", "Reset exposure settings (EV 0.0, Offset 0.0, Gamma 1.0)")
        preset_choice.add("plus-1-stop", 1, "+1 Stop Overexposure", "Brighten highlights by +1.0 EV stop")
        preset_choice.add("plus-2-stops", 2, "+2 Stops Overexposure", "High-key brighten by +2.0 EV stops")
        preset_choice.add("minus-1-stop", 3, "-1 Stop Underexposure", "Rescue highlights by -1.0 EV stop")
        preset_choice.add("minus-2-stops", 4, "-2 Stops Underexposure", "Low-key underexpose by -2.0 EV stops")
        preset_choice.add("shadow-lift", 5, "Shadow Lift", "Lift shadow black levels and brighten midtones")
        preset_choice.add("highlight-recovery", 6, "Highlight Recovery", "Compress harsh highlights and preserve midtones")
        preset_choice.add("dynamic-compression", 7, "Dynamic Compression", "HDR tonal range expansion with balanced contrast")
        preset_choice.add("custom", 8, "Custom Sliders", "Use manual exposure, offset, and gamma sliders")

        procedure.add_choice_argument(
            "preset",
            "Preset",
            "Curated photographic exposure preset or custom sliders",
            preset_choice,
            "default",
            GObject.ParamFlags.READWRITE
        )

        # 2. Exposure (-5.0 to +5.0 EV stops)
        procedure.add_double_argument(
            "exposure",
            "Exposure (EV)",
            "Linear intensity power-of-two EV stops (-5.0 to +5.0, default 0.0)",
            -5.0,
            5.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 3. Offset (-0.50 to +0.50)
        procedure.add_double_argument(
            "offset",
            "Offset",
            "Shadow and black point additive bias (-0.50 to +0.50, default 0.0)",
            -0.50,
            0.50,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 4. Gamma (0.10 to 5.00)
        procedure.add_double_argument(
            "gamma",
            "Gamma",
            "Midtone power-curve correction exponent (0.10 to 5.00, default 1.0)",
            0.10,
            5.00,
            1.0,
            GObject.ParamFlags.READWRITE
        )

        # 5. Blend Mode
        mode_choice = Gimp.Choice.new()
        mode_choice.add("normal", 0, "Normal", "Standard layer blending")
        mode_choice.add("luminosity", 1, "Luminosity", "Luminance tone blending preserving colors")
        mode_choice.add("multiply", 2, "Multiply", "Darkening shadow blend")
        mode_choice.add("screen", 3, "Screen", "Lightening highlight blend")
        mode_choice.add("overlay", 4, "Overlay", "High-contrast dynamic tone")
        mode_choice.add("soft-light", 5, "Soft Light", "Subtle tonal gradation")

        procedure.add_choice_argument(
            "blend-mode",
            "Blend Mode",
            "Photoshop blend mode for adjustment layer (normal, luminosity, multiply, screen, overlay, soft-light)",
            mode_choice,
            "normal",
            GObject.ParamFlags.READWRITE
        )

        # 6. Opacity (0.0 to 100.0%)
        procedure.add_double_argument(
            "opacity",
            "Opacity (%)",
            "Adjustment layer opacity percentage (0.0 to 100.0, default 100.0)",
            0.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # 7. Output Mode
        output_choice = Gimp.Choice.new()
        output_choice.add("new-layer", 0, "New Adjustment Layer", "Non-destructive adjustment layer preserving source pixels")
        output_choice.add("in-place", 1, "In-Place (Active Layer)", "Modify active layer buffer directly")

        procedure.add_choice_argument(
            "output-mode",
            "Output Mode",
            "Target destination for exposure adjustment (new-layer, in-place)",
            output_choice,
            "new-layer",
            GObject.ParamFlags.READWRITE
        )

        # 8. Layer Mask Type
        mask_choice = Gimp.Choice.new()
        mask_choice.add("auto", 0, "Auto (Selection Mask if selected)", "Selection mask if selection is active, else no mask")
        mask_choice.add("none", 1, "None", "No layer mask attached")
        mask_choice.add("reveal-all", 2, "Reveal-All (White)", "White editable mask")
        mask_choice.add("conceal-all", 3, "Conceal-All (Black)", "Black mask for selective brush painting")
        mask_choice.add("selection", 4, "Active Selection", "Convert active selection into editable mask")

        procedure.add_choice_argument(
            "mask-type",
            "Layer Mask",
            "Layer mask attached to adjustment layer (auto, none, reveal-all, conceal-all, selection)",
            mask_choice,
            "auto",
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run_exposure(self, procedure, run_mode, image, drawables, config, run_data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("python-fu-exposure")
            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        # Read configuration parameters
        preset = config.get_property("preset")
        exp_val = config.get_property("exposure")
        off_val = config.get_property("offset")
        gam_val = config.get_property("gamma")
        bmode_str = config.get_property("blend-mode")
        opacity_val = config.get_property("opacity")
        out_mode = config.get_property("output-mode")
        mask_str = config.get_property("mask-type")

        # Resolve numerical exposure values from preset or sliders
        if preset in PRESETS and preset != "custom":
            p = PRESETS[preset]
            ev_final = float(p["exposure"])
            off_final = float(p["offset"])
            gam_final = float(p["gamma"])
            label = p["label"]
        else:
            ev_final = float(exp_val)
            off_final = float(off_val)
            gam_final = float(gam_val)
            label = "Custom"

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
                    GLib.quark_from_string("gimp-exposure"),
                    "No valid target layer found for exposure adjustment.",
                    0
                )
            )

        Gimp.context_push()
        image.undo_group_start()

        try:
            if out_mode == "new-layer":
                # Create non-destructive duplicate layer
                layer_name = f"Exposure Adjustment ({label})"
                adj_layer = Gimp.Layer.new_from_drawable(target_layer, image)
                adj_layer.set_name(layer_name)
                adj_layer.set_opacity(max(0.0, min(100.0, float(opacity_val))))
                adj_layer.set_mode(BLEND_MODES.get(bmode_str, Gimp.LayerMode.NORMAL))

                # Insert immediately above target layer
                parent = target_layer.get_parent()
                pos = image.get_item_position(target_layer)
                image.insert_layer(adj_layer, parent, pos)

                # Apply exposure transformation to adjustment layer
                apply_exposure_transformation(adj_layer, image, ev_final, off_final, gam_final, respect_selection=False)

                # Attach layer mask if requested
                has_sel = not Gimp.Selection.is_empty(image)
                if mask_str == "auto":
                    if has_sel:
                        mask = adj_layer.create_mask(Gimp.AddMaskType.SELECTION)
                        adj_layer.add_mask(mask)
                elif mask_str == "reveal-all":
                    mask = adj_layer.create_mask(Gimp.AddMaskType.WHITE)
                    adj_layer.add_mask(mask)
                elif mask_str == "conceal-all":
                    mask = adj_layer.create_mask(Gimp.AddMaskType.BLACK)
                    adj_layer.add_mask(mask)
                elif mask_str == "selection":
                    if has_sel:
                        mask = adj_layer.create_mask(Gimp.AddMaskType.SELECTION)
                        adj_layer.add_mask(mask)

                # Set new layer active
                image.set_selected_layers([adj_layer])

            else:
                # In-place modification of active layer
                apply_exposure_transformation(target_layer, image, ev_final, off_final, gam_final, respect_selection=True)

            Gimp.displays_flush()
            image.undo_group_end()
            Gimp.context_pop()

            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as exc:
            image.undo_group_end()
            Gimp.context_pop()
            msg = "Exposure adjustment failed: " + str(exc)
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-exposure"),
                    msg,
                    0
                )
            )


Gimp.main(ExposurePlugin.__gtype__, sys.argv)
