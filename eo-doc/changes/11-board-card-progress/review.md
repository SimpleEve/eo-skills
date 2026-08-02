---
title: 看板 card 承载进度与卡点代码审查报告
change_id: board-card-progress
tags: [eo-board, card, journal, stage-progress, tabs]
created: 2026-08-02
updated: 2026-08-02
status: active
summary: >
  首轮审查发现 4 条 P1：阶段徽标会把历史报告/历史 P0 当成当前状态，serve 刷新会重置活动 tab，
  实施夹带 3 处未映射的旧卡面行为变化，且测试 docstring 留有 AC 溯源标注；P0 为零，暂不通过。
---

# 看板 card 承载进度与卡点 代码审查报告

> 关联 Change：[change.md](change.md)（检查表：其 §2 验收清单 AC-1~5）
> 首轮审查日期：2026-08-02 ｜ 审查范围：`337f79f..bd4856b`，重点为 `cli/eo-board`、`tests/test_board_card_progress.py`
> 本 change 为 light；按本次显式派发仅写审查报告，不改业务代码、测试或 `change.md` status，manual AC 不代勾。
> ⚠️ 首轮之后正文各节为历史快照——当前状态以「Finding 台账」与末尾「速报」为准

## Finding 台账

| ID | 级别 | 摘要 | 位置 | 状态 | 根因 | 首见/最近轮 | 基线/修复 commit |
|----|------|------|------|------|------|-------------|------------------|
| P1-1 | P1 | 阶段徽标把历史报告存在性和历史 P0 标题当成当前状态 | `cli/eo-board:464` | verified | implementation | 1/2 | `bd4856b` / `1ac1b1d` |
| P1-2 | P1 | serve 数据刷新会把用户选中的详情 tab 重置为概览 | `cli/eo-board:1711` | verified | implementation | 1/2 | `bd4856b` / `1ac1b1d` |
| P1-3 | P1 | 实施夹带 3 处未映射到 AC/决策的旧卡面行为变化 | `cli/eo-board:1527` | waived | implementation | 1/2 | `bd4856b` / —（用户裁决：总控已核实为既有工作区改动，非本 change 引入，保留） |
| P1-4 | P1 | 测试 docstring 写入 AC 编号流程溯源 | `tests/test_board_card_progress.py:428` | verified | implementation | 1/2 | `bd4856b` / `1ac1b1d` |
| P1-5 | P1 | 无活动阶段时丢失任一门 ≥3 轮的警告样式 | `cli/eo-board:562` | verified | implementation | 2/3 | `1ac1b1d` / `eba11da` |
| P2-1 | P2 | tab 的 ARIA/键盘语义未形成完整关联 | `cli/eo-board:1498` | open | implementation | 1/3 | `bd4856b` / ~ |

## 审查总结（首轮快照）

主体结构与既有单文件看板架构一致：`PROJECT_CSS` / `PROJECT_MARKUP` / `PROJECT_JS` 各只有一份定义，单项目仍由 `render_html` 唯一出口组装，聚合快照复用 `PROJECT_ASSETS`；新 Python 路径只有读取，没有新增项目写入或第三方依赖。journal 按 eo-loop 的 `• HH:MM` 骨架切分最近 5 条，无法匹配时降级为原文尾部，空文件、缺文件和读取异常均不污染其他字段。终端 `render_terminal` 与 backlog 详情 `renderBacklog` 相对基线逐字一致。

但卡面“当前阶段”没有真正判定当前性：实现仅按报告是否存在固定覆盖，且 review 的 P0 数来自历史详情标题。实际对本仓数据构建时，已归档且末尾速报明确“通过（P0 0 条）”的 `sync-plugin-layer` 被显示为 `review P0×1`。另外，serve 热刷新重建抽屉时总回到概览，动态/质量门内容更新恰会触发这一退回。两项均影响核心 Outcome，因此本轮有 P1 待修。

