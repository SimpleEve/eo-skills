---
name: eo-project-init
description: "从 PRD/MVP 文档或口头描述启动一个新项目，生成项目目录骨架、路线图、阶段模板，并注册到项目看板。支持在代码仓库侧运行，自动建立与 vault 的软链和 agent 配置注入。当用户说'启动项目'、'初始化项目'、'新建项目'时触发。"
---

# eo-project-init

## 功能

将项目想法（PRD、MVP 文档、口头描述）转化为结构化的项目目录，并注册到项目看板。支持两种场景：在 vault 内创建项目、或在代码仓库中关联已有项目。

## 输入

用户提供以下之一：
- **PRD/MVP 文档路径**：已有的需求或 MVP 文档
- **口头描述**：项目名称 + 要做什么 + 大致阶段

可选补充：
- 项目状态（默认 `active`，可选 `researching`）
- 代码仓库路径（双向关联）

## 模板与引用

**模板**（输出格式）：
- `templates/roadmap.md` — 路线图格式
- `templates/phase.md` — 阶段计划格式
- `templates/log.md` — 项目日志格式

**引用**（按需加载）：
- `references/roadmap-breakdown.md` — roadmap 拆解方法论。仅在需要拆解 roadmap/phase 时读取，已有 roadmap 时不加载。

## 执行步骤

### 1. 判断运行环境

检查当前工作目录：

**场景 A：在 vault 目录内**
→ 直接创建项目目录，如用户提供了代码仓库路径则建立关联

**场景 B：在代码仓库内**
→ 读取 `.eo-project.json` 获取 `project_vault` 路径
→ 如果不存在，引导用户提供 vault 路径并创建 `.eo-project.json`

### 2. 检测已有项目

检查 vault 侧是否已有该项目目录：

**项目目录已存在 + 有 roadmap.md**：
→ 提供三个选项：
1. **跳过拆解**：只建立代码侧关联（.eo-project.json + 软链 + agent 配置注入）
2. **更新 roadmap**：基于新输入刷新 roadmap（保留已有进度标记）
3. **重建**：确认后覆盖重写

**项目目录已存在 + 无 roadmap.md**：
→ 异常状态，提示补全，进入拆解流程

**项目目录不存在**：
→ 正常 init，进入拆解流程

### 3. 解析项目信息

从输入中提取：
- **项目名称**：用于目录命名
- **项目目标**：一句话描述
- **初始状态**：`active` / `researching`

阶段划分不在此步完成——交给步骤 5 的拆解流程。

### 4. 检查活跃项目数

读取 `00-Wiki/项目看板.md`，如果「进行中」已有 3 个项目，提醒用户考虑搁置或归档。

### 5. 创建项目目录（vault 侧）

```
<vault>/30-我的项目/<项目名>/
├── roadmap.md
├── phases/
│   ├── phase-1-<阶段名>.md
│   └── phase-2-<阶段名>.md
├── decisions/
│   └── .gitkeep
├── docs/
│   └── <原始PRD>.md       ← 如有，复制存档
├── todo/
│   └── backlog.md         ← 待办池
└── log.md
```

### 6. Roadmap 拆解

如果需要拆解 roadmap（项目目录不存在或无 roadmap.md），读取 `references/roadmap-breakdown.md` 获取拆解方法论，然后与用户对话：

1. **确认终态**（1 轮）：项目做完，用户能做到什么之前做不到的事？
2. **逆推里程碑**（1-2 轮）：从终态往回推必经中间状态
3. **展示 Phase 划分**（1 轮）：里程碑 → Phase 表格，用户确认
4. **拆任务**（1 轮）：逐个 Phase 展开任务清单
5. **用户确认** → 写入文件

⚠️ 不可静默拆解——必须展示给用户确认后再写入。整个过程不超过 5 轮对话。

如果用户已提供完整的 PRD/MVP 文档且阶段划分清晰，可以直接提取后展示确认，不走完整对话流程。

### 7. 生成 roadmap.md

读取 `templates/roadmap.md`，填充项目名、目标、阶段概览表。第一个阶段标记 🟢 active，其余 ⏳ planned。

### 8. 生成 phase 文件

读取 `templates/phase.md`，每个阶段生成一个文件到 `phases/` 目录：
- 命名：`phase-{N}-{阶段名}.md`
- 第一个阶段 `status: active`，其余 `planned`
- 任务清单用 `- [ ]` 格式

