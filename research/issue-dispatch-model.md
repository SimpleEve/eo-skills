---
tags: [issue直派, copilot-cca, devin, 质量门, pr-review, 轻量档]
date: 2026-07-18
summary: 工业级无 spec 直派省的是 TODO 不是 AC——工件从 per-change 挪到 per-repo + per-PR，代价是 44% 的工作静默蒸发
---

> **主题**：issue 直派模式（无 spec 工件的工业实现）
> **调研日期**：2026-07-18
> **素材来源**：GitHub Copilot coding agent 官方文档（cp-*.md）、GitHub 官方博客（gb-*.txt）、dotnet runtime 团队十个月实测（dn.txt，878 PR）、Devin 文档（devin-full.txt）、Claude Code Action（cc-cap.md）
> **已驱动的设计决策**：issue 档「不预写 TODO / AC 不可省 / 独立进度锚点（卡）」
> **关联设计稿**：[docs/tier-design.md](../docs/tier-design.md)

## 结论

**直派模式的成立条件不是「工件更少」，而是把工件从 per-change 挪到 per-repo（常驻指令，真正的杠杆）+ per-PR（自动 checklist + 签名 commit + session log）。AC 原封不动挪进 issue 正文。**

真正丢失且已出事的三项：

1. **AC↔TODO 映射与批末验证** → 测试固化 bug 风险；
2. **事前方案确认** → 16% wrong approach；
3. **独立进度载体** → 44% 工作静默蒸发。

## 证据

### 1. 最小输入工件：AC 没被省掉

- **GitHub 官方三要素**：`A clear description of the problem / Complete acceptance criteria on what a good solution looks like / Directions about which files need to be changed`。issue 定位：`think of the issue you assign to Copilot as a prompt`。官方推荐 issue 模板固化 acceptance criteria 字段。
- **Devin 同构**：`explicit success criteria (e.g., passing tests, matching an existing pattern, CI green)`。
- 与「AC + TODO」相比**省掉的**：人工预写 TODO（agent 自拆 checklist 进 PR body 并随 commit 勾选）、AC↔TODO 映射、分批节奏。**多要求的**：文件路径指引（有语义搜索兜底）。

### 2. 澄清环节：全行业「可选前置对话」，无强制门

- **dotnet**：`CCA largely runs in an unattended mode... you just need to give it the right instructions upfront`；适合 `fire-and-forget in nature` 的任务。
- **Copilot** 的 plan 审批只在 GitHub.com 交互路径；issue / Jira / Linear 直派明文 `only support creating a pull request directly`——用「事后关 PR」替代「事前否方案」。
- **Devin**：Ask Devin 前置对话 scope 后自动生成高上下文 prompt，同样非强制。

### 3. 质量门组合（替代 spec review）

- **唯一强制门 = PR review**，且 🚨 `The person who created the issue can't be the final approver`（禁自审自批）。
- **第二道**：agent 沙箱内 build/test/lint——`If Copilot is able to build, test and validate its changes in its own development environment, it is more likely to produce good pull requests`（官方文档出现两次，最强调的杠杆）；copilot-setup-steps.yml 预装依赖。
- **第三道**：CodeQL + secret scanning + 依赖分析 + 权限约束（只能推 `copilot/` 分支、Actions 需人批准）。
- **官方自认不充分**：`should be supplemented with careful human code review`；`Be aware of the risk of overreliance`。
- **dotnet 实测 review 成本**：CCA PR 中位 review 评论 10 条 vs 人类 PR 7 条（+43%）；21+ 评论的重迭代占比 24.5% vs 15.5%。
- **领域质量门自建模式**：`no performance PR merges without empirical evidence` → 做成 skill；`when CCA lacks a capability, build a skill that bridges the gap rather than accepting the limitation`（已建 8 个 skill）。

### 4. 尺寸甜点区与失败模式（dotnet 878 PR 实测）

- **总量**：878 CCA PR / 535 merged / 67.9%。**尺寸不是主变量**：1-50 行 76-80%，101-500 行 64%，1001+ 行反弹 72%（well-scoped 机械任务）。`task scope matters more than size`。
- **任务类型 30 个点差**：Removal/Cleanup 84.7% > Testing 75.6% > Refactoring 69.7% > Bug Fix 69.4% > Feature 64.5% > Performance 54.5%。
- **官方负面清单四类不宜直派**：复杂宽域（跨仓重构 / 深领域知识 / 大量业务逻辑 / 需设计一致性）、敏感关键（生产事故 / 安全 / PII）、模糊任务、学习任务。硬上限：单 session 59 分钟。
- **心智模型**（全文最凝练）：`CCA is excellent at implementing well-specified changes, very good at investigating issues, and relatively poor at architecting solutions`。
- **真实翻车**：BCrypt PR 20+ commit 后关闭（架构判断类）；覆盖率任务卡死 74.9% 不动（`optimizes for the immediate request and does not try to infer a broader goal`）；修对但不外推（`It's not curious, and it doesn't explore beyond the scope of its assignment`）；**最危险——测试把 bug 固化成期望**：`CCA can produce tests that validate existing incorrect behavior, effectively encoding a bug as the expected result... 65.7% of CCA's added lines are test code`。
- **review 瓶颈系统性副作用**：`One person with good judgment and a phone can generate PRs faster than a team can review them`（几小时造出 5-9 小时 review 债）。
- **准备 > 模型**：环境/指令改进前后成功率 38.1%→69%；`preparation matters more than the model`；`Instructions Are Your Lever`（copilot-instructions.md 每条教训写入后不必再教，甚至让 CCA 在 PR 内自提指令更新）。
- **人机协作数据**：有人类 commit 的 PR 成功率 86.2% vs 无 55.1%（`a force multiplier, not a replacement`）；62% merged PR 只有一次自主尝试后即等反馈。

### 5. 进度与审计载体

- **主载体 = PR 自身**（body checklist 随 commit 勾选、标题实时更新）+ 签名 commit + 每个 commit 内嵌 session log 永久链接（官方审计答案：`a permanent link from any agent-authored commit to the full session logs`）。
- **中断恢复**：@copilot 评论续跑（建议 batch 成一次 review 提交）或人直接接管分支。
- **失效点（本调研最重要警示）**：253 个 closed PR 归因——**44% 是 `auto-closed draft`**（30 天无人 review 自动过期，`the work was requested, CCA delivered something, and it expired unreviewed`）；16% wrong approach；13% superseded。PR 作为唯一载体，生命周期绑定 PR 活跃度，工作静默蒸发 → **轻量档也需要独立于 PR 的进度锚点**。
- **记账口径**：`Don't judge CCA solely by merge rate`——算上有价值关闭，价值交付率 67.9%→73.7%。

## 缺口与引用卫生

- 本篇素材**未做 [一手]/[转述] 分级标注**；来源为官方文档与官方博客原文抓取 + dotnet runtime 团队公开实测文章，原始抓取文件仍在同 scratchpad 目录群，需要溯源时回查。
- 878 PR 的全部量化结论（成功率分布、任务类型差、closed 归因、review 成本）均出自 **dotnet runtime 单团队十个月实测**，是单仓样本，外推到其他代码库时应注明来源而非当作行业基线。
- GitHub 官方对自身质量门有明确自认不充分的表述（见 §3），引用「三道质量门」时不应略去该限定。
