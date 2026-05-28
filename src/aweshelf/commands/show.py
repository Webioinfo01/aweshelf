"""Show, edit, rm commands."""

import json

import click

from aweshelf.lib.store import find_bookmark, find_by_session_id, update_bookmark, remove_bookmark


def _resolve_bookmark(identifier: str):
    """Resolve a bookmark by ID first, then by session ID."""
    b = find_bookmark(identifier)
    if b is not None:
        return b
    return find_by_session_id(identifier)


@click.command("show")
@click.argument("bookmark_id")
@click.option("--json", "as_json", is_flag=True, help="Output as raw JSON.")
def show_command(bookmark_id, as_json):
    """Show bookmark details (accepts bookmark ID or session ID)."""
    b = _resolve_bookmark(bookmark_id)
    if b is None:
        raise click.ClickException(f"bookmark not found: {bookmark_id}")
    if as_json:
        click.echo(json.dumps(b.to_dict(), indent=2, ensure_ascii=False))
    else:
        click.echo(f"ID:               {b.id}")
        click.echo(f"Provider:         {b.provider}")
        click.echo(f"Session ID:       {b.session_id}")
        click.echo(f"Title:            {b.title}")
        click.echo(f"Category:         {b.category or '-'}")
        click.echo(f"Project:          {b.project_path or '-'}")
        click.echo(f"aweswitch Profile: {b.aweswitch_profile or '-'}")
        click.echo(f"Bookmarked at:    {b.bookmarked_at}")


@click.command("edit")
@click.argument("bookmark_id")
@click.option("-t", "--title", default=None, help="New title.")
@click.option("-c", "--category", default=None, help="New category.")
@click.option("--profile", default=None, help="New aweswitch profile.")
def edit_command(bookmark_id, title, category, profile):
    """Edit a bookmark's metadata."""
    fields = {}
    if title is not None:
        fields["title"] = title
    if category is not None:
        fields["category"] = category
    if profile is not None:
        fields["aweswitch_profile"] = profile

    if not fields:
        raise click.ClickException("nothing to edit; use -t, -c, or --profile")

    b = update_bookmark(bookmark_id, **fields)
    if b is None:
        raise click.ClickException(f"bookmark not found: {bookmark_id}")
    click.echo(f"Updated {b.id}")


@click.command("rm")
@click.argument("bookmark_id")
@click.option("--force", is_flag=True, help="Skip confirmation.")
def rm_command(bookmark_id, force):
    """Remove a bookmark."""
    b = find_bookmark(bookmark_id)
    if b is None:
        raise click.ClickException(f"bookmark not found: {bookmark_id}")

    if not force:
        click.confirm(f"Remove bookmark {b.id} ({b.title})?", abort=True)

    remove_bookmark(bookmark_id)
    click.echo(f"Removed {bookmark_id}")
