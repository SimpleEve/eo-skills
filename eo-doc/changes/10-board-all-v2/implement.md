---
title: board-all-v2 实施偏差记录
change_id: board-all-v2
tags: [偏差]
created: 2026-07-27
updated: 2026-07-27
status: active
summary: >
  记录实施过程中偏离 change 方案的决策。
---

# board-all-v2 实施偏差记录

> 关联 change：[change.md](change.md)

## 偏差项

### [D-1] 抽取基线测试由「全等」放宽为「基线字段逐条保真」

- **相关 TODO**：TODO-1
- **原计划**：change 未提及既有测试的处置；`tests/test_eo_board_cache.py::test_extracted_board_matches_baseline_for_terminal_html_and_serve_data` 断言当前 `build_data` / `render_terminal` / `render_html` 与 revision `792522d` 三处**逐字节全等**。
- **实际做法**：改名为 `..._for_terminal_and_serve_data`，新增 `assert_preserves` 递归子集断言——基线的每个字段仍在且取值不变，新增字段放行；`render_terminal` 全等保留；`render_html` 的字节全等删除。
- **原因**：本 change 按 §5 给 `build_data` 增了 `changes[].activity_at` 与项目级 `activity_at`（排序键必须秒级且能看见未提交编辑），单项目模板也按 §5 注入了 data URL 与返回入口——三处全等与本 change 的既定方案直接冲突，不可能同时成立。放宽后守住的仍是原意图「抽取 eo_lib 未改变既有行为」，且终端渲染保持全等（AC-8 的「终端输出不变」另有 base_commit 基线测试兜底）。
- **影响**：无功能影响；`render_html` 的回归改由 AC-4/AC-5 的路由与自包含断言覆盖。

### [D-2] 视图层断言引入 node 作为测试期渲染器

- **相关 TODO**：TODO-2、TODO-3
- **原计划**：完成判据写「静态断言绿」，未指定断言落点。
- **实际做法**：测试把生成页面里的内嵌脚本套一层最小 DOM 垫片交给 `node` 执行，断言真实产出的 `#topbar` / `#content` innerHTML；`node` 缺失时该类用例 `skipUnless` 跳过。
- **原因**：页面全部由内嵌 JS 渲染，只对模板文本做 grep 无法证明字段、排序、降权分界真的落到页面上。
- **影响**：`cli/` 运行时依赖不变（宪法「零第三方依赖」由 `test_stays_on_stdlib_only_and_binds_loopback_only` 静态守护）；无 node 的机器上视图类断言会静默跳过，AC-1/2/3 的证据强度随之下降。
