<div align="center">
  <img src="logo/aweshelf.png" alt="aweshelf" width="860">
  <h1>aweshelf: AI Agents会话收藏管理器 <a href="https://github.com/Webioinfo01/aweskill"><img src="https://raw.githubusercontent.com/Webioinfo01/aweskill/main/logo/aweskill-badge2.svg" alt="aweskill companion"></a></h1>
  <p><strong>收藏、分类、恢复 AI 编程会话，支持 aweswitch 配置恢复。</strong></p>
  <p>轻量 CLI-first 工具，支持 Claude Code 和 Codex。</p>
  <p>
    <a href="./README.md">English</a> ·
    <strong>简体中文</strong> ·
    <a href="https://we.webioinfo.top/">Webioinfo</a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/version-0.1.9-7C3AED?style=flat-square" alt="Version">
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
## 安装

### 让 AI agent 安装

如果你在 Claude Code、Codex、Cursor 等 coding agent 中工作，直接告诉它：

```text
Read https://github.com/Webioinfo01/aweshelf/blob/main/README.ai.md and follow it to install aweshelf for this agent.
```

Agent 会先安装 `aweshelf` CLI，然后在下面两种 skill 管理方式中选择一种：

1. **通过 [aweskill](https://aweskill.webioinfo.top/)** — 从 GitHub 安装和管理 skill，支持更新、投影和备份。需要 Node.js。
2. **直接复制** — 将 `SKILL.md` 下载到 agent 的 skill 目录。除 Python 外无需额外依赖，但后续更新需要手动重新复制。

### pip

```bash
pip install aweshelf
```

### 可选：aweswitch

aweshelf 在收藏会话时会保存当前的 aweswitch profile。安装 [aweswitch](https://github.com/mugpeng/aweswitch) 可启用多配置管理 — 不安装的话 aweshelf 仍然可用，但恢复会话时不会自动切换 profile。

有了 aweswitch，你可以用原始 provider（如 Claude Code 官方 API）恢复会话，也可以切换到其他已配置的 profile，比如 `cc-xiaomi`、`cc-glm` 等 — 每个 profile 有独立的 API endpoint、token 和模型。

```bash
pip install aweswitch
```

## 扩展

- **[aweshelf-extension/vscode](https://github.com/mugpeng/aweshelf-extension/tree/main/vscode)** — VS Code / Cursor 扩展，可在侧边栏浏览、搜索和恢复书签。在扩展市场搜索 **aweshelf-ext**，或 [打开 Marketplace 页面](https://marketplace.visualstudio.com/items?itemName=webioinfo.aweshelf-ext)。也可下载 [.vsix](https://github.com/mugpeng/aweshelf-extension/releases) 安装。

## 支持工具

aweshelf 由两个配套工具驱动：

- **[aweskill](https://github.com/Webioinfo01/aweskill)** — 面向 AI agent 的 CLI skill 包管理器。负责 skill 的安装、更新和投影，支持 47+ 编程 agent。
- **[aweswitch](https://github.com/mugpeng/aweswitch)** — Agent profile 切换器。用不同 API、token 和模型启动会话。aweshelf 在书签中存储 aweswitch profile，恢复会话时自动还原配置。

## 使用

### AI Agent

安装 aweshelf skill（见上方[安装](#安装)），然后直接告诉你的 agent 做什么。

**你可以这样告诉你的 agent：**

> "收藏当前会话。"

> "列出 backend 分类下的书签。"

> "搜索和 auth 相关的书签。"

Agent 通过 [SKILL.md](resources/skills/aweshelf/SKILL.md) 理解所有可用命令和工作流。

> **提示：** 恢复会话（`aweshelf resume`）会启动新的 agent 进程，可能和当前运行的冲突。建议退出当前 agent 后，直接在终端用 `aweshelf browse` 或 `aweshelf resume` 恢复。

### 人类使用

主要的交互方式是 TUI：

```bash
aweshelf browse
```

浏览视图会按分类组织书签，右侧展示当前选中书签的详情。

![aweshelf 带分类分组的浏览视图](resources/image/example1.png)

按 `e` 可以在表格里直接编辑当前单元格，标题、分类和 profile 都可以在 TUI 内保存。

![aweshelf 内联编辑模式](resources/image/example2.png)

按 `/` 可以按标题、分类、会话、项目、首条提示词或 profile 过滤书签。

![aweshelf 搜索过滤](resources/image/example3.png)

`aweshelf browse` 打开交互式终端 UI，左侧为书签表格，右侧为详情面板。无需记忆命令，直接浏览、搜索、编辑和恢复书签。

也可以使用 VS Code / Cursor 插件，在侧边栏里浏览、搜索和恢复书签。在扩展市场搜索 **aweshelf-ext** 安装，或 [打开 Marketplace 页面](https://marketplace.visualstudio.com/items?itemName=webioinfo.aweshelf-ext)。

![aweshelf VS Code 侧边栏](resources/image/example4.png)

### 配合 aweswitch 自动收藏

如果你使用 [aweswitch](https://github.com/Webioinfo01/aweswitch) 管理配置，可以在启动会话时自动收藏：

```bash
aweswitch -c                    # 启动 + 自动收藏
aweswitch -c --profile cc-glm   # 指定配置启动 + 自动收藏
```

之后用相同配置恢复：

```bash
aweshelf resume aweshelf_0001   # 用存储的配置恢复
```

aweshelf 只能在事后收藏会话；aweswitch 弥补了这个短板——会话启动即保存，无需手动执行 `aweshelf bookmark`。

也可以直接调用 CLI 命令：

```bash
aweshelf bookmark                    # 收藏当前会话
aweshelf list                        # 列出所有书签
aweshelf resume aweshelf_0001        # 恢复书签
aweshelf search "auth"               # 搜索书签
```

完整命令参考见下方[命令](#命令)。

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
aweshelf bookmark [SESSION_ID] [-t TITLE] [-c CATEGORY] [--profile PROFILE] [--current] [--verbose] [--no-interactive]
aweshelf list [-c CATEGORY] [-p PROVIDER]
aweshelf search QUERY              # 搜索标题、分类、会话ID、项目路径、首条提示词、配置
aweshelf recent [-n COUNT]
aweshelf show BOOKMARK_ID [--json]
aweshelf edit BOOKMARK_ID [-t TITLE] [-c CATEGORY] [--profile PROFILE]
aweshelf rm BOOKMARK_ID [--force]
aweshelf resume BOOKMARK_ID [--profile PROFILE] [--raw] [--dry-run]
aweshelf browse
aweshelf self-update [--check]
aweshelf help [COMMAND]
```

## 自动更新

aweshelf 每次运行时会在后台检查 PyPI 是否有新版本。如果有更新，会在命令执行完毕后在 stderr 输出提醒。

手动更新：

```bash
aweshelf self-update
```

仅检查不更新：

```bash
aweshelf self-update --check
```

禁用后台检查：

```bash
export AWESHELF_NO_UPDATE_CHECK=1
```

## 浏览模式 (TUI)

`aweshelf browse` 打开交互式 TUI，左侧为书签表格，右侧为详情面板。
`aweshelf bookmark` 会标记已经收藏的会话，并可在确认后更新已有 bookmark。使用 `aweshelf bookmark --current` 可以确认并保存当前项目最近的会话，不打开会话选择列表。交互收藏时会提示填写标题、分类和 Claude aweswitch profile；未配置 aweswitch 时会跳过 profile 选择。使用 `--no-interactive` 可跳过所有提示——适用于 agent 和脚本场景，仅使用默认值或传入的参数创建书签。

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

详见 [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) 了解开发环境搭建、架构、测试和代码风格。

```bash
python -m pytest tests/
```

## 已知风险

aweshelf 书签存储的是 `session_id` 引用——**不会**复制会话内容。
恢复书签要求原始会话文件仍然存在于磁盘上。

| 风险 | Claude Code | Codex CLI |
|------|------------|-----------|
| 自动清理 | 不活跃超过 30 天的文件在启动时删除 | 目前无自动清理（非文档化保证） |
| Worktree | 会话绑定 worktree 路径；worktree 删除后 resume 可能失败 | 同上 |
| `cleanupPeriodDays` | [已知 bug](https://github.com/anthropics/claude-code/issues/62272)：部分场景下设置被静默忽略 | 不适用 |

缓解方式：在 `~/.claude/settings.json` 中增大 `cleanupPeriodDays`（如 `365`），但需验证是否生效。
对于关键会话，建议手动备份 JSONL 文件。

这些风险的后续改进计划见 [docs/todo/session_retention_0529.md](docs/todo/session_retention_0529.md)。
