# eo-skills v2 第三轮审查报告（r2 核验 + 两波新设计审查）

> 审查人：Claude（Orca worker）｜ 日期：2026-07-09 ｜ 准绳：writing-great-skills（同前两轮）
> 基线：bb7b58c → HEAD c41e66d，含三波提交——`7b99095`（r2 双审合并修订）、`dd581e8`（knowledgebase 正式移除）、`c41e66d`（eo-project 系列重构）
> 方法：三个 commit diff 全文通读 + 当前树逐点回验；机械核查全部重跑——17 个（现 16 个）SKILL.md YAML frontmatter 脚本校验、相对链接全量扫描、改名/kanban/log.md/节号残留 grep。

## 结论速览

- **r2 核验**：7 条编号问题（NEW-1~7）+ 2 条微量残留 **全部修复，9/9（100%）**，无一引入新问题；修订顺带修掉了一个我 r2 漏检的 P0（eo-test frontmatter 含裸冒号导致 YAML 解析失败——codex 侧发现，现全部 SKILL.md 脚本校验通过）。r1 遗留的两条部分修复项（mermaid 消费方名单、GUIDE eo-flow 节复写）也在 7b99095 一并关闭。
- **两波新设计**：整体执行质量高（kanban 退役的四处口径一致、project-init 重排后节号引用零残留、record 双模板分工清晰），但发现 **P1×1 + P2×7 + 微×2**——集中在「波及面同步不完整」：eo-backlog 的「未接入」类目体系没跟上 knowledgebase 移除，若干消费方口径没跟上 record 的 INDEX 化。

---

## 一、r2 报告逐条核验（全部落在 7b99095）

| # | r2 条目 | 状态 | 核验说明 |
|---|---------|------|---------|
| NEW-1 (P1) | init §1.5 步骤 1 默认补写吞掉步骤 5 询问 | ✅ 已修复 | 步骤 1 明确「`board` / `github` 段缺失时不在本步补写（补了默认关闭值会吞掉第 5 步的询问），只记录缺段」——连理由都写进去了；c41e66d 重排后该口径保持，并新增 kanban_path 忽略规则，不冲突 |
| NEW-2 (P1) | eo-flow「文件末尾速报」前提不成立 | ✅ 已修复 | 采纳我的方案 a：test/review/change-review 三个模板末尾新增必填「## 速报」节（标注「机器可读出口，与对话速报同款内容」），eo-flow 改为「读产出文件末尾的『## 速报』节」，并补回 implement 无报告文件的专属口径（TODO 勾完 → /eo-flow test）。信息闭环恢复。遗留一个小尾巴见 P2-6 |
| NEW-3 (P2) | `../docs/migration` 链接安装树不可达 | ✅ 已修复 | 改纯口头指路（「见 eo-skills 仓库的 docs/migration-v1-to-v2.md」），冗长 fallback 括注删除 |
| NEW-4 (P2) | 单源化丢「问题数≠选项数」与混合模式口径 | ✅ 已修复 | questioning.md §2 补「问题数 ≠ 选项数——预算约束的是决策面数量而非选项数量」（正位单源，eo-change/eo-design 同享）；brainstorming 模式表 C 行补「塑形部分照常维护台账，探索部分自由讨论」 |
| NEW-5 (P2) | eo-change 场景 A 弱指针 | ✅ 已修复 | 改真链接 `[../eo-change-review/SKILL.md]` |
| NEW-6 (P2) | §1.5 不修复 vault 软链本体 | ✅ 已修复 | 步骤 4 扩为「.gitignore 与软链核对」，含软链存在性与指向校验、按建软链节重建；c41e66d 重排后引用「9. 建立软链」与新节号一致 |
| NEW-7 (P2) | mermaid 消费方名单残留失真 | ✅ 已修复 | 名单删 eo-review、eo-change-review 行改为条件描述；同时在 eo-change-review 维度 6 加了真实指针（「change 含 §6 流程图时对照 mermaid.md §5 审查清单核对」）——名单与指针终于互相成立 |
| 微量 1 | handoff <5 条判据双写 | ✅ 已修复 | :118 改为指向关键约束表行，单一来源 |
| 微量 2 | re-sync JSON 非法占位符 | ✅ 已修复 | JSON 只留 `sync_count: 0`，`archive_count` 保留语义移入旁注 |
| （r1 遗留）P1-2 残余 / P2-17 残余 | mermaid 名单、GUIDE eo-flow 节 | ✅ 已修复 | GUIDE eo-flow 节收缩为「用法一行 + 设计要点，流程以 SKILL.md 为准」。GUIDE「为什么修 bug」节仍保留三层机制叙述——r2 已降级为低优先（写给人的动机论证），不再追 |
| （追加）codex 侧 P0 | eo-test description 单行含 `NOT FOR:` 裸冒号 → YAML 解析失败 | ✅ 已修复 | 改块标量（`|`）；我本轮用 python-yaml 重验 16 个 SKILL.md 全部通过——这是我 r1/r2 两轮漏检的盲区（只查了语义没查可解析性），已记入本轮机械核查清单 |

