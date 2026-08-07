"""Resume command."""

import json

import click

from aweshelf.lib.resume_target import (
    ResumeError,
    build_resume_target,
    echo_resume_plan,
    execute_resume,
    format_resume_target,
)
from aweshelf.lib.store import find_bookmark


@click.command("resume")
@click.argument("bookmark_id")
@click.option("--profile", default=None, help="Override aweswitch profile.")
@click.option("--raw", is_flag=True, help="Skip aweswitch, use claude/codex directly.")
@click.option("--dry-run", is_flag=True, help="Print the resume command without running it.")
@click.option("--json", "as_json", is_flag=True, help="Output dry-run target as raw JSON.")
def resume_command(bookmark_id, profile, raw, dry_run, as_json):
    """Resume a bookmarked session."""
    b = find_bookmark(bookmark_id)
    if b is None:
        raise click.ClickException(f"bookmark not found: {bookmark_id}")

    try:
        target = build_resume_target(b, profile_override=profile, raw=raw)
    except ResumeError as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        click.echo(json.dumps({
            "bookmark_id": b.id,
            "title": b.title,
            "argv": target.argv,
            "cwd": str(target.cwd) if target.cwd is not None else None,
            "command": format_resume_target(target),
            "warning": target.warning,
        }, indent=2, ensure_ascii=False))
        return

    if dry_run:
        echo_resume_plan(b, target)
        return

    execute_resume(b, target=target)
