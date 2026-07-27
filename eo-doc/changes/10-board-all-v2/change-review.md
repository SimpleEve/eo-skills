---
title: eo-board --all 聚合页 v2：change 流首页 + 双视图切换 + 路由式下钻 Change 审查报告
change_id: board-all-v2
created: 2026-07-27
status: active
summary: >
  首轮全量审查不通过，3 条 P0 分别涉及路由身份前提不成立、AC-4 点击入口覆盖断裂和 AC-9 无 TODO 映射；另有 4 条 P1 待起草方裁决。
---

# eo-board --all 聚合页 v2：change 流首页 + 双视图切换 + 路由式下钻 Change 审查报告

> 关联：[change.md](change.md) ｜ 审查日期：2026-07-27 ｜ change status：confirmed
> 前提抽查基线：`dfb1a6e875985c3735f4a1a11f29b91a96e92b63`（任务指定基线，且审查时等于 HEAD；change.md 的 `base_commit` 尚为空）

## 审查总结

结论：不通过，P0 为 3，修订并复审前不得进入 implement。方向本身与已钉设计判断一致，9 条 AC 的用户入口和异常面总体可验，6 条 TODO 的文件前提、既有每项目缓存槽、单项目泳道渲染与单文件快照能力也都真实存在；阻塞点集中在两处：`/p/<注册名>` 不能唯一覆盖当前合法的同名项目与 `--scan` 未注册项目，以及 AC-4/AC-9 的 TODO 映射不闭合。另有活动时间口径、已钉可见字段、下钻数据端点和连带文档 4 条 P1，移交起草方裁决。

## Finding 台账

<!-- 状态单一来源：本 skill 建条与核销（open→verified），修订方（/eo-change）填「处置」列。wont-fix 项后续任何轮次不得重报 -->

| ID | 级别 | 摘要 | 位置 | 状态 | 处置（修订方填） |
|----|------|------|------|------|------------------|
| P0-1 | P0 | `/p/<注册名>` 不能唯一、完整地标识当前支持的同名注册项目与 `--scan` 未注册项目 | AC-4、§5 路由表、TODO-4/5 | fixed | 用户拍板（2026-07-27）route_key = `/p/<URL 编码可读名>~<repo 标识 hash8>`，钉入 §1 已钉决策（3 条）与 §5「路由标识」；AC-4 改写覆盖同名/`--scan`/失效路由；TODO-4 改 key→config 映射分派并补同名双项目、scan 项目、CJK 名、名不一致正反例判据；TODO-5 快照同 key |
| P0-2 | P0 | AC-4 的项目条卡/change 行点击没有 TODO 落点，概要卡点击也未映射到 AC-4 | AC-4、TODO-2/3/4 | fixed | TODO-2 补条卡/change 行绑定 route_key 链接、映射 AC-4 并加「两入口命中对应项目 route」分项判据；TODO-3 补 AC-4 映射与概要卡点击分项判据；TODO-4 保留服务端路由半边，各自分项判据齐备 |
| P0-3 | P0 | 人工 AC-9 没有任何 TODO 覆盖 | AC-9、TODO-2/3 | fixed | TODO-2 补 AC-9 映射（change 流对照 variant-2 可自动核对面）、TODO-3 补 AC-9 映射（概要卡信息面不劣化断言）；两处均注明人工观感留用户验收不代勾 |
| P1-1 | P1 | “最近活动”缺少可直接实现的逐 change 时间公式，现有 `last_touch` 无法满足未提交编辑后 3 秒内浮顶 | AC-1/2/6、TODO-1/2、§5 活跃判定 | fixed | 采纳：§5 钉 change/project 两级 `activity_at` 公式（带时区秒级，明确不复用日粒度 `last_touch`）；TODO-1 字段改 activity_at 并补「未提交编辑后前移浮顶 + 3 天边界两侧 fixture」判据 |
| P1-2 | P1 | 已钉的非主 worktree 标记与项目目录没有完整进入 AC 和渲染完成判据 | §1、AC-1/2、TODO-1/2 | fixed | 采纳：AC-1 补非主 worktree `⎇branch@worktree` 行字段、AC-2 补条卡目录字段；TODO-1 项目级数据补目录、TODO-2 判据明写「含 ⎇ 标记 / 含目录」 |
| P1-3 | P1 | `/p/<项目>` 页面对应的 JSON 端点未钉定，现有单项目模板会绝对请求聚合 `/data.json` | §5 路由表、TODO-4 | fixed | 采纳：§5 钉 `/p/<route_key>/data.json` 单项目端点，渲染函数注入 data URL 替代硬编码 fetch；TODO-4 判据补两项目并发轮询互不串数据、各走各自缓存槽 |
| P1-4 | P1 | 用户文档、state 与 handbook 仍描述旧聚合页，方案既无 §4 影响面也无更新 TODO | 条件节、§3 | fixed | 采纳：新增 §4 影响面——docs/cli-reference.md、docs/GUIDE.md 本 change 内更新（TODO-6 扩文件与描述，AC-8 扩文档口径一致）；state/eo-board-cli 与 handbook/cli-eo-board 交归档 doc-manager sync，§4 写明所需最终口径 |

