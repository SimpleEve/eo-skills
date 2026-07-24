---
title: eo-sync 插件层与存量适配器迁移 Change 审查报告
change_id: sync-plugin-layer
created: 2026-07-24
status: active
summary: >
  首轮全量审查不通过：四项 P0 分别涉及退役清单漏项、平台身份回写契约、并发临界区和 Windows 安装前提。
---

# eo-sync 插件层与存量适配器迁移 Change 审查报告

> 关联：[change.md](change.md) ｜ 审查日期：2026-07-24 ｜ change status：draft
> 前提抽查基线：`5f38497da71eb7ca17b0fa10e0fe4453251399b8`（首轮审查时 HEAD；change.md 的 `base_commit` 尚为空）

## 审查总结

结论：不通过，当前有 4 条 P0 阻塞 implement。整体方向、档位、AC 数量、TODO 数量、首批适配器范围及 §5.4 的仓库外旁车取向与上游裁定基本一致；阻塞点集中在四个客观断口：现状并非六个触发 skill、第三方平台身份无法走现有通用协议、锁未覆盖产生动作计划的临界区，以及 `install.bat`/`fcntl` 的 Windows 前提不成立。另有 5 条 P1 交起草方裁决，不阻塞后续核销循环。

## Finding 台账

<!-- 状态单一来源：本 skill 建条与核销（open→verified），修订方（/eo-change）填「处置」列。wont-fix 项后续任何轮次不得重报 -->

