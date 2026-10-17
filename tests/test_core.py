from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from smart_file_organizer.core import (
    FileRecord,
    category_for,
    execute_plan,
    find_duplicates,
    format_size,
    make_plan,
    scan_folder,
    undo_last_batch,
)


def record(path: Path) -> FileRecord:
    stat = path.stat()
    return FileRecord(path, stat.st_size, stat.st_mtime, path.suffix.casefold() or "(no extension)", category_for(path))


class CategoryTests(unittest.TestCase):
    def test_known_extensions_are_case_insensitive(self) -> None:
        self.assertEqual(category_for(Path("PHOTO.JpG")), "Images")
        self.assertEqual(category_for(Path("notes.PDF")), "Documents")
        self.assertEqual(category_for(Path("main.py")), "Code")

    def test_unknown_and_extensionless_files_fall_back_to_other(self) -> None:
        self.assertEqual(category_for(Path("mystery.blah")), "Other")
        self.assertEqual(category_for(Path("LICENSE")), "Other")

    def test_format_size(self) -> None:
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(1024), "1.0 KB")
        self.assertEqual(format_size(1024 * 1024), "1.0 MB")


class ScanAndPlanTests(unittest.TestCase):
    def test_scan_is_top_level_only_and_skips_hidden_files_and_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "report.pdf").write_text("content")
            (root / ".secret.txt").write_text("hidden")
            (root / "nested").mkdir()
            (root / "nested" / "child.jpg").write_text("child")
            records = scan_folder(root)
            self.assertEqual([r.path.name for r in records], ["report.pdf"])

    def test_scan_rejects_missing_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                scan_folder(Path(temp) / "missing")

    def test_plan_is_read_only_and_groups_by_category(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = root / "photo.png"
            original.write_bytes(b"img")
            plan = make_plan(scan_folder(root))
            self.assertEqual(len(plan), 1)
            self.assertEqual(plan[0].category, "Images")
            self.assertEqual(plan[0].target, root / "Images" / "photo.png")
            self.assertTrue(original.exists(), "Planning must never move files")

    def test_existing_target_gets_numbered_name_instead_of_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Images").mkdir()
            (root / "Images" / "photo.png").write_bytes(b"older")
            (root / "photo.png").write_bytes(b"newer")
            plan = make_plan(scan_folder(root))
            self.assertEqual(plan[0].target.name, "photo (1).png")
            self.assertEqual((root / "Images" / "photo.png").read_bytes(), b"older")

    def test_plan_ignores_non_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Documents").mkdir()
            (root / "test.txt").write_text("ok")
            plan = make_plan(scan_folder(root))
            self.assertEqual(len(plan), 1)

    def test_selected_root_named_like_a_category_does_not_suppress_plans(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "Images"
            root.mkdir()
            (root / "note.pdf").write_text("ok")
            plan = make_plan(scan_folder(root))
            self.assertEqual(len(plan), 1)
            self.assertEqual(plan[0].target, root / "Documents" / "note.pdf")


class MoveAndUndoTests(unittest.TestCase):
    def test_execute_moves_file_and_undo_restores_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = root / "report.pdf"
            original.write_bytes(b"pdf-data")
            plan = make_plan(scan_folder(root))
            completed, errors = execute_plan(plan)
            moved = root / "Documents" / "report.pdf"
            self.assertEqual(len(completed), 1)
            self.assertEqual(errors, [])
            self.assertFalse(original.exists())
            self.assertEqual(moved.read_bytes(), b"pdf-data")
            restored, undo_errors = undo_last_batch(root)
            self.assertEqual(restored, 1)
            self.assertEqual(undo_errors, [])
            self.assertEqual(original.read_bytes(), b"pdf-data")
            self.assertFalse(moved.exists())

    def test_undo_refuses_to_overwrite_an_original_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = root / "report.pdf"
            original.write_text("old")
            completed, errors = execute_plan(make_plan(scan_folder(root)))
            self.assertEqual(len(completed), 1)
            self.assertEqual(errors, [])
            original.write_text("new file created later")
            restored, undo_errors = undo_last_batch(root)
            self.assertEqual(restored, 0)
            self.assertTrue(undo_errors)
            self.assertEqual(original.read_text(), "new file created later")
            self.assertTrue((root / "Documents" / "report.pdf").exists())

    def test_undo_without_history_reports_a_helpful_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            count, errors = undo_last_batch(temp)
            self.assertEqual(count, 0)
            self.assertTrue(errors)


class DuplicateTests(unittest.TestCase):
    def test_duplicates_use_content_not_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a, b, c = root / "a.txt", root / "copy.txt", root / "different.txt"
            a.write_bytes(b"same contents")
            b.write_bytes(b"same contents")
            c.write_bytes(b"other")
            groups = find_duplicates([record(a), record(b), record(c)])
            self.assertEqual(len(groups), 1)
            self.assertEqual({p.name for p in groups[0]}, {"a.txt", "copy.txt"})

    def test_different_size_files_are_not_read_as_duplicate_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a, b = root / "a", root / "b"
            a.write_bytes(b"a")
            b.write_bytes(b"bb")
            self.assertEqual(find_duplicates([record(a), record(b)]), [])


if __name__ == "__main__":
    unittest.main()
