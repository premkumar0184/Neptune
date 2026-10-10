#!/usr/bin/env python3
"""
PhotoGIMP Non-Destructive Clarity & Dehaze Helper Plugin for GIMP 3.x

Creates a dedicated non-destructive Clarity & Dehaze adjustment layer duplicating
the target drawable and applying midtone local contrast amplification (Clarity)
and atmospheric haze reduction (Dehaze) inspired by Adobe Photoshop and Adobe Camera Raw.

Photoshop Equivalence:
- Topics.txt line 104: Adjust contrast with Clarity and Dehaze.
- photoshop_docs.md Section 108 line 3260-3277: Adjust midtone contrast and reduce haze non-destructively
  using the Clarity and dehaze adjustment layer in professional photoeditor.
  - Clarity: Adjusts midtone contrast and adds definition to images.
  - Dehaze: Adjusts haze and improves contrast.

Key Advantages over destructive filtering:
1. 100% Non-Destructive: Duplicates target layer into an isolated adjustment layer.
2. Authentic Midtone Local Contrast Enhancement (Clarity):
   - Positive Clarity boosts local micro-contrast around edges and texture without blown highlights.
   - Negative Clarity applies a gentle portrait glow softening skin blemishes and wrinkles.
3. Atmospheric Penetration / Fog Simulation (Dehaze):
   - Positive Dehaze cuts through atmospheric humidity and distance haze, restoring deep blacks and color.
   - Negative Dehaze introduces dreamy mist and atmospheric fog.
4. Curated Photographic Presets:
   - Landscape: Crisp Punch & Dehaze (Clarity +40, Dehaze +35)
   - Atmospheric: Cut Mountain Haze (Clarity +20, Dehaze +60)
   - Portrait: Soft Glamour Glow (Clarity -30, Dehaze 0)
   - Creative: Atmospheric Mist & Fog (Clarity -20, Dehaze -40)
   - Architecture: High-Structure Contrast (Clarity +60, Dehaze +20)
   - Custom Sliders (-100 to +100 Clarity, -100 to +100 Dehaze)
5. Reveal-All Layer Mask: Attached automatically for selective brush painting on subjects or skies.
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
    "landscape": {
        "label": "Landscape: Crisp Punch & Dehaze",
        "clarity": 40.0,
        "dehaze": 35.0,
    },
    "cut-haze": {
        "label": "Atmospheric: Cut Mountain Haze",
        "clarity": 20.0,
        "dehaze": 60.0,
    },
    "soft-portrait": {
        "label": "Portrait: Soft Glamour Glow",
        "clarity": -30.0,
        "dehaze": 0.0,
    },
    "mist-fog": {
        "label": "Creative: Atmospheric Mist & Fog",
        "clarity": -20.0,
        "dehaze": -40.0,
    },
    "architecture": {
        "label": "Architecture: High-Structure Contrast",
        "clarity": 60.0,
        "dehaze": 20.0,
    },
    "custom": {
        "label": "Custom Clarity & Dehaze",
    },
}


def clarity_dehaze(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-clarity-dehaze"),
                "No valid image provided.",
                0
            )
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-clarity-dehaze')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    # Read configuration parameters
    preset = config.get_property('preset')
    clarity_val = config.get_property('clarity')
    dehaze_val = config.get_property('dehaze')
    opacity = config.get_property('opacity')
    add_mask = config.get_property('add-mask')

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
                GLib.quark_from_string("gimp-clarity-dehaze"),
                "No valid target layer found.",
                0
            )
        )

    Gimp.context_push()
    image.undo_group_start()

    try:
        preset_info = PRESETS.get(preset, PRESETS["landscape"])
        label = preset_info.get("label", "Custom")
        layer_name = f"Clarity & Dehaze ({label})"

        # Resolve numerical Clarity and Dehaze amounts
        if preset in PRESETS and preset != "custom":
            p = PRESETS[preset]
            c_amount = float(p["clarity"])
            d_amount = float(p["dehaze"])
        else:
            c_amount = max(-100.0, min(100.0, float(clarity_val)))
            d_amount = max(-100.0, min(100.0, float(dehaze_val)))

        # Create non-destructive duplicate layer
        cd_layer = Gimp.Layer.new_from_drawable(target_layer, image)
        cd_layer.set_name(layer_name)
        cd_layer.set_opacity(max(10.0, min(100.0, float(opacity))))
        cd_layer.set_mode(Gimp.LayerMode.NORMAL)

        parent = target_layer.get_parent()
        pos = image.get_item_position(target_layer)
        image.insert_layer(cd_layer, parent, pos)

        # 1. Apply Clarity Filter:
        # Positive Clarity: Wide-radius edge-preserving unsharp mask for midtone local contrast
        if c_amount > 0.001:
            scale_val = (c_amount / 100.0) * 1.5
            filt_c = Gimp.DrawableFilter.new(cd_layer, "gegl:unsharp-mask", "")
            filt_c_cfg = filt_c.get_config()
            filt_c_cfg.set_property("std-dev", 25.0)
            filt_c_cfg.set_property("scale", float(scale_val))
            filt_c_cfg.set_property("threshold", 0.0)
            cd_layer.append_filter(filt_c)
            cd_layer.merge_filters()
        # Negative Clarity: Soft portrait glow
        elif c_amount < -0.001:
            blur_radius = (-c_amount / 100.0) * 4.0
            filt_blur = Gimp.DrawableFilter.new(cd_layer, "gegl:gaussian-blur", "")
            filt_blur_cfg = filt_blur.get_config()
            filt_blur_cfg.set_property("std-dev-x", float(blur_radius))
            filt_blur_cfg.set_property("std-dev-y", float(blur_radius))
            cd_layer.append_filter(filt_blur)
            cd_layer.merge_filters()

        # 2. Apply Dehaze Filter:
        # Modulates contrast (identity=1.0), brightness, and color saturation
        if abs(d_amount) > 0.001:
            contrast_val = 1.0 + (d_amount / 100.0) * 0.40
            brightness_adj = -(d_amount / 100.0) * 0.08
            filt_bc = Gimp.DrawableFilter.new(cd_layer, "gegl:brightness-contrast", "")
            filt_bc_cfg = filt_bc.get_config()
            filt_bc_cfg.set_property("contrast", float(contrast_val))
            filt_bc_cfg.set_property("brightness", float(brightness_adj))
            cd_layer.append_filter(filt_bc)
            cd_layer.merge_filters()

            # Positive dehaze also recovers chromatic vibrance lost to Rayleigh scattering
            if d_amount > 0.001:
                vib_amount = (d_amount / 100.0) * 0.30
                filt_vib = Gimp.DrawableFilter.new(cd_layer, "gegl:vibrance", "")
                filt_vib_cfg = filt_vib.get_config()
                filt_vib_cfg.set_property("vibrance", float(vib_amount))
                cd_layer.append_filter(filt_vib)
                cd_layer.merge_filters()

        # Attach reveal-all layer mask if requested
        if add_mask:
            mask = cd_layer.create_mask(Gimp.AddMaskType.WHITE)
            cd_layer.add_mask(mask)

        # Set newly created layer as active
        image.set_selected_layers([cd_layer])

        Gimp.displays_flush()
        image.undo_group_end()
        Gimp.context_pop()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    except Exception as exc:
        image.undo_group_end()
        Gimp.context_pop()
        msg = "Clarity & Dehaze layer creation failed: " + str(exc)
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-clarity-dehaze"),
                msg,
                0
            )
        )


class ClarityDehazePlugin(Gimp.PlugIn):
    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-clarity-dehaze"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            clarity_dehaze,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        procedure.set_menu_label("Clarity and _Dehaze...")
        procedure.set_documentation(
            "Enhances midtone local contrast and reduces atmospheric haze",
            "Creates a dedicated non-destructive Clarity & Dehaze adjustment layer duplicating the target drawable. "
            "Clarity enhances midtone local contrast and texture definition. Dehaze cuts through humidity, fog, "
            "and atmospheric haze to restore deep contrast and vibrant color inspired by Adobe Photoshop.",
            name
        )
        procedure.set_attribution("Antigravity Ralph / PhotoGIMP", "PhotoGIMP", "2026")

        procedure.add_menu_path("<Image>/Colors")
        procedure.add_menu_path("<Image>/Filters/Enhance")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        # Preset Choice Argument
        preset_choice = Gimp.Choice.new()
        preset_choice.add(
            "landscape",
            0,
            "Landscape: Crisp Punch & Dehaze",
            "Punch through landscape haze with crisp foliage and rock definition (Clarity +40, Dehaze +35)"
        )
        preset_choice.add(
            "cut-haze",
            1,
            "Atmospheric: Cut Mountain Haze",
            "Strong haze reduction for distant mountain ranges and foggy horizons (Clarity +20, Dehaze +60)"
        )
        preset_choice.add(
            "soft-portrait",
            2,
            "Portrait: Soft Glamour Glow",
            "Gentle negative clarity skin softening and subtle glamour glow (Clarity -30, Dehaze 0)"
        )
        preset_choice.add(
            "mist-fog",
            3,
            "Creative: Atmospheric Mist & Fog",
            "Soft atmospheric fog and dreamy ambient mist effect (Clarity -20, Dehaze -40)"
        )
        preset_choice.add(
            "architecture",
            4,
            "Architecture: High-Structure Contrast",
            "High-impact midtone structural contrast for urban and architectural scenes (Clarity +60, Dehaze +20)"
        )
        preset_choice.add(
            "custom",
            5,
            "Custom Clarity & Dehaze",
            "Manually adjust Clarity and Dehaze sliders"
        )

        procedure.add_choice_argument(
            "preset",
            "_Preset",
            "Clarity and Dehaze preset style",
            preset_choice,
            "landscape",
            GObject.ParamFlags.READWRITE
        )

        # Clarity Slider (-100 to +100, default 40.0)
        procedure.add_double_argument(
            "clarity",
            "_Clarity",
            "Midtone local contrast enhancement (-100 to +100)",
            -100.0,
            100.0,
            40.0,
            GObject.ParamFlags.READWRITE
        )

        # Dehaze Slider (-100 to +100, default 35.0)
        procedure.add_double_argument(
            "dehaze",
            "_Dehaze",
            "Atmospheric haze reduction and contrast restoration (-100 to +100)",
            -100.0,
            100.0,
            35.0,
            GObject.ParamFlags.READWRITE
        )

        # Layer Opacity Slider (10% to 100%, default 100%)
        procedure.add_double_argument(
            "opacity",
            "Layer _Opacity (%)",
            "Overall opacity of the Clarity & Dehaze adjustment layer (10% to 100%)",
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


Gimp.main(ClarityDehazePlugin.__gtype__, sys.argv)
