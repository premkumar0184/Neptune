# Current Task

Status: COMPLETED

Task: Upgrade PhotoGIMP/install.sh for GIMP 3.2+ support and non-interactive batch installation mode.
Why: The host system runs GIMP 3.2.6 (config dir ~/.config/GIMP/3.2). The current installer fails in non-interactive environments when multiple GIMP runtimes are detected and lacks explicit flag handling for automated deployment and verification.
Affected areas: PhotoGIMP/install.sh
Acceptance criteria:
1. `PhotoGIMP/install.sh` parses `--batch` or `-y` / `--yes` command-line flags for non-interactive execution. [PASSED]
2. Installer detects GIMP 3.2+ (and any GIMP 3.x) native installations correctly. [PASSED]
3. Config files from `PhotoGIMP/.config/GIMP/3.0` are installed to the active GIMP config directory (`~/.config/GIMP/3.2/` or detected dir). [PASSED]
4. Automated backup of existing config is created prior to installation. [PASSED]
5. Running `PhotoGIMP/install.sh --batch` succeeds with exit code 0. [PASSED]

Verification commands:
- `./PhotoGIMP/install.sh --batch` [EXECTUTED - Exit code 0]
- Test checking installed files in `~/.config/GIMP/3.2/` (`gimprc`, `sessionrc`, `shortcutsrc`, `toolrc`, `theme.css`). [VERIFIED]

Rollback/checkpoint: Git commit on master.
