---
name: eo-change
description: |
  发起变更，产出「验收清单（AC）+ 分批 TODO」的 change 工件。触发：新增 / 加功能 / 增强 / 重构 / change / /eo-change。
  NOT FOR: bug 修复（走 /eo-fix）；trivial 小改（本 skill 会主动短路成直改，不产生工件）。
---

# eo-change — 发起变更

发起一次变更。change 是**过程工件**：起草期承载澄清与拆解，实施期承载进度，归档即冻结为审计历史——**不合并回任何文档**（活文档 state/agent-handbook 由 doc-manager 以代码为信源另行维护）。

## 核心理念

1. **验收驱动**：AC 先于 TODO 产出，是 implement 的完成判据、review 的检查表、fix 的期望行为锚点
2. **三档渐进式严谨**：trivial 直改零工件；轻档（`tier: light`）只有意图 + AC；全档必填仅 3 节、其余条件化。判档表见 [../eo-shared/granularity.md](../eo-shared/granularity.md) §5——判档权在 agent，宣告后用户一个词可改档
3. **量化粒度**：超软标建议拆、超硬标拒绝确认，指标数值以 [../eo-shared/granularity.md](../eo-shared/granularity.md) §1 为准
4. **提问有预算**：事实自查、决策上抛、决策台账钉结论——规则见 [../eo-shared/questioning.md](../eo-shared/questioning.md)
5. **状态自动流转**：用户在对话里确认，skill 落盘 status，用户永不手改 frontmatter

## 前置条件

- **必须能找到 `.eo-project.json`**（cwd 或父目录）。找不到 → 报错退出，提示运行 `/eo-project-init`。`eo-doc/` 路径由 `doc_root` 解析
- `eo-doc/changes/` 不存在时 lazy 创建（含 INDEX.md 骨架）

## 工作流程

### 第一步：意图理解与复杂度定级

1. 读用户的变更描述。**若来自 /eo-brainstorming 捕获出口**：直接继承其已钉决策与 change 草案，跳过已钉项的一切重复提问，从第四步续起。**若来源是某张 backlog 卡**（用户说「把这条 backlog 做了」）：继承卡片的 title/说明/标签作为意图输入，记下卡片路径待第七步归档。**若来源是外部 GitHub issue**：继承其正文作意图输入（规范 issue 常自带 AC），记下 issue 号待落盘回写 `issue:`（联动钩子靠回写号去重，不重复建）
2. 按 [../eo-shared/questioning.md](../eo-shared/questioning.md) §2 定级：trivial / simple / complex / critical
3. **trivial → 主动短路**：告知用户「这不值得开 change，直接改」，按 [../eo-shared/granularity.md](../eo-shared/granularity.md) §2 的直改模式执行（改 → 验证 → `fix:`/`ui:` 前缀 commit；注释零溯源，提交前对新增注释自检一眼，见 [../eo-shared/conventions.md](../eo-shared/conventions.md) §2.6），本流程终止。判据任何一条不满足则回到 change 模式
4. **critical → 建议升级**：「这个方向本身还没定，建议先 /eo-brainstorming 把决策钉了再回来」；用户坚持则继续，但澄清预算放宽到 5+
5. **轻/全判档**：非 trivial 非 critical → 按 granularity.md §5 四问判档，一句话宣告（含取舍，如「按轻档走：不出 review 报告，验收靠测试 + 复核」），用户一个词可改档。**轻档 → 走文末「轻档流程」**（替代第二至第八步）；全档 → 继续第二步
6. **update vs new**：若变更明显是某个未归档 change 的意图精化 → 提议就地更新那个 change 而非新开（决策表见 granularity.md §3）

### 第二步：事实自查（静默执行）

提问之前先自答：

1. 读 `eo-doc/state/` 相关篇目（系统现状）与 `eo-doc/agent-handbook/INDEX.md` 索引到的相关代码地图
2. 读 `eo-doc/changes/INDEX.md` 最近 3 条（演化方向，避免重复/冲突）
3. **lessons 消费**：按 [../eo-shared/lessons.md](../eo-shared/lessons.md) §1 执行——扫 lessons/INDEX.md 匹配 trigger/tags，命中 ≤3 条读其「规则」节带入起草；采纳的在 §1 已钉决策标注来源
4. 变更涉及外部世界（第三方 API / 平台规则 / 技术选型）→ 按 [../eo-shared/research.md](../eo-shared/research.md) 消费规则查 `<project_root>/research/`——调研过的结论不重新调研
5. 涉及 UI 且仓库根有 `DESIGN.md` → 读入作为默认设计约束
6. 能从以上信源回答的问题，**禁止问用户**

