# Current Task

Status: COMPLETED

Task: Standardize default tool options for Photoshop behavior (selections, transform, crop) and add tool options audit to verify_config.py.
Why: PhotoGIMP lacks tool-options presets for standard selection tools (Rectangular Marquee, Elliptical Marquee, Lasso, Magic Wand, Color Select), causing them to fall back to arbitrary defaults. Also, gimp-crop-tool has a hardcoded 16:9 aspect constraint instead of Photoshop's free-form default.
Affected areas:
- PhotoGIMP/.config/GIMP/3.0/tool-options/gimp-crop-tool
- PhotoGIMP/.config/GIMP/3.0/tool-options/gimp-rect-select-tool
- PhotoGIMP/.config/GIMP/3.0/tool-options/gimp-ellipse-select-tool
- PhotoGIMP/.config/GIMP/3.0/tool-options/gimp-free-select-tool
- PhotoGIMP/.config/GIMP/3.0/tool-options/gimp-fuzzy-select-tool
- PhotoGIMP/.config/GIMP/3.0/tool-options/gimp-by-color-select-tool
- PhotoGIMP/.config/GIMP/3.0/tool-options/gimp-unified-transform-tool
- PhotoGIMP/scripts/verify_config.py

Acceptance criteria:
1. `gimp-rect-select-tool`, `gimp-ellipse-select-tool`, `gimp-free-select-tool` presets configure anti-aliasing enabled and feathering disabled by default. [PASSED]
2. `gimp-fuzzy-select-tool` (Magic Wand) and `gimp-by-color-select-tool` presets configure anti-aliasing enabled, transparent selection enabled, and Photoshop standard tolerance (threshold 32.0). [PASSED]
3. `gimp-crop-tool` preset removed forced 16:9 aspect ratio in favor of Photoshop-standard free-form crop. [PASSED]
4. `gimp-unified-transform-tool` preset configured with valid S-expression transform options. [PASSED]
5. `PhotoGIMP/scripts/verify_config.py` extended with Section 5 Tool Options audit. [PASSED]
6. `python3 PhotoGIMP/scripts/verify_config.py` passes with exit code 0. [PASSED]
7. `./PhotoGIMP/install.sh --batch` deploys updated tool-options to `~/.config/GIMP/3.2/tool-options/`. [PASSED]

Verification evidence:
- `python3 PhotoGIMP/scripts/verify_config.py` exited with code 0 (24 tool-options files validated, syntax clean, crop/wand properties verified).
- `./PhotoGIMP/install.sh --batch` exited with code 0, deploying options to `~/.config/GIMP/3.2/tool-options/`.
- Headless smoke test: `gimp --no-interface --console-messages --batch-interpreter=plug-in-script-fu-eval --batch '(begin (display "GIMP smoke test passed\n"))' --quit` passed with code 0.

Rollback/checkpoint: PhotoGIMP sub-repo commit 5a560e0.
