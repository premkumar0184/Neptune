#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Lens Blur & Optical Depth of Field Helper Plugin
==========================================================================
Photoshop Reference:
- Topics.txt line 461: "Create depth of field with lens blur"
- Topics.txt line 460: "Overview of adding blur to images"
- Topics.txt line 465: "Use Blur Gallery depth-of-field effects"
- photoshop_docs.md Section 425 lines 12355-12377:
  "Create depth of field with lens blur: Depth Map, Blur Focal Distance, Iris, Specular Highlights, Noise"
- photoshop_docs.md Section 421 line 12247:
  "Lens Blur: Detects edges and details for finer sharpening with fewer halos / realistic optical simulation."

Key Architectural Features:
1. Optical Aperture Defocus Simulation:
   - Uses native GEGL optical engine `gegl:lens-blur` simulating physical aperture diaphragm blades.
   - Unlike digital Gaussian blur, forms authentic circular/polygonal bokeh discs around specular highlights.
   - Iris radius (0.0 to 100.0 px).
2. Specular Highlights Blooming:
   - Controls specular highlight factor (0.0 to 1.0) and threshold (0.0 to 1.0).
   - High-luminance specular spots bloom into bright bokeh circles without blowing out midtone contrast.
3. Realistic Depth-of-Field Simulation Modes:
   - Radial Depth Gradient: Flattering portrait shallow DOF with sharp focal center and progressive radial falloff.
   - Linear Depth Gradient: Planar street/landscape depth with sharp focal plane and progressive background defocus.
   - Uniform Defocus: Full-frame optical lens blur with specular blooming.
   - Active Selection Mask: Confines blur strictly to user selection or isolated background.
4. Film Grain / Monochromatic Sensor Texture:
   - Photorealistic film grain integration (`gegl:noise-rgb` correlated/monochromatic) to prevent plastic smoothing.
5. Curated Photographic Presets:
   - Portrait Fast Prime f/1.4: Flattering central subject sharpness with smooth radial bokeh.
   - Street Shallow DOF f/2.0: Linear planar depth isolating street subjects from distracting background.
   - Macro Extreme Bokeh f/1.2: Deep optical defocus with vibrant specular bokeh discs.
   - Dreamy Specular Bokeh: Uniform optical lens blur with luminous specular blooms.
   - Uniform Defocus: Clean optical aperture defocus without specular blooming.
   - Custom Lens Blur: Full manual slider control.
6. 100% Non-Destructive Adjustment Layering:
   - Duplicates active drawable into an isolated adjustment layer.
   - Base layer source pixels underneath remain 100% mathematically untouched (diff == 0.000000).
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
    "portrait-fast-prime": {
        "label": "Portrait Fast Prime f/1.4",
        "desc": "Shallow depth of field with sharp central subject, smooth radial falloff, and soft optical bokeh",
        "radius": 25.0,
        "highlight_factor": 0.50,
        "highlight_threshold": 0.75,
        "depth_source": "radial",
        "focal_distance": 0.0,
        "invert_depth": False,
        "noise_amount": 0.0,
        "mask_mode": "depth-map",
        "opacity": 100.0,
    },
    "street-shallow-dof": {
        "label": "Street Shallow DOF f/2.0",
        "desc": "Planar linear depth-of-field isolating the street focal plane with progressive background defocus",
        "radius": 20.0,
        "highlight_factor": 0.35,
        "highlight_threshold": 0.80,
        "depth_source": "linear",
        "focal_distance": 0.35,
        "invert_depth": False,
        "noise_amount": 0.0,
        "mask_mode": "depth-map",
        "opacity": 100.0,
    },
    "macro-extreme-bokeh": {
        "label": "Macro Extreme Bokeh f/1.2",
        "desc": "Extreme optical defocus with vibrant specular highlights blooming into circular bokeh discs",
        "radius": 50.0,
        "highlight_factor": 0.80,
        "highlight_threshold": 0.70,
        "depth_source": "radial",
        "focal_distance": 0.0,
        "invert_depth": False,
        "noise_amount": 0.0,
        "mask_mode": "depth-map",
        "opacity": 100.0,
    },
    "dreamy-specular-bokeh": {
        "label": "Dreamy Specular Bokeh",
        "desc": "Uniform optical lens blur with luminous specular highlights across the entire image",
        "radius": 35.0,
        "highlight_factor": 0.90,
        "highlight_threshold": 0.60,
        "depth_source": "uniform",
        "focal_distance": 0.0,
        "invert_depth": False,
        "noise_amount": 0.0,
        "mask_mode": "reveal-all",
        "opacity": 100.0,
    },
    "uniform-defocus": {
        "label": "Uniform Defocus",
        "desc": "Clean optical aperture defocus without specular blooming",
        "radius": 15.0,
        "highlight_factor": 0.0,
        "highlight_threshold": 0.95,
        "depth_source": "uniform",
        "focal_distance": 0.0,
        "invert_depth": False,
        "noise_amount": 0.0,
        "mask_mode": "reveal-all",
        "opacity": 100.0,
    },
    "custom": {
        "label": "Custom Lens Blur",
        "desc": "Manual slider configuration",
        "radius": 25.0,
        "highlight_factor": 0.50,
        "highlight_threshold": 0.75,
        "depth_source": "radial",
        "focal_distance": 0.0,
        "invert_depth": False,
        "noise_amount": 0.0,
        "mask_mode": "depth-map",
        "opacity": 100.0,
    },
}


