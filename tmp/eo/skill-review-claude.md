# eo-skills v2 全套 skill 设计审查报告（按 writing-great-skills 标准）

> 审查人：Claude（Orca worker）｜ 日期：2026-07-08
> 准绳：`writing-great-skills/SKILL.md` + `GLOSSARY.md`（唯一标准，下文原则名均出自该文档）
> 范围：`/Users/debugeve/projects/eo-skills/.claude/worktrees/v2/` 下全部 17 个 eo-* skill（任务描述写 18 个，磁盘实际 17 个 + eo-shared）、eo-shared 6 个规范文件、全部 references/、README.md、docs/GUIDE.md、install.sh/install.bat。docs/v2-design.md 仅作背景。
> 方法：逐文件通读（约 5300 行全量），全部相对引用做了脚本级存在性校验，软链解析做了逻辑/物理双路径推演。

## 总评

这套 skill 的整体水位明显高于平均：NOT FOR 边界普遍清晰、状态流转单一来源于 conventions.md、「对话速报 + 缺速报=流程未完成」是教科书级的 completion criterion 实践、eo-shared 外部引用模式与标准的 External Reference 条目完全吻合。主要问题集中在三类：**v1 → v2 迁移残留（sediment）**——mermaid.md、index-templates.md、eo-flow、两个产出模板里仍有 spec/module/dev 时代的口径；**单一来源纪律的一个显著例外**——eo-brainstorming 复述了 questioning.md 的决策台账而非引用它（恰好是 eo-shared/README 自己点名的 v1 教训模式）；**一处执行路径失效**——eo-project-init 的「更新/修复分支」被 migration 文档依赖却从未被定义。

- P0：1 条 ｜ P1：8 条 ｜ P2：17 条

---

## P0 — 会导致误用/失效

### [P0-1] eo-project-init 的「更新/修复分支」未定义，内部节号指错

- **文件:位置**：`eo-project-init/SKILL.md:42-44`、`:184`
- **问题**：§1 步骤 2 写「已有 `.eo-project.json` → 走『更新/修复』分支（见 §6）」，但 §6 是「创建项目管理侧骨架」，全文不存在名为「更新/修复」的分支定义；§9 又提到「后开场景：对已初始化项目重跑本 skill（更新/修复分支）」——引用一个不存在的流程。同时步骤 2 的「未有 → 继续 §3」实际指的是 §1 的第 3 小步（读用户级配置），与下文标题「### 3. 解析项目信息」撞号（作者自己也意识到了：43 行括注「节号指下文的"询问运行模式"」正是为同类混淆打补丁）。这不是纸面瑕疵：`docs/migration-v1-to-v2.md` 迁移步骤 5 明确要求「重跑 /eo-project-init（幂等）刷新注入段」，即重跑是被体系依赖的正式路径，而该路径当前不可预期——agent 可能落入「创建骨架」流程对已有项目做重复初始化。
- **依据原则**：Context Pointer（"A must-have target behind a weakly worded pointer is a variance bug"）；Steps / Completion Criterion（步骤必须可执行、可判定）。
- **建议**：新增一节「更新/修复分支」明确定义重跑时做什么（刷新注入段、补建缺失骨架、提供 board/github 两问、其余跳过），§1.2 指向它；§1 内部小步引用改为「继续本节第 3 小步」或直接重排全文节号消除撞号。

---

## P1 — 明显偏离最佳实践

### [P1-1] eo-flow 残留 v1 归档签名 `/eo-archive <module> <change-id>`

- **文件:位置**：`eo-flow/SKILL.md:127`
- **问题**：v2 已移除模块维度（changes/ 是项目级扁平目录），`eo-archive` 只接受 change-id（eo-change 场景 A 提示的 `/eo-archive <change-id>` 是正确口径）。eo-flow 的「通过后的下一步」表却教 agent 向用户提示带 `<module>` 参数的调用。
- **依据原则**：Sediment / Relevance（"stale: drifting out of date as the behaviour it describes changes"）；Duplication（下一步提示在 eo-flow 与 eo-change 两处各写一份，已经漂移）。
- **建议**：改为 `/eo-archive <change-id>`；顺带检查该表与 eo-change 第八步提示的单一来源问题（见 P2-7）。

### [P1-2] mermaid.md 整体仍写给 v1 spec 体系

