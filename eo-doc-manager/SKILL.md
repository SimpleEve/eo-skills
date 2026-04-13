---
name: eo-doc-manager
description: |
  Manages eo-doc/ project documentation. All doc operations MUST go through this skill.

  USE FOR:
  - "初始化文档" "文档体系" "init docs" — initialize doc structure
  - "同步文档" "sync docs" "更新文档" — sync docs from git diff
  - "重建文档" "re-sync" — full doc rebuild
  - "整理资料" "结构化" "解析文档" — structure raw materials
  - "查文档" "query docs" — search docs by tag/keyword
  - Any mention of documentation management, INDEX.md, design spec, or eo-doc
---

# eo-doc-manager

项目文档全生命周期管理。五层文档体系，统一存放于 `eo-doc/`，AI 检索优化。

## 命令路由

收到指令后，解析意图并路由到对应子流程：

| 命令 | 触发词 | 流程 |
|------|--------|------|
| `init` | 初始化文档、init docs | 创建 eo-doc/ 目录结构 + 各目录 INDEX.md 骨架 |
| `modify` | 修改文档、结构化、解析、整理 | 解析目标 → 分流到对应目录 → 读取/创建 → 更新 INDEX.md |
| `sync` | 同步文档、sync docs、更新文档 | git diff 增量 → 同时更新 doc/ + agent-handbook/ + design impl_status |
| `re-sync` | 重建文档、全量同步 | 扫描全部源码 → 重建 doc/ + agent-handbook/（不覆盖 design/） |
| `select` | 只操作 design/、select agent-handbook | 缩小操作范围到指定目录 → 执行后续命令 |
| `query` | 查文档、有没有关于 X 的 | 扫描所有 INDEX.md → 按 tag/keyword 匹配 → 返回结果 |

**路由规则**：
1. 若用户给出明确命令（如 `/eo-doc-manager sync`），直接路由
2. 若自然语言触发，按触发词匹配命令
3. 若无法判断意图，列出可用命令让用户选择

## 目录结构

所有文档统一存放在项目根目录的 `eo-doc/` 下：

```text
eo-doc/
├── INDEX.md              # 顶级索引，跨目录导航汇总
├── templates/            # 项目定制模板（eo-* 技能扩展点）
│   ├── project-profile.md
│   ├── spec-layers.md
│   ├── plan-layers.md
│   └── implement-layers.md
├── dev/                  # 功能开发文档（spec/plan/review 产出）
│   └── INDEX.md
├── design/               # 源设计
│   └── INDEX.md
├── doc/                  # 当前实现
│   └── INDEX.md
├── agent-handbook/       # 代码架构
│   └── INDEX.md
├── research/             # 调研资料
│   └── INDEX.md
└── knowledgebase/        # 知识库
    └── INDEX.md
```

## 目录职责

| 目录 | 职责 | 面向 | 核心问题 | type 值 |
|------|------|------|----------|---------|
| `templates/` | 项目定制模板 — eo-* 技能的扩展点，定义项目类型、层级结构、工作流定制 | AI | "项目**怎么**定制？" | — |
| `dev/` | 功能开发文档 — 每个功能的 spec/plan/review/implement 产出 | 都 | "功能**开发**到哪了？" | — |
| `design/` | 源设计 — 期待的规划、spec、功能定义、架构蓝图 | 人 | "我们**想要**怎么做？" | `design` |
| `doc/` | 当前实现 — 系统实际做了什么，业务规则、状态流转、配置 | 人 | "系统**现在**是什么样？" | `doc` |
| `agent-handbook/` | 代码架构 — 模块入口、接口索引、依赖关系、目录结构 | AI | "代码**怎么**组织的？" | `agent` |
| `research/` | 调研资料 — 竞品分析、市场调研、技术评估 | 都 | "外部**现状**是什么？" | `research` |
| `knowledgebase/` | 知识库 — 行业知识、技术规范、最佳实践 | 都 | "通用**知识**是什么？" | `knowledgebase` |

### 关键区分

**design vs doc**：
- design = 愿景、规划、"应该做什么"（可能还没实现）
- doc = 事实、现状、"已经做了什么"（必须与代码一致）
- 同一个功能：design 里是 spec，doc 里是实现现状

