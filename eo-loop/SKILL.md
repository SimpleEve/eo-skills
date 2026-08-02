---
name: eo-loop
description: |
  eo 流程总控：按用户意图在 eo 状态机上圈一段（入口节点 → 出口节点 → 收敛标准），把 eo-change / eo-change-review / eo-implement / eo-test / eo-review / eo-archive 派发到可插拔执行基底上循环推进至收敛，窗口化汇报进度。触发：eo-loop / 串起来跑 / 循环推进到收敛 / 总控调度 / /eo-loop。
  NOT FOR: 单点动作（直接调对应 eo-* skill）；派出去不再监督的完全交接（orca-cli full handoff）；bug 口喷（/eo-fix）。
---

# eo-loop — eo 流程总控

总控只做五件事：**识别、派发、校验、循环、汇报**。三不做：不亲自写代码、不改 change 实质内容、不复述下游流程（节点内部怎么做由各 eo-* skill 自治，总控只关心状态是否推进）。

**总控无状态**：流程真相只在 change.md frontmatter 与 review/test 台账里。会话断了，任何 agent 重读 frontmatter 即可从当前节点继续——本 skill 不落自有状态文件（journal 是速报留痕，不是信源）。

**总控在哪**：用户在哪个会话喊 /eo-loop，哪个会话就是总控。不派专职 coordinator；跨 agent 时由当前会话消费 orca 原语监督。

## 前置条件

- **必须能找到 `.eo-project.json`**。同目录存在 `.eo-project.local.json` 时顶层字段覆盖合并（local 优先）。找不到 → 报错退出，提示运行 `/eo-project-init`
- 线段涉及已有 change 时，定位其 `eo-doc/changes/<NN>-<slug>/`（口头引用按 [../eo-shared/conventions.md](../eo-shared/conventions.md) §2 经 INDEX 解析）

## 调度哲学（四步闭环）

没有固定 pipeline。每一轮都走同一个闭环：

**① 圈线段**：从用户话语确定三要素——**入口节点、出口节点、收敛标准**（出口状态怎样算达成）。地图是 [../eo-shared/conventions.md](../eo-shared/conventions.md) §3 的状态机（主路径 + 回退边）。典型线段只是示例、不是枚举：

- 方案对齐：change ↔ change-review，收敛 = 审查通过、用户确认
- 实施对齐（首轮典型路径）：implement → test → review，收敛 = 台账无阻塞项（P0/P1 清零）、最新 Review 覆盖当前 `(plan_revision, H)`，且测试证据已闭合（Test 在当前 revision 的 `H` 通过 / 当前 Review 明确签署旧证据沿用 / 无历史 Test 且无待验 heavy AC）；进入反馈循环后按 ④ 的非对称回路分流，不机械重放整条路径
- 直通：change → … → review 或 archive

三要素判不出的，先查偏好文件补缺省（见「经验沉淀」）；仍缺 → 按封闭选择协议（[../eo-shared/questioning.md](../eo-shared/questioning.md) §4）问一次，不追问第二轮。

**举例措辞判据**：用户意图含「比如 / 之类 / 例如」等举例措辞 = 形态未定稿——例子是方向、不是规格。圈段时先安排探针对齐（轻档探针 / change 确认）把形态钉下来再派实施节点，不得让例子直接当定稿进派发 prompt。

**② 选基底**：对线段上每个节点确定执行者与模型，三级优先：**本次用户显式指定 > 偏好文件 > 探测缺省**。偏好层**不静默生效**：用户本次未指定模型 / effort / 基底的节点若命中偏好条目，开跑前把命中条目列出来问一次「按此偏好跑？」（封闭选择：确认 / 逐项调整）；确认即本轮生效，调整按「经验沉淀」纠偏规则回写。无偏好可查才落到探测缺省。运行时 `ls` 本 skill `references/substrates/*.md` 得到当前基底清单，读候选文件按其「探测」节确认可用；不可用即跳过换下一候选。

