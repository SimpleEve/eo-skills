---
title: cli/eo-board 只读看板 CLI
type: agent
tags: [cli, eo-board, serve, cache, rendering, routing, gates, journal, mdBlock, search]
created: 2026-07-24
updated: 2026-08-12
scope: 改动看板呈现、门禁判定、serve 缓存、聚合页视图与下钻路由、泳道卡详情 tab 时
status: active
source: cli/eo-board
summary: >
  零第三方依赖的单文件只读看板（约 4000 行）：默认全局 dashboard（终端聚合流 / --html 双视图首页快照 / --serve 轮询服务），`--all` 已退役；
  消费 eo_lib 解析层，board 专属逻辑为门禁判定、stage_progress、journal/frontmatter 投影、详情五 tab 与 HTTP 服务（含每项目单飞缓存）；
  `--project` 为显式下钻（终端单项目摘要；html 内嵌 + initial_route 直落；serve 首开 /p/<key>），泳道页顶栏项目切换器是自绘 button+listbox 下拉（无原生 select，键盘可达）；
  泳道页版面定格为列内滚动（sticky 列头），列可折叠为窄条并按项目记忆（整列头点击即折叠/展开），顶栏有可见搜索触发框，Cmd/Ctrl+K 定位搜索面板支持 `#seq` 直跳与全文片段命中。
conclusions:
  - 宪法四条：只读铁律（绝不写项目文件）、不做清单（无 SSE/无观测/无写操作/零第三方依赖）、性能靠缓存、GitHub 实时状态仅可选旗标
  - serve 缓存：每配置槽一构建锁（_BOARD_BUILD_LOCKS），锁内重算键+二次查表，同槽单飞、跨槽并行
  - 解析能力已抽至 cli/eo_lib，本文件只留呈现职责；改解析先看 eo_lib
  - 单项目泳道页只有一套资产（PROJECT_CSS/MARKUP/JS），serve 与聚合快照共用；改泳道渲染就是改这三块
  - 聚合来源：collect_sources(scan_dir, cwd_dir, explicit_dir) 合并注册条目 + cwd 自动并入 + --scan，按 repo_identity 去重；显式目标排首位
  - attach_card_progress 给每条 change 补 full_text / frontmatter / journal_entries / stage_progress；derive_stage_progress 与 blocker 共卡面
  - build_data 用 scan_all_changes_split（分叉感知扫描）：同 id 折叠为一张卡——一致副本合并维持旧口径；实质分叉时按「git 末次提交 + 目录 mtime」取最新变体出卡，其余变体收进 forks（diverged=True），与出卡同走附加管道；以 main worktree 为基准过滤状态更低的过期候选（先于折叠，过期副本不进 forks）；卡面/聚合流带「分叉×N」徽标，详情概览列出 forks 可切换（CARD_INDEX 键 ch:<id>@<worktree_name>）
  - mdBlock：先 esc 后白名单；safeHref 仅 http/https/mailto；台账未决 = open|fixed
  - route_key = `<URL 编码显示名>~<项目根 realpath 的 sha256 前 8 位>`；显示名不承担唯一性，路由映射逐请求重建
  - 泳道版面定格：`.wrap` 100vh flex 列 + `.board-scroll` 只吃横向，`.col` 列内纵向滚动（sticky `.col-head`，列尾 col-note 随内容）；`.prov` 数据来源区收进 `<details>` 默认收起，页面整体不滚
  - 列折叠：`setColumnCollapsed` 切 `.collapsed` 窄条（竖排列名+计数），localStorage 键 `eo-board:collapsed:<PROJECT_KEY>`；整列头 `.col-head` 点击即折叠/展开（点到 `.col-toggle` 时交还按钮自身处理），小原点 `◌/◉` 按钮保留作视觉指示与 aria 锚点；PROJECT_KEY 取 mount opts.projectKey（下钻 enterProject 传 `row.route_key`），回退 DATA_URL/data 指纹
  - 定位搜索：顶栏 `.gen` 左侧有可见 `.search-trigger` 触发框（`role=button` tabindex=0，⌕ + 提示文案 + ⌘K/`/` 键帽，样式对齐 chip），点击或聚焦后 Enter/空格 `openSearch()`；Cmd/Ctrl+K 与 `/`（输入态豁免）同样唤起面板，Esc 按「搜索→切换器→详情抽屉→定位态」逐层消费；`searchCards` 做 `#seq` 精确与 title/summary/full_text（backlog 用 body）不区分大小写子串匹配，按 STATUS_ORDER 分组出片段；选中 `locateSearchResult` 关面板、折叠列自动展开并持久、scrollIntoView + `located` 脉冲、他卡 dim，Esc/点空白 `clearLocate`
  - 项目切换器自绘：`buildHeader` 多项目时渲染 `.project-switch`（trigger `role=combobox` + 选项 `role=listbox/option`，href 存 `data-href`），`bindProjectSwitcher` 绑定开合与 `navigateProject` 跳转；↑/↓ `highlightProjectOption` 环形移动、Enter 选中、Esc/点外收起；单项目退化为静态 chip；选项名 `esc` 转义
  - `buildBoard` 热刷新重建前显式 `clearLocate()`，定位态不留半残；mount 的全局监听为 `keyHandler`+`clickHandler`（取代旧 escHandler），unmount 全量解绑并复位全部模块态
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
| 多项目聚合 | `collect_sources`（注册 + cwd 并入 + --scan，`repo_identity` 去重）→ `_aggregate_row` → `build_all_data`（给每行 board 注入 `dashboard_projects` 下拉清单）；`_stream_change` 行字段前置 |
| 路由 | `make_route_key` / `build_route_map` / `lookup_route` |
| 渲染 | 终端 `render_terminal`（**不**投 tab/journal）；HTML 前端 `renderChange` 五 tab 等 |
| serve / 缓存 | 聚合 handler `AllBoardRequestHandler`（类属性 `scan_dir`/`cwd_dir`/`explicit_dir`；`--project --serve` 也走它）+ 保留的单项目 `BoardRequestHandler`（主入口不再调用）；`_BOARD_CACHE` + `_BOARD_BUILD_LOCKS` |

