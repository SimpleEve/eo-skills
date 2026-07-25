---
title: 项目注册表 + eo-board 多项目聚合 + eo-sync watch Change 审查报告
change_id: registry-board-watch
created: 2026-07-25
status: active
summary: >
  首轮全量审查不通过：AC-1 要求 init 成功即已注册，但 TODO-3 明确允许注册失败后仍报告 init 成功。
---

# 项目注册表 + eo-board 多项目聚合 + eo-sync watch Change 审查报告

> 关联：[change.md](change.md) ｜ 审查日期：2026-07-25 ｜ change status：draft
> 前提抽查基线：`85ad4fccba8c983e4c104b8c78b00b00a14ca9c7`（首轮审查时 HEAD；change.md 的 `base_commit` 尚为空）

## 审查总结

结论：不通过，当前有 1 条 P0 阻塞 implement。注册表、多项目聚合、watch 三块的产品方向与两份 accepted decision 基本一致，10 条 AC、7 条 TODO 和并行批次也未越粒度边界；唯一阻塞点是 AC-1 无条件要求 init 成功后项目已进入注册表，TODO-3 却允许注册失败后仍把 init 视为成功。另有 5 条 P1 交起草方裁决，不阻塞后续核销循环；其中注册表与簿记虽都指向 git common dir，但当前方案没有共同的归一化实现与交叉测试，仍需起草方决定是否把“同源”收紧为单一 API。

## Finding 台账

<!-- 状态单一来源：本 skill 建条与核销（open→verified），修订方（/eo-change）填「处置」列。wont-fix 项后续任何轮次不得重报 -->

| ID | 级别 | 摘要 | 位置 | 状态 | 处置（修订方填） |
|----|------|------|------|------|------------------|
| P0-1 | P0 | AC-1 的“init 成功即已注册”被 TODO-3 的 best-effort 语义直接否定 | AC-1、TODO-3、TODO-4 | verified | AC-1 降格为 best-effort 契约（注册成功→可见；失败→init 仍成功但强制告警+补注册指引，补注册后可见）；TODO-3 明确两处成功出口均注册；TODO-4 补 AC-1 的 `--all` 可见性映射 |
| P1-1 | P1 | 注册表去重与簿记 hash8 没有共同的仓库身份归一化实现 | TODO-1、§5.1 | verified | 采纳单一 API 方案：TODO-1 扩为在 `eo_lib/gitio.py` 新增规范化 repo identity 函数，registry 与 `bookkeeping_path()` 同函数消费（后者为行为等价重构，§1 纯增量假设已注明例外），完成判据含主/linked worktree 交叉测试；§5.1 同步改写 |
| P1-2 | P1 | `project_name` 不是唯一键，按注册名下钻的冲突行为未定义 | AC-2、AC-4、§5.1 | verified | §5.1 新增「name 不是唯一键」裁决：同名合法共存（register 提示）、按名解析多命中报歧义列候选路径、绝不静默取第一项；AC-4 补歧义边界与验证、TODO-2/TODO-5 同步 |
| P1-3 | P1 | watch 对部分失败、锁占用、异常和坏项目的基线/重试矩阵没有验收闭环 | AC-7～AC-9、TODO-6、§5.3 | verified | §5.3 改写为四态结果矩阵（0/1 重算记基线、2/异常不记且重试，逐格定基线/重试/stderr）+ 告警抑制定义（进程内按项目×错误指纹一次，成功 run 后清除、恢复纳入）；AC-7 补部分失败不忙循环、AC-9 补抑制与恢复口径；TODO-6 完成判据逐格单测 |
| P1-4 | P1 | `watch --project` 与正常 `watch --all` 没有正向 AC | §1、TODO-6、§5.3 | verified | 新增 AC-11（--project 任意目录单项目追平；--all 一轮追平多注册项目 + 运行中新注册下一轮纳入）；TODO-6 补映射；§5.3 增 main 分派放行条目（--all/--project 不依赖 cwd，裸 watch 沿用现状） |
| P1-5 | P1 | 注册表持久化测试没有文件落点，前向兼容也未进入完成门 | TODO-1、§5.1 | verified | TODO-1 文件栏落 `tests/test_eo_lib_registry.py`；完成判据补两级未知字段 round-trip、损坏 JSON 容错、同名共存、原子替换失败不破坏旧文件；§5.1 明确条目级未知字段同样保留、损坏 JSON 报错不静默清空 |
| P2-1 | P2 | `EO_HOME` 缺省表达式使用了不可安全照抄的 `~` 写法 | §5.1 | verified | §5.1 标题与正文统一为 `${EO_HOME:-$HOME/.eo}`，并注明 Python 实现走 `os.environ.get` 回落 `Path.home()/".eo"` |

