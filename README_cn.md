<div align="center">
  <h1>aweshelf: 会话书签管理器</h1>
  <p><strong>收藏、分类、恢复 AI 编程会话，支持 aweswitch 配置恢复。</strong></p>
  <p>轻量 CLI-first 工具，支持 Claude Code 和 Codex。</p>
  <p>
    <a href="./README.md">English</a> ·
    <strong>简体中文</strong>
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

> 收藏、分类、恢复 AI 编程会话，支持 aweswitch 配置恢复。

aweshelf 可以保存你常用的 Claude Code 和 Codex 会话，用分类标记，并快速恢复——包括 bookmark 时的 aweswitch 配置（API 端点、模型、Token）。

## 安装

```bash
cd aweshelf
pip install -e .
```

## 快速开始

```bash
# 收藏当前项目最近的会话
aweshelf bookmark

# 列出所有收藏
aweshelf list

# 恢复收藏的会话
aweshelf resume aweshelf_0001

# 交互式浏览
aweshelf browse
```

## 配置

书签存储在 `~/.config/aweshelf/bookmarks.json`。可通过 `AWESHELF_CONFIG` 环境变量覆盖。

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

## 命令

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

## 开发

```bash
python -m pytest tests/
```