**③ 派发与校验裁决**：按基底文件「派发」节把节点交出去。worker 的交付**先校验、再裁决，绝不直接采信**。

**并行派发**（判据与合流规范见 [../eo-shared/granularity.md](../eo-shared/granularity.md) §6）：可并行的单位有二——同一 change 的**同层并行批**（§3 字母后缀 Batch 2a/2b），与 INDEX 摘要标注「可与 #N 并行」的 **change**（并行收敛组）。纪律：

- 派发前总控先做**文件集机械校验**（同层批 TODO 文件栏两两不相交；不过 → 降级串行并一句话报告）
- 一并行 worker 一**独立 worktree**（现场隔离，手段见基底文件）；同层全部收口后指派其一 worker 执行合并与合流 checkpoint，总控按下方三项检查校验其证据，冲突修复派回引入冲突批的原 worker
- 并行派发 >2 个 worker 前先报数量与预算，等用户点头（见事实说明）

校验按「回收」节读证据、不读 worker 的话，三项基本检查：

- **状态一致**：frontmatter status / 台账 / AC 勾选与其声明相符
- **产出实在**：声称的 commit / 报告 / 勾选真实存在，且锚定当前基线（勾了 AC 却无对应提交、review 结论基于旧基线，都是假进度）
- **边界合规**：无越界产物（test 改了业务代码、review 亲自动手修、implement 动了测试锁定 → 一律不通过）

Review 修复后的免测判定同样执行证据完整性校验：总控只读取最新 review 轮的 `测试证据处置`、既有 Test 基线 `T`、当前交付基线 `H`、受影响范围与依据。存在较旧 Test 时，只有原 reviewer 在当前 `plan_revision` 的 `H` 上明确签署 `沿用`，且 `既有通过 Test：第 N 轮 @ T` 精确对应同一 `test.md` 中当前 revision 最新的通过轮、该轮先通过下文同等级的 Test 结构/定向来源链/范围覆盖校验、台账无阻塞项、`T` 为 `H` 的祖先时才可跳过 eo-test；Implement 的影响候选、worker 口头结论、旧 revision 或字段缺失/含糊都不能放行，后一律按 `复验` 路由。处置为 `不适用` 时只接受两种可机械证明的情况：Test 已在当前 revision 的 `H` 通过且同样通过下文结构校验，或从未运行 Test 且没有待验 heavy AC；否则派 Test。

Test 交付也按当前基线校验：`H` 是最后一个触及业务代码或测试资产的本 change commit，纯报告/元数据提交不计；Test 新增或修改测试资产时必须先以 `[<change-id>]` 提交，再在新 `H` 上执行最终验证。总控只接受当前 `plan_revision` 的结构化 Test 轮次：结论通过、台账无阻塞项、`当前交付基线 B` 可解析，且 `验证方式`、`触发来源`、`测试资产提交`、`重跑范围`、`沿用范围`、`范围校验` 均明确，测试资产提交已包含在 `B` 中；定向复验还须指向同一报告内结构完整且明确通过的 `第 N 轮 @ S`（定向来源链递归有效），证明 `S` 是 `B` 的祖先、从触发来源指向的历史 Review/Test 轮解析出的影响集包含在重跑范围内，且来源证据被重跑范围与沿用范围无遗漏、无重叠地覆盖。字段残缺、revision 过期、来源链不通过、范围覆盖无法证明或存在本 change 的未提交业务代码/测试资产 → 拒收并打回对应原 worker。若 Review 在 `H` 上签署 `复验`，只有后续通过的 Test 轮明确写 `触发来源：Review 第 R 轮 @ H` 才算消费该路由；消费后即使 Review 速报仍保留 `复验` 字样，也不得再次派 Test。Test 通过后若 `status` 不是 `reviewed` 或最新 Review 未覆盖当前 `(plan_revision, H)`，先回原 reviewer；Reviewer 在 Test 已于当前 revision 的 `H` 通过时写 `不适用`，不会因此再次触发 Test。

