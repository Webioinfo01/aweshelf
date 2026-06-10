"""Tests for lib/store.py."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aweshelf.types import Bookmark
from aweshelf.lib.store import (
    BookmarkStoreError,
    generate_id,
    load_bookmarks,
    save_bookmarks,
    add_bookmark,
    remove_bookmark,
    update_bookmark,
    find_bookmark,
    find_by_session_id,
)


def make_bookmark(**kwargs) -> Bookmark:
    defaults = {
        "id": generate_id(),
        "provider": "claude",
        "session_id": "test-session-001",
        "title": "Test session",
        "category": "backend",
        "project_path": "/tmp/test",
        "aweswitch_profile": "cc-glm",
    }
    defaults.update(kwargs)
    return Bookmark(**defaults)


class StoreTests(unittest.TestCase):
    def test_generate_id_format(self):
        bid = generate_id([])
        self.assertEqual(bid, "aweshelf_0001")

    def test_generate_id_uses_next_highest_sequential_id(self):
        bookmarks = [
            make_bookmark(id="aweshelf_0001", session_id="s1"),
            make_bookmark(id="bkm_aaaaaa", session_id="s2"),
            make_bookmark(id="aweshelf_0012", session_id="s3"),
        ]
        self.assertEqual(generate_id(bookmarks), "aweshelf_0013")

    def test_load_empty_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            result = load_bookmarks(path)
            self.assertEqual(result, [])

    def test_load_nonexistent_file(self):
        result = load_bookmarks(Path("/nonexistent/path.json"))
        self.assertEqual(result, [])

    def test_load_invalid_json_raises_store_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            path.write_text("{bad json")

            with self.assertRaises(BookmarkStoreError):
                load_bookmarks(path)

    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            b = make_bookmark()
            save_bookmarks([b], path)

            loaded = load_bookmarks(path)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].id, b.id)
            self.assertEqual(loaded[0].title, b.title)

    def test_first_prompt_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            b = make_bookmark(first_prompt="Full first prompt text here")
            save_bookmarks([b], path)
            loaded = load_bookmarks(path)
            self.assertEqual(loaded[0].first_prompt, "Full first prompt text here")

    def test_first_prompt_backward_compat(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            path.write_text(json.dumps({"version": 1, "bookmarks": [{
                "id": "aweshelf_0001",
                "provider": "claude",
                "session_id": "s1",
                "title": "Old bookmark",
                "category": "",
                "project_path": "/tmp",
            }]}))
            loaded = load_bookmarks(path)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].first_prompt, "")

    def test_save_sets_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            save_bookmarks([make_bookmark()], path)
            import stat
            mode = stat.S_IMODE(path.stat().st_mode)
            self.assertEqual(mode, 0o600)

    def test_add_bookmark(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            b = make_bookmark(id="")
            result = add_bookmark(b, path)
            self.assertEqual(result.id, "aweshelf_0001")

            loaded = load_bookmarks(path)
            self.assertEqual(len(loaded), 1)

    def test_add_duplicate_session_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            b1 = make_bookmark(id="bkm_aaaaaa")
            b2 = make_bookmark(id="bkm_bbbbbb", session_id="test-session-001")
            add_bookmark(b1, path)
            with self.assertRaises(ValueError):
                add_bookmark(b2, path)

    def test_remove_bookmark(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            b = make_bookmark(id="bkm_aaaaaa")
            add_bookmark(b, path)
            result = remove_bookmark("bkm_aaaaaa", path)
            self.assertTrue(result)
            self.assertEqual(load_bookmarks(path), [])

    def test_remove_nonexistent_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            result = remove_bookmark("bkm_nope", path)
            self.assertFalse(result)

    def test_find_bookmark(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            b = make_bookmark(id="bkm_aaaaaa")
            add_bookmark(b, path)
            found = find_bookmark("bkm_aaaaaa", path)
            self.assertIsNotNone(found)
            self.assertEqual(found.title, "Test session")

    def test_find_by_session_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            b = make_bookmark()
            add_bookmark(b, path)
            found = find_by_session_id("test-session-001", path)
            self.assertIsNotNone(found)

    def test_update_bookmark(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            b = make_bookmark(id="bkm_aaaaaa")
            add_bookmark(b, path)
            updated = update_bookmark("bkm_aaaaaa", path, title="New title", category="frontend")
            self.assertIsNotNone(updated)
            self.assertEqual(updated.title, "New title")
            self.assertEqual(updated.category, "frontend")

    def test_update_nonexistent_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            result = update_bookmark("bkm_nope", path, title="x")
            self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
