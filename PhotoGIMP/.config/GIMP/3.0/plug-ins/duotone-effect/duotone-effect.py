#!/usr/bin/env python3
"""
PhotoGIMP Non-Destructive Duotone & Tritone Print Effect Helper Plugin for GIMP 3.x

Creates a dedicated non-destructive Duotone / Tritone adjustment layer duplicating
the active drawable and mapping image luminance tones to custom editorial and darkroom
print ink combinations (Ink 1 for Shadows, Ink 2 for Highlights, and optional Ink 3
for Midtones) inspired by Adobe Photoshop's Duotone Mode and Duotone Quick Action.

Photoshop Equivalence:
- Topics.txt line 660: Quick actions - Add duotone effect to images.
- Topics.txt line 679: Print - Adjust duotone ink curves.
- photoshop_docs.md Section 312 lines 8715-8722:
  "Duotone mode creates images using one to four custom inks applied to grayscale information.
   Monotones use one ink, duotones use two colors, tritones use three colors, and quadtones
   use four colors. This mode provides creative control over tonal reproduction in printed
   pieces. You can use duotones to extend the tonal range of grayscale images, add color
   tints for aesthetic effect, or match specific brand colors in printed materials. Each
   ink can be mapped to specific tonal ranges, giving you precise control over how colors
   appear in highlights, midtones, and shadows."

Key Advantages over stock destructive editing:
1. 100% Non-Destructive: Duplicates active drawable into an isolated adjustment layer.
2. Authentic Editorial & Graphic Print Presets:
   - Classic Navy & Gold: Deep Prussian navy shadows and warm golden cream highlights.
   - Forest & Pale Mint: Dark pine forest green shadows and fresh pale mint highlights.
   - Crimson & Warm Cream: Deep burgundy crimson shadows and delicate warm cream highlights.
   - Sepia & Pale Ivory: Rich dark espresso sepia shadows and antique linen ivory highlights.
   - Cyberpunk Indigo & Neon Pink: Midnight indigo shadows and electric hot pink highlights.
   - Slate, Coral & Amber (Tritone): Three-ink tritone mapping shadows, midtones, and highlights.
   - Custom Inks: Fully customizable shadow and highlight ink RGB sliders.
3. Ink Curve Midpoint Balance: Slider from 10% to 90% (default 50%) adjusting the tonal
   distribution curve between ink colors (simulating Photoshop ink curve adjustments).
4. Compositing Blend Modes:
   - Normal: Full graphic duotone poster print effect.
   - HSL Color: Colorizes image while preserving original photo luminosity.
   - Soft Light: Photographic subtle tonal grading and contrast enhancement.
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
    "navy-gold": {
        "label": "Classic Navy & Gold",
        "desc": "Deep Prussian navy shadows and warm golden cream highlights",
        "stops": [
            (0.0, 0.04, 0.10, 0.20),  # Deep navy
            (1.0, 0.96, 0.82, 0.38),  # Warm gold
        ],
    },
    "forest-mint": {
        "label": "Forest & Pale Mint",
        "desc": "Dark pine forest green shadows and fresh pale mint highlights",
        "stops": [
            (0.0, 0.06, 0.22, 0.16),  # Dark forest green
            (1.0, 0.65, 0.90, 0.80),  # Pale mint
        ],
    },
    "crimson-cream": {
        "label": "Crimson & Warm Cream",
        "desc": "Deep burgundy crimson shadows and delicate warm cream highlights",
        "stops": [
            (0.0, 0.28, 0.05, 0.09),  # Deep crimson burgundy
            (1.0, 0.97, 0.92, 0.90),  # Warm cream
        ],
    },
    "sepia-ivory": {
        "label": "Sepia & Pale Ivory",
        "desc": "Rich dark espresso sepia shadows and antique linen ivory highlights",
        "stops": [
            (0.0, 0.17, 0.09, 0.06),  # Espresso sepia
            (1.0, 0.96, 0.94, 0.89),  # Pale ivory
        ],
    },
    "cyberpunk-indigo-pink": {
        "label": "Cyberpunk Indigo & Neon Pink",
        "desc": "Midnight indigo shadows and electric hot pink highlights",
        "stops": [
            (0.0, 0.10, 0.04, 0.20),  # Midnight indigo
            (1.0, 1.00, 0.16, 0.52),  # Hot neon pink
        ],
    },
    "slate-amber-tritone": {
        "label": "Slate, Coral & Amber (Tritone)",
        "desc": "Three-ink tritone with deep slate shadows, warm coral midtones, and radiant amber highlights",
        "stops": [
            (0.0, 0.05, 0.10, 0.25),  # Deep slate shadows
            (0.5, 0.85, 0.50, 0.35),  # Warm coral midtones
            (1.0, 1.00, 0.85, 0.40),  # Radiant amber highlights
        ],
    },
    "custom": {
        "label": "Custom Inks",
        "desc": "Custom user-defined shadow and highlight ink colors",
    },
}


def duotone_effect(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-duotone-effect"),
                "No valid image provided.",
                0
            )
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-duotone-effect')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    # Read configuration parameters
    preset = config.get_property('preset')
    blend_mode = config.get_property('blend-mode')
    midpoint = config.get_property('midpoint')
    opacity = config.get_property('opacity')
    add_mask = config.get_property('add-mask')
    shadow_r = config.get_property('custom-shadow-r')
    shadow_g = config.get_property('custom-shadow-g')
    shadow_b = config.get_property('custom-shadow-b')
    highlight_r = config.get_property('custom-highlight-r')
    highlight_g = config.get_property('custom-highlight-g')
    highlight_b = config.get_property('custom-highlight-b')

    # Resolve target layer
    target_layer = None
    if drawables and len(drawables) > 0:
        d = drawables[0]
        if hasattr(d, 'is_layer_mask') and d.is_layer_mask():
            layers = image.get_layers()
            target_layer = layers[0] if len(layers) > 0 else None
        else:
            target_layer = d
    else:
        selected = image.get_selected_layers()
        if len(selected) > 0:
            target_layer = selected[0]
        else:
            layers = image.get_layers()
            target_layer = layers[0] if len(layers) > 0 else None

    if target_layer is None:
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-duotone-effect"),
                "No valid target layer found.",
                0
            )
        )

    Gimp.context_push()
    image.undo_group_start()

    try:
        preset_info = PRESETS.get(preset, PRESETS["navy-gold"])
        label = preset_info.get("label", "Custom Inks")
        layer_name = f"Duotone ({label})"

        # Create non-destructive duplicate layer
        duo_layer = Gimp.Layer.new_from_drawable(target_layer, image)
        duo_layer.set_name(layer_name)
        duo_layer.set_opacity(max(10.0, min(100.0, float(opacity))))

        # Set layer blend mode
        if blend_mode == "hsl-color":
            duo_layer.set_mode(Gimp.LayerMode.HSL_COLOR)
        elif blend_mode == "soft-light":
            duo_layer.set_mode(Gimp.LayerMode.SOFTLIGHT)
        else:  # "normal"
            duo_layer.set_mode(Gimp.LayerMode.NORMAL)

        parent = target_layer.get_parent()
        pos = image.get_item_position(target_layer)
        image.insert_layer(duo_layer, parent, pos)

        # Calculate ink color stops based on preset or custom values and midpoint
        mid_pos = max(0.1, min(0.9, float(midpoint) / 100.0))

        if preset != "custom" and preset in PRESETS:
            raw_stops = preset_info["stops"]
            if len(raw_stops) == 2:
                # 2-ink duotone: interpolate at mid_pos
                s1, r1, g1, b1 = raw_stops[0]
                s2, r2, g2, b2 = raw_stops[1]
                mid_r = (r1 + r2) * 0.5
                mid_g = (g1 + g2) * 0.5
                mid_b = (b1 + b2) * 0.5
                stops = [
                    (0.0, r1, g1, b1),
                    (mid_pos, mid_r, mid_g, mid_b),
                    (1.0, r2, g2, b2),
                ]
            else:
                # 3-ink tritone
                s1, r1, g1, b1 = raw_stops[0]
                _, r2, g2, b2 = raw_stops[1]
                s3, r3, g3, b3 = raw_stops[2]
                stops = [
                    (0.0, r1, g1, b1),
                    (mid_pos, r2, g2, b2),
                    (1.0, r3, g3, b3),
                ]
        else:
            sr = max(0.0, min(1.0, float(shadow_r)))
            sg = max(0.0, min(1.0, float(shadow_g)))
            sb = max(0.0, min(1.0, float(shadow_b)))
            hr = max(0.0, min(1.0, float(highlight_r)))
            hg = max(0.0, min(1.0, float(highlight_g)))
            hb = max(0.0, min(1.0, float(highlight_b)))
            mid_r = (sr + hr) * 0.5
            mid_g = (sg + hg) * 0.5
            mid_b = (sb + hb) * 0.5
            stops = [
                (0.0, sr, sg, sb),
                (mid_pos, mid_r, mid_g, mid_b),
                (1.0, hr, hg, hb),
            ]

        # Apply GEGL gradient-map filter
        filt = Gimp.DrawableFilter.new(duo_layer, "gegl:gradient-map", "")
        f_config = filt.get_config()

        s1, r1, g1, b1 = stops[0]
        s2, r2, g2, b2 = stops[1]
        s3, r3, g3, b3 = stops[2]
        c1 = Gegl.Color.new(f"rgb({r1:.4f}, {g1:.4f}, {b1:.4f})")
        c2 = Gegl.Color.new(f"rgb({r2:.4f}, {g2:.4f}, {b2:.4f})")
        c3 = Gegl.Color.new(f"rgb({r3:.4f}, {g3:.4f}, {b3:.4f})")

        f_config.set_property("color1", c1)
        f_config.set_property("stop1", float(s1))
        f_config.set_property("color2", c2)
        f_config.set_property("stop2", float(s2))
        f_config.set_property("color3", c3)
        f_config.set_property("stop3", float(s3))
        f_config.set_property("color4", c3)
        f_config.set_property("stop4", 1.0)
        f_config.set_property("color5", c3)
        f_config.set_property("stop5", 1.0)
        f_config.set_property("srgb", False)

        duo_layer.merge_filter(filt)

        # Attach optional reveal-all layer mask
        if add_mask:
            mask = duo_layer.create_mask(Gimp.AddMaskType.WHITE)
            duo_layer.add_mask(mask)

        # Set newly created adjustment layer as selected
        image.set_selected_layers([duo_layer])
        Gimp.displays_flush()

    except Exception as e:
        image.undo_group_end()
        Gimp.context_pop()
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-duotone-effect"),
                f"Duotone effect processing failed: {str(e)}",
                0
            )
        )

    image.undo_group_end()
    Gimp.context_pop()

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


class DuotoneEffectPlugin(Gimp.PlugIn):
    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-duotone-effect"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            duotone_effect,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        procedure.set_menu_label("Duotone _Effect...")
        procedure.set_documentation(
            "Creates a non-destructive editorial Duotone or Tritone print effect adjustment layer",
            "Creates a dedicated non-destructive Duotone adjustment layer duplicating active drawable. "
            "Maps luminance tones to custom editorial and darkroom print ink combinations with configurable "
            "ink curve midpoint balance and blend modes inspired by Adobe Photoshop's Duotone Mode "
            "and Duotone Quick Action.",
            name
        )
        procedure.set_attribution("Antigravity Ralph / PhotoGIMP", "PhotoGIMP", "2026")

        procedure.add_menu_path("<Image>/Colors")
        procedure.add_menu_path("<Image>/Filters/Retouching")
        procedure.add_menu_path("<Image>/Layer")

        # Preset Choice Argument
        preset_choice = Gimp.Choice.new()
        preset_choice.add(
            "navy-gold",
            0,
            "Classic Navy & Gold",
            "Deep Prussian navy shadows and warm golden cream highlights"
        )
        preset_choice.add(
            "forest-mint",
            1,
            "Forest & Pale Mint",
            "Dark pine forest green shadows and fresh pale mint highlights"
        )
        preset_choice.add(
            "crimson-cream",
            2,
            "Crimson & Warm Cream",
            "Deep burgundy crimson shadows and delicate warm cream highlights"
        )
        preset_choice.add(
            "sepia-ivory",
            3,
            "Sepia & Pale Ivory",
            "Rich dark espresso sepia shadows and antique linen ivory highlights"
        )
        preset_choice.add(
            "cyberpunk-indigo-pink",
            4,
            "Cyberpunk Indigo & Neon Pink",
            "Midnight indigo shadows and electric hot pink highlights"
        )
        preset_choice.add(
            "slate-amber-tritone",
            5,
            "Slate, Coral & Amber (Tritone)",
            "Three-ink tritone with deep slate shadows, warm coral midtones, and radiant amber highlights"
        )
        preset_choice.add(
            "custom",
            6,
            "Custom Inks",
            "Custom user-defined shadow and highlight ink colors"
        )

        procedure.add_choice_argument(
            "preset",
            "_Preset",
            "Curated editorial duotone/tritone ink preset",
            preset_choice,
            "navy-gold",
            GObject.ParamFlags.READWRITE
        )

        # Blend Mode Choice Argument
        blend_choice = Gimp.Choice.new()
        blend_choice.add(
            "normal",
            0,
            "Normal (Poster Print)",
            "Full graphic duotone poster print effect"
        )
        blend_choice.add(
            "hsl-color",
            1,
            "Color (HSL Tint)",
            "Colorizes tones while preserving original photograph luminosity"
        )
        blend_choice.add(
            "soft-light",
            2,
            "Soft Light (Photographic Grading)",
            "Subtle contrast enhancement and photographic mood grading"
        )

        procedure.add_choice_argument(
            "blend-mode",
            "_Blend Mode",
            "Layer compositing blend mode for the duotone layer",
            blend_choice,
            "normal",
            GObject.ParamFlags.READWRITE
        )

        # Ink Curve Midpoint Balance Slider (10% to 90%, default 50%)
        procedure.add_double_argument(
            "midpoint",
            "_Ink Balance / Midpoint (%)",
            "Tonal transition balance between shadow and highlight inks (10% to 90%)",
            10.0,
            90.0,
            50.0,
            GObject.ParamFlags.READWRITE
        )

        # Custom Shadow Ink RGB Arguments (0.0 to 1.0)
        procedure.add_double_argument(
            "custom-shadow-r",
            "Shadow Ink _Red",
            "Custom shadow ink red channel (0.0 to 1.0)",
            0.0,
            1.0,
            0.04,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "custom-shadow-g",
            "Shadow Ink _Green",
            "Custom shadow ink green channel (0.0 to 1.0)",
            0.0,
            1.0,
            0.10,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "custom-shadow-b",
            "Shadow Ink _Blue",
            "Custom shadow ink blue channel (0.0 to 1.0)",
            0.0,
            1.0,
            0.20,
            GObject.ParamFlags.READWRITE
        )

        # Custom Highlight Ink RGB Arguments (0.0 to 1.0)
        procedure.add_double_argument(
            "custom-highlight-r",
            "Highlight Ink _Red",
            "Custom highlight ink red channel (0.0 to 1.0)",
            0.0,
            1.0,
            0.96,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "custom-highlight-g",
            "Highlight Ink _Green",
            "Custom highlight ink green channel (0.0 to 1.0)",
            0.0,
            1.0,
            0.82,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "custom-highlight-b",
            "Highlight Ink _Blue",
            "Custom highlight ink blue channel (0.0 to 1.0)",
            0.0,
            1.0,
            0.38,
            GObject.ParamFlags.READWRITE
        )

        # Layer Opacity Slider (10% to 100%, default 100%)
        procedure.add_double_argument(
            "opacity",
            "Layer _Opacity (%)",
            "Overall opacity of the Duotone adjustment layer (10% to 100%)",
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


Gimp.main(DuotoneEffectPlugin.__gtype__, sys.argv)
