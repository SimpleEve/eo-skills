# 三档制设计稿：直改 / 轻档 change / 全档 change（草案，待定夺）

> status: **adopted · 已实施（2026-07-18）**。三个开放项按推荐落地：eo-implement 轻模式 / 完成门一次性 subagent 复核 / backlog 先判档（经 eo-change 第一步判档自然生效）。实施直接落 SKILL.md（本仓库即 skills 本体，不走 eo-* 流程）。落点：granularity.md §5（判档表）、conventions.md §3（轻档流转）、change-template.md（轻档模板）、eo-change（轻档流程）、eo-implement（轻模式）、ac-spec / eo-change-review / eo-review / eo-test（兼容行）。
> 依据：本轮竞品与实践调研（[research/INDEX.md](../research/INDEX.md)）。skill 落地时**不携带**任何出处说明（精简 token）；有据可循的职责由本稿与 research/ 承担。

## 1. 问题与结论

**问题**：中小型需求缺中间档——trivial 直改之上就是全套 change（AC + TODO 四要素 + 确认 + 可选 change-review），起草成本让轻量变更不成比例地贵。

**结论**：不抛 change，也**不造新名词**——change 分**轻 / 全两档**（`tier: light | full`），工件都是 change.md，轻档只有意图 + AC 两节。轻量化的正确路径是四句话：

> 命名史（2026-07-18 与用户对齐）："issue 档" 与外部 GitHub issue、change 联动所建 issue 三重撞名；"card 档" 与 backlog 卡、看板 stub 卡撞名且只描述形式——两案均废弃。最终取"不引入新概念"：判档问题从「这算 issue 还是 change」变成「这个 change 开轻还是开全」，用户心智模型只有 change 一个名词。

1. **减前置描述**——前置描述只能解释约 15% 的 agent 失配，是三档里最可压缩的部分
2. **保验收锚点**——AC 是唯一不随模型变强而失效的工件职能（独立验证的基准，治"假报完成"）
3. **验证下沉为测试**——正向可判定的 AC 落成失败测试并 commit 锁定；负向约束与观感留书面
4. **意图显式去处**——常驻层（state）承接不了单次意图；不落 change 的意图要么进 decisions/，要么明示接受蒸发

## 2. 三档总览

| | **直改档**（已有，微调） | **轻档 change**（新增） | **全档 change**（已有，微调） |
|---|---|---|---|
| 触发 | trivial 四判据 + 描述成本下界 | 影响面可圈住的小型明确需求 | 跨边界 / 跨 session / 多方对齐 |
| 工件 | 零 | 极简 change.md：意图 1-2 句 + AC ≤5 条（`tier: light`） | 完整 change.md（`tier: full`，缺省即 full） |
| TODO | 无 | **不预写**——agent 自拆，不落盘 | 三要素 + Batch |
| 验收 | 常规 commit | 测试锁定 + 独立复核 + manual 过目 | 全流程（implement/test/review） |
| 方案审查 | 无 | 无——**探针对齐**替代（落盘即请用户否一次） | change-review（可选，条件触发） |
| 归档 | cursor sync 兜底 | done 即归档；无 test.md/review.md | eo-archive 全流程 |

## 3. 判档决策表

**判档权在 agent，不在用户**：用户始终自然描述需求，不需要预判档位。agent 按本表判档并一句话宣告（含该档的取舍，如「按轻档走：不出 review 报告，验收靠测试 + 复核」），用户一个词即可改档。判错代价已设计为低——判低了有升档路径兜底，判高了只多一份工件——**边界不需要精确，只需要错得便宜**，这正是模糊地带无害的原因。

**输入源与档位正交**：用户口述 / backlog 卡 / 外部 GitHub issue / brainstorming 捕获都是输入源，统一过本判档门。外部 GitHub issue 可落任何档：报 bug → eo-fix；小而明确 → 轻档（号回写 frontmatter `issue:`，联动钩子靠回写号去重、不重复建）；大需求 → 全档（现有 board-github 联动不变）。输入自带 AC 时（规范的 GH issue 正是如此），落盘近乎零成本。

