---
id: sync-config-consolidation
seq: 5
title: board/github 配置段收编进 sync 段
summary: init 停写 board/github 旧段改写 sync 段，存量重跑代写等价迁移，兼容回落不动
status: archived
tier: light
type: enhance
base_commit: 8780d148325b2a7616cefd7785506d38384a04b3
test_lock_commit: 36675cbc430525c0932709a5af823fd338ca8476
commits: ["36675cb", "57c94ae", "6b5c983", "ca0c57e"]
issue: ~
created: 2026-07-25
---

# board/github 配置段收编进 sync 段

意图：兑现 change `sync-plugin-layer` §8 OQ-1（用户已拍板）——`.eo-project.json` 的投影开关从存量 `board` / `github` 段正式收编进 `sync` 段：新项目 init 只写 `sync` 段，存量项目重跑 init 时代写等价迁移；`cli/eo-sync` 兼容映射作为存量兜底原样保留，业务代码零改动。

依据与已钉口径（不再重问）：

- 收编方案 → change `02-sync-plugin-layer` §5.3 与 §8 OQ-1（兼容映射已护住存量，收编只动生成侧与文档侧）
- **sync 键存在性语义不得改变** → `decisions/2026-07-24-sync-plugin-layer.md`：`sync` 键存在（含 `{}`/`null`）即完全以其为准绝不回落，缺席才由旧段派生——本 change 不触碰 `cli/eo-sync` 的 `resolve_enabled`
- 迁移写显式值 → 代写的 `sync` 段对两个适配器都写显式条目（含关闭态 `enabled: false` 及等价参数），保住「问过一次永不再问」语义；旧段保留不删（老版本 skill/工具仍可读）
- 联动问答触发条件同步改口径 → 首次与 1.5 分支的「联动两问」以「合并配置 `sync` 段缺对应适配器键」为触发判据（替代「board/github 段缺失」）

## 2. 验收清单

- [x] AC-1 新项目 init 完成后，`.eo-project.json` 不含 `board`/`github` 段：联动问答答案落 `sync.obsidian`（`enabled`/`stub_dir`）与 `sync.github`（`enabled`/`issue`/`pr`）；用户跳过时写显式关闭条目（`enabled: false`），后续 skill 不再询问（锁定：tests/test_sync_consolidation_caliber.py#TestAC1InitWritesSyncSection）
- [x] AC-2 已初始化项目重跑 init（1.5 分支）：合并配置有旧 `board`/`github` 段且无 `sync` 键 → 提示用户并代写等价 `sync` 段（启用集与兼容映射派生结果逐项一致），旧段保留不删；已有 `sync` 键的项目零动作零提示（锁定：tests/test_sync_consolidation_caliber.py#TestAC2RepairBranchMigration）
- [x] AC-3 `cli/eo-sync` 及兼容映射回落逻辑零 diff：无 `sync` 键的存量配置行为与改前完全一致，`sync` 键存在性语义（存在即为准、缺席才回落）不变（锁定：tests/test_sync_consolidation_caliber.py#TestAC3CliZeroDiff，characterization 基线即绿——覆盖 change 区间 cli/ 零 diff 与存在性语义 docstring；回落行为由既有 tests/test_eo_sync.py#test_compat_mapping 覆盖）
- [x] AC-4 文档口径一致：`eo-project-init/references/config.md` 的 `board`/`github` 字段行标注 legacy（仅兼容映射消费、新配置不再生成）且 `sync` 段升为首选；`eo-shared/board-github.md` 与 `docs/GUIDE.md` 的 opt-in 措辞同步（锁定：tests/test_sync_consolidation_caliber.py#TestAC4DocsCaliber；人工:通读三处 → 无「init 仍写旧段」残留口径。确认：独立复核 subagent 代验通读三处零残留（grep 零命中 + 逐行核对 legacy 标注），用户已预授权直跑到归档，2026-07-25，基线 6b5c983）
- [x] AC-5 本仓 `.eo-project.json` 完成狗粮迁移：含等价 `sync` 段（`obsidian` 启用带 `stub_dir`、`github` 显式关闭态），`eo-sync run --dry-run` 的启用集与迁移前一致（锁定：tests/test_sync_consolidation_caliber.py#TestAC5DogfoodMigration；dry-run 基线 = 仅 obsidian 启用，create 1/skip 4）

---

独立复核：通过，2026-07-25，基线 ca0c57e（首轮复核基线 6b5c983 通过 + P2 修复 ca0c57e 增量复核通过；复核者亲跑锁定套件 18/18 绿、cli/ 零 diff 亲测、AC-4 人工通读代验零残留、57c94ae 锚点修正判定为非弱化）

注记：tests/test_eo_sync_watch_integration.py#test_transition_during_post_sync_key_recompute_is_not_lost 在本机间歇性失败（竞态窗口计时敏感），base commit 8780d14 上亦复现，与本 change 无关（cli/ 零 diff 已断言）。
