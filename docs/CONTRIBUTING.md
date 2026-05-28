# Contributing

## Development Setup

```bash
cd aweshelf
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Running Tests

```bash
python -m unittest discover -s tests -v
```

## Architecture

```
src/aweshelf/
  __init__.py          # Version
  types.py             # Bookmark dataclass
  cli.py               # Click entry point
  commands/            # One file per command, thin orchestrators
    bookmark.py        # Bookmark current or specified session
    browse.py          # Interactive TUI launcher
    list.py            # List bookmarks with optional filters
    recent.py          # Show recent sessions
    resume.py          # Resume a bookmarked session
    search.py          # Search bookmarks by keyword
    show.py            # Show bookmark details
  lib/                 # Pure business logic, no CLI coupling
    aweswitch.py       # aweswitch config parsing and profile detection
    discovery.py       # Session file discovery for Claude Code and Codex
    resume_target.py   # Resume target construction and execution
    session.py         # Session JSONL metadata extraction
    store.py           # JSON file CRUD for bookmarks
    resume.py          # Backwards-compatible shim → resume_target
  tui/                 # textual app (reads from lib/store, does not write)
```

- `lib/` has no CLI coupling — pure functions, testable in isolation
- `commands/` are thin orchestrators calling `lib/` functions
- `tui/` reads from `lib/store`, does not write

## Code Style

- Python 3.10+, type hints throughout
- `click` for CLI, `textual` for TUI
- `unittest` for tests, real temp directories (no filesystem mocking)
- Functions: `snake_case`, Types: `PascalCase`, Constants: `UPPER_CASE`
- Error messages are user-facing and actionable

## Release Workflow

1. Update `__version__` in `src/aweshelf/__init__.py`
2. Update version in `pyproject.toml`
3. Update `docs/CHANGELOG.md` with release notes
4. Update version badges in `README.md` and `README_cn.md`
5. Commit: `git commit -m "release: vX.Y.Z"`
6. Tag: `git tag vX.Y.Z`
7. Push: `git push && git push --tags`
8. GitHub Actions `release.yml` creates the GitHub Release automatically
