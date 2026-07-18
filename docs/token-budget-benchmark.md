# Token 开销实测与对标

> 状态：结论稿
> 日期：2026-07-15
> 输入：TangentCloud 22 个会话 transcript（`~/.claude/projects/-Users-debugeve-projects-TangentCloud/*.jsonl`，148MB）、gstack v1.47 全量 skill、Anthropic 官方 agent-skills（17 个）
> 起因：怀疑 change 文档写得过细导致 token 爆炸，验证「AC 与已钉决策是否该留在 change.md」

---

## 0. 结论

**change 文档不是 token 大头，且离硬指标很远。AC 与已钉决策应当留在 change.md。**

实测 change 文档占单项目上下文 **2.7%**；change.md 中位数 **98 行 / 13k 字符**，硬上限 700 行 **0/13 触及**。三家对标下来，本体系是唯一同时具备「可校验硬指标 + 条件节 + 真 progressive disclosure」的。

唯一确认的设计缺陷：§5 技术方案的条件节闸门失效（13/13 全触发），已修（见 §5）。

---

## 1. 测量口径（先读这节，否则会得出错误结论）

**文本与图片的 token 口径完全不同，混用会导致结论反向。**

| 内容 | 口径 | 说明 |
|------|------|------|
| 中文文本 | ≈ 1.7 字符 / token | 按 4 字符/token 估会低估约 2.3 倍 |
| 英文 / 代码 | ≈ 3.6 字符 / token | |
| 图片 | ≈ 宽 × 高 / 750 | **与文件体积、base64 长度无关**；长边 >1568px 先缩放 |

**实测校验**：1440×900 截图理论值 `1440×900/750 = 1728`，实测 `cache_creation = 1836` tokens（7 次采样，1722–2750），吻合。

**踩过的坑**：transcript 里图片以 base64 存储，一张 1440×900 截图占 ~190k 字符。若按「字符数 ÷ 4」估算，会得出「单张截图 47k tokens」的错误结论，进而误判截图是最大开销项。**实际单张仅 ~1800 tokens，误差 26 倍。** 任何涉及图片的 token 分析都必须按像素计，或直接读 `usage.cache_creation_input_tokens`。

---

## 2. 实测：token 花在哪（TangentCloud，22 会话 ≈ 3.05M tokens）

```
Read 代码/其他文件        20.4%  ████████████
Bash 结果                19.5%  ███████████
Edit 调用参数              9.1%  █████
Write 调用参数             7.2%  ████
Bash 调用参数              6.4%  ███
注入 skill_listing        6.4%  ███
Read eo-doc state/handbook 4.8%  ██
Read eo-doc/changes 文档   2.7%  █        ← change 工件
📷 截图                    0.4%           ← 7 次 × ~1800 tok
```

**放大器**：`cache_read / cache_creation = 63.7×`（26.05 亿 / 4090 万）。上下文里每个 token 平均被重放 64 次，**任何常驻内容成本 ×64**。但放大器对所有内容一视同仁，不改变相对结构。

**会话规模**：峰值中位数 206k tokens，最大 934k，20 个会话中 14 个超过 150k。

### 分项细节

- **Bash 结果 19.5%** 无单次巨量输出（>40k 字符 0 次），由 grep（34%）、git（16%）、go test（12%）千刀万剐累积。
- **change.md 实测**：中位数 98 行 / 13k 字符（≈6.5–9k tokens），最大 165 行。累计 Read 17 次 ≈ 81k tokens。
- **change 目录文档构成**（13 个 change 合计 456k 字符）：change.md 34.6% / review*.md 21.1% / test.md 20.5% / change-review.md 11.6% / **acceptance.md 1.5%**。
  - 注意：`review*.md` + `test.md` 合计 41.6%，**超过 change.md**。095 单个 change 有 3 份 review（review / review-opus / review-fable）共 43k 字符，是其 change.md（20k）的两倍多。若要找篇幅优化目标，review 侧性价比高于 change 侧。
- **截图**：磁盘 7.4M / 50 张，但**不 Read 就是零成本**。全仓仅 7 次图片读取 ≈ 12.6k tokens。7.4M 是 git 仓库体积问题，与 token 无关。

### change.md 章节分布（13 个合计）

| 章节 | 占比 | 出现 |
|------|------|------|
| §3 TODO | 28.4% | 13/13 |
| §1 意图（含已钉决策） | 19.7% | 13/13 |
| **§5 技术方案** | **17.0%** | **13/13** ← 条件节却全触发 |
| §2 验收清单 | 16.2% | 13/13 |
| §4 涉及文件 | 8.3% | 13/13 |
| §7 风险与回滚 | 3.6% | 9/13 |
| §8 开放问题 | 2.5% | 9/13 |
| §6 流程图 | 0.4% | 2/13 |

