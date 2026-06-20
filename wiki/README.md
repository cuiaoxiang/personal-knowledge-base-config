# 知识百科库 (Wiki)

此文件夹存放经过 AI Agent 过滤、合并和提炼的结构化高密度百科页面（作为知识库的 Semantic Memory 层）。

### 实体与页面类型
本文件夹下的笔记包含**基本实体 (Entity/Concept)** 和**派生知识 (Derived Knowledge)**：
- 🛠️ **技术/工具 (Library)**：例如 `Obsidian.md`, `C++23.md`
- 📂 **项目 (Project)**：例如 `希望杯打卡项目.md`
- 💡 **概念/架构 (Concept)**：例如 `LLM-Wiki-v2.md`
- 👤 **人物 (Person)**：例如相关联系人、技术专家
- ⚖️ **决策/设计 (Decision)**：系统架构选型、调试决议
- 💎 **综合分析 (Synthesis)**：针对复杂问题或研究方向生成的深度综合报告（派生知识）

### 百科页面标准模板 (Metadata)
所有被编译出的 Wiki 词条页面，其头部均会带有规范的元数据，用以追踪类型、置信度、确认时间以及原始文献出处：

```yaml
---
type: Library | Concept | Person | Project | Decision | Synthesis
confidence: 0.85     # 置信度 (0.0 到 1.0)；年份/定理等常识固定为 1.0；技术生态等随时间而衰减
last_confirmed: 2026-06-09  # 最近一次核实的时间
sources:
  - "[[sources/clippings/✂️ obsidian-setup.md]]"  # 链接回原始证据链
---

# 实体名称

## 概述
简短的实体介绍...

## 关联关系
- `[[C++23]]` (uses)
- `[[CUIAOXIANG]]` (owner)

## 核心内容与规则
具体的结构化知识点...
```

### 维护规范
- **合并而非堆砌**：如果新获得的知识和已有实体有关，Agent 会将其作为追加或修改合并到已有实体页面，而不是创建一堆零碎的独立文件。
- **图谱互联**：页面之间会通过 Obsidian 的 Wikilinks（如 `[[C++23]]`）互联，并显式标注关系。
