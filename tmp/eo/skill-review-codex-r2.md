# eo-skills v2 skill design review — round 2

审查标准：继续以 `/Users/debugeve/.claude/skills/writing-great-skills/SKILL.md` 与 `GLOSSARY.md` 为唯一标准，重点看 predictability、description 触发、steps 可执行性、progressive disclosure、context pointer 可达性、single source of truth、relevance/sediment/no-op/negation。

审查基线：当前 HEAD 为 `bb7b58c`；对照第一轮报告 `tmp/eo/skill-review-codex.md` 逐条核验，并额外扫描本轮修订引入的问题。范围仍为 `.claude/worktrees/v2/` 下全部 `eo-*` 目录、`eo-shared/`、`README.md`、`docs/GUIDE.md`；`docs/v2-design.md` 仅作背景。

结论摘要：第一轮 14 条中，8 条已实质修复，5 条部分修复，1 条修复引入 P0 级新问题，未发现完全未动的条目。本轮新增/残留需重点处理的问题共 4 条：P0 x1、P1 x2、P2 x1。`eo-brainstorming` 的下沉改造整体自洽；本轮新增的真实跨 skill 相对链接均可解析，模板/示例中的占位链接不计为包内断链。

## 逐条核验第一轮问题

| 原编号 | 状态 | 复核结果 |
|---|---|---|
| P0-1 AskUserQuestion runtime lock-in | 已修复 | `eo-shared/questioning.md:32` 改为 runtime 中立的封闭选择协议；主要引用点改为“按封闭选择协议”，未再把 `AskUserQuestion` 作为唯一可执行工具。 |
| P0-2 project-init 缺少已初始化项目更新/修复分支 | 部分修复 | `eo-project-init/SKILL.md:50-59` 已新增 1.5 分支，解决“无分支”的核心问题；但 board/github 后开逻辑与默认补字段顺序冲突，见新问题 P1-1。 |
| P1-1 eo-shared 作为 skills 根下 external reference | 部分修复 | `README.md:41` 与 `eo-shared/README.md:3` 已说明 `eo-shared` 是 support directory 且需整套安装；但仍依赖“无 SKILL.md 的目录会被所有 runtime 忽略”的包装假设，且 `eo-shared/README.md:3` 对 Codex/Antigravity 的“按同规则处理”缺少可验证护栏。 |
| P1-2 裸路径 context pointer 不可解析 | 已修复 | 主要真实指针已改成可解析相对链接，如 `eo-project-init/SKILL.md:170,261,265`、`eo-shared/board-github.md:48`。链接扫描剩余命中为模板/示例占位（如 `change.md`、`filename.md`、`eo-doc/...` 注入模板），不是本轮要求的包内真实指针。 |
| P1-3 description 未覆盖 branch / 误触发风险 | 修复引入新问题 | 多数 description 已收窄并补 NOT FOR；但 `eo-test/SKILL.md:3` 在未加引号的 YAML 单行里加入 ASCII `NOT FOR:`，导致 frontmatter 解析失败，见新问题 P0-1。 |
| P1-4 brainstorming/project-init sprawl | 部分修复 | `eo-brainstorming/SKILL.md` 已从长正文收敛到 125 行，工具箱与记录模板下沉到 `references/` 且主流程完整；`eo-project-init/SKILL.md` 仍有 293 行，模式问法、backlog 模板、agent 注入模板、board/github 分支仍集中在顶层。 |
| P1-5 doc-manager 模板与 INDEX 多真相源 | 部分修复 | `eo-doc-manager/SKILL.md:151-159` 已把结构化规则/INDEX 指向 reference；但 `eo-doc-manager/references/templates.md:35-69` 仍复制一份 INDEX 模板，而 `references/index-templates.md:1-53` 是另一份权威。 |
| P1-6 v1 spec/dev/module 口径沉积 | 已修复 | `eo-doc-manager/SKILL.md:51,74` 对旧目录/dev 的出现已改成迁移/遗留说明，`mermaid.md`、`implement-deviation-template.md` 的 runtime 口径已转为 v2 change/state/agent-handbook。剩余 `dev/<module>`、`spec 概念已移除` 属于迁移说明或用户文档解释。 |
| P1-7 test/review/implement 模板不自洽 | 已修复 | `eo-test/references/test-template.md:39-49`、`eo-review/references/review-template.md:63-67` 统一到 `TODO-1` 形态；`eo-implement/references/implement-deviation-template.md:6-15` 删除了 `module` 字段。 |
| P1-8 eo-flow action/next-step 口径不一致 | 已修复 | `eo-flow/SKILL.md:22-29` 的 action 表与 description 均覆盖 `fix`；`eo-flow/SKILL.md:120-122` 已把 review 通过后的归档入口统一为 `/eo-archive <change-id>`。 |
| P2-1 description 偏命令帮助 | 已修复 | 第一轮点名的 `eo-recall`、`eo-fix`、`eo-design` 均已明显收敛为触发 + NOT FOR 边界，执行机制回到正文。 |
| P2-2 README/GUIDE 路径和术语不一致 | 已修复 | `README.md:120,126,147` 与 `docs/GUIDE.md:205,222` 已统一为 `tmp/eo/handoff/<topic>.md`，GUIDE 的 handoff 横切性不再列 spec 节点。 |
| P2-3 brainstorming negation guardrail | 已修复 | `eo-brainstorming/SKILL.md:18-28,120-125` 已改为正向目标与少量硬约束，第一轮点名的密集 negation 已消失。 |
| P2-4 skill 数与 package 口径 | 部分修复 | README 已把 `eo-shared` 称为支持目录而非 skill；但当前目录仍是 17 个 `SKILL.md` + 1 个 `eo-shared`，若发布口径坚持“18 个 skill + eo-shared”，仍有数量差异需要澄清或补齐。 |

