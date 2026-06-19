---
name: scale
description: Perform global restructuring, including splitting over-large wiki pages, merging redundant entries, compiling Maps of Content (MOC), and auto-fixing all link references under user review.
---

# Scale Skill (规模化重构)

本技能用于在知识库体量增长、单文件过载或碎片化词条过多时，执行全局的架构重构，建立 MOC 并确保引用链接自愈。

## 触发方式
- 用户输入 `/scale`
- 或当某一领域的词条数量或单文件体积超出合理阈值时由 Agent 触发。

## 执行步骤与规范

### 1. 规模监测与治理策略
- **合并归类 (Merge)**：当发现多个主题重合、内容单薄的碎片化小文件时，将它们整合并入一个高密度的结构化词条中，并清理原小文件。
- **裂变拆分 (Split)**：当某一词条体积过大（例如超过 800 行）或主题不再聚焦时，将其垂直拆分为多个子词条（例如分拆为“理论/规范”与“实操/配置”）。
- **动态编译 MOC (Map of Content)**：当某一特定领域（如大语言模型、高性能计算等）的关联词条数量达到 **5 - 10 篇**时，自动编译或更新对应的 MOC 导航页面（形如 `wiki/领域名称-MOC.md`），构建逻辑上的多叉树目录。

### 2. 扁平物理护栏
- **保持物理扁平**：所有拆分、合并或新建的 Wiki 词条，必须统一保存在 `wiki/` 的一级目录下，绝对禁止使用物理子文件夹嵌套。多层级目录必须通过 Wikilinks 和 MOC 进行逻辑归类。

### 3. 自动修复双链 (Auto-fixing Links)
- 在任何合并、拆分或重命名操作后：
  - 全局扫描并遍历知识库内的所有 Markdown 文件。
  - 将所有指向旧词条名称的双链引用（例如 `[[wiki/旧名称]]`）批量安全替换为新词条引用，确保不留下任何死链。

### 4. 安全审批机制 (Safety & Implementation Plan)
- **严禁静默重构**：由于重构涉及核心资产的大规模结构变动，Agent 绝对不能在后台直接执行批量修改。
- **方案评审规范**：
  - 必须首先在 `implementation_plan.md` 助手中输出一份详细的重构实施方案。
  - 方案中需明确列出：拟合并/拆分的文件清单、新建文件命名、全局链接替换列表。
  - 将方案提请用户 Review 并点击 Approve，获得显式授权后，方可启动 native APIs 进行批量写入与修改。
