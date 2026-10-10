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
- [x] Implement native GIMP 3.x Python 3 plugin `light-tone` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/light-tone/light-tone.py`.
- [x] Create dedicated non-destructive Light adjustment layer duplicating active drawable.
- [x] Support 6-point Photoshop Light controls: Exposure (-5.0 to +5.0 EV), Contrast (-100 to +100), Highlights (-100 to +100), Shadows (-100 to +100), Whites (-100 to +100), and Blacks (-100 to +100).
- [x] Support curated lighting presets (Brighten & Pop, Recover Backlit Subject, Deep Contrast & Rich Darks, Soft Low-Contrast Wash, High Key Studio, Custom sliders).
- [x] Support layer opacity control (10% to 100%) and attached reveal-all layer mask.
- [x] Register under menu path `<Image>/Colors/Light and Tone...` and `<Image>/Filters/Retouching/Light and Tone...`.
- [x] Validate multi-control exposure adjustment, shadow recovery, highlight protection, layer mask attachment, and non-destructive base layer preservation via headless GIMP test.

### Phase 25 — Non-Destructive Duotone & Tritone Print Effect Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `duotone-effect` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/duotone-effect/duotone-effect.py`.
- [x] Create dedicated non-destructive Duotone adjustment layer duplicating active drawable.
- [x] Support two-ink / three-ink tonal luminance mapping with independent shadow ink color, highlight ink color, and optional midtone ink color.
- [x] Support curated editorial duotone presets (Classic Navy & Gold, Forest & Pale Mint, Crimson & Warm Cream, Sepia & Ivory, Cyberpunk Indigo & Neon Pink, Slate/Amber Tritone, Custom Ink Pickers).
- [x] Support compositing blend modes (Color, Soft Light, Normal), layer opacity (10% to 100%), and attached reveal-all layer mask.
- [x] Register under menu path `<Image>/Colors/Duotone Effect...`, `<Image>/Filters/Retouching/Duotone Effect...`, and `<Image>/Layer`.
- [x] Validate tonal ink mapping, blend mode response, layer mask attachment, and non-destructive source layer preservation via headless GIMP test.

### Phase 26 — Non-Destructive Diffuse Glow & Dreamy Glamour Filter Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `diffuse-glow` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/diffuse-glow/diffuse-glow.py`.
- [x] Create dedicated non-destructive Diffuse Glow adjustment layer duplicating active drawable.
- [x] Extract bright highlights above threshold, apply optical / Gaussian diffusion bloom, and add subtle organic grain.
- [x] Support curated glow presets (Dreamy Glamour Portrait, Ethereal Sunlight Bloom, Vintage Diffusion Glass, Golden Hour Warm Glow, Night Neon Radiance, Subtle Soft Focus, Custom sliders).
- [x] Support compositing blend modes (Screen, Soft Light, Addition, Normal), glow opacity (10% to 100%), and attached reveal-all layer mask.
- [x] Register under menu path `<Image>/Filters/Light and Shadow/Diffuse Glow...`, `<Image>/Filters/Retouching/Diffuse Glow...`, `<Image>/Colors/Diffuse Glow...`, and `<Image>/Layer`.
- [x] Validate highlight bloom thresholding, diffuse luminance expansion, layer mask attachment, and non-destructive base layer preservation via headless GIMP test.

### Phase 27 — Non-Destructive Skin Smoothing & Portrait Beauty Retouching Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `skin-smoothing` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/skin-smoothing/skin-smoothing.py`.
- [x] Create dedicated non-destructive Skin Smoothing adjustment layer duplicating active drawable.
- [x] Support bilateral / edge-preserving smoothing combined with high-frequency detail retention to smooth skin tones while strictly preserving facial contours, eyes, lips, and natural texture.
- [x] Support curated portrait retouching presets (Subtle Natural Retouch, Glamour Studio Smooth, High-Fashion Editorial, Matte Skin Powder, Soft Glow Beauty, Custom sliders).
- [x] Support smoothing radius (0.5 to 30.0px), edge preservation (1.0 to 50.0), detail retention (0 to 100%), layer opacity (10% to 100%), and attached reveal-all or conceal-all layer masks.
- [x] Register under menu path `<Image>/Filters/Retouching/Skin Smoothing...`, `<Image>/Filters/Enhance`, `<Image>/Colors`, and `<Image>/Layer`.
- [x] Validate skin tone variance reduction, high-contrast facial edge preservation, layer mask attachment, and non-destructive base layer preservation via headless GIMP test.

### Phase 28 — Non-Destructive Selective Color & Background Desaturation Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `selective-color-pop` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/selective-color-pop/selective-color-pop.py`.
- [x] Create dedicated non-destructive Background Desaturation / Color Pop adjustment layer duplicating active drawable.
- [x] Support non-destructively desaturating backgrounds to monochrome black and white while keeping the subject in vibrant full color.
- [x] Support radial/elliptical subject focus falloff, active selection masking, subject feathering, monochrome tinting, opacity, and attached editable layer mask.
- [x] Register under menu path `<Image>/Colors/Selective Color Pop...`, `<Image>/Filters/Retouching`, and `<Image>/Layer`.
- [x] Validate background desaturation, subject color preservation, mask attachment, and non-destructive base layer preservation via headless GIMP test.

### Phase 29 — Non-Destructive Vintage Photo Restoration & Colorization Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `photo-colorize` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/photo-colorize/photo-colorize.py`.
- [x] Create dedicated non-destructive Vintage Photo Colorization adjustment layer duplicating active drawable.
- [x] Support colorizing grayscale and vintage images with single-hue monotone washes or multi-tonal hand-colored photograph palettes (Sepia Antique, Cyanotype Blue, Vintage Amber, Rose Tint, Platinum Archival, Custom Hue/Saturation).
- [x] Support Color blend mode, layer opacity control, and attached editable layer mask for selective multi-color brush hand-painting.
- [x] Register under menu path `<Image>/Colors/Colorize Photograph...`, `<Image>/Filters/Retouching`, and `<Image>/Layer`.
- [x] Validate monotone colorization, Hue/Saturation tone mapping, layer mask attachment, and non-destructive base layer preservation via headless GIMP test.

### Phase 30 — Non-Destructive JPEG Artifacts Removal & Deblocking Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `jpeg-artifact-removal` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/jpeg-artifact-removal/jpeg-artifact-removal.py`.
- [x] Create dedicated non-destructive JPEG Cleanup / Deblocking adjustment layer duplicating active drawable.
- [x] Support reducing 8x8 DCT compression block boundaries and mosquito noise ringing while preserving sharp high-frequency edges and contours.
- [x] Support curated artifact strength presets (Subtle Web Cleanup, Medium Compression Smoothing, Aggressive Block Removal, Mosquito Ringing Suppression, 16x16 Macroblock Cleanup, Custom sliders).
- [x] Register under menu path `<Image>/Filters/Enhance/JPEG Artifacts Removal...`, `<Image>/Filters/Retouching`, and `<Image>/Layer`.
- [x] Validate compression block variance reduction, edge contrast preservation, layer mask attachment, and non-destructive base layer preservation via headless GIMP test.

### Phase 31 — Non-Destructive Charcoal & Fine-Art Sketch Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `charcoal-filter` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/charcoal-filter/charcoal-filter.py`.
- [x] Create dedicated non-destructive Charcoal Sketch adjustment layer duplicating active drawable.
- [x] Support expressive charcoal strokes, edge extraction, charcoal thickness, paper contrast, chalk highlights, curated artistic sketch presets (Fine Charcoal Drawing, Dramatic Heavy Vine, Chalk & Charcoal Duo, Rough Sketchbook, Architectural Line Art, Custom sliders).
- [x] Support blend modes (Normal, Multiply for paper drawing overlay, Soft Light), layer opacity, and attached editable layer mask.
- [x] Register under menu path `<Image>/Filters/Artistic/Charcoal Sketch...`, `<Image>/Filters/Sketch`, and `<Image>/Layer`.
- [x] Validate stroke rendering, tonal sketch response, layer mask attachment, and non-destructive base layer preservation via headless GIMP test.