- **文件:位置**：`eo-doc-manager/references/mermaid.md:5-8`（被谁引用名单）、`:14-18`（图类型表的「spec §1 / spec §3 / eo-doc/ARCHITECTURE.md」）、`:114` 与末尾审查清单（「归档后 spec 流程图残留 :::new」）、§6（「Delta 只有 1 条 ADDED」）
- **问题**：v2 已无 spec、无 Delta、无 `eo-doc/ARCHITECTURE.md`；「被以下 skill 引用」列出的 eo-project-init / eo-project-update 实际不引用本文件，真正引用它的 eo-recall（SKILL.md 第四步）反而不在名单里。change 模板 §6 注释明确把执行者引到这份规范，agent 会照着不存在的落点（spec §3）和不存在的工件（ARCHITECTURE.md）行事。
- **依据原则**：Sediment（"stale layers that settle because adding feels safe and removing feels risky"）；Relevance；Single Source of Truth（引用者名单是第二份易漂移的元数据，且已漂移）。
- **建议**：全文按 v2 重写落点列（change §6 / state 重画图 / recall 输出）；删除 spec/Delta/ARCHITECTURE.md 条目；「被谁引用」名单要么删掉要么修正。

### [P1-3] index-templates.md 声称 eo-doc/ 仍含 `dev/`

- **文件:位置**：`eo-doc-manager/references/index-templates.md:18`
- **问题**：「重构后 `eo-doc/` 仅保留 `agent-handbook/` / `state/` / `dev/` / `templates/`」——`dev/` 恰是 v2 移除的目录（被 `changes/` 取代），且本句与同 skill SKILL.md 的目录结构图直接矛盾。目录清单在 SKILL.md、config.md、本文件三处各写一份，本处已经漂移。
- **依据原则**：Duplication → 漂移（"change one place, you must change the others"）；Sediment。
- **建议**：改为 `agent-handbook/ / state/ / changes/ / templates/`，或干脆删掉这句（目录结构的单一来源在 SKILL.md / config.md，本文件只需管 INDEX 格式）。

### [P1-4] eo-brainstorming 复述 questioning.md 的决策台账，未引用 eo-shared

- **文件:位置**：`eo-brainstorming/SKILL.md:135-165`（决策池维护）、`:204`（每轮 1-2 问）、`:69`（判断不了时直接问一句）
- **问题**：「已钉（locked）/ 未钉（open）/ 不得隐式推翻 / 冲突显式提示 / upstream 优先」与 `eo-shared/questioning.md` §2/§3 是同一套纪律的两份正文，且 brainstorming 全文没有一处引用 questioning.md——而 `eo-shared/README.md` 的「被谁引用」表声称 questioning.md 被 eo-brainstorming 引用。这正是 eo-shared/README 维护规则里点名的 v1 教训模式（「规程复制进 3 个 skill 各自漂移」），且漂移已发生：questioning.md 有 defer 三态与「defer 全篇上限 3 条」，brainstorming 的池只有两态、无 defer 口径；两边的台账规则将各自演化。
- **依据原则**：Single Source of Truth / Duplication；也违反本仓库自订的维护规则（eo-shared/README.md 末段）。
- **建议**：决策池一节收缩为「台账三态、预算、冲突提示以 [../eo-shared/questioning.md] 为准」+ 仅保留 brainstorming 特有增量（决策面池的依赖图排序、每 5-7 轮进度报告、疲劳菜单、典型 upstream 链）；同时把 eo-shared/README 的表修正为与实际引用一致。

### [P1-5] eo-handoff 泄漏设计对话语境：「用户给的例子里有 13 条」

- **文件:位置**：`eo-handoff/SKILL.md:118`
- **问题**：「用户给的例子里有 13 条，那个密度是合格的」——运行时的 agent 没有任何「用户给的例子」可对照，这是 skill 设计讨论的上下文残留，指向一个执行时不存在的参照物（157/161 行示例里的「13 条」同源）。关键约束表里已有可执行版本（「口径太少（<5 条）多半是漏了」）。
- **依据原则**：Relevance（"never bearing on the task — mere exposition"）；skill 正文不该有写给评审者/编辑者的内容。
- **建议**：删除该句，保留「<5 条即重扫对话」的可执行判据（一处即可，目前 118 行与 143 行还构成一次 Duplication）。

### [P1-6] 「AC 写漏」的指路三方打架（体系级缝隙）

