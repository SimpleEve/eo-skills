---
name: eo-loop
description: |
  eo 流程总控：按用户意图圈一段（入口节点 → 出口节点 → 收敛标准），把 eo-change / eo-implement / eo-archive 及可选闸门（eo-change-review / eo-test / eo-review）派发到可插拔执行基底上推进至收敛，窗口化汇报进度。触发：eo-loop / 串起来跑 / 循环推进到收敛 / 总控调度 / /eo-loop。
  NOT FOR: 单点动作（直接调对应 eo-* skill）；派出去不再监督的完全交接（orca-cli full handoff）；bug 口喷（/eo-fix）。
---

# eo-loop — eo 流程总控

总控只做五件事：**识别、派发、路由、循环、汇报**。三不做：不亲自写代码、不改 change 实质内容、不复述下游流程（节点内部怎么做由各 eo-* skill 自治）。

**总控无状态**：流程真相只在 change.md frontmatter 与报告文件里。会话断了，任何 agent 重读 frontmatter 即可从当前节点继续。

**总控在哪**：用户在哪个会话喊 /eo-loop，哪个会话就是总控。

## 前置条件

- **必须能找到 `.eo-project.json`**。同目录存在 `.eo-project.local.json` 时顶层字段覆盖合并（local 优先）。找不到 → 报错退出，提示运行 `/eo-project-init`
- 线段涉及已有 change 时，定位其 `eo-doc/changes/<NN>-<slug>/`（口头引用按 [../eo-shared/conventions.md](../eo-shared/conventions.md) §2 经 INDEX 解析）

## 调度哲学（四步闭环）

**① 圈线段**：从用户话语确定三要素——**入口节点、出口节点、收敛标准**。v3 默认线段很短：

```
默认主路：change → implement → archive
信号命中：主路对应位置插入闸门（change 确认后插 change-review；implement 后插 test / review）
```

地图是 [../eo-shared/conventions.md](../eo-shared/conventions.md) §3 的状态机。三要素判不出的，先查偏好文件补缺省（见「经验沉淀」）；仍缺 → 按封闭选择协议（[../eo-shared/questioning.md](../eo-shared/questioning.md) §4）问一次，不追问第二轮。

**入口是已确认的 change 序列**（带「依赖 #N」标注，如 brainstorming 捕获出口确认后的产物）时：按依赖序串行推进（无标注 = 串行），逐个 change 走完对应 eo-* 节点（默认主路，信号命中照常插闸门）；节点边界 = 观测点，按「可观测性」节口径汇报。

**随手小改先过 trivial 闸**：总控会话里用户随手提的修改，先按 [../eo-shared/granularity.md](../eo-shared/granularity.md) §2 判定——trivial → 总控直改（需起环境验证才派原 impl worker），commit 前缀按 conventions §2.5，不进状态机、不产工件；改动使活跃 change 的 AC / 文本与实际不符时，顺手就地精化文本。四判据任一不满足 → 回到正常圈段。

**举例措辞判据**：用户意图含「比如 / 之类 / 例如」= 形态未定稿——先安排探针对齐（change 确认）把形态钉下来再派实施节点，不得让例子直接当定稿进派发 prompt。

**条件式 Execution Guard**：圈段后若命中任一条件——**长程**（跨多轮或跨节点）、**并行**、**无人值守**、**高风险**（安全 / 权限 / 数据 / 不可逆动作）、存在**开放未知**——本线段启用 [../eo-shared/goal-contract.md](../eo-shared/goal-contract.md)，总控在**每个节点派发前**从现有真相源即时编译控制包。来源限于当前 change.md、报告、Git 基线与用户本轮授权；本轮授权只能收紧运行边界，若与已冻结的 Why / 范围 / AC 冲突，必须先走用户裁决与 change 回炉。控制包只存在于本轮派发上下文，不落盘、不造第二信源。未命中条件则沿用普通调度。

