---
name: aweshelf
description: "Use when working with aweshelf CLI — session bookmarking, categorization, search, and resume for Claude Code and Codex sessions. 中文触发词：书签、收藏会话、恢复会话、aweshelf、session管理、browse。"
---

# Aweshelf

Use `aweshelf` CLI directly. Do not add wrapper scripts unless the CLI is missing a needed capability.

## Intent Router

Match the user's intent to a task domain, then follow the workflow below.

| User intent | Domain | First command |
|---|---|---|
| "Bookmark this session", "save current session" | Bookmark | `aweshelf bookmark --current` |
| "Bookmark a session", "pick a session to save" | Bookmark | `aweshelf bookmark` (interactive picker) |
| "List my bookmarks", "show saved sessions" | Browse | `aweshelf list` |
| "Find bookmarks about X" | Search | `aweshelf search QUERY` |
| "Resume bookmark X", "continue session X" | Resume | `aweshelf resume BOOKMARK_ID` |
| "Show details of bookmark X" | Show | `aweshelf show BOOKMARK_ID` |
| "Edit bookmark X", "rename bookmark", "change category" | Edit | `aweshelf edit BOOKMARK_ID` |
| "Delete bookmark X", "remove bookmark" | Remove | `aweshelf rm BOOKMARK_ID` |
| "Open the TUI", "browse interactively" | TUI | `aweshelf browse` |
| "Recent sessions", "what did I work on recently" | Recent | `aweshelf recent` |

## First-Time Setup

1. Install: `pip install aweshelf`
2. Verify: `aweshelf -v`

No config file is needed to start. Bookmarks are stored at `~/.config/aweshelf/bookmarks.json` automatically.

For aweswitch profile integration (auto-detecting API endpoint/model), install [aweswitch](https://github.com/Webioinfo01/aweswitch) separately.

## Core Rules

1. `aweshelf bookmark` without arguments opens an interactive session picker in the current project. Use `--current` to skip the picker and bookmark the most recent session directly.
2. Use `--no-interactive` to skip all prompts — for agents and scripting. Bookmarks are created with defaults or passed values only.
3. If a session is already bookmarked, `bookmark` will offer to update it instead of creating a duplicate.
4. `aweshelf resume BOOKMARK_ID` restores the session with the aweswitch profile that was active at bookmark time. Use `--profile` to override, `--raw` to skip aweswitch entirely.
5. `aweshelf browse` opens a TUI. This is a terminal UI — it requires a real terminal, not a piped subprocess. Do not run it inside non-interactive contexts.
6. `aweshelf list` and `aweshelf search` are safe for scripting. They output plain text and can be piped.
7. Use `--json` with `show` to get machine-readable output.

## Workflows

### Bookmark a Session

```bash
# Interactive: pick from sessions in current project
aweshelf bookmark

# Quick: bookmark the most recent session (skip picker)
aweshelf bookmark --current

# Quick with metadata
aweshelf bookmark --current -t "Fix auth bug" -c backend

# Bookmark a specific session by ID
aweshelf bookmark 550e8400-... -t "Refactor API" -c backend

# Specify aweswitch profile
aweshelf bookmark --current --profile cc-glm

# Non-interactive: for agents and scripting (zero prompts)
aweshelf bookmark <SESSION_ID> -t "title" --no-interactive
aweshelf bookmark --current --no-interactive
```

Decision order:
1. `--current` is fastest — one confirmation, done.
2. Without arguments — interactive picker shows sessions in the current project directory.
3. With `SESSION_ID` — bookmark a specific session directly (no picker). Prompts for title/category/profile unless `--no-interactive` is set.
4. Always use `--no-interactive` in agent/script context to avoid blocking on prompts.

### List and Search

```bash
# List all bookmarks
aweshelf list

# Filter by category
aweshelf list -c backend

# Filter by provider
aweshelf list -p claude

# Search across all fields
aweshelf search "auth middleware"

# Show recent sessions (not necessarily bookmarked)
aweshelf recent
aweshelf recent -n 20
```

### Show and Edit

```bash
# Show bookmark details
aweshelf show aweshelf_0001

# Show as JSON (for scripting)
aweshelf show aweshelf_0001 --json

# Edit title
aweshelf edit aweshelf_0001 -t "New title"

# Edit category
aweshelf edit aweshelf_0001 -c frontend

# Edit aweswitch profile
aweshelf edit aweshelf_0001 --profile cc-deepseek

# Combine
aweshelf edit aweshelf_0001 -t "New title" -c frontend --profile cc-glm
```

### Resume a Session

```bash
# Resume with stored profile
aweshelf resume aweshelf_0001

# Resume with a different profile
aweshelf resume aweshelf_0001 --profile cc-glm

# Resume without aweswitch (use claude/codex directly)
aweshelf resume aweshelf_0001 --raw

# Preview the command without running
aweshelf resume aweshelf_0001 --dry-run
```

Decision order:
1. Default resume uses the aweswitch profile stored in the bookmark.
2. `--profile` overrides the stored profile (useful when switching providers).
3. `--raw` skips aweswitch entirely — runs `claude` or `codex` directly.
4. `--dry-run` shows what would happen without executing.

### Remove a Bookmark

```bash
# Remove with confirmation prompt
aweshelf rm aweshelf_0001

# Remove without confirmation
aweshelf rm aweshelf_0001 --force
```

### Browse (TUI)

```bash
aweshelf browse
```

Keyboard shortcuts:
- `Enter` — Resume selected session (with confirmation)
- `e` — Inline-edit current cell (title, category, profile)
- `r` — Remove selected bookmark (with confirmation)
- `y` / `n` — Confirm / cancel action
- `c` — Toggle between Category-grouped and All view
- `s` — Cycle sort order
- `/` — Filter bookmarks
- `Esc` — Clear filter / cancel
- `?` — Show all shortcuts
- `q` — Quit

## Bookmark Data Reference

```json
{
  "id": "aweshelf_0001",
  "provider": "claude",
  "session_id": "550e8400-...",
  "title": "Fix auth middleware bug",
  "category": "backend",
  "project_path": "/Users/peng/Desktop/Project/my-app",
  "first_prompt": "Help me fix the auth middleware...",
  "aweswitch_profile": "cc-glm",
  "bookmarked_at": "2026-05-20T14:00:00Z"
}
```

Key fields:
- **id**: Auto-generated sequential ID (`aweshelf_NNNN`).
- **provider**: `claude` or `codex`.
- **session_id**: Original session UUID.
- **aweswitch_profile**: The aweswitch profile active when bookmarked. Used by `resume` to restore the same API endpoint/model. `null` if aweswitch is not configured.
- **project_path**: The project directory the session was in. Used to filter sessions in the interactive picker.
