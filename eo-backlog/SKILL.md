---
name: eo-backlog
description: "项目 backlog 卡片：往 <project_root>/backlog/ 写一张待办/灵感卡（上 Obsidian 看板的 backlog 列），或归档/删除既有卡。通过 .eo-project.json 定位。触发（仅用户明确要求时）：加入 backlog / 记一条待办 / 这个以后再说，记一下 / 这条 backlog 不做了 / /eo-backlog。NOT FOR: 对话中顺带出现的『以后 / TODO』——未经用户确认不落盘；决策与教训（走 /eo-project-record）。"
---

# eo-backlog

## 功能

backlog 卡片化管理：**每条一个文件**，落在 `<project_root>/backlog/`，靠 frontmatter 的 `eo-backlog` 标签与 `status: backlog` 出现在 Obsidian 项目看板的 backlog 列。卡片是**源数据**（不是投影）——用户在 Obsidian 里直接编辑卡片正文/标签是合法且鼓励的。

三个动作：**add**（默认，写卡）、**archive**（采纳/放弃归档）、**delete**（用户指定时才删）。

## 前置

**必须**能找到 `.eo-project.json`（cwd 或父目录）。同目录存在 `.eo-project.local.json` 时顶层字段覆盖合并（local 优先）。找不到时报错退出，提示运行 `/eo-project-init`。`backlog/` 与 `backlog/archive/` 目录 lazy 创建。

## 卡片格式

文件：`<project_root>/backlog/<YYYY-MM-DD>-<slug>.md`

```markdown
---
title: <一句话，动宾结构>
project: <项目名，取自 .eo-project.json>
status: backlog          # 激活态恒为 backlog；归档时变 adopted / dropped
tags: [eo-backlog, <内容标签…>]   # eo-backlog 是看板过滤锚点，必含且必须在激活态
created: YYYY-MM-DD
issue: ~                 # 可选：粘外来 GitHub issue URL（不主动 issue 化）
---
<一两句补充说明，可空>
```

- 待办/灵感不再分小节，用内容标签表达（如 `idea`）；拿不准就不打
- **status 恒为 `backlog`**：它不是 change，不进 draft/confirmed 流转；在看板上把 backlog 卡拖进其他状态列是误操作（会改 status），发现即纠正回来

## 动作

### add（默认）

1. 提炼 title（单行动宾）、补充说明（可空）、内容标签
2. 按上方格式写入 `backlog/<date>-<slug>.md`
3. 摘要：卡片路径 + title + 当前激活卡片数

### archive（采纳 / 放弃）

触发：change 采纳了这条 backlog（由 /eo-change 在确认后调用），或用户说「这条不做了」。

1. frontmatter 三改：`status: backlog → adopted`（采纳）或 `dropped`（放弃）；tags 里 `eo-backlog → eo-backlog-archived`（双保险退出看板）；追加关联——采纳写 `adopted_by: <change-id>`，放弃写 `dropped_reason: <一句话>`
2. **文件移入 `backlog/archive/`**（主目录只留激活卡，防膨胀）
3. 摘要：处置结果 + 关联 change（若有）

### delete（仅用户明确指定）

默认归档留痕；用户明确说「直接删掉」才物理删除文件。

### migrate（旧扁平 backlog 打散）

发现 `<project_root>/backlog.md`（或 backlog/ 下的 todo.md 等旧扁平文件）时提示可迁移：未完成的 `- [ ]` 条目逐条打散成卡片（created 取条目原日期，行内 `#tag` 转入 tags）；已完成/已放弃条目留在原文件不动；迁完在原文件顶部标注「已迁移为卡片，此文件不再写入」。幂等：已存在同名卡跳过。

## 约束

- **仅用户明确要求时写入**，不做关键词嗅探
- 激活卡的修改（改 title/标签/说明）用户手工做即可，本 skill 不代管；**归档必走 archive 动作**（三件套：status + tag + 移动，缺一会导致看板残留或审计断链）
- 不建 INDEX——看板（Bases 聚合）就是它的索引
- 决策与经验教训走 `/eo-project-record`，本 skill 不越界
- 所有路径通过 `.eo-project.json` 解析，不硬编码
