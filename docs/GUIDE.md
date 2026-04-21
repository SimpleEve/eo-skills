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
- [三种 review 的边界](#三种-review-的边界)
- [跨 agent 协作（eo-flow）](#跨-agent-协作eo-flow)
- [会话交接（eo-handoff）](#会话交接eo-handoff)
- [项目管理 skill](#项目管理-skill)
- [文档体系（eo-doc-manager）](#文档体系eo-doc-manager)
- [实验中的 skill](#实验中的-skill)
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
├── agent-handbook/   # 必建，代码架构（AI 地图）
├── dev/              # 必建，spec / change / review 流
├── templates/        # 必建（空），eo-* 扩展点
└── state/            # 按需，系统当前状态（原 doc/，首次 sync 时建）
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

一套基于 **OpenSpec 风格 Delta 机制**的代码侧开发流水线：**模块（module）是一等公民**，每个模块在 `eo-doc/dev/<module-name>/` 下有一份活文档 `spec.md`；每次业务变更以 `change.md` 的形式独立归档，归档时由 `eo-archive` 把 Delta 机械合并回 spec。

### 设计理念

1. **模块是一等公民** — 所有开发产物归属到 `eo-doc/dev/<module-name>/`
2. **spec 是活文档** — 不重写，只增量演化（ADDED / MODIFIED / REMOVED）
3. **change = proposal + plan** — 一份文档同时承载需求澄清、技术方案、TODO 拆解
4. **fix ≠ change** — bug 修复是 `eo-implement` 的内嵌职责，不开新 change、不产生 Delta
5. **change 无独立 review** — 作者自澄清即可发起；实施后的 `/eo-review` 是唯一正式审查

### 产物目录（代码侧）

```
eo-doc/dev/
└── <module-name>/              ← 一个业务模块 = 一个目录
    ├── spec.md                 ← 活文档：模块当前能力快照（工程视角）
    ├── spec-review.md          ← 仅模块初始化时一次性审查（可选）
    └── changes/
        ├── INDEX.md            ← 模块内 change 时间线
        └── <NNN-change-id>/    ← 数字前缀 + kebab-case（无 fix- 前缀）
            ├── change.md       ← Spec Delta + 技术方案 + TODO + AC
            ├── implement.md    ← 偏差记录（可选）
            ├── test.md         ← 测试报告
            └── review.md       ← 代码审查结论
```

### Skill 职责速查

| Skill | 触发时机 | 产出 | 备注 |
|-------|---------|------|------|
| `/eo-project-init` | 项目首次使用 eo-skills | `.eo-project.json` + 双侧骨架 | **所有 skill 的前置** |
| `/eo-module-init` | 新模块首次落地 | `spec.md` + `spec-review.md`（一次性） | 内部调用 `eo-spec` + `eo-spec-review` |
| `/eo-spec` | 模块内部：撰写 spec | 被 `eo-module-init` 调用 | 一般不直接调 |
| `/eo-spec-review` | 模块初始化时**必须**；archive 后 Delta 大改时**可选** | `spec-review.md` | 复检可选 |
| `/eo-change` | 已有模块的业务变更 | `changes/<NNN-xxx>/change.md` | 支持 bootstrap / feature / enhance / refactor |
| `/eo-change-review` | change draft 完成后、implement 前的方案审查 | `change-review.md` | ✅ 可选 |
| `/eo-implement` | 按 change.md TODO 实施（含 bug 修复循环） | 代码 + 可选 `implement.md` | — |
| `/eo-test` | 运行测试 / 场景验证 | `test.md` | 失败 → 回 implement |
| `/eo-review` | 实施后的**代码**审查 | `review.md` | 强制 |
| `/eo-archive` | 代码审查通过后归档 | Delta 合并回 `spec.md` + 更新 INDEX | bootstrap 仅元信息更新 |

### 典型流程图

```
项目启动：  /eo-project-init      →  .eo-project.json + 双侧最小骨架
            │
新模块：    /eo-module-init       →  spec.md（含 spec-review 一次性）
            ▼
首批实现：  /eo-change (bootstrap)→  changes/NNN-xxx/change.md
            │                         §3 写"实现范围"，认领 spec 章节
            ▼
后续演化：  /eo-change (feature/  →  changes/NNN-xxx/change.md
            enhance/refactor)        §3 写 Delta（ADDED/MODIFIED/REMOVED）
            ▼
方案审查：  /eo-change-review     →  change-review.md（可选）
            │                         P0/P1 → 回 eo-change 修
            ▼
approve：   （用户改 status: approved）
            ▼
实施：      /eo-implement         →  代码 + 勾选 TODO
            ▼
测试：      /eo-test              →  test.md（失败 → 回 implement）
            ▼
代码审查：  /eo-review            →  review.md
            │                         P0/P1 → 回 implement 修
            ▼
归档：      /eo-archive           →  bootstrap：仅元信息更新（spec 不动）
                                     其他类型：Delta 合并回 spec.md
                                     status: archived
```

### 关键约束

| 约束 | 说明 |
|------|------|
| `.eo-project.json` 存在 | 所有 eo-* skill 的前置。找不到 → 报错 |
| `change-id` 命名 | `NNN-kebab-name`（3 位数字前缀，按模块内递增）；**拒绝 `fix-` 前缀** |
| `change_type` 枚举 | `bootstrap` / `feature` / `enhance` / `refactor`（**无 `fix`**） |
| §3 内容由 type 决定 | `bootstrap` 写"实现范围"；其余三类写 Delta |
| 单次聚焦 | 一个 change 只做一件事 |
| 状态流转 | `draft → approved → implementing → done → archived` |
| spec 只由 archive 修改 | change 期间不直接改 `spec.md` |
| 跨模块 | 一个 change 只能归一个模块；跨模块需求拆多个 change，用 `depends_on` 串联 |

---

## 三种 review 的边界

| Skill | 审查对象 | 核心问题 | 上下文 | 强制 / 可选 |
|-------|---------|---------|-------|------------|
| `/eo-spec-review` | 模块 `spec.md`（活文档基线） | **需求**对不对？业务自洽吗？ | 模块整体能力 | module-init 时强制；后续可选 |
| `/eo-change-review` | 某个 change 的 `change.md` | **方案**对不对？Delta 和实施方案一致吗？ | 单 change | 全程可选（高风险建议走） |
| `/eo-review` | change 实施后的代码 | **代码**对不对？实现 vs AC？ | 单 change 的 diff | 每个 change 强制 |

关注点、上下文、回退动作完全不同，**不要混用**。

---

## 跨 agent 协作（eo-flow）

`/eo-flow <action>` 把单个步骤甩给另一个 tmux pane 里的 codex agent 执行，本 pane 继续做别的。典型场景：Claude pane 做 spec/change，Codex pane 做 implement/test/review。

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

`/eo-handoff` 在 `/clear` 之前生成最小可恢复快照到 `<repo>/tmp/<topic>-handoff.md`，让下一个会话载入这一个文件就能从当前节点继续。**不是对话总结**，而是定向提取「当前状态 + 决策口径 + 下一步动作」，主动丢弃探索过程。

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

**横切性**：和 dev track 任意节点正交。spec / change / implement / test / review 任一阶段都可触发。

**输出骨架**（6 段固定）：

| 段 | 内容 |
|---|------|
| §1 当前状态 | 在哪个节点，关键产物路径 + status |
| §2 基线 | git HEAD、工作目录状态、关键文件清单 |
| §3 下一步分叉 | 等用户决策的候选方案（A/B/C） |
| §4 关键口径清单 ⭐ | 跨 clear 必须保持的决策与不变量；每条带「为什么」 |
| §5 开机动作序列 | clear 后第一组有序动作 |
| §6 明确不写的 | 主动丢弃了什么，让用户最后检查 |

§4 是核心价值：探索过程可以丢，但收敛出来的决策不能丢。

**不依赖 `.eo-project.json`**：`tmp/` 是工作区机制，任何 git 仓库都能用，即使没跑过 `/eo-project-init` 也能用。

**tmp/ 由用户管**：默认覆盖同名文件；不自动清理；不进 `.gitignore`（项目自决）。

---

## 项目管理 skill

全部基于 `.eo-project.json` 的 `project_root` 定位：

| Skill | 用途 | 落到哪 |
|-------|------|-------|
| `/eo-project-update` | 进度、阶段、决策、阻塞 | `roadmap.md` / `phases/` / `decisions/` / `log.md` |
| `/eo-project-lesson` | 经验教训 | `lessons/` |
| `/eo-miniapp-ideation` | 微信小程序方向构思 | `docs/` |

---

## 文档体系（eo-doc-manager）

维护 `eo-doc/` 代码侧文档：

- `sync` — 增量同步（基于 git diff，只更新变化的部分）
- `re-sync` — 全量重建（改架构后用）
- `init` — 初始化骨架（一般由 `eo-project-init` 触发，单独跑用于补建缺失目录）

详细维护策略见各 reference 文档：[git-sync](../eo-doc-manager/references/git-sync.md) / [re-sync](../eo-doc-manager/references/re-sync.md) / [maintenance](../eo-doc-manager/references/maintenance.md) / [splitting](../eo-doc-manager/references/splitting.md) / [templates](../eo-doc-manager/references/templates.md)。

---

## 实验中的 skill

以下 skill 仍在调试，**暂不推荐用于生产工作流**：

- `/eo-brainstorming` — 头脑风暴 / 想法对抗与拆解；产出在项目内 `brainstorm/`。
- `/eo-workflow` — 多 pane tmux 全流程自动编排（比 `/eo-flow` 更重）。

如果只想做"单点把一步甩给另一个 pane"，请用 `/eo-flow`（已稳定）。

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