裁决三分支：

- **通过** → 推进线段，派发下一步
- **不通过、属 worker 职责内**（交付缺陷、报告缺项、越界产物）→ **直接打回**原 worker 重做，附具体不通过证据；同一节点打回 2 次仍不合格 → 升级为卡点停下问用户。注意与正常循环边的区分：review 合格地报出代码 P0 是循环输入（走 ④ 回退边派 implement 修），review 报告**本身**不合格才打回 review worker
- **不通过、超总控权限** → **停下上交用户**。总控永远不代做的决定：产品 / 架构分歧、范围或方案实质变更（回炉确认）、AC 豁免、熔断三选一、判档；进度报告首句「是否需要你裁决」指的就是本分支有没有命中

**分叉清单转达**：worker 随交付上报的分叉清单（见「派发 prompt 纪律」的分叉上报条款）不走裁决三分支——校验通过后，总控把清单攒成**一次封闭选择**（协议见 [../eo-shared/questioning.md](../eo-shared/questioning.md) §4，逐叉列 worker 所采假设作推荐项）转达用户；用户改判的项作为修订输入随下一轮回灌原 worker，维持假设的项不返工。

**④ 收敛判定**：先消费待执行的证据路由，再对照收敛标准；Review 虽已通过但处置为 `复验` 且尚无匹配该 Review 轮的后续 Test 通过、处置不可采、任一证据 revision 过期、最新 Review 未覆盖 `(plan_revision, H)` 或仍有待验 heavy AC 时，均**尚未收敛**。只有台账无阻塞项、最新 Review 覆盖当前 `(plan_revision, H)`，且测试证据按上方三种方式之一闭合，才收口（回写经验并发最终速报）。其余走下列**非对称回路**，不把首轮路径当循环体：

- `review` 有 P0/P1 → 原 impl worker 走 eo-implement 模式二 → **原 reviewer 增量复审**。仍有 P0/P1 就继续这条短回路，不启动 Test；复审通过后读取测试证据处置：`沿用` → 跳过 eo-test，尚未被匹配 Test 轮消费的 `复验` / 缺失 / 含糊 / 基线关系不成立 → 派原 test worker，`不适用` → Test 已在当前基线通过则继续收口；无历史 Test 时仅有待验 heavy AC 才首跑 Test
- 进入 `test` 后，由原 tester 根据 review 指出的影响集决定范围：不含 auto-heavy 且能映射到有限 AC、用例及依赖闭包 → **定向复验**，从明确通过的来源轮组合“重跑范围 + 沿用范围”；任一 auto-heavy AC 被弄脏、影响跨共享行为 / 契约 / 测试基础设施或影响圈不住 → **完整复验**。tester 可扩大范围，不得无证据缩小 reviewer 指出的影响集
- `test` 通过 → 若 `status` 因先前 Test FAIL 仍为 `implementing`、本轮测试资产提交推进了 `H`，或最新 Review 因 revision/其他交付提交未覆盖 `(plan_revision, H)`，先派原 reviewer 增量审查；只有 `status: reviewed`、Review 覆盖当前 `(plan_revision, H)` 且 Test 结论也在该键上时才继续收口
- `test` 有未核销 FAIL（含 Test 与 Review 同时有反馈）→ 原 impl worker 修复 → **原 test worker 复验**；通过后只要 `status` 仍为 `implementing`，或产生过业务代码/测试资产提交，就再派原 reviewer 增量审查，恢复 status 与 Review 基线新鲜度。此分支不得套用 `沿用` 跳过 tester
- acceptance 打回 → implement 修复 → 原 reviewer 增量审查，再按其测试证据处置继续
- 方案需实质修订 → eo-change 回炉

**熔断只消费、不发明**：`fix_rounds ≥3` 三选一、change-review 轮数上限，任一触发即停下，按对应 skill 的协议问用户，绝不代答、绝不无限循环。

