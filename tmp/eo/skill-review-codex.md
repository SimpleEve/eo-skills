# eo-skills v2 skill design review

审查标准：已完整阅读 `/Users/debugeve/.claude/skills/writing-great-skills/SKILL.md` 与 `GLOSSARY.md`。以下问题只按该标准判断：可预测性、description 作为唯一 invocation context pointer、步骤可执行且有完成判据、progressive disclosure、single source of truth、relevance/sediment/no-op/negation。

审查范围：`.claude/worktrees/v2/` 下实际有 18 个 `eo-*` 目录，其中 17 个含 `SKILL.md`，`eo-shared/` 为无 `SKILL.md` 的共享规范目录；另审查了各 `references/`、`README.md`、`docs/GUIDE.md`。`docs/v2-design.md` 仅用于理解背景，未按 skill 标准计分。

## P0 - 会导致误用或失效

### P0-1: 共享规范硬编码 `AskUserQuestion`，但 README 宣称支持 Codex / Antigravity

- 位置：
  - `.claude/worktrees/v2/README.md:1-3`
  - `.claude/worktrees/v2/eo-shared/questioning.md:30-34`
  - `.claude/worktrees/v2/eo-change/SKILL.md:45-48`
  - `.claude/worktrees/v2/eo-project-init/SKILL.md:49-52`
  - `.claude/worktrees/v2/eo-project-init/SKILL.md:180-184`
  - `.claude/worktrees/v2/eo-shared/board-github.md:75-80`
- 问题：README 把本包定位为 Claude Code / Codex / Antigravity 的 skill 集合，但共享提问纪律要求封闭选择“一律走 AskUserQuestion”。这是 Claude 侧工具名，不是跨 runtime 的可执行步骤；Codex 或 Antigravity 读取这些 skill 时会按不可用工具行动，轻则停住等人，重则违反平台交互约束。
- 依据原则：`Steps` 必须可直接执行并有可判定的完成方式；`description/context pointer` 不能把 agent 带到不可用材料；`Predictability` 要求同一过程在声明支持的运行时中可重复。
- 建议：在 `eo-shared/questioning.md` 定义 runtime-neutral 的“封闭选择”协议，例如“若当前 runtime 提供结构化用户输入工具则使用；否则用普通对话问题列 2-4 个选项并等待回复”。如果只支持 Claude Code，则 README/install/GUIDE/description 全部收窄为 Claude-only，并从 Codex/Antigravity 安装路径移除。

### P0-2: `eo-project-init` 的“已初始化项目更新/修复分支”不存在

- 位置：
  - `.claude/worktrees/v2/eo-project-init/SKILL.md:41-43`
  - `.claude/worktrees/v2/eo-project-init/SKILL.md:96-129`
  - `.claude/worktrees/v2/eo-project-init/SKILL.md:180-184`
  - `.claude/worktrees/v2/eo-project-init/references/board-setup.md:20-24`
- 问题：第 1 步说发现已有 `.eo-project.json` 就走“更新/修复分支（见 §6）”，但 §6 实际是“创建项目管理侧骨架”。同时 board/GitHub 后开、看板历史同步都要求重跑 `/eo-project-init`。这会让已初始化项目的 repair/rerun 路径没有可执行步骤，甚至可能误入首次创建逻辑。
- 依据原则：每个 `Step` 需要清晰、可执行、带完成判据；错误的 context pointer 会导致 premature completion 或走错分支。
- 建议：新增明确的“更新/修复已初始化项目”分支，覆盖：只补代码侧、更新 roadmap、开启 board/github 后历史同步、修复 agent 注入、重建 stub。若暂不支持 rerun，则删除后开/重跑承诺，并在已有 `.eo-project.json` 时只输出安全退出说明。

## P1 - 明显偏离最佳实践

### P1-1: `eo-shared/` 是 external reference，却被包装成 skills 根下的 `eo-*` 目录

- 位置：
  - `.claude/worktrees/v2/eo-shared/README.md:1-4`
  - `.claude/worktrees/v2/eo-shared/README.md:14-16`
  - `.claude/worktrees/v2/README.md:41-47`
  - `.claude/worktrees/v2/docs/GUIDE.md:275-283`
