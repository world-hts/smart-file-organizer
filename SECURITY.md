# Security policy

## Data handling

Smart File Organizer runs locally. It has no network client, analytics, account system, or upload functionality. It does not read the contents of files except when hashing candidates during a user-initiated duplicate scan.

The hidden `.smart-file-organizer-history.json` records original and destination paths so the last successful batch can be undone. It stays inside the selected folder and should be treated as local metadata.

## Safe-use guidance

- Review the plan before confirming moves.
- Keep a backup of important files.
- Do not manually edit the undo manifest while the app is using it.
- The app refuses to overwrite files at original locations during undo and validates that history paths stay inside the selected folder.

## Reporting an issue

Open a GitHub issue with reproduction steps and a sanitized log. Do not upload private files, personal paths, access tokens, or private folder names.