## 新问题清单

### P0-1: `eo-test` frontmatter 解析失败，skill 可能无法加载

- 位置：`.claude/worktrees/v2/eo-test/SKILL.md:1-4`
- 问题：`description` 是未加引号的单行 YAML，修订加入 `NOT FOR:`（ASCII 冒号后跟空格）后，YAML 把它解析成 mapping 分隔符并报错：`ScannerError: mapping values are not allowed here`。这会让 runtime 在读取技能 frontmatter 时失败，属于“修 description”引入的失效问题。
- 依据原则：`Description` 是 model-invoked skill 的唯一 invocation context pointer；frontmatter 不可解析时，predictability 直接归零，agent 甚至无法稳定决定是否加载该 skill。
- 建议：把 `description` 改为 quoted string 或 block scalar（`description: |`），并保留当前收窄后的触发/NOT FOR 语义；修完后对全部 `eo-*/SKILL.md` 跑一次 YAML frontmatter parse 检查。

### P1-1: `eo-project-init` 1.5 更新分支会先补默认关闭值，导致 board/github 后开问题不再触发

- 位置：`.claude/worktrees/v2/eo-project-init/SKILL.md:54-59`、`.claude/worktrees/v2/eo-project-init/SKILL.md:192-196`、`.claude/worktrees/v2/eo-project-init/references/config.md:83`
- 问题：1.5 第 1 步要求老配置缺 `board` / `github` 段时“按默认值补写”，而第 5 步又说“仅对应段缺失时”才执行联动两问。按当前顺序，老配置会先被写成显式关闭值，然后第 5 步认为段已存在而不再询问；这与 `board-github.md:77-81` 的“缺失段 = 问一次，显式 false/never = 不再问”语义冲突，会让后开场景静默失效。
- 依据原则：`Steps` 必须按顺序可执行且 completion criterion 可判定；这里同一分支内的两个步骤互相吞掉触发条件，形成不可预测流程。`Single Source of Truth` 也被破坏：config 默认、后开语义、更新分支各说一半。
- 建议：把“schema 补默认值”拆成两类：基础字段可立即补默认；`board` / `github` 缺段必须先走封闭选择协议并写入用户选择。或改成第 1 步只记录缺段，不写入，待第 5 步完成后再落盘。