**r2 核验结论：9/9 修复，无回归。**

---

## 二、两波新设计审查

### 先说做对了的（抽查通过项）

- **kanban 退役口径四处一致**：config.md（用户级字段删除、项目级标「已废弃：新配置 null / 存量被忽略」）、GUIDE（模式表看板列删除）、eo-project-init（§5 活跃项目数检查/§13 看板注册/输出摘要看板行全删，1.5 步骤 1 加「存量 kanban_path 忽略不改」）、migration（新增表行 + 步骤 8 迁移动作）。替代方案（Bases 聚合 roadmap frontmatter）在 roadmap 模板、config.md、GUIDE 三处口径一致。
- **project-init 重排后节号引用零残留**：grep 旧节号（§13/§14/第 13 步等）无命中；1.5 → 「8. 生成」「9. 建立软链」、§8 后开 → 1.5、§7 `--skip-code-side` 自指改「本节」——全部与新节号对齐。r1 时代的「看板条目单源指向 eo-project-update §4」链接随 §13 删除而消亡，无悬挂。
- **eo-project-record 双模板分工清晰**：类型判据一句话可执行（「教训回答下次怎么做，决策回答当时为什么」）；「流程内决策不进来」的三家分界（change §1 / brainstorming 决策表 / 流程外重大裁定）在 SKILL 与 how-it-works 图鉴两处口径一致；decision-template 的 frontmatter 与 reindex 的「trigger 仅 lesson」约定自洽；description 触发词覆盖两类且沿用「仅用户明确要求时」边界。52 行体量、模板下沉 references/，符合信息层级。
- **glossary 设计落位干净**：doc-style 特殊篇目约定（横切一篇、≥3 术语才建、定义只写业务语义）、git-sync 影响表加行并回指 doc-style（单源）、splitting 判断表三个新去向例句准确。
- **改名波及面大体完整**：backlog/fix/investigation/handoff/eo-shared README/lessons.md/GUIDE/README/migration 全部改到；README mermaid 还顺手修了 Rec/PRec 节点 ID 撞车；how-it-works 图鉴数组与「17 个目录」计数正确（16 skill + eo-shared）。
- **机械核查**：全部相对链接（含三波新增）双树可达、真实断链为零；16 个 SKILL.md frontmatter YAML 解析全过。

### P1

#### [R3-1] eo-backlog 的「未接入」类目体系未跟上 knowledgebase 移除——会重建已退役的小节

- **文件:位置**：`eo-backlog/SKILL.md:3`（description「未接入的未来规划」）、`:26`（输入示例「这个要等 research skill」）、`:40`（分类表路由到 `## 未接入（等 skill 支持再接入）`）、`:56`
- **问题**：dd581e8 的设计意图是「占位清零」——init 的 backlog 模板已删掉「未接入」节、config.md/GUIDE 把 backlog 定义收窄为「待办池 + 灵感」。但 eo-backlog 自身的四处口径全部未动：description（每回合常驻上下文）仍宣传一个已退役的类目；输入示例「这个要等 research skill」在 research/ 已接入后语义整个反了；分类表继续把「等 skill / placeholder / 暂时」路由到「未接入」节，而 §3 的兜底规则「小节若不存在（用户手改过模板），补齐小节标题再写入」会**主动重建**设计上刚删除的小节——skill 与模板的分类体系分家（同一结构两处定义，已经漂移）。
- **依据原则**：Single Source of Truth / Duplication（分类节结构在 init 模板与 backlog 分类表各写一份）；Sediment；Description 是常驻 context load，承载已失效类目最亏。
- **建议**：eo-backlog 三处同步——description 去掉「或未接入的未来规划」；输入删「未接入」类及示例；分类表删该行，原信号词（「等 skill」「暂时」）并入「灵感 & 以后再说」。若想保留「等条件成熟再做」的语义，在灵感条目后缀「（等 X）」即可，不需要独立小节。

### P2

#### [R3-2] eo-recall 消费 decisions/ 的方式与 record 的 INDEX 契约脱节

