# Photoshop Feature Matrix for Linux Photo Editor (GIMP 3.x / PhotoGIMP)

This document is the authoritative mapping between Adobe Photoshop features (from `Topics.txt` and `photoshop_docs.md`) and GIMP / PhotoGIMP equivalents, real capability gaps, and implementation status.

---

## 1. Professional Retouching & Workflow Extensions (Custom GIMP 3.x Plugins)

### Feature: Frequency Separation
- **Source topic**: Retouch and correct - Retouch and repair images / Frequency Separation
- **Photoshop behavior**: Splits an image into a Low Frequency layer (color and tone via Gaussian Blur) and a High Frequency layer (fine texture via High Pass or Subtract math with Linear Light blend mode). Allows independent retouching of skin blemishes/textures without altering skin tone, and blending colors without smoothing pores.
- **GIMP equivalent**: Implemented via custom Python 3 plugin `python-fu-frequency-separation` in `<Image>/Filters/Retouching/Frequency Separation...`.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/frequency-separation/frequency-separation.py`.
- **Current capability**: Automated one-click creation of `Frequency Separation` layer group containing `Low Frequency (Color & Tone)` (Gaussian blur) and `High Frequency (Texture)` (High-pass with Grain Merge blend mode).
- **Gap**: None.
- **Dependencies**: Python 3 (`gi.repository.Gimp`, `gi.repository.Gegl`).
- **Implementation priority**: High (Phase 6).
- **Verification strategy**: `verify_config.py` plugin check + automated headless GIMP test creating Low/High frequency layer group on test image and asserting layer structure.
- **Status**: Implemented & Verified (Iteration 8).

---

### Feature: Luminosity Masks Generator
- **Source topic**: Make selections - Select areas based on color or tone / Channels panel
- **Photoshop behavior**: Generates 9 precision channel masks (Lights 1-3, Darks 1-3, Midtones 1-3) based on pixel luminance, allowing targeted exposure and tonal adjustments without manual edge painting.
- **GIMP equivalent**: Implemented via custom Python 3 plugin `python-fu-luminosity-masks` in `<Image>/Select/Luminosity Masks...`.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/luminosity-masks/luminosity-masks.py`.
- **Current capability**: Automated one-click generation of all 9 tonal channels: Lights 1/2/3, Darks 1/2/3, Midtones 1/2/3. Each channel uses iterative GEGL buffer copy + selection-intersection narrowing for progressively focused tonal ranges.
- **Gap**: None.
- **Dependencies**: Python 3 (`gi.repository.Gimp`, `gi.repository.Gegl`), `Gimp.Layer.new_from_drawable`, `Gimp.Channel.combine_masks`.
- **Implementation priority**: High (Phase 7).
- **Verification strategy**: Headless GIMP test confirms 9 channels created with correct names and verifies pixel luminance mathematics on test splits (exit 0).
- **Verification evidence** (Iteration 9):
  1. Headless Script-Fu: `gimp --no-interface --batch '...' --quit` → `Channel count: 9 / Midtones 3 / Midtones 2 / Midtones 1 / Darks 3 / Darks 2 / Darks 1 / Lights 3 / Lights 2 / Lights 1 / batch command executed successfully` (exit code 0).
  2. Objective pixel behavioral assertion: `gimp --no-interface --batch-interpreter=python-fu-eval` sampled pixel RGB values on split white/black test canvas: `Lights 1` white side = 1.000, black side = 0.000; `Darks 1` white side = 0.000, black side = 1.000 (exit code 0).
- **Status**: IMPLEMENTED_VERIFIED (Iteration 9).

---

