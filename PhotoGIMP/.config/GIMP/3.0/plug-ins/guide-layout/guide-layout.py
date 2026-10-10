#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Guide Layout & Compositional Alignment Helper Plugin
==============================================================
Photoshop Reference:
- Topics.txt lines 493-502: "Use grids and measurement guides: Alignment grids and guides,
  Overview of guides, grids, and smart guides, Create guides, Move guides, Edit guides, Remove guides"
- photoshop_docs.md Section 450-454 lines 13150-13290:
  "View > New Guide Layout: Create guides in columns, rows, or margins",
  "View > Guides > Clear Guides: Clear guides from your professional photoeditor document"

Key Architectural Features:
1. Curated Compositional Presets:
   - Rule of Thirds: Photographic 3x3 grid dividing image at 33.33% and 66.67%.
   - Golden Ratio / Phi Grid: Divine proportion dividing image at 38.2% and 61.8% for classical balance.
   - Center Crosshairs: 50% horizontal and vertical guides for central symmetry and 4-quadrant alignment.
   - Safe Margins Frame: 5% outer boundary margins framing safe artwork / print margins.
   - Web 12-Column Grid: 12 responsive columns with 16px gutters and 5% side margins.
   - Print Editorial 3x2 Grid: 3 columns and 2 rows with 12px gutters and 5% print margins.
   - Custom Guide Layout: Full manual control over columns, rows, gutters (px), and margins (%).
2. Clear Existing Guides:
   - Checkbox to remove all prior canvas guides before generating the layout (Photoshop standard).
3. Companion Clear Guides Procedure:
   - `python-fu-clear-guides` for 1-click removal of all document guides (`View > Guides > Clear Guides`).
4. Full Undo Grouping:
   - Encapsulated in a single undo group so entire guide grids can be added or removed with one Ctrl+Z.
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
    "rule-of-thirds": {
        "label": "Rule of Thirds",
        "desc": "Classic photographic 3x3 grid dividing image at 33.3% and 66.7%",
        "columns": 3,
        "rows": 3,
        "col_gutter": 0.0,
        "row_gutter": 0.0,
        "margin_top": 0.0,
        "margin_bottom": 0.0,
        "margin_left": 0.0,
        "margin_right": 0.0,
    },
    "golden-ratio": {
        "label": "Golden Ratio / Phi Grid",
        "desc": "Harmonic divine proportion grid dividing image at 38.2% and 61.8%",
        "columns": 0,
        "rows": 0,
        "col_gutter": 0.0,
        "row_gutter": 0.0,
        "margin_top": 0.0,
        "margin_bottom": 0.0,
        "margin_left": 0.0,
        "margin_right": 0.0,
    },
    "center-split": {
        "label": "Center Crosshairs",
        "desc": "Horizontal and vertical 50% center division into 4 quadrants",
        "columns": 2,
        "rows": 2,
        "col_gutter": 0.0,
        "row_gutter": 0.0,
        "margin_top": 0.0,
        "margin_bottom": 0.0,
        "margin_left": 0.0,
        "margin_right": 0.0,
    },
    "safe-margins": {
        "label": "Safe Margins Frame (5%)",
        "desc": "5% outer boundary margins framing safe artwork area",
        "columns": 0,
        "rows": 0,
        "col_gutter": 0.0,
        "row_gutter": 0.0,
        "margin_top": 5.0,
        "margin_bottom": 5.0,
        "margin_left": 5.0,
        "margin_right": 5.0,
    },
    "web-12-column": {
        "label": "Web 12-Column Responsive Grid",
        "desc": "12 equal columns with 16px gutters and 5% side margins",
        "columns": 12,
        "rows": 0,
        "col_gutter": 16.0,
        "row_gutter": 0.0,
        "margin_top": 0.0,
        "margin_bottom": 0.0,
        "margin_left": 5.0,
        "margin_right": 5.0,
    },
    "print-editorial": {
        "label": "Print Editorial 3x2 Grid",
        "desc": "3 columns and 2 rows with 12px gutters and 5% print margins",
        "columns": 3,
        "rows": 2,
        "col_gutter": 12.0,
        "row_gutter": 12.0,
        "margin_top": 5.0,
        "margin_bottom": 5.0,
        "margin_left": 5.0,
        "margin_right": 5.0,
    },
    "custom": {
        "label": "Custom Guide Layout",
        "desc": "Manual column, row, gutter, and margin configuration",
        "columns": 3,
        "rows": 3,
        "col_gutter": 0.0,
        "row_gutter": 0.0,
        "margin_top": 0.0,
        "margin_bottom": 0.0,
        "margin_left": 0.0,
        "margin_right": 0.0,
    },
}


