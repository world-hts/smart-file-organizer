#!/usr/bin/env python3
"""Deterministic standard-library project validation."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "app.py", "README.md", "START_HERE_TR.md", "PROJECT_ROADMAP.md",
    "CHANGELOG.md", "SECURITY.md", "LICENSE", "pyproject.toml",
    "smart_file_organizer/__init__.py", "smart_file_organizer/core.py",
    "smart_file_organizer/gui.py", "tests/test_core.py",
]


def main() -> int:
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    if missing:
        print("Missing required files:", ", ".join(missing), file=sys.stderr)
        return 1
    python_files = sorted([*ROOT.glob("*.py"), *ROOT.glob("smart_file_organizer/*.py"), *ROOT.glob("tests/*.py"), *ROOT.glob("scripts/*.py")])
    for path in python_files:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            print(f"Syntax error in {path.relative_to(ROOT)}: {exc}", file=sys.stderr)
            return 1
    # The V1 package intentionally has no third-party runtime dependencies.
    import tomllib
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if project.get("project", {}).get("dependencies") != []:
        print("Expected no third-party runtime dependencies", file=sys.stderr)
        return 1
    print("Project verification passed.")
    print(f"Required project files: {len(REQUIRED)}")
    print(f"Python syntax files checked: {len(python_files)}")
    print("Runtime dependencies: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