## P0 - 必须修订（阻塞 implement）

### [P0-1] 路由身份前提不成立

- 类型：前提不成立
- 位置：change.md AC-4、§5 路由表、TODO-4/5
- 描述：§5 把 serve 路由钉为 `/p/<注册名>`，并计划“重名歧义沿用 `--project` 的拒绝语义”。但当前注册表契约明确允许不同仓库同名共存，`--project` 按名多命中时只能报歧义、不能选中任一项目；同时既有 `--scan` 与 `--all --html/--serve` 正交，聚合数据还会包含没有注册名的临时项目。一个原始注册名路径段因此既不唯一，也不覆盖全部合法项目行。
- 证据：`cli/eo_lib/registry.py:3-5,64-90,105-107` 明确 name 非唯一且同名合法；`cli/eo-board:2017-2035` 只在名字唯一时解析；`cli/eo-board:1607-1654` 会把未注册扫描项目并入 rows；聚焦回归 `test_project_name_ambiguity_lists_candidates`、`test_scan_merges_unregistered_without_writing_registry`、`test_argparse_matrix_scan_composes_with_html` 共 3/3 通过。
- 影响：同名项目的任意卡/行点击只能落歧义页，扫描项目没有可用注册名，AC-4“任意项目条卡、change 行、概要卡均进入对应泳道页”在当前合法输入域内不可满足；静态快照的 `#/p/<名>` 同样受影响。
- 建议：为每个有效 row 产出唯一 `route_key`，名字只作显示。建议采用“URL 编码可读名 + repo identity 的 hash8”并让注册/扫描两类来源共用，例如 `/p/<quoted-name>~<hash8>`；serve 每次按当前 sources 重建 key→config 映射，快照嵌同一 key。补同名双项目、未注册 scan 项目、注册名与配置名不一致、CJK 名和失效 key 的正反例。

### [P0-2] AC-4 的三个点击入口没有闭合到 TODO

- 类型：TODO↔AC 映射断裂
- 位置：change.md AC-4、TODO-2/3/4
- 描述：AC-4 要求项目条卡、change 行、概要卡三个入口都可点击。TODO-4 只负责 handler 路由与返回入口；TODO-2 负责项目条卡和 change 流，却没有点击接线、AC-4 映射或对应完成判据；TODO-3 虽写“卡片升级为可点下钻”，却只标 AC-3。结果是路由后端有落点，但入口侧两项悬空、另一项映射错误。
- 影响：implement 按 TODO 勾选可以在没有项目条卡/change 行链接的情况下宣告 AC-4 对应工作完成，后续批末检查也缺少定位入口。
- 建议：TODO-2 明写项目条卡与 change 行绑定 `route_key` 链接并增加“两个入口均命中对应项目”的完成判据，映射 AC-4；TODO-3 增补 AC-4 映射并保留概要卡点击判据；TODO-4 继续负责服务端路由。多条 TODO 共同覆盖 AC-4 后，各自保留分项完成判据。

### [P0-3] AC-9 没有 TODO 覆盖

- 类型：TODO↔AC 映射断裂
- 位置：change.md AC-9、TODO-2/3
- 描述：AC-9 要用户分别过目 change 流视图与概要卡视图，但 TODO-1 至 TODO-6 的“对应 AC”均未包含 AC-9。TODO-2/3 正是两个视图的实现落点，却没有把人工验收面映射回来。
- 影响：AC-9 成为悬空 AC；即使代码完成，也没有 TODO 告诉 implement 哪些改动会生成/刷新该人工验收项。
- 建议：TODO-2 增补 AC-9（change 流对照定稿），TODO-3 增补 AC-9（概要卡不劣化）；两项的完成判据分别保留可自动检查的结构/信息面，人工观感仍只由用户在后续验收单确认，不在 TODO 阶段代勾。

