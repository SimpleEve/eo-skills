# Obsidian 看板配置（starter 自动生成 + 可选升级）

> 数据层（`<project_root>/board/` 的 stub 卡片）由各流程 skill 自动维护；呈现层的 **starter 看板由 skill 自动创建**（本文件含模板），只有「并排列 kanban 视图」这一项可选升级需要用户在 UI 点几下。

## starter 看板（skill 自动创建）

开启 board 时，若 `<vault_root>/eo-change-board.base` 不存在，按下方模板创建（**仅官方 Bases 语法**——table/cards 是 Obsidian 1.9+ 内置视图，无插件依赖；文件存在则绝不触碰，用户在 UI 的调整由 Obsidian 写回）：

```yaml
filters:
  and:
    - file.hasTag("eo-change")
views:
  - type: cards
    name: 看板（按状态分组）
    order:
      - file.name
      - project
      - type
      - todo_done
      - todo_total
    groupBy:
      property: status
      direction: ASC
  - type: table
    name: 盘点
    order:
      - file.name
      - project
      - status
      - type
      - todo_done
      - todo_total
      - updated
```

- 过滤锚点是 stub frontmatter 的 `eo-change` 标签——**全 vault 聚合**，多项目的 board/ 卡片自动进同一看板
- 文件放 vault 根，用户可在 Obsidian 里拖到任意位置（不影响功能）
- cards 按 `status` 分组是「纵向分节」的准看板；分组顺序为字母序（官方限制）

## 可选升级：并排列 kanban 视图（用户 UI 操作，一次性）

1. 设置 → 第三方插件 → 浏览 → 安装并启用 **Kanban Bases View**（为官方 Bases 提供并排状态列视图；官方 kanban 视图发布后可把视图类型一换切官方，数据零迁移）
2. 打开 `eo-change-board.base` → 添加视图 → 类型选 Kanban Bases View → Group by `status`，卡片属性勾 `project` / `type` / `todo_done` / `todo_total`；多项目泳道设 `project`
3. 社区插件的 YAML 键名随版本变动——这一步**只在 UI 配置**，由 Obsidian 写回文件，skill 不代写

## 数据层备忘

stub 卡片是 change frontmatter 的投影（`id / title / project / status / type / todo_done / todo_total / issue / pr / updated / tags: [eo-change, …]`），可随时全量重建，**不要手工编辑**（会被覆盖）；正文中的 change 路径是纯文本（vault 外路径不可链接，复制到 IDE 打开）。看板数据丢失/错乱 → 重跑 `/eo-project-init`（更新分支）触发历史同步重建。
