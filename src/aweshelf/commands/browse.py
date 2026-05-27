"""Browse command — TUI entry point."""

import click

from aweshelf.lib.resume_target import execute_resume


@click.command("browse")
def browse_command():
    """Browse bookmarks interactively."""
    try:
        from aweshelf.tui.app import BookmarkBrowser
    except ImportError as exc:
        raise click.ClickException("textual is required for browse. Install with: pip install textual") from exc

    app = BookmarkBrowser()
    result = app.run()

    if result is not None:
        execute_resume(result)
