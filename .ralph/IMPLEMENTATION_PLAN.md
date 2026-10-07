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
- [ ] Implement native GIMP 3.x Python 3 plugin `glowing-edges` in `PhotoGIMP/.config/GIMP/3.0/plug-ins/glowing-edges/glowing-edges.py`.
- [ ] Create dedicated non-destructive Glowing Edges / Neon Stylize adjustment layer duplicating active drawable and isolating luminous edge contours.
- [ ] Support edge detection and glowing light properties: Edge Width / Radius (0.1 to 20.0px), Edge Brightness / Intensity (0.0 to 10.0), Smoothness / Pre-filtering, and Neon color grading modes (Full Neon Spectral, Electric Cyan, Hot Magenta, Laser Green, Golden Amber, Monochrome White).
- [ ] Support compositing blend modes (Screen, Addition, Soft Light, Normal), layer opacity (10% to 100%), and attached editable layer mask (Reveal All, Conceal All, Selection).
- [ ] Register under menu path `<Image>/Filters/Artistic/Glowing Edges...`, `<Image>/Filters/Stylize/Glowing Edges...`, and `<Image>/Layer`.
- [ ] Validate edge luminance extraction, neon glow colorization, layer mask attachment, and non-destructive base layer preservation via headless GIMP test.






