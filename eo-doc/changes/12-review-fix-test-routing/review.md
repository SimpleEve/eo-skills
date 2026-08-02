---
title: 按测试影响路由 Review 修复代码审查报告
change_id: review-fix-test-routing
tags: [eo-loop, eo-review, eo-test, eo-archive, workflow]
created: 2026-08-02
updated: 2026-08-02
status: active
summary: >
  首轮审查通过：五条 AC 与五项 TODO 均被协议和静态回归覆盖，未发现 P0/P1/P2；
  本 change 无正式 Test 历史且无待验 heavy AC，测试证据处置为不适用。
---

# 按测试影响路由 Review 修复 代码审查报告

> 关联 Change：[change.md](change.md)（检查表：其 §2 验收清单 AC-1~5）
> 首轮审查日期：2026-08-02 ｜ 审查范围：`4374c8b..6f5e408`，覆盖 eo-loop、eo-implement、eo-test、eo-review、eo-archive、共享约定、报告模板与静态回归
> ⚠️ 首轮之后正文各节为历史快照——当前状态以「Finding 台账」与末尾「速报」为准

## Finding 台账

| ID | 级别 | 摘要 | 位置 | 状态 | 根因 | 首见/最近轮 | 基线/修复 commit |
|----|------|------|------|------|------|-------------|------------------|
| — | — | 无 finding | — | — | — | — | `6f5e408` / — |

## 审查总结（首轮快照）

实现把原先可能被机械重放的 `Implement → Test → Review` 拆成按反馈来源和证据新鲜度路由的非对称回路：Review 反馈先由原 reviewer 增量复审，只有既有 Test 证据失效时才回原 tester；Test FAIL 则始终优先回原 tester 核销。统一交付基线 `H` 同时纳入业务代码与测试资产，Test / Review 的新鲜度键统一为 `(plan_revision, H)`，Loop 与 Archive 均只消费结构化证据，不越权自行判断。

角色权限、报告字段、状态恢复边界及 fail-closed 条件在共享约定和五个节点 skill 中保持一致。定向复验要求可追溯的通过来源轮、明确的重跑/沿用分区以及 `I ⊆ R` 覆盖证明；影响无法圈定、触及 heavy 面或来源链残缺时升级完整复验。归档门能拒绝过期 Review、未消费的复验路由、残缺定向来源链与未纳入基线的测试资产，未发现可绕过证据门的路径。

验证证据：在精确提交树 `6f5e408` 上重跑 `tests.test_loop_retest_routing_caliber`，26/26 通过；实施阶段精确提交树全仓验证为 288/288，通过两轮独立协议审查及反向 mutation 探针。diff 未引入流程溯源型代码注释，也未发现无法映射到 AC/TODO 的行为扩面。

## P0 - 必须修复（阻塞性问题）

无。

## P1 - 建议修复（重要但不阻塞）

无。

## P2 - 可选优化（锦上添花）

无。

## 验收标准覆盖检查

| AC 编号 | 描述 | 状态 |
|---------|------|------|
| AC-1 | Review 修复后先走 Implement ↔ 原 Reviewer 短回路，可证明沿用时不启动 Test | ✅ 通过：Loop 收敛规则、Implement 权限边界、Review 结构化签署与免测负向断言形成闭环 |
| AC-2 | 有限影响只做定向复验，并记录重跑范围与沿用范围 | ✅ 通过：Tester 分流、来源链、证据分区和当前基线组合结论均有静态锁定 |
| AC-3 | heavy/共享面/不确定影响进入完整复验，缺失或含糊时 fail-closed | ✅ 通过：完整复验触发集合与无效基线、缺失处置负向用例均已覆盖 |
| AC-4 | Test FAIL 始终回原 Tester，之后 Review 覆盖最后交付提交 | ✅ 通过：Loop、Implement、Test 状态恢复边界及原 Reviewer 回收路径保持一致 |
| AC-5 | Archive 仅接受当前 Test 或当前 Review 签署的旧证据沿用 | ✅ 通过：归档门校验 revision、H、来源轮、定向覆盖、测试资产提交及复验消费关系 |

## TODO 完成度检查

| TODO | 描述 | 状态 |
|------|------|------|
| TODO-1 | 共享约定中的非对称回路、权限与 fail-closed 规则 | ✅ 完成 |
| TODO-2 | Implement 影响候选与 Reviewer 独立测试证据处置 | ✅ 完成 |
| TODO-3 | Loop 路由及 Test 定向/完整复验结构化记录 | ✅ 完成 |
| TODO-4 | Archive 当前基线与沿用证据新鲜度门 | ✅ 完成 |
| TODO-5 | 跨文件静态回归与误绿探针 | ✅ 完成 |

## 架构与边界核对

| 核对项 | 结论 |
|--------|------|
| 单一规则源 | ✅ 状态与回退边集中于 `eo-shared/conventions.md`，各节点只声明自身职责 |
| 角色隔离 | ✅ Implement 只给影响候选；Reviewer 决定沿用/复验；Tester 决定复验范围；Loop 机械路由 |
| Test FAIL 优先级 | ✅ 未核销 FAIL 不能被 Review 的沿用签署绕过 |
| 新鲜度 | ✅ Test 与 Review 均以 `(plan_revision, H)` 为键，测试资产推进同一交付基线 |
| 定向证据完整性 | ✅ 来源轮、祖先关系、重跑/沿用分区和影响覆盖均可机械校验 |
| 归档兼容性 | ✅ 无历史 Test 且无待验 heavy AC 的既有放行语义保持不变 |

## 第 1 轮记录（revision 1 · 2026-08-02）

- 审查基线：`revision 1, H=6f5e408`
- 核销：无
- reopen：无
- 新增：无
- 测试证据处置：不适用
- 既有通过 Test：无；当前交付基线：`6f5e408`
- 受影响 AC / 测试：无
- 依据：本 change 从未运行正式 eo-test、没有 `test.md`，且 AC-1~5 均为无需起环境的静态可验证项并已全部勾选，无待验 auto-heavy AC
- 本轮结论：通过

## 速报

结论：通过（P0 0 条，P1 0 条，P2 0 条）［第 1 轮 · revision 1 · 基线 `6f5e408`］
测试证据处置：不适用
既有通过 Test：无；当前交付基线：`6f5e408`
受影响 AC / 测试：无；依据：从未运行正式 eo-test，且无待验 heavy AC
下一步：可进入 /eo-archive review-fix-test-routing
