---
title: 投影同步现状（看板 stub 与 GitHub 联动）
type: state
tags: [sync, board, github, obsidian, workflow]
created: 2026-07-25
updated: 2026-07-25
scope: 想知道看板卡片/GitHub issue 什么时候更新、怎么手动刷新时
status: active
source: cli/eo-sync
summary: >
  投影统一由 eo-sync 单命令执行：archive 归档时自动跑一次，平时手动 eo-sync run；
  状态流转期间看板不实时是预期行为（watch 自动档已获准，随 C3 落地）。
conclusions:
  - 六个流程 skill 不再逐流转写 stub/建 issue——写路径零投影负担
  - eo-sync run 幂等可反复跑；--dry-run 完全只读；并发跑有文件锁保护
  - 配置：首选 sync 段（init 新配置只写它；重跑 init 对旧段项目代写等价迁移，旧段保留）；存量 board/github 段经兼容映射仍生效，无需改 .eo-project.json
---

## 投影何时更新

| 时机 | 行为 |
|------|------|
| `/eo-archive` 归档收口 | 自动执行一次 `eo-sync run`（失败降级告警不阻塞归档） |
| 手动 `eo-sync run` | 任意时刻、任意 worktree；把全部 change 的当前状态投影出去 |
| `eo-sync watch [--all]` 常驻 | 状态流转后至多一个轮询间隔（默认 10s）自动追平；无变化零成本静默 |

## 使用速查

```bash
eo-sync adapters        # 有哪些适配器、哪些启用
eo-sync run --dry-run   # 只看计划（change × 目标 → create/update/delete/skip + 原因）
eo-sync run             # 执行投影（本项目：Obsidian board/ stub 卡；GitHub 联动关闭）
```

安装：`./install.sh` 把三个 CLI 链接进 `~/.local/bin`（POSIX-only，Windows 用 WSL）。

## 安全语义

- 投影是派生数据，可随时全量重建；stub 整文件覆盖写、issue 靠回写号去重
- 孤儿删除仅在快照可证完整时执行（过滤/扫描告警/枚举降级 → 本轮跳过删除并告警）
- run 之后仓库内至多出现 change frontmatter 的幂等键回写（issue/pr 等）；簿记在 `~/.eo/sync-state/`，仓库零新增文件