### Feature: Non-Destructive Dodge & Burn Layer
- **Source topic**: Retouch and correct - Dodge and burn image areas
- **Photoshop behavior**: Creates a 50% neutral gray layer in Overlay or Soft Light blend mode, allowing non-destructive exposure painting with black/white brush without directly modifying source pixels.
- **GIMP equivalent**: Implemented via custom Python 3 plugin `python-fu-dodge-burn-layer` in `<Image>/Layer/New Dodge & Burn Layer...` and `<Image>/Filters/Retouching/Dodge & Burn Layer...`.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/dodge-burn-layer/dodge-burn-layer.py`.
- **Current capability**: One-click creation of 50% neutral gray overlay layer with interactive dialog for blend mode choice (Soft Light subtle vs Overlay high contrast), layer name, and opacity; prepares White/Black brush colors and selects layer for immediate painting.
- **Gap**: None.
- **Dependencies**: Python 3 (`gi.repository.Gimp`, `gi.repository.Gegl`).
- **Implementation priority**: Medium (Phase 8).
- **Verification strategy**: Automated headless GIMP test verifying PDB registration, layer creation, neutral gray fill (`#808080`), 0.000000 composite difference (perfect neutrality), and pixel brightening/darkening when painting.
- **Verification evidence** (Iteration 10):
  1. `verify_config.py`: Section 6 passed with 3 active Python plugins.
  2. Objective pixel behavioral test: `gimp --no-interface --batch-interpreter=python-fu-eval`: Soft Light neutrality diff = 0.000000, Overlay neutrality diff = 0.000000; dodged luminance = 0.871 (base 0.352), burned luminance = 0.112 (base 0.352). Exit code 0.
- **Status**: IMPLEMENTED_VERIFIED (Iteration 10).

---

### Feature: High Pass Sharpening Helper
- **Source topic**: Adjust image color and tone - Sharpening and noise reduction / Smart filters - Sharpen image using edge mask
- **Photoshop behavior**: High Pass filter applied to duplicate layer in Overlay/Soft Light mode with layer mask to sharpen micro-contrast and edges without halo artifacts.
- **GIMP equivalent**: Implemented via custom Python 3 plugin `python-fu-high-pass-sharpen` in `<Image>/Filters/Enhance/High Pass Sharpen...` and `<Image>/Filters/Retouching/High Pass Sharpen...`.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/high-pass-sharpen/high-pass-sharpen.py`.
- **Current capability**: One-click duplication of active layer, GEGL `gegl:high-pass` filter application with radius slider, Soft Light / Overlay blend mode assignment, opacity control, and optional reveal-all layer mask attachment.
- **Gap**: None.
- **Dependencies**: GEGL `gegl:high-pass`, Python 3 (`gi.repository.Gimp`, `gi.repository.Gegl`).
- **Implementation priority**: Medium (Phase 9).
- **Verification strategy**: Headless automated test verifying PDB registration, layer creation, layer mask attachment, edge micro-contrast enhancement, and smooth region noise invariance.
- **Verification evidence** (Iteration 11):
  1. `verify_config.py`: Section 6 passed with 4 active Python plugins.
  2. Objective pixel behavioral test: `gimp --no-interface --batch-interpreter=python-fu-eval`: Edge contrast increased from 0.4000 to 0.4295 in Soft Light and to 0.4420 in Overlay; flat region noise deviation was < 0.0006. Exit code 0.
- **Status**: IMPLEMENTED_VERIFIED (Iteration 11).

---

### Feature: Quick Export (Web & Social Formats)
- **Source topic**: Save and export images - Export files to different formats / Export your work using the Quick Export as option
- **Photoshop behavior**: Quick Export as PNG / JPEG with scaling presets (1x, 2x, 0.5x), automatic document directory output, and bypass of modal configuration dialogs.
- **GIMP equivalent**: Implemented via custom Python 3 plugin `quick-export.py` registering `python-fu-quick-export` and `python-fu-quick-export-png` in `<Image>/File` and `<Image>/File/Export`.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/quick-export/quick-export.py`.
- **Current capability**: One-click instant PNG export (`Quick Export as PNG`) and configurable export dialog (`Quick Export...`) supporting PNG/JPEG formats, 1x/0.5x/2x scaling presets, quality control, and document folder resolution.
- **Gap**: None.
- **Dependencies**: Python 3 (`gi.repository.Gimp`, `gi.repository.Gio`), PDB `file-png-export`, `file-jpeg-export`.
- **Implementation priority**: Medium (Phase 10).
- **Verification strategy**: Automated headless GIMP test verifying PDB registration, valid file creation on disk, correct PNG/JPEG signatures, accurate image scaling dimensions (1x, 0.5x, 2x), and document layer integrity.
- **Verification evidence** (Iteration 12):
  1. `verify_config.py`: Section 6 passed with 5 active Python plugins.
  2. Objective file and dimension behavioral test: `gimp --no-interface --batch-interpreter=python-fu-eval`: 1x PNG export (200x100), JPEG export (valid SOI header), 0.5x scaling (100x50), 2x scaling (400x200), and original canvas integrity confirmed untouched. Exit code 0.
