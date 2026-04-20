---
name: eo-project-init
description: "eo-skills 在当前仓库的总入口：生成 .eo-project.json、初始化项目管理侧（roadmap/log/backlog）和代码侧最小骨架（eo-doc/），按需建 vault 软链和 agent 配置注入。触发：启动项目 / 初始化项目 / 新建项目 / /eo-project-init。"
---

# eo-project-init

## 定位

**所有 eo-* skill 的总入口**。其它 skill（eo-change / eo-implement / eo-doc-manager / …）都依赖 `.eo-project.json`；未运行过本 skill 的项目无法使用其它 eo-* skill。

一次 init 完成三件事：
1. 生成 `.eo-project.json`（项目级配置，所有 skill 读它）
2. 初始化**项目管理侧**（vault 或 local 模式）——最小骨架
3. 初始化**代码侧** `eo-doc/` 最小骨架（内部调用 `eo-doc-manager init` 的子流程）

配置与目录约定详见 [references/config.md](references/config.md)。

## 输入

用户提供以下之一：
- **PRD/MVP 文档路径**
- **口头描述**：项目名称 + 要做什么 + 大致阶段
- **仅项目名**：快速创建空骨架（后续再补充）

可选：
- 代码仓库路径（当前 cwd 不是代码仓库时）
- 运行模式偏好（vault / local），不指定则按用户级配置推断

## 执行步骤

### 1. 解析配置来源

1. **旧路径自动迁移**（静默，执行一次）：若 `~/.eo-skills.json` 存在且 `~/.eo/config.json` 不存在，执行：
   ```bash
   mkdir -p ~/.eo
   mv ~/.eo-skills.json ~/.eo/config.json
   ```
   迁移后打印一行提示：`已将旧配置 ~/.eo-skills.json 迁移至 ~/.eo/config.json`。之后不再检查旧路径。

2. **检查 cwd 是否已有 `.eo-project.json`**：
   - 已有 → 走「更新/修复」分支（见 §6）
   - 未有 → 继续 §3

3. **读取 `~/.eo/config.json`**（用户级默认，可能不存在）：
   - 存在 → 取 `default_mode` / `vault_root` 等作为推荐值进入 §2（节号指下文的"询问运行模式"）
   - 不存在 → 进入 §2 时推荐值为空

### 2. 询问运行模式（必须问，不默认）

**不要直接默认到 local**。向用户展示两种模式的区别，让其选择：

```
这个项目的"项目管理侧"（roadmap / log / backlog / decisions / lessons 等）放在哪里？

A) vault 模式 —— 集中到 Obsidian/文档 vault，跨项目统一浏览
   • project_root = <vault_root>/<projects_subdir>/<项目名>/
   • 默认把整个 vault 项目目录软链挂到代码侧 eo-doc/vault/（单点整挂，vault 侧新增子目录代码侧自动可见）
   • 可选挂到全局项目看板（kanban_path）统一追踪进度
   • 适合：多个项目并行、用 Obsidian 做 PKM、想在一处看所有项目状态

B) local 模式 —— 放在仓库自己的 .eo-project/ 下，跟代码走
   • project_root = <repo>/.eo-project/
   • 默认进 .gitignore（不提交），也可选随仓库提交
   • 不建软链、不挂看板
   • 适合：单个项目、没有统一 vault、不想跨目录跳转
```

用户回答后：
- 若选 vault 但用户级配置无 `vault_root` → 当场询问 `vault_root` 路径（以及可选的 `projects_subdir` / `kanban_path` / `create_symlink`），写入 `~/.eo/config.json`（必要时先 `mkdir -p ~/.eo`）
- 若用户级已有推荐值，展示并让用户确认或覆盖

最终落定 `mode = "vault" | "local"` 进入 §3。

### 3. 解析项目信息

从输入中提取：
- **项目名称**（`project_name`）
- **项目目标**：一句话描述
- **初始状态**：`active` / `researching`

