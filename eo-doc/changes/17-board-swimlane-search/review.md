---
title: 泳道页定位搜索与列显隐代码审查报告
change_id: board-swimlane-search
tags: [eo-board, swimlane, search, review]
created: 2026-08-12
updated: 2026-08-12
status: active
summary: >
  第 2 轮已核销首轮 2 个 P1，当前无未决 P0/P1；Review 覆盖基线刷新到 a62ef3c，测试证据需定向复验。
---

# 泳道页定位搜索与列显隐 代码审查报告

> 关联 Change：[change.md](change.md)（检查表：其 §2 验收清单）
> 首轮审查日期：2026-08-12 ｜ 审查范围：`cli/eo-board`、`tests/test_board_swimlane_search.py`（`4fd2a2a..69380cb`）
> ⚠️ 首轮之后正文各节为历史快照——当前状态以「Finding 台账」与末尾「速报」为准

## Finding 台账

<!-- 状态单一来源；轮次编号全文件单调递增（跨 revision 不清零）。写入权（writer matrix）：
     eo-review 建条与核销（open→verified；verified 后再打回 = reopen 回 open）；
     fixed + 修复 commit 按根因回写：implementation → eo-implement，test-asset → eo-test，requirement → eo-change 的实际修改者；
     waived = 用户显式裁决不修（当场获得裁决的 skill 写入，附原话要点；不阻塞 reviewed/归档）；
     eo-change 回炉时追加作废行并把仍 open/fixed 的行批量标 superseded。历史轮次节谁都不改。
     根因枚举：implementation / test-asset / requirement（打回实为需求问题 → 建议回炉） -->

| ID | 级别 | 摘要 | 位置 | 状态 | 根因 | 首见/最近轮 | 基线/修复 commit |
|----|------|------|------|------|------|-------------|------------------|
| P1-1 | P1 | 阶段徽标分支引用未定义的 `rv_open_p2`，含未决 P0/P1 的项目会在扫描时崩溃 | `cli/eo-board:613` | verified | implementation | 1/2 | `69380cb` / `0e7d75e` |
| P1-2 | P1 | 热刷新用例以 unmount/mount 代替生产 polling→buildBoard 路径，无法防止接线回归 | `tests/test_board_swimlane_search.py:409` | verified | test-asset | 1/2 | `69380cb` / `a62ef3c` |

## 审查总结（首轮快照）

搜索、定位、折叠与 XSS 处理的主体实现与 AC 一致：document 级监听在 unmount 时解绑，Escape 按搜索面板、详情抽屉、定位态逐层消费；`buildBoard` 重建前清除定位 class，折叠偏好保持；快照显式传 `route_key`，serve 下钻从 data URL 解析同一路由键；搜索标题、分组和正文片段均经 `esc`/`markSnippet` 安全渲染，既有 `mdInline` 先转义并限制链接协议。AC-6 是 manual 项，本轮只确认实现结构，不因未勾判缺陷。

当前仍不达到流转标准：`16c9d89` 夹带了与本 change 无法映射的阶段徽标改动，并在活跃 review 门分支引用未定义变量；此外测试资产声称覆盖的 serve 热刷新场景没有执行生产轮询回调。故本轮有保留通过，保持 `status: implementing`。

## P0 - 必须修复（阻塞性问题）

无。

## P1 - 建议修复（重要但不阻塞）

### [P1-1] 阶段徽标分支引用未定义变量

- **类型**：逻辑错误 / 反向覆盖
- **位置**：`cli/eo-board:613`
- **描述**：`derive_stage_progress` 在 `rv_active` 分支读取 `rv_open_p2`，但 H 中既没有赋值也没有对应解析函数。只要某张 change 卡存在未决 P0/P1，`attach_card_progress → derive_stage_progress` 即抛 `NameError`，看板扫描失败。该 P2 徽标改动也无法映射本 change 的任一 AC/TODO。
- **影响**：正在修复审查 finding 的项目无法正常生成终端、HTML 或 serve 看板；本 change 自身写入未决 P1 后即可触发。
- **建议**：从本交付中裁剪这段无关改动，或在其所属变更中完整实现并测试 P2 台账解析/计数；不得只依赖工作区未提交代码补齐变量。

### [P1-2] serve 热刷新测试没有执行生产路径

- **类型**：测试资产保真度
- **位置**：`tests/test_board_swimlane_search.py:409`
- **描述**：`hotRefreshBuildBoard` 场景明确执行 `api.unmount()` 后重新 `mount()`；这会由 unmount 自身清空 `locatedKey` 和 DOM，未触发 `startPolling` 的 fetch 回调，也未验证该回调真实调用 `buildBoard`。另一个源码字符串断言只锁定 `buildBoard` 函数体开头存在 `clearLocate()`，即便轮询接线被删仍会恒绿。
- **影响**：AC-7/TODO-5 要求的 serve 3 秒热刷新清定位态没有真实回归保护，生产接线退化时测试报告仍可能通过。
- **建议**：驱动 fake timer/fetch 执行真实 polling 回调，或暴露最小刷新入口并从生产回调与测试共用；断言刷新后定位态清除、折叠态保留，并确保删除生产 `refreshLoop → buildBoard` 接线时用例变红。

