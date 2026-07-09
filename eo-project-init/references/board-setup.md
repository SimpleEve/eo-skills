# Obsidian 看板配置（starter 自动生成 + 数据层备忘）

> 数据层（`<project_root>/board/` 的 stub 卡片）由各流程 skill 自动维护；呈现层的 **starter 看板由 skill 自动创建**（本文件含模板）。

## starter 看板（skill 自动创建）

开启 board 时，若 `<vault_root>/eo-project-board.base` **不存在**则按下方模板创建；**已存在绝不触碰**——用户在 Obsidian UI 的一切调整（视图增删、列序、颜色等）由 Obsidian 写回该文件。

```yaml
filters:
  and:
    - file.hasTag("eo-change")
    - file.path.contains("/board/")
views:
  - type: kanban-view
    name: 看板（按状态分组）
    groupBy:
      property: status
      direction: ASC
    groupByProperty: note.status
    order:
      - file.name
      - title
      - project
      - type
      - tags
      - todo_done
      - todo_total
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

- 过滤器 = `eo-change` 标签 **且** 路径含 `/board/`——双条件对 vault 里偶然出现的行内 `#eo-change` hashtag 免疫；全 vault 聚合，多项目 board/ 卡片进同一看板
- 主视图 `kanban-view` 来自社区插件 **Kanban Bases View**（设置 → 第三方插件安装启用；并排状态列 + 泳道）。**未装插件时**该视图显示不可用——在 UI 把视图类型换成官方 `cards`（同样支持按 status 分组）即可，或装上插件
- 模板只含插件的最小稳定键；columnOrders / cardOrders / columnColors 等机器状态由插件运行时自行写回，skill 不生成
- 文件放 vault 根，可在 Obsidian 里拖到任意位置

## 数据层备忘

stub 卡片是 change frontmatter 的投影（`id / title / project / status / type / todo_done / todo_total / issue / pr / updated / tags: [eo-change, …]`），可随时全量重建，**不要手工编辑**（会被覆盖）；正文中的 change 路径是纯文本（vault 外路径不可链接，复制到 IDE 打开）。看板数据丢失/错乱 → 重跑 `/eo-project-init`（更新分支）触发历史同步重建。
