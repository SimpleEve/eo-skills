---
name: eo-change
description: |
  变更管理技能。对某个模块发起一次业务变更：澄清意图、声明对 spec 的 Delta、拆解 TODO，一次产出即开工载体。

  USE FOR:
  - "新增" "加功能" "增强" "重构" "change" "feat" "/eo-change"
  - 任何对已有模块的业务能力变化（新增/增强/重构），产生 spec Delta 的请求
  - change 本身承载"spec 增量 + 技术方案 + TODO"，一次产出即开工载体

  NOT FOR:
  - 纯 bug 修复（change 的实施代码没按 spec 正确实现）——不产生 spec Delta，属于 eo-implement 的职责范围，在 implement/test/review 循环内解决，不要为 bug 新开 change
---

# eo-change — 模块变更

对某个模块发起一次变更。change 文档是**单一真相载体**：既是需求澄清（Delta），又是实施方案（TODO）。归档时 Delta 自动合并回模块 spec。

## 核心理念

1. **模块是一等公民**：所有 change 归属到 `eo-doc/dev/<module-name>/changes/` 下
2. **spec 是活文档**：change 不重写 spec，只声明 Delta（ADDED / MODIFIED / REMOVED）
3. **change = proposal + plan**：合并原 spec 澄清和 plan 技术方案，消除中间交接
4. **无独立 proposal-review**：作者自澄清，实施后的 code review 是唯一正式审查环节
5. **固定产出**：`eo-doc/dev/<module-name>/changes/<NNN-change-id>/change.md`

## 模板发现

启动时检查 `eo-doc/templates/`：
- 若 `project-profile.md` 存在 → 读取，了解项目类型和层级结构
- 若 `plan-layers.md`（或兼容 `change-layers.md`）存在 → 读取，启用层级 Part 模式（TODO 按层拆分）
- 若均不存在 → 使用默认 S/C/G 三分类结构

## 前置条件

- 目标模块目录 `eo-doc/dev/<module-name>/` 必须存在且含 `spec.md`（`status: confirmed`）
- 如果模块不存在 → 提示用户先执行 `/eo-module-init <module-name>` 完成模块初始化
- 如果模块 spec 存在但 `status: draft` → 提示用户先完成 spec-review

## 工作流程

### 第一步：识别模块（单模块 vs 跨模块判定）

1. 阅读用户的变更描述
2. **扫描 `eo-doc/dev/` 下所有模块的 `spec.md` frontmatter**（title / module_name / tags / summary）
3. 语义匹配出涉及的模块（可能多于 1 个），向用户确认
4. 若无匹配：提示用户走 `/eo-module-init` 创建新模块，暂停本流程
5. **关键决策：以"是否要动别人的 spec"为界**（详见下方"判断边界：单模块 vs 跨模块"）
   - 只调用别的模块、不改对方 spec → **单 change**，归主模块
   - 多个模块 spec 都需要 Delta → **拆多个 change**，每模块一个，用 `depends_on` 关联
6. 若判定为跨模块拆分 → 向用户明确说明"会产出 N 个 change"，并按 `depends_on` 顺序依次产出

### 第二步：理解变更意图

1. 阅读目标模块的 `spec.md`（了解"当前能力基线"）
2. 阅读该模块 `changes/` 下最近的 3 个历史 change（了解演化方向，避免重复/冲突）
3. 识别变更类型，按以下矩阵判断：

   | 问题 | change_type | 说明 |
   |------|-------------|------|
   | spec 有，代码**无** → 首次把 spec 实现出来 | `bootstrap` | module-init 后首批落地，或空能力首次实现 |
   | spec **无**，代码无 → 加一个 spec 里不存在的新能力 | `feature` | 真正的"加 spec"（Delta ADDED） |
   | spec 有，代码有 → 调整现有能力 | `enhance` | Delta MODIFIED 为主 |
   | spec 有，代码有 → 内部重构、对外能力不变 | `refactor` | Delta 以内部章节的 MODIFIED 为主，对外能力表不动 |

   - **`bootstrap` 的核心区别**：不改 spec，只把 spec 已声明的章节落成代码。§3 不写 Delta，改写"实现范围"（见 §3 模板的 bootstrap 分支）
   - **不接受 `fix` 作为类型**：若用户描述是"修 bug"——属于对某个已归档 change 的实施缺陷修复，不是新 change：
     - 若相关 change 尚未归档 → 让用户回到 `/eo-implement` 继续修
     - 若已归档但确实是"实现不符合 spec" → 仍走 eo-implement 开补丁式实施（不建新 change）
     - 若归档后发现的是 spec 本身错了（业务语义变化）→ 那就是真正的 `enhance`，按 enhance 处理
