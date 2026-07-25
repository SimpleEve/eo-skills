---
id: watch-single-instance
seq: 6
title: eo-sync watch 单实例保护
summary: watch 同作用域硬互斥（--all 撞 --all、同仓 --project 互撞即报错退出），跨域重叠仅告警
status: archived
tier: light
type: enhance
base_commit: 4ad83a6d48f252185791301e9ccc50dba85b7d73
test_lock_commit: 385fd1a3e6aa76b930224c3e3f8c9fd5ec8b5885
commits: ["385fd1a", "632e3c1"]
issue: ~
created: 2026-07-25
---

# eo-sync watch 单实例保护

意图：防止多个 `eo-sync watch` 在同一作用域上互相踩踏（重复轮询、重复告警、竞争 run 锁）——同作用域硬互斥：第二个 `--all` 撞 `--all`、或同 repo identity 的项目级 watch 互撞时，启动即以非零码报错退出（提示含持有者 pid、启动时间、作用域）；`--all` 与单项目 `--project` 作用域重叠时仅启动告警不禁止。run 层锁语义不动。

已钉决策（用户已定语义 + 实现侧推定）：

- 锁文件位置 → `${EO_HOME:-$HOME/.eo}/sync-state/`（用户钉定）：`watch-all.lock`（--all 域）与 `watch-<project_name>-<hash8>.lock`（项目域，hash8 与簿记同源 = `repo_identity` SHA-256 前 8 位）
- 陈锁语义 → 复用既有 `acquire_lock`（flock 权威 + holder JSON + `STALE_LOCK_SECONDS`=600s 且 pid 死自清），不另写等价实现
- 互斥失败退出码 → 复用 `EXIT_LOCKED`(2)，与 run 层锁竞争口径一致（非零即满足用户要求）
- 裸 `watch`（无 --all/--project，按 cwd 解析项目）视同项目域——与同仓 `--project` 互斥（推定：裸 watch 语义上就是单项目 watch）
- 跨域重叠检测以 **flock 探测**为准（能非阻塞取到 = 无活锁，取到即放；holder JSON 仅用于提示文案）——不以文件存在性判活（释放不删文件，与 run 层一致）
- SIGTERM/SIGINT 退出 → try/finally 释放 flock（既有 SIGTERM→KeyboardInterrupt 转换路径复用）

## 2. 验收清单

- [x] AC-1 同作用域硬互斥：已有 `watch --all` 运行时再启 `--all`，或同 repo identity 的项目级 watch（`--project`/裸 watch）已运行时再启同仓项目级 watch → 第二个实例启动即以退出码 2 退出，报错信息含持有者 pid、启动时间与作用域描述（锁定：tests/test_eo_sync_watch_lock.py#test_all_scope_second_instance_exits_locked + #test_project_scope_mutex_same_repo_including_bare_watch，后者含异仓项目不互斥的反向断言）
- [x] AC-2 跨域重叠仅告警：`--all` 运行中启动单项目 watch（或反向）→ 打印重叠告警（含对方 pid）但正常启动进入轮询，不退出（锁定：tests/test_eo_sync_watch_lock.py#test_cross_scope_overlap_warns_but_both_run）
- [x] AC-3 陈锁自清：作用域锁文件的持有者 pid 已死且超过陈锁时限 → 新 watch 自动清理陈锁并成功启动（锁定：tests/test_eo_sync_watch_lock.py#test_stale_scope_lock_is_cleared_on_start，断言 holder pid 被接管）
- [x] AC-4 退出即释放：watch 收到 SIGTERM/SIGINT 退出后，同作用域 watch 可立即成功启动（锁不残留）（锁定：tests/test_eo_sync_watch_lock.py#test_signal_exit_releases_lock_for_next_start，SIGTERM 与 SIGINT 各一轮）
- [x] AC-5 零回归：run 层锁语义与既有 watch 行为不变——既有全套件测试保持绿（锁定：既有 tests/ 全套件，characterization 基线即绿——覆盖 run 锁矩阵（test_eo_sync.py）与 watch 集成行为（test_eo_sync_watch_integration.py））

---

独立复核：通过，2026-07-25，基线 632e3c1（复核者亲跑锁定套件 5/5 + 全套件 150/150 绿、锁定后测试零改动亲测、已钉决策六项逐条比对一致）

注记（复核 P2 观察，复核者明示可不处理）：`_warn_scope_overlap` 的 glob `watch-*.lock` 理论上可误匹配名字以 `watch-` 开头的项目的 run 层簿记锁（`watch-x-<hash8>.json.lock`），后果仅为一条多余的重叠告警，不影响互斥正确性。
