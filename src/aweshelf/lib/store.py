"""JSON file CRUD for bookmarks."""

import json
import os
import re
import tempfile
from pathlib import Path

from aweshelf.types import Bookmark


CONFIG_DIR = Path("~/.config/aweshelf")
ID_RE = re.compile(r"^aweshelf_(\d+)$")


class BookmarkStoreError(ValueError):
    """Raised when the bookmark store cannot be read safely."""


def bookmark_path() -> Path:
    env = os.environ.get("AWESHELF_CONFIG")
    if env:
        return Path(env).expanduser()
    return (CONFIG_DIR / "bookmarks.json").expanduser()


def generate_id(bookmarks: list[Bookmark] | None = None) -> str:
    bookmarks = bookmarks or []
    highest = 0
    for bookmark in bookmarks:
        match = ID_RE.match(bookmark.id)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"aweshelf_{highest + 1:04d}"


def load_bookmarks(path: Path | None = None) -> list[Bookmark]:
    path = path or bookmark_path()
    path = Path(path).expanduser()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise BookmarkStoreError(f"invalid bookmark JSON at {path}: {exc}") from exc
    except OSError as exc:
        raise BookmarkStoreError(f"failed to read bookmark store at {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("bookmarks", []), list):
        raise BookmarkStoreError(f"bookmark store at {path} must contain a bookmarks list")
    raw = data.get("bookmarks", [])
    try:
        return [Bookmark.from_dict(b) for b in raw]
    except (KeyError, TypeError) as exc:
        raise BookmarkStoreError(f"bookmark store at {path} contains invalid bookmark data") from exc


def save_bookmarks(bookmarks: list[Bookmark], path: Path | None = None) -> None:
    path = path or bookmark_path()
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"version": 1, "bookmarks": [b.to_dict() for b in bookmarks]}
    fd, tmp_name = tempfile.mkstemp(prefix=".bookmarks-", suffix=".json", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.chmod(tmp_name, 0o600)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def find_bookmark(bookmark_id: str, path: Path | None = None) -> Bookmark | None:
    bookmarks = load_bookmarks(path)
    for b in bookmarks:
        if b.id == bookmark_id:
            return b
    return None


def find_by_session_id(session_id: str, path: Path | None = None) -> Bookmark | None:
    bookmarks = load_bookmarks(path)
    for b in bookmarks:
        if b.session_id == session_id:
            return b
    return None


def add_bookmark(bookmark: Bookmark, path: Path | None = None) -> Bookmark:
    bookmarks = load_bookmarks(path)
    for b in bookmarks:
        if b.session_id == bookmark.session_id:
            raise ValueError(f"session already bookmarked: {b.id}")
    if not bookmark.id:
        bookmark.id = generate_id(bookmarks)
    bookmarks.append(bookmark)
    save_bookmarks(bookmarks, path)
    return bookmark


def remove_bookmark(bookmark_id: str, path: Path | None = None) -> bool:
    bookmarks = load_bookmarks(path)
    new_bookmarks = [b for b in bookmarks if b.id != bookmark_id]
    if len(new_bookmarks) == len(bookmarks):
        return False
    save_bookmarks(new_bookmarks, path)
    return True


def update_bookmark(bookmark_id: str, path: Path | None = None, **fields) -> Bookmark | None:
    bookmarks = load_bookmarks(path)
    for b in bookmarks:
        if b.id == bookmark_id:
            for key, value in fields.items():
                if hasattr(b, key) and value is not None:
                    setattr(b, key, value)
            save_bookmarks(bookmarks, path)
            return b
    return None


def list_categories(path: Path | None = None) -> list[str]:
    bookmarks = load_bookmarks(path)
    cats = sorted(set(b.category for b in bookmarks if b.category))
    return cats


def filter_bookmarks(bookmarks: list[Bookmark], query: str) -> list[Bookmark]:
    """Search bookmarks across title, category, session ID, project, first prompt, and profile."""
    q = query.lower()
    return [
        b for b in bookmarks
        if q in b.title.lower()
        or q in b.category.lower()
        or q in b.session_id.lower()
        or q in b.project_path.lower()
        or q in b.first_prompt.lower()
        or (b.aweswitch_profile and q in b.aweswitch_profile.lower())
    ]


def format_bookmark_detail(b: Bookmark, max_first_prompt: int = 0) -> str:
    """Format bookmark details as plain text.

    Args:
        max_first_prompt: Truncate first_prompt to this many chars from each end.
            0 means show full value.
    """
    first_prompt = b.first_prompt or "-"
    if max_first_prompt > 0 and len(first_prompt) > max_first_prompt * 2:
        first_prompt = f"{first_prompt[:max_first_prompt]}...{first_prompt[-max_first_prompt:]}"
    lines = [
        f"ID:               {b.id}",
        f"Title:            {b.title}",
        f"First prompt:     {first_prompt}",
        f"Provider:         {b.provider}",
        f"Session ID:       {b.session_id}",
        f"Category:         {b.category or '-'}",
        f"Project:          {b.project_path or '-'}",
        f"aweswitch Profile: {b.aweswitch_profile or '-'}",
        f"Bookmarked at:    {b.bookmarked_at}",
    ]
    return "\n".join(lines)
