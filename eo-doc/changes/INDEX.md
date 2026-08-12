# 变更时间线

| # | change | 档 | 类型 | 状态 | 日期 | 摘要 |
|---|--------|----|------|------|------|------|
| 1 | [shared-lib-board-cache](01-shared-lib-board-cache/change.md) | full | enhance | archived | 2026-07-24 | cli 解析能力抽为共享库供 eo-sync 复用；eo-board 补 local 覆盖合并，--serve 加缓存 |
| 2 | [sync-plugin-layer](02-sync-plugin-layer/change.md) | full | feature | archived | 2026-07-24 | 投影插件化为 eo-sync 单命令同步；stub/issue/PR 迁内置适配器，逐流转触发点全面退役 |
| 3 | [registry-board-watch](03-registry-board-watch/change.md) | full | feature | archived | 2026-07-25 | 新建 ~/.eo/projects.json 生态注册表；eo-board 多项目聚合与下钻；eo-sync watch 自动追平投影 |
| 4 | [sot-default-local-committed](04-sot-default-local-committed/change.md) | light | enhance | archived | 2026-07-25 | init 新项目默认 local 且管理侧随仓库提交，vault 仍可选，存量零改动 |
| 5 | [sync-config-consolidation](05-sync-config-consolidation/change.md) | light | enhance | archived | 2026-07-25 | init 停写 board/github 旧段改写 sync 段，存量重跑代写等价迁移，兼容回落不动 |
| 6 | [watch-single-instance](06-watch-single-instance/change.md) | light | enhance | archived | 2026-07-25 | watch 同作用域硬互斥（--all 撞 --all、同仓 --project 互撞即报错退出），跨域重叠仅告警 |
| 7 | [project-root-normalization](07-project-root-normalization/change.md) | light | enhance | archived | 2026-07-25 | 配置读取时把相对 project_root 按 repo root 解析并解软链，告警放行；解析不到仍报错 |
| 8 | [eo-helper-entry](08-eo-helper-entry/change.md) | full | feature | archived | 2026-07-25 | 新增 eo-helper 数字菜单唯一入口；eo-board --all 补 --html/--serve；README 命令面收纳 |
| 9 | [loop-fork-escalation](09-loop-fork-escalation/change.md) | light | enhance | archived | 2026-07-25 | worker 不问用户但形态分叉须清单上报，总控攒成封闭选择转达用户后回灌 |
| 10 | [board-all-v2](10-board-all-v2/change.md) | full | feature | archived | 2026-07-27 | 聚合首页升级 change 流与概要卡双视图切换，/p/<key> 稳定键路由下钻泳道页（含 --scan 项目），--html 单文件 hash 路由 |
| 11 | [board-card-progress](11-board-card-progress/change.md) | light | feature | archived | 2026-08-02 | card 详情改五 tab（含全文/journal 动态），卡面标质量门阶段轮次，≥3 轮警告样式 |
| 12 | [review-fix-test-routing](12-review-fix-test-routing/change.md) | full | enhance | archived | 2026-08-02 | Review 修复后仅在既有测试证据失效时进入 Test |
| 13 | [loop-risk-triggered-verification](13-loop-risk-triggered-verification/change.md) | full | enhance | archived | 2026-08-02 | eo-loop 仅在出现客观风险信号时升级核查 |
| 14 | [board-worktree-split](14-board-worktree-split/change.md) | light | enhance | archived | 2026-08-04 | 多 worktree 并行同一 change 且实质分叉时 board 各出一卡，一致副本仍合并；卡面 branch/worktree 分行显示 |
| 15 | [board-fork-collapse](15-board-fork-collapse/change.md) | light | enhance | archived | 2026-08-12 | 同 change 多 worktree 副本只出最新一卡，分叉副本收进徽标可下钻 |
| 16 | [board-global-dashboard](16-board-global-dashboard/change.md) | full | enhance | archived | 2026-08-12 | 移除单项目默认入口，三形态默认全局 dashboard；泳道页项目 chip 改下拉切换 |
| 17 | [board-swimlane-search](17-board-swimlane-search/change.md) | full | feature | confirmed | 2026-08-12 | 泳道页新增 Cmd+K 定位搜索（#seq 直跳、全文命中片段）、列内独立滚动、列折叠隐藏并持久记忆 |