## P1 - 建议修订（移交起草方裁决，不阻塞循环）

### [P1-1] 活动排序口径尚未闭合到现有数据形态

AC-1/2/6 和 §5 反复使用“最近 commit 或 change/backlog mtime 复合信号”，但没有钉逐 change、项目级各自取哪些路径、取 max 的先后和时间精度。当前 `compute_change_git_stats` 在 change 目录已有 git 历史时只写最后一次 commit 的日期，只有完全无历史才回退文件 mtime（`cli/eo-board:77-92`）；因此缓存键虽会因目录 mtime 变化而失效（`cli/eo_lib/freshness.py:37-69`），重建后的现有 `last_touch` 仍可能不变，更不能稳定区分同一天多条 change 的先后。

建议在 §5 明写两个字段：`change.activity_at = max(该 change 目录最后 commit 时间, 该目录文件 max-mtime)`；`project.activity_at = max(各 worktree HEAD/refs 所需 commit 时间, changes/backlog 数据源 max-mtime)`，统一为带时区的秒级时间，3 天边界按同一时区计算。TODO-1 的完成判据补“有历史的 tracked change 发生未提交编辑后 activity_at 前移并排到流顶”以及 3 天边界两侧 fixture；不要把现有日粒度 `last_touch` 直接抬升为新排序键。

### [P1-2] 两项已钉可见字段未进入验收闭环

§1 明列非主 worktree 时显示 `⎇branch@worktree`，项目条卡/概要卡都显示目录；TODO-1 只承诺产出 branch/worktree 数据，AC-1 与 TODO-2 的渲染字段却没有该标记。AC-2 同样漏了项目条卡目录，虽然定稿 `design/variant-2.html:220-229,237-246` 实际画出了分支/worktree 与路径。

建议把非主 worktree 标记补进 AC-1 与 TODO-2 的行字段/静态断言，把目录补进 AC-2 与 TODO-2 的条卡字段/断言。这样实现不会只抬数据却漏渲染，也不会因 AC 没写而把定稿中的目录静默删掉。

### [P1-3] 下钻页的数据端点仍有两种不等价实现

§5 只写聚合 `/data.json`，对单项目数据说“沿用其既有端点形态按路由取用”。当前单项目 HTML 模板硬编码 `fetch('/data.json')`（`cli/eo-board:1398-1420`），聚合 handler 的 `/data.json` 又明确返回聚合数据（`cli/eo-board:1966-1992`）。如果把现有 `render_html` 原样挂到 `/p/<key>`，3 秒轮询会取错 JSON；如果让 `/data.json` 随 Referer 或页面态分派，则端点语义不稳定且不利于缓存测试。

建议在 §5 钉一个明确形态：例如页面 `/p/<route_key>`、数据 `/p/<route_key>/data.json`，由渲染函数注入 data URL；或统一走 `/api/project/<route_key>`。TODO-4 的完成判据补两项目并发轮询互不串数据、未知/失效 key 返回含首页链接的指引，以及单项目数据仍走各自缓存槽。

### [P1-4] 连带文档没有处置落点

`docs/cli-reference.md:53-66`、`docs/GUIDE.md:259-266` 仍把聚合 web 描述为概要卡并把下钻限定为 `--project`；`eo-doc/state/eo-board-cli.md:19-40` 与 `eo-doc/agent-handbook/cli-eo-board.md:21-34` 也仍记录旧的 `/`、`/data.json` 和聚合形态。本 change 会改变日常主入口和服务路由，但 §3 只列代码/测试，且没有 §4 说明这些连带文件由何时更新。

建议增加 §4 影响面，明确用户文档与代码侧 state/handbook 的更新责任；若本 change 内更新，增一个 Batch 3 TODO 并扩 AC-8 或新增文档一致性 AC，避免出现无法映射的文档 TODO。若明确交给 archive 的 doc-manager sync，也要在 §4 写出触发点与所需最终口径。

## P2 - 可选优化

无新增 P2。AC-5 的“零网络请求”可在后续测试分层时用浏览器请求拦截补强，但声明本身已有明确触发与观察结果，不构成方案 finding。

## AC 质量检查

