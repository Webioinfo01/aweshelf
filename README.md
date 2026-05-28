<div align="center">
  <img src="logo/aweshelf.png" alt="aweshelf" width="860">
  <h1>aweshelf: Session Bookmark Manager</h1>
  <p><strong>Bookmark, categorize, and restore AI coding sessions with aweswitch profiles.</strong></p>
  <p>A lightweight CLI-first tool for Claude Code and Codex session management.</p>
  <p>
    <strong>English</strong> ·
    <a href="./README_cn.md">简体中文</a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/version-0.1.2-7C3AED?style=flat-square" alt="Version">
    <img src="https://img.shields.io/badge/python-%E2%89%A53.10-0EA5E9?style=flat-square" alt="Python">
  </p>
  <p>
    <img src="https://img.shields.io/badge/status-alpha-c96a3d?style=flat-square" alt="Status">
    <img src="https://img.shields.io/badge/install-pip-22C55E?style=flat-square" alt="pip install">
    <img src="https://img.shields.io/badge/platform-terminal-334155?style=flat-square" alt="Platform">
    <img src="https://img.shields.io/pepy/dt/aweshelf?style=flat-square" alt="PyPI downloads">
    <img src="https://img.shields.io/github/stars/Webioinfo01/aweshelf?style=flat-square" alt="GitHub stars">
  </p>
</div>

> Bookmark, categorize, and restore AI coding sessions with aweswitch profiles.

aweshelf lets you save your favorite Claude Code and Codex sessions, tag them with categories, and restore them instantly — including the aweswitch profile (API endpoint, model, token) that was active when you bookmarked.

## Install

```bash
pip install aweshelf
```

## Quick Start

```bash
# Bookmark the current project's most recent session
aweshelf bookmark

# List all bookmarks
aweshelf list

# Resume a bookmark
aweshelf resume aweshelf_0001

# Browse interactively
aweshelf browse
```

## Config

Bookmarks are stored at `~/.config/aweshelf/bookmarks.json`. Override with `AWESHELF_CONFIG` env var.

```json
{
  "version": 1,
  "bookmarks": [
    {
      "id": "aweshelf_0001",
      "provider": "claude",
      "session_id": "550e8400-...",
      "title": "Fix auth middleware bug",
      "category": "backend",
      "project_path": "/Users/peng/Desktop/Project/my-app",
      "aweswitch_profile": "cc-glm",
      "bookmarked_at": "2026-05-20T14:00:00Z"
    }
  ]
}
```

## Commands

```bash
aweshelf bookmark [SESSION_ID] [-t TITLE] [-c CATEGORY] [--profile PROFILE] [--verbose]
aweshelf list [-c CATEGORY] [-p PROVIDER]
aweshelf search QUERY              # search title, category, session, project, prompt, profile
aweshelf recent [-n COUNT]
aweshelf show BOOKMARK_ID [--json]
aweshelf edit BOOKMARK_ID [-t TITLE] [-c CATEGORY] [--profile PROFILE]
aweshelf rm BOOKMARK_ID [--force]
aweshelf resume BOOKMARK_ID [--profile PROFILE] [--raw] [--dry-run]
aweshelf browse
aweshelf help [COMMAND]
```

## Browse (TUI)

`aweshelf browse` opens an interactive TUI with a sidebar table and detail pane.
`aweshelf bookmark` prompts for title, category, and aweswitch profile when picking a session interactively. Profiles must exist in aweswitch config.

| Key | Action |
|-----|--------|
| `Enter` | Resume selected session (with confirmation) |
| `e` | Inline-edit the current cell (title, category, profile) |
| `r` | Remove selected bookmark (with confirmation) |
| `y` / `n` | Confirm / cancel action |
| `c` | Toggle between Category-grouped and All view |
| `s` | Cycle sort order (category+id / id) |
| `/` | Filter bookmarks |
| `Esc` | Clear filter / cancel |
| `[` / `]` | Shrink / grow sidebar |
| `?` | Show keyboard shortcuts |
| `q` | Quit |

In edit mode: type to edit the active cell, `Tab`/`Right` to next field, `Shift+Tab`/`Left` to previous, `Up`/`Down` to move rows, `Enter` to save, `Esc` to exit.

## Development

```bash
python -m pytest tests/
```
