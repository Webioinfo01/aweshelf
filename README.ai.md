# aweshelf Bootstrap Protocol

This document is for AI coding agents. First install the `aweshelf` CLI, then choose one of two ways to manage the aweshelf skill for the current agent.

## Language Behavior

- Reply in the user's language when possible.
- If the user asks in Chinese, continue in Chinese.
- If the user asks in English, continue in English.

## Step 1: Install aweshelf CLI

### Prerequisites

- Python >= 3.10 (`python3 --version`)
- pip available (`pip --version`)

If Python is missing, tell the user to install it from https://www.python.org/.

### Steps

#### 1. Install aweshelf Python package

```bash
pip install aweshelf
```

#### 2. Verify aweshelf CLI

```bash
aweshelf -v
```

Expected output: `aweshelf X.Y.Z`

---

## Step 2: Install or manage the aweshelf skill

Choose one of the following skill management options. Both options assume the `aweshelf` CLI was installed in Step 1.

### Option A: Via aweskill (recommended if aweskill is available)

Use this option if the user already has aweskill installed, or is willing to install it. This gives full skill management — install, update, projection, backup.

#### Prerequisites

- Node.js >= 20 (`node --version`) — required by aweskill
- npm available (`npm --version`)

If Node.js is missing, tell the user to install it from https://nodejs.org/.

#### Steps

##### A1. Install aweskill (if not already installed)

```bash
npm install -g aweskill
```

##### A2. Initialize the aweskill central store (if not already done)

```bash
aweskill store init
```

##### A3. Install aweshelf skill from GitHub

```bash
aweskill install Webioinfo01/aweshelf
```

##### A4. Identify the current agent

```bash
aweskill agent supported
```

Look for lines marked with `✓`. Common agent ids: `claude-code`, `cursor`, `codex`, `gemini-cli`, `windsurf`, `opencode`, `qwen-code`.

If you cannot determine the agent id, ask the user.

##### A5. Project aweshelf skill to this agent

```bash
aweskill agent add skill aweshelf --global --agent <agent-id>
```

##### A6. Verify

```bash
aweskill agent list --global --agent <agent-id>
```

Expected: `aweshelf` shows as `linked`.

---

### Option B: Direct copy (no aweskill needed)

Use this option if the user does not have aweskill and does not want to install Node.js. This copies the SKILL.md file directly into the agent's skill directory.

#### Prerequisites

- `curl` or `wget` available

#### Steps

##### B1. Identify the current agent's skill directory

Determine which agent is running and its global skill directory:

| Agent | Skill directory |
|---|---|
| Claude Code | `~/.claude/skills/aweshelf/` |
| Codex | `~/.codex/skills/aweshelf/` |
| Cursor | `.cursor/skills/aweshelf/` (project-level) |
| Gemini CLI | `~/.gemini/skills/aweshelf/` |
| Windsurf | `~/.windsurf/skills/aweshelf/` |
| OpenCode | `~/.opencode/skills/aweshelf/` |
| Qwen Code | `~/.qwen/skills/aweshelf/` |

If the agent is not in this list, ask the user where to place the skill file.

##### B2. Download and place SKILL.md

```bash
mkdir -p <skill-directory>
curl -fsSL https://raw.githubusercontent.com/Webioinfo01/aweshelf/main/resources/skills/aweshelf/SKILL.md -o <skill-directory>/SKILL.md
```

Replace `<skill-directory>` with the path from step B1.

---

## Final Step (both options)

After setup, tell the user to invoke skills (`/` in Claude Code, `$` in Codex, or the equivalent in other agents) and check if `aweshelf` appears in the list. If it does, the skill is ready to use immediately. If not, the user should restart the agent.

> aweshelf is installed. Invoke skills (type `/` or `$` depending on your agent) and look for `aweshelf` — if it appears, you're good to go. If not, restart the agent. Then you can ask me things like:
>
> - "Bookmark the current session."
> - "List my bookmarks in the backend category."
> - "Resume bookmark aweshelf_0003."

If the user is speaking Chinese, use this version instead:

> aweshelf 已安装。请调用 skills（输入 `/` 或 `$`，取决于你的 agent），看看列表中是否出现了 `aweshelf`。如果出现了，说明已就绪可以直接使用。如果没有，请重启 agent 后再试。然后你可以继续问我，例如：
>
> - "收藏当前会话。"
> - "列出 backend 分类下的书签。"
> - "恢复书签 aweshelf_0003。"

## Safety Rules

- If you cannot determine the agent id or skill directory, ask the user before proceeding.
- Do not copy skills to all agents by default. Only set up the current agent unless the user explicitly requests otherwise.
- If any command fails, report the exact command and error message to the user. Do not silently retry.
