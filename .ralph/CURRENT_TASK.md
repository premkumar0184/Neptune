# Current Task

Status: COMPLETED

Task: Refine Single-Window workspace (sessionrc, gimprc) and theme.css for GIMP 3.x native compatibility and panel alignment.
Why: gimprc lacked explicit single-window-mode activation, sessionrc was missing the Undo History dockable (History panel in Photoshop spec), and theme.css contained hardcoded Flatpak file paths (/app/share/...) causing GTK CSS load failures on native GIMP.
Affected areas:
- PhotoGIMP/.config/GIMP/3.0/gimprc
- PhotoGIMP/.config/GIMP/3.0/sessionrc
- PhotoGIMP/.config/GIMP/3.0/theme.css
- PhotoGIMP/scripts/verify_config.py

Acceptance criteria:
1. `gimprc` explicitly enforces `(single-window-mode yes)`. [PASSED]
2. `sessionrc` includes `gimp-undo-history` in right-panel book alongside Layers/Channels/Paths. [PASSED]
3. `theme.css` has no hardcoded Flatpak `/app/` paths; uses portable GTK3 CSS overrides. [PASSED]
4. `verify_config.py` extended with Section 3 workspace audit (single-window-mode, gimp-undo-history, Flatpak path check). [PASSED]
5. `python3 PhotoGIMP/scripts/verify_config.py` passes with exit code 0. [PASSED — all 5 sexp files valid, all 23 shortcuts pass, all 3 workspace checks pass]
6. `./PhotoGIMP/install.sh --batch` deploys configuration to `~/.config/GIMP/3.2/` cleanly. [PASSED — exit code 0]

Verification evidence:
- `python3 PhotoGIMP/scripts/verify_config.py` exit code 0 — all sections passed
- `./PhotoGIMP/install.sh --batch` exit code 0 — config deployed to /home/prem/.config/GIMP/3.2/
- Live file checks confirmed: (single-window-mode yes) in gimprc, gimp-undo-history in sessionrc, 0 flatpak paths in theme.css

Rollback/checkpoint: PhotoGIMP sub-repo commit e57593f.