| ID | 级别 | 摘要 | 位置 | 状态 | 处置（修订方填） |
|----|------|------|------|------|------------------|
| P0-1 | P0 | 退役清单漏掉现存流程触发点 | §1、AC-6、TODO-5 | verified | ①轮：退役范围改「全部现存触发点」+ AC-6 扫描命令 + TODO-5 补 eo-test/conventions。②轮：`--exclude-dir=eo-doc` + 正则扩全变体 + 四文件白名单反滤；补 acceptance.md 与 change-template 三处。③轮（熔断定向修）：选措辞调整方案（不扩白名单——行号白名单脆、文件级掏空零边界）：TODO-5 裁定保留的 4 处描述行（change-template.md:14「看板 stub 卡面」→「看板卡面」、:24「PR 创建后回写」→「归档同步回写」、conventions.md:36/:45「看板 stub」→「stub 卡」）措辞调整出正则、语义不变，入 TODO-5 清单（conventions 六处 / change-template 五处）；完成判据加「改写后新表述不得落正则」。**自证**：起草基线实跑白名单外命中 23 行，逐行映射 TODO-5 删除/改口径/措辞调整动作，无一游离（eo-change×6、implement×4、fix/review/test/init 各 1、acceptance×1、conventions×5、template×3），TODO-5 实施后零输出可达 |
| P0-2 | P0 | `writeback` 硬编码 `issue/pr`，推翻已钉的平台身份参数 | TODO-2、§5.2 | verified | §5.2 改通用身份契约：capabilities 增 `identity_fields` 字段所有权声明，writeback 泛化为 `{<字段名>: <标量>}`，补核校验规则（未声明拒绝/同名冲突 fail closed/非空不覆盖/null 忽略）与 eo_lib 保序回写；§1 幂等行加 Notion page_id；TODO-2/TODO-4 同步（github 走 `identity_fields: ["issue","pr"]` 无特权） |
| P0-3 | P0 | 非 dry-run 的 plan 在锁外，陈旧计划仍可串行重复 apply | AC-7、TODO-1、§5.5 | verified | §5.5 锁范围改为扫描前取锁、持锁完成 scan→plan→apply→回写→簿记原子落盘（权威计划只在锁内生成）；dry-run 只读并明示提示性计划（AC-3 同步）；AC-7 补「串行两次 run 第二次全 skip、不重复创建远端对象」；TODO-1 编排描述与 TODO-7 竞态用例同步 |
| P0-4 | P0 | Windows 安装与锁实现建立在不存在/不可用的基线上 | TODO-6、§5.5 | verified | 裁决 v1 明示 POSIX-only（§1 已钉决策行 + §5.5 + §7 平台边界）：TODO-6 改仅 install.sh 接线（该链接逻辑仅存于 install.sh，假前提删除），install.bat 只加「不支持 Windows 原生安装，可用 WSL」提示；Windows launcher + msvcrt 锁留待需求出现独立立项 |
| P1-1 | P1 | 同状态多 worktree 的 change 选择没有语义消歧 | §5.5 | verified | §5.5 补消歧规则：同状态优先发起 run 的 worktree → 内容 hash 一致任取 → 分叉 fail closed 列候选告警，不以枚举顺序为目标；规则落 eo_lib 扫描层（TODO-1） |
| P1-2 | P1 | 平台 ID 回写与其它投影的同轮可见顺序未定义 | AC-1、§5.1-§5.2 | verified | §5.1 增两阶段编排：`identity_fields` 非空者先 apply，核回写后刷新快照再跑纯投影适配器——声明驱动、无「GitHub 先于 Obsidian」硬编码；同阶段字典序确定；AC-1 补「含同轮回写字段」 |
| P1-3 | P1 | archive 第五层回写会在结算提交后重新制造脏 change.md | AC-8、TODO-5、§5.6 | verified | ②轮裁决「允许第二个收尾 commit」：不调层序（层序前移不可行——PR 创建依赖结算 commit 已推送、issue 兜底关闭要求 status 已 archived；并入下次结算违反 AC-8），第五层有回写即追加 `[<id>] sync 身份回写` commit，无回写零额外 commit；conventions §2.5 改「至多两个收尾 commit」（入 TODO-5）；补冻结语义注记（归档后唯一例外写入 = 身份回写，系决策 #8 推论）；AC-8 同步改口径 |
| P1-4 | P1 | Batch 1 的夹具依赖被安排到 Batch 3 | TODO-1、TODO-7 | verified | 最小协议夹具（tests/fixtures/eo-sync-fixture）与 smoke 测试移入 Batch 1 TODO-1 文件栏，完成判据改「凭本批自带夹具、不依赖后续批」；TODO-7 降为扩夹具成完整矩阵 |
| P1-5 | P1 | starter `.base` 保留与连带口径没有完成门 | §1、TODO-5、§4 | verified | ①轮：`.base` 保留断言入完成判据 + §4 分两类。②轮残项：change-template.md 三处旧联动口径（`issue:` 注释 / 轻档「看板 stub、GitHub 联动同一套」行 / 轻档联动钩子去重注释）补入 TODO-5 文件栏与描述 |
| P1-6 | P1 | 新身份字段缺少“字段不存在时”的保序插入规则 | TODO-1、§5.2 | verified | §5.2 增「保序回写」细则（不依赖预改模板）：已存字段（含 `~`）原地替换值、保留行内注释；不存在字段以单行标量追加在 frontmatter 关闭 `---` 前（锚点与模板内容无关）；键名校验 `^[a-z][a-z0-9_]*$` + change 生命周期保留键黑名单，非法声明 run 启动即拒绝；TODO-2 契约文档与 TODO-7 用例（追加/保注释/非法键拒绝）同步 |
| P1-7 | P1 | archive 的第二个身份 commit 缺少远端传播规则 | AC-8、TODO-5、§5.6 | verified | §5.6 增「远端传播」：本次 run 创建/更新了 PR → 回写 commit 后追加 `git push` 同分支一次（PR 跟踪分支，追加推送自动进入 PR，合并后 SoT 含幂等键）；push 失败告警不阻塞归档（幂等键已在本地，随任意后续 push 传播）；第四层 doc cursor 落后该 commit 明示接受（身份字段无文档语义，下次 doc sync 越过）；AC-8 补 PR 场景推送口径，TODO-5 的 eo-archive 改写项同步 |
| P2-1 | P2 | `EO_HOME` 缺省表达式没有沿用现行可展开写法 | §5.4 | verified | §5.4 改 `"${EO_HOME:-$HOME/.eo}"`，并注实现取 `os.environ.get("EO_HOME")` 缺省 `Path.home()/".eo"` |
| P2-2 | P2 | 协议“次版本”与适配器失败后的总退出码未落成可执行规则 | AC-4、§5.2、§7 | verified | §5.2 落成规则：整数主版本 + 「双方必须忽略未知字段」为次版本演进通道；run 总退出码 0/1/2（全成/部分失败/锁占用）；AC-4 补总退出码口径，§7 同步 |

## P0 - 必须修订（阻塞 implement）

### [P0-1] 退役清单漏掉现存流程触发点

