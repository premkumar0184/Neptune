# Implementation Plan — Linux Photo Editor (GIMP 3.x / PhotoGIMP)

Status: IN_PROGRESS

This file is the authoritative roadmap of product-development work to transform GIMP 3.x on Linux into a professional, Photoshop-grade photo editing environment.

---

## Completed Baseline Phases (Configuration & Integration Overlay)

- [x] **Phase 0 — Repository Archaeology & Baseline Analysis**: Verified GIMP 3.2.6, PhotoGIMP assets, and initialized tracking.
- [x] **Phase 1 — GIMP 3.2+ Multi-Target Installer**: Non-interactive batch mode (`--batch`), multi-target deployment (`--all`), isolated runtime backups.
- [x] **Phase 2 — Photoshop Keybinding Alignment**: Active Photoshop shortcuts configured in `shortcutsrc` (`Ctrl+A`, `Ctrl+D`, `Ctrl+Shift+I`, `Ctrl+J`, `Ctrl+T`, `Ctrl+Z`, `Ctrl+Shift+Z`, `Ctrl+L`, `Ctrl+M`, `Ctrl+U`, `B`, `E`, `V`, `M`, `L`, `W`, `C`, `J`, `S`, `T`, `Z`).
- [x] **Phase 3 — Single-Window Workspace & Theme**: Configured `sessionrc` dockable layout with Undo History panel, clean GIMP 3.x `gimprc`, portable dark `theme.css`, native desktop launcher, and multi-resolution icons.
- [x] **Phase 4 — Tool Options & Retouching Defaults**: Standardized presets in `tool-options/` (free-form crop, anti-aliased selections, tolerance 32 for Magic Wand / Color Select).
- [x] **Phase 5 — Automated Configuration Quality Gate**: Built `verify_config.py` with 5 automated audit sections and documented manual testing in `docs/SMOKE_TESTING.md`.

---

## Active Product Development Phases (Photoshop Feature Extensions)

### Phase 6 — Frequency Separation Retouching Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `frequency-separation` (`python-fu-frequency-separation`) in `PhotoGIMP/.config/GIMP/3.0/plug-ins/frequency-separation/frequency-separation.py`.
- [x] Implement interactive dialog with Gaussian blur radius slider (default: 3.0px) and seamless layer reconstruction math.
- [x] Create grouped `Frequency Separation` folder with `Low Frequency` (color/tone) and `High Frequency` (texture/detail) layers.
- [x] Register under menu path `<Image>/Filters/Retouching/Frequency Separation...`.
- [x] Validate plugin syntax, registration, and execute automated headless GIMP test splitting a test image and verifying layer structure.

### Phase 7 — Luminosity Masks Channel Generator
- [x] Implement native GIMP 3.x Python 3 plugin `luminosity-masks` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/luminosity-masks/luminosity-masks.py`.
- [x] Automatically calculate 9 precision tonal channels: Lights (1, 2, 3), Darks (1, 2, 3), and Midtones (1, 2, 3).
- [x] Register under menu path `<Image>/Select/Luminosity Masks...`.
- [x] Validate channel generation on test image via headless GIMP test (exit 0, 9 channels named correctly).

### Phase 8 — Non-Destructive Dodge & Burn Layer Helper
- [x] Implement native GIMP 3.x Python 3 plugin `dodge-burn-layer` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/dodge-burn-layer/dodge-burn-layer.py`.
- [x] Create 50% neutral gray overlay layer (`#808080`) set to Overlay or Soft Light blend mode.
- [x] Register under menu path `<Image>/Layer/New Dodge & Burn Layer...` and `<Image>/Filters/Retouching/Dodge & Burn Layer...`.
- [x] Validate layer creation, neutrality (0.000000 diff), and dodging/burning properties via headless GIMP test.

