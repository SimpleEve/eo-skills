---
title: 看板 card 承载进度与卡点 测试报告
change_id: board-card-progress
tags: [eo-board, card, journal, stage-progress, tabs]
created: 2026-08-02
updated: 2026-08-02
status: active
summary: >
  第 1 轮：锁定套件审计通过并补 2 条缺口（无门 stage_progress=None、无 journal 动态空态 HTML）；
  12/12 绿；AC-1/2/4/5 人工过目项待用户勾选，自动化 FAIL 为零。
---

# 看板 card 承载进度与卡点 测试报告

> 关联 Change：[change.md](change.md)（验收锚点：其 §2 验收清单）
> 首轮测试日期：2026-08-02 ｜ 测试环境：macOS Darwin 25.5.0 arm64，Python 3.12.12，Node v26.5.1
> 实施基线：`base_commit` 337f79f → HEAD `bc4e335`（cli/eo-board + 锁定测试）
> ⚠️ 首轮之后正文各节为历史快照——当前状态以「FAIL 台账」与末尾「速报」为准

## FAIL 台账

无。

## AC 覆盖映射

| AC | 自动化覆盖 | 人工过目 | 本轮结论 |
| -- | ---------- | -------- | -------- |
| AC-1 五 tab 详情 | `ProjectJsSurfaceTests` 声明五 label + `detail-tab`/`detail-pane`；`ProjectJsRenderTests` DOM 渲染含五 tab 与原节内容片段 | 需 `eo-board --serve` 逐 tab 点过目 | 自动 ✅；人工 待勾 |
| AC-2 全文 tab | `test_full_text_matches_change_md_on_disk`；render 详情含 change 标题/正文片段 | 需对照 IDE 打开的 change.md | 自动 ✅；人工 待勾 |
| AC-3 journal 动态 | `JournalAndFullTextTests` 全组（有 journal / 无 journal 不污染 / 最近窗口 limit）；`test_journal_absent_renders_empty_hint_in_detail` 空态 HTML；render 含「是否需要你裁决」 | —（锁定全自动） | ✅ |
| AC-4 卡面阶段徽标 | `StageProgressTests` test/review 阶段与 label；render 卡面含 stage 文案 | 需实卡过目徽标 | 自动 ✅；人工 待勾 |
| AC-5 ≥3 轮警告 | `test_stage_warn_when_any_gate_rounds_ge_3`；render 卡面 `card-warn` | 需过目警告样式区分度 | 自动 ✅；人工 待勾 |

边界（意图声明，非 AC 编号）：`test_terminal_renderer_ignores_new_progress_fields` 确认终端形态不投影 tab/journal。

## 测试总结（首轮快照）

| 指标 | 数值 |
| --- | --- |
| 本 change 锁定单元测试总数 | 12 |
| 本 change 锁定单元测试通过 | 12 |
| 本 change 锁定单元测试失败 | 0 |
| 全仓回归（discover）总数 | 275 |
| 全仓回归通过 | 275 |
| 全仓回归失败 | 0 |
| 集成 / 浏览器人工场景 | 0（manual 不代跑） |

## 单元测试详情

### 审计结论

implement 落下的锁定文件 `tests/test_board_card_progress.py`（`test_lock_commit` ffca522 起）断言真实覆盖 AC-3/4/5 数据层与五 tab 表面；未发现弱化/删除断言。本 skill 仅补两处缺口，既有断言一字未改：

1. `test_stage_progress_none_without_gates` — 无质量门时 `stage_progress is None`（实现 `derive_stage_progress` 契约）
2. `test_journal_absent_renders_empty_hint_in_detail` — 无 journal 时详情 DOM 含「暂无 loop 窗口报告」空态且五 tab 仍在（AC-3 空态 UI 路径）

### ✅ 通过的测试