- 类型：前提不成立 / TODO↔AC 映射断裂
- 位置：change.md §1 第 30 行、AC-6、TODO-5
- 证据：基线 `eo-test/SKILL.md:60` 在 test 失败回退时仍要求“联动刷新 stub”；`eo-shared/conventions.md:47` 的撞号自愈和 `:87` 的状态回退也仍要求即时 upsert/刷新 stub。TODO-5 只列 eo-change、eo-implement、eo-review、eo-fix、eo-archive、eo-project-init 六个 skill，完成判据也只 grep 这六处。
- 影响：按当前 TODO 全部实施后，test 回退和引用 conventions 的流程仍会在状态流转期写投影，AC-6 的“流转零投影动作”客观不成立。
- 建议：把范围改为“所有逐流转触发点”，至少纳入 `eo-test/SKILL.md` 与 `eo-shared/conventions.md`；用一条可复现的全仓扫描命令配 allowlist 验证，而不是以六个文件名作边界。若仍保留“六”这个计数，须先解释第七处为何不是触发点。

### [P0-2] 平台身份回写契约不是可扩展协议

- 类型：TODO 推翻已钉参数
- 位置：change.md TODO-2、§5.2 第 92 行
- 证据：`decisions/2026-07-24-sync-plugin-layer.md:26` 已钉平台身份包括 `issue` 号、PR URL 和 Notion `page_id`，且 change.md §1 第 40 行要求内置与第三方走同协议；但 §5.2 把响应固定为 `writeback: {<change_id>: {issue: N, pr: URL}}`，TODO-2 的 Notion 契约项也没有平台身份回写。
- 影响：第三方 Notion 适配器不能通过协议返回 `page_id`；新增任何带源侧身份的目标都必须修改 eo-sync 核，违背第三方可扩和“无后门”。
- 建议：将 writeback 设计为可声明、可校验的通用 frontmatter 身份映射，并在 capabilities 中声明字段所有权；补齐允许字段、冲突处理、空值/删除、未知字段拒绝及 eo_lib 保序回写规则。Notion 仍只写契约和夹具，不实现真实适配器。

### [P0-3] 锁没有覆盖权威计划，无法满足 AC-7

- 类型：TODO↔AC 映射断裂
- 位置：change.md AC-7、TODO-1、§5.5
- 证据：§5.5 明定“apply 阶段”才取锁，plan 不取锁。可复现时序为：进程 A、B 都基于旧簿记 plan 出 create；A 先取锁、apply、回写并释放；B 随后成功取锁并执行锁外生成的旧 plan。B 不会看到锁占用提示，且可重复创建远端对象。
- 影响：锁只防同一时刻写文件，不防陈旧计划串行落地；AC-7 的“后到者干净退出”与 AC-1 的幂等性都没有被 TODO-1 所述方案保证。
- 建议：非 dry-run 从“生成权威 plan”起一直锁到适配器 apply、frontmatter 回写和簿记原子落盘结束；若要保留锁外预览，可先算提示性计划，取锁后必须重新 plan/重校验。测试用 barrier 强制两进程都先完成锁外预计算，再验证只能一个 apply。

### [P0-4] Windows 安装与锁实现前提不成立

- 类型：前提不成立
- 位置：change.md TODO-6、§5.5
- 证据：基线 `install.bat:42-73` 只有 skill junction 安装，没有任何 eo-board CLI 接线可供“复用”；同时 §5.5 指定的 `fcntl.flock` 是 POSIX 路径，而 TODO-6 明确要求 `install.bat` 安装新 CLI。其完成判据只有 POSIX 的 `command -v`，没有 Windows 可执行入口或运行验证。
- 影响：TODO-6 无法按文字复用既有 Windows CLI 逻辑；即使新写链接，extensionless Python 命令和 `fcntl` 也不能据当前方案证明可在 Windows 运行。
- 建议：二选一并写进 AC/TODO：一是明确 v1 CLI 仅支持 POSIX，移除 `install.bat` 接线承诺；二是补 Windows `.cmd`/launcher 安装方案、`where` + 实际执行验证，并把锁抽成跨平台实现。不可一边承诺 bat 安装，一边只定义 POSIX 锁。

## P1 - 建议修订（移交起草方裁决，不阻塞）

### [P1-1] 同状态多 worktree 没有语义消歧

