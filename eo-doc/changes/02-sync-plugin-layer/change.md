---
id: sync-plugin-layer
seq: 2
title: eo-sync 插件层与存量适配器迁移
summary: 投影插件化为 eo-sync 单命令同步；stub/issue/PR 迁内置适配器，逐流转触发点全面退役
status: implementing
tier: full
type: feature
base_commit: 5f38497da71eb7ca17b0fa10e0fe4453251399b8
plan_revision: 1
fix_rounds: 0
fix_consumed: []
commits: []
issue: ~
pr: ~
created: 2026-07-24
---

# eo-sync 插件层与存量适配器迁移

## 速览

- **改什么**：投影同步收敛为 `eo-sync` 单命令：插件化 CLI 核（capabilities/plan/apply 协议 + PATH 发现）+ 内置 Obsidian stub 与 GitHub issue/PR 适配器；流程 skill 与横切规范里的**全部**逐流转投影触发点退役
- **为什么**：触发点×目标矩阵散落在多个 skill 正文与 eo-shared 横切规范里，新增投影目标（如 Notion）要处处改；不用 Obsidian 的用户在每次状态流转为呈现层付费
- **行为差异**：之前每次状态流转各 skill 顺手 upsert stub / 建 issue → 之后流转零投影动作，archive 收口自动同步一次 + 任意时刻手动 `eo-sync run`；第三方在 PATH 放一个 `eo-sync-<name>` 可执行并在配置启用即可接入新目标
- **怎么验**：AC 8 条（人工 0 条）；跑 `eo-sync run --dry-run` 看计划、跑 `eo-sync run` 对拍存量 board/ 卡即可走查

## 1. 意图

现状三类投影（Obsidian stub / GitHub issue / GitHub PR）的触发逻辑散落在**流程 skill 正文**（eo-change / eo-implement / eo-review / eo-fix / eo-test / eo-archive / eo-project-init）与**横切规范**（eo-shared/conventions.md 的 seq 自愈第④步、回退边「刷新 stub」、终态处置表 stub 行）多处：扩展成本线性放大，且「每次流转顺手写」让写路径为呈现层付费。本 change 落地 [decisions/2026-07-24-sync-plugin-layer.md] 的裁定：CLI 为核的插件化 `eo-sync`，存量投影迁为内置适配器（投影内容行为等价），触发点收敛为 archive 自动一次 + 手动。C1（change #1）已交付 `cli/eo_lib` 五域共享库，本 change 复用它而不重写解析。

已钉决策（继承自 decisions/2026-07-24-sync-plugin-layer.md 与 brainstorm 关键决策表 #3-#9 #14，全部已裁定，不重开）：

- **契约** → `capabilities()`（声明支持实体、操作、各目标生命周期起点）+ `plan()`（create/update/delete/skip，可 dry-run）+ `apply()`；进程协议 stdin/stdout-JSON + exit code + 协议版本号（Taskwarrior 范式）
- **发现** → `eo-sync-*` PATH 前缀负责「有哪些」，配置 `sync` 段负责「启用哪些 + 参数」；存量 `board`/`github` 段的正式收编是「将来」——本 change 只做等价兼容映射（见 §5.3），收编时机入 §8
- **方向** → 严格单向（本地 → 投影），唯一逆向是漂移告警（只报不回写）
- **幂等** → 平台身份（issue 号 / PR URL / Notion page_id 等）回写 change frontmatter——协议以 capabilities 声明的**身份字段**通用承载（见 §5.2），核不硬编码任何具体平台；纯簿记走旁车文件不进 SoT（路径与格式本 change 裁决，见 §5.4）
- **触发点** → archive 收口自动一次 + 手动 `eo-sync run`；v1 不加 git hook / 定时档。逐流转触发点**直接退役、不留兼容层**——退役范围是**全部现存触发点**，以全仓扫描 + 白名单收敛（AC-6），不以 skill 计数为边界（破坏性变更由决策 #9 预钉，非本次新开）
- **首批适配器** → Obsidian stub 与 GitHub issue/PR 迁为内置适配器，投影内容与 board-github.md 现行写法等价、生命周期起点差异保留（stub 从 draft、issue 从 confirmed、PR 在 archived）；**Notion 只定契约不实现**（决策 #14）
- 内置适配器与第三方**同协议、同发现路径**，无后门（假设，从「语言无关、第三方可扩」推导：内置走特权通道会让协议失去 dogfooding）
- starter 看板 `.base` 创建**留在 eo-project-init**：一次性 setup 动作，非同步动作，不迁入适配器（假设，用户未逐条确认；保留断言入 TODO-5 完成判据）
- **v1 CLI 与锁明示 POSIX-only**：install.bat 不接线 CLI、只加不支持提示（WSL 可用）——仓库既有 CLI（eo-board）本就只有 install.sh 链接惯例，不承诺未实现路径（review#1 P0-4 处置裁决）
- 两个 defer 项（簿记旁车路径与格式、多 worktree 回写串行点）在本方案 §5.4 / §5.5 裁决，不再悬置

