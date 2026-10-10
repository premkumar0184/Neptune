#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Gradient Fill Layer & Multi-Style Gradient Helper Plugin
==================================================================================
Photoshop Reference:
- Topics.txt:
  - Line 101: Create fill layers
  - Line 342: Apply a gradient fill
  - Line 343: Edit a gradient
- photoshop_docs.md:
  - Section 336 lines 9880-9905: apply-gradient-fill.html
    "Apply a gradient fill in photoeditor to blend colors naturally and add depth
     to your artwork. The photoeditor workspace displays the Gradient Fill layer
     applied to an image, with gradient options visible in the options bar...
     Select a gradient type: Linear, Radial, Angle, Reflected, and Diamond...
     Select Dither to smooth the gradient and reduce banding, and Reverse to flip
     the gradient colors... Gradient Fill layer..."
  - Section 337 lines 9909-9932: edit-a-gradient.html
    "Learn how to customize gradient colors, transitions, and transparency using
     on-canvas controls and the Properties panel in professional photoeditor."
  - Section 338 lines 9942-9944:
    "For more information about working non-destructively with adjustment layers,
     see Adjustment and fill layers."

Key Architectural Features:
1. Photoshop-Standard Gradient Fill Layer (`python-fu-gradient-fill`):
   - Fulfills Photoshop's Layer > New Fill Layer > Gradient... architecture:
     creates a dedicated full-canvas gradient layer above the active layer and
     automatically converts any active selection into an attached editable layer mask,
     leaving underlying artwork 100% untouched (diff == 0.000000).
   - Also supports Selection-Only fill (gradient confined to selection on new layer)
     and In-Place rendering with Preserve Transparency option.
2. 5 Photoshop Gradient Styles:
   - Linear: Classic directional gradient transition.
   - Radial: Concentric circular falloff from center.
   - Angle: Conical rotational sweep around center.
   - Reflected: Bilateral symmetric linear reflection radiating from center line.
   - Diamond: Geometric diamond / square falloff from center.
3. Geometric Controls:
   - Angle: Rotation in degrees (-180.0 to +180.0, default 90.0 vertical).
   - Scale: Distance expansion percentage (10.0 to 200.0, default 100.0).
   - Reverse: Flip gradient color endpoints.
   - Dither: Anti-banding dithering toggle.