控制包只投影六项，不创造新要求：**意图与出口 / 证据门（每项结论由哪个角色基于什么工件证明）/ 运行边界 / 取舍顺序（引 goal-contract）/ 未知权限（引 goal-contract Unknown 分流）/ 路由事实**。

Unknown 的运行时动作（分类语义以 goal-contract 为唯一来源）：

- **A 类**：核对确在权限包络内 → 允许 worker 先做后报
- **B 类**：worker 变更前发求裁决信号并暂停受影响分支；总控把同窗 B 类合并成一次封闭选择交用户
- **C 类**：worker 变更前立即停下，总控立即上交用户
- **证据未知**：只允许一次有界探测（写清问题、预算、停止条件）；仍拿不到 → fail-closed，结论只能「未验证 / 阻塞」，不得用 worker 自述补证

**② 选基底**：对线段上每个节点确定执行者与模型，三级优先：**本次用户显式指定 > 偏好文件 > 探测缺省**。偏好层与探测缺省均**不静默生效**：命中偏好条目或探测选定后，开跑前列出「节点 → 基底/模型」与依据问一次「按此跑？」；确认后收口照常回写偏好。运行时 `ls` 本 skill `references/substrates/*.md` 得到基底清单，读候选文件按其「探测」节确认可用。

**③ 派发、路由与风险升级**：按基底文件「派发」节把节点交出去。worker 完成后，默认只读取决定下一步所需的**路由事实**：frontmatter 当前状态、预期工件指针、报告结论、未决清单。这是路由职责，不是对 worker 内容再做一轮核查；正常路径不打开完整 diff、不重跑节点命令。

**无风险即推进**：路由事实齐备且不冲突 → 直接进下一节点。交付来自其他 agent、worker 首次参与、换基底、普通节点交接，均**不是风险信号**；不得因此抽查或信任分层。

只有出现下列**可指认的风险信号**才升级核查；主观不信任不构成信号：

- frontmatter、预期工件、报告结论、worker 完成声明互相冲突
- 推进所必需的工件或字段缺失、不可解析，或存在未提交交付改动
- 已有可观察证据显示节点越过角色权限或约定文件边界
- AC、安全、权限、数据或不可逆动作发生本轮计划外变化
- worker 主动上报 Unknown B / C、证据未知、阻塞或决策门
- 同一交付被打回后仍重复出现同类异常

升级后只处理触发信号对应的范围：状态/工件缺陷打回原 worker；需要实质判断时派对应有权节点；产品/架构分歧、范围变更、AC 豁免、熔断等超总控权限事项停下上交用户。同一节点打回 2 次仍不合格 → 升级为卡点问用户。总控不得亲自实施、改测试、兼任审查。

**并行派发**（判据与合流见 [../eo-shared/granularity.md](../eo-shared/granularity.md) §6）：同一 change 的同层并行批（Batch 2a/2b）。纪律：

- 派发前先做**文件集机械校验**（两两不相交；不过 → 降级串行并一句话报告）
- 一并行 worker 一**独立 worktree**；同层全部收口后指派其一执行合并与合流 checkpoint
- 并行派发 >2 个 worker 前先报数量与预算，等用户点头

**④ 收敛判定**：对照收敛标准——出口节点达成 + 所有已产报告无未决阻塞项。未收敛走反馈回路：

- 报告有未决 P0/P1 或测试失败 → 原 impl worker 走 /eo-fix 循环内分支修复 → 回**原**复审方核销（增量，不重开全文）
- acceptance 打回 → implement 修复 → 有 review 闸门的回原 reviewer 核销
- 方案需实质修订 → eo-change 回炉

**收敛即交付汇报**：出口节点达成时，总控向用户发**完整交付汇报**——回复契约四条（[../eo-shared/reply-contract.md](../eo-shared/reply-contract.md)）+ 证据面渲染（引 change 目录 `evidence.md` 与 frontmatter `brief`，引用不重建、不转述 worker 速报）；出口是 archive 时，归档确认提问按 eo-archive 第一层口径与该汇报同条发出。线段收尾不得只有三行归档速报。

