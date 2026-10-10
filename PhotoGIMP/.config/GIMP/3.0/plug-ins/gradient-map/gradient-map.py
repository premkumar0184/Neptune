#!/usr/bin/env python3
"""
PhotoGIMP Non-Destructive Gradient Map & Cinematic Color Grading Helper Plugin for GIMP 3.x

Creates a dedicated non-destructive Gradient Map adjustment layer duplicating
the target drawable and mapping image luminance tones to curated photographic and
cinematic color palettes via GEGL `gegl:gradient-map`. Supports configurable blend
modes (Soft Light, Overlay, Color, Normal), layer opacity, gradient reversal,
and an attached reveal-all layer mask inspired by Adobe Photoshop's Gradient Map command.

Photoshop Equivalence:
- Topics.txt line 342: Apply a gradient fill / Edit a gradient
- photoshop_docs.md line 3081: Gradient Map: Maps tones to gradient colors
- photoshop_docs.md line 3225: Gradient Map Maps tones to gradient colors

Key Advantages over destructive color mapping:
1. 100% Non-Destructive: Duplicates target layer into an isolated adjustment layer.
2. Curated Cinematic & Photographic Palettes: Teal & Orange, Sepia Vintage,
   Cyberpunk Neon, Copper & Patina, Fine Art B&W, Golden Sunset, and Custom.
3. Multi-Stop GEGL Tone Mapping: Uses GEGL `gegl:gradient-map` to map tonal luminance
   seamlessly across shadows, midtones, and highlights.
4. Flexible Blend Modes: Soft Light (subtle grading), Overlay (punchy grading),
   Color (HSL hue/saturation only), or Normal (full gradient fill).
5. Reveal-All Layer Mask: Attached automatically for selective brush painting.
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
    "teal-orange": {
        "label": "Teal & Orange",
        "desc": "Cinematic Hollywood Look",
        "stops": [
            (0.0, 0.02, 0.08, 0.20),  # Deep navy teal shadows
            (0.5, 0.85, 0.45, 0.22),  # Warm coral midtones
            (1.0, 1.00, 0.95, 0.85),  # Warm ivory highlights
        ],
    },
    "sepia-vintage": {
        "label": "Sepia Vintage",
        "desc": "Antique Warm Tones",
        "stops": [
            (0.0, 0.14, 0.06, 0.02),  # Dark espresso shadows
            (0.5, 0.62, 0.38, 0.16),  # Warm chestnut amber midtones
            (1.0, 0.98, 0.92, 0.80),  # Antique linen highlights
        ],
    },
    "cyberpunk-neon": {
        "label": "Cyberpunk Neon",
        "desc": "Synthwave Mood",
        "stops": [
            (0.0, 0.05, 0.00, 0.20),  # Midnight indigo shadows
            (0.5, 0.92, 0.00, 0.60),  # Vivid neon magenta midtones
            (1.0, 0.15, 0.90, 1.00),  # Electric cyan highlights
        ],
    },
    "copper-patina": {
        "label": "Copper & Patina",
        "desc": "Metallic Mood",
        "stops": [
            (0.0, 0.20, 0.10, 0.05),  # Deep oxidized bronze shadows
            (0.5, 0.18, 0.72, 0.65),  # Weathered turquoise midtones
            (1.0, 0.85, 0.98, 0.92),  # Pale mint highlights
        ],
    },
    "fine-art-bw": {
        "label": "Fine Art B&W",
        "desc": "Silver Gelatin Monochrome",
        "stops": [
            (0.0, 0.00, 0.00, 0.00),  # Pure deep black shadows
            (0.5, 0.50, 0.50, 0.50),  # Neutral silver gray midtones
            (1.0, 1.00, 1.00, 1.00),  # Bright clean white highlights
        ],
    },
    "golden-sunset": {
        "label": "Golden Sunset",
        "desc": "Warm Sunlight Glow",
        "stops": [
            (0.0, 0.18, 0.04, 0.08),  # Deep burgundy shadows
            (0.5, 0.90, 0.55, 0.12),  # Rich golden amber midtones
            (1.0, 1.00, 0.98, 0.88),  # Radiant sunlight highlights
        ],
    },
    "custom": {
        "label": "Custom Two-Tone",
        "desc": "Custom Gradient Colors",
    },
}


def gradient_map(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-gradient-map"),
                "No valid image provided.",
                0
            )
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-gradient-map')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    # Read configuration parameters
    preset = config.get_property('preset')
    blend_mode = config.get_property('blend-mode')
    opacity = config.get_property('opacity')
    reverse = config.get_property('reverse')
    add_mask = config.get_property('add-mask')
    custom_start_r = config.get_property('custom-start-red')
    custom_start_g = config.get_property('custom-start-green')
    custom_start_b = config.get_property('custom-start-blue')
    custom_end_r = config.get_property('custom-end-red')
    custom_end_g = config.get_property('custom-end-green')
    custom_end_b = config.get_property('custom-end-blue')

    # Resolve target layer (must be a Gimp.Layer, not a Gimp.LayerMask)
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
                GLib.quark_from_string("gimp-gradient-map"),
                "No valid target layer found.",
                0
            )
        )

    Gimp.context_push()
    image.undo_group_start()

    try:
        preset_info = PRESETS.get(preset, PRESETS["teal-orange"])
        label = preset_info.get("label", "Custom")
        suffix = " Inverted" if reverse else ""
        layer_name = f"Gradient Map ({label}{suffix})"

        # Create non-destructive duplicate layer
        gm_layer = Gimp.Layer.new_from_drawable(target_layer, image)
        gm_layer.set_name(layer_name)
        gm_layer.set_opacity(max(10.0, min(100.0, float(opacity))))

        # Set layer blend mode
        if blend_mode == "soft-light":
            gm_layer.set_mode(Gimp.LayerMode.SOFTLIGHT)
        elif blend_mode == "overlay":
            gm_layer.set_mode(Gimp.LayerMode.OVERLAY)
        elif blend_mode == "hsl-color":
            gm_layer.set_mode(Gimp.LayerMode.HSL_COLOR)
        else:  # "normal"
            gm_layer.set_mode(Gimp.LayerMode.NORMAL)

        parent = target_layer.get_parent()
        pos = image.get_item_position(target_layer)
        image.insert_layer(gm_layer, parent, pos)

        # Prepare gradient stops
        if preset in PRESETS and preset != "custom":
            stops = list(preset_info["stops"])
        else:
            sr = max(0.0, min(1.0, float(custom_start_r)))
            sg = max(0.0, min(1.0, float(custom_start_g)))
            sb = max(0.0, min(1.0, float(custom_start_b)))
            er = max(0.0, min(1.0, float(custom_end_r)))
            eg = max(0.0, min(1.0, float(custom_end_g)))
            eb = max(0.0, min(1.0, float(custom_end_b)))
            stops = [
                (0.0, sr, sg, sb),
                (1.0, er, eg, eb),
            ]

        if reverse:
            rev_colors = [c[1:] for c in reversed(stops)]
            stops = [(stops[i][0], *rev_colors[i]) for i in range(len(stops))]

        # Apply GEGL gradient-map filter
        filt = Gimp.DrawableFilter.new(gm_layer, "gegl:gradient-map", "")
        filt_config = filt.get_config()

        if len(stops) == 2:
            s1, r1, g1, b1 = stops[0]
            s2, r2, g2, b2 = stops[1]
            c1 = Gegl.Color.new(f"rgb({r1:.4f}, {g1:.4f}, {b1:.4f})")
            c2 = Gegl.Color.new(f"rgb({r2:.4f}, {g2:.4f}, {b2:.4f})")
            filt_config.set_property("color1", c1)
            filt_config.set_property("stop1", float(s1))
            filt_config.set_property("color2", c2)
            filt_config.set_property("stop2", float(s2))
            filt_config.set_property("color3", c2)
            filt_config.set_property("stop3", 1.0)
            filt_config.set_property("color4", c2)
            filt_config.set_property("stop4", 1.0)
            filt_config.set_property("color5", c2)
            filt_config.set_property("stop5", 1.0)
        else:  # 3 stops
            s1, r1, g1, b1 = stops[0]
            s2, r2, g2, b2 = stops[1]
            s3, r3, g3, b3 = stops[2]
            c1 = Gegl.Color.new(f"rgb({r1:.4f}, {g1:.4f}, {b1:.4f})")
            c2 = Gegl.Color.new(f"rgb({r2:.4f}, {g2:.4f}, {b2:.4f})")
            c3 = Gegl.Color.new(f"rgb({r3:.4f}, {g3:.4f}, {b3:.4f})")
            filt_config.set_property("color1", c1)
            filt_config.set_property("stop1", float(s1))
            filt_config.set_property("color2", c2)
            filt_config.set_property("stop2", float(s2))
            filt_config.set_property("color3", c3)
            filt_config.set_property("stop3", float(s3))
            filt_config.set_property("color4", c3)
            filt_config.set_property("stop4", 1.0)
            filt_config.set_property("color5", c3)
            filt_config.set_property("stop5", 1.0)

        filt_config.set_property("srgb", False)

        gm_layer.append_filter(filt)
        gm_layer.merge_filters()

        # Attach reveal-all layer mask if requested
        if add_mask:
            mask = gm_layer.create_mask(Gimp.AddMaskType.WHITE)
            gm_layer.add_mask(mask)

        # Set newly created layer as active
        image.set_selected_layers([gm_layer])

        Gimp.displays_flush()
        image.undo_group_end()
        Gimp.context_pop()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    except Exception as exc:
        image.undo_group_end()
        Gimp.context_pop()
        msg = "Gradient Map layer creation failed: " + str(exc)
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-gradient-map"),
                msg,
                0
            )
        )


class GradientMapPlugin(Gimp.PlugIn):
    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-gradient-map"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            gradient_map,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        procedure.set_menu_label("Gradient _Map...")
        procedure.set_documentation(
            "Maps luminance tones to curated cinematic gradients and photographic looks",
            "Creates a dedicated non-destructive Gradient Map adjustment layer duplicating the target drawable. "
            "Maps luminance tones across shadows, midtones, and highlights to curated color palettes via GEGL gradient-map. "
            "Supports Soft Light, Overlay, Color, and Normal blend modes with layer mask attachment inspired by Adobe Photoshop.",
            name
        )
        procedure.set_attribution("Antigravity Ralph / PhotoGIMP", "PhotoGIMP", "2026")

        procedure.add_menu_path("<Image>/Colors")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        # Preset Choice Argument
        preset_choice = Gimp.Choice.new()
        preset_choice.add(
            "teal-orange",
            0,
            "Teal & Orange (Cinematic Look)",
            "Deep navy cyan shadows, warm coral midtones, and ivory highlights"
        )
        preset_choice.add(
            "sepia-vintage",
            1,
            "Sepia Vintage (Antique Tone)",
            "Roasted espresso shadows, warm chestnut midtones, and antique linen highlights"
        )
        preset_choice.add(
            "cyberpunk-neon",
            2,
            "Cyberpunk Neon (Synthwave)",
            "Midnight indigo shadows, neon magenta midtones, and electric cyan highlights"
        )
        preset_choice.add(
            "copper-patina",
            3,
            "Copper & Patina (Metallic Mood)",
            "Deep oxidized bronze shadows, weathered turquoise midtones, and pale mint highlights"
        )
        preset_choice.add(
            "fine-art-bw",
            4,
            "Fine Art B&W (Silver Gelatin)",
            "Rich deep black shadows, neutral silver midtones, and clean crisp white highlights"
        )
        preset_choice.add(
            "golden-sunset",
            5,
            "Golden Sunset (Warm Glow)",
            "Deep burgundy shadows, rich golden amber midtones, and radiant sunlight highlights"
        )
        preset_choice.add(
            "custom",
            6,
            "Custom Two-Tone Gradient",
            "Manually specify custom start (shadow) and end (highlight) colors"
        )

        procedure.add_choice_argument(
            "preset",
            "_Preset",
            "Gradient color mapping preset style",
            preset_choice,
            "teal-orange",
            GObject.ParamFlags.READWRITE
        )

        # Blend Mode Choice Argument
        mode_choice = Gimp.Choice.new()
        mode_choice.add(
            "soft-light",
            0,
            "Soft Light (Subtle Grading)",
            "Subtle cinematic color grading preserving highlights and shadows (Photoshop default)"
        )
        mode_choice.add(
            "overlay",
            1,
            "Overlay (Punchy Grading)",
            "High contrast cinematic color grading with rich tonal saturation"
        )
        mode_choice.add(
            "hsl-color",
            2,
            "Color (Hue & Saturation Only)",
            "Applies gradient colors while strictly preserving underlying layer luminance"
        )
        mode_choice.add(
            "normal",
            3,
            "Normal (Full Gradient Map)",
            "Direct tonal gradient replacement suitable for duotones and poster effects"
        )

        procedure.add_choice_argument(
            "blend-mode",
            "_Blend Mode",
            "Layer blend mode for grading interaction with base image",
            mode_choice,
            "soft-light",
            GObject.ParamFlags.READWRITE
        )

        # Layer Opacity Slider (10% to 100%, default 70%)
        procedure.add_double_argument(
            "opacity",
            "Layer _Opacity (%)",
            "Overall opacity of the Gradient Map adjustment layer (10% to 100%)",
            10.0,
            100.0,
            70.0,
            GObject.ParamFlags.READWRITE
        )

        # Reverse Gradient Option
        procedure.add_boolean_argument(
            "reverse",
            "_Reverse Gradient",
            "Reverse gradient mapping direction (highlights to shadows)",
            False,
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

        # Custom Start Color (Shadows) Sliders
        procedure.add_double_argument(
            "custom-start-red",
            "Start _Red (Shadows)",
            "Custom shadow tint red channel intensity (0.0 to 1.0)",
            0.0,
            1.0,
            0.05,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "custom-start-green",
            "Start _Green (Shadows)",
            "Custom shadow tint green channel intensity (0.0 to 1.0)",
            0.0,
            1.0,
            0.15,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "custom-start-blue",
            "Start _Blue (Shadows)",
            "Custom shadow tint blue channel intensity (0.0 to 1.0)",
            0.0,
            1.0,
            0.35,
            GObject.ParamFlags.READWRITE
        )

        # Custom End Color (Highlights) Sliders
        procedure.add_double_argument(
            "custom-end-red",
            "End R_ed (Highlights)",
            "Custom highlight tint red channel intensity (0.0 to 1.0)",
            0.0,
            1.0,
            1.00,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "custom-end-green",
            "End G_reen (Highlights)",
            "Custom highlight tint green channel intensity (0.0 to 1.0)",
            0.0,
            1.0,
            0.85,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "custom-end-blue",
            "End B_lue (Highlights)",
            "Custom highlight tint blue channel intensity (0.0 to 1.0)",
            0.0,
            1.0,
            0.65,
            GObject.ParamFlags.READWRITE
        )

        return procedure


Gimp.main(GradientMapPlugin.__gtype__, sys.argv)
