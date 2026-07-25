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
- [会话交接（eo-handoff）](#会话交接eo-handoff)
- [项目管理 skill](#项目管理-skill)
- [文档体系（eo-doc-manager）](#文档体系eo-doc-manager)
- [看板与 GitHub 联动（opt-in）](#看板与-github-联动opt-in)
- [多项目总览与生态注册表（eo-board --all）](#多项目总览与生态注册表eo-board---all)
- [Skill 安装结构](#skill-安装结构)

---

## 运行模式：local vs vault

| 模式 | 触发条件 | 项目管理侧落在哪 | 软链 |
|------|---------|---------------|------|
| **local**（默认） | 缺省推荐——未显式配 `default_mode: "vault"` 时 init 询问推荐它 | 仓库内 `.eo-project/`（缺省随仓库提交；明确不想提交才进 `.gitignore`） | 不建 |
| **vault** | `~/.eo/config.json` 有 `vault_root` 且用户在 init 询问中选它 | `<vault_root>/<projects_subdir>/<project_name>/` | 默认在 `<repo>/<doc_root>/vault` 建指向 `<project_root>`（整目录单点挂，`create_symlink` 控制） |

配置约定：

- **用户级**：`~/.eo/config.json`（`vault_root` / `projects_subdir` 等；同时承载 eo-platform 等生态侧状态）
- **项目级**：`.eo-project.json`（每项目一份，提交进仓库，所有 skill 读它）
- **项目级个人覆盖**：`.eo-project.local.json`（可选，不提交；顶层字段覆盖 `.eo-project.json`，协作时放 `project_root` / `mode` 等机器相关字段）
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
├── roadmap.md     # 必建（frontmatter 含 status/phase/summary——项目级总览由 Bases 聚合它，旧手工看板已退役）
├── backlog.md     # 必建（待办池 + 灵感）
├── phases/        # 按需
├── decisions/     # 按需（eo-project-record 维护，带 INDEX）
├── lessons/       # 按需（eo-project-record 维护，带 INDEX）
├── brainstorm/    # 按需
├── board/         # 按需（change 看板 stub，sync.obsidian 启用时自动维护）
├── research/      # 按需（调研沉淀，recall/change 消费）
└── docs/          # 按需（PRD、设计、规划）
```

---

## 开发工作流（Dev Track）

一条以 **change 工件**为中心的代码侧开发流水线：每次变更以 `change.md`（验收清单 + TODO）独立承载，归档时更新活文档（state / agent-handbook）并冻结 change 目录——**不反写任何 spec**。

### 设计理念（v2）

1. **代码是唯一真相源** — state/ 与 agent-handbook/ 是活文档，永远可从代码再生；change 是过程工件，归档即冻结
2. **验收驱动** — change 的第一个产出物是用户视角验收清单（AC），它是 implement 的完成判据、review 的检查表、fix 的期望行为锚点
3. **三档渐进式严谨** — 文档重量与变更粒度挂钩：trivial 直改零工件；轻档 change（tier: light）只有意图 + AC，测试锁定验收、收口即归档；全档必填仅 3 节、其余条件化。判档表见 eo-shared/granularity.md §5
4. **量化粒度** — TODO 3-7 理想 / 10 硬上限，超标拆 change 序列
5. **fix 直接修复** — bug 口喷给 `/eo-fix`，定位后直接修；难缠 bug 自动升级深挖模式；实为需求变更才转 change
6. **并行友好拆解** — 并行判据是「互不干扰」（文件集不相交 + 无逻辑依赖）而非依赖图：全档 Batch 标同层并行组（`2a`/`2b`），超标拆出的 change 序列标「可与 #N 并行」；派发（worktree 隔离）与合流 checkpoint 归 eo-loop。单一来源 eo-shared/granularity.md §6

### 产物目录（代码侧）

```
eo-doc/changes/
├── INDEX.md                ← 项目级 change 时间线
└── <change-id>/            ← kebab-case slug 即 id（frontmatter 另有 seq 显示别名 #N）
    ├── change.md           ← 速览 + 意图 + AC + TODO（+ 条件节）
    ├── change-review.md    ← 方案审查（可选）
    ├── test.md             ← 测试报告
    ├── review.md           ← 代码审查结论
    ├── acceptance.md       ← 人工验收单（有「人工:」AC 时）
    └── design/             ← 本 change 的高保真稿（可选）
```

### Skill 职责速查

| Skill | 触发时机 | 产出 | 备注 |
|-------|---------|------|------|
| `/eo-project-init` | 项目首次使用 eo-skills | `.eo-project.json` + 双侧骨架 | **所有 skill 的前置** |
| `/eo-brainstorming` | 想法不成形 / 新项目从零起步 | 已钉决策 + 首批 change 草案（捕获出口；视觉/UI 结论可移交 /eo-design） | 可选前置 |
| `/eo-change` | 发起变更（bootstrap / feature / enhance / refactor） | `changes/<NN>-<slug>/change.md`（轻档 = 意图 + AC；全档 = 速览 + AC 前置 + TODO 分批，可并行批标 `2a`/`2b`） | trivial 短路直改；轻/全判档见 granularity §5；确认时对话亮速览 + AC |
| `/eo-change-review` | change draft 完成后、implement 前的方案审查 | `change-review.md` | ✅ 可选 |
| `/eo-implement` | 全档按 Batch 分批实施；轻档走轻模式（含 bug 修复循环） | 代码 + 勾选 TODO/AC + 人工验收单（有人工项时）；轻档收口即归档 | 批末 checkpoint（**只跑轻验证**，跑为主写为例外） |
| `/eo-fix` | 发现 bug（口喷即可） | 快路**直接修复** + 落点记账；语义分歧才取证；难缠 bug 自动深挖 | 需求变更转 change |
| `/eo-test` | 运行测试 / 场景验证 | `test.md`（以 AC 为锚 + 读码取输入） | **重验证唯一执行者**；单测**审计 + 补缺，不重写**；失败 → 回 implement |
| `/eo-review` | 实施后的**代码**审查 | `review.md` | 全档强制；轻档由 implement 完成门独立复核替代 |
| `/eo-archive` | 代码审查/完成门通过后归档 | 触发 doc sync 更新 state/handbook + 冻结 change | 人工验收唯一硬门；不反写 spec；轻档走轻档门验完成门留痕（收口自动触发） |
| `/eo-design` | 设计系统 / 视觉方案 / 高保真 / 设计审计 | `DESIGN.md`（真相源）+ HTML 工件 + CLAUDE.md 约束注入 | init / variants / apply / audit 四模式 |
| `/eo-recall` | 「当时怎么设计的 / 逻辑怎么实现的 / 为什么这么定」 | 只读问答：分层作答带出处；可出 mermaid / HTML 解释页 | 活文档的消费入口；吸收原 doc-manager query |
| `/eo-loop` | 把多个节点串起来循环推进到收敛（如 implement→test→review 至 P0/P1 清零） | 总控调度 + `tmp/eo/loop/<slug>/journal.md` 进度报告留痕 | ✅ 可选；无状态总控，基底可插拔（子 agent / codex / orca），worker 零回报义务（总控主动观测），调度偏好自动沉淀；并行收敛组（互不干扰的同层批 / change）多 worker 并行，worktree 隔离 + 合流校验 |

### 典型流程图

```
项目启动：  /eo-project-init      →  .eo-project.json + 双侧最小骨架
            │
（可选）：  /eo-brainstorming     →  已钉决策 + 首批 change 草案（新项目 = 多个 bootstrap change）
            ▼
发起变更：  /eo-change            →  changes/<NN>-<slug>/change.md
            │                         速览（人读 30 秒入口）+ AC 前置 + TODO 分批 + 粒度校验
            │                         互不干扰的批标同层并行组（Batch 2a/2b，granularity §6）
            │                         （trivial → 主动短路成直改，不产生工件）
            │                         （轻档 tier: light → 探针对齐后走 implement 轻模式：
            │                           测试锁定 → 实施 → 完成门 → finalizer 收口即归档，不经下方各环节）
            ▼
方案审查：  /eo-change-review     →  change-review.md（可选）
            │                         P0 → 回 eo-change 修（复审默认增量核销，≤3 轮；P1 移交起草方裁决）
            ▼
确认：      （对话亮速览 + AC 确认，skill 自动置 status: confirmed）
            ▼
实施：      /eo-implement         →  按 Batch 写代码 + 勾 TODO/AC（**只跑轻验证**），批末 checkpoint
            │                         重验证项（起服务 / 多环境组合 / 点击流）不跑，留给 eo-test
            ▼
验证与审查：**两条链路，无固定默认**，agent 按本 change 的风险面择一
            │
            ├─ 链路 A：/eo-test → /eo-review
            │    行为面广、重验证项多，主要风险是「跑不跑得通」→ 先把矩阵跑完再审码
            │
            └─ 链路 B：/eo-review → /eo-test
                 逻辑密集、边界多（算法 / 数据处理 / 协议解析），主要风险是「想没想到」
                 → review 读码为主、不起环境，便宜且早暴露；P0 早修，test 只跑终版不白跑
            │
            │    /eo-test   → test.md（**重验证唯一执行者**，环境矩阵一次跑完；单测审计 + 补缺；失败 → 回 implement）
            │    /eo-review → review.md（AC 覆盖 + 代码质量；P0/P1 → 回 implement 修）
            ▼
归档：      /eo-archive           →  AC 全勾 + 人工验收硬门 → commit 区间 → doc sync
                                     更新 state/ + agent-handbook/
                                     冻结 change（status: archived，不反写 spec）
```

### 关键约束

| 约束 | 说明 |
|------|------|
| `.eo-project.json` 存在 | 所有 eo-* skill 的前置。找不到 → 报错 |
| `change-id` 命名 | kebab-case **slug 即 id**（目录/commit 前缀/stub 文件名用它，创建时查重）；frontmatter `seq` 是显示别名（#N，允许 worktree 并行撞号、INDEX 更新时自愈）；**拒绝 `fix-` 前缀**；存量数字前缀 id 冻结兼容 |
| `change_type` 枚举 | `bootstrap` / `feature` / `enhance` / `refactor`（**无 `fix`**） |
| 粒度硬指标 | TODO 数与行数超软标建议拆、超硬标必须拆；数值以 `eo-shared/granularity.md` 为准 |
| 状态流转 | 主路径 `draft → confirmed → implementing → reviewed → archived` + 显式回退边（`reviewed →(阻塞反馈) implementing`、`implementing →(回炉) draft`，见 conventions.md §3）。**skill 自动流转**，用户不手改 frontmatter；reviewed = 代码审查已过、待人工验收/归档。看板列序另含最前端的 `backlog` 列 |
| trivial 直改 | 满足硬判据（不改行为/接口/数据、无方案权衡、单会话）→ 不开 change，直改 + commit |
| 归档不反写 | archive 只更新活文档 + 冻结 change；spec 概念已移除 |
| 人工验收门 | manual 类 AC（「人工:」标记）只有用户能勾；implement 完成时生成人工验收单 `acceptance.md`（软门不阻塞），archive 是唯一硬门；全 auto 的 change 不生成不打扰（规范见 `eo-shared/acceptance.md`） |
| 三级验证归属 | AC 按**「谁在哪个阶段勾」**分流：`auto-light`（implement 批末）/ `auto-heavy`（**eo-test** 一次跑完；起服务·多环境组合·点击流）/ `manual`（用户在验收单勾）。light/heavy **不在起草期标注**——由 agent 读「验证」栏当场判，判不准按 heavy。三方勾选权不重叠 = 同一件事不会被两个阶段各跑一遍；**测试编写同理单一归属**——implement 批末跑为主写为例外，回归资产沉淀归 eo-test（审计 + 补缺、按风险分层，不重写）（规范见 `eo-shared/ac-spec.md`） |
| 环境不归 agent 所有 | 重验证的环境**假定已就绪**：探测复用、用完不停，只在换环境组合时重启；起停命令与代价是**项目特异知识**，记成项目 lesson 由 implement/test/fix 的 lessons 消费步骤自动送达，不写进通用 skill |
| 并行纪律 | 并行只发生在**互不干扰**处（文件集不相交 + 无逻辑依赖，granularity §6）：同层批派发前文件集机械校验、一 worker 一独立 worktree、层末合流 checkpoint；多 change 并行圈收敛组归 eo-loop；判不准不并行，串行是安全缺省 |

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

## 会话交接（eo-handoff）

`/eo-handoff` 在 `/clear` 之前生成最小可恢复快照到 `<repo>/tmp/eo/handoff/<topic>.md`，让下一个会话载入这一个文件就能从当前节点继续。**不是对话总结**，而是定向提取「当前状态 + 决策口径 + 下一步动作」，主动丢弃探索过程。

和容易混淆的两个东西的边界：

| 名称 | 对端 | 性质 |
|------|------|------|
| 内置 `/compact` | 同一会话续命 | 机械压缩对话流，保留所有信息 |
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
| `/eo-project-record` | 项目记忆：关键决策 + 经验教训 | `decisions/` + `lessons/`（各带 INDEX，供 recall/change/fix 消费） |

---

## 文档体系（eo-doc-manager）

维护 `eo-doc/` 代码侧文档：

- `sync` — 增量同步（基于 git diff，只更新变化的部分）
- `re-sync` — 全量重建（改架构后用）
- `init` — 初始化骨架（一般由 `eo-project-init` 触发，单独跑用于补建缺失目录）

详细维护策略见各 reference 文档：[git-sync](../eo-doc-manager/references/git-sync.md) / [re-sync](../eo-doc-manager/references/re-sync.md) / [maintenance](../eo-doc-manager/references/maintenance.md) / [splitting](../eo-doc-manager/references/splitting.md) / [templates](../eo-doc-manager/references/templates.md)。

---

## 投影同步（eo-sync，opt-in）

投影目标（Obsidian 看板卡 / GitHub issue/PR）由 `eo-sync` 单命令统一同步——**逐流转投影已退役**，触发点收敛为三个：archive 收口自动 `eo-sync run` 一次、任意时刻手动 `eo-sync run`（`--dry-run` 看计划）、`eo-sync watch` 自动档（下述）。目标经 `.eo-project.json` 的 `sync` 段逐项目 opt-in（存量 legacy `board` / `github` 段经兼容映射仍生效，新配置由 init 只写 `sync` 段），缺省关闭；投影内容见 `eo-shared/board-github.md`（内置适配器实现说明），协议契约见 `docs/sync-adapter-protocol.md`。第三方在 PATH 放一个 `eo-sync-<name>` 可执行并在配置启用即可接入新目标。

- **Obsidian 看板**（vault 模式）：`eo-sync-obsidian` 把 change frontmatter 投影为 `<project_root>/board/` 的卡片（整文件重写、幂等）；呈现层在 Obsidian 用 Bases + Kanban Bases View 配置一次（指南：`eo-project-init/references/board-setup.md`），支持多项目聚合与泳道。开启开关时由 `/eo-project-init` 调 `eo-sync run` 做历史同步。
- **GitHub**：`eo-sync-github` 投影 change 层一对一 issue（confirmed 起建、编号回写去重、archive 兜底关）；PR 按 `github.pr` 策略（`auto` = 非默认分支自动建，body 含 AC 勾选清单与条件性 `Closes`——AC 全勾才关 issue）。**本地文件是唯一真相源**，严格单向推送，唯一逆向通道是漂移检测告警。

### watch 自动档（eo-sync watch）

`eo-sync watch [--interval N] [--all | --project <path>]`——呈现层自费的 pull 常驻进程，让状态流转在一个轮询间隔（默认 10 秒，下限 1）内自动上板；六个流程 skill 的零投影负担不变（写路径不为呈现层付费）。

- **键短路**：每轮以 eo_lib freshness 键与上一基线比对，键不变零成本跳过（短路轮零输出）；键变才进程内调用既有 `run` 编排，stderr 打一行诊断。首轮无基线视为键已变（启动即追平停摆积压）。
- **基线口径**：run 退出 0/1 后**重算**键，与 run 前键一致才记为基线；不一致说明同步窗口内出现了无法归因于本次 run 的新状态（第三方流转或自身回写，键粒度无法区分，一律视为不能证明）——不记基线，下一轮重 run（幂等，多跑一轮无害且必然追平），**绝不把未投影的流转吸收进基线**；锁占用（退出 2）与异常轮同样不记基线、下一轮自动重试。
- **锁**：复用 `run` 的文件锁——撞上手动/archive 的 run 时本轮跳过该项目，不崩溃不等待。
- **作用域**：缺省 = cwd 所在项目；`--project <path>` 任意目录只追平指定项目；`--all` 每轮重读注册表（watch 期间新注册的项目下一轮即纳入），无需在项目内运行。
- **故障隔离与告警抑制**：`--all` 下单项目配置缺失/非法只告警并跳过该项目；同一（项目, 错误指纹）常驻期间只告警一次不刷屏，项目恢复（成功完成一次 run）即清除抑制记录、自动重新纳入。
- **常驻形态**：前台进程，SIGINT/SIGTERM 干净退出；launchd/systemd 守护化留待真实需求。

---

## 多项目总览与生态注册表（eo-board --all）

多项目枚举基于用户级注册表 `${EO_HOME:-$HOME/.eo}/projects.json`（schema v1：`{"version": 1, "projects": [{"name", "path", "registered_at"}]}`），eo-board 与 `eo-sync watch --all` 共用同一张表：

- **登记**：`/eo-project-init` 成功时顺手注册（失败不阻塞 init，输出补注册指引）；`eo-board --register [path]` / `--unregister [path]` 手工维护（缺省 path=当前目录）。去重键 = 规范化 repo identity（git common dir realpath），同一仓库任意 worktree 重复 register 幂等；注册表写入不破 eo-board 只读铁律（铁律管项目仓库文件，注册表是用户级生态文件、仅显式动作写入）。
- **聚合**：`eo-board --all` 任意目录一屏总览——每注册项目一行（项目名 + draft/confirmed/implementing/reviewed 计数 + archived 总数 + backlog 数 + as-of 新鲜度戳），失效项目行内报错不中断；v1 仅终端形态（`--html`/`--serve` 聚合未做，等真实需求）。
- **下钻**：`eo-board --project <路径|注册名>` 等价于在该项目目录运行，三形态通用；注册名命中多个项目时报歧义并列候选路径（不静默取第一项）。
- **扫描兜底**：`eo-board --all --scan <父目录>` 把含 `.eo-project.json` 的一层子目录临时并入本次聚合并提示可注册，**不写注册表**。

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
