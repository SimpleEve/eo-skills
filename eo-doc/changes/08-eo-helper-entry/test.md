---
title: eo-helper 单一交互入口测试报告
change_id: eo-helper-entry
tags: [eo-helper, eo-board, pty, serve]
created: 2026-07-25
updated: 2026-07-25
status: active
summary: >
  审计既有 200 项回归并补充真实 PTY、真实聚合 serve 和临时前缀安装验证后，205 项测试全绿；AC-9 仍为用户人工验收项。
---

# eo-helper 单一交互入口测试报告

> 关联 Change：[change.md](change.md)（验收锚点：其 §2 验收清单）
> 首轮测试日期：2026-07-25 ｜ 测试环境：macOS / Python 3.14 / 临时 Git 仓库与临时 `EO_HOME`
> ⚠️ 首轮之后正文各节为历史快照——当前状态以「FAIL 台账」与末尾「速报」为准

## FAIL 台账

无。本轮未发现实现或测试基建失败。

## 测试总结（首轮快照）

| 指标 | 数值 |
| ---- | ---- |
| 回归测试总数 | 205 |
| 回归测试通过 | 205 |
| 回归测试失败 | 0 |
| 新增重验证场景 | 5 |
| 新增重验证通过 | 5 |
| 新增重验证失败 | 0 |

## 覆盖审计与补缺

既有 `tests/test_eo_board_cache.py` 已真实审计 AC-1 的聚合 HTML/坏条目、AC-2 的同槽单飞及稳定键命中计数、AC-3 的注册表逐请求重读和空表指引；`tests/test_eo_helper.py` 已覆盖固定菜单映射、非 TTY、非法输入、EOF/Ctrl+C 与 mock 层的短命令/长驻命令分支。未重写这些通过覆盖，仅补下列无法由 mock 或 handler 级测试充分证明的重验证：真实进程的聚合状态热刷新与空表后注册、真实 PTY 的前台会话与 `os.exec`、临时前缀安装。

| 测试文件 | 新增或审计重点 | 对应 AC / TODO |
| -------- | -------------- | -------------- |
| `tests/test_eo_board_cache.py` | 审计缓存调用计数、跨槽 Barrier 并发、HTML/错误行；新增真实 `--all --serve` 状态流转与空表后注册 | AC-1、AC-2、AC-3 / TODO-1~3 |
| `tests/test_eo_helper.py` | 审计七项 argv 映射、非 TTY、异常输入、短/长命令的函数级行为 | AC-4、AC-5、AC-6 / TODO-4 |
| `tests/test_eo_helper_pty.py` | 新增真实 PTY 短命令回菜单、长驻 `exec` PID 接管与 Ctrl+C；临时 `EO_BIN_DIR` 安装 | AC-4、AC-5、AC-7 / TODO-4~5 |
| `tests/test_eo_sync*.py`、`tests/test_eo_lib_*.py` 与其余套件 | 审计全量回归，均在临时状态目录或 fixture 中运行 | 回归保护 |

## 一次性执行证据

| 验证点（AC / 输入） | 命令 | 关键输出 | 结论 |
| ------------------- | ---- | -------- | ---- |
| AC-2/3/4/5/7 focused heavy | `python3 -m unittest -v tests.test_eo_board_cache.BoardAllAggregateTests tests.test_eo_helper tests.test_eo_helper_pty` | 30 项通过；真实随机端口 serve、PTY Ctrl+C、临时前缀安装均通过 | ✅ |
| 全量回归 | `python3 -m unittest discover -s tests -p 'test_*.py' -q` | `Ran 205 tests in 74.603s`，`OK` | ✅ |
| 静态可执行性 | `git diff --check && python3 -m py_compile tests/test_eo_board_cache.py tests/test_eo_helper.py tests/test_eo_helper_pty.py` | 退出码 0 | ✅ |

## 集成 / 场景验证详情

### 场景 1：聚合 serve 状态流转与缓存
- **操作步骤**：临时 Git 项目注册到临时 `EO_HOME`，随机端口启动 `eo-board --all --serve --no-open`；读取页面轮询脚本与 `/data.json`，把 change 从 `draft` 改为 `reviewed` 后等待 3.1 秒再请求。
- **期望结果**：页面保留 `setInterval(refreshLoop, 3000)`，下一轮数据为 `reviewed`；稳定键重复请求不增 `build_data` 计数，同槽六路并发只构建一次、两个槽各一次。
- **实际结果**：✅ `test_all_serve_cli_refreshes_changed_status_on_next_poll` 通过；审计的 `test_all_serve_single_flight_per_slot_and_stable_key_no_rebuild` 通过并打印 hit/miss 诊断。

### 场景 2：挂起 serve 的注册表变化与空表指引
- **操作步骤**：以空临时注册表启动随机端口聚合 serve，读取 `/`；服务不重启，另建项目并通过 `eo-board --register` 写入同一临时 `EO_HOME`，再读 `/data.json`。
- **期望结果**：空表页面给出 `--register` 指引；新项目即时成为唯一聚合行。
- **实际结果**：✅ `test_all_serve_cli_rereads_registry_after_empty_guidance` 通过；handler 级的坏条目隔离和逐请求重读覆盖亦通过。

### 场景 3：真实 PTY 菜单会话
- **操作步骤**：在临时 PATH 放置可控 `eo-sync`/`eo-board`，PTY 启动 `eo-helper`。短命令选 4 后观察回显、子命令输出、退出码与重回菜单；长驻选 2 后比较 shell PID，发送 Ctrl+C。
- **期望结果**：短命令原样输出、明确显示 `退出码 7` 并回菜单；长驻进程 PID 不变，Ctrl+C 进入底层命令并以 130 退出。
- **实际结果**：✅ `test_short_command_echoes_output_nonzero_status_and_returns_to_menu` 与 `test_long_command_execs_in_place_and_ctrl_c_reaches_underlying_process` 通过。

### 场景 4：临时前缀安装
- **操作步骤**：设临时 `HOME` 与 `EO_BIN_DIR` 执行 `sh install.sh --codex-only`，从生成的前缀链接直接运行 `eo-helper`（非 TTY）。
- **期望结果**：`eo-helper` 链接指向仓库 CLI，安装尾部主推该入口，命令能打印菜单映射。
- **实际结果**：✅ `test_install_links_helper_in_temporary_prefix_and_promotes_it` 通过。

## 未覆盖的测试场景

- AC-9：README 新用户视角的通读顺畅度为明确人工验收项，未以静态检查或自动测试替代；保持 [acceptance.md](acceptance.md) 中的未勾选项，待用户确认。

## 遗留问题

无自动化失败。AC-9 人工验收未完成，不在本报告中自动勾选或归档。

## 速报

结论：通过［第 1 轮 · revision 1 · 基线 `c757368`］
未覆盖 AC：AC-9（明确人工验收，保留 acceptance.md 给用户）
下一步：可进入 /eo-review（尚未审码）
