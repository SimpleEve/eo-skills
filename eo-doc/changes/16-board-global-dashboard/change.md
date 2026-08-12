---
id: board-global-dashboard
seq: 16
title: board 收敛为全局 dashboard
summary: 移除单项目默认入口，三形态默认全局 dashboard；泳道页项目 chip 改下拉切换
status: implementing
tier: full
type: enhance
base_commit: 4c89b569658f043c7b144be64e27ae9543d92b89
plan_revision: 1
fix_rounds: 0
fix_consumed: []
commits: []
issue: ~
pr: ~
created: 2026-08-12
---

# board 收敛为全局 dashboard

## 速览

- **改什么**：`eo-board` 终端 / `--html` / `--serve` 的默认形态从「当前目录单项目」改为「全局 dashboard（聚合首页 + 下钻）」，`--all` 旗标退役；泳道页顶栏项目 chip 变成可切换项目的下拉。
- **为什么**：单项目入口与聚合下钻功能重叠、维护两套口径；用户裁决「直接移除单项目形式，整个 board 改成全局 dashboard」。
- **行为差异**：之前在项目目录里跑 `eo board` 直接看本项目泳道摘要 → 之后看到全部注册项目的聚合首页，看单项目用 `--project` 直达；之前泳道页项目名是静态文字 → 之后是可点开切换其他项目的下拉。
- **怎么验**：AC 7 条（人工 0 条）；三种形态各跑一次 + 下拉在快照与 serve 各点一次。

## 1. 意图

board 现有单项目与 `--all` 聚合两套入口，聚合形态（双视图首页 + `/p/<key>` 下钻）已覆盖单项目入口的全部价值。brainstorming（`brainstorm/2026-08-12-board全局dashboard化与泳道易用性.md`）裁决：移除单项目形态，board 收敛为单一全局 dashboard，泳道页降级为 dashboard 的下钻页。用户原话：「直接移除单项目形式吧，没必要，整个 board 就改成全局 dashboard」。

已钉决策（来自 brainstorming 捕获，不重复提问）：
- 板形态 → 全局 dashboard 单一口径：home 聚合双视图 + `/p/<key>` 下钻，移除单项目独立入口（理由：用户裁决「没必要」，聚合形态已覆盖）
- 终端同步全局化 → 默认输出聚合终端流，单项目查看靠 `--project`（假设，用户未逐条确认；不对则确认时纠正）
- `--project` → 保留，语义不变（任意目录直达该项目泳道页），降为显式过滤器
- 项目下拉 → 泳道页顶栏项目 chip 改下拉，serve 与静态 `--html` 快照均可跳转（理由：全局化后各项目数据同进程/同快照，无死链问题）
- 破坏性变更 → 直接替换，不保留单项目入口兼容路径（用户原话「直接移除」）
- cwd 未注册项目 → 含 `.eo-project.json` 的 cwd 自动并入 dashboard（与 `--scan` 临时并入同口径），保住「cd 进项目直接看」的便利（假设，用户未逐条确认）
- 与 #17 的实施顺序 → #16 先于 #17 串行实施（理由：两者同改 `cli/eo-board` 的 PROJECT_CSS/MARKUP/JS 共享资产，并行必撞；change-review P1-4，eo-change 场景 B 裁决采纳，与总控既定编排一致）；#17 开工前须基于本 change 交付基线重读共享资产

## 2. 验收清单