**doc vs agent-handbook**：
- doc = 给人看的系统描述（业务规则、状态流转、配置含义）
- agent-handbook = 给 AI 看的代码地图（文件入口、接口签名、依赖关系、调用示例）
- doc 回答"系统做了什么"，agent-handbook 回答"代码在哪里、怎么调用"

**design vs research**：
- research = 观察、分析、比较（输入信息，不做决策）
- design = 决策、规划、定义（基于调研结论做出的项目方案）

**templates/**：
- 不是文档，是 eo-* 技能的扩展点
- 定义项目类型（project-profile）、多层对齐模板（spec-layers）、分层 Part 模板（plan-layers）、分层执行模板（implement-layers）
- 模板文件可选创建，不存在时 eo-* 技能使用内置默认行为
- eo-doc-manager 的 sync/re-sync 不处理 templates/（它们不是从源码生成的）

**dev/**：
- 功能开发文档的集合，每个功能一个子目录（如 `dev/user-auth/`）
- 子目录内由 eo-spec、eo-plan、eo-implement、eo-review 等技能按约定产出
- dev/ 不参与 sync/re-sync，由开发流程技能管理

## 代码优先原则

doc/ 和 agent-handbook/ 的内容必须从**源码**生成，不是从已有文档迁移。原因：已有文档可能过时、遗漏或与代码不一致，如果直接搬运就失去了文档管理的意义——我们要的是"代码的真实状态"，不是"旧文档说的状态"。

**正确路径**：读源码 → 提取模块/接口/规则 → 生成文档 → 最后参考旧文档补充人工业务背景

**禁止路径**：读旧文档 → 改格式/改名 → 放入 eo-doc/（这是迁移，不是生成）

此原则适用于 init 和 re-sync。sync 是增量更新，不受此约束。

## doc/ 写作规范（重要）

doc/ 不是"代码说明书"，而是**给人看的玩法/业务规格文档**。只描述"这个模块做什么、有什么规则"，不贴代码、不贴文件路径。

### 粒度：按业务模块拆，不按技术模块

- **业务模块** = 产品/业务视角的功能单元（玩家、用户、策划、运营能理解的词）
- **技术模块** = 代码层视角的拆分单元（按端/按子系统/按目录）——这是 agent-handbook/ 的职责，**不要**用在 doc/
- 子系统内有多种显著不同的子类型时，每个子类型独立一篇（游戏类项目的例子：建筑系统可拆为「建造」通用机制 +「民居」+「消防站」+「生产建筑」+「仓库」等）
- 每篇聚焦一个模块。若模块跨端/跨层（如 Unity + Server），在同一篇里合并描述业务规则，不按端拆

### 风格：规格说明体（spec-style）

- 用业务语言写给人看（产品/策划/业务方），不是写给开发者的 API 说明
- **允许**引用配置表名、字段名、枚举值作为术语（它们是规则的固定锚点）
- **禁止**贴代码路径、类名、文件名、方法签名、代码片段（那些是 agent-handbook/ 的事）
- **禁止写死具体数值**。数值会频繁调整，文档写死会很快过时。规则用"**由 `XxxConfig.FieldName` 决定**"这种方式描述
  - ✅ 正确：`民居每日消耗由 HouseConfig.WaterCost 与 HouseConfig.FoodCost 决定`
  - ❌ 错误：`民居每日消耗 2 水和 3 食物`
  - ❌ 错误：`起火阈值 FireThreshold=30` — 写成 `起火阈值由 FireStationConfig.FireThreshold 决定`
- 公式、优先级、时序、边界条件**要描述清楚**"怎么算"和"谁优先"，但其中的具体数字用字段引用代替
- 枚举值名、常量名、字段名可以保留（它们是"术语"），但伴随的具体数字不要写
- 对尚未实现的规则，标注 `**TODO：<原因>**`

### 结构骨架（每篇 doc 统一采用）

```markdown
---
title: <模块名>
type: doc
tags: [<领域>, <模块>, ...]
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
summary: >
  一句话说明这个模块是什么、承担什么业务职责。
---

# <模块名>

## 1. 概述
- 功能简述：一句话业务定位
- 所属系统：上位系统（如"建筑系统的子模块"）
- 关联配置：列出本模块读取的配置表（表名 + 职责）
- 关联模块：简列与本模块有交互的其他业务模块（链接到对应 doc）

## 2. 核心玩法 / 核心流程
从使用者视角描述"这个模块怎么运作"。包含：
- 使用者能对这个模块做什么动作
- 模块自身有什么状态/产出/消耗
- 典型的使用流程（几条主线）

## 3. 规则与参数
具体规则、数值、时序、优先级、边界条件。按小节拆：
- 3.1 <子规则1>（步骤化/条件化描述）
- 3.2 <子规则2>
- ...

## 4. 与其他模块的交互
以本模块为中心，描述它向其他模块**发起**什么、从其他模块**接收**什么。
用表格或列表，不画架构图。

## 5. 当前未实现 / TODO
代码里没做、但规则已定或部分定的项，标注原因（如依赖未完成的子系统）。
```

**不要**保留"用户故事"章节（那是 spec 的未来愿景视角）。doc/ 写的是现状。

### 数据来源优先级

1. 代码实际行为 — 规则与参数的第一来源
2. 配置表 / 数据定义文件 — 数值、枚举、优先级的来源
3. 协议/接口定义 — 字段约束、状态枚举的来源
4. 旧文档（含 agent-handbook/、dev/*/spec.md 等） — 仅补充"代码无法推断的业务背景"（如为什么这样设计），**不得**复制其技术描述