| 测试文件 | 测试用例 | 对应 AC |
| --- | --- | --- |
| `tests/test_board_card_progress.py` | `JournalAndFullTextTests.test_journal_entries_loaded_when_present` | AC-3 |
| `tests/test_board_card_progress.py` | `JournalAndFullTextTests.test_journal_absent_empty_state_without_poisoning_other_fields` | AC-3 |
| `tests/test_board_card_progress.py` | `JournalAndFullTextTests.test_full_text_matches_change_md_on_disk` | AC-2 |
| `tests/test_board_card_progress.py` | `JournalAndFullTextTests.test_parse_journal_entries_keeps_recent_window_reports` | AC-3 |
| `tests/test_board_card_progress.py` | `StageProgressTests.test_stage_progress_from_test_gate` | AC-4 |
| `tests/test_board_card_progress.py` | `StageProgressTests.test_stage_progress_from_review_gate` | AC-4 |
| `tests/test_board_card_progress.py` | `StageProgressTests.test_stage_warn_when_any_gate_rounds_ge_3` | AC-5 |
| `tests/test_board_card_progress.py` | `StageProgressTests.test_stage_progress_none_without_gates` | AC-4 边界 |
| `tests/test_board_card_progress.py` | `ProjectJsSurfaceTests.test_project_js_declares_five_tabs_and_stage_warn_hooks` | AC-1 / AC-5 表面 |
| `tests/test_board_card_progress.py` | `ProjectJsSurfaceTests.test_terminal_renderer_ignores_new_progress_fields` | 边界：终端不动 |
| `tests/test_board_card_progress.py` | `ProjectJsRenderTests.test_render_change_and_card_via_test_hooks` | AC-1~5 DOM 合成 |
| `tests/test_board_card_progress.py` | `ProjectJsRenderTests.test_journal_absent_renders_empty_hint_in_detail` | AC-3 空态 DOM |

### ❌ 失败的测试

无。

## 一次性执行证据

| 验证点 | 命令 | 关键输出 | 结论 |
| --- | --- | --- |
| 锁定套件（补缺后） | `python -m unittest tests.test_board_card_progress -v` | `Ran 12 tests in 1.998s` / `OK` | ✅ |
| 全仓回归 | `python -m unittest discover -s tests -v` | `Ran 275 tests in 94.465s` / `OK` | ✅ |

## 集成 / 场景验证详情

无 auto-heavy 场景本轮代跑。以下为 change §2 标注的 **manual** 项，**不代勾**，留给用户 / 后续人工验收：

### 场景 M1：五 tab 过目（AC-1）

- **操作步骤**：`eo-board --serve` 打开任一 change 卡详情，逐 tab 点「概览｜清单｜质量门｜动态｜全文」
- **期望结果**：点击直达对应内容、无需长滚动，原抽屉各节内容不丢
- **实际结果**：待人工
- **证据**：—

### 场景 M2：全文对照（AC-2）

- **操作步骤**：全文 tab 与 IDE 打开的同一 `change.md` 对照
- **期望结果**：内容一致
- **实际结果**：待人工（数据层 `full_text` 已与磁盘全文 `assertEqual`）
- **证据**：`test_full_text_matches_change_md_on_disk`

### 场景 M3：卡面徽标过目（AC-4）

- **操作步骤**：构造/选取 test、review 阶段各一 change，过目卡面徽标
- **期望结果**：无需点开详情即可见阶段与轮次（如 `test ≈2 轮` / `review P0×1`）
- **实际结果**：待人工（数据层 stage_progress 已断言）
- **证据**：`StageProgressTests`

### 场景 M4：≥3 轮警告样式过目（AC-5）

- **操作步骤**：找一轮次 ≥3 的 change，与其余卡片比较警告样式
- **期望结果**：`card-warn` 视觉语言一眼可辨
- **实际结果**：待人工（DOM 已断言 `card-warn` class）
- **证据**：`test_stage_warn_when_any_gate_rounds_ge_3` + render 卡面

## 未覆盖的测试场景

