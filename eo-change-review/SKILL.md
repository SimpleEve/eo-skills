---
name: eo-change-review
description: |
  Change 方案审查技能。在 change 进入 implement 前，对 change.md 的 Delta 正确性、实施方案可行性、TODO 完整性做质量把关。

  USE FOR:
  - "审查 change" "review change" "change 审查" "审方案" "/eo-change-review"
  - change.md 写完 draft 后，用户希望在 implement 前做一次方案级 review
  - 发现 Delta 抄了整篇 spec、方案和 Delta 不匹配、TODO 遗漏、AC 覆盖不全等问题

  NOT FOR:
  - 代码审查 → `/eo-review`
  - spec 初次质量把关 → `/eo-spec-review`
  - bug 修复循环内的回归审查 → 留在 `/eo-implement` 内解决
---

# eo-change-review — Change 方案审查

对某个处于 `draft` 状态的 change 做方案级审查，在 implement 前把牢"方向是否正确、TODO 是否完整、Delta 是否合规"。**可选环节**——小 change 可跳过，大 change / 高风险 change / 涉及多层协作的 change 建议跑。

## 与其他 review 的关系

| Skill | 审查对象 | 问的问题 |
|-------|---------|---------|
| `eo-spec-review` | 模块 `spec.md`（活文档基线） | 需求对不对？业务自洽吗？ |
| **`eo-change-review`**（本技能） | 某个 change 的 `change.md` | 方案对不对？Delta 和实施方案一致吗？ |
| `eo-review` | change 实施后的代码 | 代码对不对？实现 vs AC？ |

三者关注点、上下文、回退动作完全不同，**不要混用**。

## 核心原则

1. **方向级审查，不替作者做决定**：审查只产出报告，方案修订由用户决定后重跑 `/eo-change`
2. **Delta 是重中之重**：change 的价值密度集中在 §3 Spec Delta；Delta 不对，后面全白做
3. **不审代码**：此时代码还没写；即使已有 spike 代码也不在审查范围
4. **固定产出**：输出到 `eo-doc/dev/<module-name>/changes/<change-id>/change-review.md`

## 前置条件

- change.md 存在于 `eo-doc/dev/<module-name>/changes/<change-id>/`
- change.md frontmatter `status` 为 `draft`（若已 approved 也允许，但提示用户通常无需再审）
- 对应模块 `eo-doc/dev/<module-name>/spec.md` 存在（审查 Delta 需要对照 spec 当前状态）

## 模板发现

启动时检查 `eo-doc/templates/`：
- 若 `project-profile.md` 存在 → 读取，了解项目层级结构
- 若 `plan-layers.md` 存在且 change 采用层级 Part 结构 → 启用**维度 6：层级 Part 合规性**
- 否则跳过维度 6

## 工作流程

### 第一步：阅读上下文 + 识别审查模式

1. 读 `eo-doc/dev/<module-name>/changes/<change-id>/change.md`（本次审查对象）
2. **从 frontmatter 读取 `change_type`**，确定审查模式：
   - `bootstrap` → **实现范围模式**（不审 Delta，审"认领范围合规性"）
   - `feature` / `enhance` / `refactor` → **Delta 模式**（审 ADDED/MODIFIED/REMOVED 合规性）
3. 读 `eo-doc/dev/<module-name>/spec.md`（模块基线）
4. 读同模块最近 3 个 change（包括 bootstrap 与 mutation 类，前者是为了核对认领边界，后者是为了避免冲突）
5. 若模块有 `doc/<module>.md`（玩法层业务文档）→ 读，理解业务背景
6. **执行模板发现**（见上方）

> ⚠️ **不要主观追问审查模式**：`change_type` 是确定性字段，必须从 change.md 直接读取并据此分派。**禁止**向用户提问"这份 change 是在改 spec 还是只是拆实施批次"——若 change.md 没填 `change_type` 或填错，应作为 P0 问题报告（"frontmatter `change_type` 缺失/不匹配"），而不是反向追问。

### 第二步：系统审查

按以下维度逐一审查：

#### 维度 1：§3 合规性（最关键）

> **按模式分派**：

**Delta 模式（feature / enhance / refactor）**：
- §3 Spec Delta 是否存在且非空？至少一条 ADDED / MODIFIED / REMOVED
- 每条 Delta 是否定位到 spec 的具体章节（`§X.Y`）？
- ADDED 条目是否真的是"新增"？（检查 spec.md 是否已有同名能力）
- MODIFIED 条目的"旧描述"是否能在当前 spec.md 中找到？（否则归档时会冲突）
- REMOVED 条目对应的能力是否真实存在于 spec.md 中？
- **反模式检测**：是不是把整段 spec 抄了一遍当成 ADDED？Delta 应该是"增量"，不是"新 spec"
  - ⚠️ 若 Delta 大段复述 spec 现有内容 → 也许根本不该是 Delta 模式，建议作者改为 `bootstrap` 类型
