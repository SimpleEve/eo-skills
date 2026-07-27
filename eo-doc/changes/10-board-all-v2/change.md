---
id: board-all-v2
seq: 10
title: eo-board --all 聚合页 v2：change 流首页 + 双视图切换 + 路由式下钻
summary: 聚合首页升级 change 流与概要卡双视图切换，/p/<key> 稳定键路由下钻泳道页（含 --scan 项目），--html 单文件 hash 路由
status: implementing
tier: full
type: feature
base_commit: 5a0247f80534d30acc1ed59e5f629ed0e14e6275
plan_revision: 1
fix_rounds: 0
fix_consumed: []
commits: []
issue: ~
pr: ~
created: 2026-07-27
---

# eo-board --all 聚合页 v2：change 流首页 + 双视图切换 + 路由式下钻

## 速览

- **改什么**：多项目聚合页从「不可点概要卡」升级为「change 流 ⇄ 概要卡」双视图首页，任意卡/行点击即下钻该项目泳道页
- **为什么**：聚合页是日常主入口（eo-helper 选项 2），实际使用判定信息太少、点不开；change #8 OQ-1（下钻 defer）凭真实使用信号翻案
- **行为差异**：之前——聚合页每项目一张概要卡（计数+backlog+as-of），不可点，下钻要另记 `--project` 命令 → 之后——默认看到跨项目「进行中 change 流」（标题/状态/进度/门禁/动静一眼可见），顶部可切回概要卡视图；项目条卡、change 行、概要卡点击都直达该项目泳道页并可返回首页，同名项目与 `--scan` 临时并入的未注册项目同样可下钻；`--html` 快照单文件同能力
- **怎么验**：AC 9 条（人工 1 条）；挂 `eo-board --all --serve` 直接点

## 1. 意图

来源：brainstorm/2026-07-26-board-all聚合页改版与下钻.md 捕获出口（决策台账整体移交）；决策记录 decisions/2026-07-27-board-all-v2-route-drilldown.md（change #8 OQ-1 翻案后继裁决）。用户原话要点：现状「基本不可用」「点不开、信息太少」；「顶部的卡片还是需要包含一个做切换的位置……并不是说只有一个首页，其实是可以切换的」；「项目内部的这些甬道信息并没有被直接删掉……点进去依然可以看到项目内部的详情信息」。

已钉决策（来自 brainstorming 捕获 + 起草澄清，不重问）：

- 首页信息优先级 → 活跃项目与活跃 change 优先，活跃窗口 3 天（用户点名）
- 首页默认视图 → 变体 2「change 流为主角」：跨项目非 archived change 流按最近活动倒序 + 顶部项目摘要条卡；布局定稿 design/variant-2.html（对比稿三选一，用户拍板 2026-07-27）
- 旧概要卡处置 → **保留为首页第二视图**，页内切换（切换位置在顶部卡区，默认 change 流视图；非 CLI 旗标、非删除），概要卡升级为可点下钻（用户裁决 2026-07-27，破坏性变更协议问询结论）
- 下钻形态 → 路由式：聚合 serve 同进程 `/p/<key>` 复用单项目泳道渲染与缓存槽；`--html` 快照嵌全量数据 hash 路由同页切换，保持单文件自包含（OQ-1 翻案裁决）
- 路由标识 → `/p/<URL 编码可读名>~<repo 标识 hash8>`：显示名不承担唯一性，稳定键（route_key）承担；注册与 `--scan` 两类来源共用同一套机制（用户拍板 2026-07-27）
- `--scan` 临时并入的未注册项目同样可下钻，不对来源设例外（用户拍板 2026-07-27）
- 返回语义 → 泳道页页内「返回首页」回默认 change 流视图；浏览器返回键按历史恢复进入前视图（用户拍板 2026-07-27）
- change 行字段 → seq+slug、状态、tier·type 标签、summary（空回退标题）、TODO 进度条、AC 进度、非主 worktree 时 ⎇branch@worktree、门禁 blocker（有才显示）、最近动静徽标（用户点名 + 告警加料）
- 项目条卡/概要卡字段 → 名字、目录、主分支、worktree 数、五状态计数、backlog 数、as-of（用户点名）
- archived 明细不进流、不进卡内明细；归档计数仍可见（用户点名）
- 活跃判定 = 最近 commit 或 change/backlog 文件 mtime 复合信号，与 serve 缓存 freshness 键同源（假设 A1，用户未逐条确认）
- 「tag」= frontmatter tier·type，change 无独立 tag 字段（假设 A2）
- 非 archived change 全展示（含久未动 draft），3 天规则只管排序/降权不过滤（假设 A3）
- 宪法四条（只读/无 SSE/零第三方依赖/缓存换性能）、3 秒轮询、127.0.0.1、视觉沿用既有设计语言 → 全部不动（继承 decisions/2026-07-24-dashboard-deprecated-board-cli.md）

## 2. 验收清单

