---
tags: [sdd, 论战, 分层判据, 工件, 事后探针, 收敛]
date: 2026-07-18
summary: 去 spec 化论战收敛于「按风险分档」而非单向变轻——工件唯一不失效的职能是独立验证的基准，分层靠事后探针不靠事前估计
---

> **主题**：去 spec 化论战与分层判据
> **调研日期**：2026-07-18
> **素材来源**：六份增量报告合并（含两次自我更正）
> **已驱动的设计决策**：三档制判档四轴、事后探针原则、相对量原则、change-review 3 轮上限留档加固
> **关联设计稿**：[docs/tier-design.md](../docs/tier-design.md)
>
> 除特别标注外，引文均经调研 agent 回一手来源核实。

## 结论

1. **轻量派反对的是「前置写全」，不是规格本身**——被模型吸收的是「重放上下文」职能，长上下文变强后前置大 spec 的边际收益下降。
2. **工件唯一不随模型变强失效的职能 = 独立验证的基准**。验证者与执行者的信息隔离是结构问题，不是能力问题。
3. **常驻工件与 per-change 工件必须分开定档**：负面证据全部针对「每任务一次性 spec 用于小任务」；常驻工件（AGENTS.md）小任务即回本。
4. **分层靠事后探针触发，不靠事前估计**——事前估计是最易错的一步。
5. **spec 迭代无内生停点**，必须外生收敛终止；eo change-review 的 P0-only + 3 轮上限是正解，留档防回退。
6. **趋势不是单向变轻**，准确表述是「从一刀切走向按风险/规模分档」。

## 证据

### 1. 轻量派论据（被模型吸收的职能）

- **Peter Steinberger**《Just Talk To It》2025-10-14（6 月还是 SDD 实践者，10 月放弃）：`Designing a big spec, then let the model build it... IMO that's the old way`；长上下文吸收重放职能：`that was useful for Sonnet, but GPT-5 is far better at dealing with larger contexts`；例外档保留：`If it's something tricky, I ask it to write everything into a spec, give that to GPT-5-Pro for review`。
- **marmelab（Zaninotto）** 2025-11-12：`Most coding agents already have a plan mode and a task list. In most cases, SDD adds little benefit`；**审查翻倍**：`review time doubles`；`For large existing codebases, SDD is mostly unusable`。体量佐证：spec-kit 为「显示当前日期」一个功能生成 8 文件 1300 行。
- **虚假安全感**：`agents don't always follow the spec... marked the "verify implementation" task as done without writing a single unit test`。
- **Kent Beck**（经 Fowler Fragments 2026-01-08 逐字转载，⚠️ 广被错挂 Fowler 名下）：`The descriptions of Spec-Driven development that I have seen emphasize writing the whole specification before implementation. This encodes the (to me bizarre) assumption...`——反对的是「前置写全」，非规格本身。Thorsten Ball 展开：`why would this time be different... building software is learning about the software... you need more feedback loops`。
- **Mitchell Hashimoto**（⚠️ 第一轮定性「坚定工件派」已更正）：2026-04 播客 `you don't need to plan as much anymore`、plan/execute 分离 `that actually doesn't produce better results`（ASR 字幕，正式引用前建议听原音）。2026 范式：先松散冲一版（"draw the owl"），diff >1500 行才回头分解——**可审查性阈值，事后测量**。2025 年立场（`the first hour is going back and forth on a markdown spec`）须标注为过期口径。他的分层轴：问题资深度（senior 级问题不派 agent）/ **击键经济学**（`less keystrokes for me to fix this myself` → 描述成本下界）/ 项目风险（Ghostty 全审，婚礼网站不看）。
- **争点已收敛**：Steinberger 与 Mitchell 2025→2026 同向下调 plan 默认档，分歧只在下调多少。

### 2. 工件派论据（不被吸收的职能）

- **核心（唯一不随模型变强失效）：工件 = 独立验证的基准**。Reddit mossiv：`because there is no plan anymore, there's nothing the super powers review agents can review against`；siberianmi：新鲜 session 拿原 spec 复核，`This step will catch the previous agent trying to cheat on tests though because the cards have explicit success criteria`；rupayanc：`the spec is basically a unit test in disguise`。
- **量化** [转述，arXiv 2605.29442，20,574 session]：欠规格只解释 **15.36%** 失配；Developer Constraint Violation 38.33% / Misread Intent 26.95% / Inaccurate Self-Reporting 22.58%——**61% 失配属事后域，靠验收与验证治**；失配跨 session 传染 0.336→0.519（+54%）；`91.49% of visible resolutions still require explicit user correction`。
- **常驻工件配对实验** [arXiv 2601.20404v2，124 PR 同任务两跑]：AGENTS.md 使时间 −20.27%、token −20.08%，样本全为 ≤100 LOC / ≤5 文件——**常驻工件小任务即回本；负面证据全部针对每任务一次性 spec 用于小任务**。两类工件必须分开定档。
- **Armin Ronacher**：不用 plan mode 但要 `a file on disk somewhere that I can see, that I can read, that I can review, that I can edit`——拒绝的是交互封装，不是落盘工件。
- **实测漂移周期**（Reddit Kevin_Xiang）：`Without both (spec + context doc), I drift within 2-3 sessions.`；context doc 应含被否决的方案。
- **时间分解**（Reddit）：定义 spec 15-20 分钟、refine/review 约 1 小时、审代码 15-60 分钟——**写只占 ~15%，审是大头**。

