---
title: eo-board --all 聚合页 v2 代码审查报告
change_id: board-all-v2
tags: [eo-board, aggregate, routing, review]
created: 2026-07-27
updated: 2026-07-27
status: active
summary: >
  第 2 轮已核销修复 commit 043e692 的 P1-1/P2-1/P2-2，
  当前 P0/P1/P2 均为 0，代码审查通过。
---

# eo-board --all 聚合页 v2 代码审查报告

> 关联 Change：[change.md](change.md)（检查表：其 §2 验收清单）
> 首轮审查日期：2026-07-27 ｜ 实施区间：`5a0247f..21165f8`
> 审查范围：`cli/eo-board`、`cli/eo_lib/`、`tests/test_eo_board_cache.py`、`docs/GUIDE.md`、`docs/cli-reference.md` 及 change 实施工件
> ⚠️ 首轮之后正文各节为历史快照——当前状态以「Finding 台账」与末尾「速报」为准

## Finding 台账

<!-- 状态单一来源；轮次编号全文件单调递增（跨 revision 不清零）。写入权（writer matrix）：
     eo-review 建条与核销；fixed + 修复 commit 由 eo-implement 回写；用户可裁决 waived。 -->

| ID | 级别 | 摘要 | 位置 | 状态 | 根因 | 首见/最近轮 | 基线/修复 commit |
|----|------|------|------|------|------|-------------|------------------|
| P1-1 | P1 | 永久测试注释把硬编码基线解释为“本 change 的 base_commit”，违反流程溯源不进代码注释的纪律 | `tests/test_eo_board_cache.py:28` | verified | implementation | 1/2 | `21165f8` / `043e692` |
| P2-1 | P2 | Node 视图助手只执行聚合首页脚本，未自动挂载共享的 `EO_PROJECT` 泳道组件 | `tests/test_eo_board_cache.py:432` | verified | implementation | 1/2 | `21165f8` / `043e692` |
| P2-2 | P2 | 404 测试分支未显式关闭 `HTTPError` 响应，聚焦测试会输出 `ResourceWarning` | `tests/test_eo_board_cache.py:858` | verified | implementation | 1/2 | `21165f8` / `043e692` |

### 轮 1 修复说明（eo-implement 回填）

- **P1-1**：`BASE_COMMIT_REVISION` 注释改为只描述永久契约（「聚合终端输出的兼容基线：此版本之后各版本须逐字节保持一致」）；同时把仍带流程语境的用例名 `..._against_the_change_base_commit` 改为 `..._against_the_compat_baseline`。常量本身保留。
- **P2-1**：新增 `NODE_MOUNT_RUNNER` 最小 DOM 垫片，真正执行 `PROJECT_JS` 的 `mount()`，断言落在共享泳道组件写出的看板骨架上，两条用例分别覆盖聚合快照 `#/p/<route_key>` 路由（含首页让位、样式表互斥、返回入口）与单项目 `--html` 页启动脚本（无返回入口）。三次变异验证均被捕获：聚合路由不再进项目视图 → FAIL；共享骨架 script id 改名 → ERROR；`buildBoard` 掏空 → FAIL×2。
- **P2-2**：`fetch_status()` 用 `with e:` 包住读取，显式释放 `HTTPError` 响应。**未能在本机复现**该 `ResourceWarning`（`-W always::ResourceWarning` 与 `catch_warnings` + `gc.collect()` 两种方式均无告警，疑与 CPython 版本/时序有关）；修复本身无条件正确，故照改。

## 审查总结（首轮快照）

聚合数据、双视图、serve/hash 两套路由、跨槽缓存与异常隔离均按方案落地；
`activity_at` 取 commit 与目录 mtime 的最大值，未提交编辑能进入 freshness
重建并推动流排序。静态快照的已知项目 hash 路由另用真实 Chrome 验证可挂载
完整泳道、隐藏首页并显示返回入口，未发现当前功能副作用。

两项实施偏差本身成立：基线数据改为递归“旧字段保真、新字段可增”仍严格保持
列表长度/顺序、标量值、终端输出和 serve 旧字段；Node 仅存在于测试文件，
运行时源码的 AST 导入守护覆盖 `cli/eo-board` 与当前全部 `eo_lib/*.py`，且
运行时代码不存在 Node 调用。不过永久测试里仍留有一处明确的流程溯源注释，
按项目注释纪律记 P1，因此本轮不流转 `reviewed`。

