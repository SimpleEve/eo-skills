---
title: board 收敛为全局 dashboard 测试报告
change_id: board-global-dashboard
tags: [eo-board, dashboard, multi-project, test]
created: 2026-08-12
updated: 2026-08-12
status: active
summary: >
  第 2 轮定向复验通过（Review 第 2 轮 @ 98de445）：linked-worktree --project html/serve
  直达、默认同仓去重、backlog 纯文本、README↔helper 菜单映射全绿；交付基线 98a11cc。
---

# board 收敛为全局 dashboard 测试报告

> 关联 Change：[change.md](change.md)（验收锚点：其 §2 验收清单）
> 首轮测试日期：2026-08-12 ｜ 测试环境：Python 3.12.12 / macOS Darwin / node（挂载路径）
> ⚠️ 首轮之后正文各节为历史快照——当前状态以「FAIL 台账」与末尾「速报」为准

## FAIL 台账

| ID | 级别 | 摘要 | 位置 | 状态 | 根因 | 首见/最近轮 | 基线/修复 commit |
|----|------|------|------|------|------|-------------|------------------|
| （无） | — | — | — | — | — | — | — |

## 测试总结（首轮快照）

| 指标           | 数值 |
| -------------- | ---- |
| 单元测试总数   | 95   |
| 单元测试通过   | 95   |
| 单元测试失败   | 0    |
| 集成测试总数   | 5    |
| 集成测试通过   | 5    |
| 集成测试失败   | 0    |

说明：单元测试 = `tests.test_eo_board_cache`（80）+ `tests.test_eo_helper`（15）；集成 = auto-heavy AC-1 三形态 + AC-3 html/serve 下拉跳转 + AC-7 10 项目计时（一次性执行证据）。

## 单元测试详情

### ✅ 通过的测试

| 测试文件 | 测试用例（代表） | 对应 AC / TODO |
| -------- | ---------------- | -------------- |
| `tests/test_eo_board_cache.py` | BoardGlobalDashboardTests（默认终端/html、cwd 并入、空态、`--project` 终端、dashboard_projects 注入、snapshot/serve 下拉） | AC-1..AC-6 / TODO-1..4 |
| `tests/test_eo_board_cache.py` | BoardMultiProjectTests（聚合行、坏条目、scan 去重、`--all` 退役、scan 默认可组合、`--project` 歧义） | AC-1, AC-2, AC-5, AC-6 |
| `tests/test_eo_board_cache.py` | BoardAllStreamDataTests / HomeView / CardsView / RouteTests / SnapshotRoute / Aggregate / Regression | 聚合数据层、路由、缓存、文档口径回归 |
| `tests/test_eo_board_cache.py` | BoardCacheServeTests CLI serve 热刷新（默认全局 + cwd 并入 + `/p/<key>`） | AC-1, AC-5 |
| `tests/test_eo_helper.py` | 菜单 5 项全局口径、exec/run 编号、help 输出 | TODO-6 |
| `tests/test_eo_helper_pty.py` / `test_eo_sync_watch_integration.py` | helper 实机菜单、board 探针去 `--all` | TODO-6 / 连带适配 |

### ❌ 失败的测试

无。

## 一次性执行证据

| 验证点（AC / 输入） | 命令 | 关键输出 | 结论 |
| ------------------- | ---- | -------- | ---- |
| AC-1 终端默认全局 | `eo-board`（隔离 `EO_HOME` + 2 注册项目） | `eo board · 全局 dashboard · 注册 2 项目`；含 alpha/beta 行 | ✅ |
| AC-1 `--html` 默认全局 | `eo-board --html -o dash.html --no-open` | 含 `id="eo-board-all-data"`、`所有项目` | ✅ |
| AC-1 `--serve` 默认全局 | `eo-board --serve --port <free> --no-open` | `/` 为聚合首页；`/data.json` 含 `reg_count`/rows | ✅ |
| AC-1 `--all` 退役 | `eo-board --all` | `error: --all 已退役：全局 dashboard 已是默认形态，去掉该旗标即可` | ✅ |
| AC-3 html 下拉数据 | 解析 10+ 项目快照内嵌 JSON + 脚本 | `dashboard_projects` href 均为 `#/p/...`；脚本含 `project-switch` 与 `location.href = switcher.value` | ✅ |
| AC-3 serve 下拉跳转 | `GET /p/<key>` + `GET /p/<other>` | 页内 `dashboard_projects` 12 项、`href` 为 `/p/...`；选中非当前项 HTTP 200 | ✅ |
| AC-7 10 项目计时 | 注册 10 项目后 `eo-board --html` | `elapsed=0.342s`（硬门 ≤5s） | ✅ |

## 集成 / 场景验证详情

### 场景 1：三形态默认全局 dashboard（AC-1）
- **操作步骤** ｜隔离 EO_HOME，注册 alpha/beta，分别跑无旗标终端、`--html`、`--serve` ｜ **期望** 均为聚合首页而非单项目 ｜ **实际**：✅ ｜ **证据**：见上表

### 场景 2：泳道项目下拉 html + serve（AC-3）
- **操作步骤** ｜html 快照内嵌 `dashboard_projects` + node 挂载路径断言 select；serve 拉 `/p/<key>` 数据与跨项目 href 可达 ｜ **期望** 两种形态均可列出全部可下钻项并跳转 ｜ **实际**：✅ ｜ **证据**：`BoardGlobalDashboardTests` + 一次性执行

