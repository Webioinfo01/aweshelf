"""List, search, recent commands."""

import click

from aweshelf.lib.store import load_bookmarks


def format_table(bookmarks: list) -> str:
    if not bookmarks:
        return "No bookmarks found."

    headers = ["ID", "PROVIDER", "TITLE", "CATEGORY", "PROFILE", "SESSION"]
    rows = []
    for b in bookmarks:
        rows.append([
            b.id,
            b.provider,
            b.title[:40] + ("..." if len(b.title) > 40 else ""),
            b.category or "-",
            b.aweswitch_profile or "-",
            b.session_id,
        ])

    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    lines = []
    header_line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    lines.append(header_line)
    lines.append("  ".join("-" * w for w in widths))
    for row in rows:
        line = "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))
        lines.append(line)

    return "\n".join(lines)


@click.command("list")
@click.option("-c", "--category", default=None, help="Filter by category.")
@click.option("-p", "--provider", default=None, help="Filter by provider.")
@click.option("-s", "--sort", "sort_by", type=click.Choice(["id", "recent"]), default="id",
              help="Sort order (default: id).")
@click.option("-n", "--limit", default=0, type=int, help="Max rows to show (0 = all).")
def list_command(category, provider, sort_by, limit):
    """List all bookmarks."""
    bookmarks = load_bookmarks()
    if category:
        bookmarks = [b for b in bookmarks if b.category == category]
    if provider:
        bookmarks = [b for b in bookmarks if b.provider == provider]
    if sort_by == "recent":
        bookmarks.sort(key=lambda b: b.bookmarked_at, reverse=True)
    if limit > 0:
        bookmarks = bookmarks[:limit]
    click.echo(format_table(bookmarks))


@click.command("search")
@click.argument("query")
def search_command(query):
    """Search bookmarks by title, category, session ID, project, or profile."""
    bookmarks = load_bookmarks()
    query_lower = query.lower()
    results = [
        b for b in bookmarks
        if query_lower in b.title.lower()
        or query_lower in b.category.lower()
        or query_lower in b.session_id.lower()
        or query_lower in b.project_path.lower()
        or (b.aweswitch_profile and query_lower in b.aweswitch_profile.lower())
    ]
    click.echo(format_table(results))


@click.command("recent", hidden=True)
@click.option("-n", "--count", default=10, help="Number of recent bookmarks.")
def recent_command(count):
    """Show recently bookmarked sessions (alias for: list --sort recent -n N)."""
    bookmarks = load_bookmarks()
    bookmarks.sort(key=lambda b: b.bookmarked_at, reverse=True)
    click.echo(format_table(bookmarks[:count]))
