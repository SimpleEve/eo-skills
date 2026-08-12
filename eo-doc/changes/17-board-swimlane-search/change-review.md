---
title: 泳道页定位搜索与列显隐 Change 审查报告
change_id: board-swimlane-search
created: 2026-08-12
status: active
summary: >
  首轮全量审查未发现 P0；AC 与 TODO 映射闭合，4 项当前基线适配与拆解建议移交起草方裁决。
---

# 泳道页定位搜索与列显隐 Change 审查报告

> 关联：[change.md](change.md) ｜ 审查日期：2026-08-12 ｜ change status：confirmed

## 审查总结

方案与已冻结的「单项目定位面板 + 列内滚动 + 列折叠」方向一致，8 条 AC 均可独立验证，5 条 TODO 对 AC-1～AC-8 的正反向映射闭合，也没有占位符或粒度硬超限。按用户要求以 #16 归档后的 HEAD `4fd2a2a6a46b23a2b80a48721db01cc73d08241a` 核验：`PROJECT_CSS / PROJECT_MARKUP / PROJECT_JS` 仍是快照与 serve 共用的泳道资产，change 的 `full_text`、backlog 的 `body` 及标题/summary/seq 已在页面 DATA 中，纯客户端搜索与数据层零改动前提成立；但现有说明区与「页面整体不滚」尚未闭环，多 TODO 共担 AC-5 缺分项完成判据，且 #16 新增的挂载/热刷新生命周期与测试资产交接未写入计划。结论：✅ P0=0，可进入 implement；4 条 P1 不阻塞，由起草方裁决。

## Finding 台账

<!-- 状态单一来源：本 skill 建条与核销（open→verified），修订方（/eo-change）填「处置」列。wont-fix 项后续任何轮次不得重报 -->

| ID | 级别 | 摘要 | 位置 | 状态 | 处置（修订方填） |
|----|------|------|------|------|------------------|
| P1-1 | P1 | 「页面整体不滚」未交代现有 `.prov` 说明区的可达方式 | §2 AC-6、§3 TODO-1 | fixed | 采纳口径 a：AC-6 维持「页面整体不滚」，TODO-1 增写 `.prov` 迁入折叠入口（默认收起、展开不撑出滚动） |
| P1-2 | P1 | TODO-3/4 共担 AC-5，但缺各自完成判据 | §3 TODO-3、TODO-4 | fixed | TODO-3 补空态容器判据；TODO-4 补空结果 + backlog 分组判据 |
| P1-3 | P1 | 搜索交互未显式衔接当前 `mount/unmount` 与热刷新重建生命周期 | §3 TODO-3～TODO-5 | fixed | TODO-3 补监听解绑 + Escape 分层判据；TODO-5 选定「热刷新后显式清除整套定位态」策略 |
| P1-4 | P1 | 新交互缺 `/eo-test` 测试资产交接清单 | 条件节 §4（缺失） | fixed | 新增 §4 交接清单（两测试文件 + 覆盖点枚举），不新增 implement TODO |

## P0 - 必须修订（阻塞 implement）

无。

## P1 - 建议修订（移交起草方裁决，不阻塞）

### [P1-1] 页面定格与现有说明区未闭环（类型：当前基线适配）

- 位置：change.md §2 AC-6、§3 TODO-1
- 描述：AC-6 要求「页面整体不滚」，TODO-1 只写 board 区填满视口剩余高度。当前 `PROJECT_MARKUP` 在 `.board-scroll` 后仍有整块 `.prov` 数据来源说明区，`.wrap` 也保留 64px 底部空间；若实现通过锁住页面纵向滚动来满足 AC，说明区可能变得不可达；若继续允许页面滚动，则 AC 的字面判据无法通过。
- 建议：起草方在 AC-6/TODO-1 选择并写明一种可观察口径：a) 页面只固定 board 工作区，说明区迁入可独立打开的折叠/抽屉入口；或 b) 保留说明区的页面滚动，但把 AC 收窄为「board 区不随列内容增高，卡片只在列内滚动」。如坚持整个页面不滚，TODO-1 必须同时写明 `.prov` 的迁移或可达方式。

### [P1-2] AC-5 的多 TODO 分工缺完成判据（类型：TODO 拆解质量）

- 位置：change.md §3 TODO-3、TODO-4
- 描述：TODO-3 与 TODO-4 都映射 AC-5，前者负责面板/空态呈现，后者负责匹配与 backlog 数据消费；任一 TODO 单独完成都不能证明 AC-5 已达成。粒度规范要求多条 TODO 共担同一 AC 时逐条写完成判据。
- 建议：给 TODO-3 增补「完成判据：面板可消费零结果并呈现空态容器/文案」；给 TODO-4 增补「完成判据：无命中返回空结果，backlog 的 title/body 命中进入对应泳道分组」。保持验证操作只写在 AC-5，不在 TODO 重复验收步骤。

