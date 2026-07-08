# eo-skills v2 详细设计

> 状态：draft（待逐节评审）
> 日期：2026-07-07
> 输入：vault/eo-skill/research/v2/（现状盘点 + 5 竞品调研）、vault/eo-skill/decisions/v2/（6 个已钉决策）

---

## 0. 设计原则

1. **代码是唯一真相源**。文档分两类：**活文档**（state/、agent-handbook/，永远可以从代码再生）和**过程工件**（change 目录，随变更生灭，归档即冻结为审计历史，从不合并回任何地方）。
2. **渐进式严谨（条件性工件）**。文档重量必须与变更粒度挂钩：简单变更只写必填节，方案、流程图、风险等章节只在满足显式触发条件时才产出。
3. **事实自查、决策上抛**。能从代码 / state / handbook 查到的信息禁止问用户；只把真正的决策交给用户，且每问附推荐答案。
4. **验收驱动**。每个 change 的第一个产出物是用户视角的验收清单（AC），它同时是 implement 的完成判据、review 的检查表、fix 的期望行为锚点——AC 接替了 v1 中 spec 的「期望行为基线」职责。
5. **量化粒度**。「一个 change 只做一件事」升级为可校验的数字指标（采用 spec-kitty 数值），超标强制拆分。
6. **状态自动流转**。change 的 status 由 skill 在对话确认后自动写入，用户不再手改 frontmatter（v1 一次 change 手改 ≥5 次是纯摩擦）。
7. **skill 保持干净**。SKILL.md 及 references/ 正文只含操作指令与**运行时文件引用**（references/、eo-shared/ 等随包分发的文件，用可解析的相对路径）；设计稿引用、决策编号、调研出处、写作时的思路来源——这些杂物一律不进 skill，它们的家在 docs/ 与 vault。（临时例外：重构期的「v2 过渡状态」横幅，重写时随之删除。）

---

## 1. 总览

### 1.1 Skill 清单变化

| Skill | v2 处置 | 说明 |
|---|---|---|
| eo-workflow | **移除** | 目录 + 4 文件 7 处引用一并清理 |
| eo-spec | **移除** | spec 职责归 change（AC 承接期望行为，brainstorming 承接首次拆解对话） |
| eo-spec-review | **移除** | 审查对象消失 |
| eo-module-init | **移除** | 模块概念取消（决策 #3）；新项目/新能力首开即 bootstrap change |
| eo-change | **重构（核心）** | 新模板 + 内嵌提问纪律 + AC 前置 + 粒度校验 |
| eo-brainstorming | **增强** | 保留全部机制，新增「捕获出口」：结论可直接拆成 change 序列 |
| eo-implement | **调整** | TODO 分批 + 批间 checkpoint + commit 纪律（推荐非强制） |
| eo-fix | **重构** | 三方对比改为 AC ↔ state ↔ 代码；普通模式直接修复（不再只诊断）；新增深挖模式（吸收 eo-investigate 候选） |
| eo-archive | **重构** | 不再反写 spec；改为「校验 → commit 区间 → 触发 doc sync → 冻结」 |
| eo-doc-manager | **增强** | 移除 dev/ 概念；sync 支持 range 与脏变更三选项；归档计数 + 一致性校验 |
| eo-test | **微调** | 测试锚点从 spec/change §6 改为 AC；其余不变 |
| eo-review | **微调** | 检查表以 AC 为锚；清理 spec/模块引用 |
| eo-change-review | **保留现状** | 决策 #1：暂不轻量化，预留观测（已入 backlog）；新增粒度超标检查项 |
| eo-project-init | **调整** | 骨架与注入内容更新；待确定问题全部走 AskUserQuestion |
| eo-design | **新增** | 四模式：init / variants / apply / audit（参考 gstack 全链路） |
| eo-flow | **保留，延后修改** | 本次只清理其中 eo-workflow 与 spec 相关引用 |
| eo-backlog / eo-handoff / eo-project-update / eo-project-lesson / eo-miniapp-ideation | 不动 | |

### 1.2 文档口径：3 → 2 + 1

| 文档 | 性质 | 维护者 | 信源 |
|---|---|---|---|
| state/ | 活文档（业务现状） | eo-doc-manager | 代码 |
| agent-handbook/ | 活文档（代码地图） | eo-doc-manager | 代码 |
| changes/<id>/ | 过程工件，归档冻结 | eo-change / eo-implement / eo-archive | 用户意图 + 决策台账 |
| DESIGN.md | 项目级设计真相源（新增） | eo-design | 设计决策 |

移除：`spec.md`、`spec-history.md`、`eo-doc/dev/<module>/` 整个模块维度。