## P0 - 必须修复（阻塞性问题）

无。

## P1 - 建议修复（重要但不阻塞运行）

### [P1-1] 基线常量注释携带 change 流程溯源

- **类型**：注释纪律（流程溯源）
- **位置**：`tests/test_eo_board_cache.py:28`
- **描述**：`BASE_COMMIT_REVISION` 后的注释以“本 change 的 base_commit”
  解释 SHA。该信息属于 change 工件与 git blame 已能承载的实施 provenance，
  归档后会成为永久测试里的流程残留；`eo-shared/conventions.md` §2.6 明确
  要求此类溯源不得进入代码注释。
- **影响**：不影响运行时，但违反本仓库硬性代码规范，且让测试基线的领域意图
  依赖已结束的工作流语境。
- **建议**：保留确有价值的历史基线常量，把注释改成只描述永久契约，例如
  “聚合终端输出兼容基线”，不再引用“本 change”或 `base_commit` 流程字段。

## P2 - 可选优化

### [P2-1] 共享泳道组件缺少自动执行级回归

`render_snapshot()` 只截取并执行页面最后一段聚合首页脚本，最小 DOM 也只提供
`eo-board-all-data`、`topbar`、`content`；它不会执行 `PROJECT_JS`，无法挂载
`EO_PROJECT`。因此 D-1 所称由 AC-4/AC-5 断言承接的 `render_html` 回归，目前
主要验证的是路由响应、字符串注入和自包含资产，而不是共享泳道组件真实执行。
本轮真实 Chrome 探针已证明当前实现可用，故不判功能缺陷；建议后续补一条已知
`#/p/<route_key>` 的浏览器级或等价 DOM 挂载断言，守住这次较大的模板抽取。

### [P2-2] 404 测试响应未显式释放

`fetch_status()` 捕获 `HTTPError` 后读取正文便直接返回，没有用上下文管理器或
`finally` 关闭响应。本轮 54 项聚焦测试虽通过，但 Python 报出一次
`ResourceWarning: Implicitly cleaning up <HTTPError 404: 'Not Found'>`。
建议读取后显式关闭，避免重复错误路径在更严格的 warning 策略下污染结果。

## 验收标准覆盖检查

| AC 编号 | 审查结论 | 证据摘要 |
|---------|----------|----------|
| AC-1 | 通过 | 聚合数据含全部非 archived change 字段；Node 产出断言覆盖排序、降权分界、blocker、分支和进度 |
| AC-2 | 通过 | 项目条卡含名称、路径、主分支、worktree 数、五状态、backlog、as-of，静默项目仍保留且降饱和 |
| AC-3 | 通过 | `#/` 默认流、`#/cards` 切换及 hash 记忆成立；概要卡信息面回归通过 |
| AC-4 | 实现通过，待 eo-test 勾选 | 三入口共用 route_key；同名/CJK/scan 项目、项目数据端点、跨槽隔离与未知路由均有覆盖；真实快照下钻探针通过 |
| AC-5 | 实现通过，待 eo-test 勾选 | 快照嵌完整 board 与共享资产、无外部请求；已知项目 hash 路由用真实 Chrome 验证可用 |
| AC-6 | 通过 | mtime 编辑触发 freshness 重建并浮顶；稳定键命中、同槽单飞、不同槽并行的调用计数成立 |
| AC-7 | 通过 | 空表指引、结构坏条目/失效路径隔离成立，坏条目无 route_key 且不贡献 change |
| AC-8 | 通过 | 聚合终端输出对 `5a0247f` 归一化全等，参数矩阵与两份用户文档口径一致 |
| AC-9 | 人工项，不核 | 保持未勾；布局与密度由用户验收，不代判 |

## TODO 完成度检查