## P0 - 必须修订（阻塞 implement）

### [P0-1] AC-1 的成功后置条件与 TODO-3 互相矛盾

- 类型：TODO↔AC 映射断裂
- 位置：change.md AC-1、TODO-3、TODO-4
- 证据：AC-1 无条件要求“`/eo-project-init` 成功后自动出现在注册表，随后 `eo-board --all` 能看到它”；TODO-3 却规定注册失败“不阻塞 init、提示手工补注册”，于是同一次运行可同时满足 TODO-3 的“init 成功”并违反 AC-1。真实 `eo-project-init/SKILL.md:50-61,237-244` 还有更新分支和首次创建两处成功出口，TODO-3 未说明注册动作落在哪些出口。AC-1 的 `--all` 可见性还依赖 TODO-4，但 TODO-4 只标了 AC-3/AC-9。
- 影响：实施者无法同时遵守 AC 与 TODO；后续 review 也无法判定“init 成功但注册失败并告警”究竟是通过还是失败。
- 建议：二选一统一契约：若注册是成功后置条件，就让注册失败使 init 明确返回未完成并给恢复入口；若坚持 best-effort，就把 AC-1 改为“初始化主体成功，注册失败时明确告警且手工补注册后可见”。同时说明首次创建与更新/修复分支是否都注册，并把 TODO-4 的映射补上 AC-1。

## P1 - 建议修订（移交起草方裁决，不阻塞）

### [P1-1] common-dir 同源还没有收敛为共同实现

基线 `cli/eo-sync:155-165` 在 `bookkeeping_path()` 内私有地执行 `git rev-parse --git-common-dir`、相对路径归一化和 SHA-256 hash8；`cli/eo_lib/gitio.py:6-56` 只有通用 `run_git` 与 worktree 枚举。TODO-1 仅新增 `registry.py`，因此可以做到“都读取 git common dir”，但只能再写一份归一化逻辑，尚不能证明相对/绝对 common-dir、符号链接和后续修订始终同源。建议在 `eo_lib.gitio` 抽一个规范化 repo identity API，让 `bookkeeping_path()` 与 registry 同时消费；至少补主 worktree/linked worktree 的 registry identity 与 bookkeeping hash8 交叉测试。若起草方认定“同源”仅指同一 git 命令，也应把该定义和逐字等价算法写清。

### [P1-2] 按注册名下钻缺少冲突规则

`cli/eo_lib/config.py:36-50` 只校验单项目 `project_name` 为非空字符串，生态内没有唯一性约束；schema 又只按 git common dir 去重，所以两个不同仓库可合法同名。此时 AC-4 的 `eo-board --project <注册名>` 无法唯一解析。建议在 §5.1 定义冲突行为并补边界验证，例如同名注册拒绝并列出既有路径、允许同名但按名称下钻时报歧义并要求路径，或引入独立稳定 alias；不要静默取数组第一项。

### [P1-3] watch 的失败基线与忙重试语义没有验收矩阵

§5.3 已选择 `run` 返回 0/1 后重算基线、返回 2 或异常不更新，并要求坏项目“告警一次”；但 AC-7 只验证成功 run 的自回写不自触发，AC-8 只验证锁占用，AC-9 也没有验证常驻数轮后的告警抑制与恢复。建议把 0/1/2/异常四类结果写成可执行矩阵：是否重算基线、下一轮是否重试、stderr 允许几行；另定义坏配置的“告警一次”是每进程、每错误指纹还是状态转换一次，以及配置恢复后如何重新纳入。这样既能证明不忙循环，也不会把瞬时失败永久吞掉。

### [P1-4] 两个已钉 watch 作用域缺少正向 AC