**入口统一在 eo-change 第一步**（bug 仍走 eo-fix，方向未定仍升 brainstorming，均不变）：

1. **描述成本下界**：说清怎么改所需的字数 ≈ 直接改掉的成本 → **直改档**（trivial 四判据之外的新增下界）
2. 以下四问**任一为"是" → 全档**，全"否" → **轻档**：
   - **影响面圈不住**？（跨模块边界 / 动共享不变量 / 改对外接口或持久化结构）
   - **需要多方对齐**？（第二个人或并行 agent 需要在同一份理解上工作）
   - **预计跨 session**？（单次会话收不了口，需要中断恢复锚点）
   - **误解代价高**？（agent 理解偏了会造成难逆损失，或返工远贵于澄清）

**两条形式原则**（判据的判据）：

- **判不准默认低档**，升档靠**事后信号**而非事前估计：实施中发现影响面圈不住、agent 两次以上跑偏、AC 超过 5 条装不下——这些是升档探针。事前估计本身是最容易错的一步。
- **判界写相对量**（"影响面能否圈住""可审查性"），不写死绝对数字——绝对阈值会随模型能力上移而过时。

## 4. 轻档规格

### 4.1 工件（就是极简的 change.md）

存放、目录名、seq、INDEX、看板 stub、GitHub 联动**全部与全档同一套**——轻档不是新工件，是 change.md 的最小形态：

```markdown
---
id: export-name-fix        # slug 即身份，规则同 conventions.md §2
seq: 15                    # 与全档共用序号空间，目录 <NN>-<slug>/
tier: light                # light | full；缺省视为 full（存量 change 零迁移）
status: draft              # 状态机与全档共用：draft → confirmed → implementing → archived（轻档跳过 reviewed）
issue: ~                   # 联动创建或外部来源的 GitHub issue 号（复用全档字段，钩子靠它去重）
created: 2026-07-18
---

# <标题>

意图：<为什么做 + 做什么，1-2 句>

## 验收清单
- [ ] AC-1 <正向可判定>（锁定：tests/export.test.ts#case-x）
- [ ] AC-2 <当……失败时，用户看到……>
- [ ] AC-3 <观感类>（人工:<做什么 → 过目什么>）
```

- **无 TODO 节、无涉及文件节、无条件节**。AC 上限 5 条——装不下即扩档信号
- AC 撰写规则复用 ac-spec.md（增量制验证栏、条数不模板化、manual 标记），**skill 内不重复**

### 4.2 生命周期（状态机与全档共用）

```
澄清（1-2 问）→ 落盘(draft) → 探针对齐(confirmed) → 测试锁定 + 实施(implementing) → 完成门 → done(archived)
                                                              ↘ 扩档信号 → tier 改 full，原地续走全流程
```

1. **落盘 + 探针对齐**：写完立即请用户否一次。探针的成功标准是**尽快暴露分歧**，不是通过评审；用户点头即 `confirmed` 进入实施，无修订循环
2. **测试锁定**：实施前把 auto 类 AC 逐条落成失败测试，确认**因断言失败**（而非报错），commit 锁定。AC 行回填测试锚点
3. **派发实施**：eo-implement 轻模式（或经 eo-flow 甩给外部 agent）。agent 自拆 TODO，工作记录留在对话与 commit，不回写工件
4. **实施纪律**：**禁改测试文件**。确需改（AC 本身写错）→ 停手上报，用户确认后改 AC、重锁测试再继续
5. **完成门**：测试绿 + lint/typecheck + **新鲜上下文独立复核**（见 §4.3）+ manual 项用户过目
6. **收口**：commit 带 `[<change-id>]` 前缀；status 置 `archived`；值得留的决策按 eo-project-record 门槛落 decisions/（琐碎选择不建卡）；不产 test.md / review.md

### 4.3 轻档的测试与审查（不是省略，是吸收与压缩）