- **文件:位置**：`eo-test/SKILL.md:60` ↔ `eo-fix/SKILL.md:5`（NOT FOR）↔ `eo-implement/SKILL.md:45`
- **问题**：同一件事（流程内发现 AC 写漏）有三种互相矛盾的指路：eo-implement 步骤 4 说「告知用户，经确认后就地补进 change.md」；eo-test 约束说「记录到报告并建议用户走 /eo-fix 判定」；而 eo-fix 的 NOT FOR 明确把「implement-test-review 循环内的反馈」排除在外（归 implement 模式二）。按字面执行，test 把用户送到 fix，fix 的边界又把这类场景推回去——agent 在两个 skill 的描述之间弹跳。
- **依据原则**：体系级职责边界（Granularity——split 的意义在于边界互斥）；Description 是 agent 选择加载的唯一依据，互相指向矛盾即 invocation 层的 bug。
- **建议**：统一口径为「循环内 AC 写漏 → 记录进 test.md 并建议回 /eo-implement（其步骤 4 已含就地补 AC 的确认流程）」；/eo-fix 只保留流程外口喷场景的 AC 补写权（其取证路第 3 行）。

### [P1-7] eo-brainstorming 体量失衡（329 行，无 references/）

- **文件:位置**：`eo-brainstorming/SKILL.md` 全文（全套最长的 SKILL.md，是次长者的 1.13 倍、中位数的 3 倍）
- **问题**：两个提问工具箱（探索/塑形，共 ~70 行示例问句）、70 行固定模板、典型 upstream 链，都是典型的按需查阅 reference——不是每次运行每条路径都需要（探索模式用不到塑形工具箱，反之亦然，这正是标准说的 branch 分野）；它们淤在顶层，把「意图识别 → 对话循环 → 收敛 → 落盘 → 捕获出口」的主干步骤埋在中间。
- **依据原则**：Sprawl（"the cure is the ladder"）；Progressive Disclosure（"disclose what only some branches need, inline what every path needs"）；Information Hierarchy（in-file reference 埋没 steps 是 variance 杠杆）。
- **建议**：建 `references/question-toolkits.md`（两个工具箱 + upstream 链示例）与 `references/record-template.md`（固定模板），SKILL.md 各留一行带触发条件的指针（「进入探索模式提问前读 …」）。预计顶层可减 ~140 行。

### [P1-8] GUIDE 与 conventions.md 就「tmp/eo/ 是否进 .gitignore」互相矛盾

- **文件:位置**：`docs/GUIDE.md:237` ↔ `eo-shared/conventions.md`（§1 纪律第 2 条）↔ `eo-handoff/SKILL.md:145`
- **问题**：conventions.md 与 eo-handoff 约束表都说「`tmp/eo/` 由 eo-project-init 写入 .gitignore」（eo-project-init §8 也确实执行），GUIDE 却写「不进 `.gitignore`（项目自决）」。GUIDE 的 handoff 一节几乎整节复写 skill 正文（定位表、6 段骨架、何时用），这次漂移是复写的直接代价。
- **依据原则**：Duplication → 漂移；Single Source of Truth。
- **建议**：GUIDE 该句改为与 conventions 一致；handoff 一节收缩为「一段定位 + 指向 skill/conventions 的链接」，不再全文复写。

---

## P2 — 可改进

### [P2-1] v1 残留零星清单（各一处，机械修复）

| 文件:位置 | 残留 | 依据 |
|---|---|---|
| `eo-brainstorming/SKILL.md:296` | 模板注释「在 spec / change 阶段查阅依据」——spec 已移除 | Sediment |
| `eo-implement/references/implement-deviation-template.md:8` | frontmatter `module: <module-name>`——模块维度已移除 | Sediment |
| `eo-review/references/review-template.md:67`、`eo-test/references/test-template.md:41` | `TODO-S1` 编号制式；change-template 用的是 `TODO-1`（Batch 分组无 S 前缀），三个产出模板间制式不一致 | 模板与正文自洽 |
| `README.md:120` | mermaid 节点 label `tmp/<topic>-handoff.md`——v1 路径，同文件 147 行与 migration 文档均已是 `tmp/eo/handoff/<topic>.md` | Sediment（用户可见误导） |

### [P2-2] eo-recall 的 description 把 identity 塞进了触发器

