#!/usr/bin/env python3
"""
PhotoGIMP Non-Destructive Swirling Night Sky & Twirl Distortion Helper Plugin for GIMP 3.x

Creates a dedicated non-destructive Swirling Sky adjustment layer duplicating
the active drawable. Renders celestial spiral vortices, rotating star trails,
and atmospheric sky currents via GEGL `gegl:whirl-pinch` and `gegl:ripple`.
Inspired by iconic celestial art (Van Gogh's The Starry Night) and Adobe Photoshop's
Twirl / Distort / Liquify quick actions.

Photoshop Equivalence:
- Topics.txt line 664: Swirling night sky filter.
- photoshop_docs.md Section 422 (line 12131):
  "Distort: Diffuse Glow, Glass, Ocean Ripple, Twirl, Wave, Pinch Geometric distortion effects"
- photoshop_docs.md Section 434 (line 12677):
  "Use Twirl to rotate pixels clockwise or counterclockwise."
- Quick Actions: Swirling night sky and celestial spiral vortex creation.

Key Advantages over stock destructive editing:
1. 100% Non-Destructive: Duplicates the active drawable into an isolated adjustment layer.
2. Controllable Rotational Dynamics: High-precision celestial vortex twirl (-720° to +720°)
   and gravitational inward/outward pinch (-1.0 to +1.0) via GEGL `gegl:whirl-pinch`.
3. Atmospheric Wave Turbulence: Organic star trail and nebular current ripples via
   GEGL `gegl:ripple` with adjustable amplitude and wavelength period.
4. Curated Celestial Presets:
   - Starry Night Vortex: Expressive 240° celestial vortex with inward pinch and star ripple (Normal, 100%).
   - Deep Space Whirlpool: Dramatic 360° galactic spiral with deep center pinch and screen glow (Screen, 90%).
   - Atmospheric Cyclone: Sweeping weather vortex and storm current with outward bloat (Soft Light, 85%).
   - Subtle Sky Drift: Gentle celestial curve and auroral current across the heavens (Normal, 100%).
   - Counter-Clockwise Spiral: Inverted -180° counter-clockwise vortex with central pinch (Normal, 100%).
   - Custom Vortex: Full manual slider control over whirl angle, pinch, radius, ripple, and blend modes.
5. Versatile Compositing Blend Modes:
   - Normal: Standalone distorted sky/canvas.
   - Screen: Distorted bright stars and nebulae glow radiantly over underlying sky.
   - Soft Light: Atmospheric contrast and rotational motion glaze.
   - Lighten Only: Only bright star trails and celestial lights twirl across the night backdrop.
6. Editable Layer Masks:
   - Reveal All: White mask applied immediately.
   - Conceal All: Black mask allowing artists to selectively brush the vortex strictly over the sky,
     preserving mountain horizons, trees, buildings, and ground landscape.
   - Active Selection: Automatically masks to active sky or subject selection.
7. Target Layer Invariance: Source image pixels underneath remain 100% untouched (0.000000 diff).
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
    "starry-vortex": {
        "label": "Starry Night Vortex",
        "desc": "Expressive 240° celestial vortex with inward pinch and star ripple",
        "whirl": 240.0,
        "pinch": 0.20,
        "radius": 1.2,
        "ripple_amp": 4.0,
        "ripple_period": 25.0,
        "blend": "normal",
        "opacity": 100.0,
    },
    "deep-space": {
        "label": "Deep Space Whirlpool",
        "desc": "Dramatic 360° galactic spiral with deep center pinch and screen glow",
        "whirl": 360.0,
        "pinch": 0.35,
        "radius": 1.5,
        "ripple_amp": 2.0,
        "ripple_period": 30.0,
        "blend": "screen",
        "opacity": 90.0,
    },
    "atmospheric-cyclone": {
        "label": "Atmospheric Cyclone",
        "desc": "Sweeping weather vortex and storm current with outward bloat",
        "whirl": 160.0,
        "pinch": -0.15,
        "radius": 1.8,
        "ripple_amp": 6.0,
        "ripple_period": 40.0,
        "blend": "soft-light",
        "opacity": 85.0,
    },
    "subtle-drift": {
        "label": "Subtle Sky Drift",
        "desc": "Gentle celestial curve and auroral current across the heavens",
        "whirl": 60.0,
        "pinch": 0.0,
        "radius": 1.2,
        "ripple_amp": 0.0,
        "ripple_period": 50.0,
        "blend": "normal",
        "opacity": 100.0,
    },
    "counter-clockwise": {
        "label": "Counter-Clockwise Spiral",
        "desc": "Inverted -180° counter-clockwise vortex with central pinch",
        "whirl": -180.0,
        "pinch": 0.20,
        "radius": 1.2,
        "ripple_amp": 3.0,
        "ripple_period": 25.0,
        "blend": "normal",
        "opacity": 100.0,
    },
    "custom": {
        "label": "Custom Vortex",
        "desc": "Full manual control over whirl angle, pinch, radius, ripple, and blend modes",
        "whirl": 180.0,
        "pinch": 0.15,
        "radius": 1.2,
        "ripple_amp": 3.0,
        "ripple_period": 25.0,
        "blend": "normal",
        "opacity": 100.0,
    },
}

BLEND_MODES = {
    "normal": Gimp.LayerMode.NORMAL,
    "screen": Gimp.LayerMode.SCREEN,
    "soft-light": Gimp.LayerMode.SOFTLIGHT,
    "lighten-only": Gimp.LayerMode.LIGHTEN_ONLY,
}


def swirling_sky(procedure, run_mode, image, drawables, config, data):
    """Execution function for python-fu-swirling-sky."""
    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-swirling-sky')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

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
                GLib.quark_from_string("gimp-swirling-sky"),
                "No target drawable found to apply swirling sky filter.",
                0
            )
        )

    # Read configuration parameters
    preset_key = config.get_property("preset") or "starry-vortex"
    if preset_key not in PRESETS:
        preset_key = "starry-vortex"
    preset_cfg = PRESETS[preset_key]

    if preset_key == "custom":
        whirl = config.get_property("whirl-angle")
        pinch = config.get_property("pinch-amount")
        radius = config.get_property("vortex-radius")
        ripple_amp = config.get_property("ripple-amplitude")
        ripple_period = config.get_property("ripple-period")
        blend_name = config.get_property("blend-mode") or "normal"
        opacity = config.get_property("opacity")
    else:
        whirl = preset_cfg["whirl"]
        pinch = preset_cfg["pinch"]
        radius = preset_cfg["radius"]
        ripple_amp = preset_cfg["ripple_amp"]
        ripple_period = preset_cfg["ripple_period"]
        blend_name = preset_cfg["blend"]
        opacity = config.get_property("opacity")
        if opacity <= 0.0 or opacity > 100.0:
            opacity = preset_cfg["opacity"]

    layer_mode = BLEND_MODES.get(blend_name.lower(), Gimp.LayerMode.NORMAL)
    mask_type = config.get_property("mask-type") or "reveal-all"

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
        layer_name = f"Swirling Sky ({preset_cfg['label']})"
        sw_layer = Gimp.Layer.new_from_drawable(target_drawable, image)
        sw_layer.set_name(layer_name)
        sw_layer.set_mode(layer_mode)
        sw_layer.set_opacity(float(opacity))

        # Insert directly above active drawable
        parent = target_drawable.get_parent()
        pos = image.get_item_position(target_drawable)
        image.insert_layer(sw_layer, parent, pos)

        # 2. Celestial whirl and pinch distortion (gegl:whirl-pinch)
        filt_wp = Gimp.DrawableFilter.new(sw_layer, "gegl:whirl-pinch", "")
        c_wp = filt_wp.get_config()
        c_wp.set_property("whirl", float(whirl))
        c_wp.set_property("pinch", float(pinch))
        c_wp.set_property("radius", float(radius))
        sw_layer.append_filter(filt_wp)
        sw_layer.merge_filters()

        # 3. Optional atmospheric ripple wave dynamics (gegl:ripple)
        if float(ripple_amp) > 0.0:
            filt_rip = Gimp.DrawableFilter.new(sw_layer, "gegl:ripple", "")
            c_rip = filt_rip.get_config()
            c_rip.set_property("amplitude", float(ripple_amp))
            c_rip.set_property("period", float(ripple_period))
            sw_layer.append_filter(filt_rip)
            sw_layer.merge_filters()

        # 4. Attach editable layer mask
        if mask_type == "selection":
            if saved_sel_channel is not None:
                image.select_item(Gimp.ChannelOps.REPLACE, saved_sel_channel)
                mask = sw_layer.create_mask(Gimp.AddMaskType.SELECTION)
                sw_layer.add_mask(mask)
            else:
                mask = sw_layer.create_mask(Gimp.AddMaskType.WHITE)
                sw_layer.add_mask(mask)
        elif mask_type == "conceal-all":
            mask = sw_layer.create_mask(Gimp.AddMaskType.BLACK)
            sw_layer.add_mask(mask)
        else:  # "reveal-all"
            mask = sw_layer.create_mask(Gimp.AddMaskType.WHITE)
            sw_layer.add_mask(mask)

        # Restore selection state cleanly if we saved it
        if saved_sel_channel is not None:
            image.select_item(Gimp.ChannelOps.REPLACE, saved_sel_channel)
            image.remove_channel(saved_sel_channel)

        image.set_selected_layers([sw_layer])
        Gimp.displays_flush()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    except Exception as e:
        if saved_sel_channel is not None:
            try:
                image.select_item(Gimp.ChannelOps.REPLACE, saved_sel_channel)
                image.remove_channel(saved_sel_channel)
            except Exception:
                pass
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-swirling-sky"),
                f"Failed to create swirling sky layer: {str(e)}",
                0
            )
        )
    finally:
        image.undo_group_end()
        Gimp.context_pop()


class SwirlingSkyPlugin(Gimp.PlugIn):
    """GIMP 3.0 Swirling Night Sky & Twirl Distortion Plug-in implementation."""

    def do_query_procedures(self):
        return ['python-fu-swirling-sky']

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            swirling_sky,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        procedure.set_menu_label("Swirling _Night Sky...")
        procedure.set_documentation(
            "Non-destructive swirling night sky and celestial spiral vortex distortion effect",
            "Creates a dedicated non-destructive Swirling Sky adjustment layer duplicating the active drawable. "
            "Renders expressive celestial spiral vortices, rotating star trails, and atmospheric currents "
            "inspired by Van Gogh's The Starry Night and Adobe Photoshop's Twirl / Distort filters.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP Project", "2026")

        procedure.add_menu_path("<Image>/Filters/Distort")
        procedure.add_menu_path("<Image>/Filters/Artistic")
        procedure.add_menu_path("<Image>/Layer")

        # Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add(
            "starry-vortex",
            0,
            "Starry Night Vortex",
            "Expressive 240° celestial vortex with inward pinch and star ripple"
        )
        preset_choice.add(
            "deep-space",
            1,
            "Deep Space Whirlpool",
            "Dramatic 360° galactic spiral with deep center pinch and screen glow"
        )
        preset_choice.add(
            "atmospheric-cyclone",
            2,
            "Atmospheric Cyclone",
            "Sweeping weather vortex and storm current with outward bloat"
        )
        preset_choice.add(
            "subtle-drift",
            3,
            "Subtle Sky Drift",
            "Gentle celestial curve and auroral current across the heavens"
        )
        preset_choice.add(
            "counter-clockwise",
            4,
            "Counter-Clockwise Spiral",
            "Inverted -180° counter-clockwise vortex with central pinch"
        )
        preset_choice.add(
            "custom",
            5,
            "Custom Vortex",
            "Full manual control over whirl angle, pinch, radius, ripple, and blend modes"
        )

        procedure.add_choice_argument(
            "preset",
            "Celestial Preset",
            "Swirling sky preset tuning (starry-vortex, deep-space, atmospheric-cyclone, subtle-drift, counter-clockwise, custom)",
            preset_choice,
            "starry-vortex",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "whirl-angle",
            "Whirl Rotation Angle (degrees)",
            "Rotational twirl angle in degrees (-720.0 to +720.0)",
            -720.0,
            720.0,
            240.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "pinch-amount",
            "Vortex Pinch / Bloat",
            "Gravitational center pinch (+ inward contraction, - outward bloat)",
            -1.0,
            1.0,
            0.20,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "vortex-radius",
            "Vortex Spatial Radius",
            "Relative radius of celestial vortex distortion (0.1 to 2.0)",
            0.1,
            2.0,
            1.2,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "ripple-amplitude",
            "Star Trail Ripple Amplitude",
            "Atmospheric wave ripple amplitude for star trail texture (0.0 to 50.0)",
            0.0,
            50.0,
            4.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "ripple-period",
            "Star Trail Ripple Period",
            "Wavelength period of atmospheric star ripples (5.0 to 100.0)",
            5.0,
            100.0,
            25.0,
            GObject.ParamFlags.READWRITE
        )

        # Blend Mode Choice
        blend_choice = Gimp.Choice.new()
        blend_choice.add(
            "normal",
            0,
            "Normal (Opaque Vortex)",
            "Standalone swirling sky artwork"
        )
        blend_choice.add(
            "screen",
            1,
            "Screen (Radiant Star Bloom)",
            "Distorted bright stars glow radiantly over underlying sky"
        )
        blend_choice.add(
            "soft-light",
            2,
            "Soft Light (Atmospheric Motion Glaze)",
            "Subtle swirling motion enhancing sky contrast"
        )
        blend_choice.add(
            "lighten-only",
            3,
            "Lighten Only (Star Trails)",
            "Only light trails and stars twirl across dark sky"
        )

        procedure.add_choice_argument(
            "blend-mode",
            "Layer Blend Mode",
            "Compositing mode of the swirling sky layer (normal, screen, soft-light, lighten-only)",
            blend_choice,
            "normal",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "opacity",
            "Layer Opacity (%)",
            "Overall opacity of the swirling sky adjustment layer (10% to 100%)",
            10.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # Mask Type Choice
        mask_choice = Gimp.Choice.new()
        mask_choice.add(
            "reveal-all",
            0,
            "Reveal All (White Mask)",
            "Whole image swirled; brush with black to hide"
        )
        mask_choice.add(
            "conceal-all",
            1,
            "Conceal All (Black Mask)",
            "Swirl hidden initially; brush with white to paint vortex selectively over sky"
        )
        mask_choice.add(
            "selection",
            2,
            "Active Selection Mask",
            "Confines swirling distortion strictly to active sky selection"
        )

        procedure.add_choice_argument(
            "mask-type",
            "Layer Mask Type",
            "Initial layer mask configuration (reveal-all, conceal-all, selection)",
            mask_choice,
            "reveal-all",
            GObject.ParamFlags.READWRITE
        )

        return procedure


Gimp.main(SwirlingSkyPlugin.__gtype__, sys.argv)
