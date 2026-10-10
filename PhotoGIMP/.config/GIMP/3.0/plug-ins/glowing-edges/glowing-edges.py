#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Glowing Edges & Neon Stylize Filter Plugin
====================================================================
Photoshop Reference:
- Topics.txt line 451: "Apply filters from the filter gallery"
- Topics.txt line 452: "Filter Gallery overview"
- Topics.txt line 484: "Apply texture and surface effects to filters"
- photoshop_docs.md Section 416 lines 12128-12135 (Filter Gallery:
  Category: Stylize, Examples: Glowing Edges, Solarize, Wind
  Purpose: Stylization and edge effects)

Key Architectural Features:
1. High-Contrast Edge Detection & Neon Illumination:
   - Identifies boundaries and contours in the image and transforms them into
     luminous neon lines against a dark backdrop or superimposed atop the composition.
2. Full Photoshop Parameter Mapping:
   - Edge Width (1.0 to 15.0px): Controls the thickness of glowing contour lines.
   - Edge Brightness (1.0 to 20.0): Controls the luminance intensity and glow radiation.
   - Smoothness (1.0 to 15.0): Pre-filtering to reduce high-frequency noise and yield
     fluid, continuous neon curves.
3. Multiple Neon Color Tonalities:
   - Spectral: Retains original multi-colored edge spectrum.
   - Electric Cyan: Neon cyan/blue cybernetic glow.
   - Hot Magenta: Synthwave pink/purple radiance.
   - Laser Green: Neon green wireframe glow.
   - Golden Amber: Incandescent warm golden neon glow.
   - Monochrome White: Clean architectural blueprint contour drawing.
4. Professional Compositing Blend Modes:
   - Screen (31): Overlays radiant neon lines onto base image with transparent dark background.
   - Addition (33): Linear Dodge luminous bloom overlay.
   - Soft Light (45): Subtle contour contrast enhancement.
   - Normal (28): Dark background neon line art artwork.
5. Curated Presets:
   - Classic Neon: Balanced spectral contours in Screen mode.
   - Cyberpunk Cyan: High-intensity electric cyan glow.
   - Synthwave Magenta: Radiant retro synthwave pink/magenta contours.
   - Laser Wireframe: High-contrast green wireframe on dark background.
   - Architectural White: Crisp white contour sketch.
   - Custom: Full manual slider control.
6. Non-Destructive Adjustment Layering & Masks:
   - Creates an isolated adjustment layer duplicating the active drawable.
   - Attaches editable layer masks (Reveal All, Conceal All for brush-in accents, Selection).
   - Base layer source pixels underneath remain 100% mathematically untouched (0.000000 diff).
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


BLEND_MODES = {
    "screen": Gimp.LayerMode.SCREEN,
    "addition": Gimp.LayerMode.ADDITION,
    "soft-light": Gimp.LayerMode.SOFTLIGHT,
    "normal": Gimp.LayerMode.NORMAL,
}

TONE_GRADIENTS = {
    "electric-cyan": {
        "color1": "rgb(0.0, 0.0, 0.0)",
        "color2": "rgb(0.0, 0.45, 0.85)",
        "color3": "rgb(0.2, 0.95, 1.0)",
    },
    "hot-magenta": {
        "color1": "rgb(0.0, 0.0, 0.0)",
        "color2": "rgb(0.7, 0.05, 0.55)",
        "color3": "rgb(1.0, 0.25, 0.85)",
    },
    "laser-green": {
        "color1": "rgb(0.0, 0.0, 0.0)",
        "color2": "rgb(0.0, 0.6, 0.15)",
        "color3": "rgb(0.25, 1.0, 0.35)",
    },
    "golden-amber": {
        "color1": "rgb(0.0, 0.0, 0.0)",
        "color2": "rgb(0.8, 0.35, 0.0)",
        "color3": "rgb(1.0, 0.85, 0.25)",
    },
    "monochrome-white": {
        "color1": "rgb(0.0, 0.0, 0.0)",
        "color2": "rgb(0.5, 0.5, 0.5)",
        "color3": "rgb(1.0, 1.0, 1.0)",
    },
}

