#!/usr/bin/env python3
"""
PhotoGIMP Non-Destructive Diffuse Glow & Glamour Filter Helper Plugin for GIMP 3.x

Creates a dedicated non-destructive Diffuse Glow adjustment layer duplicating the
active drawable, blooming highlights into luminous halos, softening skin and contrast,
and optionally adding subtle optical diffusion grain texture. Inspired by Adobe
Photoshop's Diffuse Glow filter (Filter Gallery -> Distort -> Diffuse Glow) and
Photoshop Quick Action "Apply diffuse glow to images".

Photoshop Equivalence:
- Topics.txt line 663: Quick actions - Apply diffuse glow to images.
- Topics.txt line 12131: Filter Gallery - Distort: Diffuse Glow.
- photoshop_docs.md Section 417 line 12131:
  "Diffuse Glow renders an image as though it were viewed through a soft diffusion
   filter. The filter adds translucent white noise, with the glow fading from the center
   of a selection."

Key Advantages over stock destructive editing:
1. 100% Non-Destructive: Duplicates active drawable into an isolated adjustment layer.
2. Authentic Photoshop Controls:
   - Glow Amount (0-100%): Controls bloom intensity and luminance radiance.
   - Clear Amount (0-100%): Higher threshold values keep darker tones clear and
     restrict the glow exclusively to specular highlights.
   - Diffusion Radius (1-100px): Optical spread of the soft focus halo.
   - Graininess (0-50%): Translucent organic diffusion grain added to the glow layer,
     simulating physical diffusion glass (Pro-Mist / Fog filters).
   - Warmth Tint (0-3000K): Optional golden hour color temperature shift for warm
     editorial glamour portraits.
3. Curated Creative Presets:
   - Dreamy Glamour Portrait: Soft-focus beauty look with gentle highlight bloom (Soft Light).
   - Ethereal Sunlight Bloom: Luminous highlight radiance with wide diffusion halos (Screen).
   - Vintage Diffusion Glass: Classic diffusion filter with visible grain texture (Soft Light).
   - Golden Hour Warm Glow: Sunset amber highlight bloom with rich warm color tone (Screen).
   - Night Neon Radiance: High-threshold specular bloom for cityscapes and neon (Addition).
   - Subtle Soft Focus: Delicate skin smoothing and gentle highlight diffusion (Soft Light).
   - Custom Sliders: Full manual control across all parameters.
4. Compositing Blend Modes:
   - Screen: Classic luminous highlight bloom.
   - Soft Light: Dreamy contrast and glamour portrait softening.
   - Addition: Intense specular radiance for night and neon photography.
   - Normal: Direct diffusion filter appearance.
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
    "dreamy-glamour": {
        "label": "Dreamy Glamour Portrait",
        "desc": "Soft-focus beauty look with gentle highlight bloom and skin softening",
        "glow_amount": 45.0,
        "clear_amount": 45.0,
        "radius": 15.0,
        "graininess": 8.0,
        "warmth": 0.0,
        "blend_mode": "soft-light",
        "opacity": 80.0,
    },
    "ethereal-bloom": {
        "label": "Ethereal Sunlight Bloom",
        "desc": "Luminous highlight radiance with wide diffusion halos",
        "glow_amount": 65.0,
        "clear_amount": 55.0,
        "radius": 25.0,
        "graininess": 0.0,
        "warmth": 0.0,
        "blend_mode": "screen",
        "opacity": 85.0,
    },
    "vintage-diffusion": {
        "label": "Vintage Diffusion Glass",
        "desc": "Classic camera diffusion filter with visible silver halide grain texture",
        "glow_amount": 50.0,
        "clear_amount": 40.0,
        "radius": 12.0,
        "graininess": 22.0,
        "warmth": 0.0,
        "blend_mode": "soft-light",
        "opacity": 85.0,
    },
    "golden-hour-bloom": {
        "label": "Golden Hour Warm Glow",
        "desc": "Sunset amber highlight bloom with rich warm color temperature",
        "glow_amount": 55.0,
        "clear_amount": 50.0,
        "radius": 20.0,
        "graininess": 5.0,
        "warmth": 2000.0,
        "blend_mode": "screen",
        "opacity": 75.0,
    },
    "night-radiance": {
        "label": "Night Neon Radiance",
        "desc": "High-threshold specular bloom for street lights and neon signs",
        "glow_amount": 75.0,
        "clear_amount": 70.0,
        "radius": 30.0,
        "graininess": 0.0,
        "warmth": 0.0,
        "blend_mode": "addition",
        "opacity": 90.0,
    },
    "subtle-softfocus": {
        "label": "Subtle Soft Focus",
        "desc": "Delicate skin smoothing and gentle highlight diffusion",
        "glow_amount": 25.0,
        "clear_amount": 40.0,
        "radius": 8.0,
        "graininess": 0.0,
        "warmth": 0.0,
        "blend_mode": "soft-light",
        "opacity": 60.0,
    },
    "custom": {
        "label": "Custom Sliders",
        "desc": "Full manual control using custom slider values",
    },
}

BLEND_MODES = {
    "screen": Gimp.LayerMode.SCREEN,
    "soft-light": Gimp.LayerMode.SOFTLIGHT,
    "addition": Gimp.LayerMode.ADDITION,
    "normal": Gimp.LayerMode.NORMAL,
}


def diffuse_glow(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-diffuse-glow"),
                "No valid image provided.",
                0
            )
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-diffuse-glow')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(
                Gimp.PDBStatusType.CANCEL,
                GLib.Error()
            )
        dialog.destroy()

    if not drawables:
        selected_layers = image.get_selected_layers()
        if selected_layers:
            target_drawable = selected_layers[0]
        else:
            layers = image.get_layers()
            if not layers:
                return procedure.new_return_values(
                    Gimp.PDBStatusType.CALLING_ERROR,
                    GLib.Error.new_literal(
                        GLib.quark_from_string("gimp-diffuse-glow"),
                        "Image contains no layers to apply diffuse glow to.",
                        0
                    )
                )
            target_drawable = layers[0]
    else:
        target_drawable = drawables[0]

    # Read configuration values
    preset = config.get_property("preset")
    g_amount = config.get_property("glow-amount")
    c_amount = config.get_property("clear-amount")
    rad = config.get_property("radius")
    grain = config.get_property("graininess")
    warm = config.get_property("warmth")
    b_mode = config.get_property("blend-mode")
    opac = config.get_property("opacity")
    add_mask = config.get_property("add-mask")

    # If a recognized preset is chosen (and not 'custom'), load its preset parameters
    if preset in PRESETS and preset != "custom":
        p_def = PRESETS[preset]
        g_amount = p_def.get("glow_amount", g_amount)
        c_amount = p_def.get("clear_amount", c_amount)
        rad = p_def.get("radius", rad)
        grain = p_def.get("graininess", grain)
        warm = p_def.get("warmth", warm)
        b_mode = p_def.get("blend_mode", b_mode)
        opac = p_def.get("opacity", opac)
        preset_label = p_def["label"]
    else:
        preset_label = "Custom"

    # Clamp parameters safely
    g_amount = max(0.0, min(100.0, float(g_amount)))
    c_amount = max(0.0, min(100.0, float(c_amount)))
    rad = max(1.0, min(100.0, float(rad)))
    grain = max(0.0, min(50.0, float(grain)))
    warm = max(0.0, min(3000.0, float(warm)))
    opac = max(10.0, min(100.0, float(opac)))

    layer_mode = BLEND_MODES.get(b_mode.lower(), Gimp.LayerMode.SOFTLIGHT)

    image.undo_group_start()
    Gimp.context_push()

    try:
        # Determine parent group and position
        parent = target_drawable.get_parent()
        position = 0
        if parent:
            children = parent.get_children()
            if target_drawable in children:
                position = children.index(target_drawable)
        else:
            top_layers = image.get_layers()
            if target_drawable in top_layers:
                position = top_layers.index(target_drawable)

        # Duplicate target drawable into isolated Diffuse Glow layer
        glow_layer = target_drawable.copy()
        glow_layer.set_name(f"Diffuse Glow ({preset_label})")
        glow_layer.set_mode(layer_mode)
        glow_layer.set_opacity(opac)

        image.insert_layer(glow_layer, parent, position)

        # 1. Apply GEGL Bloom filter (Highlight glow & diffusion)
        filt_bloom = Gimp.DrawableFilter.new(glow_layer, "gegl:bloom", "")
        cfg_bloom = filt_bloom.get_config()
        cfg_bloom.set_property("threshold", float(c_amount))
        cfg_bloom.set_property("radius", float(rad))
        cfg_bloom.set_property("strength", float(g_amount))
        cfg_bloom.set_property("softness", 25.0)
        glow_layer.append_filter(filt_bloom)
        glow_layer.merge_filters()

        # 2. Apply translucent organic grain if graininess > 0
        if grain > 0.001:
            noise_val = (grain / 100.0) * 0.20
            filt_noise = Gimp.DrawableFilter.new(glow_layer, "gegl:noise-rgb", "")
            cfg_noise = filt_noise.get_config()
            cfg_noise.set_property("independent", False)  # Monochromatic silver halide grain
            cfg_noise.set_property("gaussian", True)
            cfg_noise.set_property("red", float(noise_val))
            cfg_noise.set_property("green", float(noise_val))
            cfg_noise.set_property("blue", float(noise_val))
            glow_layer.append_filter(filt_noise)
            glow_layer.merge_filters()

        # 3. Apply golden hour warmth tint if warmth > 0
        if warm > 0.001:
            filt_temp = Gimp.DrawableFilter.new(glow_layer, "gegl:color-temperature", "")
            cfg_temp = filt_temp.get_config()
            cfg_temp.set_property("original-temperature", 6500.0)
            cfg_temp.set_property("intended-temperature", float(6500.0 + warm))
            glow_layer.append_filter(filt_temp)
            glow_layer.merge_filters()

        # 4. Attach optional reveal-all layer mask
        if add_mask:
            mask = glow_layer.create_mask(Gimp.AddMaskType.WHITE)
            glow_layer.add_mask(mask)

        # Select newly created adjustment layer
        image.set_selected_layers([glow_layer])
        Gimp.displays_flush()

    except Exception as e:
        image.undo_group_end()
        Gimp.context_pop()
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-diffuse-glow"),
                f"Diffuse glow processing failed: {str(e)}",
                0
            )
        )

    image.undo_group_end()
    Gimp.context_pop()

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


class DiffuseGlowPlugin(Gimp.PlugIn):
    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-diffuse-glow"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            diffuse_glow,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        procedure.set_menu_label("Diffuse _Glow...")
        procedure.set_documentation(
            "Creates a non-destructive Diffuse Glow and glamour soft-focus adjustment layer",
            "Creates a dedicated non-destructive Diffuse Glow adjustment layer duplicating active drawable. "
            "Blooms highlights into luminous halos, softens skin, and adds optional diffusion grain texture "
            "inspired by Adobe Photoshop's Diffuse Glow filter and Quick Action.",
            name
        )
        procedure.set_attribution("Antigravity Ralph / PhotoGIMP", "PhotoGIMP", "2026")

        procedure.add_menu_path("<Image>/Filters/Light and Shadow")
        procedure.add_menu_path("<Image>/Filters/Retouching")
        procedure.add_menu_path("<Image>/Colors")
        procedure.add_menu_path("<Image>/Layer")

        # Arguments
        procedure.add_string_argument(
            "preset",
            "Preset",
            "Photographic and creative diffusion glow preset (dreamy-glamour, ethereal-bloom, "
            "vintage-diffusion, golden-hour-bloom, night-radiance, subtle-softfocus, custom)",
            "dreamy-glamour",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "glow-amount",
            "Glow Amount (%)",
            "Strength and luminance of the diffusion bloom (0-100%)",
            0.0,
            100.0,
            50.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "clear-amount",
            "Clear Amount / Threshold (%)",
            "Clearness threshold (0-100%). Higher values keep darker tones clear and restrict bloom to highlights",
            0.0,
            100.0,
            50.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "radius",
            "Diffusion Radius (px)",
            "Spread radius of the optical diffusion halo (1-100px)",
            1.0,
            100.0,
            15.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "graininess",
            "Graininess (%)",
            "Translucent organic diffusion grain added to the glow layer (0-50%)",
            0.0,
            50.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "warmth",
            "Warmth Tint (Kelvin)",
            "Golden amber warming shift applied to the glow bloom (0-3000K)",
            0.0,
            3000.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_string_argument(
            "blend-mode",
            "Blend Mode",
            "Compositing blend mode (screen, soft-light, addition, normal)",
            "soft-light",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "opacity",
            "Layer Opacity (%)",
            "Overall opacity of the Diffuse Glow adjustment layer (10-100%)",
            10.0,
            100.0,
            80.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_boolean_argument(
            "add-mask",
            "Add Layer Mask",
            "Attach a reveal-all white layer mask for selective brush painting",
            True,
            GObject.ParamFlags.READWRITE
        )

        return procedure


Gimp.main(DiffuseGlowPlugin.__gtype__, sys.argv)
