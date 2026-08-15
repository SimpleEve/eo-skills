# review.md 固定模板（v3 简版）

eo-review 按下方模板写入 `eo-doc/changes/<change-id>/review.md`。**覆盖式**：复审时整体重写（历史由 git 兜）——先核销上一版未决清单（fixed → verified / 回 open），再加上新发现。

```markdown
---
title: <功能名称>代码审查报告
change_id: <change-id>
created: YYYY-MM-DD
summary: 一句话审查结论。
---

# <功能名称> 代码审查报告

> 关联：[change.md](change.md)（检查表：其 §2）｜ 日期：YYYY-MM-DD ｜ 基线：<HEAD short-sha>
> 结论：通过 / 不通过（P0 x 条）/ 有保留通过（P1 x 条）

## Finding 清单

<!-- 核销：fixed 项按修复 commit 复验 → verified / 回 open；
     waived = 用户当场裁决不修（附原话要点，不阻塞归档）。
     根因枚举：implementation / test-asset / requirement（实为需求问题 → 建议回炉） -->

| ID | 级别 | 摘要 | 位置 | 根因 | 状态 |
|----|------|------|------|------|------|
| P0-1 | P0 | <一句话> | `file:line` | implementation | open / fixed / verified / waived |

## AC 覆盖检查

| AC | 状态 |
|----|------|
| AC-1 | ✅ / ❌ / ⚠️ |

## P0 - 必须修复（阻塞）

### [P0-1] <标题>
- 位置：`file:line` ｜ 描述 ｜ 影响 ｜ 建议（不写代码）

## P1 - 建议修复（不阻塞）

## P2 - 可选优化
```