**回答 OpenSpec 之问**（不反写后「系统现在是什么样」的唯一口径在哪）：在 state/ + agent-handbook/，由 doc-manager 以代码为唯一信源、以 commit 区间为增量单位维护。这是 v2 相对所有竞品的差异化——它们都没有这一层。

### 1.3 主流程链

```
（可选）eo-brainstorming ──捕获──▶ change 序列草案
                                      │
eo-change（提问纪律 → AC 前置 → TODO 分批拆解 → 粒度校验 → 对话确认，status: confirmed）
   │
eo-implement（按 Batch 执行，批末 checkpoint + commit；fix 循环归此）
   │
eo-test（AC 为锚）──▶ eo-review（AC 为检查表；强制）
   │
eo-archive（AC 全勾校验 → commit 区间 → doc-manager sync → 冻结 change）
```

bug 入口：eo-fix 诊断路由（→ implement 修 / 就地更新 change / 新开 change）。

---

## 2. 文档体系

### 2.1 eo-doc/ v2 目录结构

```
eo-doc/
  agent-handbook/        # 代码地图（不变）
  state/                 # 业务现状（不变）
  changes/               # 项目级扁平 change 目录（原 dev/<module>/changes/ 上提）
    INDEX.md             # 变更时间线（承接 v1 spec-history 的流水职责，只此一份）
    001-<slug>/
      change.md
      review.md          # eo-review 产物
      change-review.md   # eo-change-review 产物（可选）
      test.md            # eo-test 产物（可选）
      design/            # 本 change 相关的高保真稿（可选，eo-design 产出）
  templates/
  .sync-cursor           # doc-manager 状态（新增计数字段，见 §6）
```

- change-id：项目级三位连号 + 语义 slug（`014-batch-export`）。v1 是模块级编号，迁移见 §10。
- **跨模块判定移除**（决策 #3）：change 只挂项目。原「是否动别人的 spec」判界废弃；变更范围就是 §4 涉及文件 + AC 的辐射面。

### 2.2 DESIGN.md（仓库根）

gstack 模式：不到百行的「token + rationale + 决策日志」单文件。结构：Product Context / Aesthetic Direction / Typography / Color / Spacing / Layout / Motion / Decisions Log（日期｜决策｜理由，追加式）。约束链见 §8。

### 2.3 tmp 工件约定（tmp/eo/）

所有 skill 的临时产物收进统一命名空间，按域分子目录：

```
tmp/eo/
├── handoff/<topic>.md        # 会话交接快照（目录已表意，去掉 -handoff 后缀）
├── fix/<date>-<slug>.md      # 深挖模式调查记录
└── design/<date>-<topic>/    # 设计变体与预览 HTML
```

纪律：① tmp/eo/ 下一切**可丢弃**，任何 skill 不得当信源引用——有长期价值的结论在产生时即沉淀到正式位置（根因 → change / lessons；design 选中结论 → DESIGN.md 决策日志；handoff 被下个会话消费后即弃）；② project-init 负责把 `tmp/eo/` 写入 .gitignore；③ 文件名带日期/topic 前缀，清理按 mtime，无需登记表。多包一层 `eo/` 的理由：不侵占项目自己的 tmp/，且 `rm -rf tmp/eo` 即全量清理。

---

## 3. eo-change（核心重构）

### 3.1 流程

1. **意图理解与复杂度定级**：trivial / simple / complex / critical 四级，决定提问预算（§3.2）。critical 级建议先升级到 eo-brainstorming（决策 #2：双轨隔离，change 内只做轻量澄清）。
2. **事实自查**：先读 state/、agent-handbook/、相关代码，以及 vault lessons/ 中的相关教训（lessons 消费机制——eo-change / eo-implement / eo-fix 启动时都检索一次），把能自答的问题消化掉。
3. **预算内澄清**（§3.2 提问纪律）。
4. **产出验收清单（AC）**——先于 TODO（§3.3）。
5. **TODO 拆解 + 分批**（§3.4）。
6. **粒度自检**（§3.5），超标则提议拆成 change 序列。
7. **写 change.md**（§3.6 模板），对话中让用户确认；确认后 skill 自动置 `status: confirmed`。
8. 更新 changes/INDEX.md。

### 3.2 提问纪律（内嵌轻量版）

综合 grillme / spec-kit / spec-kitty / eo-brainstorming 决策池：

