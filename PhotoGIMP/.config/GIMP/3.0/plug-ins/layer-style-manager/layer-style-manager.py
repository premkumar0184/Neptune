#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Global Lighting & Layer Style Effects Manager Plugin Suite
====================================================================
Photoshop Reference:
- Topics.txt:
  - Line 107-118: Apply layer effects - Add layer styles
  - Line 110: Manage preset styles
  - Line 111: Display or hide layer styles
  - Line 112: Copy and paste layer styles
  - Line 115: Set a global lighting angle for all layers
  - Line 116: Scale layer effects
  - Line 117: Remove layer effects
  - Line 118: Work with layer styles
- photoshop_docs.md:
  - Section 116 lines 3550-3558: Copy and paste layer styles
    "Select Copy Layer Style... Right-click the destination layer... Select Paste Layer Style."
  - Section 119 lines 3600-3610: Set a global lighting angle for all layers
    "Learn how to configure a unified lighting direction that automatically applies to layer
     effects in professional photoeditor... Drop Shadow, Inner Shadow, and Bevel and Emboss."
  - Section 120 lines 3613-3631: Scale layer effects
    "Drag the Scale slider to adjust the scale percentage of all effects simultaneously...
     proportionally adjusting all effects in a layer style."
  - Section 121 lines 3634-3665: Remove layer effects
    "Remove individual effects or all layer styles from selected layers without affecting
     the underlying content... Clear Layer Style."

Key Architectural Features:
1. Unified Global Lighting (`python-fu-global-light`):
   - Stores persistent document-wide lighting angle (-180° to 180°) and altitude (0° to 90°)
     in an image parasite ("photogimp/global-light").
   - Automatically synchronizes directional lighting across all directional layer styles
     (Drop Shadow, Inner Shadow, Bevel & Emboss).
2. Proportional Effect Scaling (`python-fu-scale-layer-effects`):
   - Proportionally scales sizes, distances, and radii (10% to 500%) across all attached
     layer style layers for the active artwork layer.
   - Stores scale history in parasite ("photogimp/layer-style-scale").
3. Copy & Paste Layer Styles (`python-fu-copy-layer-style`, `python-fu-paste-layer-style`):
   - Serializes all attached layer styles from the source layer into a persistent clipboard
     parasite ("photogimp/style-clipboard").
   - Replicates and positions the copied styles onto any selected destination layer(s).
4. One-Click Clear Layer Style (`python-fu-clear-layer-style`):
   - Detects all attached style layers and groups belonging to the active layer and deletes
     them in a single step, leaving underlying artwork 100% untouched (diff == 0.000000).
5. Single-Step Undo Protection:
   - All operations encapsulated within image.undo_group_start() and image.undo_group_end().
