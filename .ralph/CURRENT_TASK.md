# Current Task

Status: COMPLETED

Task: Implement multi-target installation (--all and Both option) with isolated per-target backups in PhotoGIMP/install.sh, and document Linux desktop smoke testing in docs/SMOKE_TESTING.md.
Why: When both native and Flatpak GIMP are installed, users previously had to choose one or manually re-run with different flags; adding --all and option 3 ("Both") ensures complete coverage with independent backups. Documenting smoke testing completes the manual quality gate documentation required by Phase 5.
Affected areas:
- PhotoGIMP/install.sh
- docs/SMOKE_TESTING.md
- PhotoGIMP/scripts/verify_config.py

Acceptance criteria:
1. `PhotoGIMP/install.sh` supports `--all` argument in addition to `--native`, `--flatpak`, and `--batch`. [PASSED]
2. When both runtimes are detected in interactive mode, installer offers option `3) Both`. [PASSED]
3. Separate backups are created for each target configuration directory prior to overwriting files. [PASSED]
4. `docs/SMOKE_TESTING.md` documents structured manual smoke test steps across GNOME, KDE Plasma, and XFCE desktops. [PASSED]
5. `./PhotoGIMP/install.sh --help` outputs the new usage information with exit code 0. [PASSED]
6. `./PhotoGIMP/install.sh --batch` continues to function cleanly with exit code 0. [PASSED]
7. `python3 PhotoGIMP/scripts/verify_config.py` passes with exit code 0. [PASSED]

Verification evidence:
- `./PhotoGIMP/install.sh --help` displays usage `Usage: ./PhotoGIMP/install.sh [--batch|-y|--yes] [--native|--flatpak|--all]` with code 0.
- `./PhotoGIMP/install.sh --batch` executed cleanly, creating isolated backup `~/.config/GIMP/GIMP-backup-*-native` and deploying configuration with code 0.
- `docs/SMOKE_TESTING.md` created with desktop integration, workspace layout, shortcuts, and rollback instructions.
- `python3 PhotoGIMP/scripts/verify_config.py` verified with code 0.

Rollback/checkpoint: PhotoGIMP sub-repo commit 35a9612.
