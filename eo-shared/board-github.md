# 看板 stub 与 GitHub 联动（单一来源）

> 被 eo-change / eo-implement / eo-review / eo-fix / eo-archive / eo-project-init 引用。两套联动全部 **opt-in**（`.eo-project.json` 的 `board` / `github` 段，缺省关闭）；未开启时本文件的一切步骤直接跳过，零成本。

## 通用原则

- **本地文件是唯一真相源**：stub 和 GitHub issue/PR 都是 change frontmatter 的**投影**。同步严格单向（本地 → 投影），唯一逆向动作是漂移检测**告警**（只报告不回写）。
- **幂等**：stub 整文件重写、issue 靠回写的编号去重——重复执行无副作用。

## 一、看板 stub（`board.enabled: true`，vault 模式）

### 触发点

**通用原则：change.md 的 frontmatter（status）或 §2/§3 勾选数发生变化的任何落盘动作，顺手 upsert stub**（一次写盘，不问用户）——stub 从 **draft 起全生命周期投影**，看板的 draft 列因此始终真实。具体锚点：

| 触发 skill | 时机 |
|-----------|------|
| eo-change | **写入 change.md（draft）时即新建 stub**；修订、确认置 `confirmed` 时更新 |
| eo-implement | 置 `implementing` 时；每个批末 checkpoint（刷新 todo/ac 进度）；人工验收门勾 manual 后 |
| eo-review | 通过置 `reviewed` 时 |
| eo-fix | 修复计入活跃 change（勾了 TODO/AC）时 |
| eo-archive | 置 `archived` 后（第五层收尾）：最后一次 upsert（`status: archived`）。**tags 与文件位置都不动**——`eo-change` tag 是 Bases 过滤锚点，动了卡片从所有视图消失；活跃看板不想看 archived 列由呈现层解决（starter 看板的 kanban 主视图自带 `status != "archived"` 视图级过滤，盘点 table 保留全史） |

草稿被**放弃**（change 目录删除/终止）时同步删除对应 stub，不留孤儿卡。

注意不对称是有意的：**GitHub issue 仍在 confirmed 才建**（对外投影保守——草稿夭折不该在外部世界留痕）；stub 是本地可重建镜像（对内投影积极）。

### stub 写法

路径：`<project_root>/<board.stub_dir>/<change-id>.md`（目录不存在则建）。**整文件覆盖写**，全部内容派生自 change.md，无手工成分：

```markdown
---
id: batch-export
seq: 14                  # 显示别名（#14），与 change.md 同步；无则省略
title: 批量导出
project: <project_name>
status: confirmed        # 与 change.md 同步
type: feature
tier: full               # light | full，与 change.md 同步；缺省 full
summary: <一句话意图，≤50 字，纯文本>   # 与 change.md frontmatter 同步，卡面一眼看意图
branch: feature/export   # upsert 时的 git 分支；在默认分支则省略（worktree 并行时一眼可辨）
todo_done: 2
todo_total: 6
ac_done: 1
ac_total: 4
issue: 42                # 无则省略
pr: https://github.com/...   # 无则省略
created: 2026-07-07
updated: 2026-07-08
tags: [eo-change]          # eo-change 是看板过滤锚点,必含且全生命周期恒定(含 archived,绝不换名);可再附加内容标签
---

`<仓库内 change.md 的相对路径>`
```

正文只放 change 路径，且**必须是纯文本（inline code），禁止写成 markdown 链接**——change 在代码仓库内、vault 之外，Obsidian 无法解析这种链接，点了也打不开；纯文本路径供人复制到 IDE 打开。描述性信息（summary 等）一律进 frontmatter：Bases 卡面显示的是属性，正文在卡上不可见。

- `todo_done/todo_total` 数 change.md §3 的 checkbox（轻档无 §3 → 两字段省略）；`ac_done/ac_total` 数 §2 的 checkbox（看板一眼看验收进度）
- **starter 看板自动创建**：开启 board 时（含历史同步），若 `<vault_root>/eo-project-board.base` **不存在**则按 [../eo-project-init/references/board-setup.md](../eo-project-init/references/board-setup.md) 的模板创建（kanban-view 主视图 + table 盘点，双条件过滤，全 vault 聚合）；**已存在则绝不触碰**——用户在 Obsidian UI 的一切调整由 Obsidian 写回该文件。kanban-view 依赖社区插件 Kanban Bases View，未装时用户可在 UI 把视图类型换官方 cards
- stub 是投影：允许随时全量重建（`/eo-project-init` 开启开关时做历史同步就是批量执行本节写法）

## 二、GitHub issue（`github.issue: true`）

### confirmed 时建 issue（eo-change）

1. frontmatter 已有 `issue` 号 → 跳过（去重唯一依据是回写的编号，**绝不靠标题匹配**）
2. `gh issue create --title "<id> <title>" --body <生成>`（id = slug；`seq` 不进标题——对外投影没人会回去改号）；body 按档生成：全档 = §1 意图摘要 + §2 AC 清单 + §3 TODO 作 checkbox 列表（GitHub 原生显示 n of m 进度）；轻档 = 「意图：」行 + §2 AC 清单
3. issue 号回写 change frontmatter `issue: <N>`（stub 随之带上）
4. `gh` 不可用 / 无 remote / 未登录 → 提示一次并跳过，不阻塞主流程
5. **body 刷新**（幂等，靠回写号定位）：AC 增删、扩档（light→full 补入 TODO 清单）、收口/归档时 `gh issue edit <N> --body <重新生成>`——投影不与本地真相源漂移。外部来源 issue 在 frontmatter 记完整 `owner/repo#N` 或 URL（跨仓时裸号不可定位）

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

任一 skill 走到触发点时发现配置合并结果（`.eo-project.json` + 可选 `.eo-project.local.json` 覆盖）**缺失对应段**（区别于显式 `false`/`never`——那是用户已选择关闭）：

1. 按 [questioning.md](questioning.md) §4 的封闭选择协议问一次（board：开/关；github：issue 开/关 + pr 三选，推荐 `auto`）
2. 答案写回：该顶层段已存在于 `.eo-project.local.json` → 写 local（写共享文件会被覆盖屏蔽）；否则写 `.eo-project.json`
3. 此后所有 skill 按配置静默执行，不再询问
