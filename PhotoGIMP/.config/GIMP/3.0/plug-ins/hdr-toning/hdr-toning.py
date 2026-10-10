#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive HDR Toning & Tone Mapping Plugin
===========================================================
Photoshop Reference:
- Topics.txt line 347: "HDR and channel manipulation - Adjust HDR exposure and toning"
- Topics.txt line 106: "Adjust image lighting with Light"
- Topics.txt line 269: "Adjust image shadows and highlights"
- photoshop_docs.md Section 338 lines 9951-9985:
  "HDR Toning provides multiple tone-mapping methods including Local Adaptation,
   Equalize Histogram, Exposure and Gamma, and Highlight Compression. Each method
   offers different controls for managing conversion from HDR to lower bit depths...
   In the HDR Toning dialog, select a Method from the dropdown menu and adjust the
   available settings to control contrast, exposure, and tonal range...
   Edge Glow, Tone and Detail, Color controls (Vibrance, Saturation)..."

Key Architectural Features:
1. Tone Mapping Methods:
   - Local Adaptation: High-fidelity local tone mapping via GEGL Mantiuk (gegl:mantiuk06)
     with adaptive contrast, detail scaling, and Edge Glow halo filtering.
   - Equalize Histogram: Full-spectrum dynamic range stretch (gegl:stretch-contrast)
     expanding compressed tonal distributions.
   - Exposure and Gamma: Linear EV exposure compensation (gegl:exposure) and
     midtone power-law gamma curves (gegl:gamma).
   - Highlight Compression: Compresses dynamic range peaks to prevent highlight clipping
     while opening up deep shadow detail.
2. Edge Glow / Detail Microcontrast:
   - Configurable Edge Glow Radius (1.0 to 100.0px) and Strength (0.0 to 5.0) via gegl:unsharp-mask,
     producing the iconic HDR microcontrast halo and razor-sharp structural acutance.
3. Exposure, Gamma & Dynamic Range Recovery:
   - Linear Exposure (-5.0 to +5.0 EV) and midtone Gamma curve (0.1 to 3.0).
   - Shadow Recovery (0 to 100%) and Highlight Recovery (0 to 100%).
4. Intelligent Color Controls:
   - Vibrance (-100 to +100%) and Saturation (-100 to +100%).
   - True Monochrome HDR mode when Saturation is set to -100%.
5. Curated Photographic Presets:
   - Default Photorealistic, High Dynamic Vivid, Dramatic Monochrome, Architectural Crisp,
     Surreal Dreamy, Night Cityglow, Custom.
6. Flexible Layer Mask Modes:
   - Reveal-All White Mask, Conceal-All Black Mask, Active Selection Mask.