- **跨模块拒绝**：所有 Delta 条目的 spec 路径必须指向**本模块**；指向其他模块 → P0（详见 eo-change "判断边界：单模块 vs 跨模块"）

**实现范围模式（bootstrap）**：
- §3.B.1 是否列出认领的 spec 章节？章节引用是否真实存在于 spec.md？
- §3.B.2 是否声明了与其他 bootstrap change 的边界？
  - 扫描该模块所有 bootstrap change（draft / approved / archived），检查是否有**重复认领**同一 spec 章节
  - 若已有 bootstrap change 而本 change 的 §3.B.2 写"无" → P0
- 是否误写了 ADDED/MODIFIED/REMOVED？bootstrap 不允许写 Delta → P0
- **反模式抑制**：bootstrap 模式下"复述 spec" 是预期行为，**不报告**为反模式

#### 维度 2：§3 与实施方案一致性

**Delta 模式**：
- §4 实施方案做的事是否**完整覆盖** §3 Delta 声明的每一条能力？
- §4 是否**多做**了 Delta 未声明的事？（多做意味着有能力没进 spec，后续断层）
- §4 是否**少做**了某条 Delta？（Delta 声明了但 TODO 没有对应任务）
- 能力 ↔ TODO 映射是否清晰可追溯？

**实现范围模式（bootstrap）**：
- §4 TODO 是否完整覆盖 §3.B.1 认领的每个 spec 章节？
- §4 是否**越界**做了认领范围外的事？（越界则可能踩到其他 bootstrap change 的边界）
- 是否漏了 spec 中该章节的某些子能力？（核对 spec 该章节的全部条目）
- TODO ↔ 认领章节映射是否可追溯？

#### 维度 3：TODO 拆解完整性

- 每个 TODO 是否有明确的"描述 / 涉及文件 / 依赖 / 验收标准"？
- 依赖关系是否自洽（无循环依赖、无悬空依赖）？
- 可并行的 TODO 是否标明？（避免串行化导致工期虚高）
- TODO 颗粒度是否合理？（过粗：一个 TODO 包含 10 个子步骤；过细：一行代码一个 TODO）
- 是否漏了典型的横切任务：Proto/Config 生成、索引更新、迁移脚本、登录恢复等

#### 维度 4：AC 覆盖度

- §5 AC 是否覆盖 Delta 的每一条 ADDED / MODIFIED？
- 每条 AC 是否使用 Given-When-Then 格式？
- 是否覆盖异常路径、边界场景（不仅仅是 golden path）？
- AC 是否可测（避免"性能良好"这类不可验证的描述）？

#### 维度 5：范围与风险

- §2.1 In Scope / §2.2 Out of Scope 是否足够明确？
- **单次聚焦**：是不是混入了多个不相关改动？若是，建议拆成多个 change
- §7 影响评估（向后兼容 / 数据影响 / 依赖影响 / 回滚策略）是否填写且合理？
- §8 风险与缓解是否覆盖了方案中的关键技术风险？
- **变更类型一致性**：`change_type` 与实际改动匹配吗？
  - 宣称 `refactor` 但 §3 Delta 大量 ADDED/MODIFIED → 应改为 `feature`/`enhance`
  - 宣称 `feature` 但 §3 全是 MODIFIED → 应改为 `enhance`
  - 宣称 `feature`/`enhance` 但 Delta 在复述 spec 已有内容 → 应改为 `bootstrap`
  - 宣称 `bootstrap` 但 §3 写了 ADDED/MODIFIED/REMOVED → P0，类型或内容二选一修正

#### 维度 6：层级 Part 合规性（仅多层 Part 模式）

> 条件维度：仅当 `eo-doc/templates/plan-layers.md` 存在且 change 采用层级 Part 结构时启用。

- 每个层的 Part 是否按模板定义的结构（变更概要 / 外部依赖 / TODO 列表）填写？
- TODO 前缀是否与模板一致？
- 涉及文件是否在模板定义的目录范围内（未越界修改其他层的代码）？
- 层间依赖顺序是否符合模板的"层间依赖默认顺序"？
- 是否违反禁止事项（如在 spec 需求层写了接口签名 / 消息字段）？

### 第三步：撰写审查报告

按下方模板写入 `eo-doc/dev/<module-name>/changes/<change-id>/change-review.md`。

### 第四步：汇报结论

向用户汇报：
- 审查结论（✅ 可进入 implement / ⚠️ 小幅修订 / ❌ 需重写）
- P0/P1/P2 问题数量
- 如需修订：建议用户回到 `/eo-change` 修订 change.md 后可再跑一次 `/eo-change-review`
- 如通过：用户可将 change.md `status` 从 `draft` 改为 `approved`，进入 `/eo-implement`

