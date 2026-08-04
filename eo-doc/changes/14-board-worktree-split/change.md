---
id: board-worktree-split
seq: 14
title: 看板按 worktree 拆分并行 change 卡
summary: 多 worktree 并行同一 change 且实质分叉时，board 各出一卡；内容一致副本仍合并
status: implementing
tier: light
type: enhance
base_commit: f496ca5
test_lock_commit: 3d121ed
commits: []
issue: ~
created: 2026-08-04
---

# 看板按 worktree 拆分并行 change 卡

意图：多个 worktree 并行推进同一个 change 时，board 上只展示一张卡（`pick_change_winner` 取状态最高者，其余候选丢弃），看不到各 worktree 各自的真实进度。改为：同 id 候选按 change.md 内容 hash 分组，**实质分叉（>1 组）才各出一卡**，内容一致的副本仍合并为一卡——从 main 切出的 worktree 天然携带已合并 change 的只读副本，不能无脑按 worktree 拆出重复卡。范围只覆盖 eo-board（终端 / --html / --serve / 聚合页 change 流同一数据源），Obsidian sync 链路（stub 一卡一 id）不动。顺带：卡面 worktree/branch 标记目前连成一行（`⎇branch@worktree`）太长，改为分行显示。

补充场景：worktree 单向合入 main 后不回拉，遗留 worktree 携带过期 change.md（如 main 已 archived、遗留仍 implementing）会被当作"实质分叉"出多余卡。引入基准 worktree 过滤：以 main worktree（`worktrees[0]`）为基准，状态严格低于基准的候选视为被超越的过期版本，过滤掉不出卡；状态 >= 基准的才进分组（含同状态不同内容的有意义分叉）。

已钉决策：
- 拆分范围 → 只拆 eo-board 呈现层；eo-sync 的 `resolve_change` / stub / 簿记语义零改动（用户确认）
- 拆分条件 → 实质分叉才拆：同 id 各候选按 change.md 内容 sha256 分组（status 不同天然导致 hash 不同，一并覆盖）；一致副本合并取状态最高代表，维持现状（用户确认）
- 判定落点 → `cli/eo_lib/changes.py` 新增分组函数（与 `resolve_change` 的 hash 比较先例同源），`pick_change_winner` / `scan_all_changes` 原语义保留
- 无分叉零扰动 → 拆分标记（如 `diverged` 字段）仅在真分叉时进数据；无分叉场景看板输出与现状一致，serve 缓存基线不破
- 可辨识 → 拆出的每张卡（含主 worktree 那张）都显示 worktree/branch 标记，不再只标非主 worktree
- 标记分行 → 卡片类展示（泳道卡面、聚合流行、卡详情概览）的 branch 与 worktree 各占一行，不再连成一行（用户追加）；终端表格列是行结构不是卡，维持现状

## 2. 验收清单

- [x] AC-1 同一 change 在两个 worktree 内容实质分叉（如各自勾选不同 TODO、或 status 不同）时，board 上该 change 显示为多张卡，各卡展示自己的状态与 AC/TODO 进度（验证：构造双 worktree fixture 分别改 change.md，跑 eo-board 看两张卡）（锁定：tests/test_eo_board_cache.py#BoardWorktreeSplitTests.test_ac1_diverged_change_shows_multiple_cards）
- [x] AC-2 多个 worktree 中 change.md 内容完全一致的副本只出一张卡，不出现重复卡（验证：worktree 原样携带 change 目录副本时，看板卡数与拆分前一致）（锁定：tests/test_eo_board_cache.py#BoardWorktreeSplitTests.test_ac2_identical_copies_merge_to_one_card）
- [ ] AC-3 卡片类展示（泳道卡面 / 聚合流行 / 卡详情概览）中 branch 与 worktree 分行显示，不再连成一行；拆分场景下包括主 worktree 在内的每张卡都带归属标记，一眼可辨（人工:构造分叉场景 → 过目卡面标记分行 + 各卡归属标记）（锁定：tests/test_eo_board_cache.py#BoardWorktreeSplitTests.test_ac3_diverged_main_worktree_card_carries_marker_data 覆盖数据层；卡面分行人工验收）
- [x] AC-4 终端 / --html / --serve / --all 聚合流四处拆分行为一致；每张卡可独立打开详情，详情内容对应该 worktree 那份 change.md（验证：--html 快照点开两张分叉卡，全文 tab 各显各的内容）（锁定：tests/test_eo_board_cache.py#BoardWorktreeSplitTests.test_ac4_diverged_cards_have_unique_keys_and_distinct_detail）
- [x] AC-5 回归：无分叉场景看板输出与拆分前一致；--serve 挂起时任一 worktree 修改 change.md，3 秒内拆分状态正确刷新不陈旧（验证：既有缓存基线测试不破 + 改动另一 worktree 的 change.md 看页面变化）（锁定：tests/test_eo_board_cache.py#BoardWorktreeSplitTests.test_ac5_serve_refreshes_divergence_within_three_seconds）
- [x] AC-6 基准 worktree（默认 main）上某 change 状态高于其他 worktree（如 main=archived、遗留=implementing）时，状态更低的过期版本被过滤不出卡；基准状态更低时不误杀（其他保留）；基准没有该 change 时不过滤（验证：构造 main=archived + stale=implementing 双 worktree fixture，跑 board 看只出一张 archived 卡）（锁定：tests/test_eo_board_cache.py#BoardWorktreeSplitTests.test_ac6_stale_lower_status_filtered + test_ac6_base_lower_does_not_filter_higher + test_ac6_base_missing_change_no_filter）

## 独立复核

独立复核：未执行（subagent 不可用——无 anthropic API key），2026-08-04，基线 d979e56

subagent 起不了，以下为执行者自述（不作数，需用户验证或补跑）：

- AC 覆盖：AC-1~AC-5 均有实现 + 锁定测试覆盖；AC-3 卡面分行为人工项
- 测试完整性：实现 commit d979e56 不含测试文件改动（git show 确认），test_lock_commit 7766ec2 锁定后未篡改
- 过拟合/硬编码：group_changes_by_divergence 用通用 sha256 分组，无 fixture 特判
- 镀金：diff 仅含 change 要求的分组函数 + 四处卡面分行 + _key 唯一化 + CSS，无多余实现
- 注释纪律：新增注释为功能性 docstring（含 resolve_change 同源指针），无溯源 token / 叙事辩护
