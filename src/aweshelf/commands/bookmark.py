"""Bookmark command."""

import click

from aweshelf.lib.aweswitch import (
    detect_profile,
    load_aweswitch_config,
    profiles_for_provider,
)
from aweshelf.lib.discovery import find_project_sessions, find_recent_session
from aweshelf.lib.session import parse_session_meta
from aweshelf.lib.store import (
    add_bookmark,
    bookmark_path,
    load_bookmarks,
    save_bookmarks,
)
from aweshelf.lib.category import list_categories
from aweshelf.types import Bookmark

DEFAULT_LIST_LIMIT = 10
AWESWITCH_URL = "https://github.com/Webioinfo01/aweswitch"


def _validate_profile(profile: str | None, provider: str, config: dict | None) -> str | None:
    if not profile:
        return None
    if provider != "claude":
        raise click.ClickException("aweswitch profile is currently supported for claude sessions only")
    if not config or profile not in profiles_for_provider(provider, config):
        raise click.ClickException(f"aweswitch profile not found: {profile}")
    return profile


def _prompt_profile(default_profile: str | None, provider: str, config: dict | None) -> str | None:
    if provider != "claude":
        return None
    if not config:
        click.echo(f"aweswitch config not found; profile selection skipped. See {AWESWITCH_URL}")
        return default_profile
    available_profiles = profiles_for_provider("claude", config)
    if not available_profiles:
        click.echo(f"No Claude profiles found in aweswitch config; profile selection skipped. See {AWESWITCH_URL}")
        return default_profile

    if default_profile not in available_profiles:
        default_profile = None
    click.echo(f"Available Claude profiles: {', '.join(available_profiles)}")
    prompt = (
        "Profile (blank keeps default)"
        if default_profile
        else "Profile (blank stores no profile)"
    )
    while True:
        profile_input = click.prompt(prompt, default=default_profile or "", show_default=False)
        if not profile_input:
            return None
        if profile_input in available_profiles:
            return profile_input
        click.echo(f"aweswitch profile not found: {profile_input}")


def _replace_bookmark(bookmark: Bookmark, path) -> Bookmark:
    bookmarks = load_bookmarks(path)
    for index, existing in enumerate(bookmarks):
        if existing.id == bookmark.id:
            bookmarks[index] = bookmark
            save_bookmarks(bookmarks, path)
            return bookmark
    raise ValueError(f"bookmark not found: {bookmark.id}")


def pick_session(
    sessions: list[dict],
    limit: int = DEFAULT_LIST_LIMIT,
    existing_by_session: dict[str, Bookmark] | None = None,
) -> dict:
    """Let user pick a session from a numbered list."""
    existing_by_session = existing_by_session or {}
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
        existing = existing_by_session.get(sid)
        suffix = f"  bookmarked {existing.id}" if existing else ""
        click.echo(f"  {i:>3}. [{provider}] {title}{suffix}")
        click.echo(f"       {sid}")

    if total > limit:
        click.echo(f"\n  ... and {total - limit} more")
    click.echo()

    while True:
        choice = click.prompt("Pick a session (number)", type=int)
        if 1 <= choice <= len(shown):
            return sessions[choice - 1]
        click.echo(f"Please enter 1-{len(shown)}")


def _confirm_current_session(session: dict) -> None:
    click.echo("Current session candidate:")
    click.echo(f"  [{session.get('provider', '?')}] {session.get('title', 'Untitled')}")
    click.echo(f"  {session.get('session_id', '?')}")
    project_path = session.get("project_path", "")
    if project_path:
        click.echo(f"  {project_path}")
    if not click.confirm("Bookmark this session?", default=True):
        click.echo("Bookmark unchanged.")
        raise SystemExit(0)