独立验证：`python3 -m unittest tests.test_board_card_progress -v` 为 12/12 通过；`python3 -m unittest -q tests.test_eo_board_cache` 为 56/56 通过；`git diff --check 337f79f..HEAD` 通过。测试通过不覆盖下列语义问题，AC-1/2/4/5 的人工过目仍由用户完成。

## P0 - 必须修复（阻塞性问题）

无。

## P1 - 建议修复（重要但不阻塞）

### [P1-1] 阶段徽标会把历史结果冒充为当前状态

- **类型**：逻辑错误
- **位置**：`cli/eo-board:464`（固定覆盖链）；`cli/eo-board:484`（历史 P0 标题计数）；`cli/eo-board:489`（未勾 acceptance 无条件覆盖）
- **描述**：`derive_stage_progress` 不接收 change status、门结论或触碰时间，只要报告存在就按 `change_review -> test -> review -> acceptance` 固定覆盖。review 标签又直接使用 `parse_review_gate` 对历史 `### [P0-*]` 标题的总数，因此 finding 已 verified、速报已通过后仍会显示 `review P0×N`；只要 acceptance 存在且有未勾项，还会遮掉失败的 test/review。
- **影响**：卡片正面会错误回答“现在卡在哪”，与 AC-4 及 brainstorm 的核心 Outcome 相反；用户可能把已清零的 P0 当成当前阻塞，或看不到真正未过的门。
- **证据**：当前仓真实构建结果中，`sync-plugin-layer` 的 review 速报为“通过（P0 0 条，P1 0 条）”，徽标却是 `review P0×1`。
- **建议**：按 status、未决台账/FAIL 与门的实际新旧关系推导当前门；review P0 数读取台账中未决状态，至少在速报通过时不得展示历史 P0 数。acceptance 仅在流程实际进入人工验收时覆盖。

### [P1-2] serve 热刷新丢失当前 tab

- **类型**：潜在 Bug
- **位置**：`cli/eo-board:1711`；关联 `cli/eo-board:1422`、`cli/eo-board:1671`
- **描述**：轮询发现数据变化后调用 `openDetail(openDetailId, true)`，但 `renderChange` 每次都把概览写成唯一 active pane；`isRefresh` 只阻止 scrollTop 清零，没有保存/恢复活动 tab。
- **影响**：用户正在“动态”“质量门”或“全文”查看时，journal/gate 更新会把界面突然切回概览，tab 直达状态不能稳定保持。现有 Node 测试只断言 HTML 里有五个 tab，没有触发点击或刷新路径。
- **建议**：刷新前记录活动 `data-tab`，重建后恢复同一 pane（目标不存在时再回概览），并补一条点击后刷新仍停留原 tab 的 DOM 回归。

### [P1-3] AC 之外改变了既有卡面字段渲染

- **类型**：范围外行为新增
- **位置**：`cli/eo-board:1527`、`cli/eo-board:1541`、`cli/eo-board:1556`
- **描述**：同一实施提交把测试锁定 commit 从完整显示改成 8 位 + tooltip，并把 change/backlog 卡标题从纯文本转为迷你 Markdown；这些变化不映射 AC-1~5、TODO 或已钉决策。`renderBacklog` 详情本身确实逐字未动，但 backlog 卡正面行为仍被顺带改变。
- **影响**：扩大了本 change 的回归面，也破坏“只改 change 详情与进度卡面”的可审计边界。
- **建议**：撤回这三处捎带变化，另有明确需求时走独立 change 或 backlog。

### [P1-4] 测试注释含流程溯源编号

- **类型**：注释纪律（溯源标注）
- **位置**：`tests/test_board_card_progress.py:428`
- **描述**：测试 docstring 以 `AC-3` 标注来源，违反 `eo-shared/conventions.md` §2.6“溯源不进注释”；commit 前缀与 change/test 报告已承担追踪关系。
- **影响**：归档后注释会随 AC 编号变化而腐烂，并把流程工件语义带入长期代码。
- **建议**：仅保留领域行为描述，例如“无 journal 时动态 pane 出空态且五 tab 保持可用”。