### [P1-3] 搜索状态未衔接 #16 后的视图生命周期（类型：当前基线适配）

- 位置：change.md §3 TODO-3～TODO-5
- 描述：#16 后泳道组件会在静态 hash 路由切换时反复 `mount/unmount`，当前 `mount` 已注册抽屉 Escape 监听并由 `unmount` 移除；serve 的 `refreshLoop` 还会每次用 `buildHeader/buildBoard` 重建卡片 DOM。TODO-3 只写新增快捷键，TODO-5 只写定位类，没有说明监听器清理、Escape 优先级，以及热刷新重建后如何收口搜索/高亮瞬时状态，存在重复监听或残留 dim/highlight 状态的实现分叉。
- 建议：在 TODO-3 增补完成判据「快捷键/点外监听只在组件 mounted 期间存在，unmount 完整解绑；Escape 按搜索面板→详情抽屉→定位态的已打开层级消费」；在 TODO-5 增补完成判据「`buildBoard` 热刷新后按稳定 card key 恢复仍存在的定位态，或显式清除整套定位态，不允许只残留 dim/highlight 的一半状态」。两种刷新策略均不改变已钉功能范围，由起草方选定一种即可。

### [P1-4] 测试资产连带面未交接（类型：条件节缺失）

- 位置：change.md 条件节 §4（缺失）
- 描述：当前共享泳道挂载、热刷新、详情 tab 与项目下拉已有 DOM/Node 测试基线；本 change 新增全局键盘监听、localStorage、列 DOM 重建和搜索定位，既可能要求现有 fake DOM 垫片适配，也需要持久验证资产覆盖两种页面形态。§3 没有也不应让 implement 写测试资产，但方案未给 `/eo-test` 留交接清单。
- 建议：新增 §4，仅列测试责任而不新增 implement TODO：由 `/eo-test` 审计并按需适配 `tests/test_eo_board_cache.py`、`tests/test_board_card_progress.py`，至少覆盖快捷键与卸载解绑、关键词/`#seq`/空态、backlog body、折叠按项目记忆、折叠列定位自动展开、serve 热刷新，以及快照/serve 共用资产；测试文件写入仍归 `/eo-test`。

## P2 - 可选优化

无。

## AC 质量检查

| AC | 用户视角 | 可验证 | 技术无关 | 备注 |
|----|---------|--------|---------|------|
| AC-1 | ✅ | ✅ | ✅ | 三种唤起与两类关闭路径明确，含输入焦点边界 |
| AC-2 | ✅ | ✅ | ✅ | 标题、summary、正文与命中片段均可观察 |
| AC-3 | ✅ | ✅ | ✅ | 覆盖精确编号与不存在编号空态 |
| AC-4 | ✅ | ✅ | ✅ | 定位、高亮、他卡降权与恢复路径明确 |
| AC-5 | ✅ | ✅ | ✅ | 覆盖普通无匹配与 backlog 搜索；TODO 分工见 P1-2 |
| AC-6 | ✅ | ✅ | ✅ | 人工项标注正确；现有说明区如何保留可达见 P1-1 |
| AC-7 | ✅ | ✅ | ✅ | 折叠形态、刷新保持与反向展开均可观察 |
| AC-8 | ✅ | ✅ | ✅ | 覆盖定位命中折叠列的组合边界 |

异常/边界覆盖：AC-3 覆盖不存在的 seq，AC-5 覆盖关键词零结果，AC-8 覆盖折叠列命中组合；满足至少一条失败/边界 AC 的要求。

## TODO↔AC 映射检查

| TODO | 对应 AC | 状态 |
|------|---------|------|
| TODO-1 | AC-6 | ✅ 映射成立；当前说明区布局闭环见 P1-1 |
| TODO-2 | AC-7 | ✅ |
| TODO-3 | AC-1、AC-5 | ⚠️ 映射成立；与 TODO-4 共担 AC-5 时缺完成判据（P1-2） |
| TODO-4 | AC-2、AC-3、AC-5 | ⚠️ 映射成立；与 TODO-3 共担 AC-5 时缺完成判据（P1-2） |
| TODO-5 | AC-4、AC-8 | ✅ |

反向覆盖：AC-1→TODO-3，AC-2/3→TODO-4，AC-4→TODO-5，AC-5→TODO-3/4，AC-6→TODO-1，AC-7→TODO-2，AC-8→TODO-5；无悬空 AC、越界 TODO 或占位符。

## 粒度检查

TODO 数：5（软标 3-7 / 硬标 10）｜ 全文：66 行（软标 200-500 / 硬标 700）｜ 结论：合规。

