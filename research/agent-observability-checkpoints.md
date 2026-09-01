---
tags: [checkpoint, 可观测性, output-styles, claude-code, devin, cursor, openhands, copilot-cca, 双模式汇报, 可打断]
date: 2026-08-21
summary: 业界收敛于「默认自主推进 + 全量事件流兜底 + 随时打断接管」——双模式输出走单事实源双层投影而非双份摘要，且 checkpoint 词义三方撞车需显式声明
---

> **主题**：自动推进 agent 的 checkpoint 语义、可观测性与双模式汇报
> **调研日期**：2026-08-21
> **素材来源**：Claude Code 官方文档（output-styles / checkpointing，抓取当日）、claude-howto checkpoints 指南（2026-08-04，基于 CC 2.1.220）、Cursor 官方帮助与 capabilities 文档、GitHub Docs/Blog（2025-10 ~ 2026-04）、Devin 官方文档 + 第三方实测（fast.io，2026-07）、OpenHands ICLR 2025 论文与 SDK 论文（arXiv 2025-11）
> **拟驱动的设计决策**：Auto 模式 checkpoint=可观测点语义落地；双模式输出（产品友好汇报 / 架构技术提炼）的产出形态
> **关联背景**：eo-loop 已有「窗口化汇报硬窗口（≤10 分钟）」与「合流 checkpoint」用法（eo-loop/SKILL.md）

## 结论

**三条命题同向收敛：渲染契约写在提示词层（非后处理）、推进模式取「默认自主 + 随时可打断」、双模式取「一处产出两处渲染」。**

1. Claude Code output styles 是**系统提示词层**的机制（Markdown frontmatter + 指令注入 system prompt 末尾 + 会话内持续 reminder），不是格式后处理；无现成「面向非技术用户」内置模式，但机制本身（风格契约与行为能力可分离）可直接照搬。
2. 「默认推进 + 随时可打断」是四家（Claude Code / Devin / Cursor / Copilot CCA）+ OpenHands 的共同形态，**没有一家在事中阻塞等人**；汇报粒度收敛为两档——事中轻量状态行、节点处证据包。⚠️ checkpoint 词义三方撞车：业界=可回退快照、eo-loop 现有=合流节点、拟定=可观测点，必须显式声明或换词。
3. 双模式输出的业界主流是**单一事实源 + 两个缩放层级**（摘要层在前、全量层经链接/折叠可达），无主流产品维护双份独立摘要——双写漂移是公认风险。

## 证据

### 命题 1：output styles = 系统提示词层风格契约，无现成非技术模式但机制可照搬

