---
name: eo-change-review
description: |
  对 change.md 做方案级审查（AC 质量、TODO↔AC 映射、粒度合规、意图一致性）。触发：审查 change / change 审查 / 审方案 / /eo-change-review。
  NOT FOR: 代码审查（/eo-review）、implement 内的回归审查。
---

# eo-change-review — Change 方案审查

对一个 change 做方案级审查，在 implement 前把牢「方向是否正确、AC 是否可验收、TODO 是否完整、粒度是否合规」。**可选环节**——小 change 可跳过；AC ≥5 条 / 含 §5 技术方案 / type=refactor / 高风险 change 建议跑。

## 与另一种 review 的关系

| Skill | 审查对象 | 问的问题 |
|-------|---------|---------|
| **`eo-change-review`**（本技能） | 某个 change 的 `change.md` | 方案对不对？AC 质量、TODO 完整性？ |
| `eo-review` | change 实施后的代码 | 代码对不对？实现 vs AC？ |

两者关注点、上下文、回退动作完全不同，**不要混用**。

## 核心原则

1. **方案级审查，不替作者做决定**：只产出报告，修订由用户回 `/eo-change` 执行
2. **AC 是重中之重**：change 的价值密度集中在 §2 验收清单；AC 不可验收，后面全白做
3. **不审代码**：此时代码还没写；即使已有 spike 代码也不在范围内
4. **固定产出**：`eo-doc/changes/<change-id>/change-review.md`

## 前置条件

- **必须能找到 `.eo-project.json`**。找不到 → 报错退出，提示运行 `/eo-project-init`
- `eo-doc/changes/<change-id>/change.md` 存在，status 为 `draft` 或 `confirmed`（implementing 及之后 → 提示应走 /eo-review）

## 工作流程

### 第一步：阅读上下文

1. 读目标 change.md 全文（v2 模板：§1 意图 + 已钉决策、§2 AC、§3 TODO、§4 涉及文件、条件节 §5-§8）
2. 读 `eo-doc/changes/INDEX.md` 最近 3 条（避免与在途/已归档 change 冲突或重复）
3. 读 `eo-doc/state/` 相关篇目（系统现状，校验变更前提）
4. frontmatter `type` 缺失或不在枚举（bootstrap/feature/enhance/refactor）→ 直接 P0 报告，**不向用户追问类型归属**

### 第二步：系统审查

- **维度 1 · AC 质量（最关键）**：对照 [../eo-shared/ac-spec.md](../eo-shared/ac-spec.md) 逐条检查——用户视角？可独立验证（有验证方式）？技术无关且可度量（无「正常工作」类主观词）？覆盖异常路径（至少 1 条失败/边界 AC）？refactor 类是否写了「行为不变」的回归口径？
- **维度 2 · TODO↔AC 映射**：每条 TODO 标注了对应 AC 且映射成立？每条 AC 至少被一条 TODO 覆盖？出现映射不到 AC 的 TODO（越界）或没有 TODO 的 AC（悬空）→ P0
- **维度 3 · TODO 拆解质量**：四要素齐全（描述/文件/对应 AC/完成判据）？**占位符检测**（「补充错误处理」「后续完善」→ P0）？Batch 分组合理、Batch 1 是可独立验证的 MVP？依赖自洽无循环？
- **维度 4 · 粒度合规**：对照 [../eo-shared/granularity.md](../eo-shared/granularity.md)——TODO 数与全文行数在软标内（超软标 P1 建议拆、超硬标 P0 必须拆）；反向检查：是否 trivial 到根本不该开 change（→ P1 建议转直改）
- **维度 5 · 意图一致性**：§1 已钉决策与 §2/§3 是否自洽（TODO 有没有偷偷推翻已钉结论）？`type` 与实际内容匹配（宣称 refactor 却新增用户可见能力 → 应改 feature）？混入多个不相关改动 → 建议拆
- **维度 6 · 条件节合规**：触发条件满足却缺节（有新外部依赖但无 §5；有不可逆操作但无 §7）→ P1；触发条件不满足却写了 → P2（瘦身建议）；§8 defer 超过 3 条 → P1

### 第三步：撰写报告

按下方模板写入 `eo-doc/changes/<change-id>/change-review.md`。

### 第四步：对话速报（硬性——缺速报 = 流程未完成）

```
结论：通过 / 不通过（P0 x 条）/ 有保留通过（P1 x 条）
P0（阻塞 implement）：
1. <一句话> — change.md §X
P1（应修）：
2. <一句话> — change.md §X
P2（可后置）：
3. <一句话>
下一步：<见下方终态措辞>
（详细分析见 <change-review.md 路径>）
```

终态措辞**二选一，严禁混用**：

- **通过（无 P0/P1）**：「下一步 `/eo-implement <change-path>`（status 若仍为 draft，先回 /eo-change 对话确认）。注意：`/eo-review` 是代码审查，要在 implement 之后，现在还不轮到它。」
- **需修订（有 P0/P1）**：「回 `/eo-change <change-path>` 逐条修订，修订后**再跑一次** `/eo-change-review` 复审，循环到 P0=P1=0。🚫 不要跳过复审直接 implement，不要跑 /eo-review（代码还没写）。」

## 固定模板 — change-review.md

```markdown
---
title: <标题> Change 审查报告
change_id: <NNN-change-id>
created: YYYY-MM-DD
status: active
summary: >
  一句话审查结论。
---

# <标题> Change 审查报告

> 关联：[change.md](change.md) ｜ 审查日期：YYYY-MM-DD ｜ change status：draft / confirmed

## 审查总结
一段话 + 明确结论：✅ 可进入 implement / ⚠️ 小幅修订后进入 / ❌ 需大幅修订

## P0 - 必须修订（阻塞 implement）
### [P0-1] <标题>
- 类型：AC 不可验收 / 映射断裂 / 占位符 / 粒度超硬标 / 类型错配
- 位置：change.md §X ｜ 描述 ｜ 影响 ｜ 建议

## P1 - 建议修订
### [P1-1] <标题>（类型：粒度超软标 / 条件节缺失 / 异常路径未覆盖 / defer 超限…）

## P2 - 可选优化

## AC 质量检查
| AC | 用户视角 | 可验证 | 技术无关 | 备注 |
|----|---------|--------|---------|------|

## TODO↔AC 映射检查
| TODO | 对应 AC | 状态 |
|------|---------|------|
| TODO-1 | AC-1 | ✅ / ⚠️ / ❌ |

## 粒度检查
TODO 数：N（软标 3-7 / 硬标 10）｜ 全文：N 行（软标 500 / 硬标 700）｜ 结论：合规 / 建议拆 / 必须拆

## 结构完整性
| 节 | 状态 | 备注 |
|----|------|------|
| §1 意图 + 已钉决策 | ✅/⚠️/❌ | |
| §2 验收清单 | ✅/⚠️/❌ | |
| §3 TODO（Batch） | ✅/⚠️/❌ | |
| §4 涉及文件 | ✅/⚠️/❌ | |
| 条件节 §5-§8 | ✅/⚠️/❌ | 触发条件 vs 实际取舍 |
```

## 关键约束

- **不改 change.md**：只产报告，修订归 `/eo-change`
- **P0 精准**：只有真正阻塞 implement / 导致返工的问题才 P0
- **不审代码**、不审业务方向本身（方向的家在 brainstorming/意图确认）
- **避免触发钩子噪声**：报告中避免使用「关键决策」等字样（可能触发上游配置的记录钩子），用「设计判断」「模式选择」代替
- **可操作**：每个问题的建议必须具体到用户能直接行动
