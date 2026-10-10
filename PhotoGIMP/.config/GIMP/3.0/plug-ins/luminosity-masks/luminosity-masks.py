#!/usr/bin/env python3
"""
PhotoGIMP Luminosity Masks Plugin for GIMP 3.x

Generates 9 precision tonal selection channels from the current image composite:
  Lights 1, Lights 2, Lights 3   — progressively narrower highlight selections
  Darks 1,  Darks 2,  Darks 3    — progressively narrower shadow selections
  Midtones 1, Midtones 2, Midtones 3 — progressively narrower midtone selections

Equivalent to the Photoshop technique of loading luminosity selections from
the Channels panel, used in professional landscape and portrait editing.

Algorithm
---------
1. Flatten a duplicate of the image; desaturate via LUMINANCE mode.
2. Import the result as a temporary layer in the *target* image.
3. L1 = direct buffer copy of the luminosity layer → channel.
4. L2 = L1 loaded as selection, luminosity channel intersected with that selection.
5. L3 = L2 loaded as selection, luminosity channel intersected with that selection.
6. D1/D2/D3 = pixel-inverted copies of L1/L2/L3.
7. M1/M2/M3 = INTERSECT of Ln with Dn (midtones band).
8. Remove temporary reference layer; clear selection.

API notes (GIMP 3.x)
--------------------
- Gegl.Buffer.copy(src_rect, repeat_mode, dst_buf, dst_rect)
- Gimp.Layer.new_from_drawable(src_drawable, dest_image) — cross-image copy
- image.select_item(Gimp.ChannelOps.REPLACE, channel)
- channel.combine_masks(other, Gimp.ChannelOps.INTERSECT, 0, 0)
- channel.invert()
"""

import sys

import gi

gi.require_version('Gimp', '3.0')
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl, GLib, GObject, Gimp

# Channel display colour (semi-transparent cyan, common for mask channels)
_CHANNEL_COLOR_HTML = "rgba(0,200,200,0.5)"
_CHANNEL_OPACITY = 50.0   # percent


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_lum_reference(image):
    """Return a temporary grayscale luminosity layer inserted into *image*.

    1. Duplicate the image, flatten the copy, desaturate by LUMINANCE.
    2. Import via Gimp.Layer.new_from_drawable so it belongs to *image*.
    3. Delete the duplicate.
    The caller must remove the returned layer with ``image.remove_layer()``.
    """
    dup = image.duplicate()
    flat = dup.flatten()

    # Desaturate using weighted luminosity (ITU-R BT.709).
    # NOTE: Gimp.Drawable.desaturate() is deprecated in GIMP 3.x but remains
    # functional in 3.2.6.  Gimp.DrawableFilter (gegl:gray) requires a live
    # display context and fails on temporary layers with "filter is hidden".
    flat.desaturate(Gimp.DesaturateMode.LUMINANCE)  # noqa: deprecated-ok

    # Cross-image copy: the new layer correctly belongs to *image*
    ref = Gimp.Layer.new_from_drawable(flat, image)
    ref.set_name("__lum_ref__")
    image.insert_layer(ref, None, 0)

    dup.delete()
    return ref


def _buf_copy(src_drawable, dst_channel):
    """Copy pixel data from *src_drawable* buffer to *dst_channel* buffer.

    Uses the GIMP 3 / GEGL API:
      src_buf.copy(src_rect, abyss_policy, dst_buf, dst_rect)
    """
    w = src_drawable.get_width()
    h = src_drawable.get_height()
    rect = Gegl.Rectangle.new(0, 0, w, h)

    src_buf = src_drawable.get_buffer()
    dst_buf = dst_channel.get_buffer()
    src_buf.copy(rect, Gegl.AbyssPolicy.CLAMP, dst_buf, rect)
    dst_buf.flush()


def _new_channel(image, name):
    """Create and insert an empty channel with standard display colour."""
    color = Gegl.Color.new(_CHANNEL_COLOR_HTML)
    ch = Gimp.Channel.new(
        image, name,
        image.get_width(), image.get_height(),
        _CHANNEL_OPACITY, color
    )
    image.insert_channel(ch, None, -1)
    return ch


# ── Channel construction logic ────────────────────────────────────────────────

def _make_l1(image, lum_ref):
    """Lights 1 — full luminosity range, direct copy."""
    ch = _new_channel(image, "Lights 1")
    _buf_copy(lum_ref, ch)
    return ch


