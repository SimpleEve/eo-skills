---
name: eo-project-record
description: "项目记忆的统一写入口：经验教训（lessons/）与关键决策（decisions/），带 INDEX 与检索锚点，供 eo-change / eo-fix / eo-recall 消费。通过 .eo-project.json 定位。触发（仅用户明确要求记录时）：把这个坑记下来 / 记条经验 / lesson learned / 把这个决策记下来 / 记录决策 / reindex lessons / reindex decisions / /eo-project-record。NOT FOR: 对话提到踩坑或决策但用户未要求记录；待办类（走 /eo-backlog）。"
---

# eo-project-record

## 功能

项目记忆的统一写入口，两种记录类型、两个目录、各自 INDEX：

| 类型 | 目录 | 记什么 | 谁消费 |
|------|------|--------|--------|
| **lesson** | `<project_root>/lessons/` | 踩坑、最佳实践、意外收获 | eo-change / eo-implement / eo-fix 启动时按 trigger 自动消费 |
| **decision** | `<project_root>/decisions/` | 关键决策：背景、候选、裁定、理由 | eo-recall 缘由瀑布（以及一切「当初为什么」的场景） |

分不清类型时的判据：**教训回答「下次怎么做」，决策回答「当时为什么这么定」**。一次对话产出两者都有 → 各记一条，互相 `[[链接]]`。

## 前置

必须能找到 `.eo-project.json`。同目录存在 `.eo-project.local.json` 时顶层字段覆盖合并（local 优先）。找不到 → 报错退出，提示运行 `/eo-project-init`。从中读取 `project_root` / `project_name`。

## 执行步骤

### 1. 判型与提炼

从用户输入判定类型（lesson / decision），提炼标题与核心内容。两个目录均 lazy 创建。

### 2a. lesson 类型

格式严格按 [../eo-shared/lessons.md](../eo-shared/lessons.md) §2（结论前置：规则 → 适用条件 → 背景；frontmatter 必填 `trigger` 与 `summary` 检索锚点）；文件 `lessons/<YYYY-MM-DD>-<slug>.md`；同步维护 `lessons/INDEX.md`（格式见 lessons.md §3）。

### 2b. decision 类型

按 [references/decision-template.md](references/decision-template.md) 写入 `decisions/<YYYY-MM-DD>-<slug>.md`；同步维护 `decisions/INDEX.md`（表格：日期 / 标题链接 / status / summary）。

注意分工：**流程内的决策不用进来**——change 起草的已钉决策落 change.md §1、brainstorming 的落其记录「关键决策」表。本类型只收**流程外的重大决策**（方向取舍、架构选型、规则变更这类会被将来反复问「当时为什么」的）。

### 3. 收尾

- 输出：文件路径 + 一句话摘要 + 该目录累计条数
- 内容涉及已有记录的修正 → 旧文件 `status` 改 `superseded` 并在顶部指向新条目（正文不改）

### reindex（存量迁移动作）

用户说「reindex lessons / reindex decisions / 迁移旧记录」时：扫描对应目录全部文件——缺 `trigger`（仅 lesson）/`summary`/`status` 的，读正文提炼后**只回填 frontmatter**（正文一字不动）；重建该目录 INDEX.md。幂等，可重复跑。

## 约束

- 记录文件正文创建后不改，补充走新建；**唯一例外**是 `status: superseded` 标注
- 每次写入必须同步对应 INDEX——没进索引的记录等于没写（消费方只扫 INDEX）
- 记录按项目隔离；仅用户明确要求时写入，不做关键词嗅探
