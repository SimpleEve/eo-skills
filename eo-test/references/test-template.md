# test.md 固定模板

eo-test 按下方模板维护 `eo-doc/changes/<change-id>/test.md`：**首轮全量写入，复审轮追加不覆盖**（只更新台账 + 追加轮次记录 + 原地更新速报）。

```markdown
---
title: <功能名称>测试报告
change_id: <change-id>
tags: [标签1, 标签2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
summary: >
  一句话概述测试结论。
---

# <功能名称> 测试报告

> 关联 Change：[change.md](change.md)（验收锚点：其 §2 验收清单）
> 首轮测试日期：YYYY-MM-DD ｜ 测试环境：运行时 / OS / 版本
> ⚠️ 首轮之后正文各节为历史快照——当前状态以「FAIL 台账」与末尾「速报」为准

## FAIL 台账

<!-- 状态单一来源；FAIL-x 编号与轮次编号全文件单调递增（跨 revision 不清零）。写入权（writer matrix）：
     eo-test 建条与核销（open→verified；verified 后再失败 = reopen 回 open）；
     fixed + 修复 commit 由 eo-implement 修复循环回写；
     waived = 用户显式裁决不修（当场获得裁决的 skill 写入，附原话要点；不阻塞归档）；
     eo-change 回炉时追加作废行并把仍 open/fixed 的行批量标 superseded。历史轮次节谁都不改。
     级别枚举：阻塞（业务缺陷，挡归档）/ 非阻塞（提示类）。
     根因枚举：implementation（业务 bug）/ test-harness（测试代码错误，由本 skill 自修并直接核销）/
     environment（环境假失败，修基建不计实施缺陷）/ requirement（实为需求问题 → 建议回炉） -->

| ID | 级别 | 摘要 | 位置 | 状态 | 根因 | 首见/最近轮 | 基线/修复 commit |
|----|------|------|------|------|------|-------------|------------------|
| FAIL-1 | 阻塞 | <一句话> | `path/to/test#用例` | open / fixed / verified / waived / superseded | implementation | 1/1 | `abc123` / ~ |

## 测试总结（首轮快照）

| 指标           | 数值 |
| -------------- | ---- |
| 单元测试总数   | N    |
| 单元测试通过   | N    |
| 单元测试失败   | N    |
| 集成测试总数   | N    |
| 集成测试通过   | N    |
| 集成测试失败   | N    |

## 单元测试详情

### ✅ 通过的测试

| 测试文件        | 测试用例 | 对应 AC / TODO |
| --------------- | -------- | -------------- |
| `path/to/test`  | 测试描述 | AC-1 / TODO-1  |

### ❌ 失败的测试

#### [FAIL-1] <测试用例名称>
- **测试文件**：`path/to/test`
- **对应 AC / TODO**：AC-x / TODO-x（映射不到 AC 的边界失败照记——输入来自代码，见 SKILL 核心原则 3）
- **失败原因**：详细描述（根因落台账「根因」列：业务 bug = implementation；测试代码错误 = test-harness，本 skill 直接修正并核销）
- **修复建议**：针对业务 bug 提出修改建议
- **错误日志**：
```
相关的错误输出
```

## 一次性执行证据

<!-- 回归资产分层（SKILL 核心原则 4）：未沉淀为测试文件的验证点在此留证；无则整节省略 -->

| 验证点（AC / 输入） | 命令 | 关键输出 | 结论 |
| ------------------- | ---- | -------- | ---- |
| AC-x | `cmd` | 摘要 | ✅ / ❌ |

## 集成 / 场景验证详情

### 场景 1：<场景名称>
- **操作步骤** ｜ **期望结果** ｜ **实际结果**：✅ / ❌ ｜ **证据**：命令输出 / 日志 / 截图路径

## 未覆盖的测试场景

列出 Change 中要求但本次未覆盖的测试场景及原因。

## 遗留问题

列出需要人工关注的问题。

<!-- 复审轮在「速报」之前追加，不改上文：

## 第 N 轮记录（revision R · YYYY-MM-DD）

- 测试基线：`<本轮实施最后一个 [change-id] commit short-sha>`
- 核销：FAIL-1 verified（修复 commit `def456`）；FAIL-2 open（复测仍失败：<一句话>）
- reopen：无 ／ FAIL-3 第二次失败（<一句话>）
- 新增：无 ／ [FAIL-4] <一句话> — `path#用例`（详情本节展开）
- 本轮结论：通过 / 不通过（失败 x 项）

回炉时由 eo-change 追加一行，历史轮次节保留不删：
> revision N 作废（YYYY-MM-DD）——后续见 revision N+1
-->

## 速报

结论：通过 / 不通过（失败 x 项）［第 N 轮 · revision R · 基线 `<short-sha>`］
⚠️ 复发：<ID> 第二次失败（无则省略此行）
下一步：回 /eo-implement 修复后重测 / 可进入 /eo-review
```

> 末尾「速报」节必填且恒为末节——它是本报告的机器可读出口（编排方与 eo-archive 读文件即取当前结论），与对话速报同款内容。
