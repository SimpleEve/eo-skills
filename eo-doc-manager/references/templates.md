# 文档模板

## 通用结构化文档模板

```markdown
---
title: [简明描述性标题]
type: agent | state
tags: [tag1, tag2, tag3]
created: YYYY-MM-DD
updated: YYYY-MM-DD
scope: [一句话：谁/什么/何时适用]
status: draft | active | archived
source: [原始 URL 或项目内部路径]
summary: >
  1-2 句核心摘要。AI 靠这个决定是否需要读全文。
conclusions:
  - 关键结论或发现1
  - 关键结论或发现2
---

[2-3 句上下文：这份文档何时/为何重要，解决什么问题，谁应该参考。]

## [章节标题]

[结构化内容。事实用列表，分析用短段落。
每个章节自包含、可独立扫读。]

## 来源

- [来源名称](URL) — 简述该来源涵盖的内容
- [内部文档](./path/to/doc.md) — 与本文档的关系
```

## INDEX.md 模板

### 目录级 INDEX.md

```markdown
# [分类名] Index

> Last updated: YYYY-MM-DD
> Total: N docs

| File | Title | Tags | Updated | Summary |
|------|-------|------|---------|---------|
| [filename.md](filename.md) | 标题 | `tag1` `tag2` | YYYY-MM-DD | 一句摘要 |
```

### 分组式 INDEX（10+ 篇时使用）

```markdown
# [分类名] Index

> Last updated: YYYY-MM-DD
> Total: N docs

## [子分类 A]

| File | Title | Tags | Updated | Summary |
|------|-------|------|---------|---------|
| [file1.md](file1.md) | 标题 | `tag` | YYYY-MM-DD | 摘要 |

## [子分类 B]

| File | Title | Tags | Updated | Summary |
|------|-------|------|---------|---------|
| [file2.md](file2.md) | 标题 | `tag` | YYYY-MM-DD | 摘要 |
```

## Frontmatter 字段规则

| 字段 | 必填 | 说明 |
|------|------|------|
| title | 是 | 简明、描述性、同分类内唯一 |
| type | 是 | `agent` 或 `state` |
| tags | 是 | 2-5 个标签，小写，多词用连字符 |
| created | 是 | YYYY-MM-DD，首次创建日期 |
| updated | 是 | YYYY-MM-DD，最近修改日期 |
| scope | 是 | 谁/什么/何时适用 |
| status | 是 | `draft` / `active` / `archived` |
| source | 是 | 原始 URL（优先）或项目内部路径 |
| summary | 是 | 1-2 句，足以做分流判断 |
| conclusions | 推荐 | 2-5 条关键要点，列表形式 |

## 内容编写规则

1. **无填充**：删除"值得注意的是"、"如上所述"等冗余短语
2. **事实用列表**：事实性信息 → 列表
3. **分析用段落**：分析性内容 → 短段落（3-5 句）
4. **对比用表格**：功能/竞品对比 → Markdown 表格
5. **层级上限**：`##` 为章节，`###` 仅在必要时使用，禁止 `####`
6. **行数预算**：目标 100-300 行/篇，硬上限 500 行
7. **交叉引用**：同目录用 `[标题](./file.md)`，跨目录用 `[标题](../state/file.md)`

## 按类型的模板差异

### State（当前实现文档）

侧重描述系统当前的实际行为。给人阅读，用业务语言。**必须与代码一致**。

```yaml
conclusions:
  - [当前系统的核心行为]
  - [关键业务规则]
  - [重要配置或约束]
```

典型章节：概述、业务规则、状态流转、配置说明、边界条件、来源

**State 关键规则**：
- 只描述已实现的功能，不写规划或设计意图（规划/设计属于项目管理侧）
- 用业务语言而非代码语言
- 描述"什么"和"为什么"，不描述"怎么实现的"
- sync/re-sync 可自动生成和更新

### Agent-handbook（代码架构文档）

专用于代码架构索引，让 AI 不读源码即可定位模块和接口。**必须与代码一致**。

```markdown
---
title: 任务引擎模块
type: agent
tags: [task-engine, module]
created: 2026-03-20
updated: 2026-03-20
scope: 任务调度与执行相关功能
status: active
source: src/lib/task-runtime/
summary: >
  处理任务的创建、调度、执行和状态管理。
  入口为 src/lib/task-runtime/engine.ts，对外暴露 TaskEngine 和 runTask。
conclusions:
  - TaskEngine 是核心类，封装任务调度逻辑
  - executor 模式支持不同任务类型的执行策略
  - 通过 repository.ts 持久化任务状态
---

本模块负责任务的全生命周期管理，是系统自动化层的核心。

## 入口与目录结构

- **入口文件**: `src/lib/task-runtime/engine.ts`
- **核心导出**: `TaskEngine`, `runTask`, `TaskStatus`

```
src/lib/task-runtime/
├── engine.ts          # 任务引擎核心
├── executors/
│   ├── content.ts     # 内容抓取执行器
│   └── opportunity.ts # 机会分析执行器
└── ...
```

## 关键接口

| 接口 | 签名 | 用途 |
|------|------|------|
| runTask | `runTask(task: Task): Promise<TaskResult>` | 执行单个任务 |
| TaskEngine.schedule | `schedule(config: ScheduleConfig): void` | 注册定时任务 |

## 依赖关系

- **依赖**: `task-persistence/repository`（状态持久化）、`lib/db`（数据库）
- **被依赖**: `actions/sync`（Server Action 触发）、`monitorAutomation`（自动化调度）

## 使用示例

```typescript
import { runTask } from '@/lib/task-runtime/engine';

const result = await runTask({
  type: 'content-fetch',
  monitorItemId: 'xxx',
});
```

## 来源

- [源码目录](src/lib/task-runtime/)
```

**Agent-handbook 关键规则**：
- 不贴实现代码，只写接口签名和调用示例
- 目录结构用 tree 格式
- 关键接口用表格：接口名、签名、用途
- 依赖关系明确写"依赖谁"和"被谁依赖"
- 每个模块一篇，文件名与模块名对应
- 精确到文件路径，有意义时精确到行号