§5.5 称 `scan_all_changes` 已消歧；基线 `cli/eo_lib/changes.py:230` 只按状态取 `max`，同 id 同状态时静默返回枚举中的第一份。建议定义同状态内容分叉的规则：优先调用者 worktree、按明确 revision/commit 选择，或检测分叉后 fail closed 并列出候选；不要把枚举顺序当回写目标。

### [P1-2] 同一 run 内的平台 ID 可见顺序未定义

现行 stub 规范会投影 `issue/pr`，而这些字段只有 GitHub `apply` 返回后才存在。若 Obsidian 先 plan/apply，首轮 stub 缺字段；下一 run 就会 update，不满足 AC-1 的“紧接着再跑全部 skip”。建议在通用协议中声明依赖/阶段，或规定写回后刷新快照并重算受影响投影；不要硬编码“GitHub 先于 Obsidian”的内置特权。

### [P1-3] archive 自动同步后的结算语义未闭合

eo-archive 第三层先提交 `status: archived`，第五层才跑 sync；PR URL 只会在 archived 时产生，因此正常 auto/always 路径会在归档提交之后再次修改 change.md。AC-8 将这种脏状态视作允许，但没有说明谁提交它、是否再次推进文档同步，以及“归档完成”能否带未提交 SoT 返回。建议明确同步所在层级与二次结算策略，或把返回身份纳入冻结提交前的受控阶段。

### [P1-4] Batch 1 不是当前文字宣称的独立 MVP

TODO-1 的完成判据依赖 `tests` 夹具适配器，但夹具只在 Batch 3 的 TODO-7 新增。建议把最小协议夹具和 smoke test 移入 Batch 1，Batch 3 只扩成完整矩阵；否则取消 Batch 1“可独立验证”的表述并改串行依赖。

### [P1-5] starter 看板保留与连带口径缺少完成门

§1 明定 starter `.base` 创建留在 eo-project-init，但 TODO-5 正好会改写当前同时承载“历史同步 + `.base` 创建”的段落，完成判据没有保留断言。全仓扫描还命中 `eo-shared/README.md`、`eo-project-init/references/board-setup.md`、`docs/tier-design.md`、`docs/how-it-works.html`、`docs/v2-design.md` 的旧触发口径，§4 仅列 README/GUIDE。建议给 `.base` 保留加一条明确完成判据，并把规范性引用与用户文档分成“本 change 必改”和“后续同步生成”两类列清。

## P2 - 可选优化

### [P2-1] `EO_HOME` 缺省写法

§5.4 写 `${EO_HOME:-~/.eo}`，而现行 `config.md:15` 要求 `"${EO_HOME:-$HOME/.eo}"`；shell 中前者会得到字面量 `~/.eo`。建议文档统一写 `$HOME`，实现中用 `Path.home()`，避免读者照抄后把簿记落到相对路径。

### [P2-2] 协议演进与失败退出语义

§5.2 只有整数 `protocol_version: 1`，§7 却写“加字段走次版本”；AC-4 也没有规定某适配器失败后整个 run 的最终退出码。建议明确未知字段兼容规则、版本表示与总退出码，便于 cron/agent 判断“部分成功”。

## AC 质量检查

| AC | 用户视角 | 可验证 | 技术无关 | 备注 |
|----|---------|--------|---------|------|
| AC-1 | 是 | 是 | 是 | 验证口径清晰，但实现顺序有 P1-2 |
| AC-2 | 是 | 是 | 是 | 三种生命周期起点可构造样本验证 |
| AC-3 | 是 | 是 | 是 | 零写入边界完整 |
| AC-4 | 是 | 是 | 是 | 覆盖非法 JSON、版本错、非零退出 |
| AC-5 | 是 | 是 | 是 | 覆盖零配置与存量配置 |
| AC-6 | 部分 | 是 | 部分 | 静态 grep 偏实现视角，且扫描边界漏项形成 P0-1 |
| AC-7 | 是 | 是 | 是 | 声明可验，现方案不能保证 |
| AC-8 | 是 | 是 | 部分 | git status 可观察；与 archive 结算关系待裁决 |

异常/边界覆盖已存在于 AC-4、AC-5、AC-7；无 manual AC，速览“人工 0 条”与正文一致。

## TODO↔AC 映射检查

