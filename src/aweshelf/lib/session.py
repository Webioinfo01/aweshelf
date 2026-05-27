"""Session JSONL metadata extraction."""

import json
import re
from collections.abc import Callable
from pathlib import Path

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


def extract_title_from_messages(messages: list[dict]) -> str | None:
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


def _parse_jsonl(
    jsonl_path: Path,
    extract_fields: Callable[[dict, dict], None],
    provider: str,
    max_lines: int = 80,
) -> dict:
    """Shared JSONL parser. extract_fields(entry, state) mutates state per entry."""
    state = {
        "session_id": None,
        "project_path": None,
        "model": None,
        "created_at": None,
        "user_contents": [],
    }

    try:
        with open(jsonl_path) as f:
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
                extract_fields(entry, state)
    except (OSError, FileNotFoundError):
        pass

    if not state["session_id"]:
        state["session_id"] = jsonl_path.stem

    title = extract_title_from_messages(state["user_contents"]) or "Untitled session"

    return {
        "session_id": state["session_id"],
        "title": title,
        "model": state["model"],
        "project_path": state["project_path"] or "",
        "created_at": state["created_at"],
        "provider": provider,
    }


def _extract_claude_fields(entry: dict, state: dict) -> None:
    """Extract fields from a Claude Code JSONL entry."""
    entry_type = entry.get("type", "")

    if not state["session_id"]:
        if entry_type == "permission-mode":
            state["session_id"] = entry.get("sessionId")
        elif entry_type == "summary":
            state["session_id"] = entry.get("sessionId") or entry.get("summary", {}).get("sessionId")

    if not state["project_path"]:
        if entry_type == "summary":
            state["project_path"] = entry.get("cwd") or entry.get("summary", {}).get("cwd")
        elif entry_type == "user":
            cwd = entry.get("cwd")
            if cwd:
                state["project_path"] = cwd

    if entry_type == "user":
        msg = entry.get("message", {})
        content = msg.get("content", "")
        if content:
            state["user_contents"].append({"content": content})
    if entry.get("role") == "user":
        content = entry.get("content", "")
        if content:
            state["user_contents"].append({"content": content})

    if not state["model"]:
        if entry_type == "assistant":
            msg = entry.get("message", {})
            state["model"] = msg.get("model", "")
        elif entry.get("role") == "assistant":
            state["model"] = entry.get("model", "")

    if not state["created_at"]:
        ts = entry.get("timestamp")
        if ts:
            state["created_at"] = ts


def _extract_codex_fields(entry: dict, state: dict) -> None:
    """Extract fields from a Codex CLI JSONL entry."""
    entry_type = entry.get("type", "")
    payload = entry.get("payload", {})

    if entry_type == "session_meta":
        state["session_id"] = state["session_id"] or payload.get("id")
        state["project_path"] = state["project_path"] or payload.get("cwd")
        if not state["created_at"]:
            state["created_at"] = payload.get("timestamp")

    if entry_type == "event_msg":
        payload_type = payload.get("type", "")
        if payload_type == "user_message":
            msg = payload.get("message", "")
            if msg:
                state["user_contents"].append({"content": msg})
        if not state["created_at"]:
            ts = entry.get("timestamp")
            if ts:
                state["created_at"] = ts

    if entry_type == "response_item" and not state["model"]:
        state["model"] = entry.get("model", "")


def parse_claude_session(jsonl_path: Path, max_lines: int = 80) -> dict:
    """Parse Claude Code session JSONL."""
    return _parse_jsonl(jsonl_path, _extract_claude_fields, "claude", max_lines)


def parse_codex_session(jsonl_path: Path, max_lines: int = 80) -> dict:
    """Parse Codex CLI session JSONL."""
    return _parse_jsonl(jsonl_path, _extract_codex_fields, "codex", max_lines)


def parse_session_meta(jsonl_path: Path, max_lines: int = 80) -> dict:
    jsonl_path = Path(jsonl_path).expanduser()
    provider = detect_provider(jsonl_path)
    if provider == "codex":
        return parse_codex_session(jsonl_path, max_lines)
    return parse_claude_session(jsonl_path, max_lines)