### 第三步：预算内澄清

按 [../eo-shared/questioning.md](../eo-shared/questioning.md) 全文执行：预算配比、每轮 1-2 问、封闭选择按其 §4 协议（带推荐项）、内部决策台账（已钉/未钉/defer）、视觉/UI 方向类问题必带「画 HTML 对比页」选项（其 §4 硬性规则，衔接 /eo-design variants）、疲劳信号立即降级用默认。defer 上限 3 条，落入 §8 开放问题。

### 第四步：产出验收清单（先于 TODO）

按 [../eo-shared/ac-spec.md](../eo-shared/ac-spec.md) 撰写：用户视角、可独立验证、技术无关、覆盖异常路径。**这是 change 的第一个产出物**——AC 定不下来说明澄清还没到位，回第三步。

### 第五步：TODO 拆解与分批

- 每条 TODO 三要素（描述/文件/对应 AC），逐条映射 AC；文件栏带**操作类型前缀**「新增:/修改:/删除:」（缺省视为修改——change-review 维度 7 按类型核验前提）；完成判据仅在多条 TODO 对同一 AC 时逐条补写（granularity.md §4），**禁止占位符**
- 按 Batch 分组，**Batch 1 = MVP**：跑完即可独立验证其对应的 AC（批间 STOP and VALIDATE 由 eo-implement 执行）
- 不写具体函数体；接口签名/数据结构可以描述

### 第六步：粒度自检（自动校验）

对照 [../eo-shared/granularity.md](../eo-shared/granularity.md) §1：数 TODO、`wc -l` 全文。超软标（>7 条 / >500 行）→ 建议按 AC 分组拆成 change 序列（第一个 = MVP，其余排队或进 backlog）；超硬标（>10 条 / >700 行）→ **拒绝进入确认**，必须拆。

### 第七步：写入 change.md 并确认

1. **确定 change-id（slug 即身份，规则见 [../eo-shared/conventions.md](../eo-shared/conventions.md) §2）**：用户给语义名 → kebab-case slug 即 id（拒绝 `fix-` 前缀）。查重：扫 `eo-doc/changes/` 目录与 INDEX.md，有 remote 时 `git ls-tree origin/<默认分支> -- eo-doc/changes/` 兜底（防多 worktree 并行撞名）；撞名 → 换更具体的 slug。另分配显示序号 `seq`：现有 change（含存量数字前缀 id）最大号 +1，补零作目录前缀 `<NN>-<slug>/`（供 `ls` 排序、一眼找进行中的）——seq 允许 worktree 并行撞号（自愈见第八步）
2. 按 [references/change-template.md](references/change-template.md) 写入 `eo-doc/changes/<NN>-<slug>/change.md`（目录名 = seq 补零前缀 + slug；`status: draft`，frontmatter 含 `seq` 与一句话 `summary`）；已钉决策落 §1，条件节按触发条件取舍。**写入即新建看板 stub**（[../eo-shared/board-github.md](../eo-shared/board-github.md)，board 未开启则跳过）——draft 从这一刻起就在看板上
3. 交付用户确认，按反馈修订
4. **用户在对话中确认后，skill 自动置 `status: confirmed`**——不要求用户手改 frontmatter；来源是 backlog 卡的，按 [../eo-backlog/SKILL.md](../eo-backlog/SKILL.md) 的 archive 动作归档该卡（adopted + 关联本 change-id）
5. 联动钩子：更新 stub（status 同步为 confirmed）、创建 GitHub issue（issue 只在此刻建，draft 阶段不建；对应开关未开启则跳过），见 [../eo-shared/board-github.md](../eo-shared/board-github.md)。修订循环中（场景 B）任何改动落盘也顺手 upsert stub

### 第八步：更新索引 + 提示后续