### 3. 分层判据（三轮修订后定稿）

四条判据按优先级：

1. **影响面能否局部化**（取代「改动大小」）。反例 [Reddit 嵌入式 SWE]：30M LOC 高耦合代码库 `SDD even more so (struggles)... at some point you're just encoding all the implementation knowledge into the spec itself`。跨 8 文件同构重命名不需工件；1 文件动全局不变量需要。
2. **是否需要独立验证**（见 §2，唯一不失效职能）。
3. **是否跨 session / 跨人**（传染 0.336→0.519；漂移 2-3 session）。
4. **误解代价 vs 描述成本**（下界：描述成本 ≈ 实施成本 → 免工件）。

两条形式要求：

- **事后探针触发，非事前估计**：Mitchell 1500 行 diff 事后量；Cursor 官方 `Add rules only when you notice Agent making the same mistake repeatedly`；Devin `You find yourself repeating the same reminders`。事前估计是最易错一步。
- **外生收敛终止**：spec 迭代无内生停点（`your spec wasn't wrong, it was untested`；`It will jump through hoops to implement exactly what was specced, all warts included`；优化兔子洞）。**eo change-review 的 P0-only + 3 轮上限是正解，留档防回退。**

**方向性建议：前置投入投环境（可执行断言 + 反馈回路），不投描述性文档。** 三个独立来源：Amp（Thorsten Ball `how can I get feedback on what I'm trying to build as soon as possible`）、Ghostty AGENTS.md（1388 字节全是构建/测试命令，自称 harness engineering）、Fowler。

限定（Fowler Fragments 2026-07-13）：`Conformance tests (sensors) are more valuable than specifications (guides), but it's hard to imagine all the conformance tests that are needed to say what shouldn't happen.`——**负向约束无法下沉，仍需文字工件**；`We can outsource many things, but not the acceptance criteria`。

### 4. 工具侧分层信号

- **Claude Code 官方两档**：`If you could describe the diff in one sentence, skip the plan.` / larger features → 访谈 → SPEC.md → 换新 session 执行；spec 要 self-contained（点名文件接口、声明 out of scope、端到端验证收尾）。
- **Cline 官方三档表**：Small→Act only / Medium→Plan→Act / Large→/deep-planning（触发含 `will take multiple sessions to complete`）；双向降级。
- **Cursor plan mode** 适用清单 + 返工判据：`go back to the plan. Revert the changes, refine the plan... This is often faster than fixing an in-progress agent.`
- **Amp**：删 TODO 功能（2026-01-12，`with Opus 4.5... The agent tracks its own work in a single thread just fine`）——唯一因模型变强砍工件的厂商，但砍的是运行期跟踪不是 spec；产品史：删一次性/人维护的（TODOs / handoff / custom commands），留常驻/惰性加载的（AGENTS.md / skills）。判据：`When a feature starts tying you to the old way to use agents, it goes` + `avoid overfitting on today's model capabilities` → **分层判界写相对量**。
- **Devin**：`if a task would take you three hours or less, Devin can most likely do it`；企业切片 `under 90 minutes`（两套口径勿混用）。
- **趋势**：不是单向变轻——Copilot CLI 2026-01 新增 plan mode，Cline 4.0 收紧默认自动批准。准确表述：从「一刀切」走向「按风险/规模分档」。
- **Thoughtworks Radar** [一手核实]：SDD 在 Assess 环（Vol.34, 2025-11），批评「工件冗长难审」+ bitter lesson（`handcrafting detailed rules for AI ultimately doesn't scale`）。
- **Böckeler 2×2**（问题清晰度 × 规模）：`Where does SDD sit?` 打问号；`small work packages almost seem counter to the idea of SDD`。
- **spec 作探针**（Thorsten Ball）：`write down a spec... in 30min, and show it to them, and they go "no that's not what I meant"`——spec 价值在被否定得多快。

## 缺口与引用卫生

- **不可引用**：arXiv 2601.15195（33k PR 研究，HN 评论转述未核实）。
- **已核纠错**（三条）：
  - Kent Beck 名言**错挂 Fowler** 名下（实为 Fowler Fragments 2026-01-08 逐字转载 Beck 原文）；
  - 《How I use Amp (6000 threads)》作者是 **Stephanie Jarmak**，非 Thorsten Ball；
  - Thoughtworks Radar 流传的 `a bias toward heavy up-front specification and big-bang releases` **不在原文**，勿引。
- **本篇自我更正记录**：Mitchell Hashimoto 第一轮被定性为「坚定工件派」，已更正；其 2025 年立场须标注为过期口径，2026 播客引文为 ASR 字幕，正式引用前建议听原音。
- **营销数字勿引**：BMAD `68% faster / 73% fewer bugs`（无方法学）；Kiro 40h→8h（单案例）。
- **未收敛，勿当共识**：greenfield vs brownfield 判据三人结论相反。
- Simon Willison 仅有「转载 Steinberger 背书」这一立场信号，不足以定性。
- **方法论教训**（agent 自查所得）：「未找到反向证据」≠「无反向证据」，可信度上限由检索覆盖面决定——review 口径应区分「未发现问题」与「已验证无问题」。