- **机制**（[官方文档](https://docs.claude.com/en/docs/claude-code/output-styles)，抓取 2026-08-21）：output style 直接改 system prompt——自定义 style 是一个 Markdown 文件，frontmatter（`name` / `description` / `keep-coding-instructions` / `force-for-plugin`）+ 正文指令**追加到 system prompt 末尾**；会话中持续触发 reminder 让模型遵守 style；仅作用于主会话（subagent 各有自己的 system prompt，fork 例外）；会话启动时读取一次，切换需 `/clear` 或新会话生效；选择持久化在 `.claude/settings.local.json` 的 `outputStyle` 字段。
- **内置五档**：Default / Proactive（立即执行、少确认，强于 auto mode 的自主引导）/ Concise（v2.1.237，2026-08-20 前后：结果先行、跳过铺陈、被追问给全细节，且**始终保留错误报告、安全警告、破坏性操作确认全文**）/ Explanatory（干活同时间插教育性 "Insights"）/ Learning（留 `TODO(human)` 让使用者自己写关键片段）。
- **官方自划的分层界线**（同一文档的工具对比表）：output styles 改行为基线（角色/语气/默认格式），CLAUDE.md 加项目上下文，`--append-system-prompt` 做一次性追加，agents/skills 管任务域——「改怎么说话」与「知道什么」被显式分层。
- **无现成「面向非技术用户」模式**：内置档全是开发者视角（最近的是 Explanatory 的 Insights 间插）。但 `keep-coding-instructions` 开关证明官方认可「沟通能力（怎么汇报）与行为能力（怎么干活）可分离」——正是双模式需要的设计：同一份干活能力，换一层汇报契约。
- **影响哪项决策**：双模式汇报的实现层——选「提示词层风格契约」而非「产出后做格式转换」；友好模式 ≈ 自定义 style（结果先行 + 隐藏技术名词 + 保留关键警告，参照 Concise 的保留清单），技术模式 ≈ Default + 架构维度指令。
- **置信度**：高（官方文档一手机制描述）。
- **若被证伪**：若实测发现提示词层契约压不住输出格式（长会话漂移），改选为「产出物结构化 + 展示期渲染」（退到命题 3 的形态，提示词只负责产生结构化字段）。

### 命题 2：默认推进 + 随时可打断是成熟共识；汇报粒度 = 状态行常态化 + 节点证据包

- **Claude Code checkpoints**（[claude-howto](https://github.com/luongnv89/claude-howto/blob/main/08-checkpoints/README.md)，2026-08-04，CC 2.1.220）：**每条用户输入自动打 checkpoint**（消息 + 文件改动 + 工具历史），`Esc Esc` / `/rewind` 回放，六种回退（代码+会话 / 仅会话 / 仅代码 / 双向 summarize）；保留 30 天、最多 100 个；Bash 副作用与外部改动不追踪；明确定位「不是 git 替代品」。介入粒度 = 用户输入边界，介入方式 = 随时 Esc 打断 + rewind 到任意点。
- **Cursor Cloud Agents**（[官方帮助](https://cursor.com/help/ai-features/background-agents) + [capabilities](https://cursor.com/docs/cloud-agent/capabilities)，抓取 2026-08-21）：云 VM 异步跑完为止，`reports back with proof that the work is done`——产出物是 PR + 附件证据包（videos / screenshots / logs），让人不 checkout 分支即可验收；介入 = **随时接管 remote desktop**（可随时交还）或 follow-up 指令。事中可观测性最弱，走的是「事后证据包」极端。
- **GitHub Copilot coding agent**（[Managing agent sessions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/use-copilot-agents/manage-and-track-agents) 2026-03-10；[Mission Control 讨论](https://github.com/orgs/community/discussions/177791) 2025-10-23；[commit 溯源 changelog](https://github.blog/changelog/2026-03-20-trace-any-copilot-coding-agent-commit-to-its-session-logs/) 2026-03-20）：PR body checklist 随 commit 勾选 + 标题实时更新为进度主载体；session logs 全量可溯（commit 内嵌 `Agent-Logs-Url` trailer 永久链接）；Mission Control 统一 assign / steer / track。事中介入 = 评论 @copilot 续跑或人直接接管分支（另见本仓 [issue-dispatch-model.md](issue-dispatch-model.md) §5）。
- **Devin**（[Ask Devin 文档](https://docs.devin.ai/work-with-devin/ask-devin) 2026-03-04；[fast.io IDE 实测](https://fast.io/resources/devin-ide-guide/) 2026-07-17）：session 状态内嵌在 Ask Devin 对话 / Slack 线程实时可见；**随时发消息即转向**；人可 pause、接管 IDE 修掉环境问题、再 message 交还继续。事中可介入性最强。
- **OpenHands**（[ICLR 2025 论文](https://proceedings.iclr.cc/paper_files/paper/2025/file/a4b6ad6b48850c0c331d1259fc66a69c-Paper-Conference.pdf)；[SDK 论文](https://arxiv.org/html/2511.03690v1) 2025-11-05）：event stream（action / observation）是唯一事实源，GUI 实时可视化当前 action；`The user may interrupt the agent at any moment`；SDK 把 interrupt 列为交互式应用的一等能力。
- **收敛形态**：没有一家在事中设阻塞点等人确认（事前方案确认各家都是可选前置，见 issue-dispatch-model §2）。汇报粒度两档：**事中 = 单行状态（当前在做什么 / 进度比例），节点 = 证据包（PR、截图、日志链接）**；事中从不推长文。
- ⚠️ **命名撞车（本篇最要紧的警示）**：业界 checkpoint = 可回退的状态快照（Claude Code / LangGraph interrupt 同义）；eo-loop 现有「合流 checkpoint」= 并行合并节点；本次拟定 = 可观测汇报点。三个语义互不相同，落地时要么换词（waypoint / 观测点），要么在 SKILL.md 显式声明语义差异，否则 agent 读到「checkpoint」会按 rewind 语义理解。
- **影响哪项决策**：Auto 模式「一路推进 + checkpoint 不阻塞」与业界全量一致，方向无反转风险；汇报粒度直接可抄——常态状态行（对齐现有 ≤10 分钟硬窗口）+ checkpoint 处证据包式汇报；命名必须处理撞车。
- **置信度**：高（四家官方文档 + 一篇论文，互相印证）。
- **若被证伪**：若发现某主流产品以「事中阻塞确认」为主且留存更好（目前无此证据），则 Auto 模式需重开「风险信号命中时是否阻塞」的讨论；当前证据下维持不阻塞。

### 命题 3：双模式 = 单一事实源 + 两个缩放层级；双份独立摘要无主流先例

- **生成期渲染层**（运行时切换）：Claude Code output styles 是唯一纯「渲染层」代表，但它切的是**整个会话的产出风格**，一切一换，不是同一产出物双视图。
- **单事实源双缩放**（主流，三家同构）：
  - Copilot CCA：PR body（人类摘要）+ session logs（全量技术细节），commit trailer 永久互链；
  - Cursor：PR 摘要 + 证据包附件（videos / screenshots / logs）；
  - Devin：对话内自然语言状态 + session 多窗格（shell / editor / browser 全量现场）。
  - 共同点：**摘要层与全量层来自同一事件流**，层间用链接相连，无人维护两份独立撰写的摘要。
- **文档界同构**：progressive disclosure 惯例（executive summary 在前、details 折叠在后，如 GitHub `<details>` 块）也是单文档分层，不是双文档。
- **影响哪项决策**：双模式输出定为「**一处产出两处渲染**」——checkpoint 产出物是一份结构化记录（事实源），友好汇报与技术提炼是它的两个投影；技术细节层必须可溯源（链接或折叠），不做双份独立摘要。生成期（提示词契约，命题 1）决定摘要层长什么样，事实源本身不受影响——两个命题在此合流。
- **置信度**：中高（三家产品形态一致，但均为官方/第三方描述，无公开实证研究量化两种形态优劣）。
- **若被证伪**：若实测发现「一份事实源渲染两视图」导致友好层信息不足（技术事件流失产品语言），备选是「双份摘要但同源生成」——一次生成、同 commit 落盘、禁止后续独立编辑，把漂移风险锁在生成时刻。

## 缺口与引用卫生

- 本篇素材**未做 [一手]/[转述] 分级标注**；Claude Code / Cursor / GitHub / Devin 为官方文档与官方 changelog 原文抓取（一手），fast.io 与 claude-howto 为第三方整理（转述，claude-howto 标注了官方文档出处），OpenHands 为同行评审论文。
- Cursor 与 Devin 的事中可观测性描述主要来自官方营销/帮助页，缺一线工程团队的量化实测（对比：Copilot CCA 有 dotnet 878 PR 实测，见 issue-dispatch-model）；「事中不推长文」是从产品形态归纳，无官方明文。
- 「无双份独立摘要先例」是缺席性证据（absence of evidence）——调研范围内未见，不等于不存在；若后续发现反例（如某些 release-notes 生成器维护受众双轨文档），命题 3 结论需降级。
- output styles 的 Concise / Proactive 两档发布时间极新（v2.1.237，2026-08-20 前后），行为稳定性未经时间检验。