更新 `eo-doc/changes/INDEX.md`，顺手对 seq 列查重：发现重号（多 worktree 并行分配所致）→ `created` 晚者让号——改 frontmatter `seq` + `git mv` 目录（`<旧NN>`→`<新NN>`）+ 改 INDEX 行（含链接路径）+ upsert stub，一句话报告（**commit 前缀/issue 全程不动**，见 [../eo-shared/conventions.md](../eo-shared/conventions.md) §2）。顺手**防蒸发**：非 archived 且 30 天未动的轻档条目列一行提醒。然后按场景提示：

**场景 A — 首次产出**（目录下无含未决 P0 的 change-review.md）：

> change 已就绪（status: confirmed）。后续：
> 🟡（可选；符合 [../eo-change-review/SKILL.md](../eo-change-review/SKILL.md) 开头「建议跑」条件时主动提示）`/eo-change-review` — 方案审查
> 1. `/eo-implement <change-path>` — 按 Batch 实施
> 2. `/eo-test <change-path>` → `/eo-review <change-path>`
> 3. `/eo-archive <change-id>` — review 通过后归档

**场景 B — 返工修订**（change-review.md 存在未决 P0）：

1. **逐条处置台账**（change-review.md 的 Finding 台账）：修复的改 change.md 并在台账「处置」列标注改动落点（状态置 `fixed`）；不认同的标 `wont-fix` + 一句理由，并在对话中向用户播报（用户异议随时改回）
2. **P1 不阻塞**：采纳与否由本 skill 裁决——采纳顺手修，不采纳标 `wont-fix`；P1 的修复**不触发复审**
3. 修订后**必须**再跑 `/eo-change-review` 复审（默认增量核销；AC 增删、已钉决策变动等锚变化自动升全量），循环到 **P0=0**；复审累计上限 3 轮，到限由用户按其终态措辞裁决
4. 此时代码未写，**严禁**走 /eo-review 或直接 implement；复审通过前保持 `status: draft`


## 轻档流程（tier: light）

判档为轻档后走此流程，**替代第二至第八步**：

1. **快速自查**：读 `eo-doc/state/` 相关篇目、lessons INDEX 命中项（按 [../eo-shared/lessons.md](../eo-shared/lessons.md) §1 匹配 trigger/tags，≤2 条）、`changes/INDEX.md` 最近 3 条（防重复/冲突）；涉及 UI 且仓库根有 `DESIGN.md` → 读入；涉及外部世界 → 按 [../eo-shared/research.md](../eo-shared/research.md) 消费规则查 `research/`。能自答的不问用户
2. **澄清**：预算 1-2 问（协议同 questioning.md），问完即写——AC 定不下来说明澄清不到位，或该转全档
3. **落盘（draft）**：按 [references/change-template.md](references/change-template.md) 轻档模板写入 `changes/<NN>-<slug>/change.md`（id/seq/查重/让号规则与全档同一套）；AC ≤5 条、覆盖异常路径、manual 标「人工:」；外部 GitHub issue 来源 → 号回写 `issue:`。写入即建看板 stub（未开启跳过）
4. **探针对齐（→ confirmed）**：把意图 + AC 亮给用户否一次——探针的成功标准是**尽快暴露分歧**，不是通过评审。用户点头 → `status: confirmed` + 联动钩子（stub 刷新；GitHub issue 联动开启且 frontmatter 无 issue 号才建）。用户否 → 就地改再亮一次；方案分歧大 → 转全档从第二步续起
5. **更新 INDEX + 提示后续**：INDEX 行「档」列标 `light`；seq 查重自愈与防蒸发报告同第八步。后续提示：

   > 轻档已就绪（confirmed）。下一步：`/eo-implement <change-path>`——轻模式：测试锁定 → 实施 → 完成门，收口即归档。

轻档**不进 change-review**（方案分歧在探针对齐里暴露）；实施中的扩档由 eo-implement 轻模式停手转入下方扩档子流程。

### 扩档子流程（light → full，由 eo-implement 轻模式停手转入）