- 问题：`eo-shared` 自称“非 skill”，但安装文档说把所有 `eo-*` 目录软链到 skills 目录；GUIDE 又说所有 skill 都遵循 `<skill-name>/SKILL.md` 结构。这把 external reference 放进 skill system，依赖“无 SKILL.md 会被所有 agent 忽略”的隐式行为。该隐式行为一旦在某 runtime 变化，整包加载会失效；即使当前可用，也让“skill 目录”和“共享引用目录”的边界不清。
- 依据原则：`External Reference` 应作为非 invocable reference 存放；`Granularity` 的切分要避免额外 context/cognitive load；`Single Source of Truth` 要让包装与语义一致。
- 建议：把共享规范移出 `eo-*` skill 命名空间，例如 `_eo-shared/` 或 `references/eo-shared/`，安装脚本显式安装支持目录；或者给 `eo-shared` 一个最小、不可 model-invoked 的 `SKILL.md` 并在文档中承认它是 reference-only skill。无论哪种，README/GUIDE/install 的称谓要一致。

### P1-2: 多处跨 skill context pointer 使用不可解析的裸路径

- 位置：
  - `.claude/worktrees/v2/eo-project-init/SKILL.md:155-159`
  - `.claude/worktrees/v2/eo-project-init/SKILL.md:249`
  - `.claude/worktrees/v2/eo-design/references/design-md-template.md:48-64`
  - `.claude/worktrees/v2/eo-shared/board-github.md:47-49`
  - `.claude/worktrees/v2/eo-project-init/references/config.md:77-79`
- 问题：这些指针写成 ``eo-doc-manager/references/...``、``eo-design/references/...``、``eo-shared/...`` 等裸路径。按 skill 加载规则，relative path 应相对当前文件所在目录解析；这些裸路径从当前目录出发并不存在。agent 可能凭经验猜对，也可能读不到所需 reference。
- 依据原则：`Context Pointer` 的措辞决定何时、如何可靠地加载材料；不可解析的 pointer 是 predictability bug。
- 建议：统一改成可点击且真实存在的相对链接；从某个 skill 的 `SKILL.md` 指向 sibling skill 用 `../eo-doc-manager/...`，从 `references/` 内指向 sibling skill 用 `../../eo-doc-manager/...`，从 `eo-project-init/references/config.md` 指向 shared 用 `../../eo-shared/...`。生成到项目 change.md 的模板注释不要引用包内相对路径，改为“按当前 skill 的 AC 规范执行”或直接删除注释。

### P1-3: 多个 description 未覆盖实际 branch，或使用过宽 trigger

- 位置：
  - `.claude/worktrees/v2/eo-test/SKILL.md:1-3`
  - `.claude/worktrees/v2/eo-doc-manager/SKILL.md:1-3`
  - `.claude/worktrees/v2/eo-backlog/SKILL.md:1-3`
  - `.claude/worktrees/v2/eo-project-update/SKILL.md:1-3`
  - `.claude/worktrees/v2/eo-project-lesson/SKILL.md:1-3`
- 问题：`eo-test` 用 `test` 这种通用词且没有 NOT FOR，会抢普通“跑一下测试/写个 test”的任务；`eo-doc-manager` 正文支持 `modify / re-sync / select`，但 description trigger 只写“初始化文档 / 同步文档”，自然语言“重建文档/整理文档/只同步 state”未必加载；`eo-backlog`/`eo-project-update`/`eo-project-lesson` 缺少“仅当用户明确要求记录”的边界，容易把普通对话里的“以后/决定/教训”误判为落盘任务。
- 依据原则：model-invoked `Description` 是唯一自动加载依据；每个 branch 要有一个清楚 trigger，且 description 应降低误触发。
- 建议：逐个 description 改成“Use when...”式分支：`eo-test` 限定“已有 eo change 且用户要 test.md/AC 验证报告”；`eo-doc-manager` 加 `重建/re-sync/修改文档/结构化/整理/select state/agent-handbook`；项目记录类明确“only when user explicitly asks to record/capture/log”并加 NOT FOR。

### P1-4: `eo-brainstorming` 与 `eo-project-init` 的 SKILL.md 过长，branch reference 未下沉

- 位置：
  - `.claude/worktrees/v2/eo-brainstorming/SKILL.md:71-175`
  - `.claude/worktrees/v2/eo-brainstorming/SKILL.md:176-249`
  - `.claude/worktrees/v2/eo-brainstorming/SKILL.md:251-320`
  - `.claude/worktrees/v2/eo-project-init/SKILL.md:49-129`
  - `.claude/worktrees/v2/eo-project-init/SKILL.md:162-249`