- **Status**: IMPLEMENTED_VERIFIED (Iteration 12).

---

### Feature: Unified End-to-End Regression Suite & Plugin Quality Gate
- **Source topic**: Technical requirements / Automated testing / Quality control
- **Photoshop behavior**: Rigorous continuous regression test suite asserting plugin integrity and mathematical accuracy.
- **GIMP equivalent**: Standalone test runners `tests/run_all_tests.py` and `tests/gimp_e2e_suite.py` plus strict inventory auditing in `verify_config.py`.
- **GIMP source locations**: `tests/gimp_e2e_suite.py`, `tests/run_all_tests.py`, `PhotoGIMP/scripts/verify_config.py`.
- **Current capability**: 3-stage automated quality pipeline: Stage 1 audits configuration, shortcuts, workspace, desktop launcher, tool options, and REQUIRED_PLUGINS inventory; Stage 2 validates installer batch mode and executable permissions; Stage 3 executes 30 headless assertions verifying PDB registration, layer math, channels, neutrality, edge sharpening, and export presets.
- **Gap**: None.
- **Verification evidence** (Iteration 13):
  1. `python3 tests/run_all_tests.py`: All 3 stages passed cleanly in 13.44s.
  2. 30/30 assertions in `tests/gimp_e2e_suite.py` passed with exit code 0.
- **Status**: IMPLEMENTED_VERIFIED (Iteration 13).

---

### Feature: Non-Destructive Vignette & Lens Lighting Helper
- **Source topic**: Retouch and correct - Vignette / Darken edges to focus center (`Topics.txt` lines 106 & 661, `photoshop_docs.md` Section 271)
- **Photoshop behavior**: Dedicated non-destructive vignette / lens lighting effect darkening (or lightening) outer periphery while maintaining 100% untouched subject exposure at the center.
- **GIMP equivalent**: Implemented via custom Python 3 plugin `python-fu-vignette-lighting` in `<Image>/Filters/Light and Shadow/Vignette Lighting...` and `<Image>/Layer/New Vignette Layer...`.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/vignette-lighting/vignette-lighting.py`.
- **Current capability**: Dedicated non-destructive overlay layer with Dark Vignette (shadow falloff) and Light Vignette (highlight / high-key) tone options, Soft Light / Overlay / Multiply blend modes, configurable radius, softness, opacity, and reveal-all layer mask attachment. Uses `#808080` (sRGB 128/255 perceptual midpoint) base fill ensuring mathematical 0.000000 center identity neutrality.
- **Gap**: None.
- **Dependencies**: GEGL `gegl:vignette`, Python 3 (`gi.repository.Gimp`, `gi.repository.Gegl`).
- **Implementation priority**: Medium (Phase 12).
- **Verification strategy**: Automated headless GIMP test verifying PDB registration, layer modes, reveal-all mask, 0.000000 center identity neutrality, -0.190 edge shadow falloff, and +0.292 highlight vignette brightening.
- **Verification evidence** (Iteration 14):
  1. `verify_config.py`: Section 6 passed with 6 active Python plugins.
  2. Objective pixel behavioral test: `gimp --no-interface --batch-interpreter=python-fu-eval`: Center identity difference is 0.000000, edge radial shadow falloff delta is -0.190, highlight vignette edge brightening delta is +0.292. Exit code 0.
- **Status**: IMPLEMENTED_VERIFIED (Iteration 14).

---