## 门禁与 stage_progress（Python）

| 符号 | 职责 |
|------|------|
| `parse_finding_ledger_open_items` | 台账表行 → 未决列表；状态 ∈ `{open, fixed}`；verified/waived/superseded 忽略 |
| `parse_review_gate` | 轮次近似、历史标题计数 + `open_p0`/`open_p1` 与 titles |
| `parse_test_gate` | 完全通过时 `fail_titles` 清空（不算当前未决） |
| `compute_gates` | 填 `rec["gates"]` 与 `rec["blocker"]`；review 未决 P0/P1 也会成 blocker（含有保留通过） |
| `derive_stage_progress` | 返回 `{stage, label, rounds, warn}` 或仅 warn 对象 / `None`；review 未决时 label 并列组合（如 `review P0×1 P1×2`）；archived 无阶段可有 warn |
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
| `changeCard` | 卡面阶段标签独立一行 `.card-stage-line` + `card-warn`（`stage_progress.warn`）；summary 走 `mdInline` |

## 泳道搜索、列显隐与版面（PROJECT_JS）

| 函数 | 职责 |
|------|------|
| `collapsedStorageKey` / `loadCollapsedColumns` / `saveCollapsedColumns` | localStorage 键 `eo-board:collapsed:<PROJECT_KEY>`，读回容错为空集 |
| `setColumnCollapsed(status, collapsed)` | 切 `.collapsed` 窄条 + toggle 按钮文案/aria，随即持久；点窄条任意处展开；`buildBoard` 给每个 `.col-head` 绑整头点击折叠/展开（`e.target.closest('.col-toggle')` 时跳过，避免与按钮重复触发） |
| `searchCards(query)` | `#<num>` 走 seq 精确（backlog 不参与）；否则 title/summary/full_text（backlog 卡用 body）不区分大小写子串匹配；按 STATUS_ORDER 顺序产出 `{key, status, card, snippet}` |
| `searchSnippet` / `markSnippet` | 命中词前后截取上下文片段；`<mark>` 高亮前先 `esc` |
| `renderSearchResults` | 空查询引导文案 / 无匹配空态；按泳道分组渲染，`activeSearchIndex` 随结果数收敛 |
| `openSearch` / `closeSearch` | 面板开关；打开即聚焦输入框并重置活动下标 |
| 顶栏搜索触发框 | `buildHeader` 渲染 `#p-search-trigger`（`.search-trigger`，`role=button`/`tabindex=0`/aria-label「打开定位搜索」，内含 ⌕ 图标 + 提示 + ⌘K/`/` 键帽），click 与 keydown（Enter/空格，`preventDefault`）均调 `openSearch()`；`.gen` 的 `margin-left:auto` 已移交触发框 |
| `locateSearchResult(index)` / `clearLocate` | 关面板 → 折叠列自动展开（并持久）→ 目标卡 `located` + board `locating`（他卡降透明）+ scrollIntoView；`clearLocate` 幂等清除 |
| `isTextInput` | `/` 唤起豁免：input/textarea/select/contentEditable 聚焦时不触发 |

