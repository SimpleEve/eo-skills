---
name: eo-plan-review
description: |
  【已废弃】实施计划审查技能。change 自带澄清，不再需要独立的 plan/proposal-review 环节。

  DEPRECATED:
  - 原 plan-review 的"前置审查"职责被合并到 change 作者的自澄清中；实施后的正式审查由 /eo-review 负责。
---

# eo-plan-review — 已废弃

> ⚠️ **此 skill 已废弃**

## 为什么废弃

新工作流的核心假设：**change 作者在 change.md 中完成所有澄清**，归档前的唯一正式审查是 `/eo-review`（code review）。独立的 proposal/plan-review 被移除，理由：
- 澄清责任前移给 change 作者，减少环节
- 实施后的 `/eo-review` 已经对照 spec + change 做全维度审查，覆盖旧 plan-review 的质量门禁

## 新工作流中的"审查"分布

| 审查阶段 | 负责 skill | 对象 | 强制 / 可选 |
|---------|-----------|------|------------|
| 模块基线审查 | `/eo-spec-review` | 模块 spec.md | module-init 强制；archive 后 Delta 大改时可选复检 |
| change 方案审查 | `/eo-change-review` | change.md（implement 前） | **✅ 全程可选**（高风险建议走） |
| 实施后代码审查 | `/eo-review` | 代码 + change.md + spec.md | 每个 change 强制 |
| 归档时 Delta 冲突检查 | `/eo-archive` | spec.md × change Delta | 归档时自动 |

## 执行动作

当用户调用 `/eo-plan-review` 时：

1. 告知用户此 skill 已废弃
2. 询问用户目的：
   - "我想验证 change 方案是否合理" → 跳转到 `/eo-change-review`（可选方案审查）
   - "我想检查代码是否符合 change" → 跳转到 `/eo-review`
   - "我想确认模块基线质量" → 跳转到 `/eo-spec-review`
