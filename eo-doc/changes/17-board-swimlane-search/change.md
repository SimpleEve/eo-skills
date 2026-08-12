---
id: board-swimlane-search
seq: 17
title: 泳道页定位搜索与列显隐
summary: 泳道页新增 Cmd+K 定位搜索（#seq 直跳、全文命中片段）、列内独立滚动、列折叠隐藏并持久记忆
status: archived
tier: full
type: feature
base_commit: 4fd2a2a6a46b23a2b80a48721db01cc73d08241a
plan_revision: 1
fix_rounds: 0
fix_consumed: []
commits: ["16c9d89", "be83265", "abb715a", "f78ef8b", "69380cb", "0e7d75e", "a62ef3c", "d7c6d32"]
issue: ~
pr: ~
created: 2026-08-12
---

# 泳道页定位搜索与列显隐

## 速览

- **改什么**：泳道页加键盘唤出的搜索面板（关键词搜标题+正文、`#21` 按编号直跳、选中后定位高亮）；每条泳道改为列内独立滚动；列头加隐藏按钮，低关注列（如 backlog）可折叠成窄条且刷新后保持。
- **为什么**：change 多了以后只能靠肉眼扫列；backlog 列常占屏但不一定关心。brainstorming 裁决搜索动机是「定位」而非「扫全景」，故用面板而非就地过滤。
- **行为差异**：之前找一条 change 要逐列扫卡 → 之后按 `/` 或 Cmd+K 输入关键词或 `#编号` 直达；之前整页滚动、长列看不到列头 → 之后页面定格、列内滚动、列头吸顶；之前 backlog 列永远占一列宽 → 之后可收成窄条。
- **怎么验**：AC 8 条（人工 1 条）；在泳道页键盘唤起面板各语法试一遍，折叠列后刷新页面。

## 1. 意图

泳道页缺定位手段与版面自主权。brainstorming（`brainstorm/2026-08-12-board全局dashboard化与泳道易用性.md`）钉下：搜索作用域仅下钻（单项目）页内，形态为 Cmd+K 定位面板；泳道列内滚动；列可折叠隐藏。本 change 是纯视图层增强，全部落在 PROJECT_CSS / PROJECT_MARKUP / PROJECT_JS 一套资产内，数据层零改动（`full_text` 已随 attach_card_progress 嵌入页面 DATA，纯客户端搜索，不违只读铁律与零依赖约束）。

已钉决策（来自 brainstorming 捕获，不重复提问）：
- 搜索作用域 → 仅下钻泳道页内，不做全局 home 搜索（用户裁决「暂时只考虑单项目搜索」；翻案条件：日后出现跨项目检索诉求）
- 搜索形态 → Cmd+K 面板定位（`#seq` 直跳、全文匹配、结果按泳道分组、命中片段预览），选中后 dim 其他卡并滚动高亮；不做就地过滤（理由：用户动机全是「定位」）
- 唤起方式 → Cmd+K（mac）/ Ctrl+K 与 `/` 双快捷键，Esc 关闭
- 搜索范围 → change 卡（标题/summary/全文）+ backlog 卡（标题/正文）（假设，用户未逐条确认）
- 泳道滚动 → 列内独立滚动，列头 sticky，列尾 col-note 随内容滚
- 列隐藏 → 列头眼睛图标折叠为窄条（显示列名+计数），localStorage 按项目记忆（键含项目路由键）（理由：隐藏是布局偏好而非检索，折叠窄条最「随手」）
- 定位到折叠列中的卡 → 该列自动展开并完成高亮，展开状态随之持久（假设，用户未逐条确认）
- 语法扩展（`is:blocked` / `is:stale` / `status:` 前缀）→ 不进本 change，记 backlog（不镀金）

## 2. 验收清单

