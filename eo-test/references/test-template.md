# test.md 固定模板

eo-test 按下方模板写入 `eo-doc/dev/<module-name>/changes/<change-id>/test.md`。

```markdown
---
title: <功能名称>测试报告
module: <module-name>
change_id: <NNN-change-id>
tags: [标签1, 标签2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
summary: >
  一句话概述测试结论。
---

# <功能名称> 测试报告

> 关联 模块：[spec.md](../../spec.md)
> 关联 Change：[change.md](change.md)
> 测试日期：YYYY-MM-DD
> 测试环境：运行时 / OS / 版本 / 其他相关信息

## 测试总结

| 指标           | 数值 |
| -------------- | ---- |
| 单元测试总数   | N    |
| 单元测试通过   | N    |
| 单元测试失败   | N    |
| 集成测试总数   | N    |
| 集成测试通过   | N    |
| 集成测试失败   | N    |
| 总体通过率     | N%   |

## 单元测试详情

### ✅ 通过的测试

| 测试文件        | 测试用例 | 对应 TODO |
| --------------- | -------- | --------- |
| `path/to/test`  | 测试描述 | TODO-S1   |

### ❌ 失败的测试

#### [FAIL-1] <测试用例名称>

- **测试文件**：`path/to/test`
- **对应 TODO**：TODO-XX
- **失败原因**：详细描述（明确区分是测试错误还是业务 bug）
- **修复建议**：针对业务 bug 提出修改建议
- **错误日志**：
```
相关的错误输出
```

## 集成 / 场景验证详情

### 场景 1：<场景名称>
- **操作步骤**：...
- **期望结果**：...
- **实际结果**：✅ 符合预期 / ❌ 与预期不符
- **证据**：命令输出 / 日志 / 截图路径

## 未覆盖的测试场景

列出 Change 中要求但本次未覆盖的测试场景及原因。

## 遗留问题

列出需要人工关注的问题。
```
