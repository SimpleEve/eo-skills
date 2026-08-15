# test.md 固定模板（v3 简版）

eo-test 按下方模板写入 `eo-doc/changes/<change-id>/test.md`。**覆盖式**：同一 change 再次调用时整体重写（历史由 git 兜），核销未决清单后重新出结论。

```markdown
---
title: <功能名称>测试报告
change_id: <change-id>
created: YYYY-MM-DD
summary: 一句话测试结论。
---

# <功能名称> 测试报告

> 关联：[change.md](change.md)（验收锚点：其 §2）｜ 日期：YYYY-MM-DD ｜ 基线：<HEAD short-sha>
> 结论：通过 / 不通过（失败 x 项）

## 未决清单

<!-- 修复后核销：fixed 项复测 → verified / 回 open； waived = 用户当场裁决不修（附原话要点，不阻塞归档） -->

| 项 | 失败现象 | 位置 | 修复 commit | 状态 |
|----|---------|------|------------|------|
| F-1 | <一句话> | `path/to/test#用例` | ~ | open / fixed / verified / waived |

## 覆盖与补缺摘要

- 已有证据：<既有测试 / implement 自验证据，一句>
- 补缺：<新写了哪些测试；未落文件的验证点列一次性执行证据（命令 + 关键输出）>
- 未覆盖：<AC-x 及原因；全覆盖写「无」>

## 失败详情（有未决项时）

### [F-1] <用例名>
- 对应 AC ｜ 失败原因 ｜ 修复建议 ｜ 关键错误输出
```
