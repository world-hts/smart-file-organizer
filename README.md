# Smart File Organizer

A local-first desktop utility for reviewing, grouping, and safely organizing files. It is built with Python and Tkinter, with no third-party runtime dependencies and no network access.

## What it does

- Scans regular, non-hidden files directly inside a selected folder. It intentionally does not recurse into nested directories.
- Suggests destination folders by file type: Images, Documents, Video, Audio, Archives, Code, Design, Fonts, and Other.
- Presents an explicit move plan before taking action.
- Avoids overwriting existing files by selecting a numbered name such as `photo (1).png` when needed.
- Stores a local undo manifest in the selected folder and can reverse the last completed batch, refusing to overwrite an original path that has since been occupied.
- Finds exact duplicates using file size as a prefilter and SHA-256 hashes for candidate groups. It never deletes duplicates.
- Uses no cloud services, external APIs, or uploaded file content.

## Requirements

- Python 3.11 or newer
- Tkinter included with a GUI-enabled Python distribution

No `pip install` is required.

## Run

```bash
python3 app.py
```

On macOS, select the folder to inspect, click **Preview organization**, review the proposed destinations, and then confirm the move. The app only considers files directly inside the selected folder; items inside existing subfolders are not scanned or changed.

## Quality checks

```bash
python3 scripts/verify_project.py
python3 -m unittest discover -s tests -v
```

The tests use Python's standard library and temporary directories.

## Safety and data handling

- Nothing moves until the user approves the preview.
- No file is uploaded or sent over the network.
- Hidden files, symlinks, and subdirectory contents are skipped by the scanner.
- Duplicate detection is non-destructive.
- Move history is saved as `.smart-file-organizer-history.json` inside the selected folder. It contains original and destination paths, so remove it when no longer needed; this file is ignored by scans.
- Back up important files before running any tool that changes their locations. File moves can fail due to permissions or disk errors; the app reports per-file errors and keeps successful moves in the history when possible.
- Undo validates that stored paths remain within the selected folder and never intentionally overwrites an existing original path.

## Scope notes

“Smart” refers to deterministic file-type rules and duplicate-content checks, not an AI model. V1 does not rename files, inspect file contents, delete items, recurse into folders, or modify metadata.

## Technology

Python · Tkinter/ttk · `pathlib` · `hashlib` · `shutil` · `unittest`