def run_bookmark(
    session_id: str | None = None,
    title: str | None = None,
    category: str | None = None,
    profile: str | None = None,
    interactive: bool = True,
    verbose: bool = False,
    current: bool = False,
) -> Bookmark:
    if current and session_id is not None:
        raise click.ClickException("--current cannot be used with SESSION_ID")

    path = bookmark_path()
    picked_interactively = session_id is None and interactive and not current
    prompts_from_discovered_session = picked_interactively or (current and interactive)
    existing_bookmark = None
    existing_by_session = {b.session_id: b for b in load_bookmarks(path)}

    if picked_interactively:
        sessions = find_project_sessions()
        if not sessions:
            raise SystemExit("aweshelf: no session found in current project")
        limit = len(sessions) if verbose else DEFAULT_LIST_LIMIT
        session = pick_session(sessions, limit, existing_by_session)
        session_id = session["session_id"]
        existing_bookmark = existing_by_session.get(session_id)
        if existing_bookmark and not click.confirm(
            f"Session already bookmarked as {existing_bookmark.id}. Update it?",
            default=False,
        ):
            click.echo("Bookmark unchanged.")
            raise SystemExit(0)
        source_path = session.get("source_path", "")
        provider = session.get("provider", "claude")
        auto_title = session.get("title", "")
        first_prompt = session.get("first_prompt", "")
        project_path = session.get("project_path", "")
    elif current:
        session = find_recent_session()
        if session is None:
            raise SystemExit("aweshelf: no session found in current project")
        _confirm_current_session(session)
        session_id = session["session_id"]
        existing_bookmark = existing_by_session.get(session_id)
        if existing_bookmark and not click.confirm(
            f"Session already bookmarked as {existing_bookmark.id}. Update it?",
            default=False,
        ):
            click.echo("Bookmark unchanged.")
            raise SystemExit(0)
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
        title = (
            existing_bookmark.title
            if existing_bookmark
            else auto_title or first_prompt[:80] or "Untitled session"
        )
        if prompts_from_discovered_session:
            title = click.prompt("Title (blank keeps current/default title)", default=title, show_default=False)

    if interactive and category is None:
        cats = list_categories(path)
        click.echo()
        if cats:
            click.echo(f"Existing categories: {', '.join(cats)}")
        category_default = existing_bookmark.category if existing_bookmark else ""
        cat_input = click.prompt("Category", default=category_default, show_default=False)
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

    if prompts_from_discovered_session:
        if existing_bookmark and profile is None:
            profile = existing_bookmark.aweswitch_profile
        profile = _prompt_profile(profile, provider, config)
    else:
        profile = _validate_profile(profile, provider, config)

    bookmark = Bookmark(
        id=existing_bookmark.id if existing_bookmark else "",
        provider=provider,
        session_id=session_id,
        title=title,
        category=category,
        project_path=project_path,
        first_prompt=first_prompt,
        aweswitch_profile=profile,
    )

    if existing_bookmark:
        bookmark = _replace_bookmark(bookmark, path)
        bookmark._aweshelf_status = "updated"
        return bookmark

    bookmark = add_bookmark(bookmark, path)
    bookmark._aweshelf_status = "bookmarked"
    return bookmark


@click.command("bookmark")
@click.argument("session_id", required=False)
@click.option("-t", "--title", default=None, help="Bookmark title.")
@click.option("-c", "--category", default=None, help="Category for the bookmark.")
@click.option("--profile", default=None, help="aweswitch profile to use.")
@click.option("--current", is_flag=True, help="Bookmark the most recent session in this project.")
@click.option("--verbose", is_flag=True, help="Show all sessions (no limit).")
def bookmark_command(session_id, title, category, profile, current, verbose):
    """Bookmark a session for quick access."""
    try:
        b = run_bookmark(
            session_id,
            title,
            category,
            profile,
            interactive=True,
            verbose=verbose,
            current=current,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    status = getattr(b, "_aweshelf_status", "bookmarked")
    verb = "Updated" if status == "updated" else "Bookmarked"
    click.echo(f"\n{verb} {b.id} — {b.title}")
