# Research INDEX

> 消费方按 tags / summary 匹配，命中 ≤2 篇读正文相关节。引用时带上 `date`。
> 本批调研驱动的设计稿：[docs/tier-design.md](../docs/tier-design.md)

| 日期 | 标题 | tags | summary |
|------|------|------|---------|
| 2026-07-18 | [竞品条目粒度](change-granularity-competitors.md) | 粒度, 竞品, spec-kit, openspec, kiro, taskmaster, bmad, ac, task | 五家竞品无一在 AC 行内嵌验证方式、无一有独立「涉及文件」节，单条 TODO 级完成判据是孤例——驱动 change 条目三处瘦身 |
| 2026-07-18 | [test-as-spec / TDD](tdd-test-as-spec.md) | tdd, test-as-spec, reward-hacking, 验收, ac, bdd | test-as-spec 不取消书面 AC 而是给它归宿——五类验收测试承接不了，且作弊唯一有效解药是独立复核而非提示词 |
| 2026-07-18 | [去 spec 化论战与分层判据](spec-artifact-debate.md) | sdd, 论战, 分层判据, 工件, 事后探针, 收敛 | 去 spec 化论战收敛于「按风险分档」而非单向变轻——工件唯一不失效的职能是独立验证的基准，分层靠事后探针不靠事前估计 |
| 2026-07-18 | [issue 直派模式](issue-dispatch-model.md) | issue直派, copilot-cca, devin, 质量门, pr-review, 轻量档 | 工业级无 spec 直派省的是 TODO 不是 AC——工件从 per-change 挪到 per-repo + per-PR，代价是 44% 的工作静默蒸发 |
| 2026-07-18 | [常驻项目上下文层](resident-context-layer.md) | 常驻上下文, claude-md, steering, memory-bank, adr, prompt-debt, 注入检索 | 常驻层从未承担单次变更意图职能且只是建议不是约束——change 变薄时抽掉的意图必须显式指定去处，P0 约束必须配确定性检查 |
