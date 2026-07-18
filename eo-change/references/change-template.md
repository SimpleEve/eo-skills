# change.md 固定模板（v2）

eo-change 按下方模板写入 `eo-doc/changes/<NN>-<slug>/change.md`（目录 = seq 补零前缀 + slug；身份是 slug，见 [eo-shared/conventions.md](../../eo-shared/conventions.md) §2）。

必填仅 §1-§4。§5-§8 是**条件节**：满足触发条件才写，不满足整节省略（连标题都不留）。如果写出来的 change.md 明显超过本模板量级，先查 [eo-shared/granularity.md](../../eo-shared/granularity.md) 的硬指标。

```markdown
---
id: batch-export     # slug 即身份（commit 前缀/stub 文件名用它），首个 commit 后不可改名
seq: 14              # 显示序号（#14），补零作目录前缀 14-<slug>/；撞号自愈见 conventions.md §2
title: 批量导出
summary: <一句话意图，≤50 字，纯文本>   # INDEX 摘要列与看板 stub 卡面的单一来源
status: draft        # draft | confirmed | implementing | reviewed | archived（skill 自动流转，用户不手改）
type: feature        # bootstrap | feature | enhance | refactor
base_commit: ~       # eo-implement 首次执行时写入
commits: []          # eo-archive 归档时写入（仅审计用，不决定同步范围）
issue: ~             # GitHub 联动开启时，confirmed 后回写 issue 号
pr: ~                # PR 创建后回写 URL
created: 2026-07-07
---

# <标题>

## 1. 意图

<为什么做，1-3 段，含用户原话要点。>

已钉决策（来自起草澄清 / brainstorming 捕获）：
- <决策面> → <结论>（理由：…）
- <决策面> → <结论>（假设，用户未逐条确认）

## 2. 验收清单

<!-- 规范见 eo-shared/ac-spec.md：用户视角、可独立验证、技术无关、覆盖异常路径；能自动验的不写成人工 -->
- [ ] AC-1 <用户能……>（验证：<操作 + 预期观察>）
- [ ] AC-2 <当……失败时，用户看到……>（验证：……）
- [ ] AC-3 <体验/观感类>（人工:<做什么 → 过目什么>）

## 3. TODO

<!-- 3-7 条理想 / 10 条硬上限；每条四要素；禁止占位符；按 Batch 分组，Batch 1 = MVP -->

### Batch 1（MVP）
- [ ] TODO-1 <描述>（文件：…；对应 AC-1；完成判据：…）
- [ ] TODO-2 <描述>（文件：…；对应 AC-2；完成判据：…）

### Batch 2
- [ ] TODO-3 <描述>（文件：…；对应 AC-3；完成判据：…）

## 4. 涉及文件

- `path/to/file` — <改动性质一句话>

<!-- ============ 以下为条件节，满足触发条件才写 ============ -->

## 5. 技术方案

<!-- 触发（任一成立才写，都不满足 → 整节省略）：新架构模式 / 新外部依赖 / 安全・性能・数据迁移复杂度。
     判据须可证伪——「编码前有歧义」这类恒真描述不构成触发；有歧义应在第三步澄清掉，而非落进本节。 -->

## 6. 流程图

<!-- 触发：状态机、多角色交互等「画比说清楚」的场景。规范见 eo-doc-manager/references/mermaid.md -->

## 7. 风险与回滚

<!-- 触发：不可逆操作 / 数据迁移 / 对外接口变更 -->

## 8. 开放问题

<!-- 触发：决策台账存在 defer 项（上限 3 条）；或归档时的 AC 豁免记录 -->
- OQ-1 <问题>（defer 原因：…）
```

## type 字段说明

| type | 语义 |
|------|------|
| `bootstrap` | 从零起步（新项目 / 新能力首开），无存量代码约束。**仅是标记**，无任何特殊章节或认领机制 |
| `feature` | 新增用户可见能力 |
| `enhance` | 调整已有能力 |
| `refactor` | 内部重构，用户可见行为不变（AC 写「行为不变」的回归口径） |

**无 `fix` 类型**：bug 修复走 `/eo-fix`——有活跃 change 时计入该 change；trivial 直改；实为需求变更才新开 change。
