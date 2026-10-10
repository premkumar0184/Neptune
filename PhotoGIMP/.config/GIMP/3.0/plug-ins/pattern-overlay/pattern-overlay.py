#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Pattern Overlay Layer Style Helper Plugin
===================================================================
Simulates Adobe Photoshop's non-destructive Pattern Overlay layer style:
  - Photoshop Menu: Layer > Layer Style > Pattern Overlay...
  - Photoshop Menu: Filters > Light and Shadow > Pattern Overlay (Layer Style)...
  - Photoshop Docs: Section 113-115 lines 3433-3500 (Layer Style effects and options)
  - Topics.txt: Lines 107-118, 361, 432

Photoshop Pattern Overlay Architecture:
  1. Pattern Presets & Textures:
     - Checkerboard: High-contrast 2x2 alternating checker matrix.
     - Diagonal Stripes: 45-degree linear pinstripes.
     - Grid Mesh: Precision technical drafting orthogonal grid mesh.
     - Polka Dots: Circular polka dot array.
     - Halftone Dots: Vintage screen halftone dot matrix.
     - Carbon Fiber: Woven twill composite fiber texture.
     - Active Pattern: Currently active GIMP toolbox pattern resource.
  2. Geometric & Spatial Controls:
     - Scale (10.0% to 500.0%, default 100.0%): Seamless spatial frequency scaling.
     - Angle (-180.0° to 180.0%, default 0.0°): Seamless geometric pattern rotation.
     - Link with Layer (default True): Anchors pattern coordinate origin to target layer bounds.
  3. Customizable Dual-Tone Pattern Colors:
     - Color 1 (RGB): Primary pattern foreground swatch.
     - Color 2 (RGB): Secondary pattern background swatch.
  4. Strict Boundary Silhouette Clipping:
     - Overlay pixels are strictly clipped to the target layer's silhouette:
       A_overlay(x, y) = A_pattern(x, y) * A_target(x, y).
       Outside pixels are strictly alpha == 0.000000.
       Anti-aliased and semi-transparent edges in the target layer are matched exactly.
  5. Photoshop Blend Modes & Opacity:
     - Normal, Multiply, Screen, Overlay, Soft Light, Color (HSL Color), Darken, Lighten.
     - Opacity slider (0.0% to 100.0%, default 100.0%).
  6. Non-Destructive Layer Architecture:
     - Dedicated overlay layer inserted directly above the target layer in the stack.
     - Target layer artwork and underlying canvas pixels remain 100% untouched (diff == 0.000000).
     - Single-step Ctrl+Z undo protection.
