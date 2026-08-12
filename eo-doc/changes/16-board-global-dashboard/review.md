---
title: board 收敛为全局 dashboard 代码审查报告
change_id: board-global-dashboard
tags: [eo-board, dashboard, review]
created: 2026-08-12
updated: 2026-08-12
status: active
summary: >
  第 4 轮核销 P1-4：917ef5f 的真实 CLI 子进程用例已覆盖 linked-worktree serve 入口、首开 URL 与数据路由；台账清零，Review 覆盖当前 H。
---

# board 收敛为全局 dashboard 代码审查报告

> 关联 Change：[change.md](change.md)（检查表：其 §2 验收清单）
> 首轮审查日期：2026-08-12 ｜ 审查范围：`4c89b569..5679e2e`（`8e2e5c1`、`b880f4e` 业务实现 + `5679e2e` 测试资产；排除其后的纯工件提交 `1a508da` 与当前工作区无关脏改）
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
| P1-1 | P1 | `--project` 指向同仓 linked worktree 时 html/serve 不能直达该路径 | `cli/eo-board:2514`; `cli/eo-board:3227`; `cli/eo-board:3354` | verified | implementation | 1/2 | `5679e2e` / `98de445` |
| P1-2 | P1 | Batch 2 夹带未映射到 AC/TODO 的 backlog 摘要 Markdown 行为变化 | `cli/eo-board:2022` | verified | implementation | 1/2 | `5679e2e` / `98de445` |
| P1-3 | P1 | README 仍按旧七项菜单编号指引同步与 watch | `README.md:189` | verified | implementation | 1/2 | `5679e2e` / `98de445` |
| P1-4 | P1 | linked-worktree serve 回归用例绕过真实 CLI 入口与首开 URL 接线 | `tests/test_eo_board_cache.py:2094` | verified | test-asset | 3/4 | `98a11cc` / `917ef5f` |

## 审查总结（首轮快照）

默认三形态聚合化、`--all` 退役、cwd 临时并入、空态、项目下拉和 10 项目性能门主体实现清晰，复用了既有聚合路由与缓存边界，未发现 P0、安全问题或明显性能退化。但显式 `--project` 的 html/serve 新路径把目标项目重新交给按 repo identity 去重的聚合集合：当注册表已有同仓另一 worktree 时，用户指定的 worktree 会被排除，初始路由却仍按被排除路径生成，违反 AC-2 的「按路径直达且行为不变」。此外，交付夹带了 backlog 摘要 Markdown 渲染这一范围外行为，并遗漏了 helper 菜单缩编后的 README 编号更新。当前有 3 条未决 P1，`status` 保持 `implementing`，不能流转为 `reviewed`。

## P0 - 必须修复（阻塞性问题）

无。

## P1 - 建议修复（重要但不阻塞）

### [P1-1] `--project` 的 linked-worktree 路径在 html/serve 下失去直达语义

- **类型**：潜在 Bug / 验收覆盖缺失
- **位置**：`cli/eo-board:2514`、`cli/eo-board:3227`、`cli/eo-board:3354`
- **描述**：`cmd_project_html` 与 `cmd_all_serve(..., cfg=cfg)` 通过 `cwd_dir=cfg["repo_root"]` 把显式目标重新并入全局来源；但 `collect_sources` 先把注册条目的 `repo_identity` 放入 `known`，同仓主/linked worktree 会归一为同一 identity。若注册表保存主 worktree，而用户传入同仓 linked worktree 路径，目标 worktree 不会进入 rows/routes；随后 html 的 `initial_route` 与 serve 首开 URL 又按 linked worktree 路径生成不同 route key，分别落到快照未命中页与 HTTP 404。旧实现直接用显式目标 `cfg` 渲染，不存在该回归。
- **影响**：AC-2 对「`--project <名|路径>` 行为与现状一致、三形态直达」的承诺仅部分达成；终端和注册名路径可用，但合法的同仓 worktree 路径在 html/serve 下失败。
- **建议**：让显式 `--project` 目标始终进入并优先成为下钻来源，即使注册表已有相同 repo identity；同时保持普通 dashboard/`--scan` 的同仓去重口径。补齐 linked-worktree 路径在 html 初始路由和 serve 首开/数据路由上的回归资产。