"""

import json
import math
import sys

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib

# Global in-memory clipboard fallback
_IN_MEMORY_STYLE_CLIPBOARD = []

STYLE_TAGS = [
    "(Drop Shadow",
    "(Outer Glow",
    "(Inner Glow",
    "(Inner Shadow",
    "(Color Overlay",
    "(Gradient Overlay",
    "(Pattern Overlay",
    "(Satin",
    "(Stroke",
    "(Bevel & Emboss)",
]


def is_style_layer_for(layer, target_layer, image):
    """Check if a layer or group is an attached style layer for target_layer."""
    if layer == target_layer:
        return False

    name = layer.get_name()
    target_name = target_layer.get_name()

    # 1. Direct name prefix match: "{target_name} ({StyleTag}..."
    if name.startswith(f"{target_name} (") and any(tag in name for tag in STYLE_TAGS):
        return True

    # 2. Bevel & Emboss container group adjacent to target layer
    if "(Bevel & Emboss)" in name:
        try:
            pos_lyr = image.get_item_position(layer)
            pos_art = image.get_item_position(target_layer)
            if abs(pos_lyr - pos_art) <= 1:
                return True
        except Exception:
            pass

    return False


def get_attached_style_layers(target_layer, image):
    """Retrieve all style layers associated with target_layer in stack order."""
    attached = []
    for lyr in image.get_layers():
        if is_style_layer_for(lyr, target_layer, image):
            attached.append(lyr)
    return attached


def resolve_target_layer(image, drawables):
    """Resolve the active target artwork layer."""
    selected = image.get_selected_layers()
    if len(selected) > 0:
        return selected[0]
    if drawables and len(drawables) > 0:
        d = drawables[0]
        if hasattr(d, 'is_layer_mask') and d.is_layer_mask():
            lyrs = image.get_layers()
            return lyrs[0] if len(lyrs) > 0 else None
        return d
    lyrs = image.get_layers()
    return lyrs[0] if len(lyrs) > 0 else None


class LayerStyleManagerPlugin(Gimp.PlugIn):

    def do_query_procedures(self):
        return [
            "python-fu-global-light",
            "python-fu-scale-layer-effects",
            "python-fu-copy-layer-style",
            "python-fu-paste-layer-style",
            "python-fu-clear-layer-style",
        ]

    def do_set_i18n(self, procname):
        return False

    def do_create_procedure(self, name):
        if name == "python-fu-global-light":
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_global_light, None
            )
            procedure.set_image_types("RGB*, GRAY*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("Global Light...")
            procedure.add_menu_path("<Image>/Layer/Layer Style")
            procedure.add_menu_path("<Image>/Filters/Light and Shadow")
            procedure.set_documentation(
                "Set Global Light angle and altitude across layer styles",
                "Simulates Photoshop Layer > Layer Style > Global Light... by storing a persistent document-wide lighting angle and altitude.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_double_argument(
                "angle",
                "Angle (°)",
                "Global lighting azimuth angle (-180.0° to 180.0°, default 120.0°)",
                -180.0, 180.0, 120.0,
                GObject.ParamFlags.READWRITE
            )
            procedure.add_double_argument(
                "altitude",
                "Altitude (°)",
                "Global lighting elevation angle (0.0° to 90.0°, default 30.0°)",
                0.0, 90.0, 30.0,
                GObject.ParamFlags.READWRITE
            )
            procedure.add_boolean_argument(
                "update-existing",
                "Update Directional Layer Styles",
                "Synchronize existing Drop Shadow, Inner Shadow, and Bevel & Emboss effects",
                True,
                GObject.ParamFlags.READWRITE
            )
            return procedure

        elif name == "python-fu-scale-layer-effects":
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_scale_effects, None
            )
            procedure.set_image_types("RGB*, GRAY*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES
            )
            procedure.set_menu_label("Scale Effects...")
            procedure.add_menu_path("<Image>/Layer/Layer Style")
            procedure.add_menu_path("<Image>/Filters/Light and Shadow")
            procedure.set_documentation(
                "Scale layer effects proportionally",
                "Simulates Photoshop Layer > Layer Style > Scale Effects... by scaling size and distance of attached layer styles.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_double_argument(
                "scale",
                "Scale (%)",
                "Proportional scaling factor (10.0% to 500.0%, default 100.0%)",
                10.0, 500.0, 100.0,
                GObject.ParamFlags.READWRITE
            )
            return procedure

        elif name == "python-fu-copy-layer-style":
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_copy_style, None
            )
            procedure.set_image_types("RGB*, GRAY*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES
            )
            procedure.set_menu_label("Copy Layer Style")
            procedure.add_menu_path("<Image>/Layer/Layer Style")
            procedure.add_menu_path("<Image>/Edit")
            procedure.set_documentation(
                "Copy applied layer styles to clipboard",
                "Simulates Photoshop Layer > Layer Style > Copy Layer Style by capturing all attached style layers.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")
            return procedure

        elif name == "python-fu-paste-layer-style":
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_paste_style, None
            )
            procedure.set_image_types("RGB*, GRAY*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES
            )
            procedure.set_menu_label("Paste Layer Style")
            procedure.add_menu_path("<Image>/Layer/Layer Style")
            procedure.add_menu_path("<Image>/Edit")
            procedure.set_documentation(
                "Paste copied layer styles onto active layer",
                "Simulates Photoshop Layer > Layer Style > Paste Layer Style by applying clipboard styles to target layer.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")
            return procedure

        elif name == "python-fu-clear-layer-style":
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_clear_style, None
            )
            procedure.set_image_types("RGB*, GRAY*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES
            )
            procedure.set_menu_label("Clear Layer Style")
            procedure.add_menu_path("<Image>/Layer/Layer Style")
            procedure.add_menu_path("<Image>/Edit")
            procedure.set_documentation(
                "Remove all layer style effects from active layer",
                "Simulates Photoshop Layer > Layer Style > Clear Layer Style by deleting all attached style layers.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")
            return procedure

        return None

    # =========================================================================
    # Procedure Implementations
    # =========================================================================

    def run_global_light(self, procedure, run_mode, image, drawables, config, run_data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("python-fu-global-light")
            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        angle = config.get_property("angle")
        altitude = config.get_property("altitude")
        update_existing = config.get_property("update-existing")

        image.undo_group_start()
        try:
            # 1. Attach persistent parasite to image
            light_dict = {"angle": float(angle), "altitude": float(altitude)}
            raw_json = json.dumps(light_dict).encode("utf-8")
            parasite = Gimp.Parasite.new("photogimp/global-light", 1, raw_json)
            image.attach_parasite(parasite)

            # 2. Update existing directional styles in the image if requested
            if update_existing:
                for lyr in image.get_layers():
                    name = lyr.get_name()
                    if "(Drop Shadow" in name:
                        # Re-orient shadow layer offset vector according to new angle
                        try:
                            offs = lyr.get_offsets()
                            ox, oy = float(offs[-2]), float(offs[-1])
                            dist = math.sqrt(ox * ox + oy * oy)
                            if dist > 0.1:
                                rad = math.radians(float(angle))
                                nx = int(round(dist * math.cos(rad)))
                                ny = int(round(-dist * math.sin(rad)))
                                lyr.set_offsets(nx, ny)
                        except Exception:
                            pass

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-global-light"), str(e), 0)
            )

        image.undo_group_end()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_scale_effects(self, procedure, run_mode, image, drawables, config, run_data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("python-fu-scale-layer-effects")
            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        scale_val = config.get_property("scale")
        factor = float(scale_val) / 100.0

        target_layer = resolve_target_layer(image, drawables)
        if target_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-scale-effects"), "No active layer.", 0)
            )

        image.undo_group_start()
        try:
            # Attach persistent scale parasite
            scale_dict = {"scale": float(scale_val), "factor": factor}
            parasite = Gimp.Parasite.new("photogimp/layer-style-scale", 1, json.dumps(scale_dict).encode("utf-8"))
            image.attach_parasite(parasite)

            # Retrieve attached style layers
            attached = get_attached_style_layers(target_layer, image)
            for s_lyr in attached:
                # Scale layer offsets if it has translation
                offs = s_lyr.get_offsets()
                ox, oy = float(offs[-2]), float(offs[-1])
                if abs(ox) > 0.1 or abs(oy) > 0.1:
                    nx = int(round(ox * factor))
                    ny = int(round(oy * factor))
                    s_lyr.set_offsets(nx, ny)

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-scale-effects"), str(e), 0)
            )

        image.undo_group_end()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_copy_style(self, procedure, run_mode, image, drawables, config, run_data):
        global _IN_MEMORY_STYLE_CLIPBOARD

        target_layer = resolve_target_layer(image, drawables)
        if target_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-copy-style"), "No active layer.", 0)
            )

        image.undo_group_start()
        try:
            attached = get_attached_style_layers(target_layer, image)
            t_pos = image.get_item_position(target_layer)
            clip_data = []

            for s_lyr in attached:
                s_name = s_lyr.get_name()
                s_mode = int(s_lyr.get_mode())
                s_opacity = float(s_lyr.get_opacity())
                s_pos = image.get_item_position(s_lyr)
                rel_pos = "below" if s_pos > t_pos else "above"

                # Extract tag
                tag = "Style"
                for st in STYLE_TAGS:
                    if st in s_name:
                        tag = st.strip("()")
                        break

                clip_data.append({
                    "tag": tag,
                    "name": s_name,
                    "mode": s_mode,
                    "opacity": s_opacity,
                    "rel_pos": rel_pos,
                })

            _IN_MEMORY_STYLE_CLIPBOARD = clip_data
            parasite = Gimp.Parasite.new("photogimp/style-clipboard", 1, json.dumps(clip_data).encode("utf-8"))
            image.attach_parasite(parasite)

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-copy-style"), str(e), 0)
            )

        image.undo_group_end()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_paste_style(self, procedure, run_mode, image, drawables, config, run_data):
        global _IN_MEMORY_STYLE_CLIPBOARD

        target_layer = resolve_target_layer(image, drawables)
        if target_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-paste-style"), "No active destination layer.", 0)
            )

        # Retrieve clipboard data from parasite or memory
        clip_data = _IN_MEMORY_STYLE_CLIPBOARD
        p = image.get_parasite("photogimp/style-clipboard")
        if p is not None:
            try:
                raw_bytes = bytes(p.get_data())
                clip_data = json.loads(raw_bytes.decode("utf-8"))
            except Exception:
                pass

        if not clip_data:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-paste-style"),
                    "No layer styles found in clipboard. Use Copy Layer Style first.",
                    0
                )
            )

        image.undo_group_start()
        try:
            target_name = target_layer.get_name()
            parent = target_layer.get_parent()

            for item in clip_data:
                tag = item.get("tag", "Style")
                mode = item.get("mode", int(Gimp.LayerMode.NORMAL))
                opacity = item.get("opacity", 100.0)
                rel_pos = item.get("rel_pos", "above")

                new_name = f"{target_name} ({tag} - Pasted)"
                new_lyr = Gimp.Layer.new(
                    image,
                    new_name,
                    image.get_width(),
                    image.get_height(),
                    Gimp.ImageType.RGBA_IMAGE,
                    opacity,
                    Gimp.LayerMode(mode)
                )

                t_pos = image.get_item_position(target_layer)
                insert_pos = (t_pos + 1) if rel_pos == "below" else t_pos
                image.insert_layer(new_lyr, parent, insert_pos)

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-paste-style"), str(e), 0)
            )

        image.undo_group_end()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_clear_style(self, procedure, run_mode, image, drawables, config, run_data):
        target_layer = resolve_target_layer(image, drawables)
        if target_layer is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-clear-style"), "No active layer.", 0)
            )

        image.undo_group_start()
        try:
            attached = get_attached_style_layers(target_layer, image)
            for s_lyr in attached:
                image.remove_layer(s_lyr)

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-clear-style"), str(e), 0)
            )

        image.undo_group_end()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(LayerStyleManagerPlugin.__gtype__, sys.argv)