7. Non-Destructive Adjustment Layer:
   - Unlike Photoshop's destructive command that flattens all document layers, this plugin
     creates an isolated non-destructive layer duplicating the target drawable.
   - Base layer source pixels underneath remain 100% mathematically untouched (diff == 0.000000).
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
    "default-photorealistic": {
        "label": "Default Photorealistic",
        "desc": "Natural tone expansion with subtle microcontrast and balanced vibrance",
        "method": "local-adaptation",
        "edge_glow_radius": 15.0,
        "edge_glow_strength": 0.8,
        "gamma": 1.0,
        "exposure": 0.0,
        "detail": 1.5,
        "shadow_recovery": 25.0,
        "highlight_recovery": 20.0,
        "vibrance": 20.0,
        "saturation": 5.0,
        "opacity": 100.0,
    },
    "high-dynamic-vivid": {
        "label": "High Dynamic Vivid",
        "desc": "Bold HDR look with dramatic local contrast and saturated color pop",
        "method": "local-adaptation",
        "edge_glow_radius": 25.0,
        "edge_glow_strength": 1.8,
        "gamma": 0.90,
        "exposure": 0.25,
        "detail": 3.0,
        "shadow_recovery": 40.0,
        "highlight_recovery": 35.0,
        "vibrance": 45.0,
        "saturation": 20.0,
        "opacity": 100.0,
    },
    "dramatic-monochrome": {
        "label": "Dramatic Monochrome",
        "desc": "High acutance black-and-white tone-mapped architectural/fine-art style",
        "method": "local-adaptation",
        "edge_glow_radius": 20.0,
        "edge_glow_strength": 2.0,
        "gamma": 0.95,
        "exposure": 0.10,
        "detail": 3.5,
        "shadow_recovery": 30.0,
        "highlight_recovery": 30.0,
        "vibrance": 0.0,
        "saturation": -100.0,
        "opacity": 100.0,
    },
    "architectural-crisp": {
        "label": "Architectural Crisp",
        "desc": "Clean structural detail, sharp edge glow, and open shadow luminosity",
        "method": "equalize-histogram",
        "edge_glow_radius": 12.0,
        "edge_glow_strength": 1.4,
        "gamma": 1.05,
        "exposure": 0.0,
        "detail": 2.0,
        "shadow_recovery": 35.0,
        "highlight_recovery": 25.0,
        "vibrance": 15.0,
        "saturation": 5.0,
        "opacity": 85.0,
    },
    "surreal-dreamy": {
        "label": "Surreal Dreamy",
        "desc": "Intense microcontrast detail with compressed highlights and ethereal tone",
        "method": "local-adaptation",
        "edge_glow_radius": 35.0,
        "edge_glow_strength": 2.5,
        "gamma": 0.85,
        "exposure": -0.20,
        "detail": 4.5,
        "shadow_recovery": 50.0,
        "highlight_recovery": 50.0,
        "vibrance": 35.0,
        "saturation": 15.0,
        "opacity": 100.0,
    },
    "night-cityglow": {
        "label": "Night Cityglow",
        "desc": "Opens up deep shadow details, stabilizes bright neon highlights, and enriches night tonality",
        "method": "highlight-compression",
        "edge_glow_radius": 18.0,
        "edge_glow_strength": 1.2,
        "gamma": 0.90,
        "exposure": 0.30,
        "detail": 2.0,
        "shadow_recovery": 60.0,
        "highlight_recovery": 40.0,
        "vibrance": 30.0,
        "saturation": 15.0,
        "opacity": 100.0,
    },
    "custom": {
        "label": "Custom HDR Toning",
        "desc": "Manual slider configuration",
        "method": "local-adaptation",
        "edge_glow_radius": 15.0,
        "edge_glow_strength": 1.0,
        "gamma": 1.0,
        "exposure": 0.0,
        "detail": 1.5,
        "shadow_recovery": 25.0,
        "highlight_recovery": 20.0,
        "vibrance": 20.0,
        "saturation": 10.0,
        "opacity": 100.0,
    },
}


class HdrToningPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-hdr-toning"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, self.run, None
        )
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
        procedure.set_menu_label("HDR Toning...")
        procedure.add_menu_path("<Image>/Image/Adjustments")
        procedure.add_menu_path("<Image>/Filters/Enhance")
        procedure.add_menu_path("<Image>/Filters/Retouching")
        procedure.add_menu_path("<Image>/Layer")

        procedure.set_documentation(
            "Non-Destructive HDR Toning & Tone Mapping Helper",
            "Simulates Photoshop Image > Adjustments > HDR Toning with tone mapping methods, "
            "Edge Glow microcontrast, Exposure, Gamma, dynamic range recovery, and color vibrance "
            "on an isolated non-destructive adjustment layer without flattening document layers.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add("default-photorealistic", 0, "Default Photorealistic", "Natural tone expansion with subtle microcontrast")
        preset_choice.add("high-dynamic-vivid", 1, "High Dynamic Vivid", "Dramatic local contrast and saturated color pop")
        preset_choice.add("dramatic-monochrome", 2, "Dramatic Monochrome", "High acutance black-and-white tone-mapped style")
        preset_choice.add("architectural-crisp", 3, "Architectural Crisp", "Clean structural detail, sharp edge glow, open shadows")
        preset_choice.add("surreal-dreamy", 4, "Surreal Dreamy", "Intense microcontrast with compressed highlights")
        preset_choice.add("night-cityglow", 5, "Night Cityglow", "Opens deep shadow details and stabilizes bright neon highlights")
        preset_choice.add("custom", 6, "Custom HDR Toning", "Manual slider configuration")

        procedure.add_choice_argument(
            "preset",
            "HDR Toning Preset",
            "Curated photographic HDR preset",
            preset_choice,
            "default-photorealistic",
            GObject.ParamFlags.READWRITE
        )

        # 2. Method Choice
        method_choice = Gimp.Choice.new()
        method_choice.add("local-adaptation", 0, "Local Adaptation", "Local tone mapping with Edge Glow halo and microcontrast")
        method_choice.add("equalize-histogram", 1, "Equalize Histogram", "High-contrast histogram dynamic range equalization")
        method_choice.add("exposure-gamma", 2, "Exposure and Gamma", "Linear EV exposure compensation and midtone power gamma curve")
        method_choice.add("highlight-compression", 3, "Highlight Compression", "Compresses highlight peaks while lifting deep shadows")

        procedure.add_choice_argument(
            "method",
            "Tone Mapping Method",
            "Algorithm for dynamic range compression and tone mapping",
            method_choice,
            "local-adaptation",
            GObject.ParamFlags.READWRITE
        )

        # 3. Edge Glow Radius
        procedure.add_double_argument(
            "edge-glow-radius",
            "Edge Glow Radius (px)",
            "Radius of the local contrast halo in pixels (1.0 to 100.0, default 15.0)",
            1.0,
            100.0,
            15.0,
            GObject.ParamFlags.READWRITE
        )

        # 4. Edge Glow Strength
        procedure.add_double_argument(
            "edge-glow-strength",
            "Edge Glow Strength",
            "Intensity of the local contrast Edge Glow halo (0.0 to 5.0, default 0.8)",
            0.0,
            5.0,
            0.8,
            GObject.ParamFlags.READWRITE
        )

        # 5. Gamma
        procedure.add_double_argument(
            "gamma",
            "Midtone Gamma",
            "Midtone gamma curve (<1.0 brightens midtones, >1.0 darkens) (0.1 to 3.0, default 1.0)",
            0.1,
            3.0,
            1.0,
            GObject.ParamFlags.READWRITE
        )

        # 6. Exposure (EV)
        procedure.add_double_argument(
            "exposure",
            "Exposure (EV)",
            "Linear exposure compensation in exposure values (-5.0 to +5.0 EV, default 0.0)",
            -5.0,
            5.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 7. Detail
        procedure.add_double_argument(
            "detail",
            "Tone & Detail",
            "Microcontrast texture detail boost factor (0.0 to 10.0, default 1.5)",
            0.0,
            10.0,
            1.5,
            GObject.ParamFlags.READWRITE
        )

        # 8. Shadow Recovery
        procedure.add_double_argument(
            "shadow-recovery",
            "Shadow Recovery (%)",
            "Lifts deep underexposed shadow details (0.0% to 100.0%, default 25.0%)",
            0.0,
            100.0,
            25.0,
            GObject.ParamFlags.READWRITE
        )

        # 9. Highlight Recovery
        procedure.add_double_argument(
            "highlight-recovery",
            "Highlight Recovery (%)",
            "Pulls down overexposed highlight peaks (0.0% to 100.0%, default 20.0%)",
            0.0,
            100.0,
            20.0,
            GObject.ParamFlags.READWRITE
        )

        # 10. Vibrance
        procedure.add_double_argument(
            "vibrance",
            "Color Vibrance (%)",
            "Smart saturation boost prioritizing muted colors and skin tones (-100.0% to +100.0%, default 20.0%)",
            -100.0,
            100.0,
            20.0,
            GObject.ParamFlags.READWRITE
        )

        # 11. Saturation
        procedure.add_double_argument(
            "saturation",
            "Color Saturation (%)",
            "Global saturation adjustment; -100% creates monochrome HDR (-100.0% to +100.0%, default 5.0%)",
            -100.0,
            100.0,
            5.0,
            GObject.ParamFlags.READWRITE
        )

        # 12. Opacity
        procedure.add_double_argument(
            "opacity",
            "Layer Opacity (%)",
            "Overall opacity of the HDR Toning adjustment layer (10.0% to 100.0%, default 100.0%)",
            10.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # 13. Mask Mode Choice
        mask_choice = Gimp.Choice.new()
        mask_choice.add("reveal-all", 0, "Reveal-All White Mask", "Applies HDR Toning across entire canvas")
        mask_choice.add("conceal-all", 1, "Conceal-All Black Mask", "Hides effect until selectively painted with white brush")
        mask_choice.add("selection", 2, "Active Selection Mask", "Confines HDR Toning strictly to active selection boundary")

        procedure.add_choice_argument(
            "mask-mode",
            "Layer Mask Mode",
            "Initial layer mask configuration (reveal-all, conceal-all, selection)",
            mask_choice,
            "reveal-all",
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run(self, procedure, run_mode, image, drawables, config, data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            Gimp.ui_init("hdr-toning.py")
            dialog = Gimp.ProcedureDialog.new(procedure, config, "HDR Toning & Tone Mapping")
            dialog.fill([
                "preset", "method", "edge-glow-radius", "edge-glow-strength",
                "gamma", "exposure", "detail", "shadow-recovery",
                "highlight-recovery", "vibrance", "saturation", "opacity", "mask-mode"
            ])
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        # Resolve target drawable safely
        target_drawable = None
        selected_layers = image.get_selected_layers()
        if len(selected_layers) > 0:
            target_drawable = selected_layers[0]
        elif drawables and len(drawables) > 0:
            d = drawables[0]
            if hasattr(d, 'is_layer_mask') and d.is_layer_mask():
                target_drawable = image.get_layers()[0] if len(image.get_layers()) > 0 else None
            else:
                target_drawable = d
        else:
            layers = image.get_layers()
            if len(layers) > 0:
                target_drawable = layers[0]

        if target_drawable is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-hdr-toning"),
                    "No target drawable found to apply HDR Toning.",
                    0
                )
            )

        preset_key = config.get_property("preset") or "default-photorealistic"
        if preset_key not in PRESETS:
            preset_key = "default-photorealistic"
        preset_cfg = PRESETS[preset_key]

        if preset_key == "custom":
            method_val = config.get_property("method") or "local-adaptation"
            eg_radius_val = config.get_property("edge-glow-radius")
            eg_strength_val = config.get_property("edge-glow-strength")
            gamma_val = config.get_property("gamma")
            exp_val = config.get_property("exposure")
            detail_val = config.get_property("detail")
            shadow_rec_val = config.get_property("shadow-recovery")
            hl_rec_val = config.get_property("highlight-recovery")
            vib_val = config.get_property("vibrance")
            sat_val = config.get_property("saturation")
            opacity_val = config.get_property("opacity")
        else:
            method_val = preset_cfg["method"]
            eg_radius_val = preset_cfg["edge_glow_radius"]
            eg_strength_val = preset_cfg["edge_glow_strength"]
            gamma_val = preset_cfg["gamma"]
            exp_val = preset_cfg["exposure"]
            detail_val = preset_cfg["detail"]
            shadow_rec_val = preset_cfg["shadow_recovery"]
            hl_rec_val = preset_cfg["highlight_recovery"]
            vib_val = preset_cfg["vibrance"]
            sat_val = preset_cfg["saturation"]
            opacity_val = config.get_property("opacity")
            if opacity_val <= 0.0 or opacity_val > 100.0:
                opacity_val = preset_cfg["opacity"]

        mask_mode = config.get_property("mask-mode") or "reveal-all"

        Gimp.context_push()
        image.undo_group_start()

        saved_sel_channel = None
        try:
            # Check active selection (Decision D-003)
            has_user_selection = not Gimp.Selection.is_empty(image)
            if has_user_selection:
                saved_sel_channel = Gimp.Selection.save(image)
                Gimp.Selection.none(image)

            # 1. Duplicate active drawable into isolated adjustment layer
            layer_name = f"HDR Toning ({preset_cfg['label']})"
            hdr_layer = Gimp.Layer.new_from_drawable(target_drawable, image)
            hdr_layer.set_name(layer_name)
            hdr_layer.set_mode(Gimp.LayerMode.NORMAL)
            hdr_layer.set_opacity(float(opacity_val))

            parent = target_drawable.get_parent()
            pos = image.get_item_position(target_drawable)
            image.insert_layer(hdr_layer, parent, pos)

            # 2. Tone Mapping Stage
            if method_val == "local-adaptation":
                filt_mantiuk = Gimp.DrawableFilter.new(hdr_layer, "gegl:mantiuk06", "")
                c_man = filt_mantiuk.get_config()
                # Map detail parameter to contrast & detail
                c_man.set_property("contrast", float(max(0.01, min(1.0, 0.05 + 0.10 * detail_val))))
                c_man.set_property("saturation", 1.0)
                c_man.set_property("detail", float(max(1.0, min(99.0, detail_val * 4.0))))
                hdr_layer.merge_filter(filt_mantiuk)

            elif method_val == "equalize-histogram":
                filt_eq = Gimp.DrawableFilter.new(hdr_layer, "gegl:stretch-contrast", "")
                c_eq = filt_eq.get_config()
                c_eq.set_property("keep-colors", True)
                hdr_layer.merge_filter(filt_eq)

            elif method_val == "highlight-compression":
                # Compress highlight peaks and lift deep shadows
                filt_exp = Gimp.DrawableFilter.new(hdr_layer, "gegl:exposure", "")
                c_exp = filt_exp.get_config()
                # Shadow recovery lifts black level (0.0 to 0.05)
                c_exp.set_property("black-level", float(max(-0.1, min(0.1, (shadow_rec_val / 100.0) * 0.04))))
                # Highlight recovery compresses exposure (-0.0 to -0.6 EV)
                c_exp.set_property("exposure", float(-0.5 * (hl_rec_val / 100.0) + exp_val))
                hdr_layer.merge_filter(filt_exp)

            # For exposure-gamma, direct EV and gamma filters are applied below

            # 3. Edge Glow & Detail Microcontrast Stage
            if method_val in ("local-adaptation", "equalize-histogram") and eg_strength_val > 0.001:
                filt_glow = Gimp.DrawableFilter.new(hdr_layer, "gegl:unsharp-mask", "")
                c_glow = filt_glow.get_config()
                c_glow.set_property("std-dev", float(eg_radius_val))
                c_glow.set_property("scale", float(eg_strength_val))
                hdr_layer.merge_filter(filt_glow)

            # 4. Exposure & Gamma Stage
            if method_val != "highlight-compression" and abs(exp_val) > 0.001:
                filt_exp = Gimp.DrawableFilter.new(hdr_layer, "gegl:exposure", "")
                c_exp = filt_exp.get_config()
                c_exp.set_property("exposure", float(exp_val))
                hdr_layer.merge_filter(filt_exp)

            if abs(gamma_val - 1.0) > 0.001:
                p_levels = Gimp.get_pdb().lookup_procedure("gimp-drawable-levels")
                if p_levels:
                    c_levels = p_levels.create_config()
                    c_levels.set_property("drawable", hdr_layer)
                    c_levels.set_property("channel", Gimp.HistogramChannel.VALUE)
                    c_levels.set_property("low-input", 0.0)
                    c_levels.set_property("high-input", 1.0)
                    c_levels.set_property("clamp-input", True)
                    c_levels.set_property("gamma", float(gamma_val))
                    c_levels.set_property("low-output", 0.0)
                    c_levels.set_property("high-output", 1.0)
                    c_levels.set_property("clamp-output", True)
                    p_levels.run(c_levels)

            # 5. Color Vibrance & Saturation Stage
            if sat_val <= -99.9:
                # Full monochrome HDR mode (saturation = 0.0 in gegl:vibrance)
                filt_vib = Gimp.DrawableFilter.new(hdr_layer, "gegl:vibrance", "")
                c_vib = filt_vib.get_config()
                c_vib.set_property("vibrance", 0.0)
                c_vib.set_property("saturation", 0.0)
                hdr_layer.merge_filter(filt_vib)
            elif abs(vib_val) > 0.001 or abs(sat_val) > 0.001:
                filt_vib = Gimp.DrawableFilter.new(hdr_layer, "gegl:vibrance", "")
                c_vib = filt_vib.get_config()
                c_vib.set_property("vibrance", float(vib_val))
                c_vib.set_property("saturation", float(max(0.0, min(10.0, 1.0 + (sat_val / 100.0)))))
                hdr_layer.merge_filter(filt_vib)

            # 6. Layer Mask Attachment
            if mask_mode == "conceal-all":
                mask = hdr_layer.create_mask(Gimp.AddMaskType.BLACK)
                hdr_layer.add_mask(mask)
            elif mask_mode == "selection" and saved_sel_channel is not None:
                image.select_item(Gimp.ChannelOps.REPLACE, saved_sel_channel)
                mask = hdr_layer.create_mask(Gimp.AddMaskType.SELECTION)
                hdr_layer.add_mask(mask)
                Gimp.Selection.none(image)
            else:  # "reveal-all"
                mask = hdr_layer.create_mask(Gimp.AddMaskType.WHITE)
                hdr_layer.add_mask(mask)

            # Restore user selection if existed
            if saved_sel_channel is not None:
                image.select_item(Gimp.ChannelOps.REPLACE, saved_sel_channel)
                image.remove_channel(saved_sel_channel)

            image.set_selected_layers([hdr_layer])
            hdr_layer.set_visible(True)

        except Exception as e:
            image.undo_group_end()
            Gimp.context_pop()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-hdr-toning"),
                    f"HDR Toning failed: {str(e)}",
                    0
                )
            )

        image.undo_group_end()
        Gimp.context_pop()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(HdrToningPlugin.__gtype__, sys.argv)
