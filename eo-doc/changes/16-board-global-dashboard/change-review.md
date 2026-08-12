---
title: board 收敛为全局 dashboard Change 审查报告
change_id: board-global-dashboard
created: 2026-08-12
status: active
summary: >
  首轮全量审查发现 AC-2 无 TODO 覆盖，需修复 1 条 P0 后再进入 implement。
---

# board 收敛为全局 dashboard Change 审查报告

> 关联：[change.md](change.md) ｜ 审查日期：2026-08-12 ｜ change status：confirmed

## 审查总结

方案意图与已冻结的模式选择整体一致，7 条 AC 均可独立验证，7 条 TODO 与目标文件也基本相符；但 AC-2「保留 `--project` 语义与五 tab 详情」未被任何 TODO 显式覆盖，形成客观映射断裂。另有类型口径、文档连带面、测试资产职责、相邻 change 串行关系和性能阈值冻结方式 5 项建议交起草方裁决。结论：❌ 需修订 1 条 P0 后再进入 implement。

## Finding 台账

<!-- 状态单一来源：本 skill 建条与核销（open→verified），修订方（/eo-change）填「处置」列。wont-fix 项后续任何轮次不得重报 -->

| ID | 级别 | 摘要 | 位置 | 状态 | 处置（修订方填） |
|----|------|------|------|------|------------------|
| P0-1 | P0 | AC-2 无 TODO 显式覆盖 | §2 AC-2、§3 | verified | TODO-1 增补 AC-2 映射 + 完成判据写实（保留显式单项目分支） |
| P1-1 | P1 | `type: refactor` 与明确的用户可见行为变化不符 | frontmatter、§1 | verified | frontmatter type 改 `enhance` |
| P1-2 | P1 | 对外命令面变化未纳入用户文档与代码侧文档同步 | §3 TODO-6、§7 | verified | 新增 §4：README/docs 四件随 TODO-6 同批；eo-doc 两篇注明 doc-manager sync |
| P1-3 | P1 | TODO-7 的测试资产文件声明与写入职责冲突 | §3 TODO-7 | verified | TODO-7 移除，测试适配改列 §4 的 /eo-test 交接清单 |
| P1-4 | P1 | 相邻 change #17 与本 change 同改泳道共享资产，未声明实施顺序 | §3 TODO-4 | verified | §1 已钉决策新增「#16 先于 #17 串行」声明 |
| P1-5 | P1 | AC-7 的硬阈值仍允许实施期调整，确认后的验收尺子不稳定 | §2 AC-7、§8 OQ-1 | verified | 用户裁决：5 秒冻结为硬门，AC-7 改写、OQ-1 撤除（§8 整节省略） |

## P0 - 必须修订（阻塞 implement）

### [P0-1] AC-2 无 TODO 显式覆盖

- 类型：映射断裂
- 位置：change.md §2 AC-2、§3 TODO-1～TODO-7
- 描述：现有 TODO 的映射集合为 AC-1、AC-3、AC-4、AC-5、AC-6、AC-7，没有任何 TODO 标注 AC-2。虽然真实代码和既有测试已经存在 `--project` 路径，但 TODO 全部完成时仍无法证明入口重排没有破坏该保留语义。
- 影响：实施者可能完成全部 TODO，却遗漏显式 `--project` 分支或只验证聚合页下钻，AC-2 会悬空。
- 建议：优先在 TODO-1 增补「对应 AC-2」，并把完成判据写实为「保留 `resolve_project_token` 后的显式单项目分支；按名和按路径直达泳道页，终端 / `--html` / `--serve` 均不经过默认聚合入口且五 tab 保持」。若起草方认为入口切换与回归保护应分离，则新增一条只修改 `cli/eo-board` 的实现 TODO，并同样映射 AC-2；测试资产适配仍交 `/eo-test`。

## P1 - 建议修订（移交起草方裁决，不阻塞）

### [P1-1] 类型口径与行为面不符（类型：意图一致性）

- 位置：change.md frontmatter、§1、§2 AC-1/AC-3
- 描述：方案会改变三个默认入口、退役旗标并新增项目下拉，是明确的用户可见行为变化；`refactor` 通常表达内部重组且要求行为不变，本方案没有也不应有「行为不变」回归口径。
- 建议：把类型改为 `enhance`；若起草方把项目下拉视为独立新能力，也可裁决为 `feature`，但不应继续使用 `refactor`。

