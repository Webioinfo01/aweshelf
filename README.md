<div align="center">
  <h1>aweshelf: Session Bookmark Manager</h1>
  <p><strong>Bookmark, categorize, and restore AI coding sessions with aweswitch profiles.</strong></p>
  <p>A lightweight CLI-first tool for Claude Code and Codex session management.</p>
  <p>
    <strong>English</strong> ·
    <a href="./README_cn.md">简体中文</a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/version-0.1.0-7C3AED?style=flat-square" alt="Version">
    <img src="https://img.shields.io/badge/python-%E2%89%A53.10-0EA5E9?style=flat-square" alt="Python">
  </p>
  <p>
    <img src="https://img.shields.io/badge/status-alpha-c96a3d?style=flat-square" alt="Status">
    <img src="https://img.shields.io/badge/install-pip-22C55E?style=flat-square" alt="pip install">
    <img src="https://img.shields.io/badge/platform-terminal-334155?style=flat-square" alt="Platform">
    <img src="https://img.shields.io/github/stars/mugpeng/aweshelf?style=flat-square" alt="GitHub stars">
  </p>
</div>

> Bookmark, categorize, and restore AI coding sessions with aweswitch profiles.

aweshelf lets you save your favorite Claude Code and Codex sessions, tag them with categories, and restore them instantly — including the aweswitch profile (API endpoint, model, token) that was active when you bookmarked.

## Install

```bash
cd aweshelf
pip install -e .
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
aweshelf bookmark [SESSION_ID] [-t TITLE] [-c CATEGORY] [--profile PROFILE]
aweshelf list [-c CATEGORY] [-p PROVIDER]
aweshelf search QUERY
aweshelf recent [-n COUNT]
aweshelf show BOOKMARK_ID [--json]
aweshelf edit BOOKMARK_ID [-t TITLE] [-c CATEGORY] [--profile PROFILE]
aweshelf rm BOOKMARK_ID [--force]
aweshelf resume BOOKMARK_ID [--profile PROFILE] [--raw] [--dry-run]
aweshelf browse
```

## Development

```bash
python -m pytest tests/
```
