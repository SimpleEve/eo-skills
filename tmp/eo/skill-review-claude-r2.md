# eo-skills v2 第二轮审查报告（对 commit bb7b58c 的核验 + 新问题扫描）

> 审查人：Claude（Orca worker）｜ 日期：2026-07-08 ｜ 准绳：writing-great-skills（同第一轮）
> 对象：commit `bb7b58c`（fable5+codex5.5 双审合并修订）后的当前工作树
> 方法：通读修订 diff 全文（33 文件，排除 tmp/ 报告），对第一轮 26 条逐一回验当前文件；相对链接全量重新脚本校验；AskUserQuestion / spec / dev / module 残留全仓 grep 清零核对；重点复读 eo-project-init 1.5、eo-brainstorming 重构后全文、eo-flow 第 4 步、questioning.md §4 及其全部 8 个引用点。

## 结论速览

- **核验**：第一轮 26 条中 **23 条已修复、2 条部分修复、1 条未修复（双方认可的观察项）**，按条通过率 88%（部分修复折半约 92%）。合并方案普遍不低于我的原建议，多处更优（如「已移除的目录」表改成行为指令、description 边界扩展到 backlog/update/lesson/test）。
- **新问题**：修订本身引入 **P1×2 + P2×5 +微量残留×2**。两条 P1 都属于「单一来源化时把信息移走了，但接收端没接住」——eo-project-init 1.5 的步骤自冲突（后开联动两问永不触发）和 eo-flow 速报前提错误（下一步信息实际不可达）。

---

## 一、第一轮 26 条逐条核验