- **预算按复杂度配比**：trivial 0-1 问、simple 1-3 问、complex 3-5 问、critical 5+ 问（并建议升级 brainstorming）。每轮最多 1-2 问。
- **封闭选择一律走 AskUserQuestion**：2-4 个选项 + 推荐项标注（Recommended）；开放问题走正文，放消息末尾。
- **决策台账**：内部维护「已钉（结论+理由）/ 未钉 / defer」三态，不渲染给用户；已钉项不得重问、不得被后续讨论隐式推翻；defer 项写入 change.md §8 开放问题，**全篇上限 3 条**。
- **UI/UX 类问题**：文字难以描述时，选项末尾附「生成 HTML 对比页帮你决策」（低保真、自包含、可点选；借 superpowers visual companion 思路，产物放 tmp/ 不入库，结论回填决策台账）。
- **疲劳信号识别**：用户说「别问了 / 先做吧 / 就这样」→ 立即用合理默认推进，假设显式写入 §1 并标注「（假设）」。
- **反模式表**（写进 SKILL.md，比正面规则更有约束力）：一次塞 3+ 个问题；问代码里能查到的事实；重问已钉结论；不给选项的抽象大问题；结束不做覆盖确认。

### 3.3 验收清单（AC）规范

- **用户视角、可独立验证**，每条一个可勾选项，附验证方式。Success Criteria 风格要求技术无关（正例「用户 3 步内完成导出」，反例「API 200ms 返回」）。
- 复杂行为可附 Given/When/Then 场景（可选，不强制）。
- AC 的三重身份：implement 的完成判据（全勾才算 done）、review 的检查表、fix 的期望行为锚点（接替 v1 的 F-spec）。
- AC 先于 TODO 产出——TODO 拆解必须逐条映射到 AC（每条 TODO 标注「对应 AC-x」）。

### 3.4 TODO 拆解与分批

- TODO 按 **Batch** 分组，Batch 1 即 MVP（借 spec-kit「STOP and VALIDATE」）：跑完一批即可独立验证其对应 AC。
- 每条 TODO 四要素：描述 / 涉及文件 / 对应 AC / 完成判据。**禁止占位符**（「add error handling」「后续完善」出现即拆解失败，借 superpowers）。
- 移除 v1 的双分支（Delta/bootstrap 章节认领）× 双模式（S-C-G/层级 Part）全部结构。bootstrap 退化为一个普通 `type: bootstrap` 标记（表示从零起步，无存量代码约束），不再有任何特殊章节。

### 3.5 粒度硬指标（决策 #4，照抄 spec-kitty 试运行）

| 指标 | 理想 | 硬上限 | 超限动作 |
|---|---|---|---|
| TODO 数 | 3-7 | 10 | 必须拆 change 序列 |
| change.md 全文 | 200-500 行 | 700 行 | 必须拆 change 序列 |

- eo-change 第 6 步自动校验（wc -l + 数 TODO），超软标建议拆、超硬标拒绝确认。
- eo-change-review 增加同项检查（决策 #1 的观测点之一）。
- 拆分方式：按 AC 分组切成序列，第一个 = MVP，其余入 changes/INDEX.md 排队或进 backlog。
- **更新 vs 新开决策表**（借 OpenSpec）："Update preserves context. New change provides clarity."——意图相同的精化（发现边缘情况、方法微调、范围缩到 MVP）就地更新本 change；意图本质变化 / 范围重叠 <50% / 原 change 可独立收尾 → 新开。

### 3.6 change.md v2 模板

```markdown
---
id: 014-batch-export
title: 批量导出
status: draft        # draft | confirmed | implementing | done | archived（skill 自动流转）
type: feature        # bootstrap | feature | enhance | refactor
base_commit: ~       # eo-implement 首次执行时写入
commits: []          # eo-archive 归档时写入
created: 2026-07-07
---

# <标题>

## 1. 意图
<为什么做，1-3 段>

已钉决策（来自起草澄清 / brainstorming 捕获）：
- <决策面> → <结论>（理由：…）
- <决策面> → <结论>（假设，用户未确认）

## 2. 验收清单
- [ ] AC-1 <用户能…>（验证：…）
- [ ] AC-2 …

## 3. TODO
### Batch 1（MVP）
- [ ] TODO-1 <描述>（文件：…；对应 AC-1；完成判据：…）
### Batch 2
- [ ] TODO-4 …

## 4. 涉及文件
- path/to/file — <改动性质>

<!-- 以下为条件节，满足触发条件才写 -->

## 5. 技术方案
触发：新架构模式 / 新外部依赖 / 安全・性能・数据迁移复杂度 / 编码前有歧义。

## 6. 流程图
触发：状态机、多角色交互等「画比说清楚」的场景。

## 7. 风险与回滚
触发：不可逆操作 / 数据迁移 / 对外接口变更。

## 8. 开放问题
触发：决策台账存在 defer 项（上限 3 条）。
```

必填只有 §1-§4；模板全文（含条件节说明）控制在 ~80 行，对比 v1 的 217 行。

### 3.7 轻量路径：直改模式

问题：样式微调、布局挪动、琐碎修复这类变更，开 change + 归档全流程是纯开销。

设计——双轨，不设中间档：