| AC | 用户视角 | 可验证 | 技术无关 | 备注 |
|----|---------|--------|---------|------|
| AC-1 | 是 | 是 | 部分 | 行字段与排序可直接核对；活动公式和 worktree 标记见 P1-1/P1-2 |
| AC-2 | 是 | 是 | 是 | 项目条卡与静默态可观察；目录字段见 P1-2 |
| AC-3 | 是 | 是 | 是 | 默认视图、切换和刷新保持均有明确动作与结果 |
| AC-4 | 是 | 是 | 是 | 点击/返回/未知名均可验；方案路由身份与 TODO 覆盖分别见 P0-1/P0-2 |
| AC-5 | 是 | 是 | 部分 | 命令、单文件、hash 路由和零网络结果清楚；内部自包含约束可机械验证 |
| AC-6 | 部分 | 是 | 部分 | 3 秒热刷新是用户结果；调用计数是必要的缓存回归证据 |
| AC-7 | 是 | 是 | 是 | 空表与坏条目隔离覆盖边界/失败路径 |
| AC-8 | 是 | 是 | 是 | 终端输出与 argparse 正反例均为用户可见兼容性 |
| AC-9 | 是 | 是 | 是 | “人工:”标记与两个过目入口正确，但无 TODO 映射（P0-3） |

异常/边界由 AC-4、AC-7、AC-8 承担；AC-9 是唯一人工项，agent 不代勾。未发现“正常工作”类主观自动 AC，也未发现超出 §1 的镀金 AC。

## TODO↔AC 映射检查

| TODO | 对应 AC | 状态 |
|------|---------|------|
| TODO-1 | AC-1、AC-2、AC-6 | 通过：聚合字段、项目活动和 getter 一致性有地基落点；活动公式见 P1-1 |
| TODO-2 | AC-1、AC-2、AC-3 | 不通过：项目条卡/change 行点击应覆盖 AC-4，change 流人工对照应覆盖 AC-9（P0-2/P0-3） |
| TODO-3 | AC-3 | 不通过：描述中的概要卡点击属于 AC-4，概要卡人工不劣化属于 AC-9，均未映射（P0-2/P0-3） |
| TODO-4 | AC-4、AC-6 | 部分：handler、返回入口和缓存有落点，但 route key 前提不成立、数据端点未钉（P0-1/P1-3） |
| TODO-5 | AC-5 | 通过：单文件双视图与 hash 路由一对一覆盖 |
| TODO-6 | AC-7、AC-8 | 通过：异常隔离、终端与参数矩阵回归均有测试落点 |

AC-4 只有服务端路由半边被 TODO-4 覆盖，三个点击入口没有完整映射；AC-9 完全悬空。其余 AC 均至少有一条 TODO 覆盖，未发现占位符或意图外 TODO。

## TODO 机械前提核验

| TODO | 操作与对象 | 基线结果 |
|------|------------|----------|
| TODO-1 | 修改 `cli/eo-board`、`tests/test_eo_board_cache.py` | 两对象存在；`build_data`、`_aggregate_row`、`build_all_data`、`_fresh_entry`、`_get_board_entry_cached` 形态相符 |
| TODO-2 | 修改 `cli/eo-board`、`tests/test_eo_board_cache.py` | 两对象存在；`ALL_HTML_TEMPLATE` 与定稿 HTML 均存在，可扩为 change 流与切换壳 |
| TODO-3 | 修改 `cli/eo-board`、`tests/test_eo_board_cache.py` | 现有聚合概要卡模板、path/count/backlog/as-of 字段与静态测试均存在 |
| TODO-4 | 修改 `cli/eo-board`、`tests/test_eo_board_cache.py` | `AllBoardRequestHandler`、`BoardRequestHandler`、`render_html` 和每项目缓存槽存在；端点适配见 P1-3 |
| TODO-5 | 修改 `cli/eo-board`、`tests/test_eo_board_cache.py` | `render_all_html`、`cmd_all_html` 和内嵌 JSON 手法存在；快照 `serve=false` 时不启动 fetch 轮询 |
| TODO-6 | 修改 `tests/test_eo_board_cache.py` | 对象存在；已有空注册表、坏条目、终端输出、scan 组合与 argparse 矩阵覆盖可扩展 |

## 粒度检查

TODO 数：6（理想 3-7 / 硬上限 10）｜ 全文：87 行（软标 200-500 / 硬上限 700）｜ 结论：合规。

三个 Batch 都是纯数字串行批：Batch 1 先抬数据并交付可独立查看的 change 流 MVP，Batch 2 消费该数据完成第二视图与路由，Batch 3 做兼容性收口；没有并行后缀、文件交叉误标或依赖循环。该 change 改同一条聚合浏览链路，不属于 trivial，也没有混入第二个无关意图。