**打地鼠信号与裁决门**：同一 change 修复轮次 ≥2 且各轮**失败触发位置互不相同**（凭报告未决清单的位置列机械可判），或修复轮次 ≥3 → 停下向用户发封闭选择四选一：

a) **全链审查**（链路类缺陷缺省推荐）——原 impl worker 走 /eo-fix 深挖链路变体：枚举链上全部可死点、逐点配恢复证明，按死点矩阵批量修复
b) **继续逐点修复**——缺陷相互独立、非链路形态时
c) **卡点检查**——方向存疑，新鲜上下文做根因分类（/eo-fix 子流程）
d) **回炉**——方案本身要改

总控不代答、不以任何形式默认继续逐点修复。

## 节点清单

| 节点 | 消费 | 产出 | 边界 |
|------|------|------|------|
| eo-change | 意图 / 回炉反馈 | change.md（draft → confirmed 经用户确认） | 含风险信号播报与回炉子流程 |
| eo-change-review（可选闸门） | draft/confirmed 的 change.md | change-review.md | 信号命中或点名才派 |
| eo-implement | confirmed 的 change.md | 业务代码 + 测试 + AC 勾选（implementing） | 反馈修复归 /eo-fix 循环内分支 |
| eo-test（可选闸门） | implementing 后的代码 | 测试补缺 + test.md | 严禁改业务代码 |
| eo-review（可选闸门） | implementing 后的代码 | review.md（通过 → reviewed） | 代码级审查 |
| eo-archive | implementing / reviewed | archived（不可逆） | 四问核对门 |

## 执行基底（可插拔）

基底 = 「把一个节点交给谁执行」的载体。一基底一文件，放 `references/substrates/`，增减基底 = 加删文件。每个基底文件必须含五节（照 `references/substrates/_template.md`）：**探测 / 派发 / 等待与观测 / 回收 / 已知陷阱**。「已知陷阱」节只放出厂陷阱——运行时新学到的坑记进偏好文件的「已知陷阱」节（`~/.eo-skills/loop/preferences/`，条目前缀 `[<基底名>]`，跨项目写 `_global.md`），读基底文件时一并读。

初始三基底与优先倾向（被 ② 的三级优先覆盖）：

| 调用形态 | 倾向基底 |
|----------|----------|
| 总控是 Claude Code，执行者也是 Claude | claude-subagent |
| 总控运行在 Codex 侧 | codex-subagent |
| 节点要跨 agent 运行 | orca-orchestration |

**交互式硬约束（全基底通用）**：节点派发一律走**交互式通道**——总控会话内 subagent，或 orca 交互终端 + dispatch task。**严禁 `codex exec`、`claude -p` 等一次性非交互式调用**承载节点：纯黑盒、无会话复用、无求裁决通道。

**派发 prompt 纪律**：写目标、不写步骤——只给节点 skill 名、change 目录路径、本轮收敛标准、必要输入；命中 Execution Guard 时再附即时控制包；不复述下游流程；不要求 worker 中途回报进度。**Unknown 上报**：仅 A 类可先斩后奏随交付记录；B / C 类须变更前求裁决。

**worker 复用纪律**：一个 change 的 loop 内，worker 按**角色**一次创建、跨轮次复用——修复回原 impl worker，核销回原复审方（增量核销依赖其上下文）。边界：**跨角色必须隔离**（review / test 绝不复用 impl worker——独立性是审查的价值）；重建仅当换执行者/模型、上下文已污染、或 worker 不可达。

## 可观测性：窗口化等待 + 主动观测

**进度是总控查出来的，不是 worker 报上来的**：worker 除完成/求裁决信号外零回报义务。总控在窗口内主动读证据——终端输出、change.md 勾选、报告增量、git log——手段见各基底文件「等待与观测」节。

一切等待必须窗口化，单窗 ≤10 分钟。**窗口到期或观测点（节点边界），无论有无进展**，向用户发进度报告并追加到 `tmp/eo/loop/<slug>/journal.md`：

