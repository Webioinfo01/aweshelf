"""Category-related operations for bookmark store."""

from pathlib import Path

from aweshelf.lib.store import load_bookmarks, load_store, save_bookmarks


def _normalize_category(category: str | None) -> str:
    return (category or "").strip()


def list_categories(path: Path | None = None) -> list[str]:
    """List all known categories, combining explicit categories and bookmark values."""
    bookmarks, categories = load_store(path)
    categories_set = set(categories)
    categories_set.update(b.category for b in bookmarks if b.category)
    return sorted(categories_set)


def add_category(category: str, path: Path | None = None) -> str:
    """Add a category and persist it."""
    category = _normalize_category(category)
    if not category:
        raise ValueError("category cannot be empty")

    _, categories = load_store(path)
    if category in categories:
        return category

    bookmarks = load_bookmarks(path)
    categories = categories + [category]
    save_bookmarks(bookmarks, path, categories)
    return category


def remove_category(
    category: str,
    path: Path | None = None,
    *,
    clear_bookmarks: bool = False,
) -> bool:
    """Remove a category. Return True if store changed."""
    category = _normalize_category(category)
    if not category:
        raise ValueError("category cannot be empty")

    bookmarks = load_bookmarks(path)
    _, categories = load_store(path)
    used = [b for b in bookmarks if b.category == category]
    if used and not clear_bookmarks:
        raise ValueError(
            f"category '{category}' is in use by {len(used)} bookmark(s); use --force to remove it"
        )

    changed = False
    if category in categories:
        categories = [item for item in categories if item != category]
        changed = True

    if clear_bookmarks and used:
        for bookmark in used:
            bookmark.category = ""
        changed = True

    if not changed:
        changed = bool(used and clear_bookmarks)

    if changed:
        save_bookmarks(bookmarks, path, categories)
        return True

    return False


def list_categories_with_bookmarks(path: Path | None = None) -> tuple[list[str], dict[str, list[dict]]]:
    """Return categories and a mapping of category to bookmark summaries."""
    categories = list_categories(path)
    grouped: dict[str, list[dict]] = {category: [] for category in categories}
    for bookmark in load_bookmarks(path):
        if bookmark.category in grouped:
            grouped[bookmark.category].append(
                {
                    "id": bookmark.id,
                    "session_id": bookmark.session_id,
                    "title": bookmark.title,
                }
            )
    for category in grouped:
        grouped[category].sort(key=lambda b: (b["session_id"], b["id"]))
    return categories, grouped
