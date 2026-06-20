# 📑 LLM Wiki 架构规范 (GEMINI.md)

本文件定义了使用 LLM 智能体作为图书管理员来管理个人知识库（个人知识库）的架构模式、规则、工作流和生命周期维护策略。

---

## 🌐 全局语言与排版约定 (Global Language & Formatting Policy)
* **“中文优先”原则**：在这个知识库的所有层级中（包括文件命名、大纲标题、正文内容、MOC 目录等），除了不可翻译的专业术语或代码库原名（如 API 名称、协议、专有名词）外，必须**尽可能使用中文**作为主要语言进行创作与组织。
* **“核心文档 Emoji 标识”原则**：对于重要的全局规范、宪章等核心文档（例如 `GEMINI.md`、`SOUL.md`），必须在第一、二级标题前加上合适的 Emoji 前缀，而三级及以下子标题不加 Emoji。

---

## 📁 目录结构

知识库组织为三个核心层：

```text
个人知识库/
├── GEMINI.md          # 本规范及指令引导文件
├── index.md           # 百科词条主索引文件
├── sources/           # 原始暂存层：未处理的观测记录、剪藏和日志
└── wiki/              # 编译百科层：按实体整理的高密度结构化 Markdown 页面
```

- **`sources/` (分布式信源核心)**：`sources` 不再仅仅是一个物理文件夹，而是一个**逻辑上的数据流网络**。
  - **本地 Inbox**：作为当前知识库的本地信源池，存放 Web Clipper 剪藏、临时会话的总结 (raw data) 以及所有本地缓存的附件（如 `sources/attachments/` 下的图片）。
    - **规范 1 (文件命名)**：所有网页剪藏文章必须统一添加 `✂️` 前缀；所有对话结晶的总结必须统一添加 `💬` 前缀。
    - **规范 2 (YAML 属性)**：以上所有文件必须在 YAML Frontmatter 中包含 `tags`（如 `tags: [chat]` 或 `tags: [clippings]`）。其中，`💬` 类的对话总结必须包含 `last_modified_timestamp`（最后修改时间戳）以触发增量同步；而 `✂️` 类网页剪藏由于内容固定，保留原有的 `created`（创建日期）属性即可，无需添加最后修改时间戳。
  - **分布式外部节点**：外部 Vault（如“个人笔记”）中被授权的特定文件夹被视为逻辑挂载点。Agent 严禁向本地拷贝其文本，必须采取“物理解耦、逻辑统一”的存算分离读取架构，从而避免数据冗余。
- **`wiki/`**：包含合并提炼后的知识。其中的每个页面都对应一个具体的**实体**（项目、技术、概念、人物、决策等）。
  - **规范 1 (标题排版)**：为了保持文档整洁与自愈重构逻辑的精准，编译后的百科词条正文中的各级章节标题（`##`、`###` 等）**一律不使用数字编号前缀**（例如：必须使用 `## 核心架构`，严禁使用 `## 1. 核心架构`，但类似 `## 2026年巅峰算力` 等表示数据或年份而非章节序号的数字不在此限制内）。
- **`index.md`**：供人类阅读的 `wiki/` 页面总导航目录。

---

## ⏳ 信息生命周期与合并层级

知识随着置信度增长，在知识库内进行分层提炼：

1. **工作记忆 (Working Memory - sources/)**：未处理的原始日志、剪藏与片段。
2. **情境记忆 (Episodic Memory)**：会话或特定任务的阶段性总结。
3. **语义记忆 (Semantic Memory - wiki/)**：高密度的结构化事实、实体和关系页面，以及针对复杂主题的**综合分析报告 (Synthesis)**。
4. **程序记忆 (Procedural Memory)**：可复用的工作流和执行规范（如本规范本身）。

### 置信度与衰减
`wiki/` 中的核心事实应当包含以下元数据（可在 Frontmatter 或行内标明）：
- **置信度 (Confidence, 0.0 至 1.0)**：必须依据知识的“物理属性与衰减挥发性”进行动态定级，严禁机械式全盘打满 1.0：
  - `0.5`: 单次粗略观测或临时性脚本片段。
  - `0.85`: 高频迭代的软件生态、CLI 命令行工具最佳实践（如 Node.js, 代理配置, UI 框架）。这些知识极易随版本更迭失效，必须让其暴露在半年期的衰减扫描中。
  - `0.95`: 底层硬件架构、编译协议、稳固的物理组网机制（如 Apple Silicon 内存调度机制）。相对稳定，但仍受代际更替影响。
  - `1.0`: 永恒真理或绝对固化的领域常识（如纯数学理论、算法基石）。它们对时间戳免疫，衰减扫描将永久跳过此类节点。