### [P1-2] 对外命令面文档连带面未入计划（类型：条件节缺失）

- 位置：change.md §3 TODO-6、§7
- 描述：TODO-6 只列 `cli/eo-board` 与 `cli/eo-helper`，但当前 `README.md`、`docs/GUIDE.md`、`docs/cli-reference.md`、`docs/how-it-works.html` 仍把无旗标入口描述为单项目、把 `--all` 描述为聚合入口；`eo-doc/state/eo-board-cli.md` 与 `eo-doc/agent-handbook/cli-eo-board.md` 也会随实现过期。
- 建议：在 §4 明列连带文档及责任归属；用户文档纳入实现批或独立文档批，`eo-doc/` 侧注明实现完成后走 `/eo-doc-manager sync`，避免把过期命令面带入归档。

### [P1-3] TODO-7 的测试资产职责不自洽（类型：TODO 拆解质量）

- 位置：change.md §3 TODO-7
- 描述：文件栏声明「修改 `tests/test_eo_board_cache.py`」，同时完成判据又明确测试文件由 `/eo-test` 落笔。按本项目测试资产单一写入规则，implement 不能完成一个以修改测试文件为文件落点的 TODO；而「预期失败清单」也没有明确的非测试资产落点。
- 建议：把 TODO-7 从 implement TODO 移到 §4 的 `/eo-test` 交接清单，列明需适配的入口、`--project`、空态、scan 与路由用例；实现批只保留业务代码 TODO 和一次性回归探针。若仍保留 TODO-7，则删除「修改测试文件」这一落点，并明确清单写入批末交付记录而非仓库测试资产。

### [P1-4] 与 change #17 的共享资产顺序未声明（类型：在途冲突）

- 位置：change.md §3 TODO-4；`eo-doc/changes/INDEX.md` #17
- 描述：本 change 的项目下拉与已 confirmed 的 #17 搜索/列显隐都会修改 `cli/eo-board` 内同一套 `PROJECT_CSS / PROJECT_MARKUP / PROJECT_JS` 资产。两者并行实施会形成高概率文本冲突和基线漂移。
- 建议：在实施编排中固定 #16 先于 #17；#16 收口后让 #17 基于新交付基线刷新再实施。若总控选择反向顺序，也应显式串行并在后实施者开始前重读共享资产，不能并行派发。

### [P1-5] AC-7 的验收阈值仍可漂移（类型：AC 稳定性）

- 位置：change.md §2 AC-7、§8 OQ-1
- 描述：AC-7 给出可度量的 `≤ 5 秒`，但同时允许「实施期上报调整」。这会让已 confirmed 的通过/失败尺子由实施结果反向决定。
- 建议：二选一写清：保留 5 秒为本 revision 的硬门，超时即报告失败并由总控裁决是否回炉；或把本轮目标改成「记录 10 项目基线且不显著回退」并在确认阶段先冻结可计算的回退阈值。不要由实施者在结果出来后自行改 AC。

## P2 - 可选优化

无。

## AC 质量检查

| AC | 用户视角 | 可验证 | 技术无关 | 备注 |
|----|---------|--------|---------|------|
| AC-1 | ✅ | ✅ | ✅ | 三种默认形态与可观察结果明确 |
| AC-2 | ✅ | ✅ | ✅ | 声明可验，但 TODO 映射悬空（P0-1） |
| AC-3 | ✅ | ✅ | ✅ | 两种 HTML 形态、项目集合与跳转结果明确 |
| AC-4 | ✅ | ✅ | ✅ | cwd 边界可独立验证 |
| AC-5 | ✅ | ✅ | ✅ | 覆盖未注册 cwd 与进程重启不残留边界 |
| AC-6 | ✅ | ✅ | ✅ | 覆盖空注册表失败/空态路径 |
| AC-7 | ✅ | ✅ | ✅ | 阈值可度量，但实施期校准口径不稳定（P1-5） |

异常/边界覆盖：AC-5 覆盖未注册 cwd，AC-6 覆盖无项目空态；`--all` 退役后的提示行为已在 TODO-1 写明，但建议后续测试阶段纳入负向用例。

