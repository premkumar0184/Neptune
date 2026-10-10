# Current Task — Iteration 84

## Task
**UI Modernization — PhotoCraft Pro / Studio Theme & Styling (`theme.css`, `verify_config.py`)**

## Status
**COMPLETED**

## Rationale
Per `AGENTS.md` ("Turn PhotoGIMP into a polished Linux photo editor that keeps all of the Photoshop-style capability already added while adopting a cleaner, more premium, PhotoCraft-like visual and interaction language... modernize the UI shell, panel structure, theme, spacing, typography, and workspace behavior to feel closer to PhotoCraft; do not regress functionality while improving the visual experience") and user request:
1. **PhotoCraft Pro GTK3 Design System Tokens**:
   - Integrated PhotoCraft color tokens (`photocraft/crates/ui-egui/src/theme.rs` Pro / Studio dark theme):
     - Backgrounds: `#242426` window chrome, `#28282b` dockables/cards, `#1a1a1c` canvas surround, `#1c1c1e` borders.
     - Foregrounds: `#dedee2` primary text, `#96969e` dimmed text, `#686870` disabled text.
     - Accents: `#378ef0` PhotoCraft Spectrum blue accent with `#2680eb` hover and `#1a6edb` active states.
     - Inputs & Fields: `#1c1c1e` text input background, `1px solid #3c3c42` border, `#378ef0` focus outline, `#dedee2` text.
2. **PhotoCraft Action Elements**:
   - Flat, sleek notebook tab strips (`notebook header tabs tab`) with subtle padding, `#378ef0` active indicator, and clean hover states.
   - PhotoCraft pill buttons: `button.suggested-action` and `button.default` styled as Spectrum blue pill buttons (`border-radius: 14px`), and `.text-button` styled as secondary dark pill buttons.
   - Sleek precision sliders (`scale contents trough`, `scale slider`) and `GimpSpinScale` compound controls with accent progress fills and clean white/light circular thumbs matching PhotoCraft's Curves/Levels inspectors.
   - Clean dropdown menus, popovers with subtle box shadows (`0 8px 24px rgba(0,0,0,0.5)`), modern compact statusbar, and slim scrollbars.
3. **Automated Verification**:
   - Added `check_theme_photocraft_tokens` to `PhotoGIMP/scripts/verify_config.py` Section 3 to ensure tokens are audited and preserved.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/theme.css`: Comprehensive GTK3 stylesheet implementing PhotoCraft Pro/Studio theme.
- `PhotoGIMP/scripts/verify_config.py`: Added `check_theme_photocraft_tokens` to Workspace Configuration Audit (Section 3).
- `PhotoGIMP/install.sh`: Deployed modern theme to `~/.config/GIMP/3.2/`.
- `.ralph/CURRENT_TASK.md`: Updated for Iteration 84.
- `.ralph/PROGRESS.md`: Logged Iteration 84.
- `.ralph/RUN_STATE.json`: Updated iteration and state.

## Acceptance Criteria
1. [x] Comprehensive PhotoCraft Pro / Studio stylesheet written to `PhotoGIMP/.config/GIMP/3.0/theme.css`.
2. [x] Zero hardcoded Flatpak `/app/` paths in `theme.css`.
3. [x] PhotoCraft design tokens audited in `PhotoGIMP/scripts/verify_config.py`.
4. [x] Config audit `python3 PhotoGIMP/scripts/verify_config.py` passes all sections.
5. [x] Automated batch install `bash PhotoGIMP/install.sh --batch` deploys theme and verifies 75 plugins.
6. [x] Full quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly (952/952 tests pass).

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```
