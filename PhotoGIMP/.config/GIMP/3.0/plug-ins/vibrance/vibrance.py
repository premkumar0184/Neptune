#!/usr/bin/env python3
"""
PhotoGIMP Non-Destructive Vibrance & Smart Saturation Helper Plugin for GIMP 3.x

Creates a non-destructive Vibrance adjustment layer duplicating the target layer
and applying intelligent color saturation control powered by GEGL gegl:vibrance.
Vibrance enhances muted, desaturated tones while protecting already-saturated
colors and skin tones from clipping, inspired by Adobe Photoshop's Vibrance command.

Photoshop Equivalence:
- Topics.txt line 324: Adjust color saturation using a Vibrance adjustment layer.
- Topics.txt line 100: Correct color balance with Color and vibrance.
- photoshop_docs.md Section 104 & line 3194: Vibrance increases the intensity of muted colors.
- photoshop_docs.md Section 319 & line 9166-9188: Use a Vibrance adjustment layer to
  enhance muted colors while preserving skin tones and preventing color clipping.

Key Advantages over destructive uniform saturation:
1. 100% Non-Destructive: Duplicates active drawable into an isolated adjustment layer.
2. Intelligent Saturation Curve: Muted colors receive strong enhancement while vivid
   colors and human skin tones are protected from ugly orange color casting.
3. Dual Photoshop Controls: Direct Vibrance (-100 to +100) and Saturation (-100 to +100) sliders.
4. Curated Photographic Presets: Portrait (skin-safe), Landscape, Vivid, Subtle, Muted, and Custom.
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
    "default": (25.0, 0.0, "Default (+25 Vibrance)"),
    "portrait": (30.0, -5.0, "Portrait (Skin Tone Safe)"),
    "landscape": (50.0, 10.0, "Landscape (Sky & Foliage)"),
    "vivid": (65.0, 20.0, "Vivid Pop"),
    "subtle": (15.0, 0.0, "Subtle Lift"),
    "muted": (-30.0, -20.0, "Muted Aesthetic"),
    "custom": (None, None, "Custom Sliders"),
}


def vibrance(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-vibrance"),
                "No valid image provided.",
                0
            )
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-vibrance')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    # Read configuration parameters
    preset = config.get_property('preset')
    custom_vib = config.get_property('vibrance')
    custom_sat = config.get_property('saturation')
    opacity = config.get_property('opacity')
    add_mask = config.get_property('add-mask')

    # Resolve vibrance and saturation values
    if preset in PRESETS and preset != "custom":
        vib_val, sat_val, label = PRESETS[preset]
    else:
        vib_val = float(custom_vib)
        sat_val = float(custom_sat)
        label = f"Vib {int(vib_val):+d}, Sat {int(sat_val):+d}"

    # Map user-facing -100..+100 saturation to GEGL scale factor (0.0 .. 10.0, where 1.0 is unity)
    gegl_sat = max(0.0, min(10.0, 1.0 + (sat_val / 100.0)))
    gegl_vib = max(-100.0, min(100.0, float(vib_val)))

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
                GLib.quark_from_string("gimp-vibrance"),
                "No valid target layer found.",
                0
            )
        )

    Gimp.context_push()
    image.undo_group_start()

    try:
        layer_name = f"Vibrance ({label})"
        vib_layer = Gimp.Layer.new_from_drawable(target_layer, image)
        vib_layer.set_name(layer_name)
        vib_layer.set_opacity(max(10.0, min(100.0, float(opacity))))
        vib_layer.set_mode(Gimp.LayerMode.NORMAL)

        parent = target_layer.get_parent()
        pos = image.get_item_position(target_layer)
        image.insert_layer(vib_layer, parent, pos)

        # Apply GEGL vibrance filter
        filt = Gimp.DrawableFilter.new(vib_layer, "gegl:vibrance", "")
        cfg = filt.get_config()
        cfg.set_property("vibrance", float(gegl_vib))
        cfg.set_property("saturation", float(gegl_sat))
        vib_layer.merge_filter(filt)

        # Attach reveal-all layer mask if requested
        if add_mask:
            mask = vib_layer.create_mask(Gimp.AddMaskType.WHITE)
            vib_layer.add_mask(mask)

        # Set newly created layer as active
        image.set_selected_layers([vib_layer])

        Gimp.displays_flush()
        image.undo_group_end()
        Gimp.context_pop()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    except Exception as exc:
        image.undo_group_end()
        Gimp.context_pop()
        msg = "Vibrance layer creation failed: " + str(exc)
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-vibrance"),
                msg,
                0
            )
        )


class VibrancePlugin(Gimp.PlugIn):
    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-vibrance"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            vibrance,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        procedure.set_menu_label("_Vibrance...")
        procedure.set_documentation(
            "Enhances muted colors while preserving skin tones and preventing color clipping",
            "Creates a dedicated non-destructive Vibrance adjustment layer powered by GEGL gegl:vibrance. "
            "Applies intelligent saturation control that boosts muted tones while protecting already-saturated "
            "colors and skin tones from blowout, inspired by Adobe Photoshop.",
            name
        )
        procedure.set_attribution("Antigravity Ralph / PhotoGIMP", "PhotoGIMP", "2026")

        procedure.add_menu_path("<Image>/Colors")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        # Preset Choice Argument
        preset_choice = Gimp.Choice.new()
        preset_choice.add(
            "default",
            0,
            "Default (+25 Vibrance)",
            "Balanced intelligent saturation boost for general photography"
        )
        preset_choice.add(
            "portrait",
            1,
            "Portrait (Skin Tone Safe)",
            "Lifts background and eyes while gently protecting delicate skin tones"
        )
        preset_choice.add(
            "landscape",
            2,
            "Landscape (Sky & Foliage)",
            "Stronger vibrancy boost bringing out deep vegetation greens and sky blues"
        )
        preset_choice.add(
            "vivid",
            3,
            "Vivid Pop",
            "High impact vibrant color boost for advertising and creative styles"
        )
        preset_choice.add(
            "subtle",
            4,
            "Subtle Lift",
            "Gentle natural color lift for conservative retouching"
        )
        preset_choice.add(
            "muted",
            5,
            "Muted Aesthetic",
            "Subtle desaturation and film-like tonal muting"
        )
        preset_choice.add(
            "custom",
            6,
            "Custom Sliders",
            "Specify custom Vibrance and Saturation slider values"
        )

        procedure.add_choice_argument(
            "preset",
            "_Preset",
            "Vibrance adjustment style preset",
            preset_choice,
            "default",
            GObject.ParamFlags.READWRITE
        )

        # Vibrance Slider (-100 to +100, default +25)
        procedure.add_double_argument(
            "vibrance",
            "_Vibrance",
            "Intelligent chroma boost for muted colors (-100 to +100)",
            -100.0,
            100.0,
            25.0,
            GObject.ParamFlags.READWRITE
        )

        # Saturation Slider (-100 to +100, default 0)
        procedure.add_double_argument(
            "saturation",
            "_Saturation",
            "Uniform saturation adjustment factor (-100 to +100)",
            -100.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # Layer Opacity Slider (10% to 100%, default 100%)
        procedure.add_double_argument(
            "opacity",
            "Layer _Opacity",
            "Overall opacity of the Vibrance adjustment layer (10% to 100%)",
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


Gimp.main(VibrancePlugin.__gtype__, sys.argv)