### 9. 生成 todo/backlog.md

```markdown
---
type: backlog
project: "{{project_name}}"
updated: "{{date}}"
---

# {{project_name}} 待办池

> 不属于任何 phase 的待办、灵感、以后要做的事。

## 待办

## 灵感 & 以后再说
```

### 10. 生成 log.md

读取 `templates/log.md`，填充项目名、来源、阶段数、初始状态。

### 11. 注册到项目看板

在 `00-Wiki/项目看板.md` 对应状态分区添加：

```markdown
### <项目名>
- 状态：`active`
- 当前阶段：[[phase-1-<阶段名>]]
- 下一步：<第一个任务>
- 阻塞：无
- 决策记录：无
- 经验教训：0 条
```

### 12. 生成 .eo-project.json（代码仓库侧）

在**代码仓库根目录**生成：

```json
{
  "project_name": "<项目名>",
  "project_vault": "<vault绝对路径>/30-我的项目/<项目名>"
}
```

### 13. 建立软链（代码仓库 → vault）

在代码仓库的 `eo-doc/` 目录下创建一条软链，指向 vault 项目根目录：

```bash
ln -s <project_vault> eo-doc/vault
```

这样 vault 下所有子目录（roadmap.md、phases/、todo/、decisions/、docs/ 等）都可以通过 `eo-doc/vault/` 访问，无需逐个建链。

如果 `eo-doc/` 不存在，先创建该目录（`mkdir -p eo-doc`）。

在 `.gitignore` 中追加：
```
# eo-project vault link
eo-doc/vault
```

### 14. Agent 配置注入（代码仓库侧）

自动检测代码仓库使用的 agent 配置文件：

**检测顺序**：
1. `CLAUDE.md` — Claude Code
2. `AGENTS.md` — OpenAI Codex
3. `COPILOT.md` — GitHub Copilot
4. `CURSOR.md` — Cursor
5. 如果都不存在，问用户用哪个工具，创建对应文件

**注入方式**：使用标记段落，支持幂等更新。

查找 `<!-- eo-project:start -->` 和 `<!-- eo-project:end -->`：
- 标记存在 → 原地替换
- 标记不存在 → 末尾追加

**注入内容**：

```markdown
<!-- eo-project:start -->
## EO-Project

本项目通过 `.eo-project.json` 关联到项目 vault：`<project_vault>`

### 待办提醒

当对话中出现以下信号时，主动提醒用户是否要加入 vault todo：
- 提到"以后要做"、"下次再说"、"TODO"、"先跳过"、"回头处理"
- 发现技术债务或待优化项
- 用户做了临时方案（workaround）

提醒格式：
> 💡 检测到待办事项：「{内容}」。要加入项目 todo 吗？

用户确认后，追加到 `<project_vault>/todo/backlog.md` 的「待办」部分。

### 决策同步

当对话中出现关键技术决策时（选型、架构、方案取舍），提醒用户：
> 💡 这是一个关键决策。要记录到项目 decisions/ 吗？

用户确认后，在 `<project_vault>/decisions/` 创建决策记录。
<!-- eo-project:end -->
```

### 15. 输出摘要

展示：
- 项目目录结构
- 路线图概览
- 第一阶段任务清单
- 看板已更新
- 代码仓库关联状态（.eo-project.json + `eo-doc/vault` 软链 + agent 配置注入）

## 输出

- 项目目录：`<vault>/30-我的项目/<项目名>/`（含 todo/）
- 看板更新：`00-Wiki/项目看板.md`
- 代码仓库：`.eo-project.json` + `eo-doc/vault` 软链 + agent 配置注入

## 约束

- 项目名用用户给的原始名称，不转换
- 原始文档复制到 `docs/` 存档，不修改原文件
- **`docs/` 不是 `raw/`**——`raw/` 保留给知识图谱 ingest
- 阶段数 2-5 个，过多则建议合并
- roadmap 和 phase 是活文档，后续由 `eo-project-update` 更新
- 所有链接使用最短路径 `[[文件名]]`
- 活跃项目上限 3 个
- 软链为单条 `eo-doc/vault` → vault 项目根目录
- agent 配置注入使用 `<!-- eo-project:start/end -->` 标记，幂等可重复执行
- 注入内容中的 vault 路径使用绝对路径
