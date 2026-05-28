"""Bookmark command."""

import click

from aweshelf.lib.aweswitch import detect_profile, load_aweswitch_config, profile_exists
from aweshelf.lib.discovery import find_project_sessions, find_recent_session
from aweshelf.lib.session import parse_session_meta
from aweshelf.lib.store import add_bookmark, bookmark_path, list_categories
from aweshelf.types import Bookmark

DEFAULT_LIST_LIMIT = 10


def _validate_profile(profile: str | None, config: dict | None) -> str | None:
    if not profile:
        return None
    if not config or not profile_exists(profile, config):
        raise click.ClickException(f"aweswitch profile not found: {profile}")
    return profile


def _prompt_profile(default_profile: str | None, config: dict | None) -> str | None:
    while True:
        profile_input = click.prompt("Profile", default=default_profile or "", show_default=False)
        if not profile_input:
            return None
        if config and profile_exists(profile_input, config):
            return profile_input
        click.echo(f"aweswitch profile not found: {profile_input}")


def pick_session(sessions: list[dict], limit: int = DEFAULT_LIST_LIMIT) -> dict:
    """Let user pick a session from a numbered list."""
    shown = sessions[:limit]
    total = len(sessions)

    if total > limit:
        click.echo(f"Sessions in current project ({total} total, showing {limit} \u2014 use --verbose for all):\n")
    else:
        click.echo(f"Sessions in current project ({total} total):\n")

    for i, s in enumerate(shown, 1):
        title = s.get("title", "Untitled")
        provider = s.get("provider", "?")
        sid = s.get("session_id", "?")
        click.echo(f"  {i:>3}. [{provider}] {title}")
        click.echo(f"       {sid}")

    if total > limit:
        click.echo(f"\n  ... and {total - limit} more")
    click.echo()

    while True:
        choice = click.prompt("Pick a session (number)", type=int)
        if 1 <= choice <= len(shown):
            return sessions[choice - 1]
        click.echo(f"Please enter 1-{len(shown)}")


def run_bookmark(
    session_id: str | None = None,
    title: str | None = None,
    category: str | None = None,
    profile: str | None = None,
    interactive: bool = True,
    verbose: bool = False,
) -> Bookmark:
    path = bookmark_path()
    picked_interactively = session_id is None and interactive

    if picked_interactively:
        sessions = find_project_sessions()
        if not sessions:
            raise SystemExit("aweshelf: no session found in current project")
        limit = len(sessions) if verbose else DEFAULT_LIST_LIMIT
        session = pick_session(sessions, limit)
        session_id = session["session_id"]
        source_path = session.get("source_path", "")
        provider = session.get("provider", "claude")
        auto_title = session.get("title", "")
        first_prompt = session.get("first_prompt", "")
        project_path = session.get("project_path", "")
    elif session_id is None:
        session = find_recent_session()
        if session is None:
            raise SystemExit("aweshelf: no session found in current project")
        session_id = session["session_id"]
        source_path = session.get("source_path", "")
        provider = session.get("provider", "claude")
        auto_title = session.get("title", "")
        first_prompt = session.get("first_prompt", "")
        project_path = session.get("project_path", "")
    else:
        source_path = ""
        provider = "claude"
        auto_title = ""
        first_prompt = ""
        project_path = ""

    if title is None:
        title = auto_title or first_prompt[:80] or "Untitled session"
        if picked_interactively:
            title = click.prompt("Title", default=title, show_default=False)

    if interactive and category is None:
        cats = list_categories(path)
        click.echo()
        if cats:
            click.echo(f"Existing categories: {', '.join(cats)}")
        cat_input = click.prompt("Category", default="", show_default=False)
        category = cat_input if cat_input else ""

    if category is None:
        category = ""

    config = load_aweswitch_config()

    if profile is None and source_path:
        try:
            meta = parse_session_meta(source_path)
            if config:
                profile = detect_profile({"ANTHROPIC_BASE_URL": "", "ANTHROPIC_MODEL": meta.get("model", "")})
        except Exception:
            pass

    if picked_interactively:
        profile = _prompt_profile(profile, config)
    else:
        profile = _validate_profile(profile, config)

    bookmark = Bookmark(
        id="",
        provider=provider,
        session_id=session_id,
        title=title,
        category=category,
        project_path=project_path,
        first_prompt=first_prompt,
        aweswitch_profile=profile,
    )

    bookmark = add_bookmark(bookmark, path)
    return bookmark


@click.command("bookmark")
@click.argument("session_id", required=False)
@click.option("-t", "--title", default=None, help="Bookmark title.")
@click.option("-c", "--category", default=None, help="Category for the bookmark.")
@click.option("--profile", default=None, help="aweswitch profile to use.")
@click.option("--verbose", is_flag=True, help="Show all sessions (no limit).")
def bookmark_command(session_id, title, category, profile, verbose):
    """Bookmark a session for quick access."""
    try:
        b = run_bookmark(session_id, title, category, profile, interactive=True, verbose=verbose)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"\nBookmarked {b.id} — {b.title}")