### 4. 计算 `project_root`

- **vault 模式**：`<vault_root>/<projects_subdir>/<project_name>/`
- **local 模式**：`<repo>/.eo-project/`

检查 `project_root` 是否已存在：
- 存在且含 `roadmap.md` → 询问：1) 只建代码侧关联 2) 更新 roadmap 3) 重建（需确认）
- 存在但无 `roadmap.md` → 异常，提示补全后进入拆解
- 不存在 → 正常创建

### 5. 检查活跃项目数（仅 vault + 有看板）

若 `kanban_path` 已配置，读取看板，「进行中」已有 3 个项目时提醒用户考虑搁置或归档。

### 6. 创建项目管理侧骨架（最小）

```
<project_root>/
├── roadmap.md     # 必建
├── log.md         # 必建
└── backlog.md     # 必建
```

**按需目录一律不预建**（phases / decisions / lessons / brainstorm / docs），等对应 skill 首次写入时由那个 skill 创建。

写入 `roadmap.md`（读 [templates/roadmap.md](templates/roadmap.md)），填充项目名、目标、阶段概览占位。

写入 `log.md`（读 [templates/log.md](templates/log.md)）。

写入 `backlog.md`：

```markdown
---
type: backlog
project: "{{project_name}}"
updated: "{{date}}"
---

# {{project_name}} Backlog

> 待办池 + 未接入的未来规划（如将来想接入 research、knowledgebase skill 时的 placeholder）。

## 待办

## 灵感 & 以后再说

## 未接入（等 skill 支持再接入）
```

### 7. Roadmap 拆解（可选）

如果用户提供了 PRD/MVP 或愿意拆解：
1. 读取 [references/roadmap-breakdown.md](references/roadmap-breakdown.md) 方法论
2. 与用户对话（不超过 5 轮）：终态 → 里程碑 → Phase → 任务
3. 用户确认后，**lazy 创建** `phases/` 目录，每个阶段一个文件（读 [templates/phase.md](templates/phase.md)）
4. 更新 `roadmap.md` 的阶段概览表

仅"快速创建空骨架"时可跳过此步。

### 8. 初始化代码侧 `eo-doc/`（内部调用 eo-doc-manager init 子流程）

在代码仓库根目录创建**最小骨架**：

```
eo-doc/
├── agent-handbook/INDEX.md   # 骨架
├── dev/INDEX.md              # 骨架
└── templates/                # 空目录
```

**不创建** `state/`（首次 `/eo-doc-manager sync` 时按需建）。
**不创建** `design/ / research/ / knowledgebase/`（已移除）。

额外：
- 初始化 `eo-doc/.sync-cursor`（当前 HEAD 作为首次基线）
- 将 `eo-doc/.sync-cursor` 追加到 `.gitignore`
- CLAUDE.md 注入（详见 `eo-doc-manager/references/claude-injection.md`）

**注意**：如果用户本次只想要项目管理侧（例如纯规划项目，没代码），可用 `--skip-code-side` 跳过 §8。此时 `doc_root` 字段仍写入配置，留待将来补建。

### 9. 生成 `.eo-project.json`

在**代码仓库根目录**写入：

```json
{
  "project_name": "{{project_name}}",
  "mode": "vault" | "local",
  "project_root": "{{absolute_path_to_project_root}}",
  "doc_root": "eo-doc",
  "kanban_path": "{{absolute_kanban_path_or_null}}"
}
```

`kanban_path` 填入规则：
- vault 模式 + 用户级 `kanban_path` 有值 → 拼接为绝对路径 `<vault_root>/<kanban_path>`
- 否则 → `null`

### 10. 建立软链（vault 模式 + `create_symlink: true`）

Obsidian 侧（vault）是**源**。把整个 vault 项目目录作为一个软链挂进代码侧：

```bash
ln -s <project_root> <repo>/<doc_root>/vault
```

