---
title: 抽取共享解析库并修复 eo-board local 合并与缓存测试报告
change_id: shared-lib-board-cache
tags: [eo-board, shared-lib, cache, serve]
created: 2026-07-24
updated: 2026-07-24
status: active
summary: >
  第 1 轮重验证通过：--serve 缓存命中、所有新鲜度输入失效及 3 秒客户端轮询链路均有自动化证据；AC-5、AC-6 已勾选。
---

# 抽取共享解析库并修复 eo-board local 合并与缓存测试报告

> 关联 Change：[change.md](change.md)（验收锚点：其 §2 验收清单）
> 首轮测试日期：2026-07-24 ｜ 测试环境：macOS · Python 3.14.2 · 临时 Git fixture · 127.0.0.1 `ThreadingHTTPServer`
> ⚠️ 首轮之后正文各节为历史快照——当前状态以「FAIL 台账」与末尾「速报」为准

## FAIL 台账

无。

## 测试总结（首轮快照）

| 指标 | 数值 |
| --- | --- |
| 单元测试总数 | 0 |
| 单元测试通过 | 0 |
| 单元测试失败 | 0 |
| 集成测试总数 | 4 |
| 集成测试通过 | 4 |
| 集成测试失败 | 0 |

## 单元测试详情

无新增纯单元测试；缓存、Git/ref、文件 mtime 与 HTTP handler 的组合风险以可重复的临时 Git 仓库场景测试覆盖。

## 一次性执行证据

| 验证点（AC / 输入） | 命令 | 关键输出 | 结论 |
| --- | --- | --- | --- |
| AC-1、AC-5、AC-6 | `python3 -m unittest discover -s tests -p 'test_*.py' -v` | 4/4 通过；含实际 CLI `--serve`、`/data.json` 与 3 秒客户端轮询模拟 | ✅ |
| AC-2 抽样复核 | `python3 -c "from cli.eo_lib import find_project_config, load_project_config, split_frontmatter, scan_all_changes, count_ac, run_git; print('shared-lib-import=ok')"` | `shared-lib-import=ok` | ✅ |
| 回归编译 | `python3 -m compileall -q cli/eo_lib cli/eo-board tests` | 退出码 0 | ✅ |

## 集成 / 场景验证详情

### 场景 1：抽取后与基线三形态等价

- **对应 AC**：AC-1。
- **操作步骤**：在同一临时 Git fixture 内从 `792522d` 动态载入旧版 `eo-board`，与当前实现分别取得 `build_data`、终端渲染和 HTML 渲染；再启动当前 `BoardRequestHandler`，请求 `/data.json`。
- **期望结果**：忽略生成时间及 serve 标识后，终端、HTML 和数据面逐字段等价。
- **实际结果**：`test_extracted_board_matches_baseline_for_terminal_html_and_serve_data` 通过；三项逐字段相等。

### 场景 2：连续轮询命中缓存

- **对应 AC**：AC-5。
- **操作步骤**：通过实际 `/data.json` handler 连续请求两次，以包装后的 `build_data` 计数。
- **期望结果**：首请求构建一次，第二次不进入全量扫描。
- **实际结果**：`test_serve_reuses_cached_build_data_for_second_poll` 通过；`build_data` 计数为 1，服务诊断依次为 miss、hit。

### 场景 3：CLI serve 与 3 秒客户端轮询

- **对应 AC**：AC-1、AC-6。
- **操作步骤**：以真实命令 `python3 cli/eo-board --serve --port <临时端口> --no-open` 启动服务；确认 HTML 含 `setInterval(refreshLoop, 3000)`；修改 `change.md` 的 status，等待 3.1 秒后请求 `/data.json`。
- **期望结果**：下一个客户端轮询可取得变更后的列状态，无需重启。
- **实际结果**：`test_cli_serve_exposes_change_to_the_next_three_second_client_poll` 通过；返回 status 为 `reviewed`。

### 场景 4：全部新鲜度输入均触发重建

- **对应 AC**：AC-6、TODO-4、TODO-5。
- **操作步骤**：在同一持续运行的服务中顺序改变 change 内容、backlog 卡、roadmap、仅新增 ref、同 SHA 切换分支、新 commit，并分别替换日期为两个连续月份。
- **期望结果**：每次键改变都重进 `build_data`；可见投影同步更新，跨月刷新本月统计起点。
- **实际结果**：`test_serve_rebuilds_when_all_freshness_inputs_change` 通过；共 9 次构建，分别覆盖 changes、backlog、roadmap、refs、branch、HEAD 和 date；变更后的 status、backlog 数、roadmap phase、分支名与 `direct_commits.since` 均符合断言。

## 已审计的既有覆盖

| AC | 证据 | 本轮结论 |
| --- | --- | --- |
| AC-2 | `review.md` 第 2 轮五域独立导入证据；本轮 import 冒烟复核 | ✅ |
| AC-3 | `review.md` 第 2 轮临时项目 local `project_root` 顶层覆盖证据 | ✅ 已审计，按 auto-light 不重复起环境 |
| AC-4 | `review.md` 第 2 轮非法 local 返回码、文件路径与无 traceback 证据 | ✅ 已审计，按 auto-light 不重复起环境 |

## 未覆盖的测试场景

无。AC-3、AC-4 的 auto-light 复核采用已审计的 review 证据，不重复执行；本轮新增的 heavy 验证已覆盖全部要求路径。

## 遗留问题

无。

## 速报

结论：通过［第 1 轮 · revision 1 · 基线 `5e81f33`］
下一步：AC-5/AC-6 已重验证并勾选；可进入 /eo-review（若复审代码基线仍有效）或由流程置 reviewed 后进入 /eo-archive。