## 核心工作流

### init — 初始化文档体系

1. 检查项目根目录是否已有 `eo-doc/`
2. 若已存在，报告现状并询问是否需要补全缺失目录
3. 若不存在，创建完整目录结构 + 各目录 INDEX.md 骨架
4. 创建 `eo-doc/templates/` 目录（空目录，不自动生成模板文件；模板由用户按需创建）
5. 创建 `eo-doc/dev/` 目录 + INDEX.md（功能开发文档索引）
6. 创建顶级 INDEX.md（跨目录汇总索引）
7. 初始化 `eo-doc/.sync-cursor`（记录当前 HEAD 作为首次基线）
8. 将 `eo-doc/.sync-cursor` 追加到 `.gitignore`（本地状态，不提交）
9. **更新 CLAUDE.md — 注入 eo-doc 文档体系描述**（见下方"CLAUDE.md 注入规则"）
10. **从源码生成 doc/ 和 agent-handbook/**（遵守代码优先原则）：
   a. 分析项目根目录结构，识别源码目录、入口文件和模块边界
   b. **枚举所有业务模块**：遍历 `src/lib/`（或等效源码目录）下的子目录和独立功能域，输出模块清单（如 `opportunities`、`analysis`、`tasks`、`contentDigest` 等）
   c. **按模块生成 agent-handbook/**：模块清单中每个模块独立一篇，文件名与模块目录名对应（参考 [splitting.md](references/splitting.md) 的拆分模式）。禁止用横切面汇总文档（如 directory-map、module-boundaries、persistence-architecture）替代模块文档。仅允许 `overview.md`（技术栈+目录结构速查）和 `entrypoints.md`（页面/API/Action 索引）作为辅助入口，不可将模块内容塞入这两篇
   d. **按业务模块生成 doc/**：严格遵守 SKILL.md「doc/ 写作规范」——粒度按业务模块（非技术模块）、规格说明体风格、统一结构骨架、不贴代码
   e. 若项目中已有旧文档，仅提取其中"代码无法推断的业务背景描述"合并进来
   f. 旧文档中的接口描述、模块结构等技术内容一律以源码为准，不复用

### modify — 修改/创建文档

1. **分析输入**：识别输入类型（单篇/多篇/更新已有）
2. **分流**：判断每段内容归属哪个目录（参考 [splitting.md](references/splitting.md)）
3. **拆分**：在目录内按主题拆分（参考 [splitting.md](references/splitting.md)）
4. **结构化**：按模板格式化（参考 [templates.md](references/templates.md)）
5. **更新 INDEX.md**：同步目录级和顶级索引
6. **验证**：frontmatter 完整、INDEX 对应、行数达标

### sync — 增量同步

基于 git diff 将代码变更同步到文档。参考 [git-sync.md](references/git-sync.md)。

通过 `eo-doc/.sync-cursor` 记录上次同步的 commit hash，确保不遗漏变更：
1. 读取 `.sync-cursor` 获取上次同步点
2. `git diff <last_commit>..HEAD` 获取已提交变更 + 未提交变更
3. **同时更新三个目标**：
   - `doc/`：更新"系统现在是什么样"（业务规则、状态、配置）
   - `agent-handbook/`：更新"代码怎么组织的"（入口、接口、依赖）
   - `design/`：对比变更，更新 `impl_coverage` 和实现状态表格
4. 同步所有受影响的 INDEX.md
5. 更新 `.sync-cursor` 为当前 HEAD
6. 汇报变更结果

### re-sync — 全量重建

不基于 diff，全量扫描源码重建。参考 [re-sync.md](references/re-sync.md)。

1. 扫描项目全部源码
2. **重建** doc/ 和 agent-handbook/（清空后重新生成）
3. **不覆盖** design/、research/、knowledgebase/（这些是人写的）
4. 对 design/ 仅更新实现状态标注
5. 重建顶级 INDEX.md
6. **更新 CLAUDE.md — 重新注入 eo-doc 文档体系描述**（见下方"CLAUDE.md 注入规则"）
7. 重置 `.sync-cursor` 为当前 HEAD（建立新基线）

### select — 选择性操作

1. 解析用户指定的目录范围
2. 将后续命令的作用域限制到指定目录
3. 可与 sync/modify 组合：`select doc sync`（只同步 doc/）

### query — 查询文档

1. 读取所有 INDEX.md
2. 按 tag、关键词、文件名匹配
3. 返回匹配结果：文件路径 + 摘要 + 相关度
4. 若匹配多个，按相关度排序展示

## design 实现状态追踪

design/ 文档通过两个机制追踪实现进度：

### frontmatter 汇总信号

```yaml
impl_coverage: 2/5    # 已实现数 / 总 feature 数
```

一眼看出整体进度，用于 AI 分流判断。

### 正文实现状态表

```markdown
## 实现状态

| Feature | 状态 | 关联文档 | 备注 |
|---------|------|----------|------|
| 任务状态机 | ✅ implemented | [task-engine](../doc/task-engine.md) | |
| 优先级队列 | 📋 planned | | v2.0 规划 |
| 失败重试 | 🔶 partial | [task-engine](../doc/task-engine.md) | 仅固定间隔 |
```

状态值：`✅ implemented` / `🔶 partial` / `📋 planned`

`sync` 和 `re-sync` 时自动对比 design 和实际代码，更新此表。

## 结构化规则

### Frontmatter（YAML）

```yaml
---
title: 简明标题
type: design | doc | agent | research | knowledgebase
tags: [tag1, tag2, tag3]
created: YYYY-MM-DD
updated: YYYY-MM-DD
scope: 一句话适用范围
status: draft | active | archived
source: 原始链接或项目内部路径
summary: >
  1-2 句核心摘要，AI 靠这个决定是否读全文。
conclusions:
  - 关键结论1
  - 关键结论2
impl_coverage: 2/5    # 仅 design 类型文档需要
---
```

### 正文结构

1. 上下文段落（2-3 句，何时/为何重要）
2. `##` 结构化章节，各章节自包含、可独立扫读
3. 事实用列表，分析用短段落，对比用表格
4. 底部来源引用

参考 [templates.md](references/templates.md) 获取各类型完整模板。

### 拆分规则

参考 [splitting.md](references/splitting.md) 获取分流决策、拆分模式、命名规范。

## INDEX.md 规范

### 目录级 INDEX.md

```markdown
# [分类名] Index

> Last updated: YYYY-MM-DD
> Total: N docs

| File | Title | Tags | Updated | Summary |
|------|-------|------|---------|---------|
| [filename.md](filename.md) | 标题 | `tag1` `tag2` | YYYY-MM-DD | 一句摘要 |
```

超过 10 篇时按子分类分组。

### 顶级 INDEX.md

```markdown
# eo-doc Index

> Last updated: YYYY-MM-DD

## design/ — 源设计
| File | Title | impl_coverage | Updated | Summary |
|------|-------|---------------|---------|---------|
| [feature-x.md](design/feature-x.md) | Feature X 设计 | 2/3 | YYYY-MM-DD | 摘要 |

## doc/ — 当前实现
| File | Title | Tags | Updated | Summary |
|------|-------|------|---------|---------|

## agent-handbook/ — 代码架构
| File | Title | Tags | Updated | Summary |
|------|-------|------|---------|---------|

## research/ — 调研资料
| File | Title | Tags | Updated | Summary |
|------|-------|------|---------|---------|

## knowledgebase/ — 知识库
| File | Title | Tags | Updated | Summary |
|------|-------|------|---------|---------|
```

## CLAUDE.md 注入规则

init 和 re-sync 时，在项目 CLAUDE.md 中维护一个标记段落，让所有 agent/skill 自动获得 eo-doc 上下文。

### 注入位置

- 在 CLAUDE.md 中查找 `<!-- eo-doc:start -->` 和 `<!-- eo-doc:end -->` 标记
- 若标记存在 → 原地替换标记之间的内容
- 若标记不存在 → 在 CLAUDE.md 末尾追加整个标记段落

### 注入内容模板

```markdown
<!-- eo-doc:start -->
## eo-doc 文档体系

> **⚠️ 重要**：开始任何任务前，必须先阅读 [eo-doc/INDEX.md](eo-doc/INDEX.md) 了解项目文档全貌。

项目文档根目录：`eo-doc/`，[完整索引](eo-doc/INDEX.md)。

| 目录 | 用途 | 何时读 |
|------|------|--------|
| [design/](eo-doc/design/INDEX.md) | 初始设计、功能定义、架构蓝图 | 了解功能"想怎么做" |
| [doc/](eo-doc/doc/INDEX.md) | 业务规则、状态流转、系统现状 | 了解功能"现在是什么样" |
| [agent-handbook/](eo-doc/agent-handbook/INDEX.md) | 代码架构、模块入口、接口索引 | 看代码前先读，找准入口和边界 |
| [dev/](eo-doc/dev/INDEX.md) | 功能开发文档（spec/plan/review） | 了解功能"开发到哪了" |
| [research/](eo-doc/research/INDEX.md) | 调研资料、竞品分析 | 做决策前参考 |
| [knowledgebase/](eo-doc/knowledgebase/INDEX.md) | 行业知识、最佳实践 | 需要领域知识时 |
| [templates/](eo-doc/templates/) | 项目定制模板（eo-* 技能扩展点） | eo-* 技能启动时自动读取 |
<!-- eo-doc:end -->
```

### 注入规则

1. 只列出实际存在的目录（如 research/ 不存在就不列）
2. INDEX.md 链接指向对应目录的索引文件
3. 内容从实际目录扫描生成，不硬编码
4. 标记注释（`<!-- eo-doc:start/end -->`）不可删除，用于后续幂等更新

## 验证清单

每次操作后：
- [ ] 每篇文档 frontmatter 完整
- [ ] 目录级 INDEX.md 与目录内文档一一对应
- [ ] 顶级 INDEX.md 汇总准确
- [ ] 单篇不超 500 行（超出建议拆分）
- [ ] 标签体系统一（无近义重复）
- [ ] 所有交叉引用指向真实存在的文件
- [ ] design 文档的 impl_coverage 与实现状态表一致

## Token 效率准则

- frontmatter summary 让 AI 不读全文即可判断相关性
- conclusions 数组支持快速提取要点
- INDEX.md 表格每条约 50 token，可一次扫描整个集合
- `##` 扁平结构，避免深层嵌套
- 事实用列表，删除填充短语

## 维护协议

参考 [maintenance.md](references/maintenance.md)：
- 更新工作流（新增/修改/批量导入）
- design↔doc 一致性检查
- 臃肿检测与重组
- 归档流程
