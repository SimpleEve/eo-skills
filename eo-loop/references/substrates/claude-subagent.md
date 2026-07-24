---
substrate: claude-subagent
适用: 总控是 Claude Code，节点执行者也是 Claude（自调自）
updated: 2026-07-19
---

## 探测

Claude Code 会话内 Agent 工具原生可用，恒成立。模型按偏好或用户指定通过 model 参数传入（不指定则继承会话模型）。

## 派发

- 一**角色**一后台子 agent（起名如 `impl-<slug>` / `review-<slug>`，便于 SendMessage 寻址），跨轮次复用。首派 prompt 只给四样：加载哪个 eo-* skill、change 目录路径、本轮收敛标准、必要输入（如 review 反馈路径）
- **轮次复用 = SendMessage 发回原 agent**：修复轮、增量复审、打回重做、追问，一律续原上下文，不重开新 agent；重建时机见 SKILL.md 复用纪律
- 相互独立的节点（如同一基线上的 test 与 review）才并行；并行 >2 个先报预算等点头
- 并行组 worker（同层批 / 并行收敛组，SKILL.md ③）：spawn 时启用 worktree 隔离（Agent 工具 `isolation: worktree`），一 worker 一现场；合流 checkpoint 按 granularity §6 指派执行

## 等待与观测

后台子 agent 完成会自动唤醒总控（harness 级信号，无需 worker 配合），这是主信号。30 分钟兜底窗口：等待期挂起必须带超时（定时唤醒 / Monitor 均可）。窗口内观测**只读产物不打扰 worker**：change.md 勾选、review/test 台账增量、git log——不 SendMessage 问「进展如何」（打断即污染 worker 上下文）。到点发进度报告再续等。

## 回收

不采信子 agent 的文字汇报——按 SKILL.md ③ 读 change.md frontmatter、review/test 台账、AC 勾选核验状态推进。

## 已知陷阱

- (2026-07-19) 子 agent 上下文独立：prompt 里不给 change 路径它就会自己猜——路径必给
- (2026-07-19) 用词锚定：prompt 写「看看 / 检查一下」会弱化执行强度——用节点本义动词（审查 / 实施 / 验证）
