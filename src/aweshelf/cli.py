"""aweshelf CLI entry point."""

import click

from aweshelf import __version__
from aweshelf.commands.bookmark import bookmark_command
from aweshelf.commands.list import list_command, search_command, recent_command
from aweshelf.commands.show import show_command, edit_command, rm_command
from aweshelf.commands.resume import resume_command
from aweshelf.commands.browse import browse_command


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


def main(argv=None):
    return cli.main(args=argv, prog_name="aweshelf")


if __name__ == "__main__":
    raise SystemExit(main())
