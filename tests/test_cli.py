"""Tests for CLI commands."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aweshelf import cli as aweshelf
from aweshelf.lib.store import load_bookmarks


class CliTests(unittest.TestCase):
    def _run_with_empty_config(self, args):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            env = {"AWESHELF_CONFIG": str(path)}
            return CliRunner(env=env).invoke(aweshelf.cli, args)

    def test_help_layout(self):
        result = CliRunner().invoke(aweshelf.cli, ["-h"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Usage: aweshelf [OPTIONS] COMMAND [ARGS]...", result.output)
        self.assertIn("Bookmark, categorize, and restore AI coding sessions.", result.output)
        self.assertIn("-v, --version", result.output)
        self.assertIn("bookmark", result.output)
        self.assertIn("browse", result.output)
        self.assertIn("list", result.output)
        self.assertIn("search", result.output)
        self.assertIn("recent", result.output)
        self.assertIn("show", result.output)
        self.assertIn("edit", result.output)
        self.assertIn("rm", result.output)
        self.assertIn("resume", result.output)
        self.assertIn("help", result.output)

    def test_version_option(self):
        import aweshelf as pkg
        expected = pkg.__version__
        result = CliRunner().invoke(aweshelf.cli, ["-v"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn(expected, result.output)

    def test_list_empty(self):
        result = self._run_with_empty_config(["list"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("No bookmarks found.", result.output)

    def test_recent_empty(self):
        result = self._run_with_empty_config(["recent"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("No bookmarks found.", result.output)

    def test_search_empty(self):
        result = self._run_with_empty_config(["search", "nonexistent"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("No bookmarks found.", result.output)

    def test_show_not_found(self):
        result = self._run_with_empty_config(["show", "bkm_nope"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("not found", result.output)

    def test_edit_not_found(self):
        result = self._run_with_empty_config(["edit", "bkm_nope", "-t", "new"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("not found", result.output)

    def test_rm_not_found(self):
        result = self._run_with_empty_config(["rm", "bkm_nope"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("not found", result.output)

    def test_resume_not_found(self):
        result = self._run_with_empty_config(["resume", "bkm_nope"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("not found", result.output)

    def test_edit_no_fields(self):
        result = self._run_with_empty_config(["edit", "bkm_test"])
        self.assertNotEqual(result.exit_code, 0)

    def test_package_entry_point(self):
        pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
        data = pyproject.read_text()
        self.assertIn('aweshelf = "aweshelf.cli:main"', data)
        self.assertIn('click>=8.1', data)
        self.assertIn('textual>=0.40', data)


MOCK_SESSIONS = [
    {
        "session_id": "sess-001",
        "title": "Fix auth bug",
        "provider": "claude",
        "project_path": "/tmp/test",
        "source_path": "/tmp/test/sess-001.jsonl",
        "model": "claude-sonnet-4-20250514",
    },
    {
        "session_id": "sess-002",
        "title": "Add dark mode",
        "provider": "claude",
        "project_path": "/tmp/test",
        "source_path": "/tmp/test/sess-002.jsonl",
        "model": "claude-sonnet-4-20250514",
    },
]


class BookmarkCommandTests(unittest.TestCase):
    def _run_with_config(self, args, env_extra=None):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            env = {"AWESHELF_CONFIG": str(path)}
            if env_extra:
                env.update(env_extra)
            runner = CliRunner(env=env)
            return runner, path

    @patch("aweshelf.commands.bookmark.find_project_sessions", return_value=MOCK_SESSIONS)
    @patch("aweshelf.commands.bookmark.detect_profile", return_value=None)
    @patch("aweshelf.commands.bookmark.load_aweswitch_config", return_value=None)
    def test_bookmark_picks_session_interactively(self, mock_config, mock_detect, mock_sessions):
        runner, path = self._run_with_config(["bookmark"])
        result = runner.invoke(aweshelf.cli, ["bookmark"], input="1\nbackend\n")
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Bookmarked aweshelf_0001", result.output)
        bookmarks = load_bookmarks(path)
        self.assertEqual(len(bookmarks), 1)
        self.assertEqual(bookmarks[0].session_id, "sess-001")
        self.assertEqual(bookmarks[0].category, "backend")

    @patch("aweshelf.commands.bookmark.find_project_sessions", return_value=MOCK_SESSIONS)
    @patch("aweshelf.commands.bookmark.detect_profile", return_value=None)
    @patch("aweshelf.commands.bookmark.load_aweswitch_config", return_value=None)
    def test_bookmark_with_session_id(self, mock_config, mock_detect, mock_sessions):
        runner, path = self._run_with_config(["bookmark"])
        result = runner.invoke(aweshelf.cli, ["bookmark", "sess-999", "-t", "My session", "-c", "test"])
        self.assertEqual(result.exit_code, 0, result.output)
        bookmarks = load_bookmarks(path)
        self.assertEqual(len(bookmarks), 1)
        self.assertEqual(bookmarks[0].session_id, "sess-999")
        self.assertEqual(bookmarks[0].title, "My session")

    @patch("aweshelf.commands.bookmark.find_project_sessions", return_value=[])
    def test_bookmark_no_sessions_exits(self, mock_sessions):
        runner, _ = self._run_with_config(["bookmark"])
        result = runner.invoke(aweshelf.cli, ["bookmark"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("no session found", result.output)

    @patch("aweshelf.commands.bookmark.find_project_sessions", return_value=MOCK_SESSIONS)
    @patch("aweshelf.commands.bookmark.detect_profile", return_value=None)
    @patch("aweshelf.commands.bookmark.load_aweswitch_config", return_value=None)
    def test_bookmark_duplicate_session_errors(self, mock_config, mock_detect, mock_sessions):
        runner, path = self._run_with_config(["bookmark"])
        runner.invoke(aweshelf.cli, ["bookmark", "sess-001", "-t", "First", "-c", "cat"])
        result = runner.invoke(aweshelf.cli, ["bookmark", "sess-001", "-t", "Second", "-c", "cat"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("already bookmarked", result.output)


class SearchCommandTests(unittest.TestCase):
    @patch("aweshelf.commands.bookmark.find_project_sessions", return_value=MOCK_SESSIONS)
    @patch("aweshelf.commands.bookmark.detect_profile", return_value=None)
    @patch("aweshelf.commands.bookmark.load_aweswitch_config", return_value=None)
    def test_search_matches_category(self, mock_config, mock_detect, mock_sessions):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            env = {"AWESHELF_CONFIG": str(path)}
            runner = CliRunner(env=env)
            runner.invoke(aweshelf.cli, ["bookmark", "sess-001", "-t", "Test", "-c", "backend"])
            result = runner.invoke(aweshelf.cli, ["search", "backend"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("aweshelf_0001", result.output)

    @patch("aweshelf.commands.bookmark.find_project_sessions", return_value=MOCK_SESSIONS)
    @patch("aweshelf.commands.bookmark.detect_profile", return_value=None)
    @patch("aweshelf.commands.bookmark.load_aweswitch_config", return_value=None)
    def test_search_matches_session_id(self, mock_config, mock_detect, mock_sessions):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            env = {"AWESHELF_CONFIG": str(path)}
            runner = CliRunner(env=env)
            runner.invoke(aweshelf.cli, ["bookmark", "sess-001", "-t", "Test", "-c", "cat"])
            result = runner.invoke(aweshelf.cli, ["search", "sess-001"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("aweshelf_0001", result.output)


if __name__ == "__main__":
    unittest.main()
