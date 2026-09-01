# 多 worktree 协作规范

并行 change 各自开 worktree。看板与代码索引对多 worktree 的口径如下。

## 看板（eo-board）

- 同一 change id 多 worktree 并行：只出「最近活动」最新的一张卡
- 内容实质分叉的其余变体：收进卡面「分叉×N」徽标与详情副本列表，可切换查看
- 内容一致的副本：合并出卡，无标记
- 状态严格低于 main worktree 的过期版本：过滤，不出卡也不计入 N
- 卡面 branch 与 worktree 分行显示（`⎇ branch` / `worktree_name`）

## codegraph

- 索引按目录隔离：存 `<dir>/.codegraph/`，不跨 worktree 共享
- 每个 worktree 各自 `codegraph init`（本仓体量秒级）
- `.codegraph/` 不入库（已 gitignore）

## commit 归集

- change 提交前缀 `[<slug>]` 是跨 worktree 归集与 archive 结算的唯一索引
- slug 出生查重（含 remote 兜底），口径见 eo-shared/conventions.md §2

**何时读**：开 worktree 并行开发前；看板出现分叉徽标想确认口径时。