## 节点清单

只描述能力边界；顺序与合法流转以 conventions §3 状态机为准。

| 节点 | 消费 | 产出 | 边界 |
|------|------|------|------|
| eo-change | 意图 / 回炉反馈 | change.md（draft → confirmed 经用户确认） | 含判档（light/full）与回炉子流程 |
| eo-change-review | draft/confirmed 的 change.md | 方案审查与修订（文档修订，不产码） | 轻档用探针对齐替代，不派本节点 |
| eo-implement | confirmed | 代码 + AC 勾选（implementing） | 模式二承接 test/review 反馈修复 |
| eo-test | implementing/reviewed 后需验证的代码 | test.md 台账 + 定向/完整范围 | 严禁改业务代码；首轮完整审计，复验按影响范围分流 |
| eo-review | implementing 后的代码 | review.md P0/P1/P2（通过 → reviewed） | 代码级审查 |
| eo-archive | 全档 reviewed；轻档 implementing + 完成门留痕 | archived（不可逆） | 两档同源：轻档走轻档门；implement 收口也内嵌调用它 |

## 执行基底（可插拔）

基底 = 「把一个节点交给谁执行」的载体。**清单不写死在本文件**：一基底一文件，放 `references/substrates/`，增减基底 = 加删文件，本文件零改动。每个基底文件必须含五节（新建照 `references/substrates/_template.md`）：

**探测 / 派发 / 等待与观测 / 回收 / 已知陷阱**

初始三基底与优先倾向（倾向只是缺省，被 ② 的三级优先覆盖）：

| 调用形态 | 倾向基底 |
|----------|----------|
| 总控是 Claude Code，执行者也是 Claude | claude-subagent |
| 总控运行在 Codex 侧 | codex-subagent |
| 节点要跨 agent 运行（执行者与总控不同栈） | orca-orchestration |

**派发 prompt 纪律（全基底通用）**：写目标、不写步骤——只给节点 skill 名、change 目录路径、本轮收敛标准、必要输入（如反馈报告路径）；不复述下游流程；动词避免锚定手段（写「审查 / 实施 / 验证」，不写「搜一下 / 看看 / 检查检查」）；**不要求 worker 中途回报进度**（观测是总控的事，见「可观测性」）。**分叉上报**：节点含形态自由度（菜单结构 / 术语 / 视觉呈现等本应由用户拍板的选择）时，prompt 须要求 worker 把「本应问用户的分叉 + 各自所采假设」以清单随交付上报——worker 不问用户，但分叉不得被假设静默吃掉（清单去向见 ③「分叉清单转达」）。

**worker 复用纪律（全基底通用）**：一个 change 的 loop 内，worker 按**角色**一次创建、跨轮次复用——修复轮回**原 impl worker**、增量复审回**原 reviewer**（增量核销依赖其上下文）、打回重做回原 worker。上下文是资产，不要轮轮新开。两条边界：

- **跨角色必须隔离**：review / test 绝不复用 impl 的 worker——独立性是审查的价值，复用即失效
- **重建仅当**：换执行者或模型（用户指定 / 偏好调整）；上下文已污染（打回后仍复读旧结论，或到打回上限经用户同意重开）；worker 已不可达。各基底的复用手段见其「派发」节

## 可观测性：窗口化等待 + 主动观测

**进度是总控查出来的，不是 worker 报上来的**：worker 专注任务本身，除完成/求裁决信号外零回报义务。总控在窗口内主动读证据观测进度——终端输出、change.md 勾选、review/test 台账增量、git log——具体手段见各基底文件「等待与观测」节。

一切等待必须窗口化，单窗 ≤30 分钟。**窗口到期或节点边界，无论有无进展**，向用户发进度报告并追加到 `tmp/eo/loop/<slug>/journal.md`。骨架定长、内容随窗口内事件伸缩（静默窗口摘要一句即可）：