1. frontmatter `tier` 改 `full`，就地补齐全档模板节：§1 意图（轻档意图行扩写 + 已钉决策）、§2 保留、§3 TODO——**已完成的工作映射为已勾 TODO 并注「扩档前完成」**，剩余工作按 Batch 划分；条件节按触发条件取舍；补全档 frontmatter 字段 `plan_revision: 1`/`fix_rounds: 0`/`fix_consumed: []`（语义见 [../eo-shared/conventions.md](../eo-shared/conventions.md) §3）
2. 交用户再确认（对话确认）；**因影响面/风险信号触发的扩档，建议跑一次全量 /eo-change-review**
3. 刷新 INDEX 行（档列 light→full）、stub 与 issue body 投影（[../eo-shared/board-github.md](../eo-shared/board-github.md)，未开启跳过）
4. 回 /eo-implement 模式一，从首个未完成 Batch 续走——`base_commit`/`test_lock_commit`/已锁定测试全部保留

### 回炉子流程（方案实质修订，由 eo-implement 模式二熔断/卡点检查或用户显式要求转入）

回炉 ≠ 修 bug——是「方案本身要改」。前提：status 为 `implementing`（reviewed 的先按回退边置回，见 [../eo-shared/conventions.md](../eo-shared/conventions.md) §3）。

1. **边界检查**：先过 [../eo-shared/granularity.md](../eo-shared/granularity.md) §3 更新 vs 新开决策表——意图本质变化 / 与原范围重叠 <50% / 原 change 可独立收尾 → **新开 change**，不回炉（原 change 走正常收尾或归档豁免）；不允许借回炉绕过这条边界
2. **status → `draft`**，修订 §1/§2/§3（含已钉决策的重钉）
3. **证据失效**：旧 TODO/AC 与新版逐条映射——语义不变的保留勾选注「回炉前完成」；完成判据或 AC 语义受影响的**取消勾选**注「回炉待复验」；manual 项按 [../eo-shared/acceptance.md](../eo-shared/acceptance.md)「失效与重置」重置；`test_lock_commit` 仅在全部被锁 AC 语义不变时保留，否则值旁注 `superseded`（待轻模式重锁）；`base_commit` 无条件保留
4. **报告处置**：change-review.md / test.md / review.md（存在者）各追加一行 `> revision N 作废（<日期>）——后续见 revision N+1`，并把台账中仍为 `open`/`fixed` 的行状态批量改 `superseded`（随方案作废，archive 门不再计为阻塞）；**不压缩、不删除**旧轮次内容（报告可能未提交，git 兜不了底）
5. **投影**：INDEX 行状态回 draft、stub upsert、issue body 刷新（联动开启时）
6. **确认收口**：交用户重新确认 → `status: confirmed`，frontmatter `plan_revision` +1、`fix_rounds` 归零、`fix_consumed` 清空；再刷新一次投影。触发根因为「方案不合理 / AC 口径漂移」（且确实走了回炉——口径漂移多数走就地精化，见下）→ **必须**跑一次全量 /eo-change-review（新 revision 轮数从 1 起算、旧 wont-fix 失效）；用户显式豁免可跳，豁免记 §8。然后回 /eo-implement 模式一从首个未勾 Batch 续走

**回炉与就地精化的边界**：措辞微调、意图不变的就地补 AC（implement 流程内确认后补写）不算回炉——不动 `plan_revision`、不清计数、不走本子流程。

## changes/INDEX.md 模板

```markdown
# 变更时间线

| # | change | 档 | 类型 | 状态 | 日期 | 摘要 |
|---|--------|----|------|------|------|------|
| 14 | [batch-export](14-batch-export/change.md) | full | feature | confirmed | YYYY-MM-DD | 一句话（= frontmatter summary） |
```

## 关键约束

- **AC 先于 TODO**；每条 TODO 必须映射到 AC
- **粒度硬上限拒绝确认**（数值见 granularity.md §1）；轻/全判档以 granularity.md §5 为准
- **轻档不写 TODO、不进 change-review**；扩档只由 eo-implement 轻模式触发
- **回炉只走回炉子流程**：先过更新 vs 新开边界；证据失效逐条处理；`plan_revision`/计数只在用户重新确认时动——就地精化不算回炉
- **无 `fix` 类型**；bug 走 /eo-fix
- **status 由 skill 流转**（见 [../eo-shared/conventions.md](../eo-shared/conventions.md)），用户不手改
- **change 阶段不写代码**、不改活文档；归档不反写（由 eo-archive 触发 doc sync）
