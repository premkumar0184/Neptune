#!/usr/bin/env python3
"""
PhotoGIMP Quick Export Plugin for GIMP 3.x

Implements the standard Photoshop Quick Export workflow:
  - File > Quick Export as PNG (instant 1-click export to PNG).
  - File > Quick Export... (configurable export dialog with format, scaling,
    and output directory options).

In Photoshop and modern digital production pipelines, exporting web and social
assets shouldn't require complex multi-step modal dialogs. Quick Export applies
preset rules and scaling directly to a temporary clone of the image without
modifying the active document.
"""

import os
import sys
import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import Gio
from gi.repository import GObject
from gi.repository import GLib


def _perform_export(image, fmt, scale_mode, quality, output_dir, suffix):
    """Core export routine. Operates on a duplicated clone so the open document is untouched."""
    # 1. Determine destination folder
    if output_dir and os.path.isdir(output_dir):
        dest_dir = output_dir
    else:
        gfile = image.get_file()
        if gfile is not None and gfile.get_path():
            dest_dir = os.path.dirname(gfile.get_path())
        else:
            dest_dir = (
                GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES)
                or os.path.expanduser("~")
            )

    # 2. Determine base filename
    gfile = image.get_file()
    if gfile is not None and gfile.get_path():
        base_name = os.path.splitext(os.path.basename(gfile.get_path()))[0]
    else:
        base_name = "Untitled"

    # 3. Determine format, scaling, and output path
    ext = "png" if fmt.lower() == "png" else "jpg"
    factor = 1.0
    scale_tag = ""
    if scale_mode == "0.5x":
        factor = 0.5
        scale_tag = "@0.5x"
    elif scale_mode == "2x":
        factor = 2.0
        scale_tag = "@2x"

    final_suffix = suffix if suffix else scale_tag
    out_filename = f"{base_name}{final_suffix}.{ext}"
    out_path = os.path.join(dest_dir, out_filename)

    # 4. Duplicate and scale image clone
    dup = image.duplicate()
    try:
        if factor != 1.0:
            target_w = max(1, int(round(dup.get_width() * factor)))
            target_h = max(1, int(round(dup.get_height() * factor)))
            dup.scale(target_w, target_h)

        pdb = Gimp.get_pdb()
        gio_file = Gio.File.new_for_path(out_path)

        if ext == "png":
            proc = pdb.lookup_procedure("file-png-export")
            if proc is None:
                raise RuntimeError("PDB procedure file-png-export not found.")
            cfg = proc.create_config()
            cfg.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
            cfg.set_property("image", dup)
            cfg.set_property("file", gio_file)
            res = proc.run(cfg)
        else:
            proc = pdb.lookup_procedure("file-jpeg-export")
            if proc is None:
                raise RuntimeError("PDB procedure file-jpeg-export not found.")
            cfg = proc.create_config()
            cfg.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
            cfg.set_property("image", dup)
            cfg.set_property("file", gio_file)
            cfg.set_property("quality", float(quality))
            res = proc.run(cfg)

    finally:
        dup.delete()

    if os.path.isfile(out_path):
        size_kb = os.path.getsize(out_path) / 1024.0
        try:
            Gimp.message(f"Quick Export: Saved {out_filename} ({size_kb:.1f} KB)")
        except Exception:
            pass

    return out_path


def quick_export(procedure, run_mode, image, drawables, config, data):
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-quick-export"),
                "No valid image provided.",
                0
            )
        )

    # Interactive dialog handling
    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-quick-export')
        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    fmt = config.get_property('format')
    scale = config.get_property('scale')
    quality = config.get_property('quality')
    output_dir = config.get_property('output-dir')
    suffix = config.get_property('suffix')

    try:
        out_path = _perform_export(image, fmt, scale, quality, output_dir, suffix)
    except Exception as exc:
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-quick-export"),
                str(exc),
                0
            )
        )

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


