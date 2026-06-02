# Xiaohongshu Post

## Title

aweshelf: 像整理抽屉一样轻松收纳agent会话

## Content

Codex 团队的 Jason 最近分享了把 Codex 用到极致的心得，第一条建议就是：会话持久化。编程会话应该能随时停下来、过会儿再回来，从断点继续。

但现实中，大多数 AI 编程 Agent 并不是这样工作的。你花了一小时调试完一个 bug，关掉终端，第二天打开——上下文全没了。

aweshelf 就是来解决这个问题的。

一行命令保存会话：
aweshelf bookmark → 收藏当前会话
aweshelf list → 查看所有会话
aweshelf resume aweshelf_0001 → 从断点继续

它的核心优势：
✅ 跨 Agent——Claude Code、Codex、Cursor、Gemini CLI 都能用
✅ 跨目录——所有项目的会话统一管理
✅ 配置感知——恢复时自动用相同的 API 端点和模型
✅ TUI 浏览——终端内可视化浏览、搜索、编辑
✅ VS Code 扩展——侧边栏一键恢复
✅ Agent 友好——直接用自然语言让 Agent 帮你收藏和恢复

分工清晰：Agent 负责创建和整理，人类负责浏览和判断。同一个 JSON 文件，没有同步层，没有云端，就是本地文件。

pip install aweshelf 即可开始。

项目在 Webioinfo01/aweshelf

## Tags

#AI编程 #Claude #Cursor #效率工具 #程序员 #开发工具 #aweshelf

## Images

prompts/ 目录下有 6 张图片卡片的 prompt 文件，运行以下命令生成图片：

```bash
bun .claude/skills/peng-post-to-xhs/scripts/main.ts --batchdir prompts/ --images-dir ./
```

## Publish Command

```bash
bun .claude/skills/peng-post-to-xhs/scripts/publish.ts \
  --skip-gen \
  --images ./01-cover.png ./02-pain-point.png ./03-solution.png ./04-features.png ./05-workflow.png ./06-cta.png \
  --title "aweshelf: 像整理抽屉一样轻松收纳agent会话" \
  --content-file post-content.txt \
  --tags "AI编程" "Claude" "Cursor" "效率工具" "程序员" "开发工具" "aweshelf"
```
