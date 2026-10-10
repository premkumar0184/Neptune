#!/usr/bin/env python3
"""
PhotoGIMP Non-Destructive Film Grain & Analog Texture Helper Plugin for GIMP 3.x

Creates a dedicated non-destructive Film Grain adjustment overlay layer duplicating
the natural physical texture of silver halide film crystals (35mm, 120 Medium Format,
High-ISO Gritty B&W, and Vintage Color grain) inspired by Adobe Photoshop's Grain
adjustment layer and Camera Raw Grain panel.

Photoshop Equivalence:
- Topics.txt line 105: Adjust texture with Grain.
- photoshop_docs.md Section 109 lines 3280-3300: Add grain to your image non-destructively
  using the Grain adjustment layer in professional photoeditor.
  - Amount: Controls the overall intensity of the grain.
  - Size: Adjusts the size of individual grain particles.
  - Roughness: Alters the randomness of the grain for a smoother or rougher look.

Key Advantages over destructive filtering:
1. 100% Non-Destructive: Uses an isolated neutral gray (#808080) overlay layer.
2. Mathematically Neutral Compositing: Under Soft Light and Overlay blending,
   neutral 50% gray contributes 0.000000 difference to underlying tones.
3. Authentic Analog Film Simulation:
   - Monochromatic grain: Simulates classic silver halide crystals (exact R=G=B channel neutrality).
   - Color grain: Simulates vintage chromatic dye clouds in color negative film.
   - Particle clustering: Models physical film emulsion grain clumping (Size parameter).
   - Random roughness: Balances fine archival smoothness against gritty high-ISO punch.
4. Curated Photographic Presets:
   - 35mm Classic Film Grain (Amount 35%, Size 2, Roughness 60%, Soft Light, Mono)
   - 120 Medium Format Subtle (Amount 18%, Size 1, Roughness 40%, Soft Light, Mono)
   - Gritty High-ISO Street (Amount 65%, Size 3, Roughness 85%, Overlay, Mono)
   - Vintage 1970s Color Grain (Amount 40%, Size 2, Roughness 50%, Soft Light, Color)
   - Fine Art Archival Print (Amount 25%, Size 1, Roughness 70%, Soft Light, Mono)
   - Custom Sliders
5. Reveal-All Layer Mask: Attached automatically for selective brush painting (e.g. keeping skies or faces clean).
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
    "35mm-classic": {
        "label": "35mm Classic Film Grain",
        "amount": 35.0,
        "size": 2,
        "roughness": 60.0,
        "blend": "soft-light",
        "monochrome": True,
    },
    "120-subtle": {
        "label": "120 Medium Format Subtle",
        "amount": 18.0,
        "size": 1,
        "roughness": 40.0,
        "blend": "soft-light",
        "monochrome": True,
    },
    "gritty-street": {
        "label": "Gritty High-ISO Street",
        "amount": 65.0,
        "size": 3,
        "roughness": 85.0,
        "blend": "overlay",
        "monochrome": True,
    },
    "vintage-color": {
        "label": "Vintage 1970s Color Grain",
        "amount": 40.0,
        "size": 2,
        "roughness": 50.0,
        "blend": "soft-light",
        "monochrome": False,
    },
    "fine-art": {
        "label": "Fine Art Archival Print",
        "amount": 25.0,
        "size": 1,
        "roughness": 70.0,
        "blend": "soft-light",
        "monochrome": True,
    },
    "custom": {
        "label": "Custom Grain",
    },
}


def film_grain(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-film-grain"),
                "No valid image provided.",
                0
            )
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-film-grain')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    # Read configuration parameters
    preset = config.get_property('preset')
    amount_val = config.get_property('amount')
    size_val = config.get_property('size')
    roughness_val = config.get_property('roughness')
    mono_val = config.get_property('monochrome')
    blend_val = config.get_property('blend-mode')
    opacity = config.get_property('opacity')
    add_mask = config.get_property('add-mask')

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
                GLib.quark_from_string("gimp-film-grain"),
                "No valid target layer found.",
                0
            )
        )

    Gimp.context_push()
    image.undo_group_start()

    try:
        preset_info = PRESETS.get(preset, PRESETS["35mm-classic"])
        label = preset_info.get("label", "Custom")
        layer_name = f"Film Grain ({label})"

        # Resolve numerical parameters
        if preset in PRESETS and preset != "custom":
            p = PRESETS[preset]
            amount = float(p["amount"])
            size = int(p["size"])
            roughness = float(p["roughness"])
            blend_mode_str = p["blend"]
            monochrome = bool(p["monochrome"])
        else:
            amount = max(0.0, min(100.0, float(amount_val)))
            size = max(1, min(10, int(size_val)))
            roughness = max(0.0, min(100.0, float(roughness_val)))
            blend_mode_str = blend_val
            monochrome = bool(mono_val)

        width = image.get_width()
        height = image.get_height()

        # Map blend mode
        if blend_mode_str == "overlay":
            gimp_blend_mode = Gimp.LayerMode.OVERLAY
        else:
            gimp_blend_mode = Gimp.LayerMode.SOFTLIGHT

        # Create dedicated neutral gray overlay layer
        grain_layer = Gimp.Layer.new(
            image,
            layer_name,
            width,
            height,
            Gimp.ImageType.RGB_IMAGE,
            max(10.0, min(100.0, float(opacity))),
            gimp_blend_mode
        )

        parent = target_layer.get_parent()
        pos = image.get_item_position(target_layer)
        image.insert_layer(grain_layer, parent, pos)

        # Fill with #808080 (neutral 50% gray identity)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.5, 0.5, 0.5)"))
        grain_layer.edit_fill(Gimp.FillType.FOREGROUND)

        # Apply GEGL Gaussian RGB Noise
        noise_level = (amount / 100.0) * 0.55
        if noise_level > 0.001:
            filt_noise = Gimp.DrawableFilter.new(grain_layer, "gegl:noise-rgb", "")
            n_cfg = filt_noise.get_config()
            n_cfg.set_property("independent", not monochrome)
            n_cfg.set_property("gaussian", True)
            n_cfg.set_property("red", float(noise_level))
            n_cfg.set_property("green", float(noise_level))
            n_cfg.set_property("blue", float(noise_level))
            n_cfg.set_property("alpha", 0.0)
            grain_layer.append_filter(filt_noise)
            grain_layer.merge_filters()

            # Particle Clustering (Size parameter)
            if size > 1:
                spread_px = min(6, int(size - 1))
                filt_sp = Gimp.DrawableFilter.new(grain_layer, "gegl:noise-spread", "")
                filt_sp.get_config().set_property("amount_x", spread_px)
                filt_sp.get_config().set_property("amount_y", spread_px)
                grain_layer.append_filter(filt_sp)
                grain_layer.merge_filters()

            # Roughness / Smoothing parameter
            if roughness < 50.0:
                blur_rad = ((50.0 - roughness) / 50.0) * 1.5
                filt_blur = Gimp.DrawableFilter.new(grain_layer, "gegl:gaussian-blur", "")
                filt_blur.get_config().set_property("std-dev-x", float(blur_rad))
                filt_blur.get_config().set_property("std-dev-y", float(blur_rad))
                grain_layer.append_filter(filt_blur)
                grain_layer.merge_filters()

        # Attach reveal-all layer mask if requested
        if add_mask:
            mask = grain_layer.create_mask(Gimp.AddMaskType.WHITE)
            grain_layer.add_mask(mask)

        # Select newly created grain layer
        image.set_selected_layers([grain_layer])

        Gimp.displays_flush()
        image.undo_group_end()
        Gimp.context_pop()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    except Exception as exc:
        image.undo_group_end()
        Gimp.context_pop()
        msg = "Film Grain layer creation failed: " + str(exc)
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-film-grain"),
                msg,
                0
            )
        )


class FilmGrainPlugin(Gimp.PlugIn):
    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-film-grain"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            film_grain,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        procedure.set_menu_label("Film _Grain...")
        procedure.set_documentation(
            "Creates a non-destructive analog film grain texture overlay layer",
            "Creates a dedicated non-destructive Film Grain adjustment overlay layer on neutral gray "
            "with Soft Light or Overlay blend mode. Simulates authentic analog silver halide film grain, "
            "controlling grain Amount, particle Size, Roughness, and Monochromatic vs Color dye clouds "
            "inspired by Adobe Photoshop and Adobe Camera Raw.",
            name
        )
        procedure.set_attribution("Antigravity Ralph / PhotoGIMP", "PhotoGIMP", "2026")

        procedure.add_menu_path("<Image>/Filters/Noise")
        procedure.add_menu_path("<Image>/Filters/Retouching")
        procedure.add_menu_path("<Image>/Layer")

        # Preset Choice Argument
        preset_choice = Gimp.Choice.new()
        preset_choice.add(
            "35mm-classic",
            0,
            "35mm Classic Film Grain",
            "Natural analog 35mm film grain with moderate texture and silver halide clustering"
        )
        preset_choice.add(
            "120-subtle",
            1,
            "120 Medium Format Subtle",
            "Subtle fine grain texture characteristic of 120 medium format photographic emulsions"
        )
        preset_choice.add(
            "gritty-street",
            2,
            "Gritty High-ISO Street",
            "High-contrast, gritty high-ISO street photography grain with punchy overlay blending"
        )
        preset_choice.add(
            "vintage-color",
            3,
            "Vintage 1970s Color Grain",
            "Organic chromatic dye clouds reproducing 1970s vintage color film stocks"
        )
        preset_choice.add(
            "fine-art",
            4,
            "Fine Art Archival Print",
            "Smooth, crisp fine-art archival paper print grain texture"
        )
        preset_choice.add(
            "custom",
            5,
            "Custom Grain",
            "Manually adjust Amount, Size, and Roughness sliders"
        )

        procedure.add_choice_argument(
            "preset",
            "_Preset",
            "Analog film grain preset look",
            preset_choice,
            "35mm-classic",
            GObject.ParamFlags.READWRITE
        )

        # Grain Amount Slider (0% to 100%, default 35%)
        procedure.add_double_argument(
            "amount",
            "_Amount (%)",
            "Overall intensity of the film grain (0% to 100%)",
            0.0,
            100.0,
            35.0,
            GObject.ParamFlags.READWRITE
        )

        # Particle Size Slider (1 to 10, default 2)
        procedure.add_int_argument(
            "size",
            "_Size",
            "Size and clustering of individual grain particles (1 to 10)",
            1,
            10,
            2,
            GObject.ParamFlags.READWRITE
        )

        # Roughness Slider (0% to 100%, default 60%)
        procedure.add_double_argument(
            "roughness",
            "_Roughness (%)",
            "Randomness and sharpness of the grain particles (0% to 100%)",
            0.0,
            100.0,
            60.0,
            GObject.ParamFlags.READWRITE
        )

        # Monochromatic Grain Option
        procedure.add_boolean_argument(
            "monochrome",
            "_Monochrome Grain",
            "Monochromatic silver halide grain (checked) or organic color dye clouds (unchecked)",
            True,
            GObject.ParamFlags.READWRITE
        )

        # Blend Mode Choice
        blend_choice = Gimp.Choice.new()
        blend_choice.add("soft-light", 0, "Soft Light (Natural)", "Subtle, photographic natural grain blending")
        blend_choice.add("overlay", 1, "Overlay (Gritty)", "High-contrast, punchy street photography grain blending")

        procedure.add_choice_argument(
            "blend-mode",
            "_Blend Mode",
            "Compositing blend mode for the grain overlay layer",
            blend_choice,
            "soft-light",
            GObject.ParamFlags.READWRITE
        )

        # Layer Opacity Slider (10% to 100%, default 100%)
        procedure.add_double_argument(
            "opacity",
            "Layer _Opacity (%)",
            "Overall opacity of the Film Grain adjustment layer (10% to 100%)",
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


Gimp.main(FilmGrainPlugin.__gtype__, sys.argv)
