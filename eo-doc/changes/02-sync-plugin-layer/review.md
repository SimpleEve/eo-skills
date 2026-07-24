---
title: eo-sync 插件层与存量适配器迁移代码审查报告
change_id: sync-plugin-layer
tags: [eo-review, eo-sync, plugin]
created: 2026-07-25
updated: 2026-07-25
status: active
summary: >
  第 3 轮复审不通过：worktree 枚举瞬时降级仍可误删投影，响应与配置契约尚有两处未闭合。
---

# eo-sync 插件层与存量适配器迁移代码审查报告

> 关联 Change：[change.md](change.md)（检查表：其 §2 验收清单）
> 首轮审查日期：2026-07-25 ｜ 审查范围：`5f38497..2a6644f`（实施提交 `21458aa..2a6644f`），覆盖 `cli/eo-sync*`、`cli/eo_lib/`、协议文档、安装脚本、测试与 TODO-5 涉及的流程 skill
> 本轮基线：`2a6644f` ｜ plan revision：1
> ⚠️ 首轮之后正文各节为历史快照，当前状态以「Finding 台账」与末尾「速报」为准

## Finding 台账

<!-- 状态单一来源；轮次编号全文件单调递增（跨 revision 不清零）。写入权（writer matrix）：
     eo-review 建条与核销（open→verified；verified 后再打回 = reopen 回 open）；
     fixed + 修复 commit 由 eo-implement 修复循环回写；
     waived = 用户显式裁决不修（当场获得裁决的 skill 写入，附原话要点；不阻塞 reviewed/归档）；
     eo-change 回炉时追加作废行并把仍 open/fixed 的行批量标 superseded。历史轮次节谁都不改。
     根因枚举：implementation / requirement（打回实为需求问题 → 建议回炉） -->

| ID | 级别 | 摘要 | 位置 | 状态 | 根因 | 首见/最近轮 | 基线/修复 commit |
|----|------|------|------|------|------|-------------|------------------|
| P0-1 | P0 | worktree 枚举瞬时降级仍被误判为完整快照并删除投影 | `cli/eo-sync:593`; `cli/eo-sync:644` | fixed | implementation | 1/3 | `2a6644f` / `a3af2d6` |
| P1-1 | P1 | `identities` 含非标量 frontmatter，违反协议 v1 快照契约 | `cli/eo-sync:267`; `docs/sync-adapter-protocol.md:133` | verified | implementation | 1/3 | `2a6644f` / `3be8ca2` |
| P1-2 | P1 | 同状态 worktree 的计划来源与回写落点使用两套选择规则 | `cli/eo-sync:311`; `cli/eo_lib/changes.py:225` | verified | implementation | 1/2 | `2a6644f` / `7167f35` |
| P1-3 | P1 | apply 响应缺少 `writeback` 仍通过最小 schema 校验 | `cli/eo-sync:484`; `cli/eo-sync:500` | fixed | implementation | 1/3 | `2a6644f` / `a3af2d6` |
| P1-4 | P1 | `sync: null` 被新增为合法零目标，但公开配置契约仍限定 object | `cli/eo_lib/config.py:51`; `eo-project-init/references/config.md:82` | fixed | implementation | 1/3 | `2a6644f` / `a3af2d6` |
| P1-5 | P1 | GitHub apply 会提前提交失败簿记并把 PR 失败报告为成功 | `cli/eo-sync-github:240`; `cli/eo-sync-github:260` | verified | implementation | 1/2 | `2a6644f` / `7167f35` |
| P1-6 | P1 | archived issue 每次 run 都再次计划 close，第二次不能全 skip | `cli/eo-sync-github:133` | verified | implementation | 1/2 | `2a6644f` / `7167f35` |
| P1-7 | P1 | 逐流转投影退役仍残留执行指令与旧收口语义 | `eo-change/SKILL.md:123`; `eo-implement/SKILL.md:134` | verified | implementation | 1/2 | `2a6644f` / `7167f35` |
| P1-8 | P1 | 新增测试 docstring 再次写入 P0/P1 流程溯源 | `tests/test_eo_sync.py:428`; `tests/test_eo_sync.py:648` | verified | implementation | 1/3 | `2a6644f` / `3be8ca2` |