| # | 条目 | 状态 | 说明 |
|---|------|------|------|
| P0-1 | init 更新/修复分支未定义、节号断链 | ✅ 已修复（**但引入 NEW-1**） | 新增 §1.5 六步幂等分支，节号引用改为标题文字（「继续本节第 3 小步」「进入『2. 询问运行模式』」），§9 后开场景反向指到 1.5——断链全部闭合。但 1.5 内部步骤 1 与步骤 5 存在顺序冲突，见 NEW-1 |
| P1-1 | eo-flow `/eo-archive <module> <change-id>` v1 签名 | ✅ 已修复 | 旧表整体删除；保留的例外行已是 `/eo-archive <change-id>`（eo-flow/SKILL.md:121） |
| P1-2 | mermaid.md 整体 v1 化 | ⚠️ 部分修复 | spec §x / ARCHITECTURE.md / Delta / 归档 spec 残留全部清除，图类型表、审查清单、§6 触发条件均已对齐 v2（change §6 / state/ / recall）✅。**差**：「主要消费方」仍列 `eo-change-review / eo-review`，但两个 skill 的 SKILL.md 至今没有任何指向 mermaid.md 的指针（grep 证实）——§5「审查清单（给 review 类 skill）」实际不可达，名单第二次失真。见 NEW-7 |
| P1-3 | index-templates.md 残留 `dev/` | ✅ 已修复 | 改为 `agent-handbook/ / state/ / changes/`，与 SKILL.md 一致 |
| P1-4 | brainstorming 复述 questioning.md 决策台账 | ✅ 已修复（伴随 NEW-4 小信息丢失） | 台账三态明确「以 questioning.md §3 为准」，正文只留三条塑形特有增量（依赖标注、进度报告、疲劳菜单）；「基础纪律以 questioning.md 为准」总括句到位。单源化方向完全正确 |
| P1-5 | handoff「用户给的例子里有 13 条」语境泄漏 | ✅ 已修复 | 改为可执行判据「口径少于 5 条多半是漏了」。微量残留：该判据仍在 :118 与 :143（关键约束表）双写，r1 建议留一处——不影响执行，见微量残留 |
| P1-6 | AC 写漏三方指路打架 | ✅ 已修复 | eo-test 约束改为「建议回 /eo-implement（其流程含确认后就地补 AC；循环内问题不出循环）」，与 eo-fix NOT FOR、eo-implement 步骤 4 三方自洽 |
| P1-7 | brainstorming sprawl（329 行） | ✅ 已修复 | 现 125 行；工具箱（59 行）与记录模板（65 行）下沉 references/，指针带明确触发时机（「进入对应模式的对话循环前读对应节」）——符合 branch 披露判据。主流程完整性核验见第二部分 B 节 |
| P1-8 | GUIDE 与 conventions 的 gitignore 矛盾 | ✅ 已修复 | 矛盾句随 handoff 节收缩整体删除；收缩后以 eo-handoff/SKILL.md 为准的写法正确 |
| P2-1 | 四处 v1 零星残留（spec 措辞 / module 字段 / TODO-S1 / README 旧路径） | ✅ 已修复 | 四处全清：record-template 改「change 起草与 /eo-recall 查阅依据」；deviation 模板删 `module:`；review/test 模板统一 `TODO-1`（test 还顺手加了 `AC-1 /` 列，更优）；README mermaid 标签改 `tmp/eo/handoff/<topic>.md` |
| P2-2 | description 瘦身（recall/design/fix） | ✅ 已修复 | 三条均砍掉 identity 只留触发词；design 触发词还改成了用户真实话术（「定设计系统 / 出几版视觉方案对比」）。额外超出建议范围：backlog/update/lesson/test 四条加了「仅用户明确要求时」+NOT FOR 边界，直接压低了行为钩子类 skill 的误触发面——好改动 |
| P2-3 | 粒度硬指标数值多点复述 | ✅ 已修复 | eo-change 三处全部改为指向 granularity.md §1；GUIDE 关键约束行改为「数值以 granularity.md 为准」。change-review 报告模板内的括注数字保留——r1 即认可，属报告可读性 |
| P2-4 | doc-manager 迁移史 + frontmatter 重复 | ✅ 已修复（**但引入 NEW-3**） | 「已移除的目录」表改写为行为指令（「不读取、不重建、不同步，提示用户」）——比 r1 建议更优；两处「与旧版差异」删除；frontmatter 规格单源到 templates.md 且顶层留一行要点。新链接 `../docs/migration-v1-to-v2.md` 的安装树可达性问题见 NEW-3 |
| P2-5 | eo-shared/README「被谁引用」表漂移 | ✅ 已修复 | 改「主要消费方」并逐行修正（granularity 补 eo-brainstorming、conventions 改「主链各 skill」）；补 runtime 验证声明 + 整套安装警告（README 同步加了）——两条正是 r1 体系级建议 |
| P2-6 | 看板条目模板两处重复 | ✅ 已修复 | init §13 改为「以 eo-project-update/SKILL.md 第 4 步为单一来源 + 初始值说明」，链接可解析 |
| P2-7 | eo-flow 下一步表与各 skill 重复 | ✅ 已修复（**但引入 NEW-2**） | 表删除、改「以各 skill 速报为单一来源」方向正确，且保留了两条 eo-flow 特有例外（archive 入口、fix 回原 action）。但「读产出文件末尾的速报」前提不成立，见 NEW-2 |
| P2-8 | brainstorming 否定式引导 | ✅ 已修复 | 「绝对禁止」块（含被禁话术原文）删除，替换为正向默认动作（「先复述动机，再给一个带理由的挑战和一个替代角度」）；关键约束六条全部正向化——教科书级的 Negation 修法 |
| P2-9 | EO_HOME 声明与命令脱节 | ✅ 已修复 | 迁移命令改 `"${EO_HOME:-$HOME/.eo}"`；config.md 补「内联命令一律写…」约定 |
| P2-10 | re-sync cursor JSON 缺计数字段 | ✅ 已修复 | 补 `sync_count: 0`（附清零理由）与 `archive_count: <保留原值>`；占位符写法见微量残留 |
| P2-11 | eo-design 约束自相矛盾 + audit 路径形态 | ✅ 已修复 | 改落盘白名单（四个允许位置正向枚举）；audit 报告改 `tmp/eo/design/<date>-audit/report.md` 目录形态，与 conventions 一致 |
| P2-12 | eo-flow「read-act-read 四段」含糊 | ✅ 已修复 | 改为自解释描述（发送前 read 确认就绪、发送后 read 确认上屏） |
| P2-13 | 写给编辑者的维护口吻 | ✅ 已修复 | eo-change:103 删除；doc-manager「（原名保留…）」括注删除；doc-style.md 内保留一处历史注——正是 r1 建议的保留位 |
| P2-14 | eo-implement/eo-change 广触发词误触发面 | ➖ 未修复（可接受） | description 未动。r1 原文即写「实测后再定——No-Op 的判定是跑出来的」；双审合并选择观察，立场一致，不再追 |
| P2-15 | git-sync 汇报示例与默认口径打架 | ✅ 已修复 | 示例改「已提交增量」 |
| P2-16 | change-review 推荐条件两处口径 | ✅ 已修复（弱指针 → NEW-5） | eo-change 场景 A 改为「符合 /eo-change-review 自述的『建议跑』条件」——单源化正确，但指针无路径无链接 |
| P2-17 | GUIDE 成段复写 skill 正文 | ⚠️ 部分修复 | handoff 节收缩到位（骨架表删除、指明「以 SKILL.md 为准，此处不复写」）✅。**差**：eo-flow 节（GUIDE:175-201，派发四步复写）与「为什么修 bug 要喊 /eo-fix」节（三层机制复写）未收缩，仍是漂移温床——鉴于 fix 那节是刻意写给人的动机论证，可降级为低优先，但 eo-flow 节的步骤清单建议同样收缩 |

