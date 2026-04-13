---
name: eo-plan
description: |
  【已废弃】实施计划技能。本 skill 的职责已合并进 /eo-change。

  DEPRECATED:
  - 请使用 /eo-change 替代。change 本身承载 spec Delta + 技术方案 + TODO，不再单独出 plan。
  - 触发本 skill 时，提示用户迁移到新工作流。
---

# eo-plan — 已废弃

> ⚠️ **此 skill 已废弃，请使用 `/eo-change`**

## 迁移说明

原 `eo-plan` 的"把 spec 转化为可执行实施方案"职责已完全合并进新的 `/eo-change`：

| 旧 eo-plan 职责 | 新位置 |
|----------------|-------|
| 技术方案概述 | `change.md` §4.1 技术方案概述 |
| 外部/内部依赖 | `change.md` §4.2 外部/内部依赖 |
| TODO 拆解（S/C/G 或层级 Part） | `change.md` §4.3 TODO 拆解 |
| 依赖关系与执行顺序 | `change.md` §4.4 |
| 测试标准 | `change.md` §6 测试标准 |
| 风险与缓解 | `change.md` §8 风险与缓解 |

## 新工作流速览

```
模块不存在 → /eo-module-init
模块已存在 + 业务变更 → /eo-change → /eo-implement → /eo-test → /eo-review → /eo-archive
实施期 bug fix → /eo-implement（不开新 change）
```

## 执行动作

当用户调用 `/eo-plan` 时：

1. 告知用户 eo-plan 已废弃
2. 询问用户是想做"新模块初始化"还是"对已有模块的变更"
3. 引导跳转到 `/eo-module-init` 或 `/eo-change`
4. 不产出 plan.md 文件

## 旧 plan.md 的兼容处理

若用户项目 `eo-doc/dev/` 下已存在旧结构的 plan.md：
- 不主动迁移，保留历史文件
- 若用户对旧 plan 发起修改，建议先用 `/eo-change` 新开一个 change 承接后续演化
