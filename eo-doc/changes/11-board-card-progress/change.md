---
id: board-card-progress
seq: 11
title: 看板 card 承载进度与卡点
summary: card 详情改五 tab（含全文/journal 动态），卡面标质量门阶段轮次，≥3 轮警告样式
status: implementing
tier: light
type: feature
base_commit: 337f79f88693989355dde6b4306ad46fafe8098f
test_lock_commit: ffca52248b45d1a42b5a38044fa50bf0b7df1792
commits: []
issue: ~
created: 2026-08-02
---

# 看板 card 承载进度与卡点

意图：泳道 card 详情从长滚动改为多 tab 快速定位；eo-loop 半小时回报（journal）以「动态」tab 投影最近几条；卡片正面直接标当前质量门阶段与轮次，任一 ≥3 轮出警告样式，让卡点一眼可见。边界：终端形态与 backlog 卡详情不动。已钉决策见 brainstorm 记录 `brainstorm/2026-08-02-看板card承载进度与卡点.md`。

## 2. 验收清单

- [ ] AC-1 card 详情改为 tab 切换（概览｜清单｜质量门｜动态｜全文），点击 tab 直达对应内容、无需长滚动，原抽屉各节内容不丢；概览 tab 展示 change.md 完整 frontmatter 键值（缺失字段不占空行）；质量门 tab 顶部有「当前状态」区块（阶段/卡点/未决明细，无卡点显式空态）（人工:`eo-board --serve` 打开任一 change 卡详情，逐 tab 点一遍 → 过目内容齐全、概览含 frontmatter、质量门可见当前卡点）
- [ ] AC-2 全文 tab 以 mdBlock 迷你 markdown 渲染该 change 的 change.md 全文（覆盖 ATX 标题/表格/fenced code/列表与 task checkbox/分割线/粗体/行内代码/安全链接；链接仅 http/https/mailto 生成 href）（人工:全文 tab 与 IDE 打开的 change.md 对照 → 正文内容一致、上述结构可读）
- [ ] AC-3 有 journal（`tmp/eo/loop/<slug>/journal.md`）的 change，动态 tab 以时间逆序显示最近几条窗口报告（最新在上；条目正文 mdBlock 渲染、含「是否需要你裁决」行可读）；无 journal 的 change 动态 tab 显示空态提示且其余 tab 不受影响（锁定：tests/test_board_card_progress.py#JournalAndFullTextTests）
- [ ] AC-4 卡片正面可见当前所处质量门阶段与轮次（如 test ≈2 轮 / review P0×1），无需点开详情（人工:构造/选取 test、review 阶段各一 change → 过目卡面徽标；锁定：tests/test_board_card_progress.py#StageProgressTests）
- [ ] AC-5 任一质量门轮次 ≥3 的 change，卡片出现警告样式（复用现有 warn 视觉语言），在列中一眼可辨（人工:找一个轮次 ≥3 的 change → 过目警告样式与其余卡片的区分度；锁定：tests/test_board_card_progress.py#test_stage_warn_when_any_gate_rounds_ge_3）


独立复核：通过，2026-08-02，基线 5f03ee3
