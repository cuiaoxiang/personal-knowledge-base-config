# 原始资料库 (Sources)

此文件夹用于存放所有未经过滤和整理的原始资料（作为知识库的 Working Memory 层）。你可以将以下内容放入这里：
- 🌐 网页剪藏 (Web Clippings)
- 💬 会话记录或录音转文字 (Chat Logs / Transcripts)
- ✍️ 个人随笔/读书笔记草稿 (Rough Notes)
- 📊 原始系统日志 (Raw Logs)

### 录入与处理流程
1. 将文件保存到此目录下，文件名建议带有明确的主题或时间戳（例如 `2026-06-09-my-research.md`）。
2. 让 AI Agent 扫描此文件：你可以直接对 Agent 说：*“帮我录入/Ingest sources/2026-06-09-my-research.md”*。
3. Agent 将按照 [GEMINI.md](../GEMINI.md) 约定的规范：
   - 自动过滤敏感信息（如 API Key 等密码）。
   - 提取文件中的**实体**（项目、工具、人物、决策等）和**有向关系**。
   - 在 `wiki/` 目录中生成/更新高密度的百科页面，并在根目录 `index.md` 中注册。
4. **原则**：此目录下的原始文件一旦录入，通常保持只读状态，作为后续 Wiki 页面的“证据链”进行追溯。