- **文件:位置**：`eo-recall/SKILL.md:39`（「`<project_root>/decisions/`（文件名即索引）」）↔ `eo-project-record/SKILL.md` 约束（「没进索引的记录等于没写（**消费方只扫 INDEX**）」）
- **问题**：record 这波给 decisions/ 建立了 INDEX.md（表格含 status/summary），并把「只扫 INDEX」写成对消费方的硬约束；但点名的消费方 eo-recall 仍按旧口径「文件名即索引」检索——生产方契约与消费方行为背离。INDEX 里的 `summary`（检索锚点，模板标注必填）和 `status: superseded` 过滤在 recall 侧都用不上（recall 可能引用已被取代的决策）。
- **依据原则**：Single Source of Truth（消费协议应两端一致）；record 自己的约束成了无人执行的规则。
- **建议**：eo-recall 缘由瀑布改「查 `<project_root>/decisions/INDEX.md`（若存在，按 summary 匹配并跳过 superseded；无 INDEX 退化为按文件名扫）」。

#### [R3-3] record 的消费方表声称 eo-change 事实自查消费 decision，但 eo-change 没有这一站

- **文件:位置**：`eo-project-record/SKILL.md`（类型表「decision 谁消费：eo-recall 缘由瀑布；**eo-change 事实自查**」）↔ `eo-change/SKILL.md:37-44`（事实自查五站：state / changes INDEX / lessons / research / DESIGN——无 decisions）
- **问题**：「名单式元数据与真实指针不符」的第三次复发（前两次：mermaid 消费方名单 r1/r2、doc-style glossary 消费方）。宣称的消费路径在消费方没有对应步骤，decision 记录在 change 起草时实际不会自动出现。
- **依据原则**：Context Pointer（无指针即不可达）；消费方名单是易漂移的第二真相。
- **建议**：二选一——eo-change 事实自查加一站「变更触及既有重大裁定的领域 → 扫 decisions/INDEX.md（若存在）」；或 record 表里删掉 eo-change，只留 recall。鉴于 decision 的定位是「会被反复问『当时为什么』」，加站更符合设计意图。**体系级建议**：这类「谁消费我」名单已三次漂移，日后新增时默认反向落笔——只在消费方写指针，生产方不留名单（或标注「以消费方正文为准」）。

#### [R3-4] research/ 有两个消费点、零个生产规范

- **文件:位置**：`eo-project-init/references/config.md:141`（「research/ 按需，调研沉淀（**带 INDEX + frontmatter**…）」）↔ 全仓无任何 skill 生产 research/ 或定义其格式
- **问题**：eo-change/eo-recall 各加了消费站（写法「扫其 INDEX，若存在」有容错，好），但「带 INDEX + frontmatter」的格式承诺没有主人：谁建 INDEX、frontmatter 含哪些字段（有没有 summary/tags 锚点）、消费方按什么匹配——全部悬空。INDEX 缺失时消费方行为未定义（跳过？按文件名扫？）。
- **依据原则**：Single Source of Truth（格式口径无家）；Completion Criterion（「扫其 INDEX」在 INDEX 不存在时不可判定）。
- **建议**：最小修——config.md 该行改为「research/ 按需，调研沉淀（当前由用户手工维护；有 INDEX.md 则消费方按其 summary 匹配，无则按文件名扫）」，把退化行为写进两个消费站的括注。将来真有 research 生产 skill 时再立格式规范（backlog 里已有远期条目，方向正确）。

#### [R3-5] maintenance.md 的调研去向未跟上 research/ 接入

- **文件:位置**：`eo-doc-manager/references/maintenance.md:43` ↔ `splitting.md:17,26`
- **问题**：splitting.md 已把调研类内容的去向改为 `<project_root>/research/`，同 skill 的 maintenance.md 批量导入一节仍写「提示用户这些内容应进入 `<project_root>/docs/` 或 `backlog.md`」——同一 skill 内两份分流口径，一新一旧。
- **依据原则**：Duplication → 漂移（分流规则的单一来源应是 splitting.md）。
- **建议**：maintenance.md 该句改为「按 splitting.md 的分流规则提示归属（规划/设计 → docs/，调研 → research/）」或直接引用 splitting.md 不复述。

#### [R3-6] how-it-works.html 残留 `/eo-project-lesson`

- **文件:位置**：`docs/how-it-works.html:410`（STEP 5「回响」时间线 `who:"/eo-fix · /eo-project-lesson"`）
- **问题**：图鉴数组（CAT）改成了 eo-project-record，但五步时间线（STEPS）漏改——同页两个组件对同一 skill 各说各话，用户点开会找不到 `/eo-project-lesson`。
- **依据原则**：改名波及面完整性（本轮任务点名维度）。
- **建议**：改 `who:"/eo-fix · /eo-project-record"`。

