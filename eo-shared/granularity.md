# 粒度规范：硬指标、trivial 判据、拆分决策表（单一来源）

> 被 eo-change / eo-fix / eo-change-review 引用。目标：「一个 change 只做一件事」从软规则变成可校验的数字。

## 1. change 粒度硬指标（采用 spec-kitty 数值，试运行）

| 指标 | 理想 | 硬上限 | 超限动作 |
|------|------|--------|---------|
| TODO 数 | 3-7 | 10 | **必须**拆 change 序列 |
| change.md 全文 | 200-500 行 | 700 行 | **必须**拆 change 序列 |

- 校验时机：eo-change 收尾自检（`wc -l` + 数 TODO），超软标建议拆、超硬标**拒绝确认**；eo-change-review 复查同项。
- 量化理由（spec-kitty 原文）：超过 700 行 agent 会丢细节、跳步骤；200-500 行恰好装下全部上下文。
- 拆分方式：按 AC 分组切成序列，第一个 = MVP，其余排入 changes/INDEX.md 队列或 backlog。

## 2. trivial 硬判据（直改模式短路）

**同时满足**以下四条 → 不开 change，走直改模式（改完常规 commit，由 doc-manager cursor sync 兜底归档）：

1. 不改变用户可见的**功能语义与交互逻辑**（纯外观/样式、文案、多语言、重命名、格式化、显而易见的小 bug 修复都算 trivial）；
2. 不改对外接口、不动持久化数据结构；
3. **无需方案权衡**——不产生值得记录的技术决策（一旦要做选型或权衡，就有了开 change 的理由）；
4. 单次会话可完成。

任何一条不满足 → 升级 change 模式。**文件数不设限**：按需求性质判定——多语言、全局样式调整可涉及几十个文件仍是 trivial；反之 3 个文件的逻辑重构也不是。文件数只作提示信号（量大且非机械同质时确认一句）。

直改护栏：UI 直改仍受 DESIGN.md 约束（改前读）；commit 建议带 `fix:` / `ui:` 前缀（见 conventions.md）；**不引入「light change」中间工件**。

## 3. 更新 vs 新开决策表（借 OpenSpec）

> **"Update preserves context. New change provides clarity."**

| 情形 | 动作 |
|------|------|
| 意图相同的精化：发现边缘情况、方法微调、范围缩到 MVP | **就地更新**本 change |
| 意图本质变化 / 与原范围重叠 <50% / 原 change 可独立收尾 | **新开 change** |

## 4. TODO 质量底线

- 每条 TODO 三要素：描述 / 涉及文件 / 对应 AC。
- **完成判据是条件要素**：仅当多条 TODO 对应同一条 AC（单条完成 ≠ 该 AC 可验）时逐条写；一对一映射不写——默认判据 = 所在批末该 AC 验证通过。验证信息只在 AC 层写一遍，不在 TODO 层复述。
- **禁止占位符**：出现「补充错误处理」「后续完善」「implement later」这类词即判定拆解失败，必须写实。
- 按 Batch 分组，Batch 1 = MVP，批间可独立验证对应 AC（STOP and VALIDATE）。
