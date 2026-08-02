---
substrate: orca-orchestration
适用: 节点要跨 agent 运行（执行者与总控不是同一 agent/模型栈），且需要总控监督
updated: 2026-07-28
---

## 探测

1. **先加载 `orchestration` skill 本体**（Claude 侧用 Skill 工具调 `orchestration`，codex 侧 `$orchestration`），加载完成前不得敲任何 `orca orchestration` 命令。本文件不是命令手册，只是 eo-loop 场景的增补与陷阱清单——命令契约、生命周期语义（worker_done 自动完结、handle 解析、preamble 规则）一律以 skill 本体为准，两边冲突时信 skill 并回修本文件。
2. `orca status --json` 显示 runtime 运行中，且 orchestration 实验特性已开启。失败 → 向用户提示启动 Orca 或换基底。

## 派发

1. **总控身份钉桩**（每次派发前、每个等待窗开始时重做）：按自己的 `$ORCA_PANE_KEY`（= `tabId:leafId`，跨 Orca 重启稳定）从 terminal list 解析自己 pane 的**当前** handle：

   ```sh
   COORD=$(orca terminal list --json | jq -r --arg pk "$ORCA_PANE_KEY" '.result.terminals[] | select((.tabId + ":" + .leafId) == $pk) | .handle')
   ```

   后续收发一律显式带 `$COORD`，**禁用隐式身份解析**（省略 `--from`/`--terminal` 时 CLI 按 `$ORCA_TERMINAL_HANDLE` 环境变量解析——那是会话启动时烙死的，Orca 重启后即过期，见陷阱节）
2. `orca orchestration task-create --spec "<节点目标 + change 路径 + 收敛标准>"`；命中 SKILL.md 的条件式 Execution Guard 时，把即时控制包一并放进 spec，不额外落盘，并要求 worker 仅随交付记录 A 类、B / C 类在变更前发 `decision_gate` 后暂停
3. 建 worker 终端：implement / test / review 依赖当前工作区状态，用 `orca terminal create --worktree active --command "<agent 启动命令>"`；自定义模型/effort 写进启动命令（如 `codex --dangerously-bypass-approvals-and-sandbox -m <model> -c model_reasoning_effort="high"`——codex 不带 bypass 会每步卡权限审批）
4. `orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000` 就绪后 `orca orchestration dispatch --task <id> --to <handle> --from $COORD --inject`
5. **轮次复用**：`worker_done` 后 worker 停在 agent 提示符，正好接下一轮——同角色新任务 `task-create` 后 `dispatch --to <同一 handle> --inject` 续用同一终端，不重建。模型/effort 是启动参数，复用即锁定该组合；要换模型才重建终端（handle 报 stale 时 `terminal list` 重解析后仍按原终端续用）
6. **并行组 worker**（同层批 / 并行收敛组，SKILL.md ③）：一 worker 一独立 Orca child worktree 起终端，**不得共用 active 工作区**；合流 checkpoint 按 granularity §6 指派其一执行合并

## 等待与观测

每窗开始先重做「派发」第 1 步的身份钉桩（Orca 若重启过，handle 已漂移），然后 `orca orchestration check --wait --terminal $COORD --types worker_done,escalation,decision_gate --timeout-ms 1800000`——只等**必要信号**（完成 / 升级 / 求裁决），**不要求 worker 发 heartbeat**（dispatch 注入的 preamble 之外不追加任何回报要求，worker 专注任务）。窗口超时不是 worker 失败：总控主动观测——`terminal read` 看输出、`tui-idle` 探活、读台账增量——活着就发进度报告进下一窗。禁止 sleep 轮询。收到 `decision_gate` / `ask` 用 `reply` 应答后继续等。

## 回收

`worker_done` 的 payload 只当线索；证据核验一律读 change.md frontmatter 与 review/test 台账，并按 SKILL.md 核证据角色、基线与节点契约要求的独立报告。review-only 的 `worker_done` 不授权总控动手修——修复派回 eo-implement 模式二；Unknown B / C 或证据探测失败同样只停门。疑似判据违规但无独立结论时，按 SKILL.md 的 owner 规则派 eo-review / eo-test。

## 已知陷阱

- (2026-07-19) 终端有输出 ≠ 完成，不要据此杀 worker 重派；长任务 15-60 分钟是常态
- (2026-07-19) terminal handle 重启后会变，报 `terminal_handle_stale` 时用 `terminal list` 重解析；绝不用 handle 对比判归属
- (2026-07-19) 同一 task 连败 3 次会被 runtime 熔断置 failed——第 2 次失败就该停下向用户报卡点，别撞到熔断
- (2026-07-25) **claude TUI worker 的注入/提交竞态**（codex 弹窗吞注入的姊妹陷阱）：dispatch --inject 后立刻补回车会**跑在注入文本前面**——空回车先落、任务文本后到，文本干坐输入框永不执行；有时注入整体被吞（框内空无一物）。标准姿势：dispatch 后先 `terminal read` 验证任务文本**已在框内**再 `send --enter`；框内为空 = 注入被吞，用 task-list 取 spec 原文 `terminal send --text "<spec>" --enter` 补投（附 worker_done 上报命令）。另：claude worker 终端在完成一轮 worker_done 后常变 terminal_not_writable——轮次复用前先探测，不可写即重建终端重派
- (2026-07-24) codex 终端刚创建即 dispatch --inject，注入会被启动期的目录信任弹窗吞掉（dispatch 状态仍显示成功）：必须先 `terminal wait --for tui-idle` **满足**（satisfied:true）再 dispatch；已被吞时任务卡 dispatched 态无法重派，救法 = `terminal send --enter` 手动补投任务文本（附 worker_done 上报命令，--to 填总控终端 handle）
- (2026-07-24) worker_done 未必自动完结任务：skill 本体口径是**有效** worker_done 会自动置 completed；总控收信身份脱节时（见下条）runtime 关联不上就不会。同终端派下一轮前先 `task-list` 核对上轮状态，仍卡 dispatched 才手动 `task-update --id <上轮task> --status completed` 兜底（合法状态枚举：pending/ready/dispatched/completed/failed/blocked，没有 done）
- (2026-07-24) **隐式身份解析的真实机制与失效条件**（受控实验实证，修正本条早先「每次 Bash 调用都不可信」的错误结论）：省略 `--from`/`--terminal` 时 CLI 按 `$ORCA_TERMINAL_HANDLE` 环境变量解析身份——该值会话启动时烙死、同会话所有 Bash 子进程恒定（解析是**确定性**的，不随调用漂移），Orca 重启后 pane 换发新 handle 而 env 不更新，即过期。runtime 对死 handle 的收发**静默成功**（check 返回空、send 照收，零报错），过期后自动解析 = 稳定守着死信箱瞎等。最危险的是**混用**：dispatch 按 terminal list 显式解析活 handle、check 靠 env 自动解析死 handle，收发指向两个信箱——worker 回包完好排队、任务正常自动完结，总控却永远收不到。pull 模型信件永久排队：身份钉对后迟到的 check 也能全量补收，「监听没在场所以错过」不成立、唯一致死因就是身份不对。防治即「派发」第 1 步身份钉桩；`inbox`（跨收件人非消费）兜底审计；task-list+git 工件为完成判据的持久真相。另：check 消费型语义，同一时刻只留一个监听，起新先杀旧。
