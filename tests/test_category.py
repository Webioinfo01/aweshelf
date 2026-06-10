"""Tests for category-related behavior."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aweshelf import cli as aweshelf
from aweshelf.lib.category import (
    add_category,
    list_categories,
    list_categories_with_bookmarks,
    remove_category,
)
from aweshelf.lib.store import load_bookmarks
from aweshelf.lib.store import load_store
from aweshelf.types import Bookmark


def make_bookmark(**kwargs) -> Bookmark:
    defaults = {
        "id": "aweshelf_0001",
        "provider": "claude",
        "session_id": "test-session-001",
        "title": "Test session",
        "category": "backend",
        "project_path": "/tmp/test",
        "aweswitch_profile": "cc-glm",
    }
    defaults.update(kwargs)
    return Bookmark(**defaults)


class CategoryStoreTests(unittest.TestCase):
    def test_list_categories_from_bookmarks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            data = {
                "version": 1,
                "bookmarks": [
                    make_bookmark(id="aweshelf_0001", category="backend").to_dict(),
                    make_bookmark(id="aweshelf_0002", session_id="s2", category="frontend").to_dict(),
                    make_bookmark(id="aweshelf_0003", session_id="s3", category="backend").to_dict(),
                ],
            }
            path.write_text(json.dumps(data))
            self.assertEqual(list_categories(path), ["backend", "frontend"])

    def test_list_categories_from_explicit_categories(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            data = {
                "version": 1,
                "bookmarks": [],
                "categories": ["backend", "backend", "  frontend  ", ""],
            }
            path.write_text(json.dumps(data))
            self.assertEqual(list_categories(path), ["backend", "frontend"])

    def test_add_category(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            added = add_category("  Backend  ", path)
            self.assertEqual(added, "Backend")
            self.assertEqual(load_store(path)[1], ["Backend"])

    def test_add_category_rejects_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            with self.assertRaises(ValueError):
                add_category("   ", path)

    def test_remove_category_not_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            add_category("backend", path)
            self.assertTrue(remove_category("backend", path))
            self.assertEqual(list_categories(path), [])

    def test_remove_category_in_use_requires_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            data = {
                "version": 1,
                "bookmarks": [
                    make_bookmark(session_id="s1", category="backend").to_dict(),
                ],
                "categories": ["backend"],
            }
            path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                remove_category("backend", path)

    def test_remove_category_with_force_clears_bookmarks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            data = {
                "version": 1,
                "bookmarks": [
                    make_bookmark(id="aweshelf_0001", session_id="s1", category="backend").to_dict(),
                    make_bookmark(id="aweshelf_0002", session_id="s2", category="backend").to_dict(),
                ],
                "categories": ["backend"],
            }
            path.write_text(json.dumps(data))
            self.assertTrue(remove_category("backend", path, clear_bookmarks=True))
            loaded = load_bookmarks(path)
            self.assertEqual([b.category for b in loaded], ["", ""])
            self.assertEqual(list_categories(path), [])

    def test_list_categories_with_bookmarks_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            data = {
                "version": 1,
                "bookmarks": [
                    {
                        "id": "aweshelf_0002",
                        "provider": "claude",
                        "session_id": "sess-100",
                        "title": "Task",
                        "category": "backend",
                        "project_path": "/tmp",
                        "first_prompt": "",
                        "bookmarked_at": "2026-01-01T00:00:00",
                    },
                    {
                        "id": "aweshelf_0001",
                        "provider": "codex",
                        "session_id": "sess-001",
                        "title": "Task A",
                        "category": "backend",
                        "project_path": "/tmp",
                        "first_prompt": "",
                        "bookmarked_at": "2026-01-01T00:00:00",
                    },
                ],
                "categories": ["backend", "frontend"],
            }
            path.write_text(json.dumps(data))
            categories, grouped = list_categories_with_bookmarks(path)
            self.assertEqual(categories, ["backend", "frontend"])
            self.assertEqual(
                [b["session_id"] for b in grouped["backend"]],
                ["sess-001", "sess-100"],
            )
            self.assertEqual(grouped["frontend"], [])


class CategoryCommandTests(unittest.TestCase):
    def _run_with_categories(self, args, categories=None, bookmarks=None):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            payload = {"version": 1, "bookmarks": []}
            if categories is not None:
                payload["categories"] = categories
            if bookmarks is not None:
                payload["bookmarks"] = [b.to_dict() for b in bookmarks]
            path.write_text(json.dumps(payload))
            env = {"AWESHELF_CONFIG": str(path)}
            return CliRunner(env=env).invoke(aweshelf.cli, args)

    def test_category_list_empty(self):
        result = self._run_with_categories(["category", "list"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("No categories yet.", result.output)

    def test_category_add_and_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            env = {"AWESHELF_CONFIG": str(path)}
            runner = CliRunner(env=env)
            add_result = runner.invoke(aweshelf.cli, ["category", "add", " backend "])
            self.assertEqual(add_result.exit_code, 0, add_result.output)
            self.assertIn("Added backend", add_result.output)
            list_result = runner.invoke(aweshelf.cli, ["category", "list"])
            self.assertEqual(list_result.exit_code, 0, list_result.output)
            self.assertIn("backend", list_result.output)

    def test_category_list_with_sessions(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            payload = {
                "version": 1,
                "bookmarks": [
                    {
                        "id": "aweshelf_0001",
                        "provider": "claude",
                        "session_id": "sess-002",
                        "title": "Task A",
                        "category": "backend",
                        "project_path": "/tmp",
                        "first_prompt": "",
                        "bookmarked_at": "2026-01-01T00:00:00",
                    },
                    {
                        "id": "aweshelf_0002",
                        "provider": "codex",
                        "session_id": "sess-001",
                        "title": "Task B",
                        "category": "backend",
                        "project_path": "/tmp",
                        "first_prompt": "",
                        "bookmarked_at": "2026-01-01T00:00:00",
                    },
                ],
                "categories": ["backend", "frontend"],
            }
            path.write_text(json.dumps(payload))
            runner = CliRunner(env={"AWESHELF_CONFIG": str(path)})
            result = runner.invoke(aweshelf.cli, ["category", "list", "--sessions"])
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("backend", result.output)
            self.assertIn("aweshelf_0001", result.output)
            self.assertIn("sess-001", result.output)
            self.assertIn("sess-002", result.output)
            self.assertIn("frontend", result.output)
            self.assertIn("(none)", result.output)

    def test_category_list_with_sessions_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            payload = {
                "version": 1,
                "bookmarks": [
                    {
                        "id": "aweshelf_0002",
                        "provider": "claude",
                        "session_id": "sess-100",
                        "title": "Task",
                        "category": "backend",
                        "project_path": "/tmp",
                        "first_prompt": "",
                        "bookmarked_at": "2026-01-01T00:00:00",
                    }
                ],
                "categories": ["backend", "frontend"],
            }
            path.write_text(json.dumps(payload))
            runner = CliRunner(env={"AWESHELF_CONFIG": str(path)})
            result = runner.invoke(aweshelf.cli, ["category", "list", "--sessions", "--json"])
            self.assertEqual(result.exit_code, 0, result.output)
            data = json.loads(result.output)
            self.assertEqual(data[0]["category"], "backend")
            self.assertEqual(data[0]["bookmarks"][0]["session_id"], "sess-100")
            self.assertEqual(data[1]["category"], "frontend")
            self.assertEqual(data[1]["bookmarks"], [])

    def test_category_rm_in_use_requires_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            payload = {
                "version": 1,
                "bookmarks": [
                    {
                        "id": "aweshelf_0001",
                        "provider": "claude",
                        "session_id": "sess-001",
                        "title": "Test",
                        "category": "backend",
                        "project_path": "/tmp",
                        "first_prompt": "",
                        "bookmarked_at": "2026-01-01T00:00:00",
                    }
                ],
                "categories": ["backend"],
            }
            path.write_text(json.dumps(payload))
            runner = CliRunner(env={"AWESHELF_CONFIG": str(path)})
            result = runner.invoke(aweshelf.cli, ["category", "rm", "backend"])
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("use --force", result.output)

    def test_category_rm_with_force_clears_bookmarks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            payload = {
                "version": 1,
                "bookmarks": [
                    {
                        "id": "aweshelf_0001",
                        "provider": "claude",
                        "session_id": "sess-001",
                        "title": "Test",
                        "category": "backend",
                        "project_path": "/tmp",
                        "first_prompt": "",
                        "bookmarked_at": "2026-01-01T00:00:00",
                    },
                    {
                        "id": "aweshelf_0002",
                        "provider": "codex",
                        "session_id": "sess-002",
                        "title": "Test2",
                        "category": "backend",
                        "project_path": "/tmp",
                        "first_prompt": "",
                        "bookmarked_at": "2026-01-01T00:00:00",
                    },
                ],
                "categories": ["backend"],
            }
            path.write_text(json.dumps(payload))
            runner = CliRunner(env={"AWESHELF_CONFIG": str(path)})
            result = runner.invoke(aweshelf.cli, ["category", "rm", "backend", "--force"])
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("Removed backend", result.output)
            raw = json.loads(Path(path).read_text())
            self.assertEqual([b["category"] for b in raw["bookmarks"]], ["", ""])
            self.assertNotIn("backend", raw.get("categories", []))


if __name__ == "__main__":
    unittest.main()
