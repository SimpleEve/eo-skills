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

### [D-3] 容器宽度与字号档偏离定稿 variant-2.html

- **相关 TODO**：TODO-2、TODO-3、TODO-5（AC-9）
- **原计划**：AC-9 以 `design/variant-2.html` 为对照定稿；定稿 `.wrap` 为 `max-width: 1180px`，字号档为当前实现的原值。
- **实际做法**：聚合首页与单项目泳道页两套模板的 `.wrap` 均去掉宽度上限（保留左右 24px 内边距与 479px 以下的既有窄屏档），全部 106 处 `font-size` 声明每档 +0.5px（含失效路由指引页；favicon 内嵌 SVG 的 `font-size='90'` 是图标字形尺寸，不在此列）。
- **原因**：AC-9 人工验收（基线 5c19342）用户过目后要求「页面内容可以放到全宽，主要是下钻的视图，否则泳道展示不开」「整体的所有字号可以统一放大 0.5」。泳道页六列固定 268px + 14px 间距共约 1678px，在 1520px 上限下必然横滚，全宽是主诉求；两页一致处理避免首页/下钻页宽度语义分裂。
- **影响**：无行为语义变化，236 条单测未受影响；定稿 variant-2.html 未回改，AC-9 的定稿对照口径已就地收窄为「结构、字段与密度分界」，宽度与字号以验收反馈为准。「放大 0.5」按「每档 font-size +0.5px」落地——用户原话未给单位，此为实施假设。
