---
title: eo-board --all 聚合页 v2 测试报告
change_id: board-all-v2
tags: [eo-board, aggregate, routing, browser]
created: 2026-07-27
updated: 2026-07-27
status: active
summary: >
  第 1 轮测试通过：既有回归测试审计通过，真实 Chrome 覆盖聚合 serve 下钻与离线快照零网络路径。
---

# eo-board --all 聚合页 v2 测试报告

> 关联 Change：[change.md](change.md)（验收锚点：其 §2 验收清单）
> 首轮测试日期：2026-07-27 ｜ 测试环境：macOS，Python 3.14.2，Node 25.4.0，Google Chrome 150 headless
> ⚠️ 首轮之后正文各节为历史快照——当前状态以「FAIL 台账」与末尾「速报」为准

## FAIL 台账

无。

## 测试总结（首轮快照）

| 指标 | 数值 |
| --- | --- |
| 单元测试总数 | 236 |
| 单元测试通过 | 236 |
| 单元测试失败 | 0 |
| 集成测试总数 | 2 |
| 集成测试通过 | 2 |
| 集成测试失败 | 0 |

## 单元测试详情

实施已落测试集中在 `tests/test_eo_board_cache.py`，本轮按 AC 审计后独立执行，断言未被弱化：

| 测试文件 | 已审计覆盖 | 对应 AC / TODO |
| --- | --- | --- |
| `tests/test_eo_board_cache.py` | change 流字段、排序、降权、项目条卡与双视图 hash 记忆 | AC-1、AC-2、AC-3 / TODO-1、TODO-2、TODO-3 |
| `tests/test_eo_board_cache.py` | 路由分派、同名稳定键、`--scan` 项目、404 指引、缓存槽隔离 | AC-4、AC-6 / TODO-4 |
| `tests/test_eo_board_cache.py` | 快照内嵌全量泳道、hash 挂载、自包含静态守护 | AC-5 / TODO-5 |
| `tests/test_eo_board_cache.py` | 异常条目隔离、终端兼容、参数矩阵、依赖/回环绑定与文档口径 | AC-7、AC-8 / TODO-6 |

执行：`python3 -m unittest discover -s tests -p 'test_*.py' -q`，结果 `Ran 236 tests in 86.820s`，`OK`。

## 一次性执行证据

| 验证点 | 命令 | 关键输出 | 结论 |
| --- | --- | --- |
| AC-4 | 隔离 `EO_HOME`、两条同名注册项目和一条 `--scan` 项目下起 `python3 cli/eo-board --all --scan <dir> --serve --port 59885 --no-open`；Chrome 点击流 | 三个入口各进对应泳道；浏览器返回恢复 `#/cards`；返回首页回默认流；scan 项目直达；未知/失效 key 均为 404 指引页且含返回首页 | ✅ |
| AC-5 | 同一隔离项目运行 `python3 cli/eo-board --all --scan <dir> --html -o /tmp/eo-board-v2-e2e/all.html --no-open`；Chrome 打开 `file://` 快照 | 默认流、概要卡和 `#/p/<route_key>` 均可用；请求监听与 Performance Resource 条目中的 HTTP(S) 请求均为 `[]` | ✅ |

## 集成 / 场景验证详情

### 场景 1：聚合 serve 路由下钻

- **操作步骤**：以隔离注册表启动真实 `--all --serve`；创建两项目同名但根目录不同，并用 `--scan` 并入第三项目；在 Chrome 依次点击项目摘要条卡、change 行、概要卡，执行浏览器返回与页内返回。
- **期望结果**：三入口各抵达正确泳道；稳定键区分同名；浏览器返回恢复进入前的概要卡视图，页内返回首页回默认 change 流；scan 项目可达；未知与失效 key 给出指引页。
- **实际结果**：通过。三条 route key 不同；条卡、行和概要卡均到达预期项目；浏览器返回为 `http://127.0.0.1:59885/#/cards`，页内返回为 `http://127.0.0.1:59885/`；未知和失效路由均返回 404 且含「返回首页」。
- **证据**：`/tmp/eo-board-v2-e2e/e2e-result.json`、`/tmp/eo-board-v2-e2e/serve-home.png`。

### 场景 2：离线快照双视图与零网络

- **操作步骤**：生成 `--all --html` 单文件，以 Chrome 从 `file://` 打开，切至概要卡后点击扫描项目的 hash 路由，再返回首页；记录浏览器请求与 Resource Timing。
- **期望结果**：单文件可在三种 hash 视图间切换，且没有 HTTP(S) 网络请求。
- **实际结果**：通过。默认流 3 行、概要卡 3 张、扫描项目 `#/p/<route_key>` 泳道均已渲染；`httpRequests=[]`、`httpResources=[]`。
- **证据**：`/tmp/eo-board-v2-e2e/e2e-result.json`、`/tmp/eo-board-v2-e2e/snapshot-home.png`。

## 未覆盖的测试场景

- AC-9 为人工观感验收，按归属保持未勾；自动化不能替代布局与密度过目。

## 遗留问题

- 无阻塞缺陷。
- 无新增形态分叉；实施偏差 D-1、D-2 已在 `implement.md` 记录，本轮仅审计其既有覆盖，不产生新的用户决策点。

## 速报

结论：通过［第 1 轮 · revision 1 · 基线 `8e7f123`］
下一步：可进入 `/eo-archive`；AC-9 仍待用户按 [acceptance.md](acceptance.md) 人工验收。
