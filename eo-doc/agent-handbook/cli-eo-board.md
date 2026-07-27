---
title: cli/eo-board 只读看板 CLI
type: agent
tags: [cli, eo-board, serve, cache, rendering, routing]
created: 2026-07-24
updated: 2026-07-27
scope: 改动看板呈现、门禁判定、serve 缓存、聚合页视图与下钻路由时
status: active
source: cli/eo-board
summary: >
  零第三方依赖的单文件只读看板（2729 行）：终端摘要 / --html 静态快照 / --serve 本地轮询服务三形态，
  消费 eo_lib 解析层，board 专属逻辑为门禁判定、backlog/roadmap 聚合、渲染与 HTTP 服务（含每项目单飞缓存）；
  聚合形态另有「change 流 ⇄ 概要卡」双视图首页与 route_key 下钻路由。
conclusions:
  - 宪法四条：只读铁律（绝不写项目文件）、不做清单（无 SSE/无观测/无写操作/零第三方依赖）、性能靠缓存、GitHub 实时状态仅可选旗标
  - serve 缓存：每配置槽一构建锁（_BOARD_BUILD_LOCKS），锁内重算键+二次查表，同槽单飞、跨槽并行
  - 解析能力已抽至 cli/eo_lib，本文件只留呈现职责；改解析先看 eo_lib
  - 单项目泳道页只有一套资产（PROJECT_CSS/MARKUP/JS），serve 与聚合快照共用；改泳道渲染就是改这三块
  - route_key = `<URL 编码显示名>~<项目根 realpath 的 sha256 前 8 位>`；显示名不承担唯一性，路由映射逐请求重建
---

eo-skills 的默认呈现层。数据全部派生自 change.md frontmatter 与 backlog/roadmap 文件（不读 Obsidian stub）。

## 结构（单文件分区）

| 分区 | 内容 |
|------|------|
| 头部导入引导 | `Path(__file__).resolve()` 定位真实 `cli/` 后 `from eo_lib import ...`；入口捕获 `ConfigError` 格式化退出 |
| 门禁判定（gates） | 探测 review/test/change-review/acceptance 报告，解析 P0/P1/FAIL/轮次，合成 blocker |
| 活跃度 | `max_activity` / `is_recent`（`ACTIVE_WINDOW_DAYS = 3`）/ `compute_project_activity`——项目级 `activity_at` = max(各 worktree HEAD commit 时间, `changes/` 与 `backlog/` 树 max-mtime)，与 freshness 键共用 `eo_lib.tree_max_mtime` |
| 聚合 | backlog 扫描（vault/local 分流）、roadmap frontmatter、`git log` 直改统计、change git 统计 |
| 单项目视图资产 | `PROJECT_CSS` / `PROJECT_MARKUP` / `PROJECT_JS` 三块共享常量 → `HTML_TEMPLATE`（独立页，含内嵌 style/markup/data/script）与 `PROJECT_ASSETS`（聚合快照嵌入形态，同内容换标签壳）；`render_html(data, data_url, home_url)` 是唯一泳道页出口，`home_url` 非空即渲出「← 返回首页」 |
| 多项目聚合 | `collect_sources`（注册表 + `--scan`）→ `_aggregate_row`（逐项目一行：五状态计数、backlog、as-of、`activity_at`、`route_key`、非 archived 的 `changes[]`）→ `build_all_data`（线程池 ≤8 并发、`_safe_row` 单条目兜底）；`_stream_change` 把 change 流一行所需字段全部前置，前端不回查 |
| 路由 | `make_route_key(display_name, project_dir)` / `build_route_map`（逐请求重建，新注册与新 scan 立即可下钻；配置读不出的条目不进映射）/ `lookup_route`（原样匹配 → 解码后按可读名再比一次，容忍未编码的中文路径） |
| 渲染 | 终端表（单项目 `render_terminal` / 聚合 `render_all_terminal`）/ 自包含 HTML（JSON 注入 + 前端 JS 渲染）/ `ALL_HTML_TEMPLATE` 聚合首页（双视图 + hash 路由）/ `ROUTE_MISS_TEMPLATE` 失效路由指引页 |
| serve | 单项目 `BoardRequestHandler`：`/` 与 `/data.json`；聚合 `AllBoardRequestHandler`：`/`、`/data.json`、`/p/<route_key>`、`/p/<route_key>/data.json`，未知路径一律 404 指引页（不 5xx）。均仅绑 127.0.0.1:7333，前端 3 秒轮询 hash 比对热刷新 |
| 缓存（serve 内） | `_BOARD_CACHE` 槽（config_path 为键）+ `_BOARD_BUILD_LOCKS` 每槽构建锁；miss 时锁内重算 freshness 键并二次查表后才 `build_data`；hit/miss 各记一行 stderr 诊断。聚合首页与 `/p/<key>` 下钻共用同一批槽 |

