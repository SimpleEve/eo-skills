---
name: eo-archive
description: |
  归档已审查通过的 change：结算工作区为 commit、冻结 change 目录、触发文档同步（doc-manager sync）。触发：归档 change / archive / /eo-archive。
  NOT FOR: 未通过 review 的 change（先走 /eo-review）；文档同步本身的细节（归 /eo-doc-manager）。
---

# eo-archive — 变更归档

归档的本质：**把世界结算成 commit，然后按 commit 更新文档**。change 目录归档后整体冻结为审计历史，**不合并回任何文档**——活文档（state/ + agent-handbook/）由 doc-manager 以代码为唯一信源维护，本 skill 只是它的触发点之一。

## 核心理念

1. **零同步逻辑**：本 skill 不拥有任何文档同步细节，第四层是对 `/eo-doc-manager sync` 的内嵌调用（加载并执行其流程）
2. **AC 是归档门**：验收清单全勾才能归档；豁免必须显式记录
3. **冻结不可逆**：`status: archived` 之后 change 目录只读；后续问题按性质走 /eo-fix 或新 change
4. **commit 区间只是审计**：归集的区间写入 frontmatter 备查，不决定同步范围（同步永远是 cursor..HEAD）

## 前置条件

- **必须能找到 `.eo-project.json`**。找不到 → 报错退出，提示运行 `/eo-project-init`
- 目标 `eo-doc/changes/<change-id>/change.md` 存在且 `status: done`

## 工作流程（五层）

### 第一层：前置校验

1. `status: done`（不是 → 指出当前所处环节：draft/confirmed 回 /eo-change 或 /eo-implement；implementing 回 /eo-implement；已 archived 直接告知）
2. `review.md` 存在且结论为通过（P0/P1 已清零）
3. **验收清单全勾**：change.md §2 所有 `- [x]`，且 **manual 类 AC（「人工:」标记）的勾必须来自用户确认**（implement 人工验收门的记录；agent 代勾的 manual 项视为未勾）。存在未勾/未确认项 → 列出并按封闭选择协议（[../eo-shared/questioning.md](../eo-shared/questioning.md) §4）请用户三选一：回 /eo-implement 补齐（推荐）/ 显式豁免（豁免项与理由写入 §8 开放问题）/ 终止归档

### 第二层：工作区结算

cursor 基于 commit，sync 只能看见已提交内容，因此先结算：

1. `git status` 检查工作区
2. **属于本 change 的未提交改动** → 提交，message 带 `[<change-id>]` 前缀（见 [../eo-shared/conventions.md](../eo-shared/conventions.md)）
3. **无关脏改动** → 留在工作区不动（后续 sync 默认「只取已提交增量」不会碰它们）
4. 两类混在同一文件无法分离 → 停下问用户如何拆分

### 第三层：冻结元数据并提交

1. 从 `base_commit..HEAD` 按 `[<change-id>]` 前缀归集本 change 的提交；单 commit 直取，多 commit 列出请用户确认；存在无前缀夹杂提交时请用户圈定
2. 写入 frontmatter：`commits: [<区间>]`（仅审计用）、`status: archived`（不可逆）
3. 更新 `eo-doc/changes/INDEX.md` 对应行
4. 以上文档改动提交入库——可与第二层合为同一个 commit（推荐一次 change 一次 commit）；implement 已按批提交时，这就是一个小的收尾 meta commit

### 第四层：文档同步（内嵌调用）

执行 `/eo-doc-manager sync` 的完整流程（读其 SKILL.md 与 references 照做）：cursor..HEAD 增量更新 state/ + agent-handbook/，完成后 cursor 推进到 HEAD。

- 把 change.md 路径作为业务语境提示带入（帮助 sync 理解「为什么改」）；**信源永远是代码**，不按 change 说的写、按代码是的写
- 同步范围覆盖第二/三层的提交与期间累积的直改提交，一并吸收
- 若 sync 中途失败：change 已冻结、cursor 未推进——直接手动重跑 `/eo-doc-manager sync` 续上，不需要回滚归档

### 第五层：收尾

1. 联动钩子：按 [../eo-shared/board-github.md](../eo-shared/board-github.md) 执行——stub 置 archived、issue 兜底关闭、PR 创建（按 `github.pr` 策略；对应开关未开启则跳过）
2. 对话速报（不写额外文件）：

```
归档完成：<change-id>
- commit 区间：<...>（N 个提交）
- 文档同步：state/ 更新 X 篇、agent-handbook/ 更新 Y 篇（跳过 Z 篇）
- AC：全勾 / 豁免 N 项（已记 §8）
- 后续建议：<doc-manager 若提示一致性校验到期，转达；否则省略此行>
```

## 关键约束

| 约束 | 说明 |
|------|------|
| 不反写任何文档 | change 内容不合并回 state/handbook/其他文件；活文档更新只经由第四层的 sync |
| 零同步逻辑 | 第四层是内嵌调用 /eo-doc-manager，本文件不复述其任何步骤 |
| AC 门禁 | 未全勾必须走「补齐 / 显式豁免 / 终止」三选一，不得静默放行 |
| 归档不可逆 | archived 后不回退 status；后续问题走 /eo-fix 或新 change |
| 区间 ≠ 范围 | commit 区间只写 frontmatter 审计；同步范围永远是 cursor..HEAD |
| 一次一个 | 一次归档一个 change；多个待归档时逐个走完五层 |
