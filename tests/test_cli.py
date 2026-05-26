"""Tests for CLI commands."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aweshelf import cli as aweshelf


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


if __name__ == "__main__":
    unittest.main()
