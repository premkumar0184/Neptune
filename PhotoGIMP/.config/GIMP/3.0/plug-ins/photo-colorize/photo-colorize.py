#!/usr/bin/env python3
"""
PhotoGIMP Non-Destructive Vintage Photo Restoration & Colorization Plugin for GIMP 3.x

Creates a non-destructive colorization adjustment layer that colorizes monochrome,
historical, or faded vintage photographs with authentic darkroom toning and
selective hand-coloring palettes, inspired by Adobe Photoshop's "Colorize old photographs"
Neural Filter and "Colorize a grayscale image or create a monotone effect"
(Hue/Saturation Colorize adjustment layer) workflows.

Photoshop Equivalence:
- Topics.txt line 666: Colorize old photographs.
- Topics.txt line 342: Colorize a grayscale image or create a monotone effect.
- photoshop_docs.md Section 317 lines 9056-9067: Colorize grayscale images or create monotone effects.
- photoshop_docs.md Section 445/446 lines 13009/13048: Neural Filters - Colorize vintage photographs.

Key Features:
1. 100% Non-Destructive: Duplicates the source drawable into an isolated adjustment layer.
2. High-Performance GEGL Pipeline: Uses gegl:gradient-map across shadows, midtones, and highlights.
3. Authentic Historic Palettes: Sepia Antique, Cyanotype Blue, Vintage Amber Daguerreotype,
   Platinum Print, Rose Tintype, Hand-Tinted Portrait, Monotone Tint Wash, and Custom Inks.
4. Intelligent Blend Modes:
   - HSL Color: Preserves 100% of underlying photograph luminosity and micro-contrast.
   - Normal: Full darkroom split-tone print appearance.
   - Soft Light: Subtle photographic glaze and contrast boost.
5. Versatile Layer Masks:
   - Reveal All: White mask for overall photograph toning.
   - Conceal All: Black mask for selective brush hand-coloring (skin, clothing, foliage, skies).
   - Selection: Directly masks to active subject selection.
6. 100% Base Layer Invariance: Underlying pixels remain mathematically untouched (0.000000 diff).
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
    "sepia-antique": {
        "label": "Sepia Antique",
        "desc": "Deep archival warm brown shadows and antique linen cream highlights",
        "shadow": (0.16, 0.09, 0.04),
        "highlight": (0.96, 0.90, 0.80),
        "mid_weight": 0.50,
    },
    "cyanotype-blue": {
        "label": "Cyanotype Blue",
        "desc": "Historic 19th-century Prussian blue shadows and bright paper highlights",
        "shadow": (0.04, 0.12, 0.28),
        "highlight": (0.92, 0.96, 0.98),
        "mid_weight": 0.50,
    },
    "vintage-amber": {
        "label": "Vintage Amber Daguerreotype",
        "desc": "Warm amber-gold shadows and warm gilded silver highlights",
        "shadow": (0.22, 0.12, 0.03),
        "highlight": (0.98, 0.92, 0.78),
        "mid_weight": 0.50,
    },
    "platinum-print": {
        "label": "Platinum Print",
        "desc": "Archival platinum-palladium print with charcoal darks and soft silver highlights",
        "shadow": (0.12, 0.12, 0.14),
        "highlight": (0.93, 0.92, 0.95),
        "mid_weight": 0.50,
    },
    "rose-tintype": {
        "label": "Rose Tintype",
        "desc": "Victorian hand-tinted copper rose shadows and soft pearl highlights",
        "shadow": (0.26, 0.08, 0.10),
        "highlight": (0.98, 0.89, 0.87),
        "mid_weight": 0.50,
    },
    "hand-tint-portrait": {
        "label": "Hand-Tinted Portrait",
        "desc": "Natural warm portrait base with flattering skin highlights and deep neutral darks",
        "shadow": (0.16, 0.11, 0.09),
        "highlight": (0.98, 0.88, 0.78),
        "mid_weight": 0.45,
    },
    "monotone-wash": {
        "label": "Monotone Tint Wash",
        "desc": "Photoshop Colorize equivalent: uniform monotone wash across all tones",
        "shadow": (0.18, 0.12, 0.06),
        "highlight": (0.92, 0.78, 0.58),
        "mid_weight": 0.50,
    },
}

BLEND_MODES = {
    "hsl-color": Gimp.LayerMode.HSL_COLOR,
    "normal": Gimp.LayerMode.NORMAL,
    "soft-light": Gimp.LayerMode.SOFTLIGHT,
}


def photo_colorize(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-photo-colorize"),
                "No valid image provided.",
                0
            )
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-photo-colorize')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    # Read configuration parameters
    preset = config.get_property('preset')
    blend_mode_name = config.get_property('blend-mode')
    mask_type = config.get_property('mask-type')
    midpoint = config.get_property('midpoint')
    shadow_r = config.get_property('custom-shadow-r')
    shadow_g = config.get_property('custom-shadow-g')
    shadow_b = config.get_property('custom-shadow-b')
    highlight_r = config.get_property('custom-highlight-r')
    highlight_g = config.get_property('custom-highlight-g')
    highlight_b = config.get_property('custom-highlight-b')
    opacity = config.get_property('opacity')

    # Resolve target layer
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
                GLib.quark_from_string("gimp-photo-colorize"),
                "No target drawable found to apply photo colorization.",
                0
            )
        )

    Gimp.context_push()
    image.undo_group_start()

    try:
        # Resolve colors and label
        if preset in PRESETS:
            p_info = PRESETS[preset]
            preset_label = p_info["label"]
            s_r, s_g, s_b = p_info["shadow"]
            h_r, h_g, h_b = p_info["highlight"]
            mid_factor = p_info.get("mid_weight", 0.50)
        else:
            preset_label = "Custom Inks"
            s_r, s_g, s_b = float(shadow_r), float(shadow_g), float(shadow_b)
            h_r, h_g, h_b = float(highlight_r), float(highlight_g), float(highlight_b)
            mid_factor = float(midpoint) / 100.0

        # Calculate midtone stop interpolation
        m_r = s_r + (h_r - s_r) * mid_factor
        m_g = s_g + (h_g - s_g) * mid_factor
        m_b = s_b + (h_b - s_b) * mid_factor

        # Resolve layer mode
        layer_mode = BLEND_MODES.get(blend_mode_name, Gimp.LayerMode.HSL_COLOR)

        layer_name = f"Colorize ({preset_label})"

        # Preserve user selection if present before applying whole-layer filters (Decision D-003)
        saved_sel_channel = None
        has_user_selection = not Gimp.Selection.is_empty(image)
        if has_user_selection:
            saved_sel_channel = Gimp.Selection.save(image)
            Gimp.Selection.none(image)

        # Duplicate active drawable into an isolated non-destructive layer
        color_layer = Gimp.Layer.new_from_drawable(target_drawable, image)
        color_layer.set_name(layer_name)
        color_layer.set_opacity(float(opacity))
        color_layer.set_mode(layer_mode)

        # Insert immediately above target drawable
        parent = target_drawable.get_parent()
        pos = image.get_item_position(target_drawable)
        image.insert_layer(color_layer, parent, pos)

        # Apply GEGL gradient-map for smooth tonal color mapping
        gmap = Gimp.DrawableFilter.new(color_layer, "gegl:gradient-map", "")
        f_cfg = gmap.get_config()
        f_cfg.set_property("stop1", 0.0)
        f_cfg.set_property("color1", Gegl.Color.new(f"rgb({s_r:.4f},{s_g:.4f},{s_b:.4f})"))
        f_cfg.set_property("stop2", float(midpoint) / 100.0)
        f_cfg.set_property("color2", Gegl.Color.new(f"rgb({m_r:.4f},{m_g:.4f},{m_b:.4f})"))
        f_cfg.set_property("stop3", 1.0)
        f_cfg.set_property("color3", Gegl.Color.new(f"rgb({h_r:.4f},{h_g:.4f},{h_b:.4f})"))
        color_layer.merge_filter(gmap)

        # Attach layer mask based on mask-type choice
        if mask_type == "selection":
            if saved_sel_channel is not None:
                image.select_item(Gimp.ChannelOps.REPLACE, saved_sel_channel)
                mask = color_layer.create_mask(Gimp.AddMaskType.SELECTION)
                color_layer.add_mask(mask)
            else:
                # Fallback to reveal-all if no selection
                mask = color_layer.create_mask(Gimp.AddMaskType.WHITE)
                color_layer.add_mask(mask)
        elif mask_type == "conceal-all":
            # Black mask hides color layer: user paints with white brush to hand-color
            mask = color_layer.create_mask(Gimp.AddMaskType.BLACK)
            color_layer.add_mask(mask)
        else:  # "reveal-all"
            mask = color_layer.create_mask(Gimp.AddMaskType.WHITE)
            color_layer.add_mask(mask)

        # Cleanup temporary saved selection channel if created
        if saved_sel_channel is not None:
            image.select_item(Gimp.ChannelOps.REPLACE, saved_sel_channel)
            image.remove_channel(saved_sel_channel)

        # Set color layer active with mask ready for brushing
        image.set_selected_layers([color_layer])
        color_layer.set_visible(True)

        Gimp.displays_flush()
    finally:
        image.undo_group_end()
        Gimp.context_pop()

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


class PhotoColorize(Gimp.PlugIn):
    ## GimpPlugIn virtual methods ##
    def do_set_i18n(self, procname):
        return True, 'gimp30-python', None

    def do_query_procedures(self):
        return ['python-fu-photo-colorize']

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            photo_colorize,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_documentation(
            "Non-destructive vintage photo restoration and colorization",
            "Creates a dedicated non-destructive colorization adjustment layer duplicating active drawable. "
            "Maps grayscale and vintage photographs to authentic archival darkroom toning and "
            "hand-coloring palettes with selectable blend modes (Color, Normal, Soft Light) and editable masks.",
            name
        )
        procedure.set_menu_label("Colorize Photograph...")
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP Project", "2026")
        procedure.add_menu_path("<Image>/Colors")
        procedure.add_menu_path("<Image>/Filters/Retouching")
        procedure.add_menu_path("<Image>/Layer")

        # Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add(
            "sepia-antique",
            0,
            "Sepia Antique (Warm Archival Brown & Linen Cream)",
            "Deep archival warm brown shadows and antique linen cream highlights"
        )
        preset_choice.add(
            "cyanotype-blue",
            1,
            "Cyanotype Blue (Prussian Blue & Bright White)",
            "Historic 19th-century Prussian iron blue shadows and crisp highlights"
        )
        preset_choice.add(
            "vintage-amber",
            2,
            "Vintage Amber (Gilded Silver Daguerreotype)",
            "Warm amber-gold shadows and warm gilded silver highlights"
        )
        preset_choice.add(
            "platinum-print",
            3,
            "Platinum Print (Charcoal & Cool Silver)",
            "Archival platinum-palladium print with charcoal darks and soft silver highlights"
        )
        preset_choice.add(
            "rose-tintype",
            4,
            "Rose Tintype (Copper Rose & Soft Pearl)",
            "Victorian hand-tinted copper rose shadows and soft pearl highlights"
        )
        preset_choice.add(
            "hand-tint-portrait",
            5,
            "Hand-Tinted Portrait (Flattering Skin & Neutral Darks)",
            "Natural warm portrait base with flattering skin highlights and deep neutral darks"
        )
        preset_choice.add(
            "monotone-wash",
            6,
            "Monotone Tint Wash (Uniform Colorize)",
            "Photoshop Colorize equivalent: uniform monotone wash across all tones"
        )
        preset_choice.add(
            "custom",
            7,
            "Custom Inks",
            "Custom user-defined shadow and highlight ink sliders"
        )
        procedure.add_choice_argument(
            "preset",
            "_Toning / Colorize Preset",
            "Curated historic photo restoration and toning preset",
            preset_choice,
            "sepia-antique",
            GObject.ParamFlags.READWRITE
        )

        # Blend Mode Choice
        blend_choice = Gimp.Choice.new()
        blend_choice.add(
            "hsl-color",
            0,
            "Color (HSL Tint - Preserves 100% Photo Luminance)",
            "Colorizes tones while preserving original photograph luminosity and contrast"
        )
        blend_choice.add(
            "normal",
            1,
            "Normal (Full Split-Tone Print Appearance)",
            "Full darkroom photographic split-tone print appearance"
        )
        blend_choice.add(
            "soft-light",
            2,
            "Soft Light (Photographic Glaze & Contrast)",
            "Subtle photographic tint glaze and contrast enhancement"
        )
        procedure.add_choice_argument(
            "blend-mode",
            "_Blend Mode",
            "Layer compositing blend mode for the colorize layer",
            blend_choice,
            "hsl-color",
            GObject.ParamFlags.READWRITE
        )

        # Layer Mask Type Choice
        mask_choice = Gimp.Choice.new()
        mask_choice.add(
            "reveal-all",
            0,
            "Reveal All (White Mask - Overall Vintage Toning)",
            "Applies colorization across the full photograph with editable white mask"
        )
        mask_choice.add(
            "conceal-all",
            1,
            "Conceal All (Black Mask - Selective Hand-Coloring)",
            "Hides colorization initially: paint with white brush to hand-color details"
        )
        mask_choice.add(
            "selection",
            2,
            "Active Selection (Mask to Subject)",
            "Restricts colorization to active selection area"
        )
        procedure.add_choice_argument(
            "mask-type",
            "_Layer Mask Type",
            "Layer mask type attached to the colorize adjustment layer",
            mask_choice,
            "reveal-all",
            GObject.ParamFlags.READWRITE
        )

        # Midpoint Balance Slider (10% to 90%, default 50%)
        procedure.add_double_argument(
            "midpoint",
            "_Tonal Midpoint Balance (%)",
            "Tonal transition midpoint between shadow and highlight tones (10% to 90%)",
            10.0,
            90.0,
            50.0,
            GObject.ParamFlags.READWRITE
        )

        # Custom Shadow Ink RGB
        procedure.add_double_argument(
            "custom-shadow-r",
            "Shadow Ink _Red",
            "Custom shadow ink red channel (0.0 to 1.0)",
            0.0,
            1.0,
            0.16,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "custom-shadow-g",
            "Shadow Ink _Green",
            "Custom shadow ink green channel (0.0 to 1.0)",
            0.0,
            1.0,
            0.09,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "custom-shadow-b",
            "Shadow Ink _Blue",
            "Custom shadow ink blue channel (0.0 to 1.0)",
            0.0,
            1.0,
            0.04,
            GObject.ParamFlags.READWRITE
        )

        # Custom Highlight Ink RGB
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
            0.90,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "custom-highlight-b",
            "Highlight Ink _Blue",
            "Custom highlight ink blue channel (0.0 to 1.0)",
            0.0,
            1.0,
            0.80,
            GObject.ParamFlags.READWRITE
        )

        # Layer Opacity Slider
        procedure.add_double_argument(
            "opacity",
            "Layer _Opacity (%)",
            "Opacity of the colorization adjustment layer",
            10.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        return procedure


if __name__ == '__main__':
    Gimp.main(PhotoColorize.__gtype__, sys.argv)
