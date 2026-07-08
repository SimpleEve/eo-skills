# 决策记录模板

写入 `<project_root>/decisions/<YYYY-MM-DD>-<slug>.md`。

```markdown
---
type: decision
project: <项目名>
date: YYYY-MM-DD
status: accepted        # accepted | superseded
tags: [具体领域词]
summary: <一句话裁定结论——检索锚点，必填>
---

# <标题：陈述裁定，如「看板采用 Bases + stub 投影方案」>

## 背景

<为什么出现这个决策点，2-4 句>

## 候选方案

1. <方案 A>；2. <方案 B>；……

## 裁定

<选了什么，关键参数/边界>

## 理由

<为什么，含放弃其他候选的原因>

## 影响范围

<波及哪些模块/流程/文件>
```

- 标题写成**裁定陈述**（不是「关于 X 的讨论」）；`summary` 是 recall/INDEX 的检索锚点，必填
- 相关的 lesson / research 篇目用 `[[名称]]` 互链
- decisions/INDEX.md 行格式：`| 日期 | [标题](文件) | status | summary |`
