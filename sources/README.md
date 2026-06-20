# 原始资料库 (Sources)

此文件夹用于存放所有未经过滤和整理的原始资料（作为知识库的 Working Memory 层）。

为了保持结构清晰并支持增量解析，所有原始信源必须分类存放在以下子目录中：

- 📂 [sources/chats/](chats/)：存放所有的对话记录、研究日志或滚动会话记录（动态增量追加，无需归档）。
- 📂 [sources/clippings/](clippings/)：存放所有的网页剪藏、长篇 PDF、静态文献或书籍笔记（静态全量）。
- 📂 [sources/transcripts/](transcripts/)：存放所有视频脚本、字幕与音频转文字记录（静态全量）。
- 📂 [sources/attachments/](attachments/)：存放所有本地附件（如 Markdown 页面中引用的图片、图表等）。

### 📥 录入与处理流程
1. 将文件根据类型放入 `chats/`、`clippings/` 或 `transcripts/` 子目录下。
2. 运行 `/ingest` 指令（或输入：*“录入新增知识”*），Agent 将自动：
   - 读取本库根目录下的时间戳记录文件 `.last_sync_time`。
   - 扫描 `chats/`、`clippings/` 和 `transcripts/`，定位 `mtime` 大于上次同步时间的新增或修改文件。
   - 提取文件中的事实和有向关系，整合写入 `wiki/` 目录，并自动脱敏敏感信息。
   - 更新 `.last_sync_time` 时间戳。
3. **证据链留存**：所有原始文件将永久留存在其分类子目录中，直接作为对应 Wiki 词条的 `sources:` 证据链。由于采用了时间戳增量扫描，文件无需物理移动，也不会重复录入。