**AC（16.2%）+ 已钉决策（含于 19.7%）合计约占 change.md 的三分之一，即全局上下文的 ~0.9%。** 删除它们省下的量不足 1%，代价是 implement 的完成判据、review 的检查表、archive 硬门的解析源全部失去锚点，需靠重新提问补回——净亏。

---

## 3. 对标：三家横评

### SKILL.md 体量

| | 数量 | 中位 | 最大 |
|---|---|---|---|
| **eo-skills** | 17 | ~108 | 255（eo-project-init） |
| **Anthropic 官方** | 17 | 232 | 590（docx） |
| **gstack** | 54 | ~1200 | **2359**（spec，126,970 bytes） |

gstack 的 `spec` 单文件 ≈ Anthropic 全部 17 个 skill 之和的 60%。gstack corpus 总量 **3.09MB / 52 skills**。

> 统计陷阱：gstack 的 `.factory/ .cursor/ .opencode/ .kiro/ .slate/ .agents/ .gbrain/ .hermes/ .openclaw/` 下是 9 份 host 适配副本，统计时须排除，否则重复计数 9 倍。

### 规格类模板

| | 模板行数 | 必填 section |
|---|---|---|
| **eo change.md** | 83 | **4**（§1-§4），§5-§8 条件节 |
| **gstack spec → Issue** | ~57 | **10，全部无条件** |

gstack Standard 模板：Context / Current State / Proposed Change + Implementation Details / Acceptance Criteria / Testing Plan / Rollback Plan / Effort Estimate / Files Reference / Out of Scope / Related。Epic 变体 +4，`--audit` 变体 +3。**唯一数量约束是 Context 的 "2-3 sentences"。**

### 长度约束机制

| | 机制 | 强度 |
|---|---|---|
| **eo-skills** | `granularity.md` 硬指标表：TODO 3-7/上限 10，change.md 200-500 行/上限 700；收尾 `wc -l` 自检；**超硬标拒绝确认** | 绝对值 + 强制动作 |
| **Anthropic** | `SKILL.md <500 行`、`reference >300 行加 TOC`、`metadata ~100 words`；但附 "feel free to go longer if needed" | 软规范 |
| **gstack** | 文档里有硬预算表（单 skill 30KB / corpus 700KB，"CI fails if any budget exceeded"） | **形同虚设，见 §4** |

**eo 的 `granularity.md` 是三家中唯一给出行为学理由的**：「超过 700 行 agent 会丢细节、跳步骤；200-500 行恰好装下全部上下文」（引自 spec-kitty）。

### Progressive disclosure

| | 形态 | 规模 |
|---|---|---|
| **eo-skills** | `SKILL.md` + `references/` 按需 | 24 个 reference，22–158 行，中位 ~78 |
| **Anthropic** | 同上 | 1 个（`skill-creator/references/schemas.md` 430 行） |
| **gstack** | `sections/` + STOP 锚点，9 个 skill 已 carve | `references/` 全仓仅 1 个；**`spec` 未 carve** |

**eo 是三家中唯一真正符合 Anthropic canon（<500 行）的。**

### AC 与 decisions 的安放

| | AC | decisions | 同文档 |
|---|---|---|---|
| **gstack** | Issue `## Acceptance Criteria` | **不进正文**，落 `~/.gstack/` CLI 日志 | ❌ |
| **eo-change** | `§2 验收清单` | `§1 意图` 已钉决策（单行三元组） | ✅ |
| **eo-project-record** | — | `decisions/<date>-<slug>.md`（40 行） | 独立 |

gstack 的思路是「决策外置成结构化日志，正文零成本」：

```bash
gstack-decision-log '{"decision":"...","rationale":"...","scope":"branch","confidence":8}' 2>/dev/null || true
```
> records the accepted scope as a **durable cross-session decision so the next session sees what was settled (and why) without re-litigating it**... best-effort (`|| true` — never blocks).

**eo 实际两头都占**：正文放单行结论 + 重决策外迁 `/eo-project-record`。三招控篇幅：

1. **决策压成单行三元组** `<决策面> → <结论>（理由：…）`，不展开候选方案
2. **台账不渲染**：内部维护「已钉 / 未钉 / defer」三态作为 agent 工作记忆，只有已钉结论行和 ≤3 条 defer 落盘
3. **重决策外迁** `/eo-project-record` → 40 行模板，正文只留结论行；回流靠 `lessons.md` 的「命中 ≤3 条 + 只读 `## 规则` 节」

