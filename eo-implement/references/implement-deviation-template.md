# 实施偏差记录模板

仅在实施偏离 change 方案时创建 `changes/<change-id>/implement.md`，按下方模板填写。

```markdown
---
title: <change-id> 实施偏差记录
module: <module-name>
change_id: <change-id>
tags: [偏差]
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
summary: >
  记录实施过程中偏离 change 方案的决策。
---

# <change-id> 实施偏差记录

> 关联 change：[change.md](change.md)

## 偏差项

### [D-1] <偏差标题>
- **相关 TODO**：TODO-XX
- **原计划**：change 中的描述
- **实际做法**：实际采取的方案
- **原因**：为什么偏离
- **影响**：对其他 TODO 或后续工作的影响
```
