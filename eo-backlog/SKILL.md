---
name: eo-backlog
description: "往项目 backlog.md 追加待办、灵感或未接入的未来规划。通过 .eo-project.json 定位项目。触发：加入 backlog / 记一条待办 / 以后再说 / /eo-backlog。"
---

# eo-backlog

## 功能

往 `<project_root>/backlog.md` 追加一条条目，分类落到对应小节。

**只做"追加"**。决策记录走 `eo-project-update`，经验教训走 `eo-project-lesson`，本 skill 不越界。

配置与目录约定见 [eo-project-init/references/config.md](../eo-project-init/references/config.md)。

## 前置

**必须**能找到 `.eo-project.json`（cwd 或父目录）。找不到时报错退出，提示运行 `/eo-project-init`。

`backlog.md` 由 `eo-project-init` 初始化时必建，理论上一定存在。若丢失则按 [eo-project-init/SKILL.md](../eo-project-init/SKILL.md) 的模板重建一份空骨架再写入。

## 输入

- **待办**："D6 先跳过，回头处理"、"TODO: 补测试"、"记一条待办"
- **灵感**："以后可以考虑 X"、"有个想法"、"先记一笔"
- **未接入**："这个要等 research skill"、"暂时塞这里"

## 路径解析

从 `.eo-project.json` 读取 `project_root`，操作 `<project_root>/backlog.md`。不硬编码。

## 执行步骤

### 1. 分类

| 类型 | 信号词 | 落到小节 |
|------|--------|---------|
| 待办 | "TODO"、"待办"、"回头"、"先跳过"、"workaround" | `## 待办` |
| 灵感 | "以后"、"想法"、"先记一笔"、"idea"、"考虑" | `## 灵感 & 以后再说` |
| 未接入 | "等 skill"、"未接入"、"placeholder"、"暂时" | `## 未接入（等 skill 支持再接入）` |

判断不了就按"待办"兜底，并在输出摘要里明示分类，让用户能一句话纠正。

### 2. 提炼条目

从用户输入提炼一行条目，格式：

```markdown
- [ ] {简述} — {YYYY-MM-DD}
```

- 简述保持单行、动宾结构（"补 X 的单测"、"调研 Y 方案"）
- 原始上下文信息量大时，允许在简述后加 `（{一句补充}）`，但整条不超过两行
- 日期用今天（从环境的 `Today's date` 读取）

灵感和未接入类别**不用 checkbox**，用无序列表 `-`。

### 3. 追加写入

读 `<project_root>/backlog.md`，在对应小节末尾追加条目。小节若不存在（用户手改过模板），补齐小节标题再写入。

更新 frontmatter 的 `updated: YYYY-MM-DD`。

### 4. 输出摘要

向用户展示：
- 追加到哪个小节
- 条目原文
- `backlog.md` 当前每小节的条目数

## 输出

- `<project_root>/backlog.md` 追加一条，frontmatter `updated` 刷新

## 约束

- **只追加，不修改已有条目**。要改/划掉/删除，让用户自己动手或用编辑器。
- **不建 `decisions/` / `lessons/`**（那是 `eo-project-update` / `eo-project-lesson` 的职责）
- 所有路径通过 `.eo-project.json` 解析，不硬编码
- `project_root` 不可达 → 报错提示检查配置
- 分类拿不准时默认"待办"+ 明示分类，让用户纠正，不要反复追问