### Feature: Depth of Field & Background Defocus Helper
- **Source topic**: Blur and sharpen filters - Create depth of field with lens blur (`Topics.txt` lines 461 & 659, `photoshop_docs.md` Section 425)
- **Photoshop behavior**: Optical lens blur with depth map / gradient protection isolating the sharp subject from blurred background, simulating camera lens aperture bokeh and specular highlights.
- **GIMP equivalent**: Implemented via custom Python 3 plugin `python-fu-depth-blur` in `<Image>/Filters/Blur/Depth Defocus (Lens Blur)...`.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/depth-blur/depth-blur.py`.
- **Current capability**: Creates an isolated, non-destructive blur layer duplicating the active drawable. Supports Optical Lens Blur (`gegl:lens-blur` with specular bokeh highlights) and Gaussian Blur (`gegl:gaussian-blur`). Automatically generates a depth protection mask (radial falloff, active selection, or full reveal) ensuring the in-focus subject remains mathematically 100% sharp (0.000000 difference) while smoothly defocusing background elements, with editable mask for manual brush refinement.
- **Gap**: None.
- **Dependencies**: GEGL `gegl:lens-blur`, `gegl:gaussian-blur`, `gegl:vignette`, Python 3 (`gi.repository.Gimp`, `gi.repository.Gegl`).
- **Implementation priority**: Medium (Phase 13).
- **Verification strategy**: Automated headless GIMP test verifying PDB registration, layer modes, mask attachment, center subject sharpness invariance (0.000000 diff), background defocus attenuation (delta > 0.15), and active selection depth isolation.
- **Verification evidence** (Iteration 15):
  1. `verify_config.py`: Section 6 passed with 7 active Python plugins.
  2. Objective pixel behavioral test: `gimp --no-interface --batch-interpreter=python-fu-eval`: Center identity difference is 0.000000 (100% sharp), corner background defocus delta is 0.356, selection mode mask successfully isolated subject (0.0) from background (1.0). Exit code 0.
- **Status**: IMPLEMENTED_VERIFIED (Iteration 15).

---

### Feature: Shadows & Highlights Recovery Helper
- **Source topic**: Adjust light and tone - Adjust image shadows and highlights (`Topics.txt` line 269, `photoshop_docs.md` Section 273)
- **Photoshop behavior**: Local neighborhood tonal analysis to correct backlighting, lift dark shadows, and darken/compress blown highlights.
- **GIMP equivalent**: Implemented via custom Python 3 plugin `python-fu-shadow-highlight` in `<Image>/Colors/Shadows and Highlights...` and `<Image>/Filters/Retouching/Shadows and Highlights...`.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/shadow-highlight/shadow-highlight.py`.
- **Current capability**: Creates an isolated, non-destructive recovery layer duplicating the active drawable. Applies GEGL `gegl:shadows-highlights` with configurable shadow lift (0-100%), highlight compression (0-100%), local spatial radius, midtone compression, and attached reveal-all layer mask. Keeps base layer pixels 100% untouched.
- **Gap**: None.
- **Dependencies**: GEGL `gegl:shadows-highlights`, Python 3 (`gi.repository.Gimp`, `gi.repository.Gegl`).
- **Implementation priority**: Medium (Phase 14).
- **Verification strategy**: Automated headless GIMP test verifying PDB registration, layer modes, mask attachment, shadow lift (delta > +0.20), highlight compression (delta < -0.15), and base layer preservation.
- **Verification evidence** (Iteration 16):
  1. `verify_config.py`: Section 6 passed with 8 active Python plugins.
  2. Objective pixel behavioral test: `gimp --no-interface --batch-interpreter=python-fu-eval`: Shadow tone recovered from 0.050 to 0.418 (delta +0.368), highlight tone compressed from 0.947 to 0.723 (delta -0.224), base layer pixels 100% untouched (diff 0.000000). Exit code 0.
- **Status**: IMPLEMENTED_VERIFIED (Iteration 16).

---

