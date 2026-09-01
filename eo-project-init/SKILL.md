---
name: eo-project-init
description: "eo-skills 在当前仓库的总入口：生成 .eo-project.json、初始化项目管理侧（roadmap）和代码侧最小骨架（eo-doc/），以及 agent 配置注入。触发：启动项目 / 初始化项目 / 新建项目 / /eo-project-init。"
---

# eo-project-init

## 定位

**所有 eo-* skill 的总入口**。其它 skill（eo-change / eo-implement / eo-doc-manager / …）都依赖 `.eo-project.json`；未运行过本 skill 的项目无法使用其它 eo-* skill。

一次 init 完成三件事：
1. 生成 `.eo-project.json`（项目级配置，所有 skill 读它）
2. 初始化**项目管理侧**（`<repo>/.eo-project/`）——最小骨架
3. 初始化**代码侧** `eo-doc/` 最小骨架（内部调用 `eo-doc-manager init` 的子流程）

配置与目录约定详见 [references/config.md](references/config.md)。

## 输入

用户提供以下之一：
- **PRD/MVP 文档路径**
- **口头描述**：项目名称 + 要做什么 + 大致阶段
- **仅项目名**：快速创建空骨架（后续再补充）

可选：
- 代码仓库路径（当前 cwd 不是代码仓库时）

## 执行步骤

### 1. 检查是否已初始化

- cwd 向上已有 `.eo-project.json` → 走下方「1.5 更新/修复分支」，**不进入首次创建流程**
- 未有 → 继续首次创建流程

### 1.5 更新/修复分支（已初始化项目重跑本 skill）

对已有 `.eo-project.json` 的项目，重跑是**幂等的补齐动作**，逐项执行、已达标项静默跳过：

0. **v1 痕迹检测**：发现 `eo-doc/dev/` 存在、`kanban_path` 非 null 等信号 → 先按 [references/migrate-v1.md](references/migrate-v1.md) 执行迁移子流程（冻结 spec、建项目级 changes、kanban 退役、roadmap 补 frontmatter、backlog 打散成卡等，幂等），完成后继续下列步骤
0.5. **协作者接入（local 覆盖）**：按 config.md 规则合并同目录 `.eo-project.local.json`（如有）后，检查合并结果的 `project_root` 在本机是否存在可写。不可用（典型：clone 了别人提交的配置，`project_root` 指向他人机器上的路径）或必填字段缺失 → 按「3. 计算 `project_root`」算出本机 `project_root`，把机器相关字段（`mode` / `project_root`）写入 `.eo-project.local.json`——**不改动提交的 `.eo-project.json`**。后续步骤一律以合并结果为准
1. **配置校验**：读现有 `.eo-project.json`（合并 local 覆盖），对照 [references/config.md](references/config.md) 的 schema——基础字段（project_name/mode/project_root/doc_root）缺失按默认补写；存量配置的 `kanban_path` 字段忽略不改，已有字段一律不改；**`project_root` 非绝对路径（存量形态）是可修项**——按 repo root 解析并解软链后**回写绝对路径**并提示用户（写回落点沿用既有规则：该顶层字段已存在于 `.eo-project.local.json` → 写 local，否则写 `.eo-project.json`）；解析不出已存在目录时不猜，转「3. 计算 `project_root`」重新算出；**`sync` 段（或其适配器键）与 `state` 键缺失时不在本步补写**（补了显式关闭条目会吞掉第 5 步的询问），只记录缺失，留给第 5 步问答/迁移后落盘
2. **骨架补齐**：项目管理侧必建 roadmap.md 与代码侧 `eo-doc/` 骨架缺什么补什么；**不触碰任何已有文件的内容**
3. **注入段刷新**：按标记整段刷新 agent 配置文件中的 `eo-project` / `eo-doc` / `eo-reply-contract` 注入段（存在则整段替换，缺失则补注）；仓库根存在 `DESIGN.md` 时核对 `eo-design` 注入段
4. **.gitignore 核对**：`tmp/eo/`、`.eo-project.local.json` 缺项补写；`.eo-project/` 的 ignore 状态**保持现状不核对**——已 ignore 的不删行、未 ignore 的不补写
5. **sync / state 联动问答与存量迁移**（仅合并配置 `sync` 段缺对应适配器键时问，规则见「7. 生成 .eo-project.json」的 sync 段小节）。**存量迁移**：检测到旧 `board` / `github` 段且合并配置无 `sync` 键 → 提示用户并**代写等价 `sync` 段**（启用集与兼容映射派生结果逐项一致；旧段问答已答过的适配器写显式条目——含关闭态，**不重问**；**旧段保留不删**，旧版工具仍可读）；已有 `sync` 键 → **零动作**零提示
   **state 问答**（仅合并配置无 `state` 键时问，规则见「7. 生成 .eo-project.json」的 state 段小节）：检测到存量 `eo-doc/state/` → 问「恢复维护（推荐）/ 保持冻结」，结论写 `state.enabled` true/false；无存量 `state/` → 按 §7 同一问（推荐关闭）；已有 `state` 键 → **零动作**零提示
