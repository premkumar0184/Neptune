#!/usr/bin/env python3
"""
PhotoGIMP Non-Destructive Woodcut & Linocut Printmaking Helper Plugin for GIMP 3.x

Creates a dedicated non-destructive Woodcut Print adjustment layer duplicating
the active drawable. Simplifies fine photographic tones into carved relief gouges
via GEGL `gegl:snn-mean`, reduces tonal range to high-contrast carved block levels
via GEGL `gegl:mono-mixer` and `gegl:levels`, and maps authentic relief printing ink
and handmade paper tones via GEGL `gegl:gradient-map` across curated printmaking
traditions (Japanese Ukiyo-e, Modern Linocut, Archival Engraving, Vermilion Seal).
Inspired by Adobe Photoshop's Woodcut / Cutout / Stamp filters and quick actions.

Photoshop Equivalence:
- Topics.txt line 665: Woodcut print filter.
- photoshop_docs.md Section 422 (line 12129-12132):
  "Artistic: Cutout, Woodcut, Stamp, relief media effects"
  "Sketch: Bas Relief, Chalk & Charcoal, Stamp, Reticulation"
- Quick Actions: Artistic relief block print and linocut study creation.

Key Advantages over stock destructive editing:
1. 100% Non-Destructive: Duplicates the active drawable into an isolated adjustment layer.
2. Authentic Gouge Contour Smoothing: Uses GEGL Symmetric Nearest Neighbor Mean filter
   (`gegl:snn-mean`) to group fine photographic details into organic carved gouge blocks
   while preserving sharp silhouette relief edges.
3. Carved Relief Tonal Reduction: Converts tonal values into monochrome block relief
   with adjustable carve depth and tonal separation (`gegl:mono-mixer` + `gegl:levels`).
4. Dual Ink & Paper Tonal Mapping: Powered by GEGL `gegl:gradient-map`, accurately
   mapping dark carved relief to rich oil/water inks and highlight gouges to textured paper.
5. Curated Fine-Art Printmaking Presets:
   - Classic Japanese Woodcut: Traditional Sumi black ink relief on warm handmade Washi paper (Normal, 100%).
   - Modern Graphic Linocut: High-contrast carved relief with deep black oil ink on crisp white paper (Normal, 100%).
   - Ukiyo-e Indigo Print: Prussian blue / Aizuri-e woodblock print on aged rice paper (Normal, 100%).
   - Vermilion Seal Print: Cinnabar red Asian seal carving print on warm parchment (Normal, 100%).
   - Fine Archival Engraving: Delicate wood engraving with detailed gouges and archival ink (Multiply, 90%).
   - Custom Printmaking: Full manual control over gouge smoothing radius, carve depth, ink, paper, opacity, and blend modes.
6. Versatile Compositing Blend Modes:
   - Normal: Standalone relief print artwork on paper.
   - Multiply: Woodblock ink multiplies cleanly over the underlying photograph or artwork.
   - Soft Light: Artistic relief glaze and structure enhancement.
7. Editable Layer Masks:
   - Reveal All: White mask applied immediately.
   - Conceal All: Black mask allowing artists to selectively brush block prints onto portrait subjects.
   - Active Selection: Automatically masks to active subject or background selection.
8. Target Layer Invariance: Source image pixels underneath remain 100% untouched (0.000000 diff).
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
    "classic-japanese": {
        "label": "Classic Japanese Woodcut",
        "desc": "Traditional Sumi black ink relief on warm handmade Washi paper",
        "radius": 3.0,
        "pairs": 2,
        "in_low": 0.25,
        "in_high": 0.75,
        "ink": (0.06, 0.06, 0.06),
        "mid": (0.48, 0.46, 0.42),
        "paper": (0.96, 0.94, 0.89),
        "blend": "normal",
        "opacity": 100.0,
    },
    "modern-linocut": {
        "label": "Modern Graphic Linocut",
        "desc": "High-contrast carved relief with deep black ink on crisp white paper",
        "radius": 4.0,
        "pairs": 2,
        "in_low": 0.42,
        "in_high": 0.58,
        "ink": (0.02, 0.02, 0.02),
        "mid": (0.40, 0.40, 0.40),
        "paper": (0.98, 0.98, 0.98),
        "blend": "normal",
        "opacity": 100.0,
    },
    "ukiyo-e-indigo": {
        "label": "Ukiyo-e Indigo Print",
        "desc": "Prussian blue woodblock print on aged rice paper (Aizuri-e style)",
        "radius": 2.5,
        "pairs": 2,
        "in_low": 0.20,
        "in_high": 0.80,
        "ink": (0.05, 0.12, 0.32),
        "mid": (0.28, 0.45, 0.58),
        "paper": (0.94, 0.92, 0.86),
        "blend": "normal",
        "opacity": 100.0,
    },
    "vermilion-seal": {
        "label": "Vermilion Seal Print",
        "desc": "Cinnabar red seal carving print on warm parchment",
        "radius": 3.0,
        "pairs": 2,
        "in_low": 0.30,
        "in_high": 0.70,
        "ink": (0.78, 0.14, 0.10),
        "mid": (0.85, 0.45, 0.35),
        "paper": (0.97, 0.95, 0.91),
        "blend": "normal",
        "opacity": 100.0,
    },
    "fine-engraving": {
        "label": "Fine Archival Engraving",
        "desc": "Delicate wood engraving with fine gouges and archival ink",
        "radius": 1.5,
        "pairs": 2,
        "in_low": 0.15,
        "in_high": 0.85,
        "ink": (0.04, 0.04, 0.04),
        "mid": (0.50, 0.50, 0.50),
        "paper": (0.97, 0.97, 0.95),
        "blend": "multiply",
        "opacity": 90.0,
    },
    "custom": {
        "label": "Custom Printmaking",
        "desc": "Full manual control over gouge smoothing, carve depth, ink, paper, and blend modes",
        "radius": 3.0,
        "pairs": 2,
        "in_low": 0.25,
        "in_high": 0.75,
        "ink": (0.06, 0.06, 0.06),
        "mid": (0.50, 0.50, 0.50),
        "paper": (0.96, 0.95, 0.93),
        "blend": "normal",
        "opacity": 100.0,
    },
}

BLEND_MODES = {
    "normal": Gimp.LayerMode.NORMAL,
    "multiply": Gimp.LayerMode.MULTIPLY,
    "soft-light": Gimp.LayerMode.SOFTLIGHT,
}


def woodcut_filter(procedure, run_mode, image, drawables, config, data):
    """Execution function for python-fu-woodcut-filter."""
    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-woodcut-filter')

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
                GLib.quark_from_string("gimp-woodcut-filter"),
                "No target drawable found to apply woodcut filter.",
                0
            )
        )

    # Read configuration parameters
    preset_key = config.get_property("preset") or "classic-japanese"
    if preset_key not in PRESETS:
        preset_key = "classic-japanese"
    preset_cfg = PRESETS[preset_key]

    if preset_key == "custom":
        radius = config.get_property("gouge-smoothing")
        carve_depth = config.get_property("carve-depth")
        # Map carve_depth (0.1 to 1.0) into in_low and in_high
        half_span = max(0.05, (1.0 - carve_depth * 0.8) * 0.5)
        in_low = max(0.0, 0.5 - half_span)
        in_high = min(1.0, 0.5 + half_span)

        ink_val = config.get_property("ink-shade")
        paper_val = config.get_property("paper-tone")
        ink_col = (ink_val, ink_val, ink_val)
        paper_col = (paper_val, paper_val, paper_val)
        mid_val = (ink_val + paper_val) * 0.5
        mid_col = (mid_val, mid_val, mid_val)

        blend_name = config.get_property("blend-mode") or "normal"
        opacity = config.get_property("opacity")
    else:
        radius = preset_cfg["radius"]
        in_low = preset_cfg["in_low"]
        in_high = preset_cfg["in_high"]
        ink_col = preset_cfg["ink"]
        mid_col = preset_cfg["mid"]
        paper_col = preset_cfg["paper"]
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
        layer_name = f"Woodcut Print ({preset_cfg['label']})"
        wc_layer = Gimp.Layer.new_from_drawable(target_drawable, image)
        wc_layer.set_name(layer_name)
        wc_layer.set_mode(layer_mode)
        wc_layer.set_opacity(float(opacity))

        # Insert directly above active drawable
        parent = target_drawable.get_parent()
        pos = image.get_item_position(target_drawable)
        image.insert_layer(wc_layer, parent, pos)

        # 2. Gouge contour smoothing (gegl:snn-mean)
        filt_snn = Gimp.DrawableFilter.new(wc_layer, "gegl:snn-mean", "")
        c_snn = filt_snn.get_config()
        c_snn.set_property("radius", int(round(radius)))
        c_snn.set_property("pairs", 2)
        wc_layer.append_filter(filt_snn)
        wc_layer.merge_filters()

        # 3. Monochrome tonal conversion (gegl:mono-mixer)
        filt_mono = Gimp.DrawableFilter.new(wc_layer, "gegl:mono-mixer", "")
        c_mono = filt_mono.get_config()
        c_mono.set_property("red", 0.30)
        c_mono.set_property("green", 0.59)
        c_mono.set_property("blue", 0.11)
        c_mono.set_property("preserve-luminosity", True)
        wc_layer.append_filter(filt_mono)
        wc_layer.merge_filters()

        # 4. Carved relief contrast / depth (gegl:levels)
        filt_levels = Gimp.DrawableFilter.new(wc_layer, "gegl:levels", "")
        c_levels = filt_levels.get_config()
        c_levels.set_property("in-low", float(in_low))
        c_levels.set_property("in-high", float(in_high))
        c_levels.set_property("out-low", 0.0)
        c_levels.set_property("out-high", 1.0)
        wc_layer.append_filter(filt_levels)
        wc_layer.merge_filters()

        # 5. Ink & Paper gradient mapping (gegl:gradient-map)
        # stop1=0.0 (dark relief / carved block) -> Printing ink
        # stop2=0.5 (midtone relief wash) -> Midtone ink/paper wash
        # stop3=1.0 (highlight gouges / carved depressions) -> Handmade paper
        gmap = Gimp.DrawableFilter.new(wc_layer, "gegl:gradient-map", "")
        c_gmap = gmap.get_config()
        c_gmap.set_property("stop1", 0.0)
        c_gmap.set_property("color1", Gegl.Color.new(f"rgb({ink_col[0]:.4f},{ink_col[1]:.4f},{ink_col[2]:.4f})"))
        c_gmap.set_property("stop2", 0.5)
        c_gmap.set_property("color2", Gegl.Color.new(f"rgb({mid_col[0]:.4f},{mid_col[1]:.4f},{mid_col[2]:.4f})"))
        c_gmap.set_property("stop3", 1.0)
        c_gmap.set_property("color3", Gegl.Color.new(f"rgb({paper_col[0]:.4f},{paper_col[1]:.4f},{paper_col[2]:.4f})"))
        wc_layer.append_filter(gmap)
        wc_layer.merge_filters()

        # 6. Attach editable layer mask
        if mask_type == "selection":
            if saved_sel_channel is not None:
                image.select_item(Gimp.ChannelOps.REPLACE, saved_sel_channel)
                mask = wc_layer.create_mask(Gimp.AddMaskType.SELECTION)
                wc_layer.add_mask(mask)
            else:
                mask = wc_layer.create_mask(Gimp.AddMaskType.WHITE)
                wc_layer.add_mask(mask)
        elif mask_type == "conceal-all":
            mask = wc_layer.create_mask(Gimp.AddMaskType.BLACK)
            wc_layer.add_mask(mask)
        else:  # "reveal-all"
            mask = wc_layer.create_mask(Gimp.AddMaskType.WHITE)
            wc_layer.add_mask(mask)

        # Restore selection state cleanly if we saved it
        if saved_sel_channel is not None:
            image.select_item(Gimp.ChannelOps.REPLACE, saved_sel_channel)
            image.remove_channel(saved_sel_channel)

        image.set_selected_layers([wc_layer])
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
                GLib.quark_from_string("gimp-woodcut-filter"),
                f"Failed to create woodcut print layer: {str(e)}",
                0
            )
        )
    finally:
        image.undo_group_end()
        Gimp.context_pop()


class WoodcutFilterPlugin(Gimp.PlugIn):
    """GIMP 3.0 Woodcut & Linocut Printmaking Plug-in implementation."""

    def do_query_procedures(self):
        return ['python-fu-woodcut-filter']

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            woodcut_filter,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        procedure.set_menu_label("Woodcut _Print...")
        procedure.set_documentation(
            "Non-destructive fine-art woodcut and linocut printmaking relief effect",
            "Creates a dedicated non-destructive Woodcut Print adjustment layer duplicating the active drawable. "
            "Renders expressive carved relief gouges, authentic printing inks (Sumi, Indigo, Vermilion, Linocut), "
            "and handmade textured paper tones inspired by Adobe Photoshop's Woodcut / Cutout / Stamp filters.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP Project", "2026")

        procedure.add_menu_path("<Image>/Filters/Artistic")
        procedure.add_menu_path("<Image>/Filters/Sketch")
        procedure.add_menu_path("<Image>/Layer")

        # Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add(
            "classic-japanese",
            0,
            "Classic Japanese Woodcut",
            "Traditional Sumi black ink relief on warm handmade Washi paper"
        )
        preset_choice.add(
            "modern-linocut",
            1,
            "Modern Graphic Linocut",
            "High-contrast carved relief with deep black ink on crisp white paper"
        )
        preset_choice.add(
            "ukiyo-e-indigo",
            2,
            "Ukiyo-e Indigo Print",
            "Prussian blue woodblock print on aged rice paper (Aizuri-e style)"
        )
        preset_choice.add(
            "vermilion-seal",
            3,
            "Vermilion Seal Print",
            "Cinnabar red seal carving print on warm parchment"
        )
        preset_choice.add(
            "fine-engraving",
            4,
            "Fine Archival Engraving",
            "Delicate wood engraving with fine gouges and archival ink"
        )
        preset_choice.add(
            "custom",
            5,
            "Custom Printmaking",
            "Full manual control over gouge smoothing, carve depth, ink, paper, and blend modes"
        )

        procedure.add_choice_argument(
            "preset",
            "Printmaking Preset",
            "Woodcut print preset tuning (classic-japanese, modern-linocut, ukiyo-e-indigo, vermilion-seal, fine-engraving, custom)",
            preset_choice,
            "classic-japanese",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "gouge-smoothing",
            "Gouge Smoothing Radius (px)",
            "Relief contour smoothing and woodblock gouge width (1.0 to 10.0px)",
            1.0,
            10.0,
            3.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "carve-depth",
            "Carve Depth & Contrast",
            "Relief carve contrast and tonal separation threshold (0.1 to 1.0)",
            0.1,
            1.0,
            0.5,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "ink-shade",
            "Relief Ink Darkness",
            "Luminance of darkest printing ink (0.0 to 0.5)",
            0.0,
            0.5,
            0.06,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "paper-tone",
            "Paper Highlight Tone",
            "Luminance of background printing paper (0.5 to 1.0)",
            0.5,
            1.0,
            0.96,
            GObject.ParamFlags.READWRITE
        )

        # Blend Mode Choice
        blend_choice = Gimp.Choice.new()
        blend_choice.add(
            "normal",
            0,
            "Normal (Opaque Print Artwork)",
            "Standalone woodcut relief artwork on paper"
        )
        blend_choice.add(
            "multiply",
            1,
            "Multiply (Print Overlay)",
            "Woodblock ink multiplies over underlying photograph"
        )
        blend_choice.add(
            "soft-light",
            2,
            "Soft Light (Tonal Relief Glaze)",
            "Artistic relief glaze enhancing tonal contrast"
        )

        procedure.add_choice_argument(
            "blend-mode",
            "Layer Blend Mode",
            "Compositing mode of the woodcut layer (normal, multiply, soft-light)",
            blend_choice,
            "normal",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "opacity",
            "Layer Opacity (%)",
            "Overall opacity of the woodcut print adjustment layer (10% to 100%)",
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
            "Whole image printed; brush with black to hide"
        )
        mask_choice.add(
            "conceal-all",
            1,
            "Conceal All (Black Mask)",
            "Print hidden initially; brush with white to reveal selectively"
        )
        mask_choice.add(
            "selection",
            2,
            "Active Selection Mask",
            "Confines woodcut print strictly to active selection"
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


Gimp.main(WoodcutFilterPlugin.__gtype__, sys.argv)
