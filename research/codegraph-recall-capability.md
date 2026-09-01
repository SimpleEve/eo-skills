---
tags: [codegraph, mcp, 代码索引, recall, worktree, git-log, 文档停维护]
date: 2026-08-21
summary: codegraph 类工具只索引当前代码快照（符号/调用图/路由），不含 git 历史与设计意图——recall 须 CodeGraph + git log + 意图文档三段拼；worktree 索引按目录隔离且官方刻意不共享，每个 worktree 需独立 init（成本秒级到分钟级）
---

> **主题**：CodeGraph 类工具能否承接 eo-doc 描述性文档（agent-handbook/ + state/）停维护后的 recall 职能
> **调研日期**：2026-08-21（有界调研，未实测装机）
> **已驱动的设计决策**：停维护 agent-handbook/ 与 state/ 成立（recall = CodeGraph + git log + 意图文档三段拼）；worktree 索引选「按 worktree 各自 init」
>
> **可信度标注**：[一手] = 调研 agent 亲自抓原文核对（README / issue / changelog 原文）；[转述] = 第三方页面。benchmark 数字一律为厂商自测，注意利益相关。

## "CodeGraph" 指认与歧义

同名工具不止一个，均为「tree-sitter 解析 → 本地库（SQLite/Neo4j）→ MCP 服务」同族架构，结论在三者间一致，不影响决策：