## P2 - 可选优化（锦上添花）

无。

## 验收标准覆盖检查

| AC 编号 | 描述 | 状态 |
|---------|------|------|
| AC-1 | Cmd/Ctrl+K、`/` 唤起；Esc/点外关闭；输入态 `/` 豁免 | ✅ 通过：快捷键分流与 mounted/unmount 生命周期完整 |
| AC-2 | 关键词按泳道分组，标题/summary/全文命中并显示片段 | ✅ 通过：`searchCards` 全文匹配，`renderSearchResults` 按状态分组，片段带上下文 |
| AC-3 | `#seq` 精确命中、回车直达、缺号空态 | ✅ 通过 |
| AC-4 | 定位滚动、高亮/降透明，Esc/空白恢复 | ✅ 通过 |
| AC-5 | 空态与 backlog 标题/正文检索 | ✅ 通过 |
| AC-6 | 列内滚动、sticky 列头、`.prov` 折叠 | ⚠️ manual：实现结构覆盖，本轮不代替人工过目、不因未勾判缺陷 |
| AC-7 | 列折叠、按项目持久、刷新保持 | ⚠️ 部分通过：实现覆盖；serve 热刷新测试资产未走生产路径，见 P1-2 |
| AC-8 | 定位折叠列时自动展开并高亮 | ✅ 通过 |

## TODO 完成度检查

| TODO | 描述 | 状态 |
|------|------|------|
| TODO-1 | 列内滚动、sticky 列头、`.prov` 折叠入口 | ✅ 完成（视觉手感留 AC-6 manual） |
| TODO-2 | 列折叠与按项目持久 | ✅ 完成 |
| TODO-3 | 搜索面板与键盘交互、监听生命周期 | ✅ 完成 |
| TODO-4 | 全文/编号匹配、分组与片段 | ✅ 完成 |
| TODO-5 | 定位、清除、折叠列展开、热刷新清定位 | ⚠️ 实现完成，生产热刷新接线的测试保真度未闭合（P1-2） |

## 第 1 轮记录（revision 1 · 2026-08-12）

- 审查基线：`revision 1, 69380cb14eb0a37e75f02d2e3eca133d605f6989`
- 核销：无
- reopen：无
- 新增：[P1-1] 阶段徽标分支引用未定义变量 — `cli/eo-board:613`；[P1-2] 热刷新用例未执行生产路径 — `tests/test_board_swimlane_search.py:409`
- 测试证据处置：复验
- 既有通过 Test：第 1 轮 @ `69380cb14eb0a37e75f02d2e3eca133d605f6989`；当前交付基线：`69380cb14eb0a37e75f02d2e3eca133d605f6989`
- 受影响 AC / 测试：AC-7、TODO-5 的 serve 热刷新定位态清除；review 阶段徽标/看板扫描回归
- 依据：纯 H 的活跃 review 门路径会因 `rv_open_p2` 未定义而失败，且热刷新场景用 unmount/mount 绕过生产 polling 接线；现有“完整通过”证据不能覆盖这两个实质问题。
- 本轮结论：有保留通过（P1 2 条）

## 第 2 轮记录（revision 1 · 2026-08-12）

- 审查基线：`revision 1, a62ef3cd2c84cec9b1dc555b2da3e8620d732733`
- 核销：P1-1 verified（修复 commit `0e7d75e`：移除未定义 `rv_open_p2` 引用，P0/P1 阶段徽标分支保持）；P1-2 verified（修复 commit `a62ef3c`：fake timer/fetch 驱动真实 `startPolling → refreshLoop → buildBoard`，定位、折叠及接线断言有效）
- reopen：无
- 新增：无
- 测试证据处置：复验
- 既有通过 Test：第 1 轮 @ `69380cb14eb0a37e75f02d2e3eca133d605f6989`；当前交付基线：`a62ef3cd2c84cec9b1dc555b2da3e8620d732733`
- 受影响 AC / 测试：AC-7、TODO-5 的 serve 热刷新定位态清除（`tests.test_board_swimlane_search`）；review 未决 P0/P1 阶段徽标与看板扫描回归（`tests.test_board_card_progress`）
- 依据：`T..H` 修改了阶段徽标业务路径，并重写热刷新测试 harness/断言；静态复审确认修复有效，但既有 Test 未在新 H 执行，按证据新鲜度规则需 tester 定向复验。
- 本轮结论：通过（未决 P0 0 条，P1 0 条）

## 速报

结论：通过［第 2 轮 · revision 1 · 基线 `a62ef3c`］
测试证据处置：复验
既有通过 Test：第 1 轮 @ `69380cb14eb0a37e75f02d2e3eca133d605f6989`；当前交付基线：`a62ef3cd2c84cec9b1dc555b2da3e8620d732733`；受影响 AC / 测试：AC-7、TODO-5 的 serve 热刷新定位态清除（`tests.test_board_swimlane_search`）及 review 未决 P0/P1 阶段徽标/看板扫描回归（`tests.test_board_card_progress`）；依据：`T..H` 触及业务扫描路径和测试 harness，须在新 H 定向复验。
下一步：回 `/eo-test` 在 H=`a62ef3c` 定向复验上述范围；证据闭合后可进入人工 AC-6/归档路径。