### Phase 32 — Non-Destructive Woodcut & Linocut Printmaking Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `woodcut-filter` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/woodcut-filter/woodcut-filter.py`.
- [x] Create dedicated non-destructive Woodcut Print adjustment layer duplicating active drawable.
- [x] Support woodblock relief carving, high-contrast woodcut ink reduction, block gouge edge styling, woodcut ink color, handmade paper tone, curated presets (Classic Japanese Woodcut, Modern Graphic Linocut, Ukiyo-e Indigo Print, Vermilion Seal Print, Fine Archival Engraving, Custom sliders).
- [x] Register under menu path `<Image>/Filters/Artistic/Woodcut Print...`, `<Image>/Filters/Sketch`, and `<Image>/Layer`.
- [x] Validate relief gouge contrast, ink tone mapping, layer mask attachment, and non-destructive base layer preservation via headless GIMP test.

### Phase 33 — Non-Destructive Swirling Night Sky & Twirl Distortion Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `swirling-sky` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/swirling-sky/swirling-sky.py`.
- [x] Create dedicated non-destructive Swirling Sky / Twirl adjustment layer duplicating active drawable.
- [x] Support celestial vortices, vortex centers, spiral twirl angles, pinch/whirl radii, curated atmospheric distortion presets (Starry Night Vortex, Deep Space Whirlpool, Atmospheric Cyclone, Subtle Sky Drift, Counter-Clockwise Spiral, Custom sliders).
- [x] Register under menu path `<Image>/Filters/Distort/Swirling Night Sky...`, `<Image>/Filters/Artistic`, and `<Image>/Layer`.
- [x] Validate vortex center displacement, rotational swirl angle, layer mask attachment, and non-destructive base layer preservation via headless GIMP test.

### Phase 34 — Non-Destructive Sky Selection & Replacement Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `sky-replacement` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/sky-replacement/sky-replacement.py`.
- [x] Create dedicated non-destructive Sky Replacement adjustment layer duplicating active drawable and creating an automated sky isolation mask.
- [x] Support physical Kelvin color temperature, exposure compensation, edge shift/fade feathering, curated atmospheric sky looks (Sunset Golden Hour, Dramatic Storm Clouds, Azure Clear Day, Deep Twilight, Pastel Sunrise Dawn, Custom sky adjustment).
- [x] Register under menu path `<Image>/Edit/Sky Replacement...`, `<Image>/Select/Sky Replacement...`, `<Image>/Filters/Retouching/Sky Replacement...`, and `<Image>/Layer`.
- [x] Validate sky mask generation, horizon edge isolation, color grading, and non-destructive base layer preservation via headless GIMP test.

### Phase 35 — Non-Destructive Select Subject & Foreground Isolation Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `select-subject` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/select-subject/select-subject.py`.
- [x] Create dedicated non-destructive Select Subject / Foreground Isolation helper that analyzes center-weighted saliency, edge contrast gradients, and alpha segmentation to automatically generate subject selections and layer masks.
- [x] Support mask refinement options: edge feathering (radius 0-50px), edge contraction/expansion (grow/shrink), contrast/smoothness refinement, inverted mask toggle (Select Subject vs Select Background), and non-destructive duplicate layer output with attached mask.
- [x] Support curated subject isolation presets (Portrait Subject, Crisp Product / Object, Soft Edge / Hair Refinement, Macro Foreground, Background Removal Matte, Custom sliders).
- [x] Register under menu path `<Image>/Select/Select Subject...`, `<Image>/Select/Select Background...`, `<Image>/Select/Remove Background...`, `<Image>/Filters/Retouching/Select Subject...`, and `<Image>/Layer`.
- [x] Validate automated subject mask generation, foreground protection, edge refinement, inverted background selection, and non-destructive source layer preservation via headless GIMP test.

### Phase 36 — Non-Destructive Color Range Selection & Isolation Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `color-range` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/color-range/color-range.py`.
- [x] Create dedicated non-destructive Color Range selection helper that allows selecting specific hues and tonal ranges (Sampled Colors, Skin Tones, Highlights, Midtones, Shadows, Reds, Yellows, Greens, Cyans, Blues, Magentas).
- [x] Support fuzziness / color tolerance slider (0 to 100), range spread, edge feathering, and non-destructive duplicate layer output with attached layer mask.
- [x] Register under menu path `<Image>/Select/Color Range...`, `<Image>/Filters/Retouching/Color Range...`, and `<Image>/Layer`.
- [x] Validate color range extraction, skin tone detection, fuzziness weighting, layer mask generation, and non-destructive base layer preservation via headless GIMP test.

### Phase 37 — Non-Destructive Smart Sharpen & Optical Deconvolution Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `smart-sharpen` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/smart-sharpen/smart-sharpen.py`.
- [x] Create dedicated non-destructive Smart Sharpen adjustment layer duplicating active drawable and applying adaptive high-frequency edge sharpening while suppressing noise amplification.
- [x] Support blur removal algorithm types: Gaussian Blur, Lens Blur (optical aperture deconvolution), and Motion Blur (directional edge sharpening).
- [x] Support controls: Amount (1% to 500%), Radius (0.1 to 50.0px), Reduce Noise (0% to 100%), presets, and layer masks (Reveal All, Conceal All, Selection).
- [x] Register under menu path `<Image>/Filters/Enhance/Smart Sharpen...`, `<Image>/Filters/Retouching/Smart Sharpen...`, and `<Image>/Layer`.
- [x] Validate edge acutance enhancement, noise threshold protection, deconvolution mode selection, layer mask attachment, and non-destructive base layer preservation via headless GIMP test.

### Phase 38 — Non-Destructive Tilt-Shift & Miniature Blur Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `tilt-shift` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/tilt-shift/tilt-shift.py`.
- [x] Create dedicated non-destructive Tilt-Shift / Miniature adjustment layer duplicating active drawable and simulating selective tilt-shift lens depth of field.
- [x] Support linear focus band positioning (focal center, focus band width, transition feather gradient falloff), optical blur radius (1 to 100px), saturation boost for the miniature model effect, and orientation (Horizontal, Vertical, Diagonal).
- [x] Support curated photographic presets (Classic Miniature Model, Toy City Diorama, Subtle Portrait Shallow DOF, Vertical Architecture Tilt, Macro Miniature, Custom sliders).
- [x] Register under menu path `<Image>/Filters/Blur/Tilt-Shift Blur...`, `<Image>/Filters/Retouching/Tilt-Shift Blur...`, and `<Image>/Layer`.
- [x] Validate focal strip preservation, progressive gradient blur transition, miniature saturation boost, layer mask generation, and non-destructive base layer preservation via headless GIMP test.

### Phase 39 — Non-Destructive Lens Distortion & Perspective Correction Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `lens-distortion` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/lens-distortion/lens-distortion.py`.
- [x] Create dedicated non-destructive Lens Distortion & Optical Perspective correction adjustment layer duplicating active drawable and correcting optical aberrations.
- [x] Support geometric distortion correction modes: Barrel distortion correction (negative displacement to straighten curved wide-angle lines), Pincushion distortion correction (positive displacement to restore telephoto pinching), Curvature, and Angle of view.
- [x] Support integrated peripheral vignette illumination compensation (lightening darkened optical corners), curated presets (Wide-Angle Barrel Correction, Telephoto Pincushion Correction, Fisheye Defish, Architectural Perspective Flatten, Creative Fisheye Warp, Custom sliders), and non-destructive duplicate layer output with editable layer mask.
- [x] Register under menu path `<Image>/Filters/Distort/Lens Distortion...`, `<Image>/Filters/Retouching/Lens Distortion...`, and `<Image>/Layer`.
- [x] Validate barrel curvature flattening, pincushion expansion, corner luminance compensation, layer mask attachment, and non-destructive base layer preservation via headless GIMP test.