def quick_export_png(procedure, run_mode, image, drawables, config, data):
    """Instant one-click PNG export without modal dialog."""
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-quick-export-png"),
                "No valid image provided.",
                0
            )
        )

    try:
        out_path = _perform_export(image, "png", "1x", 0.90, "", "")
    except Exception as exc:
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-quick-export-png"),
                str(exc),
                0
            )
        )

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


class QuickExport(Gimp.PlugIn):
    ## GimpPlugIn virtual methods ##
    def do_set_i18n(self, procname):
        return True, 'gimp30-python', None

    def do_query_procedures(self):
        return [
            'python-fu-quick-export',
            'python-fu-quick-export-png'
        ]

    def do_create_procedure(self, name):
        Gegl.init(None)

        if name == 'python-fu-quick-export-png':
            procedure = Gimp.ImageProcedure.new(
                self,
                name,
                Gimp.PDBProcType.PLUGIN,
                quick_export_png,
                None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_documentation(
                "Quick Export as PNG",
                (
                    "Instantly exports the active image to PNG format in the document "
                    "folder (or Pictures directory) at 1x scale without opening modal dialogs."
                ),
                name
            )
            procedure.set_menu_label("Quick Export as PNG")
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP Project", "2026")
            procedure.add_menu_path("<Image>/File")
            procedure.add_menu_path("<Image>/File/Export")
            return procedure

        elif name == 'python-fu-quick-export':
            procedure = Gimp.ImageProcedure.new(
                self,
                name,
                Gimp.PDBProcType.PLUGIN,
                quick_export,
                None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_documentation(
                "Quick Export...",
                (
                    "Fast export of the image with presets for format (PNG/JPEG), "
                    "scaling (1x, 0.5x, 2x), quality, and destination directory."
                ),
                name
            )
            procedure.set_menu_label("Quick Export...")
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP Project", "2026")
            procedure.add_menu_path("<Image>/File")
            procedure.add_menu_path("<Image>/File/Export")

            # Format Choice: PNG or JPEG
            format_choice = Gimp.Choice.new()
            format_choice.add(
                "png",
                0,
                "PNG (Lossless with Transparency)",
                "Lossless image format preserving alpha transparency"
            )
            format_choice.add(
                "jpeg",
                1,
                "JPEG (Compressed for Web / Social)",
                "Compressed photographic format for web and social distribution"
            )
            procedure.add_choice_argument(
                "format",
                "Export _Format",
                "Output file format",
                format_choice,
                "png",
                GObject.ParamFlags.READWRITE
            )

            # Scale Choice: 1x, 0.5x, 2x
            scale_choice = Gimp.Choice.new()
            scale_choice.add(
                "1x",
                0,
                "1x (Original Size)",
                "Export at original canvas resolution"
            )
            scale_choice.add(
                "0.5x",
                1,
                "0.5x (Half Size - 50%)",
                "Export scaled down to 50% width and height"
            )
            scale_choice.add(
                "2x",
                2,
                "2x (Double Size - 200% Retina)",
                "Export scaled up to 200% width and height for high-DPI displays"
            )
            procedure.add_choice_argument(
                "scale",
                "_Scale Preset",
                "Resolution scaling preset",
                scale_choice,
                "1x",
                GObject.ParamFlags.READWRITE
            )

            procedure.add_double_argument(
                "quality",
                "JPEG _Quality",
                "Compression quality factor for JPEG export (0.5 to 1.0)",
                0.5,
                1.0,
                0.90,
                GObject.ParamFlags.READWRITE
            )

            procedure.add_string_argument(
                "output-dir",
                "Output _Folder",
                "Target folder (leave empty for document directory)",
                "",
                GObject.ParamFlags.READWRITE
            )

            procedure.add_string_argument(
                "suffix",
                "Filename _Suffix",
                "Optional filename suffix before extension (e.g. _web)",
                "",
                GObject.ParamFlags.READWRITE
            )

            return procedure


if __name__ == "__main__":
    Gimp.main(QuickExport.__gtype__, sys.argv)
