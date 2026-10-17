# Project roadmap

## V1.0.1 — macOS path consistency hotfix
- [x] Preserve selected folder path spelling in preview plans
- [x] Keep canonical path resolution at move/undo safety boundaries
- [x] Verify the existing 14-test suite after the fix

## V1.0.0 — Local-safe foundation
- [x] File-type classification
- [x] Top-level folder scanning
- [x] Read-only move planning
- [x] Human-reviewed confirmation before moves
- [x] Collision-safe destination naming
- [x] Local last-batch undo manifest
- [x] Duplicate content detection without deletion
- [x] Unit tests and repeatable verification script
- [x] No runtime dependencies or external services

## V1.1 — Quality improvements (only after V1 feedback)
- [ ] Keyboard navigation and more accessibility review
- [ ] Optional recursive scan with per-subfolder opt-in
- [ ] Configurable category rules saved locally
- [ ] Exportable preview report

## V2 — Larger workflow (not included in V1)
- [ ] Multiple named organization profiles
- [ ] Schedule only after explicit opt-in
- [ ] More comprehensive transaction/recovery journal
- [ ] Packaging/signing for macOS and Windows

V1 will not silently move files, delete duplicates, or upload file contents.