**机械核验佐证**：全仓相对链接重扫——真实链接 0 断链（报错的 23 条全部是模板代码块内占位链接，与 r1 相同集合）；`AskUserQuestion` 全仓仅剩 questioning.md §4 作为 Claude Code 示例出现一次（协议改造完整）；`spec` 残留仅剩 eo-shared/README 的 v1 教训典故（合法历史引用）；`dev/`、`module:`、`TODO-S1`、`ARCHITECTURE.md` 残留清零。

---

## 二、新问题扫描（修订引入）

### P1

#### [NEW-1] eo-project-init §1.5 步骤 1 与步骤 5 顺序冲突——「后开联动」被自己的默认补写堵死

- **文件:位置**：`eo-project-init/SKILL.md:54`（步骤 1）↔ `:58`（步骤 5）↔ `eo-shared/board-github.md` §四
- **问题**：步骤 1 规定「缺失字段按默认值补写（**如老配置缺 `board` / `github` 段**）」——即写入 `{"enabled": false}` / `"never"`。步骤 5 的联动两问触发条件是「**仅对应段缺失时**」。顺序执行下，走到步骤 5 时段永远不缺失，两问永不触发。更糟的是语义污染：board-github.md §四明确区分「缺失对应段」（该问）与「显式 false/never——那是**用户已选择关闭**」（永不再问）。步骤 1 把「从未被问过」静默改写成「用户选了关」，此后全体系没有任何路径会再问——对 v1 迁移项目（migration 文档步骤 5 明确指示「重跑 /eo-project-init」），board/GitHub 联动的 opt-in 入口从此不可达，除非手改 JSON。§9 的「后开场景……其第 5 步提供这两问」承诺随之落空。
- **依据原则**：Steps 的可执行性与顺序一致性；Completion Criterion（步骤 5 的触发条件被步骤 1 恒否决）；这是第一轮 P0-1 修复引入的回归。
- **建议**：步骤 1 改为「缺失字段按默认值补写，**board / github 段除外**（它们的缺失语义是『尚未询问』，交由步骤 5 处理）」；或把两问挪到步骤 1 内部作为 board/github 段的专属补写方式。

#### [NEW-2] eo-flow「读产出文件末尾的速报」前提不成立——去重后下一步信息实际不可达

- **文件:位置**：`eo-flow/SKILL.md:120` ↔ `eo-review/SKILL.md:70`、`eo-test/SKILL.md:43`、`eo-change-review/SKILL.md:55`、三个产出模板
- **问题**：新写法「读对应产出文件末尾的速报，按其『下一步』原样转达」建立在「速报在文件里」的前提上，但三个 skill 的速报都定义为**对话速报**（「报告写盘后在对话最后输出」），发生在 codex pane 的聊天流里；`review-template.md` / `test-template.md` / change-review 固定模板均无「下一步」或「速报」字段。且 `implement` action 根本没有报告文件（eo-flow 自己的表写着读 `git diff` + change.md）。后果：按字面执行读不到「下一步」；同时旧表承载的两条口径——implement 通过 → test、change-review 通过 → 用户确认置 confirmed 再 implement——在新文本中彻底消失（保留的两条例外只覆盖 review 和 fix）。单源化方向对，但把信息移交给了一个不存在的载体。
- **依据原则**：Context Pointer（"a must-have target behind a weakly worded pointer is a variance bug"——这里更甚，target 本身不存在）；Duplication 修复的前提是单一来源真实可达。
- **建议**（三选一，按侵入度排序）：a) 三个产出模板末尾增加「## 速报」（结论 + 下一步）节，让文件成为速报的单一来源——顺带让「缺速报=流程未完成」变成文件级可校验；b) eo-flow 改为「`tmux-bridge read <codex-pane>` 读对方 pane 尾部的对话速报」；c) 恢复一张最小四行下一步表（放弃这一处去重）。同时无论选哪个，补回 implement 与 change-review 两条下一步口径。