**整目录单点软链**，不按子目录分别软链——这样 vault 侧日后新增 `docs/` / `phases/` / `decisions/` 等子目录，代码侧自动能看到，不用回来补软链。

在 `.gitignore` 追加：

```
# eo-project vault link
<doc_root>/vault
```

local 模式**不建软链**。

### 11. 处理 `.eo-project/`（仅 local 模式）

`.eo-project/` 即 `project_root`。默认追加到 `.gitignore`：

```
# eo-project local management side
.eo-project/
```

若用户明确想让管理侧随仓库提交，当场询问后跳过 gitignore 追加。

### 12. Agent 配置注入

检测代码仓库使用的 agent 配置文件（顺序）：
1. `CLAUDE.md`
2. `AGENTS.md`
3. `COPILOT.md`
4. `CURSOR.md`
5. 都不存在 → 询问用户创建哪个

使用 `<!-- eo-project:start -->` / `<!-- eo-project:end -->` 标记段落幂等注入：

```markdown
<!-- eo-project:start -->
## EO-Project

本项目通过 `.eo-project.json` 关联到项目管理侧：`{{project_root}}`

- 模式：`{{mode}}`
- 项目管理侧（roadmap / backlog / decisions / lessons 等）：`{{project_root}}`
- 代码侧文档：`{{doc_root}}/`

### 待办提醒

当对话中出现"以后要做"、"TODO"、"先跳过"、"回头处理"等信号，或用户做了 workaround 时，主动提示：

> 💡 检测到待办事项：「{内容}」。要加入项目 backlog 吗？

用户确认后追加到 `{{project_root}}/backlog.md`。

### 决策同步

当对话中出现关键技术决策（选型、架构、方案取舍），提示：

> 💡 这是一个关键决策。要记录到 decisions/ 吗？

用户确认后，在 `{{project_root}}/decisions/` 创建决策记录（首次时 lazy 建目录）。

### 经验教训

当用户提到"踩坑"、"下次不这么干"、"学到了"时，提示：

> 💡 要记录到 lessons/ 吗？

用户确认后，在 `{{project_root}}/lessons/` 创建经验记录（首次时 lazy 建目录）。
<!-- eo-project:end -->
```

### 13. 注册到项目看板（仅 `kanban_path` 非空时）

在 `kanban_path` 指向的看板对应状态分区添加：

```markdown
### {{project_name}}
- 状态：`active`
- 当前阶段：[[phase-1-<阶段名>]]（若已拆解）
- 下一步：<第一个任务或"待拆解">
- 阻塞：无
- 决策记录：无
- 经验教训：0 条
```

`kanban_path: null` 时跳过整步。

### 14. 输出摘要

展示：
- 运行模式
- `.eo-project.json` 路径和内容
- 项目管理侧骨架结构
- 代码侧骨架结构
- 软链 / gitignore / agent 配置 / 看板 状态

## 输出

- **代码仓库**：`.eo-project.json` + `eo-doc/` 最小骨架 + agent 配置注入（+ 可选软链）
- **项目管理侧**：`<project_root>/` 含 `roadmap.md` / `log.md` / `backlog.md`（+ 可选 `phases/`）
- **看板**（可选）：`{{kanban_path}}` 对应条目

## 约束

- **`.eo-project.json` 是所有 eo-* skill 的启动前置**。本 skill 的核心产出
- 按需目录（phases / decisions / lessons / brainstorm / docs）**init 时不预建**，由对应 skill 首次写入时 lazy 创建
- 项目名用用户给的原始名称，不转换
- 原始 PRD/MVP 若提供，存到 `<project_root>/docs/`（lazy 建）
- 活跃项目上限 3 个（仅看板维护时检查）
- 软链仅 vault 模式 + `create_symlink: true` 才建
- `.eo-project/` 默认进 `.gitignore`；用户可当场覆盖
- agent 配置注入使用 `<!-- eo-project:start/end -->` 标记，幂等可重复执行