#### [R3-7] change-review 的「下一步」出现第二来源，且丢了 draft 确认前置

- **文件:位置**：`eo-change-review/SKILL.md`（模板新增「## 速报」节：「下一步：（通过）/eo-implement …」）↔ 同文件第四步终态措辞（「通过：下一步 /eo-implement（**status 若仍为 draft，先回 /eo-change 对话确认**）…」）
- **问题**：速报节修好了 r2 NEW-2 的主体，但让「下一步」在同一 skill 里有了两份措辞：终态措辞（含 draft 需先确认的关键前置）与模板占位（无此前置）。eo-flow 按合约只读文件速报节，转达的下一步会漏掉确认环节——好在 eo-implement 前置会拦住 draft（自愈），只是多绕一跳。test/review 两个模板的速报占位与其对话速报措辞一致，无此问题。
- **依据原则**：Duplication（同一口径两处措辞，已现微漂移）。
- **建议**：模板速报占位补齐：「（通过，status=confirmed）/eo-implement；（通过但仍 draft）先回 /eo-change 确认；（需修订）回 /eo-change 修订后复审」；或终态措辞一节直接改为「按模板速报节措辞输出」，让模板成为唯一来源。

#### [R3-8] migration 的移除清单与清理命令不同步

- **文件:位置**：`docs/migration-v1-to-v2.md:16`（表：移除的 skill 含 eo-project-update）↔ `:27-29`（步骤 1 的 `rm -f` 清单只有四个旧 skill）↔ 步骤 8（只提 eo-project-lesson 软链清理）
- **问题**：eo-project-update 在表里宣布移除，但两处清理指令都没带上它——残留软链虽会因目标目录消失而变成悬挂链接（不加载、无害），但同一文档对三组残留（四旧 skill / lesson / update）给出两种半套处理，读者照做后仍留垃圾。
- **依据原则**：模板/指令与正文自洽。
- **建议**：步骤 1 的 rm 花括号清单加 `eo-project-update`（或步骤 8 一并列出 lesson + update）。

### 微量（记录备查）

1. `eo-project-record/SKILL.md:3`——description 触发词有「reindex lessons」但无「reindex decisions」，而正文 reindex 明确覆盖两类；补一个词即可。
2. `eo-project-init/SKILL.md:268`——约束「按需目录（phases / decisions / lessons / brainstorm / docs）init 时不预建」枚举漏了 `research/` 与 `board/`（config.md 目录树已收录两者，同为按需不预建）；两处枚举建议以 config.md 为准、SKILL 侧改「按需目录（清单见 config.md）init 时不预建」。

---

## 三、任务点名维度的专项结论

1. **改名引用完整性**：可执行文本（全部 skill + eo-shared + README + GUIDE + migration）已清零；残留仅 how-it-works.html 一处（R3-6）与 v2-design.md 的历史表述（背景文档记录决策过程，合法）。
2. **project-init 重排自洽性**：节号引用零残留、1.5 与重排后各节互指正确、步骤顺序（1→1.5 短路 / 1→2→…→12 主线）无交叉依赖问题；kanban 相关步骤删除后无悬挂引用。r2 修的 NEW-1/NEW-6 在重排中被正确保持。
3. **record 的 description 与双模板分工**：触发词质量好（两类动作短语 + 明确边界），分工判据一句话可执行，「流程内不进来」三家分界两处口径一致；瑕疵是消费方名单越位（R3-3）与 reindex 触发词半缺（微 1）。
4. **kanban 退役口径一致性**：config/GUIDE/README/migration/init 五处一致，替代方案（Bases 聚合 roadmap frontmatter）三处口径一致；唯 migration 清理命令半套（R3-8）。
5. **新相对链接可达性**：全绿（含 record → eo-shared/lessons.md、record → references/decision-template.md、change-review → mermaid.md 等本波新增）。

## 总评

三波提交的工程纪律持续在线：r2 的 9 条全部修复且零回归，还主动修掉了我两轮漏检的 YAML 可解析性 P0（这条已加入我的机械核查清单）。新设计里 kanban 退役和 project-init 重排这两个高风险动作反而做得最干净；问题集中在**波及面的「最后一公里」**——eo-backlog 的类目体系（R3-1，唯一 P1）、三个消费方口径（R3-2/3/5）、一处 HTML 时间线（R3-6）。另有一个反复出现的模式值得立规矩：**「谁消费我」名单已第三次与真实指针脱节**（mermaid → glossary → record），建议今后此类名单只写在消费方正文里，生产方不留清单。