- [x] AC-1 用户跑 `eo-board --all --serve`，首页默认呈现跨项目「进行中 change 流」：全部非 archived change 按最近活动倒序，每行含项目徽标、seq+slug、状态、tier·type、summary（缺失时回退标题）、TODO 进度、AC 进度、门禁 blocker（仅有 blocker 的行出现）、非主 worktree 时 `⎇branch@worktree` 标记、最近动静徽标；3 天无动静的行降权区隔显示（验证：两注册项目下对照各自单项目泳道页核对行字段与排序）
- [x] AC-2 change 流视图顶部每注册项目一张摘要条卡：名字、目录、主分支、worktree 数、五状态计数、backlog 数、as-of；3 天无动静的项目条卡整体降饱和
- [ ] AC-3 首页顶部卡区有视图切换位置：change 流 ⇄ 概要卡两视图可切，默认 change 流，切换后刷新页面保持所在视图；概要卡视图信息面不低于现状（计数+backlog+as-of+路径）
- [ ] AC-4 项目条卡、change 行、概要卡点击均进入该项目泳道页，内容与单项目 `--serve` 一致；同名注册项目与 `--scan` 临时并入的未注册项目各自直达正确泳道页（路由稳定键区分，显示名不承担唯一性）；泳道页带「返回首页」入口回默认 change 流视图，浏览器返回键按历史恢复进入前视图；访问未知或失效路由时用户看到含回首页链接的指引页而非崩溃
- [ ] AC-5 用户跑 `eo-board --all --html [-o PATH]` 得到单个自包含文件：默认 change 流视图，可切概要卡视图，可进各项目泳道视图（hash 路由），全程零网络请求；`-o` 与缺省路径语义不变
- [ ] AC-6 serve 挂起时改动某项目一个 change 文件，3 秒轮询内该 change 行浮到流顶且动静徽标刷新；数据无变化的重复请求命中缓存，同项目并发请求只触发一次重扫（验证：`build_data` 调用计数断言——稳定键重复请求计数不增、同槽并发只增 1，沿用 change #8 AC-2 口径）
- [ ] AC-7 注册表为空时显示注册指引页；坏路径条目在其条卡/概要卡行内显示错误，其 change 不进流，其余项目不受影响不中断
- [ ] AC-8 终端 `eo-board --all` 输出不变；argparse 组合矩阵回归（`--all --project` 仍拒绝、`-o` 限 `--html`、`--port` 限 `--serve` 等正反例与 change #8 钉定一致）；用户文档（docs/cli-reference.md、docs/GUIDE.md）聚合页描述与新行为一致（双视图、可点下钻、`--scan` 项目并入）
- [ ] AC-9 首页两视图布局与密度过目：change 流视图对照定稿 design/variant-2.html、概要卡视图对照现状不劣化（人工:挂 `--all --serve` 切换两视图并下钻一次过目）

## 3. TODO

### Batch 1（MVP：数据抬升 + change 流视图）

- [x] TODO-1 聚合数据抬升：`build_all_data` rows 增列——每项目非 archived change 明细（id/seq/title/status/tier/type/summary/TODO 进度/AC 进度/gates blocker/branch/worktree_name/`activity_at`）与项目级主分支/目录/worktree 数/`activity_at`/route_key（activity_at 公式与 route_key 规则见 §5，3 天窗判定活跃）；单次运行与缓存槽两条 getter 路径产出一致（文件：修改: cli/eo-board、tests/test_eo_board_cache.py；对应 AC-1、AC-2、AC-6；完成判据：新增字段单测绿 + 两 getter 路径一致性断言绿 + 有 git 历史的 change 发生未提交编辑后 activity_at 前移并排到流顶 + 3 天边界两侧 fixture 断言绿）
- [x] TODO-2 首页壳与 change 流视图：按 design/variant-2.html 落地项目摘要条卡 + 跨项目 change 流 + 3 天降权分界 + blocker/动静徽标，项目条卡与 change 行绑定 route_key 链接下钻，并搭好双视图切换框架（默认 change 流；切换位置在顶部卡区）（文件：修改: cli/eo-board、tests/test_eo_board_cache.py；对应 AC-1、AC-2、AC-3、AC-4、AC-9；完成判据：AC-1/2/3——行字段（含非主 worktree `⎇` 标记）/条卡字段（含目录）/排序/降权/徽标静态断言绿，切换框架就位且默认视图正确；AC-4 分项——条卡与 change 行两个入口链接均命中对应项目 route 断言绿；AC-9 分项——change 流结构对照 variant-2 可自动核对面绿，人工观感留待用户验收不代勾）

### Batch 2（概要卡视图 + 路由下钻）