- **文件:位置**：`eo-recall/SKILL.md:3-5`
- **问题**：description 中段（「按问题类型走检索瀑布（state / agent-handbook / change 已钉决策 / decisions / brainstorm），分层作答、每个论断带出处；复杂逻辑可产 mermaid 或一次性 HTML 解释页」）是正文已有的工作方式描述，对触发决策零贡献，却每回合占据上下文。这是全套最长的 description。
- **依据原则**：Writing the description——"Cut identity that's already in the body. Keep the description to triggers"；Context Load。
- **建议**：压缩为「只读的回忆与解释入口。触发：当时怎么设计的 / 这个逻辑怎么实现的 / 为什么这么定 / 帮我回忆 / recall / /eo-recall。NOT FOR: …」。同类瘦身（程度较轻）：`eo-design/SKILL.md:4` 的四模式枚举（init/variants/apply/audit 不是用户会说的触发词，模式路由表在正文已有）、`eo-fix/SKILL.md:4` 的三层机制描述可减半。

### [P2-3] 粒度硬指标数值多点复述

- **文件:位置**：`eo-shared/granularity.md`（单一来源）之外：`eo-change/SKILL.md:16`、`:61`、`:99`；`eo-change-review/SKILL.md:113`（模板内）；`docs/GUIDE.md:147`
- **问题**：「TODO 3-7 / 10 硬上限、500 软 / 700 硬」在 skill 正文出现 3 次 + 模板 1 次 + GUIDE 1 次。granularity.md 自称「试运行」数值——一旦调参需要改 6 处。
- **依据原则**：Duplication / Single Source of Truth。
- **建议**：eo-change 内保留一处（第六步的执行点），核心理念与关键约束改为「超标拆序列（数值见 granularity.md §1）」；change-review 模板的软硬标括注可保留（报告可读性），但 GUIDE 处加"以 granularity.md 为准"。

### [P2-4] eo-doc-manager 的迁移史内容与重复 frontmatter 块

- **文件:位置**：`eo-doc-manager/SKILL.md:49-59`（「已移除的目录」表）、`:118`、`:152`（两处「与旧版差异」引用块）、`:164-180`（frontmatter YAML，与 `references/templates.md` 的通用模板重复）
- **问题**：「旧版如何、v2 为何不同」是写给迁移读者的叙事，不改变执行行为（防止重建旧目录的作用一句禁令即可承担）；frontmatter 规格在 SKILL.md 与 templates.md 各一份。
- **依据原则**：Relevance（exposition）；Sediment；Duplication。
- **建议**：迁移叙事移入 docs/migration-v1-to-v2.md（多数已在）；SKILL.md 保留一行「不再处理 doc/dev/design/research/knowledgebase，遇到即提示迁移」；frontmatter 块只留 templates.md 一份，SKILL.md 改指针。

### [P2-5] eo-shared/README「被谁引用」表已漂移

- **文件:位置**：`eo-shared/README.md`（表格）
- **问题**：questioning.md 声称被 eo-brainstorming 引用（实际未引用，见 P1-4）；ac-spec.md 声称被 eo-fix 引用（eo-fix 正文谈 AC 但无链接）；granularity.md 行漏掉 eo-brainstorming 与 change-template 两个实际引用者；conventions.md 写「全部」（eo-backlog、eo-project-lesson 等并未引用）。反向索引本身是第二份真相，天然易漂移。
- **依据原则**：Duplication（元数据级）；Single Source of Truth。
- **建议**：要么删掉「被谁引用」列（grep 可得），要么在改动引用关系时同步维护并放宽措辞（「主要消费方」）。

### [P2-6] 看板条目模板两处重复

- **文件:位置**：`eo-project-init/SKILL.md:253-263`（§13）↔ `eo-project-update/SKILL.md:113-121`（§4）
- **问题**：同一个看板条目块（状态/当前阶段/下一步/阻塞/决策/经验）在两个 skill 各写一份，字段增删要改两处。
- **依据原则**：Duplication。
- **建议**：模板放 `eo-project-init/templates/kanban-entry.md`（或 eo-shared），两个 skill 都引用。

### [P2-7] 「下一步指路」表在 eo-flow 与各 skill 两层重复