### Feature: Black & White Conversion & Tonal Toning Helper
- **Source topic**: Color effects and techniques - Convert a color image to black and white (`Topics.txt` lines 341 & 668, `photoshop_docs.md` Section 341)
- **Photoshop behavior**: Converts color images to monochrome with custom per-channel luminance weighting (Reds, Greens, Blues) and photographic toning (Sepia tint).
- **GIMP equivalent**: Implemented via custom Python 3 plugin `python-fu-black-and-white` in `<Image>/Colors/Black and White...` and `<Image>/Filters/Retouching/Black and White...`.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/black-and-white/black-and-white.py`.
- **Current capability**: Creates an isolated, non-destructive monochrome layer duplicating the active drawable. Applies GEGL `gegl:mono-mixer` for precision channel weighting with presets (Neutral, High Contrast Red filter, Infrared, Landscape, Portrait, and Custom weights) and optional warm Sepia photographic toning (`gegl:sepia`), complete with attached reveal-all layer mask and 100% source pixel preservation.
- **Gap**: None.
- **Dependencies**: GEGL `gegl:mono-mixer`, `gegl:sepia`, Python 3 (`gi.repository.Gimp`, `gi.repository.Gegl`).
- **Implementation priority**: Medium (Phase 15).
- **Verification strategy**: Automated headless GIMP test verifying PDB registration, layer modes, mask attachment, channel neutrality (`r == g == b`), red-blue weighting response (delta > +0.40), warm sepia split (`r > g > b`), and base layer preservation.
- **Verification evidence** (Iteration 17):
  1. `verify_config.py`: Section 6 passed with 9 active Python plugins.
  2. Objective pixel behavioral test: `gimp --no-interface --batch-interpreter=python-fu-eval`: Pure grayscale neutrality diff = 0.000000, Red filter luminance contrast = +0.497, Sepia warm toning confirmed (R=0.847 > G=0.694 > B=0.451), base layer pixels 100% untouched. Exit code 0.
- **Status**: IMPLEMENTED_VERIFIED (Iteration 17).

---

### Feature: Photo Filter Optical Warming & Cooling Helper
- **Source topic**: Color adjustment and fill layers - Adjustment and fill layers overview / Photo Filter (`Topics.txt` lines 93/94, `photoshop_docs.md` Section 3074 & 3218)
- **Photoshop behavior**: Simulates optical camera glass filters (Kodak Wratten 85 warming, 80 cooling, color contrasts) with density control (1% to 100%), luminosity preservation, and layer mask.
- **GIMP equivalent**: Implemented via custom Python 3 plugin `python-fu-photo-filter` in `<Image>/Colors/Photo Filter...` and `<Image>/Filters/Retouching/Photo Filter...`.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/photo-filter/photo-filter.py`.
- **Current capability**: Creates an isolated, non-destructive photo filter adjustment layer above the target layer with 16 authentic optical presets (Kodak Wratten 85 warming, 81 golden warm, 80 cooling blue, 82 soft cooling, red, orange, yellow, green, cyan, blue, magenta, sepia, deep red, deep blue, deep emerald, amber) plus custom RGB color, density slider (1% to 100%), preserve luminosity mode (`Gimp.LayerMode.LCH_COLOR` vs `SOFTLIGHT`), and attached reveal-all layer mask.
- **Gap**: None.
- **Dependencies**: Python 3 (`gi.repository.Gimp`, `gi.repository.Gegl`).
- **Implementation priority**: Medium (Phase 16).
- **Verification strategy**: Automated headless GIMP test verifying PDB registration, layer modes, mask attachment, optical warming response (R > B), cooling response (B > R), density modulation (25% vs 75%), Soft Light non-preserve luminosity mode, and base layer invariance.
- **Verification evidence** (Iteration 18):
  1. `verify_config.py`: Section 6 passed with 10 active Python plugins.
  2. Objective pixel behavioral test: `gimp --no-interface --batch-interpreter=python-fu-eval`: Warming 85 produces R=0.578 > B=0.376 (delta +0.201), Cooling 80 produces B=0.680 > R=0.413 (delta +0.267), 75% density delta increases to +0.762, Soft Light mode 45 verified, base layer pixels 100% untouched (diff 0.000000). Exit code 0.
- **Status**: IMPLEMENTED_VERIFIED (Iteration 18).

---