## 2. 验收清单

- [ ] AC-1 用户跑 `eo-sync run` 后，看板 stub 与 GitHub issue/PR 投影与 board-github.md 现行写法逐字段等价（stub 整文件重写、issue 靠回写号去重，含同轮回写的平台身份字段）；紧接着再跑一次，全部目标 skip、无任何副作用（验证：本项目 board/ 下存量卡对拍零语义 diff；GitHub 侧用测试配置验）
- [x] AC-2 生命周期起点差异保留：同一次 run 内，draft change 只产出 stub 不建 issue，confirmed 起才建 issue，PR 仅对 archived change 按 `github.pr` 策略创建（验证：三态样本端到端 dry-run，draft→仅 obsidian/stub、github/issue skip；confirmed→github/issue create；archived→pr 按 auto/默认分支判定）
- [ ] AC-3 `eo-sync run --dry-run` 逐行输出「change × 目标 → create/update/delete/skip + 原因」的计划，全程零写入（投影介质、change frontmatter、簿记文件都不动），并明示其为提示性计划（落地以持锁重算为准）
- [ ] AC-4 第三方接入：PATH 上放可执行 `eo-sync-<name>` 并在配置启用后，`eo-sync adapters` 能列出其 capabilities 且 run 将其纳入；适配器输出非法 JSON / 协议主版本不匹配 / 非零退出时，仅该适配器报错跳过，其余目标照常完成，run 总退出码非零标示存在失败（0 = 全部成功）
- [ ] AC-5 配置零成本与兼容：合并配置既无 `sync` 段也无 `board`/`github` 段 → run 提示无启用目标并以退出码 0 结束；仅有存量 `board`/`github` 段的项目无需改配置，行为按等价映射生效
- [x] AC-6 流程瘦身：状态流转期间零投影动作——执行 `grep -rniE "upsert|刷新 stub|联动 stub|看板 stub|建 issue|创建 GitHub issue|issue body|PR 创建" --include="*.md" eo-* --exclude-dir=eo-doc | grep -vE "^eo-shared/(board-github|README)\.md:|^eo-archive/SKILL\.md:|^eo-project-init/references/config\.md:"` 输出为空（实跑 = 0 行；白名单四文件残留仅 config.md:179 board/ 目录结构注解，属配置字段语义描述；eo-archive 第五层已改调 `eo-sync run`）（`--exclude-dir=eo-doc` 隔离历史工件；白名单四文件的命中仅允许是投影写法/配置字段语义/收口触发的**描述**，不得是流转期执行指令——该定性约束由 TODO-5 完成判据人工复核。零输出可达性已在起草基线自证：白名单外命中共 23 行，逐行映射到 TODO-5 的删除/改口径/措辞调整动作，无一游离——TODO-5 裁定保留的 4 处描述行以措辞调整出正则而非扩白名单，见其清单）；eo-archive 收口自动执行一次 `eo-sync run`；流转期间看板不实时刷新是预期行为而非缺陷
- [ ] AC-7 并发安全：两个 worktree 同时 `eo-sync run`，后到者看到含持有者信息的锁占用提示并干净退出（退出码区别于失败）；先后串行的两次 run，第二次全部 skip、不重复创建任何远端对象（陈旧计划无落地窗口）
- [ ] AC-8 同步不污染 SoT：手动 run 之后仓库内 `git status` 仅可能出现幂等键回写（change frontmatter 的身份字段），随工作区常规提交走；archive 收口 run 产生的回写由紧随的 `[<change-id>] sync 身份回写` commit 提交（无回写则不产生该 commit），归档完成后工作区干净；本次 run 创建/更新了 PR 时该 commit 随即推送到同一分支（PR 合并后的 SoT 含幂等键；推送失败降级为告警提示，不阻塞归档）；簿记文件位于 `$EO_HOME/sync-state/`，仓库内零新增文件

