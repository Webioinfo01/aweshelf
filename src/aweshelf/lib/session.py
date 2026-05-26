"""Session JSONL metadata extraction."""

import json
import re
from pathlib import Path
from typing import Optional

TAG_RE = re.compile(r"<[^>]+>")


def detect_provider(jsonl_path: Path) -> str:
    path_str = str(jsonl_path)
    if "/.claude/" in path_str:
        return "claude"
    if "/.codex/" in path_str:
        return "codex"
    return "claude"


def clean_title(text: str) -> str:
    text = TAG_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _truncate(text: str, limit: int = 80) -> str:
    text = text.strip()
    if len(text) > limit:
        text = text[: limit - 3] + "..."
    return text


def extract_title_from_messages(messages: list[dict]) -> Optional[str]:
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str) and content.strip():
            text = clean_title(content)
            if not text:
                continue
            return _truncate(text)
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text = clean_title(part.get("text", ""))
                    if text:
                        return _truncate(text)
    return None


def parse_claude_session(jsonl_path: Path, max_lines: int = 80) -> dict:
    """Parse Claude Code session JSONL."""
    user_contents = []
    session_id = None
    model = None
    project_path = None
    created_at = None

    try:
        with open(jsonl_path, "r") as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                entry_type = entry.get("type", "")

                if not session_id:
                    if entry_type == "permission-mode":
                        session_id = entry.get("sessionId")
                    elif entry_type == "summary":
                        session_id = entry.get("sessionId") or entry.get("summary", {}).get("sessionId")

                if not project_path:
                    if entry_type == "summary":
                        project_path = entry.get("cwd") or entry.get("summary", {}).get("cwd")
                    elif entry_type == "user":
                        cwd = entry.get("cwd")
                        if cwd:
                            project_path = cwd

                if entry_type == "user":
                    msg = entry.get("message", {})
                    content = msg.get("content", "")
                    if content:
                        user_contents.append({"content": content})
                if entry.get("role") == "user":
                    content = entry.get("content", "")
                    if content:
                        user_contents.append({"content": content})

                if not model:
                    if entry_type == "assistant":
                        msg = entry.get("message", {})
                        model = msg.get("model", "")
                    elif entry.get("role") == "assistant":
                        model = entry.get("model", "")

                if not created_at:
                    ts = entry.get("timestamp")
                    if ts:
                        created_at = ts
    except (OSError, FileNotFoundError):
        pass

    if not session_id:
        session_id = jsonl_path.stem

    title = extract_title_from_messages(user_contents) or "Untitled session"

    return {
        "session_id": session_id,
        "title": title,
        "model": model,
        "project_path": project_path or "",
        "created_at": created_at,
        "provider": "claude",
    }


def parse_codex_session(jsonl_path: Path, max_lines: int = 80) -> dict:
    """Parse Codex CLI session JSONL."""
    user_contents = []
    session_id = None
    model = None
    project_path = None
    created_at = None

    try:
        with open(jsonl_path, "r") as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                entry_type = entry.get("type", "")
                payload = entry.get("payload", {})

                if entry_type == "session_meta":
                    session_id = session_id or payload.get("id")
                    project_path = project_path or payload.get("cwd")
                    if not created_at:
                        created_at = payload.get("timestamp")

                if entry_type == "event_msg":
                    payload_type = payload.get("type", "")
                    if payload_type == "user_message":
                        msg = payload.get("message", "")
                        if msg:
                            user_contents.append({"content": msg})
                    if not created_at:
                        ts = entry.get("timestamp")
                        if ts:
                            created_at = ts

                if entry_type == "response_item":
                    if not model:
                        model = entry.get("model", "")
    except (OSError, FileNotFoundError):
        pass

    if not session_id:
        session_id = jsonl_path.stem

    title = extract_title_from_messages(user_contents) or "Untitled session"

    return {
        "session_id": session_id,
        "title": title,
        "model": model,
        "project_path": project_path or "",
        "created_at": created_at,
        "provider": "codex",
    }


def parse_session_meta(jsonl_path: Path, max_lines: int = 80) -> dict:
    jsonl_path = Path(jsonl_path).expanduser()
    provider = detect_provider(jsonl_path)
    if provider == "codex":
        return parse_codex_session(jsonl_path, max_lines)
    return parse_claude_session(jsonl_path, max_lines)