**测试——eo-test 的职能前移吸收**：测试锁定这一步就是"以 AC 为锚编写测试"（eo-test 的核心职能），只是从实施后挪到了实施前，实施的目标就是让它变绿——所以轻档没有事后测试轮，也不产 test.md。边界：AC 的验证若需要**起环境 / 多环境组合 / 点击流**（auto-heavy），说明验证成本已经不轻——这本身就是扩档信号，把重验证交还给全档的 eo-test 一次跑完。

**审查——两级都有对应物**：
- **方案级**（change-review 的对应物）→ **探针对齐**。轻档没有 TODO 映射、粒度、条件节这些审查对象，六维度里只剩"AC 质量 + 意图一致"两个面，一次人工否定比一轮结构化审查性价比高
- **代码级**（eo-review 的对应物）→ **独立复核**。新鲜上下文 subagent 逐条核对 AC 覆盖 + 防作弊三查（过拟合测试 / 硬编码特判 / 篡改验证），对话速报结论，不产报告。压缩的依据：轻档 diff 在可审查阈值内，全六维审查开销不成比例
- **随时可升级、无需扩档**：AC 就在 change.md 标准位置，eo-review / eo-test 天然可消费——用户一句「跑 /eo-review」即得完整审查报告。轻档砍的是**默认动作**，不是**能力**

### 4.4 扩档路径（原地升档）

实施中触发扩档信号 → frontmatter `tier` 改 `full`，就地补齐 TODO 等模板节（意图与 AC 原样保留，已锁定的测试继续有效），status 不变，从当前状态续走全流程。**文件不挪、目录不改、commit 前缀不变、看板 stub 无感**。

### 4.5 归档与文档同步

- **done 即归档**：收口后 change.md 不再编辑，工件本身就是审计记录，无冻结仪式；INDEX 行与看板 stub 随收口更新（与全档共用钩子）
- **文档同步不依赖 archive**：v2 本有双轨——eo-archive 主动触发 sync 是快车道，doc-manager **cursor sync 兜底**负责收割未走 archive 的常规 commit（trivial 直改已走此轨）。轻档 commit 带 `[<change-id>]` 前缀，cursor sync 照常收割，state/handbook 同步不受影响
- **防蒸发卫生规则**（借 issue 直派模式「44% 关闭 PR 系超期无人处理静默蒸发」教训）：eo-change 第八步维护 INDEX 时，顺手报告非 archived 且 30 天未动的轻档条目

## 5. change 档与直改档的微调

1. **granularity.md 判档轴调整**：「跨模块边界 / 触碰共享不变量」优先于文件数与行数（数量指标降为提示信号）
2. **trivial 判据补描述成本下界**（§3 第 1 条）
3. change-review 现协议**不动**：P0-only 阻塞 + 增量核销 + 3 轮上限——spec 迭代无内生停点，外生截断是正解（本轮调研再次加固，见 research/）
4. **显式推翻一条旧决策**：granularity.md §2 直改护栏中「不引入 light change 中间工件」系 v2 为防 trivial 膨胀而设；本设计引入中间档即推翻该条，实施时须同步改写并注明 supersede——防止 change-review 按旧口径拦新设计

## 6. 待定夺项

> 原待定夺项 1（存放）与 5（命名）已被「不造新名词、同一 change.md 分 tier」的统一方案吸收消解（见 §1 命名史与 §4.1）。

| # | 问题 | 推荐 | 备选 |
|---|------|------|------|
| 1 | 实施入口 | eo-implement 增"轻模式"（复用修复循环与 commit 纪律） | eo-change 一条龙做完（少一次 handoff，但 skill 变重） |
| 2 | 独立复核形态 | 完成门内 spawn 一次性 subagent（轻，不产报告） | 复用 eo-review 加轻模式（重，但口径统一） |
| 3 | backlog 衔接 | backlog 卡默认先判档（原 backlog→change 改为 backlog→判档） | 维持 backlog→change 不变 |

## 7. 增强项（不入本次范围，候选进 backlog）

- **Interrogatory review**：让 agent 拿着 change/卡反问用户来替代通读（对症"审占人工成本大头"）
- review 报告口径区分「未发现问题」与「已验证无问题」
- ac-spec 补 auto/manual 动态迁移语义（manual = 尚未固化态）与「LLM 可判定」中间档