## 3. TODO

### Batch 1（MVP：核 + 协议 + 自带夹具，可独立验证）

- [x] TODO-1 eo-sync 核 CLI：子命令 `run [--dry-run] [--change <id>] [--target <name>]` 与 `adapters`；`eo-sync-*` PATH 发现 + `sync` 段启用制（含 `board`/`github` 段兼容映射）；非 dry-run 全程持锁编排（scan→plan→apply→回写→簿记原子落盘，见 §5.5）；两阶段适配器排序与快照刷新（§5.1）；身份字段校验与保序回写、同状态 worktree 消歧（文件：新增: cli/eo-sync, tests/fixtures/eo-sync-fixture（最小协议夹具适配器）, tests/test_eo_sync_smoke.py；修改: cli/eo_lib/（frontmatter 保序回写辅助 + 扫描同状态消歧规则，解析复用不重写）；对应 AC-3/4/5/7/8；完成判据：凭本批自带夹具跑通 run / dry-run / 锁互斥 / 兼容映射 smoke，绿灯不依赖后续批）
- [x] TODO-2 适配器协议契约文档：三动词的 stdin/stdout JSON schema、exit code 与 run 总退出码约定、协议版本与演进规则（未知字段忽略、破坏性升主版本）、capabilities 生命周期起点与 `identity_fields` 身份字段所有权声明、回写校验与保序插入规则（允许字段/冲突/空值/未知字段与保留键拒绝/新字段追加锚点）、第三方接入指南（含 Notion 契约级要点：database row 粒度、令牌桶限速、checkpoint+hash 增量、`page_id` 作身份字段示例——只定契约不实现）（文件：新增: docs/sync-adapter-protocol.md；对应 AC-4；完成判据：schema 与 TODO-1 实现字段一致，夹具适配器仅凭本文档可独立写出）

### Batch 2a（与 2b 并行：文件集不相交，均只依赖 Batch 1 协议）

- [x] TODO-3 内置 Obsidian 适配器：stub 投影行为等价 board-github.md §一——整文件覆盖写、frontmatter 字段集与省略规则、archived 只改 status 不动 tags/文件位置、放弃草稿删 stub 不留孤儿、正文纯文本路径；生命周期起点 draft；平台身份字段照抄 change frontmatter（自身不产生回写，`identity_fields` 为空）（文件：新增: cli/eo-sync-obsidian；对应 AC-1/2；完成判据：对本项目存量 board/ 卡重投影零语义 diff）

### Batch 2b

