# 横切约定（单一来源）

> 被全部 eo-* skill 引用：tmp 工件命名空间、change 身份（slug/seq 双层）、commit 前缀、状态词汇总表。

## 1. tmp 工件命名空间：tmp/eo/

所有 skill 的临时产物收进统一命名空间（项目仓库内 `tmp/eo/`，按域分子目录）：

```
tmp/eo/
├── handoff/<topic>.md          # 会话交接快照（eo-handoff）
├── fix/<date>-<slug>.md        # 深挖模式调查记录（eo-fix）
├── design/<date>-<topic>/      # 设计变体与预览 HTML（eo-design）
├── explain/<date>-<topic>.html # 一次性解释页（eo-recall）
└── loop/<slug>/journal.md      # 总控进度报告留痕（eo-loop）
```

纪律：

- **一切可丢弃**：任何 skill 不得把 tmp/eo/ 当信源引用。有长期价值的结论在产生时即沉淀到正式位置——根因 → change / lessons；design 选中结论 → DESIGN.md 决策日志；handoff 被下个会话消费后即弃。
- `tmp/eo/` 由 eo-project-init 写入 .gitignore。
- 文件名带日期或 topic 前缀；清理按 mtime，无登记表。`rm -rf tmp/eo` 即全量清理。

## 1.5 vault 写入的链接纪律

skill 写入 vault（board stub、brainstorm 记录、lessons/decisions、backlog 等）的内容中：

- **代码仓库内的路径一律纯文本**（inline code，如 `` `eo-doc/changes/14-batch-export/change.md` ``），**禁止写成 markdown 链接**——vault 之外的路径 Obsidian 无法解析，点了打不开；纯文本供人复制到 IDE
- vault 内部互链用 `[[wikilink]]`

## 2. change 身份：slug 即 id，seq 是显示序号（也作目录前缀）

**身份 = kebab-case 语义 slug**（如 `batch-export`）。身份只钉在**不可变/对外**的位置——这些位置写下就改不动，是撞号变贵的根源，坚决只用 slug、永不带号：

- commit 前缀 `[<slug>]`（文件↔change 的反向索引，首个 commit 后不可改名，改名即断链）
- GitHub issue 标题、stub 卡**文件名** `<slug>.md`

纪律：

- **出生查重**：创建时扫本地 `changes/` 目录与 INDEX.md；有 remote 时 `git ls-tree origin/<默认分支> -- eo-doc/changes/` 兜底（防多 worktree 并行撞名）。撞名 → 换更具体的 slug
- 拒绝 `fix-` 前缀（bug 走 /eo-fix，无 fix 类型）

**目录名 = `<NN>-<slug>/`**（如 `14-batch-export/`），`NN` = `seq` 补零对齐（两位起，`01`/`14`；跨百整体加宽），供 `ls` 顺序排出、一眼找到最近/进行中的 change。目录名是**可改名投影**（`git mv` 可移，不像 commit 前缀锁死），把 seq 放进来是安全的。下游 skill 里的路径占位符 `changes/<change-id>/` 一律指该目录 `<NN>-<slug>/`（运行时解析，不靠 id 拼）。

**`seq`（frontmatter 整数，显示作 `#14`）是显示序号**，真相只存在于 change.md frontmatter 一处；目录前缀、INDEX 的 # 列、stub 卡的 seq 字段都是它的投影。分配 = 项目内现有最大号 +1（含 v1/v2 存量数字前缀）。**seq 允许撞号**——多 worktree 并行分配是常态，撞号只造成同号目录与外观歧义，不破坏任何机制：

- **自愈**（撞号只在多分支合并、两卡同树时才显形）：任何更新 INDEX 的动作（eo-change 第八步、eo-archive——轻模式收口经其轻档门，同属后者）顺手对 seq 查重；发现重号 → `created` 晚者让号（同日无法判晚者 → slug 字典序大者让号，稳定可判），一套机械动作：① 改 frontmatter `seq` → ② `git mv <旧NN>-<slug> <新NN>-<slug>`（目录含未跟踪产物则 `mv` 后 `git add`）→ ③ 改 INDEX 行（# 列 + 链接路径）→ ④ 一句话报告（投影由下次 eo-sync 重算自带新 seq，流转期不写）。**commit 前缀 `[slug]`、issue 标题/号绝不动**——这正是比 v1 便宜的根因：v1 把号钉进 commit，让号即断链；v2 只动可改名投影
- **口头引用**：用户说「14 那个」→ 查 INDEX 解析成 slug；重号未修时列出候选问一句
- **seq 绝不进** commit message、issue 标题、stub 文件名——这些改不了或没人会回去改