### P2

#### [NEW-3] `../docs/migration-v1-to-v2.md` 链接在安装树不可达

- **文件:位置**：`eo-doc-manager/SKILL.md:53`（「不处理的旧目录」）
- **问题**：这是全仓唯一一个从 skill 指向 `docs/` 的链接。`docs/` 不在 `eo-*` 通配内、不会被 install 脚本链接：按逻辑路径解析（`~/.claude/skills/docs/…`）必断；仅当读取方物理解析软链才可达。作者已意识到并附了口头 fallback 括注——可用，但这是体系里第一个「解析结果取决于 runtime 软链语义」的指针，且括注冗长（52 字解释一个链接）。
- **依据原则**：Context Pointer 可靠性；r1 体系级观察 1 的结论（引用可靠恰恰因为两棵树完整）被此链接打破。
- **建议**：正文直接写口头提示（「这是 v1 遗留目录，处理方式见仓库 docs/migration-v1-to-v2.md（迁移指南）」）不做 markdown 链接，删掉 fallback 括注；或把「冻结 spec、建项目级 changes/」两句要点内联。

#### [NEW-4] 单源化过程中丢失两处有效信息

- **文件:位置**：`eo-brainstorming/SKILL.md`（对照删除前 :204、:165）↔ `eo-shared/questioning.md` §2
- **问题**：(a) 「问题数 ≠ 选项数——同一个决策面下列 5 个候选只算 1 个问题」被随决策池节删除，questioning.md 没有接住这条——它是「每轮 1-2 问」预算在多候选决策面场景下的关键裁决口径，丢了以后严格解读预算会把一次正常的选项呈现误判为超预算；(b) 「混合模式按塑形部分维护池、探索部分自由讨论」只剩模式表 C 行的「聚焦不确定的」，池管理对混合模式的适用性口径弱化。
- **依据原则**：Single Source of Truth 的前提是唯一来源承载全部原有语义（信息应移动而非蒸发）；Completion Criterion 的清晰度。
- **建议**：(a) 补进 questioning.md §2（正位单源，eo-change/eo-design 同样受益）；(b) 在模式表 C 行补半句「（塑形部分照常维护台账）」。

#### [NEW-5] eo-change 场景 A 的弱指针

- **文件:位置**：`eo-change/SKILL.md:78`
- **问题**：「符合 /eo-change-review **自述的**『建议跑』条件时主动提示」——条件本体在 eo-change-review/SKILL.md 首段，但此处无链接无路径，执行 agent 需自行推断去哪找「自述」。
- **依据原则**：Context Pointer 的措辞决定到达可靠性。
- **建议**：改为「符合 [../eo-change-review/SKILL.md](../eo-change-review/SKILL.md) 开头『建议跑』条件时主动提示」。

#### [NEW-6] §1.5「修复」分支不修复 vault 软链

- **文件:位置**：`eo-project-init/SKILL.md:55-57`
- **问题**：步骤 4 核对 `.gitignore` 里的 `<doc_root>/vault` 行，但没有任何一步核对/重建软链本体（§10 的 `ln -s` 逻辑不在 1.5 覆盖内）。vault 模式下软链恰是最容易坏的部件（误删、克隆到新机器、仓库迁移），名为「更新/修复」的分支漏了它。
- **依据原则**：Completion Criterion 的 demand（「幂等的补齐动作」宣称覆盖修复，实际清单不 exhaustive）。
- **建议**：1.5 增加一步「（vault 模式 + create_symlink）核对 `<doc_root>/vault` 软链存在且指向 `project_root`，缺失/指错则按 §10 重建」。

#### [NEW-7] mermaid.md 消费方名单残留失真（P1-2 的未尽项）