### [P1-2] 实施范围外改变了 backlog 卡片摘要渲染

- **类型**：范围外行为新增（镀金）
- **位置**：`cli/eo-board:2022`
- **描述**：`b880f4e` 把 backlog 卡片正文摘要从 `esc(...)` 改为 `mdInline(...)`，使反引号、粗体和链接开始按 Markdown 呈现。该改动不服务默认 dashboard、项目下拉或七条 AC，也映射不到任一 TODO；虽然 `mdInline` 先转义且限制链接协议，未发现直接安全缺陷，但它仍是独立的用户可见行为变化。
- **建议**：从本 change 交付中裁剪并恢复纯文本摘要；若确有需求，另走 backlog/change 明确验收口径与回归资产。

### [P1-3] helper 菜单缩编后 README FAQ 的编号已错误

- **类型**：文档正确性
- **位置**：`README.md:189`
- **描述**：本 change 把 helper 从 7 项缩为 5 项后，「看板自动跟手」是菜单 4，「同步看板卡片」是菜单 3；README 仍指引菜单 5/4。用户按现文操作会分别进入全局终端速览与 watch，而不是文案声称的 watch 与单次同步，TODO-6 的命令面同步未完整达成。
- **建议**：把 FAQ 编号更新为 4/3，并用菜单映射的单一事实或静态断言守住 README 中的数字引用。

## P2 - 可选优化（锦上添花）

无。

## 验收标准覆盖检查

| AC 编号 | 描述 | 状态 |
|---------|------|------|
| AC-1 | 无旗标终端/html/serve 默认全局 dashboard，`--all` 退役 | ✅ 通过：`main` 无 `--project` 时统一走聚合分支，三形态与退役提示均有当前 H 证据 |
| AC-2 | `--project <名\|路径>` 三形态直达，五 tab 不受影响 | ⚠️ 部分通过：普通注册名/路径与五 tab 成立；同仓 linked-worktree 路径的 html/serve 失效，见 P1-1 |
| AC-3 | 泳道项目下拉列出全部可下钻项，html/serve 均可跳转 | ✅ 通过：静态快照注入 hash href，serve 注入 `/p/<key>`，change 事件按 option value 跳转；含 `--scan` 项资产 |
| AC-4 | 已注册项目目录无旗标运行仍显示全局首页 | ✅ 通过：默认入口不再按 cwd 选择单项目，已注册 cwd 经 identity 去重后保留全局首页 |
| AC-5 | 未注册且含配置的 cwd 临时并入、不持久化 | ✅ 通过：`collect_sources` 只追加本次 scanned 来源，不写注册表，测试校验前后注册表字节一致 |
| AC-6 | 空注册表且 cwd 无项目显示注册指引 | ✅ 通过：终端与 HTML/serve 空态均给出 `--register` 指引，无堆栈/空白页 |
| AC-7 | 10 项目 html 快照 ≤5 秒 | ✅ 通过：当前 H 一次性证据为 0.342s，低于 5s 硬门 |

## TODO 完成度检查

| TODO | 描述 | 状态 |
|------|------|------|
| TODO-1 | 默认入口切换、`--all` 退役、保留 `--project` 三形态 | ⚠️ 部分完成：默认与退役成立；显式 linked-worktree 路径的 html/serve 回归，见 P1-1 |
| TODO-2 | cwd 项目自动临时并入 | ✅ 完成 |
| TODO-3 | 终端与 HTML 空态兜底 | ✅ 完成 |
| TODO-4 | 项目下拉数据、html/serve 跳转 | ✅ 完成 |
| TODO-5 | 10 项目快照性能硬门 | ✅ 完成 |
| TODO-6 | help、helper 与用户文档同步新命令面 | ⚠️ 部分完成：CLI/helper 主体已同步，README 菜单编号仍旧，见 P1-3 |

## 代码质量与测试资产审计

