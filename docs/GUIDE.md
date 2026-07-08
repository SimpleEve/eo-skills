# eo-skills 详解

> 上手指南见 [README](../README.md)。本文是详解：每个 skill 的职责、典型流程、关键约束、设计权衡。

---

## 目录

- [运行模式：local vs vault](#运行模式local-vs-vault)
- [双侧目录：代码侧 vs 项目管理侧](#双侧目录代码侧-vs-项目管理侧)
- [开发工作流（Dev Track）](#开发工作流dev-track)
  - [设计理念](#设计理念)
  - [Skill 职责速查](#skill-职责速查)
  - [典型流程图](#典型流程图)
  - [关键约束](#关键约束)
- [两种 review 的边界](#两种-review-的边界)
- [跨 agent 协作（eo-flow）](#跨-agent-协作eo-flow)
- [会话交接（eo-handoff）](#会话交接eo-handoff)
- [项目管理 skill](#项目管理-skill)
- [文档体系（eo-doc-manager）](#文档体系eo-doc-manager)
- [看板与 GitHub 联动（opt-in）](#看板与-github-联动opt-in)
- [Skill 安装结构](#skill-安装结构)

---

## 运行模式：local vs vault

| 模式 | 触发条件 | 项目管理侧落在哪 | 软链 | 看板 |
|------|---------|---------------|------|------|
| **local**（默认） | `~/.eo/config.json` 不存在 或不配 `vault_root` | 仓库内 `.eo-project/`（默认进 `.gitignore`） | 不建 | 不维护 |
| **vault** | `~/.eo/config.json` 有 `vault_root` | `<vault_root>/<projects_subdir>/<project_name>/` | 默认在 `<repo>/<doc_root>/vault` 建指向 `<project_root>`（整目录单点挂，`create_symlink` 控制） | `kanban_path` 配了才维护 |

配置约定：

- **用户级**：`~/.eo/config.json`（`vault_root` / `projects_subdir` / `kanban_path` 等；同时承载 eo-platform 等生态侧状态）
- **项目级**：`.eo-project.json`（每项目一份，所有 skill 读它）
- 旧路径 `~/.eo-skills.json` 由 `/eo-project-init` 首次运行时自动迁移到 `~/.eo/config.json`。

完整字段见 [eo-project-init/references/config.md](../eo-project-init/references/config.md)。

---

## 双侧目录：代码侧 vs 项目管理侧

### 代码侧 `eo-doc/`（跟仓库走，由 `eo-doc-manager` 维护）

```
eo-doc/
├── agent-handbook/   # 必建，代码架构（AI 地图），活文档
├── changes/          # 必建，change 工件流（v2：项目级扁平目录，取代 dev/<module>/）
├── templates/        # 必建（空），eo-* 扩展点
└── state/            # 按需，系统当前状态（首次 sync 时建），活文档
```

### 项目管理侧（vault 模式在 vault 下，local 模式在 `.eo-project/`，由 `eo-project-*` 维护）

```
<project_root>/
├── roadmap.md     # 必建
├── log.md         # 必建
├── backlog.md     # 必建（待办 + 未接入的未来规划）
├── phases/        # 按需
├── decisions/     # 按需
├── lessons/       # 按需（项目级，替代原全局 _lessons/）
├── brainstorm/    # 按需
└── docs/          # 按需（PRD、设计、规划）
```

---

## 开发工作流（Dev Track）

一条以 **change 工件**为中心的代码侧开发流水线：每次变更以 `change.md`（验收清单 + TODO）独立承载，归档时更新活文档（state / agent-handbook）并冻结 change 目录——**不反写任何 spec**。

### 设计理念（v2）

1. **代码是唯一真相源** — state/ 与 agent-handbook/ 是活文档，永远可从代码再生；change 是过程工件，归档即冻结
2. **验收驱动** — change 的第一个产出物是用户视角验收清单（AC），它是 implement 的完成判据、review 的检查表、fix 的期望行为锚点
3. **渐进式严谨** — 文档重量与变更粒度挂钩：必填仅 4 节，方案/流程图/风险等条件化；trivial 改动直改不开 change
4. **量化粒度** — TODO 3-7 理想 / 10 硬上限，超标拆 change 序列
5. **fix 直接修复** — bug 口喷给 `/eo-fix`，定位后直接修；难缠 bug 自动升级深挖模式；实为需求变更才转 change

### 产物目录（代码侧）

```
eo-doc/changes/
├── INDEX.md                ← 项目级 change 时间线
└── <NNN-change-id>/        ← 三位连号 + kebab-case
    ├── change.md           ← 意图 + AC + TODO（+ 条件节）
    ├── change-review.md    ← 方案审查（可选）
    ├── test.md             ← 测试报告
    ├── review.md           ← 代码审查结论
    └── design/             ← 本 change 的高保真稿（可选）
```

### Skill 职责速查

| Skill | 触发时机 | 产出 | 备注 |
|-------|---------|------|------|
| `/eo-project-init` | 项目首次使用 eo-skills | `.eo-project.json` + 双侧骨架 | **所有 skill 的前置** |
| `/eo-brainstorming` | 想法不成形 / 新项目从零起步 | 已钉决策 + 首批 change 草案（捕获出口） | 可选前置 |
| `/eo-change` | 发起变更（bootstrap / feature / enhance / refactor） | `changes/<NNN-xxx>/change.md`（AC 前置 + TODO 分批） | trivial 主动短路成直改 |
| `/eo-change-review` | change draft 完成后、implement 前的方案审查 | `change-review.md` | ✅ 可选 |
| `/eo-implement` | 按 change.md TODO 分批实施（含 bug 修复循环） | 代码 + 勾选 TODO/AC | 批末 checkpoint |
| `/eo-fix` | 发现 bug（口喷即可） | 快路**直接修复** + 落点记账；语义分歧才取证；难缠 bug 自动深挖 | 需求变更转 change |
| `/eo-test` | 运行测试 / 场景验证 | `test.md`（以 AC 为锚） | 失败 → 回 implement |
| `/eo-review` | 实施后的**代码**审查 | `review.md` | 强制 |
| `/eo-archive` | 代码审查通过后归档 | 触发 doc sync 更新 state/handbook + 冻结 change | 不反写 spec |
| `/eo-design` | 设计系统 / 视觉方案 / 高保真 / 设计审计 | `DESIGN.md`（真相源）+ HTML 工件 + CLAUDE.md 约束注入 | init / variants / apply / audit 四模式 |
| `/eo-recall` | 「当时怎么设计的 / 逻辑怎么实现的 / 为什么这么定」 | 只读问答：分层作答带出处；可出 mermaid / HTML 解释页 | 活文档的消费入口；吸收原 doc-manager query |

### 典型流程图

```
项目启动：  /eo-project-init      →  .eo-project.json + 双侧最小骨架
            │
（可选）：  /eo-brainstorming     →  已钉决策 + 首批 change 草案（新项目 = 多个 bootstrap change）
            ▼
发起变更：  /eo-change            →  changes/NNN-xxx/change.md
            │                         AC 前置 + TODO 分批 + 粒度校验
            │                         （trivial → 主动短路成直改，不产生工件）
            ▼
方案审查：  /eo-change-review     →  change-review.md（可选）
            │                         P0/P1 → 回 eo-change 修
            ▼
确认：      （对话确认，skill 自动置 status: confirmed）
            ▼
实施：      /eo-implement         →  按 Batch 写代码 + 勾 TODO/AC，批末 checkpoint
            ▼
测试：      /eo-test              →  test.md（以 AC 为锚，失败 → 回 implement）
            ▼
代码审查：  /eo-review            →  review.md（AC 覆盖 + 代码质量）
            │                         P0/P1 → 回 implement 修
            ▼
归档：      /eo-archive           →  AC 全勾校验 → commit 区间 → doc sync
                                     更新 state/ + agent-handbook/
                                     冻结 change（status: archived，不反写 spec）
```

### 关键约束

| 约束 | 说明 |
|------|------|
| `.eo-project.json` 存在 | 所有 eo-* skill 的前置。找不到 → 报错 |
| `change-id` 命名 | `NNN-kebab-name`（3 位数字前缀，项目级递增）；**拒绝 `fix-` 前缀** |
| `change_type` 枚举 | `bootstrap` / `feature` / `enhance` / `refactor`（**无 `fix`**） |
| 粒度硬指标 | TODO 数与行数超软标建议拆、超硬标必须拆；数值以 `eo-shared/granularity.md` 为准 |
| 状态流转 | `draft → confirmed → implementing → done → archived`（**skill 自动流转**，用户不手改 frontmatter） |
| trivial 直改 | 满足硬判据（不改行为/接口/数据、无方案权衡、单会话）→ 不开 change，直改 + commit |
| 归档不反写 | archive 只更新活文档 + 冻结 change；spec 概念已移除 |

### 为什么修 bug 要喊 /eo-fix，而不是直接改？

诚实的回答：**大多数 bug 确实就该直接修，fix 对一个 typo 的开销也确实趋近于零**。它的存在不是流程仪式，而是三层「按需付费」的保险——不触发的层根本不会执行：

1. **落点记账（唯一必做，约 30 秒）**：修完勾对应 change 的 TODO/AC、commit 带 `[change-id]` 或 `fix:` 前缀。没有这层，实施中的 change 会和代码悄悄漂移（archive 的 AC 门禁对不上账）、commit 无法归集、直改流量无从统计——整个闭环的输入就断了。
2. **误修保险（仅「行为不对」类分歧时触发）**：裸改代码最危险的失败不是修错，是**静默推翻有意设计**——你说「列表怎么把归档项也显示了，去掉」，但那是上个 change 的 AC 白纸黑字特意做的。fix 在推翻一个行为前会花几百 token 取证（口述 > AC > state 佐证 > git 归属），是有意的就会停下来告诉你：「要推翻它，这是需求变更」。报错、崩溃这类明显缺陷**不走**这层，直接修。
3. **深挖方法论（仅难缠 bug 触发）**：复现不稳、多因纠缠时升级系统化调查（固定复现 → 假设清单 → 二分排除 → 验证还原），插桩和 bisect 结束后还原现场。

外加一个顺手的福利：fix 启动时会撞一下 lessons 的 trigger 索引——同类坑踩过的，答案直接送到上下文里。

---

## 两种 review 的边界

| Skill | 审查对象 | 核心问题 | 上下文 | 强制 / 可选 |
|-------|---------|---------|-------|------------|
| `/eo-change-review` | 某个 change 的 `change.md` | **方案**对不对？AC 质量、粒度合规、TODO↔AC 映射？ | 单 change | 全程可选（高风险建议走） |
| `/eo-review` | change 实施后的代码 | **代码**对不对？实现 vs AC？ | 单 change 的 diff | 每个 change 强制 |

关注点、上下文、回退动作完全不同，**不要混用**。

---

## 跨 agent 协作（eo-flow）

`/eo-flow <action>` 把单个步骤甩给另一个 tmux pane 里的 codex agent 执行，本 pane 继续做别的。典型场景：Claude pane 做 change 起草，Codex pane 做 implement/test/review。

**前置**：

- 装好 `tmux` + [smux](https://github.com/ShawnPana/smux)（提供 `tmux-bridge` CLI）
- 已有一个跑着 codex 的 tmux pane

**用法示例**：

```
/eo-flow implement   # 甩 implement 给 codex pane
/eo-flow test        # 甩 test 给 codex pane
/eo-flow review      # 甩 review 给 codex pane
```

eo-flow 会：

1. 找到（或新建）codex pane，校验 label
2. 派发指令并附带"回包合约"（codex 完成后通过 `tmux-bridge message` 回到本 pane）
3. 立刻把"派了什么、等谁回包"告诉用户
4. 收到回包后**读产出文件**做决策（不要只信回包字面）

**关键约束**：eo-* skill 本身不懂 smux（要能在没 tmux 的机器上独立跑）；"回包合约"由 eo-flow 在每次派发的附言里手动注入，**不要去改 eo-* skill 的 SKILL.md**。

---

## 会话交接（eo-handoff）

`/eo-handoff` 在 `/clear` 之前生成最小可恢复快照到 `<repo>/tmp/eo/handoff/<topic>.md`，让下一个会话载入这一个文件就能从当前节点继续。**不是对话总结**，而是定向提取「当前状态 + 决策口径 + 下一步动作」，主动丢弃探索过程。

和容易混淆的两个东西的边界：

| 名称 | 对端 | 性质 |
|------|------|------|
| 内置 `/compact` | 同一会话续命 | 机械压缩对话流，保留所有信息 |
| `/eo-flow` | 同时存在的另一个 agent (codex pane) | 跨 agent 任务派发 |
| `/eo-handoff` | clear 之后的下一个会话（"未来的自己"） | 跨会话状态交接 |

**何时用**：
- 当前对话快满了，但任务还没收尾，想 `/clear` 重启
- 一个跨多次会话的长任务，每次结束前留个交接文件
- `/compact` 留下的信息密度太低、噪音太多

**横切性**：和 dev track 任意节点正交，brainstorming / change / implement / test / review 任一阶段都可触发；不依赖 `.eo-project.json`，任何 git 仓库都能用。

输出为 6 段固定骨架（当前状态 / 基线 / 下一步分叉 / **关键口径清单**⭐ / 开机动作序列 / 明确不写的）——核心价值在 §4：探索过程可以丢，收敛出来的决策不能丢。骨架细节与写法以 `eo-handoff/SKILL.md` 为准，此处不复写。

---

## 项目管理 skill

全部基于 `.eo-project.json` 的 `project_root` 定位：

| Skill | 用途 | 落到哪 |
|-------|------|-------|
| `/eo-project-update` | 进度、阶段、决策、阻塞 | `roadmap.md` / `phases/` / `decisions/` / `log.md` |
| `/eo-project-lesson` | 经验教训 | `lessons/` |

---

## 文档体系（eo-doc-manager）

维护 `eo-doc/` 代码侧文档：

- `sync` — 增量同步（基于 git diff，只更新变化的部分）
- `re-sync` — 全量重建（改架构后用）
- `init` — 初始化骨架（一般由 `eo-project-init` 触发，单独跑用于补建缺失目录）

详细维护策略见各 reference 文档：[git-sync](../eo-doc-manager/references/git-sync.md) / [re-sync](../eo-doc-manager/references/re-sync.md) / [maintenance](../eo-doc-manager/references/maintenance.md) / [splitting](../eo-doc-manager/references/splitting.md) / [templates](../eo-doc-manager/references/templates.md)。

---

## 看板与 GitHub 联动（opt-in）

两套联动全部通过 `.eo-project.json` 的 `board` / `github` 段逐项目开启，缺省关闭，机制正文见 `eo-shared/board-github.md`：

- **Obsidian 看板**（vault 模式）：各流程 skill 在 change 状态流转时向 `<project_root>/board/` upsert stub 卡片（change frontmatter 的投影，零双写）；呈现层在 Obsidian 用 Bases + Kanban Bases View 配置一次（指南：`eo-project-init/references/board-setup.md`），支持多项目聚合与泳道。后开开关时由 `/eo-project-init` 历史同步全量重建 stub。
- **GitHub**：change 层一对一 issue（confirmed 建、编号回写去重、archive 兜底关）；PR 按 `github.pr` 策略（`auto` = 非默认分支自动建，body 含 AC 勾选清单与条件性 `Closes`——AC 全勾才关 issue）。**本地文件是唯一真相源**，严格单向推送，唯一逆向通道是漂移检测告警。

---

## Skill 安装结构

所有 skill 遵循 Claude Code skill 规范：

```
<skill-name>/
├── SKILL.md     ← frontmatter 声明 name / description，正文为执行说明
└── references/  ← 详细指南（按需读）
```

全局安装位置：`~/.claude/skills/<skill-name>/`（推荐软链到本仓库管理，见 [README 安装章节](../README.md#安装)）。

在 Claude Code 中通过 `/<skill-name>` 触发。