### P1-2: `EO_HOME` 用户级配置根只在迁移命令中生效，读取/引导仍硬编码 `~/.eo`

- 位置：`.claude/worktrees/v2/eo-project-init/SKILL.md:34-46`、`.claude/worktrees/v2/eo-project-init/SKILL.md:81-82`、`.claude/worktrees/v2/eo-project-init/references/config.md:15,111-115`
- 问题：`config.md` 宣称涉及用户级数据根的内联命令一律使用 `"${EO_HOME:-$HOME/.eo}"`，且 `EO_HOME` 可覆盖用户级配置位置；`eo-project-init` 的迁移命令已用 `EO_HOME`，但随后读取仍写死 `~/.eo/config.json`，引导写入也写死 `~/.eo/config.json`。设置 `EO_HOME` 的测试/多账号环境会把旧配置迁移到 A 处，却从 B 处读取和写入。
- 依据原则：共享配置路径应有 `Single Source of Truth`；步骤引用同一概念时不能分裂为两个可执行位置，否则 legwork 再充分也会走错真实文件。
- 建议：`eo-project-init` 顶层先定义 `EO_HOME="${EO_HOME:-$HOME/.eo}"` 与 `EO_CONFIG="$EO_HOME/config.json"`，后续迁移、读取、写入全部使用同一变量；`config.md:17-22,111-115` 的示例也同步改为变量写法。

### P2-1: 封闭选择协议已定义，但部分封闭选择点仍绕过该单一来源

- 位置：
  - `.claude/worktrees/v2/eo-archive/SKILL.md:30`
  - `.claude/worktrees/v2/eo-project-init/SKILL.md:100,235`
  - `.claude/worktrees/v2/eo-doc-manager/references/claude-injection.md:57`
  - `.claude/worktrees/v2/eo-shared/questioning.md:32`
- 问题：本轮把 `questioning.md:32` 改成 runtime 中立协议后，主要引用点已修，但仍有多处写“请用户三选一/询问用户/创建哪个”而没有指向 §4，也没有推荐项 + 理由。它们未必会立刻失效，但会让相同“封闭选择”在不同 skill 中表现不一致，尤其是非 Claude runtime 下容易退回开放问法。
- 依据原则：`Single Source of Truth` 要求同一行为只在一个权威处定义；`Context Pointer` 的 wording 决定 agent 是否可靠加载协议。这里 pointer 不足会让已定义的协议无法覆盖所有 branch。
- 建议：凡是 2-4 个候选项的闭合决策，都统一写“按 [../eo-shared/questioning.md](../eo-shared/questioning.md) §4 封闭选择协议”；在对应选项处标推荐项和一句理由。对模板内的二选一，也至少注明“按封闭选择协议执行”。

## 重点扫描结果

- 相对链接：新增/修订的真实包内链接（如 `../eo-shared/questioning.md`、`../eo-doc-manager/references/claude-injection.md`、`../eo-design/references/design-md-template.md`、`../eo-project-update/SKILL.md`）均可从当前文件位置解析。自动扫描命中的 `change.md`、`filename.md`、`eo-doc/...` 等是模板或注入后项目内路径，不作为包内断链。
- `eo-brainstorming` 重构：主流程仍覆盖上下文建立、模式分流、对话循环、收敛、记录落盘、捕获出口；`references/question-toolkits.md` 与 `references/record-template.md` 的指针清晰，未发现信息丢失。
- `eo-project-init` 1.5 分支：分支本身补上了第一轮 P0 的缺口，但存在 P1-1/P1-2 两个可执行性问题。
- runtime 中立封闭选择：核心硬编码问题已修，但闭合选择的引用覆盖不完整，见 P2-1。
- 单一来源化：AC、粒度、board/github、questioning 的集中引用方向正确；剩余最大重复是真实存在的 INDEX 模板双写（第一轮 P1-5 仍部分修复）。