- 问题：`eo-brainstorming` 在真正的 workflow 前内联了大量方法论、示例问题、决策池解释和固定模板；`eo-project-init` 把模式询问文案、backlog 模板、board/github、agent 注入都放在顶层。不同 branch 每次都被加载，主步骤被 reference 淹没。
- 依据原则：`Progressive Disclosure` 要把只有某些 branch 需要的 reference 下沉；`Sprawl` 会削弱步骤注意力并增加维护成本。
- 建议：`eo-brainstorming` 保留“模式分类 -> 对话循环 -> 落盘/捕获出口”的主步骤，把探索/塑形工具箱和记录模板移到 `references/dialogue-methods.md`、`references/brainstorm-template.md`。`eo-project-init` 顶层只留 branch router 和完成判据，把运行模式问法、agent 注入模板、board/github 后开流程移到 references/templates。

### P1-5: `eo-doc-manager` 模板与 INDEX 规则有多个真相源

- 位置：
  - `.claude/worktrees/v2/eo-doc-manager/SKILL.md:160-189`
  - `.claude/worktrees/v2/eo-doc-manager/SKILL.md:195-201`
  - `.claude/worktrees/v2/eo-doc-manager/references/templates.md:35-69`
  - `.claude/worktrees/v2/eo-doc-manager/references/index-templates.md:1-18`
- 问题：SKILL.md 内联 frontmatter/body 规则，同时又指向 `templates.md`；`templates.md` 又复制了一份 INDEX 模板，而 `index-templates.md` 也是 INDEX 的专门文件。三处都是可编辑的规则源，已经出现漂移风险。
- 依据原则：`Single Source of Truth` 要求每个 meaning 只有一个权威位置；重复规则会变成 `Duplication` 并抬高维护成本。
- 建议：SKILL.md 只保留“按 templates.md / index-templates.md 执行”的 context pointer；`templates.md` 只放正文/frontmatter 模板；INDEX 相关全部挪到 `index-templates.md`。删除重复段落后补一个验证清单引用即可。

### P1-6: 多个 reference 残留 v1 的 `spec/dev/module` 口径

- 位置：
  - `.claude/worktrees/v2/eo-doc-manager/SKILL.md:77-80`
  - `.claude/worktrees/v2/eo-doc-manager/references/index-templates.md:18`
  - `.claude/worktrees/v2/eo-doc-manager/references/mermaid.md:5-9`
  - `.claude/worktrees/v2/eo-doc-manager/references/mermaid.md:14-18`
  - `.claude/worktrees/v2/eo-doc-manager/references/mermaid.md:110-119`
  - `.claude/worktrees/v2/eo-implement/references/implement-deviation-template.md:7-15`
- 问题：v2 已移除 spec/dev/module 维度，但 doc-manager 仍提到 `spec-layers.md`、`dev/`；mermaid 规范仍说图用在 spec §3、`eo-doc/ARCHITECTURE.md`；implement 偏差模板仍有 `module` 字段。这些不是背景文档，而是 runtime references，agent 会照做。
- 依据原则：`Relevance` 要求每行仍服务当前 skill；过时层是 `Sediment`，会降低 predictability。
- 建议：全仓 `rg 'spec|dev/|module|ARCHITECTURE'` 后逐处判定。runtime reference 中删除 spec/dev/module；若需要历史迁移说明，放到 docs/migration 而不是 SKILL/references。

### P1-7: test/review/implement 模板与 v2 change 模板不自洽

- 位置：
  - `.claude/worktrees/v2/eo-change/references/change-template.md:36-45`
  - `.claude/worktrees/v2/eo-test/references/test-template.md:35-42`
  - `.claude/worktrees/v2/eo-review/references/review-template.md:63-67`
  - `.claude/worktrees/v2/eo-implement/references/implement-deviation-template.md:7-15`
- 问题：change 模板生成 `TODO-1 / TODO-2`，但 test/review 模板示例使用 `TODO-S1`；implement 偏差模板仍要求 `module` frontmatter。报告类 skill 会用这些模板产出互相不匹配的文档，后续 review/archive 追踪 TODO 时会产生不必要的不确定性。
- 依据原则：模板是 execution reference，必须与正文步骤共同构成一个可预测流程；不自洽属于 `Duplication` 漂移。
- 建议：统一 TODO 编号格式，建议全部用 `TODO-1`；删除 `module` 字段，改为 `change_id` + 可选 `affected_files`。同时让 test/review 模板显式引用 AC/TODO 的 v2 命名。

### P1-8: `eo-flow` 的 action/next-step 口径与其它 skill 不一致

- 位置：
  - `.claude/worktrees/v2/eo-flow/SKILL.md:20-30`
  - `.claude/worktrees/v2/eo-flow/SKILL.md:122-130`
  - `.claude/worktrees/v2/eo-archive/SKILL.md:19-23`