4. Rich Photographic Color Presets:
   - Foreground to Background (RGB).
   - Foreground to Transparent.
   - Black to White (#000000 -> #ffffff).
   - Vintage Warm Sepia (#2b1d0c -> #f6e5c5).
   - Sunset Horizon (#c0392b -> #f39c12).
   - Cyberpunk Neon (#ff007f -> #00f0ff).
   - Metallic Silver (#2c3e50 -> #ecf0f1).
   - Custom Start & End RGB sliders.
5. Professional Blend Modes & Opacity:
   - Normal, Multiply, Screen, Overlay, Soft Light, HSL Color.
   - Opacity slider (0.0 to 100.0%).
6. Layer Mask Options:
   - Auto (Selection mask if selected, else White mask), None, Reveal-All (white),
     Conceal-All (black), Active Selection.
7. Preserve Transparency:
   - Locks alpha channel during in-place fills to preserve transparent areas.
8. Single-Step Undo Protection:
   - Encapsulated within image.undo_group_start() and image.undo_group_end().
"""

import math
import sys
import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib


PROC_NAME = "python-fu-gradient-fill"

BLEND_MODES = {
    "normal": Gimp.LayerMode.NORMAL,
    "multiply": Gimp.LayerMode.MULTIPLY,
    "screen": Gimp.LayerMode.SCREEN,
    "overlay": Gimp.LayerMode.OVERLAY,
    "soft-light": Gimp.LayerMode.SOFTLIGHT,
    "color": Gimp.LayerMode.HSL_COLOR,
}

GRADIENT_STYLES = {
    "linear": Gimp.GradientType.LINEAR,
    "radial": Gimp.GradientType.RADIAL,
    "angle": Gimp.GradientType.CONICAL_ASYMMETRIC,
    "reflected": Gimp.GradientType.BILINEAR,
    "diamond": Gimp.GradientType.SQUARE,
}


class GradientFillPlugin(Gimp.PlugIn):
    def do_query_procedures(self):
        return [PROC_NAME]

    def do_set_i18n(self, procname):
        return False

    def do_create_procedure(self, name):
        if name != PROC_NAME:
            return None

        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            self.run_gradient_fill,
            None
        )
        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )
        procedure.set_menu_label("Gradient Fill Layer...")
        procedure.add_menu_path("<Image>/Layer/New Fill Layer")
        procedure.add_menu_path("<Image>/Edit")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        procedure.set_documentation(
            "Gradient Fill Layer (Non-Destructive)",
            "Creates a Photoshop-style gradient fill layer or renders multi-style gradient "
            "(Linear, Radial, Angle, Reflected, Diamond) with angle, scale, presets, blend modes, and mask.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Gradient Style
        style_choice = Gimp.Choice.new()
        style_choice.add("linear", 0, "Linear", "Directional linear gradient transition")
        style_choice.add("radial", 1, "Radial", "Concentric circular falloff from center")
        style_choice.add("angle", 2, "Angle", "Conical rotational sweep around center")
        style_choice.add("reflected", 3, "Reflected", "Symmetric bilateral linear reflection")
        style_choice.add("diamond", 4, "Diamond", "Square / diamond geometric gradient")

        procedure.add_choice_argument(
            "style",
            "Gradient Style",
            "Photoshop gradient geometry (linear, radial, angle, reflected, diamond)",
            style_choice,
            "linear",
            GObject.ParamFlags.READWRITE
        )

        # 2. Angle (degrees)
        procedure.add_double_argument(
            "angle",
            "Angle (°)",
            "Gradient direction angle in degrees (-180.0 to 180.0, default 90.0)",
            -180.0,
            180.0,
            90.0,
            GObject.ParamFlags.READWRITE
        )

        # 3. Scale (%)
        procedure.add_double_argument(
            "scale",
            "Scale (%)",
            "Gradient transition span scale percentage (10.0 to 200.0, default 100.0)",
            10.0,
            200.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # 4. Reverse
        procedure.add_boolean_argument(
            "reverse",
            "Reverse",
            "Reverse gradient color orientation",
            False,
            GObject.ParamFlags.READWRITE
        )

        # 5. Dither
        procedure.add_boolean_argument(
            "dither",
            "Dither",
            "Apply dithering to eliminate banding artifacts",
            True,
            GObject.ParamFlags.READWRITE
        )

        # 6. Color Preset
        preset_choice = Gimp.Choice.new()
        preset_choice.add("black-white", 0, "Black to White", "Monochrome neutral black to white")
        preset_choice.add("fg-to-bg", 1, "Foreground to Background", "Toolbox foreground to background")
        preset_choice.add("fg-to-transparent", 2, "Foreground to Transparent", "Toolbox foreground fade to transparent")
        preset_choice.add("vintage-warm", 3, "Vintage Warm", "Deep sepia (#2b1d0c) to cream gold (#f6e5c5)")
        preset_choice.add("sunset-horizon", 4, "Sunset Horizon", "Crimson red (#c0392b) to golden yellow (#f39c12)")
        preset_choice.add("cyberpunk-neon", 5, "Cyberpunk Neon", "Electric magenta (#ff007f) to cyan (#00f0ff)")
        preset_choice.add("metallic-silver", 6, "Metallic Silver", "Charcoal (#2c3e50) to silver (#ecf0f1)")
        preset_choice.add("custom", 7, "Custom Colors", "Use custom start and end RGB sliders")

        procedure.add_choice_argument(
            "preset",
            "Color Preset",
            "Curated gradient color harmony or custom colors",
            preset_choice,
            "black-white",
            GObject.ParamFlags.READWRITE
        )

        # 7-12. Custom RGB Sliders
        procedure.add_double_argument("start-r", "Start Red", "Start color Red (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("start-g", "Start Green", "Start color Green (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("start-b", "Start Blue", "Start color Blue (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("end-r", "End Red", "End color Red (0.0 to 1.0)", 0.0, 1.0, 1.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("end-g", "End Green", "End color Green (0.0 to 1.0)", 0.0, 1.0, 1.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("end-b", "End Blue", "End color Blue (0.0 to 1.0)", 0.0, 1.0, 1.0, GObject.ParamFlags.READWRITE)

        # 13. Fill Scope
        scope_choice = Gimp.Choice.new()
        scope_choice.add("new-fill-layer", 0, "Gradient Fill Layer", "Non-destructive full canvas layer with selection layer mask")
        scope_choice.add("selection-only", 1, "Selection Only (New Layer)", "New layer containing gradient confined to selection")
        scope_choice.add("in-place", 2, "In-Place (Active Layer)", "Render gradient directly on active layer")

        procedure.add_choice_argument(
            "fill-scope",
            "Fill Scope",
            "Destination mode for gradient (new-fill-layer, selection-only, in-place)",
            scope_choice,
            "new-fill-layer",
            GObject.ParamFlags.READWRITE
        )

        # 14. Blend Mode
        mode_choice = Gimp.Choice.new()
        mode_choice.add("normal", 0, "Normal", "Standard opaque gradient")
        mode_choice.add("multiply", 1, "Multiply", "Darkening gradient overlay")
        mode_choice.add("screen", 2, "Screen", "Lightening radiant gradient")
        mode_choice.add("overlay", 3, "Overlay", "High-contrast dynamic tone")
        mode_choice.add("soft-light", 4, "Soft Light", "Subtle tonal tint")
        mode_choice.add("color", 5, "Color (HSL)", "Colorize hue and saturation while keeping luminance")

        procedure.add_choice_argument(
            "blend-mode",
            "Blend Mode",
            "Photoshop-standard blend mode for gradient layer",
            mode_choice,
            "normal",
            GObject.ParamFlags.READWRITE
        )

        # 15. Opacity
        procedure.add_double_argument(
            "opacity",
            "Opacity (%)",
            "Gradient layer opacity percentage (0.0 to 100.0, default 100.0)",
            0.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # 16. Layer Mask
        mask_choice = Gimp.Choice.new()
        mask_choice.add("auto", 0, "Auto (Selection or White)", "Attach selection mask if active selection, otherwise white mask")
        mask_choice.add("none", 1, "None", "No mask attached")
        mask_choice.add("reveal-all", 2, "Reveal-All (White Mask)", "Fully visible editable layer mask")
        mask_choice.add("conceal-all", 3, "Conceal-All (Black Mask)", "Fully hidden mask for brush painting")
        mask_choice.add("selection", 4, "Active Selection Mask", "Mask initialized strictly from current selection")

        procedure.add_choice_argument(
            "mask-type",
            "Layer Mask Attachment",
            "Mask attached to gradient layer (auto, none, reveal-all, conceal-all, selection)",
            mask_choice,
            "auto",
            GObject.ParamFlags.READWRITE
        )

        # 17. Preserve Transparency
        procedure.add_boolean_argument(
            "preserve-transparency",
            "Preserve Transparency",
            "When rendering in-place, modify only non-transparent pixels",
            False,
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run_gradient_fill(self, procedure, run_mode, image, drawables, config, data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-gradient-fill"), "No valid image provided.", 0)
            )

        selected = image.get_selected_layers()
        active_layer = selected[0] if selected else (drawables[0] if drawables else None)
        if active_layer is None:
            layers = image.get_layers()
            if layers:
                active_layer = layers[0]
        if active_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-gradient-fill"), "No active layer found.", 0)
            )

        style = config.get_property("style")
        angle_deg = config.get_property("angle")
        scale_pct = config.get_property("scale")
        reverse = config.get_property("reverse")
        dither = config.get_property("dither")
        preset = config.get_property("preset")
        start_r = config.get_property("start-r")
        start_g = config.get_property("start-g")
        start_b = config.get_property("start-b")
        end_r = config.get_property("end-r")
        end_g = config.get_property("end-g")
        end_b = config.get_property("end-b")
        fill_scope = config.get_property("fill-scope")
        blend_name = config.get_property("blend-mode")
        opacity = config.get_property("opacity")
        mask_type = config.get_property("mask-type")
        preserve_trans = config.get_property("preserve-transparency")

        blend_mode = BLEND_MODES.get(blend_name, Gimp.LayerMode.NORMAL)
        gtype = GRADIENT_STYLES.get(style, Gimp.GradientType.LINEAR)

        W = float(image.get_width())
        H = float(image.get_height())
        cx = W * 0.5
        cy = H * 0.5
        D = 0.5 * max(W, H) * (max(10.0, min(200.0, scale_pct)) / 100.0)

        rad = angle_deg * (math.pi / 180.0)
        dx = D * math.cos(rad)
        dy = -D * math.sin(rad)

        if style == "linear":
            x1 = cx - dx
            y1 = cy - dy
            x2 = cx + dx
            y2 = cy + dy
        else:
            x1 = cx
            y1 = cy
            x2 = cx + dx
            y2 = cy + dy

        image.undo_group_start()
        Gimp.context_push()
        try:
            # Configure gradient preset and colors
            if preset == "fg-to-transparent":
                Gimp.context_set_gradient_fg_transparent()
            elif preset == "fg-to-bg":
                Gimp.context_set_gradient_fg_bg_rgb()
            elif preset == "vintage-warm":
                Gimp.context_set_gradient_fg_bg_rgb()
                Gimp.context_set_foreground(Gegl.Color.new("rgb(0.169, 0.114, 0.047)"))
                Gimp.context_set_background(Gegl.Color.new("rgb(0.965, 0.898, 0.773)"))
            elif preset == "sunset-horizon":
                Gimp.context_set_gradient_fg_bg_rgb()
                Gimp.context_set_foreground(Gegl.Color.new("rgb(0.753, 0.224, 0.169)"))
                Gimp.context_set_background(Gegl.Color.new("rgb(0.953, 0.612, 0.071)"))
            elif preset == "cyberpunk-neon":
                Gimp.context_set_gradient_fg_bg_rgb()
                Gimp.context_set_foreground(Gegl.Color.new("rgb(1.000, 0.000, 0.498)"))
                Gimp.context_set_background(Gegl.Color.new("rgb(0.000, 0.941, 1.000)"))
            elif preset == "metallic-silver":
                Gimp.context_set_gradient_fg_bg_rgb()
                Gimp.context_set_foreground(Gegl.Color.new("rgb(0.173, 0.243, 0.314)"))
                Gimp.context_set_background(Gegl.Color.new("rgb(0.925, 0.941, 0.945)"))
            elif preset == "custom":
                Gimp.context_set_gradient_fg_bg_rgb()
                Gimp.context_set_foreground(Gegl.Color.new(f"rgb({start_r:.4f}, {start_g:.4f}, {start_b:.4f})"))
                Gimp.context_set_background(Gegl.Color.new(f"rgb({end_r:.4f}, {end_g:.4f}, {end_b:.4f})"))
            else:  # black-white
                Gimp.context_set_gradient_fg_bg_rgb()
                Gimp.context_set_foreground(Gegl.Color.new("rgb(0.0, 0.0, 0.0)"))
                Gimp.context_set_background(Gegl.Color.new("rgb(1.0, 1.0, 1.0)"))

            Gimp.context_set_gradient_reverse(reverse)

            pdb = Gimp.get_pdb()
            grad_proc = pdb.lookup_procedure("gimp-drawable-edit-gradient-fill")
            if grad_proc is None:
                raise RuntimeError("gimp-drawable-edit-gradient-fill procedure not found in PDB")

            had_selection = not Gimp.Selection.is_empty(image)
            chan_orig = None
            if had_selection:
                chan_orig = Gimp.Selection.save(image)

            pos = image.get_item_position(active_layer)

            if fill_scope == "new-fill-layer":
                if had_selection:
                    Gimp.Selection.none(image)

                layer_title = f"Gradient Fill ({style.capitalize()})"
                fill_layer = Gimp.Layer.new(
                    image,
                    layer_title,
                    image.get_width(),
                    image.get_height(),
                    Gimp.ImageType.RGBA_IMAGE,
                    opacity,
                    blend_mode
                )
                image.insert_layer(fill_layer, None, pos)

                cfg_grad = grad_proc.create_config()
                cfg_grad.set_property("drawable", fill_layer)
                cfg_grad.set_property("gradient-type", gtype)
                cfg_grad.set_property("offset", 0.0)
                cfg_grad.set_property("supersample", False)
                cfg_grad.set_property("dither", dither)
                cfg_grad.set_property("x1", x1)
                cfg_grad.set_property("y1", y1)
                cfg_grad.set_property("x2", x2)
                cfg_grad.set_property("y2", y2)
                grad_proc.run(cfg_grad)

                # Attach layer mask
                if mask_type == "auto":
                    if had_selection:
                        image.select_item(Gimp.ChannelOps.REPLACE, chan_orig)
                        mask = fill_layer.create_mask(Gimp.AddMaskType.SELECTION)
                        fill_layer.add_mask(mask)
                    else:
                        mask = fill_layer.create_mask(Gimp.AddMaskType.WHITE)
                        fill_layer.add_mask(mask)
                elif mask_type == "reveal-all":
                    mask = fill_layer.create_mask(Gimp.AddMaskType.WHITE)
                    fill_layer.add_mask(mask)
                elif mask_type == "conceal-all":
                    mask = fill_layer.create_mask(Gimp.AddMaskType.BLACK)
                    fill_layer.add_mask(mask)
                elif mask_type == "selection":
                    if had_selection:
                        image.select_item(Gimp.ChannelOps.REPLACE, chan_orig)
                        mask = fill_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    else:
                        mask = fill_layer.create_mask(Gimp.AddMaskType.WHITE)
                    fill_layer.add_mask(mask)

                if had_selection:
                    image.select_item(Gimp.ChannelOps.REPLACE, chan_orig)
                    image.remove_channel(chan_orig)

                image.set_selected_layers([fill_layer])

            elif fill_scope == "selection-only":
                layer_title = f"Gradient Fill Selection ({style.capitalize()})"
                fill_layer = Gimp.Layer.new(
                    image,
                    layer_title,
                    image.get_width(),
                    image.get_height(),
                    Gimp.ImageType.RGBA_IMAGE,
                    opacity,
                    blend_mode
                )
                image.insert_layer(fill_layer, None, pos)

                cfg_grad = grad_proc.create_config()
                cfg_grad.set_property("drawable", fill_layer)
                cfg_grad.set_property("gradient-type", gtype)
                cfg_grad.set_property("offset", 0.0)
                cfg_grad.set_property("supersample", False)
                cfg_grad.set_property("dither", dither)
                cfg_grad.set_property("x1", x1)
                cfg_grad.set_property("y1", y1)
                cfg_grad.set_property("x2", x2)
                cfg_grad.set_property("y2", y2)
                grad_proc.run(cfg_grad)

                if mask_type != "none" and mask_type != "auto":
                    if mask_type == "reveal-all":
                        mask = fill_layer.create_mask(Gimp.AddMaskType.WHITE)
                        fill_layer.add_mask(mask)
                    elif mask_type == "conceal-all":
                        mask = fill_layer.create_mask(Gimp.AddMaskType.BLACK)
                        fill_layer.add_mask(mask)
                    elif mask_type == "selection":
                        if had_selection:
                            mask = fill_layer.create_mask(Gimp.AddMaskType.SELECTION)
                        else:
                            mask = fill_layer.create_mask(Gimp.AddMaskType.WHITE)
                        fill_layer.add_mask(mask)

                if chan_orig is not None:
                    image.remove_channel(chan_orig)

                image.set_selected_layers([fill_layer])

            else:  # in-place
                target_layer = active_layer
                had_lock = target_layer.get_lock_alpha()
                if preserve_trans and target_layer.has_alpha():
                    target_layer.set_lock_alpha(True)

                cfg_grad = grad_proc.create_config()
                cfg_grad.set_property("drawable", target_layer)
                cfg_grad.set_property("gradient-type", gtype)
                cfg_grad.set_property("offset", 0.0)
                cfg_grad.set_property("supersample", False)
                cfg_grad.set_property("dither", dither)
                cfg_grad.set_property("x1", x1)
                cfg_grad.set_property("y1", y1)
                cfg_grad.set_property("x2", x2)
                cfg_grad.set_property("y2", y2)
                grad_proc.run(cfg_grad)

                if preserve_trans and target_layer.has_alpha():
                    target_layer.set_lock_alpha(had_lock)

                if chan_orig is not None:
                    image.remove_channel(chan_orig)

            Gimp.displays_flush()

        except Exception as exc:
            Gimp.context_pop()
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-gradient-fill"), str(exc), 0)
            )

        Gimp.context_pop()
        image.undo_group_end()

        return procedure.new_return_values(
            Gimp.PDBStatusType.SUCCESS,
            GLib.Error()
        )


if __name__ == "__main__":
    Gimp.main(GradientFillPlugin.__gtype__, sys.argv)
