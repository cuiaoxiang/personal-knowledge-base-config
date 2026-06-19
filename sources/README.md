# 原始资料库 (Sources)

此文件夹用于存放所有未经过滤和整理的原始资料（作为知识库的 Working Memory 层）。你可以将以下内容放入这里：
- 🌐 网页剪藏 (Web Clippings)
- 💬 会话记录或录音转文字 (Chat Logs / Transcripts)
- ✍️ 个人随笔/读书笔记草稿 (Rough Notes)
- 📊 原始系统日志 (Raw Logs)

### 录入与处理流程
1. 将文件保存到此目录下（暂存为 Working Memory），文件名建议带有明确的主题或时间戳（例如 `[Clippings] my-research.md`）。
2. 让 AI Agent 扫描并编译此文件：运行 `/ingest` 指令（或直接输入：*“帮我录入 sources/文件名”*）。
3. Agent 将自动：
   - 过滤敏感信息（如 API Key 等密码）。
   - 提炼核心实体与有向关系，整合写入 `wiki/` 目录。
   - 自动将处理完成的原始文件移入 `sources/processed/` 已处理目录中，以保持 Inbox 的清洁与防碎片化。
4. **原则**：移入 `processed/` 下的原始文件保持只读状态，作为后续 Wiki 词条的“证据链”以供双链溯源。
