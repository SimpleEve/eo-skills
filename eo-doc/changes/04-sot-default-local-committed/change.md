---
id: sot-default-local-committed
seq: 4
title: SoT 默认口径：新项目默认 local 且管理侧随仓库提交
summary: init 新项目默认 local 且管理侧随仓库提交，vault 仍可选，存量零改动
status: archived
tier: light
type: enhance
base_commit: f38eba2730491a24838784e38a392e905c7f4f2b
test_lock_commit: e94cffe9edabf32f5de21da8ab38e79624e4266b
commits: ["e94cffe", "fe2a7e3"]
issue: ~
created: 2026-07-25
---

# SoT 默认口径：新项目默认 local 且管理侧随仓库提交

意图：落实决策 `2026-07-24-obsidian-demoted-to-mirror`——SoT 收进仓库为默认：eo-project-init 对新项目默认推荐 local 模式，且管理侧（roadmap / backlog / decisions / lessons）随仓库提交（不再默认把 `.eo-project/` 写进 `.gitignore`）；vault 模式仍可选，存量项目零改动。纯 skill 文档口径翻转，无代码行为变化。

已钉决策（整体继承自上述 decision，不重问）：

- 新项目缺省推荐 local + 管理侧全部提交；「询问运行模式」保留，只翻转推荐项与缺省语义（SKILL.md「不要直接默认到 local」及选项 B「默认进 .gitignore」两处反向）
- 用户级 `default_mode` 显式配置仍作推荐项尊重；仅凭 `vault_root` 存在不再自动推断推荐 vault（假设，为「默认 local」的一致推论，未逐条确认）
- 存量不迁：1.5 更新/修复分支不再把 `.eo-project/` 列为 gitignore 缺项补写项——已 ignore 的保持、未 ignore 的保持，两个方向都零改动
- 隐私 `private/` 子目录约定出现真实需求再议，本 change 不预设

## 2. 验收清单

- [x] AC-1 新项目跑 `/eo-project-init`，运行模式询问中 local 为缺省推荐项（用户级 `default_mode` 显式配 vault 时推荐 vault 不变），local 选项描述为「管理侧随仓库提交，跟代码走」（锁定：tests/test_sot_default_caliber.py#TestAC1LocalIsDefaultRecommendation）
- [x] AC-2 选 local 后 `.eo-project/` 不写入 `.gitignore`，管理侧文件可正常提交；用户明确不想提交时可当场选择追加 ignore（缺省与可选项方向对调）（锁定：tests/test_sot_default_caliber.py#TestAC2NoDefaultGitignore）
- [x] AC-3 存量已初始化项目重跑 init（1.5 更新/修复分支）对 `.eo-project/` 的 ignore 状态零改动：既有 ignore 行不删除、未 ignore 且管理侧已提交的项目不被补写 ignore（锁定：tests/test_sot_default_caliber.py#TestAC3ExistingProjectsUntouched）
- [x] AC-4 config.md 运行模式对比表、GUIDE.md 模式表、README 协作段与 SKILL.md §10/约束节均为新口径，全仓 grep 无「`.eo-project/` 默认进 `.gitignore`」类旧口径残留；vault 模式描述不变（锁定：tests/test_sot_default_caliber.py#TestAC4NoOldCaliberResidue）

---

独立复核：通过，2026-07-25，基线 fe2a7e3（锁定测试 15/15 绿、测试文件锁定后零改动、四处口径互洽、无镀金、无溯源泄漏）