- [x] AC-1 在泳道页按 Cmd+K（mac）/ Ctrl+K 或 `/` 唤出搜索面板，Esc 或点击面板外关闭；输入焦点在输入框时 `/` 不误触发（验证：三种唤起与各关闭路径各试一次）
- [x] AC-2 输入关键词，结果按泳道分组列出；标题、summary 与正文（AC/TODO/全文）命中都出结果，正文命中显示带命中词上下文的片段（验证：搜一个只出现在某 change TODO 正文里的词）
- [x] AC-3 输入 `#21` 时结果为 seq=21 的那条 change，回车直达；编号不存在时显示无匹配空态，不报错
- [x] AC-4 选中结果后面板关闭，目标卡滚动进可视区并高亮脉冲，其他卡降透明度；点击空白处或 Esc 恢复常态
- [x] AC-5 关键词无匹配时面板显示空态提示；backlog 卡的标题/正文同样可被搜到
- [x] AC-6 某列内容超高时列内滚动、页面整体不滚（含底部 `.prov` 数据来源说明区：迁入可折叠入口，默认收起，展开不引起页面纵向滚动），列头在列内吸顶始终可见（人工:把进行中列塞到超高 → 过目列头与滚动手感；展开说明区过目）——确认：「滚动部分没问题」，2026-08-12，基线 a62ef3c（于 http://127.0.0.1:7335 新代码 serve 过目）
- [x] AC-7 点列头隐藏图标，该列折叠为只显示列名与计数的窄条；刷新页面（含 serve 3 秒热刷新）后折叠状态保持；再点窄条展开还原
- [x] AC-8 搜索定位到折叠列中的卡时，该列自动展开并正常滚动高亮（验证：折叠 backlog 后搜一张 backlog 卡并选中）

## 3. TODO

### Batch 1（MVP：版面——滚动与折叠）
- [x] TODO-1 泳道布局改列内滚动：board 区填满视口剩余高度，列头 sticky，列尾 col-note 随内容；页面整体不滚——`.prov` 数据来源说明区迁入可折叠入口（默认收起，展开不撑出页面滚动）（文件：修改: cli/eo-board；对应 AC-6）
- [x] TODO-2 列折叠/展开：列头眼睛图标、窄条态（列名+计数）、localStorage 按项目键持久、热刷新后状态恢复（文件：修改: cli/eo-board；对应 AC-7）

### Batch 2（搜索面板）
- [x] TODO-3 搜索面板 UI 与键盘交互：面板/结果列表样式，Cmd/Ctrl+K 与 `/` 唤起（输入框聚焦态豁免）、Esc/点外关闭（文件：修改: cli/eo-board；对应 AC-1、AC-5；完成判据：面板可消费零结果并呈现空态容器/文案；快捷键/点外监听只在组件 mounted 期间存在，unmount 完整解绑；Escape 按「搜索面板→详情抽屉→定位态」的已打开层级逐层消费）
- [x] TODO-4 匹配逻辑：title/summary/full_text 与 backlog 卡的不区分大小写子串匹配、`#<num>` seq 精确语法、按泳道分组、正文命中截取片段（文件：修改: cli/eo-board；对应 AC-2、AC-3、AC-5；完成判据：无命中返回空结果；backlog 的 title/body 命中进入对应泳道分组）
- [x] TODO-5 选中定位：关闭面板、目标卡 scrollIntoView + 高亮脉冲 + 他卡 dim、Esc/点空白恢复、折叠列自动展开并持久（文件：修改: cli/eo-board；对应 AC-4、AC-8；完成判据：`buildBoard` 热刷新重建 DOM 后显式清除整套定位态（dim/highlight/滚动位置标记），不允许只残留一半状态）

## 4. 涉及文件

- `tests/test_eo_board_cache.py`、`tests/test_board_card_progress.py` — /eo-test 交接清单（测试资产唯一写入者）：快捷键与 unmount 解绑、关键词/`#seq`/空态、backlog body 命中、折叠按项目记忆、折叠列定位自动展开、serve 热刷新后定位态清除、快照/serve 共用资产；现有 fake DOM 垫片按需适配

## 8. 开放问题

- OQ-1 搜索语法扩展（`is:blocked` / `is:stale` / `status:` 前缀）记 backlog 排队，不进本 change（defer 原因：brainstorming 裁决不镀金）
