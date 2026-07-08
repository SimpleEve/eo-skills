# Lessons 生产与消费规范（单一来源）

> 生产方：eo-project-lesson。消费方：eo-change / eo-implement / eo-fix（启动时）。目标：教训在**下次相关任务开始时自动出现**，而不是躺在目录里等人想起。

## 1. 消费流程（eo-change / eo-implement / eo-fix 启动时执行）

1. 读 `<project_root>/lessons/INDEX.md`——**不存在则整步跳过，零成本**（不要 ls 目录逐个翻文件）
2. 用当前任务的关键词（涉及的 API / 文件路径模式 / 场景词 / 技术栈）匹配 INDEX 各行的 `trigger` 与 `tags`
3. 命中 ≤3 条 → 只读对应文件的 **`## 规则`** 节（结论前置的设计就是为此）；命中更多 → 按相关度取前 3
4. `status: superseded` 的条目跳过
5. **显式消费**：把采纳的教训带进产出——change 的 §1 已钉决策可标注「（源自 lesson: <文件名>）」；fix 直接引用规则作为假设先验。不采纳也不必解释

## 2. 生产格式（eo-project-lesson 写入）

文件：`<project_root>/lessons/<YYYY-MM-DD>-<slug>.md`。**结论前置**：给 agent 的部分在前，给人的叙事在后。

```markdown
---
type: lesson
category: pitfall | best-practice | surprise
project: <项目名>
date: YYYY-MM-DD
status: active          # active | superseded
tags: [具体技术词, 场景词]
trigger: 涉及 <API/文件模式/场景> 时         # 一句话：什么时候该想起这条
summary: <一句话教训本体>
---

# <一句话标题（陈述规则，不是描述事件）>

## 规则

<下次怎么做，直接可执行的 3-5 条。这是 agent 消费的部分，写祈使句>

## 适用条件

<什么情况下适用 / 什么情况下不适用（防误用）>

## 背景

<发生了什么、为什么会这样。给人看的叙事，放最后，可以长>
```

要点：
- `trigger` 和 `summary` 是检索锚点，**必填**；tags 用具体技术词（`fairygui` / `import-cycle`），不用空泛词（`bug` / `经验`）
- 标题写成规则（「虚拟列表复用必须清旧监听」），不写成事件（「记一次列表 bug」）
- **允许状态修订**：教训被证伪/被更好方案取代 → 原文件 `status` 改 `superseded` 并在顶部加一行指向新条目；不删除文件（其余内容仍不可改，补充走新建）

## 3. INDEX.md（生产方每次写入时维护）

```markdown
# Lessons 索引

| 日期 | 标题 | 类别 | trigger | status |
|------|------|------|---------|--------|
| 2026-05-07 | [虚拟列表复用必须清旧监听](2026-05-07-fgui-virtual-list-stale-handlers.md) | pitfall | 涉及 GList.SetVirtual/AddItemFromPool 时 | active |
```

- 一行 ≈ 50 token，消费方扫一次即覆盖全集
- 存量 lessons 无 INDEX / 缺 trigger·summary 时：eo-project-lesson 的 `reindex` 动作负责补建（读各文件正文提炼 trigger/summary 回填 frontmatter + 生成 INDEX，正文不动）
