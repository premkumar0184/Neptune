# 🔱 Neptune — Professional Linux Photo Editor

Neptune is a professional, high-performance photo editing environment for Linux built on **GIMP 3.x native architecture**. It merges the full **Adobe Photoshop-grade feature completeness**, workflow ergonomics, and keyboard shortcuts with a modern, clean, and cohesive UI inspired by the **PhotoCraft** design language.

---

## 🌟 Key Highlights

- **Photoshop Feature Parity**: Native keyboard shortcut bindings aligned with Adobe Photoshop defaults (`Ctrl+J`, `Ctrl+T`, `Ctrl+L`, `Ctrl+M`, `Ctrl+U`, `B`, `E`, `V`, `M`, `L`, `W`, `C`, `J`, `S`, `T`, `Z`).
- **Single-Window Workspace**: Modernized single-window layout with dark theme overrides and a dedicated **History (Undo)** panel.
- **20+ Production GIMP 3.x Python 3 Retouching & Grading Plugins**:
  - **Frequency Separation**: High-frequency texture and low-frequency color splitting with non-destructive layer container.
  - **Luminosity Masks**: Automated 9-channel tonal selection generator (Lights, Darks, Midtones).
  - **Non-Destructive Dodge & Burn**: 50% neutral gray overlay layer with live brush dodging and burning.
  - **High Pass Sharpening**: Detail enhancement via GEGL high-pass filter with Soft Light blending.
  - **Quick Export Suite**: Fast one-click export to PNG and JPEG with scaling presets (1x, 2x, 0.5x).
  - **Vignette & Lens Lighting**: Non-destructive radial exposure falloff with highlight and shadow modes.
  - **Depth Defocus (Lens Blur)**: Non-destructive optical and Gaussian background defocus with depth mask.
  - **Shadows & Highlights Recovery**: Local dynamic range recovery with independent tone compression.
  - **Black & White Conversion & Toning**: Channel-weighted monochrome conversion and photographic sepia toning.
  - **Photo Filter Optical Effects**: Optical lens warming and cooling filters (85, 80, Deep Red, Cyan, Amber).
  - **Vibrance & Smart Saturation**: Intelligent saturation boosting protecting saturated skin tones.
  - **Color Balance & Tonal Grading**: 3-way color grading across Shadows, Midtones, and Highlights.
  - **Gradient Map & Cinematic Grading**: Multi-stop cinematic grading (Teal & Orange, Sepia, Cyberpunk, etc.).
  - **Channel Mixer & Infrared**: Cross-channel rebalancing and monochrome/infrared photography simulation.
  - **Color Temperature & White Balance**: Physical Kelvin temperature adjustment (1000K–12000K).
  - **Clarity & Dehaze**: Wide-radius midtone local contrast enhancement and atmospheric haze penetration.
  - **Film Grain & Analog Texture**: Authentic silver halide grain simulation (35mm, Medium Format, High-ISO Street).
  - **Light & Tonal Range**: Unified 6-point darkroom controls (Exposure, Contrast, Highlights, Shadows, Whites, Blacks).
  - **Duotone & Tritone Print Effects**: Editorial 2-ink and 3-ink tonal luminance mapping with midpoint balance curves.
- **Rigorous Automated Quality Gate**: 150+ automated behavioral regression tests executing headless in GIMP 3.x (`tests/gimp_e2e_suite.py`).
- **Zero-Cloud & 100% Offline**: Pure local desktop execution preserving privacy and data sovereignty.

---

## 🚀 Quick Start & Installation

### Requirements
- **Linux** (Ubuntu, Debian, Fedora, Arch, or Flatpak)
- **GIMP 3.0+** (GIMP 3.2+ recommended)
- **Python 3** with `PyGObject` (included with standard GIMP 3 installations)

### Automated Installation
Run GIMP once to initialize default configuration files, then run the Neptune / PhotoGIMP installer:

```bash
# Non-interactive batch installation to active native GIMP 3 configuration:
bash PhotoGIMP/install.sh --batch

# Or install for all detected GIMP 3 environments (Native + Flatpak):
bash PhotoGIMP/install.sh --all
```

The installer:
1. Creates an isolated timestamped backup of any existing GIMP configuration.
2. Installs the optimized single-window workspace, theme overrides, shortcuts, and tool presets.
3. Deploys all 20+ Python 3 plugins to your GIMP user configuration directory with executable permissions.
4. Registers the Neptune desktop launcher and multi-resolution icons.

---

## 🧪 Testing & Verification

Run the unified 3-stage quality gate:

```bash
# Audits configuration syntax, verifies deployment, and runs all 150+ headless GIMP tests:
python3 tests/run_all_tests.py
```

### Direct Headless Suite Execution:
```bash
gimp --no-interface --console-messages --batch-interpreter=python-fu-eval \
     --batch "exec(open('tests/gimp_e2e_suite.py').read())" --quit
```

---

## 📁 Repository Structure

```
├── .agents/               # Agent workflows, rules, and Ralph execution state
├── .ralph/                # Implementation roadmap, feature matrix, task logs, and progress
├── docs/                  # Smoke testing guides and technical documentation
├── PhotoGIMP/             # Core PhotoGIMP overlay, configuration files, and Python plugins
│   ├── .config/GIMP/3.0/  # gimprc, sessionrc, shortcutsrc, theme.css, plug-ins/
│   ├── .local/share/      # Desktop launcher and application icons
│   ├── install.sh         # Multi-target automated installer
│   └── scripts/           # Configuration verification and plugin audit scripts
├── tests/                 # Automated test runner and headless GIMP regression suite
├── Topics.txt             # Photoshop feature inventory and reference mapping
├── photoshop_docs.md      # Photoshop behavioral specification corpus
└── README.md              # Project documentation
```

---

## 📄 License

This project builds upon the open-source community contributions of PhotoGIMP (GPLv3) and GIMP (GPLv3/LGPLv3).