§1 与 watch decision 都钉了 `watch [--all | --project <path>]`，但现有 AC 只覆盖 cwd 缺省作用域，以及 `--all` 遇到坏路径的隔离；没有一条证明从任意目录使用 `--project`，也没有证明 `--all` 会同时追平两个有效注册项目并在下一轮重读新增注册项。当前 `cli/eo-sync:794-811` 还会在分派子命令前无条件从 cwd 找配置，更需要正向 AC 锁住绕过条件。建议补一条多项目/显式项目 AC，或把这两种作用域从本 change 裁掉。

### [P1-5] 注册表前向兼容没有可执行完成门

TODO-1 声称“注册表单测绿”，但文件栏没有任何测试文件；完成判据也只列幂等、worktree 去重、原子写和 `EO_HOME`，漏掉 §5.1 的未知顶层字段保留。建议明确新增/修改的测试文件，并加入 unknown top-level round-trip、损坏 JSON、同名项目和原子替换失败不破坏旧文件等用例；其中是否保留未知 project-entry 字段也应在 schema 中明确。

## P2 - 可选优化

### [P2-1] `EO_HOME` 缺省写法

§5.1 使用 ``${EO_HOME:-~/.eo}``；在 shell 参数展开里，替换值中的 `~` 不保证再做 tilde 展开，照抄可能得到字面相对路径。建议文档统一写 ``${EO_HOME:-$HOME/.eo}``，Python 实现继续用 `os.environ.get("EO_HOME")` 回落 `Path.home() / ".eo"`。

## AC 质量检查

| AC | 用户视角 | 可验证 | 技术无关 | 备注 |
|----|---------|--------|---------|------|
| AC-1 | 是 | 是 | 是 | 声明本身清楚，但与 TODO-3 成功语义冲突（P0-1） |
| AC-2 | 是 | 是 | 是 | 重复 worktree 已覆盖；同名仓库边界缺失（P1-2） |
| AC-3 | 是 | 是 | 是 | 行字段与 ≥2 项目验证条件明确 |
| AC-4 | 是 | 是 | 是 | 路径正常流清楚；注册名冲突无预期（P1-2） |
| AC-5 | 是 | 是 | 是 | 一层深度在 §5 补足，且明确验证零写入 |
| AC-6 | 是 | 是 | 是 | 默认作用域正常流可验 |
| AC-7 | 是 | 是 | 部分 | 成功 run 的静默/诊断可观察；部分失败未覆盖（P1-3） |
| AC-8 | 是 | 是 | 是 | 锁占一轮后释放的操作和结果明确 |
| AC-9 | 是 | 是 | 是 | 有异常路径与项目间隔离；常驻告警抑制未覆盖 |
| AC-10 | 部分 | 是 | 部分 | 文档交付可验，内容受 §5 finding 影响 |

异常/边界由 AC-2、AC-5、AC-8、AC-9 承担；无 manual AC，速览“人工 0 条”与正文一致。

## TODO↔AC 映射检查

| TODO | 对应 AC | 状态 |
|------|---------|------|
| TODO-1 | AC-1、AC-2 | 警告：共同 repo identity 实现与测试/前向兼容完成门待收紧（P1-1/P1-5） |
| TODO-2 | AC-2 | 通过：手工 register/unregister 正常流有对应 AC |
| TODO-3 | AC-1 | 失败：best-effort 成功语义与 AC-1 冲突（P0-1） |
| TODO-4 | AC-3、AC-9 | 失败：实现 AC-1 的 `--all` 可见性却未标 AC-1（P0-1） |
| TODO-5 | AC-4、AC-5 | 警告：正常流成立，注册名冲突规则缺失（P1-2） |
| TODO-6 | AC-6、AC-7、AC-8、AC-9 | 警告：默认作用域有覆盖，显式/多项目正常流及失败矩阵不足（P1-3/P1-4） |
| TODO-7 | AC-10 | 通过：两份文档均存在且映射直接 |

每条 AC 都有名义 TODO 覆盖；当前 AC-1 的映射内容不能兑现，另有 TODO-6 中两个已钉正常作用域没有正向 AC。

## TODO 机械前提核验