## TODO↔AC 映射检查

| TODO | 对应 AC | 状态 |
|------|---------|------|
| TODO-1 | AC-1、AC-4 | ⚠️ 入口重排涉及 AC-2，但未标注（P0-1） |
| TODO-2 | AC-5 | ✅ |
| TODO-3 | AC-6 | ✅ |
| TODO-4 | AC-3 | ✅ |
| TODO-5 | AC-7 | ✅ |
| TODO-6 | AC-1 | ✅，但文档连带面缺失（P1-2） |
| TODO-7 | AC-1、AC-4 | ⚠️ 映射相关，但写入职责冲突（P1-3） |

反向覆盖：AC-1、AC-3～AC-7 均至少有一条 TODO；AC-2 无 TODO 覆盖。没有发现与 §1 意图无关的镀金 TODO，也没有占位符。

## 粒度检查

TODO 数：7（软标 3-7 / 硬标 10）｜ 全文：70 行（软标 200-500 / 硬标 700）｜ 结论：TODO 数合规、全文低于软标但方案信息完整，不属于 trivial；两个纯数字 Batch 为串行，无并行组安全问题。

Batch 1 能独立交付默认全局化 MVP，但需先补 P0-1 的 `--project` 保留口径，才能形成完整入口回归边界。Batch 2 依赖 Batch 1 的全局项目集合与路由语义，串行关系合理。

## 前提真实性抽查（维度 7）

首轮 `base_commit` 为空，按技能规则以审查时 HEAD `4c89b569658f043c7b144be64e27ae9543d92b89` 为变更前基线；另核对了 HEAD 上方当前未提交 diff，未把未提交改动当作本 change 的自证。

### 机械核验

| 断言 | 基线 | 证据 | 判定 |
|------|------|------|------|
| TODO-1～TODO-5 的修改目标与入口/聚合/泳道资产形态相符 | base_commit（HEAD） | `cli/eo-board:2022-2049`（静态项目 chip）、`cli/eo-board:2486-2559`（来源与聚合）、`cli/eo-board:3141-3305`（聚合三形态）、`cli/eo-board:3368-3448`（参数与默认分派） | ✅ 成立 |
| TODO-6 的两个修改目标存在且仍使用旧命令面 | HEAD | `cli/eo-board:3368-3400`；`cli/eo-helper:17-23` | ✅ 成立 |
| TODO-7 的目标测试文件存在且已有聚合、`--project`、空态、scan、路由基线 | HEAD | `tests/test_eo_board_cache.py:826-925`、`tests/test_eo_board_cache.py:1207-1282` | ✅ 目标存在；职责问题见 P1-3 |

### 高风险前提抽样

| 断言 | 基线 | 证据 | 判定 |
|------|------|------|------|
| 当前确有「无旗标单项目」与 `--all` 聚合两套入口，可通过重排默认分支收敛 | base_commit（HEAD） | `cli/eo-board:3413-3448`：`args.all` 走 `cmd_all`，否则从 cwd/`--project` 加载单项目后分派三形态 | ✅ 成立 |
| `--project` 当前支持名/路径直达，且存在行为基线 | base_commit（HEAD） | `cli/eo-board:3308-3326`；`tests/test_eo_board_cache.py:882-907` | ✅ 成立 |
| 聚合快照与 serve 已具备稳定路由和 `--scan` 下钻数据，可支撑项目下拉；当前 chip 确为静态文本 | HEAD + 当前未提交 diff | `cli/eo-board:2022-2049`、`cli/eo-board:2486-2531`、`cli/eo-board:3134-3283`；`tests/test_eo_board_cache.py:1234-1282` | ✅ 成立 |

## 结构完整性

| 节 | 状态 | 备注 |
|----|------|------|
| 速览 | ✅ | 用户可见差异与 §1/§2 一致，不是逐条复述 AC |
| §1 意图 + 已钉设计判断 | ✅ | 单一全局 dashboard、显式 `--project`、下拉、直接替换与 cwd 并入口径自洽 |
| §2 验收清单 | ⚠️ | 均可验证；AC-7 阈值冻结方式需裁决（P1-5） |
| §3 TODO（Batch） | ❌ | AC-2 悬空（P0-1）；TODO-7 职责冲突（P1-3） |
| 条件节 §4-§8 | ⚠️ | §7 回滚口径成立、§8 defer 仅 1 条；缺用户文档与代码侧文档连带面（P1-2） |

