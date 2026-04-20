---
name: eo-doc-manager
description: 管理 eo-doc/ 代码侧文档体系（init / sync / re-sync / modify / query）。所有 eo-doc 下的文档操作必须走此 skill。触发：初始化文档 / 同步文档 / 查文档 / /eo-doc-manager。
---

# eo-doc-manager

**代码侧**文档管理。项目管理侧（roadmap / decisions / lessons / design / docs）由 `eo-project-*` skill 管。

## 前置

除 `init` 外的所有命令必须能找到 `.eo-project.json`（cwd 或父目录）。找不到 → 报错退出，提示运行 `/eo-project-init`。

`init` 通常由 `/eo-project-init` 内部调用；用户直接调用 `/eo-doc-manager init` 时，若 `.eo-project.json` 不存在会提示先走 `/eo-project-init`。

## 命令路由

| 命令 | 触发词 | 流程 |
|------|--------|------|
| `init` | 初始化文档、init docs | 创建 eo-doc/ 最小骨架（3 个必建目录） |
| `modify` | 修改文档、结构化、整理 | 分流到 agent-handbook / state → 更新 INDEX.md |
| `sync` | 同步文档、sync docs、更新文档 | git diff 增量 → 更新 agent-handbook/ + state/ |
| `re-sync` | 重建文档、全量同步 | 全量扫描源码 → 重建 agent-handbook/ + state/ |
| `select` | 只操作 agent-handbook / state | 缩小作用域 → 后续命令 |
| `query` | 查文档、有没有关于 X 的 | 扫各子目录 INDEX.md → 按 tag/keyword 匹配 |

**路由规则**：
1. 明确命令（如 `/eo-doc-manager sync`） → 直接路由
2. 自然语言 → 按触发词匹配
3. 无法判断 → 列出可用命令

## 目录结构（代码侧 `eo-doc/`）

所有文档存放在项目根目录 `eo-doc/` 下（**无顶级 INDEX.md**；CLAUDE.md 中的目录表即一级索引）：

```text
eo-doc/
├── agent-handbook/   # 必建，代码架构（AI 地图）
│   └── INDEX.md
├── dev/              # 必建，spec/change/review 流（由 eo-* 工作流 skill 维护）
│   └── INDEX.md
├── templates/        # 必建（空），eo-* 技能扩展点
├── state/            # 按需，系统当前状态（首次 sync 时 lazy 建）
│   └── INDEX.md
└── .sync-cursor      # sync 基线（自动进 .gitignore）
```

### 已移除的目录

以下目录在重构中移除，**本 skill 不再处理**：

| 旧目录 | 去向 |
|--------|------|
| `eo-doc/doc/` | 改名为 `state/`（语义更准："系统现在什么样" = state） |
| `eo-doc/design/` | 迁至项目管理侧 `<project_root>/docs/`（与原始 PRD 合并） |
| `eo-doc/research/` | **暂时移除**（未来有对应 skill 再接入；先记在 `<project_root>/backlog.md`） |
| `eo-doc/knowledgebase/` | **暂时移除**（同上） |

## 目录职责

| 目录 | 职责 | 面向 | 核心问题 | type 值 |
|------|------|------|----------|---------|
| `agent-handbook/` | 代码架构 — 模块入口、接口索引、依赖关系 | AI | "代码**怎么**组织的？" | `agent` |
| `dev/` | 功能开发文档 — 每个功能的 spec/change/review/test 产出 | 都 | "功能**开发**到哪了？" | — |
| `state/` | 当前实现 — 系统实际做了什么，业务规则、状态流转、配置 | 人 | "系统**现在**是什么样？" | `state` |
| `templates/` | eo-* 技能的扩展点 — 项目类型、层级结构、工作流定制 | AI | "项目**怎么**定制？" | — |

### 关键区分

**state vs agent-handbook**：
- state = 给人看的系统描述（业务规则、状态流转、配置含义）
- agent-handbook = 给 AI 看的代码地图（文件入口、接口签名、依赖关系）
- state 回答"系统做了什么"，agent-handbook 回答"代码在哪里、怎么调用"