> 存量数字前缀 id（v1 的 `014-batch-export`，在模块内 changes/ 原地冻结）照旧有效。v2 期短暂用过的 **slug-only 目录**（无 NN 前缀）不强制迁移：下次任何 skill 触碰该 change 时，按其 frontmatter `seq` 顺手 `git mv` 补上前缀即可（身份是 slug，前缀补不补都不影响引用）。

## 2.5 commit 前缀

| 场景 | 前缀 | 示例 |
|------|------|------|
| change 相关提交（implement 批次、archive 结算/meta） | `[<change-id>]` | `[batch-export] 导出模块 Batch 1` |
| 直改模式：bug 小修 | `fix:` | `fix: 修正导出文件名日期格式` |
| 直改模式：UI/样式/文案 | `ui:` | `ui: 调整卡片间距` |

change-id 前缀是 eo-archive 归集 commit 区间的依据；`fix:`/`ui:` 前缀供 retro 统计直改流量。推荐「一次 change 一次 commit」；TODO 分批时允许一批一 commit，archive 至多补两个收尾 commit：结算 meta commit + 可选 sync 身份回写 commit（后者仅当收口 `eo-sync run` 产生身份字段回写时）。**轻档例外**：预期恰为 2-3 个 commit——test-lock commit + 实施 commit（+ 收尾 meta commit），**不得 squash**（锁定边界是独立复核的比对基准）。

## 2.6 代码注释纪律

**溯源不进注释**：文件↔change 的对应由 commit 前缀 `[<change-id>]` 承载（git blame 即得）。**严禁任何流程溯源标注**进代码注释——change 编号/slug、TODO/AC 编号、review finding（P0-x/P1-x）、FAIL-x、批次/阶段号、revision 号，只要**作为溯源标记**出现即违规；归档后这些标记对读代码的人毫无意义，只会腐烂。判据看语义不看字面：领域术语恰与 change slug 同名的正常约束注释不违规（如 slug 为 `cache-invalidation` 时描述缓存失效契约的注释照写）。

注释只写**代码本身表达不了的约束**（不变量、反直觉的坑、外部契约），一两行为限；不复述代码在做什么，**不向审查者解释这次改动为何正确**——正确性辩护属于 commit message 与对话汇报。密度对齐所在文件的既有风格。

## 3. 状态词汇总表（看板列序即此）

看板列序按主路径排列；状态机 = **主路径 + 显式回退边**（不是单向全序，下游不得按列序数值判合法流转）：

```
backlog → draft → confirmed → implementing → reviewed → archived
```

change 的 `status` 由 skill 在对话确认后自动写入，**用户永远不手改 frontmatter**：

```
draft ──(eo-change：用户对话确认)──▶ confirmed
      ──(eo-implement：首次执行)──▶ implementing
      ──(eo-review 通过)──▶ reviewed（代码审查已过；人工验收与归档尚未发生）
      ──(eo-archive：完成归档)──▶ archived（不可逆）

回退边（与主路径同等合法）：
reviewed ──(阻塞反馈：eo-test 结论不通过 / eo-review 复审出 P0/P1 / acceptance 打回 / 进入回炉前的置回)──▶ implementing
          由**产出该结果的 skill 当场执行**，不等 implement 猜；acceptance 打回常由用户
          直接标注、无产出 skill——由首个读到打回的 skill（implement / archive）补置
implementing ──(eo-change 回炉子流程：方案需实质修订)──▶ draft
          重新确认后回 confirmed；`plan_revision` +1
```

**修复后的节点路由不等于重放固定流水线**：Test / Review 是证据节点，不是 `status`。首轮可按风险选择先 Test 或先 Review；一旦进入反馈循环，按反馈来源与证据新鲜度分流：

- **Review 反馈**：`eo-review → eo-implement → 原 reviewer 增量复审`。仍有 P0/P1 就继续修，不在代码审查尚未收敛时反复启动 Test；复审通过后，若存在较旧的通过 Test 基线 `T`，原 reviewer 再审计 `T` 到当前交付基线 `H` 的完整差异，并在最新 review 轮写 `测试证据处置：沿用 / 复验`。`H` = 本 change 最后一个 `[<change-id>]` 业务代码或测试资产提交
  - `沿用`：`T` 是 `H` 的祖先，`T..H` 可完整审计，既有 Test 无阻塞项，且修复未改变受测外部行为、AC / 验证口径、测试断言 / fixture / mock / 配置 / 环境组合 / 关键依赖，也未弄脏 auto-heavy AC；跳过 eo-test
  - `复验`：任一沿用条件不成立，或处置缺失、含糊、基线关系无法证明；派回原 tester。影响不含 auto-heavy 且能映射到有限 AC、用例及依赖闭包时定向复验；任一 auto-heavy AC 被弄脏，或影响跨共享路径 / 契约 / 状态机 / schema / 并发 / 权限安全 / 外部集成 / 环境矩阵 / 测试基础设施，或范围无法圈定时完整复验
  - `不适用`：没有历史 Test，或 Test 已在当前 `(plan_revision, H)` 通过。前者按既有 heavy AC 门决定是否首跑 Test（无待验 heavy AC 则不强迫补 Test），后者直接复用当前证据键上的 Test
