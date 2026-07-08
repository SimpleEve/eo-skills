---
name: eo-review
description: |
  对已实施的代码做审查：AC 逐条核对 + 代码质量，产出 P0/P1/P2 分级报告（前提：代码已实现）。触发：review / 代码审查 / /eo-review。
  NOT FOR: change 方案审查（/eo-change-review，代码还没写时用）。
---

# eo-review — 代码审查

根据 change 文档（验收清单 + TODO）对**已实施的代码**进行审查，产出结构化审查报告。

> **定位**：`eo-review` 只审代码。审查范围前移（审 change 方案）请用 `/eo-change-review`。两种 review 关注点、上下文、产出物都不同，不要混用。
>
> | Skill | 审查对象 | 产出 |
> |-------|---------|------|
> | `/eo-change-review` | change.md（implement 前） | `change-review.md` |
> | **`/eo-review`**（本技能） | change 实施后的代码 | `review.md` |

## 核心原则

1. **AC 是检查表**：change.md §2 验收清单逐条核对实现覆盖（规范见 [../eo-shared/ac-spec.md](../eo-shared/ac-spec.md)）
2. **最佳实践审查**：代码质量、命名、架构合理性
3. **结构化产出**：P0/P1/P2 分级，输出到 `eo-doc/changes/<change-id>/review.md`
4. **通过即流转**：审查通过（无 P0/P1）时把 change.md `status` 置 `done`（skill 自动写入）

## 前置条件

- **必须能找到 `.eo-project.json`**。找不到 → 报错退出，提示运行 `/eo-project-init`
- `eo-doc/changes/<change-id>/change.md` 存在，**相关代码已实现**（TODO 至少部分勾选），status 为 `implementing` 或 `done`

### 前置拦截（硬性）

发现以下任一信号，**立即停止并纠偏**，不要开始审查：

| 信号 | 含义 | 正确路径 |
|------|------|---------|
| change.md `status: draft` / `confirmed` 且 TODO 全未勾选 | 代码还没开工 | 先 `/eo-implement`；审方案走 `/eo-change-review` |
| 用户描述是「审查 change 方案」/「implement 之前再看看」 | 要的是方案审查 | `/eo-change-review`（**不是本 skill**） |
| 用户描述是「change 重写后再看看」 | 代码未变，只是 change.md 改了 | `/eo-change-review` |

纠偏反馈模板：
> ⚠️ `/eo-review` 是**实施后的代码审查**，需要代码已经写出来。你当前的情况是 `<信号>`——应走 `/eo-change-review`（审 change.md 本身：AC / TODO 是否合规，implement 之前）。

## 工作流程

### 第一步：阅读上下文

1. `eo-doc/changes/<change-id>/change.md`：§1 意图与已钉决策、§2 AC、§3 TODO、条件节（§5 方案 / §7 风险若存在）
2. 经 `eo-doc/agent-handbook/INDEX.md` 定位相关代码地图，理解既有架构与模式
3. 本次实施的 diff（按 frontmatter `base_commit` 起算，或 `[<change-id>]` 前缀的提交）

### 第二步：确定条件维度

- 涉及 UI 且仓库根存在 `DESIGN.md` → 启用维度 6（设计一致性）
- 否则只跑维度 1-5

### 第三步：代码审查

- **维度 1 · 验收覆盖**：§2 每条 AC 逐条核对实现与验证方式；每条 TODO 的完成判据是否真实达成；有无遗漏边界场景
- **维度 2 · 逻辑正确性**：核心逻辑、异常处理、边界条件；竞态/死锁/资源泄漏/生命周期
- **维度 3 · 架构合规**：分层、模块边界、依赖方向；职责单一、无不合理耦合
- **维度 4 · 代码规范**：命名一致、类型严格（无随意 `any`）、重复代码、公共 API 注释
- **维度 5 · 安全与性能**：注入/越权/敏感信息暴露；明显性能瓶颈
- **维度 6 · 设计一致性（条件）**：UI 实现的字体/色值/间距/圆角是否符合 `DESIGN.md`；发现色板外颜色、刻度外魔法数标 P1

### 第四步：报告与速报

1. 按 [references/review-template.md](references/review-template.md) 写入 `eo-doc/changes/<change-id>/review.md`
2. 无 P0/P1 → 将 change.md `status` 置 `done`；联动钩子刷新 stub（[../eo-shared/board-github.md](../eo-shared/board-github.md)，未开启跳过）
3. **对话速报（硬性——缺速报 = 流程未完成）**：

```
结论：通过 / 不通过（P0 x 条）/ 有保留通过（P1 x 条）
P0（阻塞）：
1. <一句话> — <file:line>
P1（应修）：
2. <一句话> — <file:line>
P2（可后置）：
3. <一句话>
下一步：<回 /eo-implement 修复后复审 / 可进入 /eo-archive>
（详细分析见 <review.md 路径>）
```

无某级问题整行省略；全绿压缩为「结论 + 下一步」两行；每条一句话 + 定位，不展开分析。

## 关键约束

- **客观公正**：基于 AC 和最佳实践，不做主观偏好评判
- **定位精确**：必须给出文件路径和行号
- **不直接改代码**：只产报告，修复归 `/eo-implement`
- **分级清晰**：P0 仅限阻塞性问题
- **status 自动流转**：通过时本 skill 写 `done`，不要求用户手改