- **时效衰减 (Recency Decay)**：超过 6 个月未被确证或检索的边缘事实，其置信度将逐渐调低。具体通过“主动扫描”（自愈维护时全盘扫描）或“惰性计算”（加载/编辑特定词条时判断时间差）来触发更新。**任何由衰减引起的属性修改（置信度、确认日期等）可由 Agent 自动写入；但若因置信度过低而触发归档操作，必须呈报详细差分，获得用户的 Review 与 Approve 后方可执行。**
- **版本更替 (Supersession)**：当新观测与旧结论矛盾时，将旧事实标记为 stale（过期）并进行双链链接，激活新结论。
- **元数据更新同步准则 (Metadata Sync)**：
  - 凡是词条的正文发生了**事实性的增补、修改或合并 (Incremental Ingest)**，在提交修改时，**必须同步将 YAML 头部中的 `last_confirmed` 字段更新为当前实际执行维护的日期**（格式为 `YYYY-MM-DD`），以重置该词条的时效衰减计时器。
  - 对于**纯格式美化、错别字修正或非事实性的纯结构重构 (Refactor)**，应当**保持原有的 `last_confirmed` 日期不变**，防止因无实质影响的修改刷新时钟，进而掩盖核心技术事实本身的陈旧性。

---

## 🕸️ 知识图谱与实体提取

编译原始资料时，需提取结构化实体并记录其类型化的关联：

### 实体类型 (Entity Types)
- **Project (项目)**：正在进行的具体事情（例如 "希望杯打卡", "授权迁移"）。
- **Library (技术/工具)**：软件、框架、工具（例如 "C++23", "Obsidian"）。
- **Concept (概念)**：理论想法、学术概念或架构模式。
- **Person (人物)**：相关合作者、负责人或相关人士。
- **Decision (决策)**：架构选型、设计决策或排查决议。
- **Synthesis (综合)**：针对复杂问题、多维度主题或研究方向生成的深度综合报告（派生知识）。

### 关系类型 (Typed Relationships)
使用带有显式动作含义的双链来表示实体间的关系：
- `uses` / `depends on`（使用 / 依赖）
- `supersedes` / `replaces`（替代 / 更替）
- `caused` / `fixed`（导致 / 修复）
- `contradicts`（矛盾）

---

## ⚙️ 工作流说明

为了实现知识库的高效自愈与整洁，我们将具体的操作步骤与指令解耦为独立的 Agent 技能（Skills），并在日常交互中通过指定的前缀命令进行调用。

### 暂存层 (sources/) 防碎片化规范
为防止 `sources/` 目录随着时间推移堆积大量零碎文件，导致知识检索困难，系统在生成源文件时必须严格遵守以下三种防碎片化策略：
1. **采用“主题滚动日志 (Rolling Log)”机制**：对于持续性、同一主题的长期探究（如架构设计、系统调试），不新建文件。新讨论的内容以 `## YYYY-MM-DD 更新` 的形式追加（Append）到现有的相关滚动日志末尾。
2. **微小更新直接“直达 Wiki (Bypass)”**：对于几句话的微小纠错或单一知识点补充，彻底跳过 `sources/` 层的暂存，直接在 `wiki/` 层修改对应词条，保持系统整洁。
3. **大型信源独立建档**：只有通过 Web Clipper 剪藏的长篇外部文章、长篇 PDF，或长达数小时的重大 Debug 完整归档，才允许在 `sources/` 下独占建立一个独立的文件。

### Ingest (智能录入 - /ingest)
- **触发命令**：`/ingest <file_path>` 或 *“帮我录入 sources/文件名”*
- **核心政策**：自动处理 `sources/` 下的原始文件，提炼实体并写入 `wiki/`，同时**必须自动将处理后的原文件移入 `sources/processed/` 已处理目录**。
- **具体执行步骤**：参见 [ingest/SKILL.md](.agents/skills/ingest/SKILL.md)。

