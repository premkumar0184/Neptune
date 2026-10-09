# Current Task — Iteration 74

## Task
**Phase 72 — History States & Edit Session Audit Log Plugin (`history-log`)**

## Status
**COMPLETED**

## Rationale
In Adobe Photoshop (`Topics.txt` lines 34-40: "History panel settings", "Set History Log preferences", "View history logs", "Use snapshots in the History panel", "Manage image states"; `photoshop_docs.md` Section 41, 42, 45, 46, 47 lines 1040-1210: "Configure History Log settings", "Manage image states", "Create snapshots in the History panel"):
1. **History Log Preferences & Audit Logging**:
   - In Photoshop (`Edit > Preferences > History Log`), users configure automated tracking of image edits and operations across editing sessions.
   - Saves logs to:
     - **Metadata**: Embedded directly inside image document metadata/parasite.
     - **Text File**: Appended to an external text file on disk for team audits and legal/client records.
     - **Both**: Saved concurrently to document metadata and external text file.
   - Detail levels: `Sessions Only` (session boundaries), `Concise` (action overview and timestamps), and `Detailed` (full operational details, layer targets, parameters).
   - Allows users to view or export the history audit trail at any time.
2. **History Snapshots & Image States**:
   - In Photoshop, users create named snapshots of the document state:
     - `Create Snapshot`: Captures the state of layers. Supports `Full Document` (all layers, visibility, positions, opacities, modes), `Merged Layers` (composite raster snapshot), and `Current Layer` (active layer state).
     - `Apply / Revert to Snapshot`: Restores the document to any earlier captured snapshot state.
     - `New Document from Snapshot`: Generates a new, independent GIMP image from the snapshot state (Photoshop "Create a new document from current state" button).
     - `Delete Snapshot`: Removes individual snapshots or clears all snapshots (`__ALL__`).
3. **Canvas Artwork Integrity**:
   - Base canvas artwork pixels remain 100% untouched (`diff == 0.000000`).
   - Single-step undo group encapsulation across all operations.

Stock GIMP provides no built-in equivalent for Photoshop's History Log preferences, text file audit logging, or persistent named history snapshots. Implementing `history-log` provides full Photoshop parity on Linux.

## Affected Code
- `PhotoGIMP/.config/GIMP/3.0/plug-ins/history-log/history-log.py` (New plugin implementing 7 PDB procedures: `python-fu-set-history-log-prefs`, `python-fu-record-history-entry`, `python-fu-view-history-log`, `python-fu-create-snapshot`, `python-fu-apply-snapshot`, `python-fu-new-document-from-snapshot`, `python-fu-delete-snapshot`)
- `PhotoGIMP/scripts/verify_config.py` (Register `history-log` in `REQUIRED_PLUGINS`, updating audit inventory to 66 plugins)
- `PhotoGIMP/install.sh` (Batch deployment handles all subdirectories in `plug-ins/`)
- `tests/gimp_e2e_suite.py` (Extend with Test Suite 67: `test_history_log`, assertions HL-01 through HL-16)
- `.ralph/PHOTOSHOP_FEATURE_MATRIX.md` (Add History States & Edit Session Audit Log entry)
- `.ralph/IMPLEMENTATION_PLAN.md` (Update Phase 72 status)
- `.ralph/PROGRESS.md` (Log Iteration 74 progress)
- `.ralph/RUN_STATE.json` (Track Iteration 74 state)

## Acceptance Criteria
1. [x] Plugin directory `PhotoGIMP/.config/GIMP/3.0/plug-ins/history-log/` created with `history-log.py`.
2. [x] Plugin has executable permissions (`chmod +x`) and passes bytecode compilation (`py_compile`).
3. [x] 7 PDB procedures registered in GIMP PDB:
   - `python-fu-set-history-log-prefs` under `<Image>/Edit/Preferences/History Log...` and `<Image>/Edit`
   - `python-fu-record-history-entry` under `<Image>/Edit`
   - `python-fu-view-history-log` under `<Image>/Edit` and `<Image>/File/Export`
   - `python-fu-create-snapshot` under `<Image>/Edit` and `<Image>/Window/History`
   - `python-fu-apply-snapshot` under `<Image>/Edit` and `<Image>/Window/History`
   - `python-fu-new-document-from-snapshot` under `<Image>/Edit` and `<Image>/File/New`
   - `python-fu-delete-snapshot` under `<Image>/Edit` and `<Image>/Window/History`
4. [x] In headless GIMP tests (`tests/gimp_e2e_suite.py` Test Suite 67):
   - HL-01: Procedure signatures and argument audit across all 7 procedures.
   - HL-02: History Log preferences configuration & parasite persistence (`photogimp/history-log-prefs`).
   - HL-03: Record history entry (concise vs detailed) in metadata parasite (`photogimp/history-log-entries`).
   - HL-04: Record history entry to external text file on disk (`text_file` / `both`).
   - HL-05: View/Export history log to file with timestamped audit trail.
   - HL-06: Create Snapshot (Full Document) with layer visibility, position, and appearance.
   - HL-07: Snapshot persistent parasite storage (`photogimp/history-snapshots`).
   - HL-08: Revert/Apply Snapshot restoring full document layer states.
   - HL-09: Create Snapshot (Merged Layers) composite snapshot layer.
   - HL-10: Create Snapshot (Current Layer) active layer isolation.
   - HL-11: New Document from Snapshot creates independent new image with matching dimensions.
   - HL-12: Delete Snapshot (single deletion by name).
   - HL-13: Delete Snapshot (clear all snapshots via `__ALL__`).
   - HL-14: Graceful handling of missing snapshot (error status without crashing).
   - HL-15: Undo group encapsulation for snapshot operations.
   - HL-16: Target & base canvas artwork preservation (`diff == 0.000000`).
5. [x] `verify_config.py` Section 6 passes with all 66 required plugins audited.
6. [x] Unified quality gate `python3 tests/run_all_tests.py` passes all 3 stages cleanly with exit code 0.

## Verification Commands
```bash
python3 PhotoGIMP/scripts/verify_config.py
bash PhotoGIMP/install.sh --batch
python3 tests/run_all_tests.py
```

## Checkpoint
- PhotoGIMP submodule commit: `feat(plugins): implement history states and edit session audit log plugin`
- Outer repository commit: `feat(ralph): complete iteration 74 - history states and edit session audit log plugin`