5.5. **顺手注册**：执行 `eo-board --register`（幂等，已注册则原地更新）。**失败不阻塞本流程**——注册失败时输出告警并给手工补注册指引：「⚠ 项目注册失败（<原因>），init 已正常完成；稍后可在项目目录手工执行 `eo-board --register` 补注册（注册后任意目录 `eo-board --all` 可见本项目）」
6. **输出摘要**：列出本次补齐/刷新/跳过了什么（含注册结果），然后结束——不执行首次创建流程的其余步骤

### 2. 解析项目信息

从输入中提取：
- **项目名称**（`project_name`）
- **项目目标**：一句话描述
- **初始状态**：`active` / `researching`

### 3. 计算 `project_root`

`project_root` = `<repo>/.eo-project/`。

检查 `project_root` 是否已存在：
- 存在且含 `roadmap.md` → 按封闭选择协议三选一：1) 只建代码侧关联（推荐）2) 更新 roadmap 3) 重建（需确认）
- 存在但无 `roadmap.md` → 异常，提示补全后进入拆解
- 不存在 → 正常创建

### 4. 创建项目管理侧骨架（最小）

```
<project_root>/
└── roadmap.md     # 必建
```

**按需目录一律不预建**（backlog / phases / decisions / lessons / brainstorm / docs），等对应 skill 首次写入时由那个 skill 创建（backlog 为卡片目录，由 /eo-backlog 管理）。

写入 `roadmap.md`（读 [templates/roadmap.md](templates/roadmap.md)），填充项目名、目标、阶段概览占位。

### 5. Roadmap 拆解（可选）

如果用户提供了 PRD/MVP 或愿意拆解：
1. 读取 [references/roadmap-breakdown.md](references/roadmap-breakdown.md) 方法论
2. 与用户对话（不超过 5 轮）：终态 → 里程碑 → Phase → 任务
3. 用户确认后，**lazy 创建** `phases/` 目录，每个阶段一个文件（读 [templates/phase.md](templates/phase.md)）
4. 更新 `roadmap.md` 的阶段概览表

仅"快速创建空骨架"时可跳过此步。

### 6. 初始化代码侧 `eo-doc/`（内部调用 eo-doc-manager init 子流程）

在代码仓库根目录创建**最小骨架**：

```
eo-doc/
├── changes/INDEX.md          # 骨架
├── agent-handbook/INDEX.md   # 骨架（篇目内容见 §6.5）
└── templates/                # 空目录
```

额外：
- 询问是否启用 codegraph：启用则在仓库根执行 `codegraph init` 建索引，并把使用规范（索引按项目目录隔离，每个 worktree 需各自 `codegraph init`）写入 agent-handbook；不启用则跳过
- 将 `tmp/eo/` 追加到 `.gitignore`（tmp/eo/ 是各 skill 的临时工件命名空间，见 [../eo-shared/conventions.md](../eo-shared/conventions.md)）
- 将 `.eo-project.local.json` 追加到 `.gitignore`（个人/机器覆盖文件不提交，见 [references/config.md](references/config.md)）
- CLAUDE.md 注入（详见 [../eo-doc-manager/references/claude-injection.md](../eo-doc-manager/references/claude-injection.md)）

**注意**：如果用户本次只想要项目管理侧（例如纯规划项目，没代码），可用 `--skip-code-side` 跳过本节。此时 `doc_root` 字段仍写入配置，留待将来补建。

### 6.5 Handbook 初始化（可选，逐步授权）

`eo-doc/agent-handbook/` 是 Agent 操作手册：相对固定的操作规范，非 SSOT（代码为准），不挂自动同步；骨架由 §6 建好，是否填内容询问用户，同意才继续。模板机制（库位置 / manifest 格式 / 匹配合并细则）见 [references/handbook-templates.md](references/handbook-templates.md)。