def render_depth_mask(mask, image, depth_source, focal_distance, invert_depth):
    """
    Renders depth falloff onto the layer mask:
    - Black (0.0): In-focus area (conceals blur layer, preserving sharp base layer).
    - White (1.0): Defocused area (reveals blur layer with optical bokeh).
    """
    W = image.get_width()
    H = image.get_height()

    if depth_source == "radial":
        # Sharp central subject with radial falloff to blurry periphery
        if not invert_depth:
            # Base black mask; white vignette reveals blur on outer periphery
            Gimp.context_set_foreground(Gegl.Color.new("black"))
            mask.edit_fill(Gimp.FillType.FOREGROUND)

            filt_vig = Gimp.DrawableFilter.new(mask, "gegl:vignette", "")
            c_vig = filt_vig.get_config()
            c_vig.set_property("shape", "circle")
            c_vig.set_property("color", Gegl.Color.new("white"))
            c_vig.set_property("x", 0.5)
            c_vig.set_property("y", 0.5)
            c_vig.set_property("radius", 0.45)
            c_vig.set_property("softness", 0.70)
            mask.merge_filter(filt_vig)
        else:
            # Base white mask; black vignette preserves center blur and sharp periphery
            Gimp.context_set_background(Gegl.Color.new("white"))
            mask.edit_fill(Gimp.FillType.BACKGROUND)

            filt_vig = Gimp.DrawableFilter.new(mask, "gegl:vignette", "")
            c_vig = filt_vig.get_config()
            c_vig.set_property("shape", "circle")
            c_vig.set_property("color", Gegl.Color.new("black"))
            c_vig.set_property("x", 0.5)
            c_vig.set_property("y", 0.5)
            c_vig.set_property("radius", 0.45)
            c_vig.set_property("softness", 0.70)
            mask.merge_filter(filt_vig)

    elif depth_source == "linear":
        # Planar depth gradient (street / landscape)
        # Background (top) is blurred (white), foreground (bottom) is sharp (black)
        pdb = Gimp.get_pdb()
        grad_proc = pdb.lookup_procedure("gimp-drawable-edit-gradient-fill")
        if grad_proc is not None:
            try:
                Gimp.context_set_gradient("FG to BG (RGB)")
            except Exception:
                pass
            if not invert_depth:
                Gimp.context_set_foreground(Gegl.Color.new("black"))
                Gimp.context_set_background(Gegl.Color.new("white"))
                y_sharp = H * max(0.4, min(1.0, 1.0 - focal_distance * 0.5))
                y_blur = 0.0
            else:
                Gimp.context_set_foreground(Gegl.Color.new("white"))
                Gimp.context_set_background(Gegl.Color.new("black"))
                y_sharp = 0.0
                y_blur = H * max(0.4, min(1.0, 1.0 - focal_distance * 0.5))

            cfg = grad_proc.create_config()
            cfg.set_property("drawable", mask)
            cfg.set_property("gradient-type", Gimp.GradientType.LINEAR)
            cfg.set_property("x1", W * 0.5)
            cfg.set_property("y1", y_sharp)
            cfg.set_property("x2", W * 0.5)
            cfg.set_property("y2", y_blur)
            grad_proc.run(cfg)
        else:
            filt_vig = Gimp.DrawableFilter.new(mask, "gegl:vignette", "")
            c_vig = filt_vig.get_config()
            c_vig.set_property("shape", "horizontal")
            c_vig.set_property("color", Gegl.Color.new("white" if not invert_depth else "black"))
            c_vig.set_property("x", 0.5)
            c_vig.set_property("y", 0.5)
            c_vig.set_property("radius", 0.5)
            c_vig.set_property("softness", 0.8)
            mask.merge_filter(filt_vig)

    elif depth_source == "uniform":
        if not invert_depth:
            Gimp.context_set_background(Gegl.Color.new("white"))
            mask.edit_fill(Gimp.FillType.BACKGROUND)
        else:
            Gimp.context_set_foreground(Gegl.Color.new("black"))
            mask.edit_fill(Gimp.FillType.FOREGROUND)


class LensBlurPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-lens-blur"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, self.run, None
        )
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
        procedure.set_menu_label("Lens Blur...")
        procedure.add_menu_path("<Image>/Filters/Blur")
        procedure.add_menu_path("<Image>/Filters/Blur Gallery")
        procedure.add_menu_path("<Image>/Filters/Retouching")
        procedure.add_menu_path("<Image>/Layer")

        procedure.set_documentation(
            "Non-Destructive Lens Blur & Optical Depth of Field Helper",
            "Simulates physical camera aperture defocus, realistic bokeh circle formation, "
            "specular highlight blooming, and realistic depth maps on an isolated adjustment layer.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add("portrait-fast-prime", 0, "Portrait Fast Prime f/1.4", "Central subject sharpness with smooth radial bokeh")
        preset_choice.add("street-shallow-dof", 1, "Street Photography Shallow DOF f/2.0", "Linear planar depth isolating street subjects")
        preset_choice.add("macro-extreme-bokeh", 2, "Macro Extreme Bokeh f/1.2", "Deep optical defocus with vibrant specular bokeh discs")
        preset_choice.add("dreamy-specular-bokeh", 3, "Dreamy Specular Bokeh", "Uniform optical lens blur with luminous specular blooms")
        preset_choice.add("uniform-defocus", 4, "Uniform Defocus", "Clean optical aperture defocus without specular blooming")
        preset_choice.add("custom", 5, "Custom Lens Blur", "Manual slider configuration")

        procedure.add_choice_argument(
            "preset",
            "Photographic Preset",
            "Curated optical Lens Blur preset (portrait-fast-prime, street-shallow-dof, macro-extreme-bokeh, dreamy-specular-bokeh, uniform-defocus, custom)",
            preset_choice,
            "portrait-fast-prime",
            GObject.ParamFlags.READWRITE
        )

        # 2. Radius
        procedure.add_double_argument(
            "radius",
            "Iris Blur Radius",
            "Aperture defocus blur radius in pixels (0.0 to 100.0, default 25.0)",
            0.0,
            100.0,
            25.0,
            GObject.ParamFlags.READWRITE
        )

        # 3. Specular Highlight Factor
        procedure.add_double_argument(
            "highlight-factor",
            "Specular Highlight Factor",
            "Specular highlight luminance boost factor (0.0 to 1.0, default 0.50)",
            0.0,
            1.0,
            0.50,
            GObject.ParamFlags.READWRITE
        )

        # 4. Specular Highlight Threshold
        procedure.add_double_argument(
            "highlight-threshold",
            "Specular Highlight Threshold",
            "Luminance threshold above which highlights bloom (0.0 to 1.0, default 0.75)",
            0.0,
            1.0,
            0.75,
            GObject.ParamFlags.READWRITE
        )

        # 5. Depth Map Source Choice
        depth_choice = Gimp.Choice.new()
        depth_choice.add("radial", 0, "Radial Depth Gradient (Portrait)", "Sharp central subject with smooth radial bokeh falloff")
        depth_choice.add("linear", 1, "Linear Depth Gradient (Street/Planar)", "Planar depth gradient for street and landscape photography")
        depth_choice.add("uniform", 2, "Uniform Defocus (Full Layer)", "Uniform defocus across the entire layer")
        depth_choice.add("selection", 3, "Active Selection", "Confine depth map to current selection")

        procedure.add_choice_argument(
            "depth-source",
            "Depth Map Source",
            "Depth map falloff simulation method (radial, linear, uniform, selection)",
            depth_choice,
            "radial",
            GObject.ParamFlags.READWRITE
        )

        # 6. Focal Distance
        procedure.add_double_argument(
            "focal-distance",
            "Blur Focal Distance",
            "Focal plane position (0.0 to 1.0, default 0.0)",
            0.0,
            1.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 7. Invert Depth
        procedure.add_boolean_argument(
            "invert-depth",
            "Invert Depth Map",
            "Inverts depth map falloff (default False)",
            False,
            GObject.ParamFlags.READWRITE
        )

        # 8. Noise Amount
        procedure.add_double_argument(
            "noise-amount",
            "Noise Amount",
            "Monochromatic film grain texture amount (0.0 to 100.0, default 0.0)",
            0.0,
            100.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 9. Mask Mode Choice
        mask_choice = Gimp.Choice.new()
        mask_choice.add("depth-map", 0, "Depth Map Mask", "Render depth-of-field gradient mask on adjustment layer")
        mask_choice.add("conceal-all", 1, "Conceal All (Black Mask)", "Attach black mask for selective brush painting")
        mask_choice.add("reveal-all", 2, "Reveal All (White Mask)", "Attach full reveal-all white mask")
        mask_choice.add("selection", 3, "Active Selection Mask", "Initialize mask strictly from current selection")

        procedure.add_choice_argument(
            "mask-mode",
            "Layer Mask Mode",
            "Adjustment layer mask configuration (depth-map, conceal-all, reveal-all, selection)",
            mask_choice,
            "depth-map",
            GObject.ParamFlags.READWRITE
        )

        # 10. Opacity
        procedure.add_double_argument(
            "opacity",
            "Layer Opacity",
            "Adjustment layer opacity percentage (0.0 to 100.0, default 100.0)",
            0.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run(self, procedure, run_mode, image, drawables, config, data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-lens-blur"),
                    "No valid image provided.",
                    0
                )
            )

        if run_mode == Gimp.RunMode.INTERACTIVE:
            Gimp.ui_init("lens-blur.py")
            dialog = Gimp.ProcedureDialog.new(procedure, config, "Lens Blur & Depth of Field")
            dialog.fill([
                "preset", "radius", "highlight-factor", "highlight-threshold",
                "depth-source", "focal-distance", "invert-depth", "noise-amount",
                "mask-mode", "opacity"
            ])
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        # Resolve target drawable safely
        target_drawable = None
        selected_layers = image.get_selected_layers()
        if len(selected_layers) > 0:
            target_drawable = selected_layers[0]
        elif drawables and len(drawables) > 0:
            d = drawables[0]
            if hasattr(d, 'is_layer_mask') and d.is_layer_mask():
                layers = image.get_layers()
                target_drawable = layers[0] if len(layers) > 0 else None
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
                    GLib.quark_from_string("gimp-lens-blur"),
                    "No target drawable found to apply Lens Blur.",
                    0
                )
            )

        preset_key = config.get_property("preset") or "portrait-fast-prime"
        if preset_key not in PRESETS:
            preset_key = "portrait-fast-prime"
        preset_cfg = PRESETS[preset_key]

        if preset_key == "custom":
            radius_val = config.get_property("radius")
            highlight_factor_val = config.get_property("highlight-factor")
            highlight_thresh_val = config.get_property("highlight-threshold")
            depth_source_val = config.get_property("depth-source") or "radial"
            focal_dist_val = config.get_property("focal-distance")
            invert_depth_val = config.get_property("invert-depth")
            noise_val = config.get_property("noise-amount")
            mask_mode_val = config.get_property("mask-mode") or "depth-map"
            opacity_val = config.get_property("opacity")
        else:
            radius_val = preset_cfg["radius"]
            highlight_factor_val = preset_cfg["highlight_factor"]
            highlight_thresh_val = preset_cfg["highlight_threshold"]
            depth_source_val = preset_cfg["depth_source"]
            focal_dist_val = preset_cfg["focal_distance"]
            invert_depth_val = preset_cfg["invert_depth"]
            noise_val = preset_cfg["noise_amount"]
            mask_mode_val = preset_cfg["mask_mode"]
            opacity_val = preset_cfg["opacity"]

            # Explicit overrides if set by caller
            req_mask_mode = config.get_property("mask-mode")
            if req_mask_mode in ["conceal-all", "reveal-all", "selection", "depth-map"]:
                mask_mode_val = req_mask_mode

            req_opacity = config.get_property("opacity")
            if req_opacity > 0.0 and req_opacity <= 100.0:
                opacity_val = req_opacity

            req_invert = config.get_property("invert-depth")
            if req_invert is not None and req_invert:
                invert_depth_val = True

            req_noise = config.get_property("noise-amount")
            if req_noise > 0.0:
                noise_val = req_noise

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
            layer_name = f"Lens Blur ({preset_cfg['label']})"
            blur_layer = Gimp.Layer.new_from_drawable(target_drawable, image)
            blur_layer.set_name(layer_name)
            blur_layer.set_mode(Gimp.LayerMode.NORMAL)
            blur_layer.set_opacity(float(opacity_val))

            parent = target_drawable.get_parent()
            pos = image.get_item_position(target_drawable)
            image.insert_layer(blur_layer, parent, pos)

            # 2. Apply optical defocus blur via gegl:lens-blur
            if radius_val > 0.0:
                filt_blur = Gimp.DrawableFilter.new(blur_layer, "gegl:lens-blur", "")
                c_blur = filt_blur.get_config()
                c_blur.set_property("radius", float(radius_val))
                c_blur.set_property("highlight-factor", min(1.0, max(0.0, float(highlight_factor_val))))
                thresh_hi = min(1.0, max(0.0, float(highlight_thresh_val)))
                c_blur.set_property("highlight-threshold-high", thresh_hi)
                c_blur.set_property("highlight-threshold-low", max(0.0, thresh_hi - 0.25))
                c_blur.set_property("clip", True)
                blur_layer.merge_filter(filt_blur)

            # 3. Apply monochromatic film grain / sensor texture if requested
            if noise_val > 0.0:
                filt_noise = Gimp.DrawableFilter.new(blur_layer, "gegl:noise-rgb", "")
                c_noise = filt_noise.get_config()
                c_noise.set_property("correlated", True)
                c_noise.set_property("independent", False)
                c_noise.set_property("gaussian", True)
                noise_norm = min(1.0, max(0.0, float(noise_val) / 100.0 * 0.30))
                c_noise.set_property("red", noise_norm)
                c_noise.set_property("green", noise_norm)
                c_noise.set_property("blue", noise_norm)
                c_noise.set_property("alpha", 0.0)
                blur_layer.merge_filter(filt_noise)

            # 4. Create and attach focal depth layer mask
            if mask_mode_val == "conceal-all":
                mask = blur_layer.create_mask(Gimp.AddMaskType.BLACK)
                blur_layer.add_mask(mask)
            elif mask_mode_val == "reveal-all":
                mask = blur_layer.create_mask(Gimp.AddMaskType.WHITE)
                blur_layer.add_mask(mask)
            elif mask_mode_val == "selection":
                if saved_sel_channel is not None:
                    image.select_item(Gimp.ChannelOps.REPLACE, saved_sel_channel)
                    mask = blur_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    blur_layer.add_mask(mask)
                    image.remove_channel(saved_sel_channel)
                    saved_sel_channel = None
                    Gimp.Selection.none(image)
                else:
                    mask = blur_layer.create_mask(Gimp.AddMaskType.WHITE)
                    blur_layer.add_mask(mask)
            else:  # "depth-map"
                mask = blur_layer.create_mask(Gimp.AddMaskType.BLACK)
                blur_layer.add_mask(mask)
                render_depth_mask(mask, image, depth_source_val, focal_dist_val, invert_depth_val)

            # Set active layer to adjustment layer
            image.set_selected_layers([blur_layer])

            image.undo_group_end()
            Gimp.context_pop()
            Gimp.displays_flush()

            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as e:
            image.undo_group_end()
            Gimp.context_pop()
            if saved_sel_channel is not None:
                try:
                    image.remove_channel(saved_sel_channel)
                except Exception:
                    pass
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-lens-blur-error"),
                    f"Lens blur execution failed: {str(e)}",
                    0
                )
            )
        finally:
            if saved_sel_channel is not None:
                try:
                    image.remove_channel(saved_sel_channel)
                except Exception:
                    pass


if __name__ == "__main__":
    Gimp.main(LensBlurPlugin.__gtype__, sys.argv)