### Feature: Non-Destructive Vibrance & Smart Saturation Helper
- **Source topic**: Adjust image color and tone - Adjust color saturation using a Vibrance adjustment layer (`Topics.txt` line 324, `photoshop_docs.md` Section 104 & 319)
- **Photoshop behavior**: Enhances muted colors while preserving skin tones and preventing color clipping. Vibrance provides intelligent saturation control that adapts to existing color intensity.
- **GIMP equivalent**: Implemented via custom Python 3 plugin `python-fu-vibrance` in `<Image>/Colors/Vibrance...` and `<Image>/Filters/Retouching/Vibrance...`.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/vibrance/vibrance.py`.
- **Current capability**: Creates an isolated, non-destructive adjustment layer duplicating the target drawable and applies GEGL `gegl:vibrance`. Includes dual-slider controls (Vibrance -100 to +100 and Saturation -100 to +100), curated photographic presets (Default, Portrait skin-tone friendly, Landscape, Vivid, Subtle, Muted, Custom), adjustable opacity, attached reveal-all layer mask, and 100% source pixel preservation.
- **Gap**: None.
- **Dependencies**: GEGL `gegl:vibrance`, Python 3 (`gi.repository.Gimp`, `gi.repository.Gegl`).
- **Implementation priority**: Medium (Phase 17).
- **Verification strategy**: Automated headless GIMP test verifying PDB registration, layer modes, mask attachment, muted tone boost (+0.430), skin/saturated tone protection (>5x protection ratio), full desaturation response (spread 0.000000 on -100 saturation), and base layer preservation.
- **Verification evidence** (Iteration 19):
  1. `verify_config.py`: Section 6 passed with 11 active Python plugins.
  2. Objective pixel behavioral test: `gimp --no-interface --batch-interpreter=python-fu-eval`: Default Vibrance +25 boosted muted spread from 0.119 to 0.549 (delta +0.430) while saturated spread only rose from 0.900 to 0.983 (delta +0.083, 5.2x protection ratio), Saturation -100 yielded exact grayscale 0.000000 spread, and base layer pixels remained 100% untouched (diff 0.000000). Exit code 0.
- **Status**: IMPLEMENTED_VERIFIED (Iteration 19).

---

### Feature: Non-Destructive Color Balance & Tonal Grading Helper
- **Source topic**: Adjust image color and tone - Correct color balance / Apply Color Balance adjustment in Photoshop (`Topics.txt` line 328, `photoshop_docs.md` Section 3072 & 3216)
- **Photoshop behavior**: Changes overall color cast with 3-way color grading across Shadows, Midtones, and Highlights with Cyan-Red, Magenta-Green, and Yellow-Blue controls and luminosity preservation.
- **GIMP equivalent**: Implemented via custom Python 3 plugin `python-fu-color-balance` in `<Image>/Colors/Color Balance...` and `<Image>/Filters/Retouching/Color Balance...`.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/color-balance/color-balance.py`.
- **Current capability**: Creates an isolated, non-destructive adjustment layer duplicating the target drawable and applies 3-way color grading using `gimp-drawable-color-balance` across Shadows, Midtones, and Highlights. Features cinematic presets (Teal & Orange, Warm Sunset, Cool Moonlight, Vintage Cross-Process, Custom sliders), preserve luminosity toggle, layer opacity control, attached reveal-all layer mask, and 100% source pixel preservation.
- **Gap**: None.
- **Dependencies**: PDB `gimp-drawable-color-balance`, Python 3 (`gi.repository.Gimp`, `gi.repository.Gegl`).
- **Implementation priority**: Medium (Phase 18).
- **Verification strategy**: Automated headless GIMP test verifying PDB registration, layer modes, mask attachment, Shadows teal shift (B > R), Midtones warm orange shift (R > B), Highlights golden amber shift (R > B), custom shadow blue shift, and base layer preservation.
- **Verification evidence** (Iteration 20):
  1. `verify_config.py`: Section 6 passed with 12 active Python plugins.
  2. Objective pixel behavioral test: `gimp --no-interface --batch-interpreter=python-fu-eval`: Teal & Orange preset verified with Teal shadows (B=0.133 > R=0.018, delta +0.115), Warm orange midtones (R=0.888 > B=0.238, delta +0.650), Golden highlights (R=1.000 > B=0.708, delta +0.292), Custom shadow blue shift (B=0.198 > R=0.005), and base layer pixels 100% untouched (diff 0.000000). Exit code 0.
- **Status**: IMPLEMENTED_VERIFIED (Iteration 20).

---