- **文件:位置**：`eo-doc-manager/references/mermaid.md:5-9` ↔ `eo-review/SKILL.md`、`eo-change-review/SKILL.md`
- **问题**：名单列 `eo-change-review / eo-review — 一致性审查`，但两个 skill 无任何指向 mermaid.md 的指针，§5「审查清单（给 review 类 skill）」没有到达路径——一份写给消费者的清单，消费者不知道它存在。
- **依据原则**：Context Pointer（材料必须有指针可达才存在于体系中）；名单类元数据的 Duplication 风险（r1 P2-5 同款）。
- **建议**：要么在 eo-review 维度 1（或 eo-change-review 维度 6）加一行条件指针「change 含 §6 流程图时对照 mermaid.md §5 审查清单」，要么把两者从名单删去并把 §5 并入 change-review 的维度自身。

### 微量残留（不阻塞，记录备查）

1. `eo-handoff/SKILL.md:118` 与 `:143`——「<5 条判据」仍双写（r1 建议留一处）；语境泄漏主体已修，仅剩重复。
2. `eo-doc-manager/references/re-sync.md:60`——JSON 代码块内 `"archive_count": <保留原值>` 是非法 JSON 占位；建议移出代码块作旁注（下一行括注其实已解释，代码块内可直接写 `"archive_count": 12  // 保留原值` 风格或删字段留注）。

---

## 三、专项核验结论（任务点名的五项)

1. **新改相对链接可达性**：全量重扫 0 断链（占位链接除外，与 r1 同集合）。新增链接逐一验证：`../eo-project-update/SKILL.md`、`../eo-doc-manager/references/claude-injection.md`、`../eo-design/references/design-md-template.md`、`../../eo-shared/questioning.md`（git-sync）、`../eo-project-init/references/board-setup.md`（board-github）、`../../eo-doc-manager/references/claude-injection.md`（design-md-template）——双树均可达 ✅。唯一例外是 `../docs/migration-v1-to-v2.md`（NEW-3，仓库内可达、安装树半可达、有 fallback）。
2. **eo-brainstorming 重构后主流程自洽性**：✅ 完整。前置→角色→模式分流→方法论（三层追问 / 工具箱指针 / 台账）→五步工作流→关键约束链条无断点；两个下沉文件的指针都带明确触发时机（「进入对应模式的对话循环前」「第四步按模板写入」）；正文残留的「常规分流表」一词可由 record-template.md 的「决策与分流」节解析（第四步已给指针）。唯二损耗是 NEW-4 的两处信息丢失。125 行的新体量与信息层级符合标准。
3. **eo-project-init §1.5 可执行性**：结构上可执行、与 §2-§14 无节号冲突（§4 的 project_root 已存在三选一保留给「配置丢失但 vault 目录尚在」场景，与 1.5 不重叠）；§9 后开场景与 1.5 步骤 5 互指一致。**但步骤 1↔5 存在实质冲突（NEW-1）**，且修复清单漏软链（NEW-6）。
4. **questioning.md §4 runtime 中立协议**：✅ 协议本体措辞好（「下文各 skill 说『按封闭选择协议』即指本条」是干净的 leading-word 锚定）；全部 8 个引用点核验一致（eo-change §3、eo-design 通用规则、eo-project-init §2/§9、board-github §四、conventions 状态流转、git-sync 脏变更三选一、v2-design 背景文档 ×3）；AskUserQuestion 全仓仅剩协议内示例一处。
5. **单一来源化信息丢失**：三处——NEW-2（eo-flow 下一步口径移交给不存在的载体，最重）、NEW-4 两小项。其余单源化（粒度数值、看板模板、frontmatter、change-review 条件、GUIDE handoff）核对无损。

## 总评

这轮修订质量高：26 条里 23 条修干净，多处采用了比原建议更优的正向化写法（行为指令化的旧目录处理、description 的「仅用户明确要求时」边界、落盘白名单）。遗留风险集中且同源——**两条 P1 都是「把重复删掉之后，单一来源没有真正接住语义」**：1.5 的默认补写吞掉了后开询问的触发条件，eo-flow 把下一步口径指向了一个只存在于对话里的「文件速报」。建议下一轮小修只做四件事：NEW-1 的段排除、NEW-2 的速报落位（推荐模板加「速报」尾节方案，一并让三个 skill 的「缺速报=未完成」变成文件可校验）、NEW-4a 补进 questioning.md §2、NEW-6 补软链核对；NEW-3/5/7 与微量残留可并入日常清淤。
