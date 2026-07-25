---
title: 项目注册表 + eo-board 多项目聚合 + eo-sync watch 代码审查报告
change_id: registry-board-watch
tags: [registry, eo-board, eo-sync, watch]
created: 2026-07-25
updated: 2026-07-25
status: active
summary: >
  首轮审查发现 3 条 P1：结构性坏注册条目可击穿项目隔离，watch 基线遗漏配置状态，
  且 run 后 freshness 重算异常会终止常驻循环；当前未达到 reviewed 门。
---

# 项目注册表 + eo-board 多项目聚合 + eo-sync watch 代码审查报告

> 关联 Change：[change.md](change.md)（检查表：其 §2 验收清单）
> 首轮审查日期：2026-07-25 ｜ 审查范围：`85ad4fc..8b30a1c`（实施提交 `8290253..8b30a1c`）
> ⚠️ 首轮之后正文各节为历史快照——当前状态以「Finding 台账」与末尾「速报」为准

## Finding 台账

<!-- 状态单一来源；轮次编号全文件单调递增（跨 revision 不清零）。写入权（writer matrix）：
     eo-review 建条与核销（open→verified；verified 后再打回 = reopen 回 open）；
     fixed + 修复 commit 由 eo-implement 修复循环回写；
     waived = 用户显式裁决不修（当场获得裁决的 skill 写入，附原话要点；不阻塞 reviewed/归档）；
     eo-change 回炉时追加作废行并把仍 open/fixed 的行批量标 superseded。历史轮次节谁都不改。
     根因枚举：implementation / requirement（打回实为需求问题 → 建议回炉） -->

| ID | 级别 | 摘要 | 位置 | 状态 | 根因 | 首见/最近轮 | 基线/修复 commit |
|----|------|------|------|------|------|-------------|------------------|
| P1-1 | P1 | 非字符串 registry path 会击穿 board 行隔离并终止 watch --all | `cli/eo-board:1561`、`cli/eo-sync:849` | fixed | implementation | 1/1 | `8b30a1c` / `5da41b8` |
| P1-2 | P1 | watch 基线不含配置状态，配置变更与同键故障恢复会被静默短路 | `cli/eo-sync:802`、`cli/eo_lib/freshness.py:37` | fixed | implementation | 1/1 | `8b30a1c` / `5da41b8` |
| P1-3 | P1 | run 后 freshness 重算未进入异常矩阵，单项目异常可终止整个 watch | `cli/eo-sync:820` | fixed | implementation | 1/1 | `8b30a1c` / `5da41b8` |
| P2-1 | P2 | --scan 不去重本轮新发现的同仓 worktree | `cli/eo-board:1595` | fixed | implementation | 1/1 | `8b30a1c` / `5da41b8` |
| P2-2 | P2 | CLI 帮助重新使用不可安全照抄的 EO_HOME 缺省表达式 | `cli/eo-board:1735` | fixed | implementation | 1/1 | `8b30a1c` / `5da41b8` |

## 审查总结（首轮快照）

主体分层与增量边界清楚：`repo_identity()` 是从原 `bookkeeping_path()` 算法原样抽出的单一 API，主/linked worktree 的 hash8 交叉测试通过；registry 使用同目录临时文件加 `os.replace()`，替换失败保留旧文件，损坏 JSON 不会被静默清空；`eo-board --all` 的正常项目扫描任务没有共享可变状态，`--scan` 的既有回归也证明注册表字节不变。文档只新增已裁决的触发点和用法，未把投影负担塞回六个流程 skill，零第三方依赖与 board 项目文件只读边界均保持。

当前仍有 3 条 P1。最直接的是 registry 只校验 `projects` 外壳为列表，结构性坏条目可让 `Path(...)` 抛错并越过 board/watch 的项目级隔离；watch 另有两处状态机缺口：其基线没有纳入本次 run 的配置输入，且成功 run 后的第二次 freshness 计算不受异常保护。因此 status 保持 `implementing`，修复后须复审。

## P0 - 必须修复（阻塞性问题）

无。

## P1 - 建议修复（重要但不阻塞）

### [P1-1] 结构性坏注册条目可终止整个多项目命令

