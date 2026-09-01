---
substrate: claude-subagent
适用: 总控是 Claude Code，节点执行者也是 Claude（自调自）
updated: 2026-07-28
---

## 探测

Claude Code 会话内 Agent 工具原生可用，恒成立。模型按偏好或用户指定通过 model 参数传入（不指定则继承会话模型）。

## 派发

- 一**角色**一后台子 agent（起名如 `impl-<slug>` / `review-<slug>`，便于 SendMessage 寻址），跨轮次复用。首派 prompt 给四样：加载哪个 eo-* skill、change 目录路径、本轮收敛标准、必要输入（如 review 反馈路径）；命中 SKILL.md 的条件式 Execution Guard 时再附其即时控制包，不落独立文件
- 控制包要求 worker 仅把 A 类选择随交付记录；命中 B / C 类时在变更前停止受影响分支，通过 SendMessage 向总控发结构化求裁决信号（类别、分叉、影响、推荐），等总控回灌裁决后再续原 agent
- **轮次复用 = SendMessage 发回原 agent**：修复轮、增量复审、打回重做、追问，一律续原上下文，不重开新 agent；重建时机见 SKILL.md 复用纪律
- 相互独立的节点（如同一基线上的 test 与 review）才并行；并行 >2 个先报预算等点头
- 并行组 worker（同层批 / 并行收敛组，SKILL.md ③）：spawn 时启用 worktree 隔离（Agent 工具 `isolation: worktree`），一 worker 一现场；合流 checkpoint 按 granularity §6 指派执行

## 等待与观测

后台子 agent 完成会自动唤醒总控（harness 级信号，无需 worker 配合），这是主信号。10 分钟兜底窗口：等待期挂起必须带超时（定时唤醒 / Monitor 均可）。窗口内观测**只读产物不打扰 worker**：change.md 勾选、review/test 台账增量、git log——不 SendMessage 问「进展如何」（打断即污染 worker 上下文）。到点发进度报告再续等。

## 回收

完成通知只用于唤醒总控和定位产物。正常路径按 SKILL.md ③ 读取 frontmatter 当前状态、预期工件指针、当前基线与最新结构化处置后直接路由，不打开完整 diff、不抽查或复做节点内容。只有这些事实缺失 / 冲突、出现可观察越界、计划外判据变化、Unknown B / C 或证据探测失败等客观风险信号时，才针对对应异常升级；需要实质判断就派 eo-review / eo-test，不由总控补做节点工作。

## 已知陷阱

> 本节只放出厂陷阱；运行时陷阱记在 `~/.eo-skills/loop/preferences/` 的「已知陷阱」节（前缀 `[claude-subagent]`），一并读。

- (2026-07-19) 子 agent 上下文独立：prompt 里不给 change 路径它就会自己猜——路径必给
- (2026-07-19) 用词锚定：prompt 写「看看 / 检查一下」会弱化执行强度——用节点本义动词（审查 / 实施 / 验证）
- (2026-07-24) Agent 工具偶发 teammate pane 创建超时（「Timed out waiting for the Orca runtime / tmux split pane handle」，orca status 却显示 ready、CLI 建终端正常）：重试 2 次仍失败即切换基底——orca 终端跑 `claude --model <id> --dangerously-skip-permissions`，走 orca-orchestration 的 task/dispatch 流程，模型钉住不变
