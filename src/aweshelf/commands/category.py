"""Category management commands."""

import json

import click

from aweshelf.lib.category import add_category, list_categories, list_categories_with_bookmarks, remove_category


@click.group("category", help="Manage bookmark categories.")
def category_command():
    pass


@click.command("list")
@click.option(
    "--sessions",
    "-s",
    "show_sessions",
    is_flag=True,
    help="Show sessions under each category.",
)
@click.option("--json", "as_json", is_flag=True, help="Output as raw JSON.")
def category_list_command(as_json: bool, show_sessions: bool) -> None:
    """List existing categories."""
    categories = list_categories()
    if show_sessions:
        _, grouped = list_categories_with_bookmarks()
    else:
        grouped = {}
    if as_json:
        if not show_sessions:
            click.echo(json.dumps(categories, indent=2, ensure_ascii=False))
            return
        payload = []
        for category in categories:
            payload.append(
                {
                    "category": category,
                    "bookmarks": grouped.get(category, []),
                }
            )
        click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    if not categories:
        click.echo("No categories yet.")
        return
    for category in categories:
        click.echo(category)
        if show_sessions:
            if grouped.get(category):
                for bookmark in grouped[category]:
                    click.echo(f"  - {bookmark['id']} | {bookmark['session_id']} | {bookmark['title']}")
            else:
                click.echo("  - (none)")


@click.command("add")
@click.argument("name")
def category_add_command(name: str) -> None:
    """Add a new category."""
    try:
        added = add_category(name)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Added {added}")


@click.command("rm")
@click.argument("name")
@click.option("--force", is_flag=True, help="Also clear the category on existing bookmarks.")
def category_remove_command(name: str, force: bool) -> None:
    """Remove a category."""
    try:
        removed = remove_category(name, clear_bookmarks=force)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    if not removed:
        raise click.ClickException(f"category not found: {name}")
    click.echo(f"Removed {name}")


category_command.add_command(category_list_command)
category_command.add_command(category_add_command)
category_command.add_command(category_remove_command)