## P2 - 可选优化（锦上添花）

### [P2-1] tab 语义对辅助技术不完整

- **位置**：`cli/eo-board:1422`、`cli/eo-board:1641`
- **描述**：按钮/面板有 `role=tab/tabpanel` 与 `aria-selected`，但没有稳定 `id`、`aria-controls`、`aria-labelledby`、roving tabindex 或左右方向键切换；隐藏 pane 也未同步 `aria-hidden`。
- **建议**：在不改变视觉的前提下补齐 WAI-ARIA tab 关联和键盘导航。

## 验收标准覆盖检查

| AC 编号 | 描述 | 状态 |
|---------|------|------|
| AC-1 | 五 tab 切换、原抽屉内容不丢 | ⚠️ 部分通过：五 pane 分组、点击绑定与内容迁移成立；serve 刷新不保留活动 tab（P1-2），人工点击/滚动观感待用户 |
| AC-2 | 全文 tab 与 change.md 一致 | ✅ 实现覆盖：磁盘全文原样读取，经 JSON 注入和 HTML 转义后放入 `<pre>`；人工对照待用户 |
| AC-3 | journal 最近窗口、有/无两态及降级 | ✅ 通过：最近 5 条、裁决行、无 journal 空态和解析失败尾部降级均有代码路径；锁定测试通过 |
| AC-4 | 卡面显示当前质量门阶段与轮次 | ❌ 未通过：徽标存在，但会展示历史 P0/错误阶段（P1-1）；人工视觉待用户 |
| AC-5 | 任一质量门轮次 ≥3 显示警告 | ✅ 实现覆盖：跨 change-review/test/review 取最大轮次，`card-warn` 复用 warn 色；人工区分度待用户 |

## TODO 完成度检查

本 change 为 light，无 §3 TODO；AC 即工作清单。反向核对发现 3 处无法映射 AC/已钉决策的卡面行为变化，见 P1-3。

## 架构与边界核对

| 核对项 | 结论 |
|--------|------|
| 三资产与唯一出口 | ✅ `PROJECT_CSS` / `PROJECT_MARKUP` / `PROJECT_JS` 各一份；`render_html` 一份；聚合快照复用 `PROJECT_ASSETS` |
| journal 降级 | ✅ 标准骨架分条；无匹配时保留末 40 行；缺失/空/读取异常均有独立降级 |
| 只读铁律 | ✅ 新增业务路径仅 `Path.read_text`，未新增项目写入；既有 HTML 输出命令边界未变 |
| 零第三方依赖 | ✅ imports 仍为标准库 + 仓内 `eo_lib`；标准库守护测试通过 |
| 终端形态 | ✅ `render_terminal` 相对基线逐字一致 |
| backlog 详情 | ✅ `renderBacklog` 相对基线逐字一致；但 backlog 卡标题有范围外变化，见 P1-3 |
| manual AC | ⏳ AC-1/2/4/5 人工过目未由本轮代勾 |

## 第 2 轮记录（revision 1 · 2026-08-02）

- 审查基线：`1ac1b1d`（`51c9cf4` 仅回填台账与测试重跑记录，无业务代码）
- 核销：P1-1 verified——`derive_stage_progress` 已结合 status、速报结论与台账未决 P0；本仓真实构建中 `sync-plugin-layer` 为 `stage_progress=None`，不再显示历史 `review P0×1`。
- 核销：P1-2 verified——刷新前读取 `.detail-tab.active`，重建后经 `bindDetailTabs(..., restoreTab)` 恢复；新增 DOM 回归真实点击“动态”后模拟 refresh，前后均为 journal pane。
- 核销：P1-4 verified——原 `AC-3` docstring 已改为纯领域行为描述，修复 diff 未发现新的流程溯源注释。
- 裁决：P1-3 waived——按本轮明确输入，总控已核实三处为用户工作区既有改动而非本 change 引入；不再阻塞。
- 保留：P2-1 open——本轮明确后置，未要求修复，不阻塞结论。
- reopen：无。
- 新增：[P1-5] 无活动阶段时丢失任一门 ≥3 轮的警告样式 — `cli/eo-board:562`。

