# change.md 固定模板（v3）

eo-change 按下方模板写入 `eo-doc/changes/<NN>-<slug>/change.md`（目录 = seq 补零前缀 + slug；身份是 slug，见 [eo-shared/conventions.md](../../eo-shared/conventions.md) §2）。

v3 单一形态（轻/全档已合并）：**必填 = §1-§4**（四问骨架，用户是第一受众）；§5 技术备注是 implementer 视角的折叠节；§6 是条件节，满足触发条件才写。如果写出来的 change.md 明显超过本模板量级，先查 [eo-shared/granularity.md](../../eo-shared/granularity.md) 的硬指标。

```markdown
---
id: batch-export     # slug 即身份（commit 前缀/stub 文件名用它），首个 commit 后不可改名
seq: 14              # 显示序号（#14），补零作目录前缀 14-<slug>/；撞号自愈见 conventions.md §2
title: 批量导出
summary: <一句话意图，≤50 字，纯文本>   # INDEX 摘要列与看板卡面的单一来源
status: draft        # draft | confirmed | implementing | reviewed | archived（skill 自动流转，用户不手改；reviewed 可选）
type: feature        # bootstrap | feature | enhance | refactor
base_commit: ~       # eo-implement 首次执行时写入
commits: []          # eo-archive 归档时写入（仅审计用，不决定同步范围）
issue: ~             # eo-sync 同步时由 github 适配器回写号（confirmed 起）
pr: ~                # eo-sync 归档同步回写 URL
created: 2026-08-15
---

# <标题>

## §1 解决什么问题

<!-- 为谁解决什么问题、为什么现在做。1-3 句人话，含用户原话要点。
     已钉决策（来自起草澄清 / brainstorming 捕获）跟在意图后： -->

已钉决策：
- <决策面> → <结论>（理由：…）

## §2 完成后我应该看到什么

<!-- AC 规范见 eo-shared/ac-spec.md：演示脚本口吻 + 归属标注 + 阻塞标注；能自动验的不写成人工；
     至少 1 条异常路径；条数不模板化。缺省即阻塞，非阻塞显式标 -->
- [ ] AC-1 [自动] 打开导出对话框选中多条，点导出后得到 `<项目名>-<日期>.zip`，行数等于选中数
- [ ] AC-2 [自动] 当选中数为 0 时点导出，看到「请先选择条目」提示且不产生文件
- [ ] AC-3 [人工·非阻塞] 导出完成提示不遮挡列表内容（人工:导出一次过目提示位置）

## §3 谁验收、按什么标准

<!-- 自动项：跑什么命令 / 看什么输出（增量制——§2 声明已说清的此处不重复）；
     人工项：指向验收单（implement 完成时生成）。小 change 两三句即可 -->
- 自动项：eo-implement 批末逐条执行，命令 + 关键输出留在速报
- 人工项（AC-3）：归档前照 acceptance.md 过目勾选

## §4 不通过怎么办

<!-- 缺省写法如下，只有需要定制时才改写 -->
- 阻塞项不通过 → 禁止归档：回 /eo-implement 修复，方案本身要改则回炉
- 非阻塞项不通过 → 记 backlog 继续，不挡归档

## §5 技术备注（implementer 视角）

<!-- TODO 3-7 条理想 / 10 条硬上限；每条三要素（描述/文件/对应 AC）；
     按 Batch 分组，Batch 1 = MVP（跑完即可独立验证其对应 AC）；
     互不干扰的批可标同层并行组（字母后缀 Batch 2a/2b，判据见 granularity §6）；纯数字 = 串行 -->

### Batch 1（MVP）
- [ ] TODO-1 <描述>（文件：path/to/a.ts；对应 AC-1）

### Batch 2
- [ ] TODO-2 <描述>（文件：…；对应 AC-2）

<!-- ============ 以下为条件节，满足触发条件才写 ============ -->

## §6 风险与开放问题

<!-- 触发（任一）：命中风险信号（granularity §5，含用户豁免记录）/ 不可逆操作与回滚 /
     defer 的开放问题（上限 3 条）/ 归档时的 AC 豁免记录 -->
- <信号或豁免一句：什么信号、挂/豁免了哪个闸门、日期>
- OQ-1 <开放问题>（defer 原因：…）
```

## type 字段说明

| type | 语义 |
|------|------|
| `bootstrap` | 从零起步（新项目 / 新能力首开），无存量代码约束。仅是标记，无特殊章节 |
| `feature` | 新增用户可见能力 |
| `enhance` | 调整已有能力 |
| `refactor` | 内部重构，用户可见行为不变（AC 写「行为不变」的回归口径） |

**无 `fix` 类型**：bug 修复走 `/eo-fix`——有活跃 change 时计入该 change；trivial 直改；实为需求变更才新开 change。
