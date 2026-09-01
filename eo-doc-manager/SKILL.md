---
name: eo-doc-manager
description: 管理 eo-doc/ 代码侧文档体系（init / modify / sync）：维护 changes/INDEX.md、agent-handbook/ 规范篇与 templates/；`state.enabled` 时cursor 增量再生 state/ 现状篇。所有 eo-doc 下的文档维护操作必须走此 skill。触发：初始化文档 / 修改文档 / 整理文档 / 同步文档 / /eo-doc-manager。NOT FOR：查询与解释文档内容（走 /eo-recall）。
---

# eo-doc-manager

**代码侧**文档管理。项目管理侧（roadmap / decisions / lessons / design / docs）由 `eo-project-*` skill 管。

## 前置

除 `init` 外的所有命令必须能找到 `.eo-project.json`（cwd 或父目录）。同目录存在 `.eo-project.local.json` 时顶层字段覆盖合并（local 优先）。找不到 → 报错退出，提示运行 `/eo-project-init`。

`init` 通常由 `/eo-project-init` 内部调用；用户直接调用 `/eo-doc-manager init` 时，若 `.eo-project.json` 不存在会提示先走 `/eo-project-init`。

## 命令路由

| 命令 | 触发词 | 流程 |
|------|--------|------|
| `init` | 初始化文档、init docs | 创建 eo-doc/ 最小骨架（changes/ + agent-handbook/INDEX + templates/） |
| `modify` | 修改文档、整理文档 | 维护 changes/INDEX.md / agent-handbook/ 规范篇 / templates/ |
| `sync` | 同步文档、同步 state、重新生成现状文档 | cursor 增量再生 `state/` 现状篇（需 `state.enabled`，流程见下） |

> 「查文档 / 当时怎么设计的 / 这个逻辑怎么实现的」→ 走 `/eo-recall`（本 skill 不提供 query，回归纯维护职责）。

**路由规则**：
1. 明确命令 → 直接路由
2. 自然语言 → 按触发词匹配
3. 无法判断 → 列出可用命令

## 目录结构（代码侧 `eo-doc/`）

所有文档存放在项目根目录 `eo-doc/` 下（**无顶级 INDEX.md**；agent 配置注入段中的目录表即一级索引）：

```text
eo-doc/
├── changes/          # 必建，change 工件流（子目录由 eo-* 工作流 skill 产出）
│   └── INDEX.md      # 项目级 change 时间线
├── agent-handbook/   # 可选，Agent 操作手册（篇目含 INDEX.md）
├── state/            # 可选（`state.enabled` 时由 sync 增量再生维护）
└── templates/        # 必建（空），eo-* 技能扩展点
```

### 不处理的历史目录

`eo-doc/` 下可能存在的历史目录（`doc/`、`dev/`、`design/`、`research/`、`knowledgebase/`）：**不读取、不重建、不删除**，仅供历史查阅；v1 遗留的迁移处理见 eo-skills 仓库的 docs/migration-v1-to-v2.md。
`state/` 单独处置：配置 `state.enabled: true` → 由本 skill `sync` 维护的活文档层；未启用 → 视同历史目录冻结留存（不删除）。

## 目录职责

| 目录 | 职责 | 面向 | 核心问题 |
|------|------|------|----------|
| `changes/` | change 工件流 — 每次变更的 change/review/test 产出 | 都 | "变更**进行**到哪了？" |
| `agent-handbook/` | Agent 操作手册 — 相对固定的操作规范（worktree 协作 / 架构分工 / 目录约定 / UI token 用法 / agent 协作），非 SSOT（代码为准），不挂自动同步 | AI | "操作时按什么**规范**？" |
| `state/` | 业务现状活文档 — 模块现状篇（`state.enabled` 时存在），代码为唯一信源cursor 增量再生，非 SSOT | 都 | "系统**现在**是什么样？" |
| `templates/` | eo-* 技能的扩展点 — 项目类型、工作流定制 | AI | "项目**怎么**定制？" |

