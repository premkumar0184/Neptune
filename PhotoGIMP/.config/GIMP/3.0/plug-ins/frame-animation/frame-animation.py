#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Frame Animation & Tweening Helper Plugin
==================================================
Photoshop Reference:
- Topics.txt lines 512-523:
  - Create animation frames
  - Edit animation frames
  - Unify layer properties in animation frames
  - Copy frames with layer properties
  - Create frames using tweening
  - Manage layer visibility in animation frames
  - Specify a delay time in frame animations
  - Choose a frame disposal method
  - Specify looping in frame animations
  - Delete animations
- photoshop_docs.md Section 472-477 lines 13880-14010:
  - Window > Timeline: Create Frame Animation
  - Create frames using tweening
  - Specify a delay time in frame animations
  - Choose a frame disposal method
  - Specify looping in frame animations
  - Delete animations

Key Architectural Features:
1. Frame Animation Setup (`python-fu-frame-animation-setup`):
   - Configures uniform frame timing with standard FPS presets:
     - 10 fps (100ms) - Standard Animation Default
     - 12 fps (83ms) - Cinema Animation Standard
     - 24 fps (42ms) - Film Cinematic Standard
     - 30 fps (33ms) - High Frame Rate Video Standard
     - 20 fps (50ms) - Fast Action Web
     - 5 fps (200ms) - Casual Slideshow
     - 2 fps (500ms) - Slow Presentation
     - Custom delay (10-10000ms)
   - Frame disposal modes:
     - `(replace)`: Dispose previous frame (Photoshop Dispose)
     - `(combine)`: Do not dispose previous frame (Photoshop Do Not Dispose)
     - `preserve`: Keep existing disposal settings
   - Target scope: All Layers or Selected / Active Layer only.
   - Reverse layer order toggle to flip playback direction.

2. Create Tween Frames (`python-fu-create-tween`):
   - Generates smooth in-between frames between keyframe layers with linear opacity crossfading.
   - Supports consecutive pairs across full animation or active pair.
   - Configurable frames to add (1 to 50), frame delay, and disposal tag.
   - Mathematically merges crossfaded duplicates into single self-contained intermediate frames.
   - Places tween frames at exact stack positions between keyframes.

3. Ping-Pong Loop Animation (`python-fu-pingpong-animation`):
   - Duplicates layers in reverse order (excluding turnaround endpoints) to produce
     seamless forward-and-backward bounce loops without jump cuts.

4. Remove Animation Tags (`python-fu-remove-animation-tags`):
   - Photoshop "Delete Animations" equivalent: cleanly strips all `(\\d+ms)` and
     `(replace|combine)` tags from layer names.

5. Single-Step Undo Protection:
   - All batch operations encapsulated in `image.undo_group_start()` / `image.undo_group_end()`.
