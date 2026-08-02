---
id: loop-risk-triggered-verification
seq: 13
title: 将 eo-loop 核查改为风险触发
summary: eo-loop 仅在出现客观风险信号时升级核查
status: implementing
tier: full
type: enhance
base_commit: 618a8a3
plan_revision: 1
fix_rounds: 0
fix_consumed: []
commits: []
issue: ~
pr: ~
created: 2026-08-02
---

# 将 eo-loop 核查改为风险触发

## 速览

- **改什么**：eo-loop 不再默认核查或抽查其他 agent 的交付，只在出现客观风险信号时升级为针对性核查。
- **为什么**：一次偶发踩坑不应成为全部正常交付持续承担的固定流程成本，也不应让总控变成隐形的 implement、test 或 review。
- **行为差异**：之前每次 worker 交付都先走校验裁决，容易扩大成实质复核；之后正常交付只读取推进状态机所需的路由事实，命中风险信号才核查对应异常。
- **怎么验**：AC 5 条（人工 0 条）；用正常交付、风险交付和三种执行基底的静态口径断言验证。

## 1. 意图

将 eo-loop 的默认交付处理从“先校验、再裁决，绝不直接采信”调整为“读取路由事实并推进”。交付来自其他 agent、新 worker 或首次协作本身都不是风险信号，不触发首次、随机或按比例抽查。

loop 仍需消费 frontmatter、工件指针、基线和结构化处置等推进状态机必需的信息，但这属于路由职责，不等同于重新判断下游工作的实质正确性。只有出现可指认的冲突、缺失、越界或高风险变化时才升级核查；升级范围只覆盖触发信号，涉及代码、测试或审查的实质判断仍交给对应有权节点。

已钉决策（来自 brainstorming 捕获）：
- 默认核查策略 → 不核查、不抽查，只消费路由事实（理由：避免把偶发事件固化为永久流程税）。
- 抽查机制 → 不设置首次抽查、随机抽查、按比例抽查或 worker 信任分层（理由：保持 loop 精简清晰）。
- 升级条件 → 仅客观风险信号触发，不能以“来自其他 agent”或主观不信任代替（理由：让异常成本由异常承担）。
- 升级范围 → 只核风险信号对应范围，实质工作派给 implement、test、review 等有权节点（理由：保持总控职责单一）。
- 无信号但内容错误的归属 → 由节点契约及下游 test/review 发现；若形成系统性漏检，优先加强责任节点，而不是扩张 loop（理由：问题在最接近根因处修复）。

## 2. 验收清单

- [x] AC-1 当 worker 交付具备状态机推进所需的工件、基线和结构化处置，且未出现风险信号时，eo-loop 直接推进下一合法节点，不抽查或重新判断交付内容。
- [x] AC-2 worker 来自其他 agent、首次参与当前 change、使用新的可用执行基底或完成普通节点交接，本身均不触发首次、随机或按比例核查。
- [x] AC-3 当状态、工件与声明冲突，必要工件或字段缺失，基线过期或无法解析，节点权限/文件边界被越过，AC、测试锁、judge、安全、权限、数据或不可逆动作发生非预期变化，或 worker 主动上报未知、阻塞、决策门时，eo-loop 才升级核查；没有可指认信号时不得以主观怀疑触发。
- [x] AC-4 风险升级只核查触发信号对应的范围；需要判断实现、测试或 review 实质正确性时，eo-loop 派给对应有权节点，不自行复做，也不因一个局部信号扩大为全面核查。
- [x] AC-5 Claude 子 agent、Codex 子 agent 与 Orca 跨 agent 三种执行基底遵循同一边界：正常路径只提供路由事实，风险信号走针对性升级，缺失或冲突的必需路由事实不得被包装成可推进状态。

## 3. TODO

### Batch 1（MVP）

- [x] TODO-1 重写 eo-loop 的交付回收与裁决边界：默认只消费路由事实，明确非触发项、客观风险信号、针对性升级及与下游质量门的职责去重。（文件：修改: eo-loop/SKILL.md；对应 AC-1、AC-2、AC-3、AC-4）

### Batch 2

- [x] TODO-2 对齐执行基底模板及 Claude、Codex、Orca 三种基底的派发/回收措辞，移除无条件“不采信即核验”的口径，保留必需路由事实缺失或冲突时的风险升级。（文件：修改: eo-loop/references/substrates/_template.md、eo-loop/references/substrates/claude-subagent.md、eo-loop/references/substrates/codex-subagent.md、eo-loop/references/substrates/orca-orchestration.md；对应 AC-5）

### Batch 3

- [x] TODO-3 调整并补充 eo-loop 静态回归，正向锁定风险触发式升级，反向断言无抽查、无主观不信任触发、无总控实质复做，并覆盖所有执行基底口径。（文件：修改: tests/test_loop_execution_guard_caliber.py、tests/test_loop_fork_caliber.py、tests/test_loop_retest_routing_caliber.py；新增: tests/test_loop_risk_triggered_verification_caliber.py；对应 AC-1、AC-2、AC-3、AC-4、AC-5）