### Feature: Non-Destructive Gradient Map & Cinematic Color Grading Helper
- **Source topic**: Adjust image color and tone - Apply a gradient fill / Edit a gradient (`Topics.txt` line 342, `photoshop_docs.md` Section 3081 & 3225: "Gradient Map: Maps tones to gradient colors")
- **Photoshop behavior**: Maps the equivalent grayscale range of the image to the colors of a designated gradient fill, allowing sophisticated color grading (such as Teal & Orange or duotone toning) without altering source pixels.
- **GIMP equivalent**: Implemented via custom Python 3 plugin `python-fu-gradient-map` in `<Image>/Colors/Gradient Map...` and `<Image>/Filters/Retouching/Gradient Map...`.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/gradient-map/gradient-map.py`.
- **Current capability**: Creates an isolated, non-destructive adjustment layer duplicating the target drawable and applies GEGL `gegl:gradient-map` across luminance tones. Features curated photographic and cinematic presets (Teal & Orange, Sepia Vintage, Cyberpunk Neon, Copper & Patina, Fine Art B&W, Golden Sunset, Custom Two-Tone), blend mode selection (Soft Light, Overlay, Color, Normal), layer opacity slider, gradient reversal toggle (`reverse=True`), attached reveal-all layer mask, and 100% source pixel preservation.
- **Gap**: None.
- **Dependencies**: GEGL `gegl:gradient-map`, Python 3 (`gi.repository.Gimp`, `gi.repository.Gegl`).
- **Implementation priority**: Medium (Phase 19).
- **Verification strategy**: Automated headless GIMP test verifying PDB registration, layer modes, mask attachment, Shadows teal mapping (B > R), Midtones warm coral mapping (R > B), Highlights ivory mapping (R > B), Soft Light mode 45 at 75.0% opacity, reverse mapping inversion, and base layer preservation.
- **Verification evidence** (Iteration 21):
  1. `verify_config.py`: Section 6 passed with 13 active Python plugins.
  2. Objective pixel behavioral test: `gimp --no-interface --batch-interpreter=python-fu-eval`: Teal & Orange preset verified with Teal shadows (B=0.202 > R=0.020), Warm coral midtones (R=0.847 > B=0.223), Warm ivory highlights (R=1.000 > B=0.847), Soft Light mode 45 at 75.0% opacity, inverted mapping with shadow magenta (R=0.896) and highlight green (G=0.799), and base layer pixels 100% untouched (diff 0.000000). Exit code 0.
- **Status**: IMPLEMENTED_VERIFIED (Iteration 21).

---

### Feature: Non-Destructive Channel Mixer & Monochrome Infrared Helper
- **Source topic**: Adjust image color and tone - Rebalances color channels (`Topics.txt` lines 93-103, `photoshop_docs.md` Section 3075 & 3219: "Channel Mixer: Rebalances color channels")
- **Photoshop behavior**: Modifies color channels using a mix of existing color channels, allowing color cast corrections, specialized monochrome film simulation, and false-color infrared photography.
- **GIMP equivalent**: Implemented via custom Python 3 plugin `python-fu-channel-mixer` in `<Image>/Colors/Channel Mixer...` and `<Image>/Filters/Retouching/Channel Mixer...`.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/channel-mixer/channel-mixer.py`.
- **Current capability**: Creates an isolated, non-destructive adjustment layer duplicating the target drawable and applies GEGL `gegl:channel-mixer`. Features authentic photographic presets (Color Infrared Red/Blue swap, B&W Standard Neutral 40/40/20, B&W Landscape 20/70/10, B&W Portrait 60/30/10, B&W High Contrast / Red Glass 100/0/0, Warm Golden Cast, Cool Cyan Cast, Custom Mixer Weights with Photoshop-style Monochrome toggle and per-channel percentage sliders), preserve luminosity toggle, layer opacity slider, attached reveal-all layer mask, and 100% source pixel preservation.
- **Gap**: None.
- **Dependencies**: GEGL `gegl:channel-mixer`, Python 3 (`gi.repository.Gimp`, `gi.repository.Gegl`).
- **Implementation priority**: Medium (Phase 20).
- **Verification strategy**: Automated headless GIMP test verifying PDB registration, layer modes, mask attachment, Color Infrared swap (Red zone -> Blue B > R, Blue zone -> Red R > B), exact monochrome neutrality (R == G == B, spread 0.000000), custom monochrome mode with opacity, and base layer preservation.
- **Verification evidence** (Iteration 22):
  1. `verify_config.py`: Section 6 passed with 14 active Python plugins.
  2. Objective pixel behavioral test: `gimp --no-interface --batch-interpreter=python-fu-eval`: Color Infrared verified with Red zone swapped to Blue (B=0.896 > R=0.100), Blue zone swapped to Red (R=0.896 > B=0.100), exact monochrome neutrality (R=G=B=0.418, spread 0.000000), Custom monochrome mode at 85.0% opacity (spread 0.000000), and base layer pixels 100% untouched (diff 0.000000). Exit code 0.
- **Status**: IMPLEMENTED_VERIFIED (Iteration 22).

---