- **colbymchenry/codegraph**（npm `@colbymchenry/codegraph`）——最可能候选。2026-05 起在 Claude Code/Cursor/Codex 圈传播最广的 "CodeGraph"：Rust 内核 + tree-sitter + SQLite（`.codegraph/codegraph.db`，FTS5），MCP 暴露单工具 `codegraph_explore`，100% 本地、无 LLM、无 API key。[一手：[README](https://github.com/colbymchenry/codegraph)，2026-08-21 抓取]
- **suatkocar/codegraph**（Rust，32 语言，44 个 MCP 工具，FTS5 + sqlite-vec + Jina v2 代码 embedding）——带 git 集成工具组，是同名工具里唯一能碰 git 历史的。[一手：[README](https://github.com/suatkocar/codegraph)，2026-08-21 抓取]
- 其余同名 MCP：Cirilcetra/codegraph（JS/TS/Python，语义搜索需 LLM API key）、andysom25/codegraph、sunerpy/codegraph-rust、CodeGraphContext（Neo4j/FalkorDB 后端）等。[转述：[HeyClaude 对比页](https://heyclau.de/compare/code-search-mcp-servers)，2026-08-16]
- 相邻类备查：claude-context（zilliztech，向量语义搜索，按绝对路径建索引）、Serena（LSP，无预建图）、Sourcegraph / GitHub code navigation（服务端，按 repo@commit 粒度，本地未推送的 worktree 不可见）。

下文「CodeGraph」不另注时指 colbymchenry 版。

## 结论

1. **召回边界：只覆盖「现在怎么实现的」，不覆盖「当时怎么过来的」。** 索引对象是符号/调用边/import/框架路由/跨语言桥 + FTS5 全文，是当前工作树快照；git history、commit message、PR 讨论、Markdown 文档均不索引。自然语言问「X 怎么实现的」是其官方 benchmark 的标准场景（成立）；「历史 change 过程」结构性答不了（验证属实）。→ 停维护 agent-handbook/ 与 state/ 成立；但意图层（decisions/changes/brainstorm）必须保留，recall 是三段拼，不是 CodeGraph 单点。置信度：高。若被证伪（某工具真索引了 commit message 并能答 why）：git log 一段可弱化，但意图文档仍删不得。
2. **索引成本：小仓库秒级、大仓库分钟级、零 token（本地无 LLM），不构成任何方案的约束。** token 账反而支持停维护：厂商自测 7 仓回答架构问题 median 省 62% token / 44% 成本 / 88% 工具调用；反向代价是 session 残余上下文 +80%。置信度：中高（数字是厂商自测）。若被证伪（索引大仓小时级或 embedding 烧钱）：worktree 每开必索引的摩擦升级，改选「懒索引」。
3. **worktree：索引按项目目录组织，官方刻意不跨 worktree 共享——选「每个 worktree 各自 init」。** 「嵌套 worktree 借用主仓索引返回错误分支数据」被官方当 bug 修掉；共享/继承是 2026-05 至今未落地的开放 feature request。软链共享在不同分支并行场景是错误答案源，结构性不成立。置信度：高（一手 issue + changelog）。若被证伪（issue #155 官方机制落地）：改选官方 inherit 机制。

## 证据

### 1. 召回边界 [一手]

**索引对象**（colbymchenry README）：tree-sitter 提取节点（函数/类/方法）与边（calls/imports/extends/implements），框架路由节点（17 个框架），跨语言桥（Swift↔ObjC、RN bridge 等）；FTS5 全文索引；SQLite 存 `.codegraph/codegraph.db`。支持的 30+ 条目全是编程语言，**无 Markdown**；遵守 .gitignore、跳过 `.git`/node_modules/>1MB 文件。

**不含 git 历史**：README 全文无 history/commit 索引能力；仅有的 git 接触面是 `codegraph affected`（吃 `git diff --name-only` 的管道输入找受影响测试）——git 是输入源，不是索引对象。suatkocar 版有 9 个 git 工具（blame / file_history / recent_changes / commit_diff / symbol_history / hotspots…），但那是**按需调 git plumbing 的包装**，答「这行谁改的、这个符号最近哪些 commit 动过」，答不了「当时为什么这么做、考虑过哪些方案」——意图从未进任何一家的索引。

**自然语言召回实现方式：成立，且是官方主打场景**。benchmark 的 7 个查询全是自然语言架构问题（"How does the extension host communicate with the main process?" / "How does Django's ORM build and execute a query from a QuerySet?"），with-arm agent 平均 1–4 次 `codegraph_explore` 调用作答、**7 仓文件读取全为 0**。机制是 FTS5 关键词/符号匹配 + 图遍历 + agent 综合，不是端到端 NL 问答。注意 suatkocar 自测的短板：caller 检测 precision/recall 双满分，但**纯语义搜索 relevance F1 仅 0.37**（P 0.27 / R 0.58）——「按名字/结构找代码」可靠，「模糊语义找代码」弱；recall 技能应走「graph 定位 + 读源码 + git log 补演变」的组合，不指望一次语义搜索出答案。

### 2. 索引初始化与增量成本 [一手，数字为厂商自测]

- **colbymchenry**（README，2026-08-05 复测）：Swift compiler 27k 文件全新索引 ~100s（工作站）；Linux 内核 70k 文件 / 2M 符号 / 6.4M 边 <12min（2 核 6GB VPS）；单文件保存增量同步 ~0.3–0.4s，watcher 2s 防抖。**零 token、零 API**（本地 tree-sitter + SQLite，无 LLM）。
- **suatkocar**：54 文件 230ms，无变更增量 13ms；embedding 用本地 ONNX 模型（Jina v2 code，768 维），无 API 成本。
- **例外**：Cirilcetra 版语义搜索需 LLM provider API key；claude-context 需 embedding provider + 向量库——这两类有真 token/服务成本。
- **vs grep**（厂商 benchmark，Claude Opus 4.8 headless，7 个真实开源仓，harness 两臂均屏蔽 codegraph CLI 防污染）：median **62% fewer tokens / 44% cheaper / 88% fewer tool calls / 53% faster**；without-arm 最高 43 次工具调用 + 19 次文件读取来重建图里已有的结构。反向代价（README 自曝）：codegraph 返回的是单段高密度原文载荷，**session 结束残余上下文约 +80%**（VS Code 仓 67k vs 18k tokens）——长会话小窗口要预算。
- eo-skills 本身体量（几十个 .py/.md）：全新索引量级为秒，worktree 每开一次的成本可忽略。

### 3. worktree / 多目录支持 [一手]

- **粒度 = 项目目录**：索引存 `<dir>/.codegraph/`，按目录隔离；MCP 的 `projectPath` 参数支持同会话查任意已索引目录。索引带「属于哪个 git working tree」的 ownership 印记（[issue #926](https://github.com/colbymchenry/codegraph/issues/926)，2026-06-19：worktree 有本地索引时 MCP 仍误报「index belongs to a different git working tree」——误报本身是 ownership 检查存在的证据）。
- **官方刻意不共享**：[CHANGELOG](https://github.com/colbymchenry/codegraph/blob/main/CHANGELOG.md)（2026-06-02 抓取条目）"Git worktrees no longer silently borrow another tree's index; running CodeGraph from a worktree nested inside the main checkout used to return the wrong branch"——嵌套 worktree 曾经静默摸到主仓索引、返回错误分支的代码，被当 **bug** 修掉。
- **共享/继承机制未落地**：[issue #155](https://github.com/colbymchenry/codegraph/issues/155)（2026-05-16，开放）列了三个选项（A 主仓共享索引 / B auto-inherit 拷贝或软链 / C git 跟踪索引），至今是 feature request 状态。下游编排器也在挣扎同一问题（[oh-my-codex #3101](https://github.com/Yeachan-Heo/oh-my-codex/issues/3101)，2026-07-09：worktree-local vs leader 共享索引无标准答案）。
- **结构性结论**：不同 worktree checkout 不同分支 → 文件内容不同 → 共享索引必然对其中一边给错误答案。「软链共享 `.codegraph/`」只在同分支临时目录场景安全，对并行开发场景是错误答案源；「按 repo root 解析到主仓索引」就是已被官方修掉的那个 bug。候选机制里唯一自洽的是**每个 worktree 各自 `codegraph init`**，成本见命题 2（秒到分钟级）。

## 缺口与引用卫生

- ⚠️ **未实测**：有界调研，全部来自文档/issue 原文，未在本仓库装 codegraph 跑 `init` + recall 问答。决策落地前建议做一次 5 分钟实测：本仓 init 耗时、一个真实 recall 问题（如「board 卡片进度怎么算的」）的回答质量。
- 命题 2 的 benchmark 数字（62% token / 44% 成本 / +80% 残余上下文）均为 colbymchenry 自测，方法学公开但利益相关；方向可信，数值别当精确值引用。
- 「CodeGraph」同名工具多，以上结论对 colbymchenry / suatkocar 两版均核对过；若用户实际指的是 Cirilcetra 版或其他变体，命题 1、3 结论不变（同族架构），命题 2 的「零 token」不成立（语义搜索走 LLM API）。
- suatkocar 版的 git 工具组（blame/symbol_history 等）若好用，可把 recall 里「git log 一段」换成 MCP 调用，但覆盖的仍是 commit 事实层，不是意图层——不改变「意图文档保留」的结论。