def _make_lights_n(image, lum_ref, prev_channel, name):
    """Lights N (N > 1) — progressively narrower highlight selection.

    Load the previous Lights channel as a selection, then copy the luminosity
    layer under that selection mask. This retains full values only where the
    image was already bright in the previous mask.
    """
    image.select_item(Gimp.ChannelOps.REPLACE, prev_channel)

    ch = _new_channel(image, name)
    _buf_copy(lum_ref, ch)

    # Intersect with the current (loaded) selection so that pixels outside
    # the selection become black (not selected) in this channel.
    sel = image.get_selection()
    ch.combine_masks(sel, Gimp.ChannelOps.INTERSECT, 0, 0)

    Gimp.Selection.none(image)
    return ch


def _make_darks(image, lights_channel, name):
    """Darks N — invert of the corresponding Lights channel."""
    ch = _new_channel(image, name)
    _buf_copy(lights_channel, ch)
    # NOTE: Gimp.Drawable.invert() is deprecated but functional in GIMP 3.2.6.
    # Gimp.DrawableFilter (gegl:invert-linear) fails on channels in headless mode.
    ch.invert()  # noqa: deprecated-ok
    return ch


def _make_midtones(image, lights_channel, darks_channel, name):
    """Midtones N — INTERSECT of the corresponding Lights and Darks channels.

    Only pixels that are simultaneously in the Lights band AND the Darks band
    survive — those are the midtone values.
    """
    ch = _new_channel(image, name)
    _buf_copy(lights_channel, ch)
    ch.combine_masks(darks_channel, Gimp.ChannelOps.INTERSECT, 0, 0)
    return ch


# ── Plugin entry point ────────────────────────────────────────────────────────

def luminosity_masks(procedure, run_mode, image, drawables, config, data):
    """Generate 9 luminosity mask channels on *image*."""
    if image is None or not image.is_valid():
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR, GLib.Error()
        )

    if run_mode == Gimp.RunMode.INTERACTIVE:
        gi.require_version('GimpUi', '3.0')
        from gi.repository import GimpUi

        GimpUi.init('python-fu-luminosity-masks')
        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    Gimp.context_push()
    image.undo_group_start()

    lum_ref = None
    try:
        # Step 1: Build the grayscale luminosity reference layer
        lum_ref = _build_lum_reference(image)

        # Step 2: Clear any prior selection
        Gimp.Selection.none(image)

        # Step 3: Lights channels (iteratively narrowing highlight selections)
        l1 = _make_l1(image, lum_ref)
        l2 = _make_lights_n(image, lum_ref, l1, "Lights 2")
        l3 = _make_lights_n(image, lum_ref, l2, "Lights 3")

        # Step 4: Darks channels (inverted Lights)
        d1 = _make_darks(image, l1, "Darks 1")
        d2 = _make_darks(image, l2, "Darks 2")
        d3 = _make_darks(image, l3, "Darks 3")

        # Step 5: Midtones channels (Lights ∩ Darks)
        _make_midtones(image, l1, d1, "Midtones 1")
        _make_midtones(image, l2, d2, "Midtones 2")
        _make_midtones(image, l3, d3, "Midtones 3")

        # Step 6: Remove temporary reference layer and clear selection
        image.remove_layer(lum_ref)
        lum_ref = None
        Gimp.Selection.none(image)

        Gimp.displays_flush()

    except Exception as exc:
        if lum_ref is not None:
            try:
                image.remove_layer(lum_ref)
            except Exception:
                pass
        image.undo_group_end()
        Gimp.context_pop()
        msg = "Luminosity Masks error: " + str(exc)
        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                GLib.quark_from_string("gimp-luminosity-masks"), msg, 0
            )
        )

    image.undo_group_end()
    Gimp.context_pop()

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


# ── PlugIn class registration ─────────────────────────────────────────────────

class LuminosityMasks(Gimp.PlugIn):
    """PhotoGIMP: Luminosity Masks channel generator."""

    def do_set_i18n(self, procname):
        return True, 'gimp30-python', None

    def do_query_procedures(self):
        return ['python-fu-luminosity-masks']

    def do_create_procedure(self, name):
        Gegl.init(None)

        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN,
            luminosity_masks, None
        )
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )
        procedure.set_documentation(
            "Luminosity Masks — Generate 9 Precision Tonal Channels",
            (
                "Creates 9 luminosity mask channels from the current image composite: "
                "Lights 1/2/3 (progressively narrower highlight selections), "
                "Darks 1/2/3 (progressively narrower shadow selections), "
                "Midtones 1/2/3 (progressively narrower midtone selections). "
                "These channels can be loaded as selections for highly targeted "
                "tonal adjustments, equivalent to Photoshop luminosity masking."
            ),
            name
        )
        procedure.set_menu_label("Luminosity Masks...")
        procedure.set_attribution("PhotoGIMP", "PhotoGIMP Project", "2026")
        procedure.add_menu_path("<Image>/Select")

        return procedure


if __name__ == "__main__":
    Gimp.main(LuminosityMasks.__gtype__, sys.argv)