- 键盘交互集中在 mount 的 `keyHandler`：搜索面板开时 ↑/↓ 移动、Enter 定位；切换器开时 ↑/↓ `highlightProjectOption` 环形高亮、Enter `navigateProject` 跳转；Esc 按「搜索面板 → 项目切换器 → 详情抽屉 → 定位态」逐层消费；Cmd/Ctrl+K 与 `/` 唤起。`clickHandler` 负责点切换器外关切换器、点非卡空白 `clearLocate`
- mount 新增 `opts.projectKey`（下钻 `enterProject` 传 `row.route_key`；单项目直开时回退 DATA_URL 的 `/p/<key>` 或 `name~project_root` 指纹）；`buildBoard()` 开头无条件 `clearLocate()`，热刷新重建后定位态不残留
- 模块导出新增 `searchCards` / `searchSnippet`（测试挂钩）
- 版面 CSS：body 禁滚，`.wrap` 100vh flex 列；`.col` `overflow-y: auto` + sticky `.col-head`（`cursor:pointer` 整头可点折叠）；`.col.collapsed` 48px 窄条竖排列名；`.prov` 改 `<details>/<summary>` 折叠入口（`.prov-body` 限高内滚）；顶栏 `.search-trigger` 为 chip 风搜索框（220px 定宽、hover/focus-visible 边框反馈，键帽 10.5px）；搜索面板 `.search-backdrop/.search-panel` 与定位脉冲 `locate-pulse`（`prefers-reduced-motion` 内）

## 三形态入口

默认（无 `--project`）三形态全部走全局 dashboard：`cmd_all`（终端聚合流）/ `cmd_all_html`（双视图首页快照）/ `cmd_all_serve`（本地服务）；`--all` 旗标已退役（隐藏保留，带它报错「全局已是默认形态，去掉该旗标即可」）。`--project` 显式下钻：终端仍出单项目摘要（`build_data(cfg)` + `cmd_terminal`），`--html` 走 `cmd_project_html`（全局快照内嵌 + `initial_route` 直落该项目），`--serve` 走 `cmd_all_serve(args, cfg=cfg)`（首开 URL 为 `/p/<key>`）。`--scan` 只在默认全局形态可用（与 `--project` 互斥）；`--register/--unregister`。单次运行不走缓存。

## 全局 dashboard 双视图与下钻（默认形态）

| 关注点 | 落点 |
|--------|------|
| 首页两视图 | `ALL_HTML_TEMPLATE`：`#/` change 流、`#/cards` 概要卡；`initial_route` 时无 hash 直落 `#/p/<key>` |
| 下钻 | serve `/p/<route_key>` → `render_html(..., home_url="/")`；html 用 hash `#/p/<key>` + `embed_board` |
| 项目切换器 | 数据层注入 `dashboard_projects`（`build_all_data` 行内 / `_send_project` 逐请求），`buildHeader` 渲染自绘 `.project-switch`（trigger button + listbox 选项，跳转 href 存 `data-href`，分形态为 `#/p/<key>` 或 `/p/<key>`），`bindProjectSwitcher` 绑定交互 |
| 样式 | 聚合 CSS 与 `PROJECT_CSS` 互斥；泳道 `.wrap` = `min(94vw,1800px)`；`.drawer` = `min(920px,94vw)` |
| 失效路由 | `render_route_miss` |

## 来源

- [cli/eo-board](../../cli/eo-board) — 实现本体
- [cli-eo-lib.md](cli-eo-lib.md) — 解析层依赖
- install.sh — 符号链接安装入口
- `tests/test_eo_board_cache.py` — 缓存/路由/聚合与终端兼容基线；视图层 node 垫片
- `tests/test_board_card_progress.py` — 泳道卡进度：journal 逆序、stage_progress 当前性、tab 刷新、mdBlock/safeHref、质量门当前状态、XSS
- `tests/test_board_swimlane_search.py` — 泳道定位搜索（唤起/解绑生命周期、`#seq`/关键词/空态、backlog body 命中、折叠按项目键记忆、折叠列定位自动展开、serve 热刷新经真实 polling 接线清定位态）
- `tests/test_board_switcher_style.py` — 项目切换器自绘下拉锁定（开合/点外/Esc、方向键+回车跳转、双形态 href、当前项标记、项目名 XSS 转义、单项目静态 chip、无原生 select）