### Query (知识检索)
- **核心策略**：优先搜索 `wiki/` 目录下的结构化词条，如果信息不足，再在 `sources/` 中查找原始细节。结合词条的双链关联关系，做上下游实体的关联推荐。

### Lint (日常自愈维护 - /lint)
- **触发命令**：`/lint` 
- **核心政策**：定期对知识库健康度进行扫描，修复断链、清理孤立附件。执行**时效衰减机制**（对 last_confirmed 超过半年的词条降低置信度，但归档操作需呈报）。
- **具体执行步骤**：参见 [lint/SKILL.md](.agents/skills/lint/SKILL.md)。

### Crystallize (会话结晶 - /crystallize)
- **触发命令**：`/crystallize` 
- **核心政策**：当完成复杂研究或排错后，提炼经验并存入 `wiki/`（可生成 `type: synthesis` 的深度报告或更新对应词条）。在此过程中，必须严格遵守**跨 Vault 存算分离准则 (Cross-Vault Read-Only)** 以及 **按需深拷贝插图 (On-Demand Deep-Copy)**，并自动对 **个人画像进行沉淀 (User Profiling)**。
- **具体执行步骤**：参见 [crystallize/SKILL.md](.agents/skills/crystallize/SKILL.md)。

### Scale (规模化重构 - /scale)
- **触发命令**：`/scale` 
- **核心政策**：当词条数量过多时，执行 Split/Merge 重构或动态更新 MOC。涉及大规模变动时，必须先出具 Implementation Plan 供用户 Review 和 Approve。词条必须保持**物理扁平**（统一存放在 `wiki/` 一级文件夹内）。
- **具体执行步骤**：参见 [scale/SKILL.md](.agents/skills/scale/SKILL.md)。

## 🛡️ 知识库系统边界与防污染准则 (Strict Boundaries & Anti-Hallucination)

在知识库的架构演进与结晶过程中，Agent 必须绝对遵守以下护栏原则，严禁越界：

1. **绝对信源依赖 (Anti-Hallucination / 严禁夹带私货)**：
   - Agent 的核心身份是“秘书”与“提炼引擎”，而非“百科全书”。
   - 任何在 `wiki/` 词条中生成的知识、操作指令或经验，**必须 100% 来源于 `sources/` 下的原始文献**。严禁 Agent 动用大模型底层预训练的常识（如擅自补写 Mac 终端命令、代码最佳实践）进行知识“扩写”或“脑补”。没有观测到的事，绝对不能写进系统。
2. **系统元文件不可污染 (Meta-Files Isolation)**：
   - 系统级的入口文件（如 `README.md`）具有特殊的占位与锚点意义。它仅用于定义文件夹作用、全局元数据结构（Metadata Template）。
   - 严禁将业务内容文件（如讨论架构思想的 `LLM-Wiki-v2.md`）强行合并到 `README.md` 中。保持“规则定义（Schema）”与“内容沉淀（Content）”的物理隔离。
3. **命令行与脚本限制 (Command-Line & Script Restrictions)**：
   - **允许使用只读命令**：在定位新增/修改文件或获取其修改时间时，允许且仅允许使用无副作用的只读命令（例如 `find`、`stat`），以便高效准确地查询文件元数据（如 `mtime`）。
   - **严禁使用副作用命令及脚本**：严禁调用任何具有文件修改、删除或写入副作用的终端命令（如 `rm`、`sed`、`awk`、`tee` 等），并且绝不能编写或运行 Python、Bash 等脚本来进行自动化处理。
   - **原生 API 优先**：任何关于个人知识库内文件内容的读取、编辑或更新，必须严格通过 Antigravity 的原生 API（例如 `replace_file_content`、`write_to_file` 等）安全完成。


---

## 🧠 吞吐量与认知边界 (Cognitive Limits & Batching)

为了避免 Agent 在处理大量原始文献时发生上下文过载（Context Overflow）、幻觉增加以及“贪多嚼不烂”导致的提炼质量下降，系统在进行 Ingest 和 Scale 归档时必须严格遵守分批处理上限：