4. **执行模板发现**（见上方）

### 第三步：澄清（不要假设）

逐项列出模糊点，向用户澄清：
- 范围边界（In / Out of Scope）
- 对 spec 的 Delta 具体是什么
- 技术选型偏好
- 跨层协作的数据/接口细节（如多层项目）
- 回滚策略

**反复澄清直到 95% 确信**。宁可多问一轮，不要用"可能"、"应该"这类词。

### 第四步：分配 change-id

1. `cd eo-doc/dev/<module-name>/changes/` 扫描现有子目录
2. 取最大数字前缀 + 1，3 位补零（如 `001` / `002` / `037`）
3. 用户给语义名（小写 kebab-case），拼接为 `<NNN>-<kebab-name>`
4. 示例：`001-add-queue`、`002-enhance-overflow-handling`、`015-refactor-cache-layer`
5. 不接受以 `fix-` 开头的 change-id——bug 修复不应产生新 change

### 第五步：撰写 change.md

创建目录 `eo-doc/dev/<module-name>/changes/<NNN-change-id>/`，按下方模板写入 `change.md`。

### 第六步：用户确认

交付用户确认。根据反馈修订到用户满意后，保持 `status: draft`（暂不改 approved）。

### 第七步：更新索引

1. 更新 `eo-doc/dev/<module-name>/changes/INDEX.md`（模块内 change 时间线），若不存在则创建
2. 不需要立刻回写 module 的 `spec.md`——合并动作由 `eo-archive` 在归档时执行

### 第八步：提示后续流程

**关键分派**：先判断"这是首次产出还是返工修订"，两种场景提示完全不同。

#### 场景 A — 首次产出 change（本轮是作者第一次让它落地）

根据规模和风险判断是否建议走 change-review：

- **高风险 / 大规模 / 多层协作 change**（Delta ≥ 5 条，或跨 2 个以上层，或含 MODIFIED/REMOVED，或 change_type = bootstrap 认领章节 ≥ 3 个）：**建议**用户先跑 `/eo-change-review`
- **小型 / 低风险 change**（Delta ≤ 2 条，单层，全是 ADDED）：可直接 approved 进入 implement

统一提示模板：
> change 文档已就绪（`status: draft`）。后续流程：
>
> 🟡 **（可选，建议）** `/eo-change-review <change-path>` — 方案级审查（§3 合规、TODO 完整、AC 覆盖），通过后再 approve
> 1. 将 change.md `status` 改为 `approved`
> 2. `/eo-implement <change-path>` — 按 TODO 实施代码
> 3. `/eo-test <change-path>` — 测试与验证
> 4. `/eo-review <change-path>` — **实施后代码审查**（仅当 implement 已跑过）
> 5. `/eo-archive <module-name> <change-id>` — 代码审查通过后归档

#### 场景 B — 返工修订（作者根据 change-review 的 P0/P1 回来改 change.md）

⚠️ **关键：此时代码尚未实施，必须走 `/eo-change-review` 复审，不要走 `/eo-review`。**

`/eo-review` 是实施后的代码审查，需要代码已经写出来；此时根本没代码，路径走错会让 reviewer 空审。

统一提示模板（场景 B）：
> change 重写完成（`status: draft`）。既然前一轮 change-review 发现了问题，修订后请**再跑一次** `/eo-change-review <change-path>` 确认问题已收敛。
>
> 🔁 `/eo-change-review <change-path>` — 复审方案（**不是 /eo-review**；代码还没写，没东西给 /eo-review 审）
> 🔁 直到 change-review 无 P0/P1 → 用户改 `status: approved` → 进入 `/eo-implement`
>
> **禁止**此时直接改 `status: approved` 跳过复审，也**禁止**跳到 `/eo-implement` 或 `/eo-review`。

#### 如何判断是 A 还是 B

- 本 change 目录下存在 `change-review.md` 且含未解决的 P0/P1 → **场景 B**
- 否则 → **场景 A**

---

## 固定模板 — change.md

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

## 3. Spec Delta / 实现范围

