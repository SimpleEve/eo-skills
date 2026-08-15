---
name: eo-change-review
description: |
  按需方案审查：风险信号命中或用户点名时，对 change.md 做方案级审查（AC 质量、TODO↔AC 映射、前提真实性），产简版 change-review.md。触发：审查 change / change 审查 / 审方案 / /eo-change-review。
  NOT FOR: 代码审查（/eo-review）；默认主路（无信号时不强制）。
---

# eo-change-review — Change 方案审查（按需闸门）

v3 起本 skill 是**可选闸门**：在 implement 前把牢「方向是否正确、AC 是否可验收、TODO 是否完整」。调用依据：[../eo-shared/granularity.md](../eo-shared/granularity.md) §5 风险信号命中（且用户未豁免）或用户显式点名。

## 核心原则

1. **方案级审查，不替作者做决定**：只产出报告，修订由用户回 `/eo-change` 执行
2. **AC 是重中之重**：change 的价值密度集中在 §2；AC 不可验收，后面全白做
3. **不审实施质量**：此时代码还没写；维度 7 的前提校验落到真实代码（state 文档可能过期，读码取证不等于审码）
4. **简版报告**：`eo-doc/changes/<change-id>/change-review.md`，复审**覆盖重写**（历史由 git 兜）
5. **只有 P0 阻塞**：P1/P2 移交起草方裁决，不阻塞流程

## 前置条件

- **必须能找到 `.eo-project.json`**。找不到 → 报错退出，提示运行 `/eo-project-init`
- `eo-doc/changes/<change-id>/change.md` 存在，status 为 `draft` 或 `confirmed`（implementing 及之后 → 提示应走 /eo-review）

## 工作流程

### 第一步：阅读上下文

1. 读目标 change.md 全文（§1 意图 + 已钉决策、§2 AC、§5 TODO、§6 风险）
2. 读 `eo-doc/changes/INDEX.md` 最近 3 条（避免与在途/已归档 change 冲突或重复）
3. 读 `eo-doc/state/` 相关篇目（系统现状，校验变更前提）
4. 复审轮另加：读上一版 change-review.md 的 Finding 清单（核销后再找新 finding）

### 第二步：审查（7 维度）

- **维度 1 · AC 质量（最关键）**：对照 [../eo-shared/ac-spec.md](../eo-shared/ac-spec.md) 逐条检查——用户视角？可独立验证？技术无关且可度量（无「正常工作」类主观词）？覆盖异常路径？refactor 类是否写了「行为不变」的回归口径？
- **维度 2 · TODO↔AC 映射**：每条 TODO 标注了对应 AC 且映射成立？每条 AC 至少被一条 TODO 覆盖？越界 TODO 或悬空 AC → P0
- **维度 3 · TODO 拆解质量**：三要素齐全？占位符检测（「补充错误处理」「后续完善」→ P0）？Batch 分组合理、Batch 1 是可独立验证的 MVP？**并行组核验**（存在字母后缀批时）：文件集相交或有逻辑依赖 → P1
- **维度 4 · 粒度合规**：对照 granularity.md——超软标 P1 建议拆、超硬标 P0 必须拆；反向检查：trivial 到不该开 change → P1 建议转直改
- **维度 5 · 意图一致性**：§1 已钉决策与 §2/§5 自洽？`type` 与实际内容匹配？AC/TODO 超出 §1 意图自行扩面（镀金）→ P1 建议裁剪或转 backlog；§2 是否真是用户口吻（复述实现细节 → P1）
- **维度 6 · 条件节合规**：命中风险信号却未在 §6 记录（含豁免）→ P1；defer 超 3 条 → P1
- **维度 7 · 前提真实性抽查**：§1/§5/§6 中对现状事实、兼容性、唯一性、外部契约的断言，按不可逆性 > 数据/权限风险 > 跨模块面排序取 2-3 条定点读码核验。每条前提标基线（变更前事实审 `base_commit` 或 HEAD）。**前提不成立 → P0（必须附直接证据 file:line）；证据不足 → P1 要求补证，不猜 P0**

**定级纪律**：

- **P0 只收客观可判项**：TODO↔AC 映射断裂 / 占位符 / 粒度超硬标 / AC 不可验证 / TODO 推翻已钉决策 / 前提不成立（附直接证据）。程度与取舍类判断最高 P1
- **不确定就降级**：拿不准 P0 报 P1，拿不准 P1 报 P2；每条 P0/P1 必须落到具体位置并附可执行修复建议，给不出的不报

### 第三步：报告与速报

1. 写入 `change-review.md`（覆盖式；模板见下）。复审轮先核销上一版 Finding（fixed → verified / 回 open；`wont-fix` 项豁免不重报），新 finding 必须能指认由本轮修订引入
2. **对话速报（硬性）**：

```
结论：通过 / 不通过（P0 x 条）
P0（阻塞 implement）：
1. <一句话> — change.md §X
P1（移交起草方裁决，不阻塞）：
2. <一句话> — change.md §X
下一步：<通过 → /eo-implement（status 仍为 draft 先回 /eo-change 确认）/ 需修订 → 回 /eo-change 逐条处置后再跑本 skill 复审>
（详细分析见 <change-review.md 路径>）
```

## 固定模板 — change-review.md

```markdown
---
title: <标题> Change 审查报告
change_id: <change-id>
created: YYYY-MM-DD
summary: 一句话审查结论。
---

# <标题> Change 审查报告

> 关联：[change.md](change.md) ｜ 审查日期：YYYY-MM-DD ｜ change status：draft / confirmed
> 结论：✅ 可进入 implement / ⚠️ 小幅修订后进入 / ❌ 需大幅修订

## Finding 清单

| ID | 级别 | 摘要 | 位置 | 状态 | 处置（修订方填） |
|----|------|------|------|------|------------------|
| P0-1 | P0 | <一句话> | §3 | open / fixed / verified / wont-fix | <改动落点 或 wont-fix 理由> |

## P0 - 必须修订（阻塞 implement）
### [P0-1] <标题>
- 类型 ｜ 位置：change.md §X ｜ 描述 ｜ 影响 ｜ 建议

## P1 - 建议修订（不阻塞）

## P2 - 可选优化

## 前提真实性抽查（维度 7）

| 断言 | 基线 | 证据（file:line） | 判定 |
|------|------|------------------|------|
| <一句话前提> | HEAD | `file:line` | ✅ 成立 / ❌ 不成立 / ⚠️ 证据不足 |
```

## 关键约束

- **不改 change.md**：只产报告，修订归 `/eo-change`
- **P0 精准且客观**：只有阻塞 implement 的客观可判问题才 P0；不确定就降级
- **只有 P0 阻塞**：P1 移交起草方裁决，其修复不强制复审
- **报告覆盖式**：复审先核销再重写；wont-fix 项不重报
- **不审实施质量**（归 /eo-review）、不审业务方向本身（方向的家在 brainstorming / 意图确认）
- **可操作**：每个问题的建议必须具体到用户能直接行动
