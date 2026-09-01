---
name: eo-review
description: |
  按需代码审查：风险信号命中或用户点名时，对已实施代码做 AC 逐条核对 + 代码质量审查，产简版 review.md（P0/P1/P2）。触发：review / 代码审查 / 再找双眼睛看看 / /eo-review。
  NOT FOR: change 方案审查（/eo-change-review，代码还没写时用）；默认主路（无信号时不强制）。
---

# eo-review — 代码审查（按需闸门）

本 skill 是**可选闸门**。根据 change.md（验收清单 + TODO）对**已实施的代码**做独立审查，产出简版报告。

> 与 /eo-change-review 的区别：本 skill 审**代码**（implement 之后）；change-review 审**方案**（implement 之前）。两者都是按需闸门，不是必经节点。

## 核心原则

1. **AC 是检查表**：change.md §2 逐条核对实现覆盖
2. **最佳实践审查**：代码质量、命名、架构合理性
3. **简版报告**：结论 + P0/P1/P2 清单，输出到 `eo-doc/changes/<change-id>/review.md`；复审**覆盖重写**（历史由 git 兜）
4. **通过即流转**：审查通过（无未决 P0/P1）时把 change.md `status` 置 `reviewed`（可选状态，只有本 skill 写）
## 对抗立场

**默认这份实现有罪**——审查的目标是推翻它，不是确认它：主动构造反例、对抗输入与边界组合去戳每条 AC 和关键实现路径。「没发现问题」不是结论，「试图推翻但失败」才是——报告须能列出试过的攻击面（构造过的对抗输入、核验过的前提、推演过的失败路径）；列不出攻击面的审查视为没做。

## 前置条件

- **必须能找到 `.eo-project.json`**。同目录存在 `.eo-project.local.json` 时顶层字段覆盖合并（local 优先）。找不到 → 报错退出，提示运行 `/eo-project-init`
- `eo-doc/changes/<change-id>/change.md` 存在，**相关代码已实现**（TODO 至少部分勾选），status 为 `implementing` 或 `reviewed`
- 调用依据：§6 信号命中未豁免 / 用户显式点名。都没有 → 告知默认主路不需要本闸门，确认仍要跑再继续

### 前置拦截（硬性）

| 信号 | 正确路径 |
|------|---------|
| change.md `status: draft` / `confirmed` 且 TODO 全未勾选 | 先 `/eo-implement`；审方案走 `/eo-change-review` |
| 用户描述是「审查 change 方案」/「implement 之前再看看」 | `/eo-change-review`（不是本 skill） |
| 用户描述是「实施后发现方案/架构不对」 | eo-change **回炉子流程**（不是本 skill） |

## 工作流程

### 第一步：阅读上下文

1. `eo-doc/changes/<change-id>/change.md`：§1 意图与已钉决策、§2 AC、§5 TODO、§6 风险
2. 相关代码定位：`.codegraph/` 索引存在则 `codegraph explore` 优先召回；不存在则按目录收敛 + 源码直读
3. 本次交付的 diff（按 frontmatter `base_commit` 起算，或 `[<change-id>]` 前缀提交）

### 第二步：代码审查

- **维度 1 · 验收覆盖**：§2 每条 AC 逐条核对实现与证据；**反向核对**：diff 中映射不到任何 AC/TODO 的行为新增（镀金）→ P1 建议裁剪或转 backlog
- **维度 2 · 逻辑正确性**：核心逻辑、异常处理、边界条件；竞态/死锁/资源泄漏/生命周期
- **维度 3 · 架构合规**：分层、模块边界、依赖方向；职责单一、无不合理耦合
- **维度 4 · 代码规范**：命名一致、类型严格、重复代码；**注释纪律**（项目 `eo-doc/agent-handbook/comments.md`，未启用时以行内标准：溯源标注与叙事辩护）只作观察——发现流程溯源标注或叙事辩护注释 → P2，不阻塞
- **维度 5 · 安全与性能**：注入/越权/敏感信息暴露；明显性能瓶颈
- **维度 6 · 设计一致性（条件）**：涉及 UI 且仓库根有 `DESIGN.md` → 字体/色值/间距/圆角符合性；色板外颜色、刻度外魔法数标 P1

finding 标根因：业务源码归 `implementation`；测试本身的问题归 `test-asset`；验收口径或方案本身有误归 `requirement`。

### 第三步：报告与速报

1. 按 [references/review-template.md](references/review-template.md) 写入 `review.md`（覆盖式：复审先核销上一版未决清单——fixed 按修复 commit 复验 → verified / 回 open，再加上新发现；用户当场裁决不修的标 `waived` 附原话，不阻塞）
2. **status 流转（双向都归本 skill）**：无未决 P0/P1 → change.md `status` 置 `reviewed`；有 P0/P1 且当前已是 `reviewed`（复审翻车）→ 当场置回 `implementing`
3. **对话速报（硬性）**：

```
结论：通过 / 不通过（P0 x 条）/ 有保留通过（P1 x 条）［基线 <short-sha>］
P0（阻塞）：
1. <一句话> — <file:line>
P1（应修）：
2. <一句话> — <file:line>
下一步：<implementation finding → /eo-fix 循环内分支；requirement → /eo-change 回炉或精化；通过 → /eo-archive>
📋 <通过且存在 acceptance.md 时：可以人工验收了：<路径>（说「带我验收」可逐项走查）；否则省略此行>
（详细报告见 <review.md 路径>）
```

## 关键约束

- **客观公正**：基于 AC 和最佳实践，不做主观偏好评判
- **定位精确**：必须给出文件路径和行号
- **不直接改交付物**：只产报告；修复归 `/eo-fix` 循环内分支，需求口径归 `/eo-change`
- **分级清晰**：P0 仅限阻塞性问题
- **status 自动流转（双向）**：通过置 `reviewed`；复审翻车当场回退 `implementing`