- AC-1 真实点击流与滚动观感：依赖浏览器人工，不沉淀为 brittle E2E
- AC-2/4/5 视觉一致性：自动化只锁数据与 class/标签，不代判 CSS 观感
- backlog 卡详情与终端形态：边界由 `test_terminal_renderer_ignores_new_progress_fields` 与意图声明覆盖；backlog 详情路径本 change 明确不动，未扩测

## 遗留问题

- 无阻塞缺陷（FAIL 台账空）
- AC-1 / AC-2 / AC-4 / AC-5 人工过目部分 **待用户勾选**，不由本 skill 代勾
- 业务代码本轮零修改；补缺仅 `tests/test_board_card_progress.py`

## 速报

结论：通过（自动化 FAIL 0 项）［第 1 轮 · revision 1 · 基线 `bc4e335`］
下一步：可进入 `/eo-review`（尚未审码）；AC-1/2/4/5 人工过目仍待用户按 change §2 验收口径勾选。

### 重跑记录 · 2026-08-02（review 轮 1 修复后）

| 验证点 | 命令 | 关键输出 | 结论 |
| --- | --- | --- | --- |
| 锁定套件（含 P1 回归） | `python3 -m unittest tests.test_board_card_progress -v` | 16/16 OK | ✅ |
| 看板缓存回归 | `python3 -m unittest tests.test_eo_board_cache -q` | 56/56 OK | ✅ |
| 全仓回归 | `python3 -m unittest discover -s tests -q` | `Ran 281 tests in 97.425s` / `OK` | ✅ |

修复 commit：`1ac1b1d`（阶段徽标当前性、tab 热刷新保留、docstring 去溯源、相关回归用例）。P1-3 wont-fix（既有脏改动保留）。P2-1 本轮不修。
速报：自动化 FAIL 0；AC-1/2/4/5 人工过目仍待用户。

### 重跑记录 · 2026-08-02（review 轮 2 · P1-5 修复后）

| 验证点 | 命令 | 关键输出 | 结论 |
| --- | --- | --- | --- |
| 锁定套件（含 P1-5 回归） | `python3 -m unittest tests.test_board_card_progress -v` | 18/18 OK | ✅ |
| 全仓回归 | `python3 -m unittest discover -s tests -q` | `Ran 283 tests in 86.258s` / `OK` | ✅ |

修复 commit：`eba11da`（轮次 warn 与当前阶段解耦；「门已通过 / archived + ≥3 轮」仍 warn）。P2-1 仍 open。
速报：自动化 FAIL 0；AC-1/2/4/5 人工过目仍待用户。

### 重跑记录 · 2026-08-02（动态/全文 mdBlock 渲染）

| 验证点 | 命令 | 关键输出 | 结论 |
| --- | --- | --- | --- |
| 锁定套件 | `python3 -m unittest tests.test_board_card_progress -v` | 18/18 OK | ✅ |
| 全仓回归 | `python3 -m unittest discover -s tests -q` | `Ran 283 tests in 87.460s` / `OK` | ✅ |

动态 tab 条目正文与全文 tab 改用 `mdBlock`；DOM 断言锁定 `j-body md-block` / `full-md md-block`、无 `<pre class="full-md">`。
速报：自动化 FAIL 0；AC-1/2/4/5 人工过目仍待用户。

### 重跑记录 · 2026-08-02（frontmatter 概览 + mdBlock 扩能）

| 验证点 | 命令 | 关键输出 | 结论 |
| --- | --- | --- | --- |
| 锁定套件 | `python3 -m unittest tests.test_board_card_progress -v` | 20/20 OK | ✅ |
| 全仓回归 | `python3 -m unittest discover -s tests -q` | `Ran 285 tests in 87.928s` / `OK` | ✅ |

概览 frontmatter 键值；mdBlock 标题/表格/代码/checkbox/有序/链接 + XSS 探针；journal 列表不回退。
速报：自动化 FAIL 0；AC-1/2/4/5 人工过目仍待用户。
