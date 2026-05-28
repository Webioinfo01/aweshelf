"""Tests for CLI commands."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aweshelf import cli as aweshelf
from aweshelf.commands.list import format_table
from aweshelf.lib.store import load_bookmarks, save_bookmarks
from aweshelf.types import Bookmark


class CliTests(unittest.TestCase):
    def _run_with_empty_config(self, args):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            env = {"AWESHELF_CONFIG": str(path)}
            return CliRunner(env=env).invoke(aweshelf.cli, args)

    def _run_with_bookmarks(self, args, bookmarks):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            save_bookmarks(bookmarks, path)
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
        self.assertIn("show", result.output)
        self.assertIn("edit", result.output)
        self.assertIn("rm", result.output)
        self.assertIn("resume", result.output)

    def test_help_hides_recent_and_help_commands(self):
        result = CliRunner().invoke(aweshelf.cli, ["-h"])
        self.assertEqual(result.exit_code, 0)
        # "recent" should not appear as a command in the commands list
        self.assertNotIn("\n  recent ", result.output)
        self.assertNotIn("\n  help ", result.output)

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

    def test_format_table_includes_session_column(self):
        bookmark = Bookmark(
            id="aweshelf_0001",
            provider="claude",
            session_id="sess-001",
            title="Fix auth bug",
            category="backend",
            project_path="/tmp/test",
            aweswitch_profile="cc-glm",
        )
        output = format_table([bookmark])
        self.assertIn("ID", output.splitlines()[0])
        self.assertIn("PROVIDER", output.splitlines()[0])
        self.assertIn("TITLE", output.splitlines()[0])
        self.assertIn("CATEGORY", output.splitlines()[0])
        self.assertIn("PROFILE", output.splitlines()[0])
        self.assertIn("SESSION", output.splitlines()[0])
        self.assertIn("sess-001", output)

    def test_list_json_outputs_bookmark_array(self):
        bookmark = Bookmark(
            id="aweshelf_0001",
            provider="claude",
            session_id="sess-001",
            title="Fix auth bug",
            category="backend",
            project_path="/tmp/test",
            first_prompt="first prompt",
            aweswitch_profile="cc-glm",
            bookmarked_at="2026-05-20T10:00:00+00:00",
        )

        result = self._run_with_bookmarks(["list", "--json"], [bookmark])

        self.assertEqual(result.exit_code, 0, result.output)
        data = json.loads(result.output)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], "aweshelf_0001")
        self.assertEqual(data[0]["session_id"], "sess-001")
        self.assertEqual(data[0]["first_prompt"], "first prompt")

    def test_search_json_outputs_filtered_bookmark_array(self):
        bookmarks = [
            Bookmark(
                id="aweshelf_0001",
                provider="claude",
                session_id="sess-001",
                title="Fix auth bug",
                category="backend",
                project_path="/tmp/test",
            ),
            Bookmark(
                id="aweshelf_0002",
                provider="codex",
                session_id="sess-002",
                title="Write UI",
                category="frontend",
                project_path="/tmp/test",
            ),
        ]

        result = self._run_with_bookmarks(["search", "auth", "--json"], bookmarks)

        self.assertEqual(result.exit_code, 0, result.output)
        data = json.loads(result.output)
        self.assertEqual([item["id"] for item in data], ["aweshelf_0001"])

    def test_recent_json_outputs_recent_bookmarks_first(self):
        bookmarks = [
            Bookmark(
                id="aweshelf_0001",
                provider="claude",
                session_id="sess-001",
                title="Older",
                category="backend",
                project_path="/tmp/test",
                bookmarked_at="2026-05-20T10:00:00+00:00",
            ),
            Bookmark(
                id="aweshelf_0002",
                provider="codex",
                session_id="sess-002",
                title="Newer",
                category="frontend",
                project_path="/tmp/test",
                bookmarked_at="2026-05-21T10:00:00+00:00",
            ),
        ]

        result = self._run_with_bookmarks(["recent", "--json", "-n", "1"], bookmarks)

        self.assertEqual(result.exit_code, 0, result.output)
        data = json.loads(result.output)
        self.assertEqual([item["id"] for item in data], ["aweshelf_0002"])

    @patch(
        "aweshelf.commands.sessions.find_project_sessions",
        return_value=[
            {
                "session_id": "sess-001",
                "title": "Fix auth bug",
                "provider": "claude",
                "project_path": "/tmp/test",
                "source_path": "/tmp/test/sess-001.jsonl",
                "model": "claude-sonnet-4-20250514",
            }
        ],
    )
    def test_sessions_json_outputs_project_sessions(self, mock_sessions):
        result = CliRunner().invoke(aweshelf.cli, ["sessions", "--json", "-n", "1"])

        self.assertEqual(result.exit_code, 0, result.output)
        data = json.loads(result.output)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["session_id"], "sess-001")
        self.assertEqual(data[0]["provider"], "claude")

    @patch("aweshelf.commands.resume.find_bookmark")
    @patch("aweshelf.commands.resume.build_resume_target")
    def test_resume_dry_run_json_outputs_target(self, mock_build, mock_find):
        from pathlib import Path
        from aweshelf.lib.resume_target import ResumeTarget

        mock_find.return_value = Bookmark(
            id="aweshelf_0001",
            provider="claude",
            session_id="sess-001",
            title="Fix auth",
            category="backend",
            project_path="/tmp/project",
        )
        mock_build.return_value = ResumeTarget(
            argv=["claude", "--resume", "sess-001"],
            cwd=Path("/tmp/project"),
            warning=None,
        )

        result = CliRunner().invoke(aweshelf.cli, ["resume", "aweshelf_0001", "--dry-run", "--json"])

        self.assertEqual(result.exit_code, 0, result.output)
        data = json.loads(result.output)
        self.assertEqual(data["bookmark_id"], "aweshelf_0001")
        self.assertEqual(data["argv"], ["claude", "--resume", "sess-001"])
        self.assertEqual(data["cwd"], "/tmp/project")


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
        result = runner.invoke(aweshelf.cli, ["bookmark"], input="1\nFix login\nbackend\n")
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Bookmarked aweshelf_0001", result.output)
        bookmarks = load_bookmarks(path)
        self.assertEqual(len(bookmarks), 1)
        self.assertEqual(bookmarks[0].session_id, "sess-001")
        self.assertEqual(bookmarks[0].title, "Fix login")
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

    @patch("aweshelf.commands.bookmark.find_project_sessions")
    @patch("aweshelf.commands.bookmark.find_recent_session", return_value=MOCK_SESSIONS[1])
    @patch("aweshelf.commands.bookmark.detect_profile", return_value=None)
    @patch("aweshelf.commands.bookmark.load_aweswitch_config", return_value=None)
    def test_bookmark_current_uses_recent_session_without_listing(
        self,
        mock_config,
        mock_detect,
        mock_recent,
        mock_project_sessions,
    ):
        runner, path = self._run_with_config(["bookmark"])
        result = runner.invoke(aweshelf.cli, ["bookmark", "--current"], input="y\nCurrent title\ncurrent\n")
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Current session candidate:", result.output)
        self.assertIn("sess-002", result.output)
        self.assertNotIn("Pick a session", result.output)
        mock_project_sessions.assert_not_called()

        bookmarks = load_bookmarks(path)
        self.assertEqual(len(bookmarks), 1)
        self.assertEqual(bookmarks[0].session_id, "sess-002")
        self.assertEqual(bookmarks[0].title, "Current title")
        self.assertEqual(bookmarks[0].category, "current")

    @patch("aweshelf.commands.bookmark.find_recent_session", return_value=MOCK_SESSIONS[1])
    @patch("aweshelf.commands.bookmark.detect_profile", return_value=None)
    @patch("aweshelf.commands.bookmark.load_aweswitch_config", return_value=None)
    def test_bookmark_current_can_cancel_candidate(self, mock_config, mock_detect, mock_recent):
        runner, path = self._run_with_config(["bookmark"])
        result = runner.invoke(aweshelf.cli, ["bookmark", "--current"], input="n\n")
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Bookmark unchanged.", result.output)
        self.assertEqual(load_bookmarks(path), [])

    @patch("aweshelf.commands.bookmark.find_recent_session", return_value=MOCK_SESSIONS[1])
    @patch("aweshelf.commands.bookmark.detect_profile", return_value=None)
    @patch("aweshelf.commands.bookmark.load_aweswitch_config", return_value=None)
    def test_bookmark_current_updates_existing_session(self, mock_config, mock_detect, mock_recent):
        runner, path = self._run_with_config(["bookmark"])
        runner.invoke(aweshelf.cli, ["bookmark", "sess-002", "-t", "Old title", "-c", "old"])

        result = runner.invoke(aweshelf.cli, ["bookmark", "--current"], input="y\ny\nNew title\nnew\n")
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Session already bookmarked as aweshelf_0001. Update it?", result.output)
        self.assertIn("Updated aweshelf_0001", result.output)

        bookmarks = load_bookmarks(path)
        self.assertEqual(len(bookmarks), 1)
        self.assertEqual(bookmarks[0].id, "aweshelf_0001")
        self.assertEqual(bookmarks[0].title, "New title")
        self.assertEqual(bookmarks[0].category, "new")

    def test_bookmark_current_rejects_session_id(self):
        result = CliRunner().invoke(aweshelf.cli, ["bookmark", "sess-001", "--current"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("--current cannot be used with SESSION_ID", result.output)

    @patch("aweshelf.commands.bookmark.find_project_sessions", return_value=MOCK_SESSIONS)
    @patch("aweshelf.commands.bookmark.detect_profile", return_value="cc-glm")
    @patch(
        "aweshelf.commands.bookmark.load_aweswitch_config",
        return_value={"profiles": {"claude": {"cc-glm": {"env": {}}}}},
    )
    def test_bookmark_interactive_accepts_existing_profile(self, mock_config, mock_detect, mock_sessions):
        runner, path = self._run_with_config(["bookmark"])
        result = runner.invoke(aweshelf.cli, ["bookmark"], input="1\n\nbackend\ncc-glm\n")
        self.assertEqual(result.exit_code, 0, result.output)

        bookmarks = load_bookmarks(path)
        self.assertEqual(bookmarks[0].aweswitch_profile, "cc-glm")

    @patch("aweshelf.commands.bookmark.find_project_sessions", return_value=MOCK_SESSIONS)
    @patch("aweshelf.commands.bookmark.detect_profile", return_value=None)
    @patch(
        "aweshelf.commands.bookmark.load_aweswitch_config",
        return_value={"profiles": {"claude": {"cc-glm": {"env": {}}}}},
    )
    def test_bookmark_interactive_retries_unknown_profile(self, mock_config, mock_detect, mock_sessions):
        runner, path = self._run_with_config(["bookmark"])
        result = runner.invoke(aweshelf.cli, ["bookmark"], input="1\n\nbackend\nmissing\ncc-glm\n")
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("aweswitch profile not found: missing", result.output)

        bookmarks = load_bookmarks(path)
        self.assertEqual(bookmarks[0].aweswitch_profile, "cc-glm")

    @patch("aweshelf.commands.bookmark.find_project_sessions", return_value=MOCK_SESSIONS)
    @patch("aweshelf.commands.bookmark.detect_profile", return_value=None)
    @patch("aweshelf.commands.bookmark.load_aweswitch_config", return_value=None)
    def test_bookmark_marks_and_updates_existing_session(self, mock_config, mock_detect, mock_sessions):
        runner, path = self._run_with_config(["bookmark"])
        runner.invoke(aweshelf.cli, ["bookmark", "sess-001", "-t", "First", "-c", "cat"])

        result = runner.invoke(aweshelf.cli, ["bookmark"], input="1\ny\nUpdated\nnewcat\n")
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("bookmarked aweshelf_0001", result.output)
        self.assertIn("Session already bookmarked as aweshelf_0001. Update it?", result.output)
        self.assertIn("Updated aweshelf_0001", result.output)

        bookmarks = load_bookmarks(path)
        self.assertEqual(len(bookmarks), 1)
        self.assertEqual(bookmarks[0].id, "aweshelf_0001")
        self.assertEqual(bookmarks[0].title, "Updated")
        self.assertEqual(bookmarks[0].category, "newcat")

    @patch("aweshelf.commands.bookmark.find_project_sessions", return_value=MOCK_SESSIONS)
    @patch("aweshelf.commands.bookmark.detect_profile", return_value=None)
    @patch("aweshelf.commands.bookmark.load_aweswitch_config", return_value=None)
    def test_bookmark_existing_session_can_cancel_update(self, mock_config, mock_detect, mock_sessions):
        runner, path = self._run_with_config(["bookmark"])
        runner.invoke(aweshelf.cli, ["bookmark", "sess-001", "-t", "First", "-c", "cat"])

        result = runner.invoke(aweshelf.cli, ["bookmark"], input="1\n\n")
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Bookmark unchanged.", result.output)

        bookmarks = load_bookmarks(path)
        self.assertEqual(bookmarks[0].title, "First")
        self.assertEqual(bookmarks[0].category, "cat")

    @patch(
        "aweshelf.commands.bookmark.load_aweswitch_config",
        return_value={"profiles": {"claude": {"cc-glm": {"env": {}}}}},
    )
    def test_bookmark_with_unknown_profile_errors(self, mock_config):
        runner, _ = self._run_with_config(["bookmark"])
        result = runner.invoke(
            aweshelf.cli,
            ["bookmark", "sess-999", "-t", "My session", "-c", "test", "--profile", "missing"],
        )
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("aweswitch profile not found: missing", result.output)

    @patch(
        "aweshelf.commands.bookmark.load_aweswitch_config",
        return_value={"profiles": {"claude": {"cc-glm": {"env": {}}}, "codex": {"codex-openai": {"env": {}}}}},
    )
    def test_bookmark_profile_must_match_claude_profiles(self, mock_config):
        runner, _ = self._run_with_config(["bookmark"])
        result = runner.invoke(
            aweshelf.cli,
            ["bookmark", "sess-999", "-t", "My session", "-c", "test", "--profile", "codex-openai"],
        )
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("aweswitch profile not found: codex-openai", result.output)

    @patch("aweshelf.commands.bookmark.find_project_sessions", return_value=MOCK_SESSIONS)
    @patch("aweshelf.commands.bookmark.detect_profile", return_value=None)
    @patch(
        "aweshelf.commands.bookmark.load_aweswitch_config",
        return_value={"profiles": {"claude": {"cc-glm": {"env": {}}}, "codex": {"codex-openai": {"env": {}}}}},
    )
    def test_bookmark_profile_prompt_shows_claude_profiles_only(self, mock_config, mock_detect, mock_sessions):
        runner, _ = self._run_with_config(["bookmark"])
        result = runner.invoke(aweshelf.cli, ["bookmark"], input="1\n\nbackend\n\n")
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Available Claude profiles: cc-glm", result.output)
        self.assertNotIn("codex-openai", result.output)
        self.assertIn("blank stores no profile", result.output)

    @patch(
        "aweshelf.commands.bookmark.find_project_sessions",
        return_value=[{**MOCK_SESSIONS[0], "provider": "codex"}],
    )
    @patch("aweshelf.commands.bookmark.detect_profile", return_value=None)
    @patch(
        "aweshelf.commands.bookmark.load_aweswitch_config",
        return_value={"profiles": {"claude": {"cc-glm": {"env": {}}}, "codex": {"codex-openai": {"env": {}}}}},
    )
    def test_bookmark_skips_profile_for_codex(self, mock_config, mock_detect, mock_sessions):
        runner, path = self._run_with_config(["bookmark"])
        result = runner.invoke(aweshelf.cli, ["bookmark"], input="1\n\nbackend\n")
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertNotIn("Profile", result.output)
        self.assertNotIn("Available Claude profiles", result.output)
        self.assertIsNone(load_bookmarks(path)[0].aweswitch_profile)

    @patch("aweshelf.commands.bookmark.find_project_sessions", return_value=MOCK_SESSIONS)
    @patch("aweshelf.commands.bookmark.detect_profile", return_value=None)
    @patch("aweshelf.commands.bookmark.load_aweswitch_config", return_value=None)
    def test_bookmark_skips_profile_when_aweswitch_missing(self, mock_config, mock_detect, mock_sessions):
        runner, path = self._run_with_config(["bookmark"])
        result = runner.invoke(aweshelf.cli, ["bookmark"], input="1\n\nbackend\n")
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("aweswitch config not found; profile selection skipped.", result.output)
        self.assertIn("https://github.com/Webioinfo01/aweswitch", result.output)
        self.assertIsNone(load_bookmarks(path)[0].aweswitch_profile)

    @patch("aweshelf.commands.bookmark.find_project_sessions", return_value=[])
    def test_bookmark_no_sessions_exits(self, mock_sessions):
        runner, _ = self._run_with_config(["bookmark"])
        result = runner.invoke(aweshelf.cli, ["bookmark"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("no session found", result.output)

    @patch("aweshelf.commands.bookmark.find_project_sessions", return_value=MOCK_SESSIONS)
    @patch("aweshelf.commands.bookmark.detect_profile", return_value=None)
    @patch("aweshelf.commands.bookmark.load_aweswitch_config", return_value=None)
    def test_bookmark_duplicate_session_errors_non_interactive(self, mock_config, mock_detect, mock_sessions):
        runner, path = self._run_with_config(["bookmark"])
        runner.invoke(aweshelf.cli, ["bookmark", "sess-001", "-t", "First", "-c", "cat"])
        result = runner.invoke(aweshelf.cli, ["bookmark", "sess-001", "-t", "Second", "-c", "cat"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("already bookmarked", result.output)


class ListCommandTests(unittest.TestCase):
    def _run_with_data(self, args):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            path.write_text(json.dumps({
                "version": 1,
                "bookmarks": [
                    {
                        "id": "aweshelf_0001",
                        "provider": "claude",
                        "session_id": "sess-001",
                        "title": "First",
                        "category": "backend",
                        "project_path": "/tmp",
                        "aweswitch_profile": "cc-glm",
                        "bookmarked_at": "2026-01-01T00:00:00",
                    },
                    {
                        "id": "aweshelf_0002",
                        "provider": "codex",
                        "session_id": "sess-002",
                        "title": "Second",
                        "category": "frontend",
                        "project_path": "/tmp",
                        "aweswitch_profile": "codex",
                        "bookmarked_at": "2026-05-01T00:00:00",
                    },
                ],
            }))
            env = {"AWESHELF_CONFIG": str(path)}
            return CliRunner(env=env).invoke(aweshelf.cli, args)

    def test_list_sort_recent(self):
        result = self._run_with_data(["list", "--sort", "recent"])
        self.assertEqual(result.exit_code, 0)
        lines = result.output.strip().splitlines()
        self.assertIn("sess-002", lines[2])

    def test_list_limit(self):
        result = self._run_with_data(["list", "-n", "1"])
        self.assertEqual(result.exit_code, 0)
        lines = result.output.strip().splitlines()
        self.assertEqual(len(lines), 3)

    def test_list_sort_recent_with_limit(self):
        result = self._run_with_data(["list", "--sort", "recent", "-n", "1"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("sess-002", result.output)
        self.assertNotIn("sess-001", result.output)


class ShowCommandTests(unittest.TestCase):
    def _run_with_data(self, args):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            path.write_text(json.dumps({
                "version": 1,
                "bookmarks": [
                    {
                        "id": "aweshelf_0001",
                        "provider": "claude",
                        "session_id": "sess-001",
                        "title": "Test",
                        "category": "backend",
                        "project_path": "/tmp",
                        "aweswitch_profile": "cc-glm",
                        "bookmarked_at": "2026-01-01T00:00:00",
                    },
                ],
            }))
            env = {"AWESHELF_CONFIG": str(path)}
            return CliRunner(env=env).invoke(aweshelf.cli, args)

    def test_show_by_id(self):
        result = self._run_with_data(["show", "aweshelf_0001"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Test", result.output)

    def test_show_by_session_id(self):
        result = self._run_with_data(["show", "sess-001"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Test", result.output)

    def test_show_not_found(self):
        result = self._run_with_data(["show", "nonexistent"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("not found", result.output)


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

    def test_search_matches_first_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bookmarks.json"
            path.write_text(json.dumps({
                "version": 1,
                "bookmarks": [
                    {
                        "id": "aweshelf_0001",
                        "provider": "claude",
                        "session_id": "sess-001",
                        "title": "Test",
                        "category": "backend",
                        "project_path": "/tmp",
                        "first_prompt": "Investigate billing webhook",
                        "aweswitch_profile": "cc-glm",
                        "bookmarked_at": "2026-01-01T00:00:00",
                    },
                ],
            }))
            result = CliRunner(env={"AWESHELF_CONFIG": str(path)}).invoke(
                aweshelf.cli,
                ["search", "webhook"],
            )
            self.assertEqual(result.exit_code, 0)
            self.assertIn("aweshelf_0001", result.output)


if __name__ == "__main__":
    unittest.main()