- **文件:位置**：`eo-flow/SKILL.md:120-131` ↔ `eo-change/SKILL.md:75-83`、`eo-change-review/SKILL.md:69-72` 等各 skill 的终态措辞
- **问题**：流程「通过后下一步」的口径在 eo-flow 的表格里整套重写了一遍（P1-1 的漂移即源于此）。
- **依据原则**：Duplication → 漂移。
- **建议**：eo-flow 改为「读回包对应产出文件后，按该 skill 速报中的『下一步』转达用户」，只保留 eo-flow 特有的差异（change-review 修订内联、archive 只吃 review 通过）。

### [P2-8] eo-brainstorming 的否定式引导块

- **文件:位置**：`eo-brainstorming/SKILL.md:25-29`（绝对禁止，逐条引用被禁话术原文「这个想法太棒了！」等）、`:322-328`（关键约束 6 条全部以「不」开头）
- **问题**：禁令直接把被禁句式打印进上下文（标准原文："don't think of an elephant names the elephant"）；角色定位一节其实已给出正面行为（诚实协作者四条），禁止块是它的负片。
- **依据原则**：Negation（"prompt the positive so the banned one is never spoken"）。
- **建议**：删除引号内的示范话术，禁止块压缩为一条硬护栏（「每个方向必须至少提出一个带替代方案的质疑」——本身就是正面表述）；关键约束改写为正向祈使句（「停留在做什么/为什么做」「每轮维护决策池并按 upstream 推进」等，其中数条已有正向版本，直接去重）。

### [P2-9] EO_HOME 覆盖只存在于 config.md

- **文件:位置**：`eo-project-init/references/config.md`（「根路径可通过 EO_HOME 覆盖」）↔ `eo-project-init/SKILL.md:35-38`（迁移命令硬编码 `~/.eo`）
- **问题**：声明了环境变量覆盖，执行步骤的内联 bash 不感知它——两份口径。
- **依据原则**：Single Source of Truth；指令可执行性。
- **建议**：要么迁移命令写 `${EO_HOME:-$HOME/.eo}`，要么从 config.md 删掉 EO_HOME 声明（若尚无真实消费者）。

### [P2-10] re-sync 重置的 cursor JSON 缺字段

- **文件:位置**：`eo-doc-manager/references/re-sync.md:56-61` ↔ `git-sync.md` 的 cursor schema
- **问题**：git-sync 定义 cursor 含 `sync_count` / `archive_count`；re-sync Step 4 的重置 JSON 没有这两个字段，重置后计数语义（清零？保留？）未定义。
- **依据原则**：模板与正文自洽；Completion Criterion 的可判定性。
- **建议**：re-sync 的 JSON 补 `"sync_count": 0`，并注明 archive_count 保留原值（或明确清零）。

### [P2-11] eo-design 关键约束一句自相矛盾 + audit 产物形态与 conventions 不一致

- **文件:位置**：`eo-design/SKILL.md:74`、`:69` ↔ `eo-shared/conventions.md` §1
- **问题**：「不碰 eo-doc/ 之外的项目文档；本 skill 只产 DESIGN.md、约束注入段…」——DESIGN.md 与 CLAUDE.md 注入段都在 eo-doc/ 之外，同一句里前半禁止后半允许，靠读者脑补「除外清单」。另 audit 报告写 `tmp/eo/design/<date>-audit.md`（散文件），conventions 里 design 域的形态是 `design/<date>-<topic>/`（目录）。
- **依据原则**：指令无含糊措辞；单一来源（tmp 命名空间形态归 conventions）。
- **建议**：改为白名单式正向表述（「本 skill 的全部落盘产物限于：DESIGN.md、CLAUDE.md 注入段、tmp/eo/design/、changes/<id>/design/」）；audit 报告并入 `tmp/eo/design/<date>-audit/` 或在 conventions 补一行 audit 形态。

### [P2-12] eo-flow「/smux 的 read-act-read 四段」表述含糊

- **文件:位置**：`eo-flow/SKILL.md:93`
- **问题**：「read-act-read」字面是三段却称「四段」，且这是外部 skill（smux）的内部术语，eo-flow 未解释也未指明去 smux 哪里查——对没装 smux 语境的执行者不可解析。
- **依据原则**：Context Pointer 的措辞决定可达性；指令可直接执行。
- **建议**：改为「按 /smux 技能的跨 pane 发送流程发出（发送前后各 read 一次确认状态）」或直接写出四步。

### [P2-13] eo-change:103 写给编辑者的维护规则

