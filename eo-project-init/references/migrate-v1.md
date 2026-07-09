# v1 项目迁移子流程（由 1.5 更新/修复分支触发）

> 检测到 v1 痕迹时执行。全程**幂等**、逐项汇报；除明确列出的写入外不动任何存量内容。人类背景版见仓库 docs/migration-v1-to-v2.md（本文件是可执行版，两者以本文件为准）。

## 触发信号（任一命中即进入本流程）

- `eo-doc/dev/` 目录存在（v1 模块维度）
- `.eo-project.json` 的 `kanban_path` 为非 null 字符串
- `<project_root>/log.md` 存在且 `eo-doc/changes/` 不存在

## 迁移步骤

1. **冻结存量 spec**：对每个 `eo-doc/dev/<module>/spec.md` 与 `spec-history.md`，frontmatter 补 `status: frozen`（已有则跳过）。它们保留作历史参考，v2 任何 skill 不再读写。
2. **建项目级 changes/**：`eo-doc/changes/INDEX.md` 不存在则创建；起始编号 = 扫描全部 `dev/*/changes/` 取最大 `NNN` + 1；INDEX 顶部加一行注记「NNN 号之前的历史 change 见 `dev/<module>/changes/`（v1 存量，原地保留）」。
3. **在途 change 盘点**：列出旧目录里 status 非 archived 的 change，逐个告知：「走完余下生命周期即可（implement/test/review 照旧），**归档按 v2 执行**——不合并 Delta，直接结算 commit + 触发 sync + 冻结」。不迁移文件位置。
4. **kanban 退役**：`kanban_path` 非 null → 改写为 `null`，提示「旧手工看板已退役，看板文件（如 00-Wiki/项目看板.md 中本项目条目）可自行归档删除；项目级总览改由 Bases 聚合 roadmap frontmatter」。
5. **roadmap frontmatter 补齐**：`roadmap.md` 缺 `status` / `phase` / `summary` 字段的，从正文推断补写（推断不出的问一次）；`status` 枚举 `active | researching | paused | done`。
6. **log.md 处置**：存在则提示「v2 不再写入 log.md，时间线由 changes/INDEX + git log 承担；文件可留存或归档」，不删除。
7. **lessons 存量**：`lessons/` 有文件但无 INDEX.md → 提示「跑 `/eo-project-record` 的 reindex 补建检索锚点与索引」；decisions/ 同理。
8. **backlog 打散**：存在旧扁平 `backlog.md`（或 backlog/todo.md 等）→ 按 /eo-backlog 的 migrate 动作把未完成条目打散成卡片（created 取原日期、行内 #tag 转 tags），已完成/放弃条目留存原文件，原文件顶部标注「已迁移」。
9. **首次 sync 提示**：若 `eo-doc/state/` 不存在，迁移汇报末尾建议「跑 `/eo-doc-manager sync` 生成首批活文档——此后 state + agent-handbook 就是『系统现在是什么样』的唯一口径」。

## 收尾

汇报迁移清单（冻结 N 个 spec / changes 起始编号 / 在途 change 数 / kanban 状态 / roadmap 补了什么），然后**继续 1.5 分支的常规步骤**（配置校验、骨架补齐、注入刷新、gitignore 与软链核对、联动两问）。
