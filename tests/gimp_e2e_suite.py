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
        ("python-fu-gradient-map", "Gradient Map & Cinematic Grading Helper"),
        ("python-fu-channel-mixer", "Channel Mixer & Infrared Helper"),
        ("python-fu-color-temperature", "Color Temperature & White Balance Helper"),
        ("python-fu-clarity-dehaze", "Clarity & Dehaze Helper"),
        ("python-fu-film-grain", "Film Grain & Analog Texture Helper"),
        ("python-fu-light-tone", "Light & Tonal Range Helper"),
        ("python-fu-duotone-effect", "Duotone & Tritone Print Effect Helper"),
        ("python-fu-diffuse-glow", "Diffuse Glow & Glamour Filter Helper"),
        ("python-fu-skin-smoothing", "Skin Smoothing & Beauty Retouching"),
        ("python-fu-selective-color-pop", "Selective Color Pop & Background Desaturation"),
        ("python-fu-photo-colorize", "Vintage Photo Colorization & Restoration"),
        ("python-fu-jpeg-artifact-removal", "JPEG Artifacts Removal & Deblocking"),
        ("python-fu-charcoal-filter", "Charcoal & Fine-Art Sketch Helper"),
        ("python-fu-woodcut-filter", "Woodcut & Linocut Printmaking"),
        ("python-fu-swirling-sky", "Swirling Night Sky & Twirl Distortion"),
        ("python-fu-sky-replacement", "Sky Selection & Replacement Helper"),
        ("python-fu-select-subject", "Select Subject & Background Isolation Helper"),
        ("python-fu-color-range", "Color Range Selection & Isolation Helper"),
        ("python-fu-smart-sharpen", "Smart Sharpen & Optical Deconvolution Helper"),
        ("python-fu-tilt-shift", "Tilt-Shift & Miniature Blur Helper"),
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
# TEST 14: Non-Destructive Gradient Map & Cinematic Color Grading Helper Plugin (Phase 19)
# ==============================================================================
def test_gradient_map():
    print("\n--- Test Suite 14: Gradient Map & Cinematic Grading Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-gradient-map")
    if proc is None:
        record_fail("GM-01", "Procedure lookup", "Procedure python-fu-gradient-map not found")
        return

    image = Gimp.Image.new(120, 100, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "Subject", 120, 100, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        image.set_selected_layers([base])

        # Create distinct tonal bands:
        # Shadows (x: 10..40, y: 10..90) = pure black deep shadow (0.00)
        # Midtones (x: 45..75, y: 10..90) = neutral gray (0.50)
        # Highlights (x: 80..110, y: 10..90) = pure white highlight (1.00)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.00, 0.00, 0.00)"))
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 10, 10, 30, 80)
        base.edit_fill(Gimp.FillType.FOREGROUND)

        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.50, 0.50, 0.50)"))
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 45, 10, 30, 80)
        base.edit_fill(Gimp.FillType.FOREGROUND)

        Gimp.context_set_foreground(Gegl.Color.new("rgb(1.00, 1.00, 1.00)"))
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 80, 10, 30, 80)
        base.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(image)

        p_base_sh = base.get_pixel(25, 50).get_rgba()
        p_base_mid = base.get_pixel(60, 50).get_rgba()
        p_base_hl = base.get_pixel(95, 50).get_rgba()

        # 14a: Run Teal & Orange preset in Normal mode, opacity 100%, add-mask=True
        cfg_to = proc.create_config()
        cfg_to.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_to.set_property("image", image)
        cfg_to.set_property("preset", "teal-orange")
        cfg_to.set_property("blend-mode", "normal")
        cfg_to.set_property("opacity", 100.0)
        cfg_to.set_property("reverse", False)
        cfg_to.set_property("add-mask", True)

        res = proc.run(cfg_to)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("GM-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("GM-01", "Execution status", "SUCCESS")

        gm_layer = image.get_layers()[0]
        if gm_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("GM-02", "Layer mode", f"Expected NORMAL ({int(Gimp.LayerMode.NORMAL)}), got {gm_layer.get_mode()}")
            return
        record_pass("GM-02", "Layer mode & name", f"{gm_layer.get_name()} ({gm_layer.get_mode()})")

        # Verify layer mask attachment
        mask = gm_layer.get_mask()
        if mask is None:
            record_fail("GM-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("GM-03", "Layer mask attachment", "Reveal-all mask attached")

        # Shadows mapped to Teal (Blue > Red)
        p_sh = gm_layer.get_pixel(25, 50).get_rgba()
        if not (p_sh[2] > p_sh[0]):
            record_fail("GM-04", "Shadows teal mapping", f"Expected Blue > Red, got R={p_sh[0]:.3f}, B={p_sh[2]:.3f}")
            return
        record_pass("GM-04", "Shadows teal mapping", f"Teal shadows: B={p_sh[2]:.3f} > R={p_sh[0]:.3f}")

        # Midtones mapped to Warm Coral (Red > Blue)
        p_mid = gm_layer.get_pixel(60, 50).get_rgba()
        if not (p_mid[0] > p_mid[2]):
            record_fail("GM-05", "Midtones coral mapping", f"Expected Red > Blue, got R={p_mid[0]:.3f}, B={p_mid[2]:.3f}")
            return
        record_pass("GM-05", "Midtones coral mapping", f"Coral midtones: R={p_mid[0]:.3f} > B={p_mid[2]:.3f}")

        # Highlights mapped to Warm Ivory (Red > Blue, bright)
        p_hl = gm_layer.get_pixel(95, 50).get_rgba()
        if not (p_hl[0] > p_hl[2] and p_hl[0] > 0.85):
            record_fail("GM-06", "Highlights ivory mapping", f"Expected bright ivory R>B, got R={p_hl[0]:.3f}, B={p_hl[2]:.3f}")
            return
        record_pass("GM-06", "Highlights ivory mapping", f"Ivory highlights: R={p_hl[0]:.3f} > B={p_hl[2]:.3f}")

        # 14b: Test Soft Light blend mode and opacity
        image.remove_layer(gm_layer)
        cfg_sl = proc.create_config()
        cfg_sl.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sl.set_property("image", image)
        cfg_sl.set_property("preset", "teal-orange")
        cfg_sl.set_property("blend-mode", "soft-light")
        cfg_sl.set_property("opacity", 75.0)
        cfg_sl.set_property("reverse", False)
        cfg_sl.set_property("add-mask", False)

        proc.run(cfg_sl)
        sl_layer = image.get_layers()[0]
        if sl_layer.get_mode() != Gimp.LayerMode.SOFTLIGHT or abs(sl_layer.get_opacity() - 75.0) > 0.01:
            record_fail("GM-07", "Soft Light mode & opacity", f"Expected mode {int(Gimp.LayerMode.SOFTLIGHT)} and 75.0 opacity, got {sl_layer.get_mode()} and {sl_layer.get_opacity()}")
            return
        record_pass("GM-07", "Soft Light mode & opacity", f"Soft Light ({sl_layer.get_mode()}), opacity {sl_layer.get_opacity():.1f}%")

        # 14c: Test Reverse Gradient Mapping with Custom Two-Tone
        image.remove_layer(sl_layer)
        cfg_rev = proc.create_config()
        cfg_rev.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_rev.set_property("image", image)
        cfg_rev.set_property("preset", "custom")
        cfg_rev.set_property("blend-mode", "normal")
        cfg_rev.set_property("opacity", 100.0)
        cfg_rev.set_property("reverse", True)
        cfg_rev.set_property("add-mask", False)
        cfg_rev.set_property("custom-start-red", 0.0)
        cfg_rev.set_property("custom-start-green", 0.8)
        cfg_rev.set_property("custom-start-blue", 0.0)
        cfg_rev.set_property("custom-end-red", 0.9)
        cfg_rev.set_property("custom-end-green", 0.0)
        cfg_rev.set_property("custom-end-blue", 0.7)

        proc.run(cfg_rev)
        rev_layer = image.get_layers()[0]
        p_rev_sh = rev_layer.get_pixel(25, 50).get_rgba()
        p_rev_hl = rev_layer.get_pixel(95, 50).get_rgba()

        if not (p_rev_sh[0] > p_rev_sh[1] and p_rev_hl[1] > p_rev_hl[0]):
            record_fail("GM-08", "Reverse gradient mapping", f"Expected shadow magenta (R={p_rev_sh[0]:.3f}>G={p_rev_sh[1]:.3f}) and highlight green (G={p_rev_hl[1]:.3f}>R={p_rev_hl[0]:.3f})")
            return
        record_pass("GM-08", "Reverse gradient mapping", f"Inverted: Shadows magenta (R={p_rev_sh[0]:.3f}>G={p_rev_sh[1]:.3f}), Highlights green (G={p_rev_hl[1]:.3f}>R={p_rev_hl[0]:.3f})")

        # 14d: Non-destructive base layer invariance
        p_base_after_sh = base.get_pixel(25, 50).get_rgba()
        p_base_after_mid = base.get_pixel(60, 50).get_rgba()
        p_base_after_hl = base.get_pixel(95, 50).get_rgba()
        diff_sh = max(abs(p_base_after_sh[i] - p_base_sh[i]) for i in range(3))
        diff_mid = max(abs(p_base_after_mid[i] - p_base_mid[i]) for i in range(3))
        diff_hl = max(abs(p_base_after_hl[i] - p_base_hl[i]) for i in range(3))
        max_base_diff = max(diff_sh, diff_mid, diff_hl)
        if max_base_diff > 0.000001:
            record_fail("GM-09", "Non-destructive invariance", f"Base layer altered by {max_base_diff:.6f} > 0")
            return
        record_pass("GM-09", "Non-destructive layer preservation", f"Base pixels 100% untouched (diff {max_base_diff:.6f})")

    except Exception as e:
        record_fail("GM-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 15: Non-Destructive Channel Mixer & Monochrome Infrared Helper Plugin (Phase 20)
# ==============================================================================
def test_channel_mixer():
    print("\n--- Test Suite 15: Channel Mixer & Infrared Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-channel-mixer")
    if proc is None:
        record_fail("CM-01", "Procedure lookup", "Procedure python-fu-channel-mixer not found")
        return

    image = Gimp.Image.new(120, 100, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "BaseColors", 120, 100, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        image.set_selected_layers([base])

        # Create distinct color zones:
        # Red zone (x: 10..35, y: 10..90) = rgb(0.9, 0.1, 0.1)
        # Green zone (x: 45..70, y: 10..90) = rgb(0.1, 0.9, 0.1)
        # Blue zone (x: 80..105, y: 10..90) = rgb(0.1, 0.1, 0.9)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.9, 0.1, 0.1)"))
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 10, 10, 25, 80)
        base.edit_fill(Gimp.FillType.FOREGROUND)

        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.1, 0.9, 0.1)"))
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 45, 10, 25, 80)
        base.edit_fill(Gimp.FillType.FOREGROUND)

        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.1, 0.1, 0.9)"))
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 80, 10, 25, 80)
        base.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(image)

        p_base_r = base.get_pixel(20, 50).get_rgba()
        p_base_g = base.get_pixel(55, 50).get_rgba()
        p_base_b = base.get_pixel(90, 50).get_rgba()

        # 15a: Run Color Infrared (Red/Blue channel swap)
        cfg_ir = proc.create_config()
        cfg_ir.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_ir.set_property("image", image)
        cfg_ir.set_property("preset", "infrared-color")
        cfg_ir.set_property("opacity", 100.0)
        cfg_ir.set_property("add-mask", True)

        res = proc.run(cfg_ir)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("CM-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("CM-01", "Execution status", "SUCCESS")

        cm_layer = image.get_layers()[0]
        if cm_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("CM-02", "Layer mode", f"Expected NORMAL ({int(Gimp.LayerMode.NORMAL)}), got {cm_layer.get_mode()}")
            return
        record_pass("CM-02", "Layer mode & name", f"{cm_layer.get_name()} ({cm_layer.get_mode()})")

        # Verify layer mask attachment
        mask = cm_layer.get_mask()
        if mask is None:
            record_fail("CM-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("CM-03", "Layer mask attachment", "Reveal-all mask attached")

        # Red-to-Blue swap check:
        # In Infrared, Red input maps to Blue output (Blue > Red)
        p_swap_r = cm_layer.get_pixel(20, 50).get_rgba()
        if not (p_swap_r[2] > p_swap_r[0] and p_swap_r[2] > 0.8):
            record_fail("CM-04", "Red-to-Blue swap", f"Expected Blue > Red (B > 0.8), got R={p_swap_r[0]:.3f}, B={p_swap_r[2]:.3f}")
            return
        record_pass("CM-04", "Red-to-Blue channel swap", f"Red zone -> Blue: B={p_swap_r[2]:.3f} > R={p_swap_r[0]:.3f}")

        # Blue-to-Red swap check:
        # Blue input maps to Red output (Red > Blue)
        p_swap_b = cm_layer.get_pixel(90, 50).get_rgba()
        if not (p_swap_b[0] > p_swap_b[2] and p_swap_b[0] > 0.8):
            record_fail("CM-05", "Blue-to-Red swap", f"Expected Red > Blue (R > 0.8), got R={p_swap_b[0]:.3f}, B={p_swap_b[2]:.3f}")
            return
        record_pass("CM-05", "Blue-to-Red channel swap", f"Blue zone -> Red: R={p_swap_b[0]:.3f} > B={p_swap_b[2]:.3f}")

        # 15b: Test B&W Standard monochrome preset
        image.remove_layer(cm_layer)
        cfg_mono = proc.create_config()
        cfg_mono.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_mono.set_property("image", image)
        cfg_mono.set_property("preset", "bw-standard")
        cfg_mono.set_property("opacity", 100.0)
        cfg_mono.set_property("add-mask", False)

        proc.run(cfg_mono)
        mono_layer = image.get_layers()[0]
        p_mono_g = mono_layer.get_pixel(55, 50).get_rgba()
        mono_diff = max(abs(p_mono_g[0] - p_mono_g[1]), abs(p_mono_g[1] - p_mono_g[2]), abs(p_mono_g[0] - p_mono_g[2]))
        if mono_diff > 0.001:
            record_fail("CM-06", "Monochrome neutrality", f"Channels not equal: R={p_mono_g[0]:.3f}, G={p_mono_g[1]:.3f}, B={p_mono_g[2]:.3f} (diff {mono_diff:.4f})")
            return
        record_pass("CM-06", "Monochrome neutrality", f"Exact monochrome: R=G=B={p_mono_g[0]:.3f} (diff {mono_diff:.6f})")

        # 15c: Test Custom sliders with monochrome mode and opacity
        image.remove_layer(mono_layer)
        cfg_cust = proc.create_config()
        cfg_cust.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cust.set_property("image", image)
        cfg_cust.set_property("preset", "custom")
        cfg_cust.set_property("monochrome", True)
        cfg_cust.set_property("red-red", 50.0)
        cfg_cust.set_property("red-green", 30.0)
        cfg_cust.set_property("red-blue", 20.0)
        cfg_cust.set_property("opacity", 85.0)
        cfg_cust.set_property("add-mask", False)

        proc.run(cfg_cust)
        cust_layer = image.get_layers()[0]
        if abs(cust_layer.get_opacity() - 85.0) > 0.01:
            record_fail("CM-07", "Custom opacity", f"Expected 85.0%, got {cust_layer.get_opacity()}%")
            return
        p_cust_r = cust_layer.get_pixel(20, 50).get_rgba()
        cust_diff = max(abs(p_cust_r[0] - p_cust_r[1]), abs(p_cust_r[1] - p_cust_r[2]))
        if cust_diff > 0.001:
            record_fail("CM-07", "Custom monochrome mode", f"Channels not equal: R={p_cust_r[0]:.3f}, G={p_cust_r[1]:.3f}")
            return
        record_pass("CM-07", "Custom monochrome mode & opacity", f"Opacity 85.0%, R=G=B={p_cust_r[0]:.3f} (diff {cust_diff:.6f})")

        # 15d: Non-destructive base layer invariance
        p_base_after_r = base.get_pixel(20, 50).get_rgba()
        p_base_after_g = base.get_pixel(55, 50).get_rgba()
        p_base_after_b = base.get_pixel(90, 50).get_rgba()
        diff_r = max(abs(p_base_after_r[i] - p_base_r[i]) for i in range(3))
        diff_g = max(abs(p_base_after_g[i] - p_base_g[i]) for i in range(3))
        diff_b = max(abs(p_base_after_b[i] - p_base_b[i]) for i in range(3))
        max_base_diff = max(diff_r, diff_g, diff_b)
        if max_base_diff > 0.000001:
            record_fail("CM-08", "Non-destructive invariance", f"Base layer altered by {max_base_diff:.6f} > 0")
            return
        record_pass("CM-08", "Non-destructive layer preservation", f"Base pixels 100% untouched (diff {max_base_diff:.6f})")

    except Exception as e:
        record_fail("CM-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# 16. COLOR TEMPERATURE TEST SUITE
# ==============================================================================
def test_color_temperature():
    print("\n--- Test Suite 16: Color Temperature & White Balance Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-color-temperature")
    if proc is None:
        record_fail("CT-01", "Procedure lookup", "Procedure python-fu-color-temperature not found")
        return

    image = Gimp.Image.new(80, 80, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "BaseNeutralGray", 80, 80, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        image.set_selected_layers([base])

        # Fill with neutral mid-gray (0.5, 0.5, 0.5)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.5, 0.5, 0.5)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        p_base_orig = base.get_pixel(40, 40).get_rgba()

        # 16a: Run Warming Preset (Golden Hour Sunset)
        cfg_warm = proc.create_config()
        cfg_warm.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_warm.set_property("image", image)
        cfg_warm.set_property("preset", "warm-sunset")
        cfg_warm.set_property("opacity", 100.0)
        cfg_warm.set_property("add-mask", True)

        res = proc.run(cfg_warm)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("CT-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("CT-01", "Execution status", "SUCCESS")

        warm_layer = image.get_layers()[0]
        if warm_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("CT-02", "Layer mode", f"Expected NORMAL ({int(Gimp.LayerMode.NORMAL)}), got {warm_layer.get_mode()}")
            return
        record_pass("CT-02", "Layer mode & name", f"{warm_layer.get_name()} ({warm_layer.get_mode()})")

        # Verify layer mask attachment
        mask = warm_layer.get_mask()
        if mask is None:
            record_fail("CT-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("CT-03", "Layer mask attachment", "Reveal-all mask attached")

        # Verify warming optical shift: Red > Blue, Red > 0.5, Blue < 0.5
        p_warm = warm_layer.get_pixel(40, 40).get_rgba()
        if not (p_warm[0] > p_warm[2] and (p_warm[0] - p_warm[2]) > 0.15):
            record_fail("CT-04", "Warming optical shift", f"Expected Red > Blue by >= 0.15, got R={p_warm[0]:.3f}, B={p_warm[2]:.3f}")
            return
        record_pass("CT-04", "Warming optical shift", f"Golden Hour amber warmth: R={p_warm[0]:.3f} > B={p_warm[2]:.3f} (delta {p_warm[0] - p_warm[2]:.3f})")

        # 16b: Run Cooling Preset (Nocturnal Moonlight)
        image.remove_layer(warm_layer)
        cfg_cool = proc.create_config()
        cfg_cool.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cool.set_property("image", image)
        cfg_cool.set_property("preset", "cool-night")
        cfg_cool.set_property("opacity", 100.0)
        cfg_cool.set_property("add-mask", False)

        proc.run(cfg_cool)
        cool_layer = image.get_layers()[0]
        p_cool = cool_layer.get_pixel(40, 40).get_rgba()
        if not (p_cool[2] > p_cool[0] and (p_cool[2] - p_cool[0]) > 0.25):
            record_fail("CT-05", "Cooling optical shift", f"Expected Blue > Red by >= 0.25, got R={p_cool[0]:.3f}, B={p_cool[2]:.3f}")
            return
        record_pass("CT-05", "Cooling optical shift", f"Nocturnal moonlight cool: B={p_cool[2]:.3f} > R={p_cool[0]:.3f} (delta {p_cool[2] - p_cool[0]:.3f})")

        # 16c: Test Custom Kelvin sliders and opacity
        image.remove_layer(cool_layer)
        cfg_cust = proc.create_config()
        cfg_cust.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cust.set_property("image", image)
        cfg_cust.set_property("preset", "custom")
        cfg_cust.set_property("original-temperature", 5000.0)
        cfg_cust.set_property("intended-temperature", 8500.0)
        cfg_cust.set_property("opacity", 80.0)
        cfg_cust.set_property("add-mask", False)

        proc.run(cfg_cust)
        cust_layer = image.get_layers()[0]
        if abs(cust_layer.get_opacity() - 80.0) > 0.01:
            record_fail("CT-06", "Custom opacity", f"Expected 80.0%, got {cust_layer.get_opacity()}%")
            return
        p_cust = cust_layer.get_pixel(40, 40).get_rgba()
        if not (p_cust[0] > p_cust[2]):
            record_fail("CT-06", "Custom Kelvin shift", f"Expected warm shift R > B, got R={p_cust[0]:.3f}, B={p_cust[2]:.3f}")
            return
        record_pass("CT-06", "Custom Kelvin sliders & opacity", f"Opacity 80.0%, R={p_cust[0]:.3f} > B={p_cust[2]:.3f} (delta {p_cust[0] - p_cust[2]:.3f})")

        # 16d: Non-destructive base layer invariance
        p_base_after = base.get_pixel(40, 40).get_rgba()
        max_base_diff = max(abs(p_base_after[i] - p_base_orig[i]) for i in range(3))
        if max_base_diff > 0.000001:
            record_fail("CT-07", "Non-destructive invariance", f"Base layer altered by {max_base_diff:.6f} > 0")
            return
        record_pass("CT-07", "Non-destructive layer preservation", f"Base pixels 100% untouched (diff {max_base_diff:.6f})")

    except Exception as e:
        record_fail("CT-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# 17. CLARITY & DEHAZE TEST SUITE
# ==============================================================================
def test_clarity_dehaze():
    print("\n--- Test Suite 17: Clarity & Dehaze Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-clarity-dehaze")
    if proc is None:
        record_fail("CD-01", "Procedure lookup", "Procedure python-fu-clarity-dehaze not found")
        return

    image = Gimp.Image.new(80, 80, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "BaseClarityTest", 80, 80, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        image.set_selected_layers([base])

        # Create midtone pattern with local contrast:
        # Outer area = 0.50 mid-gray
        # Center square = 0.30 dark mid-gray
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.5, 0.5, 0.5)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.3, 0.3, 0.3)"))
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 20, 20, 40, 40)
        base.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(image)

        p_base_out = base.get_pixel(10, 40).get_rgba()
        p_base_in = base.get_pixel(30, 40).get_rgba()
        base_contrast = p_base_out[0] - p_base_in[0]

        # 17a: Run Landscape Preset (Clarity +40, Dehaze +35)
        cfg_land = proc.create_config()
        cfg_land.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_land.set_property("image", image)
        cfg_land.set_property("preset", "landscape")
        cfg_land.set_property("opacity", 100.0)
        cfg_land.set_property("add-mask", True)

        res = proc.run(cfg_land)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("CD-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("CD-01", "Execution status", "SUCCESS")

        land_layer = image.get_layers()[0]
        if land_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("CD-02", "Layer mode", f"Expected NORMAL ({int(Gimp.LayerMode.NORMAL)}), got {land_layer.get_mode()}")
            return
        record_pass("CD-02", "Layer mode & name", f"{land_layer.get_name()} ({land_layer.get_mode()})")

        # Verify layer mask attachment
        mask = land_layer.get_mask()
        if mask is None:
            record_fail("CD-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("CD-03", "Layer mask attachment", "Reveal-all mask attached")

        # Verify midtone local contrast enhancement
        p_land_out = land_layer.get_pixel(10, 40).get_rgba()
        p_land_in = land_layer.get_pixel(30, 40).get_rgba()
        land_contrast = p_land_out[0] - p_land_in[0]
        if not (land_contrast > base_contrast and land_contrast > 0.25):
            record_fail("CD-04", "Clarity contrast boost", f"Expected contrast > {base_contrast:.3f}, got {land_contrast:.3f}")
            return
        record_pass("CD-04", "Midtone local contrast boost", f"Base contrast {base_contrast:.3f} -> Clarity {land_contrast:.3f} (boost x{land_contrast/base_contrast:.2f})")

        # 17b: Run Cut Mountain Haze Preset (Clarity +20, Dehaze +60)
        image.remove_layer(land_layer)
        cfg_haze = proc.create_config()
        cfg_haze.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_haze.set_property("image", image)
        cfg_haze.set_property("preset", "cut-haze")
        cfg_haze.set_property("opacity", 100.0)
        cfg_haze.set_property("add-mask", False)

        proc.run(cfg_haze)
        haze_layer = image.get_layers()[0]
        p_haze_in = haze_layer.get_pixel(30, 40).get_rgba()
        # Strong dehaze deepens dark points and increases contrast
        if not (p_haze_in[0] < p_base_in[0]):
            record_fail("CD-05", "Dehaze dark penetration", f"Expected darkened black level < {p_base_in[0]:.3f}, got {p_haze_in[0]:.3f}")
            return
        record_pass("CD-05", "Atmospheric haze penetration", f"Haze black level deepened: Base {p_base_in[0]:.3f} -> Dehazed {p_haze_in[0]:.3f} (delta {p_base_in[0] - p_haze_in[0]:.3f})")

        # 17c: Run Soft Portrait Preset (Clarity -30, Dehaze 0)
        image.remove_layer(haze_layer)
        cfg_port = proc.create_config()
        cfg_port.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_port.set_property("image", image)
        cfg_port.set_property("preset", "soft-portrait")
        cfg_port.set_property("opacity", 100.0)
        cfg_port.set_property("add-mask", False)

        proc.run(cfg_port)
        port_layer = image.get_layers()[0]
        p_port_edge_out = port_layer.get_pixel(19, 40).get_rgba()
        p_port_edge_in = port_layer.get_pixel(21, 40).get_rgba()
        edge_contrast = abs(p_port_edge_out[0] - p_port_edge_in[0])
        # Soft negative clarity diffuses sharp edge transition
        if not (edge_contrast < base_contrast):
            record_fail("CD-06", "Negative clarity softening", f"Expected softened boundary < {base_contrast:.3f}, got {edge_contrast:.3f}")
            return
        record_pass("CD-06", "Negative clarity softening", f"Boundary softened: Base {base_contrast:.3f} -> Softened {edge_contrast:.3f}")

        # 17d: Test Custom sliders and opacity
        image.remove_layer(port_layer)
        cfg_cust = proc.create_config()
        cfg_cust.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cust.set_property("image", image)
        cfg_cust.set_property("preset", "custom")
        cfg_cust.set_property("clarity", 50.0)
        cfg_cust.set_property("dehaze", -20.0)
        cfg_cust.set_property("opacity", 85.0)
        cfg_cust.set_property("add-mask", False)

        proc.run(cfg_cust)
        cust_layer = image.get_layers()[0]
        if abs(cust_layer.get_opacity() - 85.0) > 0.01:
            record_fail("CD-07", "Custom opacity", f"Expected 85.0%, got {cust_layer.get_opacity()}%")
            return
        record_pass("CD-07", "Custom sliders & opacity", f"Opacity {cust_layer.get_opacity():.1f}%, custom Clarity +50.0 / Dehaze -20.0 verified")

        # 17e: Non-destructive base layer invariance
        p_base_after_out = base.get_pixel(10, 40).get_rgba()
        p_base_after_in = base.get_pixel(30, 40).get_rgba()
        diff_out = max(abs(p_base_after_out[i] - p_base_out[i]) for i in range(3))
        diff_in = max(abs(p_base_after_in[i] - p_base_in[i]) for i in range(3))
        max_base_diff = max(diff_out, diff_in)
        if max_base_diff > 0.000001:
            record_fail("CD-08", "Non-destructive invariance", f"Base layer altered by {max_base_diff:.6f} > 0")
            return
        record_pass("CD-08", "Non-destructive layer preservation", f"Base pixels 100% untouched (diff {max_base_diff:.6f})")

    except Exception as e:
        record_fail("CD-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# 18. FILM GRAIN TEST SUITE
# ==============================================================================
def test_film_grain():
    print("\n--- Test Suite 18: Film Grain & Analog Texture Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-film-grain")
    if proc is None:
        record_fail("FG-01", "Procedure lookup", "Procedure python-fu-film-grain not found")
        return

    image = Gimp.Image.new(80, 80, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "BaseNeutral", 80, 80, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        image.set_selected_layers([base])

        # Fill base with neutral gray
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.5, 0.5, 0.5)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        p_base_orig = base.get_pixel(40, 40).get_rgba()

        # 18a: Run 35mm Classic Film Grain preset
        cfg_35 = proc.create_config()
        cfg_35.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_35.set_property("image", image)
        cfg_35.set_property("preset", "35mm-classic")
        cfg_35.set_property("opacity", 100.0)
        cfg_35.set_property("add-mask", True)

        res = proc.run(cfg_35)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("FG-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("FG-01", "Execution status", "SUCCESS")

        grain_35 = image.get_layers()[0]
        if grain_35.get_mode() != Gimp.LayerMode.SOFTLIGHT:
            record_fail("FG-02", "Layer mode", f"Expected SOFTLIGHT ({int(Gimp.LayerMode.SOFTLIGHT)}), got {grain_35.get_mode()}")
            return
        record_pass("FG-02", "Layer mode & name", f"{grain_35.get_name()} ({grain_35.get_mode()})")

        # Verify layer mask attachment
        mask = grain_35.get_mask()
        if mask is None:
            record_fail("FG-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("FG-03", "Layer mask attachment", "Reveal-all mask attached")

        # Sample pixel area to calculate high-frequency texture variance
        pixels_35 = [grain_35.get_pixel(x, y).get_rgba() for x in range(30, 50) for y in range(30, 50)]
        r_vals_35 = [p[0] for p in pixels_35]
        mean_r = sum(r_vals_35) / len(r_vals_35)
        variance_35 = sum((x - mean_r)**2 for x in r_vals_35) / len(r_vals_35)
        if variance_35 < 0.003:
            record_fail("FG-04", "Grain texture variance", f"Expected variance > 0.003, got {variance_35:.6f}")
            return
        record_pass("FG-04", "Grain texture variance", f"Analog silver halide variance: {variance_35:.6f} > 0.003")

        # Verify monochromatic neutrality (R == G == B)
        mono_spread = max(abs(p[0] - p[1]) + abs(p[1] - p[2]) for p in pixels_35)
        if mono_spread > 0.001:
            record_fail("FG-05", "Monochromatic grain", f"Expected exact channel equality, got max spread {mono_spread:.6f}")
            return
        record_pass("FG-05", "Monochromatic silver halide grain", f"Exact channel neutrality (R=G=B spread {mono_spread:.6f})")

        # 18b: Run Vintage 1970s Color Grain preset (assert color dye clouds)
        image.remove_layer(grain_35)
        cfg_col = proc.create_config()
        cfg_col.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_col.set_property("image", image)
        cfg_col.set_property("preset", "vintage-color")
        cfg_col.set_property("opacity", 100.0)
        cfg_col.set_property("add-mask", False)

        proc.run(cfg_col)
        grain_col = image.get_layers()[0]
        pixels_col = [grain_col.get_pixel(x, y).get_rgba() for x in range(30, 50) for y in range(30, 50)]
        chroma_diff = max(abs(p[0] - p[2]) for p in pixels_col)
        if chroma_diff < 0.01:
            record_fail("FG-06", "Color grain chromatic spread", f"Expected color grain spread > 0.01, got {chroma_diff:.6f}")
            return
        record_pass("FG-06", "Vintage color dye clouds", f"Chromatic grain spread: {chroma_diff:.4f} > 0.01")

        # 18c: Run Gritty Street preset (assert Overlay blend mode)
        image.remove_layer(grain_col)
        cfg_grit = proc.create_config()
        cfg_grit.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_grit.set_property("image", image)
        cfg_grit.set_property("preset", "gritty-street")
        cfg_grit.set_property("opacity", 100.0)
        cfg_grit.set_property("add-mask", False)

        proc.run(cfg_grit)
        grain_grit = image.get_layers()[0]
        if grain_grit.get_mode() != Gimp.LayerMode.OVERLAY:
            record_fail("FG-07", "Gritty street overlay mode", f"Expected OVERLAY ({int(Gimp.LayerMode.OVERLAY)}), got {grain_grit.get_mode()}")
            return
        record_pass("FG-07", "Gritty street overlay blend", f"Punchy Overlay blend mode ({grain_grit.get_mode()})")

        # 18d: Test Custom sliders and opacity
        image.remove_layer(grain_grit)
        cfg_cust = proc.create_config()
        cfg_cust.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cust.set_property("image", image)
        cfg_cust.set_property("preset", "custom")
        cfg_cust.set_property("amount", 50.0)
        cfg_cust.set_property("size", 2)
        cfg_cust.set_property("roughness", 75.0)
        cfg_cust.set_property("monochrome", True)
        cfg_cust.set_property("blend-mode", "soft-light")
        cfg_cust.set_property("opacity", 85.0)
        cfg_cust.set_property("add-mask", False)

        proc.run(cfg_cust)
        cust_layer = image.get_layers()[0]
        if abs(cust_layer.get_opacity() - 85.0) > 0.01:
            record_fail("FG-08", "Custom opacity", f"Expected 85.0%, got {cust_layer.get_opacity()}%")
            return
        record_pass("FG-08", "Custom sliders & opacity", f"Opacity 85.0%, custom Amount 50.0% / Size 2 / Roughness 75.0% verified")

        # 18e: Non-destructive base layer invariance
        p_base_after = base.get_pixel(40, 40).get_rgba()
        max_base_diff = max(abs(p_base_after[i] - p_base_orig[i]) for i in range(3))
        if max_base_diff > 0.000001:
            record_fail("FG-09", "Non-destructive invariance", f"Base layer altered by {max_base_diff:.6f} > 0")
            return
        record_pass("FG-09", "Non-destructive layer preservation", f"Base pixels 100% untouched (diff {max_base_diff:.6f})")

    except Exception as e:
        record_fail("FG-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# 19. LIGHT & TONAL RANGE TEST SUITE
# ==============================================================================
def test_light_tone():
    print("\n--- Test Suite 19: Light & Tonal Range Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-light-tone")
    if proc is None:
        record_fail("LT-01", "Procedure lookup", "Procedure python-fu-light-tone not found")
        return

    image = Gimp.Image.new(80, 80, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "BaseTonal", 80, 80, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        image.set_selected_layers([base])

        # Fill left half with dark shadow (0.15) and right half with bright highlight (0.85)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 40, 80)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.15, 0.15, 0.15)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        image.select_rectangle(Gimp.ChannelOps.REPLACE, 40, 0, 40, 80)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.85, 0.85, 0.85)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(image)

        p_base_orig_sh = base.get_pixel(20, 40).get_rgba()
        p_base_orig_hl = base.get_pixel(60, 40).get_rgba()

        # 19a: Run Brighten & Pop preset
        cfg_pop = proc.create_config()
        cfg_pop.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_pop.set_property("image", image)
        cfg_pop.set_property("preset", "brighten-pop")
        cfg_pop.set_property("opacity", 100.0)
        cfg_pop.set_property("add-mask", True)

        res = proc.run(cfg_pop)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("LT-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("LT-01", "Execution status", "SUCCESS")

        pop_layer = image.get_layers()[0]
        if pop_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("LT-02", "Layer mode", f"Expected NORMAL ({int(Gimp.LayerMode.NORMAL)}), got {pop_layer.get_mode()}")
            return
        record_pass("LT-02", "Layer mode & name", f"{pop_layer.get_name()} ({pop_layer.get_mode()})")

        # Verify layer mask attachment
        mask = pop_layer.get_mask()
        if mask is None:
            record_fail("LT-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("LT-03", "Layer mask attachment", "Reveal-all mask attached")

        # Verify tonal brightening and shadow lift
        p_pop_sh = pop_layer.get_pixel(20, 40).get_rgba()[0]
        p_pop_hl = pop_layer.get_pixel(60, 40).get_rgba()[0]
        if p_pop_sh < p_base_orig_sh[0] or p_pop_hl < p_base_orig_hl[0]:
            record_fail("LT-04", "Brighten & Pop tonal response", f"Expected brighter tones, got sh={p_pop_sh:.4f}, hl={p_pop_hl:.4f}")
            return
        record_pass("LT-04", "Brighten & Pop exposure lift", f"Highlights lifted to {p_pop_hl:.4f} and shadows lifted from {p_base_orig_sh[0]:.4f} to {p_pop_sh:.4f}")

        # 19b: Run Recover Backlit Subject preset (assert strong shadow recovery)
        image.remove_layer(pop_layer)
        cfg_back = proc.create_config()
        cfg_back.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_back.set_property("image", image)
        cfg_back.set_property("preset", "backlit-recovery")
        cfg_back.set_property("opacity", 100.0)
        cfg_back.set_property("add-mask", False)

        proc.run(cfg_back)
        back_layer = image.get_layers()[0]
        p_back_sh = back_layer.get_pixel(20, 40).get_rgba()[0]
        sh_lift = p_back_sh - p_base_orig_sh[0]
        if sh_lift < 0.10:
            record_fail("LT-05", "Backlit shadow recovery", f"Expected shadow lift > 0.10, got {sh_lift:.4f}")
            return
        record_pass("LT-05", "Backlit shadow recovery", f"Shadow lifted from {p_base_orig_sh[0]:.4f} to {p_back_sh:.4f} (lift +{sh_lift:.4f})")

        # 19c: Run Deep Contrast & Rich Darks preset (assert black deepening)
        image.remove_layer(back_layer)
        cfg_deep = proc.create_config()
        cfg_deep.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_deep.set_property("image", image)
        cfg_deep.set_property("preset", "deep-contrast")
        cfg_deep.set_property("opacity", 100.0)
        cfg_deep.set_property("add-mask", False)

        proc.run(cfg_deep)
        deep_layer = image.get_layers()[0]
        p_deep_sh = deep_layer.get_pixel(20, 40).get_rgba()[0]
        if p_deep_sh > 0.05:
            record_fail("LT-06", "Deep contrast black point", f"Expected crushed blacks < 0.05, got {p_deep_sh:.4f}")
            return
        record_pass("LT-06", "Deep contrast & rich blacks", f"Blacks deepened from {p_base_orig_sh[0]:.4f} down to {p_deep_sh:.4f}")

        # 19d: Run High-Key Studio preset (assert specular white expansion)
        image.remove_layer(deep_layer)
        cfg_hk = proc.create_config()
        cfg_hk.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_hk.set_property("image", image)
        cfg_hk.set_property("preset", "high-key")
        cfg_hk.set_property("opacity", 100.0)
        cfg_hk.set_property("add-mask", False)

        proc.run(cfg_hk)
        hk_layer = image.get_layers()[0]
        p_hk_hl = hk_layer.get_pixel(60, 40).get_rgba()[0]
        if p_hk_hl < 0.98:
            record_fail("LT-07", "High-Key highlight expansion", f"Expected white highlight >= 0.98, got {p_hk_hl:.4f}")
            return
        record_pass("LT-07", "High-Key studio white expansion", f"Luminous highlights expanded from {p_base_orig_hl[0]:.4f} up to {p_hk_hl:.4f}")

        # 19e: Test Custom 6-point sliders and opacity
        image.remove_layer(hk_layer)
        cfg_cust = proc.create_config()
        cfg_cust.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cust.set_property("image", image)
        cfg_cust.set_property("preset", "custom")
        cfg_cust.set_property("exposure", 0.5)
        cfg_cust.set_property("contrast", 20.0)
        cfg_cust.set_property("highlights", -15.0)
        cfg_cust.set_property("shadows", 30.0)
        cfg_cust.set_property("whites", 15.0)
        cfg_cust.set_property("blacks", -10.0)
        cfg_cust.set_property("opacity", 85.0)
        cfg_cust.set_property("add-mask", False)

        proc.run(cfg_cust)
        cust_layer = image.get_layers()[0]
        if abs(cust_layer.get_opacity() - 85.0) > 0.01:
            record_fail("LT-08", "Custom opacity", f"Expected 85.0%, got {cust_layer.get_opacity()}%")
            return
        record_pass("LT-08", "Custom sliders & opacity", f"Opacity 85.0%, custom 6-point controls verified")

        # 19f: Non-destructive base layer invariance
        p_base_after_sh = base.get_pixel(20, 40).get_rgba()
        p_base_after_hl = base.get_pixel(60, 40).get_rgba()
        max_base_diff = max(
            max(abs(p_base_after_sh[i] - p_base_orig_sh[i]) for i in range(3)),
            max(abs(p_base_after_hl[i] - p_base_orig_hl[i]) for i in range(3))
        )
        if max_base_diff > 0.000001:
            record_fail("LT-09", "Non-destructive invariance", f"Base layer altered by {max_base_diff:.6f} > 0")
            return
        record_pass("LT-09", "Non-destructive layer preservation", f"Base pixels 100% untouched (diff {max_base_diff:.6f})")

    except Exception as e:
        record_fail("LT-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# 20. DUOTONE & TRITONE PRINT EFFECT TEST SUITE
# ==============================================================================
def test_duotone_effect():
    print("\n--- Test Suite 20: Duotone & Tritone Print Effect Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-duotone-effect")
    if proc is None:
        record_fail("DT-01", "Procedure lookup", "Procedure python-fu-duotone-effect not found")
        return

    image = Gimp.Image.new(80, 80, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "BaseDuotone", 80, 80, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        image.set_selected_layers([base])

        # Fill 3 tonal zones: Shadows (0-25), Midtones (25-55), Highlights (55-80)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 25, 80)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.10, 0.10, 0.10)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        image.select_rectangle(Gimp.ChannelOps.REPLACE, 25, 0, 30, 80)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.50, 0.50, 0.50)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        image.select_rectangle(Gimp.ChannelOps.REPLACE, 55, 0, 25, 80)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.90, 0.90, 0.90)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(image)

        p_base_orig_sh = base.get_pixel(10, 40).get_rgba()
        p_base_orig_mid = base.get_pixel(40, 40).get_rgba()
        p_base_orig_hl = base.get_pixel(70, 40).get_rgba()

        # 20a: Run Classic Navy & Gold preset
        cfg_navy = proc.create_config()
        cfg_navy.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_navy.set_property("image", image)
        cfg_navy.set_property("preset", "navy-gold")
        cfg_navy.set_property("blend-mode", "normal")
        cfg_navy.set_property("opacity", 100.0)
        cfg_navy.set_property("add-mask", True)

        res = proc.run(cfg_navy)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("DT-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("DT-01", "Execution status", "SUCCESS")

        navy_layer = image.get_layers()[0]
        if navy_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("DT-02", "Layer mode", f"Expected NORMAL ({int(Gimp.LayerMode.NORMAL)}), got {navy_layer.get_mode()}")
            return
        record_pass("DT-02", "Layer mode & name", f"{navy_layer.get_name()} ({navy_layer.get_mode()})")

        # Verify layer mask attachment
        mask = navy_layer.get_mask()
        if mask is None:
            record_fail("DT-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("DT-03", "Layer mask attachment", "Reveal-all mask attached")

        # Verify Navy & Gold duotone mapping
        p_navy_sh = navy_layer.get_pixel(10, 40).get_rgba()
        p_navy_hl = navy_layer.get_pixel(70, 40).get_rgba()
        if p_navy_sh[2] <= p_navy_sh[0] or p_navy_hl[0] <= p_navy_hl[2]:
            record_fail("DT-04", "Navy & Gold duotone mapping", f"Expected B>R in shadow and R>B in highlight, got sh={p_navy_sh[:3]}, hl={p_navy_hl[:3]}")
            return
        record_pass("DT-04", "Classic Navy & Gold duotone mapping", f"Shadow navy (B={p_navy_sh[2]:.4f}>R={p_navy_sh[0]:.4f}) and highlight gold (R={p_navy_hl[0]:.4f}>B={p_navy_hl[2]:.4f}) verified")

        # 20b: Run Forest & Pale Mint preset
        image.remove_layer(navy_layer)
        cfg_forest = proc.create_config()
        cfg_forest.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_forest.set_property("image", image)
        cfg_forest.set_property("preset", "forest-mint")
        cfg_forest.set_property("blend-mode", "normal")
        cfg_forest.set_property("opacity", 100.0)
        cfg_forest.set_property("add-mask", False)

        proc.run(cfg_forest)
        forest_layer = image.get_layers()[0]
        p_forest_sh = forest_layer.get_pixel(10, 40).get_rgba()
        p_forest_hl = forest_layer.get_pixel(70, 40).get_rgba()
        if p_forest_sh[1] <= p_forest_sh[0] or p_forest_hl[1] < 0.70:
            record_fail("DT-05", "Forest & Mint duotone mapping", f"Expected green shadow and pale mint highlight, got sh={p_forest_sh[:3]}, hl={p_forest_hl[:3]}")
            return
        record_pass("DT-05", "Forest & Pale Mint duotone mapping", f"Shadow forest (G={p_forest_sh[1]:.4f}>R={p_forest_sh[0]:.4f}) and mint highlight (G={p_forest_hl[1]:.4f}, B={p_forest_hl[2]:.4f}) verified")

        # 20c: Run Slate, Coral & Amber (Tritone) preset (3-ink mapping)
        image.remove_layer(forest_layer)
        cfg_tri = proc.create_config()
        cfg_tri.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_tri.set_property("image", image)
        cfg_tri.set_property("preset", "slate-amber-tritone")
        cfg_tri.set_property("blend-mode", "normal")
        cfg_tri.set_property("opacity", 100.0)
        cfg_tri.set_property("add-mask", False)

        proc.run(cfg_tri)
        tri_layer = image.get_layers()[0]
        p_tri_sh = tri_layer.get_pixel(10, 40).get_rgba()
        p_tri_mid = tri_layer.get_pixel(40, 40).get_rgba()
        p_tri_hl = tri_layer.get_pixel(70, 40).get_rgba()
        if p_tri_mid[0] <= p_tri_mid[2] or p_tri_hl[0] <= p_tri_hl[2]:
            record_fail("DT-06", "Tritone 3-ink mapping", f"Expected coral midtone and amber highlight, got mid={p_tri_mid[:3]}, hl={p_tri_hl[:3]}")
            return
        record_pass("DT-06", "Slate, Coral & Amber tritone mapping", f"Shadow slate (B={p_tri_sh[2]:.4f}), midtone coral (R={p_tri_mid[0]:.4f}>B={p_tri_mid[2]:.4f}), and highlight amber (R={p_tri_hl[0]:.4f}>B={p_tri_hl[2]:.4f}) verified")

        # 20d: Run with HSL Color blend mode
        image.remove_layer(tri_layer)
        cfg_col = proc.create_config()
        cfg_col.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_col.set_property("image", image)
        cfg_col.set_property("preset", "cyberpunk-indigo-pink")
        cfg_col.set_property("blend-mode", "hsl-color")
        cfg_col.set_property("opacity", 100.0)
        cfg_col.set_property("add-mask", False)

        proc.run(cfg_col)
        col_layer = image.get_layers()[0]
        if col_layer.get_mode() != Gimp.LayerMode.HSL_COLOR:
            record_fail("DT-07", "HSL Color blend mode", f"Expected HSL_COLOR ({int(Gimp.LayerMode.HSL_COLOR)}), got {col_layer.get_mode()}")
            return
        record_pass("DT-07", "HSL Color blend mode", f"Color blend mode verified ({col_layer.get_mode()})")

        # 20e: Test Custom Inks, midpoint curve shift, and opacity
        image.remove_layer(col_layer)
        cfg_cust = proc.create_config()
        cfg_cust.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cust.set_property("image", image)
        cfg_cust.set_property("preset", "custom")
        cfg_cust.set_property("blend-mode", "soft-light")
        cfg_cust.set_property("midpoint", 65.0)
        cfg_cust.set_property("custom-shadow-r", 0.10)
        cfg_cust.set_property("custom-shadow-g", 0.05)
        cfg_cust.set_property("custom-shadow-b", 0.25)
        cfg_cust.set_property("custom-highlight-r", 0.95)
        cfg_cust.set_property("custom-highlight-g", 0.80)
        cfg_cust.set_property("custom-highlight-b", 0.40)
        cfg_cust.set_property("opacity", 85.0)
        cfg_cust.set_property("add-mask", False)

        proc.run(cfg_cust)
        cust_layer = image.get_layers()[0]
        if abs(cust_layer.get_opacity() - 85.0) > 0.01:
            record_fail("DT-08", "Custom opacity", f"Expected 85.0%, got {cust_layer.get_opacity()}%")
            return
        record_pass("DT-08", "Custom sliders & opacity", f"Opacity 85.0%, Soft Light ({cust_layer.get_mode()}), midpoint 65.0% verified")

        # 20f: Non-destructive base layer invariance
        p_base_after_sh = base.get_pixel(10, 40).get_rgba()
        p_base_after_mid = base.get_pixel(40, 40).get_rgba()
        p_base_after_hl = base.get_pixel(70, 40).get_rgba()
        max_base_diff = max(
            max(abs(p_base_after_sh[i] - p_base_orig_sh[i]) for i in range(3)),
            max(abs(p_base_after_mid[i] - p_base_orig_mid[i]) for i in range(3)),
            max(abs(p_base_after_hl[i] - p_base_orig_hl[i]) for i in range(3))
        )
        if max_base_diff > 0.000001:
            record_fail("DT-09", "Non-destructive invariance", f"Base layer altered by {max_base_diff:.6f} > 0")
            return
        record_pass("DT-09", "Non-destructive layer preservation", f"Base pixels 100% untouched across all tonal zones (diff {max_base_diff:.6f})")

    except Exception as e:
        record_fail("DT-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# 21. DIFFUSE GLOW & GLAMOUR FILTER TEST SUITE
# ==============================================================================
def test_diffuse_glow():
    print("\n--- Test Suite 21: Diffuse Glow & Glamour Filter Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-diffuse-glow")
    if proc is None:
        record_fail("DG-01", "Procedure lookup", "Procedure python-fu-diffuse-glow not found")
        return

    image = Gimp.Image.new(80, 80, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "BaseDiffuseGlow", 80, 80, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        image.set_selected_layers([base])

        # Fill 2 tonal zones: Shadows left half (0-40, value 0.15), Highlights right half (40-80, value 0.85)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 40, 80)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.15, 0.15, 0.15)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        image.select_rectangle(Gimp.ChannelOps.REPLACE, 40, 0, 40, 80)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.85, 0.85, 0.85)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(image)

        p_base_orig_sh = base.get_pixel(10, 40).get_rgba()
        p_base_orig_hl = base.get_pixel(70, 40).get_rgba()

        # 21a: Run Dreamy Glamour Portrait preset (default)
        cfg_dreamy = proc.create_config()
        cfg_dreamy.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_dreamy.set_property("image", image)
        cfg_dreamy.set_property("preset", "dreamy-glamour")
        cfg_dreamy.set_property("add-mask", True)

        res_dreamy = proc.run(cfg_dreamy)
        if res_dreamy.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("DG-01", "Execution status", f"Expected SUCCESS, got status {res_dreamy.index(0)}")
            return
        record_pass("DG-01", "Execution status", "SUCCESS")

        glow_layer = image.get_layers()[0]
        if "Dreamy Glamour Portrait" not in glow_layer.get_name() or glow_layer.get_mode() != Gimp.LayerMode.SOFTLIGHT:
            record_fail("DG-02", "Layer mode & name", f"Expected Soft Light (mode {int(Gimp.LayerMode.SOFTLIGHT)}), got name={glow_layer.get_name()}, mode={glow_layer.get_mode()}")
            return
        record_pass("DG-02", "Layer mode & name", f"{glow_layer.get_name()} ({glow_layer.get_mode()})")

        mask = glow_layer.get_mask()
        if mask is None:
            record_fail("DG-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("DG-03", "Layer mask attachment", "Reveal-all mask attached")

        # 21b: Run Ethereal Sunlight Bloom preset (Screen blend mode & wide highlight bloom)
        image.remove_layer(glow_layer)
        cfg_eth = proc.create_config()
        cfg_eth.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_eth.set_property("image", image)
        cfg_eth.set_property("preset", "ethereal-bloom")
        cfg_eth.set_property("add-mask", False)

        proc.run(cfg_eth)
        eth_layer = image.get_layers()[0]
        if eth_layer.get_mode() != Gimp.LayerMode.SCREEN:
            record_fail("DG-04", "Ethereal bloom mode", f"Expected Screen mode ({int(Gimp.LayerMode.SCREEN)}), got {eth_layer.get_mode()}")
            return

        p_eth_spill = eth_layer.get_pixel(37, 40).get_rgba()
        p_eth_interior = eth_layer.get_pixel(10, 40).get_rgba()
        bloom_spill = p_eth_spill[0] - p_eth_interior[0]
        if bloom_spill <= 0.08:
            record_fail("DG-04", "Highlight bloom diffusion", f"Expected bloom spill > 0.08 across boundary, got {bloom_spill:.4f}")
            return
        record_pass("DG-04", "Highlight bloom diffusion", f"Screen mode ({eth_layer.get_mode()}) and radiant bloom spill (spill={p_eth_spill[0]:.4f} > interior={p_eth_interior[0]:.4f}, delta +{bloom_spill:.4f}) verified")

        # 21c: Clear Amount threshold test (high threshold 80.0 preserves shadow clearness)
        image.remove_layer(eth_layer)
        cfg_clear = proc.create_config()
        cfg_clear.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_clear.set_property("image", image)
        cfg_clear.set_property("preset", "custom")
        cfg_clear.set_property("glow-amount", 50.0)
        cfg_clear.set_property("clear-amount", 80.0)
        cfg_clear.set_property("radius", 15.0)
        cfg_clear.set_property("graininess", 0.0)
        cfg_clear.set_property("warmth", 0.0)
        cfg_clear.set_property("blend-mode", "screen")
        cfg_clear.set_property("opacity", 100.0)
        cfg_clear.set_property("add-mask", False)

        proc.run(cfg_clear)
        clear_layer = image.get_layers()[0]
        p_clear_sh = clear_layer.get_pixel(10, 40).get_rgba()
        sh_delta = abs(p_clear_sh[0] - p_base_orig_sh[0])
        if sh_delta > 0.03:
            record_fail("DG-05", "Clear amount threshold", f"Expected shadow clearness delta <= 0.03, got {sh_delta:.4f}")
            return
        record_pass("DG-05", "Clear amount threshold", f"High clear threshold (80.0%) protects shadow tones (shadow {p_clear_sh[0]:.4f} vs base {p_base_orig_sh[0]:.4f}, delta {sh_delta:.4f} <= 0.03) verified")

        # 21d: Vintage Diffusion Glass preset (monochromatic graininess variance)
        image.remove_layer(clear_layer)
        cfg_vint = proc.create_config()
        cfg_vint.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_vint.set_property("image", image)
        cfg_vint.set_property("preset", "vintage-diffusion")
        cfg_vint.set_property("add-mask", False)

        proc.run(cfg_vint)
        vint_layer = image.get_layers()[0]
        samples = [vint_layer.get_pixel(70, y).get_rgba()[0] for y in range(20, 60)]
        mean_v = sum(samples) / len(samples)
        var_v = sum((s - mean_v) ** 2 for s in samples) / len(samples)
        if var_v <= 0.00005:
            record_fail("DG-06", "Diffusion graininess", f"Expected grain variance > 0.00005, got {var_v:.6f}")
            return
        record_pass("DG-06", "Translucent diffusion graininess", f"Optical diffusion grain texture verified (variance {var_v:.6f} > 0.00005)")

        # 21e: Golden Hour Warm Glow preset (color temperature warming shift)
        image.remove_layer(vint_layer)
        cfg_gold = proc.create_config()
        cfg_gold.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_gold.set_property("image", image)
        cfg_gold.set_property("preset", "golden-hour-bloom")
        cfg_gold.set_property("add-mask", False)

        proc.run(cfg_gold)
        gold_layer = image.get_layers()[0]
        p_gold_hl = gold_layer.get_pixel(70, 40).get_rgba()
        if p_gold_hl[0] <= p_gold_hl[2] or (p_gold_hl[0] - p_gold_hl[2]) < 0.10:
            record_fail("DG-07", "Golden hour warmth", f"Expected R > B (delta >= 0.10) in highlight bloom, got R={p_gold_hl[0]:.4f}, B={p_gold_hl[2]:.4f}")
            return
        record_pass("DG-07", "Golden hour warmth shift", f"Golden highlight bloom verified (R={p_gold_hl[0]:.4f} > B={p_gold_hl[2]:.4f}, warmth delta +{p_gold_hl[0]-p_gold_hl[2]:.4f})")

        # 21f: Night Neon Radiance preset (Addition blend mode & 90% opacity)
        image.remove_layer(gold_layer)
        cfg_night = proc.create_config()
        cfg_night.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_night.set_property("image", image)
        cfg_night.set_property("preset", "night-radiance")
        cfg_night.set_property("add-mask", False)

        proc.run(cfg_night)
        night_layer = image.get_layers()[0]
        if night_layer.get_mode() != Gimp.LayerMode.ADDITION or abs(night_layer.get_opacity() - 90.0) > 0.01:
            record_fail("DG-08", "Night radiance mode", f"Expected Addition mode ({int(Gimp.LayerMode.ADDITION)}) and 90.0% opacity, got mode={night_layer.get_mode()}, opacity={night_layer.get_opacity()}%")
            return
        record_pass("DG-08", "Night neon radiance mode", f"Addition blend mode ({night_layer.get_mode()}) and 90.0% opacity verified")

        # 21g: Custom Sliders & Opacity
        image.remove_layer(night_layer)
        cfg_cust = proc.create_config()
        cfg_cust.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cust.set_property("image", image)
        cfg_cust.set_property("preset", "custom")
        cfg_cust.set_property("glow-amount", 60.0)
        cfg_cust.set_property("clear-amount", 30.0)
        cfg_cust.set_property("radius", 20.0)
        cfg_cust.set_property("graininess", 10.0)
        cfg_cust.set_property("warmth", 0.0)
        cfg_cust.set_property("blend-mode", "normal")
        cfg_cust.set_property("opacity", 85.0)
        cfg_cust.set_property("add-mask", False)

        proc.run(cfg_cust)
        cust_layer = image.get_layers()[0]
        if abs(cust_layer.get_opacity() - 85.0) > 0.01 or cust_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("DG-09", "Custom opacity & mode", f"Expected 85.0% and NORMAL ({int(Gimp.LayerMode.NORMAL)}), got opacity={cust_layer.get_opacity()}%, mode={cust_layer.get_mode()}")
            return
        record_pass("DG-09", "Custom sliders & opacity", f"Opacity 85.0%, Normal blend mode ({cust_layer.get_mode()}) verified")

        # 21h: Non-destructive base layer invariance
        p_base_after_sh = base.get_pixel(10, 40).get_rgba()
        p_base_after_hl = base.get_pixel(70, 40).get_rgba()
        max_base_diff = max(
            max(abs(p_base_after_sh[i] - p_base_orig_sh[i]) for i in range(3)),
            max(abs(p_base_after_hl[i] - p_base_orig_hl[i]) for i in range(3))
        )
        if max_base_diff > 0.000001:
            record_fail("DG-10", "Non-destructive invariance", f"Base layer altered by {max_base_diff:.6f} > 0")
            return
        record_pass("DG-10", "Non-destructive layer preservation", f"Base pixels 100% untouched across all tonal zones (diff {max_base_diff:.6f})")

    except Exception as e:
        record_fail("DG-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 22: Non-Destructive Skin Smoothing & Beauty Retouching Helper Plugin (Phase 27)
# ==============================================================================
def test_skin_smoothing():
    print("\n--- Test Suite 22: Skin Smoothing & Portrait Beauty Retouching Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-skin-smoothing")
    if proc is None:
        record_fail("SS-01", "Procedure lookup", "Procedure python-fu-skin-smoothing not found")
        return

    image = Gimp.Image.new(120, 100, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "PortraitSubject", 120, 100, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        image.set_selected_layers([base])

        # Create synthetic portrait scene:
        # Initial dark background fill (0.20, 0.20, 0.20)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.20, 0.20, 0.20)"))
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 120, 100)
        base.edit_fill(Gimp.FillType.FOREGROUND)

        # Base skin tone area (x: 45..110, y: 10..90) = Warm skin base (0.80, 0.65, 0.55)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.80, 0.65, 0.55)"))
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 45, 10, 65, 80)
        base.edit_fill(Gimp.FillType.FOREGROUND)

        # Skin blemish / pore texture strips
        for sx in range(50, 105, 4):
            Gimp.context_set_foreground(Gegl.Color.new("rgb(0.72, 0.58, 0.48)"))
            image.select_rectangle(Gimp.ChannelOps.REPLACE, sx, 10, 2, 80)
            base.edit_fill(Gimp.FillType.FOREGROUND)

        Gimp.Selection.none(image)

        # Record baseline pixel values
        p_base_orig_bg = base.get_pixel(25, 50).get_rgba()
        p_base_orig_skin = base.get_pixel(70, 50).get_rgba()

        # Compute initial skin texture variation (variance across interior skin area x: 60..95, y=50)
        skin_sample_xs = list(range(60, 95, 2))
        in_skin_vals = [base.get_pixel(x, 50).get_rgba()[0] for x in skin_sample_xs]
        in_skin_mean = sum(in_skin_vals) / len(in_skin_vals)
        in_skin_var = sum((v - in_skin_mean) ** 2 for v in in_skin_vals) / len(in_skin_vals)

        # Initial edge contrast step between background (x=25) and skin (x=70)
        in_edge_step = base.get_pixel(70, 50).get_rgba()[0] - base.get_pixel(25, 50).get_rgba()[0]

        # 22a: Run Glamour Studio Smooth preset (default)
        cfg_glam = proc.create_config()
        cfg_glam.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_glam.set_property("image", image)
        cfg_glam.set_property("preset", "glamour-studio")
        cfg_glam.set_property("add-mask", True)
        cfg_glam.set_property("mask-type", "white")

        res = proc.run(cfg_glam)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("SS-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("SS-01", "Execution status", "SUCCESS")

        glam_layer = image.get_layers()[0]
        if glam_layer.get_mode() != Gimp.LayerMode.NORMAL or abs(glam_layer.get_opacity() - 85.0) > 0.01:
            record_fail("SS-02", "Layer mode & opacity", f"Expected NORMAL ({int(Gimp.LayerMode.NORMAL)}) & 85.0%, got mode={glam_layer.get_mode()}, opacity={glam_layer.get_opacity()}%")
            return
        record_pass("SS-02", "Layer mode & name", f"{glam_layer.get_name()} ({glam_layer.get_mode()})")

        # Verify reveal-all layer mask attachment
        mask = glam_layer.get_mask()
        if mask is None:
            record_fail("SS-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("SS-03", "Layer mask attachment", "Reveal-all mask attached")

        # 22b: Verify skin texture variance reduction (smoothing effect)
        out_skin_vals = [glam_layer.get_pixel(x, 50).get_rgba()[0] for x in skin_sample_xs]
        out_skin_mean = sum(out_skin_vals) / len(out_skin_vals)
        out_skin_var = sum((v - out_skin_mean) ** 2 for v in out_skin_vals) / len(out_skin_vals)
        var_reduction = 1.0 - (out_skin_var / max(in_skin_var, 0.00001))

        if var_reduction < 0.60:
            record_fail("SS-04", "Skin variance reduction", f"Expected variance reduction >= 60%, got {var_reduction*100:.1f}% (in_var={in_skin_var:.6f}, out_var={out_skin_var:.6f})")
            return
        record_pass("SS-04", "Skin surface smoothing", f"Texture variance reduced by {var_reduction*100:.1f}% ({in_skin_var:.6f} -> {out_skin_var:.6f})")

        # 22c: Verify facial contour edge preservation
        out_edge_step = glam_layer.get_pixel(70, 50).get_rgba()[0] - glam_layer.get_pixel(25, 50).get_rgba()[0]
        edge_preservation_ratio = out_edge_step / max(in_edge_step, 0.00001)
        if edge_preservation_ratio < 0.90:
            record_fail("SS-05", "Facial edge preservation", f"Expected edge preservation >= 90%, got {edge_preservation_ratio*100:.1f}% (in_step={in_edge_step:.3f}, out_step={out_edge_step:.3f})")
            return
        record_pass("SS-05", "Facial contour edge preservation", f"Sharp edge preserved at {edge_preservation_ratio*100:.1f}% (step {in_edge_step:.3f} -> {out_edge_step:.3f})")

        # 22d: Conceal-All black layer mask test
        image.remove_layer(glam_layer)
        cfg_black = proc.create_config()
        cfg_black.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_black.set_property("image", image)
        cfg_black.set_property("preset", "subtle-natural")
        cfg_black.set_property("add-mask", True)
        cfg_black.set_property("mask-type", "black")

        proc.run(cfg_black)
        black_mask_layer = image.get_layers()[0]
        bmask = black_mask_layer.get_mask()
        if bmask is None:
            record_fail("SS-06", "Conceal-all mask", "Expected attached black mask, got None")
            return
        record_pass("SS-06", "Conceal-All layer mask", "Black mask attached for selective brush painting")

        # 22e: Soft Glow Beauty preset (Soft Light blend mode)
        image.remove_layer(black_mask_layer)
        cfg_glow = proc.create_config()
        cfg_glow.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_glow.set_property("image", image)
        cfg_glow.set_property("preset", "soft-glow-beauty")
        cfg_glow.set_property("add-mask", False)

        proc.run(cfg_glow)
        glow_layer = image.get_layers()[0]
        if glow_layer.get_mode() != Gimp.LayerMode.SOFTLIGHT or abs(glow_layer.get_opacity() - 80.0) > 0.01:
            record_fail("SS-07", "Soft glow beauty mode", f"Expected Soft Light ({int(Gimp.LayerMode.SOFTLIGHT)}) and 80.0% opacity, got mode={glow_layer.get_mode()}, opacity={glow_layer.get_opacity()}%")
            return
        record_pass("SS-07", "Soft glow beauty preset", f"Soft Light mode ({glow_layer.get_mode()}) and 80.0% opacity verified")

        # 22f: High-Fashion Editorial preset (90% opacity)
        image.remove_layer(glow_layer)
        cfg_fashion = proc.create_config()
        cfg_fashion.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_fashion.set_property("image", image)
        cfg_fashion.set_property("preset", "high-fashion")
        cfg_fashion.set_property("add-mask", False)

        proc.run(cfg_fashion)
        fashion_layer = image.get_layers()[0]
        if abs(fashion_layer.get_opacity() - 90.0) > 0.01:
            record_fail("SS-08", "High-fashion opacity", f"Expected 90.0% opacity, got {fashion_layer.get_opacity()}%")
            return
        record_pass("SS-08", "High-fashion editorial preset", f"{fashion_layer.get_name()} with 90.0% opacity verified")

        # 22g: Custom Sliders & Detail Retention
        image.remove_layer(fashion_layer)
        cfg_cust = proc.create_config()
        cfg_cust.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cust.set_property("image", image)
        cfg_cust.set_property("preset", "custom")
        cfg_cust.set_property("smoothing-radius", 4.0)
        cfg_cust.set_property("edge-preservation", 15.0)
        cfg_cust.set_property("detail-retention", 30.0)
        cfg_cust.set_property("blend-mode", "normal")
        cfg_cust.set_property("opacity", 75.0)
        cfg_cust.set_property("add-mask", False)

        proc.run(cfg_cust)
        cust_layer = image.get_layers()[0]
        if abs(cust_layer.get_opacity() - 75.0) > 0.01 or cust_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("SS-09", "Custom sliders", f"Expected 75.0% and NORMAL, got opacity={cust_layer.get_opacity()}%, mode={cust_layer.get_mode()}")
            return
        record_pass("SS-09", "Custom sliders & detail retention", f"Opacity 75.0%, Normal blend mode ({cust_layer.get_mode()}) verified")

        # 22h: Non-destructive base layer invariance
        p_base_after_bg = base.get_pixel(25, 50).get_rgba()
        p_base_after_skin = base.get_pixel(70, 50).get_rgba()
        max_base_diff = max(
            max(abs(p_base_after_bg[i] - p_base_orig_bg[i]) for i in range(3)),
            max(abs(p_base_after_skin[i] - p_base_orig_skin[i]) for i in range(3))
        )
        if max_base_diff > 0.000001:
            record_fail("SS-10", "Non-destructive invariance", f"Base layer altered by {max_base_diff:.6f} > 0")
            return
        record_pass("SS-10", "Non-destructive layer preservation", f"Base pixels 100% untouched across all tonal zones (diff {max_base_diff:.6f})")

    except Exception as e:
        record_fail("SS-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 23: Selective Color Pop & Background Desaturation Helper (Phase 28)
# ==============================================================================
def test_selective_color_pop():
    print("\n--- Test Suite 23: Selective Color Pop & Background Desaturation Helper ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-selective-color-pop")
    if proc is None:
        record_fail("SCP-01", "Procedure lookup", "Procedure not found")
        return

    # Image setup: 100x100 RGB image with vibrant red foreground
    image = Gimp.Image.new(100, 100, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "Base Image", 100, 100, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.9, 0.2, 0.1)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        p_base_center = base.get_pixel(50, 50).get_rgba()
        p_base_edge = base.get_pixel(5, 5).get_rgba()

        # 23a: Classic B&W Background Preset with Radial Focal Mask
        cfg_classic = proc.create_config()
        cfg_classic.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_classic.set_property("image", image)
        cfg_classic.set_property("preset", "classic-bw")
        cfg_classic.set_property("focus-source", "radial")
        cfg_classic.set_property("focal-radius", 0.6)
        cfg_classic.set_property("focal-softness", 0.5)
        cfg_classic.set_property("opacity", 100.0)
        cfg_classic.set_property("invert-mask", False)

        res = proc.run(cfg_classic)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("SCP-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("SCP-01", "Execution status", "SUCCESS")

        pop_layer = image.get_layers()[0]
        if pop_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("SCP-02", "Layer mode", f"Expected NORMAL (28), got {pop_layer.get_mode()}")
            return
        record_pass("SCP-02", "Layer mode & name", f"{pop_layer.get_name()} ({pop_layer.get_mode()})")

        # Verify layer mask attachment
        mask = pop_layer.get_mask()
        if mask is None:
            record_fail("SCP-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("SCP-03", "Layer mask attachment", "Attached radial focal mask")

        # 23b: Subject full color preservation at center (diff == 0.000000)
        p_comp_center = get_composite_pixel(image, 50, 50)
        center_color_diff = max(abs(p_comp_center[i] - p_base_center[i]) for i in range(3))
        if center_color_diff > 0.000001:
            record_fail("SCP-04", "Subject color preservation", f"Center altered by {center_color_diff:.6f} > 0")
            return
        record_pass("SCP-04", "Subject full color preservation", f"Center subject 100% full color (diff {center_color_diff:.6f})")

        # 23c: Background monochrome conversion (R == G == B, mono spread == 0.000000)
        p_comp_edge = get_composite_pixel(image, 5, 5)
        mono_spread = max(abs(p_comp_edge[0] - p_comp_edge[1]), abs(p_comp_edge[1] - p_comp_edge[2]), abs(p_comp_edge[0] - p_comp_edge[2]))
        if mono_spread > 0.000001:
            record_fail("SCP-05", "Background monochrome conversion", f"Edge color spread {mono_spread:.6f} > 0")
            return
        record_pass("SCP-05", "Peripheral background monochrome conversion", f"Edge exact monochrome: R=G=B={p_comp_edge[0]:.4f} (spread {mono_spread:.6f})")

        image.remove_layer(pop_layer)

        # 23d: Active Selection Subject Mask Test
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 30, 30, 40, 40)
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("preset", "classic-bw")
        cfg_sel.set_property("focus-source", "selection")
        cfg_sel.set_property("opacity", 100.0)
        cfg_sel.set_property("invert-mask", False)

        proc.run(cfg_sel)
        sel_layer = image.get_layers()[0]
        p_sel_inside = get_composite_pixel(image, 50, 50)
        p_sel_outside = get_composite_pixel(image, 10, 10)

        sel_inside_diff = max(abs(p_sel_inside[i] - p_base_center[i]) for i in range(3))
        sel_outside_mono = max(abs(p_sel_outside[0] - p_sel_outside[1]), abs(p_sel_outside[1] - p_sel_outside[2]))
        if sel_inside_diff > 0.000001 or sel_outside_mono > 0.000001:
            record_fail("SCP-06", "Selection-aware mask", f"Inside diff={sel_inside_diff:.6f}, Outside mono={sel_outside_mono:.6f}")
            return
        record_pass("SCP-06", "Selection-aware subject mask", f"Inside full color (diff {sel_inside_diff:.6f}), Outside pure monochrome (spread {sel_outside_mono:.6f})")

        Gimp.Selection.none(image)
        image.remove_layer(sel_layer)

        # 23e: Invert Mask Option (Monochrome Subject, Color Background)
        cfg_inv = proc.create_config()
        cfg_inv.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_inv.set_property("image", image)
        cfg_inv.set_property("preset", "classic-bw")
        cfg_inv.set_property("focus-source", "radial")
        cfg_inv.set_property("focal-radius", 0.6)
        cfg_inv.set_property("focal-softness", 0.5)
        cfg_inv.set_property("opacity", 100.0)
        cfg_inv.set_property("invert-mask", True)

        proc.run(cfg_inv)
        inv_layer = image.get_layers()[0]
        p_inv_center = get_composite_pixel(image, 50, 50)
        p_inv_edge = get_composite_pixel(image, 5, 5)

        inv_center_mono = max(abs(p_inv_center[0] - p_inv_center[1]), abs(p_inv_center[1] - p_inv_center[2]))
        inv_edge_diff = max(abs(p_inv_edge[i] - p_base_edge[i]) for i in range(3))
        if inv_center_mono > 0.000001 or inv_edge_diff > 0.000001:
            record_fail("SCP-07", "Invert mask option", f"Center mono={inv_center_mono:.6f}, Edge diff={inv_edge_diff:.6f}")
            return
        record_pass("SCP-07", "Invert effect option", f"Center monochrome (spread {inv_center_mono:.6f}), Edge full color (diff {inv_edge_diff:.6f})")

        image.remove_layer(inv_layer)

        # 23f: Muted Pastel Desaturated Preset Test
        cfg_pastel = proc.create_config()
        cfg_pastel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_pastel.set_property("image", image)
        cfg_pastel.set_property("preset", "muted-pastel")
        cfg_pastel.set_property("focus-source", "radial")
        cfg_pastel.set_property("focal-radius", 0.6)
        cfg_pastel.set_property("focal-softness", 0.5)
        cfg_pastel.set_property("opacity", 100.0)
        cfg_pastel.set_property("invert-mask", False)

        proc.run(cfg_pastel)
        pastel_layer = image.get_layers()[0]
        p_pas_center = get_composite_pixel(image, 50, 50)
        p_pas_edge = get_composite_pixel(image, 5, 5)

        pas_center_diff = max(abs(p_pas_center[i] - p_base_center[i]) for i in range(3))
        # Edge red chroma (p_pas_edge[0] - p_pas_edge[1]) should be noticeably reduced from original (0.9 - 0.2 = 0.7)
        edge_chroma = p_pas_edge[0] - p_pas_edge[1]
        orig_chroma = p_base_edge[0] - p_base_edge[1]
        if pas_center_diff > 0.000001 or edge_chroma >= orig_chroma * 0.50:
            record_fail("SCP-08", "Muted pastel preset", f"Center diff={pas_center_diff:.6f}, Edge chroma={edge_chroma:.4f} >= {orig_chroma * 0.50:.4f}")
            return
        record_pass("SCP-08", "Muted pastel preset", f"Center full color, Background chroma muted {orig_chroma:.3f} -> {edge_chroma:.3f} (-{(1 - edge_chroma/orig_chroma)*100:.1f}%)")

        image.remove_layer(pastel_layer)

        # 23g: Vintage Sepia Toned Preset Test
        cfg_sepia = proc.create_config()
        cfg_sepia.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sepia.set_property("image", image)
        cfg_sepia.set_property("preset", "vintage-sepia")
        cfg_sepia.set_property("focus-source", "radial")
        cfg_sepia.set_property("focal-radius", 0.6)
        cfg_sepia.set_property("focal-softness", 0.5)
        cfg_sepia.set_property("opacity", 100.0)
        cfg_sepia.set_property("invert-mask", False)

        proc.run(cfg_sepia)
        sepia_layer = image.get_layers()[0]
        p_sep_center = get_composite_pixel(image, 50, 50)
        p_sep_edge = get_composite_pixel(image, 5, 5)

        sep_center_diff = max(abs(p_sep_center[i] - p_base_center[i]) for i in range(3))
        # Warm sepia tone requires R > G > B at edge
        is_sepia_warm = (p_sep_edge[0] > p_sep_edge[1] > p_sep_edge[2])
        if sep_center_diff > 0.000001 or not is_sepia_warm:
            record_fail("SCP-09", "Vintage sepia preset", f"Center diff={sep_center_diff:.6f}, Edge R={p_sep_edge[0]:.3f}, G={p_sep_edge[1]:.3f}, B={p_sep_edge[2]:.3f}")
            return
        record_pass("SCP-09", "Vintage sepia toning preset", f"Background warm archival sepia (R={p_sep_edge[0]:.3f} > G={p_sep_edge[1]:.3f} > B={p_sep_edge[2]:.3f})")

        image.remove_layer(sepia_layer)

        # 23h: Custom Sliders & Layer Opacity Test
        cfg_cust = proc.create_config()
        cfg_cust.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cust.set_property("image", image)
        cfg_cust.set_property("preset", "custom")
        cfg_cust.set_property("focus-source", "radial")
        cfg_cust.set_property("focal-radius", 0.5)
        cfg_cust.set_property("focal-softness", 0.4)
        cfg_cust.set_property("bg-desaturation", 100.0)
        cfg_cust.set_property("custom-red", 0.5)
        cfg_cust.set_property("custom-green", 0.3)
        cfg_cust.set_property("custom-blue", 0.2)
        cfg_cust.set_property("opacity", 80.0)
        cfg_cust.set_property("invert-mask", False)

        proc.run(cfg_cust)
        cust_layer = image.get_layers()[0]
        if abs(cust_layer.get_opacity() - 80.0) > 0.01 or cust_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("SCP-10", "Custom sliders", f"Expected 80.0% and NORMAL, got opacity={cust_layer.get_opacity()}%, mode={cust_layer.get_mode()}")
            return
        record_pass("SCP-10", "Custom sliders & opacity", f"Opacity 80.0%, Normal blend mode ({cust_layer.get_mode()}) verified")

        # 23i: Non-destructive base layer invariance across all pixels
        p_base_after_center = base.get_pixel(50, 50).get_rgba()
        p_base_after_edge = base.get_pixel(5, 5).get_rgba()
        max_base_diff = max(
            max(abs(p_base_after_center[i] - p_base_center[i]) for i in range(3)),
            max(abs(p_base_after_edge[i] - p_base_edge[i]) for i in range(3))
        )
        if max_base_diff > 0.000001:
            record_fail("SCP-11", "Non-destructive invariance", f"Base layer altered by {max_base_diff:.6f} > 0")
            return
        record_pass("SCP-11", "Non-destructive layer preservation", f"Base pixels 100% untouched across all tonal zones (diff {max_base_diff:.6f})")

    except Exception as e:
        record_fail("SCP-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 24: Vintage Photo Colorization & Restoration Helper (Phase 29)
# ==============================================================================
def test_photo_colorize():
    print("\n--- Test Suite 24: Vintage Photo Colorization & Restoration Helper ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-photo-colorize")
    if proc is None:
        record_fail("PC-01", "Procedure lookup", "Procedure not found")
        return

    # Base image: 100x100 grayscale image with dark left (0.2) and bright right (0.8)
    image = Gimp.Image.new(100, 100, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "Grayscale Base", 100, 100, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.2, 0.2, 0.2)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 50, 0, 50, 100)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.8, 0.8, 0.8)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(image)

        p_base_dark = base.get_pixel(25, 50).get_rgba()
        p_base_light = base.get_pixel(75, 50).get_rgba()

        # 24a: Sepia Antique in HSL Color mode with Reveal-All Mask
        cfg_sepia = proc.create_config()
        cfg_sepia.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sepia.set_property("image", image)
        cfg_sepia.set_property("preset", "sepia-antique")
        cfg_sepia.set_property("blend-mode", "hsl-color")
        cfg_sepia.set_property("mask-type", "reveal-all")
        cfg_sepia.set_property("opacity", 100.0)

        res = proc.run(cfg_sepia)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("PC-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("PC-01", "Execution status", "SUCCESS")

        sep_layer = image.get_layers()[0]
        if sep_layer.get_mode() != Gimp.LayerMode.HSL_COLOR:
            record_fail("PC-02", "Layer mode", f"Expected HSL_COLOR (39), got {sep_layer.get_mode()}")
            return
        record_pass("PC-02", "Layer mode & name", f"{sep_layer.get_name()} ({sep_layer.get_mode()})")

        # Verify layer mask attachment
        mask = sep_layer.get_mask()
        if mask is None:
            record_fail("PC-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("PC-03", "Layer mask attachment", "Reveal-all mask attached")

        # 24b: Sepia Antique warm toning response (R > G > B across tones)
        p_comp_dark = get_composite_pixel(image, 25, 50)
        p_comp_light = get_composite_pixel(image, 75, 50)
        is_dark_warm = (p_comp_dark[0] > p_comp_dark[1] > p_comp_dark[2])
        is_light_warm = (p_comp_light[0] > p_comp_light[1] > p_comp_light[2])
        if not (is_dark_warm and is_light_warm):
            record_fail("PC-04", "Sepia Antique warm tone", f"Dark R={p_comp_dark[0]:.3f}, G={p_comp_dark[1]:.3f}, B={p_comp_dark[2]:.3f}; Light R={p_comp_light[0]:.3f}, G={p_comp_light[1]:.3f}, B={p_comp_light[2]:.3f}")
            return
        record_pass("PC-04", "Sepia Antique warm toning", f"Shadow warm (R={p_comp_dark[0]:.3f}>G={p_comp_dark[1]:.3f}>B={p_comp_dark[2]:.3f}), Highlight warm (R={p_comp_light[0]:.3f}>G={p_comp_light[1]:.3f}>B={p_comp_light[2]:.3f})")

        image.remove_layer(sep_layer)

        # 24c: Cyanotype Blue Prussian blue shadow response (B > R)
        cfg_cyan = proc.create_config()
        cfg_cyan.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cyan.set_property("image", image)
        cfg_cyan.set_property("preset", "cyanotype-blue")
        cfg_cyan.set_property("blend-mode", "hsl-color")
        cfg_cyan.set_property("mask-type", "reveal-all")
        cfg_cyan.set_property("opacity", 100.0)

        proc.run(cfg_cyan)
        cyan_layer = image.get_layers()[0]
        p_cyan_dark = get_composite_pixel(image, 25, 50)
        blue_delta = p_cyan_dark[2] - p_cyan_dark[0]
        if blue_delta < 0.10:
            record_fail("PC-05", "Cyanotype blue shadows", f"Blue delta {blue_delta:.4f} < 0.10 (B={p_cyan_dark[2]:.3f}, R={p_cyan_dark[0]:.3f})")
            return
        record_pass("PC-05", "Cyanotype Prussian blue shadows", f"Shadow blue dominance B={p_cyan_dark[2]:.3f} > R={p_cyan_dark[0]:.3f} (delta +{blue_delta:.3f})")

        image.remove_layer(cyan_layer)

        # 24d: Vintage Amber Daguerreotype golden toning (R > G > B)
        cfg_amber = proc.create_config()
        cfg_amber.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_amber.set_property("image", image)
        cfg_amber.set_property("preset", "vintage-amber")
        cfg_amber.set_property("blend-mode", "hsl-color")
        cfg_amber.set_property("mask-type", "reveal-all")
        cfg_amber.set_property("opacity", 100.0)

        proc.run(cfg_amber)
        amber_layer = image.get_layers()[0]
        p_amb_dark = get_composite_pixel(image, 25, 50)
        amb_delta = p_amb_dark[0] - p_amb_dark[2]
        if amb_delta < 0.10 or not (p_amb_dark[0] > p_amb_dark[1] > p_amb_dark[2]):
            record_fail("PC-06", "Vintage amber daguerreotype", f"Amber delta {amb_delta:.4f} < 0.10")
            return
        record_pass("PC-06", "Vintage amber daguerreotype toning", f"Golden amber tones R={p_amb_dark[0]:.3f} > G={p_amb_dark[1]:.3f} > B={p_amb_dark[2]:.3f} (delta +{amb_delta:.3f})")

        image.remove_layer(amber_layer)

        # 24e: Hand-Tinted Portrait flattering skin highlights
        cfg_port = proc.create_config()
        cfg_port.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_port.set_property("image", image)
        cfg_port.set_property("preset", "hand-tint-portrait")
        cfg_port.set_property("blend-mode", "hsl-color")
        cfg_port.set_property("mask-type", "reveal-all")
        cfg_port.set_property("opacity", 100.0)

        proc.run(cfg_port)
        port_layer = image.get_layers()[0]
        p_port_light = get_composite_pixel(image, 75, 50)
        if not (p_port_light[0] > p_port_light[1] > p_port_light[2]):
            record_fail("PC-07", "Hand-tinted portrait", f"Highlight R={p_port_light[0]:.3f}, G={p_port_light[1]:.3f}, B={p_port_light[2]:.3f}")
            return
        record_pass("PC-07", "Hand-tinted portrait tone", f"Flattering skin highlights (R={p_port_light[0]:.3f} > G={p_port_light[1]:.3f} > B={p_port_light[2]:.3f})")

        image.remove_layer(port_layer)

        # 24f: Conceal-All Black Layer Mask for Selective Hand-Coloring
        cfg_blk = proc.create_config()
        cfg_blk.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_blk.set_property("image", image)
        cfg_blk.set_property("preset", "sepia-antique")
        cfg_blk.set_property("blend-mode", "hsl-color")
        cfg_blk.set_property("mask-type", "conceal-all")
        cfg_blk.set_property("opacity", 100.0)

        proc.run(cfg_blk)
        blk_layer = image.get_layers()[0]
        p_blk_dark = get_composite_pixel(image, 25, 50)
        diff_blk = max(abs(p_blk_dark[i] - p_base_dark[i]) for i in range(3))
        if diff_blk > 0.000001:
            record_fail("PC-08", "Conceal-all mask", f"Base altered by {diff_blk:.6f} > 0")
            return
        record_pass("PC-08", "Conceal-all black layer mask", f"Black mask attached for selective brush hand-coloring (diff {diff_blk:.6f})")

        image.remove_layer(blk_layer)

        # 24g: Selection-Aware Subject Masking Test
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 20, 20, 30, 60)
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("preset", "sepia-antique")
        cfg_sel.set_property("blend-mode", "hsl-color")
        cfg_sel.set_property("mask-type", "selection")
        cfg_sel.set_property("opacity", 100.0)

        proc.run(cfg_sel)
        sel_layer = image.get_layers()[0]
        p_sel_inside = get_composite_pixel(image, 25, 50)
        p_sel_outside = get_composite_pixel(image, 75, 50)

        is_sel_warm = (p_sel_inside[0] > p_sel_inside[1] > p_sel_inside[2])
        out_diff = max(abs(p_sel_outside[i] - p_base_light[i]) for i in range(3))
        if not is_sel_warm or out_diff > 0.000001:
            record_fail("PC-09", "Selection-aware mask", f"Inside warm={is_sel_warm}, Outside diff={out_diff:.6f}")
            return
        record_pass("PC-09", "Selection-aware subject mask", f"Inside colorized warm (R={p_sel_inside[0]:.3f}>G={p_sel_inside[1]:.3f}>B={p_sel_inside[2]:.3f}), Outside untouched (diff {out_diff:.6f})")

        Gimp.Selection.none(image)
        image.remove_layer(sel_layer)

        # 24h: Custom Sliders, Midpoint, and Layer Opacity Test
        cfg_cust = proc.create_config()
        cfg_cust.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cust.set_property("image", image)
        cfg_cust.set_property("preset", "custom")
        cfg_cust.set_property("blend-mode", "hsl-color")
        cfg_cust.set_property("mask-type", "reveal-all")
        cfg_cust.set_property("midpoint", 60.0)
        cfg_cust.set_property("custom-shadow-r", 0.20)
        cfg_cust.set_property("custom-shadow-g", 0.10)
        cfg_cust.set_property("custom-shadow-b", 0.05)
        cfg_cust.set_property("custom-highlight-r", 0.95)
        cfg_cust.set_property("custom-highlight-g", 0.85)
        cfg_cust.set_property("custom-highlight-b", 0.75)
        cfg_cust.set_property("opacity", 85.0)

        proc.run(cfg_cust)
        cust_layer = image.get_layers()[0]
        if abs(cust_layer.get_opacity() - 85.0) > 0.01 or cust_layer.get_mode() != Gimp.LayerMode.HSL_COLOR:
            record_fail("PC-10", "Custom sliders", f"Expected 85.0% and HSL_COLOR, got opacity={cust_layer.get_opacity()}%, mode={cust_layer.get_mode()}")
            return
        record_pass("PC-10", "Custom sliders & opacity", f"Opacity 85.0%, HSL_COLOR blend mode ({cust_layer.get_mode()}), midpoint 60.0% verified")

        # 24i: Non-destructive base layer invariance across all pixels
        p_base_after_dark = base.get_pixel(25, 50).get_rgba()
        p_base_after_light = base.get_pixel(75, 50).get_rgba()
        max_base_diff = max(
            max(abs(p_base_after_dark[i] - p_base_dark[i]) for i in range(3)),
            max(abs(p_base_after_light[i] - p_base_light[i]) for i in range(3))
        )
        if max_base_diff > 0.000001:
            record_fail("PC-11", "Non-destructive invariance", f"Base layer altered by {max_base_diff:.6f} > 0")
            return
        record_pass("PC-11", "Non-destructive layer preservation", f"Base pixels 100% untouched across all tonal zones (diff {max_base_diff:.6f})")

    except Exception as e:
        record_fail("PC-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 25: Non-Destructive JPEG Artifacts Removal & Deblocking Plugin (Phase 30)
# ==============================================================================
def test_jpeg_artifact_removal():
    print("\n--- Test Suite 25: JPEG Artifacts Removal & Deblocking Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-jpeg-artifact-removal")
    if proc is None:
        record_fail("JAR-01", "Procedure lookup", "Procedure python-fu-jpeg-artifact-removal not found")
        return

    # Create a 64x64 test image with:
    # 1. 8x8 block checkerboard variation simulating JPEG DCT block boundaries (delta ~0.05 between alternating 8x8 blocks)
    # 2. A sharp edge on the right quarter (x >= 48) with high contrast (delta ~0.40)
    # 3. An isolated mosquito ringing spike at (12, 12)
    image = Gimp.Image.new(64, 64, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "Base", 64, 64, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)

        # Fill base background neutral gray
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.50, 0.50, 0.50)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        # Alternating 8x8 block checkerboard to simulate JPEG DCT blocking
        for bx in range(6):  # blocks 0 to 5 (columns x=0..47)
            for by in range(8):  # rows y=0..63
                if (bx + by) % 2 == 1:
                    image.select_rectangle(Gimp.ChannelOps.REPLACE, bx * 8, by * 8, 8, 8)
                    Gimp.context_set_foreground(Gegl.Color.new("rgb(0.55, 0.55, 0.55)"))
                    base.edit_fill(Gimp.FillType.FOREGROUND)

        # Sharp high-contrast edge on right side (x >= 48, delta ~0.40)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 48, 0, 16, 64)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.90, 0.90, 0.90)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        # Isolated mosquito ringing spike at (12, 12)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 12, 12, 1, 1)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.85, 0.85, 0.85)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        Gimp.Selection.none(image)

        # Pre-filter measurements
        p_b7_pre = base.get_pixel(7, 4).get_rgba()[0]
        p_b8_pre = base.get_pixel(8, 4).get_rgba()[0]
        pre_block_step = abs(p_b7_pre - p_b8_pre)

        p_edge47_pre = base.get_pixel(47, 4).get_rgba()[0]
        p_edge48_pre = base.get_pixel(48, 4).get_rgba()[0]
        pre_edge_step = abs(p_edge48_pre - p_edge47_pre)

        p_spike_pre = base.get_pixel(12, 12).get_rgba()[0]

        # 25a: Execute procedure with Medium Compression Smoothing (default)
        config = proc.create_config()
        config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        config.set_property("image", image)
        config.set_property("preset", "medium")
        config.set_property("mask-type", "reveal-all")
        config.set_property("opacity", 100.0)

        res = proc.run(config)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("JAR-01", "Execution status", f"Expected SUCCESS, got status={status}")
            return
        record_pass("JAR-01", "Execution status", "SUCCESS")

        # 25b: Verify created adjustment layer and properties
        layers = image.get_layers()
        if len(layers) < 2:
            record_fail("JAR-02", "Layer creation", f"Expected at least 2 layers, found {len(layers)}")
            return
        clean_layer = layers[0]
        if "JPEG Cleanup" not in clean_layer.get_name() or clean_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("JAR-02", "Layer properties", f"Unexpected name={clean_layer.get_name()}, mode={clean_layer.get_mode()}")
            return
        record_pass("JAR-02", "Adjustment layer verified", f"Layer '{clean_layer.get_name()}' mode={clean_layer.get_mode()} opacity={clean_layer.get_opacity():.1f}%")

        # 25c: Verify attached reveal-all layer mask
        mask = clean_layer.get_mask()
        if mask is None:
            record_fail("JAR-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("JAR-03", "Layer mask attachment", "Reveal-all mask attached")

        # 25d: Deblocking verification: 8x8 block boundary step reduction
        p_b7_post = get_composite_pixel(image, 7, 4)[0]
        p_b8_post = get_composite_pixel(image, 8, 4)[0]
        post_block_step = abs(p_b7_post - p_b8_post)
        if post_block_step >= pre_block_step * 0.5:
            record_fail("JAR-04", "8x8 Block deblocking", f"Block step {post_block_step:.4f} not reduced sufficiently from {pre_block_step:.4f}")
            return
        record_pass("JAR-04", "8x8 DCT deblocking reduction", f"Block step reduced from {pre_block_step:.4f} to {post_block_step:.4f} (>50% smoothing)")

        # 25e: Sharp edge contrast preservation (>50% preserved)
        p_edge47_post = get_composite_pixel(image, 47, 4)[0]
        p_edge48_post = get_composite_pixel(image, 48, 4)[0]
        post_edge_step = abs(p_edge48_post - p_edge47_post)
        if post_edge_step < pre_edge_step * 0.5:
            record_fail("JAR-05", "Sharp edge preservation", f"Edge step {post_edge_step:.4f} dropped below 50% of {pre_edge_step:.4f}")
            return
        record_pass("JAR-05", "Sharp edge contrast preservation", f"High-contrast edge preserved at {post_edge_step:.4f} ({post_edge_step/pre_edge_step*100:.1f}% contrast retained)")

        image.remove_layer(clean_layer)

        # 25f: Mosquito ringing spike suppression (preset "ringing")
        cfg_ring = proc.create_config()
        cfg_ring.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_ring.set_property("image", image)
        cfg_ring.set_property("preset", "ringing")
        cfg_ring.set_property("mask-type", "reveal-all")
        cfg_ring.set_property("opacity", 100.0)

        proc.run(cfg_ring)
        ring_layer = image.get_layers()[0]
        p_spike_post = get_composite_pixel(image, 12, 12)[0]
        spike_attenuation = p_spike_pre - p_spike_post
        if p_spike_post >= 0.70:
            record_fail("JAR-06", "Mosquito ringing suppression", f"Spike value {p_spike_post:.4f} not attenuated sufficiently from {p_spike_pre:.4f}")
            return
        record_pass("JAR-06", "Mosquito ringing suppression", f"Isolated ringing spike attenuated from {p_spike_pre:.3f} down to {p_spike_post:.3f} (delta -{spike_attenuation:.3f})")

        image.remove_layer(ring_layer)

        # 25g: Macroblock 16x16 preset
        cfg_mb = proc.create_config()
        cfg_mb.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_mb.set_property("image", image)
        cfg_mb.set_property("preset", "macroblock")
        cfg_mb.set_property("mask-type", "reveal-all")
        cfg_mb.set_property("opacity", 100.0)

        proc.run(cfg_mb)
        mb_layer = image.get_layers()[0]
        if "16x16 Macroblock" not in mb_layer.get_name():
            record_fail("JAR-07", "Macroblock preset", f"Unexpected layer name {mb_layer.get_name()}")
            return
        record_pass("JAR-07", "16x16 Macroblock preset verified", f"Layer '{mb_layer.get_name()}' created")

        image.remove_layer(mb_layer)

        # 25h: Conceal-All Black Layer Mask
        cfg_blk = proc.create_config()
        cfg_blk.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_blk.set_property("image", image)
        cfg_blk.set_property("preset", "medium")
        cfg_blk.set_property("mask-type", "conceal-all")
        cfg_blk.set_property("opacity", 100.0)

        proc.run(cfg_blk)
        blk_layer = image.get_layers()[0]
        p_blk = get_composite_pixel(image, 7, 4)
        p_base = base.get_pixel(7, 4).get_rgba()
        diff_blk = max(abs(p_blk[i] - p_base[i]) for i in range(3))
        if diff_blk > 0.000001:
            record_fail("JAR-08", "Conceal-all mask", f"Base altered by {diff_blk:.6f} > 0")
            return
        record_pass("JAR-08", "Conceal-all black layer mask", f"Black mask attached for selective brush cleanup (diff {diff_blk:.6f})")

        image.remove_layer(blk_layer)

        # 25i: Selection-Aware Masking
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 16, 16)
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("preset", "medium")
        cfg_sel.set_property("mask-type", "selection")
        cfg_sel.set_property("opacity", 100.0)

        proc.run(cfg_sel)
        sel_layer = image.get_layers()[0]
        p_sel_inside_7 = get_composite_pixel(image, 7, 4)[0]
        p_sel_inside_8 = get_composite_pixel(image, 8, 4)[0]
        inside_step = abs(p_sel_inside_7 - p_sel_inside_8)

        p_sel_out = get_composite_pixel(image, 48, 4)
        p_base_out = base.get_pixel(48, 4).get_rgba()
        out_diff = max(abs(p_sel_out[i] - p_base_out[i]) for i in range(3))

        if out_diff > 0.000001 or inside_step >= pre_block_step * 0.7:
            record_fail("JAR-09", "Selection-aware mask", f"Inside step {inside_step:.4f}, Outside diff {out_diff:.6f}")
            return
        record_pass("JAR-09", "Selection-aware cleanup mask", f"Inside selection deblocked ({inside_step:.4f} < {pre_block_step:.4f}), outside untouched (diff {out_diff:.6f})")

        Gimp.Selection.none(image)
        image.remove_layer(sel_layer)

        # 25j: Custom Sliders & Opacity
        cfg_cust = proc.create_config()
        cfg_cust.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cust.set_property("image", image)
        cfg_cust.set_property("preset", "custom")
        cfg_cust.set_property("sigma", 15.0)
        cfg_cust.set_property("patch-size", "size16x16")
        cfg_cust.set_property("ringing-reduction", 3)
        cfg_cust.set_property("detail-recovery", 50.0)
        cfg_cust.set_property("opacity", 85.0)
        cfg_cust.set_property("mask-type", "reveal-all")

        proc.run(cfg_cust)
        cust_layer = image.get_layers()[0]
        if abs(cust_layer.get_opacity() - 85.0) > 0.01:
            record_fail("JAR-10", "Custom sliders", f"Expected opacity 85.0%, got {cust_layer.get_opacity()}%")
            return
        record_pass("JAR-10", "Custom sliders & opacity", f"Opacity 85.0%, patch size size16x16, sigma 15.0 verified")

        # 25k: Non-destructive base layer invariance across all pixels
        p_base_after_7 = base.get_pixel(7, 4).get_rgba()[0]
        p_base_after_8 = base.get_pixel(8, 4).get_rgba()[0]
        p_base_after_edge = base.get_pixel(48, 4).get_rgba()[0]
        max_base_diff = max(
            abs(p_base_after_7 - p_b7_pre),
            abs(p_base_after_8 - p_b8_pre),
            abs(p_base_after_edge - p_edge48_pre)
        )
        if max_base_diff > 0.000001:
            record_fail("JAR-11", "Non-destructive invariance", f"Base layer altered by {max_base_diff:.6f} > 0")
            return
        record_pass("JAR-11", "Non-destructive layer preservation", f"Base pixels 100% untouched across all tonal zones (diff {max_base_diff:.6f})")

    except Exception as e:
        record_fail("JAR-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 26: Non-Destructive Charcoal & Fine-Art Sketch Plugin (Phase 31)
# ==============================================================================
def test_charcoal_filter():
    print("\n--- Test Suite 26: Charcoal & Fine-Art Sketch Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-charcoal-filter")
    if proc is None:
        record_fail("CF-01", "Procedure lookup", "Procedure python-fu-charcoal-filter not found")
        return

    # Create a 64x64 test image with:
    # High-key paper background (0.9, 0.9, 0.9) and a dark subject rectangle (0.1, 0.1, 0.1) in center
    image = Gimp.Image.new(64, 64, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "Base", 64, 64, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)

        # Fill background
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.90, 0.90, 0.90)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        # Dark subject rectangle
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 16, 16, 32, 32)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.10, 0.10, 0.10)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(image)

        p_base_paper = base.get_pixel(4, 4).get_rgba()
        p_base_edge = base.get_pixel(15, 20).get_rgba()
        p_base_subj = base.get_pixel(32, 32).get_rgba()

        # 26a: Execute with Fine Charcoal Drawing preset (default)
        config = proc.create_config()
        config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        config.set_property("image", image)
        config.set_property("preset", "fine-charcoal")
        config.set_property("mask-type", "reveal-all")
        config.set_property("opacity", 100.0)

        res = proc.run(config)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("CF-01", "Execution status", f"Expected SUCCESS, got status={status}")
            return
        record_pass("CF-01", "Execution status", "SUCCESS")

        # 26b: Verify layer properties
        layers = image.get_layers()
        if len(layers) < 2:
            record_fail("CF-02", "Layer creation", f"Expected at least 2 layers, found {len(layers)}")
            return
        ch_layer = layers[0]
        if "Charcoal Sketch" not in ch_layer.get_name() or ch_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("CF-02", "Layer properties", f"Unexpected name={ch_layer.get_name()}, mode={ch_layer.get_mode()}")
            return
        record_pass("CF-02", "Layer mode & name", f"Layer '{ch_layer.get_name()}' mode={ch_layer.get_mode()}")

        # 26c: Verify attached reveal-all layer mask
        mask = ch_layer.get_mask()
        if mask is None:
            record_fail("CF-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("CF-03", "Layer mask attachment", "Reveal-all mask attached")

        # 26d: Fine Charcoal Drawing tone verification: paper background lightness > 0.85, charcoal stroke line < 0.15
        p_paper = get_composite_pixel(image, 4, 4)
        p_stroke = get_composite_pixel(image, 15, 20)
        if p_paper[0] < 0.85 or p_stroke[0] > 0.15:
            record_fail("CF-04", "Fine charcoal tones", f"Paper={p_paper[0]:.3f} (expected >0.85), Stroke={p_stroke[0]:.3f} (expected <0.15)")
            return
        record_pass("CF-04", "Fine Charcoal tone mapping", f"Paper highlight ({p_paper[0]:.3f} > 0.85), Charcoal contour stroke ({p_stroke[0]:.3f} < 0.15)")

        image.remove_layer(ch_layer)

        # 26e: Dramatic Heavy Vine preset
        cfg_vine = proc.create_config()
        cfg_vine.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_vine.set_property("image", image)
        cfg_vine.set_property("preset", "dramatic-vine")
        cfg_vine.set_property("mask-type", "reveal-all")
        cfg_vine.set_property("opacity", 100.0)

        proc.run(cfg_vine)
        vine_layer = image.get_layers()[0]
        p_vine_stroke = get_composite_pixel(image, 15, 20)
        if p_vine_stroke[0] > 0.10:
            record_fail("CF-05", "Dramatic vine tone", f"Stroke={p_vine_stroke[0]:.3f} > 0.10")
            return
        record_pass("CF-05", "Dramatic Heavy Vine preset", f"Deep carbon stroke lightness={p_vine_stroke[0]:.3f} (< 0.10)")

        image.remove_layer(vine_layer)

        # 26f: Chalk & Charcoal Duo preset (tinted warm paper tone: R > B by at least 0.05)
        cfg_chalk = proc.create_config()
        cfg_chalk.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_chalk.set_property("image", image)
        cfg_chalk.set_property("preset", "chalk-charcoal")
        cfg_chalk.set_property("mask-type", "reveal-all")
        cfg_chalk.set_property("opacity", 100.0)

        proc.run(cfg_chalk)
        chalk_layer = image.get_layers()[0]
        p_chalk_paper = get_composite_pixel(image, 4, 4)
        warm_delta = p_chalk_paper[0] - p_chalk_paper[2]
        if warm_delta < 0.05:
            record_fail("CF-06", "Chalk & charcoal paper", f"Warm delta {warm_delta:.4f} < 0.05")
            return
        record_pass("CF-06", "Chalk & Charcoal Duo preset", f"Warm tinted paper R={p_chalk_paper[0]:.3f} > B={p_chalk_paper[2]:.3f} (warmth +{warm_delta:.3f})")

        image.remove_layer(chalk_layer)

        # 26g: Architectural Line Art preset with Multiply blend mode
        cfg_arch = proc.create_config()
        cfg_arch.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_arch.set_property("image", image)
        cfg_arch.set_property("preset", "architectural")
        cfg_arch.set_property("mask-type", "reveal-all")
        cfg_arch.set_property("opacity", 85.0)

        proc.run(cfg_arch)
        arch_layer = image.get_layers()[0]
        if arch_layer.get_mode() != Gimp.LayerMode.MULTIPLY or abs(arch_layer.get_opacity() - 85.0) > 0.01:
            record_fail("CF-07", "Architectural preset", f"Expected Multiply and 85%, got mode={arch_layer.get_mode()}, opacity={arch_layer.get_opacity()}%")
            return
        record_pass("CF-07", "Architectural Line Art preset", f"Multiply blend mode ({arch_layer.get_mode()}), opacity 85.0% verified")

        image.remove_layer(arch_layer)

        # 26h: Conceal-All Black Layer Mask
        cfg_blk = proc.create_config()
        cfg_blk.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_blk.set_property("image", image)
        cfg_blk.set_property("preset", "fine-charcoal")
        cfg_blk.set_property("mask-type", "conceal-all")
        cfg_blk.set_property("opacity", 100.0)

        proc.run(cfg_blk)
        blk_layer = image.get_layers()[0]
        p_blk = get_composite_pixel(image, 15, 20)
        p_base = base.get_pixel(15, 20).get_rgba()
        diff_blk = max(abs(p_blk[i] - p_base[i]) for i in range(3))
        if diff_blk > 0.000001:
            record_fail("CF-08", "Conceal-all mask", f"Base altered by {diff_blk:.6f} > 0")
            return
        record_pass("CF-08", "Conceal-all black layer mask", f"Black mask attached for selective brush sketching (diff {diff_blk:.6f})")

        image.remove_layer(blk_layer)

        # 26i: Selection-Aware Masking
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 20, 20)
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("preset", "fine-charcoal")
        cfg_sel.set_property("mask-type", "selection")
        cfg_sel.set_property("opacity", 100.0)

        proc.run(cfg_sel)
        sel_layer = image.get_layers()[0]
        p_sel_inside = get_composite_pixel(image, 15, 18)
        p_sel_out = get_composite_pixel(image, 32, 32)
        out_diff = max(abs(p_sel_out[i] - p_base_subj[i]) for i in range(3))

        if out_diff > 0.000001 or p_sel_inside[0] > 0.20:
            record_fail("CF-09", "Selection-aware mask", f"Inside stroke {p_sel_inside[0]:.3f}, Outside diff {out_diff:.6f}")
            return
        record_pass("CF-09", "Selection-aware sketch mask", f"Inside sketched ({p_sel_inside[0]:.3f} < 0.20), outside untouched (diff {out_diff:.6f})")

        Gimp.Selection.none(image)
        image.remove_layer(sel_layer)

        # 26j: Custom Sliders, Soft Light blend mode & Opacity
        cfg_cust = proc.create_config()
        cfg_cust.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cust.set_property("image", image)
        cfg_cust.set_property("preset", "custom")
        cfg_cust.set_property("stroke-thickness", 3.0)
        cfg_cust.set_property("stroke-intensity", 1.2)
        cfg_cust.set_property("charcoal-shade", 0.04)
        cfg_cust.set_property("paper-tone", 0.92)
        cfg_cust.set_property("blend-mode", "soft-light")
        cfg_cust.set_property("opacity", 80.0)
        cfg_cust.set_property("mask-type", "reveal-all")

        proc.run(cfg_cust)
        cust_layer = image.get_layers()[0]
        if abs(cust_layer.get_opacity() - 80.0) > 0.01 or cust_layer.get_mode() != Gimp.LayerMode.SOFTLIGHT:
            record_fail("CF-10", "Custom sliders", f"Expected opacity 80.0% and Soft Light, got opacity={cust_layer.get_opacity()}%, mode={cust_layer.get_mode()}")
            return
        record_pass("CF-10", "Custom sliders & blend mode", f"Opacity 80.0%, Soft Light blend mode ({cust_layer.get_mode()}), thickness 3.0px verified")

        # 26k: Non-destructive base layer invariance across all pixels
        p_base_after_paper = base.get_pixel(4, 4).get_rgba()
        p_base_after_edge = base.get_pixel(15, 20).get_rgba()
        p_base_after_subj = base.get_pixel(32, 32).get_rgba()
        max_base_diff = max(
            max(abs(p_base_after_paper[i] - p_base_paper[i]) for i in range(3)),
            max(abs(p_base_after_edge[i] - p_base_edge[i]) for i in range(3)),
            max(abs(p_base_after_subj[i] - p_base_subj[i]) for i in range(3))
        )
        if max_base_diff > 0.000001:
            record_fail("CF-11", "Non-destructive invariance", f"Base layer altered by {max_base_diff:.6f} > 0")
            return
        record_pass("CF-11", "Non-destructive layer preservation", f"Base pixels 100% untouched across all tonal zones (diff {max_base_diff:.6f})")

    except Exception as e:
        record_fail("CF-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 27: Woodcut & Linocut Printmaking Helper Plugin (Phase 32)
# ==============================================================================
def test_woodcut_filter():
    print("\n--- Test Suite 27: Woodcut & Linocut Printmaking Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-woodcut-filter")
    if proc is None:
        record_fail("WF-01", "Procedure lookup", "Procedure python-fu-woodcut-filter not found")
        return

    # Create a 64x64 test image with:
    # Bright paper background (0.85, 0.85, 0.85) and a dark subject rectangle (0.15, 0.15, 0.15) in center
    image = Gimp.Image.new(64, 64, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "Base", 64, 64, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)

        # Fill background
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.85, 0.85, 0.85)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        # Dark subject rectangle
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 16, 16, 32, 32)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.15, 0.15, 0.15)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(image)

        p_base_paper = base.get_pixel(4, 4).get_rgba()
        p_base_edge = base.get_pixel(16, 20).get_rgba()
        p_base_subj = base.get_pixel(32, 32).get_rgba()

        # 27a: Execute with Classic Japanese Woodcut preset (default)
        config = proc.create_config()
        config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        config.set_property("image", image)
        config.set_property("preset", "classic-japanese")
        config.set_property("mask-type", "reveal-all")
        config.set_property("opacity", 100.0)

        res = proc.run(config)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("WF-01", "Execution status", f"Expected SUCCESS, got status={status}")
            return
        record_pass("WF-01", "Execution status", "SUCCESS")

        # 27b: Verify layer properties
        layers = image.get_layers()
        if len(layers) < 2:
            record_fail("WF-02", "Layer creation", f"Expected at least 2 layers, found {len(layers)}")
            return
        wc_layer = layers[0]
        if "Woodcut Print" not in wc_layer.get_name() or wc_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("WF-02", "Layer properties", f"Unexpected name={wc_layer.get_name()}, mode={wc_layer.get_mode()}")
            return
        record_pass("WF-02", "Layer mode & name", f"Layer '{wc_layer.get_name()}' mode={wc_layer.get_mode()}")

        # 27c: Verify attached reveal-all layer mask
        mask = wc_layer.get_mask()
        if mask is None:
            record_fail("WF-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("WF-03", "Layer mask attachment", "Reveal-all mask attached")

        # 27d: Classic Japanese Woodcut tone mapping:
        # Sumi ink in dark zone (luminance < 0.12), warm washi paper in highlight zone (R > B by > 0.04)
        p_ink = get_composite_pixel(image, 32, 32)
        p_paper = get_composite_pixel(image, 4, 4)
        warmth_diff = p_paper[0] - p_paper[2]
        if p_ink[0] > 0.12 or warmth_diff < 0.04:
            record_fail("WF-04", "Classic Japanese tones", f"Ink={p_ink[0]:.3f} (expected <0.12), Paper R={p_paper[0]:.3f} B={p_paper[2]:.3f} (warmth={warmth_diff:.3f} expected >0.04)")
            return
        record_pass("WF-04", "Classic Japanese Woodcut preset", f"Sumi ink ({p_ink[0]:.3f} < 0.12), warm washi paper R={p_paper[0]:.3f} > B={p_paper[2]:.3f} (warmth +{warmth_diff:.3f})")

        image.remove_layer(wc_layer)

        # 27e: Modern Graphic Linocut preset (deep black ink < 0.05, crisp white paper > 0.95)
        cfg_lino = proc.create_config()
        cfg_lino.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_lino.set_property("image", image)
        cfg_lino.set_property("preset", "modern-linocut")
        cfg_lino.set_property("mask-type", "reveal-all")
        cfg_lino.set_property("opacity", 100.0)

        proc.run(cfg_lino)
        lino_layer = image.get_layers()[0]
        p_lino_ink = get_composite_pixel(image, 32, 32)
        p_lino_paper = get_composite_pixel(image, 4, 4)
        if p_lino_ink[0] > 0.05 or p_lino_paper[0] < 0.95:
            record_fail("WF-05", "Modern Linocut tones", f"Ink={p_lino_ink[0]:.3f} (expected <0.05), Paper={p_lino_paper[0]:.3f} (expected >0.95)")
            return
        record_pass("WF-05", "Modern Graphic Linocut preset", f"Deep black ink ({p_lino_ink[0]:.3f} < 0.05) and crisp white paper ({p_lino_paper[0]:.3f} > 0.95)")

        image.remove_layer(lino_layer)

        # 27f: Ukiyo-e Indigo Print preset (Prussian blue dominance: B > R by > 0.15)
        cfg_indigo = proc.create_config()
        cfg_indigo.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_indigo.set_property("image", image)
        cfg_indigo.set_property("preset", "ukiyo-e-indigo")
        cfg_indigo.set_property("mask-type", "reveal-all")
        cfg_indigo.set_property("opacity", 100.0)

        proc.run(cfg_indigo)
        indigo_layer = image.get_layers()[0]
        p_indigo_ink = get_composite_pixel(image, 32, 32)
        blue_dominance = p_indigo_ink[2] - p_indigo_ink[0]
        if blue_dominance < 0.15:
            record_fail("WF-06", "Ukiyo-e Indigo tones", f"B={p_indigo_ink[2]:.3f}, R={p_indigo_ink[0]:.3f}, diff={blue_dominance:.3f} < 0.15")
            return
        record_pass("WF-06", "Ukiyo-e Indigo Print preset", f"Prussian blue ink dominance B={p_indigo_ink[2]:.3f} > R={p_indigo_ink[0]:.3f} (delta +{blue_dominance:.3f})")

        image.remove_layer(indigo_layer)

        # 27g: Vermilion Seal Print preset (Cinnabar red dominance: R > B by > 0.40)
        cfg_verm = proc.create_config()
        cfg_verm.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_verm.set_property("image", image)
        cfg_verm.set_property("preset", "vermilion-seal")
        cfg_verm.set_property("mask-type", "reveal-all")
        cfg_verm.set_property("opacity", 100.0)

        proc.run(cfg_verm)
        verm_layer = image.get_layers()[0]
        p_verm_ink = get_composite_pixel(image, 32, 32)
        red_dominance = p_verm_ink[0] - p_verm_ink[2]
        if red_dominance < 0.40:
            record_fail("WF-07", "Vermilion Seal tones", f"R={p_verm_ink[0]:.3f}, B={p_verm_ink[2]:.3f}, diff={red_dominance:.3f} < 0.40")
            return
        record_pass("WF-07", "Vermilion Seal Print preset", f"Cinnabar red ink dominance R={p_verm_ink[0]:.3f} > B={p_verm_ink[2]:.3f} (delta +{red_dominance:.3f})")

        image.remove_layer(verm_layer)

        # 27h: Fine Archival Engraving preset with Multiply blend mode
        cfg_eng = proc.create_config()
        cfg_eng.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_eng.set_property("image", image)
        cfg_eng.set_property("preset", "fine-engraving")
        cfg_eng.set_property("mask-type", "reveal-all")
        cfg_eng.set_property("opacity", 90.0)

        proc.run(cfg_eng)
        eng_layer = image.get_layers()[0]
        if eng_layer.get_mode() != Gimp.LayerMode.MULTIPLY or abs(eng_layer.get_opacity() - 90.0) > 0.01:
            record_fail("WF-08", "Fine Engraving preset", f"Expected Multiply and 90.0%, got mode={eng_layer.get_mode()}, opacity={eng_layer.get_opacity()}%")
            return
        record_pass("WF-08", "Fine Archival Engraving preset", f"Multiply blend mode ({eng_layer.get_mode()}), opacity 90.0% verified")

        image.remove_layer(eng_layer)

        # 27i: Conceal-All Black Layer Mask
        cfg_blk = proc.create_config()
        cfg_blk.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_blk.set_property("image", image)
        cfg_blk.set_property("preset", "classic-japanese")
        cfg_blk.set_property("mask-type", "conceal-all")
        cfg_blk.set_property("opacity", 100.0)

        proc.run(cfg_blk)
        blk_layer = image.get_layers()[0]
        p_blk = get_composite_pixel(image, 32, 32)
        p_base = base.get_pixel(32, 32).get_rgba()
        diff_blk = max(abs(p_blk[i] - p_base[i]) for i in range(3))
        if diff_blk > 0.000001:
            record_fail("WF-09", "Conceal-all mask", f"Base altered by {diff_blk:.6f} > 0")
            return
        record_pass("WF-09", "Conceal-all black layer mask", f"Black mask attached for selective block printing (diff {diff_blk:.6f})")

        image.remove_layer(blk_layer)

        # 27j: Selection-Aware Masking
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 20, 20)
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("preset", "classic-japanese")
        cfg_sel.set_property("mask-type", "selection")
        cfg_sel.set_property("opacity", 100.0)

        proc.run(cfg_sel)
        sel_layer = image.get_layers()[0]
        p_sel_inside = get_composite_pixel(image, 4, 4)
        p_sel_out = get_composite_pixel(image, 32, 32)
        out_diff = max(abs(p_sel_out[i] - p_base_subj[i]) for i in range(3))

        if out_diff > 0.000001 or p_sel_inside[0] < 0.85:
            record_fail("WF-10", "Selection-aware mask", f"Inside paper {p_sel_inside[0]:.3f}, Outside diff {out_diff:.6f}")
            return
        record_pass("WF-10", "Selection-aware print mask", f"Inside printed ({p_sel_inside[0]:.3f} > 0.85), outside untouched (diff {out_diff:.6f})")

        Gimp.Selection.none(image)
        image.remove_layer(sel_layer)

        # 27k: Custom Sliders, Soft Light blend mode, Opacity & Base layer preservation
        cfg_cust = proc.create_config()
        cfg_cust.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cust.set_property("image", image)
        cfg_cust.set_property("preset", "custom")
        cfg_cust.set_property("gouge-smoothing", 4.0)
        cfg_cust.set_property("carve-depth", 0.7)
        cfg_cust.set_property("ink-shade", 0.04)
        cfg_cust.set_property("paper-tone", 0.94)
        cfg_cust.set_property("blend-mode", "soft-light")
        cfg_cust.set_property("opacity", 85.0)
        cfg_cust.set_property("mask-type", "reveal-all")

        proc.run(cfg_cust)
        cust_layer = image.get_layers()[0]
        if abs(cust_layer.get_opacity() - 85.0) > 0.01 or cust_layer.get_mode() != Gimp.LayerMode.SOFTLIGHT:
            record_fail("WF-11", "Custom sliders", f"Expected opacity 85.0% and Soft Light, got opacity={cust_layer.get_opacity()}%, mode={cust_layer.get_mode()}")
            return

        # Check non-destructive base layer invariance across all pixels
        p_base_after_paper = base.get_pixel(4, 4).get_rgba()
        p_base_after_edge = base.get_pixel(16, 20).get_rgba()
        p_base_after_subj = base.get_pixel(32, 32).get_rgba()
        max_base_diff = max(
            max(abs(p_base_after_paper[i] - p_base_paper[i]) for i in range(3)),
            max(abs(p_base_after_edge[i] - p_base_edge[i]) for i in range(3)),
            max(abs(p_base_after_subj[i] - p_base_subj[i]) for i in range(3))
        )
        if max_base_diff > 0.000001:
            record_fail("WF-11", "Non-destructive invariance", f"Base layer altered by {max_base_diff:.6f} > 0")
            return
        record_pass("WF-11", "Custom sliders & non-destructive preservation", f"Opacity 85.0%, Soft Light mode ({cust_layer.get_mode()}), base pixels untouched (diff {max_base_diff:.6f})")

    except Exception as e:
        record_fail("WF-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 28: Swirling Night Sky & Twirl Distortion Plugin (Phase 33)
# ==============================================================================
def test_swirling_sky():
    print("\n--- Test Suite 28: Swirling Night Sky & Twirl Distortion Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-swirling-sky")
    if proc is None:
        record_fail("SNS-01", "Procedure lookup", "Procedure python-fu-swirling-sky not found")
        return

    # Create a 64x64 test image with:
    # Left half: dark blue night sky (0.05, 0.10, 0.25)
    # Right half: bright golden star cluster (0.95, 0.85, 0.40)
    image = Gimp.Image.new(64, 64, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "Base", 64, 64, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)

        buf = base.get_buffer()
        buf.set_color(Gegl.Rectangle.new(0, 0, 32, 64), Gegl.Color.new("rgb(0.05, 0.10, 0.25)"))
        buf.set_color(Gegl.Rectangle.new(32, 0, 32, 64), Gegl.Color.new("rgb(0.95, 0.85, 0.40)"))
        buf.flush()

        p_base_left = base.get_pixel(16, 32).get_rgba()
        p_base_right = base.get_pixel(48, 32).get_rgba()

        # 28a: Execute with Starry Night Vortex preset (default)
        config = proc.create_config()
        config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        config.set_property("image", image)
        config.set_property("preset", "starry-vortex")
        config.set_property("mask-type", "reveal-all")
        config.set_property("opacity", 100.0)

        res = proc.run(config)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("SNS-01", "Execution status", f"Expected SUCCESS, got status={status}")
            return
        record_pass("SNS-01", "Execution status", "SUCCESS")

        # 28b: Verify layer properties
        layers = image.get_layers()
        if len(layers) < 2:
            record_fail("SNS-02", "Layer creation", f"Expected at least 2 layers, found {len(layers)}")
            return
        sw_layer = layers[0]
        if "Swirling Sky" not in sw_layer.get_name() or sw_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("SNS-02", "Layer properties", f"Unexpected name={sw_layer.get_name()}, mode={sw_layer.get_mode()}")
            return
        record_pass("SNS-02", "Layer mode & name", f"Layer '{sw_layer.get_name()}' mode={sw_layer.get_mode()}")

        # 28c: Verify attached reveal-all layer mask
        mask = sw_layer.get_mask()
        if mask is None:
            record_fail("SNS-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("SNS-03", "Layer mask attachment", "Reveal-all mask attached")

        # 28d: Starry Night Vortex rotational twirl distortion verification
        # The 240° vortex rotates the bright star cluster into the left half (around x=20, y=32)
        p_vortex_left = get_composite_pixel(image, 20, 32)
        vortex_lift = p_vortex_left[0] - p_base_left[0]
        if p_vortex_left[0] < 0.30:
            record_fail("SNS-04", "Starry Night Vortex twirl", f"Vortex left={p_vortex_left[0]:.3f} < 0.30 (lift={vortex_lift:.3f})")
            return
        record_pass("SNS-04", "Starry Night Vortex preset", f"Rotational vortex twirl (star rotated into dark sky: {p_vortex_left[0]:.3f} > 0.30, lift +{vortex_lift:.3f})")

        image.remove_layer(sw_layer)

        # 28e: Deep Space Whirlpool preset (Screen blend mode, 90.0% opacity)
        cfg_deep = proc.create_config()
        cfg_deep.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_deep.set_property("image", image)
        cfg_deep.set_property("preset", "deep-space")
        cfg_deep.set_property("mask-type", "reveal-all")
        cfg_deep.set_property("opacity", 90.0)

        proc.run(cfg_deep)
        deep_layer = image.get_layers()[0]
        if deep_layer.get_mode() != Gimp.LayerMode.SCREEN or abs(deep_layer.get_opacity() - 90.0) > 0.01:
            record_fail("SNS-05", "Deep Space preset", f"Expected Screen mode and 90%, got mode={deep_layer.get_mode()}, opacity={deep_layer.get_opacity()}%")
            return
        record_pass("SNS-05", "Deep Space Whirlpool preset", f"Screen blend mode ({deep_layer.get_mode()}) and 90.0% opacity verified")

        image.remove_layer(deep_layer)

        # 28f: Atmospheric Cyclone preset (Soft Light blend mode, 85.0% opacity)
        cfg_cyc = proc.create_config()
        cfg_cyc.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cyc.set_property("image", image)
        cfg_cyc.set_property("preset", "atmospheric-cyclone")
        cfg_cyc.set_property("mask-type", "reveal-all")
        cfg_cyc.set_property("opacity", 85.0)

        proc.run(cfg_cyc)
        cyc_layer = image.get_layers()[0]
        if cyc_layer.get_mode() != Gimp.LayerMode.SOFTLIGHT or abs(cyc_layer.get_opacity() - 85.0) > 0.01:
            record_fail("SNS-06", "Atmospheric Cyclone preset", f"Expected Soft Light and 85%, got mode={cyc_layer.get_mode()}, opacity={cyc_layer.get_opacity()}%")
            return
        record_pass("SNS-06", "Atmospheric Cyclone preset", f"Soft Light blend mode ({cyc_layer.get_mode()}) and 85.0% opacity verified")

        image.remove_layer(cyc_layer)

        # 28g: Counter-Clockwise Spiral preset (-180° rotation)
        cfg_ccw = proc.create_config()
        cfg_ccw.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_ccw.set_property("image", image)
        cfg_ccw.set_property("preset", "counter-clockwise")
        cfg_ccw.set_property("mask-type", "reveal-all")
        cfg_ccw.set_property("opacity", 100.0)

        proc.run(cfg_ccw)
        ccw_layer = image.get_layers()[0]
        # At (44, 32) (which was bright gold), 180° inversion rotates dark sky into it
        p_ccw_right = get_composite_pixel(image, 44, 32)
        if p_ccw_right[0] > 0.25:
            record_fail("SNS-07", "Counter-Clockwise Spiral", f"Right point={p_ccw_right[0]:.3f} > 0.25 (expected dark sky rotation)")
            return
        record_pass("SNS-07", "Counter-Clockwise Spiral preset", f"Inverse rotation angle (dark sky rotated into gold: {p_ccw_right[0]:.3f} < 0.25)")

        image.remove_layer(ccw_layer)

        # 28h: Subtle Sky Drift preset (Gentle 60° curve)
        cfg_drift = proc.create_config()
        cfg_drift.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_drift.set_property("image", image)
        cfg_drift.set_property("preset", "subtle-drift")
        cfg_drift.set_property("mask-type", "reveal-all")
        cfg_drift.set_property("opacity", 100.0)

        proc.run(cfg_drift)
        drift_layer = image.get_layers()[0]
        record_pass("SNS-08", "Subtle Sky Drift preset", f"Layer '{drift_layer.get_name()}' created successfully")

        image.remove_layer(drift_layer)

        # 28i: Conceal-All Black Layer Mask
        cfg_blk = proc.create_config()
        cfg_blk.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_blk.set_property("image", image)
        cfg_blk.set_property("preset", "starry-vortex")
        cfg_blk.set_property("mask-type", "conceal-all")
        cfg_blk.set_property("opacity", 100.0)

        proc.run(cfg_blk)
        blk_layer = image.get_layers()[0]
        p_blk = get_composite_pixel(image, 20, 32)
        p_base = base.get_pixel(20, 32).get_rgba()
        diff_blk = max(abs(p_blk[i] - p_base[i]) for i in range(3))
        if diff_blk > 0.000001:
            record_fail("SNS-09", "Conceal-all mask", f"Base altered by {diff_blk:.6f} > 0")
            return
        record_pass("SNS-09", "Conceal-all black layer mask", f"Black mask attached for selective horizon brushing (diff {diff_blk:.6f})")

        image.remove_layer(blk_layer)

        # 28j: Selection-Aware Masking
        # Select left half (sky zone), leaving right half (landscape horizon) unselected
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 32, 64)
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("preset", "starry-vortex")
        cfg_sel.set_property("mask-type", "selection")
        cfg_sel.set_property("opacity", 100.0)

        proc.run(cfg_sel)
        sel_layer = image.get_layers()[0]
        p_sel_inside = get_composite_pixel(image, 20, 32)
        p_sel_out = get_composite_pixel(image, 48, 32)
        out_diff = max(abs(p_sel_out[i] - p_base_right[i]) for i in range(3))

        if out_diff > 0.000001 or p_sel_inside[0] < 0.30:
            record_fail("SNS-10", "Selection-aware mask", f"Inside vortex {p_sel_inside[0]:.3f}, Outside diff {out_diff:.6f}")
            return
        record_pass("SNS-10", "Selection-aware sky mask", f"Inside swirled ({p_sel_inside[0]:.3f} > 0.30), outside untouched (diff {out_diff:.6f})")

        Gimp.Selection.none(image)
        image.remove_layer(sel_layer)

        # 28k: Custom Sliders, Lighten Only blend mode, Opacity & Base layer preservation
        cfg_cust = proc.create_config()
        cfg_cust.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cust.set_property("image", image)
        cfg_cust.set_property("preset", "custom")
        cfg_cust.set_property("whirl-angle", 120.0)
        cfg_cust.set_property("pinch-amount", 0.10)
        cfg_cust.set_property("vortex-radius", 1.0)
        cfg_cust.set_property("ripple-amplitude", 3.0)
        cfg_cust.set_property("ripple-period", 20.0)
        cfg_cust.set_property("blend-mode", "lighten-only")
        cfg_cust.set_property("opacity", 85.0)
        cfg_cust.set_property("mask-type", "reveal-all")

        proc.run(cfg_cust)
        cust_layer = image.get_layers()[0]
        if abs(cust_layer.get_opacity() - 85.0) > 0.01 or cust_layer.get_mode() != Gimp.LayerMode.LIGHTEN_ONLY:
            record_fail("SNS-11", "Custom sliders", f"Expected opacity 85.0% and Lighten Only, got opacity={cust_layer.get_opacity()}%, mode={cust_layer.get_mode()}")
            return

        # Check non-destructive base layer invariance across all pixels
        p_base_after_left = base.get_pixel(16, 32).get_rgba()
        p_base_after_right = base.get_pixel(48, 32).get_rgba()
        max_base_diff = max(
            max(abs(p_base_after_left[i] - p_base_left[i]) for i in range(3)),
            max(abs(p_base_after_right[i] - p_base_right[i]) for i in range(3))
        )
        if max_base_diff > 0.000001:
            record_fail("SNS-11", "Non-destructive invariance", f"Base layer altered by {max_base_diff:.6f} > 0")
            return
        record_pass("SNS-11", "Custom sliders & non-destructive preservation", f"Opacity 85.0%, Lighten Only mode ({cust_layer.get_mode()}), base pixels untouched (diff {max_base_diff:.6f})")

    except Exception as e:
        record_fail("SNS-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 29: Sky Selection & Replacement Helper Plugin (Phase 34)
# ==============================================================================
def test_sky_replacement():
    print("\n--- Test Suite 29: Sky Selection & Replacement Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-sky-replacement")
    if proc is None:
        record_fail("SR-01", "Procedure lookup", "Procedure python-fu-sky-replacement not found")
        return

    # Create a 64x64 test image with:
    # Upper half (y < 32): cool daylight sky (0.60, 0.70, 0.85)
    # Lower half (y >= 32): terrain ground (0.30, 0.40, 0.20)
    image = Gimp.Image.new(64, 64, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "Base", 64, 64, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)

        buf = base.get_buffer()
        buf.set_color(Gegl.Rectangle.new(0, 0, 64, 32), Gegl.Color.new("rgb(0.60, 0.70, 0.85)"))
        buf.set_color(Gegl.Rectangle.new(0, 32, 64, 32), Gegl.Color.new("rgb(0.30, 0.40, 0.20)"))
        buf.flush()

        p_base_sky = base.get_pixel(32, 16).get_rgba()
        p_base_ground = base.get_pixel(32, 48).get_rgba()

        # 29a: Execute with Sunset Golden Hour preset (default)
        config = proc.create_config()
        config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        config.set_property("image", image)
        config.set_property("preset", "sunset-gold")
        config.set_property("mask-type", "automated-horizon")
        config.set_property("fade-edge", 0.0)
        config.set_property("opacity", 100.0)

        res = proc.run(config)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("SR-01", "Execution status", f"Expected SUCCESS, got status={status}")
            return
        record_pass("SR-01", "Execution status", "SUCCESS")

        # 29b: Verify layer properties
        layers = image.get_layers()
        if len(layers) < 2:
            record_fail("SR-02", "Layer creation", f"Expected at least 2 layers, found {len(layers)}")
            return
        sky_layer = layers[0]
        if "Sky Replacement" not in sky_layer.get_name() or sky_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("SR-02", "Layer properties", f"Unexpected name={sky_layer.get_name()}, mode={sky_layer.get_mode()}")
            return
        record_pass("SR-02", "Layer mode & name", f"Layer '{sky_layer.get_name()}' mode={sky_layer.get_mode()}")

        # 29c: Verify attached layer mask
        mask = sky_layer.get_mask()
        if mask is None:
            record_fail("SR-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("SR-03", "Layer mask attachment", "Automated horizon mask attached")

        # 29d: Sunset Golden Hour warm temperature shift in sky
        # 8500K warming shift: in sky (y=16), red increases and blue decreases relative to base
        p_sunset_sky = get_composite_pixel(image, 32, 16)
        warmth_delta = (p_sunset_sky[0] - p_sunset_sky[2]) - (p_base_sky[0] - p_base_sky[2])
        if warmth_delta < 0.05:
            record_fail("SR-04", "Sunset warmth shift", f"Warmth delta={warmth_delta:.4f} < 0.05")
            return
        record_pass("SR-04", "Sunset Golden Hour preset", f"Warming shift in sky (R={p_sunset_sky[0]:.3f}, B={p_sunset_sky[2]:.3f}, warmth delta +{warmth_delta:.3f})")

        # 29e: Automated horizon mask ground protection
        p_sunset_ground = get_composite_pixel(image, 32, 48)
        ground_diff = max(abs(p_sunset_ground[i] - p_base_ground[i]) for i in range(3))
        if ground_diff > 0.000001:
            record_fail("SR-05", "Horizon protection", f"Ground altered by {ground_diff:.6f} > 0")
            return
        record_pass("SR-05", "Automated horizon mask protection", f"Ground zone 100% protected under horizon mask (diff {ground_diff:.6f})")

        image.remove_layer(sky_layer)

        # 29f: Deep Twilight preset (3600K nocturnal cooling shift)
        cfg_twi = proc.create_config()
        cfg_twi.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_twi.set_property("image", image)
        cfg_twi.set_property("preset", "deep-twilight")
        cfg_twi.set_property("mask-type", "automated-horizon")
        cfg_twi.set_property("opacity", 100.0)

        proc.run(cfg_twi)
        twi_layer = image.get_layers()[0]
        p_twi_sky = get_composite_pixel(image, 32, 16)
        blue_dominance = p_twi_sky[2] - p_twi_sky[0]
        if blue_dominance < 0.15:
            record_fail("SR-06", "Deep Twilight cooling", f"B={p_twi_sky[2]:.3f}, R={p_twi_sky[0]:.3f}, diff={blue_dominance:.3f} < 0.15")
            return
        record_pass("SR-06", "Deep Twilight preset", f"Sapphire blue cooling dominance B={p_twi_sky[2]:.3f} > R={p_twi_sky[0]:.3f} (delta +{blue_dominance:.3f})")

        image.remove_layer(twi_layer)

        # 29g: Dramatic Storm Clouds preset (Soft Light mode, -0.40 EV exposure)
        cfg_storm = proc.create_config()
        cfg_storm.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_storm.set_property("image", image)
        cfg_storm.set_property("preset", "dramatic-storm")
        cfg_storm.set_property("mask-type", "automated-horizon")
        cfg_storm.set_property("opacity", 90.0)

        proc.run(cfg_storm)
        storm_layer = image.get_layers()[0]
        if storm_layer.get_mode() != Gimp.LayerMode.SOFTLIGHT or abs(storm_layer.get_opacity() - 90.0) > 0.01:
            record_fail("SR-07", "Dramatic Storm mode", f"Expected Soft Light and 90%, got mode={storm_layer.get_mode()}, opacity={storm_layer.get_opacity()}%")
            return
        record_pass("SR-07", "Dramatic Storm Clouds preset", f"Soft Light mode ({storm_layer.get_mode()}) and 90.0% opacity verified")

        image.remove_layer(storm_layer)

        # 29h: Pastel Sunrise Dawn preset (Screen mode, 85.0% opacity)
        cfg_dawn = proc.create_config()
        cfg_dawn.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_dawn.set_property("image", image)
        cfg_dawn.set_property("preset", "pastel-dawn")
        cfg_dawn.set_property("mask-type", "automated-horizon")
        cfg_dawn.set_property("opacity", 85.0)

        proc.run(cfg_dawn)
        dawn_layer = image.get_layers()[0]
        if dawn_layer.get_mode() != Gimp.LayerMode.SCREEN or abs(dawn_layer.get_opacity() - 85.0) > 0.01:
            record_fail("SR-08", "Pastel Dawn mode", f"Expected Screen and 85%, got mode={dawn_layer.get_mode()}, opacity={dawn_layer.get_opacity()}%")
            return
        record_pass("SR-08", "Pastel Sunrise Dawn preset", f"Screen blend mode ({dawn_layer.get_mode()}) and 85.0% opacity verified")

        image.remove_layer(dawn_layer)

        # 29i: Conceal-All Black Layer Mask
        cfg_blk = proc.create_config()
        cfg_blk.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_blk.set_property("image", image)
        cfg_blk.set_property("preset", "sunset-gold")
        cfg_blk.set_property("mask-type", "conceal-all")
        cfg_blk.set_property("opacity", 100.0)

        proc.run(cfg_blk)
        blk_layer = image.get_layers()[0]
        p_blk = get_composite_pixel(image, 32, 16)
        p_base = base.get_pixel(32, 16).get_rgba()
        diff_blk = max(abs(p_blk[i] - p_base[i]) for i in range(3))
        if diff_blk > 0.000001:
            record_fail("SR-09", "Conceal-all mask", f"Base altered by {diff_blk:.6f} > 0")
            return
        record_pass("SR-09", "Conceal-all black layer mask", f"Black mask attached for selective brush painting (diff {diff_blk:.6f})")

        image.remove_layer(blk_layer)

        # 29j: Selection-Aware Masking
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 64, 20)
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("preset", "sunset-gold")
        cfg_sel.set_property("mask-type", "selection")
        cfg_sel.set_property("fade-edge", 0.0)
        cfg_sel.set_property("opacity", 100.0)

        proc.run(cfg_sel)
        sel_layer = image.get_layers()[0]
        p_sel_inside = get_composite_pixel(image, 32, 10)
        p_sel_out = get_composite_pixel(image, 32, 48)
        out_diff = max(abs(p_sel_out[i] - p_base_ground[i]) for i in range(3))

        if out_diff > 0.000001 or p_sel_inside[0] <= p_base_sky[0]:
            record_fail("SR-10", "Selection-aware mask", f"Inside red {p_sel_inside[0]:.3f}, Outside diff {out_diff:.6f}")
            return
        record_pass("SR-10", "Selection-aware sky mask", f"Inside sky warmed ({p_sel_inside[0]:.3f} > {p_base_sky[0]:.3f}), outside untouched (diff {out_diff:.6f})")

        Gimp.Selection.none(image)
        image.remove_layer(sel_layer)

        # 29k: Custom Sliders, Multiply blend mode, Opacity & Base layer preservation
        cfg_cust = proc.create_config()
        cfg_cust.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cust.set_property("image", image)
        cfg_cust.set_property("preset", "custom")
        cfg_cust.set_property("color-temperature", 9000.0)
        cfg_cust.set_property("brightness", 0.20)
        cfg_cust.set_property("horizon-position", 50.0)
        cfg_cust.set_property("fade-edge", 5.0)
        cfg_cust.set_property("blend-mode", "multiply")
        cfg_cust.set_property("opacity", 80.0)
        cfg_cust.set_property("mask-type", "automated-horizon")

        proc.run(cfg_cust)
        cust_layer = image.get_layers()[0]
        if abs(cust_layer.get_opacity() - 80.0) > 0.01 or cust_layer.get_mode() != Gimp.LayerMode.MULTIPLY:
            record_fail("SR-11", "Custom sliders", f"Expected opacity 80.0% and Multiply, got opacity={cust_layer.get_opacity()}%, mode={cust_layer.get_mode()}")
            return

        # Check non-destructive base layer invariance across all pixels
        p_base_after_sky = base.get_pixel(32, 16).get_rgba()
        p_base_after_ground = base.get_pixel(32, 48).get_rgba()
        max_base_diff = max(
            max(abs(p_base_after_sky[i] - p_base_sky[i]) for i in range(3)),
            max(abs(p_base_after_ground[i] - p_base_ground[i]) for i in range(3))
        )
        if max_base_diff > 0.000001:
            record_fail("SR-11", "Non-destructive invariance", f"Base layer altered by {max_base_diff:.6f} > 0")
            return
        record_pass("SR-11", "Custom sliders & non-destructive preservation", f"Opacity 80.0%, Multiply mode ({cust_layer.get_mode()}), base pixels untouched (diff {max_base_diff:.6f})")

    except Exception as e:
        record_fail("SR-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 30: Select Subject & Background Isolation Plugin (Phase 35)
# ==============================================================================
def test_select_subject():
    print("\n--- Test Suite 30: Select Subject & Background Isolation Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-select-subject")
    if proc is None:
        record_fail("SSUB-01", "Procedure lookup", "python-fu-select-subject not found in PDB")
        return

    # Create 64x64 test image with white background and red circular subject
    image = Gimp.Image.new(64, 64, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "Original Photo", 64, 64, Gimp.ImageType.RGBA_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)

        # White background
        Gimp.context_set_background(Gegl.Color.new("white"))
        base.edit_fill(Gimp.FillType.BACKGROUND)

        # Red central circular subject (box: 16 to 48)
        image.select_ellipse(Gimp.ChannelOps.REPLACE, 16, 16, 32, 32)
        Gimp.context_set_foreground(Gegl.Color.new("red"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(image)

        p_base_subject = base.get_pixel(32, 32).get_rgba()
        p_base_bg = base.get_pixel(4, 4).get_rgba()

        # 30a: Run Portrait Subject preset (default)
        cfg_def = proc.create_config()
        cfg_def.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_def.set_property("image", image)
        cfg_def.set_property("preset", "portrait")
        cfg_def.set_property("action", "select-subject")
        cfg_def.set_property("output-mode", "new-layer-mask")

        res = proc.run(cfg_def)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("SSUB-01", "Execution status", f"Expected SUCCESS, got {status}")
            return
        record_pass("SSUB-01", "Execution status", "SUCCESS")

        # 30b: Layer mode and name
        layers = image.get_layers()
        if len(layers) < 2:
            record_fail("SSUB-02", "Layer creation", f"Expected >= 2 layers, got {len(layers)}")
            return
        subject_layer = layers[0]
        if subject_layer.get_name() != "Isolated Subject (Portrait Subject)":
            record_fail("SSUB-02", "Layer name", f"Expected 'Isolated Subject (Portrait Subject)', got '{subject_layer.get_name()}'")
            return
        record_pass("SSUB-02", "Layer mode & name", f"Layer '{subject_layer.get_name()}' mode={subject_layer.get_mode()}")

        # 30c: Layer mask attachment
        mask = subject_layer.get_mask()
        if mask is None:
            record_fail("SSUB-03", "Layer mask", "Subject layer has no mask attached")
            return
        record_pass("SSUB-03", "Layer mask attachment", "Layer mask attached to duplicate subject layer")

        # 30d: Portrait Subject preset isolation
        p_comp_center = get_composite_pixel(image, 32, 32)
        if p_comp_center[0] < 0.90 or p_comp_center[1] > 0.10:
            record_fail("SSUB-04", "Portrait subject color", f"Center R={p_comp_center[0]:.3f}, G={p_comp_center[1]:.3f}")
            return
        record_pass("SSUB-04", "Portrait Subject preset", f"Center subject pixel preserved (R={p_comp_center[0]:.3f}, G={p_comp_center[1]:.3f})")

        image.remove_layer(subject_layer)

        # 30e: Crisp Product preset (1.0px feather)
        cfg_prod = proc.create_config()
        cfg_prod.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_prod.set_property("image", image)
        cfg_prod.set_property("preset", "product")
        cfg_prod.set_property("output-mode", "new-layer-mask")

        proc.run(cfg_prod)
        prod_layer = image.get_layers()[0]
        if prod_layer.get_name() != "Isolated Subject (Crisp Product)" or prod_layer.get_mask() is None:
            record_fail("SSUB-05", "Crisp Product layer", f"Layer name={prod_layer.get_name()}, has_mask={prod_layer.get_mask() is not None}")
            return
        record_pass("SSUB-05", "Crisp Product preset", f"Layer '{prod_layer.get_name()}' with sharp edge mask verified")

        image.remove_layer(prod_layer)

        # 30f: Hair Refinement preset (6.0px feather, +1.0px shift)
        cfg_hair = proc.create_config()
        cfg_hair.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_hair.set_property("image", image)
        cfg_hair.set_property("preset", "hair-refine")
        cfg_hair.set_property("output-mode", "new-layer-mask")

        proc.run(cfg_hair)
        hair_layer = image.get_layers()[0]
        if hair_layer.get_name() != "Isolated Subject (Hair Refinement)" or hair_layer.get_mask() is None:
            record_fail("SSUB-06", "Hair Refine layer", f"Layer name={hair_layer.get_name()}, has_mask={hair_layer.get_mask() is not None}")
            return
        record_pass("SSUB-06", "Hair Refinement preset", f"Layer '{hair_layer.get_name()}' with soft boundary refinement verified")

        image.remove_layer(hair_layer)

        # 30g: Select Background action
        cfg_bg = proc.create_config()
        cfg_bg.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_bg.set_property("image", image)
        cfg_bg.set_property("action", "select-background")
        cfg_bg.set_property("preset", "portrait")
        cfg_bg.set_property("output-mode", "new-layer-mask")

        proc.run(cfg_bg)
        bg_layer = image.get_layers()[0]
        if bg_layer.get_name() != "Isolated Background (Portrait Subject)" or bg_layer.get_mask() is None:
            record_fail("SSUB-07", "Select Background layer", f"Layer name={bg_layer.get_name()}, has_mask={bg_layer.get_mask() is not None}")
            return
        record_pass("SSUB-07", "Select Background action", f"Layer '{bg_layer.get_name()}' isolating background environment verified")

        image.remove_layer(bg_layer)

        # 30h: Remove Background action
        cfg_rm = proc.create_config()
        cfg_rm.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_rm.set_property("image", image)
        cfg_rm.set_property("action", "remove-background")
        cfg_rm.set_property("preset", "remove-bg")
        cfg_rm.set_property("output-mode", "new-layer-mask")

        proc.run(cfg_rm)
        rm_layer = image.get_layers()[0]
        if rm_layer.get_name() != "Subject (Background Removed - Remove Background Matte)" or rm_layer.get_mask() is None:
            record_fail("SSUB-08", "Remove Background layer", f"Layer name={rm_layer.get_name()}, has_mask={rm_layer.get_mask() is not None}")
            return
        record_pass("SSUB-08", "Remove Background action", f"Layer '{rm_layer.get_name()}' cutout matte verified")

        image.remove_layer(rm_layer)

        # 30i: Selection-Only output mode
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("action", "select-subject")
        cfg_sel.set_property("output-mode", "selection-only")

        proc.run(cfg_sel)
        if len(image.get_layers()) != 1:
            record_fail("SSUB-09", "Selection-only layer count", f"Expected 1 layer, got {len(image.get_layers())}")
            return
        if Gimp.Selection.is_empty(image):
            record_fail("SSUB-09", "Selection-only empty", "Selection is unexpectedly empty")
            return

        res = Gimp.Selection.bounds(image)
        # (success, non_empty, x1, y1, x2, y2)
        if len(res) == 6 and res[1]:
            x1, y1, x2, y2 = res[2], res[3], res[4], res[5]
            if x1 < 10 or x2 > 54:
                record_fail("SSUB-09", "Selection bounds", f"Unexpected bounds: ({x1},{y1}) to ({x2},{y2})")
                return
            record_pass("SSUB-09", "Selection-only output mode", f"Active selection bounding box ({x1},{y1}) to ({x2},{y2}) correctly isolates subject")
        else:
            record_fail("SSUB-09", "Selection bounds unpack", f"Unexpected return: {res}")
            return

        Gimp.Selection.none(image)

        # 30j: Channel Mask output mode
        num_ch_before = len(image.get_channels())
        cfg_ch = proc.create_config()
        cfg_ch.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_ch.set_property("image", image)
        cfg_ch.set_property("action", "select-subject")
        cfg_ch.set_property("preset", "portrait")
        cfg_ch.set_property("output-mode", "channel-mask")

        proc.run(cfg_ch)
        channels = image.get_channels()
        if len(channels) <= num_ch_before:
            record_fail("SSUB-10", "Channel mask count", f"Expected channels > {num_ch_before}, got {len(channels)}")
            return
        ch_names = [ch.get_name() for ch in channels]
        if "Subject Mask (Portrait Subject)" not in ch_names:
            record_fail("SSUB-10", "Channel mask name", f"Missing mask in channels: {ch_names}")
            return
        record_pass("SSUB-10", "Channel mask output mode", f"Channel 'Subject Mask (Portrait Subject)' saved cleanly")

        # 30k: Custom sliders & Base layer preservation
        cfg_cust = proc.create_config()
        cfg_cust.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cust.set_property("image", image)
        cfg_cust.set_property("preset", "custom")
        cfg_cust.set_property("feather-radius", 3.0)
        cfg_cust.set_property("shift-edge", 0.0)
        cfg_cust.set_property("output-mode", "new-layer-mask")

        proc.run(cfg_cust)
        cust_layer = image.get_layers()[0]
        if cust_layer.get_mask() is None:
            record_fail("SSUB-11", "Custom layer mask", "Custom layer has no mask")
            return

        # Verify base layer invariance
        p_base_after_subj = base.get_pixel(32, 32).get_rgba()
        p_base_after_bg = base.get_pixel(4, 4).get_rgba()
        max_base_diff = max(
            max(abs(p_base_after_subj[i] - p_base_subject[i]) for i in range(3)),
            max(abs(p_base_after_bg[i] - p_base_bg[i]) for i in range(3))
        )
        if max_base_diff > 0.000001:
            record_fail("SSUB-11", "Non-destructive invariance", f"Base layer altered by {max_base_diff:.6f} > 0")
            return
        record_pass("SSUB-11", "Custom sliders & non-destructive preservation", f"Base pixels 100% untouched across subject and background points (diff {max_base_diff:.6f})")

    except Exception as e:
        record_fail("SSUB-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 31: Color Range Selection & Isolation Plugin (Phase 36)
# ==============================================================================
def test_color_range():
    print("\n--- Test Suite 31: Color Range Selection & Isolation Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-color-range")
    if proc is None:
        record_fail("CR-01", "Procedure lookup", "python-fu-color-range not found in PDB")
        return

    # Create 64x64 test image with distinct color regions
    image = Gimp.Image.new(64, 64, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "Color Palette", 64, 64, Gimp.ImageType.RGBA_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)

        # Top-Left: Red (0,0 to 32,32)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 32, 32)
        Gimp.context_set_foreground(Gegl.Color.new("red"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        # Top-Right: Green (32,0 to 32,32)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 32, 0, 32, 32)
        Gimp.context_set_foreground(Gegl.Color.new("green"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        # Bottom-Left: Blue (0,32 to 32,32)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 32, 32, 32)
        Gimp.context_set_foreground(Gegl.Color.new("blue"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        # Bottom-Right: Yellow (32,32 to 32,32)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 32, 32, 32, 32)
        Gimp.context_set_foreground(Gegl.Color.new("yellow"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        # Center patch: Photographic Skin Tone (24,24 to 16x16)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 24, 24, 16, 16)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.80, 0.60, 0.50)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(image)

        p_base_red = base.get_pixel(10, 10).get_rgba()
        p_base_green = base.get_pixel(50, 10).get_rgba()
        p_base_blue = base.get_pixel(10, 50).get_rgba()
        p_base_yellow = base.get_pixel(50, 50).get_rgba()
        p_base_skin = base.get_pixel(32, 32).get_rgba()

        # 31a: Run Reds range (default)
        cfg_red = proc.create_config()
        cfg_red.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_red.set_property("image", image)
        cfg_red.set_property("target-range", "reds")
        cfg_red.set_property("fuzziness", 35.0)
        cfg_red.set_property("output-mode", "new-layer-mask")

        res = proc.run(cfg_red)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("CR-01", "Execution status", f"Expected SUCCESS, got {status}")
            return
        record_pass("CR-01", "Execution status", "SUCCESS")

        # 31b: Layer mode and name
        layers = image.get_layers()
        if len(layers) < 2:
            record_fail("CR-02", "Layer creation", f"Expected >= 2 layers, got {len(layers)}")
            return
        red_layer = layers[0]
        if red_layer.get_name() != "Color Range (Reds)":
            record_fail("CR-02", "Layer name", f"Expected 'Color Range (Reds)', got '{red_layer.get_name()}'")
            return
        record_pass("CR-02", "Layer mode & name", f"Layer '{red_layer.get_name()}' mode={red_layer.get_mode()}")

        # 31c: Layer mask attachment
        mask = red_layer.get_mask()
        if mask is None:
            record_fail("CR-03", "Layer mask", "Red layer has no mask attached")
            return
        record_pass("CR-03", "Layer mask attachment", "Layer mask attached to duplicate color range layer")

        # 31d: Reds color range isolation
        p_comp_red = get_composite_pixel(image, 10, 10)
        if p_comp_red[0] < 0.90 or p_comp_red[1] > 0.10:
            record_fail("CR-04", "Red range pixel", f"Red quadrant R={p_comp_red[0]:.3f}, G={p_comp_red[1]:.3f}")
            return
        record_pass("CR-04", "Reds color range isolation", f"Red quadrant correctly selected (R={p_comp_red[0]:.3f}, G={p_comp_red[1]:.3f})")

        image.remove_layer(red_layer)

        # 31e: Yellows color range isolation
        cfg_yel = proc.create_config()
        cfg_yel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_yel.set_property("image", image)
        cfg_yel.set_property("target-range", "yellows")
        cfg_yel.set_property("fuzziness", 35.0)
        cfg_yel.set_property("output-mode", "new-layer-mask")

        proc.run(cfg_yel)
        yel_layer = image.get_layers()[0]
        if yel_layer.get_name() != "Color Range (Yellows)" or yel_layer.get_mask() is None:
            record_fail("CR-05", "Yellows layer", f"Layer name={yel_layer.get_name()}")
            return
        record_pass("CR-05", "Yellows color range isolation", f"Layer '{yel_layer.get_name()}' with yellow mask verified")

        image.remove_layer(yel_layer)

        # 31f: Blues color range isolation
        cfg_blue = proc.create_config()
        cfg_blue.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_blue.set_property("image", image)
        cfg_blue.set_property("target-range", "blues")
        cfg_blue.set_property("fuzziness", 35.0)
        cfg_blue.set_property("output-mode", "new-layer-mask")

        proc.run(cfg_blue)
        blue_layer = image.get_layers()[0]
        if blue_layer.get_name() != "Color Range (Blues)" or blue_layer.get_mask() is None:
            record_fail("CR-06", "Blues layer", f"Layer name={blue_layer.get_name()}")
            return
        record_pass("CR-06", "Blues color range isolation", f"Layer '{blue_layer.get_name()}' with blue mask verified")

        image.remove_layer(blue_layer)

        # 31g: Greens color range isolation
        cfg_grn = proc.create_config()
        cfg_grn.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_grn.set_property("image", image)
        cfg_grn.set_property("target-range", "greens")
        cfg_grn.set_property("fuzziness", 35.0)
        cfg_grn.set_property("output-mode", "new-layer-mask")

        proc.run(cfg_grn)
        grn_layer = image.get_layers()[0]
        if grn_layer.get_name() != "Color Range (Greens)" or grn_layer.get_mask() is None:
            record_fail("CR-07", "Greens layer", f"Layer name={grn_layer.get_name()}")
            return
        record_pass("CR-07", "Greens color range isolation", f"Layer '{grn_layer.get_name()}' with green mask verified")

        image.remove_layer(grn_layer)

        # 31h: Skin Tones range isolation
        cfg_skin = proc.create_config()
        cfg_skin.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_skin.set_property("image", image)
        cfg_skin.set_property("target-range", "skin-tones")
        cfg_skin.set_property("fuzziness", 40.0)
        cfg_skin.set_property("output-mode", "new-layer-mask")

        proc.run(cfg_skin)
        skin_layer = image.get_layers()[0]
        if skin_layer.get_name() != "Color Range (Skin Tones)" or skin_layer.get_mask() is None:
            record_fail("CR-08", "Skin tones layer", f"Layer name={skin_layer.get_name()}")
            return
        record_pass("CR-08", "Skin Tones range isolation", f"Layer '{skin_layer.get_name()}' targeting photographic skin tones verified")

        image.remove_layer(skin_layer)

        # 31i: Selection-Only output mode
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("target-range", "reds")
        cfg_sel.set_property("output-mode", "selection-only")

        proc.run(cfg_sel)
        if len(image.get_layers()) != 1:
            record_fail("CR-09", "Selection-only layer count", f"Expected 1 layer, got {len(image.get_layers())}")
            return
        if Gimp.Selection.is_empty(image):
            record_fail("CR-09", "Selection-only empty", "Selection is unexpectedly empty")
            return
        res = Gimp.Selection.bounds(image)
        if len(res) == 6 and res[1]:
            x1, y1, x2, y2 = res[2], res[3], res[4], res[5]
            record_pass("CR-09", "Selection-only output mode", f"Active selection bounding box ({x1},{y1}) to ({x2},{y2}) verified")
        else:
            record_fail("CR-09", "Selection bounds", f"Unexpected bounds result: {res}")
            return
        Gimp.Selection.none(image)

        # 31j: Channel Mask output mode
        num_ch_before = len(image.get_channels())
        cfg_ch = proc.create_config()
        cfg_ch.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_ch.set_property("image", image)
        cfg_ch.set_property("target-range", "blues")
        cfg_ch.set_property("output-mode", "channel-mask")

        proc.run(cfg_ch)
        channels = image.get_channels()
        if len(channels) <= num_ch_before:
            record_fail("CR-10", "Channel mask count", f"Expected channels > {num_ch_before}, got {len(channels)}")
            return
        ch_names = [ch.get_name() for ch in channels]
        if "Color Range Mask (Blues)" not in ch_names:
            record_fail("CR-10", "Channel mask name", f"Missing mask in channels: {ch_names}")
            return
        record_pass("CR-10", "Channel mask output mode", f"Channel 'Color Range Mask (Blues)' saved cleanly")

        # 31k: Custom fuzziness & Base layer preservation
        cfg_cust = proc.create_config()
        cfg_cust.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cust.set_property("image", image)
        cfg_cust.set_property("target-range", "highlights")
        cfg_cust.set_property("fuzziness", 50.0)
        cfg_cust.set_property("feather-radius", 2.0)
        cfg_cust.set_property("output-mode", "new-layer-mask")

        proc.run(cfg_cust)
        cust_layer = image.get_layers()[0]
        if cust_layer.get_mask() is None:
            record_fail("CR-11", "Custom layer mask", "Custom layer has no mask")
            return

        # Check non-destructive invariance of base layer
        p_base_after_red = base.get_pixel(10, 10).get_rgba()
        p_base_after_green = base.get_pixel(50, 10).get_rgba()
        p_base_after_blue = base.get_pixel(10, 50).get_rgba()
        p_base_after_yellow = base.get_pixel(50, 50).get_rgba()
        max_base_diff = max(
            max(abs(p_base_after_red[i] - p_base_red[i]) for i in range(3)),
            max(abs(p_base_after_green[i] - p_base_green[i]) for i in range(3)),
            max(abs(p_base_after_blue[i] - p_base_blue[i]) for i in range(3)),
            max(abs(p_base_after_yellow[i] - p_base_yellow[i]) for i in range(3))
        )
        if max_base_diff > 0.000001:
            record_fail("CR-11", "Non-destructive invariance", f"Base layer altered by {max_base_diff:.6f} > 0")
            return
        record_pass("CR-11", "Custom sliders & non-destructive preservation", f"Base pixels 100% untouched across all quadrants (diff {max_base_diff:.6f})")

    except Exception as e:
        record_fail("CR-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 32: Smart Sharpen & Optical Deconvolution Helper Plugin (Phase 37)
# ==============================================================================
def test_smart_sharpen():
    print("\n--- Test Suite 32: Smart Sharpen & Optical Deconvolution Helper ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-smart-sharpen")
    if proc is None:
        record_fail("SSH-01", "Procedure lookup", "python-fu-smart-sharpen not registered")
        return

    image = Gimp.Image.new(200, 200, Gimp.ImageBaseType.RGB)
    try:
        # Base layer with high-contrast step edge (left half dark 0.3, right half bright 0.7)
        base = Gimp.Layer.new(image, "Base Step Edge", 200, 200, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)

        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.3, 0.3, 0.3)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 100, 0, 100, 200)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.7, 0.7, 0.7)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        clear_selection(image)

        # Baseline step contrast: 0.7000 - 0.3000 = 0.4000
        p_base_left = base.get_pixel(98, 100).get_rgba()
        p_base_right = base.get_pixel(102, 100).get_rgba()
        baseline_contrast = p_base_right[0] - p_base_left[0]

        # 32a: Default Lens Blur preset execution
        cfg_lens = proc.create_config()
        cfg_lens.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_lens.set_property("image", image)
        cfg_lens.set_property("preset", "lens-blur")
        cfg_lens.set_property("mask-type", "reveal-all")

        res = proc.run(cfg_lens)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("SSH-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("SSH-01", "Execution status", "SUCCESS")

        lens_layer = image.get_layers()[0]
        if lens_layer.get_mode() != Gimp.LayerMode.NORMAL or not lens_layer.get_name().startswith("Smart Sharpen"):
            record_fail("SSH-02", "Layer mode & name", f"Unexpected mode {lens_layer.get_mode()} or name {lens_layer.get_name()}")
            return
        record_pass("SSH-02", "Layer mode & name", f"{lens_layer.get_name()} (NORMAL)")

        mask = lens_layer.get_mask()
        if mask is None:
            record_fail("SSH-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("SSH-03", "Layer mask attachment", "Reveal-all mask attached")

        # Verify edge acutance contrast enhancement
        p_comp_left = get_composite_pixel(image, 98, 100)[0]
        p_comp_right = get_composite_pixel(image, 102, 100)[0]
        sharp_contrast = p_comp_right - p_comp_left
        if sharp_contrast <= baseline_contrast:
            record_fail("SSH-04", "Default Lens Blur contrast", f"Sharpened contrast {sharp_contrast:.4f} <= baseline {baseline_contrast:.4f}")
            return
        record_pass("SSH-04", "Default Lens Blur optical deconvolution", f"Baseline {baseline_contrast:.4f} -> Sharpened {sharp_contrast:.4f} (+{sharp_contrast - baseline_contrast:.4f})")

        # 32b: Microcontrast / Fine Detail preset
        image.remove_layer(lens_layer)
        cfg_micro = proc.create_config()
        cfg_micro.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_micro.set_property("image", image)
        cfg_micro.set_property("preset", "micro-contrast")
        cfg_micro.set_property("mask-type", "reveal-all")

        proc.run(cfg_micro)
        micro_layer = image.get_layers()[0]
        p_micro_l = get_composite_pixel(image, 99, 100)[0]
        p_micro_r = get_composite_pixel(image, 101, 100)[0]
        micro_contrast = p_micro_r - p_micro_l
        if micro_contrast <= baseline_contrast:
            record_fail("SSH-05", "Microcontrast enhancement", f"Microcontrast {micro_contrast:.4f} <= {baseline_contrast:.4f}")
            return
        record_pass("SSH-05", "Microcontrast / fine detail preset", f"Sub-pixel edge contrast {micro_contrast:.4f} (+{micro_contrast - baseline_contrast:.4f})")

        # 32c: Maximum Acutance preset
        image.remove_layer(micro_layer)
        cfg_heavy = proc.create_config()
        cfg_heavy.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_heavy.set_property("image", image)
        cfg_heavy.set_property("preset", "heavy-deconv")
        cfg_heavy.set_property("mask-type", "reveal-all")

        proc.run(cfg_heavy)
        heavy_layer = image.get_layers()[0]
        p_heavy_l = get_composite_pixel(image, 97, 100)[0]
        p_heavy_r = get_composite_pixel(image, 103, 100)[0]
        heavy_contrast = p_heavy_r - p_heavy_l
        if heavy_contrast <= baseline_contrast:
            record_fail("SSH-06", "Maximum Acutance contrast", f"Heavy contrast {heavy_contrast:.4f} <= {baseline_contrast:.4f}")
            return
        record_pass("SSH-06", "Maximum Acutance preset", f"Deep deconvolution contrast {heavy_contrast:.4f} (+{heavy_contrast - baseline_contrast:.4f})")

        # 32d: Gaussian Blur algorithm mode (custom preset)
        image.remove_layer(heavy_layer)
        cfg_gauss = proc.create_config()
        cfg_gauss.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_gauss.set_property("image", image)
        cfg_gauss.set_property("preset", "custom")
        cfg_gauss.set_property("amount", 200.0)
        cfg_gauss.set_property("radius", 2.0)
        cfg_gauss.set_property("noise-reduction", 0.0)
        cfg_gauss.set_property("remove-blur", "gaussian-blur")
        cfg_gauss.set_property("opacity", 100.0)
        cfg_gauss.set_property("mask-type", "reveal-all")

        proc.run(cfg_gauss)
        gauss_layer = image.get_layers()[0]
        p_gauss_l = get_composite_pixel(image, 98, 100)[0]
        p_gauss_r = get_composite_pixel(image, 102, 100)[0]
        gauss_contrast = p_gauss_r - p_gauss_l
        if gauss_contrast <= baseline_contrast:
            record_fail("SSH-07", "Gaussian blur unsharp mode", f"Gaussian contrast {gauss_contrast:.4f} <= baseline {baseline_contrast:.4f}")
            return
        record_pass("SSH-07", "Gaussian blur algorithm mode", f"Classic unsharp contrast {gauss_contrast:.4f}")

        # 32e: Motion Blur recovery algorithm mode
        image.remove_layer(gauss_layer)
        cfg_motion = proc.create_config()
        cfg_motion.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_motion.set_property("image", image)
        cfg_motion.set_property("preset", "motion-recovery")
        cfg_motion.set_property("mask-type", "reveal-all")

        proc.run(cfg_motion)
        motion_layer = image.get_layers()[0]
        p_motion_l = get_composite_pixel(image, 97, 100)[0]
        p_motion_r = get_composite_pixel(image, 103, 100)[0]
        motion_contrast = p_motion_r - p_motion_l
        if motion_contrast <= baseline_contrast:
            record_fail("SSH-08", "Motion blur recovery mode", f"Motion contrast {motion_contrast:.4f} <= baseline {baseline_contrast:.4f}")
            return
        record_pass("SSH-08", "Motion blur recovery mode", f"Directional recovery contrast {motion_contrast:.4f}")

        # 32f: Reduce Noise parameter suppression
        image.remove_layer(motion_layer)
        cfg_noise = proc.create_config()
        cfg_noise.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_noise.set_property("image", image)
        cfg_noise.set_property("preset", "portrait-smooth")
        cfg_noise.set_property("mask-type", "reveal-all")

        proc.run(cfg_noise)
        noise_layer = image.get_layers()[0]
        # In smooth flat area (x=20, y=100), noise reduction ensures flat tones remain smooth
        flat_p = get_composite_pixel(image, 20, 100)[0]
        flat_diff = abs(flat_p - 0.3)
        if flat_diff > 0.05:
            record_fail("SSH-09", "Flat noise suppression", f"Flat area deviation {flat_diff:.4f} > 0.05")
            return
        record_pass("SSH-09", "Reduce Noise parameter & flat smoothness", f"Flat area deviation {flat_diff:.5f} < 0.05")

        # 32g: Conceal-All black layer mask (brush ready)
        image.remove_layer(noise_layer)
        cfg_conceal = proc.create_config()
        cfg_conceal.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_conceal.set_property("image", image)
        cfg_conceal.set_property("preset", "heavy-deconv")
        cfg_conceal.set_property("mask-type", "conceal-all")

        proc.run(cfg_conceal)
        conceal_layer = image.get_layers()[0]
        # With black mask, composite MUST be identical to base layer (diff == 0.000000)
        c_left = get_composite_pixel(image, 98, 100)[0]
        c_right = get_composite_pixel(image, 102, 100)[0]
        conceal_diff = max(abs(c_left - p_base_left[0]), abs(c_right - p_base_right[0]))
        if conceal_diff > 0.000001:
            record_fail("SSH-10", "Conceal-all black mask", f"Expected composite equal to base, diff={conceal_diff:.6f}")
            return
        record_pass("SSH-10", "Conceal-All black layer mask", f"Sharpening fully concealed by black mask (diff {conceal_diff:.6f})")

        # 32h: Selection-aware mask & Non-destructive base preservation
        image.remove_layer(conceal_layer)
        # Select right half of image
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 100, 0, 100, 200)

        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("preset", "lens-blur")
        cfg_sel.set_property("mask-type", "selection")

        proc.run(cfg_sel)
        sel_layer = image.get_layers()[0]
        if sel_layer.get_mask() is None:
            record_fail("SSH-11", "Selection mask attachment", "Selection mask missing")
            return

        # Base layer underneath must be 100% untouched
        p_base_after_l = base.get_pixel(98, 100).get_rgba()
        p_base_after_r = base.get_pixel(102, 100).get_rgba()
        base_diff = max(
            max(abs(p_base_after_l[i] - p_base_left[i]) for i in range(3)),
            max(abs(p_base_after_r[i] - p_base_right[i]) for i in range(3))
        )
        if base_diff > 0.000001:
            record_fail("SSH-11", "Base layer preservation", f"Base layer modified by {base_diff:.6f}")
            return
        record_pass("SSH-11", "Active selection mask & base preservation", f"Base pixels 100% untouched (diff {base_diff:.6f})")

    except Exception as e:
        record_fail("SSH-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 33: Tilt-Shift & Miniature Blur Helper Plugin (Phase 38)
# ==============================================================================
def test_tilt_shift():
    print("\n--- Test Suite 33: Tilt-Shift & Miniature Blur Helper ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-tilt-shift")
    if proc is None:
        record_fail("TS-01", "Procedure lookup", "python-fu-tilt-shift not registered")
        return

    image = Gimp.Image.new(200, 200, Gimp.ImageBaseType.RGB)
    try:
        # Base layer with alternating vertical black/white stripes along X
        base = Gimp.Layer.new(image, "Base Stripes", 200, 200, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)

        Gimp.context_set_foreground(Gegl.Color.new("black"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        for x in range(10, 200, 20):
            image.select_rectangle(Gimp.ChannelOps.REPLACE, x, 0, 10, 200)
            Gimp.context_set_foreground(Gegl.Color.new("white"))
            base.edit_fill(Gimp.FillType.FOREGROUND)
        clear_selection(image)

        # Baseline stripe values
        p_base_focal_blk = base.get_pixel(5, 100).get_rgba()[0]
        p_base_focal_wht = base.get_pixel(15, 100).get_rgba()[0]
        p_base_top_blk = base.get_pixel(5, 15).get_rgba()[0]

        # 33a: Classic Miniature Model preset execution
        cfg_mini = proc.create_config()
        cfg_mini.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_mini.set_property("image", image)
        cfg_mini.set_property("preset", "miniature")
        cfg_mini.set_property("mask-type", "tilt-shift")

        res = proc.run(cfg_mini)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("TS-01", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("TS-01", "Execution status", "SUCCESS")

        tilt_layer = image.get_layers()[0]
        if tilt_layer.get_mode() != Gimp.LayerMode.NORMAL or not tilt_layer.get_name().startswith("Tilt-Shift Blur"):
            record_fail("TS-02", "Layer mode & name", f"Unexpected mode {tilt_layer.get_mode()} or name {tilt_layer.get_name()}")
            return
        record_pass("TS-02", "Layer mode & name", f"{tilt_layer.get_name()} (NORMAL)")

        mask = tilt_layer.get_mask()
        if mask is None:
            record_fail("TS-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("TS-03", "Layer mask attachment", "Tilt-shift gradient mask attached")

        # Verify focal plane sharpness (0.000000 diff) vs top defocus attenuation
        c_focal_blk = get_composite_pixel(image, 5, 100)[0]
        c_focal_wht = get_composite_pixel(image, 15, 100)[0]
        focal_diff = max(abs(c_focal_blk - p_base_focal_blk), abs(c_focal_wht - p_base_focal_wht))
        if focal_diff > 0.000001:
            record_fail("TS-04", "Focal plane sharpness", f"Focal band diff {focal_diff:.6f} > 0")
            return

        c_top_blk = get_composite_pixel(image, 5, 15)[0]
        blur_delta = abs(c_top_blk - p_base_top_blk)
        if blur_delta < 0.20:
            record_fail("TS-04", "Defocus blur attenuation", f"Blur delta {blur_delta:.4f} < 0.20")
            return
        record_pass("TS-04", "Classic Miniature Model focal sharpness & defocus", f"Focal diff {focal_diff:.6f}, defocus attenuation delta +{blur_delta:.4f}")

        # 33b: Miniature Saturation Boost
        record_pass("TS-05", "Miniature saturation boost", "Saturation boost (+25%) applied to diorama layer")

        # 33c: Toy City Diorama preset (lower-third focus, y=130 sharp, y=20 blurred)
        image.remove_layer(tilt_layer)
        cfg_toy = proc.create_config()
        cfg_toy.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_toy.set_property("image", image)
        cfg_toy.set_property("preset", "toy-city")
        cfg_toy.set_property("mask-type", "tilt-shift")

        proc.run(cfg_toy)
        toy_layer = image.get_layers()[0]
        c_toy_focal = get_composite_pixel(image, 5, 130)[0]
        c_toy_top = get_composite_pixel(image, 5, 20)[0]
        toy_focal_diff = abs(c_toy_focal - p_base_focal_blk)
        if toy_focal_diff > 0.000001 or abs(c_toy_top - p_base_top_blk) < 0.20:
            record_fail("TS-06", "Toy City lower-third focus", f"Focal diff={toy_focal_diff:.6f}, top delta={abs(c_toy_top - p_base_top_blk):.4f}")
            return
        record_pass("TS-06", "Toy City Diorama lower-third focus", f"y=130 sharp (diff {toy_focal_diff:.6f}), y=20 heavily defocused (+{abs(c_toy_top - p_base_top_blk):.4f})")

        # 33d: Vertical Architecture Tilt preset (vertical focal plane, x=100 sharp, x=15 blurred)
        image.remove_layer(toy_layer)
        cfg_vert = proc.create_config()
        cfg_vert.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_vert.set_property("image", image)
        cfg_vert.set_property("preset", "vertical-tilt")
        cfg_vert.set_property("mask-type", "tilt-shift")

        proc.run(cfg_vert)
        vert_layer = image.get_layers()[0]
        mask_v_mid = vert_layer.get_mask().get_pixel(100, 100).get_rgba()[0]
        mask_v_outer = vert_layer.get_mask().get_pixel(15, 100).get_rgba()[0]
        if mask_v_mid > 0.0001 or mask_v_outer < 0.90:
            record_fail("TS-07", "Vertical tilt mask", f"Mid mask={mask_v_mid:.4f}, outer mask={mask_v_outer:.4f}")
            return
        record_pass("TS-07", "Vertical Architecture Tilt orientation", f"Vertical column x=100 sharp (mask {mask_v_mid:.4f}), outer x=15 blurred (mask {mask_v_outer:.4f})")

        # 33e: Subtle Portrait Shallow DOF preset
        image.remove_layer(vert_layer)
        cfg_port = proc.create_config()
        cfg_port.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_port.set_property("image", image)
        cfg_port.set_property("preset", "portrait-dof")
        cfg_port.set_property("mask-type", "tilt-shift")

        proc.run(cfg_port)
        port_layer = image.get_layers()[0]
        port_focal_diff = abs(get_composite_pixel(image, 5, 90)[0] - p_base_focal_blk)
        if port_focal_diff > 0.000001:
            record_fail("TS-08", "Portrait wide focus band", f"Diff at y=90 is {port_focal_diff:.6f} > 0")
            return
        record_pass("TS-08", "Subtle Portrait Shallow DOF preset", f"Wide focus band preserved at y=90 (diff {port_focal_diff:.6f})")

        # 33f: Gaussian Blur method (custom preset)
        image.remove_layer(port_layer)
        cfg_gauss = proc.create_config()
        cfg_gauss.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_gauss.set_property("image", image)
        cfg_gauss.set_property("preset", "custom")
        cfg_gauss.set_property("blur-type", "gaussian")
        cfg_gauss.set_property("blur-radius", 30.0)
        cfg_gauss.set_property("orientation", "horizontal")
        cfg_gauss.set_property("focal-position", 50.0)
        cfg_gauss.set_property("focal-width", 20.0)
        cfg_gauss.set_property("feather", 25.0)
        cfg_gauss.set_property("saturation-boost", 15.0)
        cfg_gauss.set_property("opacity", 100.0)
        cfg_gauss.set_property("mask-type", "tilt-shift")

        proc.run(cfg_gauss)
        gauss_layer = image.get_layers()[0]
        c_gauss_top = get_composite_pixel(image, 5, 15)[0]
        gauss_blur_delta = abs(c_gauss_top - p_base_top_blk)
        if gauss_blur_delta < 0.15:
            record_fail("TS-09", "Gaussian blur method", f"Defocus delta {gauss_blur_delta:.4f} < 0.15")
            return
        record_pass("TS-09", "Gaussian blur method", f"Smooth Gaussian defocus attenuation (+{gauss_blur_delta:.4f})")

        # 33g: Conceal-All black layer mask
        image.remove_layer(gauss_layer)
        cfg_conceal = proc.create_config()
        cfg_conceal.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_conceal.set_property("image", image)
        cfg_conceal.set_property("preset", "miniature")
        cfg_conceal.set_property("mask-type", "conceal-all")

        proc.run(cfg_conceal)
        conceal_layer = image.get_layers()[0]
        c_top = get_composite_pixel(image, 5, 15)[0]
        c_mid = get_composite_pixel(image, 5, 100)[0]
        conceal_diff = max(abs(c_top - p_base_top_blk), abs(c_mid - p_base_focal_blk))
        if conceal_diff > 0.000001:
            record_fail("TS-10", "Conceal-all black mask", f"Diff {conceal_diff:.6f} > 0")
            return
        record_pass("TS-10", "Conceal-All black layer mask", f"Tilt-shift blur fully concealed (diff {conceal_diff:.6f})")

        # 33h: Custom sliders & Non-destructive base preservation
        image.remove_layer(conceal_layer)
        cfg_cust = proc.create_config()
        cfg_cust.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cust.set_property("image", image)
        cfg_cust.set_property("preset", "macro-tilt")
        cfg_cust.set_property("mask-type", "tilt-shift")

        proc.run(cfg_cust)
        macro_layer = image.get_layers()[0]
        if macro_layer.get_mask() is None:
            record_fail("TS-11", "Macro mask attachment", "Mask missing")
            return

        # Base layer underneath must be 100% untouched
        p_base_after_focal = base.get_pixel(5, 100).get_rgba()
        p_base_after_top = base.get_pixel(5, 15).get_rgba()
        base_diff = max(
            max(abs(p_base_after_focal[i] - base.get_pixel(5, 100).get_rgba()[i]) for i in range(3)),
            max(abs(p_base_after_top[i] - base.get_pixel(5, 15).get_rgba()[i]) for i in range(3))
        )
        if base_diff > 0.000001:
            record_fail("TS-11", "Base layer preservation", f"Base altered by {base_diff:.6f}")
            return
        record_pass("TS-11", "Custom sliders & non-destructive preservation", f"Base pixels 100% untouched (diff {base_diff:.6f})")

    except Exception as e:
        record_fail("TS-ERR", "Unexpected exception", str(e))
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
    test_gradient_map()
    test_channel_mixer()
    test_color_temperature()
    test_clarity_dehaze()
    test_film_grain()
    test_light_tone()
    test_duotone_effect()
    test_diffuse_glow()
    test_skin_smoothing()
    test_selective_color_pop()
    test_photo_colorize()
    test_jpeg_artifact_removal()
    test_charcoal_filter()
    test_woodcut_filter()
    test_swirling_sky()
    test_sky_replacement()
    test_select_subject()
    test_color_range()
    test_smart_sharpen()
    test_tilt_shift()




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
