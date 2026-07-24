---
substrate: orca-orchestration
适用: 节点要跨 agent 运行（执行者与总控不是同一 agent/模型栈），且需要总控监督
updated: 2026-07-19
---

## 探测

`orca status --json` 显示 runtime 运行中，且 orchestration 实验特性已开启。失败 → 向用户提示启动 Orca 或换基底。

## 派发

1. `orca orchestration task-create --spec "<节点目标 + change 路径 + 收敛标准>"`
2. 建 worker 终端：implement / test / review 依赖当前工作区状态，用 `orca terminal create --worktree active --command "<agent 启动命令>"`；自定义模型/effort 写进启动命令（如 `codex --dangerously-bypass-approvals-and-sandbox -m <model> -c model_reasoning_effort="high"`——codex 不带 bypass 会每步卡权限审批）
3. `orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000` 就绪后 `orca orchestration dispatch --task <id> --to <handle> --inject`
4. **轮次复用**：`worker_done` 后 worker 停在 agent 提示符，正好接下一轮——同角色新任务 `task-create` 后 `dispatch --to <同一 handle> --inject` 续用同一终端，不重建。模型/effort 是启动参数，复用即锁定该组合；要换模型才重建终端（handle 报 stale 时 `terminal list` 重解析后仍按原终端续用）
5. **并行组 worker**（同层批 / 并行收敛组，SKILL.md ③）：一 worker 一独立 Orca child worktree 起终端，**不得共用 active 工作区**；合流 checkpoint 按 granularity §6 指派其一执行合并

## 等待与观测

`orca orchestration check --wait --types worker_done,escalation,decision_gate --timeout-ms 1800000`——只等**必要信号**（完成 / 升级 / 求裁决），**不要求 worker 发 heartbeat**（dispatch 注入的 preamble 之外不追加任何回报要求，worker 专注任务）。窗口超时不是 worker 失败：总控主动观测——`terminal read` 看输出、`tui-idle` 探活、读台账增量——活着就发进度报告进下一窗。禁止 sleep 轮询。收到 `decision_gate` / `ask` 用 `reply` 应答后继续等。

## 回收

`worker_done` 的 payload 只当线索；证据核验一律读 change.md frontmatter 与 review/test 台账。review-only 的 `worker_done` 不授权总控动手修——修复派回 eo-implement 模式二。

## 已知陷阱

- (2026-07-19) 终端有输出 ≠ 完成，不要据此杀 worker 重派；长任务 15-60 分钟是常态
- (2026-07-19) terminal handle 重启后会变，报 `terminal_handle_stale` 时用 `terminal list` 重解析；绝不用 handle 对比判归属
- (2026-07-19) 同一 task 连败 3 次会被 runtime 熔断置 failed——第 2 次失败就该停下向用户报卡点，别撞到熔断
- (2026-07-24) codex 终端刚创建即 dispatch --inject，注入会被启动期的目录信任弹窗吞掉（dispatch 状态仍显示成功）：必须先 `terminal wait --for tui-idle` **满足**（satisfied:true）再 dispatch；已被吞时任务卡 dispatched 态无法重派，救法 = `terminal send --enter` 手动补投任务文本（附 worker_done 上报命令，--to 填总控终端 handle）
