---
title: eo-sync 插件层与存量适配器迁移测试报告
change_id: sync-plugin-layer
tags: [eo-sync, plugin, integration]
created: 2026-07-25
updated: 2026-07-25
status: active
summary: >
  第 1 轮重验证通过：本项目存量看板二跑全 skip，GitHub 仅以隔离 dry-run 配置验证，簿记未进入仓库。
---

# eo-sync 插件层与存量适配器迁移测试报告

> 关联 Change：[change.md](change.md)（验收锚点：其 §2 验收清单）
> 首轮测试日期：2026-07-25 ｜ 测试环境：macOS / Python 3.14.2 / 临时 `EO_HOME`
> ⚠️ 首轮之后正文各节为历史快照——当前状态以「FAIL 台账」与末尾「速报」为准

## FAIL 台账

| ID | 级别 | 摘要 | 位置 | 状态 | 根因 | 首见/最近轮 | 基线/修复 commit |
|----|------|------|------|------|------|-------------|------------------|
| 无 | - | 本轮无失败 | - | - | - | - | - |

## 测试总结（首轮快照）

| 指标 | 数值 |
|------|------|
| 单元测试总数 | 67 |
| 单元测试通过 | 67 |
| 单元测试失败 | 0 |
| 集成测试总数 | 3 |
| 集成测试通过 | 3 |
| 集成测试失败 | 0 |

## 单元测试详情

### ✅ 已审计并通过的测试

| 测试文件 | 覆盖点 | 对应 AC / TODO |
|----------|--------|----------------|
| `tests/test_eo_sync.py`（58 例） | 协议、发现/兼容映射、dry-run 零写、锁/串行、身份回写、簿记隔离、孤儿清理、配置语义、GitHub 降级与快照完整性 | AC-2~8 / TODO-1、4、5、7 |
| `tests/test_eo_sync_smoke.py`（5 例） | 夹具端到端 run、二跑 skip、锁、兼容映射 | AC-3~5、7、8 / TODO-1、7 |
| `tests/test_eo_board_cache.py`（4 例） | 既有共享库/看板缓存回归 | 回归基线 |

### 补缺

新增 `GithubFixTests.test_github_dry_run_plans_without_remote_or_writes`：隔离临时 git 仓库用 `sync.github` 测试配置运行 `eo-sync run --dry-run`，断言 draft issue skip、confirmed issue create、archived issue/PR create，且 `EO_HOME/sync-state`、change 内容与 `git status --porcelain` 均零写入。该用例补上原 66 例对 GitHub 目标的真实 CLI dry-run 覆盖；未重写既有测试。

## 一次性执行证据

| 验证点（AC / 输入） | 命令 | 关键输出 | 结论 |
|---------------------|------|----------|------|
| AC-1 本项目存量 board 对拍 | `EO_HOME=<temp> PATH="$PWD/cli:$PATH" python3 cli/eo-sync run --target obsidian` | `shared-lib-board-cache`、`sync-plugin-layer` 两张存量卡均为 `obsidian/stub -> skip`；卡片 SHA-1 前后完全一致 | ✅ |
| AC-1 紧接二跑、AC-8 | 同一隔离 `EO_HOME` 立即重复上述命令 | 两张卡仍全 `skip`；旁车仅在 `<temp>/sync-state/eo-skills-91073d57.json`，源码仓库 `git status` 与 board 卡 SHA-1 均不变 | ✅ |
| AC-6 抽样复核 | change.md AC-6 所列 `grep -rniE ... | grep -vE ...` 扫描 | 白名单外命中 0 行 | ✅ |

## 集成 / 场景验证详情

### 场景 1：存量 Obsidian 投影二跑
- **操作步骤**：对本项目现有 `board/shared-lib-board-cache.md`、`board/sync-plugin-layer.md` 使用真实 `eo-sync run --target obsidian`，再以同一隔离簿记目录立即重跑。
- **期望结果**：存量卡与 `board-github.md` 的字段契约一致，两个 run 都是全 skip，无卡片改写。
- **实际结果**：两轮均为 2 个 `skip`，卡片散列前后相同。✅

### 场景 2：GitHub 目标隔离 dry-run
- **操作步骤**：运行新增的 `GithubFixTests.test_github_dry_run_plans_without_remote_or_writes`。
- **期望结果**：不访问、不创建真实 GitHub issue/PR；仅输出 issue `create` 提示性计划，仓库与旁车均不写。
- **实际结果**：目标用例通过；只执行协议 plan，未调用 `gh`。✅

### 场景 3：SoT 与簿记边界
- **操作步骤**：观察场景 1 的临时 `EO_HOME/sync-state`，并比较 run 前后源码仓库状态和 board 卡散列。
- **期望结果**：簿记只在 `EO_HOME`，仓库无新增；本轮无身份回写时工作区不变。
- **实际结果**：只产生隔离旁车 JSON/lock；仓库原有的 4 个无关未提交文件保持不变，未新增同步工件。✅

## 未覆盖的测试场景

无。GitHub 真实建 issue/PR 依验收约束使用隔离配置和 dry-run 替代，未触碰 remote。

## 遗留问题

无阻塞问题。archive 收口后的真实远端推送属于归档时机，未在本轮对真实 GitHub 执行。

## 速报

结论：通过［第 1 轮 · revision 1 · 基线 `b2e9950`］
下一步：可进入 /eo-review