**已有项目**（生成 = 匹配合并，不是裸 copy）：
1. 派子 agent 扫描五个面：lint/commit 配置、`git log` 归纳的 commit 规律、目录结构、架构分工、UI token 用法
2. 按 manifest signals 匹配候选 preset（私有库优先），按封闭选择协议确认（含「不用模板」）
3. 合并生成：实证 > 模板 > 待补——模板篇目为底，扫描实证覆盖冲突项，扫描不到依据的标「待补」；已配置文件化的只落一行指针（指向配置文件）
4. worktree 协作与 codegraph 使用两篇逐个询问授权后才写入（comments 注释纪律随 preset 默认生成，无需单独授权）

**空项目**：询问项目类型，选定 preset 纯 copy。

### 7. 生成 `.eo-project.json`

在**代码仓库根目录**写入：

```json
{
  "project_name": "{{project_name}}",
  "mode": "local",
  "project_root": "{{absolute_path_to_project_root}}",
  "doc_root": "eo-doc",
  "kanban_path": null
}
```

`kanban_path`：固定写 `null`；存量配置该字段被所有 skill 忽略。项目级总览由 Bases 聚合各项目 roadmap.md 的 frontmatter 承担。

**协作/多机场景**：机器相关字段（`project_root` / `mode` / `sync`——顶层段整段覆盖）可拆到不提交的 `.eo-project.local.json`（顶层字段覆盖合并，规则见 [references/config.md](references/config.md)）。首次 init 默认全部写入 `.eo-project.json` 即可；协作者 clone 后重跑本 skill 走「1.5 更新/修复分支」的协作者接入步骤生成 local 覆盖。

**sync 段**（投影开关，`eo-sync` 直接消费——机制见 [../eo-shared/board-github.md](../eo-shared/board-github.md)，schema 见 [references/config.md](references/config.md)；新配置只写 `sync` 段本身，存量 `board` / `github` 段由兼容映射护住）：按封闭选择协议问一次（触发判据 = 合并配置 `sync` 段缺对应适配器键）——
- github 适配器（检测到 git remote 指向 GitHub 时才问；pr 推荐 `auto`）：写 `sync.github = {"enabled": true, "issue": <bool>, "pr": "auto"|"always"|"never"}`

用户跳过 → 对应适配器写显式关闭条目（`{"enabled": false}`），后续 skill 不再询问。**后开场景**：对已初始化项目重跑本 skill 走「1.5 更新/修复分支」，其第 5 步提供这一问。
**state 段**（现状文档层开关，`/eo-doc-manager sync` 与 archive 联动直接消费，schema 见 [references/config.md](references/config.md)）：按封闭选择协议问一次（触发判据 = 合并配置无 `state` 键）——「启用 state 现状文档层？」（推荐**关闭**：保持精简，需要「系统现在是什么样」活文档的项目再开）。启用 → 写 `state.enabled: true` 并建 `eo-doc/state/`（空目录，首篇由 `/eo-doc-manager sync` 生成）；跳过/拒绝 → 写显式 `{"enabled": false}`，后续不再询问。

### 8. 处理 `.eo-project/`

`.eo-project/` 即 `project_root`。**缺省随仓库提交，不写入 `.gitignore`**——roadmap / backlog / decisions / lessons 是协作者最需要的项目记忆，跟代码走。

仅当用户明确表示不想提交管理侧时，当场追加：

```
# eo-project local management side
.eo-project/
```

### 9. Agent 配置注入

检测代码仓库使用的 agent 配置文件（顺序）：
1. `CLAUDE.md`
2. `AGENTS.md`
3. `COPILOT.md`
4. `CURSOR.md`
5. 都不存在 → 按封闭选择协议问创建哪个（推荐 CLAUDE.md）

注入两个标记段（均幂等、整段替换）：

**1. 项目上下文段**（`<!-- eo-project:start/end -->`）：