| TODO | 操作与对象 | 基线结果 |
|------|------------|----------|
| TODO-1 | 新增 `cli/eo_lib/registry.py` | 父目录和 Python 模块惯例存在，目标名无冲突；共同 identity API 不存在，见 P1-1 |
| TODO-2 | 修改 `cli/eo-board` | 对象存在；当前 parser 仅有 html/serve 形态，main 会先从 cwd 载配置 |
| TODO-3 | 修改 `eo-project-init/SKILL.md` | 对象存在；有更新分支与首次创建两处成功出口，见 P0-1 |
| TODO-4 | 修改 `cli/eo-board`、`tests/test_eo_board_cache.py` | 两对象存在；`build_data(cfg)` 可复用，现有 cache 仅由 serve 路径消费 |
| TODO-5 | 修改 `cli/eo-board`、`tests/test_eo_board_cache.py` | 两对象存在；与 TODO-4 同一串行批，文件相交不构成并行冲突 |
| TODO-6 | 修改 `cli/eo-sync`、`tests/test_eo_sync.py` | 两对象存在；`cmd_run` 已返回 0/1/2，main 当前无条件依赖 cwd 配置 |
| TODO-7 | 修改 `docs/GUIDE.md`、`docs/sync-adapter-protocol.md` | 两对象存在，与待新增 CLI 用法相符 |

## 粒度检查

TODO 数：7（理想 3-7 / 硬上限 10）｜ 全文：127 行（软标 200-500 / 硬上限 700）｜ 结论：合规。

Batch 2a 与 2b 的声明文件集不相交，且都只消费 Batch 1 的注册表模块，没有彼此的生产者-消费者关系，可保留并行后缀。Batch 3 串行引用两侧最终 CLI 形态也合理。

## §5 三块裁决与上游一致性

| 面 | 判定 | 说明 |
|----|------|------|
| dashboard/activity 废弃，board 唯一呈现层 | 一致 | 未引入 SSE、activity 观测或第二服务 |
| 用户级注册表，init + 手工维护 + 扫描兜底 | 基本一致 | 写用户级文件的例外有上游授权；同源 identity 与名称冲突仍有 P1-1/P1-2 |
| board 只读项目文件、零第三方依赖、GitHub 可选 | 一致 | register 只写用户级注册表，聚合不引入实时 GitHub |
| board 性能靠缓存、不上重架构 | 一致 | 已归档 change #1 将进程内 cache 明确限定为 `--serve`，并规定 terminal/html 单次全量扫；本 change 的终端 `--all` 并发扫描沿用该边界 |
| watch 为呈现侧自费 pull，流程 skill 零负担 | 一致 | 没有把投影触发点塞回六个流程 skill |
| freshness 短路、锁占跳过、终端常驻 | 方向一致 | 自回写吸收成立；失败/告警重试矩阵需 P1-3 补闭环 |
| `watch --all` 共用注册表且不依赖 cwd | 名义一致 | TODO 提及 main 放行；缺正常多项目 AC，见 P1-4 |
| launchd/systemd 后置 | 一致 | OQ 未偷渡进 TODO |

§8 有 2 条 defer，未超过上限；两条都在已钉 MVP 边界内。未触发 §4、§6、§7：所有连带文件已列入 TODO，无流程图，无不可逆操作。

## 前提真实性抽查（维度 7）

| 断言 | 基线 | 证据 | 判定 |
|------|------|------|------|
| registry 去重可与 bookkeeping hash8 共用同一仓库身份源 | `85ad4fcc` | 两边都可读取 git common dir；但 `cli/eo-sync:155-165` 私有实现归一化/hash8，`cli/eo_lib/gitio.py:6-56` 无 identity API，TODO-1 也无交叉测试 | 证据不足（P1-1 补共同实现或等价性证据） |
| run 后重算 freshness 可吸收 identity 回写，锁占可留到下一轮 | `85ad4fcc` | `cli/eo-sync:639-713` 非 dry-run 持锁执行回写与簿记后释放并返回；`cli/eo_lib/freshness.py:37-69` 键含 changes 树 mtime；`cli/eo-sync:643-651,717` 区分锁占 2 与完成 0/1 | 成立；失败矩阵的验收缺口见 P1-3 |
| terminal `--all` 单次全量扫符合当前 board 缓存边界 | accepted decision + archived change #1 + `85ad4fcc` | decision 规定性能走缓存而非重架构；`eo-doc/changes/01-shared-lib-board-cache/change.md:86-100` 将进程内 cache 落在 `--serve`，并明定 terminal/html 单次全量扫不受影响 | 成立 |

