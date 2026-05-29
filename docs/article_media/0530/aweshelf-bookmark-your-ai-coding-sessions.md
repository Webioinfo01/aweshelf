# aweshelf: Bring Codex Team's Durable Threads Experience to Every Agent

![aweshelf](../../../logo/aweshelf.png)

Jason ([@jxnlco](https://x.com/jxnlco)) recently shared how to get the most out of OpenAI Codex. His first point was [**Durable threads**](https://x.com/jxnlco/status/2057153744630890620) — the idea that a coding session should survive across time. You should be able to stop, come back later, and pick up exactly where you left off.

That sounds obvious. But it is not how most AI coding agents work today.

You just spent an hour with Claude Code debugging a race condition in your auth middleware. Or maybe you were troubleshooting a Snakemake pipeline where STAR alignment kept failing on a new reference genome. Either way, the session was productive. You found the root cause, sketched a fix, and started refactoring.

Then you closed the terminal.

The next morning, you open a new session. The context is gone. You try to reconstruct what you were doing. You scroll through shell history. You grep through git log. You vaguely remember the file path. You start explaining the problem again from scratch.

This is the default experience with AI coding agents. Every session is ephemeral. When it ends, the context evaporates.

The reality is uneven. Codex, Claude Code, and a few other next-generation agents have built session persistence, restoration, and forking into their core workflows. But many agents still offer only weak local history — chat logs or project-level snapshots — without a unified, searchable, forkable, portable abstraction for durable threads. And even among agents that support resume, you typically only see sessions from the current working directory. Switch to a different project, and the history is invisible.

That is the problem `aweshelf` solves — unified session management across any agent, any directory, with profile-aware restoration.

GitHub: [github.com/Webioinfo01/aweshelf](https://github.com/Webioinfo01/aweshelf)

## The Old Workflow: Sessions Are Disposable

AI coding agents produce valuable work: debugging sessions, refactoring plans, architecture explorations, test strategies. But the tooling treats each session as temporary.

When you close a Claude Code or Codex session, you lose:

- the conversation history
- the files you were editing
- the mental model you built up
- the specific API endpoint, model, and token you were using

Some platforms are starting to solve this. Codex has durable threads. Claude Code has session resume. But these features are tied to each agent's own ecosystem, and resume typically only works within the current directory. You cannot search across agents, switch projects, or restore a session with a different API configuration.

You can try to reconstruct this later. Sometimes you succeed. Often you just start over.

The cost is not just time. It is the accumulated reasoning that made the session productive in the first place.

## The aweshelf Workflow: Bookmark, Categorize, Restore

`aweshelf` is a lightweight CLI that lets you save, organize, and restore AI coding sessions, also provide TUI for human operation:

![](../../../resources/image/example1.png)

The core loop is simple:

```bash
aweshelf bookmark                    # save the current session
aweshelf list                        # see all saved sessions
aweshelf resume aweshelf_0001        # restore a session
```

But the interesting part is what gets saved. A bookmark captures:

- the session ID (so the agent can reconnect)
- the project path (so you know where you were working)
- a title and category (so you can find it later)
- the aweswitch profile (so the agent restarts with the same API endpoint, model, and token)

That last detail matters. If you use [aweswitch](https://github.com/Webioinfo01/aweswitch) to manage multiple API configurations — say, one for the official Claude API and another for a self-hosted endpoint — `aweshelf` remembers which one you were using. When you restore, the session picks up exactly where you left off.

Without aweswitch, `aweshelf` still works — you just lose the automatic profile restore. Install it when you need multi-config support:

```bash
pip install aweswitch
```

## Pair with aweskill and aweswitch

`aweshelf` works well on its own. But combined with two companion tools from the [Webioinfo](https://we.webioinfo.top/) ecosystem, the workflow gets even smoother:

- **[aweskill](https://github.com/Webioinfo01/aweskill)** — a skill package manager for 47+ AI coding agents. Install `aweshelf` as a skill once, and any agent you use — Claude Code, Codex, Cursor, Gemini CLI — can read its SKILL.md and operate the CLI without manual setup. Think of it as `npm` for agent skills.
- **[aweswitch](https://github.com/Webioinfo01/aweswitch)** — a profile switcher that saves and restores API configurations. When `aweshelf` bookmarks a session, it records which aweswitch profile was active. Resume later, and the agent restarts with the exact same endpoint, model, and token.

Together, the three tools cover the full lifecycle: **aweskill** installs the skill, **aweswitch** manages the API config, and **aweshelf** bookmarks the session. The agent handles all three — you focus on the code.

> Want to go deeper? Read [Let Your AI Agent Manage aweskill for You](https://aweskill.webioinfo.top/articles/let-your-ai-agent-manage-aweskill-for-you/) (English) or the [中文版](https://mp.weixin.qq.com/s/Fb0Q7nKEJtORSTz7Ukv_EA).

## Use Case 1: Ask the Agent to Bookmark a Session

You are deep into a debugging session with Claude Code. You have explored the codebase, narrowed down the issue, and written a partial fix. Or maybe you have been working with your agent to build a gene annotation pipeline and just got GFF3 parsing working. Either way, you need to stop for a meeting.

Instead of switching to a terminal, you say:

```text
Bookmark this session as "Fix auth race condition" in the backend category.
```

```text
Bookmark this session as "Gene annotation pipeline — GFF3 parsing done" in the bioinfo category.
```

The agent runs:

```bash
aweshelf bookmark -t "Fix auth race condition" -c backend
aweshelf bookmark -t "Gene annotation pipeline — GFF3 parsing done" -c bioinfo
```

No interactive prompts. No manual input. The agent knows the flags because `aweshelf` has a stable CLI and a SKILL.md that agents can read.

Later, when you have time, you say:

```text
Resume the auth race condition bookmark.
```

The agent finds the matching bookmark and runs:

```bash
aweshelf resume aweshelf_0003
```

The session restarts in the same project, with the same API configuration. You pick up where you left off — without ever leaving the agent.

## Use Case 2: Ask the Agent to Search and Organize

After a few weeks of daily use, you have dozens of bookmarks. You do not remember the exact IDs, but you know what you were working on.

You say:

```text
Find my bookmarks related to "RNA-seq".
```

The agent runs:

```bash
aweshelf search "RNA-seq"
```

It reports the matches — titles, categories, project paths — and asks which one you want.

Or you want a broader view:

```text
Show me all my bioinfo bookmarks.
```

```bash
aweshelf list -c bioinfo
```

The agent can also create bookmarks in bulk. If you just finished a sprint and want to save the current state:

```text
Bookmark this session as "Variant calling pipeline — DeepGeno integrated" in the bioinfo category.
```

```bash
aweshelf bookmark -t "Variant calling pipeline — DeepGeno integrated" -c bioinfo
```

All of this happens in natural language. You never need to remember command syntax.

## Use Case 3: Ask the Agent to Resume with a Different Profile

Suppose you were working with the official Claude API, but now you want to continue with a different provider — maybe a self-hosted endpoint with a different model.

You say:

```text
Resume aweshelf_0003 but use the cc-glm profile instead.
```

The agent runs:

```bash
aweshelf resume aweshelf_0003 --profile cc-glm
```

If you use [aweswitch](https://github.com/Webioinfo01/aweswitch), `aweshelf` stored the original profile in the bookmark. You can resume with the same profile by default, or switch to any configured profile.

This is useful when you want to test how a different model handles the same task, or when you need to switch providers for cost or availability reasons. The agent handles the switch; you focus on the work.

## Use Case 4: Browse Agent-Created Bookmarks in the TUI

Your agent has been bookmarking sessions for weeks. You want to see what you have.

```bash
aweshelf browse
```

The TUI opens with bookmarks grouped by category. The left panel shows the table; the right panel shows details for the selected bookmark.

![aweshelf browse view with category groups](../../../resources/image/example1.png)

Press `/` to filter by title, category, session ID, project, or profile. Press `e` to edit the title or category inline. Press `Enter` to resume a session.

This is where the human and agent workflows meet. The agent creates and organizes bookmarks during work sessions. The human browses, edits, and resumes them in the TUI when it is time to pick up past work.

You do not have to choose between "agent-operated" and "human-operated." The agent saves. The human browses. Both operate the same data.

## Use Case 5: Resume from the VS Code Sidebar

Not everyone wants to use the terminal. The [aweshelf VS Code extension](https://marketplace.visualstudio.com/items?itemName=webioinfo.aweshelf-ext) adds a sidebar panel for browsing, searching, and resuming bookmarks.

![aweshelf VS Code sidebar](../../../resources/image/example4.png)

Install it from the VS Code or Cursor extension marketplace by searching **aweshelf-ext**. The sidebar shows bookmarks grouped by category, with right-click actions for resuming, editing, copying session IDs, and removing bookmarks.

This is especially useful when you open your editor in the morning and want to pick up where you left off — whether that is a web app refactoring or a single-cell RNA-seq analysis. Instead of opening a terminal and running `aweshelf list`, you click a bookmark in the sidebar and resume.

The same bookmarks your agent created during yesterday's session are right there — categorized, searchable, and one click away.

## Use Case 6: Let the Agent Find and Resume Any Past Session

After a few months, you have dozens of bookmarks. Some are stale. Some are gold.

You say:

```text
Find the session where we were working on the scRNA-seq clustering issue.
```

```text
Find the ETL pipeline timeout session.
```

The agent runs:

```bash
aweshelf search "scRNA-seq clustering"
aweshelf search "ETL timeout"
```

It finds the match, shows the details — project path, category, date, profile — and asks if you want to resume.

```bash
aweshelf resume aweshelf_0017
```

You do not need to remember the bookmark ID. You do not need to remember the category. You just describe what you were working on, and the agent finds it.

This is the difference between a bookmark system that requires you to remember IDs and one that lets you describe what you want.

The same applies in the TUI. Press `/` to search, press `e` to edit the current cell inline — title, category, and profile can all be changed without leaving the table. Whether you prefer natural language with the agent or keyboard shortcuts in the TUI, the data is the same.

## Use Case 7: Edit Bookmarks Your Way

Bookmarks are not static. A session that was "debugging" yesterday might be "fixed — needs review" today. A bioinformatics pipeline you tagged as "RNA-seq QC" might need to be renamed to "RNA-seq QC — STAR alignment fixed" after you resolved the reference genome issue.

From the TUI, press `e` to enter inline edit mode. Change the title, category, or profile directly in the table. `Tab` moves to the next field, `Enter` saves, `Esc` cancels.

![aweshelf inline edit mode](../../../resources/image/example2.png)

Or ask the agent:

```text
Rename aweshelf_0005 to "Refactor payment service" and move it to the backend category.
```

```text
Update aweshelf_0012 title to "DEG analysis — fixed batch effect" and move it to the bioinfo category.
```

The agent runs:

```bash
aweshelf edit aweshelf_0005 -t "Refactor payment service" -c backend
aweshelf edit aweshelf_0012 -t "DEG analysis — fixed batch effect" -c bioinfo
```

No matter who makes the change — you in the TUI, or the agent through the CLI — the bookmark is updated everywhere. The TUI, the VS Code sidebar, and the CLI all see the same state.

This is the point. The agent does the mechanical work. The human does the judgment work. The data does not care who touched it.

## Why This Matters

The idea of durable threads is gaining traction. Jason's advice for Codex users was clear: make your sessions durable. Codex, Claude Code, and other next-generation agents have already built session persistence into their core workflows. But many agents still lack a unified, searchable, forkable abstraction for durable threads — and even built-in resume only sees sessions from the current directory.

`aweshelf` fills this gap. It brings Codex team's experience to every agent, with unified session management across directories and profile-aware restoration through aweswitch. The value is not in which agent you use — it is in the work you did and whether you can find it again.

`aweshelf` makes sessions durable across any agent, with a simple division of labor:

`aweshelf` addresses this with a simple division of labor:

**The agent creates.** During a work session, you tell the agent what to save. It runs the CLI, fills in the metadata, and organizes the bookmark. You stay focused on the code.

**The human browses.** When it is time to pick up past work, you open the TUI or the VS Code sidebar. You see your bookmarks grouped by category. You filter, edit, and resume with a click or a keystroke.

**Both operate the same data.** The agent writes bookmarks through the CLI. The human reads them through the TUI or VS Code. No sync layer. No special protocol. Just a JSON file on disk.

This works because `aweshelf` follows a few principles:

- documented for both humans and agents
- scriptable through a stable CLI
- conservative about destructive actions
- inspectable before applying changes
- easy to verify after each operation

It does not try to be a platform. It does not sync to the cloud. It does not require an account. The bookmarks are on disk. The format is plain JSON. The agent can read and write without guessing. The human can browse without memorizing commands.

## More from Webioinfo

`aweshelf` is part of the [Webioinfo](https://we.webioinfo.top/) ecosystem — a collection of tools for AI-assisted development:

- **[aweskill](https://aweskill.webioinfo.top/)** — CLI-first Skill package manager for 47+ AI coding agents. Install, update, and project Skills across Claude Code, Codex, Cursor, and more.
- **[awescholar](https://github.com/Webioinfo01/awescholar)** — Automated scientific literature discovery. Search, annotate, filter, and generate research reports with LLM-powered pipelines.
- **[aweswitch](https://github.com/Webioinfo01/aweswitch)** — Agent profile switcher. Launch sessions with different API endpoints, tokens, and models.

## Try It

Install:

```bash
pip install aweshelf
```

Bookmark your current session:

```bash
aweshelf bookmark
```

Browse your bookmarks:

```bash
aweshelf browse
```

Or ask your coding agent:

```text
Read https://github.com/Webioinfo01/aweshelf/blob/main/README.ai.md and follow it to install aweshelf for this agent.
```

If you use multiple API configurations, install [aweswitch](https://github.com/Webioinfo01/aweswitch) to save and restore profiles alongside bookmarks.

---

**Install**: `pip install aweshelf`

**VS Code Extension**: [aweshelf-ext on Marketplace](https://marketplace.visualstudio.com/items?itemName=webioinfo.aweshelf-ext)

**GitHub**: [github.com/Webioinfo01/aweshelf](https://github.com/Webioinfo01/aweshelf)

**More tools**: [we.webioinfo.top](https://we.webioinfo.top/)
