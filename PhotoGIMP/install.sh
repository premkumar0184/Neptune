#!/bin/bash
# PhotoGIMP installer for Linux
# Detects the installed GIMP version and copies config files accordingly.

set -eu

BATCH_MODE=0
FORCED_SOURCE=""

for arg in "$@"; do
	case "$arg" in
		--batch|-y|--yes)
			BATCH_MODE=1
			;;
		--native)
			FORCED_SOURCE="native"
			;;
		--flatpak)
			FORCED_SOURCE="flatpak"
			;;
		--all|--both)
			FORCED_SOURCE="all"
			;;
		-h|--help)
			echo "Usage: $0 [--batch|-y|--yes] [--native|--flatpak|--all]"
			exit 0
			;;
	esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_SRC="$SCRIPT_DIR/.config/GIMP/3.0"

# Source - https://stackoverflow.com/a/37939589
# Posted by yairchu, modified by community. See post 'Timeline' for change history
# Retrieved 2026-08-02, License - CC BY-SA 4.0

function version { echo "$@" | awk -F. '{ printf("%d%03d%03d%03d\n", $1,$2,$3,$4); }'; }

# --- Detect GIMP installation and config location ---

detect_gimp() {
	local gimp_params=(
		--no-interface
		--console-messages
		--batch-interpreter=plug-in-script-fu-eval
		--batch
		'(begin
			(display "GIMP_CONFIG_DIR=")
			(display gimp-directory)
			(newline))'
		--quit
	)

	flatpak_config=""
	flatpak_version=""
	flatpak_command=""
	native_config=""
	native_version=""
	native_command=""
	local selection

	# Check for flatpak installation
	if command -v flatpak >/dev/null && flatpak info org.gimp.GIMP >/dev/null 2>&1; then
		flatpak_config=$(
			set -o pipefail
			flatpak run org.gimp.GIMP "${gimp_params[@]}" 2>&1 | sed -n 's/^GIMP_CONFIG_DIR=//p'
		)

		flatpak_version=$(flatpak run org.gimp.GIMP --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1)
		flatpak_command="org.gimp.GIMP"
	fi

	local IFS=:
	read -r -a path_entries <<< "$PATH"
	local path
	local command
	local command_version
	local binary_path
	for path in "${path_entries[@]}"; do
		if [ -z "$path" ]; then
			path="."
		fi

		for binary_path in "$path"/gimp-3.*; do
			if [ ! -f "$binary_path" ] || [ ! -x "$binary_path" ]; then
				continue
			fi

			command="${binary_path##*/}"
			command_version=$("$command" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1)
			if [ -z "$command_version" ] || [ "$(version "$command_version")" -lt "$(version "3.0")" ]; then
				continue
			fi

			if [ -z "$native_command" ] || [ "$(version "$command_version")" -gt "$(version "$native_version")" ]; then
				native_command="$command"
				native_version="$command_version"
			fi
		done
	done

	# If we didn't find a gimp-3.x command, try just gimp
	if [ -z "$native_command" ] && command -v gimp >/dev/null; then
		command_version=$(gimp --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1)
		if [ -n "$command_version" ] && [ "$(version "$command_version")" -ge "$(version "3.0")" ]; then
			native_command="gimp"
			native_version="$command_version"
		fi
	fi

	if [ -n "$native_command" ]; then
		native_config=$(
			set -o pipefail
			"$native_command" "${gimp_params[@]}" 2>&1 | sed -n 's/^GIMP_CONFIG_DIR=//p'
		)
	fi

	# Determine target selection
	if [ -n "$FORCED_SOURCE" ]; then
		GIMP_SOURCE="$FORCED_SOURCE"
	elif [ -n "$native_command" ] && [ -n "$flatpak_command" ]; then
		if [ "$BATCH_MODE" -eq 1 ]; then
			GIMP_SOURCE="native"
		else
			echo ""
			echo "Flatpak and Native installations of GIMP were detected"
			echo "1) Flatpak (recommended)"
			echo "2) Native"
			echo "3) Both (Flatpak and Native)"

			while true; do
				printf "Select installation [1]: "
				if ! IFS= read -r selection; then
					echo ""
					echo "No selection received. Run the installer interactively"
					exit 1
				fi

				case "$selection" in
					""|1) GIMP_SOURCE="flatpak"; break ;;
					2) GIMP_SOURCE="native"; break ;;
					3) GIMP_SOURCE="all"; break ;;
					*) echo "Please enter 1, 2, or 3" ;;
				esac
			done
		fi
	elif [ -n "$native_command" ]; then
		GIMP_SOURCE="native"
	elif [ -n "$flatpak_command" ]; then
		GIMP_SOURCE="flatpak"
	else
		return 1
	fi

	return 0
}

# --- Main ---

echo "PhotoGIMP Installer"
echo "==================="

