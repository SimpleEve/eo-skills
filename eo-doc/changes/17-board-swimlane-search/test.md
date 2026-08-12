---
title: 泳道页定位搜索与列显隐 测试报告
change_id: board-swimlane-search
tags: [eo-board, swimlane, search, collapse, test]
created: 2026-08-12
updated: 2026-08-12
status: active
summary: >
  第 2 轮定向复验通过（Review 第 2 轮 @ a62ef3c）：serve 热刷新定位清除与
  阶段徽标/看板扫描回归全绿；AC-6 manual 未勾；交付基线 a62ef3c。
---

# 泳道页定位搜索与列显隐 测试报告

> 关联 Change：[change.md](change.md)（验收锚点：其 §2 验收清单）
> 首轮测试日期：2026-08-12 ｜ 测试环境：Python 3.12 / macOS Darwin / node（泳道 DOM 垫片）
> ⚠️ 首轮之后正文各节为历史快照——当前状态以「FAIL 台账」与末尾「速报」为准

## FAIL 台账

| ID | 级别 | 摘要 | 位置 | 状态 | 根因 | 首见/最近轮 | 基线/修复 commit |
|----|------|------|------|------|------|-------------|------------------|
| （无） | — | — | — | — | — | — | — |

## 测试总结（首轮快照）

| 指标           | 数值 |
| -------------- | ---- |
| 单元测试总数   | 9    |
| 单元测试通过   | 9    |
| 单元测试失败   | 0    |
| 集成测试总数   | 0    |
| 集成测试通过   | 0    |
| 集成测试失败   | 0    |

说明：主资产 `tests/test_board_swimlane_search.py`（9）；连带回归 `tests.test_board_card_progress` + `BoardGlobalDashboardTests` + `BoardAllSnapshotRouteTests` 共 52 绿（含既有 mount 不被搜索 markup 破坏）。

## 单元测试详情

### ✅ 通过的测试

| 测试文件 | 测试用例 | 对应 AC / TODO |
| -------- | -------- | -------------- |
| `tests/test_board_swimlane_search.py` | `test_search_open_close_and_slash_exempt_when_typing` | AC-1 / TODO-3（Cmd/Ctrl+K、`/`、Esc、点外、输入框豁免、unmount 解绑） |
| `tests/test_board_swimlane_search.py` | `test_seq_search_enter_locate_and_missing_empty` | AC-3 / TODO-4（`#21` 命中、Enter 定位、`#999` 空态） |
| `tests/test_board_swimlane_search.py` | `test_locate_dims_via_board_locating_and_blank_click_clears` | AC-4 / TODO-5（`locating`+`located`、空白点击清除） |
| `tests/test_board_swimlane_search.py` | `test_collapse_persists_in_local_storage_across_remount` | AC-7 / TODO-2（按 `projectKey` 记忆、跨项目隔离） |
| `tests/test_board_swimlane_search.py` | `test_locate_into_collapsed_column_auto_expands` | AC-8 / TODO-5（折叠 backlog 后定位自动展开） |
| `tests/test_board_swimlane_search.py` | `test_hot_refresh_clears_locate_state_but_keeps_collapse` | AC-7 + TODO-5 完成判据（热刷新后定位清除、折叠保持） |
| `tests/test_board_swimlane_search.py` | `test_keyword_and_backlog_body_match_via_search_cards` | AC-2/AC-5 补强（正文 token / backlog body） |
| `tests/test_board_swimlane_search.py` | `test_project_js_exposes_search_and_collapse_surface` | 表面锁：search/collapse/unmount/clearLocate 入口 |
| `tests/test_board_swimlane_search.py` | `test_snapshot_mount_passes_project_key_for_collapse_memory` | AC-7 快照侧 `projectKey: row.route_key` |

### ❌ 失败的测试

无。

## 一次性执行证据

| 验证点（AC / 输入） | 命令 | 关键输出 | 结论 |
| ------------------- | ---- | -------- | ---- |
| 待 test AC 套件终验 | `python3 -m unittest tests.test_board_swimlane_search` @ `69380cb` | Ran 9 tests · OK | ✅ |
| 连带回归 | `… board_card_progress + BoardGlobalDashboardTests + BoardAllSnapshotRouteTests` | Ran 52 tests · OK | ✅ |

## 集成 / 场景验证详情

本 change 逻辑集中在共享 `PROJECT_JS` 客户端；重验证以 node 垫片上的 `EO_PROJECT.mount` 真实入口 + keydown/click 派发完成（等价点击流，不启浏览器）。AC-6 为 **manual**，本 skill 不勾不验。

### 场景 1：键盘唤起 / 关闭 / 解绑（AC-1）
- **操作** ｜ Cmd+K / Ctrl+K / `/` 打开，Esc 与点 backdrop 关闭，输入框聚焦时 `/` 不误关，unmount 后 document 监听计数归零 ｜ **实际**：✅

