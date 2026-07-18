---
tags: [粒度, 竞品, spec-kit, openspec, kiro, taskmaster, bmad, ac, task]
date: 2026-07-18
summary: 五家竞品无一在 AC 行内嵌验证方式、无一有独立「涉及文件」节，单条 TODO 级完成判据是孤例——驱动 change 条目三处瘦身
---

> **主题**：五家竞品的 change/spec 条目粒度对照
> **调研日期**：2026-07-18
> **调研方式**：5 个并行 agent，deepwiki + 官方模板原文 + 真实仓库样本
> **已驱动的设计决策**：change 条目三处瘦身（AC 验证栏增量制 / TODO 完成判据条件化 / §4 涉及文件转条件节）+ ac-spec「条数不模板化」护栏
> **关联设计稿**：[docs/tier-design.md](../docs/tier-design.md)

## 结论

1. **五家无一在 AC 行内嵌验证方式**——验证性编码进句式（EARS/GWT），不是用自然语言把同一件事写两遍 → AC 验证栏改增量制。
2. **单条 TODO 级完成判据是孤例**（仅重量级路线 Taskmaster 有）；其余判据全在阶段级或外部动作 → TODO 完成判据条件化（仅多对一时写）。
3. **无一家有独立「涉及文件」节**，路径全在 task 行内 → §4 转条件节。
4. **文件路径与 TODO→AC 映射被多家强制**，保留。
5. **数量护栏（3-7/10、700 行硬上限）是 eo 领先竞品之处**（Kiro 无上限被骂 sledgehammer），保留。

## 证据

### spec-kit（github/spec-kit）[一手：模板原文]

- 单条条目一律「一行、一句、一个 ID」，无子字段。FR 不带验证方式，验证外置到 Acceptance Scenario（GWT，挂 user story 不挂 FR）/ Success Criteria / 阶段末 Checkpoint。
- task 强制格式 `- [ ] [TaskID] [P?] [Story?] Description with file path`，缺文件路径直接列 ❌ WRONG。task 只映射到 user story（`[US1]`），无 task→FR 映射。单条 task 无 DoD，判据在阶段级 Checkpoint。
- 数量：task 数与行数完全无上限；硬数字全在别处（NEEDS CLARIFICATION ≤3、澄清提问 ≤5、checklist 软上限 40）。篇幅靠「细节外置 implementation-details/」吸收。
- 粒度基准原文：`each task must be specific enough that an LLM can complete it without additional context`。
- 现行 specify.md 已反转为默认猜、少问：`Make informed guesses / Document assumptions / Limit clarifications: Maximum 3`。
- **设计者松绑实锤**：作者 Den Delimarsky 开源两个月内把 clarify 从 `must be run` 降为 `recommended`（commit 0037a3f）、TDD 从 `MUST COMPLETE BEFORE` 降为 `OPTIONAL`（commit 5042c76）。
- **轻量层教训**：社区提案 #1174「speckit.tinySpec」22 👍 等 8 个月，以 `"verified": false`、0 下载的第三方扩展结案——轻量档要做进核心，不能推给插件。最高票 issue 是 #1191「spec 难以更新/维护」114 reactions——比「太重」更痛的是维护漂移。

### OpenSpec（Fission-AI/OpenSpec）[一手：schema/validator/真实 change]

- **spec 严格**：`### Requirement`（一句 SHALL，软上限 500 字符 WARNING）+ 强制 ≥1 个 `#### Scenario:`（GWT bullet，3-5 行 ≈ 一个测试用例）。validator ERROR 级：`REQUIREMENT_NO_SCENARIOS`。
- **task 松散**：单行 checkbox `- [ ] X.Y 描述`，路径/判据不强制不解析；tasks.md 是「living checklist」。
- **proposal 短**：Why 段机器校验 50–1000 字符（constants.ts：`MIN_WHY_SECTION_LENGTH=50` / `MAX=1000`）；`MAX_DELTAS_PER_CHANGE=10`（warning）。
- 哲学：Progressive Rigor（`keep specs lightweight by default and scale rigor only when risk or coordination complexity demands it`）；`Update preserves context. New change provides clarity.`；`A good change has one intent you can say in a sentence`；`Match the ceremony to the stakes`。

### Kiro（kiro.dev）[一手：系统提示词双仓交叉验证 + 9 个真实项目 spec 实测]

- AC = 单行 EARS 断言（`WHEN [event] THEN [system] SHALL [response]`），平均 99 字符（n=445），不带验证方式/子项。验证性由句式本身保证。
- 每 story 强收敛 5 条 AC（多项目全部恰好 5 条）；中等 feature：requirements 100-170 行 / 8-10 story / 40-60 AC；design 恒为 requirements 的 3-5 倍。
- task = 标题 + 4-6 条含文件路径的子要点 + `_Requirements: 1.1, 1.2_` 精确到 AC 级回指。**可执行契约在 tasks.md 不在 requirements.md**。
- 数量无官方上限（仅 tasks「最多两级层级」）。
- **社区批评一边倒「粒度不自适应」**：Birgitta Böckeler（martinfowler.com）实测小 bug 被展开成 4 user story / 16 AC，`a sledgehammer to crack a nut`；HN 用户实测 `12+ tasks with 4+ sub-tasks each`。AWS 补 Quick Plan 只去审批门、粒度不变（`Both produce the same artifacts`）。
- CSDN 评测者独立撞到同一数字：「10 个需求每个恰好 5 条验收标准，更像模板化输出，人来写有些只要 3 条有些要 10 条」——**AC 条数模板化是被诟病根因**（两条独立证据链）。

### Taskmaster（eyaltoledano/claude-task-master）[一手：schema 源码 + 182 真实 task 实测统计]

- 单 task ≈ 1.9KB 自足施工单：description 均值 154 字符 / details 1134（含伪代码、路径、签名）/ testStrategy 547（强制必填，写到「函数名+输入+期望值+跑测命令」可执行程度）。
- 58% 的 task details 含具体文件路径（来自默认开启的 codebase 分析）。
- **完全无 PRD 溯源字段**——task 生成即与需求原文脱钩。
- 拆解：`complexityScore(1-10)` → `recommendedSubtasks` → `expansionPrompt` 链预规划；`defaultSubtasks=5`；两层封顶。发现 bug：`recommendedSubtasks:0` 被 falsy 吞掉、默认 5 生效。

### BMAD（bmad-code-org/BMAD-METHOD）[一手：模板 + 4 个第三方真实 story 实测]

- AC 低密度：一行一句可测断言，5-11 条/story，验证方式外置（测试任务 / Verification 节）。
- Tasks 高密度：顶层强制 `(AC: #)` 回指，子任务带路径/动作/版本号，4-5 顶层 × 3-8 子任务、两层，结构极稳定。
- 信息重心在 Dev Notes：占全文 25-54%、恒 ≥ Tasks 2 倍——赌注是「dev agent 只读 story 一个文件」。story 正常 199-405 行；spec-template 顶部注释 `Aim for 900–1600 tokens`。
- 官方自己在 checklist Step 4 与 verbosity 搏斗：`Clarity over verbosity / Token efficiency / Context overload`。epic 级上下文裁剪规则：`No full copies / Nothing derivable from the codebase / Target 800–1500 tokens`。

## 缺口与引用卫生

- 五家均标注 **[一手]**：模板原文 / schema 源码 / validator / 系统提示词 / 真实仓库样本，无纯转述来源。
- ⚠️ **Taskmaster**：deepwiki 对 `parse-prd.json` 曾给出**完全编造的 guidelines**，本篇 Taskmaster 全部引用需回 raw 原文核实后方可再引。