### Phase 40 — Non-Destructive Glowing Edges & Neon Stylize Filter Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `glowing-edges` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/glowing-edges/glowing-edges.py`.
- [x] Create dedicated non-destructive Glowing Edges / Neon Stylize adjustment layer duplicating active drawable and isolating luminous edge contours.
- [x] Support edge detection and glowing light properties: Edge Width / Radius (0.1 to 20.0px), Edge Brightness / Intensity (0.0 to 10.0), Smoothness / Pre-filtering, and Neon color grading modes (Full Neon Spectral, Electric Cyan, Hot Magenta, Laser Green, Golden Amber, Monochrome White).
- [x] Support compositing blend modes (Screen, Addition, Soft Light, Normal), layer opacity (10% to 100%), and attached editable layer mask (Reveal All, Conceal All, Selection).
- [x] Register under menu path `<Image>/Filters/Artistic/Glowing Edges...`, `<Image>/Filters/Stylize/Glowing Edges...`, and `<Image>/Layer`.
- [x] Validate edge luminance extraction, neon glow colorization, layer mask attachment, and non-destructive base layer preservation via headless GIMP test.

### Phase 41 — Non-Destructive Oil Paint & Fine Art Impasto Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `oil-paint` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/oil-paint/oil-paint.py`.
- [x] Create dedicated non-destructive Oil Paint & Fine Art Impasto adjustment layer duplicating active drawable and simulating thick oil brush strokes and canvas texture.
- [x] Support painterly stroke parameters: Stylization (stroke clustering radius 1 to 30 via gegl:snn-mean), Cleanliness / Smoothness (0.0 to 10.0), Brush Scale / Impasto relief thickness (0.1 to 10.0), Bristle Detail (micro-grooves in stroke flow), and Directional Surface Lighting (Light Angle 0° to 360°, Shine / Specular luster 0.0 to 5.0).
- [x] Support curated artistic presets (Classic Impressionist Oil, Thick Impasto Palette Knife, Smooth Glaze Portrait, Expressionist Dynamic, Fine Canvas Detail, Custom sliders).
- [x] Register under menu path `<Image>/Filters/Artistic/Oil Paint...`, `<Image>/Filters/Stylize/Oil Paint...`, and `<Image>/Layer`.
- [x] Validate painterly stroke clustering, high-frequency edge preservation, surface relief shine response, layer mask attachment, and non-destructive base layer preservation via headless GIMP test.

### Phase 42 — Non-Destructive Iris Blur & Vignette Bokeh Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `iris-blur` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/iris-blur/iris-blur.py`.
- [x] Create dedicated non-destructive Iris Blur adjustment layer duplicating active drawable and simulating optical Blur Gallery iris depth-of-field.
- [x] Support elliptical focal region controls: focal center (x, y), in-focus subject radius, ellipse proportion, squeeze (-1.0 to 1.0), transition feather falloff, rotation angle, optical blur radius (1 to 100px), and optical bokeh specular highlight boost.
- [x] Support curated photographic presets (Portrait Face Isolation, Macro Subject Pinpoint, Street Photography Candid, Cinematic Anamorphic Oval, Vignette Peripheral Softness, Custom sliders).
- [x] Register under menu path `<Image>/Filters/Blur/Iris Blur...`, `<Image>/Filters/Blur Gallery/Iris Blur...`, `<Image>/Filters/Retouching`, and `<Image>/Layer`.
- [x] Validate inner focal zone pin-sharp preservation, elliptical gradient falloff, outer defocus depth, layer mask attachment, and non-destructive base layer preservation via headless GIMP test.

### Phase 43 — Non-Destructive HDR Toning & Tone Mapping Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `hdr-toning` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/hdr-toning/hdr-toning.py`.
- [x] Create dedicated non-destructive HDR Toning adjustment layer duplicating active drawable and simulating Photoshop Image > Adjustments > HDR Toning / tone mapping without flattening layers.
- [x] Support tone mapping methods (Local Adaptation via Mantiuk/Fattal, Equalize Contrast, Exposure and Gamma, Highlight Compression), Edge Glow detail radius and strength, Tone and Detail boost, Exposure (-5.0 to +5.0 EV), Gamma (0.1 to 3.0 via gimp-drawable-levels), and Color Vibrance/Saturation.
- [x] Support curated photographic presets (Default Photorealistic, High Dynamic Vivid, Dramatic Monochrome, Architectural Crisp, Surreal Dreamy, Night Cityglow, Custom sliders).
- [x] Register under menu path `<Image>/Image/Adjustments/HDR Toning...`, `<Image>/Filters/Enhance/HDR Toning...`, `<Image>/Filters/Retouching`, and `<Image>/Layer`.
- [x] Validate tone-mapping dynamic range expansion, shadow/highlight recovery, microcontrast detail enhancement, layer mask generation, and non-destructive base layer preservation via headless GIMP test.

### Phase 44 — Non-Destructive Match Color & Perceptual Color Transfer Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `match-color` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/match-color/match-color.py`.
- [x] Create dedicated non-destructive Match Color adjustment layer duplicating active drawable and simulating Photoshop Image > Adjustments > Match Color.
- [x] Support color transfer controls: Luminance (1% to 200%), Color Intensity / Saturation (1% to 200%), Fade (0% to 100%), and Neutralize color cast toggle.
- [x] Support curated grading palettes (Warm Golden Hour, Cool Cinema Blue, Vintage Film Tone, Lush Foliage Emerald, Skin Tone Harmony, Sunset Crimson, Neutralize Only, Custom palette) and multi-layer / multi-image source sampling.
- [x] Register under menu path `<Image>/Image/Adjustments/Match Color...`, `<Image>/Colors/Match Color...`, `<Image>/Filters/Retouching`, and `<Image>/Layer`.
- [x] Validate perceptual color statistics transfer, luminance scaling, cast neutralization, fade opacity blending, layer mask attachment, and non-destructive base layer preservation via headless GIMP test.

### Phase 45 — Non-Destructive Apply Image & Channel Math Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `apply-image` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/apply-image/apply-image.py`.
- [x] Create dedicated non-destructive Apply Image & Channel Math helper duplicating active drawable and simulating Photoshop Image > Apply Image and Image > Calculations.
- [x] Support source channel selection (Composite RGB, Red, Green, Blue, Alpha, Luminance, Invert channel), blending modes (Multiply, Screen, Overlay, Soft Light, Subtract, Add, Normal, Difference, Linear Light, etc.), Opacity (1% to 100%), Offset, Scale, and Mask blending.
- [x] Support darkroom composite techniques (Frequency Separation texture extraction, Luminosity channel extraction, High-contrast dodge/burn math).
- [x] Register under menu path `<Image>/Image/Apply Image...`, `<Image>/Image/Calculations...`, `<Image>/Filters/Retouching`, and `<Image>/Layer`.
- [x] Validate channel extraction, blend mode math, invert flag, offset/scale scaling, layer mask attachment, and non-destructive base layer preservation via headless GIMP test.

### Phase 46 — Non-Destructive Replace Color & Targeted Object Recoloring Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `replace-color` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/replace-color/replace-color.py`.
- [x] Create dedicated non-destructive Replace Color adjustment layer duplicating active drawable and simulating Photoshop Image > Adjustments > Replace Color.
- [x] Support color replacement pipeline: target sample color (R, G, B), Fuzziness tolerance (0 to 100) generating smooth alpha/layer mask falloff, Hue shift (-180° to +180°), Saturation shift (-100 to +100), Lightness shift (-100 to +100), and Colorize mode option.
- [x] Support blend modes (Color, Hue, Normal, Soft Light), layer opacity, and editable layer mask options (Fuzziness Mask, Selection, Reveal All).
- [x] Register under menu path `<Image>/Image/Adjustments/Replace Color...`, `<Image>/Colors/Replace Color...`, `<Image>/Filters/Retouching`, and `<Image>/Layer`.
- [x] Validate targeted color isolation, fuzziness mask falloff, hue/saturation/lightness remapping, layer mask generation, and non-destructive base layer preservation via headless GIMP test.

