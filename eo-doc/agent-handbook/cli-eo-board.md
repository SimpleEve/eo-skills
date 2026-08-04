---
title: cli/eo-board 只读看板 CLI
type: agent
tags: [cli, eo-board, serve, cache, rendering, routing, gates, journal, mdBlock]
created: 2026-07-24
updated: 2026-08-04
scope: 改动看板呈现、门禁判定、serve 缓存、聚合页视图与下钻路由、泳道卡详情 tab 时
status: active
source: cli/eo-board
summary: >
  零第三方依赖的单文件只读看板（约 3400 行）：终端摘要 / --html 静态快照 / --serve 本地轮询服务三形态，
  消费 eo_lib 解析层，board 专属逻辑为门禁判定、stage_progress、journal/frontmatter 投影、详情五 tab 与 HTTP 服务（含每项目单飞缓存）；
  聚合形态另有「change 流 ⇄ 概要卡」双视图首页与 route_key 下钻路由。
conclusions:
  - 宪法四条：只读铁律（绝不写项目文件）、不做清单（无 SSE/无观测/无写操作/零第三方依赖）、性能靠缓存、GitHub 实时状态仅可选旗标
  - serve 缓存：每配置槽一构建锁（_BOARD_BUILD_LOCKS），锁内重算键+二次查表，同槽单飞、跨槽并行
  - 解析能力已抽至 cli/eo_lib，本文件只留呈现职责；改解析先看 eo_lib
  - 单项目泳道页只有一套资产（PROJECT_CSS/MARKUP/JS），serve 与聚合快照共用；改泳道渲染就是改这三块
  - attach_card_progress 给每条 change 补 full_text / frontmatter / journal_entries / stage_progress；derive_stage_progress 与 blocker 共卡面
  - build_data 用 scan_all_changes_split（分叉感知扫描）：同 id 候选按 change.md 内容 sha256 分组，实质分叉各出一卡（diverged=True）、一致副本合并；以 main worktree 为基准过滤状态更低的过期候选；卡面 _key 追加 @worktree_name 去重
  - mdBlock：先 esc 后白名单；safeHref 仅 http/https/mailto；台账未决 = open|fixed
  - route_key = `<URL 编码显示名>~<项目根 realpath 的 sha256 前 8 位>`；显示名不承担唯一性，路由映射逐请求重建
---

eo-skills 的默认呈现层。数据全部派生自 change.md frontmatter、质量门报告与 backlog/roadmap 文件（不读 Obsidian stub）。

## 结构（单文件分区）

| 分区 | 内容 |
|------|------|
| 头部导入引导 | `Path(__file__).resolve()` 定位真实 `cli/` 后 `from eo_lib import ...`；入口捕获 `ConfigError` 格式化退出 |
| 门禁判定（gates） | `parse_*_gate` / `compute_gates`：探测 review/test/change-review/acceptance；台账 `parse_finding_ledger_open_items`（**open+fixed** 为未决）；合成 `blocker` |
| 阶段与进度投影 | `derive_stage_progress(gates, status)`：当前阶段徽标 + `warn`（`STAGE_WARN_ROUNDS=3`，与 stage 解耦）；`_gate_verdict_pass` 不含「有保留通过」 |
| journal | `parse_journal_entries`：按 `• HH:MM` 切窗，最近 N 条后**逆序**；`attach_card_progress` 读 `tmp/eo/loop/<id>/journal.md` |
| frontmatter 再投影 | `attach_card_progress`：`split_frontmatter(full_text)` → `frontmatter` 公开字典（空值省略） |
| 活跃度 | `max_activity` / `is_recent`（`ACTIVE_WINDOW_DAYS = 3`）/ `compute_project_activity` |
| 聚合 | backlog 扫描、roadmap、`git log` 直改统计、change git 统计；`build_data` 内对每条 change 调 `attach_card_progress` |
| 单项目视图资产 | `PROJECT_CSS` / `PROJECT_MARKUP` / `PROJECT_JS` → `render_html` 唯一泳道出口 |
| 多项目聚合 | `collect_sources` → `_aggregate_row` → `build_all_data`；`_stream_change` 行字段前置 |
| 路由 | `make_route_key` / `build_route_map` / `lookup_route` |
| 渲染 | 终端 `render_terminal`（**不**投 tab/journal）；HTML 前端 `renderChange` 五 tab 等 |
| serve / 缓存 | 单项目与聚合 handler；`_BOARD_CACHE` + `_BOARD_BUILD_LOCKS` |