```
• <HH:MM> <本窗口事件标题，如「review 处理结果」「Batch 2 实施中」>

<一句定性：发生了什么 + 是否需要用户裁决——无则明说「没有需要你裁决的事项」，
 有则列明分歧并暂停等答复>

<实质摘要：按主题归组的要点（如问题归几组、各组一行），不是操作流水账>

- 派发：<task / dispatch 凭据（orca 时）或 worker 标识>
- owner：<基底 + 模型>
- 当前规则：<本轮循环策略，如「Review 短回路先收敛；同一 reviewer 核销后再按测试证据处置决定是否派 Test」>

下一次固定进度报告约 <HH:MM +30min>。
```

journal 属 tmp/eo 命名空间（[../eo-shared/conventions.md](../eo-shared/conventions.md) §1）：可丢弃、不作信源，仅供跨会话回看报告流水。

## 经验沉淀（调度偏好）

把「你习惯怎么调度」变成缺省值。位置 `~/.eo-skills/loop/preferences/`：`_global.md`（跨项目）+ `<项目短名>.md`（覆盖全局同名条目）；格式与读写纪律见 [references/preferences-format.md](references/preferences-format.md)。

- **读**：② 选基底时作为第二优先级——**列出命中条目请用户确认后生效，不静默套用**；① 圈线段判不出时查「习惯线段」节（同样列出确认）
- **写**：收口时回写本次实际生效的「节点 → 基底/模型」映射（与既存条目一致则只刷日期），**缺省写进 `<项目短名>.md`**——调度习惯首先是项目属性；用户明示跨项目（「所有项目都这样」）或同一映射已在 ≥2 个项目文件出现时才写 `_global.md`。用户当场纠偏（「下次 review 还是用 codex」）→ 立即写入
- **性质**：可能有效的提示、而非保证——按偏好调度失败 → 回退探测缺省，并把失败记进该文件陷阱节
- 目录不存在 → 静默创建

## 事实说明

- codex 的 skill 前缀是 **`$` 不是 `/`**；模型与 effort 是**启动参数**，中途不可切换
- worker 的完成声明 ≠ 状态推进；状态真相只在 frontmatter 与台账
- 回退边（status 置回）由**产出该结果的 skill 当场执行**（conventions §3），总控不代写 status
- review 结果不授权总控动手修——修复一律派回 eo-implement 模式二
- Review 修复不自动回 Test：先回原 reviewer 增量复审；只有结构化处置为 `复验`（或处置不可采）才派原 tester
- 并行派发 >2 个 worker 前，先报数量与预算，等用户点头

## 关键约束

| 约束 | 说明 |
|------|------|
| 三不做 | 总控不写码、不改 change 实质、不复述下游流程 |
| 先校验再裁决 | worker 交付不直接采信：三项检查 → 通过 / 打回（附证据）/ 上交用户；代用户做裁决 = 违规 |
| 反馈回路非对称 | Review 修复先走 implement↔review 短回路，再按 reviewer 的测试证据处置决定是否 Test；Test FAIL 修复则必须先回 tester |
| worker 按角色复用 | 同角色跨轮次复用原 worker（上下文资产）；跨角色隔离；换模型 / 污染 / 不可达才重建 |
| 无状态 | 不落自有状态文件；中断恢复 = 重读 frontmatter |
| 熔断只消费 | 到限即停、按下游 skill 协议问用户，绝不无限循环 |
| 汇报硬窗口 | 任何等待 ≤30 分钟必有一次进度报告；报告首要回答「需不需要你裁决」 |
| worker 零回报 | 进度由总控主动观测；派发 prompt 不得附加中途回报要求 |
| 基底即文件 | 新基底照 _template.md 建文件即生效；禁止把基底细节写回本文件 |
| 一次一收敛组 | 缺省逐 change 收敛、不交叉派发；仅当 change 间标注互不干扰（INDEX「可与 #N 并行」或用户显式指定）才圈进同一并行收敛组——组内并行、组间串行（granularity §6） |
