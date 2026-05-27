"""Session file discovery for Claude Code and Codex."""

import os
from pathlib import Path

from aweshelf.lib.session import parse_session_meta


CLAUDE_PROJECTS_DIR = Path("~/.claude/projects").expanduser()
CODEX_SESSIONS_DIR = Path("~/.codex/sessions").expanduser()


def find_claude_sessions() -> list[dict]:
    results = []
    if not CLAUDE_PROJECTS_DIR.exists():
        return results
    for jsonl_path in CLAUDE_PROJECTS_DIR.rglob("*.jsonl"):
        if "/subagents/" in str(jsonl_path):
            continue
        try:
            meta = parse_session_meta(jsonl_path)
            meta["source_path"] = str(jsonl_path)
            results.append(meta)
        except Exception:
            continue
    return results


def find_codex_sessions() -> list[dict]:
    results = []
    if not CODEX_SESSIONS_DIR.exists():
        return results
    for jsonl_path in CODEX_SESSIONS_DIR.rglob("*.jsonl"):
        try:
            meta = parse_session_meta(jsonl_path)
            meta["source_path"] = str(jsonl_path)
            results.append(meta)
        except Exception:
            continue
    return results


def find_all_sessions() -> list[dict]:
    return find_claude_sessions() + find_codex_sessions()


def _filter_project_sessions(sessions: list[dict], project_path: str) -> list[dict]:
    """Filter sessions matching project_path, fall back to all sessions."""
    project_sessions = []
    for s in sessions:
        pp = s.get("project_path", "")
        if pp and (project_path.startswith(pp) or pp.startswith(project_path)):
            project_sessions.append(s)
    return project_sessions or sessions


def _sort_by_mtime(sessions: list[dict]) -> list[dict]:
    """Sort sessions by file modification time, newest first."""
    def get_mtime(s):
        sp = s.get("source_path", "")
        try:
            return os.path.getmtime(sp)
        except OSError:
            return 0
    return sorted(sessions, key=get_mtime, reverse=True)


def find_project_sessions(project_path: str | None = None) -> list[dict]:
    cwd = project_path or os.getcwd()
    sessions = find_all_sessions()
    filtered = _filter_project_sessions(sessions, cwd)
    return _sort_by_mtime(filtered)


def find_recent_session(project_path: str | None = None) -> dict | None:
    sessions = find_project_sessions(project_path)
    return sessions[0] if sessions else None