- **逻辑正确性**：主体分支和异常隔离成立；显式目标与全局去重复用时丢失路径语义，见 P1-1。
- **架构合规**：沿用 `collect_sources → build_all_data → route_map` 现有边界，未新增反向依赖；但显式过滤器与聚合去重的语义不应无条件共用。
- **代码规范**：未发现随意 `any`、明显重复实现或会阻塞交付的命名问题；新增业务注释未发现流程溯源标注或叙事辩护。
- **安全与性能**：项目名/href 经 HTML 转义，route key 来自内部生成；服务仍仅绑定 127.0.0.1。未发现注入、越权或明显性能瓶颈，AC-7 当前证据通过。
- **设计一致性**：仓库根无 `DESIGN.md`，维度 6 未启用。
- **测试资产保真度**：当前资产覆盖普通注册项目的终端路径、按名 html 及聚合下钻，但没有覆盖「注册主 worktree + 显式指定同仓 linked-worktree 路径」的 html/serve 契约；该缺口已让 P1-1 穿过首轮完整测试。未发现恒绿、弱化断言或 flaky 模式。
- **反向覆盖**：除 P1-2 外，未发现其他无法映射到 AC/TODO 的行为新增。
- **Unknown 处置**：P1-1～P1-3 均属 A 类交付判断，随本报告记录；未出现需要在变更前触发 decision gate 的 B/C 类事项。

## 第 1 轮记录（revision 1 · 2026-08-12）

- 审查基线：`revision 1 @ 5679e2e58a4e831ea5802487964f29785e9dc823`
- 核销：无
- reopen：无
- 新增：[P1-1] linked-worktree 路径的 html/serve 不能直达 — `cli/eo-board:2514`；[P1-2] backlog 摘要 Markdown 为范围外行为新增 — `cli/eo-board:2022`；[P1-3] README helper 菜单编号错误 — `README.md:189`
- 测试证据处置：复验
- 既有通过 Test：第 1 轮 @ `5679e2e58a4e831ea5802487964f29785e9dc823`；当前交付基线：`5679e2e58a4e831ea5802487964f29785e9dc823`
- 受影响 AC / 测试：AC-2；`test_project_by_name_and_by_path_from_anywhere`、`test_project_html_opens_swimlane_via_initial_route_with_home_link`、`--project --serve` 首开/路由用例，以及 TODO-6 的 README↔helper 菜单映射静态校验
- 依据：Test 虽在当前 revision 的 H 上完整通过，但没有覆盖同仓 linked-worktree 的显式路径组合，静态审查已发现该组合上的实质 AC-2 回归，故不能以「覆盖 H」免除修复后的复验。
- 本轮结论：有保留通过（P1 3 条）；`status` 保持 `implementing`。

## 第 2 轮记录（revision 1 · 2026-08-12）

- 审查基线：`revision 1 @ 98de44534c02b1918f2607a459c3305e8d3c7555`
- 核销：P1-1 verified（修复 commit `98de445`：显式目标经 `explicit_dir` 进入 html initial route、serve route map、首页与 data.json；默认聚合不传该参数，原有 repo identity 去重口径未变）；P1-2 verified（修复 commit `98de445`：backlog 摘要恢复 `esc` 纯文本）；P1-3 verified（修复 commit `98de445`：README 菜单编号更新为 watch 4 / sync 3，与 `cli/eo-helper` 一致）
- reopen：无
- 新增：无
- 测试证据处置：复验
- 既有通过 Test：第 1 轮 @ `5679e2e58a4e831ea5802487964f29785e9dc823`；当前交付基线：`98de44534c02b1918f2607a459c3305e8d3c7555`
- 受影响 AC / 测试：AC-2；linked-worktree 路径的 `--project --html` initial route、`--project --serve` 首开与 `/p/<key>/data.json`，默认 `build_all_data` 同仓去重回归；backlog 摘要纯文本与 README↔helper 菜单映射静态断言
- 依据：`T=5679e2e` 是 `H=98de445` 的祖先且 Test 台账无阻塞项，但 `T..H` 改动了 AC-2 的 html/serve 外部路径，而既有 Test 明确未覆盖 linked-worktree 组合，H 上也没有新增测试资产或复验记录，故旧证据不可沿用。
- 本轮结论：通过（未决 P0 0 条，P1 0 条，P2 0 条）；`status` 由 `implementing` 流转为 `reviewed`。

