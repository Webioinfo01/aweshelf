<div align="center">
  <img src="logo/aweshelf.png" alt="aweshelf" width="860">
  <h1>aweshelf: 会话书签管理器</h1>
  <p><strong>收藏、分类、恢复 AI 编程会话，支持 aweswitch 配置恢复。</strong></p>
  <p>轻量 CLI-first 工具，支持 Claude Code 和 Codex。</p>
  <p>
    <a href="./README.md">English</a> ·
    <strong>简体中文</strong> ·
    <a href="https://we.webioinfo.top/">Webioinfo</a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/version-0.1.3-7C3AED?style=flat-square" alt="Version">
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

> 收藏、分类、恢复 AI 编程会话，支持 aweswitch 配置恢复。

aweshelf 可以保存你常用的 Claude Code 和 Codex 会话，用分类标记，并快速恢复——包括 bookmark 时的 aweswitch 配置（API 端点、模型、Token）。

## 安装

```bash
pip install aweshelf
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
aweshelf bookmark [SESSION_ID] [-t TITLE] [-c CATEGORY] [--profile PROFILE] [--current] [--verbose]
aweshelf list [-c CATEGORY] [-p PROVIDER]
aweshelf search QUERY              # 搜索标题、分类、会话ID、项目路径、首条提示词、配置
aweshelf recent [-n COUNT]
aweshelf show BOOKMARK_ID [--json]
aweshelf edit BOOKMARK_ID [-t TITLE] [-c CATEGORY] [--profile PROFILE]
aweshelf rm BOOKMARK_ID [--force]
aweshelf resume BOOKMARK_ID [--profile PROFILE] [--raw] [--dry-run]
aweshelf browse
aweshelf help [COMMAND]
```

## 浏览模式 (TUI)

`aweshelf browse` 打开交互式 TUI，左侧为书签表格，右侧为详情面板。
`aweshelf bookmark` 会标记已经收藏的会话，并可在确认后更新已有 bookmark。使用 `aweshelf bookmark --current` 可以确认并保存当前项目最近的会话，不打开会话选择列表。交互收藏时会提示填写标题、分类和 Claude aweswitch profile；未配置 aweswitch 时会跳过 profile 选择。

| 按键 | 操作 |
|------|------|
| `Enter` | 恢复选中的会话（带确认） |
| `e` | 内联编辑当前单元格（标题、分类、配置） |
| `r` | 删除选中书签（带确认） |
| `y` / `n` | 确认 / 取消操作 |
| `c` | 切换分类分组 / 全部视图 |
| `s` | 循环排序方式（分类+ID / ID） |
| `/` | 过滤书签 |
| `Esc` | 清除过滤 / 取消 |
| `[` / `]` | 缩小 / 扩大侧边栏 |
| `?` | 显示快捷键帮助 |
| `q` | 退出 |

编辑模式：输入文字编辑当前单元格，`Delete` 清空当前单元格，`Tab`/`Right` 切换下一个字段，`Shift+Tab`/`Left` 切换上一个，`Up`/`Down` 切换行，`Enter` 保存，`Esc` 退出。

## 开发

```bash
python -m pytest tests/
```
