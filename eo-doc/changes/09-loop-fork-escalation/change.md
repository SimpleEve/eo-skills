---
id: loop-fork-escalation
seq: 9
title: 补 eo-loop 分叉上报机制
summary: worker 不问用户但形态分叉须清单上报，总控攒成封闭选择转达用户后回灌
status: implementing
tier: light
type: enhance
base_commit: 6998899d55eba93a0e3a0335a4e013780c298796
test_lock_commit: e2d0601f728ace75259af3389b22e542f7acefb5
commits: []
issue: ~
created: 2026-07-25
---

# 补 eo-loop 分叉上报机制

意图：loop 纪律「worker 不向用户提问」把下游 skill 的澄清环节整体关死——C9 起草时用户举例措辞被 worker 当定稿、菜单/术语/视觉分叉被假设静默吃掉，事后才补对齐（用户拍板于 2026-07-25 C9 复盘，本 change 为其规范化沉淀）。补进 eo-loop 规范：派发纪律要求 worker 把「本应问用户的分叉 + 所采假设」清单化随交付上报；总控把清单攒成一次封闭选择转达用户，裁决随修订轮回灌；圈线段时「比如/之类」等举例措辞判为形态未定稿，先探针再派。

## 2. 验收清单

- [x] AC-1 eo-loop/SKILL.md「派发 prompt 纪律」含分叉上报条款：含形态自由度的节点，须令 worker 把「本应问用户的分叉 + 各自所采假设」以清单随交付上报（锁定：tests/test_loop_fork_caliber.py#TestAC1DispatchPromptForkReporting）
- [x] AC-2 eo-loop/SKILL.md「③派发与校验裁决」含总控汇总条款：把分叉清单攒成一次封闭选择转达用户，用户裁决随修订轮回灌（锁定：tests/test_loop_fork_caliber.py#TestAC2CoordinatorBatchesForksToUser）
- [x] AC-3 eo-loop/SKILL.md「①圈线段」含举例措辞判据：用户意图含「比如/之类」等举例措辞 = 形态未定稿，先探针对齐再派实施（锁定：tests/test_loop_fork_caliber.py#TestAC3ExampleWordingIsNotFinal）
- [x] AC-4 eo-loop/references/substrates/_template.md 派发节含分叉清单提示位（锁定：tests/test_loop_fork_caliber.py#TestAC4TemplateDispatchSlot）