- **直改模式（trivial）**：不产生任何 change 工件。定位 → 改 → 验证 → 常规 commit（建议 `fix:` / `ui:` 前缀，供 retro 统计）。文档侧安全网：doc-manager 的 cursor sync 本来就按 commit 流增量归档（与 change 无关），直改提交会被下次 sync 吸收；直改完成时报告 cursor 落后量，超过阈值（暂定 10 个 commit）建议顺手跑一次 sync。
- **change 模式**：现行 v2 流程。

分诊与护栏：

- eo-change 与 eo-fix 入口共享 **trivial 硬判据**（写入 eo-shared/granularity.md）——同时满足：①不改变用户可见的功能语义与交互逻辑（纯外观/样式、文案、多语言、重命名、格式化、显而易见的小 bug 修复都算 trivial）；②不改对外接口、不动持久化数据结构；③无需方案权衡——不产生值得记录的技术决策（一旦要做选型或权衡，就有了开 change 的理由）；④单次会话可完成。任何一条不满足 → 升级 change 模式（防「一切皆 trivial」的滑坡）。
- **文件数不设限**：按需求性质判定——多语言、全局样式调整可涉及几十个文件仍是 trivial；反之 3 个文件的逻辑重构也不是。文件数只作提示信号（量大且非机械同质改动时提醒确认一句）。
- eo-change 定级为 trivial 时主动短路：「不值得开 change，直接改」。
- UI 直改仍受 DESIGN.md 约束（改前读；eo-design audit 可事后兜底）。
- **不引入「light change」文件工件**：第三种工件类型是复杂度回潮。留痕由 commit message 承担，观测由 retro 统计前缀，都不需要新文件。

---

## 4. eo-brainstorming（增强：捕获出口）

现有机制（三层追问、每轮 1-2 问、locked/open 决策池、upstream 优先、进度报告、疲劳菜单）**全部保留**。新增：

- **捕获出口**：归档产出时，若结论指向可实施变更，提议「拆成 change 序列」——每个 change 草案含意图 + AC 草稿 + 粗粒度 TODO，第一个 = MVP（承接 v1「spec 首次拆解对话」的职责：新项目冷启动 = brainstorming → 首批 bootstrap change，可能多个）。
- 衔接机制：已钉决策直接预填充 change.md §1「已钉决策」，eo-change 起草时**跳过已钉项的重复提问**（决策台账继承）。
- 与 change 的边界（决策 #2）：change 内嵌轻量澄清应付日常；「做不做 / 方向未定 / critical 级」才升级 brainstorming。互不强制。

---

## 5. eo-implement / eo-fix

### 5.1 eo-implement

- 首次执行：写入 `base_commit`（当前 HEAD），status 自动 `confirmed → implementing`。
- **按 Batch 执行**：批末 checkpoint——验证该批对应 AC、勾选 TODO、汇报、询问「继续下一批 / 停」。
- **commit 纪律（决策 #6，推荐非强制）**：推荐一次 change 一次 commit；TODO 分批时允许一批一 commit，message 统一带 change-id 前缀（`[014] ...`），便于 archive 归集区间。
- fix 循环：change 生命周期内（含 archived 前）的 bug 修复归 implement，不开新 change（v1 定位保留）。
- 全部 TODO 完成 + AC 全勾 → 提示走 test/review；review 通过后 status 自动置 `done`。

### 5.2 eo-fix（重构：定位 + 修复一体，含深挖模式）

定位改变：v1「只诊断不改文件」的约束源于要先判「bug 属于哪个 spec」；spec 消失后判界负担不复存在，**普通模式直接完成修复**，路由只保留「这其实是业务变更」的出口。该约束删除。

三方事实：

- **F-ac**：change 验收清单声明的期望行为（活跃 change 优先，无活跃则查最近 archived change）
- **F-state**：state/ 记载的系统现状
- **F-code**：实现事实

**普通模式（快路径）**：定位原因 → 直接修复 → 验证。修复落点自动判断：有相关活跃 change → 修复计入该 change（勾选相关 TODO/AC，commit 带 change-id 前缀）；无活跃 change → 走直改路径（§3.7），常规 commit，由 doc-manager 的 cursor sync 吸收。

修复前的路由判定（仅剩这几个分叉）：

| 情形 | 动作 |
|---|---|
| 实现 bug（代码 ≠ AC，或普通缺陷） | 本 skill 内直接修复 |
| AC 写漏且 change 未 archived | 先补 AC/TODO 再修（Update preserves context） |
| 实为需求变更 / 涉事 change 已 archived 且改动非平凡 | 新开 change（New change provides clarity） |
| F-state 与 F-code 矛盾 | 文档陈旧 → 触发 doc-manager sync 后重判 |
| 原因无法定位 / 无法稳定复现 | **自动升级深挖模式** |

