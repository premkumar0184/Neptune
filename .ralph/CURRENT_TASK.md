# Current Task

Status: COMPLETED

Task: Implement native GIMP 3.x Python 3 Frequency Separation retouching plugin in PhotoGIMP/.config/GIMP/3.0/plug-ins/frequency-separation/frequency-separation.py.
Why: Frequency Separation is a cornerstone professional Photoshop retouching technique from photoshop_docs.md. GIMP has no built-in automated Frequency Separation tool. Implementing a native GIMP 3.x GObject-Introspection plugin provides one-click non-destructive frequency separation into Low Frequency (tones/colors) and High Frequency (texture/pores) layers.
Affected areas:
- PhotoGIMP/.config/GIMP/3.0/plug-ins/frequency-separation/frequency-separation.py
- PhotoGIMP/scripts/verify_config.py
- .ralph/IMPLEMENTATION_PLAN.md
- .ralph/PHOTOSHOP_FEATURE_MATRIX.md
- .ralph/PROGRESS.md
- .ralph/RUN_STATE.json

Acceptance criteria:
1. `frequency-separation.py` is a valid Python 3 GIMP plugin using `gi.repository.Gimp` (API version 3.0) and `gi.repository.Gegl`. [PASSED]
2. The plugin registers under menu path `<Image>/Filters/Retouching` as `Frequency Separation...`. [PASSED]
3. Running the procedure on an image creates a `Frequency Separation` layer group containing:
   - `Low Frequency (Color & Tone)` layer with Gaussian blur applied.
   - `High Frequency (Texture)` layer with high-frequency texture and Grain Merge / Linear Light blending. [PASSED]
4. Plugin is executable (`chmod +x`) and passes syntax check with `python3 -m py_compile`. [PASSED]
5. Automated headless GIMP test runs the procedure on a generated test image and verifies successful layer creation without errors. [PASSED]
6. `install.sh` deploys the plugin to `~/.config/GIMP/3.2/plug-ins/` with execute permissions. [PASSED]

Verification evidence:
- `python3 PhotoGIMP/scripts/verify_config.py` passed with all 6 sections clean (code 0).
- `./PhotoGIMP/install.sh --batch` deployed plugin to `~/.config/GIMP/3.2/plug-ins/frequency-separation/frequency-separation.py`.
- Headless execution via Script-Fu and GIMP PDB created layer group `Frequency Separation (Portrait)` containing `[High Frequency (Texture)]` and `[Low Frequency (Color & Tone)]` with exit code 0.

Rollback/checkpoint: PhotoGIMP sub-repo commit 307b1c8.
