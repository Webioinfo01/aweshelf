# Bookmark Your AI Coding Sessions — and Actually Find Them Again

You just spent an hour with Claude Code debugging a race condition in your auth middleware. The session was productive. You found the root cause, sketched a fix, and started refactoring.

Then you closed the terminal.

The next morning, you open a new session. The context is gone. You try to reconstruct what you were doing. You scroll through shell history. You grep through git log. You vaguely remember the file path. You start explaining the problem again from scratch.

This is the default experience with AI coding agents. Every session is ephemeral. When it ends, the context evaporates.

That is the problem `aweshelf` solves.

GitHub: [github.com/Webioinfo01/aweshelf](https://github.com/Webioinfo01/aweshelf)

## The Old Workflow: Sessions Are Disposable

AI coding agents produce valuable work: debugging sessions, refactoring plans, architecture explorations, test strategies. But the tooling treats each session as temporary.

When you close a Claude Code or Codex session, you lose:

- the conversation history
- the files you were editing
- the mental model you built up
- the specific API endpoint, model, and token you were using

You can try to reconstruct this later. Sometimes you succeed. Often you just start over.

The cost is not just time. It is the accumulated reasoning that made the session productive in the first place.

## The aweshelf Workflow: Bookmark, Categorize, Restore

`aweshelf` is a lightweight CLI that lets you save, organize, and restore AI coding sessions.

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

That last detail matters. If you use [aweswitch](https://github.com/mugpeng/aweswitch) to manage multiple API configurations — say, one for the official Claude API and another for a self-hosted endpoint — `aweshelf` remembers which one you were using. When you restore, the session picks up exactly where you left off.

Without aweswitch, `aweshelf` still works — you just lose the automatic profile restore. Install it when you need multi-config support:

```bash
pip install aweswitch
```

## Use Case 1: Save a Productive Session Before Closing

You are deep into a debugging session with Claude Code. You have explored the codebase, narrowed down the issue, and written a partial fix. But you need to stop for a meeting.

Instead of losing everything:

```text
Bookmark this session.
```

The agent runs:

```bash
aweshelf bookmark
```

It prompts for a title and category. You type "Fix auth race condition" and tag it as "backend". The session is saved.

Later, when you have time:

```bash
aweshelf resume aweshelf_0003
```

The agent restarts in the same project, with the same API configuration. You pick up where you left off.

## Use Case 2: Organize Sessions by Project or Topic

Over a few weeks, you accumulate bookmarks from different projects: frontend refactors, backend debugging, data pipeline work, documentation drafts.

Without organization, the list becomes a flat mess. With categories, it stays navigable:

```bash
aweshelf bookmark -t "Migrate to FastAPI" -c backend
aweshelf bookmark -t "Redesign dashboard" -c frontend
aweshelf bookmark -t "Fix ETL timeout" -c data
```

You can filter when listing:

```bash
aweshelf list -c backend
```

Or search across everything:

```bash
aweshelf search "auth"
```

The TUI (`aweshelf browse`) groups bookmarks by category in a sidebar table, with details on the right. Press `/` to filter, `e` to edit inline, `Enter` to resume.

![aweshelf browse view with category groups](../../../resources/image/example1.png)

## Use Case 3: Let the Agent Manage Bookmarks

If you are working inside a coding agent, you do not need to switch to a terminal. Just ask:

```text
Bookmark this session as "Refactor payment flow" in the backend category.
```

The agent runs the `aweshelf bookmark` command with the right flags. No manual input needed.

You can also ask:

```text
List my backend bookmarks.
```

or:

```text
Search for bookmarks related to "payment".
```

The agent translates natural language into `aweshelf` commands, runs them, and reports the results. This works because `aweshelf` has a stable CLI and a SKILL.md that agents can read.

## Use Case 4: Resume with a Different Profile

Suppose you were working with the official Claude API, but now you want to continue with a different provider — maybe a self-hosted endpoint with a different model.

If you use aweswitch, `aweshelf` stored the original profile in the bookmark. You can resume with the same profile:

```bash
aweshelf resume aweshelf_0003
```

Or switch to a different one:

```bash
aweshelf resume aweshelf_0003 --profile cc-glm
```

The agent restarts with the new API configuration, but in the same project context. This is useful when you want to test how a different model handles the same task, or when you need to switch providers for cost or availability reasons.

## Use Case 5: Browse and Search from VS Code

Not everyone wants to use the terminal. The [aweshelf VS Code extension](https://marketplace.visualstudio.com/items?itemName=webioinfo.aweshelf-ext) adds a sidebar panel for browsing, searching, and resuming bookmarks.

![aweshelf VS Code sidebar](../../../resources/image/example4.png)

Install it from the VS Code or Cursor extension marketplace by searching **aweshelf-ext**. The sidebar shows bookmarks grouped by category, with right-click actions for resuming, editing, copying session IDs, and removing bookmarks.

## Use Case 6: Quickly Find and Resume Any Past Session

After a few months, you have dozens of bookmarks. Some are stale. Some are gold.

The fastest way to find what you need:

```bash
aweshelf search "refactor"
```

This searches across titles, categories, session IDs, project paths, and even the first prompt of each session. You do not need to remember the exact bookmark ID — just a keyword from what you were working on.

From the TUI, press `/` and type a filter. The sidebar updates in real time.

## Why This Matters

AI coding sessions are becoming more valuable over time. A well-structured debugging session can save hours of work. A thorough architecture exploration can prevent weeks of wrong turns.

But the tooling has not caught up. Most agents treat sessions as disposable. When the terminal closes, the context is gone.

`aweshelf` is a small tool that addresses this gap:

- **Save**: bookmark a session in one command, with metadata that matters
- **Organize**: categorize and search across bookmarks
- **Restore**: resume a session with the same project context and API configuration
- **Automate**: let your agent manage bookmarks through natural language
- **Browse**: use the TUI or VS Code extension for a visual overview

It does not try to be a platform. It does not sync to the cloud. It does not require an account. It is a local CLI that stores bookmarks in a JSON file you can read, edit, and back up.

The best tools for AI coding agents should be:

- documented for both humans and agents
- scriptable through a stable CLI
- conservative about destructive actions
- inspectable before applying changes
- easy to verify after each operation

`aweshelf` follows those principles. The bookmarks are on disk. The format is plain JSON. The CLI is predictable. The agent can read and write bookmarks without guessing.

## More from Webioinfo

`aweshelf` is part of the [Webioinfo](https://we.webioinfo.top/) ecosystem — a collection of tools for AI-assisted development:

- **[aweskill](https://aweskill.webioinfo.top/)** — CLI-first Skill package manager for 47+ AI coding agents. Install, update, and project Skills across Claude Code, Codex, Cursor, and more.
- **[awescholar](https://github.com/mugpeng/awescholar)** — Automated scientific literature discovery. Search, annotate, filter, and generate research reports with LLM-powered pipelines.
- **[aweswitch](https://github.com/mugpeng/aweswitch)** — Agent profile switcher. Launch sessions with different API endpoints, tokens, and models.

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
Install aweshelf and bookmark this session.
```

If you use multiple API configurations, install [aweswitch](https://github.com/mugpeng/aweswitch) to save and restore profiles alongside bookmarks.

---

**Install**: `pip install aweshelf`

**VS Code Extension**: [aweshelf-ext on Marketplace](https://marketplace.visualstudio.com/items?itemName=webioinfo.aweshelf-ext)

**GitHub**: [github.com/Webioinfo01/aweshelf](https://github.com/Webioinfo01/aweshelf)

**More tools**: [we.webioinfo.top](https://we.webioinfo.top/)
