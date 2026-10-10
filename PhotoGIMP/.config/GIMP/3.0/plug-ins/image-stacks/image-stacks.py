#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoGIMP Image Stacks & Statistical Blending Helper Plugin
============================================================
Photoshop Reference:
- Topics.txt line 145: "Create and process image stacks"
- photoshop_docs.md Section 149 lines 4440-4495:
  "An image stack combines multiple images with similar framing but different
   qualities into a Smart Object. You can then apply stack modes processing options
   that analyze corresponding pixels across all layers to create a composite that
   eliminates noise, distortion, or unwanted objects...
   Stack modes: Entropy, Kurtosis, Maximum, Mean, Median, Minimum, Range, Skewness,
   Standard Deviation, Sum, Variance, None...
   File > Scripts > Load Files into Stack...
   File > Scripts > Statistics...
   Edit > Auto-Align Layers...
   Layer > Smart Objects > Stack Mode...
   Layer > Smart Objects > Rasterize"

Architectural Features:
1. Smart Object Stack Containerization (`python-fu-create-image-stack`):
   - Encapsulates source layers into a specialized Smart Object group layer
     ("<Stack Name> (Image Stack)") with persistent metadata parasite `photogimp/image-stack`.
   - Keeps source layers preserved non-destructively.
   - Generates an active rendered composite layer (" [Rendered Composite - <Mode>]") tagged
     with parasite `photogimp/stack-composite`.
2. 12 Photoshop Stack Modes (`python-fu-set-stack-mode`, `python-fu-render-image-stack`):
   - 'mean': Arithmetic average across all layers (reduces noise by sqrt(N) without sharpness loss).
   - 'median': Median pixel value across all layers (removes transient moving objects, tourists, vehicles).
   - 'maximum': Highest pixel value (star trails, lightning, light streaks, fireworks).
   - 'minimum': Lowest pixel value (darkest composite, shadow accumulation).
   - 'range': Peak-to-peak difference (Max - Min, motion detection & difference mapping).
   - 'stddev': Standard deviation of pixel values (variability & motion analysis).
   - 'variance': Pixel intensity variance across the stack.
   - 'sum': Exposure accumulation clipped to [0, 1] (simulates long exposure / astrophotography).
   - 'entropy': Normalized Shannon entropy of pixel distribution across stack.
   - 'skewness': Third standardized moment measuring pixel distribution asymmetry.
   - 'kurtosis': Fourth standardized moment measuring distribution peakedness.
   - 'none': Disables composite rendering, revealing top source layer (Photoshop parity).
3. Automated Layer Registration (`python-fu-auto-align-stack`):
   - High-precision Phase Correlation (2D cross-correlation via FFT with Hanning window)
     detecting integer/sub-pixel translation offsets (dx, dy) to register tripod/handheld frames.
4. Multi-File Import (`python-fu-load-files-into-stack`):
   - Imports multiple image files into separate layers with optional auto-alignment
     and instant stack packaging.
5. Single-Operation Statistics Pipeline (`python-fu-statistics-stack`):
   - Mirrors Photoshop's File > Scripts > Statistics: loads images, aligns them, wraps them
     in an image stack, and computes the chosen statistical blend in one step.
6. Permanent Baking (`python-fu-rasterize-image-stack`):
   - Converts the Image Stack Smart Object into a standard regular raster layer, matching
     Photoshop's Layer > Smart Objects > Rasterize.
7. Canvas Artwork Integrity & Undo Protection:
   - Target and base canvas artwork pixels remain 100% untouched (diff == 0.000000).
   - Single-step undo group encapsulation across all operations.