"""

import os
import re
import sys
import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib


PROC_SETUP = "python-fu-frame-animation-setup"
PROC_TWEEN = "python-fu-create-tween"
PROC_PINGPONG = "python-fu-pingpong-animation"
PROC_REMOVE_TAGS = "python-fu-remove-animation-tags"

FPS_DELAYS = {
    "10fps": 100,
    "12fps": 83,
    "24fps": 42,
    "30fps": 33,
    "20fps": 50,
    "5fps": 200,
    "2fps": 500,
}


def clean_animation_name(name):
    """Strips delay and disposal tags from layer name."""
    if not name:
        return ""
    cleaned = re.sub(r'\s*\(\s*\d+\s*ms\s*\)', '', name, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*\(\s*(?:replace|combine)\s*\)', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def extract_delay_ms(name, default=100):
    """Extracts existing delay in ms if present."""
    if not name:
        return default
    m = re.search(r'\(\s*(\d+)\s*ms\s*\)', name, flags=re.IGNORECASE)
    return int(m.group(1)) if m else default


def extract_disposal(name, default="replace"):
    """Extracts existing disposal mode if present."""
    if not name:
        return default
    m = re.search(r'\(\s*(replace|combine)\s*\)', name, flags=re.IGNORECASE)
    return m.group(1).lower() if m else default


class FrameAnimationPlugin(Gimp.PlugIn):
    def do_query_procedures(self):
        return [
            PROC_SETUP,
            PROC_TWEEN,
            PROC_PINGPONG,
            PROC_REMOVE_TAGS,
        ]

    def do_create_procedure(self, name):
        if name == PROC_SETUP:
            return self._create_setup_procedure(name)
        elif name == PROC_TWEEN:
            return self._create_tween_procedure(name)
        elif name == PROC_PINGPONG:
            return self._create_pingpong_procedure(name)
        elif name == PROC_REMOVE_TAGS:
            return self._create_remove_tags_procedure(name)
        return None

    # --------------------------------------------------------------------------
    # Procedure Definitions
    # --------------------------------------------------------------------------

    def _create_setup_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_setup, None)
        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES |
            Gimp.ProcedureSensitivityMask.NO_DRAWABLES
        )
        procedure.set_menu_label("Frame Animation Setup...")
        procedure.add_menu_path("<Image>/Filters/Animation")
        procedure.add_menu_path("<Image>/Image/Animation")

        procedure.set_documentation(
            "Frame Animation Setup & Timing Helper",
            "Configures uniform frame duration (ms or FPS presets), disposal methods "
            "(replace vs combine), and layer playback order across animation layers.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. FPS Preset
        fps_choice = Gimp.Choice.new()
        fps_choice.add("10fps", 0, "10 fps (100ms) - Standard Default", "10 frames per second standard web animation")
        fps_choice.add("12fps", 1, "12 fps (83ms) - Cinema Animation", "12 frames per second cinematic animation")
        fps_choice.add("24fps", 2, "24 fps (42ms) - Film Cinematic", "24 frames per second cinematic film standard")
        fps_choice.add("30fps", 3, "30 fps (33ms) - High Frame Rate Video", "30 frames per second video standard")
        fps_choice.add("20fps", 4, "20 fps (50ms) - Fast Action Web", "20 frames per second fast web animation")
        fps_choice.add("5fps", 5, "5 fps (200ms) - Casual Slideshow", "5 frames per second casual slideshow")
        fps_choice.add("2fps", 6, "2 fps (500ms) - Slow Presentation", "2 frames per second presentation pacing")
        fps_choice.add("custom", 7, "Custom Delay", "Use custom delay duration in milliseconds")

        procedure.add_choice_argument(
            "fps-preset",
            "Frame Rate / Delay Preset",
            "Target frame rate preset or custom delay duration",
            fps_choice,
            "10fps",
            GObject.ParamFlags.READWRITE
        )

        # 2. Custom Delay
        procedure.add_int_argument(
            "custom-delay",
            "Custom Delay (ms)",
            "Duration per frame in milliseconds (10 to 10000, default 100)",
            10,
            10000,
            100,
            GObject.ParamFlags.READWRITE
        )

        # 3. Disposal Method
        disp_choice = Gimp.Choice.new()
        disp_choice.add("replace", 0, "Dispose (replace)", "Each frame clears prior frame before displaying")
        disp_choice.add("combine", 1, "Do Not Dispose (combine)", "Cumulative frame display preserving underlying frames")
        disp_choice.add("preserve", 2, "Preserve Existing Disposal", "Keep existing layer disposal tags if present")

        procedure.add_choice_argument(
            "disposal",
            "Frame Disposal Method",
            "Frame disposal behavior during playback (replace, combine, preserve)",
            disp_choice,
            "replace",
            GObject.ParamFlags.READWRITE
        )

        # 4. Target Layers
        target_choice = Gimp.Choice.new()
        target_choice.add("all-layers", 0, "All Layers in Image", "Apply animation setup to all layers in document")
        target_choice.add("selected-layer", 1, "Selected / Active Layer Only", "Apply animation setup only to currently active layer")

        procedure.add_choice_argument(
            "target-layers",
            "Target Scope",
            "Which layers to apply animation timing and disposal to",
            target_choice,
            "all-layers",
            GObject.ParamFlags.READWRITE
        )

        # 5. Reverse Order
        procedure.add_boolean_argument(
            "reverse-order",
            "Reverse Playback Order",
            "Invert the layer stack order to play animation backwards (default False)",
            False,
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def _create_tween_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_tween, None)
        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )
        procedure.set_menu_label("Create Tween Frames...")
        procedure.add_menu_path("<Image>/Filters/Animation")
        procedure.add_menu_path("<Image>/Image/Animation")

        procedure.set_documentation(
            "Create Tween Frames",
            "Generates smooth intermediate frames between keyframes using opacity crossfading.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Tween Mode
        mode_choice = Gimp.Choice.new()
        mode_choice.add("consecutive-pairs", 0, "All Consecutive Layer Pairs", "Tween across the entire layer stack sequence")
        mode_choice.add("active-pair", 1, "Active Layer and Next Layer Above", "Tween only between active layer and the layer directly above it")

        procedure.add_choice_argument(
            "tween-mode",
            "Tween Range Mode",
            "Whether to tween all consecutive layers or active pair only",
            mode_choice,
            "consecutive-pairs",
            GObject.ParamFlags.READWRITE
        )

        # 2. Frames to Add
        procedure.add_int_argument(
            "frames-to-add",
            "Frames to Add",
            "Number of intermediate in-between frames to generate (1 to 50, default 3)",
            1,
            50,
            3,
            GObject.ParamFlags.READWRITE
        )

        # 3. Frame Delay
        procedure.add_int_argument(
            "delay-ms",
            "Tween Frame Delay (ms)",
            "Duration per tween frame in milliseconds (10 to 5000, default 100)",
            10,
            5000,
            100,
            GObject.ParamFlags.READWRITE
        )

        # 4. Disposal
        disp_choice = Gimp.Choice.new()
        disp_choice.add("replace", 0, "Dispose (replace)", "Tween frames clear prior content")
        disp_choice.add("combine", 1, "Do Not Dispose (combine)", "Tween frames overlay on prior content")
        disp_choice.add("inherit", 2, "Inherit from Keyframe", "Inherit disposal method from adjacent keyframe")

        procedure.add_choice_argument(
            "disposal",
            "Tween Frame Disposal",
            "Disposal method tag applied to generated tween frames",
            disp_choice,
            "replace",
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def _create_pingpong_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_pingpong, None)
        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )
        procedure.set_menu_label("Ping-Pong Loop Animation...")
        procedure.add_menu_path("<Image>/Filters/Animation")
        procedure.add_menu_path("<Image>/Image/Animation")

        procedure.set_documentation(
            "Ping-Pong Loop Animation",
            "Duplicates intermediate frames in reverse order to produce seamless looping animation.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        procedure.add_boolean_argument(
            "include-endpoints",
            "Include First and Last Frames",
            "Whether to duplicate the turnaround endpoint frames (False avoids duplicate frames at turnaround)",
            False,
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def _create_remove_tags_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run_remove_tags, None)
        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES |
            Gimp.ProcedureSensitivityMask.NO_DRAWABLES
        )
        procedure.set_menu_label("Remove Animation Tags")
        procedure.add_menu_path("<Image>/Filters/Animation")
        procedure.add_menu_path("<Image>/Image/Animation")

        procedure.set_documentation(
            "Remove Animation Tags",
            "Removes frame duration and disposal tags from all layer names in document.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        return procedure

    # --------------------------------------------------------------------------
    # Execution Handlers
    # --------------------------------------------------------------------------

    def run_setup(self, procedure, run_mode, image, drawables, config, data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-frame-animation"),
                    "No valid image provided.",
                    0
                )
            )

        fps_preset = config.get_property("fps-preset")
        custom_delay = config.get_property("custom-delay")
        disposal_mode = config.get_property("disposal")
        target_mode = config.get_property("target-layers")
        reverse_order = config.get_property("reverse-order")

        # Calculate effective delay
        if fps_preset == "custom":
            delay_ms = max(10, min(10000, int(custom_delay)))
        else:
            delay_ms = FPS_DELAYS.get(fps_preset, 100)

        image.undo_group_start()
        try:
            # Resolve target layers
            if target_mode == "selected-layer":
                selected = image.get_selected_layers()
                target_layers = list(selected) if selected else []
                if not target_layers:
                    active = image.get_active_layer()
                    if active:
                        target_layers = [active]
            else:
                target_layers = list(image.get_layers())

            for layer in target_layers:
                cur_name = layer.get_name()
                base_name = clean_animation_name(cur_name)

                # Determine disposal tag
                if disposal_mode == "replace":
                    disp_tag = "(replace)"
                elif disposal_mode == "combine":
                    disp_tag = "(combine)"
                elif disposal_mode == "preserve":
                    cur_disp = extract_disposal(cur_name, "replace")
                    disp_tag = f"({cur_disp})"
                else:
                    disp_tag = "(replace)"

                new_name = f"{base_name} ({delay_ms}ms) {disp_tag}".strip()
                layer.set_name(new_name)

            # Reversing layer stack order if requested
            if reverse_order:
                all_layers = list(image.get_layers())
                for layer in all_layers:
                    image.reorder_item(layer, None, 0)

            Gimp.displays_flush()
        finally:
            image.undo_group_end()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_tween(self, procedure, run_mode, image, drawables, config, data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-frame-animation"),
                    "No valid image provided.",
                    0
                )
            )

        tween_mode = config.get_property("tween-mode")
        frames_to_add = max(1, min(50, int(config.get_property("frames-to-add"))))
        delay_ms = max(10, min(5000, int(config.get_property("delay-ms"))))
        disposal_arg = config.get_property("disposal")

        image.undo_group_start()
        try:
            all_layers = list(image.get_layers())
            if len(all_layers) < 2:
                # Need at least 2 layers to tween
                return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

            # Consecutive pairs in top-to-bottom stack order:
            # In GIMP stack (top-to-bottom): all_layers[0] is top, all_layers[-1] is bottom.
            # In bottom-up playback order: all_layers[i+1] is earlier frame (bottom), all_layers[i] is later frame (top).
            pairs = []
            if tween_mode == "active-pair":
                active = image.get_active_layer()
                if active and active in all_layers:
                    idx = all_layers.index(active)
                    if idx > 0:
                        # active is bottom, layer directly above it in stack is top
                        pairs.append((all_layers[idx], all_layers[idx - 1]))
                    elif idx < len(all_layers) - 1:
                        # active is top, layer directly below it is bottom
                        pairs.append((all_layers[idx + 1], all_layers[idx]))
                if not pairs:
                    # Fallback to bottom-most adjacent pair
                    pairs.append((all_layers[-1], all_layers[-2]))
            else:
                # consecutive-pairs: iterate in top-to-bottom stack order
                # Top pair first: (all_layers[1], all_layers[0])
                # Down to bottom pair: (all_layers[-1], all_layers[-2])
                for i in range(len(all_layers) - 1):
                    layer_bottom = all_layers[i + 1]
                    layer_top = all_layers[i]
                    pairs.append((layer_bottom, layer_top))

            # Process pairs
            for layer_bottom, layer_top in pairs:
                # Determine disposal tag
                if disposal_arg == "replace":
                    disp_tag = "(replace)"
                elif disposal_arg == "combine":
                    disp_tag = "(combine)"
                elif disposal_arg == "inherit":
                    disp_tag = f"({extract_disposal(layer_top.get_name(), 'replace')})"
                else:
                    disp_tag = "(replace)"

                pos_top = image.get_item_position(layer_top)

                # Insert frames k = 1 to frames_to_add at pos_top + 1
                for k in range(1, frames_to_add + 1):
                    alpha = k / (frames_to_add + 1.0)
                    pct = int(round(alpha * 100.0))

                    # Duplicate bottom and top keyframes
                    dup_bottom = layer_bottom.copy()
                    image.insert_layer(dup_bottom, None, pos_top + 1)

                    dup_top = layer_top.copy()
                    image.insert_layer(dup_top, None, pos_top + 1)
                    dup_top.set_opacity(alpha * 100.0)

                    # Merge top duplicate down onto bottom duplicate
                    merged = image.merge_down(dup_top, Gimp.MergeType.CLIP_TO_BOTTOM_LAYER)
                    clean_b = clean_animation_name(layer_bottom.get_name())
                    clean_t = clean_animation_name(layer_top.get_name())
                    tween_name = f"Tween {clean_b}-{clean_t} ({pct}%) ({delay_ms}ms) {disp_tag}"
                    merged.set_name(tween_name)

            Gimp.displays_flush()
        finally:
            image.undo_group_end()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_pingpong(self, procedure, run_mode, image, drawables, config, data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-frame-animation"),
                    "No valid image provided.",
                    0
                )
            )

        include_endpoints = config.get_property("include-endpoints")

        image.undo_group_start()
        try:
            # Playback order bottom-up:
            layers_bottom_up = list(reversed(image.get_layers()))
            if len(layers_bottom_up) < 2:
                return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

            if include_endpoints:
                reverse_seq = layers_bottom_up[::-1]
            else:
                if len(layers_bottom_up) < 3:
                    # Nothing to reverse if only 2 frames without endpoints
                    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
                reverse_seq = layers_bottom_up[-2:0:-1]

            # Insert duplicated layers at the top of the stack (position 0)
            for src_layer in reverse_seq:
                dup = src_layer.copy()
                orig_name = src_layer.get_name()
                clean = clean_animation_name(orig_name)
                delay = extract_delay_ms(orig_name)
                disposal = extract_disposal(orig_name)
                dup.set_name(f"{clean} (Loop Reverse) ({delay}ms) ({disposal})")
                image.insert_layer(dup, None, 0)

            Gimp.displays_flush()
        finally:
            image.undo_group_end()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def run_remove_tags(self, procedure, run_mode, image, drawables, config, data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-frame-animation"),
                    "No valid image provided.",
                    0
                )
            )

        image.undo_group_start()
        try:
            for layer in image.get_layers():
                clean = clean_animation_name(layer.get_name())
                if clean:
                    layer.set_name(clean)

            Gimp.displays_flush()
        finally:
            image.undo_group_end()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(FrameAnimationPlugin.__gtype__, sys.argv)