if ! detect_gimp; then
	echo ""
	echo "No supported GIMP 3.x installation was detected."
	echo "Install GIMP 3.x, start it once, then run this script again."
	exit 1
fi

TARGET_SOURCES=()
TARGET_CONFIGS=()
TARGET_VERSIONS=()
TARGET_COMMANDS=()

if [ "$GIMP_SOURCE" = "all" ] || [ "$GIMP_SOURCE" = "flatpak" ]; then
	if [ -n "$flatpak_config" ]; then
		TARGET_SOURCES+=("flatpak")
		TARGET_CONFIGS+=("$flatpak_config")
		TARGET_VERSIONS+=("$flatpak_version")
		TARGET_COMMANDS+=("$flatpak_command")
	fi
fi

if [ "$GIMP_SOURCE" = "all" ] || [ "$GIMP_SOURCE" = "native" ]; then
	if [ -n "$native_config" ]; then
		TARGET_SOURCES+=("native")
		TARGET_CONFIGS+=("$native_config")
		TARGET_VERSIONS+=("$native_version")
		TARGET_COMMANDS+=("$native_command")
	fi
fi

if [ "${#TARGET_CONFIGS[@]}" -eq 0 ]; then
	echo "No matching GIMP installation found for source: $GIMP_SOURCE"
	exit 1
fi

for idx in "${!TARGET_CONFIGS[@]}"; do
	cur_source="${TARGET_SOURCES[$idx]}"
	cur_config="${TARGET_CONFIGS[$idx]}"
	cur_version="${TARGET_VERSIONS[$idx]}"
	cur_command="${TARGET_COMMANDS[$idx]}"

	echo ""
	echo "Target: $cur_source (GIMP $cur_version)"
	echo "Config directory: $cur_config"

	if [ "$(version "$cur_version")" -lt "$(version "3.0")" ]; then
		echo "Version $cur_version is not supported (requires 3.0+). Skipping."
		continue
	fi

	if [ ! -d "$cur_config" ]; then
		echo "Config directory does not exist yet ($cur_config)."
		echo "Please start GIMP once, close it, then run this script again."
		exit 1
	fi

	# Check running status
	case "$cur_source" in
		flatpak)
			while read -r pid application; do
				case "$pid" in ""|*[!0-9]*) continue ;;
				esac
				if [ "$application" = "$cur_command" ] && kill -0 "$pid" 2>/dev/null; then
					echo "GIMP (Flatpak) is currently running. Please close it first."
					exit 1
				fi
			done < <(flatpak ps --columns=pid,application 2>/dev/null || true)
			;;
		native)
			if pgrep -x 'gimp|gimp-3\.[0-9]+' >/dev/null; then
				echo "GIMP (native) is currently running. Please close it first."
				exit 1
			fi
			;;
	esac

	# Backup existing config
	BACKUP="$(dirname "$cur_config")/GIMP-backup-$(date +%Y%m%d-%H%M%S)-$cur_source"
	CONFIG_BACKUP="$BACKUP/$(basename "$cur_config")"
	echo "Backing up current config to: $BACKUP"
	mkdir -p "$BACKUP"
	cp -a "$cur_config" "$BACKUP/"

	# Copy PhotoGIMP config files
	echo "Installing PhotoGIMP config to $cur_config..."
	cp -a "$CONFIG_SRC"/. "$cur_config"/

	# Ensure all plug-in scripts have executable permissions
	if [ -d "$cur_config/plug-ins" ]; then
		find "$cur_config/plug-ins" -type f -name "*.py" -exec chmod +x {} +
		plugin_count=$(find "$cur_config/plug-ins" -type f -name "*.py" | wc -l)
		echo "Verified executable permissions on $plugin_count plug-in(s) in $cur_config/plug-ins."
	fi
done

# Install desktop file and icons
DESKTOP_SRC="$SCRIPT_DIR/.local/share/applications/org.gimp.GIMP.desktop"
DESKTOP_DST="$HOME/.local/share/applications/org.gimp.GIMP.desktop"

if [ -f "$DESKTOP_SRC" ]; then
	mkdir -p "$(dirname "$DESKTOP_DST")"
	cat -- "$DESKTOP_SRC" > "$DESKTOP_DST"
	echo "Desktop file installed to $DESKTOP_DST."

	if command -v update-desktop-database >/dev/null 2>&1; then
		update-desktop-database "$(dirname "$DESKTOP_DST")" 2>/dev/null || true
	fi
fi

if [ -d "$SCRIPT_DIR/.local/share/icons" ]; then
	cp -a "$SCRIPT_DIR/.local/share/icons"/. "$HOME/.local/share/icons"/
	echo "Icons installed to $HOME/.local/share/icons/."

	if command -v gtk-update-icon-cache >/dev/null 2>&1; then
		gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
	fi
fi

echo ""
echo "Done! Start GIMP to use PhotoGIMP."