## 审查总结（首轮快照）

核心锁边界已经放在权威扫描之前，持锁覆盖 scan→plan→apply→回写→簿记，簿记也采用同目录临时文件加 `os.replace`；三态 dry-run、部分失败隔离、POSIX 安装接线和既有 38 个 unittest 均通过。当前仍不能进入 reviewed：`--change` 会真实删除范围外 stub，是直接的数据破坏；同时通用身份字段只实现了写回、没有实现再次读取，same-status worktree 的计划与回写可能错位，GitHub 适配器也未兑现第二次全 skip 和真实失败传播。TODO-5 的正则证据虽然为零行，但人工语义复核发现回炉路径仍要求即时刷新投影。

## P0 - 必须修复（阻塞性问题）

### [P0-1] `--change` 会删除所有范围外投影

- **类型**：逻辑错误 / 数据破坏
- **位置**：`cli/eo-sync:305`、`cli/eo-sync-obsidian:132-140`
- **描述**：核先用 `--change` 过滤快照，却仍把适配器的完整簿记命名空间传给 `plan`。Obsidian 和夹具都把「簿记存在但快照缺席」解释为 change 已放弃，因而对未选中的 change 生成 `delete`。
- **影响**：全量同步 `c1/c2` 后执行 `eo-sync run --change c1`，实测 `c2.md` 被删除，命令仍退出 0；传入不存在的 id 会把全部已记账投影判为孤儿。未来带远端 delete 的第三方适配器会把同一缺陷放大为远端数据删除。
- **建议**：协议显式传递扫描范围与快照完整性；选择性 run 时禁止从「缺席」推导删除，或把删除检测限定为一次无扫描警告的全量 run。补两 change 的落地回归用例，覆盖命中、未命中和扫描降级三种场景。

## P1 - 应修复

### [P1-1] 通用身份字段只有写路径，没有读路径

- **类型**：架构问题 / 功能缺失
- **位置**：`cli/eo_lib/changes.py:183-206`、`cli/eo-sync:275-296`
- **描述**：`parse_change_file` 与 `build_snapshot` 只硬编码 `issue`/`pr`，第三方写回的 `page_id`、`fixture_ref` 等字段下次扫描不会交还适配器。文档把 `identity_fields` 定义为通用平台身份，并用 Notion `page_id` 作示例，但适配器无法从协议快照读取已落 SoT 的身份。
- **影响**：旁车丢失或重建后，第三方只能把已有对象当成未创建对象，通用幂等键退化为不可消费的记录；协议仍实质偏爱内置 GitHub 字段。
- **建议**：按 capabilities 为每个适配器把其身份字段加入快照，或提供稳定的 `identities` 映射；补「写回→删除旁车→再 run 仍 skip/定位原对象」用例。

### [P1-2] same-status worktree 的计划与回写会指向不同文件

- **类型**：并发逻辑错误
- **位置**：`cli/eo-sync:307`、`cli/eo_lib/changes.py:235-237`、`cli/eo_lib/changes.py:268-275`
- **描述**：快照用 `pick_change_winner`，同状态时沿用枚举第一份；回写却按 `resolve_writeback_path` 优先发起 worktree。实测同一候选集会得到 `plan=wa/change.md`、`writeback=wb/change.md`。
- **影响**：适配器可能按主 worktree 的 title/issue/pr 操作远端，却把新身份写进发起 worktree；回写后刷新仍可能重新选回第一份，看不到同轮身份，破坏同轮可见与 fail-closed 语义。
- **建议**：扫描与回写共用同一个候选选择结果/对象，选择时一次性应用「最高状态→发起 worktree→同内容任取→分叉拒绝」，不要在 plan 后重新推导落点。

### [P1-3] 协议边界只验 JSON 与版本，不验 verb 响应 schema