---

## 固定模板 — change-review.md

```markdown
---
title: <变更标题> Change 审查报告
module: <module-name>
change_id: <NNN-change-id>
tags: [标签1, 标签2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
summary: >
  一句话概述审查结论。
---

# <变更标题> Change 审查报告

> 关联 Change：[change.md](change.md)
> 模块 Spec：[spec.md](../../spec.md)
> 审查日期：YYYY-MM-DD
> Change 状态：draft | approved

## 审查总结

一段话概述 change 整体质量，是否达到可进入 implement 阶段的标准。
明确结论：✅ 可进入 implement / ⚠️ 需小幅修订后进入 / ❌ 需大幅修订

## P0 - 必须修订（阻塞 implement）

### [P0-1] <问题标题>
- **类型**：Delta 错误 / Delta-方案不一致 / TODO 缺失 / AC 缺失 / 范围失控
- **位置**：change.md §X.Y
- **描述**：问题具体描述
- **影响**：若不修会导致 implement 阶段什么问题
- **建议**：修订方向

## P1 - 建议修订（不阻塞但影响实施质量）

### [P1-1] <问题标题>
- **类型**：Delta 粒度过粗 / TODO 依赖不清 / 风险评估遗漏 / 层间边界模糊
- **位置**：change.md §X.Y
- **描述**：问题具体描述
- **建议**：改进方向

## P2 - 可选优化（锦上添花）

### [P2-1] <问题标题>
- **类型**：措辞优化 / 分类调整 / 文档链接补充
- **描述**：建议内容

## §3 合规性检查

> 按 `change_type` 选一种表格填写：

**Delta 模式表（feature / enhance / refactor）**

| Delta 条目 | 类型 | spec 定位 | 状态 | 备注 |
|-----------|------|-----------|------|------|
| <能力名1> | ADDED | §X.Y | ✅ / ⚠️ / ❌ | ... |
| <能力名2> | MODIFIED | §X.Y | ✅ / ⚠️ / ❌ | 旧描述在 spec 中是否存在 |
| <能力名3> | REMOVED | §X.Y | ✅ / ⚠️ / ❌ | ... |

**实现范围表（bootstrap）**

| 认领章节 | 认领范围 | 章节是否存在 | 是否被其他 bootstrap 认领 |
|---------|---------|------------|-------------------------|
| spec §3.1 | 完整 / 子集 | ✅ / ❌ | ✅ 无冲突 / ❌ 与 `NNN-xxx` 重叠 |

## §3 ↔ TODO 映射检查

> Delta 模式填"Delta 条目"；bootstrap 模式填"认领章节"。

| §3 条目 | 对应 TODO | 覆盖状态 |
|--------|-----------|---------|
| ADDED-1 / §3.1 | TODO-S1, TODO-C2 | ✅ 完整覆盖 / ⚠️ 部分覆盖 / ❌ 遗漏 |

## AC 覆盖检查

| Delta 条目 | 对应 AC | 覆盖状态 |
|-----------|---------|---------|
| ADDED-1 | AC-1, AC-2 | ✅ 已覆盖 / ❌ 缺失 / ⚠️ 不完整 |

## 结构完整性检查

| 章节 | 状态 | 备注 |
|------|------|------|
| §1 变更意图 | ✅ / ❌ / ⚠️ | ... |
| §2 范围（In/Out Scope） | ✅ / ❌ / ⚠️ | ... |
| §3 Spec Delta | ✅ / ❌ / ⚠️ | ... |
| §4 实施方案 / TODO | ✅ / ❌ / ⚠️ | ... |
| §5 验收标准 | ✅ / ❌ / ⚠️ | ... |
| §6 测试标准 | ✅ / ❌ / ⚠️ | ... |
| §7 影响评估 | ✅ / ❌ / ⚠️ | ... |
| §8 风险与缓解 | ✅ / ❌ / ⚠️ | ... |
```

---

## 关键约束

- **不改 change.md**：审查只产出报告，修订由用户回到 `/eo-change` 执行
- **P0 精准**：只有真正会阻塞 implement / 导致返工的问题才标 P0
- **不重复 spec-review**：不审 spec 本身的业务合理性（那是 spec-review 的职责）；只审"本次变更是否合规"
- **不审代码**：即使 change 附带了 spike 代码也不评价代码本身
- **模式分派是确定性的**：`change_type` 是什么就按什么审，不向用户追问模式归属；`change_type` 缺失/错填 → P0 报告
- **避免触发钩子噪声**：报告中避免使用"关键决策""critical decision"等字样（会触发上游 CLAUDE.md 的 decisions/ 捕获钩子），用"设计判断""模式选择"代替
- **可操作**：每个问题的建议必须具体到用户能直接行动