- **文件:位置**：`eo-change/SKILL.md:103`
- **问题**：「提问纪律、AC 规范、粒度判据的正文只在 eo-shared/，本文件不复述」是给 skill 维护者的纪律，不是给执行 agent 的指令（agent 无法「不复述」一个文件）。
- **依据原则**：Relevance；No-Op（对执行行为零改变）。
- **建议**：删除（维护纪律的家在 eo-shared/README.md 已有）。同类：`eo-doc-manager/SKILL.md:98`「（原名保留，指代 state 的写作规范）」与 `doc-style.md:5` 的文件名历史注——保留一处（doc-style.md 内）即可。

### [P2-14] 广触发词在非 eo 项目的误触发成本

- **文件:位置**：`eo-implement/SKILL.md:4`（「实现 / 写代码」）、`eo-change/SKILL.md:4`（「新增 / 加功能」）
- **问题**：这些是任何编码会话都会出现的高频词。在未 init 的仓库中，它们会触发加载 → 读 `.eo-project.json` 失败 → 报错退出，把一次普通的「帮我写个函数」变成一次流程打断。前置报错是正确的失败方式，但触发面可以更准。
- **依据原则**：Description 的触发词是 agent 加载的唯一依据；误触发是 invocation 层的 Predictability 问题。
- **建议**：description 补一个廉价限定或 NOT FOR（如「NOT FOR: 未接入 eo-skills 的仓库里的日常编码」），或触发词前加「按 change …」语境词。实测后再定——若实际误触发率低，此条可关闭（No-Op 的判定是跑出来的，不是辩出来的）。

### [P2-15] git-sync 汇报示例与默认口径打架（微小）

- **文件:位置**：`eo-doc-manager/references/git-sync.md`（Step 8 示例首行「基于 abc1234..def5678 + 未提交变更」）
- **问题**：默认（推荐）路径是「只取已提交增量」，示例却展示了带脏变更的口径，示例比规则更容易被模仿。
- **依据原则**：模板/示例与正文自洽。
- **建议**：示例改为纯 committed 区间，脏变更口径加括注「（选了含脏变更时）」。

### [P2-16] eo-change-review 推荐条件两处口径

- **文件:位置**：`eo-change-review/SKILL.md:10` ↔ `eo-change/SKILL.md:78`
- **问题**：「AC ≥5 / 含 §5 / refactor / 高风险」的建议触发条件在两个 skill 各写一份（当前一致，属漂移候选）。
- **依据原则**：Duplication。
- **建议**：以 eo-change-review 开头一句为单一来源，eo-change 场景 A 改为「符合 /eo-change-review 建议条件时提示」。

### [P2-17] GUIDE 对 skill 正文的成段复写（漂移温床）

- **文件:位置**：`docs/GUIDE.md` 的 handoff 节（205-237，6 段骨架表全文复写）、eo-flow 节（步骤复写）、「为什么修 bug 要喊 /eo-fix」节（三层机制复写）
- **问题**：GUIDE 作为人类文档允许冗余，但成段照抄 skill 正文的部分已经产生一处实际矛盾（P1-8）。skill 是单一来源，GUIDE 应写「为什么」与导览，不重写「怎么做」。
- **依据原则**：Duplication / Single Source of Truth（对文档体系同样成立，任务口径也要求 README/GUIDE 一致性）。
- **建议**：三节各收缩为动机 + 边界表 + 指向 SKILL.md 的链接；「为什么修 bug 要喊 /eo-fix」写得很好，建议保留但去掉与 skill 逐字重合的机制细节。

---

## 体系级观察

### ✅ 验证通过（无需动作，供安心）