| TODO | 对应 AC | 状态 |
|------|---------|------|
| TODO-1 | AC-3/4/5/7/8 | 失败：锁边界不能成立 AC-7（P0-3） |
| TODO-2 | AC-4 | 失败：第三方身份回写契约不成立（P0-2） |
| TODO-3 | AC-1/2 | 警告：受同轮 ID 可见顺序影响（P1-2） |
| TODO-4 | AC-1/2 | 警告：受同轮 ID 可见顺序影响（P1-2） |
| TODO-5 | AC-5/6 | 失败：退役扫描边界漏项（P0-1） |
| TODO-6 | AC-1/4 | 失败：Windows 基线与验证口径不成立（P0-4） |
| TODO-7 | AC-3/4/5/7/8 | 警告：需随 P0-2/P0-3/P0-4 补协议、竞态及平台矩阵 |

每条 AC 均有名义 TODO 覆盖；当前有四处映射虽标号存在，但方案内容不能兑现对应 AC。

## TODO 机械前提核验

| TODO | 操作与对象 | 基线结果 |
|------|------------|----------|
| TODO-1 | 新增 `cli/eo-sync`；修改 `cli/eo_lib/` | 父目录与无扩展 CLI 惯例存在；共享库存在且可扩 frontmatter 回写 |
| TODO-2 | 新增 `docs/sync-adapter-protocol.md` | `docs/` 存在，目标名无冲突 |
| TODO-3 | 新增 `cli/eo-sync-obsidian` | `cli/` 存在，目标名无冲突 |
| TODO-4 | 新增 `cli/eo-sync-github` | `cli/` 存在，目标名无冲突 |
| TODO-5 | 修改六 skill、board-github/config | 所列对象均存在；真实引用面超出清单，见 P0-1/P1-5 |
| TODO-6 | 修改 `install.sh`/`install.bat` | 两文件存在；只有 `install.sh` 有 eo-board CLI 链接惯例，见 P0-4 |
| TODO-7 | 新增 `tests/test_eo_sync.py` | `tests/` 与 Python 测试惯例存在，目标名无冲突 |

## 粒度检查

TODO 数：7（理想 3-7 / 硬上限 10）｜ 全文：120 行（软标 200-500 / 硬上限 700）｜ 结论：合规。

Batch 2a/2b 的文件集不相交，且二者都只消费 Batch 1 协议，没有互相消费，字母后缀可保留。Batch 1 的验证夹具却落在 Batch 3，见 P1-4。

## 已钉参数与 defer 裁决核对

| 面 | 判定 | 说明 |
|----|------|------|
| capabilities/plan/apply、JSON、版本 | 基本一致 | 演进细则仍有 P2-2 |
| PATH 发现 + 配置启用 | 一致 | 存量段只做兼容映射，正式收编留 OQ-1 |
| 严格单向、漂移只告警 | 一致 | TODO-4 保持该边界 |
| 平台身份回写、簿记旁车 | 不一致 | `issue/pr` 写死，漏第三方 `page_id`，见 P0-2 |
| archive 自动一次 + 手动 | 一致 | 结算闭环仍有 P1-3 |
| Notion 只定契约不实现 | 范围一致 | 身份契约本身尚未闭合 |
| §5.4 旁车路径与格式 | 方向成立 | 仓库外且 worktree 共用；缺省路径记法见 P2-1 |
| §5.5 文件锁而非主 worktree 独占 | 选择成立 | 临界区有 P0-3，等状态目标选择有 P1-1 |
| 逐流转触发点直接退役 | 不完整 | 基线实际引用面超出六 skill，见 P0-1 |

§8 有 3 条 defer，未超过上限；OQ-1/OQ-2 与上游“将来收编”“v1 不加自动档”一致，OQ-3 是新增加固议题且未偷偷进入 TODO。

## 前提真实性抽查（维度 7）

| 断言 | 基线 | 证据 | 判定 |
|------|------|------|------|
| 当前逐流转投影触发仅散落在六个流程 skill | `5f38497d` | `git show 5f38497d:eo-test/SKILL.md` 第 60 行仍刷新 stub；`eo-shared/conventions.md:47,87` 仍规定即时投影 | 不成立（P0-1） |
| `$EO_HOME/sync-state` 可在仓库外由同仓库各 worktree 共享 | `5f38497d` + HEAD 运行态 | 主 worktree `git common dir=.git`，v2 worktree 为同一仓库绝对 `.git`；解析绝对路径后相同；`config.md:5-15` 已定义 EO_HOME | 成立（表达式细节见 P2-1） |
| `scan_all_changes` 已为多 worktree 回写完成消歧 | `5f38497d` | `cli/eo_lib/changes.py:230` 同状态时由 `max` 返回首项，无内容分叉/调用者 worktree 规则 | 证据不足（P1-1 补规则） |