**深挖模式（自动升级，替代原 eo-investigate 候选）**：升级时向用户显式宣告；方法论全文在 `references/investigation.md`（固定复现 → 假设清单 → 二分排除 → 验证，借 superpowers systematic-debugging 四阶段），**仅升级时才加载**；约束信封切换——允许临时插桩、加日志、git bisect，结束后还原现场；产出调查记录（`tmp/eo/fix/<date>-<slug>.md`，见 §2.3，若关联 change 则附到其目录）；根因确认后回到普通模式路由表定归属。

保留 v1 的轻量定位纪律（INDEX + frontmatter 收敛，禁全局 grep）。

---

## 6. eo-archive / eo-doc-manager（归档闭环）

### 6.1 eo-archive v2 五层

归档的本质：**把世界结算成 commit，然后按 commit 更新文档**——archive 自己不拥有任何同步逻辑。

1. **前置校验**：status done、review.md 通过、AC 全勾（未全勾需用户显式豁免并把豁免记入 change.md §8）。
2. **工作区结算**：cursor 基于 commit，sync 只能看见已提交内容。属于本 change 的未提交改动 → 提交（带 change-id 前缀）；**无关脏改动留在工作区**（sync 默认「只取已提交增量」不会碰它们）；两类混在同一文件无法分离时问用户一次。
3. **冻结元数据并提交**：从 `base_commit..HEAD` 按 change-id 前缀归集本 change 提交、写入 frontmatter `commits`（**仅审计与 PR body 用，不决定同步范围**）；status → `archived`（不可逆）；更新 changes/INDEX.md。这些文档改动本身提交入库——单 commit 纪律下与第 2 步合为同一个 commit，implement 已按批提交时这就是一个小的收尾 meta commit。
4. **文档同步（内嵌调用，零自有逻辑）**：执行 `/eo-doc-manager sync` 的完整流程（cursor..HEAD → 推进 cursor），archive 的 SKILL.md 不复述任何同步细节——同步语义只存在于 doc-manager 一处（v1 的教训：一套逻辑多处描述必然漂移）。范围覆盖第 2/3 步的提交与期间累积的直改提交，结束时 cursor == HEAD。change.md 作为业务语境提示传入，但信源永远是代码。若中途失败：change 已冻结、cursor 未推进，手动重跑 `/eo-doc-manager sync` 即可续上（archive 只是 sync 的两个触发点之一）。
5. **收尾**：issue/PR（§14）、看板 stub（§13）、对话速报（sync 触达文档清单 + 一致性校验建议，见 §6.2 阈值）。

对比 v1 八步：Delta 解析、旧文本精确匹配、冲突三选一裁决、spec-history 双表记账全部消失。

### 6.2 eo-doc-manager v2 增强

