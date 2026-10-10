#!/usr/bin/env python3
"""
PhotoGIMP Non-Destructive JPEG Artifacts Removal & Deblocking Helper Plugin for GIMP 3.x

Creates a dedicated non-destructive JPEG Cleanup / Deblocking adjustment layer duplicating
the active drawable. Employs 2D DCT-domain deblocking (`gegl:denoise-dct`) to eliminate
8x8 block boundary discontinuities, edge-preserving Symmetric Nearest Neighbor mean filtering
(`gegl:snn-mean`) to suppress high-frequency mosquito ringing halos around high-contrast edges,
and unsharp micro-detail recovery (`gegl:unsharp-mask`) to preserve genuine subject texture.
Inspired by Adobe Photoshop's Neural Filters (JPEG Artifacts Removal) and professional photo
restoration workflows.

Photoshop Equivalence:
- Topics.txt line 673: Remove JPEG artifacts from images.
- photoshop_docs.md Section 445 & 446 (lines 13009, 13048):
  "Neural Filters in photoeditor simplify complex editing workflows... remove JPEG artifacts...
   Output: New layer masked: Duplicates the layer with a mask isolating the filter effect."
- photoshop_docs.md Section 149 & 429: Noise and compression artifact reduction.

Key Advantages over stock destructive editing:
1. 100% Non-Destructive: Duplicates the active drawable into an isolated adjustment layer.
2. 2D DCT Deblocking: Utilizes GEGL `gegl:denoise-dct` to reconstruct Discrete Cosine Transform
   quantization blocks (8x8 or 16x16) without destroying overall photographic contrast.
3. Edge-Preserving Ringing Suppression: Utilizes GEGL `gegl:snn-mean` to smooth out Gibbs
   mosquito oscillations and halo spikes while locking down contrast edges.
4. Micro-Detail Recovery: Utilizes GEGL `gegl:unsharp-mask` with a noise threshold to restore
   authentic image focus and edge definition.
5. Curated Compression Presets:
   - Subtle Web Cleanup: Gentle deblocking for lightly compressed web images (sigma 4.0, SNN 1).
   - Medium Compression Smoothing: Balanced deblocking for standard JPEG photos (sigma 8.0, SNN 2).
   - Aggressive Block Removal: Strong deblocking for heavy JPEG compression and low bitrates (sigma 16.0, SNN 3).
   - Mosquito Ringing Suppression: Ringing-focused smoothing for high-contrast edges and text (sigma 6.0, SNN 4).
   - 16x16 Macroblock Cleanup: Deblocking tailored for coarse 16x16 macroblock grids (sigma 12.0, size16x16, SNN 3).
   - Custom Sliders: Full manual control over DCT sigma, patch size, SNN radius, and detail retention.
6. Editable Layer Masks:
   - Reveal All: White mask applied immediately.
   - Conceal All: Black mask allowing artists to selectively brush deblocking over problem regions.
   - Active Selection: Automatically masks to active subject or background selection.
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
    "subtle": {
        "label": "Subtle Web Cleanup",
        "desc": "Gentle deblocking and noise reduction for light web compression",
        "sigma": 4.0,
        "patch_size": "size8x8",
        "ringing_reduction": 1,
        "detail_recovery": 20.0,
        "opacity": 100.0,
    },
    "medium": {
        "label": "Medium Compression Smoothing",
        "desc": "Balanced block reduction and ringing suppression for standard JPEG photos",
        "sigma": 8.0,
        "patch_size": "size8x8",
        "ringing_reduction": 2,
        "detail_recovery": 35.0,
        "opacity": 100.0,
    },
    "aggressive": {
        "label": "Aggressive Block Removal",
        "desc": "Strong deblocking for heavy JPEG compression and low-quality images",
        "sigma": 16.0,
        "patch_size": "size8x8",
        "ringing_reduction": 3,
        "detail_recovery": 45.0,
        "opacity": 100.0,
    },
    "ringing": {
        "label": "Mosquito Ringing Suppression",
        "desc": "Specialized edge-preserving smoothing targeting halo oscillations around text and sharp contours",
        "sigma": 6.0,
        "patch_size": "size8x8",
        "ringing_reduction": 4,
        "detail_recovery": 15.0,
        "opacity": 100.0,
    },
    "macroblock": {
        "label": "16x16 Macroblock Cleanup",
        "desc": "Deblocking tailored for coarse 16x16 video and heavily subsampled JPEG macroblocks",
        "sigma": 12.0,
        "patch_size": "size16x16",
        "ringing_reduction": 3,
        "detail_recovery": 30.0,
        "opacity": 100.0,
    },
    "custom": {
        "label": "Custom Deblocking",
        "desc": "Full manual control over DCT sigma, patch size, SNN radius, and detail retention",
        "sigma": 8.0,
        "patch_size": "size8x8",
        "ringing_reduction": 2,
        "detail_recovery": 35.0,
        "opacity": 100.0,
    },
}


def jpeg_artifact_removal(procedure, run_mode, image, drawables, config, data):
    """Execution function for python-fu-jpeg-artifact-removal."""
    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-jpeg-artifact-removal')

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
                GLib.quark_from_string("gimp-jpeg-artifact-removal"),
                "No target drawable found to apply JPEG artifacts removal.",
                0
            )
        )

    # Read configuration parameters
    preset_key = config.get_property("preset") or "medium"
    if preset_key not in PRESETS:
        preset_key = "medium"
    preset_cfg = PRESETS[preset_key]

    if preset_key == "custom":
        sigma = config.get_property("sigma")
        patch_size = config.get_property("patch-size") or "size8x8"
        ringing_reduction = config.get_property("ringing-reduction")
        detail_recovery = config.get_property("detail-recovery")
        opacity = config.get_property("opacity")
    else:
        sigma = preset_cfg["sigma"]
        patch_size = preset_cfg["patch_size"]
        ringing_reduction = preset_cfg["ringing_reduction"]
        detail_recovery = preset_cfg["detail_recovery"]
        opacity = config.get_property("opacity")
        # Allow slider override if non-default
        if opacity <= 0.0 or opacity > 100.0:
            opacity = preset_cfg["opacity"]

    mask_type = config.get_property("mask-type") or "reveal-all"

    Gimp.context_push()
    image.undo_group_start()

    saved_sel_channel = None
    try:
        # Check if there is an active selection
        has_user_selection = not Gimp.Selection.is_empty(image)
        if has_user_selection:
            saved_sel_channel = Gimp.Selection.save(image)
            # Clear selection so filters process whole layer smoothly without boundary artifacts
            Gimp.Selection.none(image)

        # 1. Duplicate active drawable into isolated adjustment layer
        layer_name = f"JPEG Cleanup ({preset_cfg['label']})"
        clean_layer = Gimp.Layer.new_from_drawable(target_drawable, image)
        clean_layer.set_name(layer_name)
        clean_layer.set_mode(Gimp.LayerMode.NORMAL)
        clean_layer.set_opacity(float(opacity))

        # Insert directly above active drawable
        parent = target_drawable.get_parent()
        pos = image.get_item_position(target_drawable)
        image.insert_layer(clean_layer, parent, pos)

        # 2. Apply 2D DCT Deblocking (gegl:denoise-dct)
        if sigma > 0.1:
            filt_dct = Gimp.DrawableFilter.new(clean_layer, "gegl:denoise-dct", "")
            cfg_dct = filt_dct.get_config()
            cfg_dct.set_property("patch-size", str(patch_size))
            cfg_dct.set_property("sigma", float(sigma))
            clean_layer.append_filter(filt_dct)
            clean_layer.merge_filters()

        # 3. Apply Edge-Preserving Ringing / Mosquito Noise Suppression (gegl:snn-mean)
        if ringing_reduction > 0:
            filt_snn = Gimp.DrawableFilter.new(clean_layer, "gegl:snn-mean", "")
            cfg_snn = filt_snn.get_config()
            cfg_snn.set_property("radius", int(ringing_reduction))
            cfg_snn.set_property("pairs", 2)
            clean_layer.append_filter(filt_snn)
            clean_layer.merge_filters()

        # 4. Apply Micro-Detail Recovery (gegl:unsharp-mask)
        if detail_recovery > 0.001:
            scale_val = (float(detail_recovery) / 100.0) * 0.6
            filt_unsharp = Gimp.DrawableFilter.new(clean_layer, "gegl:unsharp-mask", "")
            cfg_unsharp = filt_unsharp.get_config()
            cfg_unsharp.set_property("std-dev", 1.0)
            cfg_unsharp.set_property("scale", float(scale_val))
            cfg_unsharp.set_property("threshold", 0.01)
            clean_layer.append_filter(filt_unsharp)
            clean_layer.merge_filters()

        # 5. Attach editable layer mask based on mask-type choice
        if mask_type == "selection":
            if saved_sel_channel is not None:
                image.select_item(Gimp.ChannelOps.REPLACE, saved_sel_channel)
                mask = clean_layer.create_mask(Gimp.AddMaskType.SELECTION)
                clean_layer.add_mask(mask)
            else:
                mask = clean_layer.create_mask(Gimp.AddMaskType.WHITE)
                clean_layer.add_mask(mask)
        elif mask_type == "conceal-all":
            mask = clean_layer.create_mask(Gimp.AddMaskType.BLACK)
            clean_layer.add_mask(mask)
        else:  # "reveal-all"
            mask = clean_layer.create_mask(Gimp.AddMaskType.WHITE)
            clean_layer.add_mask(mask)

        # Cleanup temporary saved selection channel if created
        if saved_sel_channel is not None:
            image.select_item(Gimp.ChannelOps.REPLACE, saved_sel_channel)
            image.remove_channel(saved_sel_channel)

        # Set cleanup layer active
        image.set_selected_layers([clean_layer])
        clean_layer.set_visible(True)

        Gimp.displays_flush()

    except Exception as e:
        image.undo_group_end()
        Gimp.context_pop()
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-jpeg-artifact-removal"),
                f"JPEG artifact removal processing failed: {str(e)}",
                0
            )
        )

    image.undo_group_end()
    Gimp.context_pop()

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


class JpegArtifactRemovalPlugin(Gimp.PlugIn):
    ## GimpPlugIn virtual methods ##
    def do_set_i18n(self, procname):
        return True, 'gimp30-python', None

    def do_query_procedures(self):
        return ['python-fu-jpeg-artifact-removal']

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            jpeg_artifact_removal,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        procedure.set_menu_label("JPEG Artifacts _Removal...")
        procedure.set_documentation(
            "Non-destructive JPEG compression artifacts removal and deblocking",
            "Creates a dedicated non-destructive adjustment layer duplicating the active drawable. "
            "Eliminates 8x8 DCT grid blocking discontinuities, suppresses edge-ringing mosquito noise, "
            "and recovers fine texture inspired by Adobe Photoshop's Neural Filters (JPEG Artifacts Removal).",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP Project", "2026")

        procedure.add_menu_path("<Image>/Filters/Enhance")
        procedure.add_menu_path("<Image>/Filters/Retouching")
        procedure.add_menu_path("<Image>/Layer")

        # Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add(
            "subtle",
            0,
            "Subtle Web Cleanup",
            "Gentle deblocking and noise reduction for light web compression"
        )
        preset_choice.add(
            "medium",
            1,
            "Medium Compression Smoothing",
            "Balanced block reduction and ringing suppression for standard JPEG photos"
        )
        preset_choice.add(
            "aggressive",
            2,
            "Aggressive Block Removal",
            "Strong deblocking for heavy JPEG compression and low-quality images"
        )
        preset_choice.add(
            "ringing",
            3,
            "Mosquito Ringing Suppression",
            "Edge-preserving smoothing targeting halo oscillations around text and contours"
        )
        preset_choice.add(
            "macroblock",
            4,
            "16x16 Macroblock Cleanup",
            "Deblocking tailored for coarse 16x16 video and heavily subsampled JPEG macroblocks"
        )
        preset_choice.add(
            "custom",
            5,
            "Custom Sliders",
            "Full manual control over DCT sigma, patch size, SNN radius, and detail retention"
        )

        procedure.add_choice_argument(
            "preset",
            "Artifact Cleanup Preset",
            "Deblocking preset tuning (subtle, medium, aggressive, ringing, macroblock, custom)",
            preset_choice,
            "medium",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "sigma",
            "Deblocking Strength (Sigma)",
            "DCT noise standard deviation threshold for smoothing block discontinuities (1.0 to 50.0)",
            1.0,
            50.0,
            8.0,
            GObject.ParamFlags.READWRITE
        )

        # Patch Size Choice
        patch_choice = Gimp.Choice.new()
        patch_choice.add(
            "size8x8",
            0,
            "8x8 Standard DCT Blocks",
            "Standard JPEG Discrete Cosine Transform 8x8 block grid"
        )
        patch_choice.add(
            "size16x16",
            1,
            "16x16 Macroblocks",
            "Coarse 16x16 chroma macroblock grid"
        )

        procedure.add_choice_argument(
            "patch-size",
            "DCT Block Patch Size",
            "Patch dimension matching compression block size (size8x8 or size16x16)",
            patch_choice,
            "size8x8",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_int_argument(
            "ringing-reduction",
            "Mosquito Ringing Reduction",
            "Symmetric Nearest Neighbor radius for eliminating edge-ringing halos (0 to 10)",
            0,
            10,
            2,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "detail-recovery",
            "Detail Recovery (%)",
            "High-frequency micro-contrast restoration to preserve subject sharpness (0 to 100%)",
            0.0,
            100.0,
            35.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "opacity",
            "Layer Opacity (%)",
            "Overall opacity of the JPEG cleanup adjustment layer (10% to 100%)",
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
            "Whole image cleaned; brush with black to hide"
        )
        mask_choice.add(
            "conceal-all",
            1,
            "Conceal All (Black Mask)",
            "Cleanup hidden initially; brush with white to apply selectively"
        )
        mask_choice.add(
            "selection",
            2,
            "Active Selection Mask",
            "Confines cleanup effect strictly to the active selection"
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


Gimp.main(JpegArtifactRemovalPlugin.__gtype__, sys.argv)