### Feature: Non-Destructive Color Temperature & White Balance Helper
- **Source topic**: Adjust image color and tone - Correct color balance with Color and vibrance (`Topics.txt` line 100, `photoshop_docs.md` Section 104 line 3184 & 3192: "Adjust Temperature, Tint, Vibrance, Saturation and fix White Balance to achieve balanced and natural-looking colors")
- **Photoshop behavior**: Adjusts image color temperature along the physical blackbody radiation spectrum (Kelvin) to warm up golden hour tones, cool down shade/nocturnal tones, or calibrate neutral white balance.
- **GIMP equivalent**: Implemented via custom Python 3 plugin `python-fu-color-temperature` in `<Image>/Colors/Color Temperature...` and `<Image>/Filters/Retouching/Color Temperature...`.
- **GIMP source locations**: `PhotoGIMP/.config/GIMP/3.0/plug-ins/color-temperature/color-temperature.py`.
- **Current capability**: Creates an isolated, non-destructive adjustment layer duplicating the target drawable and applies GEGL `gegl:color-temperature`. Features authentic physical Kelvin presets (Warming: Golden Hour / Sunset Glow 6500K -> 9000K, Warming: Tungsten Indoor Glow 5500K -> 7500K, Cooling: Shade / Blue Hour 6500K -> 4800K, Cooling: Nocturnal Moonlight 6500K -> 3800K, Candlelight Glow 5500K -> 10500K, Daylight Normalization 4000K -> 5500K, Custom Kelvin sliders 1000K-12000K), layer opacity slider (10% to 100%), attached reveal-all layer mask, and 100% source pixel preservation.
- **Gap**: None.
- **Dependencies**: GEGL `gegl:color-temperature`, Python 3 (`gi.repository.Gimp`, `gi.repository.Gegl`).
- **Implementation priority**: Medium (Phase 21).
- **Verification strategy**: Automated headless GIMP test verifying PDB registration, layer modes, mask attachment, Warming shift (R > B, delta > 0.15), Cooling shift (B > R, delta > 0.25), Custom Kelvin sliders with opacity, and base layer preservation.
- **Verification evidence** (Iteration 23):
  1. `verify_config.py`: Section 6 passed with 15 active Python plugins.
  2. Objective pixel behavioral test: `gimp --no-interface --batch-interpreter=python-fu-eval`: Golden Hour sunset warming verified (R=0.578 > B=0.386, delta 0.191), Nocturnal moonlight cooling verified (B=1.000 > R=0.356, delta 0.644), Custom Kelvin sliders with 80.0% opacity verified (R=0.658 > B=0.296, delta 0.362), and base layer pixels 100% untouched (diff 0.000000). Exit code 0.
- **Status**: IMPLEMENTED_VERIFIED (Iteration 23).

---

## 2. Core Editing & Adjustment Infrastructure (Native GIMP 3.x Built-ins)

### Feature: Curves, Levels & Color Adjustments
- **Source topic**: Adjust image color and tone - Correct color balance
- **Photoshop behavior**: Levels (`Ctrl+L`), Curves (`Ctrl+M`), Hue/Saturation (`Ctrl+U`), Color Balance.
- **GIMP equivalent**: `gimp-curves-tool`, `gimp-levels-tool`, `gimp-hue-saturation-tool`, `gimp-color-balance-tool`.
- **Status**: Native equivalent; shortcuts mapped in PhotoGIMP `shortcutsrc`.

### Feature: Layer Masks & Blending Modes
- **Source topic**: Create and manage layers - Work with layer masks / Blend modes
- **Photoshop behavior**: Layer masks, clipping masks, standard blend modes (Multiply, Screen, Overlay, Soft Light, Linear Light, Color, Luminosity).
- **GIMP equivalent**: GIMP 3.x supports 38 GEGL layer blend modes and full layer mask support (white, black, alpha, selection).
- **Status**: Native equivalent.

### Feature: Selections & Quick Mask
- **Source topic**: Make selections - Select areas with selection tools / Quick Mask
- **Photoshop behavior**: Marquee (`M`), Lasso (`L`), Magic Wand (`W`), Quick Mask (`Q`).
- **GIMP equivalent**: Rect/Ellipse Select, Free Select, Fuzzy Select, Quick Mask toggle (`Shift+Q` / `Q`).
- **Status**: Native equivalent; tool options presets standardized in `tool-options/`.

---

## 3. Configuration & Desktop Integration Overlay

### Feature: Single-Window Photoshop Workspace & Theme
- **Photoshop behavior**: Single-window dockable layout with dark theme.
- **Status**: Configured via `sessionrc`, `gimprc`, `theme.css`, `install.sh`, and `verify_config.py`.
