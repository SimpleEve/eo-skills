---
name: eo-recall
description: |
  只读的回忆与解释入口：「这个功能当时怎么设计的 / 这段逻辑代码上怎么实现的 / 当初为什么这么定」——按问题类型走检索瀑布（state / agent-handbook / change 已钉决策 / decisions / brainstorm），分层作答、每个论断带出处；复杂逻辑可产 mermaid 或一次性 HTML 解释页。触发：当时怎么设计的 / 这个逻辑怎么实现的 / 为什么这么定 / 帮我回忆 / recall / /eo-recall。
  NOT FOR: 修 bug（/eo-fix）、发起变更（/eo-change）、维护文档（/eo-doc-manager sync）。
---

# eo-recall — 回忆与解释

活文档体系的**消费入口**：把「我忘了当初……」变成一次有出处、分口径的检索问答。**严格只读**——除 `tmp/eo/explain/` 的一次性解释页外不写任何文件。

## 核心原则

1. **查了才答**：答案必须来自本次检索到的文档/代码，每个论断带出处（文档路径或 file:line）
2. **无记载不编造**：文档里查不到就明说「文档无记载，以下是我从代码现读的」——把「回忆」和「现场推断」显式分开
3. **口径分层**：需求设计视角与代码实现视角分开作答，不搅在一起
4. **禁全局 grep**：走 INDEX 收敛，同 eo-fix 的定位纪律

## 前置

**必须能找到 `.eo-project.json`**。找不到 → 报错退出，提示运行 `/eo-project-init`。

## 工作流程

### 第一步：问题分类（可复合）

| 问的是 | 类型 | 主信源 |
|--------|------|--------|
| 「现在是什么样 / 规则是什么」 | 现状 | state/ |
| 「代码在哪、怎么实现的」 | 实现 | agent-handbook/ → 源码 |
| 「当时为什么这么定」 | 缘由 | change §1 已钉决策 → vault decisions/ → brainstorm/ |

复合问题（最常见：「这个系统当时怎么设计的」= 现状 + 缘由）按需叠加信源。

### 第二步：检索瀑布

- **现状**：`eo-doc/state/INDEX.md` 按关键词收敛 → 只读命中篇目
- **实现**：`eo-doc/agent-handbook/INDEX.md` → 命中模块篇（入口/接口/依赖）→ 按图索骥读源码**相关段落**（不通读文件）
- **缘由**：`eo-doc/changes/INDEX.md` 找相关 change → 读其 §1 意图与已钉决策；再查 `<project_root>/decisions/`（文件名即索引）与 `<project_root>/brainstorm/` 的相关记录；lessons 若 trigger 命中也一并带上（踩坑背景常常就是「为什么后来改成这样」）
- 候选 >3 或全无命中 → 追问关键词，不硬猜

### 第三步：分层作答

```
## 需求上（设计口径）
<规则/流程/边界，出处：state/xx.md、change 014 §1、decisions/2026-xx.md>

## 代码上（实现口径）
<入口、关键路径、数据流，出处：handbook/xx.md、src/xx.ts:120-160>

## 当时为什么这么定（若问及）
<已钉决策 + 理由，出处>

⚠️ 文档与代码不一致处 / 文档无记载处，单独列出
```

- 发现 state/handbook 与代码矛盾 → 如实报告并提示「文档陈旧，建议 /eo-doc-manager sync」，以代码为准
- 不确定的就说不确定，不填补空白

### 第四步：富输出（按需，默认不产文件）

- 流程 / 状态机 / 多角色交互类逻辑 → 主动提议：「画个 mermaid？」（对话内直接给，规范见 [../eo-doc-manager/references/mermaid.md](../eo-doc-manager/references/mermaid.md)）
- 盘根错节的大逻辑（多系统联动、你需要反复对照的）→ 提议生成**一次性自包含 HTML 解释页**：`tmp/eo/explain/<date>-<topic>.html`，零外部依赖、用项目真实名词与数据、可交互（点击展开/分步演示）；它是可丢弃工件（见 [../eo-shared/conventions.md](../eo-shared/conventions.md)），有长期价值的结论应沉淀到 state（提示用户跑 sync/modify）而不是留在 tmp

### 第五步：顺手指路（一行，可选）

回答末尾按语境补一句出口：「想改这个行为 → /eo-change」「这看着像 bug → /eo-fix」。不自动派发。

## 关键约束

| 约束 | 说明 |
|------|------|
| 严格只读 | 不改代码、不改任何文档；唯一产物是 tmp/eo/explain/ 的一次性页面 |
| 出处必带 | 无出处的论断不许出现在「设计/实现口径」小节里 |
| 无记载显式声明 | 「文档无记载」是合法且必须的答案组成 |
| 禁全局 grep | INDEX 收敛；候选多就追问 |
| 不越权指路 | 只提示入口，不代跑 /eo-change、/eo-fix |
