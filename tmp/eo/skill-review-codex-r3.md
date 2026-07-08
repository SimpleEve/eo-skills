# eo-skills v2 skill design review — round 3

审查标准：已重新完整阅读 `/Users/debugeve/.claude/skills/writing-great-skills/SKILL.md` 与 `GLOSSARY.md`；以下仍只按 predictability、description 触发、steps 可执行性、progressive disclosure、context pointer 可达性、single source of truth、relevance/sediment/no-op/negation 判断。

审查基线：当前 HEAD `c41e66d`；对照 r2 报告 `tmp/eo/skill-review-codex-r2.md` 核验，并重点审查 `7b99095`、`dd581e8`、`c41e66d` 三波提交引入的新设计。

结论摘要：按 r2 报告全部 18 项计，15 项已修复，3 项部分修复，0 项未修，0 项修出新问题；通过率 83%。本轮新增问题 4 条：P1 x3、P2 x1；未发现 P0。全量 `SKILL.md` frontmatter 当前均可 YAML 解析；新增真实包内相对链接均可达，自动扫描剩余缺失均为模板/示例占位。

## 一、r2 问题核验

| r2 条目 | 状态 | 复核结果 |
|---|---|---|
| P0-1 AskUserQuestion runtime lock-in | 已修复 | `eo-shared/questioning.md:32` 仍是 runtime 中立协议，主要调用点按协议引用。 |
| P0-2 project-init 缺更新/修复分支 | 已修复 | `eo-project-init/SKILL.md:50-59` 保留 1.5 分支，且步骤重排后仍先处理已初始化项目。 |
| P1-1 eo-shared 作为 skills 根下 external reference | 部分修复 | README/`eo-shared/README.md` 继续说明其为支持目录且整套安装；但仍依赖“无 SKILL.md 会被各 runtime 忽略”的包装假设。 |
| P1-2 裸路径 context pointer | 已修复 | 真实跨 skill 链接均改为可解析相对链接；本轮链接扫描未发现新增真实断链。 |
| P1-3 description 修订导致 eo-test YAML 失效 | 已修复 | `eo-test/SKILL.md:3-5` 改为 block scalar，全部 `eo-*/SKILL.md` frontmatter 解析通过。 |
| P1-4 brainstorming/project-init sprawl | 部分修复 | `eo-brainstorming` 已保持 125 行且自洽；`eo-project-init/SKILL.md` 仍 273 行，模式问法、backlog 模板、注入模板、联动分支仍在顶层。 |
| P1-5 doc-manager 模板/INDEX 多真相源 | 已修复 | `templates.md:35-37` 已只指向 `index-templates.md`，不再复制 INDEX 模板。 |
| P1-6 v1 spec/dev/module sediment | 已修复 | runtime references 已转为 v2 口径；剩余 `dev/<module>`/spec 只出现在迁移说明或背景文档。 |
| P1-7 test/review/implement 模板不自洽 | 已修复 | TODO 形态、`module` 字段问题已清零。 |
| P1-8 eo-flow action/next-step 不一致 | 已修复 | `fix` 与 `/eo-archive <change-id>` 口径保持一致。 |
| P2-1 description 偏命令帮助 | 已修复 | r2 点名的 description 已保持触发 + 边界形态。 |
| P2-2 README/GUIDE 路径术语 | 已修复 | `tmp/eo/handoff/<topic>.md` 与 spec 移除口径保持一致。 |
| P2-3 brainstorming negation | 已修复 | 保持正向对抗性准则。 |
| P2-4 skill 数/package 口径 | 已修复 | 当前为 16 个 `SKILL.md` + `eo-shared` 支持目录；README 不再宣称旧数量，migration 明确删除/改名。 |
| r2 P0-1 eo-test frontmatter | 已修复 | 见上，YAML parse 全量通过。 |
| r2 P1-1 project-init board/github 后开被默认值吞掉 | 已修复 | `eo-project-init/SKILL.md:54` 明确 `board` / `github` 缺段不在配置校验步补写，留给第 5 步问答。 |
| r2 P1-2 EO_HOME 用户级配置根 | 部分修复 | `eo-project-init/SKILL.md:46,81` 已使用 `EO_CONFIG`；但 `references/config.md:17-24,108-112` 仍用 `~/.eo/config.json` / `mkdir -p ~/.eo && mv ...` 作可执行口径。 |
| r2 P2-1 封闭选择协议引用不完整 | 已修复 | `eo-archive:S30`、`eo-project-init:S99,S223`、`claude-injection.md:57` 等已补协议引用与推荐项。 |

## 二、本轮新问题

### P1-1: research/ 被 eo-change/eo-recall 消费，但没有生产方、INDEX schema 或维护规则

- 位置：
  - `.claude/worktrees/v2/eo-change/SKILL.md:42`
  - `.claude/worktrees/v2/eo-recall/SKILL.md:39`
  - `.claude/worktrees/v2/eo-project-init/references/config.md:143`
  - `.claude/worktrees/v2/docs/GUIDE.md:66`