**templates/**：
- 不是文档，是 eo-* 技能的扩展点
- 定义项目类型（`project-profile.md`）、多层对齐模板（`spec-layers.md`）、分层 Part 模板（`plan-layers.md`）、分层执行模板（`implement-layers.md`）
- 模板可选，不存在时 eo-* 技能使用内置默认行为
- sync / re-sync 不处理 templates/（它们不是从源码生成的）

**dev/**：
- 子目录由 eo-module-init、eo-change、eo-implement、eo-review、eo-archive 等技能按约定产出
- dev/ 不参与 sync / re-sync，由开发流程技能管理

## 代码优先原则

state/ 和 agent-handbook/ 的内容必须从**源码**生成，不是从已有文档迁移。

**正确路径**：读源码 → 提取模块/接口/规则 → 生成文档 → 最后参考旧文档补充人工业务背景
**禁止路径**：读旧文档 → 改格式/改名 → 放入 eo-doc/（这是迁移，不是生成）

此原则适用于 init 和 re-sync。sync 是增量更新，不受此约束。

## state/ 写作规范

见 [references/doc-style.md](references/doc-style.md)（原名保留，指代 state 的写作规范）。

## 核心工作流

### init — 初始化最小骨架

通常由 `/eo-project-init` 内部调用。直接调用时：

1. 检查 `.eo-project.json` 是否存在；不存在 → 提示先走 `/eo-project-init` 并退出
2. 读取 `.eo-project.json` 的 `doc_root`（默认 `eo-doc`）作为根
3. 创建最小骨架：
   - `<doc_root>/agent-handbook/INDEX.md`（骨架）
   - `<doc_root>/dev/INDEX.md`（骨架）
   - `<doc_root>/templates/`（空目录，不自动生成模板文件）
4. **不创建** `state/`（首次 sync 时 lazy 建）
5. 初始化 `<doc_root>/.sync-cursor`（当前 HEAD 作为首次基线）
6. 将 `<doc_root>/.sync-cursor` 追加到 `.gitignore`
7. CLAUDE.md 注入（见下方"CLAUDE.md 注入规则"）
8. **不自动生成 state/ 和 agent-handbook/ 内容**——留待 `/eo-doc-manager sync` 或 `re-sync` 首次触发

> 与旧版差异：旧版 init 会立即 re-sync 生成 agent-handbook / doc。新版拆开——init 只建骨架，内容生成是单独动作（避免新项目还没多少代码就先做一次全量扫描）。

### modify — 修改/创建文档

1. **分析输入**：识别输入类型（单篇/多篇/更新已有）
2. **分流**：判断归属 `agent-handbook/` 还是 `state/`（参考 [splitting.md](references/splitting.md)）
3. **拆分**：同目录内按主题拆分（参考 [splitting.md](references/splitting.md)）
4. **结构化**：按模板格式化（参考 [templates.md](references/templates.md)）
5. **更新子目录 INDEX.md**
6. **验证**：frontmatter 完整、INDEX 对应、行数达标

### sync — 增量同步

基于 git diff 将代码变更同步到 state/ 和 agent-handbook/。参考 [git-sync.md](references/git-sync.md)。

通过 `<doc_root>/.sync-cursor` 记录上次同步点：
1. 读取 `.sync-cursor` 获取上次同步 commit
2. `git diff <last_commit>..HEAD` + 未提交变更
3. **同时更新两个目标**（不再有 design/）：
   - `agent-handbook/`：代码地图（入口、接口、依赖）
   - `state/`：系统现状（业务规则、状态、配置）——**若 state/ 不存在则首次 lazy 创建**
4. 更新所有受影响 INDEX.md
5. 更新 `.sync-cursor` 为当前 HEAD
6. 汇报变更

### re-sync — 全量重建

参考 [re-sync.md](references/re-sync.md)。

1. 扫描全部源码
2. **重建** agent-handbook/ 和 state/（清空后重新生成）
3. 更新 CLAUDE.md 注入
4. 重置 `.sync-cursor`

> 与旧版差异：旧版有 design/ 的 impl_status 校准步骤。新版移除——design 已迁至项目管理侧，不再由本 skill 管。

### select — 选择性操作

1. 解析指定目录（`agent-handbook` / `state`）
2. 将后续命令作用域限制到指定目录
3. 组合：`select state sync`（只同步 state/）

### query — 查询文档

1. 读各子目录 INDEX.md
2. 按 tag / 关键词 / 文件名匹配
3. 返回：路径 + 摘要 + 相关度

## 结构化规则

### Frontmatter（YAML）

```yaml
---
title: 简明标题
type: agent | state
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
---
```

### 正文结构

1. 上下文段落（2-3 句）
2. `##` 结构化章节，自包含、可独立扫读
3. 事实用列表，分析用短段落，对比用表格
4. 底部来源引用

参考 [templates.md](references/templates.md) 获取模板。

### 拆分规则

参考 [splitting.md](references/splitting.md)。

## INDEX.md 规范

见 [references/index-templates.md](references/index-templates.md)。

## CLAUDE.md 注入规则

见 [references/claude-injection.md](references/claude-injection.md)。

## 验证清单

每次操作后：
- [ ] 每篇文档 frontmatter 完整
- [ ] 子目录 INDEX.md 与目录内文档一一对应
- [ ] 单篇不超 500 行（超出建议拆分）
- [ ] 标签体系统一（无近义重复）
- [ ] 所有交叉引用指向真实存在的文件

## Token 效率准则

- frontmatter summary 让 AI 不读全文即可判断相关性
- conclusions 数组支持快速提取要点
- INDEX.md 表格每条约 50 token，可一次扫描整个集合
- `##` 扁平结构，避免深层嵌套

## 维护协议

参考 [maintenance.md](references/maintenance.md)：
- 更新工作流（新增/修改/批量导入）
- state↔agent-handbook 一致性检查
- 臃肿检测与重组
- 归档流程