## 三形态入口

`eo-board`（终端）/ `--html [-o P]` / `--serve`；多项目三形态：`--all`（终端 / `--html` 自包含聚合快照 / `--serve` 聚合页逐请求重读注册表+跨槽并行+空表指引页；argparse 组合矩阵钉定 --port 限 serve、--no-open 限 html/serve）（注册表聚合，线程池并发、坏条目行内隔离、as-of 戳）/ `--project <路径|注册名>`（任意目录下钻，重名歧义拒绝）/ `--all --scan <父目录>`（一层兜底、同仓 worktree 去重、零写入）；`--register/--unregister` 维护注册表（写 ~/.eo，预钉例外）——共用 `build_data(cfg)`，只是渲染出口不同。单次运行形态不走缓存（天然全量扫）。

## 聚合页双视图与下钻（`--all --html` / `--all --serve`）

| 关注点 | 落点 |
|--------|------|
| 首页两视图 | `ALL_HTML_TEMPLATE` 内前端 JS：`#/` = 跨项目 change 流（非 archived，按 `activity_at` 倒序，`active=false` 的行降权并以分界线区隔）、`#/cards` = 概要卡；视图态记在 URL hash，刷新不丢 |
| 下钻路由 | serve 走真实路径 `/p/<route_key>`（`_send_project` 查 `build_route_map` → `get_board_data_cached` → `render_html(..., home_url="/")`）；`--html` 走同一套 key 的 hash 路由 `#/p/<route_key>`，泳道数据由 `build_all_data(embed_board=True)` 内嵌单文件，离线零请求 |
| 两套样式共存 | 快照同文件里既有聚合首页样式又有 `PROJECT_CSS`；进泳道视图时禁用聚合样式表并挂载 `PROJECT_CSS`，靠样式表互斥分流，**没有第二套模板分支**——`render_all_html` 仅在真嵌了泳道数据时才带 `PROJECT_ASSETS`，serve 首页不背这份体量 |
| 容器宽度口径 | `ALL_HTML_TEMPLATE` 的 `.wrap` = `max-width: 1280px` 居中（管首页两视图）；`PROJECT_CSS` 的 `.wrap` = `max-width: min(94vw, 1800px)` 居中（管泳道页，六列约需 1678px 故上限取 1800）；`.drawer` = `min(920px, 94vw)`。两处 `.wrap` 靠上面的样式表互斥天然分流 |
| 失效路由 | `render_route_miss` 列出当前可下钻项目并给回首页链接；空聚合时给注册/`--scan` 指引 |

## 来源

- [cli/eo-board](../../cli/eo-board) — 实现本体
- [cli-eo-lib.md](cli-eo-lib.md) — 解析层依赖
- install.sh — 符号链接安装入口
- `tests/test_eo_board_cache.py`（1615 行）— 缓存单飞、路由、渲染与终端兼容基线。两点约定：①「终端输出兼容基线」常量守 `render_terminal` 逐字节不变，`build_data`/`render_html` 只做「旧字段保真、新字段放行」的递归子集断言；②视图层断言用最小 DOM 垫片把内嵌脚本交给 `node` 真跑（`NODE_MOUNT_RUNNER`），断言落在渲染产出的 DOM 上——`node` 缺失时该类用例 `skipUnless` 跳过，运行时仍是零第三方依赖（由 `test_stays_on_stdlib_only_and_binds_loopback_only` 静态守护）