- [ ] TODO-3 概要卡视图并入切换框架：现有概要卡模板保留为第二视图，卡片升级为可点下钻（绑定 route_key 链接），视图状态经 hash 记忆（刷新保持）（文件：修改: cli/eo-board、tests/test_eo_board_cache.py；对应 AC-3、AC-4、AC-9；完成判据：AC-3——切换/记忆断言绿；AC-4 分项——概要卡点击命中对应项目 route 断言绿；AC-9 分项——概要卡信息面回归不劣化断言绿，人工观感留待用户验收不代勾）
- [ ] TODO-4 serve 路由 `/p/<route_key>`：serve 按当前 sources（注册 + `--scan`）重建 key→config 映射并分派 handler，复用单项目泳道渲染与缓存槽，单项目数据端点 `/p/<route_key>/data.json`（渲染函数注入 data URL），泳道页加返回聚合首页入口（仅聚合 serve 下渲染，指向 `/` 默认 change 流视图），未知/失效 key 返回指引页（文件：修改: cli/eo-board、tests/test_eo_board_cache.py；对应 AC-4、AC-6；完成判据：路由分派/返回入口/未知与失效 key 指引断言绿 + 同名双项目、scan 未注册项目、CJK 名、注册名与配置名不一致正反例绿 + 两项目并发轮询互不串数据且各走各自缓存槽、单飞计数断言绿）
- [ ] TODO-5 `--all --html` 快照 hash 路由：嵌首页双视图数据 + 全部项目完整泳道数据（含 `--scan` 并入项目），前端按 `#/`、`#/cards`、`#/p/<route_key>` 切视图（与 serve 同一套 route_key），零外部请求（文件：修改: cli/eo-board、tests/test_eo_board_cache.py；对应 AC-5）

### Batch 3（回归收口）

- [ ] TODO-6 异常路径、组合矩阵与文档收口：空注册表指引、坏条目行内隔离（不进流、不炸其他项目）、argparse 正反例、终端 `--all` 输出回归、零新第三方依赖与 127.0.0.1 绑定静态核对；用户文档聚合页段落更新至双视图/可点下钻/`--scan` 并入新口径（文件：修改: tests/test_eo_board_cache.py、docs/cli-reference.md、docs/GUIDE.md；对应 AC-7、AC-8）

## 4. 影响面

触发：改变日常主入口（eo-helper 选项 2）与 serve 路由面，连带文档需明确处置责任。

- **本 change 内更新**：docs/cli-reference.md（eo-board 节）、docs/GUIDE.md（聚合页段落）——Batch 3 TODO-6 落地，AC-8 覆盖口径一致性
- **归档时 doc-manager sync 更新**（以代码为信源，本 change 不动）：eo-doc/state/eo-board-cli.md、eo-doc/agent-handbook/cli-eo-board.md。所需最终口径：serve 路由表为 `/`（双视图首页）+ `/p/<route_key>` 泳道页 + `/data.json` 聚合数据 + `/p/<route_key>/data.json` 单项目数据；`--html` 快照 hash 路由三态（`#/`、`#/cards`、`#/p/<route_key>`）；route_key = URL 编码可读名~repo 标识 hash8，注册与 `--scan` 来源共用

## 5. 技术方案

触发：serve 从单页升级为多路由（新架构模式），编码前钉方向。

- **路由标识（已钉）**：route_key = `<URL 编码可读名>~<repo 标识 hash8>`，hash8 取项目根目录 canonical 绝对路径的 hash 前 8 位（覆盖无 remote 的 `--scan` 项目；显示名改名不破坏同批次内定位）。显示名不承担唯一性——同名项目、注册名与配置名不一致、CJK 名均由稳定键区分，无需沿用 `--project` 的重名拒绝语义。serve 每次按当前 sources（注册表 + `--scan`）重建 key→config 映射；快照嵌同一套 key
- **路由表（serve）**：`/` 首页壳（change 流 + 概要卡双视图，hash 管视图态）；`/p/<route_key>` 单项目泳道页（复用既有单项目模板 + 返回入口注入，返回指向 `/` 默认 change 流视图，浏览器返回键按历史恢复）；`/data.json` 聚合数据（rows 已抬升 change 明细）；`/p/<route_key>/data.json` 单项目数据——渲染函数注入 data URL，替代单项目模板硬编码的 `fetch('/data.json')`，两项目并发轮询互不串数据；未知/失效 key → 含回首页链接的指引页
- **缓存零新机制**：聚合与泳道页共用 `get_board_data_cached` 每项目槽（同槽单飞、跨槽并行）；聚合层不加第二层缓存
- **快照（--html）**：`build_all_data` + 各项目完整 `build_data` 一次性嵌入，前端 hash 路由切视图；数据体量小（本机项目数量级），单文件自包含
- **活跃判定（公式已钉）**：`change.activity_at = max(该 change 目录最后 commit 时间, 该目录内文件 max-mtime)`；`project.activity_at = max(各 worktree HEAD commit 时间, changes/backlog 数据源 max-mtime)`；统一为带时区的秒级时间，3 天边界按同一时区计算。排序键用 activity_at，**不复用**现有日粒度 `last_touch`（其有 commit 历史时忽略未提交 mtime，无法满足编辑后 3 秒浮顶）；信号源与 freshness 键同源，行/卡降权只是渲染分支
- **宪法核对**：只读 ✓；零第三方依赖（stdlib + 内嵌 JS）✓；仅绑 127.0.0.1 ✓；无 SSE，沿用 3 秒轮询 hash 比对 ✓；旧概要卡模板保留为视图分支，无参数面新增

## 8. 开放问题

- OQ-1 change 行点击是否锚定滚动到泳道页对应卡片（defer 原因：锚点定位成本待实现时评估，先保证行点击直达该项目泳道页）