- **类型**：健壮性 / 插件隔离
- **位置**：`cli/eo-sync:115-124`、`cli/eo-sync:437-459`
- **描述**：`invoke_adapter` 只要求顶层为 dict 且版本为 1；`actions`、`writeback`、`results`、`bookkeeping` 的容器类型、action op 与标量身份值均未校验。比如 `actions: "x"` 会在调用方执行 `a.get` 时抛异常，`writeback: []` 会在 `.items()` 处抛异常，对象值还会被写成非契约标量。
- **影响**：一个输出「语法合法 JSON、结构不合法」的第三方适配器可中断整次 run，后续适配器不再完成，与适配器级失败隔离和协议文档不一致。
- **建议**：在进入编排前按三动词逐层验证最小结构和枚举；结构错误统一转成该适配器失败、继续其它目标、总退出码 1。未知字段仍按 v1 规则忽略。

### [P1-4] 显式空 `sync` 无法关闭存量兼容映射

- **类型**：配置语义错误
- **位置**：`cli/eo_lib/config.py:72`、`cli/eo-sync:129-147`
- **描述**：配置加载把「缺少 sync」「`sync: {}`」「sync 类型非法」都压成 `{}`，`resolve_enabled` 又以 truthy 判断段是否存在。实测 `{"sync": {}, "board": {"enabled": true}}` 仍启用 obsidian。
- **影响**：用户按协议用空 `sync` 显式选择零目标时，旧 `board/github` 配置仍被执行，违反 AC-5 的「sync 段存在则完全以其为准」；类型错误也会静默降级而不是配置失败。
- **建议**：保留段是否存在的信息并校验其对象类型；以键存在性而不是非空性决定是否走兼容映射，补空对象与非法类型用例。

### [P1-5] GitHub apply 的真实结果没有可靠进入簿记与退出状态

- **类型**：逻辑错误 / 幂等性
- **位置**：`cli/eo-sync-github:196-203`、`cli/eo-sync-github:225-242`、`cli/eo-sync:457-458`
- **描述**：issue body 编辑无论成功失败都先写入目标 `body_hash`，所以下次会直接 skip 失败的更新；PR 分支路径忽略 `gh pr create` 返回码，随后 `gh pr view` 失败也仍返回 `ok: true`。`gh` 缺失/无 remote 时返回的 `skipped/note` 又被核丢弃，最终输出仍显示计划中的 create/update；未登录也没有按契约预检为非阻塞 skip。
- **影响**：瞬时 issue edit 失败会被永久记成已同步；PR 创建失败时 run 退出 0 且无 URL 回写；用户看不到跳过原因，无法据退出码判断实际结果。
- **建议**：仅在远端动作成功后更新簿记；PR 使用实际 create 响应或显式目标分支查询并传播非零；核消费逐 action 的 `ok/skipped/note`，用实际结果输出与计算退出码；补未安装、未登录、create/edit/close/pr 失败矩阵。

### [P1-6] archived issue 不满足串行第二次全 skip

- **类型**：幂等性回归
- **位置**：`cli/eo-sync-github:120-122`
- **描述**：只要 status 为 archived 且已有 issue，每次 plan 都无条件生成 `update/close`，不读取远端关闭状态，也不使用簿记记录已关闭。相同输入连续调用 plan，第二次仍是 update。
- **影响**：AC-7 已勾的「第二次全部 skip」只由夹具用例证明，内置 GitHub 目标实际会重复调用 `gh issue close`，并可能因“已关闭”返回码造成后续 run 失败。
- **建议**：成功关闭后记入可复核状态，并在 plan 中以远端只读状态或可信簿记判 skip；增加 archived+issue 的两次真实适配器 plan/apply 回归。

### [P1-7] TODO-5 的语义退役没有真正清零