- [x] TODO-4 内置 GitHub 适配器：issue 自 confirmed 建（回写号去重、绝不靠标题）、body 按档生成与幂等刷新、archive 兜底关闭；PR 按 auto/always/never 策略仅对 archived 创建；漂移检测告警（只报不回写）；issue 号 / PR URL 经通用身份字段契约（`identity_fields: ["issue","pr"]`）返回交核回写，无特权通道；`gh` 不可用/无 remote → 提示跳过不阻塞（文件：新增: cli/eo-sync-github；对应 AC-1/2；完成判据：dry-run 下对 draft/confirmed/archived 三态样本产出的计划与 board-github.md §二/§三逐条一致）

### Batch 3（瘦身与收尾）

- [x] TODO-5 逐流转触发点全面退役 + 文档降级：eo-change / eo-implement / eo-review / eo-fix / eo-test 删除逐流转 stub/issue 联动钩子行（含 eo-test 回退边的「联动刷新 stub」）；eo-shared/conventions.md 六处（四处改口径：seq 自愈第④步删 upsert stub——投影由下次 sync 重算自带新 seq、回退边「刷新 stub」删除、终态处置表 stub 行改「由 eo-sync 投影」、§2.5 收尾 commit 口径改「至多两个：结算 meta commit + 可选 sync 身份回写 commit」；两处保留描述行措辞调整出 AC-6 正则：§2 的「看板 stub 文件名」与「看板 stub 的 seq 字段」改「stub 卡」类表述，语义不变）；eo-shared/acceptance.md 回修行删「联动 stub」；eo-change/references/change-template.md 五处（三处旧联动口径改 eo-sync 口径：`issue:` 字段注释、轻档「看板 stub、GitHub 联动与全档同一套」行、轻档 `issue:` 注释的联动钩子去重表述；两处保留描述行措辞调整出正则：`summary` 注释「看板 stub 卡面」改「看板卡面」、`pr:` 注释「PR 创建后回写」改「归档同步回写」）；eo-archive 第五层改为「调用 `eo-sync run` 一次，回写按 §5.6 以第二个收尾 commit 提交并在 PR 场景追加推送同分支，失败告警不阻塞归档」并补冻结语义注记（归档后唯一允许的后续写入 = eo-sync 身份字段回写）；eo-project-init 联动问答改写 `sync` 段、开启后历史同步改为调 `eo-sync run`，**保留 starter `.base` 创建段落**；board-github.md 重写定位声明为「内置适配器实现说明」并删除触发点矩阵；config.md 增补 `sync` 段 schema（文件：修改: eo-change/SKILL.md, eo-implement/SKILL.md, eo-review/SKILL.md, eo-fix/SKILL.md, eo-test/SKILL.md, eo-archive/SKILL.md, eo-project-init/SKILL.md, eo-shared/conventions.md, eo-shared/acceptance.md, eo-shared/board-github.md, eo-change/references/change-template.md, eo-project-init/references/config.md；对应 AC-5/6；完成判据：AC-6 扫描命令零输出（改写后的新表述不得落其正则）+ 白名单四文件命中逐行人工复核为描述性 + eo-project-init 的 `.base` 创建段落保留断言通过）
- [ ] TODO-6 安装接线（POSIX-only）：install.sh 把 cli/eo-sync 与两个内置适配器链接进 `EO_BIN_DIR`（复用 eo-board 既有链接逻辑——该逻辑仅存在于 install.sh）；install.bat 增加一行明确提示「eo-* CLI 暂不支持 Windows 原生安装，可用 WSL」（文件：修改: install.sh, install.bat；对应 AC-1/4；完成判据：POSIX 新装路径下 `command -v eo-sync eo-sync-obsidian eo-sync-github` 全部命中；install.bat 有不支持提示且不产生假接线）
- [ ] TODO-7 测试矩阵（扩 Batch 1 夹具为完整覆盖）：协议往返、发现与启用制、兼容映射、dry-run 零写入、双进程锁竞态（后到者退出码 + 串行两次 run 第二次全 skip）、身份回写校验（冲突拒绝、未知字段拒绝、非空不覆盖、保留键拒绝）、保序插入（已存字段替换保注释、新字段追加在 `---` 前、非法键名拒绝）、同状态分叉 fail-closed、部分失败总退出码、簿记幂等与陈锁清理（`EO_HOME` 指向临时目录隔离）（文件：新增: tests/test_eo_sync.py（复用 Batch 1 夹具）；对应 AC-3/4/5/7/8；完成判据：pytest 全绿且不触碰真实 `~/.eo`）