### Phase 9 — High Pass Sharpening Helper
- [x] Implement native GIMP 3.x Python 3 plugin `high-pass-sharpen` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/high-pass-sharpen/high-pass-sharpen.py`.
- [x] Duplicate active layer, apply `gegl:high-pass` filter with configurable radius, and set blend mode to Soft Light / Overlay.
- [x] Register under menu path `<Image>/Filters/Enhance/High Pass Sharpen...` and `<Image>/Filters/Retouching/High Pass Sharpen...`.
- [x] Validate sharpening layer generation, edge micro-contrast enhancement, and noise invariance via headless GIMP test.

### Phase 10 — Quick Export (Web & Social Presets)
- [x] Implement native GIMP 3.x Python 3 plugin `quick-export` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/quick-export/quick-export.py`.
- [x] Fast one-click export to PNG / JPEG in document directory with automatic scaling (1x, 2x, 0.5x).
- [x] Register under menu path `<Image>/File` and `<Image>/File/Export` (`Quick Export as PNG` and `Quick Export...`).
- [x] Validate exported image files, scaling presets, and document integrity via headless GIMP test.

### Phase 11 — End-to-End Plugin Suite Quality Gate & Full Automated Regression Suite
- [x] Extend `PhotoGIMP/scripts/verify_config.py` with Section 6 Plugin Suite audit (REQUIRED_PLUGINS inventory, permissions, byte-compilation, shebang, GIMP 3 API, live user config checks).
- [x] Ensure `PhotoGIMP/install.sh` deploys all plugin directories to user config `plug-ins/` with executable permissions.
- [x] Build and execute full headless GIMP test suite (`tests/gimp_e2e_suite.py` and `tests/run_all_tests.py`) exercising all 5 custom plugins with 30/30 automated tests passing.

---

## Next Product Development Phases (Photoshop Creative Tools)

### Phase 12 — Non-Destructive Vignette & Lens Lighting Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `vignette-lighting` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/vignette-lighting/vignette-lighting.py`.
- [x] Support non-destructive radial exposure falloff (dark vignette or highlight vignette) with configurable radius, softness, and blend mode.
- [x] Register under menu path `<Image>/Filters/Light and Shadow/Vignette Lighting...` and `<Image>/Layer/New Vignette Layer...`.
- [x] Validate non-destructive layer creation and radial luminance falloff via headless GIMP test (center diff 0.000000, edge darkening -0.190, edge brightening +0.292).

### Phase 13 — Depth of Field & Background Defocus Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `depth-blur` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/depth-blur/depth-blur.py`.
- [x] Duplicate active drawable into a non-destructive blur layer with configurable Gaussian / lens blur radius.
- [x] Attach an interactive radial / elliptical depth gradient mask preserving subject sharpness in the center while defocusing backgrounds.
- [x] Register under menu path `<Image>/Filters/Blur/Depth Defocus (Lens Blur)...`.
- [x] Validate non-destructive layer creation, center subject edge sharpness preservation, and background blur via headless GIMP test (center diff 0.000000, corner defocus delta 0.356).

### Phase 14 — Non-Destructive Shadows & Highlights Recovery Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `shadow-highlight` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/shadow-highlight/shadow-highlight.py`.
- [x] Duplicate active drawable into a non-destructive tone recovery layer with configurable shadow recovery and highlight compression.
- [x] Utilize GEGL `gegl:shadows-highlights` with tone radius and adjustment sliders for local dynamic range recovery.
- [x] Register under menu path `<Image>/Colors/Shadows and Highlights...` and `<Image>/Filters/Retouching/Shadows and Highlights...`.
- [x] Validate tonal recovery, preservation of midtone contrast, and shadow detail expansion via headless GIMP test (shadow lift +0.368, highlight compression -0.224, base unchanged).

### Phase 15 — Professional Black & White Conversion & Tonal Toning Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `black-and-white` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/black-and-white/black-and-white.py`.
- [x] Duplicate active drawable into a non-destructive monochrome layer with configurable per-channel weights (Red, Green, Blue / Yellow / Cyan / Magenta).
- [x] Provide preset monochrome looks (High Contrast, Neutral, Infrared, Landscape, Portrait, Custom) and photographic toning (Sepia tone).
- [x] Register under menu path `<Image>/Colors/Black and White...` and `<Image>/Filters/Retouching/Black and White...`.
- [x] Validate monochrome conversion accuracy, tonal channel weighting response, and non-destructive base layer isolation via headless GIMP test (neutrality diff 0.000000, red filter contrast +0.497, sepia warm split verified).

