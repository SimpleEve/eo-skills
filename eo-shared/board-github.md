# eo-sync 内置适配器：Obsidian stub 与 GitHub issue/PR 投影实现说明

> `eo-sync` 两个内置适配器（`eo-sync-obsidian` / `eo-sync-github`）投影 change frontmatter 的**内容契约**——本文件描述「投影成什么样」，不描述「何时触发」（触发已收敛为 archive 收口自动一次 + 手动 `eo-sync run`，逐流转投影已退役）。协议、发现与身份回写见 [../docs/sync-adapter-protocol.md](../docs/sync-adapter-protocol.md)。两适配器由 `.eo-project.json` 的 `sync` 段**opt-in**（存量 legacy `board` / `github` 段经兼容映射仍生效，新配置不再生成旧段）；未启用即不投影、零成本。

## 通用原则

- **本地文件是唯一真相源**：stub 和 GitHub issue/PR 都是 change frontmatter 的**投影**。同步严格单向（本地 → 投影），唯一逆向动作是漂移检测**告警**（只报告不回写）。
- **幂等**：stub 整文件重写、issue 靠回写的编号去重——重复执行无副作用。

## 一、Obsidian stub 适配器（`eo-sync-obsidian`；vault 模式，`sync.obsidian` 或 legacy `board.enabled`）

生命周期起点 **draft**（全生命周期投影，看板 draft 列真实）。适配器纯投影、`identity_fields` 为空——自身不产生平台身份，`issue`/`pr` 照抄 change frontmatter。`archived` 时只改 `status`、**tags 与文件位置都不动**（`eo-change` tag 是 Bases 过滤锚点，动了卡片从所有视图消失；活跃看板隐藏 archived 由 starter 看板的 `status != "archived"` 视图级过滤解决，盘点 table 保留全史）。草稿被**放弃**（change 目录删除）→ 适配器按簿记检测孤儿、删除对应 stub，不留孤儿卡。

**投影不对称是有意的**：stub 从 draft 起投影（对内积极、本地可重建镜像），GitHub issue 自 confirmed 起建号（对外保守——草稿夭折不该在外部世界留痕）。

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
branch: feature/export   # 投影时的 git 分支；在默认分支则省略（worktree 并行时一眼可辨）
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

## 二、GitHub issue（`eo-sync-github`；`sync.github` 或 legacy `github.issue: true`）

### issue 投影：生命周期起点 confirmed 起建号

1. frontmatter 已有 `issue` 号 → 跳过（去重唯一依据是回写的编号，**绝不靠标题匹配**）
2. `gh issue create --title "<id> <title>" --body <生成>`（id = slug；`seq` 不进标题——对外投影没人会回去改号）；body 按档生成：全档 = §1 意图摘要 + §2 AC 清单 + §3 TODO 作 checkbox 列表（GitHub 原生显示 n of m 进度）；轻档 = 「意图：」行 + §2 AC 清单
3. issue 号回写 change frontmatter `issue: <N>`（stub 随之带上）
4. `gh` 不可用 / 无 remote / 未登录 → 提示一次并跳过，不阻塞主流程
5. **body 刷新**（幂等，靠回写号定位）：AC 增删、扩档（light→full 补入 TODO 清单）、收口/归档时 `gh issue edit <N> --body <重新生成>`——投影不与本地真相源漂移。外部来源 issue 在 frontmatter 记完整 `owner/repo#N` 或 URL（跨仓时裸号不可定位）

### archived 兜底关闭（archive 收口 run）

- issue 仍 open → `gh issue close <N> --comment "archived: <commit 区间>"`
- **漂移检测**：issue 已被人在 GitHub 关闭但 change 尚未 archived（在其他时点发现）→ 报一行告警，不改本地状态

## 三、GitHub PR（`eo-sync-github`，`sync.github.pr`（或 legacy `github.pr`）策略；仅对 archived，archive 收口 run 生成）

| 值 | 行为 |
|----|------|
| `never` | 什么都不做 |
| `auto`（推荐） | 当前在**非默认分支**且有 remote → push + `gh pr create`；在默认分支 → 跳过，零提问 |
| `always` | 总是建 PR（在默认分支时提示先切分支） |

PR body 自动生成：意图摘要 + AC 清单（勾选状态照抄）+ **条件性关闭**——AC 全勾 → `Closes #<issue>`；有豁免项 → `Linked to #<issue> (partial)`（issue 关闭语义严格等于验收完成）。PR URL 回写 frontmatter `pr:`。

## 四、首次配置（问一次，永不再问）

`eo-project-init` 初始化（或后开时的更新分支）发现配置合并结果（`.eo-project.json` + 可选 `.eo-project.local.json` 覆盖）的 `sync` 段**缺对应适配器键**（区别于显式关闭条目 `{"enabled": false}`——那是用户已选择关闭）：

1. 按 [questioning.md](questioning.md) §4 的封闭选择协议问一次（obsidian：开/关；github：issue 开/关 + pr 三选，推荐 `auto`），答案落 `sync.obsidian` / `sync.github`（新配置不写 legacy `board`/`github` 段）
2. 答案写回：该顶层段已存在于 `.eo-project.local.json` → 写 local（写共享文件会被覆盖屏蔽）；否则写 `.eo-project.json`
3. 此后 `eo-sync` 按配置静默投影，不再询问

**存量迁移**（重跑 init 的 1.5 分支）：合并配置只有 legacy `board`/`github` 段、无 `sync` 键 → 提示并代写等价 `sync` 段（启用集与兼容映射派生一致，含显式关闭条目；旧段保留不删）；已有 `sync` 键 → 零动作。