def clear_image_guides(image):
    """Deletes all existing guides from the image."""
    gid = image.find_next_guide(0)
    while gid > 0:
        next_gid = image.find_next_guide(gid)
        image.delete_guide(gid)
        gid = next_gid


def compute_guide_coordinates(W, H, preset_key, cols, rows, col_gutter, row_gutter,
                                m_top, m_bottom, m_left, m_right):
    """Computes exact horizontal and vertical pixel coordinates for guides."""
    v_guides = []
    h_guides = []

    if preset_key == "golden-ratio":
        # Classical divine proportion (1/phi^2 ≈ 0.381966, 1/phi ≈ 0.618034)
        v_guides.append(int(round(W * 0.38196601)))
        v_guides.append(int(round(W * 0.61803399)))
        h_guides.append(int(round(H * 0.38196601)))
        h_guides.append(int(round(H * 0.61803399)))
        return sorted(list(set(v_guides))), sorted(list(set(h_guides)))

    ml_px = int(round(W * float(m_left) / 100.0))
    mr_px = int(round(W * float(m_right) / 100.0))
    mt_px = int(round(H * float(m_top) / 100.0))
    mb_px = int(round(H * float(m_bottom) / 100.0))

    # Margin guides
    if ml_px > 0 and ml_px < W:
        v_guides.append(ml_px)
    if mr_px > 0 and (W - mr_px) > 0 and (W - mr_px) != ml_px:
        v_guides.append(W - mr_px)
    if mt_px > 0 and mt_px < H:
        h_guides.append(mt_px)
    if mb_px > 0 and (H - mb_px) > 0 and (H - mb_px) != mt_px:
        h_guides.append(H - mb_px)

    usable_w = W - ml_px - mr_px
    usable_h = H - mt_px - mb_px

    # Vertical column guides
    if cols > 1 and usable_w > 0:
        total_gutter_w = (cols - 1) * float(col_gutter)
        if usable_w > total_gutter_w:
            col_w = (usable_w - total_gutter_w) / float(cols)
            for i in range(1, cols):
                if col_gutter <= 0.0:
                    x = int(round(ml_px + i * col_w))
                    if 0 < x < W:
                        v_guides.append(x)
                else:
                    x1 = int(round(ml_px + i * col_w + (i - 1) * col_gutter))
                    x2 = int(round(ml_px + i * col_w + i * col_gutter))
                    if 0 < x1 < W:
                        v_guides.append(x1)
                    if 0 < x2 < W:
                        v_guides.append(x2)

    # Horizontal row guides
    if rows > 1 and usable_h > 0:
        total_gutter_h = (rows - 1) * float(row_gutter)
        if usable_h > total_gutter_h:
            row_h = (usable_h - total_gutter_h) / float(rows)
            for j in range(1, rows):
                if row_gutter <= 0.0:
                    y = int(round(mt_px + j * row_h))
                    if 0 < y < H:
                        h_guides.append(y)
                else:
                    y1 = int(round(mt_px + j * row_h + (j - 1) * row_gutter))
                    y2 = int(round(mt_px + j * row_h + j * row_gutter))
                    if 0 < y1 < H:
                        h_guides.append(y1)
                    if 0 < y2 < H:
                        h_guides.append(y2)

    return sorted(list(set(v_guides))), sorted(list(set(h_guides)))


class GuideLayoutPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return [
            "python-fu-guide-layout",
            "python-fu-clear-guides"
        ]

    def do_create_procedure(self, name):
        if name == "python-fu-clear-guides":
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_clear_guides, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("Clear Guides")
            procedure.add_menu_path("<Image>/View/Guides")
            procedure.add_menu_path("<Image>/Image/Guides")
            procedure.add_menu_path("<Image>/View")
            procedure.set_documentation(
                "Clear All Canvas Guides",
                "Removes all horizontal and vertical guides from the active image document.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")
            return procedure

        # Main python-fu-guide-layout procedure
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, self.run_guide_layout, None
        )
        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES |
            Gimp.ProcedureSensitivityMask.NO_DRAWABLES
        )
        procedure.set_menu_label("New Guide Layout...")
        procedure.add_menu_path("<Image>/View/Guides")
        procedure.add_menu_path("<Image>/Image/Guides")
        procedure.add_menu_path("<Image>/View")

        procedure.set_documentation(
            "New Guide Layout & Compositional Alignment Helper",
            "Generates structured guide layouts including Rule of Thirds, Golden Ratio / Phi Grid, "
            "Center Crosshairs, Safe Margins, Web 12-Column grids, and custom column/row grids.",
            name
        )
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

        # 1. Preset Choice
        preset_choice = Gimp.Choice.new()
        preset_choice.add("rule-of-thirds", 0, "Rule of Thirds", "Classic photographic 3x3 grid dividing image at 33.3% and 66.7%")
        preset_choice.add("golden-ratio", 1, "Golden Ratio / Phi Grid", "Divine proportion grid dividing image at 38.2% and 61.8%")
        preset_choice.add("center-split", 2, "Center Crosshairs", "Horizontal and vertical 50% center division into 4 quadrants")
        preset_choice.add("safe-margins", 3, "Safe Margins Frame (5%)", "5% outer boundary margins framing safe artwork area")
        preset_choice.add("web-12-column", 4, "Web 12-Column Responsive Grid", "12 equal columns with 16px gutters and 5% side margins")
        preset_choice.add("print-editorial", 5, "Print Editorial 3x2 Grid", "3 columns and 2 rows with 12px gutters and 5% print margins")
        preset_choice.add("custom", 6, "Custom Guide Layout", "Manual column, row, gutter, and margin configuration")

        procedure.add_choice_argument(
            "preset",
            "Guide Layout Preset",
            "Curated guide layout preset (rule-of-thirds, golden-ratio, center-split, safe-margins, web-12-column, print-editorial, custom)",
            preset_choice,
            "rule-of-thirds",
            GObject.ParamFlags.READWRITE
        )

        # 2. Clear Existing Guides
        procedure.add_boolean_argument(
            "clear-existing",
            "Clear Existing Guides",
            "Remove all existing guides before generating new layout (default True)",
            True,
            GObject.ParamFlags.READWRITE
        )

        # 3. Columns
        procedure.add_int_argument(
            "columns",
            "Columns",
            "Number of vertical column divisions (0 to 64, default 3)",
            0,
            64,
            3,
            GObject.ParamFlags.READWRITE
        )

        # 4. Rows
        procedure.add_int_argument(
            "rows",
            "Rows",
            "Number of horizontal row divisions (0 to 64, default 3)",
            0,
            64,
            3,
            GObject.ParamFlags.READWRITE
        )

        # 5. Column Gutter
        procedure.add_double_argument(
            "col-gutter",
            "Column Gutter Width",
            "Width of space between columns in pixels (0.0 to 200.0, default 0.0)",
            0.0,
            200.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 6. Row Gutter
        procedure.add_double_argument(
            "row-gutter",
            "Row Gutter Height",
            "Height of space between rows in pixels (0.0 to 200.0, default 0.0)",
            0.0,
            200.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        # 7. Margins
        procedure.add_double_argument(
            "margin-top",
            "Top Margin (%)",
            "Top margin percentage of image height (0.0 to 50.0, default 0.0)",
            0.0,
            50.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "margin-bottom",
            "Bottom Margin (%)",
            "Bottom margin percentage of image height (0.0 to 50.0, default 0.0)",
            0.0,
            50.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "margin-left",
            "Left Margin (%)",
            "Left margin percentage of image width (0.0 to 50.0, default 0.0)",
            0.0,
            50.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "margin-right",
            "Right Margin (%)",
            "Right margin percentage of image width (0.0 to 50.0, default 0.0)",
            0.0,
            50.0,
            0.0,
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run_clear_guides(self, procedure, run_mode, image, drawables, config, data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-clear-guides"),
                    "No valid image provided.",
                    0
                )
            )

        image.undo_group_start()
        try:
            clear_image_guides(image)
            image.undo_group_end()
            Gimp.displays_flush()
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
        except Exception as exc:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-clear-guides"),
                    f"Failed to clear guides: {str(exc)}",
                    0
                )
            )

    def run_guide_layout(self, procedure, run_mode, image, drawables, config, data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-guide-layout"),
                    "No valid image provided.",
                    0
                )
            )

        if run_mode == Gimp.RunMode.INTERACTIVE:
            Gimp.ui_init("guide-layout.py")
            dialog = Gimp.ProcedureDialog.new(procedure, config, "New Guide Layout")
            dialog.fill([
                "preset", "clear-existing", "columns", "rows",
                "col-gutter", "row-gutter",
                "margin-top", "margin-bottom", "margin-left", "margin-right"
            ])
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        preset_key = config.get_property("preset") or "rule-of-thirds"
        if preset_key not in PRESETS:
            preset_key = "rule-of-thirds"
        preset_cfg = PRESETS[preset_key]

        clear_existing = config.get_property("clear-existing")

        if preset_key == "custom":
            cols_val = config.get_property("columns")
            rows_val = config.get_property("rows")
            col_gutter_val = config.get_property("col-gutter")
            row_gutter_val = config.get_property("row-gutter")
            mt_val = config.get_property("margin-top")
            mb_val = config.get_property("margin-bottom")
            ml_val = config.get_property("margin-left")
            mr_val = config.get_property("margin-right")
        else:
            cols_val = preset_cfg["columns"]
            rows_val = preset_cfg["rows"]
            col_gutter_val = preset_cfg["col_gutter"]
            row_gutter_val = preset_cfg["row_gutter"]
            mt_val = preset_cfg["margin_top"]
            mb_val = preset_cfg["margin_bottom"]
            ml_val = preset_cfg["margin_left"]
            mr_val = preset_cfg["margin_right"]

        image.undo_group_start()
        try:
            W = image.get_width()
            H = image.get_height()

            # 1. Clear existing guides if requested
            if clear_existing:
                clear_image_guides(image)

            # 2. Compute guide coordinates
            v_guides, h_guides = compute_guide_coordinates(
                W, H, preset_key, cols_val, rows_val,
                col_gutter_val, row_gutter_val,
                mt_val, mb_val, ml_val, mr_val
            )

            # 3. Add vertical guides
            for x in v_guides:
                image.add_vguide(x)

            # 4. Add horizontal guides
            for y in h_guides:
                image.add_hguide(y)

            image.undo_group_end()
            Gimp.displays_flush()
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as exc:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(
                    GLib.quark_from_string("gimp-guide-layout"),
                    f"Guide layout creation failed: {str(exc)}",
                    0
                )
            )


if __name__ == "__main__":
    Gimp.main(GuideLayoutPlugin.__gtype__, sys.argv)