### Phase 47 — Non-Destructive Lens Blur & Optical Depth of Field Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `lens-blur` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/lens-blur/lens-blur.py`.
- [x] Create dedicated non-destructive Lens Blur adjustment layer duplicating active drawable and simulating Photoshop Filter > Blur > Lens Blur.
- [x] Support optical depth-of-field controls: Iris radius (0 to 100px), Specular Highlights boost (factor 0.0 to 1.0, threshold 0.0 to 1.0), Depth Map source (Radial Gradient, Linear Depth Gradient, Uniform, Selection), and monochromatic film grain noise.
- [x] Support curated photographic presets (Portrait Fast Prime f/1.4, Street Photography Shallow DOF f/2.0, Macro Extreme Bokeh f/1.2, Dreamy Specular Bokeh, Uniform Defocus, Custom sliders).
- [x] Register under menu path `<Image>/Filters/Blur/Lens Blur...`, `<Image>/Filters/Blur Gallery/Lens Blur...`, `<Image>/Filters/Retouching`, and `<Image>/Layer`.
- [x] Validate focal plane preservation, aperture bokeh circle formation, specular highlight boost, depth map mask generation, and non-destructive base layer preservation via headless GIMP test.

### Phase 48 — Non-Destructive Texturizer & Surface Canvas Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `texturizer` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/texturizer/texturizer.py`.
- [x] Create dedicated non-destructive Texturizer adjustment layer duplicating active drawable and simulating Photoshop Filter > Texture > Texturizer / Filter Gallery surface texturing.
- [x] Support classic surface textures: Canvas, Burlap, Brick, Sandstone, Fine Paper Grain, with scaling (50% to 200%), relief depth (1 to 50), and directional lighting (Top, Top-Left, Left, Bottom-Left, Bottom, Bottom-Right, Right, Top-Right).
- [x] Support curated artistic presets (Gallery Fine Art Canvas, Rustic Burlap Weave, Weathered Brickwork, Architectural Sandstone, Subtle Paper Grain, Custom sliders).
- [x] Register under menu path `<Image>/Filters/Artistic/Texturizer...`, `<Image>/Filters/Texture/Texturizer...`, `<Image>/Filters/Retouching`, and `<Image>/Layer`.
- [x] Validate surface relief bump mapping, lighting angle response, relief scaling, layer mask generation, and non-destructive base layer preservation via headless GIMP test.

### Phase 49 — Guide Layout & Compositional Alignment Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `guide-layout` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/guide-layout/guide-layout.py`.
- [x] Create dedicated Guide Layout helper simulating Photoshop View > New Guide Layout and View > Guides > Clear Guides.
- [x] Support classic photographic and graphic design compositional guides: Rule of Thirds (3x3 grid), Golden Ratio / Phi Grid (1:0.618:1), Center Crosshairs (50% H & V), Margin Guides (top/bottom/left/right margins), and Modular Columns & Rows (custom columns/rows with gutters).
- [x] Support options: clear existing guides toggle, custom gutter width (px), custom margin percentages, horizontal and vertical orientation toggles.
- [x] Register under menu path `<Image>/View/Guides/New Guide Layout...`, `<Image>/Image/Guides/New Guide Layout...`, and `<Image>/View/Guides/Clear All Guides`.
- [x] Validate guide placement coordinates, rule-of-thirds offsets, golden-ratio geometry, margin spacing, clear guides action, and headless GIMP test suite.

### Phase 50 — Frame Animation & Tweening Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `frame-animation` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/frame-animation/frame-animation.py`.
- [x] Create dedicated Frame Animation helper simulating Photoshop Timeline > Create Frame Animation and Tweening controls.
- [x] Support animation setup: uniform frame delay (ms / standard FPS presets: 12 fps, 24 fps, 30 fps, 10 fps), frame disposal mode (`replace` vs `combine`), ping-pong reverse loop creation, and crossfade opacity tweening between adjacent keyframes.
- [x] Register under menu path `<Image>/Filters/Animation/Frame Animation Setup...`, `<Image>/Image/Animation/Frame Animation Setup...`, `<Image>/Filters/Animation/Create Tween Frames...`, `<Image>/Filters/Animation/Ping-Pong Loop...`, and `<Image>/Filters/Animation/Remove Animation Tags`.
- [x] Validate frame delay formatting in layer names, disposal tags, tween layer interpolation, ping-pong sequence generation, and headless GIMP test suite.

### Phase 51 — Seamless Pattern Generator & Tile Preview Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `seamless-pattern` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/seamless-pattern/seamless-pattern.py`.
- [x] Create dedicated Seamless Pattern & Tile Preview helper simulating Photoshop Pattern Maker, Pattern Preview, and Edit > Fill > Pattern workflows.
- [x] Support seamless tile synthesis methods: edge-wrap blending with adjustable feather/overlap width (5-50%), 4-quadrant kaleidoscope / symmetrical mirroring for 100% boundary continuity, and multi-repetition tiled preview (2x2, 3x3, 4x4 tiling grid on expanded preview canvas).
- [x] Register under menu path `<Image>/Filters/Map/Create Seamless Pattern Tile...`, `<Image>/View/Pattern Tile Preview...`, and `<Image>/Edit/Fill with Pattern Tile...`.
- [x] Validate seamless edge continuity, kaleidoscope symmetry, multi-tile preview dimensions, layer mask attachment, base layer pixel preservation, and headless GIMP test suite.

### Phase 52 — Non-Destructive Selection & Layer Stroke Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `stroke-layer` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/stroke-layer/stroke-layer.py`.
- [x] Create dedicated Non-Destructive Stroke Layer helper simulating Photoshop `Edit > Stroke...` and Layer Style Stroke effect.
- [x] Support stroke position geometries: `inside`, `center`, and `outside` relative to active selection boundary or layer alpha boundary.
- [x] Support stroke width (1 to 100px), stroke color (Foreground, Black, White, Custom RGB), layer blend modes (Normal, Multiply, Screen, Overlay, Soft Light), layer opacity, and dedicated stroke layer generation preserving base layers (`diff == 0.000000`).
- [x] Register under menu path `<Image>/Edit/Stroke Selection (Non-Destructive)...`, `<Image>/Layer/Stroke Layer...`, and `<Image>/Filters/Retouching`.
- [x] Validate stroke width, positioning (inside/center/outside), color fidelity, blend mode assignment, non-destructive layer preservation, and headless GIMP test suite.