- **类型**：流程契约违反
- **位置**：`eo-change/SKILL.md:123`、`eo-implement/SKILL.md:134`
- **描述**：AC-6 的指定 grep 确实零输出，但回炉确认步骤仍写「再刷新一次投影」，这是 confirmed 流转期的执行指令；轻档收口摘要仍复述旧的「GitHub 联动→stub 终态」，与其声称的 eo-archive 单一信源和新第五层名称不一致。
- **影响**：执行 eo-change 回炉时仍可能即时写投影，直接违反「状态流转期间零投影动作」；旧摘要会继续教后续 agent 按已退役机制理解归档。
- **建议**：删除回炉确认的即时刷新，改为「由下次 eo-sync 重算」；轻档摘要只写「投影同步（eo-sync）」或干脆不复述 archive 层内步骤。补一条不依赖易规避关键词的人工语义扫描清单。

### [P1-8] 新增注释违反流程溯源纪律

- **类型**：注释纪律
- **位置**：`cli/eo_lib/changes.py:258`、`tests/fixtures/eo-sync-fixture:7`、`tests/test_eo_sync_smoke.py:1`
- **描述**：生产 docstring 写「规则（change §5.5）」；测试夹具与 smoke 文件写「供 AC-4」「Batch 1」。这些是 change 节号/AC/批次的流程来源标注，不是读代码所需的长期语义。
- **影响**：归档后注释依赖历史工件上下文并会腐烂，正是 `conventions.md §2.6` 和本 review 维度 4 明令记 P1 的情形。
- **建议**：直接陈述「多 worktree 回写消歧」「协议失败注入」「eo-sync smoke」等稳定行为，移除 change/AC/Batch 溯源。

## P2 - 可后置

本轮无 P2。

## 验收标准覆盖检查

| AC 编号 | 描述 | 状态 |
|---------|------|------|
| AC-1 | 投影字段等价与紧接第二次全 skip | 不核：按任务边界归 `/eo-test` |
| AC-2 | draft/confirmed/archived 生命周期起点 | ✅ 通过：三态内置适配器 dry-run 符合起点与 PR 策略 |
| AC-3 | dry-run 逐行计划且零写入 | ✅ 通过：提示性计划、无 board/state/frontmatter 写入 |
| AC-4 | 第三方发现、协议错误隔离与总退出码 | ⚠️ 部分通过：夹具的非法 JSON/主版本/非零退出均通过；结构合法但 schema 非法的响应仍会打断全局（P1-3） |
| AC-5 | 零配置与存量兼容映射 | ❌ 未通过：缺段路径通过，显式空 `sync` 错误回落（P1-4） |
| AC-6 | 流转期零投影、archive 自动一次 | ❌ 未通过：指定 grep 零行，但回炉确认仍有即时投影指令（P1-7） |
| AC-7 | 锁互斥、串行第二次全 skip | ❌ 未通过：锁占用退出码 2 与持锁区间通过；内置 GitHub archived issue 第二次仍 update（P1-6） |
| AC-8 | SoT 污染与 archive 身份 commit | 不核：按任务边界归 `/eo-test` |

## TODO 完成度检查

| TODO | 描述 | 状态 |
|------|------|------|
| TODO-1 | 核 CLI、持锁编排、身份回写、worktree 消歧 | ❌ 未完成：选择性 run 误删、通用身份读路径缺失、计划/回写候选错位 |
| TODO-2 | 协议 v1 契约文档 | ⚠️ 部分完成：文档成形，但通用身份与 schema 隔离未被实现兑现 |
| TODO-3 | 内置 Obsidian 适配器 | ⚠️ 部分完成：正常全量投影成立，过滤快照会误触发 delete |
| TODO-4 | 内置 GitHub 适配器 | ❌ 未完成：失败传播、簿记与 archived 幂等存在缺陷 |
| TODO-5 | 逐流转触发点全面退役 | ❌ 未完成：关键词门通过但语义残留 |
| TODO-6 | POSIX 安装接线 | ✅ 完成：临时 HOME/EO_BIN_DIR 安装后三个命令均可发现并执行 |
| TODO-7 | 完整测试矩阵 | ❌ 未完成：38 个 unittest 全绿，但没有覆盖 `--change` 多对象、内置 GitHub apply/二次 archived 或空 sync |

## 验证记录