### Phase 16 — Photo Filter Optical Warming & Cooling Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `photo-filter` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/photo-filter/photo-filter.py`.
- [x] Create non-destructive color temperature / photo filter layer simulating optical lens filters (Warming 85, Cooling 80, Deep Red, Orange, Amber, Cyan, Deep Blue).
- [x] Configurable filter density slider (1% to 100%), preserve luminosity toggle, and attached layer mask.
- [x] Register under menu path `<Image>/Colors/Photo Filter...` and `<Image>/Filters/Retouching/Photo Filter...`.
- [x] Validate optical color shifts (warming shifts R>B, cooling shifts B>R), density scaling, and non-destructive source layer preservation via headless GIMP test.

### Phase 17 — Non-Destructive Vibrance & Smart Saturation Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `vibrance` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/vibrance/vibrance.py`.
- [x] Create dedicated non-destructive Vibrance adjustment layer powered by GEGL `gegl:vibrance`.
- [x] Provide intelligent saturation boosting that lifts muted colors while protecting already saturated skin tones and preventing color clipping.
- [x] Dual-slider controls: Vibrance (-100 to +100, default +25) and Saturation (-100 to +100, default 0), with layer opacity and attached reveal-all layer mask.
- [x] Register under menu path `<Image>/Colors/Vibrance...` and `<Image>/Filters/Retouching/Vibrance...`.
- [x] Validate muted color boost, saturated tone protection, layer mask attachment, and non-destructive base layer isolation via headless GIMP test.

### Phase 18 — Non-Destructive Color Balance & Tonal Grading Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `color-balance` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/color-balance/color-balance.py`.
- [x] Create dedicated non-destructive Color Balance adjustment layer duplicating the active drawable.
- [x] Support independent 3-way color grading across Shadows, Midtones, and Highlights with Cyan-Red, Magenta-Green, and Yellow-Blue controls.
- [x] Support preserve luminosity toggle and attached reveal-all white layer mask for local brush masking.
- [x] Register under menu path `<Image>/Colors/Color Balance...` and `<Image>/Filters/Retouching/Color Balance...`.
- [x] Validate tonal range color shifts, preserve luminosity stability, layer mask attachment, and non-destructive source layer preservation via headless GIMP test.

### Phase 19 — Non-Destructive Gradient Map & Cinematic Color Grading Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `gradient-map` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/gradient-map/gradient-map.py`.
- [x] Create dedicated non-destructive Gradient Map adjustment layer powered by GEGL `gegl:gradient-map`.
- [x] Map luminance tones of active image to curated photographic and cinematic palettes (Teal & Orange, Sepia Vintage, Cyberpunk Neon, Copper Patina, Fine Art Monochrome, Golden Sunset, Custom Two-Tone).
- [x] Support configurable blend modes (Soft Light, Overlay, Color, Normal), layer opacity, gradient reversal, and attached reveal-all layer mask.
- [x] Register under menu path `<Image>/Colors/Gradient Map...` and `<Image>/Filters/Retouching/Gradient Map...`.
- [x] Validate tonal luminance mapping, smooth multi-stop color transitions, blend mode interaction, and non-destructive source layer preservation via headless GIMP test.

### Phase 20 — Non-Destructive Channel Mixer & Monochrome Infrared Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `channel-mixer` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/channel-mixer/channel-mixer.py`.
- [x] Create dedicated non-destructive Channel Mixer adjustment layer powered by GEGL `gegl:channel-mixer`.
- [x] Support rebalancing RGB channels, cross-channel gains, and fine-art monochrome/infrared photography simulation presets (Infrared Look, Color Swap, B&W High-Contrast Film, Custom gains).
- [x] Support preserve luminosity toggle, layer opacity control, and attached reveal-all layer mask.
- [x] Register under menu path `<Image>/Colors/Channel Mixer...` and `<Image>/Filters/Retouching/Channel Mixer...`.
- [x] Validate cross-channel gain shifts, infrared color inversion, layer mask attachment, and non-destructive source layer preservation via headless GIMP test.