**changes/**：
- 子目录由 eo-change、eo-implement、eo-review、eo-archive 等技能按约定产出
- 本 skill 负责 `changes/INDEX.md` 的整理与修复（条目对应、孤儿清理、seq 查重）

**templates/**：
- 不是文档，是 eo-* 技能的扩展点（如项目类型画像 `project-profile.md`）
- 模板可选，不存在时 eo-* 技能使用内置默认行为
- 由项目按需自建，本 skill 只建空目录、不生成模板内容

## 核心工作流

### init — 初始化最小骨架

通常由 `/eo-project-init` 内部调用。直接调用时：

1. 检查 `.eo-project.json` 是否存在；不存在 → 提示先走 `/eo-project-init` 并退出
2. 读取 `.eo-project.json` 的 `doc_root`（默认 `eo-doc`）作为根
3. 创建最小骨架：
   - `<doc_root>/changes/INDEX.md`（骨架）
   - `<doc_root>/agent-handbook/INDEX.md`（骨架；篇目内容由 /eo-project-init 的 handbook 初始化流程按需产出）
   - `<doc_root>/templates/`（空目录，不自动生成模板文件）
4. 注入段刷新（见下方「注入规则」）

### modify — 维护 changes/INDEX.md、agent-handbook/ 与 templates/

1. **changes/INDEX.md 整理**：条目与 `changes/` 子目录一一对应（无孤儿、无漏收），状态/摘要列与各 change.md frontmatter 一致；seq 列顺手查重（重号 → created 晚者让号，见 [../eo-shared/conventions.md](../eo-shared/conventions.md) §2）
2. **agent-handbook/ 篇目维护**：按用户输入或 init 扫描结果创建/修改规范篇；内容不从源码生成、不挂自动同步；只写方向性规范，细节判断交运行时
3. **templates/ 管理**：按用户输入创建/修改项目定制模板；模板内容来自用户输入，不从源码生成
4. **验证**：INDEX 与目录一一对应、交叉引用指向真实存在的文件
### sync — cursor 增量再生 state/ 现状篇

前置：合并配置 `state.enabled: true`；未启用 → 告知该层未开启（可由 `/eo-project-init` 更新分支开启）并退出。

**机制**：单游标、单机制——游标文件 `eo-doc/.sync-cursor`（YAML：`last_commit` / `sync_count` / `archive_count`）记录上次同步到的 commit；每次 sync 只处理 `cursor..HEAD` 的已提交增量，完成后推进游标到 HEAD。archive 收口与手动调用是**同一机制的两个触发点**；不提供按 change 定界的 range 同步（range 不动游标会被下次重扫，动游标会跳过区间外交错的直改/其他 change 提交）。

1. **读游标**：`.sync-cursor` 不存在 → 首次 sync = 全量生成（全部模块逐篇生成），完成后写游标 = HEAD
2. **脏变更三选项**（检测到工作区脏时按封闭选择协议问）：① 只取 cursor..HEAD 增量，不扫脏变更（默认推荐——脏变更提交后自然被下次 sync 覆盖）② 含脏变更一起同步（代码即将定稿时用）③ 全部重扫（等价重新首同步，游标仍推进到 HEAD）
3. **算增量**：`git diff --name-only <cursor>..HEAD`；**排除 `eo-doc/` 路径**（归档元数据等纯文档提交直接跳过，不做影响分析）
4. **路径映射模块**：按 `agent-handbook/architecture.md` 的划分（无该篇则按顶层目录）把变更文件映射到受影响模块集合；映射不到任何模块的路径（根配置等）→ 速报列出并跳过
5. **逐受影响模块读码重写** `state/<module>.md`（未受影响的篇不动）：
   - 篇头：`> 非 SSOT：代码为准，本篇为派生快照｜基线 <commit-short-sha>｜last_sync <date>｜由 /eo-doc-manager sync 生成`
   - 三节：**入口**（主要文件/符号）、**行为契约**（对外可观测行为与规则）、**依赖**（依赖谁、被谁依赖）
6. **孤儿篇处置**：模块已不存在的存量篇 → 列出并请用户确认后删除
7. **推进游标**：`.sync-cursor` 写入新 HEAD 并累计 `sync_count`；archive 联动触发的本次另累计 `archive_count`
8. **一致性抽查**：`sync_count` 每满 5 → 抽查 state ↔ agent-handbook 同源文档是否前后矛盾、篇头与正文是否漂移，只报告不自动改
9. **速报**：触达 N 篇（模块清单）/ 删除 M 篇 / 游标 `<old-sha>..<new-sha>`

## INDEX.md 规范

见 [references/index-templates.md](references/index-templates.md)。

## 注入规则

见 [references/claude-injection.md](references/claude-injection.md)。

## 验证清单

每次操作后：
- [ ] `changes/INDEX.md` 与 `changes/` 子目录一一对应
- [ ] 所有交叉引用指向真实存在的文件

## 维护协议

参考 [maintenance.md](references/maintenance.md)。