## 第 3 轮记录（revision 1 · 2026-08-12）

- 审查基线：`revision 1 @ 98a11cc40ba7a8c7ee9274d2ab5eada065d43826`
- 核销：无（P1-1～P1-3 保持 verified）
- reopen：无
- 新增：[P1-4] linked-worktree serve 回归用例绕过真实 CLI 入口与首开 URL 接线 — `tests/test_eo_board_cache.py:2094`（根因：test-asset）
- 增量审计：`98a11cc` 仅新增 `tests/test_eo_board_cache.py`、`tests/test_eo_helper.py` 测试资产（112 行新增、无删除），无业务代码或其他交付物夹带。linked-worktree html 用例走真实 CLI 并核对 initial route/目标 row；默认聚合用例区分普通同仓去重与显式目标；backlog 用例同时锁定 `esc`/排除 `mdInline`；README 用例与 helper 完整菜单映射共同约束编号，这些断言均真实有效，未发现恒绿、弱化、过拟合特判或 flaky 模式。serve 用例存在下述保真缺口。
- [P1-4] **描述**：`test_project_serve_linked_worktree_route_and_data_are_reachable` 没有执行 `eo-board --project <linked> --serve`，而是在测试内直接构造已带 `cwd_dir`/`explicit_dir` 的 `AllBoardRequestHandler`；因此没有约束生产入口 `main → cmd_all_serve(args, cfg) → handler.explicit_dir`，也没有断言 `cmd_all_serve` 生成的首开 URL 是 linked route。删除 `cli/eo-board:3556` 的 `cfg=cfg`、`cli/eo-board:3394-3398` 的显式目标接线或 `cli/eo-board:3405-3406` 的首开路由时，该测试仍可保持通过，不能真实防住 P1-1 的 serve 原始回归点。**建议**：测试真实 CLI 接线（可对子进程启动 serve 后请求其启动 URL，或在不复制生产接线的前提下替换 server/Timer 并直接调用入口），同时断言首开 URL、`/p/<linked_key>`、`/p/<linked_key>/data.json` 与首页数据。
- 测试证据处置：不适用（Test 已覆盖 H）
- 本轮结论：有保留通过（未决 P0 0 条，P1 1 条，P2 0 条）；按控制包不改 `change.md`，其 `status` 暂保持 `reviewed`，但 P1-4 核销前不得归档。

## 第 4 轮记录（revision 1 · 2026-08-12）

- 审查基线：`revision 1 @ 917ef5f362ed53499eb68a784befb75954686bd5`
- 核销：P1-4 verified（修复 commit `917ef5f`：用例以子进程真实执行 `eo-board --project <linked> --serve`，从 CLI banner 断言首开 URL 为 `/p/<linked_key>`，再请求该项目页、`/p/<linked_key>/data.json` 与首页 `/data.json`；由此覆盖 `main → cmd_all_serve(args, cfg) → explicit_dir` 接线。若删除 `cli/eo-board:3556` 的 `cfg=cfg`，banner 将退化为聚合根 URL并使首开 URL 断言失败；若破坏 `explicit_dir` 注入，linked route/data/home 断言将失败）
- reopen：无
- 新增：无
- 增量审计：`917ef5f` 仅修改 `tests/test_eo_board_cache.py`，无业务代码或其他交付物夹带；用例不再手工构造 handler，未发现恒绿、弱化、过拟合特判或新增 flaky 模式。
- 测试证据处置：不适用（Test 已覆盖 H）
- 本轮结论：通过（未决 P0 0 条，P1 0 条，P2 0 条）；`status` 保持 `reviewed`。

## 速报

结论：通过［第 4 轮 · revision 1 · 基线 `917ef5f`］
测试证据处置：不适用（Test 已覆盖 H）
下一步：当前 revision/H 的 Test 与 Review 证据均已闭合，可进入 `/eo-archive board-global-dashboard`。
（详细分析见 `eo-doc/changes/16-board-global-dashboard/review.md`）
