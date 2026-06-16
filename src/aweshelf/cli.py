"""aweshelf CLI entry point."""

import shutil
import subprocess
import sys
from pathlib import Path

import click

from aweshelf import __version__
from aweshelf.update_check import check_async, get_pypi_latest, _version_gte
from aweshelf.commands.bookmark import bookmark_command
from aweshelf.commands.list import list_command, search_command, recent_command
from aweshelf.commands.show import show_command, edit_command, rm_command
from aweshelf.commands.resume import resume_command
from aweshelf.commands.browse import browse_command
from aweshelf.commands.sessions import sessions_command


@click.group(
    name="aweshelf",
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Bookmark, categorize, and restore AI coding sessions.",
)
@click.version_option(__version__, "-v", "--version", message="%(version)s")
def cli():
    pass


cli.add_command(bookmark_command)
cli.add_command(list_command)
cli.add_command(search_command)
cli.add_command(recent_command)
cli.add_command(show_command)
cli.add_command(edit_command)
cli.add_command(rm_command)
cli.add_command(resume_command)
cli.add_command(browse_command)
cli.add_command(sessions_command)


@cli.command("self-update")
@click.option("--check", is_flag=True, help="Show versions without updating.")
def self_update_command(check):
    """Update aweshelf to the latest version."""
    try:
        latest = get_pypi_latest()
    except Exception as e:
        raise SystemExit(f"Failed to check PyPI: {e}")
    if _version_gte(__version__, latest):
        click.echo(f"aweshelf is up to date ({__version__}).")
        return
    click.echo(f"Current: {__version__}  Latest: {latest}")
    if check:
        return

    if Path(sys.prefix, "pyvenv.cfg").exists() and "pipx" in sys.prefix:
        cmd = [shutil.which("pipx") or "pipx", "upgrade", "aweshelf"]
    else:
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "aweshelf"]

    click.echo(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode == 0:
        click.echo("Done. Restart aweshelf to use the new version.")
    else:
        raise SystemExit(result.returncode)


def main(argv=None):
    get_reminder = check_async(sys.argv[1:] if argv is None else argv)
    try:
        return cli.main(args=argv, prog_name="aweshelf")
    finally:
        reminder = get_reminder()
        if reminder:
            click.echo(f"⚠  {reminder}", err=True)


if __name__ == "__main__":
    raise SystemExit(main())