- 问题：knowledgebase 移除后，`research/` 被定位为“调研沉淀，recall/change 消费”，且消费步骤要求“扫其 INDEX”。但当前没有 skill 或 reference 定义 `research/INDEX.md` 的列、frontmatter 必填字段、写入/更新/归档规则，也没有说明由谁创建/维护。agent 到达消费点时只知道“有个 INDEX”，不知道如何可靠判断相关性。
- 依据原则：`Context Pointer` 必须把 agent 带到可用材料；`Single Source of Truth` 要给共享数据结构一个权威定义；缺 schema 会让同一消费步骤在不同项目中不可预测。
- 建议：新增一个轻量 `eo-shared/research.md` 或 `eo-project-record` 的 `research` 分支，定义 frontmatter、INDEX 行格式与维护规则；若暂不生产 research，则把消费步骤改成“仅当项目已有人工维护的 `research/INDEX.md` 且格式为 X 时读取，否则跳过”。

### P1-2: project-init 的“初始状态”与 roadmap frontmatter 枚举不自洽

- 位置：
  - `.claude/worktrees/v2/eo-project-init/SKILL.md:89-91`
  - `.claude/worktrees/v2/eo-project-init/templates/roadmap.md:1-8`
  - `.claude/worktrees/v2/docs/migration-v1-to-v2.md:37`
- 问题：project-init 解析的初始状态允许 `active / researching`，但新 roadmap 模板的 `status` 注释只允许 `active | paused | done`，且 Bases 项目总览依赖该字段。若把 `researching` 直接填进 `{{status}}`，会产生不在枚举内的项目状态；若它应映射到 `phase`，当前步骤没有说明。
- 依据原则：模板是 execution reference，必须与正文步骤自洽；不自洽会让同一输入生成不同 frontmatter，破坏 predictability。
- 建议：把 `researching` 改为 `phase` 候选而非 `status`，或把 roadmap `status` 枚举扩为 `active | researching | paused | done` 并同步 GUIDE/migration。

### P1-3: how-it-works 仍引用已删除的 `/eo-project-lesson`

- 位置：`.claude/worktrees/v2/docs/how-it-works.html:410`
- 问题：交互说明页 STEP 5 的 `who` 仍写 `/eo-fix · /eo-project-lesson`，但该 skill 已删除并改名扩展为 `/eo-project-record`。同页后面的图鉴已更新为 `eo-project-record`，因此页面内部也形成新旧入口并存。
- 依据原则：用户文档中的旧入口会污染 invocation 语言；`Relevance/Sediment` 要求删除已失效 skill 名，尤其是 model-invoked skill 的 leading word 发生改名时。
- 建议：把该处改为 `/eo-fix · /eo-project-record`，并全仓非 tmp 扫 `eo-project-lesson|eo-project-update`；migration 中描述旧名/清理旧软链的语境可以保留。

### P2-1: eo-project-record description 漏掉 reindex decisions 分支

- 位置：
  - `.claude/worktrees/v2/eo-project-record/SKILL.md:3`
  - `.claude/worktrees/v2/eo-project-record/SKILL.md:44-46`
- 问题：正文 `reindex` 分支支持 `reindex lessons / reindex decisions / 迁移旧记录`，但 description 只列 `reindex lessons`。自然语言要求重建 decisions 索引时，agent 可能不会加载本 skill。
- 依据原则：model-invoked `Description` 是唯一自动加载依据；每个 branch 至少应有一个触发词。
- 建议：在 description 触发词中加入 `reindex decisions / 重建决策索引 / 迁移旧记录`，或把 reindex 限定为用户显式 `/eo-project-record reindex` 的子命令并在 description 中概括为 `reindex records`。

## 三、重点扫描结果

- 改名引用：非 tmp 范围内，`eo-project-update` 只在 migration 破坏性变更清单中作为旧名出现；`eo-project-lesson` 除 migration 合法旧名说明外，仅 `docs/how-it-works.html:410` 是误残留。
- project-init 重排：1.5 → 2-12 的主顺序基本自洽，`board/github` 后开吞默认值问题已修；主要新风险是 roadmap `status` 枚举。
- knowledgebase 移除：`state/glossary.md` 特殊篇目、git-sync 影响表、splitting 分流表之间基本一致；缺口集中在 `research/` 消费契约没有单一来源。
- kanban_path 退役：`config.md`、`project-init`、`GUIDE`、migration 对“旧手工看板退役、kanban_path 忽略/置 null、项目总览走 roadmap frontmatter”总体一致；change 级 `board` stub + GitHub 联动仍保留，未视为旧手工看板残留。
- 相对链接：新增真实链接均可达。扫描出的 `change.md`、`filename.md`、`eo-doc/...`、`[标题](文件)` 等是模板占位或注入后项目内路径，不计为包内断链。
