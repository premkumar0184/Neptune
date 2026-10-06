#!/usr/bin/env python3
"""
PhotoGIMP End-to-End Headless Regression Test Suite
Exercises all 5 custom Photoshop workflow plugins via GIMP 3.x Python-Fu.

Runs under:
  gimp --no-interface --console-messages --batch-interpreter=python-fu-eval --batch "exec(open('tests/gimp_e2e_suite.py').read())" --quit
"""

import os
import shutil
import struct
import sys
import time

import gi
gi.require_version("Gimp", "3.0")
gi.require_version("Gegl", "0.4")
from gi.repository import Gimp, Gegl, GLib


# --- Test Reporting Helpers ---

TOTAL_TESTS = 0
PASSED_TESTS = 0
FAILED_TESTS = 0
FAILURES = []


def record_pass(test_id, name, detail=""):
    global TOTAL_TESTS, PASSED_TESTS
    TOTAL_TESTS += 1
    PASSED_TESTS += 1
    msg = f"  [PASS] {test_id}: {name}"
    if detail:
        msg += f" ({detail})"
    print(msg)


def record_fail(test_id, name, error_msg):
    global TOTAL_TESTS, FAILED_TESTS
    TOTAL_TESTS += 1
    FAILED_TESTS += 1
    FAILURES.append((test_id, name, error_msg))
    print(f"  [FAIL] {test_id}: {name} -- ERROR: {error_msg}")


def clear_selection(image):
    Gimp.Selection.none(image)


def get_composite_pixel(image, x, y):
    dup = image.duplicate()
    flat = dup.flatten()
    rgba = flat.get_pixel(x, y).get_rgba()
    dup.delete()
    return rgba


# ==============================================================================
# TEST 1: PDB Registration Audit
# ==============================================================================
def test_pdb_registration():
    print("\n--- Test Suite 1: PDB Procedure Registration ---")
    pdb = Gimp.get_pdb()
    required_procs = [
        ("python-fu-frequency-separation", "Frequency Separation"),
        ("python-fu-luminosity-masks", "Luminosity Masks"),
        ("python-fu-dodge-burn-layer", "Dodge & Burn Layer"),
        ("python-fu-high-pass-sharpen", "High Pass Sharpen"),
        ("python-fu-quick-export", "Quick Export Dialog"),
        ("python-fu-quick-export-png", "Quick Export as PNG"),
        ("python-fu-vignette-lighting", "Vignette Lighting Layer"),
        ("python-fu-depth-blur", "Depth Defocus / Background Blur"),
        ("python-fu-shadow-highlight", "Shadows & Highlights Recovery"),
        ("python-fu-black-and-white", "Black & White Conversion & Toning"),
        ("python-fu-photo-filter", "Photo Filter Optical Lens Effect"),
        ("python-fu-vibrance", "Vibrance & Smart Saturation Helper"),
        ("python-fu-color-balance", "Color Balance & Tonal Grading Helper"),
    ]

    for proc_name, label in required_procs:
        try:
            exists = pdb.procedure_exists(proc_name)
            if not exists:
                record_fail("PDB-REG", proc_name, "Procedure does not exist in GIMP PDB")
                continue
            proc = pdb.lookup_procedure(proc_name)
            if proc is None:
                record_fail("PDB-REG", proc_name, "Lookup returned None")
                continue
            record_pass("PDB-REG", f"{label} ({proc_name})", "registered")
        except Exception as e:
            record_fail("PDB-REG", proc_name, str(e))


