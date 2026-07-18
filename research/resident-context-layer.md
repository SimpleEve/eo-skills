---
tags: [常驻上下文, claude-md, steering, memory-bank, adr, prompt-debt, 注入检索]
date: 2026-07-18
summary: 常驻层从未承担单次变更意图职能且只是建议不是约束——change 变薄时抽掉的意图必须显式指定去处，P0 约束必须配确定性检查
---

> **主题**：常驻项目上下文层（memory bank / steering / rules / knowledge）
> **调研日期**：2026-07-18
> **素材来源**：本地落盘素材（cline-mb.md / cline-rules.md / agdr.md / mneme-adr.md / devin-knowledge.md / claude-md-ecosystem.md / claude-md-maintenance-antirot.md 等），零联网
> **已驱动的设计决策**：「意图必须显式给去处，常驻层兜不住」「常驻层是建议不是约束」
> **关联设计稿**：[docs/tier-design.md](../docs/tier-design.md)

## 结论

1. **常驻层从未承担单次变更意图职能**。单次意图只有三种归宿（无第四种）：独立 per-change 工件 / append-only 决策日志 / 蒸发。change 变薄时被抽掉的意图**必须显式指定去处**（decisions/ 或明示接受蒸发）。
2. **常驻层的根本上限是「建议不是约束」**。所有 rules file / memory 方案都停在「in-context but advisory」这一档，只影响概率。**P0 级不可违反的约束必须配确定性检查（hook/CI）。**
3. 常驻层的失败模式是**膨胀成 prompt debt**——存储解决了，记忆没有；防腐要靠硬预算、零和机制、指针而非副本。

## 证据

### 1. 各家常驻层结构

- **Cline Memory Bank**：6 固定文件（projectbrief / productContext / activeContext / systemPatterns / techContext / progress），全部「当前状态快照」，无 append-only 决策日志；activeContext.md 下个任务直接覆写。
- **Kiro Steering**：product.md / tech.md / structure.md 三 foundational（每次交互默认注入）+ 自定义；写作建议含 `Explain why decisions were made`，但**无独立决策条目类型**；ADR 只是可塞进 auto 模式的一类内容。
- **Devin Knowledge**：无固定分类；**关键切分**：`codebase-level (vs. task-level) context`——task 级明确排除在常驻层外；单次变更意图只存在于 session prompt，无落盘工件。
- **Claude Code**：CLAUDE.md（人写，规则）+ auto memory（机器写，learnings，200 行 / 25KB 硬限）双轨，按「谁写」切分；无决策记录类型。
- **AgDR（对照组，唯一把「为什么」做成一等公民）**：frontmatter（timestamp / agent / model / trigger / `status: proposed|executed|superseded` + supersedes 链）+ Options / Decision / Consequences；`written by the agent at the moment it makes the call and committed alongside the code`；建卡门槛：`Don't create AgDRs for: Trivial choices / Following existing conventions / Bug fixes with obvious solutions`。

### 2. 单次变更意图的三种归宿（无第四种）

(a) 独立 per-change 工件（Kiro spec，退场路径素材零命中）；(b) append-only 决策日志（AgDR）；(c) **蒸发**（Devin session prompt / Cline activeContext 覆写 / Claude Code 无载体）。

AgDR 对蒸发后果的诊断：`Six weeks later... nobody, human or agent, can reconstruct the reasoning. The context evaporated the moment that session ended.`

### 3. 维护与防腐

