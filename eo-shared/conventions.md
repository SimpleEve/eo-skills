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

## 2. change 身份：slug 即 id，seq 是显示序号（也作目录前缀）

**身份 = kebab-case 语义 slug**（如 `batch-export`）。身份只钉在**不可变/对外**的位置——这些位置写下就改不动，是撞号变贵的根源，坚决只用 slug、永不带号：

- commit 前缀 `[<slug>]`（文件↔change 的反向索引，首个 commit 后不可改名，改名即断链）
- GitHub issue 标题、stub 卡**文件名** `<slug>.md`

纪律：

- **出生查重**：创建时扫本地 `changes/` 目录与 INDEX.md；有 remote 时 `git ls-tree origin/<默认分支> -- eo-doc/changes/` 兜底（防多 worktree 并行撞名）。撞名 → 换更具体的 slug
- 拒绝 `fix-` 前缀（bug 走 /eo-fix，无 fix 类型）

**目录名 = `<NN>-<slug>/`**（如 `14-batch-export/`），`NN` = `seq` 补零对齐（两位起，`01`/`14`；跨百整体加宽），供 `ls` 顺序排出、一眼找到最近/进行中的 change。目录名是**可改名投影**（`git mv` 可移，不像 commit 前缀锁死），把 seq 放进来是安全的。下游 skill 里的路径占位符 `changes/<change-id>/` 一律指该目录 `<NN>-<slug>/`（运行时解析，不靠 id 拼）。

**`seq`（frontmatter 整数，显示作 `#14`）是显示序号**，真相只存在于 change.md frontmatter 一处；目录前缀、INDEX 的 # 列、stub 卡的 seq 字段都是它的投影。分配 = 项目内现有最大号 +1（含存量数字前缀目录）。**seq 允许撞号**——多 worktree 并行分配是常态，撞号只造成同号目录与外观歧义，不破坏任何机制：

- **自愈**（撞号只在多分支合并、两卡同树时才显形）：任何更新 INDEX 的动作（eo-change 第九步、eo-archive）顺手对 seq 查重；发现重号 → `created` 晚者让号（同日无法判晚者 → slug 字典序大者让号，稳定可判），一套机械动作：① 改 frontmatter `seq` → ② `git mv <旧NN>-<slug> <新NN>-<slug>`（目录含未跟踪产物则 `mv` 后 `git add`）→ ③ 改 INDEX 行（# 列 + 链接路径）→ ④ 一句话报告（投影由下次 eo-sync 重算自带新 seq，流转期不写）。**commit 前缀 `[slug]`、issue 标题/号绝不动**——它们一旦钉入不可改之处，让号即断链；seq 只动可改名投影
- **口头引用**：用户说「14 那个」→ 查 INDEX 解析成 slug；重号未修时列出候选问一句
- **seq 绝不进** commit message、issue 标题、stub 文件名——这些改不了或没人会回去改

> 存量数字前缀 id（如 `014-batch-export`，在模块内 changes/ 原地冻结）照旧有效。**slug-only 目录**（无 NN 前缀的存量形态）不强制迁移：下次任何 skill 触碰该 change 时，按其 frontmatter `seq` 顺手 `git mv` 补上前缀即可（身份是 slug，前缀补不补都不影响引用）。

## 2.5 commit 前缀

| 场景 | 前缀 | 示例 |
|------|------|------|
| change 相关提交（eo-test 锁定/测试资产、implement 批次、archive 结算/meta） | `[<change-id>]` | `[batch-export] 导出模块 Batch 1` |
| 直改模式：bug 小修 | `fix:` | `fix: 修正导出文件名日期格式` |
| 直改模式：UI/样式/文案 | `ui:` | `ui: 调整卡片间距` |

change-id 前缀是 eo-archive 归集 commit 区间的依据；`fix:`/`ui:` 前缀供 retro 统计直改流量。推荐「一次 change 一次 commit」；TODO 分批时允许一批一 commit，archive 至多补两个收尾 commit：结算 meta commit + 可选 sync 身份回写 commit（后者仅当收口 `eo-sync run` 产生身份字段回写时）。

**前缀选择不因活跃 change 改向**：trivial 直改（[granularity.md](granularity.md) §2）即使落在某活跃 change 的范围内，仍走 `fix:`/`ui:`——一行 CSS 不该触发该 change 的复审。

## 3. 状态词汇总表（看板列序即此）

看板列序按主路径排列；状态机 = **主路径 + 显式回退边**（不是单向全序，下游不得按列序数值判合法流转）：

```
backlog → draft → confirmed → implementing → [reviewed] → archived
```

**`reviewed` 是可选状态**：只有实际跑了 /eo-review 且通过时才由它写入；不跑 review 的 change 从 `implementing` 直接归档。状态枚举本身不变（eo-board / eo-sync 消费这些字符串）。

change 的 `status` 由 skill 在对话确认后自动写入，**用户永远不手改 frontmatter**：

```
draft ──(eo-change：用户对话确认)──▶ confirmed
confirmed ──(eo-implement：首次执行)──▶ implementing
implementing ──(可选：eo-review 通过)──▶ reviewed
implementing / reviewed ──(eo-archive：四问门通过)──▶ archived（不可逆）

回退边（与主路径同等合法）：
reviewed ──(阻塞反馈：eo-review 复审出 P0/P1 / acceptance 打回)──▶ implementing
          由产出该结果的 skill 当场执行；acceptance 打回常由用户直接标注、无产出 skill
          ——由首个读到打回的 skill（/eo-fix / implement / archive）补置
implementing ──(eo-change 回炉：方案需实质修订)──▶ draft，重新确认后回 confirmed
```

**反馈循环路由**（仅在挂了对应闸门时存在）：报告有未决阻塞项 → 原 impl worker 走 /eo-fix 循环内分支修复 → 回**原**复审方核销（增量，不重开全文）。同一 change 修复轮次 ≥3，或各轮失败触发位置互不相同（打地鼠信号）→ 停下问用户（豁免一轮 / 卡点检查 / 回炉），不代答、不无限循环。熔断判据凭报告与对话机械可判，**不使用 `plan_revision` / `fix_rounds` / `fix_consumed` 等 frontmatter 计数器**——修订历史由 git 兜。

**文本同步不是回炉**：change 活跃期内，意图不变的文本维护（措辞对齐实际实现、就地补 AC、typo）是编辑行为，不走回炉。边界细则以 eo-change「回炉与就地精化的边界」为单一来源。

用户的确认动作发生在对话里（回复确认，或按 [questioning.md](questioning.md) §4 封闭选择协议选择），skill 负责落盘。

**终态处置**（两类卡片不对称，且都不影响对方）：

| 状态 | 卡片类型 | 写入者 | 处置 |
|------|---------|--------|------|
| `adopted` / `dropped` | backlog 卡 | eo-backlog archive | 三件套：status + tag 换 `eo-backlog-archived` + 移 `backlog/archive/`（退出看板；卡是源数据，归档留痕在文件） |
| `archived` | change 卡 | eo-sync（archive 收口触发） | 由 eo-sync 投影 `status: archived`——**tags 与文件位置绝不动**：`eo-change` tag 是 Bases 过滤锚点，动了卡片从所有视图（含盘点）消失。活跃视图隐藏 archived 由呈现层的视图级过滤解决 |

backlog 卡的激活态恒为 `backlog`（它不是 change，不进 change 流转）。存量项目的 `status: done` 一律视同 `reviewed`，skill 读到即顺手改写。