---

## 4. gstack 的四条反面教训

gstack 的 `docs/designs/v2_PLAN.md` 有一段罕见坦诚的自我批评，值得整段读：

> gstack has an externally documented reputation for being "fat."... "**potentially consuming 10K+ tokens before any real code is written**"... **Anthropic's own canonical Skills guidance prescribes the "progressive disclosure" pattern — gstack diverges from this.**
> - 31 skills, **2.1MB total corpus**
> - **28 of 31 skills exceed the 40KB soft ceiling (~10K tokens each)**
> - ship.md is 164KB (~41K tokens); ship.md.tmpl is only 48KB — **115KB is resolver-injected**

它随后定了硬预算表（单 skill 30KB / corpus 700KB，CI 强制）。**实测全线失守：corpus 涨到 3.09MB（+47%），7 个 skill 仍 100KB+，30KB 目标零达成。**

### ① 绝对预算会退化成比值棘轮

CI 实际执行的不是 30KB，而是「不超 baseline 的 1.5 倍」，且 baseline 本身就是超标状态（`test/skill-size-budget.test.ts:41-49`）：

```ts
// Default per-skill ratio is 1.50 (50% growth tolerance). Adjusted v1.52.0.0
// from 1.05 → 1.50: a 5% ratio tripped on legitimate feature additions...
const DEFAULT_RATIO = 1.50;
```

门槛被「合理的功能增长」从 1.05 一路放宽到 1.50。**对 eo 的启示：`granularity.md` 用绝对值 + 超硬标拒绝确认是对的，不要改成相对比值。**

### ② 比值守卫对大块重复注入天然免疫（实锤 bug）

`spec/SKILL.md` 第 31-795 行与第 1101-1865 行**逐字节相同**（`diff` 验证：IDENTICAL 765-line block）。

根因：`spec/SKILL.md.tmpl:289` 在行文中引用章节名——

```
Read `GSTACK_PLAN_MODE` from the environment (emitted by `{{PREAMBLE}}`'s preamble bash)
```

而 `scripts/gen-skill-docs.ts:678` 是全局正则替换，无「引用 vs 展开」之分：

```ts
input.replace(/\{\{(\w+(?::[^}]+)?)\}\}/g, (_match, fullKey) => {
```

于是 46KB 前言被塞进句子中间。`spec` 是全仓唯一出现两次 `{{PREAMBLE}}` 的模板。

**代价：每次 `/spec` 白烧 46,335 bytes ≈ 12K tokens（前言 ×2 占文件的 73%）。CI 放行原因：126,970 / 100.2KB baseline = ×1.267 < 1.50。**

**启示**：模板宏若既可「被引用」又可「被展开」，必须有转义语法。

### ③ 要控 token 先控公共前言，而非先 carve 正文

gstack 每个 skill 都注入 46KB 公共前言（Preamble / AskUserQuestion Format / Voice / Telemetry 等），46KB × 52 = 2.4MB。carve 只能压业务正文，压不动前言——所以「12-15KB 骨架」的设计目标落地成 55–97KB，**差 5-6 倍**。`maxSkeletonBytes` 守卫值全是「现状 +1~2KB」的贴脸阈值（ship 81,085 vs 上限 90,000），**这不是预算，是防倒退棘轮**。

**eo 的 `eo-shared/` 是按需引用而非无条件注入，天然避开了这个坑——此设计不可改。**

### ④ 长度约束必须与质量约束同层级写

gstack `spec/SKILL.md:664` 有一条显式反长度控制的原则：

> ## Completeness Principle — Boil the Ocean
> **AI makes completeness cheap, so the complete thing is the goal. Recommend full coverage** ... never as an excuse for a shortcut.

叠加 14 条 Quality Standards + 打质量分的 gate（判据是 "missing acceptance criteria, fuzzy success metrics"），**`/spec` 五阶段在结构上单调递增，没有任何环节会让文档变短**。

对比 eo 的反模式表是「禁止占位符」（压缩方向），gstack 的反模式表是「Vague acceptance criteria / Missing 'Out of Scope'」（膨胀方向）。

---

## 5. 已修：§5 技术方案的条件节闸门失效

**现象**：§5 是条件节，模板写明「都不满足 → 整节省略」，实测 **13/13 全触发**，占 change.md 篇幅 17%。

**双重根因**：

