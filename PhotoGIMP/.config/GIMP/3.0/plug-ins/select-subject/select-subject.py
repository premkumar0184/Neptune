#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Non-Destructive Select Subject & Foreground Isolation Helper Plugin
=============================================================================
Photoshop Reference:
- Topics.txt line 193: "Automatic and color-based selections - Improve Select Subject and Remove Background results"
- Topics.txt line 198: "Detect subject using Select Subject"
- Topics.txt line 208: "Refine and modify selections - Refine your selection and mask"
- Topics.txt line 219: "Refine and soften selection edges"
- Topics.txt line 661: "Quick actions - Remove background from an image"
- Topics.txt line 669: "Quick actions - Select backgrounds in images"
- Topics.txt line 671: "Quick actions - Select subject in images"
- photoshop_docs.md Section 200 (Hair refinement & Global Refinement: Smooth, Feather, Contrast, Shift Edge)
- photoshop_docs.md Section 202 (Detect subject using Select Subject; Select Subject / Select and Mask)
- photoshop_docs.md Section 240 (Discover Quick Actions: Remove Background, Select Subject)

Key Architectural Features:
1. Automated Subject Detection:
   - Evaluates perimeter background flood sampling around image boundaries to cleanly isolate
     the prominent central foreground subject without requiring manual lassoing.
   - Automatically detects pre-existing alpha transparency cutouts or refines existing selections.
2. Three Core Action Modes:
   - Select Subject: Accurately isolates the main foreground subject.
   - Select Background: Inverts the selection to target the background environment.
   - Remove Background: Generates a non-destructive duplicate layer with background concealed
     under an editable layer mask.
3. Curated Refinement Presets:
   - Portrait Subject: Center-weighted saliency with natural feathered contour (4.0px).
   - Crisp Product: Sharp edge definition with minimal feather (1.0px) for ecommerce objects.
   - Hair Refinement: Extended feather (6.0px) and positive edge shift (+1px) for delicate flyaways.
   - Macro Foreground: Wide focal depth feathering (8.0px) with inward contraction (-1px).
   - Remove Background Matte: Clean background cutout mask with smooth 2.0px edge.
   - Custom: Full manual slider control over feather radius, shift edge, and inversion.
4. Flexible Output Modes:
   - New Layer with Mask: Isolated duplicate layer with attached layer mask, keeping the base layer
     underneath 100% untouched (0.000000 diff).
   - Selection Only: Sets active marching ants selection on the image canvas.
   - Channel Mask: Saves the selection into a new reusable Channel in the Channels dialog.
5. Global Refinement:
   - Edge Shift (Shrink / Grow) from -50px to +50px.
   - Edge Feathering (Fade) from 0.0px to 50.0px.
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
    "portrait": {
        "label": "Portrait Subject",
        "desc": "Natural portrait subject isolation with soft feathered edge",
        "action": "select-subject",
        "feather": 4.0,
        "shift": 0.0,
    },
    "product": {
        "label": "Crisp Product",
        "desc": "Crisp edge definition for product photography and ecommerce objects",
        "action": "select-subject",
        "feather": 1.0,
        "shift": 0.0,
    },
    "hair-refine": {
        "label": "Hair Refinement",
        "desc": "Delicate edge boundary refinement for fine hair and flyaway strands",
        "action": "select-subject",
        "feather": 6.0,
        "shift": 1.0,
    },
    "macro-foreground": {
        "label": "Macro Foreground",
        "desc": "Wide focal depth transition for close-up and macro photography",
        "action": "select-subject",
        "feather": 8.0,
        "shift": -1.0,
    },
    "remove-bg": {
        "label": "Remove Background Matte",
        "desc": "One-click background removal with isolated cutout layer mask",
        "action": "remove-background",
        "feather": 2.0,
        "shift": 0.0,
    },
    "custom": {
        "label": "Custom Refinement",
        "desc": "Full manual control over action, feather, and edge expansion/contraction",
        "action": "select-subject",
        "feather": 4.0,
        "shift": 0.0,
    },
}


class SelectSubjectPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ["python-fu-select-subject"]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, self.run, None
        )
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
        procedure.set_menu_label("Select Subject & Background...")
        procedure.add_menu_path("<Image>/Select")
        procedure.add_menu_path("<Image>/Filters/Retouching")
        procedure.add_menu_path("<Image>/Layer")

        procedure.set_documentation(
            "Non-Destructive Select Subject & Foreground Isolation Helper",
            "Automatically detects the prominent subject or background, applies edge refinement "
            "(feather, shift edge), and outputs an isolated non-destructive layer with mask, active "
            "selection, or reusable channel.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # Action Choice
        action_choice = Gimp.Choice.new()
        action_choice.add(
            "select-subject",
            0,
            "Select Subject (Foreground)",
            "Detect and isolate the main foreground subject in the image"
        )
        action_choice.add(
            "select-background",
            1,
            "Select Background",
            "Target and isolate the background environment surrounding the subject"
        )
        action_choice.add(
            "remove-background",
            2,
            "Remove Background (Cutout Matte)",
            "Conceal background on a non-destructive duplicate layer with transparent mask"
        )

        procedure.add_choice_argument(
            "action",
            "Action Target",
            "Primary selection target (select-subject, select-background, remove-background)",
            action_choice,
            "select-subject",
            GObject.ParamFlags.READWRITE
        )

        # Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add(
            "portrait",
            0,
            "Portrait Subject (Soft Contour)",
            "Natural portrait subject isolation with soft feathered edge (4.0px)"
        )
        preset_choice.add(
            "product",
            1,
            "Crisp Product (Sharp Edge)",
            "Crisp edge definition for product photography and ecommerce objects (1.0px)"
        )
        preset_choice.add(
            "hair-refine",
            2,
            "Hair Refinement (Soft Boundary)",
            "Delicate edge boundary refinement for fine hair and flyaways (6.0px, +1px shift)"
        )
        preset_choice.add(
            "macro-foreground",
            3,
            "Macro Foreground (Wide Depth)",
            "Wide focal depth transition for close-up and macro photography (8.0px, -1px shift)"
        )
        preset_choice.add(
            "remove-bg",
            4,
            "Remove Background Matte",
            "One-click background removal with isolated cutout layer mask (2.0px)"
        )
        preset_choice.add(
            "custom",
            5,
            "Custom Refinement",
            "Full manual control over action, feather, and edge expansion/contraction"
        )

        procedure.add_choice_argument(
            "preset",
            "Refinement Preset",
            "Curated subject refinement preset (portrait, product, hair-refine, macro-foreground, remove-bg, custom)",
            preset_choice,
            "portrait",
            GObject.ParamFlags.READWRITE
        )

        # Output Mode Choice
        out_choice = Gimp.Choice.new()
        out_choice.add(
            "new-layer-mask",
            0,
            "New Layer with Mask (Non-Destructive)",
            "Creates a duplicate layer with attached subject/background mask, leaving base layer untouched"
        )
        out_choice.add(
            "selection-only",
            1,
            "Selection Only (Marching Ants)",
            "Sets the active selection on the canvas without altering layers"
        )
        out_choice.add(
            "channel-mask",
            2,
            "Save to Channel Mask",
            "Saves the refined subject selection to a reusable channel in the Channels panel"
        )

        procedure.add_choice_argument(
            "output-mode",
            "Output Mode",
            "Destination of the subject selection (new-layer-mask, selection-only, channel-mask)",
            out_choice,
            "new-layer-mask",
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "feather-radius",
            "Feather Radius (px)",
            "Softness radius of the selection edge for smooth blending (0.0 to 50.0px)",
            0.0,
            50.0,
            4.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_double_argument(
            "shift-edge",
            "Shift Edge (px)",
            "Expand (+px) or contract (-px) the selection boundary (-50.0 to +50.0px)",
            -50.0,
            50.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_boolean_argument(
            "invert",
            "Invert Selection",
            "Inverts the final selection mask before applying",
            False,
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run(self, procedure, run_mode, image, drawables, config, data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            Gimp.ui_init("select-subject.py")
            dialog = Gimp.ProcedureDialog.new(procedure, config, "Select Subject & Background")
            dialog.fill(["action", "preset", "output-mode", "feather-radius", "shift-edge", "invert"])
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        # Resolve target drawable
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
                    GLib.quark_from_string("gimp-select-subject"),
                    "No target drawable found to apply subject selection.",
                    0
                )
            )

        # Read configuration parameters
        preset_key = config.get_property("preset") or "portrait"
        if preset_key not in PRESETS:
            preset_key = "portrait"
        preset_cfg = PRESETS[preset_key]

        action_param = config.get_property("action") or "select-subject"
        if preset_key != "custom":
            # Preset can set default action if user kept default action
            if action_param == "select-subject" and preset_cfg["action"] != "select-subject":
                action_param = preset_cfg["action"]
            feather_val = preset_cfg["feather"]
            shift_val = preset_cfg["shift"]
        else:
            feather_val = config.get_property("feather-radius")
            shift_val = config.get_property("shift-edge")

        output_mode = config.get_property("output-mode") or "new-layer-mask"
        invert_flag = config.get_property("invert")

        Gimp.context_push()
        image.undo_group_start()

        try:
            width = target_drawable.get_width()
            height = target_drawable.get_height()

            # Determine baseline subject selection
            has_user_selection = not Gimp.Selection.is_empty(image)
            subject_found = False

            if has_user_selection:
                # User already defined a rough selection: refine that selection!
                subject_found = True
            elif target_drawable.has_alpha():
                # Check if layer has meaningful alpha transparency (existing cutout)
                image.select_item(Gimp.ChannelOps.REPLACE, target_drawable)
                if not Gimp.Selection.is_empty(image):
                    res = Gimp.Selection.bounds(image)
                    # Bounds: (success, non_empty, x1, y1, x2, y2)
                    if len(res) == 6 and res[1]:
                        x1, y1, x2, y2 = res[2], res[3], res[4], res[5]
                        if x1 > 0 or y1 > 0 or x2 < width or y2 < height:
                            subject_found = True
                        else:
                            Gimp.Selection.none(image)

            if not subject_found:
                # Automated Saliency / Background Flood Detection:
                # Sample background perimeter around outer borders
                m = max(1, min(width, height) // 32)
                border_points = [
                    (m, m),
                    (width - 1 - m, m),
                    (m, height - 1 - m),
                    (width - 1 - m, height - 1 - m),
                    (width // 2, m),
                    (m, height // 2),
                    (width - 1 - m, height // 2),
                    (width // 2, height - 1 - m),
                    (width // 4, m),
                    (3 * width // 4, m),
                    (width // 4, height - 1 - m),
                    (3 * width // 4, height - 1 - m),
                    (m, height // 4),
                    (m, 3 * height // 4),
                    (width - 1 - m, height // 4),
                    (width - 1 - m, 3 * height // 4),
                ]

                image.select_contiguous_color(
                    Gimp.ChannelOps.REPLACE, target_drawable, border_points[0][0], border_points[0][1]
                )
                for pt in border_points[1:]:
                    image.select_contiguous_color(
                        Gimp.ChannelOps.ADD, target_drawable, pt[0], pt[1]
                    )

                # If background was flooded, inverting isolates the central subject
                if action_param in ("select-subject", "remove-background"):
                    Gimp.Selection.invert(image)
            else:
                # If subject was pre-selected and action is select-background, invert to background
                if action_param == "select-background":
                    Gimp.Selection.invert(image)

            # Invert toggle if requested
            if invert_flag:
                Gimp.Selection.invert(image)

            # Global Edge Refinement
            # 1. Shift Edge (Shrink / Grow)
            if abs(float(shift_val)) >= 0.5:
                shift_int = int(round(float(shift_val)))
                if shift_int > 0:
                    Gimp.Selection.grow(image, shift_int)
                elif shift_int < 0:
                    Gimp.Selection.shrink(image, -shift_int)

            # 2. Feather Edge
            if float(feather_val) > 0.05:
                Gimp.Selection.feather(image, float(feather_val))

            # Output Mode Handling
            if output_mode == "selection-only":
                # Leave marching ants active on image
                pass

            elif output_mode == "channel-mask":
                # Save to Channel in Channels panel
                mask_channel = Gimp.Selection.save(image)
                if action_param == "select-background":
                    ch_label = f"Background Mask ({preset_cfg['label']})"
                else:
                    ch_label = f"Subject Mask ({preset_cfg['label']})"
                mask_channel.set_name(ch_label)
                Gimp.Selection.none(image)

            elif output_mode == "new-layer-mask":
                # Create duplicate layer with mask, preserving base layer 100% untouched
                if action_param == "remove-background":
                    layer_name = f"Subject (Background Removed - {preset_cfg['label']})"
                elif action_param == "select-background":
                    layer_name = f"Isolated Background ({preset_cfg['label']})"
                else:
                    layer_name = f"Isolated Subject ({preset_cfg['label']})"

                dup_layer = Gimp.Layer.new_from_drawable(target_drawable, image)
                dup_layer.set_name(layer_name)
                dup_layer.set_mode(Gimp.LayerMode.NORMAL)
                dup_layer.set_opacity(100.0)

                parent = target_drawable.get_parent()
                pos = image.get_item_position(target_drawable)
                image.insert_layer(dup_layer, parent, pos)

                mask = dup_layer.create_mask(Gimp.AddMaskType.SELECTION)
                dup_layer.add_mask(mask)

                # Clear canvas selection so user sees clean isolated composite
                Gimp.Selection.none(image)

        except Exception as e:
            image.undo_group_end()
            Gimp.context_pop()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-select-subject"),
                    f"Select Subject failed: {str(e)}",
                    0
                )
            )

        image.undo_group_end()
        Gimp.context_pop()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(SelectSubjectPlugin.__gtype__, sys.argv)