### Phase 21 — Non-Destructive Color Temperature & White Balance Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `color-temperature` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/color-temperature/color-temperature.py`.
- [x] Create dedicated non-destructive Color Temperature adjustment layer powered by GEGL `gegl:color-temperature`.
- [x] Support physical Kelvin white balance correction and creative temperature styling (Golden Hour Sunset 6500K->9000K, Tungsten Indoor Glow 5500K->7500K, Shade / Blue Hour 6500K->4800K, Nocturnal Moonlight 6500K->3800K, Candlelight Glow 5500K->10500K, Daylight Normalization 4000K->5500K, Custom Kelvin sliders 1000K-12000K).
- [x] Support layer opacity control, blend modes, and attached reveal-all layer mask.
- [x] Register under menu path `<Image>/Colors/Color Temperature...` and `<Image>/Filters/Retouching/Color Temperature...`.
- [x] Validate Kelvin temperature shifts (cooling shifts B>R, warming shifts R>B), layer mask attachment, and non-destructive source layer preservation via headless GIMP test.

### Phase 22 — Non-Destructive Clarity & Dehaze Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `clarity-dehaze` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/clarity-dehaze/clarity-dehaze.py`.
- [x] Create dedicated non-destructive Clarity & Dehaze adjustment layer duplicating active drawable.
- [x] Support midtone local contrast enhancement (Clarity slider -100 to +100) using wide-radius edge-preserving unsharp masking / local contrast filtering.
- [x] Support atmospheric haze reduction and contrast restoration (Dehaze slider -100 to +100) using contrast stretching and black point recovery.
- [x] Support curated presets (Landscape: Crisp Punch & Dehaze, Atmospheric: Cut Mountain Haze, Portrait: Soft Glamour Glow, Creative: Atmospheric Mist & Fog, Architecture: High-Structure Contrast, Custom sliders).
- [x] Support layer opacity control (10% to 100%) and attached reveal-all layer mask.
- [x] Register under menu path `<Image>/Colors/Clarity and Dehaze...` and `<Image>/Filters/Enhance/Clarity and Dehaze...`.
- [x] Validate midtone contrast enhancement, haze penetration, layer mask attachment, and non-destructive source layer preservation via headless GIMP test.

### Phase 23 — Non-Destructive Film Grain & Analog Texture Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `film-grain` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/film-grain/film-grain.py`.
- [x] Create dedicated non-destructive Film Grain adjustment overlay layer (`#808080` neutral gray with Soft Light / Overlay blending).
- [x] Support grain amount (0-100%), particle size, roughness/clumping, and monochromatic vs organic color grain options.
- [x] Support authentic analog presets (35mm Classic Film Grain, 120 Medium Format Subtle, Gritty High-ISO Street, Vintage 1970s Color Grain, Fine Art Archival Print, Custom sliders).
- [x] Support layer opacity control (10% to 100%) and attached reveal-all layer mask.
- [x] Register under menu path `<Image>/Filters/Noise/Film Grain...` and `<Image>/Layer/New Film Grain Layer...`.
- [x] Validate non-destructive overlay creation, noise texture variance, blend mode neutrality, layer mask attachment, and base layer preservation via headless GIMP test.

### Phase 24 — Non-Destructive Light & Tonal Range Helper Plugin
- [ ] Implement native GIMP 3.x Python 3 plugin `light-tone` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/light-tone/light-tone.py`.
- [ ] Create dedicated non-destructive Light adjustment layer duplicating active drawable.
- [ ] Support 6-point Photoshop Light controls: Exposure (-5.0 to +5.0 EV), Contrast (-100 to +100), Highlights (-100 to +100), Shadows (-100 to +100), Whites (-100 to +100), and Blacks (-100 to +100).
- [ ] Support curated lighting presets (Brighten & Pop, Recover Backlit Subject, Deep Contrast & Rich Darks, Soft Low-Contrast Wash, High Key Studio, Custom sliders).
- [ ] Support layer opacity control (10% to 100%) and attached reveal-all layer mask.
- [ ] Register under menu path `<Image>/Colors/Light and Tone...` and `<Image>/Filters/Retouching/Light and Tone...`.
- [ ] Validate multi-control exposure adjustment, shadow recovery, highlight protection, layer mask attachment, and non-destructive base layer preservation via headless GIMP test.
