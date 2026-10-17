# Changelog

## 1.0.1 — 2026-10-17
- Fixed macOS temporary-directory path aliases (`/var/...` vs `/private/var/...`) so preview targets retain the selected path spelling. Execution still canonicalizes paths for safety checks.
- Re-ran all 14 standard-library tests and project verification.

## 1.0.0 — 2026-10-17
- Initial standalone desktop release.
- Added type-based folder suggestions and move-plan preview.
- Added collision-safe moves and last-batch undo.
- Added SHA-256 duplicate grouping without deletion.
- Added dark desktop interface, Turkish setup guide, project roadmap, and standard-library tests.
