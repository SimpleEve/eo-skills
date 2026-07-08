# Obsidian 看板配置指南（一次性，人工操作）

> `board.enabled` 开启后，各流程 skill 会向 `<project_root>/board/` 维护 stub 卡片（数据层，自动）。**呈现层由你在 Obsidian 里配置一次**——skill 永不写 `.base` 文件（社区插件的 YAML 键名随版本变动，由 Obsidian UI 写回最稳）。

## 数据层（skill 自动维护，无需操作）

每个 change 一张 stub 卡片：`board/<change-id>.md`，frontmatter 含 `id / title / project / status / type / todo_done / todo_total / issue / pr / updated / tags: [eo-change]`。stub 是 change.md 的投影，可随时全量重建，**不要手工编辑**（会被覆盖）。

## 呈现层（你配置一次）

1. **装插件**：社区插件市场安装 **Kanban Bases View**（为官方 Bases 提供并排列看板视图；官方 kanban 视图发布后可把视图 type 一换切官方，数据零迁移）
2. **建 .base**：在 vault 任意位置（建议 `00-Wiki/` 或项目目录）新建 Base，用 UI 配置：
   - **Filter**：`tags contains eo-change`（多项目聚合天然生效——所有项目的 board/ 目录都会被扫到；要单项目就再加 `project == <项目名>`）
   - **视图 1（主）**：type 选 Kanban Bases View，group by `status`（列序：draft → confirmed → implementing → done → archived），卡片属性显示 `project / type / todo_done / todo_total`
   - **视图 2（退路）**：官方 Cards，group by `status`
   - **视图 3（盘点）**：官方 Table，列 `id / project / status / todo_done / todo_total / updated`，按 `updated` 倒序
3. **泳道（可选）**：Kanban Bases View 支持二维分组——按 `project` 做泳道，多项目一屏观测
4. 配好后不要手工改 `.base` 的 YAML；调整一律走 Obsidian UI

## 提示

- stub 卡片正文带 change.md 引用，点卡片可跳到工件
- `issue` / `pr` 字段有值时卡片可直达 GitHub
- 看板数据丢失/错乱 → 重跑 `/eo-project-init`（更新分支）触发历史同步全量重建