- 问题：`eo-flow` 的 description 只列 review/test/implement/change-review，但 action 表还有 `fix`；通过后的下一步写 `/eo-archive <module> <change-id>`，而 v2 archive 前置条件只消费项目级 `eo-doc/changes/<change-id>/change.md`，不再有 module 参数。该错误会在最关键的“review 通过后归档”提示中把用户带到旧命令。
- 依据原则：`Description` 要覆盖真实 branch；步骤中的完成后指令是 completion criterion 的一部分，必须与下游 skill 的入口一致；旧参数是 `Sediment`。
- 建议：description 加上 `fix` branch 或把 `fix` 改成内部分支不对外触发；下一步统一为 `/eo-archive <change-id>`。同时全仓搜索 `<module> <change-id>` 清理旧命令。

## P2 - 可改进

### P2-1: description 普遍偏“命令帮助”，仍有可剪的 context load

- 位置：
  - `.claude/worktrees/v2/eo-recall/SKILL.md:1-5`
  - `.claude/worktrees/v2/eo-fix/SKILL.md:1-5`
  - `.claude/worktrees/v2/eo-design/SKILL.md:1-5`
- 问题：这些 description 把执行摘要、内部机制和多组同义触发词都塞进 frontmatter。它们确实能帮助调用，但按标准，每个词都会常驻上下文，description 应只保留触发 branch 和必要边界。
- 依据原则：`Description` 是 model-invoked skill 的常驻 context load；“one trigger per branch”，同义词重复是 `Duplication`。
- 建议：把机制细节移回正文。例如 `eo-recall` 可收敛为“Use when the user asks to recall/explain current behavior, implementation location, or why a decision was made; answer read-only with sources. NOT FOR bug fixes/changes/doc maintenance.”

### P2-2: README/GUIDE 与 skill 正文有少量路径和术语不一致

- 位置：
  - `.claude/worktrees/v2/README.md:126-128`
  - `.claude/worktrees/v2/docs/GUIDE.md:203-235`
  - `.claude/worktrees/v2/docs/GUIDE.md:220`
- 问题：README 的流程图说明仍写 `tmp/<topic>-handoff.md`，而 skill/GUIDE 正文是 `tmp/eo/handoff/<topic>.md`；GUIDE 的 handoff 横切性仍列 `spec` 节点。虽然不是 skill runtime instruction，但会给用户形成旧口径。
- 依据原则：`Single Source of Truth` 与 `Relevance`；用户文档中的旧说法会反向污染触发词和期望。
- 建议：README/GUIDE 全部统一到 `tmp/eo/handoff/<topic>.md`，删除 `spec` 节点；发布前跑一次 docs/skill 关键词清扫。

### P2-3: `eo-brainstorming` 使用大量 negation guardrail，可改为正向目标

- 位置：
  - `.claude/worktrees/v2/eo-brainstorming/SKILL.md:25-30`
  - `.claude/worktrees/v2/eo-brainstorming/SKILL.md:202-207`
  - `.claude/worktrees/v2/eo-brainstorming/SKILL.md:322-329`
- 问题：这里有多组“禁止/不要”式约束。部分是硬护栏，可以保留；但密集 negation 会把被禁止行为反复激活，且可用正向行为替代。
- 依据原则：`Negation` failure mode；优先 prompt the positive，硬禁令才保留，并配套“应该做什么”。
- 建议：把“绝对禁止无脑认同/空洞鼓励/回避质疑”改写为“默认先复述动机，再给一个有理由的挑战和一个替代方向”；把“不下沉实现细节”改为“讨论停留在用户价值、边界、优先级，技术只在影响方向时点到为止”。

### P2-4: 实际 skill 数与任务口径不一致，发布说明需澄清

- 位置：
  - `.claude/worktrees/v2/eo-shared/README.md:1-4`
  - `.claude/worktrees/v2/README.md:41-47`
  - `.claude/worktrees/v2/docs/GUIDE.md:275-283`
- 问题：本次目录内是 17 个 `SKILL.md` + 1 个 `eo-shared`；若外部口径是“18 个 skill + eo-shared”，当前包少一个 skill。若 18 是把 `eo-shared` 也算进 `eo-*` 目录，则 README/GUIDE 应避免称它为 skill。
- 依据原则：`Description`/安装文档承担 routing role；命名和数量口径不一致会增加 cognitive load。
- 建议：发布前明确“17 skills + eo-shared support directory”或补回缺失 skill；README 的安装说明把“所有 eo-* skill”改成“所有 eo-* skill 目录及 eo-shared 支持目录”。
