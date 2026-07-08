# 看板 stub 与 GitHub 联动（单一来源）

> 被 eo-change / eo-implement / eo-review / eo-fix / eo-archive / eo-project-init 引用。两套联动全部 **opt-in**（`.eo-project.json` 的 `board` / `github` 段，缺省关闭）；未开启时本文件的一切步骤直接跳过，零成本。

## 通用原则

- **本地文件是唯一真相源**：stub 和 GitHub issue/PR 都是 change frontmatter 的**投影**。同步严格单向（本地 → 投影），唯一逆向动作是漂移检测**告警**（只报告不回写）。
- **幂等**：stub 整文件重写、issue 靠回写的编号去重——重复执行无副作用。

## 一、看板 stub（`board.enabled: true`，vault 模式）

### 触发点

change 的 frontmatter 发生以下变化后，顺手 upsert 对应 stub（一次写盘，不问用户）：

| 触发 skill | 时机 |
|-----------|------|
| eo-change | 确认置 `confirmed` 后（新建 stub） |
| eo-implement | 置 `implementing` 时；每个批末 checkpoint（刷新 todo 进度） |
| eo-review | 通过置 `done` 时 |
| eo-fix | 修复计入活跃 change（勾了 TODO/AC）时 |
| eo-archive | 置 `archived` 后（第五层收尾） |

### stub 写法

路径：`<project_root>/<board.stub_dir>/<change-id>.md`（目录不存在则建）。**整文件覆盖写**，全部内容派生自 change.md，无手工成分：

```markdown
---
id: 014-batch-export
title: 批量导出
project: <project_name>
status: confirmed        # 与 change.md 同步
type: feature
todo_done: 2
todo_total: 6
issue: 42                # 无则省略
pr: https://github.com/...   # 无则省略
created: 2026-07-07
updated: 2026-07-08
tags: [eo-change]
---

[change.md](<仓库内 change.md 的绝对路径或可点击引用>) ｜ <一句话意图摘要>
```

- `todo_done/todo_total` 数 change.md §3 的 checkbox
- **skill 永不写 `.base` 文件**——看板视图由用户在 Obsidian 里配置一次（指南见 `eo-project-init/references/board-setup.md`）
- stub 是投影：允许随时全量重建（`/eo-project-init` 开启开关时做历史同步就是批量执行本节写法）

## 二、GitHub issue（`github.issue: true`）

### confirmed 时建 issue（eo-change）

1. frontmatter 已有 `issue` 号 → 跳过（去重唯一依据是回写的编号，**绝不靠标题匹配**）
2. `gh issue create --title "<id> <title>" --body <生成>`；body = §1 意图摘要 + §2 AC 清单 + §3 TODO 作 checkbox 列表（GitHub 原生显示 n of m 进度）
3. issue 号回写 change frontmatter `issue: <N>`（stub 随之带上）
4. `gh` 不可用 / 无 remote / 未登录 → 提示一次并跳过，不阻塞主流程

### archive 时兜底（eo-archive 第五层）

- issue 仍 open → `gh issue close <N> --comment "archived: <commit 区间>"`
- **漂移检测**：issue 已被人在 GitHub 关闭但 change 尚未 archived（在其他时点发现）→ 报一行告警，不改本地状态

## 三、GitHub PR（`github.pr`，eo-archive 第五层执行）

| 值 | 行为 |
|----|------|
| `never` | 什么都不做 |
| `auto`（推荐） | 当前在**非默认分支**且有 remote → push + `gh pr create`；在默认分支 → 跳过，零提问 |
| `always` | 总是建 PR（在默认分支时提示先切分支） |

PR body 自动生成：意图摘要 + AC 清单（勾选状态照抄）+ **条件性关闭**——AC 全勾 → `Closes #<issue>`；有豁免项 → `Linked to #<issue> (partial)`（issue 关闭语义严格等于验收完成）。PR URL 回写 frontmatter `pr:`。

## 四、首次配置（问一次，永不再问）

任一 skill 走到触发点时发现 `.eo-project.json` **缺失对应段**（区别于显式 `false`/`never`——那是用户已选择关闭）：

1. AskUserQuestion 问一次（board：开/关；github：issue 开/关 + pr 三选，推荐 `auto`）
2. 答案写回 `.eo-project.json`
3. 此后所有 skill 按配置静默执行，不再询问