```markdown
<!-- eo-project:start -->
## EO-Project

本项目已接入 eo-skills。项目管理侧（roadmap / backlog 卡片 / decisions / lessons 等）位置从 `.eo-project.json` 的 `project_root` 字段解析（同目录存在 `.eo-project.local.json` 时顶层字段覆盖，local 优先），下文记作 `<project_root>`。

- 代码侧文档：`{{doc_root}}/`

### 项目记录入口

仅当**用户明确表达**要记录时响应（不做关键词嗅探，避免误触发）：

- 用户明确说「加个待办 / 记到 backlog / 以后做」→ 调用 `/eo-backlog` 写卡到 `<project_root>/backlog/`
- 用户明确说「把这个决策记下来」→ 调用 `/eo-project-record` 写入 `<project_root>/decisions/`
- 用户明确说「记一条经验 / 踩坑记录一下」→ 调用 `/eo-project-record` 写入 `<project_root>/lessons/`

对话中出现疑似待办/决策/教训但用户未明说时，**至多在当前话题收尾处轻提一句**「要不要记入 backlog/decisions/lessons？」，不打断进行中的工作。
<!-- eo-project:end -->
```

**2. 回复契约段**（`<!-- eo-reply-contract:start/end -->`）：

```markdown
<!-- eo-reply-contract:start -->
## 回复契约（长任务收尾）

长开发任务收尾时，用一段人话向用户汇报，四条各一句：

1. **做了什么**——行为变化，不是 diff 清单
2. **为什么这么做**——关键决策与理由，被否掉的方案一并点名
3. **主要产出**——文件 / 功能 / 命令，用户去哪看、怎么验
4. **遇到的问题与解法**——没有就明说「无」

受众分两层：对开发者讲接口与路径，对需求方讲行为与结果。一句一事，不铺陈过程。
<!-- eo-reply-contract:end -->
```

段内正文以 [../eo-shared/reply-contract.md](../eo-shared/reply-contract.md)「契约正文」为单一来源，整段搬运不改写——注入是被动兜底通道（覆盖非 eo 流程的直改收尾）；eo 流程收尾的硬步骤（eo-archive 交付汇报 / eo-loop 线段收尾报告）以该文「生效通道」为准。

**模板纪律**：项目上下文段**不内联** `project_root` 绝对路径——它因人/机器而异且 agent 配置文件提交进仓库，内联会把个人路径泄进 git 并在协作者机器上失真。运行时一律从配置合并结果解析。

**DESIGN.md 检查**：若仓库根存在 `DESIGN.md` 但 agent 配置文件中无 `<!-- eo-design:start -->` 标记段，执行 `/eo-design` 的约束注入子步骤补上（注入模板见 [../eo-design/references/design-md-template.md](../eo-design/references/design-md-template.md)）。

### 10. 注册到生态注册表（顺手注册）

执行 `eo-board --register`（在仓库根目录），把项目登记进用户级注册表 `${EO_HOME:-$HOME/.eo}/projects.json`，供 `eo-board --all` / `eo-sync watch --all` 跨项目枚举。

**失败不阻塞 init**——注册失败（如注册表目录不可写）时本 skill 仍算成功完成，但必须输出告警与手工补注册指引：「⚠ 项目注册失败（<原因>），init 已正常完成；稍后可在项目目录手工执行 `eo-board --register` 补注册（注册后任意目录 `eo-board --all` 可见本项目）」

### 11. 输出摘要

展示：
- `.eo-project.json` 路径和内容
- 项目管理侧骨架结构
- 代码侧骨架结构
- gitignore / agent 配置 / 生态注册 状态

## 输出

- **代码仓库**：`.eo-project.json` + `eo-doc/` 最小骨架 + agent 配置注入
- **项目管理侧**：`<project_root>/` 含 `roadmap.md`（+ 按需 `backlog/` 卡片、`phases/` 等）

## 约束

- **`.eo-project.json` 是所有 eo-* skill 的启动前置**。本 skill 的核心产出
- 按需目录（phases / decisions / lessons / brainstorm / docs）**init 时不预建**，由对应 skill 首次写入时 lazy 创建
- 项目名用用户给的原始名称，不转换
- 原始 PRD/MVP 若提供，存到 `<project_root>/docs/`（lazy 建）
- `.eo-project/` 缺省随仓库提交、不进 `.gitignore`；用户明确不想提交时当场覆盖。存量项目重跑本 skill 不改其既有 ignore 状态
- `.eo-project.local.json` **始终**进 `.gitignore`（个人/机器覆盖，不提交）；协作者接入只写 local，不改共享的 `.eo-project.json`
- agent 配置注入使用 `<!-- ...:start/end -->` 标记段（`eo-project` / `eo-reply-contract`），幂等可重复执行
