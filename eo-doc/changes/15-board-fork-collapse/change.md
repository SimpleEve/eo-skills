---
id: board-fork-collapse
seq: 15
title: 看板分叉副本折叠为单卡
summary: 同 change 多 worktree 副本只出最新一卡，分叉副本收进徽标可下钻
status: implementing
tier: light
type: enhance
base_commit: a1766935ebd564b368978c87a35737bf209d2ede
test_lock_commit: 8197f9b3ea180a3ba8d59017439d72d501f94a0b
commits: []
issue: ~
created: 2026-08-12
---

# 看板分叉副本折叠为单卡

意图：change 14 引入的「实质分叉各出一卡」在多 worktree 日常使用中噪音过大——同一 change 遍地重复卡。改为同 id 只出「最近活动」最新的一张卡，分叉信号不丢：卡面带「分叉×N」徽标，详情内可查看/切换各副本。

已钉决策（2026-08-12 对话确认）：

- **直接替换** change 14 的多卡展示（破坏性变更已按协议问清，用户选定「单卡 + 分叉徽标」，不留多卡兼容模式）；change 14 的 AC-1/3/4 锁定测试语义随本 change 失效，实施时同步改写为新口径
- 「最新」尺子与 change 流排序同源（git 推导末次触碰 + 目录 mtime 取 max，即 activity_at 同一把尺），不新造第二套时间口径；平手回退：状态 rank 高者 → 路径字典序（确定性）
- 基准过滤（状态低于主 worktree 的过期副本）先于折叠执行，过期副本既不出卡也不计入徽标 N
- 改的是展示层 `scan_all_changes_split`（仅 eo-board 消费）；eo-sync 的 `resolve_change` 写回消歧（分叉 fail-closed）不动

## 2. 验收清单

- [x] AC-1 同一 change 在多个 worktree 存在副本时（含内容分叉），泳道卡面与聚合 change 流各只出现一张卡，且为最近活动最新的那份；内容一致副本场景与现状一致（单卡、无徽标）（锁定：tests/test_eo_board_cache.py#BoardForkCollapseTests.test_diverged_copies_collapse_to_latest_single_card + test_latest_wins_regardless_of_worktree + test_identical_copies_merge_to_one_card（characterization））
- [x] AC-2 分叉场景下该卡带「分叉×N」徽标（N = 其余内容变体数），卡详情内列出各副本归属（branch@worktree、状态、最近活动）并可切换查看任一副本的详情内容（人工：构造双 worktree 分叉 → 过目徽标计数与副本切换；数据层基质锚定：BoardForkCollapseTests.test_shown_card_and_forks_carry_attribution_data + test_single_card_key_and_fork_switch_in_detail）（确认：card-platform 真实快照过目徽标与副本切换，原话"已过目，可以"，2026-08-12，基线 ff8482f）
- [x] AC-3 基准过滤不回归：主 worktree 状态更高时，状态更低的过期副本不出卡、不计入徽标 N；基准没有该 change 时不过滤（锁定：BoardForkCollapseTests.test_ac6_stale_lower_status_filtered + test_base_lower_keeps_higher_via_collapse + test_ac6_base_missing_change_no_filter）
- [x] AC-4 终端 / --html / --serve / --all 四处折叠口径一致；--serve 挂起时修改某 worktree 的 change.md，一个轮询周期内「最新卡」归属正确刷新（锁定：BoardForkCollapseTests.test_serve_refreshes_latest_attribution_after_divergence + 既有缓存/基线等价用例 characterization）

独立复核：通过，2026-08-12，基线 ff8482f（本地只读 reviewer subagent；P2 注释辩护两条已修 @4285dea，P3 锁定缺口两条——终端/聚合流徽标直接断言、fork 点击绑定触发——按回归资产分层接受不补）
