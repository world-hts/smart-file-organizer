"""Pure file-planning and safe move helpers. No network access is used."""
from __future__ import annotations

import hashlib
import json
import shutil
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

CATEGORY_EXTENSIONS: dict[str, frozenset[str]] = {
    "Images": frozenset({".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".svg", ".ico", ".avif"}),
    "Documents": frozenset({".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md", ".pages", ".xls", ".xlsx", ".ods", ".csv", ".ppt", ".pptx", ".key", ".numbers"}),
    "Video": frozenset({".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".mpeg", ".mpg", ".3gp"}),
    "Audio": frozenset({".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg", ".opus", ".aiff", ".wma"}),
    "Archives": frozenset({".zip", ".7z", ".rar", ".tar", ".gz", ".bz2", ".xz", ".dmg", ".iso", ".pkg"}),
    "Code": frozenset({".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".scss", ".json", ".xml", ".yml", ".yaml", ".toml", ".sh", ".zsh", ".sql", ".dart", ".java", ".kt", ".swift", ".go", ".rs", ".c", ".h", ".cpp", ".mdx"}),
    "Design": frozenset({".psd", ".ai", ".eps", ".fig", ".sketch", ".indd", ".blend", ".obj", ".stl", ".afdesign", ".afphoto"}),
    "Fonts": frozenset({".ttf", ".otf", ".woff", ".woff2"}),
}
CATEGORY_ORDER = ("Images", "Documents", "Video", "Audio", "Archives", "Code", "Design", "Fonts", "Other")
HISTORY_FILE = ".smart-file-organizer-history.json"


@dataclass(frozen=True)
class FileRecord:
    path: Path
    size: int
    modified: float
    extension: str
    category: str


@dataclass(frozen=True)
class MovePlan:
    source: Path
    target: Path
    category: str
    size: int


def category_for(path: Path) -> str:
    suffix = path.suffix.casefold()
    for category, extensions in CATEGORY_EXTENSIONS.items():
        if suffix in extensions:
            return category
    return "Other"


def format_size(size: int) -> str:
    value = float(max(0, size))
    units = ("B", "KB", "MB", "GB", "TB")
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} B"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def scan_folder(folder: Path | str) -> list[FileRecord]:
    """List regular, non-hidden files in the selected folder (not recursively).

    Directory contents are deliberately not traversed to avoid surprising moves.
    Symlinks, hidden items, and the app's own undo metadata are skipped.
    """
    # Preserve the selected path spelling for plans and display. On macOS,
    # TemporaryDirectory may return /var/... while resolve() rewrites it to
    # /private/var/...; mixing those spellings makes otherwise identical Path
    # objects compare unequal. Execution still resolves paths before enforcing
    # move boundaries.
    root = Path(folder).expanduser()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Folder does not exist or is not a directory: {root}")
    records: list[FileRecord] = []
    try:
        children = sorted(root.iterdir(), key=lambda p: p.name.casefold())
    except OSError as exc:
        raise OSError(f"Cannot read folder: {root}: {exc}") from exc
    for path in children:
        if path.name.startswith(".") or path.name == HISTORY_FILE or path.is_symlink() or not path.is_file():
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        records.append(FileRecord(path=path, size=stat.st_size, modified=stat.st_mtime,
                                  extension=path.suffix.casefold() or "(no extension)",
                                  category=category_for(path)))
    return records


def _non_conflicting_target(target: Path, source: Path) -> Path:
    if target == source or not (target.exists() or target.is_symlink()):
        return target
    base, suffix = target.stem, target.suffix
    index = 1
    while True:
        candidate = target.with_name(f"{base} ({index}){suffix}")
        if candidate == source or not (candidate.exists() or candidate.is_symlink()):
            return candidate
        index += 1


def make_plan(records: Iterable[FileRecord]) -> list[MovePlan]:
    """Create a deterministic plan. This function never changes the filesystem."""
    plans: list[MovePlan] = []
    for record in records:
        destination_dir = record.path.parent / record.category
        target = _non_conflicting_target(destination_dir / record.path.name, record.path)
        plans.append(MovePlan(record.path, target, record.category, record.size))
    return plans


def _write_history(root: Path, records: list[dict[str, str]]) -> None:
    history_path = root / HISTORY_FILE
    payload = {"schema": 1, "created_at": datetime.now(timezone.utc).isoformat(), "moves": records}
    temporary = history_path.with_suffix(history_path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temporary.replace(history_path)


def execute_plan(plans: Iterable[MovePlan]) -> tuple[list[dict[str, str]], list[tuple[MovePlan, str]]]:
    """Execute a previously previewed plan; return successful moves and failures.

    Targets are rechecked immediately before moving. If anything fails, other
    independent moves continue, and every successful move is recorded for undo.
    """
    plan_list = list(plans)
    completed: list[dict[str, str]] = []
    errors: list[tuple[MovePlan, str]] = []
    if not plan_list:
        return completed, errors
    root = plan_list[0].source.parent.resolve()
    for item in plan_list:
        try:
            if not item.source.exists() or not item.source.is_file() or item.source.is_symlink():
                raise FileNotFoundError("Source is missing or is not a regular file")
            target = item.target
            # Avoid overwriting if the destination appeared after the preview.
            if target.exists():
                target = _non_conflicting_target(target, item.source)
            root_resolved = root.resolve()
            if item.source.parent.resolve() != root_resolved:
                raise ValueError("Source is no longer a direct child of the selected folder")
            target.parent.mkdir(parents=True, exist_ok=True)
            resolved_parent = target.parent.resolve()
            if resolved_parent != root_resolved and root_resolved not in resolved_parent.parents:
                raise ValueError("Destination resolves outside the selected folder")
            shutil.move(str(item.source), str(target))
            completed.append({"source": str(item.source), "target": str(target)})
        except (OSError, shutil.Error, ValueError) as exc:
            errors.append((item, str(exc)))
    if completed:
        try:
            _write_history(root, completed)
        except OSError as exc:
            # Tell the caller undo metadata could not be safely persisted.
            errors.append((plan_list[0], f"Moved files, but could not save undo history: {exc}"))
    return completed, errors


def undo_last_batch(folder: Path | str) -> tuple[int, list[str]]:
    """Undo the most recent saved batch, without overwriting original files."""
    root = Path(folder).expanduser().resolve()
    history_path = root / HISTORY_FILE
    if not history_path.is_file():
        return 0, ["No undo history found for this folder."]
    try:
        payload = json.loads(history_path.read_text(encoding="utf-8"))
        if payload.get("schema") != 1 or not isinstance(payload.get("moves"), list):
            raise ValueError("Unsupported undo history format")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return 0, [f"Undo history could not be read: {exc}"]
    moves = payload["moves"]
    restored = 0
    errors: list[str] = []
    remaining: list[dict[str, str]] = []
    for item in reversed(moves):
        try:
            source = Path(item["source"]).expanduser().resolve()
            target_raw = Path(item["target"]).expanduser()
            if target_raw.is_symlink():
                raise ValueError(f"Refusing to restore from a symbolic link: {target_raw}")
            target = target_raw.resolve()
            if source.parent != root:
                raise ValueError(f"Refusing to restore outside the selected folder: {source}")
            if target != root and root not in target.parents:
                raise ValueError(f"Refusing to move a file from outside the selected folder: {target}")
            if not target.exists() or not target.is_file():
                raise FileNotFoundError(f"Organized file not found: {target.name}")
            if source.exists():
                raise FileExistsError(f"Original path is occupied; refusing to overwrite: {source.name}")
            source.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(target), str(source))
            restored += 1
        except (KeyError, OSError, shutil.Error, ValueError) as exc:
            errors.append(str(exc))
            if isinstance(item, dict):
                remaining.append(item)
    if remaining:
        payload["moves"] = list(reversed(remaining))
        try:
            temp = history_path.with_suffix(history_path.suffix + ".tmp")
            temp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            temp.replace(history_path)
        except OSError as exc:
            errors.append(f"Could not update undo history: {exc}")
    else:
        try:
            history_path.unlink(missing_ok=True)
        except OSError as exc:
            errors.append(f"Files were restored, but history could not be removed: {exc}")
    return restored, errors


def find_duplicates(records: Iterable[FileRecord]) -> list[list[Path]]:
    """Return same-content groups. Hash only same-sized files to save work."""
    by_size: dict[int, list[Path]] = defaultdict(list)
    for record in records:
        by_size[record.size].append(record.path)
    duplicates: list[list[Path]] = []
    for paths in by_size.values():
        if len(paths) < 2:
            continue
        by_hash: dict[str, list[Path]] = defaultdict(list)
        for path in paths:
            digest = hashlib.sha256()
            try:
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
            except OSError:
                continue
            by_hash[digest.hexdigest()].append(path)
        duplicates.extend(group for group in by_hash.values() if len(group) > 1)
    return duplicates