- **Test 反馈**：存在未核销 Test FAIL 时固定走 `eo-test → eo-implement → 原 tester 复验`，不得被 Review 的证据沿用分支绕过；Test 失败曾把 status 置回 `implementing` 时，复验通过后无论 `H` 是否变化都回原 reviewer（`reviewed` 的恢复权归 Review）；若产生过新的业务代码或测试资产提交，Reviewer 同时增量审查这些提交，恢复状态与 Review 基线新鲜度
- **Test 资产与基线**：测试文件、fixture、mock、harness、测试配置都属于测试资产。eo-test 本轮改动测试资产时，须先以 `[<change-id>]` 提交，再在更新后的 `H` 上执行最终验证；`test.md` / `review.md` / change 元数据等纯流程工件提交不推进 `H`。Test 报告以 `B` 记录本轮最终执行基线（执行时 `B = H`）。Test / Review 的完整新鲜度键是 `(plan_revision, commit)`：任何业务代码或测试资产提交都会推进 `H`，而回炉提升 `plan_revision` 即使 `H` 不变也会使旧证据过期
- **权限边界**：Implement 只提供修复 commit、finding / FAIL 映射、同层验证和受影响 AC 候选；它的“预计无测试影响”只是 reviewer 的输入，不能自行批准跳过独立 Test。Loop 只校验并消费 review/test 的结构化处置，不亲自看 diff 作语义判定

无需为该路由新增 frontmatter 状态：Review 通过仍可置 `reviewed`；其后 Test 若失败再按既有回退边置回 `implementing`，Test 通过则保持 `reviewed`。

**修复循环与回炉字段**（全档 change.md frontmatter；轻档不使用——轻档熔断 = 两次以上跑偏即扩档，扩档确认后从零起算）：

| 字段 | 类型/缺省 | 写入者 | 语义 |
|------|----------|--------|------|
| `plan_revision` | 整数，缺省视为 1 | eo-change 回炉子流程（用户重新确认时 +1） | 方案版本。fix 计数、change-review 轮数、wont-fix 豁免、报告台账全部以当前 revision 为界 |
| `fix_rounds` | 整数，缺省视为 0 | eo-implement 模式二第 0 步 | 当前 revision 内的修复轮次；≥3 触发熔断三选一；回炉确认时归零 |
| `fix_consumed` | 列表，缺省 `[]` | eo-implement 模式二第 0 步 | 已消费的失败反馈标识（`review#N` / `test#N` / `acceptance#<AC编号>@<验收基线sha>`）——幂等计数依据，触发集为空 = 续修不计数；回炉确认时清空 |

**change 分轻/全两档**（frontmatter `tier: light | full`，**缺省视为 full**，存量 change 零迁移）。轻档共用上表状态机但**跳过 reviewed**：draft →（探针对齐）confirmed →（测试锁定 + 实施）implementing →（完成门通过，收口立即内嵌调用 eo-archive）archived——**归档两档同源于 eo-archive**，按档分流准入：全档验 review 基线新鲜度，轻档走轻档门（验完成门留痕：独立复核基线新鲜 + 锁定测试绿 + manual 确认记录）。轻模式收口负责在完成门通过后立即触发；其他上下文（主控 / 用户）持完成门留痕直接调 /eo-archive 亦可，门槛不因入口减免。判档规则见 [granularity.md](granularity.md) §5。

用户的确认动作发生在对话里（回复确认，或按 [questioning.md](questioning.md) §4 封闭选择协议选择），skill 负责落盘。

**终态处置**（两类卡片不对称，且都不影响对方）：

| 状态 | 卡片类型 | 写入者 | 处置 |
|------|---------|--------|------|
| `adopted` / `dropped` | backlog 卡 | eo-backlog archive | 三件套：status + tag 换 `eo-backlog-archived` + 移 `backlog/archive/`（退出看板；卡是源数据，归档留痕在文件） |
| `archived` | change 卡 | eo-sync（archive 收口触发） | 由 eo-sync 投影 `status: archived`——**tags 与文件位置绝不动**：`eo-change` tag 是 Bases 过滤锚点，动了卡片从所有视图（含盘点）消失。活跃视图隐藏 archived 由呈现层的视图级过滤解决 |

backlog 卡的激活态恒为 `backlog`（它不是 change，不进 change 流转）。存量项目的 `status: done` 是 `reviewed` 的旧名——skill 读到即视同 reviewed 并顺手改写。
