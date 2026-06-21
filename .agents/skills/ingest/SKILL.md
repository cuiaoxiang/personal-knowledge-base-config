---
name: ingest
description: Compile raw files in sources/ into structured wiki pages, perform data desensitization, and update sync status for archiving.
---

# Ingest Skill (智能录入与归档)

本技能用于处理用户在 `sources/` 目录下存入的原始文件（剪藏、对话日志等），将其中的核心事实提炼编译为 Wiki 词条，并对其同步状态进行逻辑归档。

## 触发方式
- 用户输入 `/ingest` 或 `/ingest <file_path>`
- 或用户下达指令：“录入新增知识” 或 “帮我录入 sources/文件名”

## 执行步骤与规范

### 1. 信源定位与读取
- **指定文件录入**：若用户指定了特定文件路径 `<file_path>`：
  - **如果路径是 `.pdf` 文件**（传入路径必定在 Vault 之外，例如 `/Users/cuiaoxiang/My Drive/Readings/Thesis/paper.pdf`）：
    1. **解析并总结标题**：Agent 读取并总结该外部 PDF，获得其中文核心学术标题，格式化为 `🏛️ [论文中文标题]`。
    2. **生成同名摘要 MD 文件**：原地保留外部 PDF 不动（不复制、不移动、不重命名）。在 Vault 的 `sources/papers/` 目录下创建同名 `🏛️ [论文中文标题].md`：
       - YAML 头中 `sources` 属性写入该外部 PDF 的 `file:///` 绝对路径（路径必须进行 URL 百分号编码，例如将空格转为 `%20`，以确保在 Obsidian Properties 中可被正常识别并点击打开。例如：`sources: - "file:///Users/cuiaoxiang/My%20Drive/Readings/Thesis/paper.pdf"`）。
       - 正文仅提炼写入论文的深度核心大纲、摘要与关键发现（总行数控制在 1000 行以内），不包含任何正文 PDF 超链接。
    3. **重定向指针**：将当前处理目标重新指向该新生成的 `.md` 提炼页，继续执行后续解析。
  - **如果路径是 `.md` 文件**（例如 `sources/chats/💬 Antigravity-研究日志.md`）：Agent 直接定位并读取该文件。
- **全局增量录入**：若用户未指定路径（仅输入 `/ingest`）：
  1. 读取本库根目录下的时间戳记录文件 `.last_sync_time`。
  2. 遍历 `sources/chats/`、`sources/clippings/`、`sources/transcripts/` 和 `sources/papers/` 目录，获取每个文件的最近修改时间 `mtime`。
  3. 筛选出所有满足 `mtime > .last_sync_time` 的新增或被修改的文件作为待处理队列。
- **行数控制**：确认单次处理总行数不超过 1000 行（指生成的 Markdown 总行数）。若超出，向用户提议分批（Batching）处理。

### 2. 差异化读取与增量逻辑
- **对于 `sources/clippings/`、`sources/transcripts/` 与 `sources/papers/`（静态全量信源，包括新生成的 `.md` 论文摘要）中的变更文件**：
  - 属于全新或全量更新的静态资料，读取整篇 Markdown 文件内容进行全量编译提取。
- **对于 `sources/chats/`（动态增量滚动日志）中的变更文件**：
  - 读取并解析文件内容。对比其内部 `## YYYY-MM-DD 更新` 的章节标题日期与 `.last_sync_time`。
  - **仅读取并分析日期晚于 `.last_sync_time` 的更新章节**。跳过历史已同步的内容，以极大地节省 Token 并防止重复提取。

### 3. 信源正文去直链原则
- 为了保持知识库内文档精简美观，在 Ingest 处理或生成的 `sources/` 各类 MD 信源文件（如 `sources/papers/` 中的论文摘要、`sources/transcripts/` 中的视频转录稿等）中，**正文部分一律不保留指向外部原件的超链接**（如本地 PDF 直链、YouTube 视频 URL）。
- 所有指向外部原件的直链有且仅声明在 YAML 头部的 `sources`（或 `source`）属性中。
- 对于包含空格的外部文件路径，在 YAML 写入时必须进行 URL 百分号编码（将空格转为 `%20`），以确保在 Obsidian 的 Properties 面板中可以被正常点击打开。

### 4. 数据敏感性脱敏
- 在分析内容前，扫描并脱敏敏感信息（如 API Key、私人密码、Token 等），确保这些信息不会写入 `wiki/` 或任何日志中（替换为 `[REDACTED]`）。

### 5. 实体提炼与知识整合
- 扫描增量内容，提取核心实体与有向关联关系（`uses`, `depends on`, `supersedes`, `caused`, `fixed`, `contradicts`）。
- **绝对信源依赖**：在知识提炼与合并过程中，**必须 100% 依赖 sources 中的原始文本事实**。严禁带入任何未经 source 记录的预训练常识或代码猜测，防止知识库被脑补信息污染。
- **扁平物理目录**：所有编译出的词条必须平铺保存在 `wiki/` 根目录下，禁止新建任何子目录。
- 对于提炼出的每个实体：
  - **增量合并 (Merge)**：如果该实体在 `wiki/` 下已存在同名 Markdown 页面（大小写不敏感），将新事实、操作规程或结论合并/追加到已有页面。
    - 更新头部 YAML 的 `last_confirmed` 日期为当前实际执行维护的日期 (`YYYY-MM-DD`)。
    - 将原信源以 `[[sources/chats/文件名]]`、`[[sources/clippings/文件名]]`、`[[sources/transcripts/文件名]]` 或 `[[sources/papers/文件名]]` 的双链形式追加到 YAML 的 `sources:` 列表中（若已存在则不重复添加）。
    - 重新评估并更新置信度 `confidence`。
  - **全新创建 (New)**：如果实体尚不存在，创建 `wiki/实体名称.md`（优先使用中文作为文件名与标题）。
    - 统一包含如下 YAML 元数据模板：
      ```yaml
      ---
      type: Library | Concept | Person | Project | Decision | Synthesis
      confidence: 0.85     # 视物理属性或时效敏感度而定，定理/年份常识为 1.0，高频更迭工具为 0.85
      last_confirmed: YYYY-MM-DD  # 当前执行日期
      sources:
        - "[[sources/chats/原文件名]]"  # 或 "[[sources/clippings/原文件名]]"、"[[sources/transcripts/原文件名]]" 或 "[[sources/papers/原文件名]]"
      ---
      ```
    - 正文统一包含以下二级章节（注意：各级章节标题一律不使用数字编号前缀）：
      - `## 概述`
      - `## 关联关系` (列出双链关系)
      - `## 核心内容与规则`

### 6. 索引导航与时间戳重置
- 如果创建了全新百科页面，必须将其以双链形式加入到根目录的 `index.md` 对应的 MOC/Index 章节下。
- **重置时钟**：同步提取完成后，使用 `write_to_file` 将当前运行的系统时间戳（格式为 `YYYY-MM-DD HH:mm:ss`）覆写到本库根目录下的 `.last_sync_time` 文件中，以重置增量起点。
- **原文件保留**：原文件永久保留在 `sources/chats/`、`sources/clippings/`、`sources/transcripts/` 或 `sources/papers/` 原位，不再进行任何物理移动或删除。