- `python3 -m unittest discover -s tests -p 'test*.py'`：38 tests，全部通过。
- `python3 tests/test_eo_sync.py`：29 tests，全部通过；`python3 tests/test_eo_sync_smoke.py`：5 tests，全部通过。
- `python3 -m pytest ...`：当前 Python 环境未安装 pytest，未以 pytest runner 执行；同一用例已用 unittest 入口执行。
- AC-6 指定 grep：反滤后 0 行；补充语义扫描命中 `eo-change/SKILL.md:123` 与 `eo-implement/SKILL.md:134`。
- P0 定向复现：初次全量后 board 为 `c1.md,c2.md`；`run --change c1` 输出 `c2 → delete`，落地后只余 `c1.md`，退出码 0。
- 三态 dry-run：draft 仅 stub create、issue/pr skip；confirmed issue+stub create、pr skip；archived issue+stub create、默认分支 auto PR skip；仓库与旁车零写入。
- `git show --check 21458aa 7771c58 5da3e6a 2a6644f`、`git diff --check 5f38497..2a6644f`、`sh -n install.sh`：通过。

## 第 2 轮记录（revision 1 · 2026-07-25）

- 审查基线：`7167f35`
- 核销：P1-2、P1-5、P1-6、P1-7 → `verified`。
- 未核销：P0-1、P1-1、P1-3、P1-4、P1-8 由 `fixed` 回 `open`；这些 finding 尚未到过 `verified`，本轮不记复发。
- 新增：无。本轮只复核第 1 轮台账；AC-1/AC-8 仍归 `/eo-test`，其余 AC 不重做全量验收。

### 未核销证据

1. **P0-1**：`snapshot_complete` 只看有没有 `--change`，不看扫描是否降级。定向复现先全量生成 `c1/c2` stub，再让 `c2/change.md` 暂时缺少 frontmatter；第二次全量 run 已告警跳过 `c2`，却仍计划并执行 `c2 → delete`，退出码为 0，stub 从存在变为被删。同状态内容分叉导致快照缺项时也会走同一路径。
2. **P1-1**：第三方身份字段的读路径已可工作，旁车删除后会 skip；但 `_read_identities()` 原样返回全部 frontmatter。本 change 的实际快照含列表值 `fix_consumed`、`commits`，与协议 v1 声明的「全部标量字段映射」不一致。
3. **P1-3**：容器错型已能隔离，但最小结构仍未校验。对只有 `protocol_version` 的 plan/apply 响应，两个校验函数都返回通过；缺少 `actions`、`results`、`writeback`、`bookkeeping` 的适配器会被静默当成成功，而不是隔离并令 run 退出 1。
4. **P1-4**：`sync: {}` 与普通非法字符串已覆盖；但 `_validate_merged()` 把显式 JSON `null` 与字段缺席混为一类。定向配置 `sync: null` 加 `board.enabled: true` 可成功加载，并实际回落启用 `obsidian`，违反 `sync` 必须为 object 的配置契约。
5. **P1-8**：旧三处溯源已删除，但修复测试新增七个带 `P0-1` / `P1-x` 的类 docstring；自检又没有扫描 `tests/test_eo_sync.py`，因此绿灯没有覆盖违规所在文件。

### 已核销证据

- **P1-2**：`resolve_change()` 一次选定权威 rec，`scan_snapshots()` 保存该对象，`apply_writeback()` 直接复用；定向用例确认计划与回写路径一致、分叉返回空权威项。
- **P1-5 / P1-6**：GitHub edit/close/PR 成败矩阵确认失败不推进簿记、非零结果如实返回，PR 成功只调用一次并回写 URL；成功 close 写 `issue_closed`，下一次 plan 为 skip。
- **P1-7**：回炉确认已改为「下次 eo-sync 重算」，轻档收口只保留 archive 内嵌调用所需的 `eo-sync run` 语义，原非投影流程步骤仍在。
- `python3 -m unittest tests.test_eo_sync tests.test_eo_sync_smoke`：50 tests，全部通过；上述反例表明现有测试尚未覆盖五个未核销边界。