### 场景 3：10 项目快照性能（AC-7）
- **操作步骤** ｜注册 10 项目 `time` 等价 perf_counter 跑 `--html` ｜ **期望** ≤5s ｜ **实际**：0.342s ✅

## 未覆盖的测试场景

- 浏览器内真实点击下拉 option 的视觉点击流：由 node 挂载路径 + 内嵌脚本/数据契约覆盖跳转机制（`change → location.href = option.value`），未起真实 GUI 浏览器。
- 工作区存在与本 change 无关的未提交 `cli/eo-board` 脏改动（P2 卡面展示）；验证按当前工作树执行，交付基线 H 仅含已提交本 change 业务+测试资产。

## 遗留问题

无阻塞项。下一步由 eo-review 在基线 `5679e2e` 上做代码审查（status 仍为 `implementing`）。

## 第 1 轮记录（revision 1 · 2026-08-12）

- 测试基线：`5679e2e58a4e831ea5802487964f29785e9dc823`
- 验证方式：首轮完整
- 触发来源：首轮
- 来源 Test：无；当前交付基线：`5679e2e58a4e831ea5802487964f29785e9dc823`
- 测试资产提交：`5679e2e`（`[board-global-dashboard] 适配测试：默认全局入口与项目下拉`；触及 `tests/test_eo_board_cache.py`、`tests/test_eo_helper.py`、`tests/test_eo_helper_pty.py`、`tests/test_eo_sync_watch_integration.py`）
- 重跑范围：全部 AC-1..AC-7；board/helper 相关单元测试全集；auto-heavy AC-1/AC-3；AC-7 计时
- 沿用范围：无
- 范围校验：首轮完整（全部证据均在重跑范围）
- 核销：无
- reopen：无
- 新增：无
- 本轮结论：通过（失败 0 项）

## 第 2 轮记录（revision 1 · 2026-08-12）

- 测试基线：`98a11cc40ba7a8c7ee9274d2ab5eada065d43826`
- 验证方式：定向复验
- 触发来源：Review 第 2 轮 @ `98de445`
- 来源 Test：第 1 轮 @ `5679e2e`；当前交付基线：`98a11cc40ba7a8c7ee9274d2ab5eada065d43826`
- 测试资产提交：`98a11cc`（`[board-global-dashboard] 复验补缺：linked-worktree 直达与菜单映射`；触及 `tests/test_eo_board_cache.py`、`tests/test_eo_helper.py`）
- 重跑范围：
  - AC-2：`test_project_html_linked_worktree_sets_initial_route_for_explicit_path`、`test_project_serve_linked_worktree_route_and_data_are_reachable`、`test_project_by_name_and_by_path_from_anywhere`、`test_project_html_opens_swimlane_via_initial_route_with_home_link`、`test_project_terminal_still_directs_to_single_project_summary`
  - 默认同仓去重：`test_default_aggregate_still_dedups_same_repo_without_explicit_dir`、`test_scan_dedups_same_repo_worktrees`
  - backlog 纯文本：`test_backlog_note_renders_as_escaped_plain_text_not_mdinline`
  - README↔helper：`HelperMenuMapTests`（含 `test_readme_faq_menu_numbers_match_helper_map`）
  - 依赖冒烟：`BoardGlobalDashboardTests` 其余用例（默认入口/下拉数据层）
- 沿用范围：第 1 轮已通过且本轮 I 未弄脏的 AC-1/AC-3/AC-4/AC-5/AC-6/AC-7 证据（含 auto-heavy 三形态与下拉 html/serve、AC-7 计时）；`5679e2e` 为 `98a11cc` 祖先
- 范围校验：触发影响集 I = {AC-2 linked-worktree html/serve、默认聚合同仓去重、backlog 纯文本、README↔helper} ⊆ 重跑 R；来源证据 E = (R ∩ E) ⊎ 沿用 U（U 为 AC-1/3/4/5/6/7 与未受影响聚合/缓存用例）；未升级完整复验理由：I 可圈定、无 auto-heavy 弄脏、共享路径变更仅为 `explicit_dir` 可选参数默认 None
- 核销：无（本轮无 FAIL 台账项；Review P1-1..3 已由 implement 标 verified，本轮复测通过）
- reopen：无
- 新增：无
- 本轮结论：通过（失败 0 项）

## 速报

结论：通过（失败 0 项）［第 2 轮 · revision 1 · 基线 `98a11cc`］
验证方式：定向复验
触发来源：Review 第 2 轮 @ `98de445`
来源 Test：第 1 轮 @ `5679e2e`；当前交付基线：`98a11cc`
测试资产提交：`98a11cc`
重跑范围：AC-2 linked-worktree html/serve + 默认同仓去重 + backlog esc + README↔helper + 相关依赖冒烟；沿用范围：第 1 轮 AC-1/3/4/5/6/7（含 auto-heavy）
范围校验：I ⊆ R；来源证据 E = (R ∩ E) ⊎ 沿用 U；`5679e2e` 为 `98a11cc` 祖先
下一步：status=reviewed，但最新 Review 基线为 `98de445`、未覆盖本轮测试资产 `98a11cc` → 回原 reviewer 增量审查覆盖新 H 后可 `/eo-archive`
