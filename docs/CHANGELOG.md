# Changelog

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