PRESETS = {
    "classic-neon": {
        "label": "Classic Neon",
        "desc": "Classic Photoshop Glowing Edges with multi-spectral neon contour lines in Screen mode",
        "width": 2.0,
        "brightness": 8.0,
        "smoothness": 4.0,
        "tone": "spectral",
        "blend_mode": "screen",
        "opacity": 100.0,
    },
    "cyberpunk-cyan": {
        "label": "Cyberpunk Cyan",
        "desc": "Vibrant electric cyan and deep blue neon edge illumination",
        "width": 3.0,
        "brightness": 12.0,
        "smoothness": 5.0,
        "tone": "electric-cyan",
        "blend_mode": "screen",
        "opacity": 100.0,
    },
    "synthwave-magenta": {
        "label": "Synthwave Magenta",
        "desc": "Retrowave hot pink and magenta neon glow",
        "width": 2.5,
        "brightness": 10.0,
        "smoothness": 4.0,
        "tone": "hot-magenta",
        "blend_mode": "screen",
        "opacity": 100.0,
    },
    "laser-wireframe": {
        "label": "Laser Wireframe",
        "desc": "High-acutance cybernetic laser green wireframe on dark background",
        "width": 1.5,
        "brightness": 12.0,
        "smoothness": 2.0,
        "tone": "laser-green",
        "blend_mode": "normal",
        "opacity": 100.0,
    },
    "architectural-white": {
        "label": "Architectural White",
        "desc": "Monochrome architectural blueprint / white neon contour drawing",
        "width": 2.0,
        "brightness": 10.0,
        "smoothness": 6.0,
        "tone": "monochrome-white",
        "blend_mode": "normal",
        "opacity": 100.0,
    },
    "custom": {
        "label": "Custom Glowing Edges",
        "desc": "Manual slider configuration",
        "width": 2.0,
        "brightness": 8.0,
        "smoothness": 4.0,
        "tone": "spectral",
        "blend_mode": "screen",
        "opacity": 100.0,
    },
}


class GlowingEdgesPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-glowing-edges"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, self.run, None
        )
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
        procedure.set_menu_label("Glowing Edges...")
        procedure.add_menu_path("<Image>/Filters/Artistic")
        procedure.add_menu_path("<Image>/Filters/Stylize")
        procedure.add_menu_path("<Image>/Layer")

        procedure.set_documentation(
            "Non-Destructive Glowing Edges & Neon Stylize Filter Helper",
            "Extracts high-contrast image boundaries and converts them into vibrant, luminous "
            "neon contour lines using non-destructive adjustment layers.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add("classic-neon", 0, "Classic Neon (Spectral Screen)", "Classic Photoshop Glowing Edges with multi-spectral contours")
        preset_choice.add("cyberpunk-cyan", 1, "Cyberpunk Cyan (Electric Blue)", "Vibrant electric cyan neon edge illumination")
        preset_choice.add("synthwave-magenta", 2, "Synthwave Magenta (Retro Pink)", "Retrowave hot pink and magenta neon glow")
        preset_choice.add("laser-wireframe", 3, "Laser Wireframe (Green / Normal)", "High-acutance cybernetic laser green wireframe on black")
        preset_choice.add("architectural-white", 4, "Architectural White (Blueprint)", "Monochrome architectural white contour sketch")
        preset_choice.add("custom", 5, "Custom Glowing Edges", "Manual slider configuration")

        procedure.add_choice_argument(
            "preset",
            "Stylize Preset",
            "Curated glowing edges preset (classic-neon, cyberpunk-cyan, synthwave-magenta, laser-wireframe, architectural-white, custom)",
            preset_choice,
            "classic-neon",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "edge-width",
            "Edge Width",
            "Thickness of the glowing neon contour lines (1.0 to 15.0px, default 2.0)",
            1.0,
            15.0,
            2.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "edge-brightness",
            "Edge Brightness",
            "Intensity and radiation of the glowing edges (1.0 to 20.0, default 8.0)",
            1.0,
            20.0,
            8.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "smoothness",
            "Smoothness",
            "Pre-filtering noise reduction for smooth fluid contours (1.0 to 15.0, default 4.0)",
            1.0,
            15.0,
            4.0,
            GObject.ParamFlags.READWRITE
        )

        # Tone Choice
        tone_choice = Gimp.Choice.new()
        tone_choice.add("spectral", 0, "Spectral Neon (Original RGB)", "Preserves multi-color spectral edges")
        tone_choice.add("electric-cyan", 1, "Electric Cyan / Blue", "Vibrant cyan neon glow")
        tone_choice.add("hot-magenta", 2, "Hot Magenta / Synthwave", "Vibrant pink/magenta neon glow")
        tone_choice.add("laser-green", 3, "Laser Green / Cyberpunk", "Vibrant laser green wireframe glow")
        tone_choice.add("golden-amber", 4, "Golden Amber / Warm", "Warm incandescent golden neon glow")
        tone_choice.add("monochrome-white", 5, "Monochrome White", "Clean neutral white edge contours")

        procedure.add_choice_argument(
            "tone",
            "Neon Color Tone",
            "Color grading palette for glowing contours (spectral, electric-cyan, hot-magenta, laser-green, golden-amber, monochrome-white)",
            tone_choice,
            "spectral",
            GObject.ParamFlags.READWRITE
        )

        # Blend Mode Choice
        blend_choice = Gimp.Choice.new()
        blend_choice.add("screen", 0, "Screen (Overlay on Image)", "Superimposes luminous lines on original image with dark transparent background")
        blend_choice.add("addition", 1, "Addition / Linear Dodge", "Hyper-bright luminous bloom overlay")
        blend_choice.add("soft-light", 2, "Soft Light (Subtle)", "Subtle edge contrast contour enhancement")
        blend_choice.add("normal", 3, "Normal (Dark Background)", "Standalone dark background neon artwork")

        procedure.add_choice_argument(
            "blend-mode",
            "Blend Mode",
            "Compositing blend mode for the Glowing Edges layer (screen, addition, soft-light, normal)",
            blend_choice,
            "screen",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "opacity",
            "Layer Opacity (%)",
            "Overall opacity of the Glowing Edges layer (10.0% to 100.0%, default 100.0%)",
            10.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # Mask Type Choice
        mask_choice = Gimp.Choice.new()
        mask_choice.add("reveal-all", 0, "Reveal All (White Mask)", "Full image neon stylization")
        mask_choice.add("conceal-all", 1, "Conceal All (Black Mask)", "Effect hidden; brush in selective glowing accents")
        mask_choice.add("selection", 2, "Active Selection Mask", "Confines glowing edges strictly to active selection")

        procedure.add_choice_argument(
            "mask-type",
            "Layer Mask Mode",
            "Initial layer mask configuration (reveal-all, conceal-all, selection)",
            mask_choice,
            "reveal-all",
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run(self, procedure, run_mode, image, drawables, config, data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            Gimp.ui_init("glowing-edges.py")
            dialog = Gimp.ProcedureDialog.new(procedure, config, "Glowing Edges Stylize")
            dialog.fill([
                "preset", "edge-width", "edge-brightness", "smoothness",
                "tone", "blend-mode", "opacity", "mask-type"
            ])
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        # Resolve target drawable
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
                    GLib.quark_from_string("gimp-glowing-edges"),
                    "No target drawable found to apply Glowing Edges stylization.",
                    0
                )
            )

        preset_key = config.get_property("preset") or "classic-neon"
        if preset_key not in PRESETS:
            preset_key = "classic-neon"
        preset_cfg = PRESETS[preset_key]

        if preset_key == "custom":
            width_val = config.get_property("edge-width")
            brightness_val = config.get_property("edge-brightness")
            smoothness_val = config.get_property("smoothness")
            tone_val = config.get_property("tone") or "spectral"
            blend_val = config.get_property("blend-mode") or "screen"
            opacity_val = config.get_property("opacity")
        else:
            width_val = preset_cfg["width"]
            brightness_val = preset_cfg["brightness"]
            smoothness_val = preset_cfg["smoothness"]
            tone_val = preset_cfg["tone"]
            blend_val = preset_cfg["blend_mode"]
            opacity_val = config.get_property("opacity")
            if opacity_val <= 0.0 or opacity_val > 100.0:
                opacity_val = preset_cfg["opacity"]

        mask_type = config.get_property("mask-type") or "reveal-all"
        layer_mode = BLEND_MODES.get(blend_val, Gimp.LayerMode.SCREEN)

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
            layer_name = f"Glowing Edges ({preset_cfg['label']})"
            neon_layer = Gimp.Layer.new_from_drawable(target_drawable, image)
            neon_layer.set_name(layer_name)
            neon_layer.set_mode(layer_mode)
            neon_layer.set_opacity(float(opacity_val))

            parent = target_drawable.get_parent()
            pos = image.get_item_position(target_drawable)
            image.insert_layer(neon_layer, parent, pos)

            # 2. Pre-filtering smoothness pass (reduces high-frequency noise)
            if float(smoothness_val) > 1.0:
                blur_radius = max(0.2, (float(smoothness_val) - 1.0) * 0.35)
                filt_smooth = Gimp.DrawableFilter.new(neon_layer, "gegl:gaussian-blur", "")
                c_smooth = filt_smooth.get_config()
                c_smooth.set_property("std-dev-x", float(blur_radius))
                c_smooth.set_property("std-dev-y", float(blur_radius))
                neon_layer.merge_filter(filt_smooth)

            # 3. High-contrast edge extraction & neon glow via gegl:edge-neon
            neon_radius = max(0.5, float(width_val) * 1.5)
            neon_amount = min(1.0, max(0.1, float(brightness_val) / 12.0))
            filt_neon = Gimp.DrawableFilter.new(neon_layer, "gegl:edge-neon", "")
            c_neon = filt_neon.get_config()
            c_neon.set_property("radius", float(neon_radius))
            c_neon.set_property("amount", float(neon_amount))
            neon_layer.merge_filter(filt_neon)

            # 4. Exposure & brightness enhancement for high intensity settings
            if float(brightness_val) > 8.0:
                exp_boost = min(3.0, (float(brightness_val) - 8.0) * 0.25)
                filt_exp = Gimp.DrawableFilter.new(neon_layer, "gegl:exposure", "")
                c_exp = filt_exp.get_config()
                c_exp.set_property("exposure", float(exp_boost))
                neon_layer.merge_filter(filt_exp)

            # 5. Neon Color Tone mapping
            if tone_val in TONE_GRADIENTS:
                # Harmonize edge energy into full-range monochrome before gradient mapping
                filt_mono = Gimp.DrawableFilter.new(neon_layer, "gegl:mono-mixer", "")
                c_mono = filt_mono.get_config()
                c_mono.set_property("preserve-luminosity", False)
                c_mono.set_property("red", 1.0)
                c_mono.set_property("green", 1.0)
                c_mono.set_property("blue", 1.0)
                neon_layer.merge_filter(filt_mono)

                t_cfg = TONE_GRADIENTS[tone_val]
                filt_tone = Gimp.DrawableFilter.new(neon_layer, "gegl:gradient-map", "")
                c_tone = filt_tone.get_config()
                c_tone.set_property("stop1", 0.0)
                c_tone.set_property("color1", Gegl.Color.new(t_cfg["color1"]))
                c_tone.set_property("stop2", 0.5)
                c_tone.set_property("color2", Gegl.Color.new(t_cfg["color2"]))
                c_tone.set_property("stop3", 1.0)
                c_tone.set_property("color3", Gegl.Color.new(t_cfg["color3"]))
                neon_layer.merge_filter(filt_tone)

            # 6. Attach Layer Mask
            if mask_type == "conceal-all":
                mask = neon_layer.create_mask(Gimp.AddMaskType.BLACK)
                neon_layer.add_mask(mask)
            elif mask_type == "selection":
                if saved_sel_channel is not None:
                    image.select_item(Gimp.ChannelOps.REPLACE, saved_sel_channel)
                    mask = neon_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    neon_layer.add_mask(mask)
                    Gimp.Selection.none(image)
                else:
                    mask = neon_layer.create_mask(Gimp.AddMaskType.WHITE)
                    neon_layer.add_mask(mask)
            else:  # reveal-all
                mask = neon_layer.create_mask(Gimp.AddMaskType.WHITE)
                neon_layer.add_mask(mask)

            # Cleanup saved selection channel
            if saved_sel_channel is not None:
                image.remove_channel(saved_sel_channel)

            image.set_selected_layers([neon_layer])
            neon_layer.set_visible(True)

        except Exception as e:
            image.undo_group_end()
            Gimp.context_pop()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-glowing-edges"),
                    f"Glowing Edges stylization failed: {str(e)}",
                    0
                )
            )

        image.undo_group_end()
        Gimp.context_pop()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(GlowingEdgesPlugin.__gtype__, sys.argv)