### 场景 2：#seq 与空态（AC-3）
- **操作** ｜ `searchCards('#21')` 命中 `ch:alpha`；`#999` 空；面板输入 `#21` 回车定位 ｜ **实际**：✅

### 场景 3：定位与恢复（AC-4）
- **操作** ｜ Enter 后 board 带 `locating`、目标 `located` + scrollIntoView；Esc/点空白清除 ｜ **实际**：✅（他卡降透明度由 CSS `.board.locating .card` 实现，断言定位态 class）

### 场景 4：折叠记忆与热刷新（AC-7 / 定位清除）
- **操作** ｜ 折叠后 remount 同 `projectKey` 恢复；热刷新序列定位清除且折叠保持 ｜ **实际**：✅

### 场景 5：折叠列内定位（AC-8）
- **操作** ｜ 折叠 backlog → 搜 `BACKLOG_BODY_TOKEN` → Enter → 列展开且卡 located ｜ **实际**：✅

## 未覆盖的测试场景

- AC-6 列内滚动/列头吸顶/`.prov` 折叠入口手感 — **manual**，归用户过目。
- 真浏览器视觉脉冲动画帧 — 由 CSS `locate-pulse` 与 class 契约覆盖，未截帧。

## 遗留问题

无阻塞项。下一步 `/eo-review`（status 仍为 `implementing`，且 Review 需覆盖含测试资产的新 H）。

## 第 1 轮记录（revision 1 · 2026-08-12）

- 测试基线：`69380cb14eb0a37e75f02d2e3eca133d605f6989`
- 验证方式：首轮完整
- 触发来源：首轮
- 来源 Test：无；当前交付基线：`69380cb14eb0a37e75f02d2e3eca133d605f6989`
- 测试资产提交：`69380cb`（`[board-swimlane-search] 测试：定位搜索、折叠记忆与热刷新清除` → `tests/test_board_swimlane_search.py`）
- 重跑范围：AC-1、AC-3、AC-4、AC-7、AC-8 及 §4 交接清单点（含热刷新定位清除）；AC-2/AC-5 补强；既有 board mount 回归
- 沿用范围：无
- 范围校验：首轮完整（全部证据均在重跑范围）；AC-6 manual 明确不在本轮勾选范围
- 核销：无
- reopen：无
- 新增：无
- 本轮结论：通过（失败 0 项）

## 第 2 轮记录（revision 1 · 2026-08-12）

- 测试基线：`a62ef3cd2c84cec9b1dc555b2da3e8620d732733`
- 验证方式：定向复验
- 触发来源：Review 第 2 轮 @ `a62ef3c`
- 来源 Test：第 1 轮 @ `69380cb`；当前交付基线：`a62ef3cd2c84cec9b1dc555b2da3e8620d732733`
- 测试资产提交：无（本轮未新增/修改测试文件；热刷新 harness 已在 `a62ef3c` 入基线）
- 重跑范围：
  - AC-7 / TODO-5 serve 热刷新定位态清除：`tests.test_board_swimlane_search`（含 `test_hot_refresh_clears_locate_state_but_keeps_collapse` 及同文件 9 例）
  - review 未决 P0/P1 阶段徽标与看板扫描回归：`tests.test_board_card_progress`（StageProgress / gates DOM / attach 路径共 26 例）；另对 `a62ef3c:cli/eo-board` 直载 `derive_stage_progress(open P0+P1)` 冒烟（无 `rv_open_p2` NameError）
- 沿用范围：第 1 轮已通过且本轮 I 未弄脏的 AC-1/AC-2/AC-3/AC-4/AC-5/AC-8 证据；AC-6 仍为 manual；`69380cb` 为 `a62ef3c` 祖先
- 范围校验：触发影响集 I = {AC-7/TODO-5 热刷新定位清除, P1-1 阶段徽标/扫描路径} ⊆ 重跑 R；来源证据 E = (R ∩ E) ⊎ 沿用 U；未升级完整复验理由：I 可圈定、无 auto-heavy 弄脏（热刷新已在测试内用 fake timer/fetch 覆盖生产 polling 回调）
- 核销：无（FAIL 台账空；Review P1-1/P1-2 已 verified，本轮复测通过）
- reopen：无
- 新增：无
- 本轮结论：通过（失败 0 项）

## 速报

结论：通过（失败 0 项）［第 2 轮 · revision 1 · 基线 `a62ef3c`］
验证方式：定向复验
触发来源：Review 第 2 轮 @ `a62ef3c`
来源 Test：第 1 轮 @ `69380cb`；当前交付基线：`a62ef3c`
测试资产提交：无
重跑范围：`tests.test_board_swimlane_search`（AC-7 热刷新）+ `tests.test_board_card_progress`（阶段徽标/扫描）；沿用范围：第 1 轮 AC-1/2/3/4/5/8（AC-6 manual）
范围校验：I ⊆ R；E = (R ∩ E) ⊎ U；`69380cb` 为 `a62ef3c` 祖先
下一步：status=reviewed 且 Review 已覆盖 B=`a62ef3c`；待人工 AC-6 后可 `/eo-archive`
