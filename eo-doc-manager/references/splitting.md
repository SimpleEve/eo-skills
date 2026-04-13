# 拆分策略指南

## 分流决策（先分流、再拆分）

处理输入材料时，第一步是判断每段内容归属 `eo-doc/` 下的哪个目录。

### 五层分流规则

| 判断维度 | design/ | doc/ | agent-handbook/ | research/ | knowledgebase/ |
|----------|---------|------|-----------------|-----------|----------------|
| **核心动作** | 规划、定义、决策 | 描述现状、记录事实 | 索引代码、映射结构 | 观察、分析、比较 | 沉淀知识、整理规范 |
| **核心问题** | "想要怎么做？" | "现在是什么样？" | "代码在哪里？" | "外部现状如何？" | "通用知识是什么？" |
| **面向** | 人 | 人 | AI | 都 | 都 |
| **与代码关系** | 可能未实现 | 必须与代码一致 | 必须与代码一致 | 无直接关系 | 无直接关系 |
| **典型动词** | 设计、定义、规划 | 实现了、支持、目前 | 入口、导出、依赖 | 调研、对比、评估 | 规范、原则、流程 |

### 边界场景判断表

| 内容场景 | 归属 | 判断理由 |
|----------|------|----------|
| "我们计划支持多租户架构，设计如下" | **design/** | 规划中的设计方案 |
| "系统目前支持单租户，数据隔离通过 tenantId 字段实现" | **doc/** | 当前实际实现的描述 |
| "多租户入口 src/lib/tenant.ts，导出 getTenant()、validateTenant()" | **agent-handbook/** | 代码定位信息 |
| "市场上 SaaS 多租户方案有 A/B/C 三种" | **research/** | 外部调研分析 |
| "多租户数据隔离最佳实践：行级隔离 vs 库级隔离" | **knowledgebase/** | 通用技术知识 |

### design vs doc 关键区分

| design/ | doc/ |
|---------|------|
| "应该做什么"（愿景） | "已经做了什么"（事实） |
| 可以包含未实现的功能 | 只描述已实现的功能 |
| 允许模糊或概念性描述 | 必须精确反映代码行为 |
| 人工编写和维护 | sync/re-sync 可自动生成 |
| 有 impl_coverage 追踪 | 无（本身就是实现记录） |

### doc vs agent-handbook 关键区分

| doc/ | agent-handbook/ |
|------|-----------------|
| 给人阅读 | 给 AI 消费 |
| 业务语言描述 | 代码语言描述 |
| "系统支持三种任务状态：待执行、执行中、已完成" | "TaskStatus 枚举定义在 src/lib/types.ts:15，值为 pending/running/done" |
| 描述规则和流转逻辑 | 描述文件路径、函数签名、导出关系 |
| 不关心代码在哪 | 必须精确到文件和行号 |

### 跨目录拆分

当一份原始材料同时包含多种类型时，按内容段落拆到不同目录：

```
原始文档: "任务引擎设计与实现.md"

拆分为:
→ eo-doc/design/task-engine-spec.md
  （功能规格、架构蓝图、未实现的规划）
→ eo-doc/doc/task-engine.md
  （当前实现的业务规则、状态流转、配置）
→ eo-doc/agent-handbook/task-engine.md
  （模块入口、接口签名、依赖关系、调用示例）

各自的 INDEX.md 都要更新。三份文档互相交叉引用。
```

## 决策树

```
输入材料
├── 单一主题，< 500 行 → 单篇文档
├── 单一主题，> 500 行 → 按子主题/方面拆分
├── 多个主题 → 按主题拆分
├── 混合类型（含多种目录内容） → 跨目录拆分
└── 更新已有文档
    ├── 已有 INDEX.md → 沿用已有模式
    ├── 已有文档合并后将超 500 行 → 建议拆分
    └── 已有模式中单文档涵盖 3+ 无关主题 → 建议重组
```

## 各类型拆分模式

### design/（源设计）

按 **设计维度** 拆分。注意：design 放规划和决策，不放实现现状。

| 模式 | 示例文件 |
|------|----------|
| 产品定义 | `product-positioning.md`、`roadmap.md` |
| 功能规格 | `{feature}-spec.md`、`{feature}-requirements.md` |
| 架构蓝图 | `architecture-overview.md`、`{module}-architecture.md` |
| API 设计 | `api-{service}.md` |
| 交互设计 | `ux-{flow}.md` |

### doc/（当前实现）

按 **业务域** 拆分。注意：doc 只写当前代码实现的事实。

| 模式 | 示例文件 |
|------|----------|
| 业务域 | `{domain}.md`（如 `content-monitoring.md`） |
| 功能模块 | `{feature}.md`（如 `task-engine.md`） |
| 系统配置 | `config.md`、`environment.md` |
| 状态与规则 | `{entity}-lifecycle.md` |

### agent-handbook/（代码架构）

按 **代码模块** 拆分，一个模块一篇。模块 = `src/lib/` 下的子目录或独立功能域。

| 模式 | 示例文件 | 说明 |
|------|----------|------|
| 功能模块 | `auth.md`、`payment.md`、`task-engine.md` | **主体**，每个业务模块独立一篇 |
| 基础设施 | `database.md`、`cache.md` | 独立的基础设施模块 |
| 工具通用 | `utils.md`、`config.md` | 共享工具模块 |
| 入口概览 | `overview.md`（目录结构、技术栈、入口索引） | **辅助**，仅做速查索引 |
| 入口地图 | `entrypoints.md`（页面、API、Server Action） | **辅助**，仅做入口索引 |

**禁止模式**（以下文件不应出现在 agent-handbook/ 中）：

| 禁止文件 | 原因 |
|----------|------|
| `directory-map.md` | 横切面汇总，应拆入各模块文档的"入口与目录结构"章节 |
| `module-boundaries.md` | 横切面汇总，模块边界应在各模块文档的"依赖关系"章节体现 |
| `persistence-architecture.md` | 横切面汇总，持久化信息应在对应模块文档中描述 |
| `system-entrypoints.md` | 与 `entrypoints.md` 功能重复，合并为一篇 |
| 任何以 `-architecture.md` 结尾的横切面文档 | 架构信息应分散到对应模块文档中 |

**核心原则**：agent-handbook 的主体是"一个模块一篇"的垂直文档，不是几篇横切面汇总文档。`overview.md` 和 `entrypoints.md` 仅作为辅助索引存在，不可将模块内容塞入其中。

### research/（调研资料）

按 **主题域** 拆分。

| 模式 | 示例文件 |
|------|----------|
| 竞品分析 | `competitor-overview.md`、`competitor-{name}.md` |
| 市场调研 | `market-{segment}.md` |
| 用户研究 | `user-personas.md`、`user-interviews-{cohort}.md` |
| 技术调研 | `tech-{topic}.md` |

### knowledgebase/（知识库）

按 **知识域** 拆分。

| 模式 | 示例文件 |
|------|----------|
| 行业知识 | `{industry}-regulations.md` |
| 技术方案 | `{tech}-guide.md` |
| 业务流程 | `{process}-overview.md` |
| 最佳实践 | `{topic}-best-practices.md` |

## 文件命名规范

- 全小写、连字符分隔：`competitive-analysis.md`
- 有子分类时加前缀：`ux-personas.md`
- agent-handbook/ 下文件名与代码模块名对应：`task-engine.md`
- 文件名中不带日期（日期放 frontmatter）
- 保持简短有描述性：2-4 个词

## 臃肿检测

出现以下情况时标记为需要重组：
1. **行数**：单文档 > 500 行
2. **主题跨度**：frontmatter 标签横跨 3+ 无关领域
3. **章节数**：超过 8 个顶级 `##` 章节
4. **交叉引用密度**：相同内容被 3+ 篇文档引用（提取为独立文档）
5. **类型混杂**：文档同时包含不同目录类型的内容（应拆分）

## 重组流程

检测到臃肿时：
1. 识别所需的最小新文档集合
2. 向用户展示拟议新结构
3. **等待用户确认**后再执行
4. 保留全部原始内容，不丢失任何信息
5. 拆分完成后更新目录级和顶级 INDEX.md
6. 更新其他文档中的交叉引用