| TODO | 审查结论 | 说明 |
|------|----------|------|
| TODO-1 | 完成 | 数据抬升、activity_at、route_key 与 fresh/cached getter 等价成立 |
| TODO-2 | 完成 | change 流、项目条卡、双视图框架与下钻链接成立 |
| TODO-3 | 完成 | 概要卡信息保真、可点击与 hash 记忆成立 |
| TODO-4 | 完成 | serve 项目路由、独立数据端点、返回/失效指引和缓存槽隔离成立 |
| TODO-5 | 完成 | 单文件快照内嵌完整泳道并按 hash 切换；自动执行覆盖可按 P2-1 加固 |
| TODO-6 | 部分完成 | 异常/参数/终端/依赖守护与文档均到位，但测试注释纪律见 P1-1 |

## 实施偏差核验

1. **D-1 成立**：`assert_preserves` 对字典逐旧键递归、对列表强制等长并逐位
   比较、对叶值全等；新增 `activity_at` 不会掩盖旧字段变化。终端仍逐字节比较，
   serve 数据也在归一化 `generated_at`/`serve` 后复用同一保真断言。删除 HTML
   字节全等是模板组件化与 data URL 注入的必要结果；当前行为无副作用，长期自动
   执行覆盖的缺口单列 P2-1。
2. **D-2 成立**：Node 只由 `tests/test_eo_board_cache.py` 经 `subprocess.run`
   调用；`cli/eo-board` 与 `cli/eo_lib/` 无 Node/npm/npx 引用。AST 守护会枚举
   当前运行时文件的绝对 import，并与 `sys.stdlib_module_names` 比对；两处 server
   绑定也静态锁定 `127.0.0.1`。当前运行时零 Python 第三方依赖约束未被改变。

## 独立验证

- `python3 -m unittest tests.test_eo_board_cache`：54 项通过，38.999s；Node
  视图用例实际执行、无 skip，同时复现 P2-2 的一条 `ResourceWarning`。
- `python3 -m compileall -q cli tests`：通过。
- `git diff --check 5a0247f..21165f8`：通过。
- 隔离临时 `EO_HOME` 生成 `--all --html`，真实 Chrome headless 打开
  `#/p/eo-skills~d8d4b1bf`：首页 `display:none`，`projRoot` 已挂载
  `p-topbar`/`p-board`，且可见“返回首页”入口。
- 总控提供的全量回归证据：234 项通过；本轮未重复跑全量，只独立复跑上述
  54 项聚焦测试。

## 形态分叉

无新增形态分叉；D-1、D-2 均按已记录实施偏差核验，不引入新的用户决策点。

## 第 2 轮记录（revision 1 · 2026-07-27）

- 审查基线：`043e692`（`020b1a5` 仅回填 finding 台账，不含实现修复）。
- 核销：P1-1 verified。基线注释与用例名已改为“终端输出兼容基线”的永久
  契约语义，不再引用 change/base_commit 流程语境；新增注释均描述测试垫片、
  路由或渲染不变量，未发现新的流程溯源。
- 核销：P2-1 verified。`NODE_MOUNT_RUNNER` 会先执行共享 `PROJECT_JS`，再分别
  执行聚合快照 hash 路由与单项目启动脚本；断言落在组件实际写出的六列泳道、
  change/backlog 卡、首页让位、样式互斥及返回入口上，不再只是搜索资产文本。
- 核销：P2-2 verified。`fetch_status()` 以 `with e:` 包住 404 正文读取，离开
  分支即关闭 `HTTPError` 响应；严格 `ResourceWarning` 策略下的对应定向用例通过。
- reopen：无。
- 新增：无（本轮为三条 finding 的定向核销，不扩为全量审查）。
- 独立验证：严格 `ResourceWarning` 策略下定向执行共享泳道双挂载、未知/失效
  路由与终端兼容基线 4 项，全部通过（2.208s）；`git diff --check
  21165f8..043e692` 通过。总控另提供 236 项全绿证据。
- 本轮结论：通过，P0/P1/P2 均为 0；change 状态已流转 `reviewed`。

## 速报

结论：通过［第 2 轮 · revision 1 · 基线 `043e692`］
下一步：代码审查已通过；进入 `/eo-test` 承接 AC-4/5，AC-9 保持人工验收。
📋 代码审查通过（`test.md` 尚不存在，正式 `/eo-test` 未完成）；人工验收单保留在 `eo-doc/changes/10-board-all-v2/acceptance.md`。