本轮结论：不通过（P0 1 条，P1 4 条）。`status` 保持 `implementing`，当前不可置 `reviewed`。

## 第 3 轮记录（revision 1 · 2026-07-25）

- 审查基线：`3be8ca2`
- 核销：P1-1、P1-8 → `verified`；P1-2、P1-5、P1-6、P1-7 保持 `verified`。
- 未核销：P0-1、P1-3、P1-4 由 `fixed` 回 `open`；三项均尚未到过 `verified`，本轮不记复发。
- 新增：无。本轮只复核第 2 轮未决台账；AC-1/AC-8 仍归 `/eo-test`，其余 AC 不重做全量验收。

### 未核销证据

1. **P0-1**：过滤、frontmatter 解析告警与适配器缺省字段三条路径已 fail-safe，但 worktree 枚举仍是两次无绑定探测：`list_worktrees()` 在取锁前执行，随后锁内 `_worktrees_enumerated_ok()` 只检查第二次命令是否成功。定向构造两个 worktree，`c2` 只存在于第二个；首次全量投影后，让第一遍 `git worktree list --porcelain` 瞬时失败、锁内复查恢复成功。第二次 run 把退化得到的单 worktree 列表误判为完整，输出并执行 `c2 → delete`，退出码 0，`c2.md` 从存在变为被删。应在锁内一次取得「worktree 列表 + 完整性」的同一份权威结果，不能用后一次成功为前一次退化背书。
2. **P1-3**：裸 plan/apply 与缺少 `actions`、`results`、`bookkeeping` 已能隔离；但 apply 缺少协议规定「无则空对象」的 `writeback` 仍返回校验通过。定向调用 `_validate_apply_response({"results": [], "bookkeeping": {}, "drift": []})` 返回 `None`，与 v1 最小结构及文档的 `writeback` 对象约束仍不一致。
3. **P1-4**：`sync: null` 已不再回落存量配置，但修复把它新增定义为合法零目标；`_validate_merged()` 明确放过 null，公开配置表与协议仍只允许 `sync: object`。定向加载 `sync: null` 成功，说明实现与对外 schema 仍分叉；应按既有契约拒绝，或先在权威契约中明确把 null 纳入合法类型，不能只靠代码注释改口径。

### 已核销证据

- **P1-1**：`_read_identities()` 已排除 list/dict；对当前 change 实测 `fix_consumed`、`commits` 不再进入 `identities`，全部剩余值均为协议允许的标量，旁车丢失读回用例保持通过。
- **P1-8**：修复提交移除了测试 docstring 中全部 finding 号；生产代码、夹具与两份测试文件扫描 `P0/P1`、change 节号均零命中，自检范围也已纳入测试文件。
- `python3 -m unittest tests.test_eo_sync tests.test_eo_sync_smoke`：56 tests，全部通过。
- `python3 -m unittest discover -s tests -p 'test*.py'`：60 tests，全部通过。
- `git diff --check 7167f35..3be8ca2`：通过。现有回归未覆盖「第一次 worktree 枚举失败、第二次复查成功」与 apply 缺 `writeback` 两个反例。

本轮结论：不通过（P0 1 条，P1 2 条）。`fix_rounds` 当前为 2；下一次模式二修复会用到第 3 轮额度。`status` 保持 `implementing`，当前不可置 `reviewed`。

## 速报

结论：不通过（P0 1 条，P1 2 条）［第 3 轮 · revision 1 · 基线 `3be8ca2`］

P0（阻塞）：
1. 首次 worktree 枚举瞬时失败、锁内复查成功时，退化快照仍会删除另一 worktree 的投影 — `cli/eo-sync:593`

P1（应修）：
1. apply 缺 `writeback` 仍通过 v1 最小 schema 校验 — `cli/eo-sync:484`
2. `sync: null` 被代码新增为合法零目标，但公开配置契约仍限定 object — `cli/eo_lib/config.py:51`

下一步：回 `/eo-implement` 模式二使用第 3 轮修复额度；修复提交后重跑 `/eo-review`，P0/P1 清零方可置 `reviewed`。