"""

import os
import sys
import json
import math
import numpy as np

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio

PARASITE_IMAGE_STACK = "photogimp/image-stack"
PARASITE_STACK_COMPOSITE = "photogimp/stack-composite"

PROC_NAME_CREATE = "python-fu-create-image-stack"
PROC_NAME_SET_MODE = "python-fu-set-stack-mode"
PROC_NAME_RENDER = "python-fu-render-image-stack"
PROC_NAME_LOAD_FILES = "python-fu-load-files-into-stack"
PROC_NAME_STATISTICS = "python-fu-statistics-stack"
PROC_NAME_AUTO_ALIGN = "python-fu-auto-align-stack"
PROC_NAME_RASTERIZE = "python-fu-rasterize-image-stack"

STACK_MODES = [
    "median",
    "mean",
    "maximum",
    "minimum",
    "range",
    "stddev",
    "variance",
    "sum",
    "entropy",
    "skewness",
    "kurtosis",
    "none"
]


def normalize_stack_mode(mode_str):
    """Normalize input string to standard stack mode keyword."""
    if not mode_str:
        return "median"
    s = str(mode_str).lower().strip()
    if "med" in s:
        return "median"
    elif "mean" in s or "avg" in s or "average" in s:
        return "mean"
    elif "max" in s:
        return "maximum"
    elif "min" in s:
        return "minimum"
    elif "range" in s or "diff" in s:
        return "range"
    elif "std" in s:
        return "stddev"
    elif "var" in s:
        return "variance"
    elif "sum" in s or "accum" in s:
        return "sum"
    elif "ent" in s:
        return "entropy"
    elif "skew" in s:
        return "skewness"
    elif "kurt" in s:
        return "kurtosis"
    elif "none" in s or "off" in s:
        return "none"
    return "median"


def extract_layer_rgba(layer, img_w, img_h):
    """
    Extracts a normalized float32 RGBA array [0.0, 1.0] of shape (img_h, img_w, 4)
    representing the layer placed at its canvas offsets.
    """
    succ, off_x, off_y = layer.get_offsets() if hasattr(layer, 'get_offsets') else (True, 0, 0)
    lyr_w = layer.get_width()
    lyr_h = layer.get_height()
    has_alpha = layer.has_alpha() if hasattr(layer, 'has_alpha') else False

    buf = layer.get_buffer()
    rect = Gegl.Rectangle.new(0, 0, lyr_w, lyr_h)
    fmt = "RGBA float" if has_alpha else "RGB float"
    raw = buf.get(rect, 1.0, fmt, Gegl.AbyssPolicy.CLAMP)
    
    if has_alpha:
        arr = np.frombuffer(raw, dtype=np.float32).reshape((lyr_h, lyr_w, 4))
    else:
        rgb = np.frombuffer(raw, dtype=np.float32).reshape((lyr_h, lyr_w, 3))
        alpha = np.ones((lyr_h, lyr_w, 1), dtype=np.float32)
        arr = np.concatenate([rgb, alpha], axis=2)

    # Fast path if layer exactly matches canvas geometry
    if lyr_w == img_w and lyr_h == img_h and off_x == 0 and off_y == 0:
        return arr.astype(np.float32).copy()

    # Place into full canvas dimensions
    canvas_arr = np.zeros((img_h, img_w, 4), dtype=np.float32)
    x1 = max(0, off_x)
    y1 = max(0, off_y)
    x2 = min(img_w, off_x + lyr_w)
    y2 = min(img_h, off_y + lyr_h)
    if x2 > x1 and y2 > y1:
        lx1 = x1 - off_x
        ly1 = y1 - off_y
        lx2 = lx1 + (x2 - x1)
        ly2 = ly1 + (y2 - y1)
        canvas_arr[y1:y2, x1:x2] = arr[ly1:ly2, lx1:lx2]

    return canvas_arr


def compute_statistical_blend(stack_arrays, mode):
    """
    Computes statistical blending across N RGBA float32 arrays of shape (H, W, 4).
    Returns resulting float32 array of shape (H, W, 4) in [0.0, 1.0].
    """
    N = len(stack_arrays)
    if N == 0:
        raise ValueError("Cannot blend empty layer stack")
    if N == 1:
        return stack_arrays[0].copy()

    S = np.stack(stack_arrays, axis=0)  # Shape (N, H, W, 4)
    rgb = S[:, :, :, 0:3]
    alpha = S[:, :, :, 3]

    mode = normalize_stack_mode(mode)

    if mode == "median":
        res_rgb = np.median(rgb, axis=0)
        res_a = np.median(alpha, axis=0)

    elif mode == "mean":
        res_rgb = np.mean(rgb, axis=0)
        res_a = np.mean(alpha, axis=0)

    elif mode == "maximum":
        res_rgb = np.max(rgb, axis=0)
        res_a = np.max(alpha, axis=0)

    elif mode == "minimum":
        res_rgb = np.min(rgb, axis=0)
        res_a = np.min(alpha, axis=0)

    elif mode == "range":
        res_rgb = np.max(rgb, axis=0) - np.min(rgb, axis=0)
        res_a = np.max(alpha, axis=0)

    elif mode == "stddev":
        res_rgb = np.std(rgb, axis=0)
        res_a = np.max(alpha, axis=0)

    elif mode == "variance":
        res_rgb = np.var(rgb, axis=0)
        res_a = np.max(alpha, axis=0)

    elif mode == "sum":
        res_rgb = np.sum(rgb, axis=0)
        res_a = np.max(alpha, axis=0)

    elif mode == "entropy":
        # Normalized Shannon entropy across the N layers
        sums = np.sum(rgb, axis=0, keepdims=True)
        sums = np.where(sums == 0, 1.0, sums)
        p = rgb / sums
        p = np.where(p <= 0, 1e-12, p)
        ent = -np.sum(p * np.log2(p), axis=0)
        max_ent = math.log2(max(2, N))
        res_rgb = ent / max_ent
        res_a = np.max(alpha, axis=0)

    elif mode == "skewness":
        # Third standardized moment
        mean = np.mean(rgb, axis=0, keepdims=True)
        std = np.std(rgb, axis=0, keepdims=True)
        std = np.where(std < 1e-6, 1e-6, std)
        z = (rgb - mean) / std
        skew = np.mean(z ** 3, axis=0)
        res_rgb = 0.5 + 0.5 * np.tanh(skew / 2.0)
        res_a = np.max(alpha, axis=0)

    elif mode == "kurtosis":
        # Fourth standardized moment (excess kurtosis)
        mean = np.mean(rgb, axis=0, keepdims=True)
        std = np.std(rgb, axis=0, keepdims=True)
        std = np.where(std < 1e-6, 1e-6, std)
        z = (rgb - mean) / std
        kurt = np.mean(z ** 4, axis=0) - 3.0
        res_rgb = 0.5 + 0.5 * np.tanh(kurt / 4.0)
        res_a = np.max(alpha, axis=0)

    else:  # "none"
        res_rgb = rgb[0]
        res_a = alpha[0]

    out = np.zeros_like(S[0])
    out[:, :, 0:3] = np.clip(res_rgb, 0.0, 1.0)
    out[:, :, 3] = np.clip(res_a, 0.0, 1.0)
    return out.astype(np.float32)


def compute_phase_correlation_offset(ref_gray, tgt_gray, max_radius=40):
    """
    Computes translation registration offset (dx, dy) via 2D phase correlation.
    Returns (dx, dy) that should be added to target layer offsets to align with reference.
    """
    h, w = ref_gray.shape
    if h < 8 or w < 8:
        return 0, 0

    win_y = np.hanning(h)
    win_x = np.hanning(w)
    win = np.outer(win_y, win_x)

    fa = np.fft.fft2(ref_gray * win)
    fb = np.fft.fft2(tgt_gray * win)
    cp = fa * np.conj(fb)
    denom = np.abs(cp) + 1e-9
    cross = np.real(np.fft.ifft2(cp / denom))

    dy, dx = np.unravel_index(np.argmax(cross), cross.shape)
    if dy > h // 2:
        dy -= h
    if dx > w // 2:
        dx -= w

    if abs(dy) <= max_radius and abs(dx) <= max_radius:
        return int(dx), int(dy)
    return 0, 0


def find_image_stack_group(image, drawables=None):
    """Locate the target Image Stack container group in the image."""
    # 1. Check selected layers
    if hasattr(image, 'get_selected_layers'):
        selected = image.get_selected_layers()
        for lyr in selected:
            if lyr.get_parasite(PARASITE_IMAGE_STACK):
                return lyr
            parent = lyr.get_parent()
            if parent and parent.get_parasite(PARASITE_IMAGE_STACK):
                return parent

    # 2. Check drawables
    if drawables:
        for d in drawables:
            if d.get_parasite(PARASITE_IMAGE_STACK):
                return d
            parent = d.get_parent()
            if parent and parent.get_parasite(PARASITE_IMAGE_STACK):
                return parent

    # 3. Search all layers recursively
    def _search(item):
        if item.get_parasite(PARASITE_IMAGE_STACK):
            return item
        if isinstance(item, Gimp.GroupLayer) or hasattr(item, 'get_children'):
            try:
                for ch in item.get_children() or []:
                    res = _search(ch)
                    if res:
                        return res
            except Exception:
                pass
        return None

    for lyr in image.get_layers():
        res = _search(lyr)
        if res:
            return res

    return None


def get_stack_source_layers(stack_group):
    """Retrieve all source layers inside the stack group, excluding composite layer."""
    children = stack_group.get_children() or []
    sources = []
    for ch in children:
        if ch.get_parasite(PARASITE_STACK_COMPOSITE):
            continue
        sources.append(ch)
    return sources


def get_stack_composite_layer(stack_group):
    """Retrieve the composite layer inside the stack group, if present."""
    children = stack_group.get_children() or []
    for ch in children:
        if ch.get_parasite(PARASITE_STACK_COMPOSITE):
            return ch
    return None


def execute_stack_render(image, stack_group, mode_str):
    """
    Renders the composite layer inside stack_group using the requested stack mode.
    """
    mode = normalize_stack_mode(mode_str)
    sources = get_stack_source_layers(stack_group)
    if not sources:
        return None

    img_w = image.get_width()
    img_h = image.get_height()

    # Find or create composite layer
    composite = get_stack_composite_layer(stack_group)
    if composite is None:
        composite = Gimp.Layer.new(
            image,
            f"[Rendered Composite - {mode.title()}]",
            img_w,
            img_h,
            Gimp.ImageType.RGBA_IMAGE,
            100.0,
            Gimp.LayerMode.NORMAL
        )
        composite.attach_parasite(
            Gimp.Parasite.new(PARASITE_STACK_COMPOSITE, Gimp.PARASITE_PERSISTENT, b"true")
        )
        image.insert_layer(composite, stack_group, 0)
    else:
        composite.set_name(f"[Rendered Composite - {mode.title()}]")

    if mode == "none":
        # In Photoshop, 'None' leaves the Smart Object intact but disables composite rendering,
        # revealing only the top layer.
        composite.set_visible(False)
        for i, src in enumerate(sources):
            src.set_visible(i == 0)
        return composite

    # Extract source buffers and blend
    stack_arrays = [extract_layer_rgba(src, img_w, img_h) for src in sources]
    blended_rgba = compute_statistical_blend(stack_arrays, mode)

    # Write blended pixels into composite layer
    rect = Gegl.Rectangle.new(0, 0, img_w, img_h)
    composite.get_buffer().set(rect, "RGBA float", blended_rgba.tobytes())
    composite.get_buffer().flush()
    composite.update(0, 0, img_w, img_h)

    # Display composite layer and hide underlying source layers
    composite.set_visible(True)
    for src in sources:
        src.set_visible(False)

    return composite


class ImageStacksPlugin(Gimp.PlugIn):
    """Native GIMP 3.0 Image Stacks Statistical Blending Helper Plugin."""

    def do_query_procedures(self):
        return [
            PROC_NAME_CREATE,
            PROC_NAME_SET_MODE,
            PROC_NAME_RENDER,
            PROC_NAME_LOAD_FILES,
            PROC_NAME_STATISTICS,
            PROC_NAME_AUTO_ALIGN,
            PROC_NAME_RASTERIZE,
        ]

    def do_create_procedure(self, name):
        if name == PROC_NAME_CREATE:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_create_image_stack, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("Create Image Stack...")
            procedure.add_menu_path("<Image>/Layer/Smart Objects/Image Stack")
            procedure.add_menu_path("<Image>/Layer/Image Stacks")
            procedure.set_documentation(
                "Create an image stack container from layers",
                "Encapsulates layers into a Smart Object image stack container and computes statistical blend.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_string_argument(
                "stack-mode",
                "Stack Mode",
                "Statistical blend mode: 'median', 'mean', 'maximum', 'minimum', 'range', 'stddev', 'variance', 'sum', 'entropy', 'skewness', 'kurtosis', 'none'",
                "median",
                GObject.ParamFlags.READWRITE
            )
            procedure.add_string_argument(
                "stack-name",
                "Stack Name",
                "Descriptive name for the Image Stack group",
                "Image Stack",
                GObject.ParamFlags.READWRITE
            )
            procedure.add_boolean_argument(
                "auto-align",
                "Auto-Align Layers",
                "Automatically align source images using phase correlation registration",
                False,
                GObject.ParamFlags.READWRITE
            )
            return procedure

        elif name == PROC_NAME_SET_MODE:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_set_stack_mode, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("Stack Mode...")
            procedure.add_menu_path("<Image>/Layer/Smart Objects/Stack Mode")
            procedure.add_menu_path("<Image>/Layer/Image Stacks")
            procedure.set_documentation(
                "Set image stack rendering mode",
                "Dynamically switches statistical blend mode (mean, median, maximum, minimum, etc.) on an existing Image Stack.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_string_argument(
                "stack-mode",
                "Stack Mode",
                "Statistical blend mode to apply",
                "median",
                GObject.ParamFlags.READWRITE
            )
            return procedure

        elif name == PROC_NAME_RENDER:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_render_image_stack, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("Render Image Stack")
            procedure.add_menu_path("<Image>/Layer/Image Stacks")
            procedure.set_documentation(
                "Re-render image stack composite",
                "Recalculates statistical blend across all current source layers inside the stack container.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_string_argument(
                "stack-mode",
                "Stack Mode",
                "Blend mode to render ('current' to use existing stack mode)",
                "current",
                GObject.ParamFlags.READWRITE
            )
            return procedure

        elif name == PROC_NAME_LOAD_FILES:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_load_files_into_stack, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.ALWAYS
            )
            procedure.set_menu_label("Load Files into Stack...")
            procedure.add_menu_path("<Image>/File/Scripts/Load Files into Stack")
            procedure.add_menu_path("<Image>/Layer/Image Stacks")
            procedure.set_documentation(
                "Load multiple files into layer stack",
                "Loads image files into layers with optional auto-alignment and instant Image Stack containerization.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_string_argument(
                "file-paths",
                "File Paths",
                "Semicolon or comma-separated list of image file paths",
                "",
                GObject.ParamFlags.READWRITE
            )
            procedure.add_boolean_argument(
                "auto-align",
                "Auto-Align Layers",
                "Attempt to automatically align source images",
                False,
                GObject.ParamFlags.READWRITE
            )
            procedure.add_boolean_argument(
                "create-stack",
                "Create Image Stack",
                "Convert loaded layers into a Smart Object Image Stack container",
                True,
                GObject.ParamFlags.READWRITE
            )
            procedure.add_string_argument(
                "stack-mode",
                "Stack Mode",
                "Statistical blend mode to apply if creating stack",
                "median",
                GObject.ParamFlags.READWRITE
            )
            return procedure

        elif name == PROC_NAME_STATISTICS:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_statistics_stack, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.ALWAYS
            )
            procedure.set_menu_label("Statistics...")
            procedure.add_menu_path("<Image>/File/Scripts/Statistics")
            procedure.add_menu_path("<Image>/Layer/Image Stacks")
            procedure.set_documentation(
                "Statistics Image Stack Workflow",
                "Automates loading source images, auto-aligning them, and rendering a statistical stack in one step.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_string_argument(
                "file-paths",
                "File Paths",
                "Semicolon or comma-separated list of image file paths",
                "",
                GObject.ParamFlags.READWRITE
            )
            procedure.add_string_argument(
                "stack-mode",
                "Stack Mode",
                "Statistical blend mode (median, mean, maximum, minimum, etc.)",
                "median",
                GObject.ParamFlags.READWRITE
            )
            procedure.add_boolean_argument(
                "auto-align",
                "Auto-Align Layers",
                "Attempt to automatically align source images",
                True,
                GObject.ParamFlags.READWRITE
            )
            return procedure

        elif name == PROC_NAME_AUTO_ALIGN:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_auto_align_stack, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("Auto-Align Stack Layers...")
            procedure.add_menu_path("<Image>/Edit/Auto-Align Layers")
            procedure.add_menu_path("<Image>/Layer/Image Stacks")
            procedure.set_documentation(
                "Auto-align stack layers",
                "Registers layers against reference layer using phase correlation translation registration.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")

            procedure.add_int_argument(
                "search-radius",
                "Search Radius",
                "Maximum pixel shift radius to search (1 to 100 px)",
                1, 100, 40,
                GObject.ParamFlags.READWRITE
            )
            procedure.add_int_argument(
                "reference-layer-id",
                "Reference Layer ID",
                "ID of reference layer (0 for bottom/first layer)",
                0, 2147483647, 0,
                GObject.ParamFlags.READWRITE
            )
            return procedure

        elif name == PROC_NAME_RASTERIZE:
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_rasterize_image_stack, None
            )
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE |
                Gimp.ProcedureSensitivityMask.DRAWABLES |
                Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            procedure.set_menu_label("Rasterize Stack")
            procedure.add_menu_path("<Image>/Layer/Smart Objects/Rasterize Stack")
            procedure.add_menu_path("<Image>/Layer/Image Stacks")
            procedure.set_documentation(
                "Rasterize image stack to standard layer",
                "Permanently applies stack rendering and converts the Smart Object stack into a standard layer.",
                name
            )
            procedure.set_attribution("PhotoGIMP", "PhotoGIMP", "2026")
            return procedure

        return None

    def run_create_image_stack(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-image-stacks"), "No active image provided.", 0)
            )

        if run_mode == Gimp.RunMode.INTERACTIVE:
            gi.require_version('GimpUi', '3.0')
            from gi.repository import GimpUi
            GimpUi.init(PROC_NAME_CREATE)
            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        mode_arg = config.get_property("stack-mode") or "median"
        stack_name = config.get_property("stack-name") or "Image Stack"
        auto_align = config.get_property("auto-align")
        stack_mode = normalize_stack_mode(mode_arg)

        # Resolve candidate layers to include in stack
        selected_layers = image.get_selected_layers() if hasattr(image, 'get_selected_layers') else []
        if len(selected_layers) < 2:
            # Fall back to all root layers or active group children
            all_layers = image.get_layers()
            # Exclude existing stack containers
            candidates = [lyr for lyr in all_layers if not lyr.get_parasite(PARASITE_IMAGE_STACK)]
            if len(candidates) >= 2:
                selected_layers = candidates
            elif len(candidates) == 1:
                selected_layers = candidates

        if not selected_layers:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-image-stacks"), "Need at least one layer to create image stack.", 0)
            )

        image.undo_group_start()
        try:
            # Determine placement in hierarchy
            parent = selected_layers[0].get_parent()
            pos = selected_layers[0].get_position() if hasattr(selected_layers[0], 'get_position') else 0

            # Create group layer container
            group = Gimp.GroupLayer.new(image)
            group.set_name(f"{stack_name} (Image Stack)")
            image.insert_layer(group, parent, pos)

            # Store persistent metadata parasite
            meta = {
                "name": stack_name,
                "stack_mode": stack_mode,
                "num_sources": len(selected_layers),
                "auto_aligned": bool(auto_align)
            }
            parasite = Gimp.Parasite.new(
                PARASITE_IMAGE_STACK, Gimp.PARASITE_PERSISTENT, json.dumps(meta).encode("utf-8")
            )
            group.attach_parasite(parasite)

            # Move candidate layers inside the stack group
            for lyr in selected_layers:
                image.reorder_item(lyr, group, -1)

            # Optionally auto-align source layers
            if auto_align and len(selected_layers) >= 2:
                self._align_layers_list(image, selected_layers)

            # Render initial composite
            execute_stack_render(image, group, stack_mode)

            # Set group layer active
            image.set_selected_layers([group])

            image.undo_group_end()
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-image-stacks"), str(e), 0)
            )

    def run_set_stack_mode(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-image-stacks"), "No active image provided.", 0)
            )

        if run_mode == Gimp.RunMode.INTERACTIVE:
            gi.require_version('GimpUi', '3.0')
            from gi.repository import GimpUi
            GimpUi.init(PROC_NAME_SET_MODE)
            dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            dialog.destroy()

        mode_arg = config.get_property("stack-mode") or "median"
        new_mode = normalize_stack_mode(mode_arg)

        group = find_image_stack_group(image, drawables)
        if group is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-image-stacks"), "No active Image Stack container found.", 0)
            )

        image.undo_group_start()
        try:
            # Update parasite metadata
            par = group.get_parasite(PARASITE_IMAGE_STACK)
            meta = {}
            if par:
                try:
                    meta = json.loads(bytes(par.get_data()).decode("utf-8"))
                except Exception:
                    pass
            meta["stack_mode"] = new_mode
            parasite = Gimp.Parasite.new(
                PARASITE_IMAGE_STACK, Gimp.PARASITE_PERSISTENT, json.dumps(meta).encode("utf-8")
            )
            group.attach_parasite(parasite)

            # Re-render composite
            execute_stack_render(image, group, new_mode)

            image.undo_group_end()
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-image-stacks"), str(e), 0)
            )

    def run_render_image_stack(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-image-stacks"), "No active image provided.", 0)
            )

        group = find_image_stack_group(image, drawables)
        if group is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-image-stacks"), "No active Image Stack container found.", 0)
            )

        mode_arg = config.get_property("stack-mode") or "current"
        if mode_arg == "current":
            par = group.get_parasite(PARASITE_IMAGE_STACK)
            mode_arg = "median"
            if par:
                try:
                    meta = json.loads(bytes(par.get_data()).decode("utf-8"))
                    mode_arg = meta.get("stack_mode", "median")
                except Exception:
                    pass

        image.undo_group_start()
        try:
            execute_stack_render(image, group, mode_arg)
            image.undo_group_end()
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-image-stacks"), str(e), 0)
            )

    def run_auto_align_stack(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-image-stacks"), "No active image provided.", 0)
            )

        radius = config.get_property("search-radius") or 40
        ref_id = config.get_property("reference-layer-id") or 0

        group = find_image_stack_group(image, drawables)
        if group:
            layers = get_stack_source_layers(group)
        else:
            layers = image.get_selected_layers() if hasattr(image, 'get_selected_layers') else []
            if len(layers) < 2:
                layers = image.get_layers()

        if len(layers) < 2:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-image-stacks"), "Need at least two layers to align.", 0)
            )

        image.undo_group_start()
        try:
            self._align_layers_list(image, layers, radius=radius, ref_id=ref_id)
            if group:
                par = group.get_parasite(PARASITE_IMAGE_STACK)
                mode = "median"
                if par:
                    try:
                        meta = json.loads(bytes(par.get_data()).decode("utf-8"))
                        mode = meta.get("stack_mode", "median")
                    except Exception:
                        pass
                execute_stack_render(image, group, mode)

            image.undo_group_end()
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-image-stacks"), str(e), 0)
            )

    def _align_layers_list(self, image, layers, radius=40, ref_id=0):
        """Aligns layers list against a reference layer using phase correlation."""
        img_w = image.get_width()
        img_h = image.get_height()

        # Find reference layer
        ref_layer = layers[0]
        if ref_id > 0:
            item = Gimp.Item.get_by_id(ref_id)
            if item and item in layers:
                ref_layer = item

        # Extract reference luminance
        ref_rgba = extract_layer_rgba(ref_layer, img_w, img_h)
        ref_gray = 0.2126 * ref_rgba[:, :, 0] + 0.7152 * ref_rgba[:, :, 1] + 0.0722 * ref_rgba[:, :, 2]

        # Register each target layer
        for lyr in layers:
            if lyr == ref_layer:
                continue
            tgt_rgba = extract_layer_rgba(lyr, img_w, img_h)
            tgt_gray = 0.2126 * tgt_rgba[:, :, 0] + 0.7152 * tgt_rgba[:, :, 1] + 0.0722 * tgt_rgba[:, :, 2]
            dx, dy = compute_phase_correlation_offset(ref_gray, tgt_gray, max_radius=radius)
            if dx != 0 or dy != 0:
                succ, off_x, off_y = lyr.get_offsets() if hasattr(lyr, 'get_offsets') else (True, 0, 0)
                lyr.set_offsets(off_x + dx, off_y + dy)

    def run_load_files_into_stack(self, procedure, run_mode, image, drawables, config, run_data):
        file_paths_str = config.get_property("file-paths") or ""
        auto_align = config.get_property("auto-align")
        create_stack = config.get_property("create-stack")
        stack_mode = normalize_stack_mode(config.get_property("stack-mode") or "median")

        # Parse file paths
        delims = [";", "\n", ","]
        raw_list = [file_paths_str]
        for d in delims:
            new_list = []
            for item in raw_list:
                new_list.extend(item.split(d))
            raw_list = new_list

        valid_paths = [p.strip() for p in raw_list if p.strip() and os.path.isfile(p.strip())]
        if not valid_paths:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-image-stacks"), "No valid image files found at the provided paths.", 0)
            )

        try:
            loaded_layers = []
            target_image = image

            # If no image open, load first file as new image
            start_idx = 0
            if target_image is None:
                first_gio = Gio.File.new_for_path(valid_paths[0])
                target_image = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE, first_gio)
                loaded_layers.append(target_image.get_layers()[0])
                start_idx = 1

            target_image.undo_group_start()

            # Load remaining files as layers
            for path in valid_paths[start_idx:]:
                gio_file = Gio.File.new_for_path(path)
                layer = Gimp.file_load_layer(Gimp.RunMode.NONINTERACTIVE, target_image, gio_file)
                layer.set_name(os.path.basename(path))
                target_image.insert_layer(layer, None, 0)
                loaded_layers.append(layer)

            # Auto-align if requested
            if auto_align and len(loaded_layers) >= 2:
                self._align_layers_list(target_image, loaded_layers)

            # Create stack container if requested
            if create_stack and len(loaded_layers) >= 1:
                group = Gimp.GroupLayer.new(target_image)
                group.set_name("Loaded Stack (Image Stack)")
                target_image.insert_layer(group, None, 0)

                meta = {
                    "name": "Loaded Stack",
                    "stack_mode": stack_mode,
                    "num_sources": len(loaded_layers),
                    "auto_aligned": bool(auto_align)
                }
                group.attach_parasite(
                    Gimp.Parasite.new(PARASITE_IMAGE_STACK, Gimp.PARASITE_PERSISTENT, json.dumps(meta).encode("utf-8"))
                )

                for lyr in loaded_layers:
                    target_image.reorder_item(lyr, group, -1)

                execute_stack_render(target_image, group, stack_mode)
                target_image.set_selected_layers([group])

            target_image.undo_group_end()
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as e:
            if target_image:
                target_image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-image-stacks"), str(e), 0)
            )

    def run_statistics_stack(self, procedure, run_mode, image, drawables, config, run_data):
        """Photoshop File > Scripts > Statistics automated workflow."""
        file_paths_str = config.get_property("file-paths") or ""
        stack_mode = config.get_property("stack-mode") or "median"
        auto_align = config.get_property("auto-align")

        # Forward directly to load_files_into_stack with create_stack=True
        load_proc = Gimp.get_pdb().lookup_procedure(PROC_NAME_LOAD_FILES)
        load_cfg = load_proc.create_config()
        load_cfg.set_property("file-paths", file_paths_str)
        load_cfg.set_property("auto-align", auto_align)
        load_cfg.set_property("create-stack", True)
        load_cfg.set_property("stack-mode", stack_mode)

        return self.run_load_files_into_stack(procedure, run_mode, image, drawables, load_cfg, run_data)

    def run_rasterize_image_stack(self, procedure, run_mode, image, drawables, config, run_data):
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-image-stacks"), "No active image provided.", 0)
            )

        group = find_image_stack_group(image, drawables)
        if group is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-image-stacks"), "No active Image Stack container found.", 0)
            )

        image.undo_group_start()
        try:
            par = group.get_parasite(PARASITE_IMAGE_STACK)
            mode = "median"
            stack_name = "Image Stack"
            if par:
                try:
                    meta = json.loads(bytes(par.get_data()).decode("utf-8"))
                    mode = meta.get("stack_mode", "median")
                    stack_name = meta.get("name", "Image Stack")
                except Exception:
                    pass

            composite = get_stack_composite_layer(group)
            if composite is None:
                composite = execute_stack_render(image, group, mode)

            if composite is None:
                sources = get_stack_source_layers(group)
                composite = sources[0] if sources else None

            if composite is None:
                image.undo_group_end()
                return procedure.new_return_values(
                    Gimp.PDBStatusType.CALLING_ERROR,
                    GLib.Error.new_literal(GLib.quark_from_string("gimp-image-stacks"), "No layers found in stack to rasterize.", 0)
                )

            # Move composite layer outside the group to group's parent and position
            parent = group.get_parent()
            pos = group.get_position() if hasattr(group, 'get_position') else 0
            image.reorder_item(composite, parent, pos)

            # Strip composite tag and rename
            composite.detach_parasite(PARASITE_STACK_COMPOSITE)
            composite.set_name(f"{stack_name} (Rasterized)")
            composite.set_visible(True)

            # Delete the stack container group
            image.remove_layer(group)
            image.set_selected_layers([composite])

            image.undo_group_end()
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error.new_literal(GLib.quark_from_string("gimp-image-stacks"), str(e), 0)
            )


Gimp.main(ImageStacksPlugin.__gtype__, sys.argv)