```
• <HH:MM> <本窗口事件标题>

<是否需要用户裁决——无则明说「没有需要你裁决的事项」；brief 级摘要：原样引用当前 change 的 brief，未写则明说「brief 未写」>

<实质摘要：按主题归组的要点，不是操作流水账>

- 派发：<task / dispatch 凭据或 worker 标识>
- owner：<基底 + 模型>
- 当前规则：<本轮循环策略一句>

下一次固定进度报告约 <HH:MM +10min>。
```

brief 级摘要取 change.md frontmatter 的 `brief`（写法与生产时机见 [../eo-shared/summary.md](../eo-shared/summary.md)）：总控只引用、不代写不改写；窗口中途 brief 无变化时一句带过。

journal 属 tmp/eo 命名空间（conventions §1）：可丢弃、不作信源。

## 经验沉淀（调度偏好）

位置 `~/.eo-skills/loop/preferences/`：`_global.md`（跨项目）+ `<项目短名>.md`（覆盖全局同名条目）；格式见 [references/preferences-format.md](references/preferences-format.md)。

- **读**：② 选基底时第二优先级——列出命中条目请用户确认后生效；① 圈线段判不出时查「习惯线段」节
- **写**：收口时回写本次实际生效的「节点 → 基底/模型」映射，**缺省写进 `<项目短名>.md`**；用户明示跨项目或同一映射已在 ≥2 个项目文件出现时才写 `_global.md`。用户当场纠偏 → 立即写入
- **性质**：提示而非保证——按偏好调度失败 → 回退探测缺省，并把失败记进该文件陷阱节
- **基底操作层的坑**（注入被吞、handle 漂移这类）也记进偏好文件的「已知陷阱」节：条目前缀 `[<基底名>]`，跨项目通用写 `_global.md`、项目特有写 `<项目短名>.md`；基底文件的「已知陷阱」节只放出厂内容，不写

## 事实说明

- codex 的 skill 前缀是 **`$` 不是 `/`**；模型与 effort 是启动参数，中途不可切换
- worker 的完成声明 ≠ 状态推进；状态真相只在 frontmatter 与报告
- 回退边（status 置回）由产出该结果的 skill 当场执行（conventions §3），总控不代写 status
- review 结果不授权总控动手修——修复一律派回原 impl worker 走 /eo-fix 循环内分支
- 并行派发 >2 个 worker 前，先报数量与预算，等用户点头

## 关键约束

| 约束 | 说明 |
|------|------|
| 三不做 | 总控不写码、不改 change 实质、不复述下游流程 |
| 严禁非交互派发 | 节点执行必须走交互式通道；一次性调用全面禁止 |
| 条件式控制包 | 仅长程 / 并行 / 无人值守 / 高风险 / 开放未知时即时编译；不落盘 |
| Unknown 权限 | 仅 A 类可先做后报；B / C 类变更前进决策门；证据未知有界探测后 fail-closed |
| 风险触发式核查 | 正常交付只消费路由事实并推进；仅有客观风险信号时针对异常范围升级 |
| worker 按角色复用 | 同角色跨轮次复用；跨角色隔离；换模型 / 污染 / 不可达才重建 |
| 无状态 | 不落自有状态文件；中断恢复 = 重读 frontmatter |
| 熔断只消费 | 打地鼠/轮次到限即停、按协议问用户，绝不无限循环 |
| 汇报硬窗口 | 任何等待 ≤10 分钟必有一次进度报告；报告首要回答「需不需要你裁决」 |
| 收尾必发交付汇报 | 线段收敛 / 归档确认前，交付汇报（回复契约四条 + 证据面渲染）与确认提问同条发出，不得只有三行速报 |
| worker 零回报 | 进度由总控主动观测；派发 prompt 不得附加中途回报要求 |
| 基底即文件 | 新基底照 _template.md 建文件即生效；禁止把基底细节写回本文件 |
| 一次一收敛组 | 缺省逐 change 收敛；带「依赖 #N」标注的 change 序列按依赖序串行推进 |