- **类型**：潜在 Bug / 故障隔离缺失
- **位置**：`cli/eo_lib/registry.py:36`、`cli/eo-board:1561`、`cli/eo-sync:849`
- **描述**：`load_registry()` 只验证顶层对象和 `projects` 列表，不验证条目的 `path` 类型；随后 board worker 和 watch scope 都在各自的保护边界之外直接执行 `Path(entry["path"])`。构造合法 JSON 条目 `{"name":"bad","path":123}` 时，`eo-board --all` 的 `pool.map()` 向主线程传播 `TypeError`，有效项目也不再输出；`eo-sync watch --all` 则在 `watch_scope()` 中直接退出常驻进程。现有测试只覆盖“字符串路径不存在”，没有覆盖结构性坏条目。
- **影响**：一行失效数据可以拖垮所有有效项目，违反 AC-9 的 board 行内报错与实现要求的 watch 单项目隔离。
- **建议**：在 registry 边界明确校验/规范化条目字段，或让两个消费方把路径构造也纳入逐条异常边界；board 返回错误行，watch 按稳定指纹告警一次并继续。

### [P1-2] watch freshness 基线遗漏同步配置与故障健康状态

- **类型**：逻辑错误 / 状态机缺口
- **位置**：`cli/eo-sync:802-810`、`cli/eo_lib/freshness.py:37-69`
- **描述**：每轮虽然重新加载合并配置，但用于短路的 `compute_freshness_key()` 只覆盖 board 数据输入，不含 `.eo-project.json` / `.eo-project.local.json` 或 `sync` 适配器参数。独立探针在首轮完成后把 `sync: null` 改为启用适配器，第二轮 runner 调用数仍停在 1；同样地，已有 baseline 后经历一次非法配置再恢复原内容，恢复轮因 key 相同在第 810 行返回，配置错误 suppression 仍残留，之后同一故障不会重新告警。
- **影响**：watch 运行期间启用目标或修改适配器参数不能自动生效；“故障修复后清除抑制、再故障重新告警”的恢复闭环也不完整。
- **建议**：为 watch 构造包含同步相关合并配置（及 local 覆盖）的稳定指纹，并把健康/故障转换纳入状态；配置加载失败时应使后续健康轮无法沿用旧 baseline 静默返回。

### [P1-3] run 后 freshness 重算异常逃逸四态矩阵

- **类型**：潜在 Bug / 生命周期
- **位置**：`cli/eo-sync:820`
- **描述**：run 前的配置加载和 freshness 计算、runner 本身都有异常保护，但退出 0/1 后用于吸收回写的第二次 `compute_freshness_key(cfg)` 在保护边界之外。该函数的目录遍历存在真实文件系统竞态窗口（例如根目录在 `is_dir()` 与 `stat()` 间消失）；独立探针令第二次计算抛错时，异常直接越过 `watch_project_tick()` 和只捕获 `KeyboardInterrupt` 的外层循环。
- **影响**：一个项目在成功/部分失败 run 后的瞬时文件系统异常会终止整个 `watch --all`，而不是“不记 baseline、按指纹告警、下一轮重试”。
- **建议**：把 run 后重算纳入同一个逐项目异常矩阵；失败时不更新 baseline、抑制重复告警并返回外层循环，保持其它项目继续运行。

## P2 - 可选优化（锦上添花）

### [P2-1] --scan 应对本轮发现项继续扩充 identity 集合

`cli/eo-board:1595-1600` 的 `known` 只包含 registry 条目，发现一个未注册目录后没有把其 `repo_identity` 加入集合；同一父目录下若同时存在同仓主/linked worktree，会出现两个临时项目行。追加前先写回 `known` 即可保持“一个 repo identity 一行”的一致语义。

### [P2-2] CLI 帮助中的 EO_HOME 写法与已钉口径不一致

`cli/eo-board:1735,1747` 使用 `${EO_HOME:-~/.eo}`，而 change、GUIDE 和 init 已统一为 `${EO_HOME:-$HOME/.eo}`；前者若被复制到 shell，参数展开结果里的 `~` 不保证再次做 tilde expansion。建议统一帮助文本。

## 验收标准覆盖检查

