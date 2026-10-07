# Architecture / Product Decisions

Record durable decisions that future Antigravity sessions must know.

## Format

## D-NNN — Title
Date:
Decision:
Reason:
Alternatives considered:
Consequences:

---

## D-001 — Portable GTK3 Theme Overrides for PhotoGIMP
- **Date**: 2026-10-06
- **Decision**: Avoid hardcoded Flatpak file paths (such as `file:///app/share/...`) in `theme.css`. Use portable GTK3 dark theme overrides directly in `theme.css`.
- **Reason**: Hardcoded Flatpak paths break silently on native package manager installations (Arch, Fedora, Ubuntu).
- **Alternatives considered**: Separate theme.css per install target (unnecessary complexity; portable CSS works universally).
- **Consequences**: Theme renders consistently across native, AppImage, and Flatpak deployments.

---

## D-002 — Single-Window Mode Configuration in GIMP 3.x
- **Date**: 2026-10-06
- **Decision**: Manage Single-Window Mode exclusively via `sessionrc` using `(session-info "toplevel" (factory-entry "gimp-single-image-window") (open-on-exit) ...)`. Do NOT place `(single-window-mode yes)` into `gimprc`.
- **Reason**: GIMP 3.x deprecated and removed `single-window-mode` from the `gimprc` parser. Its presence in `gimprc` triggers a fatal parse error on startup and causes GIMP to discard user preferences.
- **Alternatives considered**: Retaining `(single-window-mode yes)` for GIMP 2.10 backwards compatibility (rejected: host project target is GIMP 3.x).
- **Consequences**: GIMP 3.x launches cleanly in single-window mode without startup parser errors.

---

## D-003 — Active Selection Isolation During Layer Filter Merging
- **Date**: 2026-10-07
- **Decision**: In Python 3 plugins that process a duplicated layer before attaching a selection-derived or radial layer mask (such as Selective Color Pop or Depth Defocus), always save the active selection (`Gimp.Selection.save(image)`), clear the selection (`Gimp.Selection.none(image)`), apply the filter, and then restore the selection (`image.select_item(...)`).
- **Reason**: In GIMP 3.x, `Drawable.merge_filter()` automatically constrains the pixel processing region to whatever active selection exists on the image at execution time. If the user has selected their subject, applying a filter to the duplicated layer without clearing the selection will filter only the subject area and leave the background unprocessed.
- **Alternatives considered**: Inverting the selection before filtering (causes artifacts at boundaries and breaks radial falloff modes).
- **Consequences**: Layer filters process the entire canvas reliably, layer masks accurately isolate the subject, and the user's original selection is preserved after execution.