> **按 `change_type` 选分支**：
> - `bootstrap` → 使用"3.B 实现范围"分支（不写 Delta，声明认领的 spec 章节）
> - `feature` / `enhance` / `refactor` → 使用"3.A Spec Delta"分支（写 ADDED / MODIFIED / REMOVED）

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

---

## changes/INDEX.md 模板

```markdown
# <module-name> 变更时间线

| 编号 | 标题 | 类型 | 状态 | 日期 | 摘要 |
|------|------|------|------|------|------|
| [001-xxx](001-xxx/change.md) | ... | feature | archived | YYYY-MM-DD | ... |
```

---

## 判断边界：change vs module-init

| 信号 | 走 eo-change | 走 eo-module-init |
|------|--------------|-------------------|
| 目标模块已存在 spec | ✅ | ❌ |
| 目标模块完全不存在 | ❌（先 init） | ✅ |
| 是对已有能力的修改 | ✅ | ❌ |
| 是全新模块的首次落地 | ❌ | ✅ |

当模块 spec 需要大规模结构性重写（Delta 占 spec 80% 以上）时，不要跳回 `eo-module-init`，而是用 `change_type: refactor` 发一个 change，逐步演化。

---

## 判断边界：单模块 vs 跨模块

**核心准则：以"是否要动别人的 spec"为界。**
一个 change 结构上只能归属一个模块，Delta 只能合并到一份 `spec.md`。跨模块需求按下表处理：

| 场景 | 归属 | 做法 |
|------|------|------|
| **A. 只调用不改契约** — 新 change 只是调用对方模块已有的接口/能力，对方 spec 不动 | **单 change**，归主模块 | §2.3 或 §4.2 列出"依赖的外部模块"；对方 spec 不产生 Delta |
| **B. 多模块 spec 都要动** — 新功能需要在多个模块的 spec 同时 ADDED/MODIFIED/REMOVED | **拆多个 change**，每模块一个 | 用 `depends_on` frontmatter 和共享命名关联 |
| **C. 只动 Proto/Config，不改业务模块 spec** | 归调用方模块 | Proto/Config 不是一等模块，归属消费侧 |

### 场景 B 的协调手段

1. **命名共享后缀**：不同模块里的 change 用相同语义尾缀，数字前缀按各自模块内递增
   - `dev/inventory/changes/007-crafting-system/`
   - `dev/building/changes/012-crafting-system/`
2. **frontmatter 加 `depends_on` / `related`**：
   ```yaml
   depends_on:
     - inventory/007-crafting-system
   related:
     - building/012-crafting-system
   ```
3. **change.md 顶部加"跨模块关联"小节**：互相链接，说明依赖方向
4. **实施时序**：被依赖方先 approve → implement → archive → 再 approve 依赖方。`/eo-workflow implement` 一次只跑一个 change，天然强制顺序

### 反模式

- ❌ **建 `dev/cross/` 虚拟模块**把跨模块需求塞进去 — 破坏"模块一等公民"，archive 无法定位目标 spec
- ❌ **建 umbrella change 引用多个子 change** — 多一层没带来收益，Delta 合并该拆还是得拆
- ❌ **单个 change 挂多个模块的 Delta** — `/eo-archive` 会拒绝（它只认单一目标 spec，见 eo-archive 的"拒绝跨模块 Delta"规则）

---

## 关键约束

- **change-id 命名**：`NNN-kebab-name`，NNN 按模块内现有 change 最大编号 +1，3 位补零
- **§3 必须填写**：
  - `feature` / `enhance` / `refactor` → 必须写至少一条 Delta（ADDED/MODIFIED/REMOVED 任一）；产生不了 Delta 大概率是 bug fix，归 implement 循环
  - `bootstrap` → 必须写"实现范围"（认领的 spec 章节列表）；不允许写 ADDED/MODIFIED/REMOVED
- **bootstrap 不重复认领**：同一模块多个 bootstrap change 不能认领同一 spec 章节；§3.B.2 必须显式声明边界
- **不写详细实现代码**：TODO 可描述接口签名 / 数据结构 / 模块职责，但不写具体函数体
- **单次聚焦**：一个 change 只做一件事；若发现混入多个不相关改动，拆成多个 change
- **状态流转**：draft → approved（用户确认）→ implementing（eo-implement 启动时改）→ done（审查通过）→ archived（eo-archive 完成）
- **不改模块 spec**：change 阶段不直接修改 `spec.md`，合并由 `eo-archive` 负责