## 结构完整性

| 节 | 状态 | 备注 |
|----|------|------|
| 速览 | 通过 | 与 §1/§2 主方向一致 |
| §1 意图 + 已钉参数 | 警告 | 平台身份协议与真实触发面有 P0 |
| §2 验收清单 | 通过 | 8 条、边界覆盖充足、无 manual |
| §3 TODO（Batch） | 失败 | 四处内容映射不能兑现 AC |
| 条件节 §4-§8 | 警告 | defer 数合规；§4 连带面、§5 临界区、archive 结算待修 |

## 复审记录（第 2 轮 · 全量 · 2026-07-24）

- 模式：自动升级全量。命中两条机械信号：AC-3/4/6/7/8 发生语义性改写；§1 新增“退役范围全量化”“POSIX-only”两项已钉模式选择。
- 核销通过：P0-2/P0-3/P0-4、P1-1/P1-2/P1-4、P2-1/P2-2 verified。通用身份声明、持锁权威计划、POSIX 边界、worktree 消歧、两阶段编排、Batch 1 自带夹具、EO_HOME 与退出码均已落到 AC/TODO/§5 对应位置。
- 未核销 P0-1：AC-6 新增的命令实际会递归展开到 `eo-doc/`，因此永久命中本 change 与历史审查报告；同时模式只含 `upsert|刷新 stub|建 issue`，漏掉基线 `eo-shared/acceptance.md:69` 的“联动 stub”以及“新建看板 stub/创建 GitHub issue/PR 创建”等现存触发表达。TODO-5 也未列 `eo-shared/acceptance.md`，所以“全部现存触发点”仍没有可执行的零结果边界。
- 未核销 P1-3：§5.6 仍没有给出一个与当前 eo-archive 层序兼容的单 meta commit 时序。现行第三层已经提交冻结元数据、第四层推进 doc cursor、第五层才 sync；第五层回写既不能并入已经提交的 meta commit，也不能在不 amend/新增第二 commit 的情况下保持工作区干净。
- 未核销 P1-5：starter `.base` 保留断言已到位；但本轮声称列清“必改连带口径”仍漏 `eo-change/references/change-template.md:23,110,124` 的旧“confirmed 联动回写/看板 stub 与 GitHub 联动/联动钩子去重”口径。
- 新增 P1-6：由本轮通用 `identity_fields` 修订引入。§5.2 只规定“替换目标字段行”，而 Notion `page_id` 等第三方字段默认不在 change 模板中；需明确字段不存在时的插入锚点、键名校验与注释/顺序保留，否则通用回写仍依赖预先改模板。
- 全量复查：type=feature 合法；8 条 AC 均有 TODO 覆盖，异常路径由 AC-4/5/7 承担；TODO 7 条、全文 139 行，未越粒度硬线；Batch 2a/2b 文件集不相交且无互相消费；§8 defer 仍为 3 条。除 P0-1 外未发现新增 P0。

### 本轮前提抽查

| 断言 | 基线 | 证据 | 判定 |
|------|------|------|------|
| AC-6 的扫描边界可证明全部逐流转触发点归零 | `5f38497d` + 本轮 change | 实跑 change.md 所列命令命中 `eo-doc/changes/02-sync-plugin-layer/{change,change-review}.md`；`eo-shared/acceptance.md:69` 的“联动 stub”不匹配现有正则 | 不成立（P0-1） |
| POSIX-only 与既有安装形态一致 | `5f38497d` | `install.sh:164-185` 有 eo-board CLI 链接；`install.bat:42-73` 仅安装 skill junction | 成立（P0-4 verified） |
| archive 回写可直接并入既有单个收尾 meta commit | `5f38497d` | `eo-archive/SKILL.md:63-81` 在第五层 sync 前已完成第三层 meta commit和第四层 doc sync；`conventions.md:61` 限定至多一个收尾 meta commit | 证据不足（P1-3） |

## 复审记录（第 3 轮 · 全量 · 2026-07-24）