## 4. 涉及文件

本 change 必改的连带口径（TODO 行未覆盖处）：

- `README.md` / `docs/GUIDE.md` — 提及看板/GitHub 联动与 CLI 命令处的口径同步（触发点收敛 + 新命令 eo-sync）
- `eo-shared/README.md` — board-github.md 索引行的定位描述随降级同步
- `eo-project-init/references/board-setup.md` — 如含逐流转触发口径则同步（`.base` 模板本体不动）

**不在本 change 改**：`docs/v2-design.md`、`docs/tier-design.md`、`docs/how-it-works.html` —— 历史设计文档/生成物，口径清理归 C5（dashboard 遗留清理）及后续 doc sync，避免本 change 范围膨胀。

## 5. 技术方案

### 5.1 架构、所有权与编排顺序

核（`cli/eo-sync`，零第三方依赖，复用 `eo_lib`）负责：发现、配置解析与兼容映射、持锁编排、簿记持久化、SoT 回写。适配器只做「算投影 + 写平台侧」：`plan` 是纯函数（不产生任何写入），`apply` 只写自己的目标介质（vault stub 文件 / GitHub API）——**适配器永不写代码仓库文件**；幂等键回写与簿记更新由核依 apply 返回统一执行。库层沿用 eo_lib 错误所有权：抛 `ConfigError`，退出责任在 CLI 入口。

**两阶段编排**（同轮身份可见性，声明驱动无内置特权）：`identity_fields` 非空的适配器先 plan/apply；核执行其回写后**刷新 change 快照**，再跑纯投影适配器——同轮内后者读到新平台身份，保证紧接的第二次 run 全 skip（AC-1/AC-7）。同阶段内按适配器名字典序，顺序确定。

### 5.2 协议 v1

调用形态 `eo-sync-<name> capabilities|plan|apply`，stdin JSON 请求 / stdout JSON 响应，exit 0 成功、非 0 失败（stderr 供人读）。

- **版本与演进**：请求响应均带整数 `protocol_version: 1`（主版本）；**次版本演进通道 = 双方必须忽略未知字段**，破坏性改动才递增主版本；主版本不匹配 → 跳过该适配器并告警（AC-4）
- `capabilities` → `{protocol_version, name, entities: ["change"], projections: [{id, lifecycle_start: "draft"|"confirmed"|"archived", ops: [...]}], identity_fields: [<拥有回写权的 frontmatter 字段名>]}`（无回写则空列表）
- `plan` ← 项目上下文（project_name/project_root/doc_root/repo_root）+ 全量 change 快照（frontmatter + AC/TODO 计数 + 相对路径 + 分支，来自 `scan_all_changes`）+ 该适配器簿记命名空间 + 启用参数；→ `{actions: [{op: create|update|delete|skip, projection, change_id, reason, payload}], drift: [<告警文本>]}`
- `apply` ← plan 的 actions；→ 逐 action 结果 + `writeback: {<change_id>: {<字段名>: <标量>}}` + 新簿记命名空间
- **回写校验（核执行）**：字段必须 ∈ 该适配器声明的 `identity_fields`，未声明/未知字段 → 拒绝该条回写并告警；键名校验 `^[a-z][a-z0-9_]*$` 且不得为 change 生命周期保留键（id/seq/title/summary/status/tier/type/base_commit/plan_revision/fix_rounds/fix_consumed/commits/created 等）——声明保留键的适配器在 run 启动即被拒绝；两个启用适配器声明同名字段 → 同样 fail closed；目标字段已有**不同**非空值 → 不覆盖、告警（平台身份只写空位，幂等键一经写入不变）；null 值忽略（严格单向下身份不删除）
- **保序回写（eo_lib 执行，不依赖预改模板）**：目标字段已存在（含值为 `~`）→ 原地替换冒号后的值、保留该行行内注释；字段不存在（第三方身份字段如 `page_id` 默认不在模板中）→ 以 `<key>: <值>` 单行标量**追加在 frontmatter 关闭 `---` 之前**（锚点与模板内容无关，任何 change 文件通用）；其余行的顺序、格式、注释一律原样保留
- **run 总退出码**：0 = 全部成功；1 = 存在适配器/动作失败（其余目标已完成，部分成功详情见输出）；2 = 锁占用退出；配置错误沿用 ConfigError 非零路径