1. **跨 skill 相对引用在软链安装下可靠**。逐条脚本校验：全部 43 组真实相对链接目标存在（报「broken」的 23 条均为模板代码块内的占位链接，正常）。解析推演：install.sh 用 `ln -s`、install.bat 用 `mklink /J`（junction，物理解析），`../eo-shared/*.md` 无论按逻辑路径（`~/.claude/skills/eo-shared` 同样被链）还是物理路径（仓库内兄弟目录）解析都命中——因为两棵树都是完整的。**唯一失效场景**：用户绕过脚本手工拷贝单个 skill 目录。建议 README 安装节加一句「必须整套链接/拷贝（含 eo-shared），单拷某个 skill 会断 ../eo-shared 引用」。
2. **eo-shared 非技能目录模式合规**。与标准 GLOSSARY「External Reference」条目严丝合缝（"plain file, no description, not invocable, the only shared home two user-invoked skills can use"）。隐患仅剩两点：(a) 各 agent 运行时对无 SKILL.md 目录的容忍度是经验假设（Claude Code 当前忽略，其它 runtime 未验证），可在 eo-shared/README 标注已验证的 runtime；(b) install 的「已存在即跳过」意味着 eo-shared 改名/重构时旧链残留——migration 文档已示范过清理手法，可复用。
3. **强实践值得保持**：速报模板 + 「缺速报 = 流程未完成」是锋利的 completion criterion（可判定、防 premature completion）；「STOP and VALIDATE」「Update preserves context. New change provides clarity.」「按需付费」「证据瀑布」是高质量 leading word 用法；状态流转、commit 前缀、tmp 命名空间的单一来源纪律在 conventions.md 落得很实。
4. **触发词体系总体不打架**：fix 归 eo-fix、循环内修复归 eo-implement 的分工在 description 层干净（v1 的 implement 抢 fix 触发词已修）；review/change-review 的碰撞由 eo-review 的「前置拦截」硬性化解，是好的防误用设计。
5. **数量核对**：磁盘实际 17 个 skill + eo-shared（任务描述的「18 个」与磁盘不符，以磁盘为准）；README「我该用哪个」表覆盖 16 个 + 明示 change-review 为可选增强，无遗漏。

### ⚠️ 需要一次决策的结构问题

6. **eo-doc-manager references 是 sediment 重灾区**（P1-2、P1-3、P2-4、P2-10、P2-15 全部落在这里）。这批文件多数直接继承自 v1，只做了局部改写。建议专开一个 change 对 `eo-doc-manager/references/` 做一次按 v2 口径的通读清淤，而不是逐条打补丁。
7. **description 总上下文负担**：17 条 description 合计约 1100+ tokens 常驻。P2-2 的三条瘦身后可省约 15%。若未来继续加 skill，可考虑把纯手动触发的（如 eo-archive、eo-flow 实际几乎总是斜杠调用）转 user-invoked——但当前 brainstorming 捕获出口→eo-change、archive→doc-manager 的 skill 间到达依赖存在，转换前需逐个核对到达链。

---

## 附录：逐 skill 一句话评级

| skill | description | 正文操作性 | 渐进披露 | 突出问题 |
|---|---|---|---|---|
| eo-archive | ✅ 优 | ✅ 五层结构清晰 | ✅ | — |
| eo-backlog | ✅ | ✅ | ✅（无需下沉） | — |
| eo-brainstorming | ✅ | ⚠️ 决策池复述 eo-shared | ❌ 329 行无 references/ | P1-4、P1-7、P2-8 |
| eo-change | ✅ 优 | ✅ 引用纪律最佳 | ✅ | P2-3、P2-13 |
| eo-change-review | ✅ | ✅ 终态措辞二选一设计好 | ✅ | P2-16 |
| eo-design | ⚠️ 模式枚举 | ✅ | ✅ visual-craft 下沉得当 | P2-11 |
| eo-doc-manager | ✅ | ⚠️ 迁移史混入 | ✅ 结构好但 refs 陈旧 | P1-2、P1-3、P2-4 |
| eo-fix | ⚠️ 略长 | ✅ 全套最佳之一（按需付费/证据瀑布） | ✅ investigation 下沉得当 | — |
| eo-flow | ✅ | ✅ 坑位标注扎实 | ✅ | P1-1、P2-12 |
| eo-handoff | ✅ | ✅ | ✅ | P1-5 |
| eo-implement | ✅ 优 | ✅ | ✅ | 模板 module 残留 |
| eo-project-init | ✅ | ❌ 节号断链 | ⚠️ 291 行可再沉 | **P0-1** |
| eo-project-lesson | ✅ | ✅ 与 eo-shared/lessons 分工干净 | ✅ | — |
| eo-project-update | ✅ | ✅ | ✅ | P2-6 |
| eo-recall | ❌ 过长 | ✅ 检索瀑布设计好 | ✅ | P2-2 |
| eo-review | ✅ | ✅ 前置拦截是亮点 | ✅ | 模板 TODO-S1 |
| eo-test | ✅ | ✅ | ✅ | P1-6 |
| eo-shared（非 skill） | n/a | ✅ | n/a | P2-5（被谁引用表） |