1. **单次处理总行数上限**：每次执行归档（Crystallize）任务时，Agent 一次性读取并处理的 `sources/` 源文件总行数**不得超过 1000 行**（或物理文件大小约 40KB - 50KB）。
2. **单次文件数量上限**：每次归档周期的源文件数量建议控制在 **2 - 4 个** 以内。
3. **强制分批（Batching）**：当遇到包含 5 个以上文件或总行数远超 1000 行的目录归档指令时，Agent **必须主动拒绝一次性吞入**。Agent 需自行制定“分批实施方案（Batch Implementation Plan）”（例如：Batch 1 处理硬件相关，Batch 2 处理软件配置），并在每完成一个 Batch 后清理上下文，再向用户请求继续执行下一个 Batch。

---

## ⏰ 附录 A：知识库的两个 Cronjob

本附录用于安全存放系统级的自动化脚本代码。将它们写在这里，能够确保随着 Git 白名单机制一同备份至云端，在物理设备损坏时快速重建整个生命周期维护流水线。

### A.1 系统的 Crontab

**安装部署方式**：
直接在 macOS 终端复制并执行以下单行命令（使用了 Bash 隔离防止 Shell 转义冲突）：

```bash
bash -c '(crontab -l 2>/dev/null; echo "0 12 * * 0 cd \"$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/个人知识库\" && git add GEMINI.md SOUL.md wiki/README.md sources/README.md .agents/ .gitignore && git commit -m \"chore: weekly auto-sync\" && git push -q") | crontab -'
```

### A.2 Antigravity 的 Scheduled Task

依赖 Antigravity Manager 的大模型调度能力，负责执行高度智能化的 Lint（日常体检、时效衰减）与 Scale（词条合并、MOC 导航）任务。

**部署方式**：
通过 `/schedule` 唤醒 Agent，并下达对应的 Prompt；或者在 Antigravity 界面侧边栏的 Scheduled Tasks 模块里直接添加。

- **Cron 表达式**: `0 0 * * *` (每日凌晨 0:00)
- **Prompt**: 
  ```text
  请前往 /Users/cuiaoxiang/Library/Mobile Documents/iCloud~md~obsidian/Documents/个人知识库 下的“LLM 学习”和“码农的自我修养”这两个目录，执行日常自愈维护。

  ⚠️【重要：会话命名规则】
  启动后，请立即将当前会话的标题命名为 `🌙YYYY/MM/DD`（请根据当前实际执行任务的时间动态替换，例如：`🌙2026/06/12`）。

  ⚠️【执行限制】
  【严禁运行 Python 脚本或任何具有文件写入/删除/修改副作用的终端命令（如 rm, sed, awk 等）】。仅允许调用只读元数据查询命令（如 stat, find 等）。对于本库内容的增删改，必须纯粹利用原生的编辑 API，通过依次调度自定义技能来完成以下工作：

  1. **本库体检 (Lint)**：运行 `/lint` 技能对本库进行自愈检查，完成死链修复、孤立附件清理和置信度时效衰减。
  2. **外部 Vault 知识同步**：严格且仅限扫描外部 Vault 的以下两个白名单目录：
     - /Users/cuiaoxiang/Library/Mobile Documents/iCloud~md~obsidian/Documents/个人笔记/LLM 学习
     - /Users/cuiaoxiang/Library/Mobile Documents/iCloud~md~obsidian/Documents/个人笔记/码农的自我修养
     读取本库根目录下的 `.last_sync_time` 隐藏文件（记录上次自愈维护成功的时间戳）。若不存在，则默认扫描最近 24 小时内有更新的内容；若存在，则扫描自该时间戳以来有更新或新增的内容（遵循跨 Vault 只读准则，采用 obsidian:// 协议溯源），提取新知识并同步更新到本库的 Wiki 层。
  3. **架构重构 (Scale)**：运行 `/scale` 技能，若某一垂直领域的关联词条数量达到 5-10 篇，自动编译或更新该领域的 MOC 页面，并自动修复所有双链引用。
  4. **生成诊断报告**：自愈维护完成后，自动生成一份本次自愈维护的诊断报告（包含置信度衰减统计、死链修复清单、外部知识库同步提取的词条与摘要，以及本次新增 MOC 规划）。**务必使用 write_to_file 将该报告覆写保存至当前知识库根目录下，强制命名为 `.最近一次自愈报告.md`**，同时，将本次成功运行的当前时间戳（格式为 YYYY-MM-DD HH:mm:ss 或 Unix 时间戳）写入本库根目录下的 `.last_sync_time` 文件中，以重置增量同步起点。
  ```
