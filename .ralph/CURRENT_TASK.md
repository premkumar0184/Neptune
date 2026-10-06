# Current Task

Status: COMPLETED

Task: Create native-GIMP desktop launcher and extend install.sh to install desktop file and icons for native installations.
Why: The existing `org.gimp.GIMP.desktop` uses `Exec=flatpak run ...` which only works for Flatpak. On native GIMP 3.2.6, install.sh skips desktop file and icon installation entirely. Users get no application launcher entry or icons when installing PhotoGIMP natively.
Affected areas:
- PhotoGIMP/.local/share/applications/org.gimp.GIMP.desktop  (update Exec for native)
- PhotoGIMP/install.sh  (install desktop + icons for native too, not just Flatpak)
- PhotoGIMP/scripts/verify_config.py  (add check: desktop file Exec line is not Flatpak-only)

Acceptance criteria:
1. `org.gimp.GIMP.desktop` Exec line uses `gimp %U` (native) as the default; file remains valid per `desktop-file-validate`. [PASSED]
2. `install.sh` installs the desktop file and icons for native installs as well as Flatpak. [PASSED]
3. After `./install.sh --batch`, `~/.local/share/applications/org.gimp.GIMP.desktop` exists with a native Exec line. [PASSED]
4. After `./install.sh --batch`, icon sizes exist in `~/.local/share/icons/hicolor/`. [PASSED]
5. `python3 PhotoGIMP/scripts/verify_config.py` passes exit code 0 (new check: desktop file not Flatpak-only). [PASSED]
6. Splash screen `~/.config/GIMP/3.2/splashes/` already has the file (already handled by config copy — verify). [PASSED]

Verification evidence:
- `desktop-file-validate ~/.local/share/applications/org.gimp.GIMP.desktop` exited with 0 (valid desktop file syntax).
- `./PhotoGIMP/install.sh --batch` installed desktop file and icons into `~/.local/share/applications/` and `~/.local/share/icons/hicolor/`.
- Confirmed `Exec=gimp %U` and `TryExec=gimp` in `~/.local/share/applications/org.gimp.GIMP.desktop`.
- Confirmed icon assets in `~/.local/share/icons/hicolor/128x128/apps/photogimp.png`.
- Confirmed splash image `splash-screen-2025-v2.png` in `~/.config/GIMP/3.2/splashes/`.
- `python3 PhotoGIMP/scripts/verify_config.py` passed exit code 0 with all 4 sections validated.

Rollback/checkpoint: PhotoGIMP sub-repo commit c273e6a.
