# Changelog

## v0.1.7

Better list output and category-as-view model.

Inspired by [PR #2](https://github.com/Webioinfo01/aweshelf/pull/2) (category management), this release takes a simpler approach: categories are derived from bookmarks, not managed as independent entities. Instead of `category add/list/rm` commands, `aweshelf list --by category` provides the same visibility with zero state to maintain.

### Highlights

- `aweshelf list --by category|provider|profile` — group and count bookmarks by any dimension
- `aweshelf sessions` removes redundant PROJECT column (filtered by current project already)
- `aweshelf sessions -n` help now shows default value (20); output hints when truncated
- `aweshelf list` adds PROJECT column to distinguish cross-project bookmarks

## v0.1.6

Docs refresh and version sync.

### Highlights

- Sync Chinese README with English version
- Update VS Code extension references to aweshelf-extension
- Add new blog post: "Bookmark Your AI Coding Sessions"
- Update media page with aweskill and aweswitch pairing
- Fix `__init__.py` version mismatch (was stuck at 0.1.3)

## v0.1.5

VS Code extension support, search enhancements, and new sessions command.

### Highlights

- VS Code extension now available at [mugpeng/aweshelf-extension](https://github.com/mugpeng/aweshelf-extension) — browse, search, bookmark, and resume sessions directly from VS Code
- Search command gains `--category`, `--provider`, and `--sort` options for server-side filtering and sorting
- New `sessions` command for listing discovered sessions
- Resume command improvements
- Add LICENSE (MPL-2.0)
- Engineering Taste section added to CONTRIBUTING.md

## v0.1.4

Code dedup, AI agent docs, and README restructure.

### Highlights

- Refactor: extract `filter_bookmarks` and `format_bookmark_detail` to `lib/store.py` — deduplicate search and display logic from list, show, and TUI browse
- New `README.ai.md` — dedicated install and usage guide for AI coding agents
- New `resources/skills/aweshelf/SKILL.md` — aweskill skill definition
- README restructure: add AI/human usage sections, aweskill badge, Supported by section
- Add aweswitch to Install and Supported by sections
- Update CONTRIBUTING.md with missing command files
- Add example screenshots in `resources/image/`

## v0.1.3

CLI polish, improved bookmarking flow, and browse TUI refinements.

### Highlights

- Bookmark: auto-detect current session when no session ID is given
- Bookmark: interactive aweswitch profile selection with validation
- Browse: show `Del` shortcut for clearing edited cells
- Browse: refine edit and confirm prompt text for clarity
- CLI: remove redundant `help` command — use `-h`/`--help` instead
- CLI: `list` gains `--sort id|recent` and `-n/--limit` flags; `recent` becomes hidden alias
- CLI: `show` now accepts both bookmark ID and session ID
- Docs: add TUI shortcut reference and CLI options to README

## v0.1.2

Browse mode overhaul — inline editing, mode-based UI, and quality-of-life improvements.

### Highlights

- Browse: inline cell editing with `[e]` key — edit title, category, URL, and notes directly in the TUI
- Browse: replace separate EditScreen/ConfirmScreen with mode-based inline editing for a more cohesive UX
- Browse: category toggle shortcut changed from `m` to `c` for clarity
- Browse: align browse and list column layout for consistency
- Browse: add edit and remove bookmarks in browse mode
- Browse: add category mode toggle and sort cycle (`s` key)
- First session prompt is now persisted to avoid repeated prompts
- Fix: remove `$` prefix from category color names for Python API compatibility
- Fix: stabilize browse selection actions
- Docs: add logo and PyPI downloads badge

## v0.1.1

Bug fixes, TUI search, and test coverage improvements.

### Highlights

- Fix: bookmark_command now catches duplicate session errors gracefully instead of showing a traceback
- Fix: all exception handlers use `raise ... from exc` for proper exception chains
- Search command now matches across title, category, session_id, project_path, and profile
- TUI browse: add `/` to filter bookmarks and `Esc` to clear filter
- TUI browse: draggable sidebar resize with `[`/`]` keys and mouse drag
- Add `test_discovery.py` covering session discovery module (9 tests)
- Add bookmark command and search integration tests (6 tests)
- Replace `Optional[X]` with `X | None` across all modules (Python 3.10+)
- Add ruff linter config and pytest config to pyproject.toml

## v0.1.0

Initial release — bookmark, categorize, and restore AI coding sessions.

### Highlights

- Bookmark Claude Code and Codex sessions with title and category
- Auto-detect aweswitch profiles at bookmark time
- Resume sessions with aweswitch profile restoration
- Interactive TUI browser with textual
- CLI commands: bookmark, list, search, recent, show, edit, rm, resume, browse
- Sequential bookmark IDs (`aweshelf_0001`)
- Atomic bookmark writes with `0o600` permissions
- Deduplicated session parser (`_parse_jsonl` + provider-specific field extractors)
- Deduplicated discovery logic (`_filter_project_sessions`, `_sort_by_mtime`)
- Shared resume execution helper (`execute_resume`) for CLI and TUI
- Backwards-compatible `lib/resume.py` shim after rename to `lib/resume_target.py`
