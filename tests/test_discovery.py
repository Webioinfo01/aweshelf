"""Tests for lib/discovery.py."""

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aweshelf.lib.discovery import (
    _filter_project_sessions,
    _sort_by_mtime,
    find_claude_sessions,
    find_codex_sessions,
    find_project_sessions,
    find_recent_session,
)


def write_jsonl(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


class FilterProjectSessionsTests(unittest.TestCase):
    def test_returns_matching_sessions(self):
        sessions = [
            {"session_id": "s1", "project_path": "/home/user/project-a"},
            {"session_id": "s2", "project_path": "/home/user/project-b"},
        ]
        result = _filter_project_sessions(sessions, "/home/user/project-a")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["session_id"], "s1")

    def test_falls_back_to_all_when_no_match(self):
        sessions = [
            {"session_id": "s1", "project_path": "/other/path"},
        ]
        result = _filter_project_sessions(sessions, "/home/user/project-a")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["session_id"], "s1")

    def test_matches_subpath(self):
        sessions = [
            {"session_id": "s1", "project_path": "/home/user/project"},
        ]
        result = _filter_project_sessions(sessions, "/home/user/project/sub/dir")
        self.assertEqual(len(result), 1)

    def test_empty_project_path_falls_back(self):
        sessions = [
            {"session_id": "s1", "project_path": ""},
        ]
        result = _filter_project_sessions(sessions, "/home/user/project")
        self.assertEqual(len(result), 1)


class SortByMtimeTests(unittest.TestCase):
    def test_sorts_newest_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            p1 = Path(tmp) / "old.jsonl"
            p2 = Path(tmp) / "new.jsonl"
            p1.write_text("{}\n")
            time.sleep(0.05)
            p2.write_text("{}\n")

            sessions = [
                {"session_id": "old", "source_path": str(p1)},
                {"session_id": "new", "source_path": str(p2)},
            ]
            result = _sort_by_mtime(sessions)
            self.assertEqual(result[0]["session_id"], "new")

    def test_handles_missing_source_path(self):
        sessions = [
            {"session_id": "s1", "source_path": ""},
            {"session_id": "s2", "source_path": "/nonexistent/path"},
        ]
        result = _sort_by_mtime(sessions)
        self.assertEqual(len(result), 2)


class FindSessionsTests(unittest.TestCase):
    def test_find_claude_sessions_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            import aweshelf.lib.discovery as disc
            orig = disc.CLAUDE_PROJECTS_DIR
            disc.CLAUDE_PROJECTS_DIR = Path(tmp)
            try:
                result = find_claude_sessions()
                self.assertEqual(result, [])
            finally:
                disc.CLAUDE_PROJECTS_DIR = orig

    def test_find_claude_sessions_with_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_jsonl(
                Path(tmp) / "projects" / "test-session.jsonl",
                [
                    {"type": "summary", "sessionId": "abc-123", "cwd": "/tmp/proj"},
                    {"role": "user", "content": "Fix bug"},
                ],
            )
            import aweshelf.lib.discovery as disc
            orig = disc.CLAUDE_PROJECTS_DIR
            disc.CLAUDE_PROJECTS_DIR = Path(tmp) / "projects"
            try:
                result = find_claude_sessions()
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0]["session_id"], "abc-123")
                self.assertIn("source_path", result[0])
            finally:
                disc.CLAUDE_PROJECTS_DIR = orig

    def test_find_codex_sessions_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            import aweshelf.lib.discovery as disc
            orig = disc.CODEX_SESSIONS_DIR
            disc.CODEX_SESSIONS_DIR = Path(tmp)
            try:
                result = find_codex_sessions()
                self.assertEqual(result, [])
            finally:
                disc.CODEX_SESSIONS_DIR = orig

    def test_find_project_sessions_returns_sorted(self):
        with tempfile.TemporaryDirectory() as tmp:
            p1 = Path(tmp) / "s1.jsonl"
            p2 = Path(tmp) / "s2.jsonl"
            write_jsonl(p1, [{"role": "user", "content": "first"}])
            time.sleep(0.05)
            write_jsonl(p2, [{"role": "user", "content": "second"}])

            import aweshelf.lib.discovery as disc
            orig_claude = disc.CLAUDE_PROJECTS_DIR
            orig_codex = disc.CODEX_SESSIONS_DIR
            disc.CLAUDE_PROJECTS_DIR = Path(tmp)
            disc.CODEX_SESSIONS_DIR = Path(tmp) / "empty"
            (Path(tmp) / "empty").mkdir(exist_ok=True)
            try:
                result = find_project_sessions()
                self.assertEqual(len(result), 2)
                self.assertEqual(result[0]["title"], "second")
            finally:
                disc.CLAUDE_PROJECTS_DIR = orig_claude
                disc.CODEX_SESSIONS_DIR = orig_codex

    def test_find_recent_session_returns_none_when_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            import aweshelf.lib.discovery as disc
            orig_claude = disc.CLAUDE_PROJECTS_DIR
            orig_codex = disc.CODEX_SESSIONS_DIR
            disc.CLAUDE_PROJECTS_DIR = Path(tmp)
            disc.CODEX_SESSIONS_DIR = Path(tmp)
            try:
                result = find_recent_session()
                self.assertIsNone(result)
            finally:
                disc.CLAUDE_PROJECTS_DIR = orig_claude
                disc.CODEX_SESSIONS_DIR = orig_codex


if __name__ == "__main__":
    unittest.main()