| AC 编号 | 描述 | 状态 |
|---------|------|------|
| AC-1 | init 两个成功出口顺手注册，失败 best-effort 告警 | ✅ 通过：更新分支 `eo-project-init/SKILL.md:61` 与首次创建分支 `:238-242` 均有落点；register CLI 回归通过 |
| AC-2 | register / unregister、worktree 去重、同名共存 | ✅ 通过：单一 identity API 与往返/幂等/同名/linked worktree 用例通过 |
| AC-3 | --all 每项目一行计数、backlog、as-of | ✅ 通过：双项目聚合回归通过 |
| AC-4 | 任意目录按路径/注册名下钻，歧义拒绝 | ✅ 通过：路径、名称与双候选报错用例通过 |
| AC-5 | --scan 一层并入且零 registry 写入 | ✅ 通过：运行前后 registry bytes 相同；P2-1 为同仓扫描去重优化 |
| AC-6 | watch 状态流转一个间隔内追平 | ⏭ 本轮不核：watch 常驻执行证据归 `/eo-test` |
| AC-7 | watch 键短路、四态基线与部分失败静默 | ⏭ 常驻验收归 `/eo-test`；静态审查发现 P1-2/P1-3 |
| AC-8 | 锁占跳过、下轮追平 | ⏭ 本轮不核：watch 常驻执行证据归 `/eo-test` |
| AC-9 | 坏项目隔离、告警抑制与恢复 | ⚠️ 部分通过：字符串失效路径正常隔离；结构性坏条目击穿 board 半边（P1-1），watch 常驻半边归 `/eo-test` |
| AC-10 | GUIDE 与协议文档同步 | ✅ 通过：触发点、作用域、注册表和多项目命令口径一致 |
| AC-11 | watch --project / --all 常驻正向行为 | ⏭ 本轮不核：watch 常驻执行证据归 `/eo-test` |

## TODO 完成度检查

| TODO | 描述 | 状态 |
|------|------|------|
| TODO-1 | registry + repo identity 单一 API + hash8 等价重构 | ✅ 完成：算法等价、原子替换、损坏容错、未知字段与交叉测试均到位 |
| TODO-2 | board register / unregister | ✅ 完成 |
| TODO-3 | init 两出口顺手注册 | ✅ 完成 |
| TODO-4 | --all 并发聚合与失效行隔离 | ⚠️ 部分完成：正常并发聚合成立，结构性坏条目隔离缺口见 P1-1 |
| TODO-5 | --project 与 --scan | ✅ 完成：P2-1 为边界优化 |
| TODO-6 | watch 四态、抑制、作用域与退出 | ⚠️ 部分完成：主路径与既有单测成立，状态/异常闭环见 P1-1～P1-3 |
| TODO-7 | GUIDE 与协议文档 | ✅ 完成 |

## 验证记录

- `python3 tests/test_eo_lib_registry.py`：14/14 通过。
- `python3 tests/test_eo_board_cache.py`：11/11 通过。
- `python3 tests/test_eo_sync.py`：69/69 通过。
- `python3 tests/test_eo_sync_smoke.py`：5/5 通过。
- 合计 99/99；`git diff --check 85ad4fc..8b30a1c` 通过。
- 额外对抗探针：非字符串 registry path 在 board/watch 均复现未捕获 `TypeError`；有效配置仅修改 `sync` 后 runner 未再次调用；run 后 freshness 重算异常会逃逸；已有 baseline 的配置故障恢复后 suppression 未清除。

## 速报

结论：有保留通过（P1 3 条）［第 1 轮 · revision 1 · 基线 `8b30a1c`］
P1（应修）：
1. 结构性坏 registry path 会终止 `eo-board --all` / `eo-sync watch --all` — `cli/eo-board:1561`
2. watch 基线遗漏同步配置与故障健康状态，配置变更/恢复可被静默短路 — `cli/eo-sync:802`
3. run 后 freshness 重算异常会终止整个 watch 循环 — `cli/eo-sync:820`
P2（可后置）：
4. `--scan` 未去重本轮新发现的同仓 worktree — `cli/eo-board:1595`
5. CLI 帮助仍使用 `${EO_HOME:-~/.eo}` — `cli/eo-board:1735`
下一步：回 `/eo-implement` 模式二修复 P1-1～P1-3 后复审；watch 常驻 AC 的执行证据仍由 `/eo-test` 收口。
