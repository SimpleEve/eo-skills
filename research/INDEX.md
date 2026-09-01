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
| 2026-08-21 | [agent 可观测性与 checkpoint](agent-observability-checkpoints.md) | checkpoint, 可观测性, output-styles, claude-code, devin, cursor, openhands, copilot-cca, 双模式汇报, 可打断 | 业界收敛于「默认推进+随时可打断+单事实源双层投影」——双模式输出走一处产出两处渲染，checkpoint 词义三方撞车需显式声明 |
| 2026-08-21 | [CodeGraph 召回能力与 worktree 索引](codegraph-recall-capability.md) | codegraph, mcp, 代码索引, recall, worktree, git-log, 文档停维护 | codegraph 类工具只索引当前代码快照不含 git 历史与意图——agent-handbook/state 可停维护但 recall 须 CodeGraph+git log+意图文档三段拼；worktree 索引按目录隔离、官方刻意不共享，各自 init（秒到分钟级） |
