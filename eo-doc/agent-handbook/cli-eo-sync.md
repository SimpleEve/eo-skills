---
title: cli/eo-sync 投影同步核与内置适配器
type: agent
tags: [cli, sync, adapter, projection, lock]
created: 2026-07-25
updated: 2026-07-25
scope: 改动投影同步、适配器协议、簿记/锁/回写逻辑时
status: active
source: cli/eo-sync
summary: >
  单命令投影同步：eo-sync 核（826 行，发现/启用/持锁编排/簿记/回写）+ 内置 obsidian（199 行，stub 投影）与
  github（308 行，issue/PR 投影）适配器；协议 v1 契约见 docs/sync-adapter-protocol.md。
conclusions:
  - 严格单向：适配器 plan 是纯函数、apply 只写自己的目标介质，永不写仓库文件；SoT 回写（identity_fields）与簿记由核统一执行
  - 持锁 scan→plan→apply 全链：权威计划只在锁内生成；快照与 snapshot_complete 是单一原子结构，不可证完整时孤儿删除一律跳过（fail-safe）
  - 触发点：archive 收口自动一次 + 手动 run；watch 自动档已获准（并入 C3 实施）
---

投影层唯一写入面。发现 `eo-sync-*`（PATH 前缀）≠ 执行（须合并配置 `sync` 段或存量 `board`/`github` 段兼容映射启用）。

## 核（cli/eo-sync）分区

| 分区 | 关键函数 | 职责 |
|------|---------|------|
| 发现与启用 | `discover_adapters` / `resolve_enabled` | PATH 扫描 + `sync` 段（缺失时 board/github 兼容映射；`sync: null` = 显式零目标） |
| 协议调用 | `invoke_adapter(exe,verb,req,timeout)` / `load_capabilities` | stdin/stdout JSON、protocol_version=1、坏适配器单体跳过不打断全局 |
| 快照 | `build_scan` / `build_snapshot` / `_warn_incomplete` | 持锁扫描；(snapshots, snapshot_complete) 原子结构；worktree 消歧（同状态：发起 run 的 worktree 优先→hash 一致任取→分叉 fail-closed） |
| 簿记 | `bookkeeping_path` / `load_bookkeeping` / `save_bookkeeping` | `${EO_HOME:-~/.eo}/sync-state/<project>-<hash8>.json`（hash8=git common dir SHA-256 前 8 位），原子落盘 |
| 锁 | `acquire_lock` / `_lock_is_stale` | flock + pid/时间戳；陈锁（>10min 且 pid 死）自清重试一次；后到者非零退出 |
| 回写 | `validate_identity_ownership` + apply 后统一回写 | 字段 ∈ 声明的 `identity_fields`、键名校验、保留键黑名单、同名冲突 fail-closed、非空不覆盖、保序插入（eo_lib `upsert_frontmatter_fields`） |

子命令：`run [--dry-run] [--change <id>] [--target <name>]`、`adapters`。退出码 0/1/2（全成/部分失败/锁占用）。`--change` 过滤时快照标记不完整，孤儿删除自动跳过。

## 内置适配器

- `eo-sync-obsidian`：stub 投影（起点 draft），行为等价原 board-github.md 写法；`identity_fields` 为空（纯投影）
- `eo-sync-github`：issue（起点 confirmed）/PR（起点 archived，按 `github.pr` 策略）；`identity_fields: ["issue","pr"]` 无特权通道；`gh` 不可用提示跳过

## 测试

`tests/test_eo_sync.py`（801 行，unittest 标准库）：协议往返/发现启用/兼容映射/dry-run 零写入/锁互斥与陈锁/簿记幂等/快照完整性 fail-safe/回写校验矩阵。`EO_HOME` 一律临时目录隔离。

## 来源

- [docs/sync-adapter-protocol.md](../../docs/sync-adapter-protocol.md) — 协议 v1 契约（第三方接入指南 + Notion 契约级要点）
- [cli-eo-lib.md](cli-eo-lib.md) — 解析层依赖（新增 `upsert_frontmatter_fields` 保序回写、`list_worktrees_status` 降级感知枚举）
- [changes/02-sync-plugin-layer/](../changes/02-sync-plugin-layer/change.md) — 方案与四轮审查台账（审计历史）
