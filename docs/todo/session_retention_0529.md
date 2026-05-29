# Session Retention — TODO 2025-05-29

aweshelf bookmarks are references (session_id), not copies. If the underlying session file
is deleted or becomes inaccessible, the bookmark becomes a dead link.

aweshelf 书签存储的是 session_id 引用，不会复制会话内容。如果底层会话文件被删除或不可访问，书签将变成死链接。

## Known Risks / 已知风险

### 1. Claude Code auto-cleanup / 自动清理

- Default `cleanupPeriodDays`: 30 (inactive files deleted at startup)
  默认 30 天，不活跃的文件在启动时被删除
- Configurable in `~/.claude/settings.json`, but [known bugs](https://github.com/anthropics/claude-code/issues/62272) where the setting is silently ignored
  可在 `~/.claude/settings.json` 中配置，但[已知 bug](https://github.com/anthropics/claude-code/issues/62272) 会导致设置被静默忽略
- Only affects sessions with mtime older than N days — actively used sessions are safe
  仅影响 mtime 超过 N 天的会话——正在使用的会话不受影响

### 2. Codex CLI retention / 持久化

- No documented auto-cleanup today
  目前无自动清理
- Not a guaranteed policy — future versions may introduce retention
  非文档化保证——未来版本可能引入清理策略

### 3. Worktree isolation / Worktree 隔离

- Sessions created in a git worktree are tied to that worktree's `project_path`
  在 git worktree 中创建的会话绑定该 worktree 的 project_path
- If the worktree is deleted, `aweshelf resume` may fail (path no longer exists)
  如果 worktree 被删除，`aweshelf resume` 可能失败（路径不存在）
- `claude --resume` defaults to searching current project only
  `claude --resume` 默认只搜索当前项目

## Future Considerations / 后续改进计划

- [ ] **Health check command / 健康检查命令**: `aweshelf check` — scan all bookmarks, report which sessions are missing/expired / 扫描所有书签，报告哪些会话已失效
- [ ] **Status indicator / 状态指示**: `aweshelf list` / `aweshelf browse` — mark bookmarks whose JSONL is missing / 标记 JSONL 已丢失的书签
- [ ] **Snapshot mode / 快照模式**: optionally copy key session metadata (first prompt, summary) into aweshelf's own store at bookmark time / 收藏时可选将会话关键元数据（首条提示词、摘要）存入 aweshelf 自身存储
- [ ] **Export command / 导出命令**: `aweshelf export <id>` — copy the full JSONL to a user-specified location / 将完整 JSONL 复制到用户指定位置
- [ ] **Worktree-aware resume / Worktree 感知恢复**: detect worktree path, fall back to session_id-based search across all projects / 检测 worktree 路径，回退到跨项目 session_id 搜索