- **移除 dev/**：不再管理模块 spec 目录；changes/ 由开发流程技能管理、不参与 sync（同 v1 约定）。
- **archive 作为 sync 触发点（无独立 range 模式）**：archive 触发的就是常规 cursor sync（cursor..HEAD，完成后推进 cursor）。不提供按 change 定界的 range 同步——若 range 同步不动 cursor，被同步的 commit 会在下次 cursor sync 被重扫；若动 cursor，又会跳过区间外交错的提交（直改、其他 change）。单游标、单机制，archive 与手动 sync 只是同一机制的两个触发点。
- **diff 分析排除 `eo-doc/` 路径**：归档元数据提交（change.md / INDEX）是纯文档变更，sync 扫到直接跳过，不做影响分析。
- **脏变更三选项**（常规 sync 检测到工作区脏时询问）：
  1. 只取 cursor..HEAD 增量，不扫脏变更（默认推荐——脏变更提交后自然会被下次 sync 覆盖，根治 v1 的二次同步与 revert 幽灵文档问题）；
  2. 含脏变更一起同步（明知代码即将定稿时用）；
  3. 全部重扫（等价小型 re-sync）。
- **归档计数**：`.sync-cursor` 增加 `sync_count`、`archive_count`；state/handbook 各文档 frontmatter 增加 `last_sync`（commit + 日期）。
- **自动一致性校验**：`sync_count` 每满 5（初始阈值，可调）或用户手动触发 → 抽查 state ↔ agent-handbook 同源文档是否前后矛盾、frontmatter summary 与正文是否漂移，报告不自动改。

---

## 7. eo-test / eo-review / eo-change-review（微调）

- **eo-test**：测试用例来源从 change §6 测试标准改为 AC 逐条推导（AC → 至少一个可执行验证）；「严禁改业务代码」不变。
- **eo-review**：检查维度改为「AC 覆盖（逐条核对）+ 代码质量 P0/P1/P2」；清理 spec/模块引用。
- **eo-change-review**（决策 #1：保留现状深度）：检查维度中 spec Delta 正确性删除，替换为「AC 质量（可测、无歧义、用户视角）+ 粒度合规（§3.5 指标）+ TODO↔AC 映射完整性」。观测其使用率与价值，后续决定是否轻量化（backlog 已记）。

### 7.1 对话速报（硬性要求）

所有产出报告文档的 skill（eo-review、eo-change-review、eo-test、eo-design audit、doc-manager 一致性校验）在报告写盘后，**必须**在对话的最后一条消息输出速报——用户不打开报告文件就能获知基本结果。速报是流程的最后一步而非可选礼貌，SKILL.md 中以「缺速报 = 流程未完成」的措辞写死。固定格式：

```
结论：通过 / 不通过（P0 x 条）/ 有保留通过（P1 x 条）
P0（阻塞）：
1. <一句话> — <位置>
P1（应修）：
2. <一句话> — <位置>
P2（可后置）：
3. <一句话>
下一步：<修复后复审 / 可进入 xx 环节>
（详细分析见 <报告文件路径>）
```

- 无某级问题时该级整行省略；全绿时速报可以压缩为两行（结论 + 下一步）。
- 每条一句话 + 定位，禁止在速报里展开分析——展开的归报告文件。
- eo-test 的速报字段相应替换为：结论 / 失败用例逐条 / 未覆盖 AC / 下一步。

---

## 8. eo-design（新增，参考 gstack 全链路——决策 #5）

单 skill 四模式（`/eo-design <mode>`），产物与约束链：

### 8.1 模式

| 模式 | 对应 gstack | 职责 |
|---|---|---|
| `init` | design-consultation | 0→1 建立设计系统：预填充（读 README/已有 DESIGN.md）→ 一个合并问题 + memorable-thing 强制问题 → （可选）竞品视觉调研 → 一次性完整提案（SAFE/RISK 拆分：2-3 个安全选择 + ≥2 个刻意冒险各说得失）→ 自包含 HTML 预览页（候选字体/色板/组件示例/明暗切换，用产品真实内容）→ 用户确认 → 落地 DESIGN.md + CLAUDE.md 注入 |
| `variants` | design-shotgun | 针对某屏幕的多变体发散：先出 N 个文字概念（反趋同硬要求：像三个不同团队而非同一团队三种浓度）→ 确认后生成 HTML 变体 → 对比页收集反馈 → 迭代 → 选中结论进 DESIGN.md Decisions Log |
| `apply` | design-html | 把选中方向落成生产级 HTML/组件；DESIGN.md token 优先级最高；真实内容禁 lorem ipsum；AI slop 黑名单自检 |
| `audit` | design-review | 对已实现页面做「与 DESIGN.md 一致性」审计 + 修复建议（轻量版，可后置实现） |

### 8.2 产物存放

- `DESIGN.md`：仓库根，唯一设计真相源。
- 变体/预览 HTML：`tmp/eo/design/<date>-<topic>/`（约定见 §2.3），不入库；选中变体的结论（含关键 token）写入 DESIGN.md Decisions Log。
- 服务具体 change 的高保真稿：`changes/<id>/design/`，随 change 归档冻结。

### 8.3 约束链（gstack 五重引用的 eo 版）

1. `init` 落地 DESIGN.md 的同时向 CLAUDE.md 注入 `<!-- eo-design:start/end -->` 段：「任何视觉/UI 决策前必须读 DESIGN.md；不得未经用户批准偏离；发现不符合 DESIGN.md 的实现要标记」。
2. eo-change 起草涉及 UI 时：DESIGN.md 存在则作为默认约束读入；不存在则提示可先跑 `/eo-design init`。
3. eo-review 增加检查项：UI 变更是否符合 DESIGN.md。
4. `variants`/`apply` 声明 DESIGN.md token 优先级高于任何临时发挥。

### 8.4 依赖降级

竞品视觉调研依赖联网（走用户环境的 web-access/browse），设计为**可选步骤**，跳过不阻塞主链；预览一律用自包含 HTML（gstack 的 Path B），不依赖外部二进制。

---

## 9. eo-project-init（调整）与共享规范

### 9.1 骨架与注入

- 代码侧骨架：`eo-doc/{agent-handbook,state,changes,templates}`（dev/ 消失）。
- CLAUDE.md 注入更新：
  - `eo-doc` 段目录表改为三行（agent-handbook / state / changes，各注「何时读」）；
  - 保留三个行为钩子（backlog / decisions / lessons）；
  - 若 DESIGN.md 存在，检查并补 eo-design 约束段。
- 全部待确定问题（建哪个 agent 文件、vault 模式等）用 AskUserQuestion 呈现，带推荐项。
- 注意 v1 已知副作用：行为钩子的触发词曾污染下游 skill 措辞（change-review 被迫避用「关键决策」字样）——v2 注入的钩子触发条件收窄为「用户明确表达」而非关键词匹配。

### 9.2 eo-shared/（新增共享目录）

install.sh 是逐目录软链，跨 skill 相对路径引用不可靠。方案：新建 `eo-shared/` 目录（无 SKILL.md，不可触发），随包一起软链到 `~/.claude/skills/eo-shared`，存放单一来源的共享规范：

- `questioning.md` — 提问纪律全文（eo-change / eo-brainstorming / eo-design 引用）
- `ac-spec.md` — 验收清单规范（eo-change / eo-test / eo-review / eo-fix 引用）
- `granularity.md` — 粒度指标、trivial 硬判据与拆分决策表
- `conventions.md` — 横切约定：tmp/eo/ 工件命名空间（§2.3）、commit 前缀（change-id / fix: / ui:）、状态自动流转

各 SKILL.md 以稳定路径 `~/.claude/skills/eo-shared/<file>` 引用。**实施时需先验证**：无 SKILL.md 的目录在三个 agent 环境（claude/codex/antigravity）的 skills 目录下均无副作用；install.sh 的 `has_skill_dirs` 过滤逻辑需放行该目录。若验证失败，降级方案是各 skill 内嵌精简版 + 构建脚本同步。

---

## 10. 移除与迁移

### 10.1 移除清理清单（调研确认的引用点）

- **eo-workflow**：目录本体；README.md:119（流程图节点）、README.md:128（实验声明）、docs/GUIDE.md:268、eo-flow/SKILL.md:5/16/187、eo-change/SKILL.md:193。
- **eo-spec / eo-spec-review / eo-module-init**：目录本体；README/GUIDE 相关章节与流程图；eo-change（前置条件、Delta、跨模块判界）、eo-archive（全文重写）、eo-fix（F-spec）、eo-doc-manager（dev/ 说明）、eo-flow（分叉表中 spec-review/change-review 行）中的全部 spec 引用。
- **eo-flow**：本次仅做上述引用清理，功能重构延后（用户决策）。

### 10.2 v1 项目迁移

- 存量 `eo-doc/dev/<module>/spec.md`：frontmatter 加 `status: frozen`，不再被任何 skill 读写，保留作历史参考；spec-history.md 同冻结。
- 进行中的 v1 change：走完当前生命周期，但归档动作按 v2 执行（不反写 spec，直接 sync + 冻结）。
- 新 change 一律建到 `eo-doc/changes/`（项目级连号从现有最大号续起）。
- 产出 `docs/migration-v1-to-v2.md` 面向已安装用户，说明破坏性变更与迁移步骤。

---

## 11. 实施批次（用 v2 自己的粒度理念拆分）

| Batch | 内容 | 对应 AC |
|---|---|---|
| 1 拆骨 | 移除 eo-workflow/eo-spec/eo-spec-review/eo-module-init + 全部交叉引用清理；README/GUIDE 流程图初步改写 | 全仓库 grep 无残留引用 |
| 2 核心 | eo-change 重构（新模板、提问纪律、AC 前置、粒度校验、trivial 短路）+ eo-brainstorming 捕获出口 + eo-shared/ 建立 + lessons 消费注入 | 新 change 全流程可走通 |
| 3 闭环 | eo-archive 重构 + eo-doc-manager 增强（archive 触发点/脏变更/计数/校验）+ eo-implement 调整 + eo-fix 重构（直接修复 + 深挖模式） | 一个 change 从 confirmed 到 archived 全链路可走通，state/handbook 被正确增量更新，重复 sync 不发生 |
| 4 design | eo-design 四模式 + project-init 注入更新 | init→DESIGN.md→CLAUDE.md 注入链可走通 |
| 5 收尾 | eo-test/eo-review/eo-change-review 微调、eo-handoff 路径迁移 tmp/eo/handoff/、迁移文档、install.sh 验证 eo-shared、README/GUIDE 定稿 | 远程安装后新老项目均可用 |
| 6 联动 | board stub 写入（change/implement/archive 钩子）+ project-init 的 board 开关与历史同步 + GitHub issue/PR 注入 + .base 三视图配置指南 | 开启开关的项目：Obsidian 看板可用、issue/PR 全链路可走通 |

每批一个（或一组）commit，批间可停可评审——v2 改造本身按 v2 的节奏做。

## 12. 开放问题

1. ~~eo-shared/ 软链兼容性~~ 已验证：install.sh 按 `eo-*` 通配无条件软链、不检查 SKILL.md，eo-shared/ 自动分发；无 SKILL.md 目录对各 agent 无副作用（Batch 5 安装实测再确认一次 codex/antigravity）。
2. 一致性校验阈值（暂定 sync_count=5，用数据调）。
3. change-id 项目级连号与 v1 存量模块级编号并存时 INDEX 的呈现方式。
4. eo-design 竞品调研步骤与用户环境 web-access skill 的对接方式（可选步骤，不阻塞）。
5. 直改模式的 cursor 落后提醒阈值（暂定 10，用数据调）。

---

## 13. 看板与可观测（stub 契约）

调研结论见 vault research/v2/《看板可观测与GitHub联动》《obsidian看板组件对比》。

- **数据层**：skill 在 change 状态流转时向 vault 项目目录 upsert 一张 stub 卡片笔记，frontmatter：`id / title / project / status / type / todo_done / todo_total / issue / pr / updated / tags: [eo-change]`。stub 完全由 change frontmatter 派生，幂等、可全量重建，**零双写**（看板只是 frontmatter 的投影）。
- **呈现层**：一个共享 `.base` 文件三视图——主视图 **Kanban Bases View** 插件（真·并排状态列 + 列色 + 封面 + 按项目泳道）、官方 cards+groupBy 做退路、table 做盘点。官方 Bases kanban 视图在 roadmap 上为 Active，发布后改视图 type 即切换，数据零迁移。**skill 永不写 .base**——装好插件后在 UI 配一次、抄 Obsidian 写回的键名（社区插件 YAML 键随版本变动）。
- **开关**：`.eo-project.json` 新增 `board` 段（`enabled` / `stub_dir`），逐项目 opt-in。schema 变更须登记跨项目关系文档（eo-platform 只读消费）。
- **历史同步**：后开开关的项目由 eo-project-init 全量重建 stub（repair 语义，幂等，成本趋零）。
- **server 不在本仓库做**：见 §15。eo-skills 只承诺 change frontmatter 与 stub schema 作为稳定文件契约。

## 14. GitHub 联动（opt-in）

- **配置**：`.eo-project.json` 的 `github` 段 `{ sync, issue, pr: "auto"|"always"|"never" }`。首次遇到未配置时 AskUserQuestion 问一次并写回，此后永不再问。
- **change ↔ issue**：粒度停在 change 层，一对一。`draft→confirmed` 时建 issue（草稿夭折不留孤儿）；issue 号回写 frontmatter（`issue: 42`，去重唯一依据，绝不靠标题匹配）；TODO 作为 issue body checklist（原生 n of m 进度）；archive 兜底关闭。
- **change ↔ PR**：`pr: auto`（推荐默认）= archive 收尾时在非默认分支自动 push + `gh pr create`，默认分支直接提交不建 PR，零提问。PR body 自动生成：意图摘要 + AC 勾选清单 + **条件性 Closes**（AC 全勾才写 `Closes #N`，否则 `Linked to #N (partial)`——issue 关闭语义严格等于验收完成）。PR URL 回写 frontmatter，board stub 带上。
- **真相源裁决**：本地文件是唯一真相源，GitHub 是投影 + 协作评论区。严格单向推送；唯一逆向通道是漂移检测告警（issue 已关但本地未 archived → 报一行，不自动改）。不做双向同步（echo loop / 冲突 / rate limit 三重税，gstack 与 spec-kit 双双选单向互为印证）。
- **backlog**：不直接 issue 化；条目被采纳为 change 时随 change 升级成 issue；反向支持粘 issue URL 落 backlog（单向拉取）。

## 15. 展望：生态划界与候选技能（不在 v2 范围）

- **eo-board server 独立立项**：多项目看板 server（实时推送、点击交互、聚合视图）不进 eo-skills 仓库——server 是有自己变更节奏的独立产品，与「md 文件 + 软链」的分发模型不兼容。定位为**重做后 eo-platform 的第一个垂直切片**（旧 platform 设计已废弃；围绕看板这个具体需求重启，比抽象注册表先行健康）。第一版严格只读；写操作必须 shell out 给 skill/CLI，绝不直接改文件（防止长成第二真相源）。消费 §13 文件契约；建议作为 v2 工作流的第一个狗粮项目。
- **候选技能决策池**（全文见 vault research/v2/《竞品-外围skill生态与候选补充》）：
  - ~~eo-investigate~~ → 已并入 v2 的 eo-fix 深挖模式（§5.2）；
  - lessons 消费机制 → 已并入 v2（§3.1）；
  - eo-ship（git 收尾/release，中优——PR 创建已内置 archive，需要 CHANGELOG/版本号/攒 release 时再抽出）；
  - eo-retro（周期复盘 + 执行决策 #1 的 change-review 观测，中优）；
  - eo-guard（PreToolUse hook 硬护栏，中优——eo 首次引入 hook 需单独评估）；
  - eo-security（低优）；eo-doctor（并入 doc-manager 子命令，低优）。
  - 不引入清单（11 类）及理由见调研文档。
