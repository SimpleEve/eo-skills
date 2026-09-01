# Research 调研沉淀规范（单一来源）

> 生产方：任何产出调研的场景（子 agent 调研、人工整理、brainstorming 的资料收集）。消费方：eo-recall（缘由瀑布）、eo-change（事实自查，涉及外部世界时）。目标：**调研过的结论不重新调研**。

## 目录与文件

`<project_root>/research/` 下每篇一个主题，可按子目录分批（如 `research/auth-survey/`）。frontmatter 必填：

```markdown
---
tags: [具体主题词]
date: YYYY-MM-DD
summary: <一句话结论——检索锚点，必填>
---
```

## INDEX.md（生产时同步维护）

每个含调研文件的目录一份 INDEX.md：

```markdown
| 日期 | 标题 | tags | summary |
|------|------|------|---------|
| 2026-07-07 | [竞品-openspec](竞品-openspec.md) | sdd, archive | 反写模式最成熟实现，社区痛点为碎片化 |
```

## 消费规则（recall / change 引用本节）

1. `research/` 或其 INDEX **不存在 → 整步跳过，零成本**；存在多级子目录时先扫根 INDEX（若有）再进子目录 INDEX
2. 按当前任务关键词匹配 `tags` / `summary`，命中 ≤2 篇读正文相关节
3. 结论可能过时（外部世界会变）——引用时带上 `date`，超过半年的敏感结论（平台规则、API 行为）提示「调研于 X，建议核实」

## 维护规则

- **谁产出谁建/更新 INDEX**——没进索引的调研等于没做
- 结论被证伪 → frontmatter 加 `status: superseded` 并指向新篇；不删文件
- 本目录不写教训（归 lessons/）、不写决策（归 decisions/）——它只回答「外部世界是什么样」