### 5.3 发现、启用与兼容映射

PATH 前缀 `eo-sync-*` 回答「有哪些」；**执行只限合并配置 `sync` 段显式启用者**（发现 ≠ 执行，这也是第三方可执行文件的信任边界）。`sync` 段 schema（落 config.md）：`"sync": {"<name>": {"enabled": true, ...适配器参数}}`。兼容映射：合并配置**无** `sync` 段时由存量段派生等价启用集——`board.enabled/stub_dir` → obsidian 适配器参数，`github.issue/pr` → github 适配器参数；`sync` 段存在则完全以其为准，不做深合并。正式收编（init 停写旧段、存量迁移）→ OQ-1。

### 5.4 裁决①：簿记旁车路径与格式

**路径**：`"${EO_HOME:-$HOME/.eo}"/sync-state/<project_name>-<hash8>.json`（实现取 `os.environ.get("EO_HOME")`，缺省 `Path.home()/".eo"`——沿用 config.md 既有可展开写法），`hash8` = git common dir 绝对路径 SHA-256 前 8 位——全部 worktree 共享同一 common dir，天然得到「一仓库一份簿记」，且 project_name 撞名不冲突。**格式**：`{"version": 1, "adapters": {"<name>": {"<change-id>": {"content_hash", "synced_status", "synced_at"}}}}`，适配器可在自己的命名空间存扩展键（如 Notion checkpoint）。**弃决策候选 `eo-doc/changes/.sync-state.json` 的理由**：仓库内路径需维护 .gitignore 且有误提交进 SoT 的风险；多 worktree 下每份 untracked 各自漂移，簿记的增量语义直接失效。`~/.eo/` 是既有用户级数据根约定（config.md），天然仓库外、单份共享、`EO_HOME` 可重定向供测试隔离。

### 5.5 裁决②：多 worktree 回写串行点

**锁范围覆盖权威计划**：非 dry-run 的 run 在扫描之前取锁，持锁完成 scan → plan → apply → frontmatter 回写 → 簿记原子落盘（临时文件 + rename）后释放——权威计划只在锁内生成，不存在「锁外旧计划串行落地」的窗口；后到进程抢锁失败 → 打印持有者信息（pid + 时间戳）后以退出码 2 退出（不排队，调用方稍后重跑）。`--dry-run` 只读不取锁，输出明示为提示性计划。陈锁（时间戳超 10 分钟且 pid 不存活）自动清理后重试一次。

**锁实现**：POSIX `fcntl.flock` 独占簿记同名 `.lock` 文件；**v1 明示 POSIX-only**（机械事实：install.bat 从未接线任何 CLI，仓库 CLI 惯例是 extensionless Python + shebang；Windows 原生支持需求出现时，launcher 安装与 msvcrt 锁分支一并独立立项，不在本 change 假装承诺）。

**弃「主 worktree 独占」的理由**：archive 自动触发发生在实施所在的任意 worktree，独占主 worktree 会让 feature worktree 上的归档无法自动同步，破坏决策 #9 的触发点设计。