### Phase 53 — Non-Destructive Solid Color Fill Layer & Canvas Fill Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `solid-color-fill` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/solid-color-fill/solid-color-fill.py`.
- [x] Create dedicated Solid Color Fill Layer helper simulating Photoshop `Layer > New Fill Layer > Solid Color...` and `Edit > Fill...` (Contents: Color).
- [x] Support color sources: Foreground Color, Background Color, 50% Neutral Gray (#808080), Solid Black (#000000), Solid White (#ffffff), and Custom RGB sliders.
- [x] Support fill scopes: Full canvas document fill or active selection confinement.
- [x] Support blend modes (Normal, Multiply, Screen, Overlay, Soft Light, Color), opacity (0-100%), and editable layer masks (Reveal-All, Conceal-All, Active Selection), preserving underlying base artwork (`diff == 0.000000`).
- [x] Register under menu path `<Image>/Layer/New Fill Layer/Solid Color...`, `<Image>/Edit/Fill with Solid Color...`, and `<Image>/Filters/Retouching`.
- [x] Validate color accuracy across all presets, selection mask confinement, blend mode assignment, opacity scaling, non-destructive base layer preservation, and headless GIMP test suite.

### Phase 54 — Non-Destructive Gradient Fill Layer & Multi-Style Gradient Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `gradient-fill` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/gradient-fill/gradient-fill.py`.
- [x] Create dedicated Gradient Fill Layer helper simulating Photoshop `Layer > New Fill Layer > Gradient...` and Gradient tool fill workflows (`Topics.txt` lines 101, 342, 343; `photoshop_docs.md` Section 336-337).
- [x] Support gradient types / styles: Linear, Radial, Angle (conical asymmetric 360° sweep), Reflected (symmetric bilateral linear), and Diamond (shaped).
- [x] Support gradient color presets (Foreground to Background, Foreground to Transparent, Black to White, Neutral Vintage Warm, Sunset Horizon, Cyberpunk Neon, Metallic Silver) and custom start/end colors.
- [x] Support gradient controls: Angle (-180° to 180°), Scale (10% to 200%), Reverse gradient toggle, Dither toggle, blend modes (Normal, Multiply, Screen, Overlay, Soft Light, HSL Color), opacity (0-100%), and attached editable layer masks (Reveal-All, Conceal-All, Active Selection).
- [x] Register under menu path `<Image>/Layer/New Fill Layer/Gradient...`, `<Image>/Edit/Fill with Gradient...`, and `<Image>/Filters/Retouching`.
- [x] Validate gradient style geometry, angle rotation, scale expansion, color transition accuracy, reverse toggle, blend modes, layer mask attachment, and non-destructive base layer preservation via headless GIMP test suite.

### Phase 55 — Non-Destructive Exposure Adjustment Layer & Tonal Range Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `exposure` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/exposure/exposure.py`.
- [x] Create dedicated Exposure adjustment layer simulating Photoshop `Layer > New Adjustment Layer > Exposure...` and `Image > Adjustments > Exposure...` (`Topics.txt` lines 93-96, 347; `photoshop_docs.md` Section 338 lines 9935-9985).
- [x] Support Photoshop three-parameter exposure tone equation: $I' = ((I \cdot 2^{\text{exposure}}) + \text{offset})^{1 / \text{gamma}}$ in linear RGB color space:
  - `exposure`: -5.0 to +5.0 EV stops (default 0.0, highlight scaling).
  - `offset`: -0.5 to +0.5 (default 0.0, shadow/black point additive adjustment).
  - `gamma`: 0.01 to 9.99 (default 1.0, midtone power curve correction).
- [x] Support curated photographic exposure presets (Default / Reset, +1 Stop Overexposure, +2 Stops Overexposure, -1 Stop Underexposure, -2 Stops Underexposure, Shadow Boost / Lift, Highlight Recovery, High Dynamic Compression, Custom sliders).
- [x] Support non-destructive layer workflow: duplicates active drawable into dedicated adjustment layer, applies exposure transformation, attaches editable layer mask (Auto, None, Reveal-All, Conceal-All, Active Selection), blend modes (Normal, Luminosity, Multiply, Screen, Overlay, Soft Light), and opacity.
- [x] Register under menu path `<Image>/Layer/New Adjustment Layer/Exposure...`, `<Image>/Image/Adjustments/Exposure...`, and `<Image>/Filters/Retouching`.
- [x] Validate EV stop scaling, shadow offset response, gamma midtone power curve, preset fidelity, blend modes, layer mask generation, and non-destructive base layer preservation via headless GIMP test suite.

### Phase 56 — Non-Destructive Drop Shadow Layer Style Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `drop-shadow` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/drop-shadow/drop-shadow.py`.
- [x] Create dedicated Drop Shadow Layer Style helper simulating Photoshop `Layer > Layer Style > Drop Shadow...` (`Topics.txt` lines 107-118, 432; `photoshop_docs.md` Section 113-114 lines 3433-3500).
- [x] Support Photoshop Layer Style Drop Shadow parameters: Angle (-180° to 180°), Distance (0 to 200px), Spread (0 to 100%), Size / Blur Radius (0 to 200px), Opacity (0 to 100%), Shadow Color (Custom RGB or Black), Blend Mode (Multiply, Normal, Darken, Linear Burn), Noise / Graininess (0 to 100%), and Layer Knocks Out Drop Shadow toggle.
- [x] Support non-destructive shadow layer positioning directly beneath target layer, editable layer mask attachment, and 100% preservation of source layer artwork (`diff == 0.000000`).
- [x] Register under menu path `<Image>/Layer/Layer Style/Drop Shadow...`, `<Image>/Filters/Light and Shadow/Drop Shadow (Layer Style)...`, and `<Image>/Filters/Retouching`.
- [x] Validate angle offset trigonometry, distance translation, spread expansion, size gaussian falloff, knockout clipping, and headless GIMP test suite.

### Phase 57 — Channel Calculations & Two-Source Blending Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `calculations` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/calculations/calculations.py`.
- [x] Create dedicated Calculations dialog simulating Photoshop `Image > Calculations...` (`Topics.txt` line 350; `photoshop_docs.md` Section 340).
- [x] Support two-source channel blending: Source 1 (Image/Layer, Channel: Gray, Red, Green, Blue, Alpha, Invert toggle), Source 2 (Image/Layer, Channel: Gray, Red, Green, Blue, Alpha, Invert toggle), Blending Mode (Multiply, Screen, Overlay, Soft Light, Hard Light, Normal, Darken, Lighten, Difference, Subtract, Add), Scale and Offset calibration, Opacity (0 to 100%), and Mask option.
- [x] Support output destinations: New Document, New Channel, New Layer, or Selection.
- [x] Register under menu path `<Image>/Image/Calculations...`, `<Image>/Select/Calculations...`, and `<Image>/Filters/Retouching`.
- [x] Validate cross-channel math, invert operations, subtraction/addition formulas, selection output generation, and headless GIMP test suite.

### Phase 58 — Non-Destructive Outer Glow Layer Style Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `outer-glow` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/outer-glow/outer-glow.py`.
- [x] Create dedicated Outer Glow Layer Style helper simulating Photoshop `Layer > Layer Style > Outer Glow...` (`Topics.txt` lines 107-118; `photoshop_docs.md` Section 113-115).
- [x] Support Photoshop Outer Glow parameters: Blend Mode (Screen, Normal, Lighten, Color Dodge, Linear Dodge / Add), Opacity (0 to 100%), Noise (0 to 100%), Color (Solid Color RGB), Technique (Softer / Precise), Spread (0 to 100%), Size / Blur Radius (0 to 200px), Range contour falloff (1% to 100%), and curated style presets (Neon Cyberpunk, Soft Warm Halo, Golden Radiance, Ethereal White, Magical Magenta, Radioactive Green, Subtle Soft, Custom).
- [x] Support non-destructive glow layer placement immediately beneath parent layer, silhouette knockout clipping, editable layer mask attachment, and 100% preservation of source layer artwork (`diff == 0.000000`).
- [x] Register under menu path `<Image>/Layer/Layer Style/Outer Glow...`, `<Image>/Filters/Light and Shadow/Outer Glow (Layer Style)...`, and `<Image>/Filters/Retouching`.
- [x] Validate spread dilation, gaussian blur softness falloff, noise injection, glow color fidelity, blend modes, and headless GIMP test suite.

### Phase 59 — Non-Destructive Pattern Fill Layer & Pattern Overlay Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `pattern-fill` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/pattern-fill/pattern-fill.py`.
- [x] Create dedicated Pattern Fill Layer helper simulating Photoshop `Layer > New Fill Layer > Pattern...`, `Layer > Layer Style > Pattern Overlay...`, and `Edit > Fill...` (Contents: Pattern) (`Topics.txt` lines 356, 361-364; `photoshop_docs.md` Section 113-115).
- [x] Support Photoshop Pattern Fill parameters: Pattern selection (checkerboard, diagonal stripes, grid mesh, polka dots, halftone dots, carbon fiber, active GIMP pattern), Scale (10% to 500%), Angle (-180° to 180°), Color 1 and Color 2 RGB palette swatches, Opacity (0 to 100%), Blend Mode (Normal, Multiply, Screen, Overlay, Soft Light, HSL Color), and fill scope (Full canvas Pattern Fill Layer with selection mask, Selection Only, or In-Place with preserve transparency).
- [x] Support non-destructive pattern layer creation, editable layer mask attachment (Auto, None, Reveal-All, Conceal-All, Selection), and 100% preservation of underlying artwork (`diff == 0.000000`).
- [x] Register under menu path `<Image>/Layer/New Fill Layer/Pattern...`, `<Image>/Layer/Layer Style/Pattern Overlay...`, `<Image>/Edit/Fill with Pattern...`, and `<Image>/Filters/Retouching`.
- [x] Validate pattern scaling, repetition tiling, rotation angle, selection mask confinement, blend mode assignment, and headless GIMP test suite.

### Phase 60 — Non-Destructive Inner Glow Layer Style Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `inner-glow` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/inner-glow/inner-glow.py`.
- [x] Create dedicated Inner Glow Layer Style helper simulating Photoshop `Layer > Layer Style > Inner Glow...` (`Topics.txt` lines 107-118; `photoshop_docs.md` Section 113-115 lines 3433-3500).
- [x] Support Photoshop Inner Glow parameters: Blend Mode (Screen, Normal, Lighten, Color Dodge, Linear Dodge / Add, Overlay, Multiply), Opacity (0 to 100%), Noise (0 to 100%), Glow Color (Solid Color RGB), Technique (Softer / Precise), Source (Edge / Center), Choke (0 to 100%), Size / Blur Radius (0 to 200px), Range contour falloff (1% to 100%), and curated style presets (Neon Edge Radiance, Candlelight Warmth, Center Spotlight, Cyberpunk Core, Subtle Rim Inset, Custom Sliders).
- [x] Support non-destructive glow layer placement clipped to parent layer contents, editable layer mask attachment, and 100% preservation of source layer artwork (`diff == 0.000000`).
- [x] Register under menu path `<Image>/Layer/Layer Style/Inner Glow...`, `<Image>/Filters/Light and Shadow/Inner Glow (Layer Style)...`, and `<Image>/Filters/Retouching`.
- [x] Validate edge/center radiance, choke contraction, blur size falloff, noise injection, glow color fidelity, blend modes, and headless GIMP test suite.

### Phase 61 — Non-Destructive Inner Shadow Layer Style Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `inner-shadow` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/inner-shadow/inner-shadow.py`.
- [x] Create dedicated Inner Shadow Layer Style helper simulating Photoshop `Layer > Layer Style > Inner Shadow...` (`Topics.txt` lines 107-118; `photoshop_docs.md` Section 113-115 lines 3433-3500).
- [x] Support Photoshop Inner Shadow parameters: Angle (-180° to 180° with directional light trigonometry), Distance (0 to 200px), Choke (0 to 100% boundary contraction prior to blur), Size / Blur Radius (0 to 200px), Opacity (0 to 100%), Shadow Color (Custom RGB or Black), Blend Mode (Multiply, Normal, Darken, Color Burn, Linear Burn), Noise / Graininess (0 to 100%), and curated presets (Standard Inset, Deep Carved Inset, Subtle Bevel Inset, Soft Ambient Inset, Hard Edge Cutout, Custom Sliders).
- [x] Support non-destructive shadow layer placement clipped strictly inside parent layer silhouette, editable layer mask attachment, and 100% preservation of source layer artwork (`diff == 0.000000`).
- [x] Register under menu path `<Image>/Layer/Layer Style/Inner Shadow...`, `<Image>/Filters/Light and Shadow/Inner Shadow (Layer Style)...`, and `<Image>/Filters/Retouching`.
- [x] Validate angle offset trigonometry, distance translation, choke contraction, size gaussian falloff, silhouette clipping, noise injection, and headless GIMP test suite.

### Phase 62 — Non-Destructive Color Overlay Layer Style Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `color-overlay` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/color-overlay/color-overlay.py`.
- [x] Create dedicated Color Overlay helper simulating Photoshop `Layer > Layer Style > Color Overlay...` (`Topics.txt` lines 107-118, 432; `photoshop_docs.md` Section 113-115 lines 3433-3500).
- [x] Support Photoshop Color Overlay parameters: Solid Color RGB swatch (0.0 to 1.0), Blend Mode (Normal, Multiply, Screen, Overlay, Soft Light, Color, Darken, Lighten), Opacity (0 to 100%), Curated Presets (Standard Red, Warm Amber, Cool Cyan, Emerald Green, Royal Purple, Pure White, Deep Black, Monochrome Tint, Custom), and strict silhouette clipping to target layer pixels.
- [x] Support non-destructive overlay layer placement directly above target layer, editable layer mask attachment (Auto, None, Reveal-All, Conceal-All, Selection), and 100% preservation of source layer artwork (`diff == 0.000000`).
- [x] Register under menu path `<Image>/Layer/Layer Style/Color Overlay...`, `<Image>/Filters/Light and Shadow/Color Overlay (Layer Style)...`, and `<Image>/Filters/Retouching`.
- [x] Validate solid color rendering, silhouette clipping, blend modes, opacity scaling, presets, layer mask attachment, and headless GIMP test suite.

### Phase 63 — Non-Destructive Gradient Overlay Layer Style Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `gradient-overlay` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/gradient-overlay/gradient-overlay.py`.
- [x] Create dedicated Gradient Overlay helper simulating Photoshop `Layer > Layer Style > Gradient Overlay...` (`Topics.txt` lines 107-118, 432; `photoshop_docs.md` Section 113-115 lines 3433-3500).
- [x] Support Photoshop Gradient Overlay parameters: 5 Geometry styles (Linear, Radial, Angle, Reflected, Diamond), Angle (-180° to 180°), Scale (10% to 500%), Reverse toggle, Dither anti-banding toggle, Align with Layer centering, Presets (Black-White, FG-BG, Vintage Sepia, Sunset Horizon, Cyberpunk Neon, Ocean Breeze, Golden Glow, Custom dual-tone RGB), Blend Modes (Normal, Multiply, Screen, Overlay, Soft Light, Color, Darken, Lighten), Opacity (0 to 100%), and strict silhouette clipping to target layer pixels.
- [x] Support non-destructive overlay layer placement immediately above target layer, editable layer mask attachment (Auto, None, Reveal-All, Conceal-All, Selection), and 100% preservation of source layer artwork (`diff == 0.000000`).
- [x] Register under menu path `<Image>/Layer/Layer Style/Gradient Overlay...`, `<Image>/Filters/Light and Shadow/Gradient Overlay (Layer Style)...`, and `<Image>/Filters/Retouching`.
- [x] Validate gradient rendering, geometry scaling/rotation, silhouette clipping, blend modes, presets, and headless GIMP test suite (assertions GO-01 to GO-16).

### Phase 64 — Non-Destructive Pattern Overlay Layer Style Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `pattern-overlay` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/pattern-overlay/pattern-overlay.py`.
- [x] Create dedicated Pattern Overlay helper simulating Photoshop `Layer > Layer Style > Pattern Overlay...` (`Topics.txt` lines 107-118, 432; `photoshop_docs.md` Section 113-115 lines 3433-3500).
- [x] Support Photoshop Pattern Overlay parameters: Pattern selection (Checkerboard, Diagonal Stripes, Grid Mesh, Polka Dots, Halftone Dots, Carbon Fiber, Active GIMP Pattern), Scale (10% to 500%), Angle (-180° to 180°), Color 1 / Color 2 tinting swatches, Blend Mode (Normal, Multiply, Screen, Overlay, Soft Light, HSL Color, Darken, Lighten), Opacity (0% to 100%), Link with Layer coordinate alignment, and strict silhouette boundary clipping.
- [x] Support non-destructive overlay layer placement directly above target layer, editable layer mask attachment (Auto, None, Reveal-All, Conceal-All, Selection), and 100% preservation of source layer artwork (`diff == 0.000000`).
- [x] Register under menu path `<Image>/Layer/Layer Style/Pattern Overlay...`, `<Image>/Filters/Light and Shadow/Pattern Overlay (Layer Style)...`, and `<Image>/Filters/Retouching`.
- [x] Validate pattern tiling, rotation, scaling, silhouette boundary clipping, blend modes, and headless GIMP test suite (assertions PO-01 to PO-16).

### Phase 65 — Non-Destructive Satin Layer Style Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `satin` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/satin/satin.py`.
- [x] Create dedicated Satin Layer Style helper simulating Photoshop `Layer > Layer Style > Satin...` (`Topics.txt` lines 107-118, 432; `photoshop_docs.md` Section 113-115 lines 3433-3500: "Satin: Blend Mode, Opacity, Angle, Distance, Size, Contour, Invert").
- [x] Support Photoshop Satin parameters: Blend Mode (Multiply, Normal, Darken, Color Burn, Linear Burn, Soft Light, Overlay, Screen), Opacity (0% to 100%), Solid Color RGB swatch, Angle (-180° to 180° with dual directional offset trigonometry), Distance (0 to 200px), Size / Blur Radius (0 to 200px), Invert toggle (creates interior silk/satin specular sheen vs matte shadow), Contour falloff modulation, and film grain noise.
- [x] Support non-destructive overlay layer placement directly above target layer, strict silhouette boundary clipping ($A_{\text{overlay}} = A_{\text{satin}} \cdot A_{\text{target}}$), editable layer mask attachment, and 100% preservation of source layer artwork (`diff == 0.000000`).
- [x] Register under menu path `<Image>/Layer/Layer Style/Satin...`, `<Image>/Filters/Light and Shadow/Satin (Layer Style)...`, and `<Image>/Filters/Retouching`.
- [x] Validate dual offset distance casting, angle trigonometry, Gaussian blur size, invert specular sheen, silhouette boundary clipping, and headless GIMP test suite (assertions ST-01 to ST-16).

### Phase 66 — Non-Destructive Bevel and Emboss Layer Style Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `bevel-emboss` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/bevel-emboss/bevel-emboss.py`.
- [x] Create dedicated Bevel & Emboss helper simulating Photoshop `Layer > Layer Style > Bevel & Emboss...` (`Topics.txt` lines 107-118, 432; `photoshop_docs.md` Section 113-115 lines 3433-3610: "Bevel & Emboss: Style (Inner Bevel, Outer Bevel, Emboss, Pillow Emboss), Technique (Smooth, Chisel Hard, Chisel Soft), Depth, Direction (Up, Down), Size, Soften, Shading Angle & Altitude, Highlight Mode/Opacity, Shadow Mode/Opacity").
- [x] Support Photoshop Bevel & Emboss styles: Inner Bevel, Outer Bevel, Emboss, Pillow Emboss.
- [x] Support directional lighting trigonometry with Angle (-180° to 180°) and Altitude (0° to 90°), separate Highlight (Screen/Normal, custom color/opacity) and Shadow (Multiply/Normal, custom color/opacity) passes.
- [x] Support non-destructive overlay layer placement, editable layer mask attachment, and 100% preservation of source layer artwork (`diff == 0.000000`).
- [x] Register under menu path `<Image>/Layer/Layer Style/Bevel and Emboss...`, `<Image>/Filters/Light and Shadow/Bevel and Emboss (Layer Style)...`, and `<Image>/Filters/Retouching`.
- [x] Validate bevel styles, lighting angle/altitude, highlight/shadow separation, soften blur falloff, and headless GIMP test suite (assertions BE-01 to BE-16).

### Phase 67 — Non-Destructive Stroke Layer Style Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `stroke-style` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/stroke-style/stroke-style.py`.
- [x] Create dedicated Stroke Layer Style helper simulating Photoshop `Layer > Layer Style > Stroke...` (`Topics.txt` lines 107-118, 432; `photoshop_docs.md` Section 113-115 lines 3433-3500: "Stroke: Size, Position [Outside, Inside, Center], Blend Mode, Opacity, Overprint, Fill Type [Color, Gradient, Pattern]").
- [x] Support Photoshop Stroke positioning: Outside (stroke expands outward from silhouette boundary), Inside (stroke is inset strictly within layer content boundary), and Center (stroke is centered on boundary edge).
- [x] Support Fill Types: Solid Color RGB swatch, Gradient (Linear / Radial / Reflected with dual tones and angle/scale), and Pattern texture repetition.
- [x] Support non-destructive overlay layer placement (outside placed beneath target layer or inside placed above parent layer), editable layer mask attachment, and 100% preservation of source layer artwork (`diff == 0.000000`).
- [x] Register under menu path `<Image>/Layer/Layer Style/Stroke...`, `<Image>/Filters/Light and Shadow/Stroke (Layer Style)...`, and `<Image>/Filters/Retouching`.
- [x] Validate stroke positioning (Inside, Outside, Center), size dilation/erosion geometry, fill types, blend modes, opacity scaling, layer mask attachment, and headless GIMP test suite (assertions STRK-01 to STRK-16).

### Phase 68 — Global Lighting & Layer Style Effects Manager Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `layer-style-manager` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/layer-style-manager/layer-style-manager.py`.
- [x] Simulate Photoshop `Layer > Layer Style > Global Light...`, `Copy Layer Style`, `Paste Layer Style`, `Clear Layer Style`, and `Scale Effects...` (`Topics.txt` lines 111-120; `photoshop_docs.md` Section 116-121 lines 3550-3665).
- [x] Support unified Global Light azimuth angle and altitude across all directional layer styles (Drop Shadow, Inner Shadow, Bevel & Emboss).
- [x] Support copying style parameters across layers, clearing applied layer style containers, toggling style visibility, and scaling layer effect radii proportionally (10% to 500%).
- [x] Register under menu path `<Image>/Layer/Layer Style/Global Light...`, `<Image>/Layer/Layer Style/Scale Effects...`, `<Image>/Layer/Layer Style/Copy Layer Style`, `<Image>/Layer/Layer Style/Paste Layer Style`, and `<Image>/Layer/Layer Style/Clear Layer Style`.
- [x] Validate global angle synchronization, effect scaling arithmetic, style copy/paste persistence, and headless GIMP test suite.

### Phase 69 — Knockout Blending & Texture Cutout Effects Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `knockout-blending` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/knockout-blending/knockout-blending.py`.
- [x] Simulate Photoshop `Layer > Layer Style > Blending Options > Knockout` (Shallow / Deep) (`Topics.txt` line 120: "Create texture effects with Knockout"; `photoshop_docs.md` Section 124 lines 3684-3698: "Learn how to use the Knockout blending option to punch through layers and reveal underlying content for texture effects in photoeditor desktop... Knockout: Shallow punches through to group boundary; Deep punches through to background/base layer").
- [x] Support Shallow Knockout (punches through layers inside active layer group to reveal parent group backdrop) and Deep Knockout (punches through all intermediate layers down to base canvas).
- [x] Support Fill Opacity separation (0% to 100%) allowing layer effects (strokes, bevels, shadows) to remain visible while layer fill punches through.
- [x] Register under menu path `<Image>/Layer/Layer Style/Knockout Options...`, `<Image>/Layer/Blending Options/Knockout...`, and `<Image>/Filters/Retouching`.
- [x] Validate shallow and deep knockout transparency punching, fill opacity decoupling, and headless GIMP test suite.

### Phase 70 — Smart Filters & Non-Destructive Filter Effects Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `smart-filters` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/smart-filters/smart-filters.py`.
- [x] Simulate Photoshop `Filter > Convert for Smart Filters` and Smart Filter stack management (`Topics.txt` lines 454, 459: "Smart filters - Sharpening overview", "Apply and manage Smart Filters"; `photoshop_docs.md` Section 138 lines 4057-4066, Section 153 lines 4408-4434, Section 413-415 lines 12047-12115, Section 446 lines 13049-13056: "Apply Smart Filters", "Edit Smart Filters", "Smart Filter mask").
- [x] Support converting layers to Smart Object containers with pristine source content preservation, non-destructive filter passes (Gaussian Blur, Smart Sharpen, High Pass, Vignette, Noise Reduction, Diffuse Glow, Pixelize), attached Smart Filter mask, and re-editable filter parameters.
- [x] Support rasterizing Smart Filters permanently into a single raster layer (`python-fu-rasterize-smart-filters`) matching Photoshop `Layer > Rasterize > Smart Object`.
- [x] Support clearing Smart Filters (`python-fu-clear-smart-filters`) to discard filters and restore pristine source pixels with 100% fidelity (`diff == 0.000000`).
- [x] Register under menu path `<Image>/Filters/Smart Filters...`, `<Image>/Layer/Smart Objects/Convert for Smart Filters`, and `<Image>/Layer/Rasterize/Smart Object`.
- [x] Validate non-destructive filter re-application, filter mask preservation across edits, presets, and headless GIMP test suite (assertions SF-01 to SF-16).

### Phase 71 — Layer Comps & Composition Variations Manager Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `layer-comps` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/layer-comps/layer-comps.py`.
- [x] Simulate Photoshop `Window > Layer Comps` (`Topics.txt` lines 138-141; `photoshop_docs.md` Section 145 lines 4175-4268: "Create and manage layer comps - Capture multiple design variations in a single file using snapshots of layer visibility, position, and appearance... Create a new layer comp... Apply and view layer comps... Update a layer comp... Clear layer comp warnings... Delete a layer comp... Export layer comps to files").
- [x] Support capturing layer state snapshots (Visibility, Position / Offsets, Appearance / Opacity & Blend Mode), switching between comps, updating comps, cycle next/prev navigation, and exporting variations to PNG/JPEG.
- [x] Register under menu path `<Image>/Layer/Layer Comps`, `<Image>/Window/Layer Comps`, and `<Image>/File/Export`.
- [x] Validate snapshot persistence in image parasites (`photogimp/layer-comps`), selective property recording, missing layer resilience, file export, and headless GIMP test suite (assertions LC-01 to LC-16).

### Phase 72 — History States & Edit Session Audit Log Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `history-log` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/history-log/history-log.py`.
- [x] Simulate Photoshop `Edit > Preferences > History Log` and Snapshot Management (`Topics.txt` lines 34-40; `photoshop_docs.md` Section 41, 42, 45, 46, 47 lines 1040-1210: "Configure History Log settings: Customize History Log preferences in photoeditor to save logs in metadata, a text file, or both... Manage image states... Create temporary versions without saving to disk").
- [x] Support recording detailed non-destructive edit session history (metadata and external disk file), exporting audit logs, and creating named image state snapshots (Full Document, Merged Layers, Current Layer), with snapshot restoration and spawning new documents from snapshots.
- [x] Register under menu path `<Image>/Edit`, `<Image>/Edit/Preferences`, `<Image>/Window/History`, `<Image>/File/New`, and `<Image>/File/Export`.
- [x] Validate session history tracking, snapshot isolation, and headless GIMP test suite (assertions HL-01 to HL-16).

### Phase 73 — Placeholder Frames & Clipping Masks Layout Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `placeholder-frames` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/placeholder-frames/placeholder-frames.py`.
- [x] Simulate Photoshop Frame Tool (`Topics.txt` lines 150-155: "Draw frames", "Convert shapes or text to frames", "Place an image into a frame", "Select a frame and its content", "Add a stroke to a frame").
- [x] Support creating rectangular / elliptical placeholder frames, placing images into frames with auto-fitting (Fill, Fit, Stretch), and stroke boundary styling.
- [x] Register under menu path `<Image>/Layer/Frames...` and `<Image>/Tools/Transform Tools/Frame...`.
- [x] Validate frame container hierarchy, clipping mask geometry, and headless GIMP test suite (assertions PF-01 to PF-16).

### Phase 74 — Image Stacks Statistical Blending Helper Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `image-stacks` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/image-stacks/image-stacks.py`.
- [x] Simulate Photoshop Image Stacks (`Topics.txt` line 145: "Create and process image stacks"; `photoshop_docs.md` Section 149 lines 4440-4495: "Create and process image stacks... apply stack modes processing options that analyze corresponding pixels across all layers... Mean, Median, Maximum, Minimum, Range, Standard Deviation, Variance, Sum, Entropy, Skewness, Kurtosis, None... File > Scripts > Statistics... File > Scripts > Load Files into Stack... Edit > Auto-Align Layers... Layer > Smart Objects > Stack Mode... Layer > Smart Objects > Rasterize").
- [x] Support 12 statistical stack modes: Median (moving object removal), Mean (noise reduction), Maximum (star trails/light streaks), Minimum (shadow accumulation), Range (motion detection), StdDev, Variance, Sum (exposure accumulation), Entropy, Skewness, Kurtosis, and None (bypass rendering).
- [x] Support Smart Object image stack container (`photogimp/image-stack`), active composite layer (`photogimp/stack-composite`), multi-file loading (`python-fu-load-files-into-stack`), one-shot Statistics pipeline (`python-fu-statistics-stack`), phase-correlation auto-alignment (`python-fu-auto-align-stack`), and stack rasterization (`python-fu-rasterize-image-stack`).
- [x] Register under menu path `<Image>/Layer/Smart Objects/Image Stack`, `<Image>/Layer/Smart Objects/Stack Mode`, `<Image>/Layer/Smart Objects/Rasterize Stack`, `<Image>/Layer/Image Stacks`, `<Image>/File/Scripts/Load Files into Stack`, `<Image>/File/Scripts/Statistics`, and `<Image>/Edit/Auto-Align Layers`.
- [x] Validate stack container hierarchy, statistical algorithms, dynamic mode switching, phase correlation alignment, multi-file import, and headless GIMP test suite (assertions IS-01 to IS-18).

### Phase 75 — Artboards & Multi-Canvas Layout Manager Plugin
- [x] Implement native GIMP 3.x Python 3 plugin `artboards` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/artboards/artboards.py`.
- [x] Simulate Photoshop Artboards (`Topics.txt` lines 146-149: "Get started with artboards", "Artboard properties and behaviors", "Create artboard documents", "Add artboards to the current document"; `photoshop_docs.md` Section 150-153 lines 4498-4595: "Artboards are special layer groups that clip the contents of any contained elements to their boundaries... act as individual canvases within a document... Presets (Desktop, Mobile, Tablet, Social, Print)... Artboard from Layers... Artboard from Group... Duplicate Artboard... Export Artboards to Files").
- [x] Support 6 PDB procedures: `python-fu-create-artboard`, `python-fu-artboard-from-layers`, `python-fu-artboard-from-group`, `python-fu-duplicate-artboard`, `python-fu-resize-artboard`, and `python-fu-export-artboards`.
- [x] Support device presets (Desktop 1080p/1440p/4K, Mobile iPhone/Android, Tablet iPad, Social Square/Story, Print A4), non-destructive group boundary clipping masks, custom backgrounds, and standalone cropped batch export (PNG/JPEG).
- [x] Register under menu path `<Image>/Layer/Artboards`, `<Image>/Tools/Transform Tools/Artboard`, and `<Image>/File/Export/Export Artboards to Files...`.
- [x] Validate artboard container hierarchies, coordinate bounds, boundary mask clipping, duplication, resizing, multi-canvas coexistence, batch export, and headless GIMP test suite (assertions AB-01 to AB-18).

### Phase 76 — Content-Aware Scale & Intelligent Seam Carving Helper Plugin
- [ ] Implement native GIMP 3.x Python 3 plugin `content-aware-scale` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/content-aware-scale/content-aware-scale.py`.
- [ ] Simulate Photoshop `Edit > Content-Aware Scale` (`Topics.txt` lines 163-164: "Preserve visual content when scaling images", "Specify content to protect when scaling"; `photoshop_docs.md` Section 167 lines 4900-4960: "Resize images while preserving important visual content using Content-Aware Scale in photoeditor... Seam carving identifies high-energy features (people, buildings, foreground subjects) and preserves them while carving or expanding low-energy background areas... Amount slider (0% to 100%)... Protect Skin Tones toggle... Protect Alpha Channel / Selection mask").
- [ ] Support non-destructive scaling to custom target width and height, Amount slider (linear blend between uniform scaling and content-aware preservation), Protect Skin Tones detector, and custom protection channel/selection mask.
- [ ] Register under menu path `<Image>/Edit/Content-Aware Scale...` and `<Image>/Tools/Transform Tools/Content-Aware Scale...`.
- [ ] Validate aspect ratio retargeting, subject protection, skin tone preservation, amount interpolation, and headless GIMP test suite.


