# ==============================================================================
# TEST 2: Frequency Separation Retouching Plugin (Phase 6)
# ==============================================================================
def test_frequency_separation():
    print("\n--- Test Suite 2: Frequency Separation Retouching Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-frequency-separation")
    if proc is None:
        record_fail("FS-01", "Procedure lookup", "Procedure not found")
        return

    image = Gimp.Image.new(200, 200, Gimp.ImageBaseType.RGB)
    try:
        # Create base portrait layer
        base = Gimp.Layer.new(image, "Portrait", 200, 200, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.7, 0.5, 0.4)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        # Run procedure headlessly
        config = proc.create_config()
        config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        config.set_property("image", image)
        config.set_property("radius", 4.0)

        res = proc.run(config)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("FS-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("FS-01", "Execution status", "SUCCESS")

        # Verify layer structure
        layers = image.get_layers()
        if len(layers) < 2:
            record_fail("FS-02", "Layer count", f"Expected >= 2 layers, got {len(layers)}")
            return
        record_pass("FS-02", "Layer count", f"{len(layers)} top-level layers")

        group = layers[0]
        if not isinstance(group, Gimp.GroupLayer):
            record_fail("FS-03", "Group container", f"Top layer is not GroupLayer: {type(group)}")
            return
        record_pass("FS-03", "Group container", group.get_name())

        children = group.get_children()
        child_names = [c.get_name() for c in children]
        if "High Frequency (Texture)" not in child_names or "Low Frequency (Color & Tone)" not in child_names:
            record_fail("FS-04", "Component layers", f"Missing components in: {child_names}")
            return
        record_pass("FS-04", "Component layers", f"{child_names}")

        # Verify High Frequency layer blend mode is Grain Merge
        high_layer = [c for c in children if c.get_name() == "High Frequency (Texture)"][0]
        high_mode = high_layer.get_mode()
        if high_mode != Gimp.LayerMode.GRAIN_MERGE:
            record_fail("FS-05", "Blend mode", f"Expected GRAIN_MERGE, got {high_mode}")
            return
        record_pass("FS-05", "High frequency blend mode", "GRAIN_MERGE (non-destructive)")

    except Exception as e:
        record_fail("FS-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 3: Luminosity Masks Channel Generator (Phase 7)
# ==============================================================================
def test_luminosity_masks():
    print("\n--- Test Suite 3: Luminosity Masks Channel Generator ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-luminosity-masks")
    if proc is None:
        record_fail("LM-01", "Procedure lookup", "Procedure not found")
        return

    image = Gimp.Image.new(200, 200, Gimp.ImageBaseType.RGB)
    try:
        # Base layer with split black (left) and white (right)
        base = Gimp.Layer.new(image, "Base", 200, 200, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)

        # Fill black
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.0, 0.0, 0.0)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        # Fill right half white
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 100, 0, 100, 200)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(1.0, 1.0, 1.0)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        clear_selection(image)

        # Run procedure headlessly
        config = proc.create_config()
        config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        config.set_property("image", image)

        res = proc.run(config)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("LM-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("LM-01", "Execution status", "SUCCESS")

        # Verify all 9 channels exist
        channels = image.get_channels()
        channel_names = [ch.get_name() for ch in channels]
        expected_channels = [
            "Lights 1", "Lights 2", "Lights 3",
            "Darks 1", "Darks 2", "Darks 3",
            "Midtones 1", "Midtones 2", "Midtones 3"
        ]

        missing = [c for c in expected_channels if c not in channel_names]
        if missing:
            record_fail("LM-02", "Channel inventory", f"Missing channels: {missing}")
            return
        record_pass("LM-02", "Channel inventory", f"All 9 precision channels created")

        # Sample pixel values on Lights 1 and Darks 1
        l1_channel = [ch for ch in channels if ch.get_name() == "Lights 1"][0]
        d1_channel = [ch for ch in channels if ch.get_name() == "Darks 1"][0]

        # Black half sample (x=50, y=100)
        l1_black = l1_channel.get_pixel(50, 100).get_rgba()[0]
        d1_black = d1_channel.get_pixel(50, 100).get_rgba()[0]

        # White half sample (x=150, y=100)
        l1_white = l1_channel.get_pixel(150, 100).get_rgba()[0]
        d1_white = d1_channel.get_pixel(150, 100).get_rgba()[0]

        # Assertions
        if abs(l1_white - 1.0) > 0.05 or abs(l1_black - 0.0) > 0.05:
            record_fail("LM-03", "Lights 1 luminance", f"White: {l1_white:.3f}, Black: {l1_black:.3f}")
            return
        record_pass("LM-03", "Lights 1 luminance math", f"White={l1_white:.3f}, Black={l1_black:.3f}")

        if abs(d1_white - 0.0) > 0.05 or abs(d1_black - 1.0) > 0.05:
            record_fail("LM-04", "Darks 1 luminance", f"White: {d1_white:.3f}, Black: {d1_black:.3f}")
            return
        record_pass("LM-04", "Darks 1 luminance math", f"White={d1_white:.3f}, Black={d1_black:.3f}")

    except Exception as e:
        record_fail("LM-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 4: Non-Destructive Dodge & Burn Layer Helper (Phase 8)
# ==============================================================================
def test_dodge_burn_layer():
    print("\n--- Test Suite 4: Non-Destructive Dodge & Burn Layer Helper ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-dodge-burn-layer")
    if proc is None:
        record_fail("DB-01", "Procedure lookup", "Procedure not found")
        return

    image = Gimp.Image.new(120, 120, Gimp.ImageBaseType.RGB)
    try:
        # Base layer with tone
        base = Gimp.Layer.new(image, "Base", 120, 120, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.65, 0.40, 0.25)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        p_base = base.get_pixel(60, 60).get_rgba()

        # Run Soft Light mode
        config = proc.create_config()
        config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        config.set_property("image", image)
        config.set_property("mode", "softlight")
        config.set_property("name", "Dodge & Burn (Neutral Gray)")
        config.set_property("opacity", 100.0)

        res = proc.run(config)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("DB-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("DB-01", "Execution status", "SUCCESS")

        db_layer = image.get_layers()[0]
        if db_layer.get_mode() != Gimp.LayerMode.SOFTLIGHT:
            record_fail("DB-02", "Layer mode", f"Expected SOFTLIGHT, got {db_layer.get_mode()}")
            return
        record_pass("DB-02", "Layer mode & name", f"{db_layer.get_name()} (SOFTLIGHT)")

        # Verify #808080 neutral gray fill (GEGL linear value is ~0.21586)
        expected_gray = Gegl.Color.new("#808080").get_rgba()
        db_pixel = db_layer.get_pixel(60, 60).get_rgba()
        if abs(db_pixel[0] - expected_gray[0]) > 0.005:
            record_fail("DB-03", "Neutral gray fill", f"Pixel value {db_pixel[0]:.4f} != {expected_gray[0]:.4f}")
            return
        record_pass("DB-03", "Neutral gray fill", f"#808080 verified (linear {db_pixel[0]:.4f})")

        # Verify mathematical neutrality (diff = 0.000000)
        comp_pixel = get_composite_pixel(image, 60, 60)
        diff = max(abs(comp_pixel[i] - p_base[i]) for i in range(3))
        if diff > 0.000001:
            record_fail("DB-04", "Mathematical neutrality", f"Composite difference {diff:.6f} > 0")
            return
        record_pass("DB-04", "Mathematical neutrality", f"Identity diff = {diff:.6f}")

        # Verify dodging and burning effect by painting white and black
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 60, 120)
        Gimp.context_set_foreground(Gegl.Color.new("#ffffff"))
        db_layer.edit_fill(Gimp.FillType.FOREGROUND)

        image.select_rectangle(Gimp.ChannelOps.REPLACE, 60, 0, 60, 120)
        Gimp.context_set_foreground(Gegl.Color.new("#000000"))
        db_layer.edit_fill(Gimp.FillType.FOREGROUND)
        clear_selection(image)

        dodged_pixel = get_composite_pixel(image, 30, 60)
        burned_pixel = get_composite_pixel(image, 90, 60)

        if dodged_pixel[0] <= p_base[0] or burned_pixel[0] >= p_base[0]:
            record_fail("DB-05", "Dodge/Burn response", f"Dodged: {dodged_pixel[0]:.3f}, Base: {p_base[0]:.3f}, Burned: {burned_pixel[0]:.3f}")
            return
        record_pass("DB-05", "Dodge & burn response", f"Base={p_base[0]:.3f} -> Dodged={dodged_pixel[0]:.3f}, Burned={burned_pixel[0]:.3f}")

    except Exception as e:
        record_fail("DB-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 5: High Pass Sharpening Helper (Phase 9)
# ==============================================================================
def test_high_pass_sharpen():
    print("\n--- Test Suite 5: High Pass Sharpening Helper ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-high-pass-sharpen")
    if proc is None:
        record_fail("HPS-01", "Procedure lookup", "Procedure not found")
        return

    image = Gimp.Image.new(200, 200, Gimp.ImageBaseType.RGB)
    try:
        # Base layer with high-contrast step edge
        base = Gimp.Layer.new(image, "Base", 200, 200, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)

        # Left half 0.3, right half 0.7
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.3, 0.3, 0.3)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 100, 0, 100, 200)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.7, 0.7, 0.7)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        clear_selection(image)

        # Run procedure headlessly
        config = proc.create_config()
        config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        config.set_property("image", image)
        config.set_property("radius", 3.0)
        config.set_property("mode", "softlight")
        config.set_property("opacity", 100.0)
        config.set_property("add-mask", True)

        res = proc.run(config)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("HPS-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("HPS-01", "Execution status", "SUCCESS")

        hps_layer = image.get_layers()[0]
        if hps_layer.get_mode() != Gimp.LayerMode.SOFTLIGHT:
            record_fail("HPS-02", "Layer mode", f"Expected SOFTLIGHT, got {hps_layer.get_mode()}")
            return
        record_pass("HPS-02", "Layer mode & name", f"{hps_layer.get_name()} (SOFTLIGHT)")

        # Verify layer mask attachment
        mask = hps_layer.get_mask()
        if mask is None:
            record_fail("HPS-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("HPS-03", "Layer mask attachment", "Reveal-all mask attached")

        # Verify edge micro-contrast enhancement
        left_edge = get_composite_pixel(image, 98, 100)[0]
        right_edge = get_composite_pixel(image, 102, 100)[0]
        edge_contrast = right_edge - left_edge

        # Original step contrast was 0.7 - 0.3 = 0.4000
        if edge_contrast <= 0.405:
            record_fail("HPS-04", "Edge micro-contrast", f"Contrast {edge_contrast:.4f} <= baseline 0.4000")
            return
        record_pass("HPS-04", "Edge micro-contrast enhancement", f"Base 0.4000 -> Sharpened {edge_contrast:.4f}")

        # Verify flat area invariance (minimal deviation far from edge)
        flat_val = get_composite_pixel(image, 20, 100)[0]
        dev = abs(flat_val - 0.3)
        if dev > 0.005:
            record_fail("HPS-05", "Flat area invariance", f"Deviation {dev:.5f} > 0.005")
            return
        record_pass("HPS-05", "Flat area noise invariance", f"Deviation {dev:.5f} < 0.005")

    except Exception as e:
        record_fail("HPS-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 6: Quick Export Suite (Phase 10)
# ==============================================================================
def test_quick_export():
    print("\n--- Test Suite 6: Quick Export Suite (Presets & Formats) ---")
    pdb = Gimp.get_pdb()
    proc_png = pdb.lookup_procedure("python-fu-quick-export-png")
    proc_cfg = pdb.lookup_procedure("python-fu-quick-export")

    if proc_png is None or proc_cfg is None:
        record_fail("QE-01", "Procedure lookup", "Quick export procedures not found")
        return

    test_out_dir = "/tmp/photogimp_e2e_export_test"
    os.makedirs(test_out_dir, exist_ok=True)

    image = Gimp.Image.new(200, 100, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "Base", 200, 100, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.2, 0.5, 0.8)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        # 6a: Configurable export - 1x PNG
        cfg_1x = proc_cfg.create_config()
        cfg_1x.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_1x.set_property("image", image)
        cfg_1x.set_property("format", "png")
        cfg_1x.set_property("scale", "1x")
        cfg_1x.set_property("output-dir", test_out_dir)

        res_1x = proc_cfg.run(cfg_1x)
        if res_1x.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("QE-01", "1x PNG Export", f"Status {res_1x.index(0)}")
            return

        file_1x = os.path.join(test_out_dir, "Untitled.png")
        if not os.path.isfile(file_1x):
            record_fail("QE-01", "1x PNG File", f"File missing: {file_1x}")
            return

        # Check PNG header and dimensions
        with open(file_1x, "rb") as f:
            header = f.read(24)
            if header[:8] != b"\x89PNG\r\n\x1a\n":
                record_fail("QE-01", "1x PNG Magic", "Invalid PNG header")
                return
            w, h = struct.unpack(">II", header[16:24])
            if (w, h) != (200, 100):
                record_fail("QE-01", "1x PNG Dimensions", f"Expected (200, 100), got ({w}, {h})")
                return
        record_pass("QE-01", "1x PNG Export", f"Valid PNG ({w}x{h}, {os.path.getsize(file_1x)} bytes)")

        # 6b: 0.5x scaling export
        cfg_half = proc_cfg.create_config()
        cfg_half.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_half.set_property("image", image)
        cfg_half.set_property("format", "png")
        cfg_half.set_property("scale", "0.5x")
        cfg_half.set_property("output-dir", test_out_dir)

        proc_cfg.run(cfg_half)
        file_half = os.path.join(test_out_dir, "Untitled@0.5x.png")
        with open(file_half, "rb") as f:
            w, h = struct.unpack(">II", f.read(24)[16:24])
            if (w, h) != (100, 50):
                record_fail("QE-02", "0.5x Scale", f"Expected (100, 50), got ({w}, {h})")
                return
        record_pass("QE-02", "0.5x Scaling Preset", f"Scaled 200x100 -> {w}x{h}")

        # 6c: 2x scaling export
        cfg_2x = proc_cfg.create_config()
        cfg_2x.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_2x.set_property("image", image)
        cfg_2x.set_property("format", "png")
        cfg_2x.set_property("scale", "2x")
        cfg_2x.set_property("output-dir", test_out_dir)

        proc_cfg.run(cfg_2x)
        file_2x = os.path.join(test_out_dir, "Untitled@2x.png")
        with open(file_2x, "rb") as f:
            w, h = struct.unpack(">II", f.read(24)[16:24])
            if (w, h) != (400, 200):
                record_fail("QE-03", "2x Scale", f"Expected (400, 200), got ({w}, {h})")
                return
        record_pass("QE-03", "2x Scaling Preset", f"Scaled 200x100 -> {w}x{h}")

        # 6d: JPEG format export
        cfg_jpg = proc_cfg.create_config()
        cfg_jpg.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_jpg.set_property("image", image)
        cfg_jpg.set_property("format", "jpeg")
        cfg_jpg.set_property("scale", "1x")
        cfg_jpg.set_property("quality", 0.85)
        cfg_jpg.set_property("output-dir", test_out_dir)

        proc_cfg.run(cfg_jpg)
        file_jpg = os.path.join(test_out_dir, "Untitled.jpg")
        with open(file_jpg, "rb") as f:
            soi = f.read(2)
            if soi != b"\xff\xd8":
                record_fail("QE-04", "JPEG SOI Marker", "Invalid JPEG magic bytes")
                return
        record_pass("QE-04", "JPEG Export", f"Valid JPEG ({os.path.getsize(file_jpg)} bytes)")

        # 6e: Document integrity assertion (canvas and layers untouched)
        if image.get_width() != 200 or image.get_height() != 100 or len(image.get_layers()) != 1:
            record_fail("QE-05", "Canvas Integrity", f"Canvas altered: {image.get_width()}x{image.get_height()}, {len(image.get_layers())} layers")
            return
        record_pass("QE-05", "Canvas Integrity", "Original canvas 200x100 & layers 100% untouched")

    except Exception as e:
        record_fail("QE-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()
        if os.path.isdir(test_out_dir):
            shutil.rmtree(test_out_dir, ignore_errors=True)


# ==============================================================================
# TEST 7: Non-Destructive Vignette & Lens Lighting Helper (Phase 12)
# ==============================================================================
def test_vignette_lighting():
    print("\n--- Test Suite 7: Non-Destructive Vignette & Lens Lighting Helper ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-vignette-lighting")
    if proc is None:
        record_fail("VL-01", "Procedure lookup", "Procedure not found")
        return

    image = Gimp.Image.new(200, 200, Gimp.ImageBaseType.RGB)
    try:
        # Base layer with photo tone
        base = Gimp.Layer.new(image, "Base", 200, 200, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.6, 0.45, 0.35)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        p_base_center = base.get_pixel(100, 100).get_rgba()
        p_base_edge = base.get_pixel(10, 10).get_rgba()

        # 7a: Dark Vignette in Soft Light Mode (Default)
        cfg_dark = proc.create_config()
        cfg_dark.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_dark.set_property("image", image)
        cfg_dark.set_property("tone", "dark")
        cfg_dark.set_property("mode", "softlight")
        cfg_dark.set_property("radius", 1.2)
        cfg_dark.set_property("softness", 0.7)
        cfg_dark.set_property("opacity", 80.0)
        cfg_dark.set_property("add-mask", True)

        res = proc.run(cfg_dark)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("VL-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("VL-01", "Execution status", "SUCCESS")

        vig_layer = image.get_layers()[0]
        if vig_layer.get_mode() != Gimp.LayerMode.SOFTLIGHT:
            record_fail("VL-02", "Layer mode", f"Expected SOFTLIGHT, got {vig_layer.get_mode()}")
            return
        record_pass("VL-02", "Layer mode & name", f"{vig_layer.get_name()} (SOFTLIGHT, {vig_layer.get_opacity():.1f}%)")

        # Verify reveal-all layer mask attachment
        mask = vig_layer.get_mask()
        if mask is None:
            record_fail("VL-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("VL-03", "Layer mask attachment", "Reveal-all mask attached")

        # 7b: Mathematical center neutrality (center must be untouched)
        p_comp_center = get_composite_pixel(image, 100, 100)
        center_diff = max(abs(p_comp_center[i] - p_base_center[i]) for i in range(3))
        if center_diff > 0.000001:
            record_fail("VL-04", "Center neutrality", f"Center altered by {center_diff:.6f} > 0")
            return
        record_pass("VL-04", "Center mathematical neutrality", f"Identity diff = {center_diff:.6f}")

        # 7c: Edge darkening falloff
        p_comp_edge = get_composite_pixel(image, 10, 10)
        edge_darkening = p_base_edge[0] - p_comp_edge[0]
        if edge_darkening < 0.10:
            record_fail("VL-05", "Edge darkening", f"Edge falloff {edge_darkening:.4f} < 0.10")
            return
        record_pass("VL-05", "Edge radial shadow falloff", f"Base {p_base_edge[0]:.3f} -> Darkened {p_comp_edge[0]:.3f} (delta -{edge_darkening:.3f})")

        # 7d: Highlight Vignette Mode Test
        image_hl = Gimp.Image.new(200, 200, Gimp.ImageBaseType.RGB)
        base_hl = Gimp.Layer.new(image_hl, "Base", 200, 200, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image_hl.insert_layer(base_hl, None, 0)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.4, 0.4, 0.4)"))
        base_hl.edit_fill(Gimp.FillType.FOREGROUND)
        p_hl_edge = base_hl.get_pixel(10, 10).get_rgba()

        cfg_hl = proc.create_config()
        cfg_hl.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_hl.set_property("image", image_hl)
        cfg_hl.set_property("tone", "light")
        cfg_hl.set_property("mode", "softlight")
        cfg_hl.set_property("radius", 1.2)
        cfg_hl.set_property("softness", 0.7)
        cfg_hl.set_property("opacity", 80.0)
        cfg_hl.set_property("add-mask", False)

        proc.run(cfg_hl)
        p_comp_hl_edge = get_composite_pixel(image_hl, 10, 10)
        edge_brightening = p_comp_hl_edge[0] - p_hl_edge[0]
        if edge_brightening < 0.10:
            record_fail("VL-06", "Highlight vignette", f"Edge brightening {edge_brightening:.4f} < 0.10")
            image_hl.delete()
            return
        record_pass("VL-06", "Highlight vignette edge brightening", f"Base {p_hl_edge[0]:.3f} -> Brightened {p_comp_hl_edge[0]:.3f} (delta +{edge_brightening:.3f})")
        image_hl.delete()

    except Exception as e:
        record_fail("VL-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 8: Depth of Field & Background Defocus Helper (Phase 13)
# ==============================================================================
def test_depth_blur():
    print("\n--- Test Suite 8: Depth of Field & Background Defocus Helper ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-depth-blur")
    if proc is None:
        record_fail("DF-01", "Procedure lookup", "Procedure not found")
        return

    image = Gimp.Image.new(200, 200, Gimp.ImageBaseType.RGB)
    try:
        # Base layer with gray background and white test spots at center and corner
        base = Gimp.Layer.new(image, "Base", 200, 200, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.5, 0.5, 0.5)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        # Draw distinct white features at center (100, 100) and corner (10, 10)
        Gimp.context_set_foreground(Gegl.Color.new("white"))
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 95, 95, 10, 10)
        base.edit_fill(Gimp.FillType.FOREGROUND)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 5, 5, 10, 10)
        base.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(image)

        p_base_center = base.get_pixel(100, 100).get_rgba()
        p_base_corner = base.get_pixel(10, 10).get_rgba()

        # 8a: Lens Blur Mode with Radial Depth Mask
        cfg = proc.create_config()
        cfg.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg.set_property("image", image)
        cfg.set_property("blur-type", "lens")
        cfg.set_property("blur-radius", 15.0)
        cfg.set_property("highlight-factor", 0.2)
        cfg.set_property("depth-source", "radial")
        cfg.set_property("focal-radius", 0.8)
        cfg.set_property("focal-softness", 0.6)
        cfg.set_property("opacity", 100.0)

        res = proc.run(cfg)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("DF-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("DF-01", "Execution status", "SUCCESS")

        blur_layer = image.get_layers()[0]
        if blur_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("DF-02", "Layer mode", f"Expected NORMAL, got {blur_layer.get_mode()}")
            return
        record_pass("DF-02", "Layer mode & name", f"{blur_layer.get_name()} ({blur_layer.get_mode()})")

        # Verify layer mask attachment
        mask = blur_layer.get_mask()
        if mask is None:
            record_fail("DF-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("DF-03", "Depth mask attachment", "Attached radial depth gradient mask")

        # 8b: Subject sharpness preservation at center (diff == 0.000000)
        p_comp_center = get_composite_pixel(image, 100, 100)
        center_diff = max(abs(p_comp_center[i] - p_base_center[i]) for i in range(3))
        if center_diff > 0.000001:
            record_fail("DF-04", "Subject sharpness", f"Center altered by {center_diff:.6f} > 0")
            return
        record_pass("DF-04", "Subject sharpness invariance", f"Center diff = {center_diff:.6f} (100% sharp)")

        # 8c: Corner background defocus attenuation
        p_comp_corner = get_composite_pixel(image, 10, 10)
        corner_defocus = abs(p_comp_corner[0] - p_base_corner[0])
        if corner_defocus < 0.15:
            record_fail("DF-05", "Background defocus", f"Corner defocus {corner_defocus:.4f} < 0.15")
            return
        record_pass("DF-05", "Background defocus attenuation", f"Corner base {p_base_corner[0]:.3f} -> Defocused {p_comp_corner[0]:.3f} (delta {corner_defocus:.3f})")

        # 8d: Gaussian Blur & Selection Mode Test
        image_sel = Gimp.Image.new(200, 200, Gimp.ImageBaseType.RGB)
        base_sel = Gimp.Layer.new(image_sel, "Base", 200, 200, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image_sel.insert_layer(base_sel, None, 0)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.5, 0.5, 0.5)"))
        base_sel.edit_fill(Gimp.FillType.FOREGROUND)

        # Create active selection around center subject
        image_sel.select_rectangle(Gimp.ChannelOps.REPLACE, 80, 80, 40, 40)

        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image_sel)
        cfg_sel.set_property("blur-type", "gaussian")
        cfg_sel.set_property("blur-radius", 10.0)
        cfg_sel.set_property("depth-source", "selection")
        cfg_sel.set_property("opacity", 90.0)

        proc.run(cfg_sel)
        blur_sel_layer = image_sel.get_layers()[0]
        sel_mask = blur_sel_layer.get_mask()
        if sel_mask is None:
            record_fail("DF-06", "Selection mask mode", "Expected mask attached for selection mode")
            image_sel.delete()
            return

        # Center inside selection must have mask = black (0.0), edge outside selection must have mask = white (1.0)
        mask_center = sel_mask.get_pixel(100, 100).get_rgba()[0]
        mask_edge = sel_mask.get_pixel(10, 10).get_rgba()[0]
        if mask_center > 0.01 or mask_edge < 0.99:
            record_fail("DF-06", "Selection mask inversion", f"Expected center 0.0 and edge 1.0, got center {mask_center:.3f}, edge {mask_edge:.3f}")
            image_sel.delete()
            return
        record_pass("DF-06", "Selection depth mask isolation", f"Subject mask={mask_center:.1f} (in-focus), Background mask={mask_edge:.1f} (blurred)")
        image_sel.delete()

    except Exception as e:
        record_fail("DF-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 9: Shadows & Highlights Recovery Helper (Phase 14)
# ==============================================================================
def test_shadow_highlight():
    print("\n--- Test Suite 9: Shadows & Highlights Recovery Helper ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-shadow-highlight")
    if proc is None:
        record_fail("SH-01", "Procedure lookup", "Procedure not found")
        return

    image = Gimp.Image.new(200, 200, Gimp.ImageBaseType.RGB)
    try:
        # Base layer with deep shadow (left) and harsh highlight (right)
        base = Gimp.Layer.new(image, "Base", 200, 200, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)

        # Left: shadow 0.05
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.05, 0.05, 0.05)"))
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 10, 10, 80, 180)
        base.edit_fill(Gimp.FillType.FOREGROUND)

        # Right: highlight 0.95
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.95, 0.95, 0.95)"))
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 110, 10, 80, 180)
        base.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(image)

        p_base_shadow = base.get_pixel(50, 100).get_rgba()
        p_base_hl = base.get_pixel(150, 100).get_rgba()

        # Run shadow/highlight recovery
        cfg = proc.create_config()
        cfg.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg.set_property("image", image)
        cfg.set_property("shadows", 80.0)
        cfg.set_property("highlights", 80.0)
        cfg.set_property("radius", 20.0)
        cfg.set_property("compress", 0.0)
        cfg.set_property("opacity", 100.0)
        cfg.set_property("add-mask", True)

        res = proc.run(cfg)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("SH-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("SH-01", "Execution status", "SUCCESS")

        sh_layer = image.get_layers()[0]
        if sh_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("SH-02", "Layer mode", f"Expected NORMAL, got {sh_layer.get_mode()}")
            return
        record_pass("SH-02", "Layer mode & name", f"{sh_layer.get_name()} ({sh_layer.get_mode()})")

        # Verify layer mask attachment
        mask = sh_layer.get_mask()
        if mask is None:
            record_fail("SH-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("SH-03", "Layer mask attachment", "Reveal-all mask attached")

        # Composite sampling
        flat = image.duplicate().flatten()
        p_comp_shadow = flat.get_pixel(50, 100).get_rgba()
        p_comp_hl = flat.get_pixel(150, 100).get_rgba()
        flat.delete()

        # 9b: Shadow tone lift (must brighten dark shadow by > 0.20)
        shadow_lift = p_comp_shadow[0] - p_base_shadow[0]
        if shadow_lift < 0.20:
            record_fail("SH-04", "Shadow lift", f"Shadow lift {shadow_lift:.4f} < 0.20")
            return
        record_pass("SH-04", "Shadow tone recovery", f"Base {p_base_shadow[0]:.3f} -> Lifted {p_comp_shadow[0]:.3f} (delta +{shadow_lift:.3f})")

        # 9c: Highlight tone compression (must darken harsh highlight by < -0.15)
        hl_comp = p_comp_hl[0] - p_base_hl[0]
        if hl_comp > -0.15:
            record_fail("SH-05", "Highlight compression", f"Highlight compression {hl_comp:.4f} > -0.15")
            return
        record_pass("SH-05", "Highlight tone compression", f"Base {p_base_hl[0]:.3f} -> Compressed {p_comp_hl[0]:.3f} (delta {hl_comp:.3f})")

        # 9d: Base layer invariance (original pixels must be completely untouched)
        p_base_shadow_after = base.get_pixel(50, 100).get_rgba()
        base_diff = abs(p_base_shadow_after[0] - p_base_shadow[0])
        if base_diff > 0.000001:
            record_fail("SH-06", "Non-destructive invariance", f"Base layer altered by {base_diff:.6f} > 0")
            return
        record_pass("SH-06", "Non-destructive layer preservation", f"Base pixels 100% untouched (diff {base_diff:.6f})")

    except Exception as e:
        record_fail("SH-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 10: Professional Black & White Conversion & Tonal Toning (Phase 15)
# ==============================================================================
def test_black_and_white():
    print("\n--- Test Suite 10: Professional Black & White Conversion & Tonal Toning ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-black-and-white")
    if proc is None:
        record_fail("BW-01", "Procedure lookup", "Procedure not found")
        return

    image = Gimp.Image.new(200, 200, Gimp.ImageBaseType.RGB)
    try:
        # Base layer with pure red on left (10..90) and pure blue on right (110..190)
        base = Gimp.Layer.new(image, "Base", 200, 200, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)

        Gimp.context_set_foreground(Gegl.Color.new("rgb(1.0, 0.0, 0.0)"))
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 10, 10, 80, 180)
        base.edit_fill(Gimp.FillType.FOREGROUND)

        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.0, 0.0, 1.0)"))
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 110, 10, 80, 180)
        base.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(image)

        p_base_red = base.get_pixel(50, 100).get_rgba()
        p_base_blue = base.get_pixel(150, 100).get_rgba()

        # 10a: High Contrast Red Filter Preset (tone="none")
        cfg = proc.create_config()
        cfg.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg.set_property("image", image)
        cfg.set_property("preset", "high-contrast")
        cfg.set_property("tone", "none")
        cfg.set_property("opacity", 100.0)
        cfg.set_property("add-mask", True)

        res = proc.run(cfg)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("BW-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("BW-01", "Execution status", "SUCCESS")

        bw_layer = image.get_layers()[0]
        if bw_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("BW-02", "Layer mode", f"Expected NORMAL, got {bw_layer.get_mode()}")
            return
        record_pass("BW-02", "Layer mode & name", f"{bw_layer.get_name()} ({bw_layer.get_mode()})")

        # Verify layer mask attachment
        mask = bw_layer.get_mask()
        if mask is None:
            record_fail("BW-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("BW-03", "Layer mask attachment", "Reveal-all mask attached")

        # 10b: Exact monochrome neutrality (r == g == b)
        flat = image.duplicate().flatten()
        p_mono_red = flat.get_pixel(50, 100).get_rgba()
        p_mono_blue = flat.get_pixel(150, 100).get_rgba()
        flat.delete()

        neutrality_diff = max(abs(p_mono_red[0] - p_mono_red[1]), abs(p_mono_red[1] - p_mono_red[2]))
        if neutrality_diff > 0.000001:
            record_fail("BW-04", "Monochrome neutrality", f"Color cast detected: max channel diff {neutrality_diff:.6f} > 0")
            return
        record_pass("BW-04", "Monochrome channel neutrality", f"R={p_mono_red[0]:.3f}, G={p_mono_red[1]:.3f}, B={p_mono_red[2]:.3f} (diff {neutrality_diff:.6f})")

        # 10c: Channel weighting response (Red weight 0.60 vs Blue weight 0.10)
        weight_contrast = p_mono_red[0] - p_mono_blue[0]
        if weight_contrast < 0.40:
            record_fail("BW-05", "Channel weighting response", f"Expected red-blue contrast > 0.40, got {weight_contrast:.4f}")
            return
        record_pass("BW-05", "Channel weighting response", f"Red filter: Red luminance {p_mono_red[0]:.3f} vs Blue {p_mono_blue[0]:.3f} (delta +{weight_contrast:.3f})")

        # 10d: Warm Sepia Toning Test on separate test canvas
        image_sepia = Gimp.Image.new(100, 100, Gimp.ImageBaseType.RGB)
        base_sepia = Gimp.Layer.new(image_sepia, "Base", 100, 100, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image_sepia.insert_layer(base_sepia, None, 0)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.5, 0.5, 0.5)"))
        base_sepia.edit_fill(Gimp.FillType.FOREGROUND)

        cfg_sepia = proc.create_config()
        cfg_sepia.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sepia.set_property("image", image_sepia)
        cfg_sepia.set_property("preset", "neutral")
        cfg_sepia.set_property("tone", "sepia")
        cfg_sepia.set_property("opacity", 100.0)
        cfg_sepia.set_property("add-mask", False)

        proc.run(cfg_sepia)
        flat_s = image_sepia.duplicate().flatten()
        p_sepia = flat_s.get_pixel(50, 50).get_rgba()
        flat_s.delete()
        image_sepia.delete()

        # Authentic warm sepia tone: Red > Green > Blue
        if not (p_sepia[0] > p_sepia[1] and p_sepia[1] > p_sepia[2]):
            record_fail("BW-06", "Sepia toning", f"Expected Red > Green > Blue, got R={p_sepia[0]:.3f}, G={p_sepia[1]:.3f}, B={p_sepia[2]:.3f}")
            return
        record_pass("BW-06", "Photographic sepia toning", f"Warm split: R={p_sepia[0]:.3f} > G={p_sepia[1]:.3f} > B={p_sepia[2]:.3f}")

        # 10e: Non-destructive base layer invariance
        p_base_red_after = base.get_pixel(50, 100).get_rgba()
        base_diff = max(abs(p_base_red_after[i] - p_base_red[i]) for i in range(3))
        if base_diff > 0.000001:
            record_fail("BW-07", "Non-destructive invariance", f"Base layer altered by {base_diff:.6f} > 0")
            return
        record_pass("BW-07", "Non-destructive layer preservation", f"Base pixels 100% untouched (diff {base_diff:.6f})")

    except Exception as e:
        record_fail("BW-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 11: Photo Filter Optical Warming & Cooling Helper (Phase 16)
# ==============================================================================
def test_photo_filter():
    print("\n--- Test Suite 11: Photo Filter Optical Warming & Cooling Helper ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-photo-filter")
    if proc is None:
        record_fail("PF-01", "Procedure lookup", "Procedure not found")
        return

    image = Gimp.Image.new(100, 100, Gimp.ImageBaseType.RGB)
    try:
        # Base layer with 50% neutral gray
        base = Gimp.Layer.new(image, "Base", 100, 100, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.5, 0.5, 0.5)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        p_base = base.get_pixel(50, 50).get_rgba()

        # 11a: Warming Filter (85) at 25% density with preserve-luminosity
        cfg_warm = proc.create_config()
        cfg_warm.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_warm.set_property("image", image)
        cfg_warm.set_property("preset", "warming-85")
        cfg_warm.set_property("density", 25.0)
        cfg_warm.set_property("preserve-luminosity", True)
        cfg_warm.set_property("add-mask", True)

        res = proc.run(cfg_warm)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("PF-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("PF-01", "Execution status", "SUCCESS")

        filter_layer = image.get_layers()[0]
        if filter_layer.get_mode() != Gimp.LayerMode.LCH_COLOR:
            record_fail("PF-02", "Layer mode", f"Expected LCH_COLOR ({int(Gimp.LayerMode.LCH_COLOR)}), got {filter_layer.get_mode()}")
            return
        if abs(filter_layer.get_opacity() - 25.0) > 0.01:
            record_fail("PF-02", "Layer opacity", f"Expected 25.0%, got {filter_layer.get_opacity()}%")
            return
        record_pass("PF-02", "Layer mode & opacity", f"{filter_layer.get_name()} ({filter_layer.get_mode()}, {filter_layer.get_opacity()}%)")

        # Verify layer mask attachment
        mask = filter_layer.get_mask()
        if mask is None:
            record_fail("PF-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("PF-03", "Layer mask attachment", "Reveal-all mask attached")

        # 11b: Optical warming shift (Red > Blue on neutral canvas)
        flat = image.duplicate().flatten()
        p_warm = flat.get_pixel(50, 50).get_rgba()
        flat.delete()

        warm_delta = p_warm[0] - p_warm[2]
        if warm_delta < 0.10:
            record_fail("PF-04", "Optical warming shift", f"Expected Red-Blue delta > 0.10, got {warm_delta:.4f}")
            return
        record_pass("PF-04", "Optical warming shift (Warming 85)", f"R={p_warm[0]:.3f} > B={p_warm[2]:.3f} (delta +{warm_delta:.3f})")

        # Remove filter layer
        image.remove_layer(filter_layer)

        # 11c: Optical cooling shift (Cooling Filter 80: Blue > Red on neutral canvas)
        cfg_cool = proc.create_config()
        cfg_cool.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cool.set_property("image", image)
        cfg_cool.set_property("preset", "cooling-80")
        cfg_cool.set_property("density", 25.0)
        cfg_cool.set_property("preserve-luminosity", True)
        cfg_cool.set_property("add-mask", False)

        proc.run(cfg_cool)
        filter_cool = image.get_layers()[0]
        flat_c = image.duplicate().flatten()
        p_cool = flat_c.get_pixel(50, 50).get_rgba()
        flat_c.delete()

        cool_delta = p_cool[2] - p_cool[0]
        if cool_delta < 0.15:
            record_fail("PF-05", "Optical cooling shift", f"Expected Blue-Red delta > 0.15, got {cool_delta:.4f}")
            return
        record_pass("PF-05", "Optical cooling shift (Cooling 80)", f"B={p_cool[2]:.3f} > R={p_cool[0]:.3f} (delta +{cool_delta:.3f})")

        # 11d: Density scaling response (75% density vs 25% density)
        image.remove_layer(filter_cool)
        cfg_dense = proc.create_config()
        cfg_dense.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_dense.set_property("image", image)
        cfg_dense.set_property("preset", "cooling-80")
        cfg_dense.set_property("density", 75.0)
        cfg_dense.set_property("preserve-luminosity", True)
        cfg_dense.set_property("add-mask", False)

        proc.run(cfg_dense)
        filter_dense = image.get_layers()[0]
        flat_d = image.duplicate().flatten()
        p_dense = flat_d.get_pixel(50, 50).get_rgba()
        flat_d.delete()

        dense_delta = p_dense[2] - p_dense[0]
        if dense_delta <= cool_delta:
            record_fail("PF-06", "Density scaling response", f"Expected 75% delta ({dense_delta:.4f}) > 25% delta ({cool_delta:.4f})")
            return
        record_pass("PF-06", "Density scaling response", f"25% delta +{cool_delta:.3f} -> 75% delta +{dense_delta:.3f}")

        # 11e: Non-preserve luminosity mode (Soft Light mode for physical glass absorption)
        image.remove_layer(filter_dense)
        cfg_sl = proc.create_config()
        cfg_sl.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sl.set_property("image", image)
        cfg_sl.set_property("preset", "amber")
        cfg_sl.set_property("density", 40.0)
        cfg_sl.set_property("preserve-luminosity", False)
        cfg_sl.set_property("add-mask", False)

        proc.run(cfg_sl)
        filter_sl = image.get_layers()[0]
        if filter_sl.get_mode() != Gimp.LayerMode.SOFTLIGHT:
            record_fail("PF-07", "Non-preserve luminosity mode", f"Expected SOFTLIGHT ({int(Gimp.LayerMode.SOFTLIGHT)}), got {filter_sl.get_mode()}")
            return
        record_pass("PF-07", "Non-preserve luminosity mode", f"Soft Light absorption mode ({filter_sl.get_mode()})")

        # 11f: Non-destructive base layer invariance
        p_base_after = base.get_pixel(50, 50).get_rgba()
        base_diff = max(abs(p_base_after[i] - p_base[i]) for i in range(3))
        if base_diff > 0.000001:
            record_fail("PF-08", "Non-destructive invariance", f"Base layer altered by {base_diff:.6f} > 0")
            return
        record_pass("PF-08", "Non-destructive layer preservation", f"Base pixels 100% untouched (diff {base_diff:.6f})")

    except Exception as e:
        record_fail("PF-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 12: Non-Destructive Vibrance & Smart Saturation (Phase 17)
# ==============================================================================
def test_vibrance():
    print("\n--- Test Suite 12: Non-Destructive Vibrance & Smart Saturation ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-vibrance")
    if proc is None:
        record_fail("VIB-01", "Procedure lookup", "Procedure not found")
        return

    image = Gimp.Image.new(100, 100, Gimp.ImageBaseType.RGB)
    try:
        # Base layer with muted cyan on left, saturated red on right
        base = Gimp.Layer.new(image, "Base", 100, 100, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)

        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.4, 0.5, 0.52)"))
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 10, 10, 40, 80)
        base.edit_fill(Gimp.FillType.FOREGROUND)

        Gimp.context_set_foreground(Gegl.Color.new("rgb(1.0, 0.1, 0.1)"))
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 50, 10, 40, 80)
        base.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(image)

        p_base_muted = base.get_pixel(30, 50).get_rgba()
        p_base_sat = base.get_pixel(70, 50).get_rgba()
        spread_base_muted = max(p_base_muted[:3]) - min(p_base_muted[:3])
        spread_base_sat = max(p_base_sat[:3]) - min(p_base_sat[:3])

        # 12a: Run default Vibrance (+25 Vibrance, 0 Saturation)
        cfg_def = proc.create_config()
        cfg_def.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_def.set_property("image", image)
        cfg_def.set_property("preset", "default")
        cfg_def.set_property("opacity", 100.0)
        cfg_def.set_property("add-mask", True)

        res = proc.run(cfg_def)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("VIB-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("VIB-01", "Execution status", "SUCCESS")

        vib_layer = image.get_layers()[0]
        if vib_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("VIB-02", "Layer mode", f"Expected NORMAL ({int(Gimp.LayerMode.NORMAL)}), got {vib_layer.get_mode()}")
            return
        record_pass("VIB-02", "Layer mode & name", f"{vib_layer.get_name()} ({vib_layer.get_mode()})")

        # Verify layer mask attachment
        mask = vib_layer.get_mask()
        if mask is None:
            record_fail("VIB-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("VIB-03", "Layer mask attachment", "Reveal-all mask attached")

        # 12b: Intelligent saturation boost for muted tones
        p_vib_muted = vib_layer.get_pixel(30, 50).get_rgba()
        p_vib_sat = vib_layer.get_pixel(70, 50).get_rgba()
        spread_vib_muted = max(p_vib_muted[:3]) - min(p_vib_muted[:3])
        spread_vib_sat = max(p_vib_sat[:3]) - min(p_vib_sat[:3])

        muted_boost = spread_vib_muted - spread_base_muted
        sat_boost = spread_vib_sat - spread_base_sat

        if muted_boost < 0.25:
            record_fail("VIB-04", "Muted color boost", f"Expected muted boost > 0.25, got {muted_boost:.4f}")
            return
        record_pass("VIB-04", "Muted color saturation boost", f"Base spread {spread_base_muted:.3f} -> Vibrance spread {spread_vib_muted:.3f} (delta +{muted_boost:.3f})")

        # 12c: Saturated tone protection (muted boost should be > 2x saturated boost)
        if muted_boost <= (sat_boost * 2.0):
            record_fail("VIB-05", "Saturated tone protection", f"Muted boost {muted_boost:.4f} not > 2x saturated boost {sat_boost:.4f}")
            return
        record_pass("VIB-05", "Saturated tone protection ratio", f"Muted boost +{muted_boost:.3f} vs Saturated boost +{sat_boost:.3f} (protection ratio {muted_boost/max(0.001, sat_boost):.1f}x)")

        # 12d: Uniform full desaturation test (custom saturation=-100)
        image.remove_layer(vib_layer)
        cfg_desat = proc.create_config()
        cfg_desat.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_desat.set_property("image", image)
        cfg_desat.set_property("preset", "custom")
        cfg_desat.set_property("vibrance", 0.0)
        cfg_desat.set_property("saturation", -100.0)
        cfg_desat.set_property("opacity", 100.0)
        cfg_desat.set_property("add-mask", False)

        proc.run(cfg_desat)
        desat_layer = image.get_layers()[0]
        p_desat = desat_layer.get_pixel(70, 50).get_rgba()
        desat_spread = max(p_desat[:3]) - min(p_desat[:3])

        if desat_spread > 0.000001:
            record_fail("VIB-06", "Full desaturation response", f"Chromatic spread {desat_spread:.6f} > 0 on -100 saturation")
            return
        record_pass("VIB-06", "Full desaturation response", f"Saturation -100 produces exact monochrome (spread {desat_spread:.6f})")

        # 12e: Non-destructive base layer invariance
        p_base_after = base.get_pixel(30, 50).get_rgba()
        base_diff = max(abs(p_base_after[i] - p_base_muted[i]) for i in range(3))
        if base_diff > 0.000001:
            record_fail("VIB-07", "Non-destructive invariance", f"Base layer altered by {base_diff:.6f} > 0")
            return
        record_pass("VIB-07", "Non-destructive layer preservation", f"Base pixels 100% untouched (diff {base_diff:.6f})")

    except Exception as e:
        record_fail("VIB-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 13: Non-Destructive Color Balance & Tonal Grading (Phase 18)
# ==============================================================================
def test_color_balance():
    print("\n--- Test Suite 13: Non-Destructive Color Balance & Tonal Grading ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-color-balance")
    if proc is None:
        record_fail("CB-01", "Procedure lookup", "Procedure not found")
        return

    image = Gimp.Image.new(120, 100, Gimp.ImageBaseType.RGB)
    try:
        # Base layer with 3 tonal zones:
        # 1. Deep shadows (10..35): rgb(0.06, 0.06, 0.06)
        # 2. Midtones (45..75): rgb(0.50, 0.50, 0.50)
        # 3. Highlights (85..110): rgb(0.85, 0.85, 0.85)
        base = Gimp.Layer.new(image, "Base", 120, 100, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)

        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.06, 0.06, 0.06)"))
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 10, 10, 25, 80)
        base.edit_fill(Gimp.FillType.FOREGROUND)

        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.50, 0.50, 0.50)"))
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 45, 10, 30, 80)
        base.edit_fill(Gimp.FillType.FOREGROUND)

        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.85, 0.85, 0.85)"))
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 85, 10, 25, 80)
        base.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(image)

        p_base_sh = base.get_pixel(20, 50).get_rgba()
        p_base_mid = base.get_pixel(60, 50).get_rgba()
        p_base_hl = base.get_pixel(95, 50).get_rgba()

        # 13a: Run Teal & Orange preset
        cfg_to = proc.create_config()
        cfg_to.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_to.set_property("image", image)
        cfg_to.set_property("preset", "teal-orange")
        cfg_to.set_property("preserve-luminosity", True)
        cfg_to.set_property("opacity", 100.0)
        cfg_to.set_property("add-mask", True)

        res = proc.run(cfg_to)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("CB-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("CB-01", "Execution status", "SUCCESS")

        cb_layer = image.get_layers()[0]
        if cb_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("CB-02", "Layer mode", f"Expected NORMAL ({int(Gimp.LayerMode.NORMAL)}), got {cb_layer.get_mode()}")
            return
        record_pass("CB-02", "Layer mode & name", f"{cb_layer.get_name()} ({cb_layer.get_mode()})")

        # Verify layer mask attachment
        mask = cb_layer.get_mask()
        if mask is None:
            record_fail("CB-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("CB-03", "Layer mask attachment", "Reveal-all mask attached")

        # 13b: Cinematic Teal & Orange tonal split:
        # Shadows shift to Teal (Blue > Red)
        p_sh = cb_layer.get_pixel(20, 50).get_rgba()
        sh_teal_delta = p_sh[2] - p_sh[0]
        if sh_teal_delta < 0.05:
            record_fail("CB-04", "Shadows teal shift", f"Expected Blue > Red (delta > 0.05), got R={p_sh[0]:.3f}, B={p_sh[2]:.3f} (delta {sh_teal_delta:.3f})")
            return
        record_pass("CB-04", "Shadows teal shift", f"Teal shadows: B={p_sh[2]:.3f} > R={p_sh[0]:.3f} (delta +{sh_teal_delta:.3f})")

        # Midtones shift to Warm Orange (Red > Blue)
        p_mid = cb_layer.get_pixel(60, 50).get_rgba()
        mid_warm_delta = p_mid[0] - p_mid[2]
        if mid_warm_delta < 0.25:
            record_fail("CB-05", "Midtones warm shift", f"Expected Red > Blue (delta > 0.25), got R={p_mid[0]:.3f}, B={p_mid[2]:.3f} (delta {mid_warm_delta:.3f})")
            return
        record_pass("CB-05", "Midtones warm orange shift", f"Warm midtones: R={p_mid[0]:.3f} > B={p_mid[2]:.3f} (delta +{mid_warm_delta:.3f})")

        # Highlights shift to Warm Amber (Red > Blue)
        p_hl = cb_layer.get_pixel(95, 50).get_rgba()
        hl_warm_delta = p_hl[0] - p_hl[2]
        if hl_warm_delta < 0.15:
            record_fail("CB-06", "Highlights golden shift", f"Expected Red > Blue (delta > 0.15), got R={p_hl[0]:.3f}, B={p_hl[2]:.3f} (delta {hl_warm_delta:.3f})")
            return
        record_pass("CB-06", "Highlights golden amber shift", f"Golden highlights: R={p_hl[0]:.3f} > B={p_hl[2]:.3f} (delta +{hl_warm_delta:.3f})")

        # 13c: Custom tonal sliders on separate canvas
        image.remove_layer(cb_layer)
        cfg_custom = proc.create_config()
        cfg_custom.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_custom.set_property("image", image)
        cfg_custom.set_property("preset", "custom")
        cfg_custom.set_property("tonal-range", "shadows")
        cfg_custom.set_property("cyan-red", -40.0)
        cfg_custom.set_property("magenta-green", 0.0)
        cfg_custom.set_property("yellow-blue", 40.0)
        cfg_custom.set_property("preserve-luminosity", True)
        cfg_custom.set_property("opacity", 100.0)
        cfg_custom.set_property("add-mask", False)

        proc.run(cfg_custom)
        custom_layer = image.get_layers()[0]
        p_c_sh = custom_layer.get_pixel(20, 50).get_rgba()
        if not (p_c_sh[2] > p_c_sh[0]):
            record_fail("CB-07", "Custom tonal range control", f"Expected Blue > Red in custom shadows, got R={p_c_sh[0]:.3f}, B={p_c_sh[2]:.3f}")
            return
        record_pass("CB-07", "Custom tonal range control", f"Custom shadow blue shift: B={p_c_sh[2]:.3f} > R={p_c_sh[0]:.3f}")

        # 13d: Non-destructive base layer invariance
        p_base_after = base.get_pixel(20, 50).get_rgba()
        base_diff = max(abs(p_base_after[i] - p_base_sh[i]) for i in range(3))
        if base_diff > 0.000001:
            record_fail("CB-08", "Non-destructive invariance", f"Base layer altered by {base_diff:.6f} > 0")
            return
        record_pass("CB-08", "Non-destructive layer preservation", f"Base pixels 100% untouched (diff {base_diff:.6f})")

    except Exception as e:
        record_fail("CB-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================
def run_all_tests():
    print("=" * 70)
    print("PhotoGIMP End-to-End Plugin Suite Regression Test Runner")
    print("=" * 70)

    start_time = time.time()

    test_pdb_registration()
    test_frequency_separation()
    test_luminosity_masks()
    test_dodge_burn_layer()
    test_high_pass_sharpen()
    test_quick_export()
    test_vignette_lighting()
    test_depth_blur()
    test_shadow_highlight()
    test_black_and_white()
    test_photo_filter()
    test_vibrance()
    test_color_balance()


    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print("TEST SUITE SUMMARY")
    print("=" * 70)
    print(f"Total Tests Executed : {TOTAL_TESTS}")
    print(f"Tests Passed         : {PASSED_TESTS}")
    print(f"Tests Failed         : {FAILED_TESTS}")
    print(f"Elapsed Time         : {elapsed:.2f}s")

    if FAILED_TESTS > 0:
        print("\nFailures:")
        for fid, name, err in FAILURES:
            print(f"  - [{fid}] {name}: {err}")
        print("\nRESULT: FAILED")
        raise RuntimeError(f"{FAILED_TESTS} tests failed in plugin regression suite")
    else:
        print("\nRESULT: ALL TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_all_tests()
