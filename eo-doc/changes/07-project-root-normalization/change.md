---
id: project-root-normalization
seq: 7
title: project_root 相对路径与软链引用归一化
summary: 配置读取时把相对 project_root 按 repo root 解析并解软链，告警放行；解析不到仍报错
status: archived
tier: light
type: enhance
base_commit: 88105eacba0de454dc252109cfbc42e7bead852f
test_lock_commit: 70d871ad22809666ef5ea730192ea802fb91b819
commits: ["70d871a", "fa81025", "3804c04"]
issue: ~
created: 2026-07-25
---

# project_root 相对路径与软链引用归一化

意图：v1 遗留配置把 `project_root` 写成软链相对路径（真实复现：`/Users/debugeve/projects/Rabbit` 的 `.eo-project.json` 写 `"project_root": "eo-doc/vault"`，该路径是指向 vault 项目目录的软链），导致 `eo-board --register` 等所有 eo-* CLI 在配置校验处直接报「project_root 必须是绝对路径」而完全不可用——明明信息齐全、解析得出唯一正确目标，却被格式校验挡死。改为读取时归一化：相对路径按 repo root 解析并 realpath 解软链，成功即放行并告警建议固化；解析不出有效目录时保持现有报错（fail-closed 不丢）。同时 eo-project-init 的 1.5 更新/修复分支把这一形态列为可修项，重跑即回写绝对路径。

已钉决策（真实复现 + 实现侧推定）：

- 归一化范围 → **仅相对路径分支**做解析与 realpath；`project_root` 已是绝对路径时行为零变化（不解软链、不告警）——避免动既有项目的既有解析结果（用户口径「绝对路径零变化」）
- 解析基准 → **repo root**（`.eo-project.json` 所在目录），与 `doc_root` 的相对基准同源
- 失败判据 → 解析结果**不是已存在的目录**即视为失败（覆盖「目标不存在」与「软链悬空」），保持 ConfigError 且沿用原报错措辞主干，附解析尝试与失败原因
- 告警落点 → `stderr` 一行（用户口径），不进 stdout——`eo-board --html`/`--serve` 等 stdout 是数据通道，混入告警会污染输出
- 下游契约不变 → 归一化后 `merged["project_root"]` 仍是绝对路径字符串，所有消费方（eo-sync 簿记、eo-board 聚合、stub 投影）无需感知本变更
- init 1.5 修复动作 → 解析后**回写绝对路径**并提示；写回落点沿用既有规则（该顶层字段已在 `.eo-project.local.json` → 写 local，否则写 `.eo-project.json`）

## 2. 验收清单

- [x] AC-1 相对软链归一化并放行：`project_root` 写成相对 repo root 的路径（含指向 vault 的软链，如 Rabbit 的 `eo-doc/vault`）时，配置读取成功、解析出的绝对真实路径（软链已解引用）作为 `project_root`，并在 stderr 打印一行告警建议重跑 `/eo-project-init` 固化（锁定：tests/test_eo_lib_project_root.py#test_relative_symlink_project_root_resolves_and_warns + #test_relative_plain_dir_project_root_resolves + #test_local_override_relative_root_also_normalized）
- [x] AC-2 绝对路径零变化：`project_root` 已是绝对路径时，读取结果与改前逐字节一致（软链不解引用、无任何告警输出）（锁定：tests/test_eo_lib_project_root.py#test_absolute_project_root_unchanged_and_silent + #test_absolute_symlink_project_root_not_dereferenced，characterization 基线即绿——守护实施不越界解引用）
- [x] AC-3 解析不出目标仍报错：相对 `project_root` 指向不存在的路径、悬空软链或非目录时，仍抛出配置校验错误（不静默放行、不回落到相对值），报错含原路径（锁定：tests/test_eo_lib_project_root.py#test_relative_missing_target_still_fails_closed + #test_relative_dangling_symlink_fails_closed + #test_relative_pointing_to_file_fails_closed，characterization 基线即绿——守护归一化不过度放行）
- [x] AC-4 init 1.5 列为可修项：`eo-project-init/SKILL.md` 的 1.5 更新/修复分支把「project_root 非绝对路径/软链引用」列为可修项——解析后回写绝对路径并提示用户，回写落点沿用 local 优先规则（锁定：tests/test_eo_lib_project_root.py#InitRepairBranchCaliberTests）
- [x] AC-5 既有校验矩阵零回归：其余必填字段/mode 取值/doc_root 相对/sync 段类型的校验行为不变，既有全套件保持绿（锁定：tests/test_eo_lib_project_root.py#ExistingValidationMatrixTests + 既有 tests/ 全套件，均 characterization 基线即绿）

补充锁定（复核 P1 修复时追加，双向取证：两条在修复前 commit fa81025 上确认为 1 failure + 1 error）：
- 成环软链 / 含 NUL 的路径不穿透成裸 traceback → `#test_relative_symlink_loop_fails_closed`
- 校验与取值之间目标消失 → 取值处 fail-closed，绝不把字面量 `'None'` 传给下游 → `#test_target_vanishing_after_validation_fails_closed`

---

独立复核：通过，2026-07-25，基线 3804c04（首轮基线 fa81025 报 2×P1 + 2×P2，全部就地修复后增量复核通过；复核者以独立手法复验——自指/双环软链与 NUL 路径均得干净 ConfigError、patch `Path.is_dir` 复现 TOCTOU 确认已 fail-closed、旧 SKILL.md 套 HEAD 代码验证强化断言真会红、锁定用例仅一行被替换为更强断言无弱化、亲跑 18/18 与全套件 168/168 绿、Rabbit 真实配置解析正确且 stdout 干净）