### [P1-5] 警告状态被错误绑定到“当前阶段”是否存在

- **类型**：功能回归
- **位置**：`cli/eo-board:562`；关联 `cli/eo-board:490`、`cli/eo-board:568`、`cli/eo-board:1600`
- **描述**：修复将已通过门从“当前阶段”排除是正确的，但 `stage is None` 时直接返回 `None`，使 `max_rounds >= 3` 的 warn 也一起丢失；archived 更在计算轮次前直接返回。`changeCard` 的 `card-warn` 只读取 `stage_progress.warn`，因此警告无法独立保留。
- **影响**：AC-5 要求“任一质量门轮次 ≥3”的 change 出现警告样式，不以当前门是否未决为条件。当前内存探针中，`status=implementing`、change-review 已通过且 `rounds=3` 返回 `None`；本仓 `board-all-v2`（历史 review 约 4 轮）也从 `warn=true` 变为无 `stage_progress`。
- **建议**：把历史轮次警告与当前阶段标签解耦；即便不展示已通过/archived 的阶段徽标，仍让卡片获得可独立消费的 `warn` 信号，并补“门已通过但轮次 ≥3”回归。

- 独立验证：`python3 -m unittest tests.test_board_card_progress -v` 为 16/16 通过；`python3 -m unittest -q tests.test_eo_board_cache` 为 56/56 通过；`git diff --check 127045c..HEAD` 通过。现有测试未覆盖“门已通过且轮次 ≥3”组合，故未拦住 P1-5。
- 本轮结论：仍有 P1 待修；P1-1/2/4 已核销，P1-3 已裁决豁免。

## 第 3 轮记录（revision 1 · 2026-08-02）

- 审查基线：`eba11da`（`7eef7bf` 仅回填 P1-5 fixed 状态与测试重跑记录，无业务代码）
- 核销：P1-5 verified——`_warn_only()` 把 warn 从当前 stage/label 解耦；无活动阶段与 archived 均在 `max_rounds >= 3` 时返回 `{stage: None, label: None, warn: True}`，`changeCard` 独立读取 `sp.warn` 挂 `card-warn`。
- 交叉复验：本仓真实 `sync-plugin-layer` 与 `board-all-v2` 均为 `stage=None`、`rounds=4`、`warn=true`；Node 渲染出的两张卡都含 `card-warn`，且不含历史 `P0×`，P1-1 当前性语义未回退。
- 保留：P2-1 open——本轮仍按既定后置，不阻塞通过。
- reopen：无。
- 新增：无；`1c6cce2..7eef7bf` 修复增量未发现新的 P0/P1/P2。
- 独立验证：`python3 -m unittest tests.test_board_card_progress -v` 为 18/18 通过；`python3 -m unittest -q tests.test_eo_board_cache` 为 56/56 通过；`git diff --check 1c6cce2..HEAD` 通过。
- 本轮结论：通过；台账无 `open`/`fixed` P0/P1，P1-3 为用户裁决 waived，P2-1 后置。

## 速报

结论：通过（P0 0 条，P1 0 条，P2 1 条）［第 3 轮 · revision 1 · 基线 `eba11da`］
P2（可后置）：
1. tab 的 ARIA/键盘语义不完整 — `cli/eo-board:1498`
下一步：代码审查已通过；light change 保持 `implementing`，等待 AC-1/2/4/5 manual 用户验收后走轻档完成门/归档收口。

### 验收反馈就地精化 · 2026-08-02
用户反馈「动态/全文」纯文本呈现：已改为既有 `mdBlock` 渲染（不扩渲染器）；AC-2/AC-3 措辞就地补 markdown 口径。见后续 implement commit。