- [ ] AC-1 不带旗标运行 `eo-board` / `eo-board --html` / `eo-board --serve`，用户看到的都是全局 dashboard（终端聚合流 / 双视图首页），不再需要 `--all`（验证：三种形态各跑一次）
- [x] AC-2 `eo-board --project <名|路径>` 行为与现状一致：直达该项目泳道页，五 tab 详情不受影响（验证：对任一注册项目执行，与聚合页点进去比对）
- [ ] AC-3 泳道页顶栏项目 chip 是可点开的下拉，列出当前可下钻的全部项目（含 `--scan` 临时并入项），选中即跳到对应项目泳道页；静态 `--html` 快照与 `--serve` 两种形态下跳转都生效（验证：两种形态各切换一次）
- [x] AC-4 在已注册项目目录内运行 `eo-board`，看到的是全局首页而非该项目单项目视图
- [x] AC-5 在未注册但含 `.eo-project.json` 的目录运行 `eo-board`，该项目临时并入 dashboard（标记口径同 `--scan` 项），重启进程后不残留
- [x] AC-6 注册表为空且 cwd 无项目时，用户看到空态指引（提示如何 `--register`），不是报错堆栈或空白页
- [ ] AC-7 10 个注册项目规模下 `eo-board --html` 快照生成 ≤ 5 秒——本 revision 硬门，超时即报失败并交用户裁决是否回炉（验证：秒表/`time` 跑一次；用户裁决 2026-08-12：冻结 5s，不允许实施期调整）

## 3. TODO

### Batch 1（MVP：默认形态切换）
- [x] TODO-1 CLI 入口改默认：无 `--project` 时三形态全部走聚合路径；`--all` 旗标移除，带 `--all` 调用报错并提示「全局已是默认形态，去掉该旗标即可」（文件：修改: cli/eo-board；对应 AC-1、AC-2、AC-4；完成判据：保留 `resolve_project_token` 后的显式单项目分支——按名和按路径直达泳道页，终端 / `--html` / `--serve` 均不经过默认聚合入口且五 tab 保持）
- [x] TODO-2 cwd 项目自动并入：聚合收集源时探测 cwd 的 `.eo-project.json`，未注册则按 `--scan` 同口径临时并入（文件：修改: cli/eo-board；对应 AC-5）
- [x] TODO-3 空态兜底：注册表为空且 cwd 无项目时，终端与 HTML 均输出注册指引（文件：修改: cli/eo-board；对应 AC-6）

### Batch 2（下拉与性能）
- [ ] TODO-4 泳道页项目 chip 改下拉：数据层把可下钻项目清单（名 + 路由键）注入泳道页 DATA，前端渲染下拉并在 serve（`/p/<key>`）与 `--html`（hash `#/p/<key>`）下分别跳转（文件：修改: cli/eo-board；对应 AC-3）
- [ ] TODO-5 10 项目 `--html` 快照计时验证，超阈值先定位热点（重复扫描/重复读盘）再优化，不引入缓存到单次形态以外的黑魔法（文件：修改: cli/eo-board；对应 AC-7）
- [ ] TODO-6 `--help` 文案与 eo-helper 菜单命令面同步新口径（移除 `--all` 说法）（文件：修改: cli/eo-board、修改: cli/eo-helper；对应 AC-1）

## 4. 涉及文件

- `README.md`、`docs/GUIDE.md`、`docs/cli-reference.md`、`docs/how-it-works.html` — 用户文档仍把无旗标入口描述为单项目、`--all` 为聚合入口；随 TODO-6 同批更新命令面口径
- `eo-doc/state/eo-board-cli.md`、`eo-doc/agent-handbook/cli-eo-board.md` — 实现完成后由 /eo-doc-manager sync 以代码为信源更新，不在本 change 手改
- `tests/test_eo_board_cache.py` — /eo-test 交接清单（测试资产唯一写入者）：入口默认聚合化、`--all` 退役报错、`--project` 直达、空注册表空态、cwd 未注册并入、`--scan` 与路由用例的预期变化适配

## 7. 风险与回滚

- **对外接口变更**：`--all` 退役、cwd 默认语义变化，用户脚本/肌肉记忆里 `eo board` 的含义改变。回滚 = revert 本 change 的 commit 区间即恢复旧入口，无数据迁移。
- 缓存槽语义不变（聚合与下钻本已共用槽），无持久化结构变更。
