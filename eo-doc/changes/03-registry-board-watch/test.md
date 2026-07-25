---
title: 项目注册表 + eo-board 多项目聚合 + eo-sync watch 测试报告
change_id: registry-board-watch
tags: [registry, eo-board, eo-sync, watch, integration]
created: 2026-07-25
updated: 2026-07-25
status: active
summary: >
  既有 105 例审计通过，新增 6 个隔离的真实 watch 进程场景中 5 个通过；
  发现首轮同步后基线重算窗口会吞掉状态流转，AC-6 不通过。
---

# 项目注册表 + eo-board 多项目聚合 + eo-sync watch 测试报告

> 关联 Change：[change.md](change.md)（验收锚点：其 §2 验收清单）
> 首轮测试日期：2026-07-25 ｜ 测试环境：macOS / Python 3.14 / 临时 git 项目与临时 `EO_HOME`

## FAIL 台账

| ID | 级别 | 摘要 | 位置 | 状态 | 根因 | 首见/最近轮 | 基线/修复 commit |
|----|------|------|------|------|------|-------------|------------------|
| FAIL-1 | 阻塞 | 首轮 run 的 post-run 基线重算会吞掉同窗口内的 change 状态流转，stub 永久停在旧状态 | `cli/eo-sync:836-842`；`tests/test_eo_sync_watch_integration.py#test_transition_during_post_sync_key_recompute_is_not_lost` | fixed | implementation | 1/1 | `5da41b8` / `ae894d8` |

## 测试总结（首轮快照）

| 指标 | 数值 |
| ---- | ---- |
| 单元测试总数 | 105 |
| 单元测试通过 | 105 |
| 单元测试失败 | 0 |
| 集成测试总数 | 6 |
| 集成测试通过 | 5 |
| 集成测试失败 | 1 |

## 单元测试详情

### ✅ 通过的测试

| 测试文件 | 测试用例 | 对应 AC / TODO |
| -------- | -------- | -------------- |
| `tests/test_eo_lib_registry.py` | 14/14：原子注册表、identity 去重、EO_HOME、未知字段与 CLI 往返 | AC-1、AC-2、TODO-1/2 |
| `tests/test_eo_board_cache.py` | 13/13：`--all`、下钻、扫描与失效/结构坏条目行隔离 | AC-3、AC-4、AC-5、AC-9 board 半边 |
| `tests/test_eo_sync.py` | 73/73：watch 四态、抑制、作用域与 SIGTERM 等逻辑审计 | AC-7、AC-8、AC-9、AC-11、TODO-6 |
| `tests/test_eo_sync_smoke.py` | 5/5：内置适配器协议与同步烟测 | 投影基线 |

## 集成 / 场景验证详情

### ✅ 通过的真实 watch 场景

| 场景 | 执行与证据 | 对应 AC |
| ---- | ---------- | ------- |
| 显式项目常驻追平 | 任意临时目录启动 `watch --project`；首轮生成 confirmed stub，完整轮后改为 reviewed，在下一间隔内更新；SIGTERM 返回 0 | AC-6 正常路径、AC-11 `--project` 半边 |
| 部分失败后静置 | 临时 `eo-sync-fail` 适配器的 plan 固定退出 7；3 个轮询间隔内 stderr 仅 1 次 run 诊断和 1 次适配器告警，后续静默 | AC-7 |
| 真实 flock 竞态 | 独立进程持有同一 bookkeeping lock；watch 输出一次锁占跳过，释放后下轮生成 stub | AC-8 |
| 失效注册表路径恢复 | `eo-board --all` 对 ghost 输出行内错误；`watch --all` 仍追平 valid 项目，ghost 告警只出现一次；补齐 ghost 项目后自动生成 stub | AC-9 |
| 多项目与运行中注册 | `watch --all` 追平 first/second；运行中以 `eo-board --register` 加 third，下一轮生成 third stub | AC-11 `--all` 半边 |

### ❌ [FAIL-1] 首轮 post-run 基线窗口丢失状态流转

- **测试文件**：`tests/test_eo_sync_watch_integration.py`
- **对应 AC / TODO**：AC-6、TODO-6
- **失败原因**：真实 `watch --project` 首轮将 confirmed 状态投影为 stub 后，测试立即把 SoT 改为 reviewed。`watch_project_tick()` 随后才在 `cli/eo-sync:836-842` 重算并写入基线；它把新 SoT 的 freshness 键当作“已同步”状态保存，但该轮 adapter 已读取旧 confirmed 快照。之后轮询键相同而在 `:826-827` 静默短路，6 秒内 stub 仍为 confirmed。
- **修复建议**：将 post-run 基线与本轮实际扫描快照绑定，或在重算键与本轮执行输入不一致时再执行一次同步；不能直接把 run 之后观察到的未投影 SoT 状态吸收到基线。
- **错误日志**：
```
eo-sync watch 已启动（间隔 1s · 作用域 --project <temp>/race；Ctrl+C 停止）
[eo-sync watch] ✓ race 已同步 @ <time>
eo-sync watch 已停止。
```

## 一次性执行证据

| 验证点 | 命令 | 关键输出 | 结论 |
| ------ | ---- | -------- | ---- |
| 既有回归资产审计 | `python3 tests/test_eo_lib_registry.py && python3 tests/test_eo_board_cache.py && python3 tests/test_eo_sync.py && python3 tests/test_eo_sync_smoke.py` | 14/14 + 13/13 + 73/73 + 5/5 = 105/105 | ✅ |
| 真实常驻进程 | `python3 tests/test_eo_sync_watch_integration.py` | 6 场景：5 通过、FAIL-1 失败；所有项目、注册表、适配器和锁均在 `TemporaryDirectory` 下，`EO_HOME` 独立 | ❌ |
| 文档口径抽样 | `rg -n "watch|--all|--project|注册表" docs/GUIDE.md docs/sync-adapter-protocol.md` | GUIDE 覆盖 watch 触发、基线、锁、作用域和注册表；协议文档覆盖自动档与注册表重读 | ✅ AC-10 |
| 空白与基线检查 | `git diff --check 85ad4fc..HEAD` | 退出 0 | ✅ |

## 未覆盖的测试场景

无 manual AC。AC-1 的 `/eo-project-init` 两个成功出口本轮复用既有 registry/CLI 回归与代码审计，未重跑完整 skill 对话流程；其余 AC 均有自动证据。

## 遗留问题

- FAIL-1 阻塞 AC-6 完整通过。修复后应保留新增真实进程回归并重跑本报告全部 6 个场景。

## 速报

结论：不通过（失败 1 项）［第 1 轮 · revision 1 · 基线 `5da41b8`］
下一步：回 /eo-implement 修复 FAIL-1 后重测。
