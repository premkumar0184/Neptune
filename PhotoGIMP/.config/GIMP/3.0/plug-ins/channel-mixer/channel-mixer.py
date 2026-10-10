#!/usr/bin/env python3
"""
PhotoGIMP Non-Destructive Channel Mixer & Monochrome Infrared Helper Plugin for GIMP 3.x

Creates a dedicated non-destructive Channel Mixer adjustment layer duplicating
the target drawable and applying GEGL `gegl:channel-mixer` to rebalance color channels,
simulate specialized monochrome film looks, and recreate color infrared (Aerochrome)
photography inspired by Adobe Photoshop's Channel Mixer command.

Photoshop Equivalence:
- Topics.txt line 93-103: Color adjustment and fill layers - Work with adjustment layers.
- photoshop_docs.md line 3075: Channel Mixer: Rebalances color channels.
- photoshop_docs.md line 3219: Channel Mixer Rebalances color channels.

Key Advantages over destructive channel mixing:
1. 100% Non-Destructive: Duplicates target layer into an isolated adjustment layer.
2. Authentic Photographic Presets:
   - Color Infrared (Red/Blue Swap for surreal false-color Aerochrome look)
   - B&W Standard Neutral (40/40/20 balanced monochrome)
   - B&W Landscape (20/70/10 green boost for bright foliage and deep skies)
   - B&W Portrait (60/30/10 red boost for smooth skin tones)
   - B&W High Contrast / Red Filter (100/0/0 dramatic sky contrast)
   - Warm Golden Cast & Cool Cyan Cast
   - Custom Mixer Weights with Monochrome toggle and per-channel gain controls
3. Preserve Luminosity: Prevents perceived image brightness blowout during rebalancing.
4. Reveal-All Layer Mask: Attached automatically for selective brush painting.
5. Target Layer Invariance: Source image pixels underneath remain 100% untouched.
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
    "infrared-color": {
        "label": "Color Infrared (Red/Blue Swap)",
        "gains": (0.0, 0.0, 1.0,  0.0, 1.0, 0.0,  1.0, 0.0, 0.0),
        "preserve_lum": False,
    },
    "bw-standard": {
        "label": "B&W Standard Neutral (40/40/20)",
        "gains": (0.40, 0.40, 0.20,  0.40, 0.40, 0.20,  0.40, 0.40, 0.20),
        "preserve_lum": False,
    },
    "bw-landscape": {
        "label": "B&W Landscape (Green Boost 20/70/10)",
        "gains": (0.20, 0.70, 0.10,  0.20, 0.70, 0.10,  0.20, 0.70, 0.10),
        "preserve_lum": False,
    },
    "bw-portrait": {
        "label": "B&W Portrait (Red Boost 60/30/10)",
        "gains": (0.60, 0.30, 0.10,  0.60, 0.30, 0.10,  0.60, 0.30, 0.10),
        "preserve_lum": False,
    },
    "bw-high-contrast": {
        "label": "B&W High Contrast / Red Filter (100/0/0)",
        "gains": (1.00, 0.00, 0.00,  1.00, 0.00, 0.00,  1.00, 0.00, 0.00),
        "preserve_lum": False,
    },
    "warm-sunset": {
        "label": "Warm Golden Cast",
        "gains": (1.20, 0.00, 0.00,  0.00, 1.00, 0.00,  0.00, 0.00, 0.80),
        "preserve_lum": False,
    },
    "cool-cyan": {
        "label": "Cool Cyan Cast",
        "gains": (0.80, 0.00, 0.00,  0.00, 1.00, 0.00,  0.00, 0.00, 1.20),
        "preserve_lum": False,
    },
    "custom": {
        "label": "Custom Mixer Weights",
    },
}


def channel_mixer(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-channel-mixer"),
                "No valid image provided.",
                0
            )
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-channel-mixer')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    # Read configuration parameters
    preset = config.get_property('preset')
    monochrome = config.get_property('monochrome')
    preserve_lum = config.get_property('preserve-luminosity')
    opacity = config.get_property('opacity')
    add_mask = config.get_property('add-mask')

    # Custom channel percentage gains (-200% to +200%)
    rr = config.get_property('red-red') / 100.0
    rg = config.get_property('red-green') / 100.0
    rb = config.get_property('red-blue') / 100.0

    gr = config.get_property('green-red') / 100.0
    gg = config.get_property('green-green') / 100.0
    gb = config.get_property('green-blue') / 100.0

    br = config.get_property('blue-red') / 100.0
    bg = config.get_property('blue-green') / 100.0
    bb = config.get_property('blue-blue') / 100.0

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
                GLib.quark_from_string("gimp-channel-mixer"),
                "No valid target layer found.",
                0
            )
        )

    Gimp.context_push()
    image.undo_group_start()

    try:
        preset_info = PRESETS.get(preset, PRESETS["infrared-color"])
        label = preset_info.get("label", "Custom")
        layer_name = f"Channel Mixer ({label})"

        # Create non-destructive duplicate layer
        cm_layer = Gimp.Layer.new_from_drawable(target_layer, image)
        cm_layer.set_name(layer_name)
        cm_layer.set_opacity(max(10.0, min(100.0, float(opacity))))
        cm_layer.set_mode(Gimp.LayerMode.NORMAL)

        parent = target_layer.get_parent()
        pos = image.get_item_position(target_layer)
        image.insert_layer(cm_layer, parent, pos)

        # Resolve channel mixing gains
        if preset in PRESETS and preset != "custom":
            p_gains = preset_info["gains"]
            rr_val, rg_val, rb_val = p_gains[0:3]
            gr_val, gg_val, gb_val = p_gains[3:6]
            br_val, bg_val, bb_val = p_gains[6:9]
            pres_lum_val = bool(preset_info.get("preserve_lum", preserve_lum))
        else:
            # Custom sliders
            if monochrome:
                # In Photoshop Monochrome mode, red sliders define universal monochrome weights
                rr_val = gr_val = br_val = rr
                rg_val = gg_val = bg_val = rg
                rb_val = gb_val = bb_val = rb
            else:
                rr_val, rg_val, rb_val = rr, rg, rb
                gr_val, gg_val, gb_val = gr, gg, gb
                br_val, bg_val, bb_val = br, bg, bb
            pres_lum_val = bool(preserve_lum)

        # Apply GEGL channel-mixer filter
        filt = Gimp.DrawableFilter.new(cm_layer, "gegl:channel-mixer", "")
        filt_config = filt.get_config()

        filt_config.set_property("rr-gain", float(rr_val))
        filt_config.set_property("rg-gain", float(rg_val))
        filt_config.set_property("rb-gain", float(rb_val))

        filt_config.set_property("gr-gain", float(gr_val))
        filt_config.set_property("gg-gain", float(gg_val))
        filt_config.set_property("gb-gain", float(gb_val))

        filt_config.set_property("br-gain", float(br_val))
        filt_config.set_property("bg-gain", float(bg_val))
        filt_config.set_property("bb-gain", float(bb_val))

        filt_config.set_property("preserve-luminosity", pres_lum_val)

        cm_layer.append_filter(filt)
        cm_layer.merge_filters()

        # Attach reveal-all layer mask if requested
        if add_mask:
            mask = cm_layer.create_mask(Gimp.AddMaskType.WHITE)
            cm_layer.add_mask(mask)

        # Set newly created layer as active
        image.set_selected_layers([cm_layer])

        Gimp.displays_flush()
        image.undo_group_end()
        Gimp.context_pop()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    except Exception as exc:
        image.undo_group_end()
        Gimp.context_pop()
        msg = "Channel Mixer layer creation failed: " + str(exc)
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-channel-mixer"),
                msg,
                0
            )
        )


class ChannelMixerPlugin(Gimp.PlugIn):
    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-channel-mixer"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            channel_mixer,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        procedure.set_menu_label("Channel _Mixer...")
        procedure.set_documentation(
            "Rebalances color channels and simulates monochrome infrared looks",
            "Creates a dedicated non-destructive Channel Mixer adjustment layer duplicating the target drawable. "
            "Rebalances RGB color channels using GEGL channel-mixer to create false-color infrared photography, "
            "vintage split-toning, and precision monochrome conversions inspired by Adobe Photoshop.",
            name
        )
        procedure.set_attribution("Antigravity Ralph / PhotoGIMP", "PhotoGIMP", "2026")

        procedure.add_menu_path("<Image>/Colors")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        # Preset Choice Argument
        preset_choice = Gimp.Choice.new()
        preset_choice.add(
            "infrared-color",
            0,
            "Color Infrared (Red/Blue Swap)",
            "Swaps red and blue channels for false-color Aerochrome digital infrared look"
        )
        preset_choice.add(
            "bw-standard",
            1,
            "B&W Standard Neutral (40/40/20)",
            "Balanced black and white conversion mixing 40% red, 40% green, 20% blue"
        )
        preset_choice.add(
            "bw-landscape",
            2,
            "B&W Landscape (Green Boost 20/70/10)",
            "Landscape monochrome boosting foliage greens and darkening blue skies"
        )
        preset_choice.add(
            "bw-portrait",
            3,
            "B&W Portrait (Red Boost 60/30/10)",
            "Portrait monochrome boosting skin tones for smooth, flattering appearance"
        )
        preset_choice.add(
            "bw-high-contrast",
            4,
            "B&W High Contrast / Red Filter (100/0/0)",
            "Dramatic optical red glass filter simulation creating jet-black skies"
        )
        preset_choice.add(
            "warm-sunset",
            5,
            "Warm Golden Cast",
            "Golden amber tone boosting red channel and attenuating blue"
        )
        preset_choice.add(
            "cool-cyan",
            6,
            "Cool Cyan Cast",
            "Cool atmospheric tone boosting blue channel and attenuating red"
        )
        preset_choice.add(
            "custom",
            7,
            "Custom Mixer Weights",
            "Manually specify per-channel percentage mixing gains and monochrome mode"
        )

        procedure.add_choice_argument(
            "preset",
            "_Preset",
            "Channel mixing preset style",
            preset_choice,
            "infrared-color",
            GObject.ParamFlags.READWRITE
        )

        # Monochrome Toggle (Photoshop style)
        procedure.add_boolean_argument(
            "monochrome",
            "_Monochrome",
            "Mix all output channels identically to produce a monochrome image (Photoshop default)",
            False,
            GObject.ParamFlags.READWRITE
        )

        # Output Channel: Red
        procedure.add_double_argument(
            "red-red",
            "Red -> Red (%)",
            "Red input channel weight in Red output (-200% to +200%)",
            -200.0,
            200.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "red-green",
            "Green -> Red (%)",
            "Green input channel weight in Red output (-200% to +200%)",
            -200.0,
            200.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "red-blue",
            "Blue -> Red (%)",
            "Blue input channel weight in Red output (-200% to +200%)",
            -200.0,
            200.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # Output Channel: Green
        procedure.add_double_argument(
            "green-red",
            "Red -> Green (%)",
            "Red input channel weight in Green output (-200% to +200%)",
            -200.0,
            200.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "green-green",
            "Green -> Green (%)",
            "Green input channel weight in Green output (-200% to +200%)",
            -200.0,
            200.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "green-blue",
            "Blue -> Green (%)",
            "Blue input channel weight in Green output (-200% to +200%)",
            -200.0,
            200.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # Output Channel: Blue
        procedure.add_double_argument(
            "blue-red",
            "Red -> Blue (%)",
            "Red input channel weight in Blue output (-200% to +200%)",
            -200.0,
            200.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "blue-green",
            "Green -> Blue (%)",
            "Green input channel weight in Blue output (-200% to +200%)",
            -200.0,
            200.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "blue-blue",
            "Blue -> Blue (%)",
            "Blue input channel weight in Blue output (-200% to +200%)",
            -200.0,
            200.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # Preserve Luminosity Toggle
        procedure.add_boolean_argument(
            "preserve-luminosity",
            "_Preserve Luminosity",
            "Preserve overall image brightness when adjusting channel balances",
            False,
            GObject.ParamFlags.READWRITE
        )

        # Layer Opacity Slider (10% to 100%, default 100%)
        procedure.add_double_argument(
            "opacity",
            "Layer _Opacity (%)",
            "Overall opacity of the Channel Mixer adjustment layer (10% to 100%)",
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


Gimp.main(ChannelMixerPlugin.__gtype__, sys.argv)
