---
title: cli/eo-board 只读看板 CLI
type: agent
tags: [cli, eo-board, serve, cache, rendering]
created: 2026-07-24
updated: 2026-07-24
scope: 改动看板呈现、门禁判定、serve 缓存时
status: active
source: cli/eo-board
summary: >
  零第三方依赖的单文件只读看板（1602 行）：终端摘要 / --html 静态快照 / --serve 本地轮询服务三形态，
  消费 eo_lib 解析层，board 专属逻辑为门禁判定、backlog/roadmap 聚合、渲染与 HTTP 服务（含每项目单飞缓存）。
conclusions:
  - 宪法四条：只读铁律（绝不写项目文件）、不做清单（无 SSE/无观测/无写操作/零第三方依赖）、性能靠缓存、GitHub 实时状态仅可选旗标
  - serve 缓存：每配置槽一构建锁（_BOARD_BUILD_LOCKS），锁内重算键+二次查表，同槽单飞、跨槽并行
  - 解析能力已抽至 cli/eo_lib，本文件只留呈现职责；改解析先看 eo_lib
---

eo-skills 的默认呈现层。数据全部派生自 change.md frontmatter 与 backlog/roadmap 文件（不读 Obsidian stub）。

## 结构（单文件分区）

| 分区 | 内容 |
|------|------|
| 头部导入引导 | `Path(__file__).resolve()` 定位真实 `cli/` 后 `from eo_lib import ...`；入口捕获 `ConfigError` 格式化退出 |
| 门禁判定（gates） | 探测 review/test/change-review/acceptance 报告，解析 P0/P1/FAIL/轮次，合成 blocker |
| 聚合 | backlog 扫描（vault/local 分流）、roadmap frontmatter、`git log` 直改统计、change git 统计 |
| 渲染 | 终端表 / 自包含 HTML（JSON 注入 + 前端 JS 渲染） |
| serve | `ThreadingHTTPServer` 仅绑 127.0.0.1:7333；`/` 与 `/data.json`；前端 3 秒轮询 hash 比对热刷新 |
| 缓存（serve 内） | `_BOARD_CACHE` 槽（config_path 为键）+ `_BOARD_BUILD_LOCKS` 每槽构建锁；miss 时锁内重算 freshness 键并二次查表后才 `build_data`；hit/miss 各记一行 stderr 诊断 |

## 三形态入口

`eo-board`（终端）/ `--html [-o P]` / `--serve`；多项目：`--all`（注册表聚合，线程池并发、坏条目行内隔离、as-of 戳）/ `--project <路径|注册名>`（任意目录下钻，重名歧义拒绝）/ `--all --scan <父目录>`（一层兜底、同仓 worktree 去重、零写入）；`--register/--unregister` 维护注册表（写 ~/.eo，预钉例外）——共用 `build_data(cfg)`，只是渲染出口不同。单次运行形态不走缓存（天然全量扫）。

## 来源

- [cli/eo-board](../../cli/eo-board) — 实现本体
- [cli-eo-lib.md](cli-eo-lib.md) — 解析层依赖
- install.sh — 符号链接安装入口
