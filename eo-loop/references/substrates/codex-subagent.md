---
substrate: codex-subagent
适用: 总控运行在 Codex CLI 侧（eo-loop 被 Codex 加载执行）
updated: 2026-07-28
---

## 探测

运行环境即 Codex（`$` 前缀 skill 可用）即成立。总控在 Claude 侧而节点要 codex 模型的**跨侧**场景不属本基底——走 orca-orchestration。

## 派发

- skill 前缀是 **`$`**：`$eo-review <change 路径>`。任何时候不能写成 `/`
- prompt 遵守 SKILL.md 的最小输入；仅命中条件式 Execution Guard 时附即时控制包，不将控制包写成 `PROGRESS.md` 或其他状态文件
- 控制包要求仅 A 类随交付记录；命中 B / C 类时在变更前停止受影响工作，通过当前 Codex runtime 的 agent 消息能力发结构化求裁决信号；无可用消息能力则停止节点并以 `DECISION GATE` 结果返回，不得先采假设实施
- 子 agent / spawn 能力按 Codex 当前版本探测使用；不可用则降级为本会话顺序执行节点
- 模型与 effort 是启动参数、中途不可切——需要不同 effort 的节点分开派发
- **同角色跨轮次复用同一子会话**续发下一轮；机制上续不了则同参数重开，prompt 附上一轮报告路径作上下文补偿
- 并行组 worker（同层批 / 并行收敛组，SKILL.md ③）：一 worker 一独立现场（`git worktree add`）；无法隔离现场则不并行，降级串行

## 等待与观测

Codex 侧无完成自动唤醒时，总控主动轮询**产物**（frontmatter、台账、git log），间隔 ≥5 分钟；不向 worker 发消息催报。单窗 ≤30 分钟，到点发进度报告再续等。

## 回收

同 SKILL.md ③：读 change.md frontmatter 与 review/test 台账核验，不采信文字汇报；同时核证据角色、基线与节点契约要求的独立报告。Unknown B / C、证据探测后仍未知只触发停门；疑似判据违规但无独立结论时，按 SKILL.md 的 owner 规则派 eo-review / eo-test，总控不兼任实施、测试、审查。

## 已知陷阱

- (2026-07-19) `$` / `/` 前缀混写是 eo-flow 时期的历史高频错误，派发前自查一遍
