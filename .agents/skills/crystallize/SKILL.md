---
name: crystallize
description: Summarize active conversations and complex debug sessions into structured Concept entries or Synthesis reports, applying the cross-vault read-only and profiling rules.
---

# Crystallize Skill (会话结晶)

本技能用于将当前的复杂技术探讨、Debug 调试过程或外部笔记成果，结晶提炼为高密度的百科词条（Concept 等）或专题报告（Synthesis）。

## 触发方式
- 用户输入 `/crystallize`
- 或当会话结束、达成阶段性技术结论时由 Agent 主动建议。

## 执行步骤与规范

### 1. 归档原始会话信源 (第一阶段)
- **绝对信源依赖**：严禁直接绕过暂存区修改 Wiki。必须先在本库的 `sources/chats/` 目录下归档此次会话的原始事实：
  - **新会话**：创建名为 `💬 [主题描述].md` 的新文件。
  - **持续主题**：以 `## YYYY-MM-DD 更新` 的形式追加到已有的滚动日志末尾（如 `💬 Antigravity-研究日志.md`）。
  - **YAML 元数据**：必须包含以下属性：
    ```yaml
    ---
    type: chat
    created: YYYY-MM-DD
    last_modified_timestamp: [UNIX时间戳]
    ---
    ```
  - **内容梳理**：高保真地整理对谈历史，提取出核心问题、尝试过程、最终采纳的有效方案、底层原理解析及关键命令。

### 2. 生成或更新 Wiki 词条与 Synthesis 报告 (第二阶段)
- **Concept 词条**：若成果属于单一实体或架构模式，合并/更新至对应的 `wiki/` 百科页面下。
- **Synthesis 报告 (综合研究与深度报告)**：若成果是跨领域的复杂分析或深度调研，则在 `wiki/` 目录下生成一个独立的 Markdown 文件。
  - **双链关联**：必须在 YAML 头部的 `sources` 属性中添加对步骤 1 中创建/更新的 `sources/chats/💬 xxx.md` 文件的双链引用：
    ```yaml
    ---
    type: Synthesis
    confidence: 0.95
    last_confirmed: YYYY-MM-DD
    sources:
      - "[[sources/chats/💬 刚才创建的会话文件名.md]]"
    ---
    ```
  - 将生成的 Synthesis 报告链接挂载到 `index.md` 中的 `### 🧪 综合研究与深度报告 (Syntheses)` 章节。
  - **排版规范**：正文各级章节标题一律不使用数字编号前缀（例如：必须使用 `## 核心架构`，严禁使用 `## 1. 核心架构`）。

### 3. 跨 Vault 存算分离准则 (Cross-Vault Read-Only)
- 若结晶的知识来源是用户的其他外部 Obsidian Vault（如 `个人笔记`）：
  - **严禁拷贝文本**：绝不能将外部 Markdown 文件的文本内容复制到本知识库的 `sources/` 或 `wiki/` 中。
  - **直接读取与引用**：直接使用 `view_file` 跨目录读取原文进行提炼，在最终 Wiki 词条中使用 `obsidian://` 协议的 URI 链接进行溯源。
  - **严禁越界修改**：严禁对外部 Vault 进行任何写入、删除、重命名或移动操作。

### 4. 按需深拷贝插图 (On-Demand Deep-Copy)
- 在跨 Vault 提炼以及从本地 `sources/` 结晶时，若原始信源中有非常关键的架构图、UI 界面插图且需要展示在 Wiki 词条中：
  - **按需拉取**：仅将该图物理拷贝到本地的 `sources/attachments/` 目录下，并在 Wiki 中以 `![caption](file:///absolute/path/to/image)` 语法嵌入。
  - **拒绝冗余**：未被词条引用的多余图片一律留在原 Vault，严禁拷贝过来污染本地 attachments 目录。

### 5. 个人画像主动沉淀 (User Profiling)
- 在结晶过程中，若捕获到任何关于用户的细小信息（如开发习惯、硬件配置、主力开发机机型、生活作息、技术偏好等）：
  - **主动增量更新**：无需用户确认，主动以增量合并的方式，将这些画像事实整合更新到 `[[wiki/User]]`（我的个人档案）词条中，持续累积私人助手的记忆。