1. **触发判据含恒真项**。原文「新架构模式 / 新外部依赖 / 安全・性能・数据迁移复杂度 / **编码前有歧义**」——最后一条几乎永远为真，等于给条件节开了永久后门。
2. **审查侧不阻塞**。`eo-change-review` 维度 6 将「触发条件不满足却写了」判为 **P2**，而收敛协议是 P0-only 阻塞，故即使抓到也不拦。

**已改**（`eo-change/references/change-template.md:58`，同步 `docs/v2-design.md:218`）：删除恒真项，并显式声明判据须可证伪：

```markdown
<!-- 触发（任一成立才写，都不满足 → 整节省略）：新架构模式 / 新外部依赖 / 安全・性能・数据迁移复杂度。
     判据须可证伪——「编码前有歧义」这类恒真描述不构成触发；有歧义应在第三步澄清掉，而非落进本节。 -->
```

**未改（留作观察）**：维度 6 的 P2 定级。条件节取舍属程度判断，升 P0 会与「P0 只收客观可判项」的既定原则冲突；先看触发词收紧后的自然收敛率，若仍高再议。

---

## 6. 可对标机制清单

| # | 机制 | 出处 | 推荐度 |
|---|---|---|---|
| 1 | **条件节 + 触发判据 + 「整节省略连标题都不留」** | `eo-change/references/change-template.md:5,54-71` | ★★★ 三家独此一份 |
| 2 | **硬指标表（理想/硬上限/超限动作）+ `wc -l` 自检 + 超硬标拒绝确认** | `eo-shared/granularity.md:7-14` | ★★★ 唯一带行为学理由 |
| 3 | **STOP 祈使句锚点 + 顶部路由表 + PASSIVE manifest** | `gstack ship/SKILL.md:890-897,1018` | ★★★ gstack 最好的部分 |
| 4 | **决策外置成结构化日志，正文零成本** | `gstack plan-ceo-review/sections/review-sections.md:610-613` | ★★★ |
| 5 | **`requiredReads` E2E 断言 + canary transcript 巡检**（机械层防丢失） | `gstack v2_PLAN.md:213-215` | ★★☆ 设计好，落地未验证 |
| 6 | **文档内 section 级 PD**：结论前置，检索只读 `## 规则` 节 | `eo-shared/lessons.md:9` | ★★☆ |
| 7 | **决策台账三态不渲染，仅结论行落盘，defer ≤3** | `docs/v2-design.md:143` | ★★☆ |
| 8 | **明确「不该 carve 的」清单**（防过度工程） | `gstack v2_PLAN.md:222` | ★★☆ |
| 9 | **比值型预算 + override 审计 + 反向地板** | `gstack test/skill-size-budget.test.ts:48,82-91,162` | ★☆☆ **反面教材** |

### gstack 的 STOP 三件套（值得直接抄）

1. **顶部路由表** situation → section 映射（`ship/SKILL.md:890-897`）
2. **祈使句 STOP 锚点**（全文 8 处）：
   > **STOP.** Before running the test suites..., Read `~/.claude/skills/gstack/ship/sections/tests.md` and execute it

   `v2_PLAN.md:210` 明令：**"Imperative skeleton phrasing — 'STOP. Read ...' Not 'see ... for details.'"**
3. **PASSIVE manifest**（`ship/sections/manifest.json`）：
   > "**PASSIVE registry**... The skeleton's decision-tree prose is the **ONLY** place that decides WHEN to read a section... **No machine predicate here**"

6 层防丢失并诚实标注强弱（`v2_PLAN.md:207-215`）：`4. End-of-skill self-check (**weakest layer**)` / `5. Eval harness requiredReads — **mechanical enforcement at the test layer, not just prompt layer**` / `6. canary transcript 巡检，alert on Read-miss`。

---

## 7. 待办与未决

- **`skill_listing` 占 6.4%**（每次注入 ~7.6k tokens）。本仓 16 个 eo-* skill 的 description 合计仅 2,744 字符（~0.7k tokens），大头来自其他已注册 skill（story-* 39 处 / gstack 60 处）。**按项目裁剪注册的 skill 集合，收益高于精简任何文档。** 属运行时配置问题，不在本仓范围。
- **review 侧篇幅**：`review*.md` + `test.md` 合计占 change 目录文档 41.6%，超过 change.md。多模型复审（review-opus / review-fable）是否常态化、是否需要合并模板，待定。
- **条件节维度 6 的定级**：见 §5「未改」。
- **本次未验证**：eo-skills 在其他项目（eo-board / Rabbit / novel）的分布是否与 TangentCloud 一致。TangentCloud 是重后端 + 多 worktree 的重型项目，可能偏离典型。
