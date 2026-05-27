"""Resume command."""

import click

from aweshelf.lib.resume_target import (
    ResumeError,
    build_resume_target,
    format_resume_target,
    run_resume_target,
)
from aweshelf.lib.store import find_bookmark


@click.command("resume")
@click.argument("bookmark_id")
@click.option("--profile", default=None, help="Override aweswitch profile.")
@click.option("--raw", is_flag=True, help="Skip aweswitch, use claude/codex directly.")
@click.option("--dry-run", is_flag=True, help="Print the resume command without running it.")
def resume_command(bookmark_id, profile, raw, dry_run):
    """Resume a bookmarked session."""
    b = find_bookmark(bookmark_id)
    if b is None:
        raise click.ClickException(f"bookmark not found: {bookmark_id}")

    try:
        target = build_resume_target(b, profile_override=profile, raw=raw)
    except ResumeError as exc:
        raise click.ClickException(str(exc)) from exc
    if target.warning:
        click.echo(f"Warning: {target.warning}", err=True)
    click.echo(f"Resuming {b.id} — {b.title}")
    click.echo(f"  $ {format_resume_target(target)}")

    if dry_run:
        return

    try:
        run_resume_target(target)
    except FileNotFoundError as exc:
        raise click.ClickException(f"command not found: {target.argv[0]}") from exc
    except OSError as exc:
        raise click.ClickException(f"failed to run {target.argv[0]}: {exc}") from exc
