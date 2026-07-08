---
name: eo-project-lesson
description: "捕获项目经验教训（踩坑、最佳实践、意外收获），写入当前项目的 lessons/ 目录并维护 INDEX。通过 .eo-project.json 定位。触发（仅用户明确要求记录时）：把这个坑记下来 / 记条经验 / lesson learned / reindex lessons / /eo-project-lesson。NOT FOR: 对话提到踩坑但用户未要求记录。"
---

# eo-project-lesson

## 功能

捕获项目经验教训，写入**项目级** `lessons/` 目录（每个项目独立，不再有全局 `_lessons/`）。若项目有看板，同步更新经验教训计数。

配置与目录约定见 [eo-project-init/references/config.md](../eo-project-init/references/config.md)。

## 前置

必须能找到 `.eo-project.json`。找不到 → 报错退出，提示运行 `/eo-project-init`。

## 输入

- **经验内容**：发生了什么、学到了什么
- 类别（可选，能推断就推断）：`pitfall` / `best-practice` / `surprise`

## 路径解析

从 `.eo-project.json` 读取：
- `project_root` — 项目管理侧根
- `project_name` — 填入文件 frontmatter
- `kanban_path` — 更新经验教训计数（`null` 时跳过）

lessons 目录：`<project_root>/lessons/`（**lazy 创建**，本 skill 首次运行时建）。

## 执行步骤

### 1. 定位项目

读取 `.eo-project.json`，获取 `project_root` / `project_name` / `kanban_path`。

### 2. 提炼经验教训

从用户输入提取：
- **标题**：一句话概括
- **类别**：`pitfall` / `best-practice` / `surprise`
- **阶段**：从活跃 phase 文件读取（若有）
- **内容**：发生了什么 + 学到了什么 + 下次怎么做

### 3. 创建经验文件 + 维护索引

- 首次运行时 lazy 建 `<project_root>/lessons/` 目录
- 文件命名：`{YYYY-MM-DD}-{slug}.md`
- **格式严格按 [../eo-shared/lessons.md](../eo-shared/lessons.md) §2**（结论前置：规则 → 适用条件 → 背景；frontmatter 必填 `trigger` 与 `summary` 检索锚点）——它是 eo-change / eo-implement / eo-fix 启动时自动消费的口粮，写给 agent 看的部分必须在前
- 同步更新 `<project_root>/lessons/INDEX.md`（格式见 lessons.md §3；不存在则创建）

### 3.5 reindex（存量迁移动作）

用户说「reindex lessons / 迁移旧经验」时：扫描 lessons/ 全部文件——缺 `trigger`/`summary`/`status` 的，读正文提炼后**只回填 frontmatter**（正文一字不动）；重建 INDEX.md。幂等，可重复跑。

### 4. 更新项目看板（仅 `kanban_path` 非空）

更新对应项目条目的经验教训计数（读当前 `<project_root>/lessons/` 条目数）。

### 5. 追加项目日志

在 `<project_root>/log.md` 追加一条记录。

### 6. 输出摘要

- 经验文件路径
- 经验摘要
- 当前项目累计经验数

## 输出

- 经验文件：`<project_root>/lessons/{date}-{slug}.md`
- 看板更新（可选）：经验教训计数
- 项目日志：追加记录

## 约束

- 经验文件正文创建后不改，补充走新建；**唯一例外**：教训被证伪/取代时把 `status` 改 `superseded` 并在顶部加一行指向新条目（消费方会跳过 superseded）
- 每次写入必须同步 INDEX.md——没进索引的 lesson 等于没写（消费方只扫 INDEX）
- 经验按项目隔离，不再有全局 `_lessons/`
- 首次运行时 lazy 建 `lessons/` 目录
- 能推断的字段自动填充
- 路径通过 `.eo-project.json` 解析，不硬编码
- `kanban_path: null` 时不更新看板