## 审查边界记录

- A 类判断：类型口径、文档连带面、测试资产职责、相邻 change 串行建议与 AC 阈值稳定性均在方案审查权限内，已作为 P1 随报告交付。
- B/C 类判断：未发现需要改变冻结范围、推翻已钉模式选择或执行不可逆操作的事项，本轮未触发 decision gate。
- 本报告只评审方案并做前提取证；未审实施质量，未修改 `change.md` 或业务代码。

## 复审记录（第 2 轮 · 全量 · 2026-08-12）

- 模式：任务指定增量核销；因 AC-7 从「实施期可调整」改为「5 秒冻结硬门」构成 AC 语义改写，且 §1 新增「#16 先于 #17 串行」模式选择，命中两条机械升级信号，自动升级全量复审。
- 核销：P0-1 verified（TODO-1 已映射 AC-2，并以显式 `--project` 分支、名/路径直达、三形态不经过默认聚合入口和五 tab 保持作为完成判据）；P1-1 verified（frontmatter 已改为 `type: enhance`）；P1-2 verified（§4 已列用户文档同批更新与两篇 eo-doc 的 `/eo-doc-manager sync` 责任）；P1-3 verified（原 TODO-7 已移除，测试资产适配转入 §4 的 `/eo-test` 交接清单）；P1-4 verified（§1 已声明 #16 先于 #17 串行，#17 开工前重读共享资产）；P1-5 verified（AC-7 已冻结 5 秒硬门，原 OQ-1 与 §8 已撤除）。
- AC 质量：7 条仍均为用户可观察、可独立验证且可度量；AC-5/AC-6 覆盖未注册 cwd 与空注册表边界，AC-7 的失败处置现在固定为「超时即报失败并交用户裁决」。
- TODO↔AC：TODO-1→AC-1/2/4，TODO-2→AC-5，TODO-3→AC-6，TODO-4→AC-3，TODO-5→AC-7，TODO-6→AC-1；AC-1～AC-7 全覆盖，无悬空或越界。
- TODO / 粒度：6 条 TODO、72 行，均低于硬上限；每条具备描述、文件与 AC 映射，无占位符；两个纯数字 Batch 串行，Batch 1 可形成默认入口切换且保留 `--project` 的 MVP。
- 意图 / 条件节：`enhance` 与默认入口、旗标退役、项目下拉等用户可见增强相符；§4 明确用户文档、代码侧文档和测试资产责任；§7 回滚不涉及数据迁移；无无主 defer。
- 前提真实性：以 HEAD `4c89b569658f043c7b144be64e27ae9543d92b89` 为变更前基线复核——`cli/eo-board:2022-2049` 的项目 chip 当前为静态文本，`cli/eo-board:2486-2559` 已有聚合来源/路由基础，`cli/eo-board:3308-3448` 已有 `--project` 与 `--all` 分流；`tests/test_eo_board_cache.py:877-925`、`:1234-1282` 已有空态、名/路径直达、scan 与路由基线。当前未提交 `cli/eo-board` diff 不涉及本 change 的入口/下拉方案，未被用作自证。
- 新增 finding：无。修订内容均可指认其处置来源，没有处置造假，也没有推翻冻结的 dashboard 单一口径。
- 未决：P0 0、P1 0、P2 0 → 结论：通过。
- 权限记录：上述核销与升级判定均属 A 类方案审查判断；未发现范围扩张、冻结模式冲突或不可逆事项，未触发 B/C 类 decision gate。

## 速报

结论：通过（P0 0 条）［第 2 轮 · 全量］
P0（阻塞 implement）：无。
P1（移交起草方裁决，不阻塞循环）：无（历史 5 条均已 verified）。
P2（可后置）：无。
下一步 `/eo-implement eo-doc/changes/16-board-global-dashboard/change.md`（status 若仍为 draft，先回 /eo-change 对话确认）。未决 P1 已入台账，由起草方裁决：采纳的回 /eo-change 顺手修（不触发复审），不采纳的标 wont-fix 附理由。注意：`/eo-review` 是代码审查，要在 implement 之后，现在还不轮到它。