两个 Batch 都是纯数字串行批，且共同修改 `cli/eo-board`，没有误标并行组。Batch 1 可独立交付并验证列滚动/折叠版面能力，Batch 2 在稳定版面上交付搜索定位；依赖方向自洽。该 change 改变用户可见交互、包含持久布局偏好与多种组合边界，不属于 trivial；`type: feature` 与新增定位搜索能力相符。

## 前提真实性抽查（维度 7）

首轮 `base_commit` 为空，按技能规则及任务指定以审查时 HEAD `4fd2a2a6a46b23a2b80a48721db01cc73d08241a` 为变更前基线。工作区另有用户在途的 `cli/eo-board` 未提交改动，本表统一使用 `git show HEAD:cli/eo-board` 取证，未把在途改动当作 #17 自证。

| 断言 | 基线 | 证据 | 判定 |
|------|------|------|------|
| TODO-1～TODO-5 的修改对象存在，泳道仍由一套 `PROJECT_CSS / PROJECT_MARKUP / PROJECT_JS` 资产渲染 | base_commit（HEAD） | `cli/eo-board:1008`、`:1399`、`:1456` 定义三块共享资产；`:2608-2615` 给快照泳道注入项目下拉数据；`:3361-3362` 的 serve 项目页仍走 `render_html` | ✅ 成立 |
| 纯客户端搜索所需 change 标题、summary、seq、全文及 backlog 标题/正文均已在页面 DATA，不需数据层扩面 | base_commit（HEAD） | `cli/eo-board:679-686` 注入 `full_text`；`:728-748` 保留 backlog `title/body`；`:840-898` 汇入 `changes/backlog`；`:2001-2008` 消费 change `seq/title/summary` | ✅ 成立 |
| localStorage 可按当前项目的稳定路由键隔离折叠偏好 | HEAD（#16 后兼容性） | `cli/eo-board:2027-2052` 从 `DATA.dashboard_projects` 渲染当前项目下拉；`:2608-2615` 的快照项和 `:3367-3369` 的 serve 项均以 route key 构造 href 并标记 current | ✅ 成立；无需改数据层，可从 current 项稳定取得键 |
| 新搜索交互可直接叠加到旧的单次页面脚本生命周期 | HEAD（#16 后兼容性） | `cli/eo-board:2198-2210` 热刷新重建 header/board；`:2216-2239` 明确 mount 注册、unmount 解绑 Escape 监听 | ⚠️ 需在 TODO 中明确生命周期适配（P1-3） |

## 结构完整性

| 节 | 状态 | 备注 |
|----|------|------|
| 速览 | ✅ | 用户可见差异与 §1/§2 一致，不是逐条复述 AC |
| §1 意图 + 已钉设计判断 | ✅ | 单项目定位、不做全局搜索、列内滚动、列折叠与不镀金边界自洽 |
| §2 验收清单 | ⚠️ | 8 条均可验证；AC-6 与现有说明区的口径需补闭环（P1-1） |
| §3 TODO（Batch） | ⚠️ | 映射完整且粒度合规；AC-5 完成判据与现生命周期适配需写实（P1-2/P1-3） |
| 条件节 §4-§8 | ⚠️ | 无新依赖、不可逆操作或流程图触发；§8 defer 仅 1 条合规，缺 `/eo-test` 连带交接（P1-4） |

## 审查边界记录

- A 类判断：当前 HEAD 适配、TODO 完成判据、测试资产交接与条件节判断均在方案审查权限内，已随台账交付。
- B/C 类判断：未发现需要扩张范围、推翻已钉模式选择或执行不可逆操作的事项，本轮未触发 decision gate。
- 本报告只评审方案并做前提取证；未审实施质量，未修改 `change.md`、业务代码或测试资产。

## 速报

结论：通过（P0 0 条）［第 1 轮 · 全量］

P0（阻塞 implement）：
1. 无。

P1（移交起草方裁决，不阻塞循环）：
2. P1-1 页面定格未交代现有 `.prov` 说明区可达方式 — change.md §2 AC-6、§3 TODO-1。
3. P1-2 TODO-3/4 共担 AC-5 但缺分项完成判据 — change.md §3。
4. P1-3 搜索交互未显式衔接当前挂载、卸载与热刷新生命周期 — change.md §3 TODO-3～TODO-5。
5. P1-4 缺 `/eo-test` 测试资产交接清单 — change.md 条件节 §4。

P2（可后置）：
6. 无。

下一步 `/eo-implement eo-doc/changes/17-board-swimlane-search/change.md`（status 若仍为 draft，先回 /eo-change 对话确认）。未决 P1 已入台账，由起草方裁决：采纳的回 /eo-change 顺手修（不触发复审），不采纳的标 wont-fix 附理由。注意：`/eo-review` 是代码审查，要在 implement 之后，现在还不轮到它。