## 前提真实性抽查（维度 7）

| 断言 | 基线 | 证据 | 判定 |
|------|------|------|------|
| `/p/<注册名>` 可定位任意聚合项目，并沿用 `--project` 的同名拒绝语义 | `dfb1a6e` | `cli/eo_lib/registry.py:3-5,64-90` 允许同名合法共存；`cli/eo-board:2017-2035` 多命中只能拒绝；`cli/eo-board:1607-1654` 还纳入无注册名 scan 项目 | 不成立（P0-1） |
| 单项目泳道渲染和每项目缓存槽可供聚合 serve 复用 | `dfb1a6e` | `cli/eo-board:1426-1428` 的 `render_html` 消费完整 board data；`cli/eo-board:1459-1500` 按 config path 分槽并同槽单飞；`cli/eo-board:1629-1632` 聚合跨项目并行 | 成立；JSON 端点仍需 P1-3 钉定 |
| freshness 与现有 change 字段已足以直接产出逐 change 最近活动排序 | `dfb1a6e` | `cli/eo_lib/freshness.py:37-69` 确实覆盖 refs、change/backlog mtime；但 `cli/eo-board:77-92` 的 `last_touch` 有 commit 时忽略未提交 mtime且仅保留日期 | 证据不足（P1-1 补公式与测试） |

## 形态分叉与所采假设

- [x] 分叉：URL 使用原始注册名，还是使用唯一稳定键。采纳假设：显示名不变，route token 使用“可读名 + repo identity hash8”；原始名字不承担唯一性。
- [x] 分叉：`--scan` 临时项目只展示概要，还是也可下钻。采纳假设：也可下钻；既有 `--scan` 与三形态正交，AC-4 的“任意卡/行”不对扫描来源设例外。
- [x] 分叉：泳道页显式“返回首页”回默认视图还是记住来源视图。采纳假设：显式入口回默认 change 流；浏览器返回键按历史恢复用户进入前的 change 流/概要卡视图。

以上只作为本轮审查的裁决基线，未改写 change.md；起草方修订时应把采用的 route key 与返回语义写回 §5，避免 implement 自行选择另一形态。

## 结构完整性

| 节 | 状态 | 备注 |
|----|------|------|
| 速览 | 通过 | 双视图、下钻和快照差异与 §1/§2 一致 |
| §1 意图 + 已钉设计判断 | 警告 | 主方向一致；路由身份前提不成立，两个可见字段未闭环 |
| §2 验收清单 | 警告 | AC 本身总体可验；AC-4 依赖错误 route key，AC-9 无 TODO |
| §3 TODO（Batch） | 不通过 | AC-4 点击入口覆盖断裂，AC-9 悬空 |
| 条件节 §4-§8 | 警告 | §5 与 §8 已触发且 defer 仅 1 条；连带文档触发 §4 但缺失 |

## 速报

结论：不通过（P0 3 条）［第 1 轮 · 全量］

P0（阻塞 implement）：
1. `/p/<注册名>` 无法唯一覆盖同名注册项目和 `--scan` 未注册项目 — change.md AC-4、§5
2. AC-4 的项目条卡/change 行点击无 TODO 落点，概要卡点击映射错误 — change.md §3 TODO-2/3/4
3. 人工 AC-9 没有任何 TODO 覆盖 — change.md AC-9、§3

P1（移交起草方裁决，不阻塞循环）：
4. 逐 change 最近活动公式需钉定，不能直接复用现有日粒度 `last_touch` — change.md AC-1/6、§5
5. 非主 worktree 标记与项目目录应补入 AC/渲染判据 — change.md §1、AC-1/2、TODO-2
6. `/p/<项目>` 的单项目 JSON 端点需明确，避免误取聚合 `/data.json` — change.md §5、TODO-4
7. 连带用户文档、state 与 handbook 需在 §4/TODO 明确处置 — change.md 条件节、§3

P2（可后置）：
8. 无新增 P2。

下一步：回 `/eo-change eo-doc/changes/10-board-all-v2/change.md` 逐条处置：修复的在台账标注改动落点，不认同的标 wont-fix 附理由；然后再跑 `/eo-change-review` 复审（默认增量，锚变动自动升全量），循环到 **P0=0**。当前第 1/3 轮。🚫 不要跳过复审直接 implement，不要跑 /eo-review（代码还没写）。