**回写落点消歧**（同 id 多 worktree 候选）：先按状态取最高（`scan_all_changes` 既有行为）；**同状态多份**时优先「发起 run 的 worktree」内那份；发起处无该 change 且各候选内容 hash 一致 → 任取；内容分叉 → **fail closed**：跳过该 change 的回写并列出候选路径告警，绝不把枚举顺序当回写目标（消歧规则落 eo_lib 扫描层，TODO-1）。

### 5.6 触发点接线与 archive 结算闭环

**时序（与现行五层顺序完全兼容，不调层序）**：eo-archive 保持既有第三层结算 meta commit → 第四层 doc sync → 第五层收口调 `eo-sync run`；第五层 run 产生幂等键回写（典型：PR URL、迟到的 issue 号）时，eo-archive **立即追加第二个收尾 commit** `[<change-id>] sync 身份回写`（无回写则零额外 commit）——归档完成时工作区无未提交 SoT，AC-8 闭合。**远端传播**：本次 run 创建/更新了 PR（github 适配器已在 run 内 push 并建 PR）→ 回写 commit 后**追加 `git push` 同一分支一次**（PR 跟踪分支，追加推送自动进入 PR，合并后的 SoT 含幂等键）；push 失败 → 告警不阻塞归档（幂等键已在本地 SoT，随任意后续 push 传播）；第四层 doc cursor 落后于该回写 commit 是接受的——身份字段不含文档语义，下次 doc sync 顺带越过。配套改 conventions §2.5 口径为「archive 至多两个收尾 commit：结算 meta commit + 可选 sync 身份回写 commit」（TODO-5）。**弃另两候选的理由**：层序前移（sync 提到结算 commit 前）不可行——PR 创建依赖结算 commit 已存在并推送，且第五层的 issue 兜底关闭语义要求 status 已是 archived；「回写并入下一次结算」则让归档带着脏工作区返回，直接违反 AC-8。**冻结语义注记**（落 eo-archive）：归档后 change 目录冻结的唯一例外 = eo-sync 身份字段回写（决策 #8 钉的是「平台身份回写 change frontmatter」，而 PR URL 只可能在 archived 后产生，例外是决策自身的推论）；此后手动 run 若补写身份字段，作为工作区常规变更随下次提交走。sync 失败降级为告警不阻塞归档（投影可随时手动重跑补上）。手动 run 产生的回写**不自动提交**。eo-project-init 开启联动时的历史同步同样收敛为一次 `eo-sync run`（幂等可重跑）。

## 7. 风险与回滚

- **对外接口**：协议 v1 主版本内嵌于请求响应；次版本演进 = 忽略未知字段（前向兼容），破坏性改动升主版本——不匹配的适配器被跳过而非错误解释，第三方不会静默坏掉
- **平台边界**：v1 CLI 与锁 POSIX-only，install.bat 只做明确「不支持」提示（WSL 可用）——不承诺未实现路径
- **回滚**：流程 skill 与横切规范瘦身是纯文本改动，git revert 即恢复逐流转投影；投影本身可全量重建（stub 整文件重写、issue 幂等去重），无不可逆数据操作
- **已接受代价**（决策 #9 预钉）：状态流转期间看板不再实时；draft stub 的出现时点从「写盘即建」延后到「首次 sync」。观察手动 run 频率后再议自动档

## 8. 开放问题

- OQ-1 `board`/`github` 段正式收编进 `sync` 段（init 停写旧段 + 存量项目迁移提示）的时机（defer 原因：决策原文标注「将来收编」，兼容映射已护住存量，收编无紧迫性，宜独立小 change）
- OQ-2 sync 自动档（git hook / 定时 / `--watch`）是否引入（defer 原因：决策 #9 明确 v1 不做，观察 archive 自动 + 手动的实际频率后再议）
- OQ-3 第三方适配器信任边界是否需要显式启用制之上的加固（哈希白名单等）（defer 原因：v1 以「发现 ≠ 执行、配置显式启用」为界，无真实第三方生态前加固无对象）
