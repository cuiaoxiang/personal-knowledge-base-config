---
name: lint
description: Scan the wiki for dead links, orphaned pages, orphaned attachments, check metadata confidence age decay, and output a diagnostics report.
---

# Lint Skill (智能自愈与体检)

本技能用于定期对整个个人知识库执行健康度扫描与自动修复，确保双链完整性、清理冗余文件并计算事实置信度的时效衰减。

## 触发方式
- 用户输入 `/lint`
- 或通过系统 Scheduled Task 定期自动触发。

## 执行步骤与规范

### 自愈运行模式划分 (Execution Modes)
- **交互模式（用户在线输入 `/lint`）**：为了最大化节省 Token 消耗并缩短执行耗时，Agent 应当使用 `run_command` 运行内置的本地分析脚本：
  `python3 .agents/skills/lint/scripts/analyze_wiki.py`
  此脚本将在毫秒级内完成死链、孤立文件、孤立图片及置信度衰减的全量扫描，并将结果返回给 Agent，避免了加载 60+ 文件对大模型上下文的严重污染。
- **定时任务模式（Scheduled Task 无人值守）**：为了确保任务不会因为等待命令行运行审批（Approve）而中途卡死，Agent **在此模式下严禁使用 `run_command` 运行任何脚本或终端命令**。所有的文件匹配、时效比对与文本自愈，必须纯粹在 Agent 的大模型上下文与推理空间内，配合安全的原生只读与编辑 API（如 `list_dir`, `view_file`, `replace_file_content`, `write_to_file`）闭环完成。

### 1. 链接与孤立页面扫描
- **死链检查**：遍历所有 `wiki/` 下的 Markdown 文件，提取所有 Obsidian Wikilinks（形如 `[[wiki/文件名]]` 或 `[[文件名]]`）。
  - 核对链入目标文件是否存在，若不存在则记为**死链**。
  - 对于死链，智能匹配相似词条名进行修复，若无法确定则记录到报告中。
- **孤立页面检查**：找出没有任何其他 Wiki 页面（或 `index.md`）链接指向的 Wiki 页面，记录到报告中。

### 2. 孤立附件清理
- 扫描 `sources/attachments/` 目录下的所有图片和附件。
- 遍历个人知识库内所有的 Markdown 文件，统计所有被引用的附件文件名。
- 若 `sources/attachments/` 中存在未被任何 Markdown 文件引用的“孤立图片”，提出将其物理删除的方案，运行 `rm sources/attachments/文件名` 并提交用户审批执行，以保持存储清洁。

### 3. 语义矛盾排查
- 检查是否存在关于同一工具或概念的冲突表述（例如不同页面写有不同的底层端口、冲突的配置指令等）。
- 基于 `last_confirmed` 时间新鲜度与置信度，给出合理的冲突解决建议，并记录于报告。

### 4. 置信度时效衰减 (Recency Decay)
- 遍历所有 `wiki/` 页面，提取 YAML Frontmatter 中的 `confidence` 和 `last_confirmed`。
- 跳过 `confidence: 1.0` 的永恒真理（如纯数学理论、绝对定理）。
- 对于 `confidence < 1.0` 的词条：
  - 计算 `last_confirmed` 距离当前系统时间的间隔。
  - 若**超过 6 个月（180 天）**未被更新/确证，则执行置信度衰减扣减（例如：每过期半年扣减 `0.1` 置信度，置信度下限为 `0.0`）。
  - 直接使用 `replace_file_content` 覆写该词条的 YAML 属性，更新 `confidence`。此操作**不需要**用户介入确认。
  - **衰减归档护栏**：若置信度因衰减而**低于 0.2**，将其标记为“待归档”状态。
    - **严禁静默归档**：必须在最终报告中列出待归档词条明细，征得用户显式 Approve 后才能执行移动/归档操作。

### 5. 诊断报告与同步重置
- 自愈完成后，将本次体检结果生成一份详细的诊断报告。
- 报告必须包含：
  - 置信度衰减统计（列出已扣减词条的旧/新置信度）。
  - 死链与孤立页面清单（及修复情况）。
  - 清理的孤立附件列表。
  - 待归档（置信度 < 0.2）的词条列表及决策差分。
- **写入报告**：使用 `write_to_file` 将报告覆写保存至知识库根目录下，命名为 `.最近一次自愈报告.md`。
- **重置时钟**：将本次成功运行的当前时间戳（格式为 `YYYY-MM-DD HH:mm:ss`）写入根目录下的 `.last_sync_time` 文件中，作为下次增量自愈的起点。