- 模式：自动升级全量。AC-6 与 AC-8 均发生语义性改写，§5.6 也换成“允许第二个收尾 commit”的新时序裁决；本轮为 revision 1 的第 3/3 轮。
- 核销通过：P1-3/P1-5/P1-6 verified。第二个收尾 commit 使 archive 本地工作区清洁语义成立；change-template 三处旧联动口径已列入 TODO-5；第三方身份字段的保序插入、键名/保留键校验及测试矩阵已闭合。
- 未核销 P0-1：`--exclude-dir=eo-doc` 与扩充正则修掉了第 2 轮的两个直接问题，但 AC-6 仍要求反滤后零输出，而本轮 TODO 明确保留的描述行仍会命中且不在四文件白名单中。直接证据：`eo-change/references/change-template.md:14`（summary 是看板 stub 卡面来源）、`:24`（PR 创建后回写 URL）以及 `eo-shared/conventions.md:36,45`（stub 文件名/seq 投影说明）均不属于本轮列明的退役行，执行 AC-6 原命令仍会输出它们。因此完成 TODO-5 后也无法按当前清单证明“扫描命令零输出”，P0-1 仍 open。
- 新增 P1-7：由本轮 §5.6 第二个 commit 时序引入。GitHub 适配器在 `eo-sync run` 内先 push 并创建 PR，随后 eo-archive 才生成 `[<id>] sync 身份回写` commit；方案没有规定再次 push。若用户直接在 GitHub 合并，PR URL 回写 commit 不在远端分支，合并后的 SoT 仍缺幂等键；需明确二次 push、失败口径以及第四层 doc cursor 落后该 commit 是否接受。
- 全量复查：type=feature 合法；8 条 AC 仍全部可操作且有 TODO 覆盖，异常路径充分；TODO 7 条、全文 140 行，未越粒度硬线；Batch 2a/2b 文件集不相交且无互相消费；§8 defer 为 3 条。除 P0-1 外未发现新增 P0。

### 本轮前提抽查

| 断言 | 基线 | 证据 | 判定 |
|------|------|------|------|
| AC-6 反滤后的零输出与 TODO-5 保留口径相容 | `5f38497d` + 本轮 change | 实跑命令仍命中 `change-template.md:14,24` 与 `conventions.md:36,45`；TODO-5 只改同文件的其它列明行 | 不成立（P0-1） |
| 第二个收尾 commit 能保证 archive 本地工作区干净 | 本轮 §5.6 | AC-8、TODO-5、§5.6 与 conventions §2.5 的待改口径一致 | 成立（P1-3 verified） |
| 通用身份字段无需预改模板即可回写 | 本轮 §5.2 | 已定义缺失字段在关闭 `---` 前追加、已存字段原位替换、非法键与保留键拒绝；TODO-2/TODO-7 同步 | 成立（P1-6 verified） |

## 熔断后单次定向核销（非新轮次 · 2026-07-24）

- 范围：按用户授权仅核销 P0-1 与 P1-7，不重开全文，也不计入新的复审轮次。
- P0-1 verified：独立执行 AC-6 的白名单外基线扫描得到 23 行，分布为 eo-change×6、implement×4、fix/review/test/init 各 1、acceptance×1、conventions×5、template×3，与台账自证一致。TODO-5 已逐类覆盖 23/23；其中四处需保留的描述行明确采用方案②改写措辞并避开正则，不扩白名单，完成判据仍是原命令零输出。
- P1-7 verified：AC-8、TODO-5 与 §5.6 已一致规定 PR 场景下第二个身份回写 commit 随即再次推送同一分支；同时明确推送失败告警但不阻塞归档，以及第四层 doc cursor 暂时落后可接受，原 finding 的时序缺口已闭合。
- 未决：无。P0=0，结论：通过。

## 速报

结论：通过（P0 0 条）［熔断后单次定向核销 · 非新轮次］

P0（阻塞 implement）：
1. 无未决 P0。

P1（移交起草方裁决，不阻塞循环）：
2. 无未决 P1。

P2（可后置）：
3. 无未决 P2。

下一步：`status` 仍为 draft，先回 `/eo-change eo-doc/changes/02-sync-plugin-layer/change.md` 对话确认，再运行 `/eo-implement eo-doc/changes/02-sync-plugin-layer/change.md`。当前无未决 P1；`/eo-review` 是代码审查，要在 implement 之后，现在还不轮到它。
