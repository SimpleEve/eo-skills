# change.md 固定模板

eo-change 按下方模板写入 `eo-doc/dev/<module-name>/changes/<NNN-change-id>/change.md`。

```markdown
---
title: <变更标题>
module: <module-name>
change_id: <NNN-change-id>
change_type: bootstrap | feature | enhance | refactor
tags: [标签1, 标签2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: draft | approved | implementing | done | archived
summary: >
  一句话描述变更内容和动机。
---

# <变更标题>

> 所属模块：[<module-name>](../../spec.md)
> 变更编号：<NNN-change-id>
> 变更类型：bootstrap / feature / enhance / refactor
> 创建日期：YYYY-MM-DD

## 1. 变更意图（Why）

为什么要做这个变更？问题现象、业务驱动或改进动机是什么？
（1 段话即可，避免冗长背景。）

## 2. 范围（What）

### 2.1 In Scope
- 本次做什么
- ...

### 2.2 Out of Scope
- 本次明确不做什么
- ...

### 2.3 涉及文件（预估）
- `path/to/file1`
- `path/to/file2`

### 2.4 流程图（变更后完整流程 + Delta 高亮）

> **必画条件**：本 change 涉及用户操作流程、状态流转、多模块交互，或 Delta 中含 MODIFIED/REMOVED。
> **跳过条件**：纯配置/文案/样式；Delta 仅 1 条 ADDED 且不涉及流程分支。跳过时写一行理由。
> 规范见 [eo-doc-manager/references/mermaid.md](../../../../../eo-doc-manager/references/mermaid.md)。
>
> 画的是"变更后的完整流程"（非 diff）。用 classDef 高亮本次改动：
> - 新增节点 `:::new`
> - 修改节点 `:::changed`
> - 外部模块节点 `:::extern`
> - 删除的节点不画，在图下方用 `> 移除：<原节点名> —— <原因>` 说明

```mermaid
flowchart TD
    %% 按实际业务替换
    classDef new fill:#d4edda,stroke:#28a745,stroke-width:2px
    classDef changed fill:#fff3cd,stroke:#ffc107,stroke-width:2px
    classDef extern fill:#e9ecef,stroke:#6c757d,stroke-dasharray:5 5
```

## 3. Spec Delta / 实现范围

> **按 `change_type` 选分支**：
> - `bootstrap` → 使用"3.B 实现范围"分支（不写 Delta，声明认领的 spec 章节）
> - `feature` / `enhance` / `refactor` → 使用"3.A Spec Delta"分支(写 ADDED / MODIFIED / REMOVED)

---

### 分支 A — Spec Delta（feature / enhance / refactor）

> 归档时由 eo-archive 机械合并回 `spec.md`。至少一条 ADDED / MODIFIED / REMOVED。

#### 3.A.1 ADDED（新增能力）
- **<能力名>**：描述。定位到 spec 的章节（如 "§3.3 核心行为"）。
- ...

#### 3.A.2 MODIFIED（修改能力）
- **<能力名>**：
  - 旧：<spec 原描述>
  - 新：<修改后描述>
  - 位置：spec §X.Y
- ...

#### 3.A.3 REMOVED（移除能力）
- **<能力名>**：移除原因。位置：spec §X.Y
- ...

---

### 分支 B — 实现范围（bootstrap）

> **bootstrap change 不改 spec，不产生 Delta**。spec 已经声明了能力，本 change 只是把它们落成代码。
> 归档时 eo-archive 跳过 Delta 合并，仅更新 §9 关联变更 / §10 变更记录。

#### 3.B.1 认领的 spec 章节

列出本 change 要实现 spec 的哪些章节（**粒度到节级或能力级**）：

- `spec.md §3.1 <章节名>` — 本 change 完整实现
- `spec.md §3.3 <章节名>` — 本 change 仅实现子集（具体见 §4 TODO）
- ...

#### 3.B.2 与其他 bootstrap change 的边界

若该模块已有其他 bootstrap change（无论 draft 还是 archived），**必须**列出相互间的划界：

- 本 change 认领 §3.1 / §3.2
- 已归档的 `001-xxx` 认领了 §4.1 / §4.2
- **不得重复认领**同一 spec 章节；若粒度需要细分，精确到子节或条目

若无其他 bootstrap change，写"无"。

## 4. 实施方案（How）

### 4.1 技术方案概述
1-3 段话概述整体思路。

### 4.2 外部/内部依赖
- 外部：第三方库 / 服务 / SDK / 引擎能力
- 内部：依赖的已有模块、接口、配置

### 4.3 TODO 拆解

> **模式选择**：若 `eo-doc/templates/plan-layers.md` 存在 → 用**模式 B（层级 Part）**；否则用**模式 A（默认 S/C/G）**。
> 小型 fix 允许只有 1–2 条 TODO。

#### 模式 A — 默认三分类

##### 核心逻辑 / Runtime

- [ ] **TODO-S1: <任务标题>**
  - **描述**：做什么
  - **涉及文件**：`path/to/file`
  - **依赖**：前置 TODO（无则写"无"）
  - **验收标准**：完成后如何验证

##### 表现层 / Tooling

- [ ] **TODO-C1: <任务标题>**
  - ...

##### 共享 / 通用

- [ ] **TODO-G1: <任务标题>**
  - ...

#### 模式 B — 层级 Part（plan-layers.md 存在时）

按模板定义的层生成，每层一个 Part。层名称、TODO 前缀、涉及目录、可参考文档均从模板读取。

```
### Part N: [层名称]（TODO 前缀: [前缀]）

> 涉及范围：[模板定义的文件/目录范围]
> 可参考文档：[模板定义的 skill 列表]

#### 变更概要
该层在本次 change 中要做什么（1-3 句）。

#### 外部依赖
该层依赖其他层的哪些产出。

- [ ] **[前缀]-1: <任务标题>**
  - **描述**：...
  - **涉及文件**：...
  - **依赖**：...
  - **验收标准**：...
```

层间执行顺序由模板的"层间依赖默认顺序"定义。

### 4.4 依赖关系与执行顺序

用文字或 ASCII 图描述 TODO 依赖，标明哪些可并行。

示例：
- TODO-G1 → TODO-S1（G1 完成后 S1 才能开始）
- TODO-S2 ‖ TODO-C1（可并行）

## 5. 验收标准（AC）

使用 Given-When-Then 格式：
- **AC-1**
  - Given <前置条件>
  - When <用户操作>
  - Then <期望结果>

> **bootstrap 提示**：若 spec 本身已有 AC 章节（§5），bootstrap change 的 AC 应**直接引用**对应 spec AC（如 "AC-1 ≡ spec §5.AC-3"），避免复述。若认领的 spec 章节没有 AC，则补全。

## 6. 测试标准

### 6.1 单元测试覆盖点
逐条列出每个 TODO 需要的单元测试。

### 6.2 集成 / 场景验证
前置条件 / 操作步骤 / 期望结果 / 异常场景。

## 7. 影响评估

- **向后兼容**：是 / 否（如否，说明破坏点）
- **数据影响**：是 / 否（如是，说明迁移策略）
- **依赖影响**：列出受影响的其他模块
- **回滚策略**：一旦实施失败，如何回滚

## 8. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|

## 9. 开放问题

列出尚未解决的问题。若无则标"无"。

## 10. 实施记录

> 此章节由 eo-implement / eo-test / eo-review 增量追加，change 作者初始不需要填。

- **实施日期**：
- **偏差记录**：链接 `implement.md`（若有）
- **测试报告**：链接 `test.md`
- **审查报告**：链接 `review.md`
- **归档日期**：
```