"""

import math
import sys
import numpy as np
import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
from gi.repository import GLib

try:
    gi.require_version('Babl', '0.1')
    from gi.repository import Babl
except Exception:
    Babl = None


PROC_NAME = "python-fu-pattern-overlay"

BLEND_MODES = {
    "normal": Gimp.LayerMode.NORMAL,
    "multiply": Gimp.LayerMode.MULTIPLY,
    "screen": Gimp.LayerMode.SCREEN,
    "overlay": Gimp.LayerMode.OVERLAY,
    "soft-light": Gimp.LayerMode.SOFTLIGHT,
    "color": Gimp.LayerMode.HSL_COLOR,
    "darken": Gimp.LayerMode.DARKEN_ONLY,
    "lighten": Gimp.LayerMode.LIGHTEN_ONLY,
}


def build_pattern_tile(preset, c1, c2):
    """Generates a base RGBA float32 tile array of shape (H, W, 4)."""
    if preset == "checkerboard":
        h, w = 16, 16
        xs = (np.arange(w) // 8)
        ys = (np.arange(h) // 8)
        grid = ((xs[None, :] + ys[:, None]) % 2 == 0)
        return np.where(grid[:, :, None], c1, c2).astype(np.float32)

    elif preset == "diagonal-stripes":
        h, w = 16, 16
        xs = np.arange(w)
        ys = np.arange(h)
        grid = ((xs[None, :] + ys[:, None]) % 16) < 8
        return np.where(grid[:, :, None], c1, c2).astype(np.float32)

    elif preset == "grid-mesh":
        h, w = 16, 16
        xs = np.arange(w)
        ys = np.arange(h)
        grid = (xs[None, :] < 2) | (ys[:, None] < 2)
        return np.where(grid[:, :, None], c1, c2).astype(np.float32)

    elif preset == "polka-dots":
        h, w = 20, 20
        xs = np.arange(w, dtype=np.float32) - 10.0
        ys = np.arange(h, dtype=np.float32) - 10.0
        dist_sq = xs[None, :]**2 + ys[:, None]**2
        grid = (dist_sq <= 36.0)
        return np.where(grid[:, :, None], c1, c2).astype(np.float32)

    elif preset == "halftone-dots":
        h, w = 16, 16
        xs = np.arange(w, dtype=np.float32) - 8.0
        ys = np.arange(h, dtype=np.float32) - 8.0
        dist_sq = xs[None, :]**2 + ys[:, None]**2
        grid = (dist_sq <= 25.0)
        return np.where(grid[:, :, None], c1, c2).astype(np.float32)

    elif preset == "carbon-fiber":
        h, w = 8, 8
        xs = np.arange(w)
        ys = np.arange(h)
        grid = ((xs[None, :] // 2) + (ys[:, None] // 2)) % 2 == 0
        c2_shade = c2 * 0.65
        c2_shade[3] = 1.0
        return np.where(grid[:, :, None], c1, c2_shade).astype(np.float32)

    elif preset == "active-pattern":
        # Attempt to sample active GIMP pattern buffer
        try:
            pat = Gimp.context_get_pattern()
            if pat is not None and Babl is not None:
                info = pat.get_info()
                pw, ph = int(info[-3]), int(info[-2])
                if pw > 0 and ph > 0:
                    pbuf = pat.get_buffer(pw, ph, Babl.format("RGBA float"))
                    if pbuf is not None:
                        prect = Gegl.Rectangle.new(0, 0, pw, ph)
                        raw = pbuf.get(prect, 1.0, "RGBA float", Gegl.AbyssPolicy.NONE)
                        arr = np.frombuffer(raw, dtype=np.float32).reshape((ph, pw, 4)).copy()
                        return arr
        except Exception:
            pass

        # Fallback to checkerboard if active-pattern read is unavailable
        h, w = 16, 16
        xs = (np.arange(w) // 8)
        ys = (np.arange(h) // 8)
        grid = ((xs[None, :] + ys[:, None]) % 2 == 0)
        return np.where(grid[:, :, None], c1, c2).astype(np.float32)

    else:
        # Default fallback: checkerboard
        h, w = 16, 16
        xs = (np.arange(w) // 8)
        ys = (np.arange(h) // 8)
        grid = ((xs[None, :] + ys[:, None]) % 2 == 0)
        return np.where(grid[:, :, None], c1, c2).astype(np.float32)


class PatternOverlayPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return [PROC_NAME]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_pattern_overlay, None)
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        # Menu Registrations
        procedure.set_menu_label("Pattern Overlay (Layer Style)...")
        procedure.add_menu_path("<Image>/Layer/Layer Style")
        procedure.add_menu_path("<Image>/Filters/Light and Shadow")
        procedure.add_menu_path("<Image>/Filters/Retouching")

        procedure.set_documentation(
            "Pattern Overlay (Layer Style)",
            "Renders a non-destructive multi-style pattern overlay clipped strictly to the target layer's silhouette.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Pattern Preset Choice
        pattern_choice = Gimp.Choice.new()
        pattern_choice.add("checkerboard", 0, "Checkerboard", "High-contrast 2x2 alternating checker tile")
        pattern_choice.add("diagonal-stripes", 1, "Diagonal Stripes", "45-degree pinstripes pattern")
        pattern_choice.add("grid-mesh", 2, "Grid Mesh", "Technical drafting orthogonal grid mesh")
        pattern_choice.add("polka-dots", 3, "Polka Dots", "Circular polka dot array")
        pattern_choice.add("halftone-dots", 4, "Halftone Dots", "Vintage screen halftone dot matrix")
        pattern_choice.add("carbon-fiber", 5, "Carbon Fiber", "Woven twill composite fiber texture")
        pattern_choice.add("active-pattern", 6, "Active Pattern", "Use currently active GIMP pattern")

        procedure.add_choice_argument(
            "pattern",
            "Pattern",
            "Pattern texture preset or active toolbox pattern",
            pattern_choice,
            "checkerboard",
            GObject.ParamFlags.READWRITE
        )

        # 2. Scale (10.0% to 500.0%)
        procedure.add_double_argument(
            "scale",
            "Scale (%)",
            "Pattern scaling percentage (10.0 to 500.0, default 100.0)",
            10.0,
            500.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # 3. Angle (-180.0° to 180.0°)
        procedure.add_double_argument(
            "angle",
            "Angle (°)",
            "Pattern rotation angle in degrees (-180.0 to 180.0, default 0.0)",
            -180.0,
            180.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 4. Link with Layer (Align to Layer)
        procedure.add_boolean_argument(
            "link-layer",
            "Link with Layer",
            "Align pattern origin with target layer coordinates",
            True,
            GObject.ParamFlags.READWRITE
        )

        # 5. Blend Mode
        mode_choice = Gimp.Choice.new()
        mode_choice.add("normal", 0, "Normal", "Standard normal blending")
        mode_choice.add("multiply", 1, "Multiply", "Darkens by multiplying colors")
        mode_choice.add("screen", 2, "Screen", "Lightens by inverting, multiplying, inverting")
        mode_choice.add("overlay", 3, "Overlay", "Combines Multiply and Screen")
        mode_choice.add("soft-light", 4, "Soft Light", "Subtle diffused lighting")
        mode_choice.add("color", 5, "Color", "Preserves luminosity while tinting hue and chroma")
        mode_choice.add("darken", 6, "Darken", "Darken only mode")
        mode_choice.add("lighten", 7, "Lighten", "Lighten only mode")

        procedure.add_choice_argument(
            "blend-mode",
            "Blend Mode",
            "Layer blending mode for the pattern overlay",
            mode_choice,
            "normal",
            GObject.ParamFlags.READWRITE
        )

        # 6. Opacity (0.0% to 100.0%)
        procedure.add_double_argument(
            "opacity",
            "Opacity (%)",
            "Pattern overlay layer opacity (0.0 to 100.0)",
            0.0,
            100.0,
            100.0,
            GObject.ParamFlags.READWRITE
        )

        # 7-9. Color 1 (RGB)
        procedure.add_double_argument("c1-r", "Color 1 Red", "Primary pattern color red (0.0 to 1.0)", 0.0, 1.0, 1.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("c1-g", "Color 1 Green", "Primary pattern color green (0.0 to 1.0)", 0.0, 1.0, 1.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("c1-b", "Color 1 Blue", "Primary pattern color blue (0.0 to 1.0)", 0.0, 1.0, 1.0, GObject.ParamFlags.READWRITE)

        # 10-12. Color 2 (RGB)
        procedure.add_double_argument("c2-r", "Color 2 Red", "Secondary pattern color red (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("c2-g", "Color 2 Green", "Secondary pattern color green (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)
        procedure.add_double_argument("c2-b", "Color 2 Blue", "Secondary pattern color blue (0.0 to 1.0)", 0.0, 1.0, 0.0, GObject.ParamFlags.READWRITE)

        # 13. Layer Mask
        mask_choice = Gimp.Choice.new()
        mask_choice.add("auto", 0, "Auto (Selection or None)", "Convert active selection to mask if active; else none")
        mask_choice.add("none", 1, "None", "No layer mask attached")
        mask_choice.add("reveal-all", 2, "Reveal All (White)", "Attach white mask allowing brush concealment")
        mask_choice.add("conceal-all", 3, "Conceal All (Black)", "Attach black mask allowing selective brush reveal")
        mask_choice.add("selection", 4, "From Selection", "Convert active selection boundary to mask")

        procedure.add_choice_argument(
            "mask-type",
            "Layer Mask",
            "Layer mask attachment option",
            mask_choice,
            "auto",
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run_pattern_overlay(self, procedure, run_mode, image, drawables, config, data):
        # Interactive GUI dialog
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("python-fu-pattern-overlay")
            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        # Read configuration parameters
        pattern_str = config.get_property("pattern")
        scale_val = config.get_property("scale")
        angle_val = config.get_property("angle")
        link_layer = config.get_property("link-layer")
        bmode_str = config.get_property("blend-mode")
        opacity_val = config.get_property("opacity")
        c1_r = config.get_property("c1-r")
        c1_g = config.get_property("c1-g")
        c1_b = config.get_property("c1-b")
        c2_r = config.get_property("c2-r")
        c2_g = config.get_property("c2-g")
        c2_b = config.get_property("c2-b")
        mask_str = config.get_property("mask-type")

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
                    GLib.quark_from_string("gimp-pattern-overlay"),
                    "No valid target layer found for pattern overlay effect.",
                    0
                )
            )

        # Canvas dimensions
        img_w = image.get_width()
        img_h = image.get_height()

        Gimp.context_push()
        image.undo_group_start()

        # Save active selection if any
        has_orig_sel = not Gimp.Selection.is_empty(image)
        orig_sel_channel = Gimp.Selection.save(image) if has_orig_sel else None

        try:
            # 1. Read target layer's alpha matte for strict silhouette clipping
            rect = Gegl.Rectangle.new(0, 0, img_w, img_h)
            target_buf = target_layer.get_buffer()
            raw_target = target_buf.get(rect, 1.0, "RGBA float", Gegl.AbyssPolicy.NONE)
            arr_target = np.frombuffer(raw_target, dtype=np.float32).reshape((img_h, img_w, 4))
            target_alpha = arr_target[:, :, 3].copy()

            # 2. Build pattern tile
            c1 = np.array([c1_r, c1_g, c1_b, 1.0], dtype=np.float32)
            c2 = np.array([c2_r, c2_g, c2_b, 1.0], dtype=np.float32)
            tile = build_pattern_tile(pattern_str, c1, c2)
            th, tw = tile.shape[0], tile.shape[1]

            # 3. Determine coordinate center
            if link_layer:
                offs = target_layer.get_offsets()
                off_x, off_y = float(offs[-2]), float(offs[-1])
                lw = float(target_layer.get_width())
                lh = float(target_layer.get_height())
                cx = off_x + lw * 0.5
                cy = off_y + lh * 0.5
            else:
                cx = float(img_w) * 0.5
                cy = float(img_h) * 0.5

            # 4. Vectorized pattern coordinate mapping across canvas
            sc = max(0.05, float(scale_val) / 100.0)
            rad = math.radians(float(angle_val))
            cos_a = math.cos(-rad)
            sin_a = math.sin(-rad)

            ys, xs = np.indices((img_h, img_w), dtype=np.float32)
            xc = xs - cx
            yc = ys - cy

            u = (xc * cos_a - yc * sin_a) / sc + cx
            v = (xc * sin_a + yc * cos_a) / sc + cy

            u_idx = np.floor(u).astype(np.int32) % tw
            v_idx = np.floor(v).astype(np.int32) % th

            tiled_rgba = tile[v_idx, u_idx].copy()  # Shape: (img_h, img_w, 4)

            # 5. Strictly clip pattern overlay to target layer's silhouette
            tiled_rgba[:, :, 3] *= target_alpha

            # 6. Create dedicated pattern overlay layer
            overlay_name = f"{target_layer.get_name()} (Pattern Overlay - {pattern_str.capitalize()})"
            blend_mode_enum = BLEND_MODES.get(bmode_str, Gimp.LayerMode.NORMAL)
            overlay_layer = Gimp.Layer.new(
                image,
                overlay_name,
                img_w,
                img_h,
                Gimp.ImageType.RGBA_IMAGE,
                max(0.0, min(100.0, opacity_val)),
                blend_mode_enum
            )

            # Insert immediately above target layer in stack
            parent = target_layer.get_parent()
            pos = image.get_item_position(target_layer)
            image.insert_layer(overlay_layer, parent, pos)

            # 7. Write clipped pattern pixels into overlay GeglBuffer
            ol_buf = overlay_layer.get_buffer()
            ol_buf.set(rect, "RGBA float", tiled_rgba.tobytes())
            ol_buf.flush()
            overlay_layer.update(0, 0, img_w, img_h)

            # 8. Layer Mask Attachment
            if mask_str == "auto":
                if has_orig_sel and orig_sel_channel is not None:
                    image.select_item(Gimp.ChannelOps.REPLACE, orig_sel_channel)
                    mask = overlay_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    overlay_layer.add_mask(mask)
            elif mask_str == "reveal-all":
                mask = overlay_layer.create_mask(Gimp.AddMaskType.WHITE)
                overlay_layer.add_mask(mask)
            elif mask_str == "conceal-all":
                mask = overlay_layer.create_mask(Gimp.AddMaskType.BLACK)
                overlay_layer.add_mask(mask)
            elif mask_str == "selection":
                if has_orig_sel and orig_sel_channel is not None:
                    image.select_item(Gimp.ChannelOps.REPLACE, orig_sel_channel)
                    mask = overlay_layer.create_mask(Gimp.AddMaskType.SELECTION)
                    overlay_layer.add_mask(mask)

            # Restore original selection or clear
            if has_orig_sel and orig_sel_channel is not None:
                image.select_item(Gimp.ChannelOps.REPLACE, orig_sel_channel)
                image.remove_channel(orig_sel_channel)
            else:
                Gimp.Selection.none(image)

            # Set overlay layer as active layer
            image.set_selected_layers([overlay_layer])

            image.undo_group_end()
            Gimp.context_pop()
            Gimp.displays_flush()

            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as e:
            if has_orig_sel and orig_sel_channel is not None:
                try:
                    image.remove_channel(orig_sel_channel)
                except Exception:
                    pass
            image.undo_group_end()
            Gimp.context_pop()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-pattern-overlay"),
                    f"Pattern overlay generation failed: {str(e)}",
                    0
                )
            )


Gimp.main(PatternOverlayPlugin.__gtype__, sys.argv)