## 结构完整性

| 节 | 状态 | 备注 |
|----|------|------|
| 速览 | 通过 | 三块用户可见差异与 §1/§2 一致 |
| §1 意图 + 已钉裁决 | 警告 | 主方向一致；同源 identity 的实现强度与 watch 正向作用域待收紧 |
| §2 验收清单 | 警告 | AC-1 成功语义冲突；watch 两个正常作用域与失败矩阵不足 |
| §3 TODO（Batch） | 失败 | P0-1 造成 AC-1 映射断口；并行组本身安全 |
| 条件节 §4-§8 | 通过 | §5 三块方向与上游基本一致；§8 数量合规 |

## 复审记录（第 2 轮 · 全量 · 2026-07-25）

- 模式：自动升级全量。命中三条机械信号：新增 AC-11 且 AC-1/4/7/9 发生语义性改写；§1 的纯增量假设新增 `bookkeeping_path()` 行为等价重构例外；TODO-1～TODO-6 均有修订，超过 1/3。
- 核销：P0-1、P1-1～P1-5、P2-1 全部 verified。AC-1 与 TODO-3 已统一为 best-effort，且 TODO-4 补齐可见性映射；repo identity 落为 registry/bookkeeping 共用的单一 API 与交叉测试；注册名歧义、watch 四态矩阵与告警恢复、两种显式 watch 作用域、registry 持久化测试及 `EO_HOME` 写法均已到达台账处置落点。
- 全量复查：`type: feature` 合法；11 条 AC 均可操作且有 TODO 覆盖，AC-7/8/9 含失败与边界路径；7 条 TODO 三要素齐全，无占位符；全文 139 行、TODO 7 条，未越粒度边界。Batch 2a/2b 文件集不相交且只共同消费 Batch 1 registry API，可并行；§5 三块与两份 accepted decision、已归档 change #1/#2 现状一致；§8 defer 为 2 条。
- 新增 finding：无。新增 AC-11 与 §1 例外都由对应 TODO、§5 规则和验证口径闭合，未引入新的 P0/P1。
- 未决：无。P0=0，结论：通过。

### 本轮前提抽查

| 断言 | 基线 | 证据 | 判定 |
|------|------|------|------|
| repo identity 可抽为单一 API 且保持既有 bookkeeping hash8 | `85ad4fcc` | `cli/eo-sync:155-165` 的现行算法边界完整；TODO-1/§5.1 明确搬入 `eo_lib.gitio`、两消费方共用并以主/linked worktree 交叉测试锁定输出 | 成立（P1-1 verified） |
| watch 可按 0/1/2/异常区分基线与重试 | `85ad4fcc` | `cli/eo-sync:62,598-717` 已有 0/1/2 返回契约和持锁 finally；AC-7～AC-9、TODO-6、§5.3 逐格定义新增 watch 行为 | 成立（P1-3 verified） |
| `watch --all` / `watch --project` 可绕过当前 cwd 前置解析而不改 run 语义 | `85ad4fcc` | `cli/eo-sync:794-817` 的 cwd 解析位于子命令分派前；§5.3 只对两个显式 watch 作用域改分派，裸 watch 与 run/adapters 保持原路径，并由 AC-11/TODO-6 锁定 | 成立（P1-4 verified） |

## 速报

结论：通过（P0 0 条）［第 2 轮 · 全量］

P0（阻塞 implement）：
1. 无未决 P0。

P1（移交起草方裁决，不阻塞循环）：
2. 无未决 P1。

P2（可后置）：
3. 无未决 P2。

下一步：`/eo-implement eo-doc/changes/03-registry-board-watch/change.md`（status 仍为 draft，先回 /eo-change 对话确认）。未决 P1 已入台账，由起草方裁决：采纳的回 /eo-change 顺手修（不触发复审），不采纳的标 wont-fix 附理由。注意：`/eo-review` 是代码审查，要在 implement 之后，现在还不轮到它。
