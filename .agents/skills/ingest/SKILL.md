---
name: ingest
description: Compile raw files in sources/ into structured wiki pages, perform data desensitization, and automatically move the processed raw files to sources/processed/ for archiving.
---

# Ingest Skill (智能录入与归档)

本技能用于处理用户在 `sources/` 下存入的原始文件（剪藏、对话日志等），将其中的核心事实提炼编译为 Wiki 词条，并对原文件进行归档。

## 触发方式
- 用户输入 `/ingest <file_path>` 
- 或用户下达类似指令：“帮我录入 sources/文件名”

## 执行步骤与规范

### 1. 信源检查与读取
- 校验目标文件是否存在于 `sources/`（新暂存信源）或 `sources/processed/`（历史滚动日志）下。
- 读取文件内容，确认总行数不超过 1000 行。若超出，主动向用户提议分批处理。
- **滚动日志增量提取逻辑 (Incremental Ingest for Rolling Logs)**：
  - 若录入目标为已处于 `sources/processed/` 目录下的滚动日志文件（如 `💬` 类的长期研究日志）：
    1. 读取本库根目录下的时间戳记录文件 `.last_sync_time`。
    2. 解析并对比该滚动日志的 YAML 头部中记录的 `last_modified_timestamp`。
    3. 若有更新，**仅读取并处理日期晚于 `.last_sync_time` 的 `## YYYY-MM-DD 更新` 章节**。跳过历史已录入的内容，以极大地节省 Token 并防止重复录入。

### 2. 数据敏感性脱敏
- 在分析内容前，扫描并脱敏敏感信息（如 API Key、私人密码、Token 等），确保这些信息不会写入 `wiki/` 或任何日志中。

### 3. 实体提炼与知识整合
- 扫描内容，提取核心实体与 typed 关联关系（`uses`, `depends on`, `supersedes`, `caused`, `fixed`, `contradicts`）。
- **扁平物理目录**：所有编译出的词条必须平铺保存在 `wiki/` 根目录下，禁止新建任何子目录。
- 对于提炼出的每个实体：
  - **增量合并 (Merge)**：如果该实体在 `wiki/` 下已存在同名 Markdown 页面（大小写不敏感），将新事实、操作规程或结论合并/追加到已有页面。
    - 更新头部 YAML 的 `last_confirmed` 日期为当前实际执行维护的日期 (`YYYY-MM-DD`)。
    - 将原信源以 `[[sources/processed/文件名]]` 的双链形式追加到 YAML 的 `sources:` 列表中。
    - 重新评估置信度 `confidence`。
  - **全新创建 (New)**：如果实体尚不存在，创建 `wiki/实体名称.md`（优先使用中文作为文件名与标题）。
    - 统一包含如下 YAML 元数据模板：
      ```yaml
      ---
      type: Library | Concept | Person | Project | Decision | Synthesis
      confidence: 0.85     # 视物理属性或时效敏感度而定，定理/年份常识为 1.0，高频更迭工具为 0.85
      last_confirmed: YYYY-MM-DD  # 当前执行日期
      sources:
        - "[[sources/processed/原文件名]]"
      ---
      ```
    - 正文统一包含以下二级章节（注意：各级章节标题一律不使用数字编号前缀，如 `## 概述`，严禁使用 `## 1. 概述`）：
      - `## 概述`
      - `## 关联关系` (列出双链关系)
      - `## 核心内容与规则`

### 4. 索引导航更新
- 如果创建了全新百科页面，必须将其加入到根目录的 `index.md` 中。
- 如果新页面类型为 `Synthesis`，将其挂载到 `index.md` 的 `### 🧪 综合研究与深度报告 (Syntheses)` 章节下。

### 5. 原始信源物理归档
- 完成 Wiki 写入后，为了防止 `sources/` Inbox 堆积碎片，必须将原文件移至 `sources/processed/` 目录。
- **具体做法**：
  1. 使用 `write_to_file` 将原文件完整内容写入到 `sources/processed/文件名` 中。
  2. 运行 `mv sources/文件名 sources/processed/文件名`（或通过 `rm sources/文件名`）的命令行清理原路径，并将此命令提请用户审批运行。