- **有机器强制的只有两家**：Claude Code（200 行 / 25KB 超限报错强制重写索引；/doctor 砍「能从代码推导的内容」，留 pitfalls + rationale + 与默认不同的约定）、Devin（可调度维护 agent：`Find and merge duplicate knowledge entries / Resolve conflicting guidance`，每周跑）。Cline / Kiro 靠人工纪律。
- **Kiro 方法论**：`Each time Kiro makes a mistake... ask Kiro to make updates while the issue is still in context`（趁错误还在上下文里就更新）。
- **防过时：指针而非副本**——`documentation copied to my project folder will inevitably be out of date` → `The steering file becomes a thin pointer`；`#[[file:path]]` 引用语法。
- **膨胀实录**：Kiro 官方博客 trivial 项目 3500 行 steering → refine 到 102 行（`a context bomb`；`write steering files for an LLM, not for a human. Be terse. Be opinionated.`）；Cline Memory Bank 全量注入被社区骂（`memory bank eats up my tokens`；init 一次 500K token）。
- **最深刻诊断（"prompt debt"）**：`it grew to 80+ md files and somewhere past 5 million characters... every run started to feel like: "please scan this giant pile of notes and somehow guess which parts still matter." storage was solved. memory was not.`；跟帖：`Markdown is great as an archive... But once everything is just "more notes," the agent has no real sense of priority, freshness, authority, scope, or current relevance. That is where markdown turns into prompt debt.`
- **零和预算制**：有仓库把 hook 写成超限报 `Remove content before adding`——精简从自律变成新增的强制代价。
- **实践者痛点清单**：`old plans that are no longer true / temporary notes becoming permanent / context bloat / no clear source for why a memory exists. The part I want most is provenance.`

### 4. 注入与检索谱系

全量注入（Cline MB，最贵）→ 路径 glob 条件（Cline rules / Kiro conditional / Claude rules paths，确定性）→ 语义触发（Kiro auto / Devin trigger description，概率性）→ 手动（#filename）。

- **Kiro 四档启发式**：`"every time"→always / "matters but not every conversation"→auto / "only when editing these files"→conditional / "walk me through right now"→manual`；预算表：always 40-80 行 × 3-6 文件。
- **Devin 唯一暴露检索可观测性**（session 内显示 Accessed Knowledge）。
- **命中率风险**：写成「应主动读的文件」而非注入，`Claude reads it about 50% of the time... Gemini never`。

### 5. 常驻层的根本上限：建议不是约束

- **CLAUDE.md 官方**：`context, not enforced configuration`；`CLAUDE.md instructions shape Claude's behavior but are not a hard enforcement layer`（hooks 才是）。社区对照实验（issue #33603）：加强措辞 / 反复重申无效。
- **Kiro 同构**：`steering is guidance (the model should follow it but might not in a long context), while hooks are enforcement`。
- **mneme 三档梯子**：Ignored → **In-context but advisory（所有 rules file / memory 方案都停在这档，概率性）** → Enforced（确定性检查在改动落地前拦截）。金句：`An ADR nobody checks is a comment. An ADR a machine checks is a constraint.`；`loading an ADR into context is not the same as enforcing it. A document in the prompt shifts the odds. It does not close the door.`
- **落地形态**：检索相关 ADR → 确定性核对提议的 edit → 拒绝时点名 `This change violates ADR-014`（可重试）；edit-time + CI 双时机。

### 6. 对 eo-skills 的映射

- eo-doc/state = 状态层（对应 steering / MB）；eo-project-record decisions/ = 事件层（已是 AgDR 式，带 INDEX 与检索锚点）；change = per-change 意图工件。**三层分工与业界边界一致，不需推翻。**
- 「能从代码推导的别沉淀，只沉淀 rationale 和反直觉坑」（/doctor 口径）与 eo v2「代码是唯一真相源」原则互证。
- AGENTS.md 配对实验（−20% 时间/token，小任务即回本）支持常驻层投入；CLAUDE.md 生态教训支持硬预算与零和机制。

## 缺口与引用卫生

- 本篇素材**未做 [一手]/[转述] 分级标注**；全部来自本地落盘素材文件、零联网抓取，引用时应回原素材文件溯源。
- AGENTS.md 配对实验的 −20% 数字原始出处见 [spec-artifact-debate.md](spec-artifact-debate.md) §2（arXiv 2601.20404v2，124 PR，样本全为 ≤100 LOC / ≤5 文件），本篇为跨篇引用，外推需带该样本限定。
- 「Kiro spec 退场路径素材零命中」是**检索未命中**，不等于不存在——按本轮方法论教训，「未找到」≠「无」。
