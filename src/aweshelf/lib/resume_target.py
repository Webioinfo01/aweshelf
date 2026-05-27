"""Shared resume target construction and execution."""

import os
import shlex
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import click

from aweshelf.lib.aweswitch import build_resume_command, profile_exists as default_profile_exists
from aweshelf.types import Bookmark


@dataclass
class ResumeTarget:
    argv: list[str]
    cwd: Path | None = None
    warning: str | None = None


class ResumeError(ValueError):
    pass


def build_resume_target(
    bookmark: Bookmark,
    profile_override: str | None = None,
    raw: bool = False,
    profile_exists: Callable[[str], bool] = default_profile_exists,
) -> ResumeTarget:
    use_profile = profile_override or bookmark.aweswitch_profile
    warning = None
    if use_profile and not raw and not profile_exists(use_profile):
        if profile_override:
            raise ResumeError(
                f"aweswitch profile '{use_profile}' not found. Use --raw to skip aweswitch."
            )
        warning = f"aweswitch profile '{use_profile}' not found; falling back to raw resume."
        use_profile = None
        raw = True

    cwd = _valid_project_path(bookmark.project_path)
    argv = build_resume_command(bookmark.provider, use_profile, bookmark.session_id, raw=raw)
    return ResumeTarget(argv=argv, cwd=cwd, warning=warning)


def format_resume_target(target: ResumeTarget) -> str:
    command = " ".join(shlex.quote(part) for part in target.argv)
    if target.cwd is None:
        return command
    return f"cd {shlex.quote(str(target.cwd))} && {command}"


def run_resume_target(target: ResumeTarget) -> None:
    original_cwd = os.getcwd()
    try:
        if target.cwd is not None:
            os.chdir(target.cwd)
        os.execvpe(target.argv[0], target.argv, os.environ)
    except Exception:
        os.chdir(original_cwd)
        raise


def execute_resume(bookmark: Bookmark, profile_override: str | None = None, raw: bool = False) -> None:
    """Build and run a resume target with click-friendly error handling."""
    target = build_resume_target(bookmark, profile_override=profile_override, raw=raw)
    if target.warning:
        click.echo(f"Warning: {target.warning}", err=True)
    click.echo(f"Resuming {bookmark.id} — {bookmark.title}")
    click.echo(f"  $ {format_resume_target(target)}")
    try:
        run_resume_target(target)
    except FileNotFoundError as exc:
        raise click.ClickException(f"command not found: {target.argv[0]}") from exc
    except OSError as exc:
        raise click.ClickException(f"failed to run {target.argv[0]}: {exc}") from exc


def _valid_project_path(project_path: str) -> Path | None:
    if not project_path:
        return None
    path = Path(project_path).expanduser()
    if path.exists() and path.is_dir():
        return path
    return None
