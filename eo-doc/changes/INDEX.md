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
| 10 | [board-all-v2](10-board-all-v2/change.md) | full | feature | draft | 2026-07-27 | 聚合首页升级 change 流与概要卡双视图切换，/p/<key> 稳定键路由下钻泳道页（含 --scan 项目），--html 单文件 hash 路由 |