## 门禁与 stage_progress（Python）

| 符号 | 职责 |
|------|------|
| `parse_finding_ledger_open_items` | 台账表行 → 未决列表；状态 ∈ `{open, fixed}`；verified/waived/superseded 忽略 |
| `parse_review_gate` | 轮次近似、历史标题计数 + `open_p0`/`open_p1` 与 titles |
| `parse_test_gate` | 完全通过时 `fail_titles` 清空（不算当前未决） |
| `compute_gates` | 填 `rec["gates"]` 与 `rec["blocker"]`；review 未决 P0/P1 也会成 blocker（含有保留通过） |
| `derive_stage_progress` | 返回 `{stage, label, rounds, warn}` 或仅 warn 对象 / `None`；archived 无阶段可有 warn |
| `attach_card_progress` | `full_text` / `frontmatter` / `journal_*` / `stage_progress` |

**当前阶段优先级（简化）**：review 未决（不通过或 open/fixed P0|P1）> test 失败 > change_review 未决 > acceptance（仅 `status=reviewed`）> 进行中弱信号。

## 泳道详情五 tab（PROJECT_JS）

| 函数 | 职责 |
|------|------|
| `renderChange` | tab 壳：概览 / 清单 / 质量门 / 动态 / 全文 |
| `renderFrontmatter` | 概览 frontmatter 键值 |
| `renderCurrentGateStatus` | 质量门顶部：阶段 / 卡点 / 未决明细；空态「当前无卡点」 |
| `renderGates` | 当前状态 + 各门报告（detail 列表只用 open/fixed titles，不用历史 p0_titles） |
| `renderJournal` | journal 条目 `mdBlock`；顺序依赖数据层逆序 |
| `mdBlock` / `applyInline` / `safeHref` | 迷你 markdown：标题 #~####、表、fenced code、列表/checkbox、hr、粗体/code/链接；**safeHref** 仅 http/https/mailto |
| `bindDetailTabs` / `openDetail(..., isRefresh)` | tab 点击；热刷新时恢复活动 `data-tab` |
| `changeCard` | 卡面阶段标签 + `card-warn`（`stage_progress.warn`） |

## 三形态入口

`eo-board`（终端）/ `--html [-o P]` / `--serve`；多项目：`--all` / `--project` / `--all --scan`；`--register/--unregister`。共用 `build_data(cfg)`，渲染出口不同。单次运行不走缓存。

## 聚合页双视图与下钻（`--all --html` / `--all --serve`）

| 关注点 | 落点 |
|--------|------|
| 首页两视图 | `ALL_HTML_TEMPLATE`：`#/` change 流、`#/cards` 概要卡 |
| 下钻 | serve `/p/<route_key>` → `render_html(..., home_url="/")`；html 用 hash `#/p/<key>` + `embed_board` |
| 样式 | 聚合 CSS 与 `PROJECT_CSS` 互斥；泳道 `.wrap` = `min(94vw,1800px)`；`.drawer` = `min(920px,94vw)` |
| 失效路由 | `render_route_miss` |

## 来源

- [cli/eo-board](../../cli/eo-board) — 实现本体
- [cli-eo-lib.md](cli-eo-lib.md) — 解析层依赖
- install.sh — 符号链接安装入口
- `tests/test_eo_board_cache.py` — 缓存/路由/聚合与终端兼容基线；视图层 node 垫片
- `tests/test_board_card_progress.py` — 泳道卡进度：journal 逆序、stage_progress 当前性、tab 刷新、mdBlock/safeHref、质量门当前状态、XSS
