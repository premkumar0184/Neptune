# Known Issues

Only record reproducible or well-supported issues.

## Format

## K-NNN — Short title
Status: open / investigating / fixed
Observed:
Reproduction:
Impact:
Likely cause:
Workaround:
Related task/commit:

Do not turn guesses into facts.

## K-001 — Gimp.DrawableFilter fails on temp layers/channels in headless mode
Status: open
Observed: 2026-10-06 (Iteration 9)
Reproduction: Attempting to apply `Gimp.DrawableFilter.new(layer, "gegl:gray", "")` or `Gimp.DrawableFilter.new(ch, "gegl:invert-linear", "")` on a temporary layer from a duplicated image (or on a channel) in headless `--no-interface` mode returns the error "The filter is hidden" and raises an exception.
Impact: Cannot use `gegl:gray`, `gegl:invert-linear` via DrawableFilter on channels or flattened temporary layers. Must use deprecated `Drawable.desaturate()` and `Drawable.invert()` APIs instead.
Likely cause: DrawableFilter requires a display context (`GimpDisplay`) for certain operations. Temporary layers and channels lack this context in headless mode.
Workaround: Use deprecated `Gimp.Drawable.desaturate(Gimp.DesaturateMode.LUMINANCE)` and `Gimp.Drawable.invert()` — both are deprecated in GIMP 3.x but functional in GIMP 3.2.6 and produce no errors.
Related task/commit: Phase 7 — Luminosity Masks (Iteration 9).
