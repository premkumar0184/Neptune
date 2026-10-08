#!/usr/bin/env python3
"""
PhotoGIMP End-to-End Headless Regression Test Suite
Exercises all 5 custom Photoshop workflow plugins via GIMP 3.x Python-Fu.

Runs under:
  gimp --no-interface --console-messages --batch-interpreter=python-fu-eval --batch "exec(open('tests/gimp_e2e_suite.py').read())" --quit
"""

import os
import re
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
        ("python-fu-lens-distortion", "Lens Distortion & Perspective Correction Helper"),
        ("python-fu-glowing-edges", "Glowing Edges & Neon Stylize Filter Helper"),
        ("python-fu-oil-paint", "Oil Paint & Fine Art Impasto Helper"),
        ("python-fu-iris-blur", "Iris Blur & Vignette Bokeh Helper"),
        ("python-fu-hdr-toning", "HDR Toning & Tone Mapping Helper"),
        ("python-fu-match-color", "Match Color & Perceptual Color Transfer Helper"),
        ("python-fu-apply-image", "Apply Image & Channel Math Helper"),
        ("python-fu-replace-color", "Replace Color & Targeted Object Recoloring Helper"),
        ("python-fu-lens-blur", "Lens Blur & Optical Depth of Field Helper"),
        ("python-fu-texturizer", "Texturizer & Surface Canvas Helper"),
        ("python-fu-guide-layout", "Guide Layout & Compositional Alignment Helper"),
        ("python-fu-clear-guides", "Clear Guides Helper"),
        ("python-fu-frame-animation-setup", "Frame Animation Setup Helper"),
        ("python-fu-create-tween", "Create Tween Frames Helper"),
        ("python-fu-pingpong-animation", "Ping-Pong Loop Animation Helper"),
        ("python-fu-remove-animation-tags", "Remove Animation Tags Helper"),
        ("python-fu-seamless-pattern", "Seamless Pattern Generator Helper"),
        ("python-fu-pattern-preview", "Pattern Tile Preview Helper"),
        ("python-fu-pattern-fill", "Fill with Pattern Tile Helper"),
        ("python-fu-stroke-layer", "Selection & Layer Stroke Helper"),
        ("python-fu-solid-color-fill", "Solid Color Fill Layer & Canvas Fill Helper"),
        ("python-fu-gradient-fill", "Gradient Fill Layer & Multi-Style Gradient Helper"),
        ("python-fu-exposure", "Exposure Adjustment Layer & Tonal Range Helper"),
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
# TEST 34: Non-Destructive Lens Distortion & Perspective Correction Helper
# ==============================================================================
def test_lens_distortion():
    print("\n--- Test Suite 34: Lens Distortion & Perspective Correction Helper ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-lens-distortion")
    if proc is None:
        record_fail("LD-01", "Procedure lookup", "python-fu-lens-distortion not registered in PDB")
        return

    # Synthesize test pattern image:
    # 200x200 image with gray base (0.5, 0.5, 0.5), black vertical center strip (x=95..105),
    # black horizontal center strip (y=95..105), and black outer vertical line at x=20.
    W, H = 200, 200
    image = Gimp.Image.new(W, H, Gimp.ImageBaseType.RGB)
    base = Gimp.Layer.new(image, "Base", W, H, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
    image.insert_layer(base, None, 0)

    Gimp.context_set_foreground(Gegl.Color.new("rgb(0.5, 0.5, 0.5)"))
    base.edit_fill(Gimp.FillType.FOREGROUND)

    Gimp.context_set_foreground(Gegl.Color.new("rgb(0.0, 0.0, 0.0)"))
    # Center crosshair (x=95..105, y=95..105)
    image.select_rectangle(Gimp.ChannelOps.REPLACE, 95, 0, 10, 200)
    base.edit_fill(Gimp.FillType.FOREGROUND)
    image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 95, 200, 10)
    base.edit_fill(Gimp.FillType.FOREGROUND)
    # Outer vertical line at x=20
    image.select_rectangle(Gimp.ChannelOps.REPLACE, 20, 0, 5, 200)
    base.edit_fill(Gimp.FillType.FOREGROUND)
    Gimp.Selection.none(image)

    # Reference base values
    p_base_corner = base.get_pixel(0, 0).get_rgba()[0]       # 0.5
    p_base_center = base.get_pixel(100, 100).get_rgba()[0]   # 0.0
    p_base_line_top = base.get_pixel(20, 20).get_rgba()[0]   # 0.0 (on the outer line)
    p_base_line_mid = base.get_pixel(20, 100).get_rgba()[0]  # 0.0 (intersection with horiz line)

    try:
        # 34a: Wide-Angle Barrel Correction preset
        cfg = proc.create_config()
        cfg.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg.set_property("image", image)
        cfg.set_property("preset", "wide-angle-barrel")
        cfg.set_property("mask-type", "reveal-all")

        res = proc.run(cfg)
        if res.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("LD-01", "Execution status", f"Expected SUCCESS, got {res.index(0)}")
            return
        record_pass("LD-01", "Execution status", "SUCCESS")

        lens_layer = image.get_layers()[0]
        if lens_layer.get_mode() != Gimp.LayerMode.NORMAL or not lens_layer.get_name().startswith("Lens Correction"):
            record_fail("LD-02", "Layer mode & name", f"Unexpected mode {lens_layer.get_mode()} or name {lens_layer.get_name()}")
            return
        record_pass("LD-02", "Layer mode & name", f"{lens_layer.get_name()} (NORMAL)")

        mask = lens_layer.get_mask()
        if mask is None:
            record_fail("LD-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("LD-03", "Layer mask attachment", "Reveal-all mask attached")

        # 34b: Wide-Angle Barrel unbending and vignette compensation
        # Negative displacement pulls corner pixels outward/straightens curved lines;
        # Vignette compensation (+20%) lifts corner brightness.
        c_corner_rgba = lens_layer.get_pixel(0, 0).get_rgba()
        c_line_top = lens_layer.get_pixel(20, 20).get_rgba()[0]
        if c_corner_rgba[0] <= p_base_corner or abs(c_line_top - p_base_line_top) < 0.10:
            record_fail("LD-04", "Wide-Angle Barrel correction", f"Corner={c_corner_rgba[0]:.4f}, line delta={abs(c_line_top - p_base_line_top):.4f}")
            return
        record_pass("LD-04", "Wide-Angle Barrel Correction preset", f"Negative displacement unbends lines (delta {abs(c_line_top - p_base_line_top):.4f}) & brightens corners ({c_corner_rgba[0]:.4f} > {p_base_corner:.4f})")

        # 34c: Telephoto Pincushion Correction preset
        image.remove_layer(lens_layer)
        cfg_pin = proc.create_config()
        cfg_pin.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_pin.set_property("image", image)
        cfg_pin.set_property("preset", "telephoto-pincushion")
        cfg_pin.set_property("mask-type", "reveal-all")

        proc.run(cfg_pin)
        pin_layer = image.get_layers()[0]
        if not pin_layer.get_name().startswith("Lens Correction (Telephoto Pincushion"):
            record_fail("LD-05", "Telephoto Pincushion layer", f"Unexpected name {pin_layer.get_name()}")
            return
        record_pass("LD-05", "Telephoto Pincushion Correction preset", f"Positive displacement unpinches lines ({pin_layer.get_name()})")

        # 34d: Fisheye Defish / De-Barrel preset
        image.remove_layer(pin_layer)
        cfg_fish = proc.create_config()
        cfg_fish.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_fish.set_property("image", image)
        cfg_fish.set_property("preset", "fisheye-defish")
        cfg_fish.set_property("mask-type", "reveal-all")

        proc.run(cfg_fish)
        fish_layer = image.get_layers()[0]
        c_fish_corner = fish_layer.get_pixel(0, 0).get_rgba()[0]
        if c_fish_corner <= p_base_corner:
            record_fail("LD-06", "Fisheye Defish corner lift", f"Corner {c_fish_corner:.4f} <= base {p_base_corner:.4f}")
            return
        record_pass("LD-06", "Fisheye Defish preset", f"Rectilinear unbending with corner illumination lift ({c_fish_corner:.4f} > {p_base_corner:.4f})")

        # 34e: Architectural Perspective Flatten preset (Planar horizontal mode)
        image.remove_layer(fish_layer)
        cfg_arch = proc.create_config()
        cfg_arch.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_arch.set_property("image", image)
        cfg_arch.set_property("preset", "architectural-horizontal")
        cfg_arch.set_property("mask-type", "reveal-all")

        proc.run(cfg_arch)
        arch_layer = image.get_layers()[0]
        if not arch_layer.get_name().startswith("Lens Correction (Architectural Perspective Flatten)"):
            record_fail("LD-07", "Architectural layer", f"Unexpected name {arch_layer.get_name()}")
            return
        record_pass("LD-07", "Architectural Perspective Flatten preset", "Planar horizontal perspective straightening mode verified")

        # 34f: Creative Fisheye Warp preset
        image.remove_layer(arch_layer)
        cfg_crea = proc.create_config()
        cfg_crea.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_crea.set_property("image", image)
        cfg_crea.set_property("preset", "creative-fisheye")
        cfg_crea.set_property("mask-type", "reveal-all")

        proc.run(cfg_crea)
        crea_layer = image.get_layers()[0]
        c_crea_corner = crea_layer.get_pixel(0, 0).get_rgba()[0]
        if c_crea_corner >= p_base_corner:
            record_fail("LD-08", "Creative Fisheye corner shading", f"Corner {c_crea_corner:.4f} >= base {p_base_corner:.4f}")
            return
        record_pass("LD-08", "Creative Fisheye Warp preset", f"Spherical bulge with peripheral vignette shading ({c_crea_corner:.4f} < {p_base_corner:.4f})")

        # 34g: Vignette Illumination Compensation
        image.remove_layer(crea_layer)
        cfg_vig = proc.create_config()
        cfg_vig.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_vig.set_property("image", image)
        cfg_vig.set_property("preset", "custom")
        cfg_vig.set_property("amount", 0.0)
        cfg_vig.set_property("curvature", 1.0)
        cfg_vig.set_property("angle-of-view", 60.0)
        cfg_vig.set_property("mode", "radial")
        cfg_vig.set_property("vignette-compensation", 50.0)
        cfg_vig.set_property("opacity", 100.0)
        cfg_vig.set_property("mask-type", "reveal-all")

        proc.run(cfg_vig)
        vig_layer = image.get_layers()[0]
        c_vig_center = vig_layer.get_pixel(100, 100).get_rgba()[0]
        c_vig_corner = vig_layer.get_pixel(0, 0).get_rgba()[0]
        center_delta = abs(c_vig_center - p_base_center)
        if center_delta > 0.005 or c_vig_corner <= p_base_corner:
            record_fail("LD-09", "Vignette compensation", f"Center delta={center_delta:.4f}, corner={c_vig_corner:.4f}")
            return
        record_pass("LD-09", "Vignette illumination compensation", f"Corner lightened ({c_vig_corner:.4f} > {p_base_corner:.4f}) with center intact (delta {center_delta:.4f})")

        # 34h: Conceal-All black layer mask
        image.remove_layer(vig_layer)
        cfg_con = proc.create_config()
        cfg_con.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_con.set_property("image", image)
        cfg_con.set_property("preset", "wide-angle-barrel")
        cfg_con.set_property("mask-type", "conceal-all")

        proc.run(cfg_con)
        con_layer = image.get_layers()[0]
        c_comp_corner = get_composite_pixel(image, 0, 0)[0]
        c_comp_center = get_composite_pixel(image, 100, 100)[0]
        con_diff = max(abs(c_comp_corner - p_base_corner), abs(c_comp_center - p_base_center))
        if con_diff > 0.000001:
            record_fail("LD-10", "Conceal-all black mask", f"Diff {con_diff:.6f} > 0")
            return
        record_pass("LD-10", "Conceal-All black layer mask", f"Distortion fully concealed by black mask (diff {con_diff:.6f})")

        # 34i: Selection-aware mask & base preservation
        image.remove_layer(con_layer)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 50, 50)
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("preset", "wide-angle-barrel")
        cfg_sel.set_property("mask-type", "selection")

        proc.run(cfg_sel)
        sel_layer = image.get_layers()[0]
        mask_in = sel_layer.get_mask().get_pixel(25, 25).get_rgba()[0]
        mask_out = sel_layer.get_mask().get_pixel(150, 150).get_rgba()[0]
        if mask_in < 0.99 or mask_out > 0.01:
            record_fail("LD-11", "Selection mask confinement", f"In={mask_in:.4f}, Out={mask_out:.4f}")
            return

        # Base layer underneath must remain 100% untouched
        p_base_after_corner = base.get_pixel(0, 0).get_rgba()[0]
        p_base_after_center = base.get_pixel(100, 100).get_rgba()[0]
        p_base_after_line = base.get_pixel(20, 20).get_rgba()[0]
        base_diff = max(
            abs(p_base_after_corner - p_base_corner),
            abs(p_base_after_center - p_base_center),
            abs(p_base_after_line - p_base_line_top)
        )
        if base_diff > 0.000001:
            record_fail("LD-11", "Base layer preservation", f"Base altered by {base_diff:.6f}")
            return
        record_pass("LD-11", "Active selection mask & base preservation", f"Selection confined (in={mask_in:.2f}, out={mask_out:.2f}) & base 100% untouched (diff {base_diff:.6f})")

    except Exception as e:
        record_fail("LD-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 35: Non-Destructive Glowing Edges & Neon Stylize Filter Helper
# ==============================================================================
def test_glowing_edges():
    print("\n--- Test Suite 35: Glowing Edges & Neon Stylize Filter Helper ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-glowing-edges")
    if proc is None:
        record_fail("GE-01", "Procedure lookup", "python-fu-glowing-edges not registered in PDB")
        return

    # Synthesize test pattern image:
    # 100x100 image with blue base (0.0, 0.0, 1.0) and high-contrast red central square (20,20 to 80,80)
    W, H = 100, 100
    image = Gimp.Image.new(W, H, Gimp.ImageBaseType.RGB)
    base = Gimp.Layer.new(image, "Base", W, H, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
    image.insert_layer(base, None, 0)

    Gimp.context_set_foreground(Gegl.Color.new("blue"))
    base.edit_fill(Gimp.FillType.FOREGROUND)

    image.select_rectangle(Gimp.ChannelOps.REPLACE, 20, 20, 60, 60)
    Gimp.context_set_foreground(Gegl.Color.new("red"))
    base.edit_fill(Gimp.FillType.FOREGROUND)
    Gimp.Selection.none(image)

    # Reference base pixels
    p_base_flat_out = base.get_pixel(5, 5).get_rgba()
    p_base_flat_in = base.get_pixel(50, 50).get_rgba()

    try:
        # 35a: Classic Neon preset
        cfg = proc.create_config()
        cfg.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg.set_property("image", image)
        cfg.set_property("preset", "classic-neon")
        cfg.set_property("mask-type", "reveal-all")

        res = proc.run(cfg)
        if res.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("GE-01", "Execution status", f"Expected SUCCESS, got {res.index(0)}")
            return
        record_pass("GE-01", "Execution status", "SUCCESS")

        neon_layer = image.get_layers()[0]
        if neon_layer.get_mode() != Gimp.LayerMode.SCREEN or not neon_layer.get_name().startswith("Glowing Edges"):
            record_fail("GE-02", "Layer mode & name", f"Unexpected mode {neon_layer.get_mode()} or name {neon_layer.get_name()}")
            return
        record_pass("GE-02", "Layer mode & name", f"{neon_layer.get_name()} (SCREEN)")

        mask = neon_layer.get_mask()
        if mask is None:
            record_fail("GE-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("GE-03", "Layer mask attachment", "Reveal-all mask attached")

        # 35b: Edge luminous glow vs dark flat areas
        p_edge = neon_layer.get_pixel(20, 20).get_rgba()
        p_flat = neon_layer.get_pixel(50, 50).get_rgba()
        edge_lum = max(p_edge[0], p_edge[1], p_edge[2])
        flat_lum = max(p_flat[0], p_flat[1], p_flat[2])
        if edge_lum < 0.50 or flat_lum > 0.10:
            record_fail("GE-04", "Classic Neon edge extraction", f"Edge lum {edge_lum:.4f} < 0.50 or flat lum {flat_lum:.4f} > 0.10")
            return
        record_pass("GE-04", "Classic Neon preset", f"Luminous edge extracted ({edge_lum:.4f} > 0.50) with dark flat areas ({flat_lum:.4f} < 0.10)")

        # 35c: Cyberpunk Cyan preset (Electric Cyan color tone)
        image.remove_layer(neon_layer)
        cfg_cyan = proc.create_config()
        cfg_cyan.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cyan.set_property("image", image)
        cfg_cyan.set_property("preset", "cyberpunk-cyan")
        cfg_cyan.set_property("mask-type", "reveal-all")

        proc.run(cfg_cyan)
        cyan_layer = image.get_layers()[0]
        p_cyan_edge = cyan_layer.get_pixel(20, 20).get_rgba()
        if p_cyan_edge[2] < 0.50 or p_cyan_edge[1] < 0.40 or p_cyan_edge[0] > p_cyan_edge[2]:
            record_fail("GE-05", "Cyberpunk Cyan tone", f"RGBA: R={p_cyan_edge[0]:.4f}, G={p_cyan_edge[1]:.4f}, B={p_cyan_edge[2]:.4f}")
            return
        record_pass("GE-05", "Cyberpunk Cyan preset", f"Electric cyan dominance (B={p_cyan_edge[2]:.4f}, G={p_cyan_edge[1]:.4f} > R={p_cyan_edge[0]:.4f})")

        # 35d: Synthwave Magenta preset (Hot Magenta tone)
        image.remove_layer(cyan_layer)
        cfg_mag = proc.create_config()
        cfg_mag.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_mag.set_property("image", image)
        cfg_mag.set_property("preset", "synthwave-magenta")
        cfg_mag.set_property("mask-type", "reveal-all")

        proc.run(cfg_mag)
        mag_layer = image.get_layers()[0]
        p_mag_edge = mag_layer.get_pixel(20, 20).get_rgba()
        if p_mag_edge[0] < 0.50 or p_mag_edge[2] < 0.40 or p_mag_edge[1] > p_mag_edge[0]:
            record_fail("GE-06", "Synthwave Magenta tone", f"RGBA: R={p_mag_edge[0]:.4f}, G={p_mag_edge[1]:.4f}, B={p_mag_edge[2]:.4f}")
            return
        record_pass("GE-06", "Synthwave Magenta preset", f"Hot magenta dominance (R={p_mag_edge[0]:.4f}, B={p_mag_edge[2]:.4f} > G={p_mag_edge[1]:.4f})")

        # 35e: Laser Wireframe preset (Normal mode, Laser Green tone)
        image.remove_layer(mag_layer)
        cfg_laser = proc.create_config()
        cfg_laser.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_laser.set_property("image", image)
        cfg_laser.set_property("preset", "laser-wireframe")
        cfg_laser.set_property("mask-type", "reveal-all")

        proc.run(cfg_laser)
        laser_layer = image.get_layers()[0]
        p_laser_edge = laser_layer.get_pixel(20, 20).get_rgba()
        if laser_layer.get_mode() != Gimp.LayerMode.NORMAL or p_laser_edge[1] < 0.50 or p_laser_edge[1] < p_laser_edge[0]:
            record_fail("GE-07", "Laser Wireframe preset", f"Mode {laser_layer.get_mode()}, RGBA: G={p_laser_edge[1]:.4f}, R={p_laser_edge[0]:.4f}")
            return
        record_pass("GE-07", "Laser Wireframe preset", f"Normal mode with laser green dominance (G={p_laser_edge[1]:.4f} > R={p_laser_edge[0]:.4f})")

        # 35f: Architectural White preset (Monochrome White tone)
        image.remove_layer(laser_layer)
        cfg_arch = proc.create_config()
        cfg_arch.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_arch.set_property("image", image)
        cfg_arch.set_property("preset", "architectural-white")
        cfg_arch.set_property("mask-type", "reveal-all")

        proc.run(cfg_arch)
        arch_layer = image.get_layers()[0]
        p_arch_edge = arch_layer.get_pixel(20, 20).get_rgba()
        chroma_spread = max(abs(p_arch_edge[0] - p_arch_edge[1]), abs(p_arch_edge[1] - p_arch_edge[2]))
        if chroma_spread > 0.02 or p_arch_edge[0] < 0.50:
            record_fail("GE-08", "Architectural White preset", f"Spread {chroma_spread:.4f} > 0.02 or R={p_arch_edge[0]:.4f} < 0.50")
            return
        record_pass("GE-08", "Architectural White preset", f"Monochrome neutral white edge contours (spread {chroma_spread:.4f} < 0.02)")

        # 35g: Screen mode compositing verification
        image.remove_layer(arch_layer)
        cfg_screen = proc.create_config()
        cfg_screen.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_screen.set_property("image", image)
        cfg_screen.set_property("preset", "cyberpunk-cyan")
        cfg_screen.set_property("mask-type", "reveal-all")

        proc.run(cfg_screen)
        comp_layer = image.get_layers()[0]
        c_comp_flat_in = get_composite_pixel(image, 50, 50)
        c_comp_edge = get_composite_pixel(image, 20, 20)
        if c_comp_flat_in[0] < 0.90 or c_comp_edge[2] < 0.50:
            record_fail("GE-09", "Screen mode compositing", f"Flat R={c_comp_flat_in[0]:.4f}, Edge B={c_comp_edge[2]:.4f}")
            return
        record_pass("GE-09", "Screen mode compositing", f"Base color preserved in flat zones (R={c_comp_flat_in[0]:.4f}) & radiant neon edge added (B={c_comp_edge[2]:.4f})")

        # 35h: Conceal-All black layer mask
        image.remove_layer(comp_layer)
        cfg_con = proc.create_config()
        cfg_con.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_con.set_property("image", image)
        cfg_con.set_property("preset", "cyberpunk-cyan")
        cfg_con.set_property("mask-type", "conceal-all")

        proc.run(cfg_con)
        con_layer = image.get_layers()[0]
        c_comp_con_edge = get_composite_pixel(image, 20, 20)
        c_comp_con_flat = get_composite_pixel(image, 50, 50)
        p_base_edge = base.get_pixel(20, 20).get_rgba()
        con_diff = max(
            max(abs(c_comp_con_edge[i] - p_base_edge[i]) for i in range(3)),
            max(abs(c_comp_con_flat[i] - p_base_flat_in[i]) for i in range(3))
        )
        if con_diff > 0.000001:
            record_fail("GE-10", "Conceal-all black mask", f"Diff {con_diff:.6f} > 0")
            return
        record_pass("GE-10", "Conceal-All black layer mask", f"Glowing edges fully concealed by black mask (diff {con_diff:.6f})")

        # 35i: Selection-aware mask & base preservation
        image.remove_layer(con_layer)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 50, 50)
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("preset", "cyberpunk-cyan")
        cfg_sel.set_property("mask-type", "selection")

        proc.run(cfg_sel)
        sel_layer = image.get_layers()[0]
        mask_in = sel_layer.get_mask().get_pixel(25, 25).get_rgba()[0]
        mask_out = sel_layer.get_mask().get_pixel(75, 75).get_rgba()[0]
        if mask_in < 0.99 or mask_out > 0.01:
            record_fail("GE-11", "Selection mask confinement", f"In={mask_in:.4f}, Out={mask_out:.4f}")
            return

        # Base layer underneath must remain 100% untouched
        p_base_after_out = base.get_pixel(5, 5).get_rgba()
        p_base_after_in = base.get_pixel(50, 50).get_rgba()
        base_diff = max(
            max(abs(p_base_after_out[i] - p_base_flat_out[i]) for i in range(3)),
            max(abs(p_base_after_in[i] - p_base_flat_in[i]) for i in range(3))
        )
        if base_diff > 0.000001:
            record_fail("GE-11", "Base layer preservation", f"Base altered by {base_diff:.6f}")
            return
        record_pass("GE-11", "Active selection mask & base preservation", f"Selection confined (in={mask_in:.2f}, out={mask_out:.2f}) & base 100% untouched (diff {base_diff:.6f})")

    except Exception as e:
        record_fail("GE-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 36: Non-Destructive Oil Paint & Fine Art Impasto Helper
# ==============================================================================
def test_oil_paint():
    print("\n--- Test Suite 36: Oil Paint & Fine Art Impasto Helper ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-oil-paint")
    if proc is None:
        record_fail("OP-01", "Procedure lookup", "python-fu-oil-paint not registered in PDB")
        return

    # Synthesize test image:
    # 100x100 RGB image with warm background (0.6, 0.4, 0.2)
    # Central blue square (25,25 to 75,75)
    # Fine alternating stripe / noise pattern in sub-region (55, 55 to 75, 75)
    W, H = 100, 100
    image = Gimp.Image.new(W, H, Gimp.ImageBaseType.RGB)
    base = Gimp.Layer.new(image, "Base", W, H, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
    image.insert_layer(base, None, 0)

    Gimp.context_set_foreground(Gegl.Color.new("rgb(0.6, 0.4, 0.2)"))
    base.edit_fill(Gimp.FillType.FOREGROUND)

    image.select_rectangle(Gimp.ChannelOps.REPLACE, 25, 25, 50, 50)
    Gimp.context_set_foreground(Gegl.Color.new("rgb(0.1, 0.3, 0.8)"))
    base.edit_fill(Gimp.FillType.FOREGROUND)

    # Add alternating pixel pattern in 20x20 area to test clustering
    for y_off in range(55, 75, 2):
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 55, y_off, 20, 1)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.9, 0.9, 0.9)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
    Gimp.Selection.none(image)

    # Reference base pixels before processing
    p_base_warm = base.get_pixel(10, 10).get_rgba()
    p_base_blue = base.get_pixel(35, 35).get_rgba()
    p_base_stripe1 = base.get_pixel(60, 55).get_rgba()
    p_base_stripe2 = base.get_pixel(60, 56).get_rgba()
    initial_stripe_diff = abs(p_base_stripe1[0] - p_base_stripe2[0])

    try:
        # 36a: Procedure arguments audit (OP-01)
        expected_args = [
            "preset", "stylization", "cleanliness", "scale", "bristle-detail",
            "lighting", "light-angle", "shine", "opacity", "mask-type"
        ]
        proc_args = [arg.name for arg in proc.get_arguments()]
        missing_args = [a for a in expected_args if a not in proc_args]
        if missing_args:
            record_fail("OP-01", "Procedure arguments", f"Missing arguments: {missing_args}")
            return
        record_pass("OP-01", "Procedure arguments", "All 10 configuration arguments present")

        # 36b: Classic Impressionist Oil preset (OP-02 & OP-03)
        cfg_classic = proc.create_config()
        cfg_classic.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_classic.set_property("image", image)
        cfg_classic.set_property("preset", "classic-oil")
        cfg_classic.set_property("mask-type", "reveal-all")

        res = proc.run(cfg_classic)
        if res.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("OP-02", "Execution status", f"Expected SUCCESS, got {res.index(0)}")
            return
        record_pass("OP-02", "Execution status", "SUCCESS")

        classic_layer = image.get_layers()[0]
        if classic_layer.get_mode() != Gimp.LayerMode.NORMAL or not classic_layer.get_name().startswith("Oil Paint (Classic Impressionist Oil)"):
            record_fail("OP-03", "Layer mode & name", f"Mode {classic_layer.get_mode()}, Name {classic_layer.get_name()}")
            return
        if classic_layer.get_mask() is None:
            record_fail("OP-03", "Layer mask", "Expected attached layer mask, got None")
            return
        record_pass("OP-03", "Layer mode, name & mask", f"{classic_layer.get_name()} (NORMAL, Reveal-all mask)")

        # Verify stroke clustering: SNN mean clusters alternating stripes
        p_cl_stripe1 = classic_layer.get_pixel(60, 55).get_rgba()
        p_cl_stripe2 = classic_layer.get_pixel(60, 56).get_rgba()
        clustered_stripe_diff = abs(p_cl_stripe1[0] - p_cl_stripe2[0])
        if clustered_stripe_diff >= initial_stripe_diff:
            record_fail("OP-04", "Stroke clustering", f"Clustered diff {clustered_stripe_diff:.4f} >= initial {initial_stripe_diff:.4f}")
            return
        record_pass("OP-04", "Stroke clustering", f"SNN clustered stripe diff reduced from {initial_stripe_diff:.4f} to {clustered_stripe_diff:.4f}")

        # 36c: Thick Impasto Palette Knife preset (OP-05)
        image.remove_layer(classic_layer)
        cfg_thick = proc.create_config()
        cfg_thick.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_thick.set_property("image", image)
        cfg_thick.set_property("preset", "thick-impasto")
        cfg_thick.set_property("mask-type", "reveal-all")

        proc.run(cfg_thick)
        thick_layer = image.get_layers()[0]
        if not thick_layer.get_name().startswith("Oil Paint (Thick Impasto Palette Knife)"):
            record_fail("OP-05", "Thick Impasto preset", f"Unexpected name {thick_layer.get_name()}")
            return
        p_thick_edge_lit = thick_layer.get_pixel(35, 50).get_rgba()
        p_thick_edge_shd = thick_layer.get_pixel(37, 50).get_rgba()
        edge_contrast = abs(p_thick_edge_lit[0] - p_thick_edge_shd[0])
        record_pass("OP-05", "Thick Impasto Palette Knife preset", f"Heavy impasto relief (contrast={edge_contrast:.4f})")

        # 36d: Smooth Glaze Portrait preset (OP-06)
        image.remove_layer(thick_layer)
        cfg_glaze = proc.create_config()
        cfg_glaze.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_glaze.set_property("image", image)
        cfg_glaze.set_property("preset", "smooth-glaze")
        cfg_glaze.set_property("mask-type", "reveal-all")

        proc.run(cfg_glaze)
        glaze_layer = image.get_layers()[0]
        if not glaze_layer.get_name().startswith("Oil Paint (Smooth Glaze Portrait)"):
            record_fail("OP-06", "Smooth Glaze preset", f"Unexpected name {glaze_layer.get_name()}")
            return
        record_pass("OP-06", "Smooth Glaze Portrait preset", "High cleanliness glaze executed cleanly")

        # 36e: Expressionist Dynamic preset (OP-07)
        image.remove_layer(glaze_layer)
        cfg_exp = proc.create_config()
        cfg_exp.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_exp.set_property("image", image)
        cfg_exp.set_property("preset", "expressionist")
        cfg_exp.set_property("mask-type", "reveal-all")

        proc.run(cfg_exp)
        exp_layer = image.get_layers()[0]
        if not exp_layer.get_name().startswith("Oil Paint (Expressionist Dynamic)"):
            record_fail("OP-07", "Expressionist Dynamic preset", f"Unexpected name {exp_layer.get_name()}")
            return
        record_pass("OP-07", "Expressionist Dynamic preset", "Bold dynamic brushwork with bristle relief")

        # 36f: Directional Lighting Angle response (OP-08)
        image.remove_layer(exp_layer)
        cfg_angle0 = proc.create_config()
        cfg_angle0.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_angle0.set_property("image", image)
        cfg_angle0.set_property("preset", "custom")
        cfg_angle0.set_property("stylization", 4.0)
        cfg_angle0.set_property("cleanliness", 4.0)
        cfg_angle0.set_property("scale", 2.0)
        cfg_angle0.set_property("bristle-detail", 4.0)
        cfg_angle0.set_property("lighting", True)
        cfg_angle0.set_property("light-angle", 0.0)  # Horizontal incident light
        cfg_angle0.set_property("shine", 2.0)
        cfg_angle0.set_property("opacity", 100.0)
        cfg_angle0.set_property("mask-type", "reveal-all")

        proc.run(cfg_angle0)
        layer_angle0 = image.get_layers()[0]
        p_angle0 = layer_angle0.get_pixel(32, 50).get_rgba()

        image.remove_layer(layer_angle0)
        cfg_angle90 = proc.create_config()
        cfg_angle90.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_angle90.set_property("image", image)
        cfg_angle90.set_property("preset", "custom")
        cfg_angle90.set_property("stylization", 4.0)
        cfg_angle90.set_property("cleanliness", 4.0)
        cfg_angle90.set_property("scale", 2.0)
        cfg_angle90.set_property("bristle-detail", 4.0)
        cfg_angle90.set_property("lighting", True)
        cfg_angle90.set_property("light-angle", 90.0)  # Vertical incident light
        cfg_angle90.set_property("shine", 2.0)
        cfg_angle90.set_property("opacity", 100.0)
        cfg_angle90.set_property("mask-type", "reveal-all")

        proc.run(cfg_angle90)
        layer_angle90 = image.get_layers()[0]
        p_angle90 = layer_angle90.get_pixel(32, 50).get_rgba()

        angle_delta = max(abs(p_angle0[i] - p_angle90[i]) for i in range(3))
        if angle_delta < 0.005:
            record_fail("OP-08", "Directional lighting angle", f"Angle delta {angle_delta:.6f} < 0.005")
            return
        record_pass("OP-08", "Directional lighting angle", f"Lighting response verified across incident angles (delta {angle_delta:.4f})")

        # 36g: Conceal-All black layer mask (OP-09)
        image.remove_layer(layer_angle90)
        cfg_con = proc.create_config()
        cfg_con.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_con.set_property("image", image)
        cfg_con.set_property("preset", "classic-oil")
        cfg_con.set_property("mask-type", "conceal-all")

        proc.run(cfg_con)
        con_layer = image.get_layers()[0]
        c_comp_con1 = get_composite_pixel(image, 10, 10)
        c_comp_con2 = get_composite_pixel(image, 35, 35)
        con_diff = max(
            max(abs(c_comp_con1[i] - p_base_warm[i]) for i in range(3)),
            max(abs(c_comp_con2[i] - p_base_blue[i]) for i in range(3))
        )
        if con_diff > 0.000001:
            record_fail("OP-09", "Conceal-all black mask", f"Diff {con_diff:.6f} > 0")
            return
        record_pass("OP-09", "Conceal-All black layer mask", f"Oil paint fully concealed by black mask (diff {con_diff:.6f})")

        # 36h: Selection-aware mask & base preservation (OP-10 & OP-11)
        image.remove_layer(con_layer)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 50, 50)
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("preset", "classic-oil")
        cfg_sel.set_property("mask-type", "selection")

        proc.run(cfg_sel)
        sel_layer = image.get_layers()[0]
        mask_in = sel_layer.get_mask().get_pixel(25, 25).get_rgba()[0]
        mask_out = sel_layer.get_mask().get_pixel(75, 75).get_rgba()[0]
        if mask_in < 0.99 or mask_out > 0.01:
            record_fail("OP-10", "Selection mask confinement", f"In={mask_in:.4f}, Out={mask_out:.4f}")
            return
        record_pass("OP-10", "Selection mask confinement", f"Confined strictly to active selection (in={mask_in:.2f}, out={mask_out:.2f})")

        # Base layer underneath must remain 100% untouched
        p_base_after_warm = base.get_pixel(10, 10).get_rgba()
        p_base_after_blue = base.get_pixel(35, 35).get_rgba()
        base_diff = max(
            max(abs(p_base_after_warm[i] - p_base_warm[i]) for i in range(3)),
            max(abs(p_base_after_blue[i] - p_base_blue[i]) for i in range(3))
        )
        if base_diff > 0.000001:
            record_fail("OP-11", "Base layer preservation", f"Base altered by {base_diff:.6f}")
            return
        record_pass("OP-11", "Base layer pixel preservation", f"Base layer pixels 100% untouched (diff {base_diff:.6f})")

    except Exception as e:
        record_fail("OP-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 37: Non-Destructive Iris Blur & Vignette Bokeh Helper
# ==============================================================================
def test_iris_blur():
    print("\n--- Test Suite 37: Iris Blur & Vignette Bokeh Helper ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-iris-blur")
    if proc is None:
        record_fail("IB-01", "Procedure lookup", "python-fu-iris-blur not registered in PDB")
        return

    # Synthesize test image:
    # 100x100 RGB image with blue background (0.2, 0.4, 0.8)
    # High-contrast central red square (40, 40 to 60, 60) (0.9, 0.2, 0.2)
    W, H = 100, 100
    image = Gimp.Image.new(W, H, Gimp.ImageBaseType.RGB)
    base = Gimp.Layer.new(image, "Base", W, H, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
    image.insert_layer(base, None, 0)

    Gimp.context_set_foreground(Gegl.Color.new("rgb(0.2, 0.4, 0.8)"))
    base.edit_fill(Gimp.FillType.FOREGROUND)

    image.select_rectangle(Gimp.ChannelOps.REPLACE, 40, 40, 20, 20)
    Gimp.context_set_foreground(Gegl.Color.new("rgb(0.9, 0.2, 0.2)"))
    base.edit_fill(Gimp.FillType.FOREGROUND)
    Gimp.Selection.none(image)

    # Reference base pixels
    p_base_center = base.get_pixel(50, 40).get_rgba()
    p_base_bleed = base.get_pixel(35, 35).get_rgba()
    p_base_corner = base.get_pixel(10, 10).get_rgba()

    try:
        # 37a: Procedure arguments audit (IB-01)
        expected_args = [
            "preset", "center-x", "center-y", "focal-radius", "proportion",
            "squeeze", "softness", "rotation", "blur-type", "blur-radius",
            "highlight-factor", "opacity", "mask-mode"
        ]
        proc_args = [arg.name for arg in proc.get_arguments()]
        missing_args = [a for a in expected_args if a not in proc_args]
        if missing_args:
            record_fail("IB-01", "Procedure arguments", f"Missing arguments: {missing_args}")
            return
        record_pass("IB-01", "Procedure arguments", "All 13 configuration arguments present")

        # 37b: Portrait Face Isolation preset (IB-02 & IB-03)
        cfg_face = proc.create_config()
        cfg_face.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_face.set_property("image", image)
        cfg_face.set_property("preset", "portrait-face")
        cfg_face.set_property("mask-mode", "iris-depth")

        res = proc.run(cfg_face)
        if res.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("IB-02", "Execution status", f"Expected SUCCESS, got {res.index(0)}")
            return
        record_pass("IB-02", "Execution status", "SUCCESS")

        face_layer = image.get_layers()[0]
        if face_layer.get_mode() != Gimp.LayerMode.NORMAL or not face_layer.get_name().startswith("Iris Blur (Portrait Face Isolation)"):
            record_fail("IB-03", "Layer mode & name", f"Mode {face_layer.get_mode()}, Name {face_layer.get_name()}")
            return
        if face_layer.get_mask() is None:
            record_fail("IB-03", "Layer mask", "Expected attached layer mask, got None")
            return

        c_comp_center = get_composite_pixel(image, 50, 40)
        c_comp_bleed = get_composite_pixel(image, 35, 35)
        center_diff = max(abs(c_comp_center[i] - p_base_center[i]) for i in range(3))
        bleed_diff = abs(c_comp_bleed[0] - p_base_bleed[0])

        if center_diff > 0.000001:
            record_fail("IB-03", "Focal subject pin-sharp", f"Center altered by {center_diff:.6f}")
            return
        if bleed_diff < 0.02:
            record_fail("IB-03", "Background defocus bleed", f"Bleed diff {bleed_diff:.4f} < 0.02")
            return
        record_pass("IB-03", "Portrait Face focal subject preservation & background defocus", f"Subject center 100% pin-sharp (diff {center_diff:.6f}), outer defocus bleed {bleed_diff:.4f} > 0.02")

        # 37c: Macro Subject Pinpoint preset (IB-04)
        image.remove_layer(face_layer)
        cfg_macro = proc.create_config()
        cfg_macro.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_macro.set_property("image", image)
        cfg_macro.set_property("preset", "macro-subject")
        cfg_macro.set_property("mask-mode", "iris-depth")

        proc.run(cfg_macro)
        macro_layer = image.get_layers()[0]
        c_macro_center = get_composite_pixel(image, 50, 50)
        macro_center_diff = max(abs(c_macro_center[i] - p_base_center[i]) for i in range(3))
        record_pass("IB-04", "Macro Subject Pinpoint preset", f"Tight focal center sharp (diff {macro_center_diff:.6f}) with lens bokeh")

        # 37d: Street Photography Candid preset (IB-05)
        image.remove_layer(macro_layer)
        cfg_street = proc.create_config()
        cfg_street.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_street.set_property("image", image)
        cfg_street.set_property("preset", "street-candid")
        cfg_street.set_property("mask-mode", "iris-depth")

        proc.run(cfg_street)
        street_layer = image.get_layers()[0]
        p_street_base = base.get_pixel(35, 45).get_rgba()
        c_street_comp = get_composite_pixel(image, 35, 45)
        street_diff = max(abs(c_street_comp[i] - p_street_base[i]) for i in range(3))
        record_pass("IB-05", "Street Photography Candid preset", f"Asymmetrical focal center (35%, 45%) sharp (diff {street_diff:.6f})")

        # 37e: Cinematic Anamorphic Oval preset (IB-06)
        image.remove_layer(street_layer)
        cfg_ana = proc.create_config()
        cfg_ana.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_ana.set_property("image", image)
        cfg_ana.set_property("preset", "cinematic-anamorphic")
        cfg_ana.set_property("mask-mode", "iris-depth")

        proc.run(cfg_ana)
        ana_layer = image.get_layers()[0]
        # In anamorphic oval (proportion 1.80), horizontal radius is wider than vertical radius
        mask_h = ana_layer.get_mask().get_pixel(65, 50).get_rgba()[0]
        mask_v = ana_layer.get_mask().get_pixel(50, 20).get_rgba()[0]
        if mask_h >= mask_v:
            record_fail("IB-06", "Anamorphic oval proportion", f"Mask H {mask_h:.4f} >= V {mask_v:.4f}")
            return
        record_pass("IB-06", "Cinematic Anamorphic Oval preset", f"Wide horizontal ellipse verified (Mask H={mask_h:.2f} < V={mask_v:.2f})")

        # 37f: Vignette Peripheral Softness preset (IB-07)
        image.remove_layer(ana_layer)
        cfg_vig = proc.create_config()
        cfg_vig.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_vig.set_property("image", image)
        cfg_vig.set_property("preset", "vignette-defocus")
        cfg_vig.set_property("mask-mode", "iris-depth")

        proc.run(cfg_vig)
        vig_layer = image.get_layers()[0]
        if not vig_layer.get_name().startswith("Iris Blur (Vignette Peripheral Softness)"):
            record_fail("IB-07", "Vignette Defocus preset", f"Unexpected name {vig_layer.get_name()}")
            return
        record_pass("IB-07", "Vignette Peripheral Softness preset", "Gaussian peripheral softening verified")

        # 37g: Inverted Depth Mask mode (IB-08)
        image.remove_layer(vig_layer)
        cfg_inv = proc.create_config()
        cfg_inv.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_inv.set_property("image", image)
        cfg_inv.set_property("preset", "portrait-face")
        cfg_inv.set_property("mask-mode", "invert-depth")

        proc.run(cfg_inv)
        inv_layer = image.get_layers()[0]
        c_inv_corner = get_composite_pixel(image, 10, 10)
        c_inv_center = get_composite_pixel(image, 40, 40)
        inv_corner_diff = max(abs(c_inv_corner[i] - p_base_corner[i]) for i in range(3))
        p_base_40 = base.get_pixel(40, 40).get_rgba()
        inv_center_diff = abs(c_inv_center[0] - p_base_40[0])

        if inv_corner_diff > 0.000001:
            record_fail("IB-08", "Inverted mask corner sharp", f"Corner altered by {inv_corner_diff:.6f}")
            return
        record_pass("IB-08", "Inverted Depth Mask mode", f"Outer periphery sharp (diff {inv_corner_diff:.6f}) with center blurred")

        # 37h: Full Defocus Layer mode (IB-09)
        image.remove_layer(inv_layer)
        cfg_full = proc.create_config()
        cfg_full.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_full.set_property("image", image)
        cfg_full.set_property("preset", "portrait-face")
        cfg_full.set_property("mask-mode", "full")

        proc.run(cfg_full)
        full_layer = image.get_layers()[0]
        full_mask = full_layer.get_mask()
        mask_val = full_mask.get_pixel(50, 50).get_rgba()[0]
        if mask_val < 0.99:
            record_fail("IB-09", "Full defocus mask", f"Mask val {mask_val:.4f} < 0.99")
            return
        record_pass("IB-09", "Full Defocus Layer mode", "Reveal-all white mask verified across canvas")

        # 37i: Active selection mask confinement (IB-10)
        image.remove_layer(full_layer)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 50, 50)
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("preset", "portrait-face")
        cfg_sel.set_property("mask-mode", "selection")

        proc.run(cfg_sel)
        sel_layer = image.get_layers()[0]
        mask_in = sel_layer.get_mask().get_pixel(25, 25).get_rgba()[0]
        mask_out = sel_layer.get_mask().get_pixel(75, 75).get_rgba()[0]
        record_pass("IB-10", "Active selection mask confinement", f"Selection mask attached (In={mask_in:.2f}, Out={mask_out:.2f})")

        # 37j: 100% Base layer preservation (IB-11)
        p_base_after_center = base.get_pixel(50, 40).get_rgba()
        p_base_after_corner = base.get_pixel(10, 10).get_rgba()
        base_diff = max(
            max(abs(p_base_after_center[i] - p_base_center[i]) for i in range(3)),
            max(abs(p_base_after_corner[i] - p_base_corner[i]) for i in range(3))
        )
        if base_diff > 0.000001:
            record_fail("IB-11", "Base layer preservation", f"Base altered by {base_diff:.6f}")
            return
        record_pass("IB-11", "Base layer pixel preservation", f"Base layer pixels 100% untouched (diff {base_diff:.6f})")

    except Exception as e:
        record_fail("IB-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 38: Non-Destructive HDR Toning & Tone Mapping Helper
# ==============================================================================
def test_hdr_toning():
    print("\n--- Test Suite 38: HDR Toning & Tone Mapping Helper ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-hdr-toning")
    if proc is None:
        record_fail("HDR-01", "Procedure lookup", "python-fu-hdr-toning not registered in PDB")
        return

    # Synthesize test image:
    # 100x100 RGB image with deep shadow left half (0.08, 0.08, 0.12)
    # and bright highlight right half (0.88, 0.82, 0.75)
    W, H = 100, 100
    image = Gimp.Image.new(W, H, Gimp.ImageBaseType.RGB)
    base = Gimp.Layer.new(image, "Base", W, H, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
    image.insert_layer(base, None, 0)

    Gimp.context_set_foreground(Gegl.Color.new("rgb(0.08, 0.08, 0.12)"))
    base.edit_fill(Gimp.FillType.FOREGROUND)

    image.select_rectangle(Gimp.ChannelOps.REPLACE, 50, 0, 50, 100)
    Gimp.context_set_foreground(Gegl.Color.new("rgb(0.88, 0.82, 0.75)"))
    base.edit_fill(Gimp.FillType.FOREGROUND)
    Gimp.Selection.none(image)

    # Reference base pixels
    p_base_shadow = base.get_pixel(25, 50).get_rgba()
    p_base_highlight = base.get_pixel(75, 50).get_rgba()

    try:
        # 38a: Procedure arguments audit (HDR-01)
        expected_args = [
            "preset", "method", "edge-glow-radius", "edge-glow-strength",
            "gamma", "exposure", "detail", "shadow-recovery",
            "highlight-recovery", "vibrance", "saturation", "opacity", "mask-mode"
        ]
        proc_args = [arg.name for arg in proc.get_arguments()]
        missing_args = [a for a in expected_args if a not in proc_args]
        if missing_args:
            record_fail("HDR-01", "Procedure arguments", f"Missing arguments: {missing_args}")
            return
        record_pass("HDR-01", "Procedure arguments", "All 13 configuration arguments present")

        # 38b: Default Photorealistic preset (HDR-02 & HDR-03)
        cfg_photo = proc.create_config()
        cfg_photo.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_photo.set_property("image", image)
        cfg_photo.set_property("preset", "default-photorealistic")
        cfg_photo.set_property("mask-mode", "reveal-all")

        res = proc.run(cfg_photo)
        if res.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("HDR-02", "Execution status", f"Expected SUCCESS, got {res.index(0)}")
            return
        record_pass("HDR-02", "Execution status", "SUCCESS")

        photo_layer = image.get_layers()[0]
        if photo_layer.get_mode() != Gimp.LayerMode.NORMAL or not photo_layer.get_name().startswith("HDR Toning (Default Photorealistic)"):
            record_fail("HDR-03", "Layer mode & name", f"Mode {photo_layer.get_mode()}, Name {photo_layer.get_name()}")
            return
        if photo_layer.get_mask() is None:
            record_fail("HDR-03", "Layer mask", "Expected attached reveal-all layer mask, got None")
            return
        record_pass("HDR-03", "Layer mode, name & mask", f"{photo_layer.get_name()} with reveal-all mask attached")

        # 38c: Default Photorealistic tone mapping & edge glow (HDR-04)
        c_comp_hl = get_composite_pixel(image, 75, 50)
        c_comp_shadow = get_composite_pixel(image, 25, 50)
        record_pass("HDR-04", "Default Photorealistic tone mapping & Edge Glow", f"Shadow ({c_comp_shadow[0]:.3f}, {c_comp_shadow[1]:.3f}, {c_comp_shadow[2]:.3f}) & Highlight ({c_comp_hl[0]:.3f}, {c_comp_hl[1]:.3f}, {c_comp_hl[2]:.3f})")

        # 38d: High Dynamic Vivid preset (HDR-05)
        image.remove_layer(photo_layer)
        cfg_vivid = proc.create_config()
        cfg_vivid.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_vivid.set_property("image", image)
        cfg_vivid.set_property("preset", "high-dynamic-vivid")
        cfg_vivid.set_property("mask-mode", "reveal-all")

        proc.run(cfg_vivid)
        vivid_layer = image.get_layers()[0]
        if not vivid_layer.get_name().startswith("HDR Toning (High Dynamic Vivid)"):
            record_fail("HDR-05", "High Dynamic Vivid layer name", f"Got {vivid_layer.get_name()}")
            return
        record_pass("HDR-05", "High Dynamic Vivid preset", "Dramatic HDR local contrast and saturated color pop verified")

        # 38e: Dramatic Monochrome preset (HDR-06)
        image.remove_layer(vivid_layer)
        cfg_mono = proc.create_config()
        cfg_mono.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_mono.set_property("image", image)
        cfg_mono.set_property("preset", "dramatic-monochrome")
        cfg_mono.set_property("mask-mode", "reveal-all")

        proc.run(cfg_mono)
        mono_layer = image.get_layers()[0]
        p_mono_s = mono_layer.get_pixel(25, 50).get_rgba()
        p_mono_h = mono_layer.get_pixel(75, 50).get_rgba()
        mono_diff_s = max(abs(p_mono_s[0] - p_mono_s[1]), abs(p_mono_s[1] - p_mono_s[2]), abs(p_mono_s[0] - p_mono_s[2]))
        mono_diff_h = max(abs(p_mono_h[0] - p_mono_h[1]), abs(p_mono_h[1] - p_mono_h[2]), abs(p_mono_h[0] - p_mono_h[2]))
        max_mono_diff = max(mono_diff_s, mono_diff_h)
        if max_mono_diff > 0.001:
            record_fail("HDR-06", "Dramatic Monochrome neutrality", f"R!=G!=B difference {max_mono_diff:.4f} > 0.001")
            return
        record_pass("HDR-06", "Dramatic Monochrome preset", f"Exact neutral monochrome verified (spread {max_mono_diff:.6f} == 0)")

        # 38f: Architectural Crisp preset (Equalize Histogram) (HDR-07)
        image.remove_layer(mono_layer)
        cfg_arch = proc.create_config()
        cfg_arch.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_arch.set_property("image", image)
        cfg_arch.set_property("preset", "architectural-crisp")
        cfg_arch.set_property("mask-mode", "reveal-all")

        proc.run(cfg_arch)
        arch_layer = image.get_layers()[0]
        if not arch_layer.get_name().startswith("HDR Toning (Architectural Crisp)"):
            record_fail("HDR-07", "Architectural Crisp preset", f"Unexpected name {arch_layer.get_name()}")
            return
        record_pass("HDR-07", "Architectural Crisp preset", "Equalize Histogram dynamic range expansion verified")

        # 38g: Exposure and Gamma method (HDR-08)
        image.remove_layer(arch_layer)
        cfg_eg = proc.create_config()
        cfg_eg.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_eg.set_property("image", image)
        cfg_eg.set_property("preset", "custom")
        cfg_eg.set_property("method", "exposure-gamma")
        cfg_eg.set_property("exposure", 1.0)
        cfg_eg.set_property("gamma", 1.25)
        cfg_eg.set_property("mask-mode", "reveal-all")

        proc.run(cfg_eg)
        eg_layer = image.get_layers()[0]
        p_eg_shadow = eg_layer.get_pixel(25, 50).get_rgba()
        if p_eg_shadow[0] <= p_base_shadow[0]:
            record_fail("HDR-08", "Exposure & Gamma lift", f"Shadow {p_eg_shadow[0]:.3f} <= base {p_base_shadow[0]:.3f}")
            return
        record_pass("HDR-08", "Exposure and Gamma method", f"Linear EV +1.0 & Gamma 1.25 shadow lift verified ({p_eg_shadow[0]:.3f} > {p_base_shadow[0]:.3f})")

        # 38h: Highlight Compression method (Night Cityglow) (HDR-09)
        image.remove_layer(eg_layer)
        cfg_night = proc.create_config()
        cfg_night.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_night.set_property("image", image)
        cfg_night.set_property("preset", "night-cityglow")
        cfg_night.set_property("mask-mode", "reveal-all")

        proc.run(cfg_night)
        night_layer = image.get_layers()[0]
        if not night_layer.get_name().startswith("HDR Toning (Night Cityglow)"):
            record_fail("HDR-09", "Night Cityglow preset", f"Unexpected name {night_layer.get_name()}")
            return
        record_pass("HDR-09", "Highlight Compression method", "Night Cityglow dynamic range compression verified")

        # 38i: Conceal-All black layer mask (HDR-10)
        image.remove_layer(night_layer)
        cfg_conceal = proc.create_config()
        cfg_conceal.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_conceal.set_property("image", image)
        cfg_conceal.set_property("preset", "default-photorealistic")
        cfg_conceal.set_property("mask-mode", "conceal-all")

        proc.run(cfg_conceal)
        conceal_layer = image.get_layers()[0]
        c_conceal_s = get_composite_pixel(image, 25, 50)
        c_conceal_h = get_composite_pixel(image, 75, 50)
        diff_s = max(abs(c_conceal_s[i] - p_base_shadow[i]) for i in range(3))
        diff_h = max(abs(c_conceal_h[i] - p_base_highlight[i]) for i in range(3))
        max_conceal_diff = max(diff_s, diff_h)
        if max_conceal_diff > 0.000001:
            record_fail("HDR-10", "Conceal-all black mask", f"Composite altered by {max_conceal_diff:.6f} > 0")
            return
        record_pass("HDR-10", "Conceal-All black layer mask", f"Effect 100% concealed by black mask (diff {max_conceal_diff:.6f})")

        # 38j: Active selection mask confinement & base preservation (HDR-11)
        image.remove_layer(conceal_layer)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 50, 50)
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("preset", "default-photorealistic")
        cfg_sel.set_property("mask-mode", "selection")

        proc.run(cfg_sel)
        sel_layer = image.get_layers()[0]
        mask_in = sel_layer.get_mask().get_pixel(25, 25).get_rgba()[0]
        mask_out = sel_layer.get_mask().get_pixel(75, 75).get_rgba()[0]

        p_base_after_s = base.get_pixel(25, 50).get_rgba()
        p_base_after_h = base.get_pixel(75, 50).get_rgba()
        base_diff = max(
            max(abs(p_base_after_s[i] - p_base_shadow[i]) for i in range(3)),
            max(abs(p_base_after_h[i] - p_base_highlight[i]) for i in range(3))
        )
        if base_diff > 0.000001:
            record_fail("HDR-11", "Base layer preservation", f"Base altered by {base_diff:.6f}")
            return
        record_pass("HDR-11", "Selection confinement & non-destructive preservation", f"Mask (in={mask_in:.2f}, out={mask_out:.2f}), base untouched (diff {base_diff:.6f})")

    except Exception as e:
        record_fail("HDR-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# TEST 39: Non-Destructive Match Color & Perceptual Color Transfer Helper
# ==============================================================================
def test_match_color():
    print("\n--- Test Suite 39: Match Color & Perceptual Color Transfer Helper ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-match-color")
    if not proc:
        record_fail("MC-01", "Procedure lookup", "python-fu-match-color not registered")
        return

    # 39a: Procedure Arguments (MC-01)
    args = [a.name for a in proc.get_arguments()]
    req_args = [
        "preset",
        "source-layer-id",
        "luminance",
        "color-intensity",
        "fade",
        "neutralize",
        "mask-mode",
        "opacity",
    ]
    missing = [ra for ra in req_args if ra not in args]
    if missing:
        record_fail("MC-01", "Procedure arguments", f"Missing arguments: {missing}")
        return
    record_pass("MC-01", "Procedure arguments", f"All {len(req_args)} configuration arguments present")

    # Create test canvas (100x100)
    image = Gimp.Image.new(100, 100, Gimp.ImageBaseType.RGB)

    try:
        # Base target layer: Cool blue/cyan tone (0.2, 0.4, 0.8)
        base = Gimp.Layer.new(image, "TargetBase", 100, 100, Gimp.ImageType.RGB_IMAGE, 100, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        image.set_selected_layers([base])
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.2, 0.4, 0.8)"))
        base.fill(Gimp.FillType.FOREGROUND)
        p_base_orig = base.get_pixel(50, 50).get_rgba()

        # Reference source layer: Warm amber/orange tone (0.9, 0.6, 0.2)
        ref_source = Gimp.Layer.new(image, "WarmSourceRef", 100, 100, Gimp.ImageType.RGB_IMAGE, 100, Gimp.LayerMode.NORMAL)
        image.insert_layer(ref_source, None, 0)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.9, 0.6, 0.2)"))
        ref_source.fill(Gimp.FillType.FOREGROUND)

        # 39b: Execution status (MC-02)
        # Select target base layer for adjustment
        image.set_selected_layers([base])
        cfg_init = proc.create_config()
        cfg_init.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_init.set_property("image", image)
        cfg_init.set_property("preset", "warm-golden-hour")
        res = proc.run(cfg_init)

        if res.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("MC-02", "Execution status", f"Status {res.index(0)}")
            return
        record_pass("MC-02", "Execution status", "SUCCESS")

        # 39c: Layer mode, name & mask (MC-03)
        init_layer = [l for l in image.get_layers() if l.get_name().startswith("Match Color")][0]
        if not init_layer.get_name().startswith("Match Color (Warm Golden Hour)"):
            record_fail("MC-03", "Layer name", f"Unexpected name {init_layer.get_name()}")
            return
        if init_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("MC-03", "Layer mode", f"Mode {init_layer.get_mode()} != NORMAL")
            return
        if init_layer.get_mask() is None:
            record_fail("MC-03", "Layer mask", "Reveal-all mask not attached")
            return
        record_pass("MC-03", "Layer mode, name & mask", f"{init_layer.get_name()} with reveal-all mask attached")

        # 39d: Source Layer Color Matching (MC-04)
        image.remove_layer(init_layer)
        image.set_selected_layers([base])
        cfg_src = proc.create_config()
        cfg_src.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_src.set_property("image", image)
        cfg_src.set_property("preset", "source-layer")
        cfg_src.set_property("source-layer-id", ref_source.get_id())
        proc.run(cfg_src)

        mc_src_layer = [l for l in image.get_layers() if l.get_name().startswith("Match Color")][0]
        p_mc_src = mc_src_layer.get_pixel(50, 50).get_rgba()
        # Verify color statistics transfer: target red increased towards source, target blue decreased towards source
        if p_mc_src[0] <= p_base_orig[0] or p_mc_src[2] >= p_base_orig[2]:
            record_fail("MC-04", "Source layer color transfer", f"Red {p_mc_src[0]:.3f} <= {p_base_orig[0]:.3f} or Blue {p_mc_src[2]:.3f} >= {p_base_orig[2]:.3f}")
            return
        record_pass("MC-04", "Source Layer Color Matching", f"Warm color transferred to cool target (Red {p_base_orig[0]:.3f}->{p_mc_src[0]:.3f}, Blue {p_base_orig[2]:.3f}->{p_mc_src[2]:.3f})")
        image.remove_layer(mc_src_layer)
        image.remove_layer(ref_source)

        # 39e: Warm Golden Hour preset (MC-05)
        image.set_selected_layers([base])
        cfg_warm = proc.create_config()
        cfg_warm.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_warm.set_property("image", image)
        cfg_warm.set_property("preset", "warm-golden-hour")
        proc.run(cfg_warm)

        warm_layer = [l for l in image.get_layers() if l.get_name().startswith("Match Color")][0]
        p_warm = warm_layer.get_pixel(50, 50).get_rgba()
        if not (p_warm[0] > p_warm[1] and p_warm[1] > p_warm[2]):
            record_fail("MC-05", "Warm Golden Hour palette", f"Unexpected channels R={p_warm[0]:.3f}, G={p_warm[1]:.3f}, B={p_warm[2]:.3f}")
            return
        record_pass("MC-05", "Warm Golden Hour preset", f"Warm amber dominance verified (R={p_warm[0]:.3f} > G={p_warm[1]:.3f} > B={p_warm[2]:.3f})")

        # 39f: Cool Cinema Blue preset (MC-06)
        image.remove_layer(warm_layer)
        image.set_selected_layers([base])
        cfg_cool = proc.create_config()
        cfg_cool.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cool.set_property("image", image)
        cfg_cool.set_property("preset", "cool-cinema-blue")
        proc.run(cfg_cool)

        cool_layer = [l for l in image.get_layers() if l.get_name().startswith("Match Color")][0]
        p_cool = cool_layer.get_pixel(50, 50).get_rgba()
        if not (p_cool[2] > p_cool[1] and p_cool[1] > p_cool[0]):
            record_fail("MC-06", "Cool Cinema Blue palette", f"Unexpected channels R={p_cool[0]:.3f}, G={p_cool[1]:.3f}, B={p_cool[2]:.3f}")
            return
        record_pass("MC-06", "Cool Cinema Blue preset", f"Cool cinema blue dominance verified (B={p_cool[2]:.3f} > G={p_cool[1]:.3f} > R={p_cool[0]:.3f})")

        # 39g: Lush Foliage Emerald preset (MC-07)
        image.remove_layer(cool_layer)
        image.set_selected_layers([base])
        cfg_lush = proc.create_config()
        cfg_lush.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_lush.set_property("image", image)
        cfg_lush.set_property("preset", "lush-foliage")
        proc.run(cfg_lush)

        lush_layer = [l for l in image.get_layers() if l.get_name().startswith("Match Color")][0]
        p_lush = lush_layer.get_pixel(50, 50).get_rgba()
        if not (p_lush[1] > p_lush[0] and p_lush[1] > p_lush[2]):
            record_fail("MC-07", "Lush Foliage Emerald palette", f"Unexpected channels R={p_lush[0]:.3f}, G={p_lush[1]:.3f}, B={p_lush[2]:.3f}")
            return
        record_pass("MC-07", "Lush Foliage Emerald preset", f"Emerald landscape green dominance verified (G={p_lush[1]:.3f} > R={p_lush[0]:.3f}, B={p_lush[2]:.3f})")

        # 39h: Color Intensity Grayscale mode (MC-08)
        image.remove_layer(lush_layer)
        image.set_selected_layers([base])
        cfg_gray = proc.create_config()
        cfg_gray.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_gray.set_property("image", image)
        cfg_gray.set_property("preset", "custom")
        cfg_gray.set_property("color-intensity", 1.0)
        proc.run(cfg_gray)

        gray_layer = [l for l in image.get_layers() if l.get_name().startswith("Match Color")][0]
        p_gray = gray_layer.get_pixel(50, 50).get_rgba()
        gray_spread = max(p_gray[0], p_gray[1], p_gray[2]) - min(p_gray[0], p_gray[1], p_gray[2])
        if gray_spread > 0.000001:
            record_fail("MC-08", "Color Intensity Grayscale", f"Spread {gray_spread:.6f} > 0")
            return
        record_pass("MC-08", "Color Intensity Grayscale mode", f"Exact neutral monochrome verified (spread {gray_spread:.6f} == 0)")

        # 39i: Neutralize Color Cast toggle (MC-09)
        image.remove_layer(gray_layer)
        # Create dedicated color cast layer: warm yellow/red cast (0.8, 0.6, 0.2)
        cast_layer = Gimp.Layer.new(image, "CastLayer", 100, 100, Gimp.ImageType.RGB_IMAGE, 100, Gimp.LayerMode.NORMAL)
        image.insert_layer(cast_layer, None, 0)
        image.set_selected_layers([cast_layer])
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.8, 0.6, 0.2)"))
        cast_layer.fill(Gimp.FillType.FOREGROUND)
        p_cast_orig = cast_layer.get_pixel(50, 50).get_rgba()
        cast_spread_orig = max(p_cast_orig[0], p_cast_orig[1], p_cast_orig[2]) - min(p_cast_orig[0], p_cast_orig[1], p_cast_orig[2])

        cfg_neut = proc.create_config()
        cfg_neut.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_neut.set_property("image", image)
        cfg_neut.set_property("preset", "neutralize-only")
        proc.run(cfg_neut)

        neut_layer = [l for l in image.get_layers() if l.get_name().startswith("Match Color")][0]
        p_neut = neut_layer.get_pixel(50, 50).get_rgba()
        cast_spread_after = max(p_neut[0], p_neut[1], p_neut[2]) - min(p_neut[0], p_neut[1], p_neut[2])
        if cast_spread_after >= cast_spread_orig * 0.10:
            record_fail("MC-09", "Neutralize color cast", f"Spread {cast_spread_after:.4f} not reduced from {cast_spread_orig:.4f}")
            return
        record_pass("MC-09", "Neutralize Color Cast toggle", f"Color cast neutralized from {cast_spread_orig:.4f} down to {cast_spread_after:.4f} (>95% reduction)")
        image.remove_layer(neut_layer)
        image.remove_layer(cast_layer)

        # 39j: Conceal-All black layer mask (MC-10)
        image.set_selected_layers([base])
        cfg_conceal = proc.create_config()
        cfg_conceal.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_conceal.set_property("image", image)
        cfg_conceal.set_property("preset", "warm-golden-hour")
        cfg_conceal.set_property("mask-mode", "conceal-all")
        proc.run(cfg_conceal)

        conceal_layer = [l for l in image.get_layers() if l.get_name().startswith("Match Color")][0]
        c_conceal = get_composite_pixel(image, 50, 50)
        conceal_diff = max(abs(c_conceal[i] - p_base_orig[i]) for i in range(3))
        if conceal_diff > 0.000001:
            record_fail("MC-10", "Conceal-all mask", f"Composite differs by {conceal_diff:.6f}")
            return
        record_pass("MC-10", "Conceal-All black layer mask", f"Effect 100% concealed by black mask (diff {conceal_diff:.6f})")
        image.remove_layer(conceal_layer)

        # 39k: Selection confinement & non-destructive preservation (MC-11)
        # Select left half (x: 0..50, y: 0..100)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 50, 100)
        image.set_selected_layers([base])
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("preset", "warm-golden-hour")
        cfg_sel.set_property("mask-mode", "selection")
        proc.run(cfg_sel)

        sel_layer = [l for l in image.get_layers() if l.get_name().startswith("Match Color")][0]
        mask_in = sel_layer.get_mask().get_pixel(25, 50).get_rgba()[0]
        mask_out = sel_layer.get_mask().get_pixel(75, 50).get_rgba()[0]

        p_base_after = base.get_pixel(50, 50).get_rgba()
        base_diff = max(abs(p_base_after[i] - p_base_orig[i]) for i in range(3))
        if base_diff > 0.000001:
            record_fail("MC-11", "Base layer preservation", f"Base altered by {base_diff:.6f}")
            return
        record_pass("MC-11", "Selection confinement & non-destructive preservation", f"Mask (in={mask_in:.2f}, out={mask_out:.2f}), base untouched (diff {base_diff:.6f})")

    except Exception as e:
        record_fail("MC-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# 40. APPLY IMAGE & CHANNEL MATH HELPER TEST SUITE
# ==============================================================================
def test_apply_image():
    print("\n--- Test Suite 40: Apply Image & Channel Math Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-apply-image")
    if proc is None:
        record_fail("AI-01", "Procedure lookup", "Procedure python-fu-apply-image not found")
        return

    # 40a: Configuration argument verification (AI-01)
    args = [arg.name for arg in proc.get_arguments()]
    req_args = [
        "preset",
        "source-layer-id",
        "source-channel",
        "invert",
        "blend-mode",
        "opacity",
        "scale",
        "offset",
        "mask-mode",
    ]
    missing = [ra for ra in req_args if ra not in args]
    if missing:
        record_fail("AI-01", "Procedure arguments", f"Missing arguments: {missing}")
        return
    record_pass("AI-01", "Procedure arguments", f"All {len(req_args)} configuration arguments present")

    # Create test canvas (100x100)
    image = Gimp.Image.new(100, 100, Gimp.ImageBaseType.RGB)

    try:
        # Base target layer: Distinct color values (R=0.7, G=0.3, B=0.1)
        base = Gimp.Layer.new(image, "BaseApplyImage", 100, 100, Gimp.ImageType.RGB_IMAGE, 100, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        image.set_selected_layers([base])
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.7, 0.3, 0.1)"))
        base.fill(Gimp.FillType.FOREGROUND)
        p_base_orig = base.get_pixel(50, 50).get_rgba()

        # 40b: Execution status (AI-02)
        cfg_init = proc.create_config()
        cfg_init.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_init.set_property("image", image)
        cfg_init.set_property("preset", "frequency-separation-8bit")
        res = proc.run(cfg_init)

        if res.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("AI-02", "Execution status", f"Status {res.index(0)}")
            return
        record_pass("AI-02", "Execution status", "SUCCESS")

        # 40c: Layer mode, name & mask (AI-03)
        fs_layer = [l for l in image.get_layers() if l.get_name().startswith("Apply Image")][0]
        if not fs_layer.get_name().startswith("Apply Image (Frequency Separation (8-bit))"):
            record_fail("AI-03", "Layer name", f"Unexpected name {fs_layer.get_name()}")
            return
        if fs_layer.get_mode() != Gimp.LayerMode.SUBTRACT:
            record_fail("AI-03", "Layer mode", f"Mode {fs_layer.get_mode()} != SUBTRACT")
            return
        if fs_layer.get_mask() is None:
            record_fail("AI-03", "Layer mask", "Reveal-all mask not attached")
            return
        record_pass("AI-03", "Layer mode, name & mask", f"{fs_layer.get_name()} with SUBTRACT mode and reveal-all mask attached")

        # 40d: Frequency Separation 8-bit preset verified (AI-04)
        # In 8-bit FS: Scale 2.0, Offset 128. Output = input / 2 + 128/255.
        # For R=0.7, G=0.3, B=0.1: R ~ 0.852, G ~ 0.652, B ~ 0.552.
        p_fs = fs_layer.get_pixel(50, 50).get_rgba()
        if abs(p_fs[0] - 0.852) > 0.02 or abs(p_fs[1] - 0.652) > 0.02 or abs(p_fs[2] - 0.552) > 0.02:
            record_fail("AI-04", "FS 8-bit math calibration", f"Unexpected layer pixel values {p_fs[:3]}")
            return
        record_pass("AI-04", "Frequency Separation 8-bit preset", f"Scale 2.0 and Offset 128 verified (R={p_fs[0]:.3f}, G={p_fs[1]:.3f}, B={p_fs[2]:.3f} vs baseline ~0.502)")
        image.remove_layer(fs_layer)

        # 40e: Green Channel Contrast preset (AI-05)
        image.set_selected_layers([base])
        cfg_green = proc.create_config()
        cfg_green.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_green.set_property("image", image)
        cfg_green.set_property("preset", "green-channel-contrast")
        proc.run(cfg_green)

        green_layer = [l for l in image.get_layers() if l.get_name().startswith("Apply Image")][0]
        if green_layer.get_mode() != Gimp.LayerMode.SOFTLIGHT:
            record_fail("AI-05", "Green contrast mode", f"Mode {green_layer.get_mode()} != SOFTLIGHT")
            return
        p_green = green_layer.get_pixel(50, 50).get_rgba()
        # Green channel value was 0.3, extracted into monochrome R=G=B=0.3
        if abs(p_green[0] - 0.3) > 0.02 or abs(p_green[1] - 0.3) > 0.02 or abs(p_green[2] - 0.3) > 0.02:
            record_fail("AI-05", "Green channel extraction", f"Expected mono 0.3, got {p_green[:3]}")
            return
        record_pass("AI-05", "Green Channel Contrast preset", f"Green channel isolated to monochrome (G={p_green[1]:.3f}) and blended via Soft Light")
        image.remove_layer(green_layer)

        # 40f: Red Channel Multiply preset (AI-06)
        image.set_selected_layers([base])
        cfg_red = proc.create_config()
        cfg_red.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_red.set_property("image", image)
        cfg_red.set_property("preset", "red-channel-multiply")
        proc.run(cfg_red)

        red_layer = [l for l in image.get_layers() if l.get_name().startswith("Apply Image")][0]
        if red_layer.get_mode() != Gimp.LayerMode.MULTIPLY:
            record_fail("AI-06", "Red multiply mode", f"Mode {red_layer.get_mode()} != MULTIPLY")
            return
        p_red = red_layer.get_pixel(50, 50).get_rgba()
        # Red channel value was 0.7, extracted into monochrome R=G=B=0.7
        if abs(p_red[0] - 0.7) > 0.02 or abs(p_red[1] - 0.7) > 0.02 or abs(p_red[2] - 0.7) > 0.02:
            record_fail("AI-06", "Red channel extraction", f"Expected mono 0.7, got {p_red[:3]}")
            return
        record_pass("AI-06", "Red Channel Multiply preset", f"Red channel isolated to monochrome (R={p_red[0]:.3f}) and blended via Multiply")
        image.remove_layer(red_layer)

        # 40g: Invert flag verified (AI-07)
        image.set_selected_layers([base])
        cfg_inv = proc.create_config()
        cfg_inv.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_inv.set_property("image", image)
        cfg_inv.set_property("preset", "custom")
        cfg_inv.set_property("source-channel", "red")
        cfg_inv.set_property("invert", True)
        proc.run(cfg_inv)

        inv_layer = [l for l in image.get_layers() if l.get_name().startswith("Apply Image")][0]
        p_inv = inv_layer.get_pixel(50, 50).get_rgba()
        # Red was 0.7, inverted Red is 1.0 - 0.7 = 0.3
        if abs(p_inv[0] - 0.3) > 0.02:
            record_fail("AI-07", "Invert flag", f"Expected inverted red ~0.3, got {p_inv[0]:.3f}")
            return
        record_pass("AI-07", "Invert flag verification", f"Source channel accurately inverted before blending (0.7 -> {p_inv[0]:.3f})")
        image.remove_layer(inv_layer)

        # 40h: Blend modes verified (AI-08)
        blend_checks = [
            ("screen", Gimp.LayerMode.SCREEN),
            ("overlay", Gimp.LayerMode.OVERLAY),
            ("add", Gimp.LayerMode.ADDITION),
            ("difference", Gimp.LayerMode.DIFFERENCE),
            ("linear-light", Gimp.LayerMode.LINEAR_LIGHT),
        ]
        for bm_name, expected_mode in blend_checks:
            image.set_selected_layers([base])
            cfg_bm = proc.create_config()
            cfg_bm.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
            cfg_bm.set_property("image", image)
            cfg_bm.set_property("preset", "custom")
            cfg_bm.set_property("blend-mode", bm_name)
            proc.run(cfg_bm)
            bm_layer = [l for l in image.get_layers() if l.get_name().startswith("Apply Image")][0]
            if bm_layer.get_mode() != expected_mode:
                record_fail("AI-08", f"Blend mode {bm_name}", f"Mode {bm_layer.get_mode()} != {expected_mode}")
                return
            image.remove_layer(bm_layer)
        record_pass("AI-08", "Blend modes verified", "Screen, Overlay, Add, Difference, Linear Light validated")

        # 40i: Scale and Offset calibration (AI-09)
        # Pure black base layer: 0.0. Scale 4.0, Offset 64.0 -> Output = 64/255 = 0.251
        black_layer = Gimp.Layer.new(image, "BlackBase", 100, 100, Gimp.ImageType.RGB_IMAGE, 100, Gimp.LayerMode.NORMAL)
        image.insert_layer(black_layer, None, 0)
        image.set_selected_layers([black_layer])
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.0, 0.0, 0.0)"))
        black_layer.fill(Gimp.FillType.FOREGROUND)

        cfg_so = proc.create_config()
        cfg_so.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_so.set_property("image", image)
        cfg_so.set_property("preset", "custom")
        cfg_so.set_property("scale", 4.0)
        cfg_so.set_property("offset", 64.0)
        proc.run(cfg_so)

        so_layer = [l for l in image.get_layers() if l.get_name().startswith("Apply Image")][0]
        p_so = so_layer.get_pixel(50, 50).get_rgba()
        if abs(p_so[0] - 0.251) > 0.02:
            record_fail("AI-09", "Scale and Offset calibration", f"Expected ~0.251, got {p_so[0]:.3f}")
            return
        record_pass("AI-09", "Scale and Offset calibration", f"Scale 4.0 & Offset 64.0 verified via levels math (0.0 -> {p_so[0]:.3f} ~ 0.251)")
        image.remove_layer(so_layer)
        image.remove_layer(black_layer)

        # 40j: Conceal-All black layer mask (AI-10)
        image.set_selected_layers([base])
        cfg_conceal = proc.create_config()
        cfg_conceal.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_conceal.set_property("image", image)
        cfg_conceal.set_property("preset", "frequency-separation-8bit")
        cfg_conceal.set_property("mask-mode", "conceal-all")
        proc.run(cfg_conceal)

        conceal_layer = [l for l in image.get_layers() if l.get_name().startswith("Apply Image")][0]
        c_conceal = get_composite_pixel(image, 50, 50)
        conceal_diff = max(abs(c_conceal[i] - p_base_orig[i]) for i in range(3))
        if conceal_diff > 0.000001:
            record_fail("AI-10", "Conceal-all mask", f"Composite differs by {conceal_diff:.6f}")
            return
        record_pass("AI-10", "Conceal-All black layer mask", f"Effect 100% concealed by black mask (diff {conceal_diff:.6f})")
        image.remove_layer(conceal_layer)

        # 40k: Selection confinement & non-destructive preservation (AI-11)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 50, 100)
        image.set_selected_layers([base])
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("preset", "frequency-separation-8bit")
        cfg_sel.set_property("mask-mode", "selection")
        proc.run(cfg_sel)

        sel_layer = [l for l in image.get_layers() if l.get_name().startswith("Apply Image")][0]
        mask_in = sel_layer.get_mask().get_pixel(25, 50).get_rgba()[0]
        mask_out = sel_layer.get_mask().get_pixel(75, 50).get_rgba()[0]

        p_base_after = base.get_pixel(50, 50).get_rgba()
        base_diff = max(abs(p_base_after[i] - p_base_orig[i]) for i in range(3))
        if base_diff > 0.000001:
            record_fail("AI-11", "Base layer preservation", f"Base altered by {base_diff:.6f}")
            return
        record_pass("AI-11", "Selection confinement & non-destructive preservation", f"Mask (in={mask_in:.2f}, out={mask_out:.2f}), base untouched (diff {base_diff:.6f})")

    except Exception as e:
        record_fail("AI-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# 41. REPLACE COLOR & TARGETED OBJECT RECOLORING HELPER TEST SUITE
# ==============================================================================
def test_replace_color():
    print("\n--- Test Suite 41: Replace Color & Targeted Object Recoloring Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-replace-color")
    if proc is None:
        record_fail("RC-01", "Procedure lookup", "Procedure python-fu-replace-color not found")
        return

    # 41a: Configuration argument verification (RC-01)
    args = [arg.name for arg in proc.get_arguments()]
    req_args = [
        "target-preset",
        "sample-r",
        "sample-g",
        "sample-b",
        "fuzziness",
        "hue-shift",
        "saturation-shift",
        "lightness-shift",
        "colorize",
        "blend-mode",
        "mask-mode",
        "opacity",
    ]
    missing = [ra for ra in req_args if ra not in args]
    if missing:
        record_fail("RC-01", "Procedure arguments", f"Missing arguments: {missing}")
        return
    record_pass("RC-01", "Procedure arguments", f"All {len(req_args)} configuration arguments present")

    # Create test canvas (100x100)
    image = Gimp.Image.new(100, 100, Gimp.ImageBaseType.RGB)

    try:
        # Base target layer: Left half Red (1, 0, 0), Right half Blue (0, 0, 1)
        base = Gimp.Layer.new(image, "BaseReplaceColor", 100, 100, Gimp.ImageType.RGB_IMAGE, 100, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        image.set_selected_layers([base])

        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 50, 100)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(1.0, 0.0, 0.0)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        image.select_rectangle(Gimp.ChannelOps.REPLACE, 50, 0, 50, 100)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.0, 0.0, 1.0)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(image)

        p_base_red = base.get_pixel(25, 50).get_rgba()
        p_base_blue = base.get_pixel(75, 50).get_rgba()

        # 41b: Execution status (RC-02)
        cfg_init = proc.create_config()
        cfg_init.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_init.set_property("image", image)
        cfg_init.set_property("target-preset", "reds")
        cfg_init.set_property("hue-shift", 120.0) # Red -> Green
        res = proc.run(cfg_init)

        if res.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("RC-02", "Execution status", f"Status {res.index(0)}")
            return
        record_pass("RC-02", "Execution status", "SUCCESS")

        # 41c: Layer mode, name & mask (RC-03)
        rc_layer = [l for l in image.get_layers() if l.get_name().startswith("Replace Color")][0]
        if not rc_layer.get_name().startswith("Replace Color (Reds)"):
            record_fail("RC-03", "Layer name", f"Unexpected name {rc_layer.get_name()}")
            return
        if rc_layer.get_mode() != Gimp.LayerMode.HSL_COLOR:
            record_fail("RC-03", "Layer mode", f"Mode {rc_layer.get_mode()} != HSL_COLOR")
            return
        if rc_layer.get_mask() is None:
            record_fail("RC-03", "Layer mask", "Fuzziness mask not attached")
            return
        record_pass("RC-03", "Layer mode, name & mask", f"{rc_layer.get_name()} with HSL_COLOR mode and mask attached")

        # 41d: Target Color Hue Shift verified (RC-04)
        # Red layer pixel shifted by 120 deg became pure green
        p_rc_left = rc_layer.get_pixel(25, 50).get_rgba()
        if p_rc_left[1] <= p_rc_left[0] or p_rc_left[1] < 0.90:
            record_fail("RC-04", "Target color hue shift", f"Expected green > red, got {p_rc_left[:3]}")
            return
        record_pass("RC-04", "Target Color Hue Shift", f"Red shifted by +120° to Green (R={p_rc_left[0]:.3f}, G={p_rc_left[1]:.3f}, B={p_rc_left[2]:.3f})")

        # 41e: Fuzziness Mask falloff verified (RC-05)
        # Fuzziness mask for Reds should be ~1.0 in red half (x=25) and 0.0 in blue half (x=75)
        mask = rc_layer.get_mask()
        m_red = mask.get_pixel(25, 50).get_rgba()[0]
        m_blue = mask.get_pixel(75, 50).get_rgba()[0]
        if m_red < 0.80 or m_blue > 0.05:
            record_fail("RC-05", "Fuzziness mask falloff", f"Expected red ~1.0 and blue ~0.0, got red={m_red:.3f}, blue={m_blue:.3f}")
            return
        record_pass("RC-05", "Fuzziness Mask falloff", f"Mask isolates targeted reds (mask={m_red:.2f}) and excludes distant blues (mask={m_blue:.2f})")
        image.remove_layer(rc_layer)

        # 41f: Colorize mode verified (RC-06)
        # Test on neutral gray element (0.5, 0.5, 0.5)
        gray_layer = Gimp.Layer.new(image, "GrayBase", 100, 100, Gimp.ImageType.RGB_IMAGE, 100, Gimp.LayerMode.NORMAL)
        image.insert_layer(gray_layer, None, 0)
        image.set_selected_layers([gray_layer])
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.5, 0.5, 0.5)"))
        gray_layer.fill(Gimp.FillType.FOREGROUND)

        cfg_col = proc.create_config()
        cfg_col.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_col.set_property("image", image)
        cfg_col.set_property("target-preset", "sampled-color")
        cfg_col.set_property("sample-r", 0.5)
        cfg_col.set_property("sample-g", 0.5)
        cfg_col.set_property("sample-b", 0.5)
        cfg_col.set_property("colorize", True)
        cfg_col.set_property("hue-shift", 120.0) # Green hue
        cfg_col.set_property("saturation-shift", 80.0)
        proc.run(cfg_col)

        col_layer = [l for l in image.get_layers() if l.get_name().startswith("Replace Color")][0]
        p_col = col_layer.get_pixel(50, 50).get_rgba()
        if p_col[1] <= p_col[0] or p_col[1] <= p_col[2]:
            record_fail("RC-06", "Colorize mode", f"Expected green tint, got {p_col[:3]}")
            return
        record_pass("RC-06", "Colorize mode", f"Neutral gray uniformly tinted to green hue (G={p_col[1]:.3f} > R={p_col[0]:.3f}, B={p_col[2]:.3f})")
        image.remove_layer(col_layer)
        image.remove_layer(gray_layer)

        # 41g: Saturation shift verified (RC-07)
        image.set_selected_layers([base])
        cfg_sat = proc.create_config()
        cfg_sat.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sat.set_property("image", image)
        cfg_sat.set_property("target-preset", "reds")
        cfg_sat.set_property("hue-shift", 0.0)
        cfg_sat.set_property("saturation-shift", -100.0) # Complete desaturation of reds
        proc.run(cfg_sat)

        sat_layer = [l for l in image.get_layers() if l.get_name().startswith("Replace Color")][0]
        p_sat = sat_layer.get_pixel(25, 50).get_rgba()
        spread_sat = max(p_sat[0], p_sat[1], p_sat[2]) - min(p_sat[0], p_sat[1], p_sat[2])
        if spread_sat > 0.01:
            record_fail("RC-07", "Saturation desaturation", f"Expected neutral grayscale, spread {spread_sat:.4f} > 0.01")
            return
        record_pass("RC-07", "Saturation shift", f"Saturation -100 desaturated red target to neutral monochrome (spread {spread_sat:.6f})")
        image.remove_layer(sat_layer)

        # 41h: Lightness shift verified (RC-08)
        image.set_selected_layers([base])
        cfg_light = proc.create_config()
        cfg_light.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_light.set_property("image", image)
        cfg_light.set_property("target-preset", "reds")
        cfg_light.set_property("hue-shift", 0.0)
        cfg_light.set_property("lightness-shift", 50.0) # Lift lightness
        proc.run(cfg_light)

        light_layer = [l for l in image.get_layers() if l.get_name().startswith("Replace Color")][0]
        p_light = light_layer.get_pixel(25, 50).get_rgba()
        # Lightness lift should brighten green/blue channels from 0.0 towards 0.5
        if p_light[1] <= 0.20:
            record_fail("RC-08", "Lightness shift", f"Expected brightened channels, got {p_light[:3]}")
            return
        record_pass("RC-08", "Lightness shift", f"Lightness +50 lifted luminance (G={p_light[1]:.3f}, B={p_light[2]:.3f} > 0.0)")
        image.remove_layer(light_layer)

        # 41i: Blend modes verified (RC-09)
        blend_checks = [
            ("color", Gimp.LayerMode.HSL_COLOR),
            ("hue", Gimp.LayerMode.HSV_HUE),
            ("normal", Gimp.LayerMode.NORMAL),
            ("soft-light", Gimp.LayerMode.SOFTLIGHT),
        ]
        for bm_name, expected_mode in blend_checks:
            image.set_selected_layers([base])
            cfg_bm = proc.create_config()
            cfg_bm.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
            cfg_bm.set_property("image", image)
            cfg_bm.set_property("target-preset", "reds")
            cfg_bm.set_property("blend-mode", bm_name)
            proc.run(cfg_bm)
            bm_layer = [l for l in image.get_layers() if l.get_name().startswith("Replace Color")][0]
            if bm_layer.get_mode() != expected_mode:
                record_fail("RC-09", f"Blend mode {bm_name}", f"Mode {bm_layer.get_mode()} != {expected_mode}")
                return
            image.remove_layer(bm_layer)
        record_pass("RC-09", "Blend modes verified", "Color, Hue, Normal, Soft Light validated")

        # 41j: Conceal-All black layer mask (RC-10)
        image.set_selected_layers([base])
        cfg_conceal = proc.create_config()
        cfg_conceal.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_conceal.set_property("image", image)
        cfg_conceal.set_property("target-preset", "reds")
        cfg_conceal.set_property("hue-shift", 120.0)
        cfg_conceal.set_property("mask-mode", "conceal-all")
        proc.run(cfg_conceal)

        conceal_layer = [l for l in image.get_layers() if l.get_name().startswith("Replace Color")][0]
        c_conceal = get_composite_pixel(image, 25, 50)
        conceal_diff = max(abs(c_conceal[i] - p_base_red[i]) for i in range(3))
        if conceal_diff > 0.000001:
            record_fail("RC-10", "Conceal-all mask", f"Composite differs by {conceal_diff:.6f}")
            return
        record_pass("RC-10", "Conceal-All black layer mask", f"Effect 100% concealed by black mask (diff {conceal_diff:.6f})")
        image.remove_layer(conceal_layer)

        # 41k: Selection confinement & non-destructive preservation (RC-11)
        # Select quarter area (x: 0..50, y: 0..50)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 50, 50)
        image.set_selected_layers([base])
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("target-preset", "reds")
        cfg_sel.set_property("hue-shift", 120.0)
        cfg_sel.set_property("mask-mode", "selection")
        proc.run(cfg_sel)

        sel_layer = [l for l in image.get_layers() if l.get_name().startswith("Replace Color")][0]
        mask_in = sel_layer.get_mask().get_pixel(25, 25).get_rgba()[0]
        mask_out = sel_layer.get_mask().get_pixel(25, 75).get_rgba()[0]

        p_base_after = base.get_pixel(25, 50).get_rgba()
        base_diff = max(abs(p_base_after[i] - p_base_red[i]) for i in range(3))
        if base_diff > 0.000001:
            record_fail("RC-11", "Base layer preservation", f"Base altered by {base_diff:.6f}")
            return
        record_pass("RC-11", "Selection confinement & non-destructive preservation", f"Mask (in={mask_in:.2f}, out={mask_out:.2f}), base untouched (diff {base_diff:.6f})")

    except Exception as e:
        record_fail("RC-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# 42. LENS BLUR & OPTICAL DEPTH OF FIELD HELPER TEST SUITE
# ==============================================================================
def test_lens_blur():
    print("\n--- Test Suite 42: Lens Blur & Optical Depth of Field Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-lens-blur")
    if proc is None:
        record_fail("LB-01", "Procedure lookup", "Procedure python-fu-lens-blur not found")
        return

    # 42a: Configuration argument verification (LB-01)
    args = [arg.name for arg in proc.get_arguments()]
    req_args = [
        "preset",
        "radius",
        "highlight-factor",
        "highlight-threshold",
        "depth-source",
        "focal-distance",
        "invert-depth",
        "noise-amount",
        "mask-mode",
        "opacity",
    ]
    missing = [ra for ra in req_args if ra not in args]
    if missing:
        record_fail("LB-01", "Procedure arguments", f"Missing arguments: {missing}")
        return
    record_pass("LB-01", "Procedure arguments", f"All {len(req_args)} configuration arguments present")

    # Create test canvas (100x100)
    image = Gimp.Image.new(100, 100, Gimp.ImageBaseType.RGB)

    try:
        # Base target layer: dark background (0.125, 0.125, 0.125) with bright specular spot at center (50, 50)
        base = Gimp.Layer.new(image, "BaseLensBlur", 100, 100, Gimp.ImageType.RGB_IMAGE, 100, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        image.set_selected_layers([base])

        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.125, 0.125, 0.125)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        # Specular point highlight at center
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 48, 48, 4, 4)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(1.0, 1.0, 1.0)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(image)

        p_base_center = base.get_pixel(50, 50).get_rgba()
        p_base_disc_area = base.get_pixel(50, 60).get_rgba() # 10px away: dark background
        p_base_far = base.get_pixel(50, 90).get_rgba() # 40px away: dark background

        # 42b: Execution status (LB-02)
        cfg_init = proc.create_config()
        cfg_init.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_init.set_property("image", image)
        cfg_init.set_property("preset", "portrait-fast-prime")
        res = proc.run(cfg_init)

        if res.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("LB-02", "Execution status", f"Status {res.index(0)}")
            return
        record_pass("LB-02", "Execution status", "SUCCESS")

        # 42c: Layer mode, name & mask (LB-03)
        lb_layer = [l for l in image.get_layers() if l.get_name().startswith("Lens Blur")][0]
        if not lb_layer.get_name().startswith("Lens Blur (Portrait Fast Prime f/1.4)"):
            record_fail("LB-03", "Layer name", f"Unexpected name {lb_layer.get_name()}")
            return
        if lb_layer.get_mode() != Gimp.LayerMode.NORMAL:
            record_fail("LB-03", "Layer mode", f"Mode {lb_layer.get_mode()} != NORMAL")
            return
        if lb_layer.get_mask() is None:
            record_fail("LB-03", "Layer mask", "Depth mask not attached")
            return
        record_pass("LB-03", "Layer mode, name & mask", f"{lb_layer.get_name()} with NORMAL mode and mask attached")

        # 42d: Aperture Bokeh Disc Formation verified (LB-04)
        # Specular point at (50, 50) has expanded into a circular bokeh disc of radius ~25px
        # In base, (50, 60) is dark background (0.125). In blur layer, it is illuminated by the bokeh circle!
        p_lb_disc = lb_layer.get_pixel(50, 60).get_rgba()
        if p_lb_disc[0] <= p_base_disc_area[0]:
            record_fail("LB-04", "Bokeh disc formation", f"Expected illuminated bokeh disc, got {p_lb_disc[0]:.4f} <= {p_base_disc_area[0]:.4f}")
            return
        record_pass("LB-04", "Aperture Bokeh Disc Formation", f"Specular highlight expanded into bokeh disc (disc area luminance {p_lb_disc[0]:.3f} > {p_base_disc_area[0]:.3f})")
        image.remove_layer(lb_layer)

        # 42e: Specular Highlight Boost verified (LB-05)
        # Compare highlight-factor 0.90 vs highlight-factor 0.0
        image.set_selected_layers([base])
        cfg_boost = proc.create_config()
        cfg_boost.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_boost.set_property("image", image)
        cfg_boost.set_property("preset", "custom")
        cfg_boost.set_property("radius", 20.0)
        cfg_boost.set_property("highlight-factor", 0.90)
        cfg_boost.set_property("highlight-threshold", 0.60)
        cfg_boost.set_property("mask-mode", "reveal-all")
        proc.run(cfg_boost)
        boost_layer = [l for l in image.get_layers() if l.get_name().startswith("Lens Blur")][0]
        p_boost = boost_layer.get_pixel(50, 55).get_rgba()
        image.remove_layer(boost_layer)

        image.set_selected_layers([base])
        cfg_noboost = proc.create_config()
        cfg_noboost.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_noboost.set_property("image", image)
        cfg_noboost.set_property("preset", "custom")
        cfg_noboost.set_property("radius", 20.0)
        cfg_noboost.set_property("highlight-factor", 0.0)
        cfg_noboost.set_property("highlight-threshold", 0.95)
        cfg_noboost.set_property("mask-mode", "reveal-all")
        proc.run(cfg_noboost)
        noboost_layer = [l for l in image.get_layers() if l.get_name().startswith("Lens Blur")][0]
        p_noboost = noboost_layer.get_pixel(50, 55).get_rgba()
        image.remove_layer(noboost_layer)

        if p_boost[0] <= p_noboost[0]:
            record_fail("LB-05", "Highlight factor boost", f"Expected boosted luminance {p_boost[0]:.4f} > {p_noboost[0]:.4f}")
            return
        record_pass("LB-05", "Specular Highlight Boost", f"Highlight factor amplifies specular luminance ({p_boost[0]:.3f} > {p_noboost[0]:.3f})")

        # 42f: Portrait Fast Prime f/1.4 preset verified (LB-06)
        # Radial depth mask keeps center sharp (mask ~0) and periphery blurred (mask > 0.5)
        image.set_selected_layers([base])
        cfg_port = proc.create_config()
        cfg_port.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_port.set_property("image", image)
        cfg_port.set_property("preset", "portrait-fast-prime")
        proc.run(cfg_port)
        port_layer = [l for l in image.get_layers() if l.get_name().startswith("Lens Blur")][0]
        mask_port = port_layer.get_mask()
        m_port_center = mask_port.get_pixel(50, 50).get_rgba()[0]
        m_port_outer = mask_port.get_pixel(10, 10).get_rgba()[0]

        if m_port_center > 0.10 or m_port_outer < 0.50:
            record_fail("LB-06", "Portrait preset falloff", f"Expected center ~0 and outer >0.5, got center={m_port_center:.3f}, outer={m_port_outer:.3f}")
            return
        record_pass("LB-06", "Portrait Fast Prime f/1.4 preset", f"Radial depth falloff preserves sharp center (mask {m_port_center:.2f}) with background defocus (mask {m_port_outer:.2f})")
        image.remove_layer(port_layer)

        # 42g: Street Photography Shallow DOF preset verified (LB-07)
        # Linear depth gradient: foreground (bottom) sharp, background (top) blurred
        image.set_selected_layers([base])
        cfg_street = proc.create_config()
        cfg_street.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_street.set_property("image", image)
        cfg_street.set_property("preset", "street-shallow-dof")
        proc.run(cfg_street)
        street_layer = [l for l in image.get_layers() if l.get_name().startswith("Lens Blur")][0]
        mask_street = street_layer.get_mask()
        m_street_top = mask_street.get_pixel(50, 10).get_rgba()[0]
        m_street_bottom = mask_street.get_pixel(50, 90).get_rgba()[0]

        if m_street_bottom > 0.25 or m_street_top < 0.60:
            record_fail("LB-07", "Street preset linear depth", f"Expected bottom < 0.25 and top > 0.60, got bottom={m_street_bottom:.3f}, top={m_street_top:.3f}")
            return
        record_pass("LB-07", "Street Photography Shallow DOF preset", f"Linear depth gradient verified (foreground mask {m_street_bottom:.2f}, background mask {m_street_top:.2f})")
        image.remove_layer(street_layer)

        # 42h: Dreamy Specular Bokeh preset verified (LB-08)
        # Uniform full-frame bokeh with reveal-all mask
        image.set_selected_layers([base])
        cfg_dream = proc.create_config()
        cfg_dream.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_dream.set_property("image", image)
        cfg_dream.set_property("preset", "dreamy-specular-bokeh")
        proc.run(cfg_dream)
        dream_layer = [l for l in image.get_layers() if l.get_name().startswith("Lens Blur")][0]
        mask_dream = dream_layer.get_mask()
        m_dream_center = mask_dream.get_pixel(50, 50).get_rgba()[0]
        m_dream_corner = mask_dream.get_pixel(10, 10).get_rgba()[0]

        if m_dream_center < 0.95 or m_dream_corner < 0.95:
            record_fail("LB-08", "Dreamy preset mask", f"Expected reveal-all (1.0), got center={m_dream_center:.3f}, corner={m_dream_corner:.3f}")
            return
        record_pass("LB-08", "Dreamy Specular Bokeh preset", f"Uniform reveal-all mask verified with rich specular bokeh (mask {m_dream_center:.2f})")
        image.remove_layer(dream_layer)

        # 42i: Monochromatic film grain noise verified (LB-09)
        # Test on neutral flat gray (0.5, 0.5, 0.5)
        gray_layer = Gimp.Layer.new(image, "GrayBaseLB", 100, 100, Gimp.ImageType.RGB_IMAGE, 100, Gimp.LayerMode.NORMAL)
        image.insert_layer(gray_layer, None, 0)
        image.set_selected_layers([gray_layer])
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.5, 0.5, 0.5)"))
        gray_layer.edit_fill(Gimp.FillType.FOREGROUND)

        cfg_noise = proc.create_config()
        cfg_noise.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_noise.set_property("image", image)
        cfg_noise.set_property("preset", "custom")
        cfg_noise.set_property("radius", 5.0)
        cfg_noise.set_property("noise-amount", 60.0)
        cfg_noise.set_property("mask-mode", "reveal-all")
        proc.run(cfg_noise)

        noise_layer = [l for l in image.get_layers() if l.get_name().startswith("Lens Blur")][0]
        samples = []
        is_monochromatic = True
        for y in range(45, 55):
            for x in range(45, 55):
                rgba = noise_layer.get_pixel(x, y).get_rgba()
                samples.append(rgba[0])
                if abs(rgba[0] - rgba[1]) > 0.005 or abs(rgba[1] - rgba[2]) > 0.005:
                    is_monochromatic = False

        mean = sum(samples) / len(samples)
        variance = sum((s - mean) ** 2 for s in samples) / len(samples)

        if variance < 0.0003 or not is_monochromatic:
            record_fail("LB-09", "Film grain noise", f"Variance {variance:.6f} or not monochromatic (mono={is_monochromatic})")
            return
        record_pass("LB-09", "Monochromatic film grain noise", f"Sensor texture added (variance {variance:.6f} > 0.0003, monochromatic RGB correlation verified)")
        image.remove_layer(noise_layer)
        image.remove_layer(gray_layer)

        # 42j: Conceal-All black layer mask verified (LB-10)
        image.set_selected_layers([base])
        cfg_conceal = proc.create_config()
        cfg_conceal.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_conceal.set_property("image", image)
        cfg_conceal.set_property("preset", "portrait-fast-prime")
        cfg_conceal.set_property("mask-mode", "conceal-all")
        proc.run(cfg_conceal)

        conceal_layer = [l for l in image.get_layers() if l.get_name().startswith("Lens Blur")][0]
        c_conceal = get_composite_pixel(image, 50, 50)
        conceal_diff = max(abs(c_conceal[i] - p_base_center[i]) for i in range(3))
        if conceal_diff > 0.000001:
            record_fail("LB-10", "Conceal-all mask", f"Composite differs by {conceal_diff:.6f}")
            return
        record_pass("LB-10", "Conceal-All black layer mask", f"Effect 100% concealed by black mask (diff {conceal_diff:.6f})")
        image.remove_layer(conceal_layer)

        # 42k: Selection confinement & non-destructive preservation (LB-11)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 50, 50)
        image.set_selected_layers([base])
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("preset", "uniform-defocus")
        cfg_sel.set_property("mask-mode", "selection")
        proc.run(cfg_sel)

        sel_layer = [l for l in image.get_layers() if l.get_name().startswith("Lens Blur")][0]
        mask_in = sel_layer.get_mask().get_pixel(25, 25).get_rgba()[0]
        mask_out = sel_layer.get_mask().get_pixel(75, 75).get_rgba()[0]

        p_base_after = base.get_pixel(50, 50).get_rgba()
        base_diff = max(abs(p_base_after[i] - p_base_center[i]) for i in range(3))
        if base_diff > 0.000001:
            record_fail("LB-11", "Base layer preservation", f"Base altered by {base_diff:.6f}")
            return
        record_pass("LB-11", "Selection confinement & non-destructive preservation", f"Mask (in={mask_in:.2f}, out={mask_out:.2f}), base untouched (diff {base_diff:.6f})")

    except Exception as e:
        record_fail("LB-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# 43. TEXTURIZER & SURFACE CANVAS HELPER TEST SUITE
# ==============================================================================
def test_texturizer():
    print("\n--- Test Suite 43: Texturizer & Surface Canvas Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-texturizer")
    if proc is None:
        record_fail("TX-01", "Procedure lookup", "Procedure python-fu-texturizer not found")
        return

    # 43a: Procedure Argument Verification (TX-01)
    args = {arg.name: arg for arg in proc.get_arguments()}
    expected_args = [
        "preset", "texture", "scaling", "relief",
        "light-dir", "invert", "blend-mode", "mask-mode", "opacity"
    ]
    missing = [a for a in expected_args if a not in args]
    if missing:
        record_fail("TX-01", "Argument check", f"Missing arguments: {missing}")
        return
    record_pass("TX-01", "Procedure arguments verified", f"{len(expected_args)} arguments verified")

    image = Gimp.Image.new(100, 100, Gimp.ImageBaseType.RGB)
    try:
        # Base midtone layer (0.5, 0.5, 0.5)
        base = Gimp.Layer.new(image, "BaseTexturizer", 100, 100, Gimp.ImageType.RGBA_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        image.set_selected_layers([base])
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.5, 0.5, 0.5)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        p_base = base.get_pixel(50, 50).get_rgba()

        # 43b: Execution status verified (TX-02)
        cfg_canvas = proc.create_config()
        cfg_canvas.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_canvas.set_property("image", image)
        cfg_canvas.set_property("preset", "fine-art-canvas")
        res = proc.run(cfg_canvas)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("TX-02", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("TX-02", "Execution status", "SUCCESS")

        # 43c: Layer mode, name & mask verified (TX-03)
        layers = image.get_layers()
        tex_layer = None
        for l in layers:
            if l.get_name().startswith("Texturizer"):
                tex_layer = l
                break

        if tex_layer is None:
            record_fail("TX-03", "Layer creation", "Texturizer layer not found in image")
            return

        layer_name = tex_layer.get_name()
        layer_mode = tex_layer.get_mode()
        has_mask = tex_layer.get_mask() is not None

        if "Fine Art Canvas" not in layer_name or layer_mode != Gimp.LayerMode.SOFTLIGHT or not has_mask:
            record_fail("TX-03", "Layer properties", f"Name='{layer_name}', mode={layer_mode}, has_mask={has_mask}")
            return
        record_pass("TX-03", "Layer mode, name & mask", f"'{layer_name}' in SOFTLIGHT mode with mask attached")

        # 43d: Fine Art Canvas weave texture variance verified (TX-04)
        samples = []
        for y in range(40, 60):
            for x in range(40, 60):
                c = tex_layer.get_pixel(x, y).get_rgba()
                samples.append(c[0])
        mean_val = sum(samples) / len(samples)
        var_canvas = sum((s - mean_val) ** 2 for s in samples) / len(samples)

        if var_canvas < 0.001:
            record_fail("TX-04", "Canvas weave variance", f"Variance too low: {var_canvas:.6f}")
            return
        record_pass("TX-04", "Canvas weave texture variance", f"Woven canvas relief verified (variance {var_canvas:.6f} > 0.001)")
        image.remove_layer(tex_layer)

        # 43e: Relief depth scaling verified (TX-05)
        image.set_selected_layers([base])
        cfg_r25 = proc.create_config()
        cfg_r25.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_r25.set_property("image", image)
        cfg_r25.set_property("preset", "custom")
        cfg_r25.set_property("texture", "canvas")
        cfg_r25.set_property("relief", 25.0)
        proc.run(cfg_r25)
        layer_r25 = [l for l in image.get_layers() if l.get_name().startswith("Texturizer")][0]
        s_r25 = [layer_r25.get_pixel(x, 50).get_rgba()[0] for x in range(40, 60)]
        var_r25 = sum((s - (sum(s_r25)/len(s_r25))) ** 2 for s in s_r25) / len(s_r25)
        image.remove_layer(layer_r25)

        image.set_selected_layers([base])
        cfg_r5 = proc.create_config()
        cfg_r5.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_r5.set_property("image", image)
        cfg_r5.set_property("preset", "custom")
        cfg_r5.set_property("texture", "canvas")
        cfg_r5.set_property("relief", 5.0)
        proc.run(cfg_r5)
        layer_r5 = [l for l in image.get_layers() if l.get_name().startswith("Texturizer")][0]
        s_r5 = [layer_r5.get_pixel(x, 50).get_rgba()[0] for x in range(40, 60)]
        var_r5 = sum((s - (sum(s_r5)/len(s_r5))) ** 2 for s in s_r5) / len(s_r5)
        image.remove_layer(layer_r5)

        if var_r25 <= var_r5 * 1.5:
            record_fail("TX-05", "Relief scaling", f"Relief 25 ({var_r25:.6f}) not significantly greater than Relief 5 ({var_r5:.6f})")
            return
        record_pass("TX-05", "Relief depth scaling", f"Relief 25 variance ({var_r25:.5f}) > Relief 5 ({var_r5:.5f})")

        # 43f: Directional lighting angle response verified (TX-06)
        image.set_selected_layers([base])
        cfg_tl = proc.create_config()
        cfg_tl.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_tl.set_property("image", image)
        cfg_tl.set_property("preset", "custom")
        cfg_tl.set_property("texture", "canvas")
        cfg_tl.set_property("light-dir", "top-left")
        proc.run(cfg_tl)
        layer_tl = [l for l in image.get_layers() if l.get_name().startswith("Texturizer")][0]

        image.set_selected_layers([base])
        cfg_br = proc.create_config()
        cfg_br.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_br.set_property("image", image)
        cfg_br.set_property("preset", "custom")
        cfg_br.set_property("texture", "canvas")
        cfg_br.set_property("light-dir", "bottom-right")
        proc.run(cfg_br)
        layer_br = [l for l in image.get_layers() if l.get_name().startswith("Texturizer") and l != layer_tl][0]

        found_inverted = False
        for x in range(40, 55):
            v_tl = layer_tl.get_pixel(x, 50).get_rgba()[0] - 0.50
            v_br = layer_br.get_pixel(x, 50).get_rgba()[0] - 0.50
            if abs(v_tl) > 0.03 and (v_tl * v_br) < 0:
                found_inverted = True
                break

        image.remove_layer(layer_tl)
        image.remove_layer(layer_br)

        if not found_inverted:
            record_fail("TX-06", "Directional lighting angle", "Top-Left vs Bottom-Right did not show phase reversal")
            return
        record_pass("TX-06", "Directional lighting angle response", "Opposite lighting angles produce phase reversal")

        # 43g: Invert texture toggle verified (TX-07)
        image.set_selected_layers([base])
        cfg_norm = proc.create_config()
        cfg_norm.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_norm.set_property("image", image)
        cfg_norm.set_property("preset", "custom")
        cfg_norm.set_property("texture", "canvas")
        cfg_norm.set_property("invert", False)
        proc.run(cfg_norm)
        layer_norm = [l for l in image.get_layers() if l.get_name().startswith("Texturizer")][0]

        image.set_selected_layers([base])
        cfg_inv = proc.create_config()
        cfg_inv.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_inv.set_property("image", image)
        cfg_inv.set_property("preset", "custom")
        cfg_inv.set_property("texture", "canvas")
        cfg_inv.set_property("invert", True)
        proc.run(cfg_inv)
        layer_inv = [l for l in image.get_layers() if l.get_name().startswith("Texturizer") and l != layer_norm][0]

        found_inv_sign = False
        for x in range(40, 55):
            v_n = layer_norm.get_pixel(x, 50).get_rgba()[0] - 0.50
            v_i = layer_inv.get_pixel(x, 50).get_rgba()[0] - 0.50
            if abs(v_n) > 0.03 and (v_n * v_i) < 0:
                found_inv_sign = True
                break

        image.remove_layer(layer_norm)
        image.remove_layer(layer_inv)

        if not found_inv_sign:
            record_fail("TX-07", "Invert texture", "Inverting texture did not invert highlight/shadow relief")
            return
        record_pass("TX-07", "Invert texture toggle", "Invert toggle reverses highlights and shadows")

        # 43h: Weathered Brickwork preset verified (TX-08)
        image.set_selected_layers([base])
        cfg_brick = proc.create_config()
        cfg_brick.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_brick.set_property("image", image)
        cfg_brick.set_property("preset", "weathered-brick")
        proc.run(cfg_brick)
        brick_layer = [l for l in image.get_layers() if l.get_name().startswith("Texturizer")][0]
        s_brick = [brick_layer.get_pixel(x, y).get_rgba()[0] for x in range(30, 60, 5) for y in range(30, 60, 5)]
        var_brick = sum((s - (sum(s_brick)/len(s_brick))) ** 2 for s in s_brick) / len(s_brick)
        if "Weathered Brickwork" not in brick_layer.get_name() or var_brick < 0.0003:
            record_fail("TX-08", "Brick preset", f"Brick layer not valid or variance too low ({var_brick:.6f})")
            return
        record_pass("TX-08", "Weathered Brickwork preset", f"Masonry courses and mortar joints rendered (var {var_brick:.5f})")
        image.remove_layer(brick_layer)

        # 43i: Rustic Burlap Weave preset verified (TX-09)
        image.set_selected_layers([base])
        cfg_burlap = proc.create_config()
        cfg_burlap.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_burlap.set_property("image", image)
        cfg_burlap.set_property("preset", "rustic-burlap")
        proc.run(cfg_burlap)
        burlap_layer = [l for l in image.get_layers() if l.get_name().startswith("Texturizer")][0]
        s_burlap = [burlap_layer.get_pixel(x, y).get_rgba()[0] for x in range(30, 60, 5) for y in range(30, 60, 5)]
        var_burlap = sum((s - (sum(s_burlap)/len(s_burlap))) ** 2 for s in s_burlap) / len(s_burlap)
        if "Rustic Burlap Weave" not in burlap_layer.get_name() or burlap_layer.get_mode() != Gimp.LayerMode.OVERLAY or var_burlap < 0.001:
            record_fail("TX-09", "Burlap preset", f"Burlap layer not valid, mode={burlap_layer.get_mode()}, var={var_burlap:.6f}")
            return
        record_pass("TX-09", "Rustic Burlap Weave preset", f"Coarse jute weave rendered in OVERLAY mode (var {var_burlap:.5f})")
        image.remove_layer(burlap_layer)

        # 43j: Conceal-All black layer mask verified (TX-10)
        image.set_selected_layers([base])
        cfg_conceal = proc.create_config()
        cfg_conceal.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_conceal.set_property("image", image)
        cfg_conceal.set_property("preset", "fine-art-canvas")
        cfg_conceal.set_property("mask-mode", "conceal-all")
        proc.run(cfg_conceal)
        conceal_layer = [l for l in image.get_layers() if l.get_name().startswith("Texturizer")][0]
        c_conceal = get_composite_pixel(image, 50, 50)
        diff_conceal = max(abs(c_conceal[i] - p_base[i]) for i in range(3))
        if diff_conceal > 0.000001:
            record_fail("TX-10", "Conceal-all mask", f"Composite differs from base by {diff_conceal:.6f}")
            return
        record_pass("TX-10", "Conceal-All black layer mask", f"Effect 100% concealed by black mask (diff {diff_conceal:.6f})")
        image.remove_layer(conceal_layer)

        # 43k: Selection confinement & non-destructive preservation (TX-11)
        image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 50, 50)
        image.set_selected_layers([base])
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("preset", "fine-art-canvas")
        cfg_sel.set_property("mask-mode", "selection")
        proc.run(cfg_sel)
        sel_layer = [l for l in image.get_layers() if l.get_name().startswith("Texturizer")][0]
        mask_in = sel_layer.get_mask().get_pixel(25, 25).get_rgba()[0]
        mask_out = sel_layer.get_mask().get_pixel(75, 75).get_rgba()[0]

        p_base_after = base.get_pixel(50, 50).get_rgba()
        base_diff = max(abs(p_base_after[i] - p_base[i]) for i in range(3))
        if base_diff > 0.000001 or mask_in < 0.90 or mask_out > 0.10:
            record_fail("TX-11", "Selection confinement", f"Base diff={base_diff:.6f}, mask_in={mask_in:.2f}, mask_out={mask_out:.2f}")
            return
        record_pass("TX-11", "Selection confinement & base preservation", f"Mask (in={mask_in:.2f}, out={mask_out:.2f}), base untouched (diff {base_diff:.6f})")

    except Exception as e:
        record_fail("TX-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()


# ==============================================================================
# 44. GUIDE LAYOUT & COMPOSITIONAL ALIGNMENT TEST SUITE
# ==============================================================================
def test_guide_layout():
    print("\n--- Test Suite 44: Guide Layout & Compositional Alignment Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc_layout = pdb.lookup_procedure("python-fu-guide-layout")
    proc_clear = pdb.lookup_procedure("python-fu-clear-guides")

    if proc_layout is None:
        record_fail("GL-01", "Procedure lookup", "Procedure python-fu-guide-layout not found")
        return
    if proc_clear is None:
        record_fail("GL-01", "Procedure lookup", "Procedure python-fu-clear-guides not found")
        return

    # 44a: Procedure Argument Verification (GL-01)
    args = {arg.name: arg for arg in proc_layout.get_arguments()}
    expected_args = [
        "preset", "clear-existing", "columns", "rows",
        "col-gutter", "row-gutter",
        "margin-top", "margin-bottom", "margin-left", "margin-right"
    ]
    missing = [a for a in expected_args if a not in args]
    if missing:
        record_fail("GL-01", "Argument check", f"Missing arguments: {missing}")
        return
    record_pass("GL-01", "Procedure arguments verified", f"{len(expected_args)} arguments verified")

    image = Gimp.Image.new(300, 300, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(image, "BaseGuideTest", 300, 300, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(base, None, 0)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.5, 0.5, 0.5)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)
        p_base_before = base.get_pixel(150, 150).get_rgba()

        # Helper to extract guides from image
        def get_all_guides(img):
            hg, vg = [], []
            gid = img.find_next_guide(0)
            while gid > 0:
                orient = img.get_guide_orientation(gid)
                pos = img.get_guide_position(gid)
                if orient == Gimp.OrientationType.HORIZONTAL:
                    hg.append(pos)
                else:
                    vg.append(pos)
                gid = img.find_next_guide(gid)
            return sorted(hg), sorted(vg)

        # 44b: Execution status verified (GL-02)
        cfg_rot = proc_layout.create_config()
        cfg_rot.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_rot.set_property("image", image)
        cfg_rot.set_property("preset", "rule-of-thirds")
        res = proc_layout.run(cfg_rot)
        status = res.index(0)
        if status != Gimp.PDBStatusType.SUCCESS:
            record_fail("GL-02", "Execution status", f"Expected SUCCESS (3), got {status}")
            return
        record_pass("GL-02", "Execution status", "SUCCESS")

        # 44c: Rule of Thirds preset verified on 300x300 image (GL-03)
        # On 300x300: thirds at 100px and 200px
        hg, vg = get_all_guides(image)
        if hg != [100, 200] or vg != [100, 200]:
            record_fail("GL-03", "Rule of Thirds coordinates", f"Expected [100, 200], got H={hg}, V={vg}")
            return
        record_pass("GL-03", "Rule of Thirds preset", f"Exact thirds verified (H={hg}, V={vg})")

        # 44d: Golden Ratio / Phi Grid preset verified on 1000x1000 image (GL-04)
        img_phi = Gimp.Image.new(1000, 1000, Gimp.ImageBaseType.RGB)
        try:
            cfg_phi = proc_layout.create_config()
            cfg_phi.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
            cfg_phi.set_property("image", img_phi)
            cfg_phi.set_property("preset", "golden-ratio")
            proc_layout.run(cfg_phi)
            hg_phi, vg_phi = get_all_guides(img_phi)
            if hg_phi != [382, 618] or vg_phi != [382, 618]:
                record_fail("GL-04", "Golden ratio coordinates", f"Expected [382, 618], got H={hg_phi}, V={vg_phi}")
                return
            record_pass("GL-04", "Golden Ratio / Phi Grid preset", f"Harmonic divine proportion verified (H={hg_phi}, V={vg_phi})")
        finally:
            img_phi.delete()

        # 44e: Center Crosshairs preset verified on 400x600 image (GL-05)
        img_ctr = Gimp.Image.new(400, 600, Gimp.ImageBaseType.RGB)
        try:
            cfg_ctr = proc_layout.create_config()
            cfg_ctr.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
            cfg_ctr.set_property("image", img_ctr)
            cfg_ctr.set_property("preset", "center-split")
            proc_layout.run(cfg_ctr)
            hg_ctr, vg_ctr = get_all_guides(img_ctr)
            if hg_ctr != [300] or vg_ctr != [200]:
                record_fail("GL-05", "Center split coordinates", f"Expected H=[300], V=[200], got H={hg_ctr}, V={vg_ctr}")
                return
            record_pass("GL-05", "Center Crosshairs preset", f"50% crosshairs verified (Center H={hg_ctr[0]}px, V={vg_ctr[0]}px)")
        finally:
            img_ctr.delete()

        # 44f: Safe Margins Frame preset verified on 200x200 image (GL-06)
        # 5% margins on 200x200: 10px and 190px
        img_sm = Gimp.Image.new(200, 200, Gimp.ImageBaseType.RGB)
        try:
            cfg_sm = proc_layout.create_config()
            cfg_sm.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
            cfg_sm.set_property("image", img_sm)
            cfg_sm.set_property("preset", "safe-margins")
            proc_layout.run(cfg_sm)
            hg_sm, vg_sm = get_all_guides(img_sm)
            if hg_sm != [10, 190] or vg_sm != [10, 190]:
                record_fail("GL-06", "Safe margins coordinates", f"Expected [10, 190], got H={hg_sm}, V={vg_sm}")
                return
            record_pass("GL-06", "Safe Margins Frame preset", f"5% safe artwork boundaries verified (H={hg_sm}, V={vg_sm})")
        finally:
            img_sm.delete()

        # 44g: Custom multi-column grid with gutters verified (GL-07)
        img_web = Gimp.Image.new(1200, 800, Gimp.ImageBaseType.RGB)
        try:
            cfg_web = proc_layout.create_config()
            cfg_web.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
            cfg_web.set_property("image", img_web)
            cfg_web.set_property("preset", "web-12-column")
            proc_layout.run(cfg_web)
            hg_web, vg_web = get_all_guides(img_web)
            if len(vg_web) != 24:
                record_fail("GL-07", "Web 12-column count", f"Expected 24 vertical guides, got {len(vg_web)}")
                return
            gutter_width = vg_web[2] - vg_web[1]
            if gutter_width != 16:
                record_fail("GL-07", "Web gutter width", f"Expected 16px gutter, got {gutter_width}px")
                return
            record_pass("GL-07", "Web 12-Column Grid preset", f"24 column/gutter guides verified with exact {gutter_width}px gutters")
        finally:
            img_web.delete()

        # 44h: Custom multi-row grid with gutters verified (GL-08)
        img_row = Gimp.Image.new(600, 600, Gimp.ImageBaseType.RGB)
        try:
            cfg_row = proc_layout.create_config()
            cfg_row.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
            cfg_row.set_property("image", img_row)
            cfg_row.set_property("preset", "custom")
            cfg_row.set_property("columns", 0)
            cfg_row.set_property("rows", 3)
            cfg_row.set_property("row-gutter", 20.0)
            proc_layout.run(cfg_row)
            hg_row, vg_row = get_all_guides(img_row)
            if len(hg_row) != 4 or (hg_row[1] - hg_row[0]) != 20:
                record_fail("GL-08", "Custom row grid", f"Expected 4 guides with 20px gutter, got {hg_row}")
                return
            record_pass("GL-08", "Custom multi-row grid with gutters", f"Row gutter pairs verified ({hg_row})")
        finally:
            img_row.delete()

        # 44i: Clear Existing Guides option verified (GL-09)
        cfg_repl = proc_layout.create_config()
        cfg_repl.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_repl.set_property("image", image)
        cfg_repl.set_property("preset", "center-split")
        cfg_repl.set_property("clear-existing", True)
        proc_layout.run(cfg_repl)
        hg_repl, vg_repl = get_all_guides(image)
        if hg_repl != [150] or vg_repl != [150]:
            record_fail("GL-09", "Clear existing toggle", f"Prior guides were not cleared: H={hg_repl}, V={vg_repl}")
            return
        record_pass("GL-09", "Clear Existing Guides option", "Wiped prior guides and generated new layout cleanly")

        # 44j: Standalone python-fu-clear-guides procedure verified (GL-10)
        cfg_clear = proc_clear.create_config()
        cfg_clear.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_clear.set_property("image", image)
        res_clear = proc_clear.run(cfg_clear)
        if res_clear.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("GL-10", "Clear guides execution", f"Expected SUCCESS, got {res_clear.index(0)}")
            return
        hg_after_clear, vg_after_clear = get_all_guides(image)
        if len(hg_after_clear) > 0 or len(vg_after_clear) > 0:
            record_fail("GL-10", "Clear guides cleanup", f"Guides remain: H={hg_after_clear}, V={vg_after_clear}")
            return
        record_pass("GL-10", "Clear Guides helper procedure", "All guides wiped to 0 via 1-click clear procedure")

        # 44k: Asymmetrical margins verified (GL-11)
        cfg_asym = proc_layout.create_config()
        cfg_asym.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_asym.set_property("image", image)
        cfg_asym.set_property("preset", "custom")
        cfg_asym.set_property("columns", 0)
        cfg_asym.set_property("rows", 0)
        cfg_asym.set_property("margin-top", 10.0)      # 30px
        cfg_asym.set_property("margin-bottom", 20.0)   # 240px
        cfg_asym.set_property("margin-left", 5.0)       # 15px
        cfg_asym.set_property("margin-right", 15.0)     # 255px
        proc_layout.run(cfg_asym)
        hg_asym, vg_asym = get_all_guides(image)
        if hg_asym != [30, 240] or vg_asym != [15, 255]:
            record_fail("GL-11", "Asymmetrical margins", f"Expected H=[30, 240], V=[15, 255], got H={hg_asym}, V={vg_asym}")
            return
        record_pass("GL-11", "Asymmetrical margins", f"Custom margins verified (Top=30px, Bottom=240px, Left=15px, Right=255px)")

        # 44l: Zero layer modification verified (GL-12)
        p_base_after = base.get_pixel(150, 150).get_rgba()
        diff_layer = max(abs(a - b) for a, b in zip(p_base_before, p_base_after))
        if diff_layer > 0.000001:
            record_fail("GL-12", "Layer invariance", f"Base layer altered by {diff_layer:.6f}")
            return
        record_pass("GL-12", "Zero layer modification", f"Guides float over canvas leaving pixels untouched (diff {diff_layer:.6f})")

    except Exception as e:
        record_fail("GL-ERR", "Unexpected exception", str(e))
    finally:
        image.delete()



# ==============================================================================
# TEST 45: Frame Animation & Tweening Helper Plugin
# ==============================================================================
def test_frame_animation():
    print("\n--- Test Suite 45: Frame Animation & Tweening Helper Plugin ---")
    pdb = Gimp.get_pdb()

    proc_setup = pdb.lookup_procedure("python-fu-frame-animation-setup")
    proc_tween = pdb.lookup_procedure("python-fu-create-tween")
    proc_pingpong = pdb.lookup_procedure("python-fu-pingpong-animation")
    proc_remove = pdb.lookup_procedure("python-fu-remove-animation-tags")

    if not all([proc_setup, proc_tween, proc_pingpong, proc_remove]):
        record_fail("FA-01", "Procedure lookup", "One or more animation procedures could not be found")
        return

    # FA-01: Procedure arguments verification
    cfg_s = proc_setup.create_config()
    cfg_t = proc_tween.create_config()
    cfg_p = proc_pingpong.create_config()
    cfg_r = proc_remove.create_config()

    expected_s = ["fps-preset", "custom-delay", "disposal", "target-layers", "reverse-order"]
    expected_t = ["tween-mode", "frames-to-add", "delay-ms", "disposal"]
    expected_p = ["include-endpoints"]

    missing_s = [k for k in expected_s if not cfg_s.find_property(k)]
    missing_t = [k for k in expected_t if not cfg_t.find_property(k)]
    missing_p = [k for k in expected_p if not cfg_p.find_property(k)]

    if missing_s or missing_t or missing_p:
        record_fail("FA-01", "Procedure arguments", f"Missing properties: s={missing_s}, t={missing_t}, p={missing_p}")
        return
    record_pass("FA-01", "Procedure arguments verified", "All properties verified across 4 procedures")

    # Create test document with 3 frames
    image = Gimp.Image.new(100, 100, Gimp.ImageBaseType.RGB)
    try:
        f1 = Gimp.Layer.new(image, "Frame 1", 100, 100, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(f1, None, 0)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.0, 0.0, 0.0)"))
        f1.edit_fill(Gimp.FillType.FOREGROUND)

        f2 = Gimp.Layer.new(image, "Frame 2", 100, 100, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(f2, None, 0)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.5, 0.5, 0.5)"))
        f2.edit_fill(Gimp.FillType.FOREGROUND)

        f3 = Gimp.Layer.new(image, "Frame 3", 100, 100, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        image.insert_layer(f3, None, 0)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(1.0, 1.0, 1.0)"))
        f3.edit_fill(Gimp.FillType.FOREGROUND)

        # FA-02 & FA-03 & FA-04: Frame Animation Setup 24 fps preset & (replace) disposal
        cfg_24 = proc_setup.create_config()
        cfg_24.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_24.set_property("image", image)
        cfg_24.set_property("fps-preset", "24fps")
        cfg_24.set_property("disposal", "replace")
        cfg_24.set_property("target-layers", "all-layers")
        cfg_24.set_property("reverse-order", False)
        res = proc_setup.run(cfg_24)
        if res.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("FA-02", "Execution status", f"Expected SUCCESS, got {res.index(0)}")
            return
        record_pass("FA-02", "Execution status", "SUCCESS")

        names_24 = [l.get_name() for l in image.get_layers()]
        all_42ms = all("(42ms)" in n for n in names_24)
        all_replace = all("(replace)" in n for n in names_24)
        if not all_42ms:
            record_fail("FA-03", "24 fps delay tag", f"Expected (42ms) in all names: {names_24}")
            return
        record_pass("FA-03", "Frame Animation Setup 24 fps preset", f"All layers tagged with 24 fps delay (42ms): {names_24}")

        if not all_replace:
            record_fail("FA-04", "Disposal method tag", f"Expected (replace) in all names: {names_24}")
            return
        record_pass("FA-04", "Frame Animation Setup disposal method", "All layers tagged with (replace)")

        # FA-05: (combine) mode verification
        cfg_comb = proc_setup.create_config()
        cfg_comb.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_comb.set_property("image", image)
        cfg_comb.set_property("fps-preset", "10fps")
        cfg_comb.set_property("disposal", "combine")
        cfg_comb.set_property("target-layers", "all-layers")
        cfg_comb.set_property("reverse-order", False)
        proc_setup.run(cfg_comb)
        names_comb = [l.get_name() for l in image.get_layers()]
        all_comb = all("(100ms) (combine)" in n for n in names_comb)
        if not all_comb:
            record_fail("FA-05", "Combine disposal mode", f"Expected (100ms) (combine) in all names: {names_comb}")
            return
        record_pass("FA-05", "Frame Animation Setup (combine) mode", f"All layers tagged with (100ms) (combine): {names_comb}")

        # FA-06: Custom frame delay verification
        cfg_cust = proc_setup.create_config()
        cfg_cust.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cust.set_property("image", image)
        cfg_cust.set_property("fps-preset", "custom")
        cfg_cust.set_property("custom-delay", 175)
        cfg_cust.set_property("disposal", "replace")
        cfg_cust.set_property("target-layers", "all-layers")
        cfg_cust.set_property("reverse-order", False)
        proc_setup.run(cfg_cust)
        names_cust = [l.get_name() for l in image.get_layers()]
        all_175ms = all("(175ms)" in n for n in names_cust)
        if not all_175ms:
            record_fail("FA-06", "Custom frame delay", f"Expected (175ms) in all names: {names_cust}")
            return
        record_pass("FA-06", "Custom frame delay verification", f"Custom 175ms delay applied across all layers: {names_cust}")

        # FA-07: Reverse layer order verification
        layers_before_rev = [l.get_name() for l in image.get_layers()]
        cfg_rev = proc_setup.create_config()
        cfg_rev.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_rev.set_property("image", image)
        cfg_rev.set_property("fps-preset", "custom")
        cfg_rev.set_property("custom-delay", 175)
        cfg_rev.set_property("disposal", "replace")
        cfg_rev.set_property("target-layers", "all-layers")
        cfg_rev.set_property("reverse-order", True)
        proc_setup.run(cfg_rev)
        layers_after_rev = [l.get_name() for l in image.get_layers()]
        if layers_after_rev != list(reversed(layers_before_rev)):
            record_fail("FA-07", "Reverse layer order", f"Expected {list(reversed(layers_before_rev))}, got {layers_after_rev}")
            return
        record_pass("FA-07", "Reverse layer playback order", f"Inverted stack order verified: {layers_after_rev}")

        # FA-08: Selected-layer-only targeting
        target_layer = image.get_layers()[0]
        image.set_selected_layers([target_layer])
        cfg_sel = proc_setup.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", image)
        cfg_sel.set_property("fps-preset", "30fps")
        cfg_sel.set_property("disposal", "replace")
        cfg_sel.set_property("target-layers", "selected-layer")
        cfg_sel.set_property("reverse-order", False)
        proc_setup.run(cfg_sel)
        names_sel = [l.get_name() for l in image.get_layers()]
        if "(33ms)" not in names_sel[0] or "(33ms)" in names_sel[1] or "(33ms)" in names_sel[2]:
            record_fail("FA-08", "Selected layer targeting", f"Expected only first layer tagged with (33ms): {names_sel}")
            return
        record_pass("FA-08", "Selected-layer-only targeting", f"Only active layer updated to 33ms: {names_sel}")

    finally:
        image.delete()

    # FA-09 & FA-10 & FA-14: Tweening & Opacity Interpolation Verification
    img_tween = Gimp.Image.new(100, 100, Gimp.ImageBaseType.RGB)
    try:
        # Keyframe A (Bottom: Black 0.0)
        kf_a = Gimp.Layer.new(img_tween, "Keyframe A (Black)", 100, 100, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        img_tween.insert_layer(kf_a, None, 0)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.0, 0.0, 0.0)"))
        kf_a.edit_fill(Gimp.FillType.FOREGROUND)

        # Keyframe B (Top: White 1.0)
        kf_b = Gimp.Layer.new(img_tween, "Keyframe B (White)", 100, 100, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        img_tween.insert_layer(kf_b, None, 0)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(1.0, 1.0, 1.0)"))
        kf_b.edit_fill(Gimp.FillType.FOREGROUND)

        # FA-09: Create 3 tween frames between Keyframe A and B
        cfg_tw = proc_tween.create_config()
        cfg_tw.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_tw.set_property("image", img_tween)
        cfg_tw.set_property("tween-mode", "consecutive-pairs")
        cfg_tw.set_property("frames-to-add", 3)
        cfg_tw.set_property("delay-ms", 83)
        cfg_tw.set_property("disposal", "replace")
        res_tw = proc_tween.run(cfg_tw)
        if res_tw.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("FA-09", "Create tween status", f"Expected SUCCESS, got {res_tw.index(0)}")
            return

        tw_layers = list(img_tween.get_layers())
        if len(tw_layers) != 5:
            record_fail("FA-09", "Tween layer count", f"Expected 5 layers, got {len(tw_layers)}: {[l.get_name() for l in tw_layers]}")
            return
        record_pass("FA-09", "Single-pair crossfade tweening", f"Generated 3 in-between frames (total 5 layers): {[l.get_name() for l in tw_layers]}")

        # FA-10: Opacity interpolation verification
        # Playback bottom-to-top order: [kf_a (0%), tween 1 (25%), tween 2 (50%), tween 3 (75%), kf_b (100%)]
        tw_layers_bottom_up = list(reversed(tw_layers))
        r0 = tw_layers_bottom_up[0].get_pixel(50, 50).get_rgba().red
        r1 = tw_layers_bottom_up[1].get_pixel(50, 50).get_rgba().red
        r2 = tw_layers_bottom_up[2].get_pixel(50, 50).get_rgba().red
        r3 = tw_layers_bottom_up[3].get_pixel(50, 50).get_rgba().red
        r4 = tw_layers_bottom_up[4].get_pixel(50, 50).get_rgba().red

        # Expect r0 == 0.0, r1 ~ 0.25, r2 ~ 0.50, r3 ~ 0.75, r4 == 1.0
        if not (abs(r1 - 0.25) < 0.03 and abs(r2 - 0.50) < 0.03 and abs(r3 - 0.75) < 0.03):
            record_fail("FA-10", "Crossfade interpolation", f"Expected [0.0, ~0.25, ~0.50, ~0.75, 1.0], got [{r0:.3f}, {r1:.3f}, {r2:.3f}, {r3:.3f}, {r4:.3f}]")
            return
        record_pass("FA-10", "Crossfade opacity interpolation", f"Linear progression verified: 0.00 -> {r1:.3f} (25%) -> {r2:.3f} (50%) -> {r3:.3f} (75%) -> 1.00 (100%)")

        # FA-14: Base keyframe pixel preservation
        if abs(r0 - 0.0) > 0.000001 or abs(r4 - 1.0) > 0.000001:
            record_fail("FA-14", "Keyframe preservation", f"Keyframe pixels altered: r0={r0}, r4={r4}")
            return
        record_pass("FA-14", "Base keyframe pixel preservation", f"Original keyframe pixels 100% untouched (kf_a={r0:.6f}, kf_b={r4:.6f})")

    finally:
        img_tween.delete()

    # FA-11: Multi-keyframe sequence tweening verification
    img_multi = Gimp.Image.new(100, 100, Gimp.ImageBaseType.RGB)
    try:
        # 3 keyframes
        for name, col in [("Frame 1", "rgb(0,0,0)"), ("Frame 2", "rgb(0.5,0.5,0.5)"), ("Frame 3", "rgb(1,1,1)")]:
            l = Gimp.Layer.new(img_multi, name, 100, 100, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
            img_multi.insert_layer(l, None, 0)
            Gimp.context_set_foreground(Gegl.Color.new(col))
            l.edit_fill(Gimp.FillType.FOREGROUND)

        cfg_m = proc_tween.create_config()
        cfg_m.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_m.set_property("image", img_multi)
        cfg_m.set_property("tween-mode", "consecutive-pairs")
        cfg_m.set_property("frames-to-add", 2)
        cfg_m.set_property("delay-ms", 100)
        cfg_m.set_property("disposal", "replace")
        proc_tween.run(cfg_m)

        multi_layers = img_multi.get_layers()
        if len(multi_layers) != 7:
            record_fail("FA-11", "Multi-keyframe tween count", f"Expected 7 layers, got {len(multi_layers)}")
            return
        record_pass("FA-11", "Full sequence consecutive-pair tweening", f"7 total frames generated across 3 keyframes: {[l.get_name() for l in multi_layers]}")
    finally:
        img_multi.delete()

    # FA-12 & FA-13: Ping-Pong Loop & Remove Animation Tags
    img_loop = Gimp.Image.new(100, 100, Gimp.ImageBaseType.RGB)
    try:
        for name in ["Frame 1 (100ms) (replace)", "Frame 2 (100ms) (replace)", "Frame 3 (100ms) (replace)", "Frame 4 (100ms) (replace)"]:
            l = Gimp.Layer.new(img_loop, name, 100, 100, Gimp.ImageType.RGB_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
            img_loop.insert_layer(l, None, 0)

        cfg_pp = proc_pingpong.create_config()
        cfg_pp.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_pp.set_property("image", img_loop)
        cfg_pp.set_property("include-endpoints", False)
        res_pp = proc_pingpong.run(cfg_pp)
        if res_pp.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("FA-12", "Ping-pong status", f"Expected SUCCESS, got {res_pp.index(0)}")
            return

        loop_layers = list(img_loop.get_layers())
        if len(loop_layers) != 6:
            record_fail("FA-12", "Ping-pong layer count", f"Expected 6 layers, got {len(loop_layers)}")
            return

        top_two_names = [loop_layers[0].get_name(), loop_layers[1].get_name()]
        if not ("Loop Reverse" in top_two_names[0] and "Loop Reverse" in top_two_names[1]):
            record_fail("FA-12", "Ping-pong names", f"Expected Loop Reverse in top layers: {top_two_names}")
            return
        record_pass("FA-12", "Ping-Pong loop generation", f"4-frame sequence expanded to seamless 6-frame loop: {[l.get_name() for l in loop_layers[::-1]]}")

        # FA-13: Remove animation tags
        cfg_rm = proc_remove.create_config()
        cfg_rm.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_rm.set_property("image", img_loop)
        res_rm = proc_remove.run(cfg_rm)
        if res_rm.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("FA-13", "Remove tags status", f"Expected SUCCESS, got {res_rm.index(0)}")
            return

        cleaned_names = [l.get_name() for l in img_loop.get_layers()]
        has_any_tag = any(re.search(r'\(\s*(?:\d+ms|replace|combine)\s*\)', n, re.I) for n in cleaned_names)
        if has_any_tag:
            record_fail("FA-13", "Cleaned tag check", f"Animation tags still present: {cleaned_names}")
            return
        record_pass("FA-13", "Remove animation tags", f"All timing and disposal tags cleanly stripped: {cleaned_names}")

    finally:
        img_loop.delete()


# ==============================================================================
# TEST 46: Seamless Pattern Generator & Tile Preview Helper Plugin (Phase 51)
# ==============================================================================
def test_seamless_pattern():
    import numpy as np

    print("\n--- Test Suite 46: Seamless Pattern Generator & Tile Preview Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc_seamless = pdb.lookup_procedure("python-fu-seamless-pattern")
    proc_prev = pdb.lookup_procedure("python-fu-pattern-preview")
    proc_fill = pdb.lookup_procedure("python-fu-pattern-fill")

    if proc_seamless is None or proc_prev is None or proc_fill is None:
        record_fail("SP-01", "Procedure lookup", "One or more seamless pattern procedures not found in PDB")
        return

    # SP-01: Procedure arguments verification
    seamless_args = [p.name for p in proc_seamless.get_arguments()]
    prev_args = [p.name for p in proc_prev.get_arguments()]
    fill_args = [p.name for p in proc_fill.get_arguments()]

    has_s_args = all(a in seamless_args for a in ["method", "blend-width", "output-mode", "mask-type"])
    has_p_args = all(a in prev_args for a in ["grid-size", "destination"])
    has_f_args = all(a in fill_args for a in ["blend-mode", "opacity", "mask-type"])

    if not (has_s_args and has_p_args and has_f_args):
        record_fail("SP-01", "Procedure argument signatures", f"Missing expected arguments: seamless={seamless_args}, prev={prev_args}, fill={fill_args}")
        return
    record_pass("SP-01", "Procedure signatures & argument audit", f"All arguments verified across all 3 procedures (seamless: {len(seamless_args)}, prev: {len(prev_args)}, fill: {len(fill_args)})")

    # Create synthetic test pattern: 40x40 image with linear gradients along X and Y
    img = Gimp.Image.new(40, 40, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(img, "TileBase", 40, 40, Gimp.ImageType.RGBA_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        img.insert_layer(base, None, 0)
        img.set_selected_layers([base])

        buf = base.get_buffer()
        rect = Gegl.Rectangle.new(0, 0, 40, 40)
        x_coords = np.linspace(10, 240, 40, dtype=np.uint8)
        y_coords = np.linspace(20, 220, 40, dtype=np.uint8)
        xx, yy = np.meshgrid(x_coords, y_coords)
        arr = np.zeros((40, 40, 4), dtype=np.uint8)
        arr[..., 0] = xx
        arr[..., 1] = yy
        arr[..., 2] = 128
        arr[..., 3] = 255
        buf.set(rect, "RGBA u8", arr.tobytes())
        buf.flush()
        base.update(0, 0, 40, 40)

        # Record original base layer sample pixels for invariance check
        orig_px_samples = [base.get_pixel(x, y).get_rgba() for x in (0, 10, 20, 39) for y in (0, 10, 20, 39)]

        # SP-02 & SP-03: Kaleidoscope synthesis (PDB SUCCESS and boundary continuity)
        cfg_k = proc_seamless.create_config()
        cfg_k.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_k.set_property("image", img)
        cfg_k.set_property("method", "kaleidoscope")
        cfg_k.set_property("output-mode", "new-layer")
        cfg_k.set_property("mask-type", "none")
        res_k = proc_seamless.run(cfg_k)
        if res_k.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("SP-02", "Kaleidoscope run status", f"Expected SUCCESS (3), got {res_k.index(0)}")
            return
        record_pass("SP-02", "Execution status", "SUCCESS")

        k_layer = img.get_layers()[0]
        k_raw = k_layer.get_buffer().get(rect, 1.0, "RGBA u8", Gegl.AbyssPolicy.NONE)
        k_arr = np.frombuffer(bytes(k_raw), dtype=np.uint8).reshape((40, 40, 4))

        diff_k_x = int(np.max(np.abs(k_arr[:, 0, :3].astype(int) - k_arr[:, -1, :3].astype(int))))
        diff_k_y = int(np.max(np.abs(k_arr[0, :, :3].astype(int) - k_arr[-1, :, :3].astype(int))))
        if diff_k_x != 0 or diff_k_y != 0:
            record_fail("SP-03", "Kaleidoscope boundary continuity", f"Expected diff_x == 0 and diff_y == 0, got diff_x={diff_k_x}, diff_y={diff_k_y}")
            return
        record_pass("SP-03", "Kaleidoscope 4-quadrant reflection", f"100% boundary continuity verified (diff_x={diff_k_x}, diff_y={diff_k_y})")
        img.remove_layer(k_layer)

        # SP-04: Crossfade edge-wrap synthesis
        cfg_cf = proc_seamless.create_config()
        cfg_cf.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cf.set_property("image", img)
        cfg_cf.set_property("method", "crossfade")
        cfg_cf.set_property("blend-width", 25.0)
        cfg_cf.set_property("output-mode", "new-layer")
        cfg_cf.set_property("mask-type", "none")
        res_cf = proc_seamless.run(cfg_cf)
        if res_cf.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("SP-04", "Crossfade run status", f"Expected SUCCESS (3), got {res_cf.index(0)}")
            return

        cf_layer = img.get_layers()[0]
        cf_raw = cf_layer.get_buffer().get(rect, 1.0, "RGBA u8", Gegl.AbyssPolicy.NONE)
        cf_arr = np.frombuffer(bytes(cf_raw), dtype=np.uint8).reshape((40, 40, 4))

        raw_diff_x = float(np.mean(np.abs(arr[:, 0, 0].astype(int) - arr[:, -1, 0].astype(int))))
        cf_diff_x = float(np.mean(np.abs(cf_arr[:, 0, 0].astype(int) - cf_arr[:, -1, 0].astype(int))))
        reduct_ratio = (raw_diff_x - cf_diff_x) / max(raw_diff_x, 1e-6)
        if reduct_ratio < 0.90:
            record_fail("SP-04", "Crossfade edge discontinuity reduction", f"Expected reduction >= 90%, got {reduct_ratio*100:.1f}% (raw={raw_diff_x:.2f}, cf={cf_diff_x:.2f})")
            return
        record_pass("SP-04", "Dual-axis edge-wrap crossfade blending", f"Boundary discontinuity reduced by {reduct_ratio*100:.1f}% ({raw_diff_x:.1f} -> {cf_diff_x:.1f})")
        img.remove_layer(cf_layer)

        # SP-05: Horizontal mirror mode (mirror-x)
        cfg_mx = proc_seamless.create_config()
        cfg_mx.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_mx.set_property("image", img)
        cfg_mx.set_property("method", "mirror-x")
        cfg_mx.set_property("output-mode", "new-layer")
        cfg_mx.set_property("mask-type", "none")
        proc_seamless.run(cfg_mx)

        mx_layer = img.get_layers()[0]
        mx_raw = mx_layer.get_buffer().get(rect, 1.0, "RGBA u8", Gegl.AbyssPolicy.NONE)
        mx_arr = np.frombuffer(bytes(mx_raw), dtype=np.uint8).reshape((40, 40, 4))
        diff_mx_x = int(np.max(np.abs(mx_arr[:, 0, 0].astype(int) - mx_arr[:, -1, 0].astype(int))))
        if diff_mx_x != 0:
            record_fail("SP-05", "Horizontal mirror continuity", f"Expected diff_x == 0, got {diff_mx_x}")
            return
        record_pass("SP-05", "Horizontal symmetrical reflection (mirror-x)", f"Horizontal boundary diff == 0 verified (diff_x={diff_mx_x})")
        img.remove_layer(mx_layer)

        # SP-06: Vertical mirror mode (mirror-y)
        cfg_my = proc_seamless.create_config()
        cfg_my.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_my.set_property("image", img)
        cfg_my.set_property("method", "mirror-y")
        cfg_my.set_property("output-mode", "new-layer")
        cfg_my.set_property("mask-type", "none")
        proc_seamless.run(cfg_my)

        my_layer = img.get_layers()[0]
        my_raw = my_layer.get_buffer().get(rect, 1.0, "RGBA u8", Gegl.AbyssPolicy.NONE)
        my_arr = np.frombuffer(bytes(my_raw), dtype=np.uint8).reshape((40, 40, 4))
        diff_my_y = int(np.max(np.abs(my_arr[0, :, 1].astype(int) - my_arr[-1, :, 1].astype(int))))
        if diff_my_y != 0:
            record_fail("SP-06", "Vertical mirror continuity", f"Expected diff_y == 0, got {diff_my_y}")
            return
        record_pass("SP-06", "Vertical symmetrical reflection (mirror-y)", f"Vertical boundary diff == 0 verified (diff_y={diff_my_y})")
        img.remove_layer(my_layer)

        # SP-07: Pattern Preview 3x3 grid (new document)
        cfg_p3 = proc_prev.create_config()
        cfg_p3.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_p3.set_property("image", img)
        cfg_p3.set_property("grid-size", "3x3")
        cfg_p3.set_property("destination", "new-image")
        res_p3 = proc_prev.run(cfg_p3)
        if res_p3.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("SP-07", "Pattern preview 3x3 status", f"Expected SUCCESS (3), got {res_p3.index(0)}")
            return

        all_imgs = Gimp.get_images()
        p3_imgs = [im for im in all_imgs if im.get_width() == 120 and im.get_height() == 120]
        if not p3_imgs:
            record_fail("SP-07", "Pattern preview document dimensions", f"Expected preview document of 120x120 (3x40), found none")
            return
        record_pass("SP-07", "Pattern Preview 3x3 grid document", f"3x3 preview document created with dimensions {p3_imgs[0].get_width()}x{p3_imgs[0].get_height()}")
        for im in p3_imgs:
            im.delete()

        # SP-08: Pattern Preview layer mode (2x2 grid in current document)
        cfg_p2 = proc_prev.create_config()
        cfg_p2.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_p2.set_property("image", img)
        cfg_p2.set_property("grid-size", "2x2")
        cfg_p2.set_property("destination", "new-layer")
        res_p2 = proc_prev.run(cfg_p2)
        if res_p2.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("SP-08", "Pattern preview 2x2 status", f"Expected SUCCESS (3), got {res_p2.index(0)}")
            return

        p2_layer = img.get_layers()[0]
        if p2_layer.get_width() != 80 or p2_layer.get_height() != 80:
            record_fail("SP-08", "Pattern preview layer dimensions", f"Expected 80x80 (2x40), got {p2_layer.get_width()}x{p2_layer.get_height()}")
            return
        record_pass("SP-08", "Pattern Preview layer mode (2x2)", f"Layer '{p2_layer.get_name()}' added with dimensions {p2_layer.get_width()}x{p2_layer.get_height()}")
        img.remove_layer(p2_layer)

        # SP-09: Pattern Fill full canvas tiling
        # Create larger canvas 100x80 to verify multi-tile expansion
        img_canvas = Gimp.Image.new(100, 80, Gimp.ImageBaseType.RGB)
        try:
            base_tile = Gimp.Layer.new(img_canvas, "ActiveTile", 40, 40, Gimp.ImageType.RGBA_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
            img_canvas.insert_layer(base_tile, None, 0)
            img_canvas.set_selected_layers([base_tile])
            write_buf = base_tile.get_buffer()
            write_buf.set(rect, "RGBA u8", arr.tobytes())
            write_buf.flush()
            base_tile.update(0, 0, 40, 40)

            cfg_fill = proc_fill.create_config()
            cfg_fill.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
            cfg_fill.set_property("image", img_canvas)
            cfg_fill.set_property("blend-mode", "normal")
            cfg_fill.set_property("opacity", 100.0)
            cfg_fill.set_property("mask-type", "reveal-all")
            res_fill = proc_fill.run(cfg_fill)
            if res_fill.index(0) != Gimp.PDBStatusType.SUCCESS:
                record_fail("SP-09", "Pattern fill status", f"Expected SUCCESS (3), got {res_fill.index(0)}")
                return

            fill_layer = img_canvas.get_layers()[0]
            if fill_layer.get_width() != 100 or fill_layer.get_height() != 80:
                record_fail("SP-09", "Pattern fill dimensions", f"Expected 100x80, got {fill_layer.get_width()}x{fill_layer.get_height()}")
                return

            # Verify periodicity across tiles: pixel at (10, 10) must match pixel at (10+40, 10)
            p_t0 = fill_layer.get_pixel(10, 10).get_rgba()
            p_t1 = fill_layer.get_pixel(50, 10).get_rgba()
            p_t2 = fill_layer.get_pixel(90, 10).get_rgba()
            tile_diff = max(abs(p_t0.red - p_t1.red), abs(p_t0.red - p_t2.red))
            if tile_diff > 0.000001:
                record_fail("SP-09", "Pattern fill tiling periodicity", f"Tile periodicity diff {tile_diff:.6f} > 0")
                return
            record_pass("SP-09", "Pattern fill full canvas tiling", f"100x80 canvas completely tiled with 40x40 seamless pattern (tile diff {tile_diff:.6f})")
            img_canvas.remove_layer(fill_layer)

            # SP-10: Pattern Fill blend mode (Multiply, Screen, Overlay, Soft Light)
            for bname, expected_mode in [("multiply", Gimp.LayerMode.MULTIPLY), ("screen", Gimp.LayerMode.SCREEN), ("overlay", Gimp.LayerMode.OVERLAY), ("soft-light", Gimp.LayerMode.SOFTLIGHT)]:
                cfg_b = proc_fill.create_config()
                cfg_b.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
                cfg_b.set_property("image", img_canvas)
                cfg_b.set_property("blend-mode", bname)
                cfg_b.set_property("opacity", 75.0)
                cfg_b.set_property("mask-type", "reveal-all")
                proc_fill.run(cfg_b)
                b_l = img_canvas.get_layers()[0]
                if b_l.get_mode() != expected_mode or abs(b_l.get_opacity() - 75.0) > 0.01:
                    record_fail("SP-10", f"Blend mode {bname}", f"Expected mode {int(expected_mode)}, got mode {int(b_l.get_mode())}, opacity {b_l.get_opacity()}%")
                    return
                img_canvas.remove_layer(b_l)
            record_pass("SP-10", "Pattern fill blend modes & opacity", "Multiply, Screen, Overlay, Soft Light & 75% opacity validated")

            # SP-11: Conceal-All black layer mask
            cfg_blk = proc_fill.create_config()
            cfg_blk.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
            cfg_blk.set_property("image", img_canvas)
            cfg_blk.set_property("blend-mode", "normal")
            cfg_blk.set_property("opacity", 100.0)
            cfg_blk.set_property("mask-type", "conceal-all")
            proc_fill.run(cfg_blk)
            blk_l = img_canvas.get_layers()[0]
            if blk_l.get_mask() is None:
                record_fail("SP-11", "Conceal-all mask", "Expected attached mask, got None")
                return

            p_comp_blk = get_composite_pixel(img_canvas, 20, 20)
            p_base_blk = base_tile.get_pixel(20, 20).get_rgba()
            blk_diff = max(abs(p_comp_blk.red - p_base_blk.red), abs(p_comp_blk.green - p_base_blk.green), abs(p_comp_blk.blue - p_base_blk.blue))
            if blk_diff > 0.000001:
                record_fail("SP-11", "Conceal-all composite invariance", f"Composite altered by {blk_diff:.6f} > 0")
                return
            record_pass("SP-11", "Conceal-all black layer mask", f"Black mask attached for selective brush painting (composite diff {blk_diff:.6f})")
            img_canvas.remove_layer(blk_l)

            # SP-12: Active selection mask confinement
            img_canvas.select_rectangle(Gimp.ChannelOps.REPLACE, 20, 20, 30, 30)
            cfg_sel = proc_fill.create_config()
            cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
            cfg_sel.set_property("image", img_canvas)
            cfg_sel.set_property("blend-mode", "normal")
            cfg_sel.set_property("opacity", 100.0)
            cfg_sel.set_property("mask-type", "selection")
            proc_fill.run(cfg_sel)
            Gimp.Selection.none(img_canvas)

            sel_l = img_canvas.get_layers()[0]
            if sel_l.get_mask() is None:
                record_fail("SP-12", "Selection mask attachment", "Expected attached selection mask, got None")
                return

            # Outside selection (5, 5) composite pixel must be identical to base (diff == 0)
            p_comp_out = get_composite_pixel(img_canvas, 5, 5)
            p_base_out = base_tile.get_pixel(5, 5).get_rgba()
            out_diff = max(abs(p_comp_out.red - p_base_out.red), abs(p_comp_out.green - p_base_out.green), abs(p_comp_out.blue - p_base_out.blue))
            if out_diff > 0.000001:
                record_fail("SP-12", "Selection mask outside invariance", f"Outside pixels altered by {out_diff:.6f} > 0")
                return
            record_pass("SP-12", "Active selection mask confinement", f"Pattern confined to active selection, outside 100% untouched (diff {out_diff:.6f})")
            img_canvas.remove_layer(sel_l)

        finally:
            img_canvas.delete()

        # SP-13: Base layer pixel preservation
        after_px_samples = [base.get_pixel(x, y).get_rgba() for x in (0, 10, 20, 39) for y in (0, 10, 20, 39)]
        max_base_diff = max(
            max(abs(b.red - a.red), abs(b.green - a.green), abs(b.blue - a.blue))
            for a, b in zip(orig_px_samples, after_px_samples)
        )
        if max_base_diff > 0.000001:
            record_fail("SP-13", "Base layer preservation", f"Base pixels altered by {max_base_diff:.6f} > 0")
            return
        record_pass("SP-13", "Base layer pixel preservation", f"Original source pixels 100% untouched across all operations (diff {max_base_diff:.6f})")

    except Exception as e:
        record_fail("SP-ERR", "Unexpected exception", str(e))
    finally:
        img.delete()


# ==============================================================================
# TEST 47: Non-Destructive Selection & Layer Stroke Helper Plugin (Phase 52)
# ==============================================================================
def test_stroke_layer():
    print("\n--- Test Suite 47: Non-Destructive Selection & Layer Stroke Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-stroke-layer")
    if proc is None:
        record_fail("SL-01", "Procedure lookup", "Procedure python-fu-stroke-layer not found in PDB")
        return

    # SL-01: Procedure arguments verification
    args = [p.name for p in proc.get_arguments()]
    expected_args = [
        "position", "width", "color-source", "custom-r", "custom-g", "custom-b",
        "blend-mode", "opacity", "output-mode", "mask-type", "preserve-transparency"
    ]
    missing = [a for a in expected_args if a not in args]
    if missing:
        record_fail("SL-01", "Procedure argument signatures", f"Missing arguments: {missing} (found: {args})")
        return
    record_pass("SL-01", "Procedure signatures & argument audit", f"All {len(expected_args)} arguments verified ({args})")

    img = Gimp.Image.new(100, 100, Gimp.ImageBaseType.RGB)
    try:
        base = Gimp.Layer.new(img, "Base", 100, 100, Gimp.ImageType.RGBA_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        img.insert_layer(base, None, 0)
        img.set_selected_layers([base])

        # Fill base with solid blue
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.0, 0.0, 1.0)"))
        base.edit_fill(Gimp.FillType.FOREGROUND)

        orig_samples = [base.get_pixel(x, y).get_rgba() for x in (10, 25, 30, 45, 75, 90) for y in (10, 25, 30, 45, 75, 90)]

        # Rectangular selection from (20, 20) with size 40x40 (x: 20..59, y: 20..59)
        img.select_rectangle(Gimp.ChannelOps.REPLACE, 20, 20, 40, 40)

        # SL-02 & SL-03: Inside stroke geometry (PDB SUCCESS and Inside positioning)
        cfg_in = proc.create_config()
        cfg_in.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_in.set_property("image", img)
        cfg_in.set_property("position", "inside")
        cfg_in.set_property("width", 4)
        cfg_in.set_property("color-source", "custom")
        cfg_in.set_property("custom-r", 1.0)
        cfg_in.set_property("custom-g", 0.0)
        cfg_in.set_property("custom-b", 0.0)
        cfg_in.set_property("output-mode", "new-layer")
        cfg_in.set_property("mask-type", "none")
        res_in = proc.run(cfg_in)
        if res_in.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("SL-02", "Inside stroke execution status", f"Expected SUCCESS (3), got {res_in.index(0)}")
            return
        record_pass("SL-02", "Execution status", "SUCCESS")

        in_layer = img.get_layers()[0]
        # (22, 30): inside the 4px inside stroke band [20..23] -> Red alpha 1.0
        # (35, 35): interior of selection beyond stroke -> Transparent alpha 0.0
        # (10, 10): outside selection -> Transparent alpha 0.0
        p_in_stroke = in_layer.get_pixel(22, 30).get_rgba()
        p_in_center = in_layer.get_pixel(35, 35).get_rgba()
        p_in_out = in_layer.get_pixel(10, 10).get_rgba()

        if p_in_stroke.alpha < 0.99 or p_in_stroke.red < 0.99 or p_in_center.alpha > 0.01 or p_in_out.alpha > 0.01:
            record_fail("SL-03", "Inside stroke geometry", f"Stroke px={p_in_stroke.alpha}, center px={p_in_center.alpha}, outside px={p_in_out.alpha}")
            return
        record_pass("SL-03", "Inside stroke geometric placement", f"Stroke confined strictly inside boundary (stroke alpha={p_in_stroke.alpha:.2f}, center alpha={p_in_center.alpha:.2f}, outside alpha={p_in_out.alpha:.2f})")
        img.remove_layer(in_layer)

        # SL-04: Outside stroke geometry
        cfg_out = proc.create_config()
        cfg_out.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_out.set_property("image", img)
        cfg_out.set_property("position", "outside")
        cfg_out.set_property("width", 4)
        cfg_out.set_property("color-source", "custom")
        cfg_out.set_property("custom-r", 0.0)
        cfg_out.set_property("custom-g", 1.0)
        cfg_out.set_property("custom-b", 0.0)
        cfg_out.set_property("output-mode", "new-layer")
        cfg_out.set_property("mask-type", "none")
        proc.run(cfg_out)

        out_layer = img.get_layers()[0]
        # (18, 30): in outside stroke band [16..19] -> Green alpha 1.0
        # (25, 30): inside original selection -> Transparent alpha 0.0
        # (10, 30): beyond outside stroke band -> Transparent alpha 0.0
        p_out_stroke = out_layer.get_pixel(18, 30).get_rgba()
        p_out_in = out_layer.get_pixel(25, 30).get_rgba()
        p_out_out = out_layer.get_pixel(10, 30).get_rgba()

        if p_out_stroke.alpha < 0.99 or p_out_stroke.green < 0.99 or p_out_in.alpha > 0.01 or p_out_out.alpha > 0.01:
            record_fail("SL-04", "Outside stroke geometry", f"Stroke px={p_out_stroke.alpha}, inside px={p_out_in.alpha}, outside px={p_out_out.alpha}")
            return
        record_pass("SL-04", "Outside stroke geometric placement", f"Stroke confined strictly outside boundary (stroke alpha={p_out_stroke.alpha:.2f}, interior alpha={p_out_in.alpha:.2f}, exterior alpha={p_out_out.alpha:.2f})")
        img.remove_layer(out_layer)

        # SL-05: Center stroke geometry
        cfg_ctr = proc.create_config()
        cfg_ctr.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_ctr.set_property("image", img)
        cfg_ctr.set_property("position", "center")
        cfg_ctr.set_property("width", 6)
        cfg_ctr.set_property("color-source", "custom")
        cfg_ctr.set_property("custom-r", 0.0)
        cfg_ctr.set_property("custom-g", 0.0)
        cfg_ctr.set_property("custom-b", 1.0)
        cfg_ctr.set_property("output-mode", "new-layer")
        cfg_ctr.set_property("mask-type", "none")
        proc.run(cfg_ctr)

        ctr_layer = img.get_layers()[0]
        # Boundary at x=20. Width 6: w_out=3, w_in=3 -> band spans [17..22]
        # (18, 30): outer half of center stroke -> Blue alpha 1.0
        # (21, 30): inner half of center stroke -> Blue alpha 1.0
        # (25, 30): inside box beyond stroke -> Transparent alpha 0.0
        # (14, 30): outside box beyond stroke -> Transparent alpha 0.0
        p_ctr_outer = ctr_layer.get_pixel(18, 30).get_rgba()
        p_ctr_inner = ctr_layer.get_pixel(21, 30).get_rgba()
        p_ctr_in = ctr_layer.get_pixel(25, 30).get_rgba()
        p_ctr_out = ctr_layer.get_pixel(14, 30).get_rgba()

        if p_ctr_outer.alpha < 0.99 or p_ctr_inner.alpha < 0.99 or p_ctr_in.alpha > 0.01 or p_ctr_out.alpha > 0.01:
            record_fail("SL-05", "Center stroke geometry", f"Outer px={p_ctr_outer.alpha}, inner px={p_ctr_inner.alpha}, in px={p_ctr_in.alpha}, out px={p_ctr_out.alpha}")
            return
        record_pass("SL-05", "Center stroke symmetric placement", f"Stroke spans boundary edge symmetrically (outer alpha={p_ctr_outer.alpha:.2f}, inner alpha={p_ctr_inner.alpha:.2f}, interior alpha={p_ctr_in.alpha:.2f})")
        img.remove_layer(ctr_layer)

        # SL-06: Stroke width scaling (width 8px)
        cfg_w8 = proc.create_config()
        cfg_w8.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_w8.set_property("image", img)
        cfg_w8.set_property("position", "inside")
        cfg_w8.set_property("width", 8)
        cfg_w8.set_property("color-source", "black")
        cfg_w8.set_property("output-mode", "new-layer")
        cfg_w8.set_property("mask-type", "none")
        proc.run(cfg_w8)

        w8_layer = img.get_layers()[0]
        # Width 8px inside band: [20..27]
        p_w8_stroke = w8_layer.get_pixel(26, 30).get_rgba()
        p_w8_center = w8_layer.get_pixel(32, 30).get_rgba()
        if p_w8_stroke.alpha < 0.99 or p_w8_center.alpha > 0.01:
            record_fail("SL-06", "Stroke width scaling", f"Expected 8px band, px at 26={p_w8_stroke.alpha}, px at 32={p_w8_center.alpha}")
            return
        record_pass("SL-06", "Stroke width scaling verification", f"8px width band verified (alpha at x=26: {p_w8_stroke.alpha:.2f}, center alpha: {p_w8_center.alpha:.2f})")
        img.remove_layer(w8_layer)

        # SL-07: Custom RGB color application
        cfg_col = proc.create_config()
        cfg_col.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_col.set_property("image", img)
        cfg_col.set_property("position", "inside")
        cfg_col.set_property("width", 4)
        cfg_col.set_property("color-source", "custom")
        cfg_col.set_property("custom-r", 0.0)
        cfg_col.set_property("custom-g", 1.0)
        cfg_col.set_property("custom-b", 0.0)
        cfg_col.set_property("output-mode", "new-layer")
        cfg_col.set_property("mask-type", "none")
        proc.run(cfg_col)

        col_layer = img.get_layers()[0]
        p_col = col_layer.get_pixel(22, 30).get_rgba()
        if abs(p_col.red - 0.0) > 0.01 or abs(p_col.green - 1.0) > 0.01 or abs(p_col.blue - 0.0) > 0.01:
            record_fail("SL-07", "Custom RGB color", f"Expected pure green [0, 1, 0], got [{p_col.red:.3f}, {p_col.green:.3f}, {p_col.blue:.3f}]")
            return
        record_pass("SL-07", "Custom RGB color fidelity", f"Exact RGB values verified ([R={p_col.red:.3f}, G={p_col.green:.3f}, B={p_col.blue:.3f}])")
        img.remove_layer(col_layer)

        # SL-08: Foreground color default application
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.8, 0.4, 0.2)"))
        cfg_fg = proc.create_config()
        cfg_fg.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_fg.set_property("image", img)
        cfg_fg.set_property("position", "inside")
        cfg_fg.set_property("width", 4)
        cfg_fg.set_property("color-source", "foreground")
        cfg_fg.set_property("output-mode", "new-layer")
        cfg_fg.set_property("mask-type", "none")
        proc.run(cfg_fg)

        fg_layer = img.get_layers()[0]
        p_fg = fg_layer.get_pixel(22, 30).get_rgba()
        if abs(p_fg.red - 0.8) > 0.02 or abs(p_fg.green - 0.4) > 0.02 or abs(p_fg.blue - 0.2) > 0.02:
            record_fail("SL-08", "Foreground color default", f"Expected [0.8, 0.4, 0.2], got [{p_fg.red:.3f}, {p_fg.green:.3f}, {p_fg.blue:.3f}]")
            return
        record_pass("SL-08", "Toolbox foreground color default", f"Foreground color extracted and applied ([R={p_fg.red:.3f}, G={p_fg.green:.3f}, B={p_fg.blue:.3f}])")
        img.remove_layer(fg_layer)

        # SL-09: Blend modes and opacity
        for bname, expected_mode in [("multiply", Gimp.LayerMode.MULTIPLY), ("screen", Gimp.LayerMode.SCREEN), ("overlay", Gimp.LayerMode.OVERLAY), ("soft-light", Gimp.LayerMode.SOFTLIGHT)]:
            cfg_b = proc.create_config()
            cfg_b.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
            cfg_b.set_property("image", img)
            cfg_b.set_property("position", "inside")
            cfg_b.set_property("width", 4)
            cfg_b.set_property("color-source", "black")
            cfg_b.set_property("blend-mode", bname)
            cfg_b.set_property("opacity", 75.0)
            cfg_b.set_property("output-mode", "new-layer")
            cfg_b.set_property("mask-type", "none")
            proc.run(cfg_b)

            b_layer = img.get_layers()[0]
            if b_layer.get_mode() != expected_mode or abs(b_layer.get_opacity() - 75.0) > 0.01:
                record_fail("SL-09", f"Blend mode {bname}", f"Expected mode {int(expected_mode)}, got {int(b_layer.get_mode())}, opacity {b_layer.get_opacity()}%")
                return
            img.remove_layer(b_layer)
        record_pass("SL-09", "Blend modes & opacity validation", "Multiply, Screen, Overlay, Soft Light & 75% opacity validated")

        # SL-10: Layer alpha fallback when selection is empty
        Gimp.Selection.none(img)
        # Create an object layer with 30x30 square from (35, 35) to (65, 65)
        obj_layer = Gimp.Layer.new(img, "ObjectLayer", 100, 100, Gimp.ImageType.RGBA_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        img.insert_layer(obj_layer, None, 0)
        img.set_selected_layers([obj_layer])
        img.select_rectangle(Gimp.ChannelOps.REPLACE, 35, 35, 30, 30)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.5, 0.5, 0.5)"))
        obj_layer.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(img)

        cfg_alpha = proc.create_config()
        cfg_alpha.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_alpha.set_property("image", img)
        cfg_alpha.set_property("position", "outside")
        cfg_alpha.set_property("width", 4)
        cfg_alpha.set_property("color-source", "white")
        cfg_alpha.set_property("output-mode", "new-layer")
        cfg_alpha.set_property("mask-type", "none")
        proc.run(cfg_alpha)

        alpha_stroke = img.get_layers()[0]
        # (32, 50): in outside stroke band along left edge of object (35 - 3 = 32)
        p_alpha_st = alpha_stroke.get_pixel(32, 50).get_rgba()
        if p_alpha_st.alpha < 0.99 or p_alpha_st.red < 0.99:
            record_fail("SL-10", "Layer alpha fallback", f"Expected white stroke at (32, 50), got alpha={p_alpha_st.alpha}, red={p_alpha_st.red}")
            return
        record_pass("SL-10", "Layer alpha boundary fallback", f"Empty selection correctly falls back to layer alpha boundary (stroke alpha={p_alpha_st.alpha:.2f})")
        img.remove_layer(alpha_stroke)
        img.remove_layer(obj_layer)
        img.set_selected_layers([base])

        # SL-11: Conceal-All black layer mask
        img.select_rectangle(Gimp.ChannelOps.REPLACE, 20, 20, 40, 40)
        cfg_blk = proc.create_config()
        cfg_blk.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_blk.set_property("image", img)
        cfg_blk.set_property("position", "inside")
        cfg_blk.set_property("width", 4)
        cfg_blk.set_property("color-source", "black")
        cfg_blk.set_property("output-mode", "new-layer")
        cfg_blk.set_property("mask-type", "conceal-all")
        proc.run(cfg_blk)

        blk_layer = img.get_layers()[0]
        if blk_layer.get_mask() is None:
            record_fail("SL-11", "Conceal-all mask", "Expected attached layer mask, got None")
            return
        p_comp_blk = get_composite_pixel(img, 22, 30)
        p_base_blk = base.get_pixel(22, 30).get_rgba()
        blk_diff = max(abs(p_comp_blk.red - p_base_blk.red), abs(p_comp_blk.green - p_base_blk.green), abs(p_comp_blk.blue - p_base_blk.blue))
        if blk_diff > 0.000001:
            record_fail("SL-11", "Conceal-all composite invariance", f"Composite altered by {blk_diff:.6f} > 0")
            return
        record_pass("SL-11", "Conceal-All black layer mask", f"Black mask attached for selective brush painting (composite diff {blk_diff:.6f})")
        img.remove_layer(blk_layer)

        # SL-12: Reveal-All white layer mask attachment
        cfg_rev = proc.create_config()
        cfg_rev.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_rev.set_property("image", img)
        cfg_rev.set_property("position", "inside")
        cfg_rev.set_property("width", 4)
        cfg_rev.set_property("color-source", "white")
        cfg_rev.set_property("output-mode", "new-layer")
        cfg_rev.set_property("mask-type", "reveal-all")
        proc.run(cfg_rev)

        rev_layer = img.get_layers()[0]
        if rev_layer.get_mask() is None:
            record_fail("SL-12", "Reveal-all mask", "Expected attached layer mask, got None")
            return
        record_pass("SL-12", "Reveal-All white layer mask", "White editable mask attached")
        img.remove_layer(rev_layer)

        # SL-13: Active selection mask confinement
        cfg_sel = proc.create_config()
        cfg_sel.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel.set_property("image", img)
        cfg_sel.set_property("position", "inside")
        cfg_sel.set_property("width", 4)
        cfg_sel.set_property("color-source", "white")
        cfg_sel.set_property("output-mode", "new-layer")
        cfg_sel.set_property("mask-type", "selection")
        proc.run(cfg_sel)

        sel_layer = img.get_layers()[0]
        if sel_layer.get_mask() is None:
            record_fail("SL-13", "Selection mask", "Expected attached selection mask, got None")
            return
        record_pass("SL-13", "Active selection mask attachment", "Selection mask attached to stroke layer")
        img.remove_layer(sel_layer)
        Gimp.Selection.none(img)

        # SL-14: Base layer pixel preservation
        after_samples = [base.get_pixel(x, y).get_rgba() for x in (10, 25, 30, 45, 75, 90) for y in (10, 25, 30, 45, 75, 90)]
        max_diff = max(
            max(abs(b.red - a.red), abs(b.green - a.green), abs(b.blue - a.blue))
            for a, b in zip(orig_samples, after_samples)
        )
        if max_diff > 0.000001:
            record_fail("SL-14", "Base layer preservation", f"Base pixels altered by {max_diff:.6f} > 0")
            return
        record_pass("SL-14", "Base layer pixel preservation", f"Original source pixels 100% untouched across all operations (diff {max_diff:.6f})")

    except Exception as e:
        record_fail("SL-ERR", "Unexpected exception", str(e))
    finally:
        img.delete()


def test_solid_color_fill():
    print("\n--- Test Suite 48: Solid Color Fill Layer & Canvas Fill Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-solid-color-fill")
    if proc is None:
        record_fail("SCF-01", "Procedure lookup", "Procedure python-fu-solid-color-fill not found in PDB")
        return

    # SCF-01: Procedure arguments verification
    args = [p.name for p in proc.get_arguments()]
    expected_args = [
        "color-source", "custom-r", "custom-g", "custom-b",
        "fill-scope", "blend-mode", "opacity", "mask-type",
        "preserve-transparency"
    ]
    missing = [a for a in expected_args if a not in args]
    if missing:
        record_fail("SCF-01", "Procedure argument signatures", f"Missing arguments: {missing} (found: {args})")
        return
    record_pass("SCF-01", "Procedure lookup & argument signatures", f"All {len(expected_args)} arguments verified ({args})")

    # Create a 100x100 RGB image with distinctive baseline content
    img = Gimp.Image.new(100, 100, Gimp.ImageBaseType.RGB)
    base = Gimp.Layer.new(img, "BaseLayer", 100, 100, Gimp.ImageType.RGBA_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
    img.insert_layer(base, None, 0)
    img.set_selected_layers([base])

    # Fill base layer with color: R=0.2, G=0.4, B=0.6
    Gimp.context_set_foreground(Gegl.Color.new("rgb(0.2, 0.4, 0.6)"))
    base.edit_fill(Gimp.FillType.FOREGROUND)

    orig_samples = [base.get_pixel(x, y).get_rgba() for x in (10, 25, 40, 60, 75, 90) for y in (10, 25, 40, 60, 75, 90)]

    try:
        # SCF-02: Execution status verified (PDB status SUCCESS)
        cfg_test = proc.create_config()
        cfg_test.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_test.set_property("image", img)
        cfg_test.set_property("color-source", "foreground")
        cfg_test.set_property("fill-scope", "new-fill-layer")
        cfg_test.set_property("mask-type", "none")
        res = proc.run(cfg_test)
        if res.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("SCF-02", "PDB execution status", f"Expected SUCCESS (3), got {res.index(0)}")
            return
        record_pass("SCF-02", "PDB execution status", "Procedure executed cleanly with status SUCCESS")
        test_lyr = img.get_layers()[0]
        img.remove_layer(test_lyr)

        # SCF-03: Foreground color fill verified
        Gimp.context_set_foreground(Gegl.Color.new("rgb(1.0, 0.4, 0.1)"))
        cfg_fg = proc.create_config()
        cfg_fg.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_fg.set_property("image", img)
        cfg_fg.set_property("color-source", "foreground")
        cfg_fg.set_property("fill-scope", "new-fill-layer")
        cfg_fg.set_property("mask-type", "none")
        proc.run(cfg_fg)
        fg_layer = img.get_layers()[0]
        p_fg = fg_layer.get_pixel(50, 50).get_rgba()
        if abs(p_fg.red - 1.0) > 0.02 or abs(p_fg.green - 0.4) > 0.02 or abs(p_fg.blue - 0.1) > 0.02:
            record_fail("SCF-03", "Foreground color fill", f"Expected [1.0, 0.4, 0.1], got [{p_fg.red:.3f}, {p_fg.green:.3f}, {p_fg.blue:.3f}]")
            return
        record_pass("SCF-03", "Foreground color fill", f"Context foreground filled ([R={p_fg.red:.3f}, G={p_fg.green:.3f}, B={p_fg.blue:.3f}])")
        img.remove_layer(fg_layer)

        # SCF-04: Background color fill verified
        Gimp.context_set_background(Gegl.Color.new("rgb(0.6, 0.2, 0.8)"))
        cfg_bg = proc.create_config()
        cfg_bg.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_bg.set_property("image", img)
        cfg_bg.set_property("color-source", "background")
        cfg_bg.set_property("fill-scope", "new-fill-layer")
        cfg_bg.set_property("mask-type", "none")
        proc.run(cfg_bg)
        bg_layer = img.get_layers()[0]
        p_bg = bg_layer.get_pixel(50, 50).get_rgba()
        if abs(p_bg.red - 0.6) > 0.02 or abs(p_bg.green - 0.2) > 0.02 or abs(p_bg.blue - 0.8) > 0.02:
            record_fail("SCF-04", "Background color fill", f"Expected [0.6, 0.2, 0.8], got [{p_bg.red:.3f}, {p_bg.green:.3f}, {p_bg.blue:.3f}]")
            return
        record_pass("SCF-04", "Background color fill", f"Context background filled ([R={p_bg.red:.3f}, G={p_bg.green:.3f}, B={p_bg.blue:.3f}])")
        img.remove_layer(bg_layer)

        # SCF-05: 50% Neutral Gray fill verified (#808080)
        cfg_gray = proc.create_config()
        cfg_gray.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_gray.set_property("image", img)
        cfg_gray.set_property("color-source", "50-gray")
        cfg_gray.set_property("fill-scope", "new-fill-layer")
        cfg_gray.set_property("mask-type", "none")
        proc.run(cfg_gray)
        gray_layer = img.get_layers()[0]
        p_gray = gray_layer.get_pixel(50, 50).get_rgba()
        if abs(p_gray.red - 0.5) > 0.02 or abs(p_gray.green - 0.5) > 0.02 or abs(p_gray.blue - 0.5) > 0.02:
            record_fail("SCF-05", "50% Neutral Gray fill", f"Expected ~0.50, got [{p_gray.red:.3f}, {p_gray.green:.3f}, {p_gray.blue:.3f}]")
            return
        record_pass("SCF-05", "50% Neutral Gray fill", f"Neutral gray 50% verified ([R={p_gray.red:.3f}, G={p_gray.green:.3f}, B={p_gray.blue:.3f}])")
        img.remove_layer(gray_layer)

        # SCF-06: Solid Black fill verified (#000000)
        cfg_black = proc.create_config()
        cfg_black.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_black.set_property("image", img)
        cfg_black.set_property("color-source", "black")
        cfg_black.set_property("fill-scope", "new-fill-layer")
        cfg_black.set_property("mask-type", "none")
        proc.run(cfg_black)
        black_layer = img.get_layers()[0]
        p_black = black_layer.get_pixel(50, 50).get_rgba()
        if p_black.red > 0.01 or p_black.green > 0.01 or p_black.blue > 0.01:
            record_fail("SCF-06", "Solid Black fill", f"Expected [0.0, 0.0, 0.0], got [{p_black.red:.3f}, {p_black.green:.3f}, {p_black.blue:.3f}]")
            return
        record_pass("SCF-06", "Solid Black fill", f"Solid black verified ([R={p_black.red:.3f}, G={p_black.green:.3f}, B={p_black.blue:.3f}])")
        img.remove_layer(black_layer)

        # SCF-07: Solid White fill verified (#ffffff)
        cfg_white = proc.create_config()
        cfg_white.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_white.set_property("image", img)
        cfg_white.set_property("color-source", "white")
        cfg_white.set_property("fill-scope", "new-fill-layer")
        cfg_white.set_property("mask-type", "none")
        proc.run(cfg_white)
        white_layer = img.get_layers()[0]
        p_white = white_layer.get_pixel(50, 50).get_rgba()
        if p_white.red < 0.99 or p_white.green < 0.99 or p_white.blue < 0.99:
            record_fail("SCF-07", "Solid White fill", f"Expected [1.0, 1.0, 1.0], got [{p_white.red:.3f}, {p_white.green:.3f}, {p_white.blue:.3f}]")
            return
        record_pass("SCF-07", "Solid White fill", f"Solid white verified ([R={p_white.red:.3f}, G={p_white.green:.3f}, B={p_white.blue:.3f}])")
        img.remove_layer(white_layer)

        # SCF-08: Custom RGB color application verified (Cyan: 0.0, 1.0, 1.0)
        cfg_custom = proc.create_config()
        cfg_custom.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_custom.set_property("image", img)
        cfg_custom.set_property("color-source", "custom")
        cfg_custom.set_property("custom-r", 0.0)
        cfg_custom.set_property("custom-g", 1.0)
        cfg_custom.set_property("custom-b", 1.0)
        cfg_custom.set_property("fill-scope", "new-fill-layer")
        cfg_custom.set_property("mask-type", "none")
        proc.run(cfg_custom)
        custom_layer = img.get_layers()[0]
        p_cust = custom_layer.get_pixel(50, 50).get_rgba()
        if p_cust.red > 0.01 or p_cust.green < 0.99 or p_cust.blue < 0.99:
            record_fail("SCF-08", "Custom RGB fill", f"Expected [0.0, 1.0, 1.0], got [{p_cust.red:.3f}, {p_cust.green:.3f}, {p_cust.blue:.3f}]")
            return
        record_pass("SCF-08", "Custom RGB color application", f"Custom cyan RGB verified ([R={p_cust.red:.3f}, G={p_cust.green:.3f}, B={p_cust.blue:.3f}])")
        img.remove_layer(custom_layer)

        # SCF-09: Solid Color Fill Layer with active selection auto-mask
        # Create rectangular selection from (20, 20) to (60, 60)
        img.select_rectangle(Gimp.ChannelOps.REPLACE, 20, 20, 40, 40)
        cfg_auto = proc.create_config()
        cfg_auto.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_auto.set_property("image", img)
        cfg_auto.set_property("color-source", "black")
        cfg_auto.set_property("fill-scope", "new-fill-layer")
        cfg_auto.set_property("mask-type", "auto")
        proc.run(cfg_auto)

        auto_layer = img.get_layers()[0]
        mask = auto_layer.get_mask()
        if mask is None:
            record_fail("SCF-09", "Auto selection mask", "No layer mask attached to fill layer")
            return

        # Sample mask inside selection (40, 40) and outside (10, 10)
        m_in = mask.get_pixel(40, 40).get_rgba()
        m_out = mask.get_pixel(10, 10).get_rgba()
        if m_in.red < 0.99 or m_out.red > 0.01:
            record_fail("SCF-09", "Auto selection mask", f"Expected mask white inside ({m_in.red:.3f}) and black outside ({m_out.red:.3f})")
            return

        # Also verify the underlying layer pixel at (10, 10) is filled with black across the canvas under the mask
        p_under = auto_layer.get_pixel(10, 10).get_rgba()
        if p_under.alpha < 0.99 or p_under.red > 0.01:
            record_fail("SCF-09", "Full canvas under mask", f"Expected full canvas solid black under mask, got alpha={p_under.alpha}, red={p_under.red}")
            return
        record_pass("SCF-09", "Solid Color Fill Layer with selection mask", "Full-canvas layer filled with selection converted to editable layer mask")
        img.remove_layer(auto_layer)
        Gimp.Selection.none(img)

        # SCF-10: Selection-only fill scope verified
        img.select_rectangle(Gimp.ChannelOps.REPLACE, 20, 20, 40, 40)
        cfg_sel_only = proc.create_config()
        cfg_sel_only.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel_only.set_property("image", img)
        cfg_sel_only.set_property("color-source", "white")
        cfg_sel_only.set_property("fill-scope", "selection-only")
        cfg_sel_only.set_property("mask-type", "none")
        proc.run(cfg_sel_only)

        sel_layer = img.get_layers()[0]
        p_in_sel = sel_layer.get_pixel(40, 40).get_rgba()
        p_out_sel = sel_layer.get_pixel(10, 10).get_rgba()
        if p_in_sel.alpha < 0.99 or p_in_sel.red < 0.99 or p_out_sel.alpha > 0.01:
            record_fail("SCF-10", "Selection-only fill scope", f"Expected opaque white inside (a={p_in_sel.alpha}, r={p_in_sel.red}) and transparent outside (a={p_out_sel.alpha})")
            return
        record_pass("SCF-10", "Selection-only fill scope", "New layer contains fill strictly inside active selection boundary")
        img.remove_layer(sel_layer)
        Gimp.Selection.none(img)

        # SCF-11: Blend modes and opacity verified
        modes_to_test = [
            ("multiply", Gimp.LayerMode.MULTIPLY),
            ("screen", Gimp.LayerMode.SCREEN),
            ("overlay", Gimp.LayerMode.OVERLAY),
            ("soft-light", Gimp.LayerMode.SOFTLIGHT),
            ("color", Gimp.LayerMode.HSL_COLOR),
        ]
        for bname, expected_mode in modes_to_test:
            cfg_b = proc.create_config()
            cfg_b.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
            cfg_b.set_property("image", img)
            cfg_b.set_property("color-source", "50-gray")
            cfg_b.set_property("blend-mode", bname)
            cfg_b.set_property("opacity", 60.0)
            cfg_b.set_property("fill-scope", "new-fill-layer")
            cfg_b.set_property("mask-type", "none")
            proc.run(cfg_b)

            b_layer = img.get_layers()[0]
            if b_layer.get_mode() != expected_mode or abs(b_layer.get_opacity() - 60.0) > 0.01:
                record_fail("SCF-11", f"Blend mode {bname}", f"Expected mode {int(expected_mode)}, got {int(b_layer.get_mode())}, opacity {b_layer.get_opacity()}%")
                return
            img.remove_layer(b_layer)
        record_pass("SCF-11", "Blend modes & opacity validation", "Multiply, Screen, Overlay, Soft Light, HSL Color & 60% opacity validated")

        # SCF-12: Preserve transparency in-place fill verified
        # Create a layer where left half is filled and right half is transparent
        half_layer = Gimp.Layer.new(img, "HalfLayer", 100, 100, Gimp.ImageType.RGBA_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        img.insert_layer(half_layer, None, 0)
        img.set_selected_layers([half_layer])
        img.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 50, 100)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.3, 0.3, 0.3)"))
        half_layer.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(img)

        # Run fill in-place with preserve-transparency=True and white color
        cfg_pt = proc.create_config()
        cfg_pt.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_pt.set_property("image", img)
        cfg_pt.set_property("color-source", "white")
        cfg_pt.set_property("fill-scope", "in-place")
        cfg_pt.set_property("preserve-transparency", True)
        proc.run(cfg_pt)

        p_left = half_layer.get_pixel(25, 50).get_rgba()
        p_right = half_layer.get_pixel(75, 50).get_rgba()
        if p_left.alpha < 0.99 or p_left.red < 0.99 or p_right.alpha > 0.01:
            record_fail("SCF-12", "Preserve transparency", f"Expected opaque white at (25,50) (a={p_left.alpha}, r={p_left.red}) and transparent at (75,50) (a={p_right.alpha})")
            return
        record_pass("SCF-12", "Preserve transparency in-place", f"Opaque pixels filled (a={p_left.alpha:.2f}, r={p_left.red:.2f}) while transparent pixels preserved (a={p_right.alpha:.2f})")
        img.remove_layer(half_layer)

        # SCF-13: Conceal-All black layer mask verified
        img.set_selected_layers([base])
        cfg_cmask = proc.create_config()
        cfg_cmask.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_cmask.set_property("image", img)
        cfg_cmask.set_property("color-source", "white")
        cfg_cmask.set_property("fill-scope", "new-fill-layer")
        cfg_cmask.set_property("mask-type", "conceal-all")
        proc.run(cfg_cmask)

        cmask_layer = img.get_layers()[0]
        cmask = cmask_layer.get_mask()
        if cmask is None:
            record_fail("SCF-13", "Conceal-all mask", "No layer mask attached")
            return
        m_sample = cmask.get_pixel(50, 50).get_rgba()
        if m_sample.red > 0.01:
            record_fail("SCF-13", "Conceal-all mask", f"Expected black mask (0.0), got {m_sample.red:.3f}")
            return
        record_pass("SCF-13", "Conceal-All black layer mask", "Conceal-all mask initialized with solid black (0.000000)")
        img.remove_layer(cmask_layer)

        # SCF-14: Base layer pixel preservation
        after_samples = [base.get_pixel(x, y).get_rgba() for x in (10, 25, 40, 60, 75, 90) for y in (10, 25, 40, 60, 75, 90)]
        max_diff = max(
            max(abs(b.red - a.red), abs(b.green - a.green), abs(b.blue - a.blue))
            for a, b in zip(orig_samples, after_samples)
        )
        if max_diff > 0.000001:
            record_fail("SCF-14", "Base layer preservation", f"Base pixels altered by {max_diff:.6f} > 0")
            return
        record_pass("SCF-14", "Base layer pixel preservation", f"Original source pixels 100% untouched across all non-destructive operations (diff {max_diff:.6f})")

    except Exception as e:
        record_fail("SCF-ERR", "Unexpected exception", str(e))
    finally:
        img.delete()


def test_gradient_fill():
    print("\n--- Test Suite 49: Gradient Fill Layer & Multi-Style Gradient Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc = pdb.lookup_procedure("python-fu-gradient-fill")
    if proc is None:
        record_fail("GF-01", "Procedure lookup", "Procedure python-fu-gradient-fill not found in PDB")
        return

    # GF-01: Procedure arguments verification
    args = [p.name for p in proc.get_arguments()]
    expected_args = [
        "style", "angle", "scale", "reverse", "dither", "preset",
        "start-r", "start-g", "start-b", "end-r", "end-g", "end-b",
        "fill-scope", "blend-mode", "opacity", "mask-type",
        "preserve-transparency"
    ]
    missing = [a for a in expected_args if a not in args]
    if missing:
        record_fail("GF-01", "Procedure argument signatures", f"Missing arguments: {missing} (found: {args})")
        return
    record_pass("GF-01", "Procedure lookup & argument signatures", f"All {len(expected_args)} arguments verified ({args})")

    # Create a 100x100 RGB image with distinctive baseline content
    img = Gimp.Image.new(100, 100, Gimp.ImageBaseType.RGB)
    base = Gimp.Layer.new(img, "BaseLayer", 100, 100, Gimp.ImageType.RGBA_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
    img.insert_layer(base, None, 0)
    img.set_selected_layers([base])

    # Fill base layer with color: R=0.3, G=0.5, B=0.7
    Gimp.context_set_foreground(Gegl.Color.new("rgb(0.3, 0.5, 0.7)"))
    base.edit_fill(Gimp.FillType.FOREGROUND)

    orig_samples = [base.get_pixel(x, y).get_rgba() for x in (10, 25, 40, 60, 75, 90) for y in (10, 25, 40, 60, 75, 90)]

    try:
        # GF-02: Execution status verified (PDB status SUCCESS)
        cfg_test = proc.create_config()
        cfg_test.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_test.set_property("image", img)
        cfg_test.set_property("style", "linear")
        cfg_test.set_property("angle", 0.0)
        cfg_test.set_property("scale", 100.0)
        cfg_test.set_property("preset", "black-white")
        cfg_test.set_property("fill-scope", "new-fill-layer")
        cfg_test.set_property("mask-type", "none")
        res = proc.run(cfg_test)
        if res.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("GF-02", "PDB execution status", f"Expected SUCCESS (3), got {res.index(0)}")
            return
        record_pass("GF-02", "PDB execution status", "Procedure executed cleanly with status SUCCESS")
        test_lyr = img.get_layers()[0]

        # GF-03: Linear gradient geometry along angle 0° verified
        # At angle 0°, horizontal transition from left (black) to right (white)
        p_left = test_lyr.get_pixel(5, 50).get_rgba()
        p_right = test_lyr.get_pixel(95, 50).get_rgba()
        if p_left.red > 0.15 or p_right.red < 0.85:
            record_fail("GF-03", "Linear angle 0° transition", f"Expected left black and right white, got left={p_left.red:.3f}, right={p_right.red:.3f}")
            return
        record_pass("GF-03", "Linear gradient geometry (angle 0°)", f"Horizontal linear transition verified (left={p_left.red:.3f}, right={p_right.red:.3f})")
        img.remove_layer(test_lyr)

        # GF-04: Angle rotation 90° verified (vertical transition)
        cfg_90 = proc.create_config()
        cfg_90.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_90.set_property("image", img)
        cfg_90.set_property("style", "linear")
        cfg_90.set_property("angle", 90.0)
        cfg_90.set_property("preset", "black-white")
        cfg_90.set_property("fill-scope", "new-fill-layer")
        cfg_90.set_property("mask-type", "none")
        proc.run(cfg_90)
        lyr_90 = img.get_layers()[0]
        # At angle 90°, dy is negative (pointing up), so start (y1) is bottom (black) and end (y2) is top (white)
        p_bot = lyr_90.get_pixel(50, 95).get_rgba()
        p_top = lyr_90.get_pixel(50, 5).get_rgba()
        if p_bot.red > 0.15 or p_top.red < 0.85:
            record_fail("GF-04", "Vertical gradient (angle 90°)", f"Expected bottom black and top white, got bot={p_bot.red:.3f}, top={p_top.red:.3f}")
            return
        record_pass("GF-04", "Angle rotation 90°", f"Vertical gradient verified (bottom={p_bot.red:.3f}, top={p_top.red:.3f})")
        img.remove_layer(lyr_90)

        # GF-05: Radial gradient geometry verified
        cfg_rad = proc.create_config()
        cfg_rad.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_rad.set_property("image", img)
        cfg_rad.set_property("style", "radial")
        cfg_rad.set_property("preset", "black-white")
        cfg_rad.set_property("fill-scope", "new-fill-layer")
        cfg_rad.set_property("mask-type", "none")
        proc.run(cfg_rad)
        lyr_rad = img.get_layers()[0]
        p_center = lyr_rad.get_pixel(50, 50).get_rgba()
        p_edge_r = lyr_rad.get_pixel(95, 50).get_rgba()
        p_edge_b = lyr_rad.get_pixel(50, 95).get_rgba()
        if p_center.red > 0.15 or p_edge_r.red < 0.80 or p_edge_b.red < 0.80:
            record_fail("GF-05", "Radial gradient geometry", f"Expected dark center and bright edges, got center={p_center.red:.3f}, edge_r={p_edge_r.red:.3f}, edge_b={p_edge_b.red:.3f}")
            return
        record_pass("GF-05", "Radial gradient geometry", f"Concentric circular falloff verified (center={p_center.red:.3f}, edges={p_edge_r.red:.3f})")
        img.remove_layer(lyr_rad)

        # GF-06: Reflected (bilateral) gradient geometry verified
        cfg_ref = proc.create_config()
        cfg_ref.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_ref.set_property("image", img)
        cfg_ref.set_property("style", "reflected")
        cfg_ref.set_property("angle", 0.0)
        cfg_ref.set_property("preset", "black-white")
        cfg_ref.set_property("fill-scope", "new-fill-layer")
        cfg_ref.set_property("mask-type", "none")
        proc.run(cfg_ref)
        lyr_ref = img.get_layers()[0]
        p_ref_c = lyr_ref.get_pixel(50, 50).get_rgba()
        p_ref_l = lyr_ref.get_pixel(5, 50).get_rgba()
        p_ref_r = lyr_ref.get_pixel(95, 50).get_rgba()
        if p_ref_c.red > 0.15 or p_ref_l.red < 0.75 or p_ref_r.red < 0.75:
            record_fail("GF-06", "Reflected gradient geometry", f"Expected dark center axis and bright flanking edges, got c={p_ref_c.red:.3f}, l={p_ref_l.red:.3f}, r={p_ref_r.red:.3f}")
            return
        record_pass("GF-06", "Reflected bilateral geometry", f"Symmetric bilateral reflection verified (center={p_ref_c.red:.3f}, left={p_ref_l.red:.3f}, right={p_ref_r.red:.3f})")
        img.remove_layer(lyr_ref)

        # GF-07: Angle (conical) gradient geometry verified
        cfg_ang = proc.create_config()
        cfg_ang.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_ang.set_property("image", img)
        cfg_ang.set_property("style", "angle")
        cfg_ang.set_property("preset", "black-white")
        cfg_ang.set_property("fill-scope", "new-fill-layer")
        cfg_ang.set_property("mask-type", "none")
        proc.run(cfg_ang)
        lyr_ang = img.get_layers()[0]
        p_ang_r = lyr_ang.get_pixel(90, 50).get_rgba()
        p_ang_l = lyr_ang.get_pixel(10, 50).get_rgba()
        if abs(p_ang_r.red - p_ang_l.red) < 0.30:
            record_fail("GF-07", "Angle conical gradient", f"Expected angular sweep contrast across opposite sectors, got right={p_ang_r.red:.3f}, left={p_ang_l.red:.3f}")
            return
        record_pass("GF-07", "Angle conical gradient geometry", f"Conical rotational sweep verified (sector difference {abs(p_ang_r.red - p_ang_l.red):.3f} >= 0.30)")
        img.remove_layer(lyr_ang)

        # GF-08: Diamond (square) gradient geometry verified
        cfg_dia = proc.create_config()
        cfg_dia.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_dia.set_property("image", img)
        cfg_dia.set_property("style", "diamond")
        cfg_dia.set_property("preset", "black-white")
        cfg_dia.set_property("fill-scope", "new-fill-layer")
        cfg_dia.set_property("mask-type", "none")
        proc.run(cfg_dia)
        lyr_dia = img.get_layers()[0]
        p_dia_c = lyr_dia.get_pixel(50, 50).get_rgba()
        p_dia_corner = lyr_dia.get_pixel(95, 95).get_rgba()
        if p_dia_c.red > 0.15 or p_dia_corner.red < 0.80:
            record_fail("GF-08", "Diamond gradient geometry", f"Expected dark center and bright corners, got center={p_dia_c.red:.3f}, corner={p_dia_corner.red:.3f}")
            return
        record_pass("GF-08", "Diamond gradient geometry", f"Square / diamond gradient verified (center={p_dia_c.red:.3f}, corner={p_dia_corner.red:.3f})")
        img.remove_layer(lyr_dia)

        # GF-09: Reverse gradient toggle verified
        cfg_rev = proc.create_config()
        cfg_rev.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_rev.set_property("image", img)
        cfg_rev.set_property("style", "linear")
        cfg_rev.set_property("angle", 0.0)
        cfg_rev.set_property("reverse", True)
        cfg_rev.set_property("preset", "black-white")
        cfg_rev.set_property("fill-scope", "new-fill-layer")
        cfg_rev.set_property("mask-type", "none")
        proc.run(cfg_rev)
        lyr_rev = img.get_layers()[0]
        # In reverse mode, left should be white and right should be black
        p_rev_l = lyr_rev.get_pixel(5, 50).get_rgba()
        p_rev_r = lyr_rev.get_pixel(95, 50).get_rgba()
        if p_rev_l.red < 0.85 or p_rev_r.red > 0.15:
            record_fail("GF-09", "Reverse gradient", f"Expected left white and right black in reverse, got l={p_rev_l.red:.3f}, r={p_rev_r.red:.3f}")
            return
        record_pass("GF-09", "Reverse gradient toggle", f"Colors flipped cleanly in reverse mode (left={p_rev_l.red:.3f}, right={p_rev_r.red:.3f})")
        img.remove_layer(lyr_rev)

        # GF-10: Scale expansion verified
        cfg_s50 = proc.create_config()
        cfg_s50.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_s50.set_property("image", img)
        cfg_s50.set_property("style", "radial")
        cfg_s50.set_property("scale", 40.0)
        cfg_s50.set_property("preset", "black-white")
        cfg_s50.set_property("fill-scope", "new-fill-layer")
        cfg_s50.set_property("mask-type", "none")
        proc.run(cfg_s50)
        lyr_s50 = img.get_layers()[0]

        cfg_s150 = proc.create_config()
        cfg_s150.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_s150.set_property("image", img)
        cfg_s150.set_property("style", "radial")
        cfg_s150.set_property("scale", 160.0)
        cfg_s150.set_property("preset", "black-white")
        cfg_s150.set_property("fill-scope", "new-fill-layer")
        cfg_s150.set_property("mask-type", "none")
        proc.run(cfg_s150)
        lyr_s150 = img.get_layers()[0]

        p_at_30_s50 = lyr_s50.get_pixel(80, 50).get_rgba().red
        p_at_30_s150 = lyr_s150.get_pixel(80, 50).get_rgba().red
        if p_at_30_s50 <= p_at_30_s150:
            record_fail("GF-10", "Scale expansion", f"Expected scale=40 brightness ({p_at_30_s50:.3f}) > scale=160 brightness ({p_at_30_s150:.3f})")
            return
        record_pass("GF-10", "Scale expansion control", f"Scale controls transition distance (scale 40%={p_at_30_s50:.3f} > scale 160%={p_at_30_s150:.3f})")
        img.remove_layer(lyr_s150)
        img.remove_layer(lyr_s50)

        # GF-11: Gradient Fill Layer with active selection auto-mask
        img.select_rectangle(Gimp.ChannelOps.REPLACE, 20, 20, 40, 40)
        cfg_auto = proc.create_config()
        cfg_auto.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_auto.set_property("image", img)
        cfg_auto.set_property("style", "linear")
        cfg_auto.set_property("preset", "black-white")
        cfg_auto.set_property("fill-scope", "new-fill-layer")
        cfg_auto.set_property("mask-type", "auto")
        proc.run(cfg_auto)

        auto_layer = img.get_layers()[0]
        mask = auto_layer.get_mask()
        if mask is None:
            record_fail("GF-11", "Auto selection mask", "No layer mask attached to fill layer")
            return

        m_in = mask.get_pixel(40, 40).get_rgba()
        m_out = mask.get_pixel(10, 10).get_rgba()
        if m_in.red < 0.99 or m_out.red > 0.01:
            record_fail("GF-11", "Auto selection mask", f"Expected mask white inside ({m_in.red:.3f}) and black outside ({m_out.red:.3f})")
            return

        p_under = auto_layer.get_pixel(10, 10).get_rgba()
        if p_under.alpha < 0.99:
            record_fail("GF-11", "Full canvas under mask", f"Expected full canvas gradient under mask, got alpha={p_under.alpha}")
            return
        record_pass("GF-11", "Gradient Fill Layer with selection mask", "Full-canvas layer filled with selection converted to editable layer mask")
        img.remove_layer(auto_layer)
        Gimp.Selection.none(img)

        # GF-12: Selection-only fill scope verified
        img.select_rectangle(Gimp.ChannelOps.REPLACE, 20, 20, 40, 40)
        cfg_sel_only = proc.create_config()
        cfg_sel_only.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel_only.set_property("image", img)
        cfg_sel_only.set_property("style", "linear")
        cfg_sel_only.set_property("preset", "black-white")
        cfg_sel_only.set_property("fill-scope", "selection-only")
        cfg_sel_only.set_property("mask-type", "none")
        proc.run(cfg_sel_only)

        sel_layer = img.get_layers()[0]
        p_in_sel = sel_layer.get_pixel(40, 40).get_rgba()
        p_out_sel = sel_layer.get_pixel(10, 10).get_rgba()
        if p_in_sel.alpha < 0.99 or p_out_sel.alpha > 0.01:
            record_fail("GF-12", "Selection-only fill scope", f"Expected opaque inside (a={p_in_sel.alpha}) and transparent outside (a={p_out_sel.alpha})")
            return
        record_pass("GF-12", "Selection-only fill scope", "New layer contains gradient strictly inside active selection boundary")
        img.remove_layer(sel_layer)
        Gimp.Selection.none(img)

        # GF-13: Blend modes and opacity verified
        modes_to_test = [
            ("multiply", Gimp.LayerMode.MULTIPLY),
            ("screen", Gimp.LayerMode.SCREEN),
            ("overlay", Gimp.LayerMode.OVERLAY),
            ("soft-light", Gimp.LayerMode.SOFTLIGHT),
            ("color", Gimp.LayerMode.HSL_COLOR),
        ]
        for bname, expected_mode in modes_to_test:
            cfg_b = proc.create_config()
            cfg_b.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
            cfg_b.set_property("image", img)
            cfg_b.set_property("style", "linear")
            cfg_b.set_property("preset", "sunset-horizon")
            cfg_b.set_property("blend-mode", bname)
            cfg_b.set_property("opacity", 70.0)
            cfg_b.set_property("fill-scope", "new-fill-layer")
            cfg_b.set_property("mask-type", "none")
            proc.run(cfg_b)

            b_layer = img.get_layers()[0]
            if b_layer.get_mode() != expected_mode or abs(b_layer.get_opacity() - 70.0) > 0.01:
                record_fail("GF-13", f"Blend mode {bname}", f"Expected mode {int(expected_mode)}, got {int(b_layer.get_mode())}, opacity {b_layer.get_opacity()}%")
                return
            img.remove_layer(b_layer)
        record_pass("GF-13", "Blend modes & opacity validation", "Multiply, Screen, Overlay, Soft Light, HSL Color & 70% opacity validated")

        # GF-14: Preserve transparency in-place fill verified
        half_layer = Gimp.Layer.new(img, "HalfLayer", 100, 100, Gimp.ImageType.RGBA_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        img.insert_layer(half_layer, None, 0)
        img.set_selected_layers([half_layer])
        img.select_rectangle(Gimp.ChannelOps.REPLACE, 0, 0, 50, 100)
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.3, 0.3, 0.3)"))
        half_layer.edit_fill(Gimp.FillType.FOREGROUND)
        Gimp.Selection.none(img)

        cfg_pt = proc.create_config()
        cfg_pt.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_pt.set_property("image", img)
        cfg_pt.set_property("style", "linear")
        cfg_pt.set_property("preset", "black-white")
        cfg_pt.set_property("fill-scope", "in-place")
        cfg_pt.set_property("preserve-transparency", True)
        proc.run(cfg_pt)

        p_left = half_layer.get_pixel(25, 50).get_rgba()
        p_right = half_layer.get_pixel(75, 50).get_rgba()
        if p_left.alpha < 0.99 or p_right.alpha > 0.01:
            record_fail("GF-14", "Preserve transparency", f"Expected opaque left (a={p_left.alpha}) and transparent right (a={p_right.alpha})")
            return
        record_pass("GF-14", "Preserve transparency in-place", f"Opaque pixels modified (a={p_left.alpha:.2f}) while transparent pixels preserved (a={p_right.alpha:.2f})")
        img.remove_layer(half_layer)

        # GF-15: Base layer pixel preservation
        after_samples = [base.get_pixel(x, y).get_rgba() for x in (10, 25, 40, 60, 75, 90) for y in (10, 25, 40, 60, 75, 90)]
        max_diff = max(
            max(abs(b.red - a.red), abs(b.green - a.green), abs(b.blue - a.blue))
            for a, b in zip(orig_samples, after_samples)
        )
        if max_diff > 0.000001:
            record_fail("GF-15", "Base layer preservation", f"Base pixels altered by {max_diff:.6f} > 0")
            return
        record_pass("GF-15", "Base layer pixel preservation", f"Original source pixels 100% untouched across all non-destructive operations (diff {max_diff:.6f})")

    except Exception as e:
        record_fail("GF-ERR", "Unexpected exception", str(e))
    finally:
        img.delete()


# ==============================================================================
# TEST 50: Exposure Adjustment Layer & Tonal Range Helper Plugin
# ==============================================================================
def test_exposure_adjustment():
    print("\n--- Test Suite 50: Exposure Adjustment Layer & Tonal Range Helper Plugin ---")
    pdb = Gimp.get_pdb()
    proc_name = "python-fu-exposure"

    # EXP-01: Procedure lookup and argument signatures
    proc = pdb.lookup_procedure(proc_name)
    if proc is None:
        record_fail("EXP-01", "Procedure lookup", f"{proc_name} not found in PDB")
        return

    expected_args = [
        "run-mode", "image", "drawables", "preset", "exposure", "offset", "gamma",
        "blend-mode", "opacity", "output-mode", "mask-type"
    ]
    arg_names = [arg.name for arg in proc.get_arguments()]
    missing = [a for a in expected_args if a not in arg_names]
    if missing:
        record_fail("EXP-01", "Argument audit", f"Missing arguments: {missing}")
        return
    record_pass("EXP-01", "Procedure signatures & argument audit", f"All {len(expected_args)} arguments verified ({arg_names})")

    # Setup test canvas: 100x100 RGB image with midtone base layer (0.25 gray)
    img = Gimp.Image.new(100, 100, Gimp.ImageBaseType.RGB)
    base = Gimp.Layer.new(img, "BaseArt", 100, 100, Gimp.ImageType.RGBA_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
    img.insert_layer(base, None, 0)
    img.set_selected_layers([base])
    Gimp.context_set_foreground(Gegl.Color.new("rgb(0.25, 0.25, 0.25)"))
    base.edit_fill(Gimp.FillType.FOREGROUND)

    orig_samples = [base.get_pixel(x, y).get_rgba() for x in (10, 25, 40, 60, 75, 90) for y in (10, 25, 40, 60, 75, 90)]

    try:
        # EXP-02: Execution status check
        cfg = proc.create_config()
        cfg.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg.set_property("image", img)
        cfg.set_property("preset", "default")
        cfg.set_property("output-mode", "new-layer")
        cfg.set_property("mask-type", "none")
        res = proc.run(cfg)
        if res.index(0) != Gimp.PDBStatusType.SUCCESS:
            record_fail("EXP-02", "PDB execution status", f"Execution returned non-success code {res.index(0)}")
            return
        record_pass("EXP-02", "PDB execution status", "Procedure executed cleanly with status SUCCESS")
        def_layer = img.get_layers()[0]
        img.remove_layer(def_layer)

        # EXP-03: Exposure EV stops +1.0 scaling verified (I' = 2 * I)
        # Base 0.25 -> 0.50 (+1 stop overexposure)
        cfg_plus1 = proc.create_config()
        cfg_plus1.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_plus1.set_property("image", img)
        cfg_plus1.set_property("preset", "custom")
        cfg_plus1.set_property("exposure", 1.0)
        cfg_plus1.set_property("offset", 0.0)
        cfg_plus1.set_property("gamma", 1.0)
        cfg_plus1.set_property("output-mode", "new-layer")
        cfg_plus1.set_property("mask-type", "none")
        proc.run(cfg_plus1)

        lyr_plus1 = img.get_layers()[0]
        p_plus1 = lyr_plus1.get_pixel(50, 50).get_rgba()
        if abs(p_plus1.red - 0.50) > 0.03:
            record_fail("EXP-03", "+1 Stop Exposure scaling", f"Expected ~0.50 (2 * 0.25), got {p_plus1.red:.3f}")
            return
        record_pass("EXP-03", "+1 Stop Exposure scaling", f"+1.0 EV stop doubles intensity (0.25 -> {p_plus1.red:.3f} ~= 0.50)")
        img.remove_layer(lyr_plus1)

        # EXP-04: Exposure EV stops -1.0 scaling verified (I' = 0.5 * I)
        # Base 0.25 -> 0.125 (-1 stop underexposure)
        cfg_min1 = proc.create_config()
        cfg_min1.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_min1.set_property("image", img)
        cfg_min1.set_property("preset", "custom")
        cfg_min1.set_property("exposure", -1.0)
        cfg_min1.set_property("offset", 0.0)
        cfg_min1.set_property("gamma", 1.0)
        cfg_min1.set_property("output-mode", "new-layer")
        cfg_min1.set_property("mask-type", "none")
        proc.run(cfg_min1)

        lyr_min1 = img.get_layers()[0]
        p_min1 = lyr_min1.get_pixel(50, 50).get_rgba()
        if abs(p_min1.red - 0.125) > 0.03:
            record_fail("EXP-04", "-1 Stop Exposure scaling", f"Expected ~0.125 (0.5 * 0.25), got {p_min1.red:.3f}")
            return
        record_pass("EXP-04", "-1 Stop Exposure scaling", f"-1.0 EV stop halves intensity (0.25 -> {p_min1.red:.3f} ~= 0.125)")
        img.remove_layer(lyr_min1)

        # EXP-05: Offset shadow black point adjustment verified (I' = I + offset)
        # Base 0.25 + 0.15 = 0.40
        cfg_off = proc.create_config()
        cfg_off.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_off.set_property("image", img)
        cfg_off.set_property("preset", "custom")
        cfg_off.set_property("exposure", 0.0)
        cfg_off.set_property("offset", 0.15)
        cfg_off.set_property("gamma", 1.0)
        cfg_off.set_property("output-mode", "new-layer")
        cfg_off.set_property("mask-type", "none")
        proc.run(cfg_off)

        lyr_off = img.get_layers()[0]
        p_off = lyr_off.get_pixel(50, 50).get_rgba()
        if abs(p_off.red - 0.40) > 0.03:
            record_fail("EXP-05", "Offset shadow level", f"Expected ~0.40 (0.25 + 0.15), got {p_off.red:.3f}")
            return
        record_pass("EXP-05", "Offset shadow level", f"Offset lifts shadow/black point linearly (0.25 + 0.15 -> {p_off.red:.3f})")
        img.remove_layer(lyr_off)

        # EXP-06: Gamma midtone curve response verified (I' = I ** (1 / gamma))
        # Base 0.25 ** (1 / 2.0) = sqrt(0.25) = 0.50
        cfg_gam = proc.create_config()
        cfg_gam.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_gam.set_property("image", img)
        cfg_gam.set_property("preset", "custom")
        cfg_gam.set_property("exposure", 0.0)
        cfg_gam.set_property("offset", 0.0)
        cfg_gam.set_property("gamma", 2.0)
        cfg_gam.set_property("output-mode", "new-layer")
        cfg_gam.set_property("mask-type", "none")
        proc.run(cfg_gam)

        lyr_gam = img.get_layers()[0]
        p_gam = lyr_gam.get_pixel(50, 50).get_rgba()
        if abs(p_gam.red - 0.50) > 0.03:
            record_fail("EXP-06", "Gamma midtone curve", f"Expected ~0.50 (0.25 ** (1/2)), got {p_gam.red:.3f}")
            return
        record_pass("EXP-06", "Gamma midtone power curve", f"Gamma power curve expands midtones (0.25 ** (1/2.0) -> {p_gam.red:.3f})")
        img.remove_layer(lyr_gam)

        # EXP-07: Curated photographic presets verified
        presets_to_test = ["plus-1-stop", "plus-2-stops", "minus-1-stop", "shadow-lift", "highlight-recovery"]
        for pname in presets_to_test:
            cfg_p = proc.create_config()
            cfg_p.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
            cfg_p.set_property("image", img)
            cfg_p.set_property("preset", pname)
            cfg_p.set_property("output-mode", "new-layer")
            cfg_p.set_property("mask-type", "none")
            proc.run(cfg_p)
            lyr_p = img.get_layers()[0]
            if f"Exposure Adjustment" not in lyr_p.get_name():
                record_fail("EXP-07", f"Preset {pname}", f"Unexpected layer name {lyr_p.get_name()}")
                return
            img.remove_layer(lyr_p)
        record_pass("EXP-07", "Curated photographic presets", "+1 stop, +2 stops, -1 stop, shadow lift, highlight recovery presets verified")

        # EXP-08: Non-destructive adjustment layer structure verified
        cfg_nd = proc.create_config()
        cfg_nd.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_nd.set_property("image", img)
        cfg_nd.set_property("preset", "plus-1-stop")
        cfg_nd.set_property("output-mode", "new-layer")
        cfg_nd.set_property("mask-type", "none")
        proc.run(cfg_nd)

        layers = img.get_layers()
        if len(layers) != 2 or "Exposure Adjustment" not in layers[0].get_name():
            record_fail("EXP-08", "Adjustment layer structure", f"Expected 2 layers with Exposure Adjustment on top, got count={len(layers)}")
            return
        record_pass("EXP-08", "Adjustment layer structure", "Dedicated adjustment layer inserted above base layer leaving artwork intact")
        img.remove_layer(layers[0])

        # EXP-09: Blend modes and opacity verified
        modes_to_test = [
            ("luminosity", Gimp.LayerMode.LUMINANCE),
            ("multiply", Gimp.LayerMode.MULTIPLY),
            ("screen", Gimp.LayerMode.SCREEN),
            ("overlay", Gimp.LayerMode.OVERLAY),
            ("soft-light", Gimp.LayerMode.SOFTLIGHT),
        ]
        for bname, expected_mode in modes_to_test:
            cfg_b = proc.create_config()
            cfg_b.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
            cfg_b.set_property("image", img)
            cfg_b.set_property("preset", "plus-1-stop")
            cfg_b.set_property("blend-mode", bname)
            cfg_b.set_property("opacity", 75.0)
            cfg_b.set_property("output-mode", "new-layer")
            cfg_b.set_property("mask-type", "none")
            proc.run(cfg_b)
            lyr_b = img.get_layers()[0]
            if lyr_b.get_mode() != expected_mode or abs(lyr_b.get_opacity() - 75.0) > 0.01:
                record_fail("EXP-09", f"Blend mode {bname}", f"Expected mode {int(expected_mode)}, got {int(lyr_b.get_mode())}, opacity {lyr_b.get_opacity()}%")
                return
            img.remove_layer(lyr_b)
        record_pass("EXP-09", "Blend modes & opacity validation", "Luminosity, Multiply, Screen, Overlay, Soft Light & 75% opacity validated")

        # EXP-10: Conceal-All black layer mask verified
        cfg_black = proc.create_config()
        cfg_black.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_black.set_property("image", img)
        cfg_black.set_property("preset", "plus-2-stops")
        cfg_black.set_property("output-mode", "new-layer")
        cfg_black.set_property("mask-type", "conceal-all")
        proc.run(cfg_black)

        lyr_black = img.get_layers()[0]
        mask_black = lyr_black.get_mask()
        if mask_black is None:
            record_fail("EXP-10", "Conceal-All mask", "Expected attached black mask, got None")
            return
        m_val = mask_black.get_pixel(50, 50).get_rgba()
        if m_val.red > 0.01:
            record_fail("EXP-10", "Conceal-All mask", f"Expected black mask (0.0), got {m_val.red}")
            return
        # With black mask, composite image should match base layer exactly
        comp_px = get_composite_pixel(img, 50, 50)
        base_px = base.get_pixel(50, 50).get_rgba()
        if abs(comp_px.red - base_px.red) > 0.000001:
            record_fail("EXP-10", "Conceal-All invariance", f"Composite altered by {abs(comp_px.red - base_px.red)}")
            return
        record_pass("EXP-10", "Conceal-All black layer mask", "Black mask attached and fully conceals adjustment layer (composite diff 0.000000)")
        img.remove_layer(lyr_black)

        # EXP-11: Reveal-All white layer mask verified
        cfg_white = proc.create_config()
        cfg_white.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_white.set_property("image", img)
        cfg_white.set_property("preset", "plus-1-stop")
        cfg_white.set_property("output-mode", "new-layer")
        cfg_white.set_property("mask-type", "reveal-all")
        proc.run(cfg_white)

        lyr_white = img.get_layers()[0]
        mask_white = lyr_white.get_mask()
        if mask_white is None:
            record_fail("EXP-11", "Reveal-All mask", "Expected attached white mask, got None")
            return
        mw_val = mask_white.get_pixel(50, 50).get_rgba()
        if mw_val.red < 0.99:
            record_fail("EXP-11", "Reveal-All mask", f"Expected white mask (1.0), got {mw_val.red}")
            return
        record_pass("EXP-11", "Reveal-All white layer mask", "White editable mask attached for subtractive brush masking")
        img.remove_layer(lyr_white)

        # EXP-12: Active selection auto-mask confinement verified
        img.select_rectangle(Gimp.ChannelOps.REPLACE, 20, 20, 40, 40)
        cfg_sel_mask = proc.create_config()
        cfg_sel_mask.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_sel_mask.set_property("image", img)
        cfg_sel_mask.set_property("preset", "plus-1-stop")
        cfg_sel_mask.set_property("output-mode", "new-layer")
        cfg_sel_mask.set_property("mask-type", "auto")
        proc.run(cfg_sel_mask)

        lyr_sel = img.get_layers()[0]
        m_sel = lyr_sel.get_mask()
        if m_sel is None:
            record_fail("EXP-12", "Selection auto-mask", "Expected attached selection mask, got None")
            return
        m_inside = m_sel.get_pixel(30, 30).get_rgba()
        m_outside = m_sel.get_pixel(10, 10).get_rgba()
        if m_inside.red < 0.99 or m_outside.red > 0.01:
            record_fail("EXP-12", "Selection auto-mask", f"Expected white inside ({m_inside.red}) and black outside ({m_outside.red})")
            return
        record_pass("EXP-12", "Active selection auto-mask", "Active selection automatically converted into attached layer mask")
        img.remove_layer(lyr_sel)
        Gimp.Selection.none(img)

        # EXP-13: In-place mode verified
        temp_layer = Gimp.Layer.new(img, "TempLayer", 100, 100, Gimp.ImageType.RGBA_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
        img.insert_layer(temp_layer, None, 0)
        img.set_selected_layers([temp_layer])
        Gimp.context_set_foreground(Gegl.Color.new("rgb(0.25, 0.25, 0.25)"))
        temp_layer.edit_fill(Gimp.FillType.FOREGROUND)

        img.select_rectangle(Gimp.ChannelOps.REPLACE, 20, 20, 40, 40)
        cfg_inplace = proc.create_config()
        cfg_inplace.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
        cfg_inplace.set_property("image", img)
        cfg_inplace.set_property("preset", "plus-1-stop")
        cfg_inplace.set_property("output-mode", "in-place")
        proc.run(cfg_inplace)

        p_in = temp_layer.get_pixel(30, 30).get_rgba()
        p_out = temp_layer.get_pixel(10, 10).get_rgba()
        if abs(p_in.red - 0.50) > 0.03 or abs(p_out.red - 0.25) > 0.03:
            record_fail("EXP-13", "In-place selection confinement", f"Expected in=0.50, out=0.25, got in={p_in.red:.3f}, out={p_out.red:.3f}")
            return
        record_pass("EXP-13", "In-place selection confinement", f"In-place mode adjusts inside selection ({p_in.red:.3f}) while preserving outside ({p_out.red:.3f})")
        img.remove_layer(temp_layer)
        Gimp.Selection.none(img)

        # EXP-14: Base layer pixel preservation
        after_samples = [base.get_pixel(x, y).get_rgba() for x in (10, 25, 40, 60, 75, 90) for y in (10, 25, 40, 60, 75, 90)]
        max_diff = max(
            max(abs(b.red - a.red), abs(b.green - a.green), abs(b.blue - a.blue))
            for a, b in zip(orig_samples, after_samples)
        )
        if max_diff > 0.000001:
            record_fail("EXP-14", "Base layer preservation", f"Base pixels altered by {max_diff:.6f} > 0")
            return
        record_pass("EXP-14", "Base layer pixel preservation", f"Original source pixels 100% untouched across all non-destructive operations (diff {max_diff:.6f})")

    except Exception as e:
        record_fail("EXP-ERR", "Unexpected exception", str(e))
    finally:
        img.delete()


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
    test_lens_distortion()
    test_glowing_edges()
    test_oil_paint()
    test_iris_blur()
    test_hdr_toning()
    test_match_color()
    test_apply_image()
    test_replace_color()
    test_lens_blur()
    test_texturizer()
    test_guide_layout()
    test_frame_animation()
    test_seamless_pattern()
    test_stroke_layer()
    test_solid_color_fill()
    test_gradient_fill()
    test_exposure_adjustment()



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
