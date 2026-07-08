---
name: eo-doc-manager
description: 管理 eo-doc/ 代码侧文档体系（init / sync / re-sync / modify / select）。所有 eo-doc 下的文档维护操作必须走此 skill。触发：初始化文档 / 同步文档 / 重建文档 / re-sync / 修改文档 / 整理文档 / 只同步 state 或 agent-handbook / /eo-doc-manager。NOT FOR：查询与解释文档内容（走 /eo-recall）。
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

> 「查文档 / 当时怎么设计的 / 这个逻辑怎么实现的」→ 走 `/eo-recall`（本 skill 不再提供 query，回归纯维护职责）。

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
├── changes/          # 必建，change 工件流（由 eo-* 工作流 skill 维护）
│   └── INDEX.md
├── templates/        # 必建（空），eo-* 技能扩展点
├── state/            # 按需，系统当前状态（首次 sync 时 lazy 建）
│   └── INDEX.md
└── .sync-cursor      # sync 基线与计数（自动进 .gitignore）
```

### 不处理的旧目录

遇到 `eo-doc/` 下存在 `doc/`、`dev/`、`design/`、`research/`、`knowledgebase/` 时：**不读取、不重建、不同步**，口头提示用户「这是 v1 遗留目录，处理方式见 eo-skills 仓库的 docs/migration-v1-to-v2.md（迁移指南）」。

## 目录职责

| 目录 | 职责 | 面向 | 核心问题 | type 值 |
|------|------|------|----------|---------|
| `agent-handbook/` | 代码架构 — 模块入口、接口索引、依赖关系 | AI | "代码**怎么**组织的？" | `agent` |
| `changes/` | change 工件流 — 每次变更的 change/review/test 产出 | 都 | "变更**进行**到哪了？" | — |
| `state/` | 当前实现 — 系统实际做了什么，业务规则、状态流转、配置 | 人 | "系统**现在**是什么样？" | `state` |
| `templates/` | eo-* 技能的扩展点 — 项目类型、工作流定制 | AI | "项目**怎么**定制？" | — |

### 关键区分

**state vs agent-handbook**：
- state = 给人看的系统描述（业务规则、状态流转、配置含义）
- agent-handbook = 给 AI 看的代码地图（文件入口、接口签名、依赖关系）
- state 回答"系统做了什么"，agent-handbook 回答"代码在哪里、怎么调用"

**templates/**：
- 不是文档，是 eo-* 技能的扩展点（如项目类型画像 `project-profile.md`）
- 模板可选，不存在时 eo-* 技能使用内置默认行为
- sync / re-sync 不处理 templates/（它们不是从源码生成的）

**changes/**（v2，取代原 dev/）：
- 子目录由 eo-change、eo-implement、eo-review、eo-archive 等技能按约定产出
- changes/ 不参与 sync / re-sync，由开发流程技能管理

## 代码优先原则

state/ 和 agent-handbook/ 的内容必须从**源码**生成，不是从已有文档迁移。

**正确路径**：读源码 → 提取模块/接口/规则 → 生成文档 → 最后参考旧文档补充人工业务背景
**禁止路径**：读旧文档 → 改格式/改名 → 放入 eo-doc/（这是迁移，不是生成）

此原则适用于 init 和 re-sync。sync 是增量更新，不受此约束。

## state/ 写作规范

见 [references/doc-style.md](references/doc-style.md)。

## 核心工作流

### init — 初始化最小骨架

通常由 `/eo-project-init` 内部调用。直接调用时：

1. 检查 `.eo-project.json` 是否存在；不存在 → 提示先走 `/eo-project-init` 并退出
2. 读取 `.eo-project.json` 的 `doc_root`（默认 `eo-doc`）作为根
3. 创建最小骨架：
   - `<doc_root>/agent-handbook/INDEX.md`（骨架）
   - `<doc_root>/changes/INDEX.md`（骨架）
   - `<doc_root>/templates/`（空目录，不自动生成模板文件）
4. **不创建** `state/`（首次 sync 时 lazy 建）
5. 初始化 `<doc_root>/.sync-cursor`（当前 HEAD 作为首次基线）
6. 将 `<doc_root>/.sync-cursor` 追加到 `.gitignore`
7. CLAUDE.md 注入（见下方"CLAUDE.md 注入规则"）
8. **不自动生成 state/ 和 agent-handbook/ 内容**——留待 `/eo-doc-manager sync` 或 `re-sync` 首次触发


### modify — 修改/创建文档

1. **分析输入**：识别输入类型（单篇/多篇/更新已有）
2. **分流**：判断归属 `agent-handbook/` 还是 `state/`（参考 [splitting.md](references/splitting.md)）
3. **拆分**：同目录内按主题拆分（参考 [splitting.md](references/splitting.md)）
4. **结构化**：按模板格式化（参考 [templates.md](references/templates.md)）
5. **更新子目录 INDEX.md**
6. **验证**：frontmatter 完整、INDEX 对应、行数达标

### sync — 增量同步

基于 git diff 将代码变更同步到 state/ 和 agent-handbook/。完整流程见 [git-sync.md](references/git-sync.md)。

要点：
1. 读 `.sync-cursor` 取上次同步 commit，范围 = `<last_commit>..HEAD`
2. **工作区有脏变更时问用户三选一**（默认推荐：只取已提交增量，不扫脏变更；详见 git-sync.md）
3. **diff 分析排除 `eo-doc/` 路径**（change/INDEX 等元数据提交直接跳过）
4. 同时更新 `agent-handbook/`（代码地图）与 `state/`（系统现状，不存在则首次 lazy 建）
5. 更新受影响 INDEX.md → cursor 推进到 HEAD，`sync_count` +1
6. 汇报变更；`sync_count` 达到阈值（5）→ 提示做一次一致性抽查（见 [maintenance.md](references/maintenance.md)），完成后计数清零

**触发点有两个**：用户手动 `/eo-doc-manager sync`，以及 `/eo-archive` 归档第四层的内嵌调用——同一机制、同一游标，无独立的按 change 定界模式。

### re-sync — 全量重建

参考 [re-sync.md](references/re-sync.md)。

1. 扫描全部源码
2. **重建** agent-handbook/ 和 state/（清空后重新生成）
3. 更新 CLAUDE.md 注入
4. 重置 `.sync-cursor`


### select — 选择性操作

1. 解析指定目录（`agent-handbook` / `state`）
2. 将后续命令作用域限制到指定目录
3. 组合：`select state sync`（只同步 state/）

## 结构化规则

frontmatter 规格与正文结构以 [references/templates.md](references/templates.md) 为唯一来源（要点：frontmatter 含 type/tags/summary/conclusions 供 AI 免读全文判断相关性；正文 `##` 扁平章节、自包含可扫读）。

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
