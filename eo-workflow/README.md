# eo-workflow

多 Agent 编排工作流技能。在 tmux 多窗格中自动编排 eo-* 技能流水线。

## 使用方式

```
/eo-workflow <phase> <spec-name> [loop-interval]
```

### 参数

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| phase | 是 | 执行阶段 | `spec` / `plan` / `implement` / `full` |
| spec-name | 是 | 功能目录名（kebab-case） | `writing-studio-foundation` |
| loop-interval | 否 | 监控轮询间隔，默认 `3m` | `5m` / `2m` / `10m` |

### 示例

```bash
# 只跑 spec → spec-review 循环
/eo-workflow spec user-auth

# 只跑 plan → plan-review 循环
/eo-workflow plan user-auth

# 跑 implement → test → review 循环（最常用）
/eo-workflow implement writing-studio-foundation

# 全流程（谨慎使用）
/eo-workflow full payment-retry

# 指定 5 分钟轮询间隔
/eo-workflow implement writing-studio-foundation 5m
```

## 各阶段流程

### spec（交互式）
```
用户在 spec pane 编写 → spec confirmed → 自动派发 spec-review → 有问题则暂停等用户修复 → 循环直到通过
```

### plan（交互式）
```
自动启动 eo-plan → plan confirmed → 自动派发 plan-review → 有问题则暂停等用户修复 → 循环直到通过
```

### implement（全自动）
```
eo-implement → eo-test → 失败则修复重测 → 全通过后 eo-review → 有问题则修复重审 → 循环直到通过
```

### full（全流程）
```
spec → plan → implement 依次衔接，阶段间自动标记 status: confirmed 并清理 review pane 上下文
```

## Pane 配置

启动脚本 `start-panes.sh` 中的 agent 和 model 参数**可按需修改**：

```bash
# ─── Agent 启动命令（可按需修改 model 和 reasoning effort）───────────────
CLAUDE_CMD="cd \"$CWD\" && claude --dangerously-skip-permissions"
CODEX_IMPLEMENT="cd \"$CWD\" && codex ... -m gpt-5.4 -c model_reasoning_effort=\"medium\""
CODEX_REVIEW="cd \"$CWD\" && codex ... -m gpt-5.4 -c model_reasoning_effort=\"xhigh\""
CODEX_TEST="cd \"$CWD\" && codex ... -m gpt-5.4 -c model_reasoning_effort=\"low\""
```

### 可配置项

| 配置 | 默认值 | 说明 |
|------|--------|------|
| Claude model | 默认 Claude（当前版本） | 修改 `CLAUDE_CMD` |
| Codex model | `gpt-5.4` | 修改各 `CODEX_*` 命令的 `-m` 参数 |
| implement effort | `medium` | 实现任务，平衡速度和质量 |
| review effort | `xhigh` | 审查任务，最高思考量级 |
| test effort | `low` | 测试任务，快速执行 |
| loop interval | `3m` | 启动时口头指定，如 `/eo-workflow implement xxx 5m` |

### Pane 布局

| Phase | Pane 数 | 布局 |
|-------|---------|------|
| spec / plan | 3（main + 交互 + review） | `even-horizontal`（等宽竖列） |
| implement | 4（main + implement + test + review） | `main-vertical`（main 左侧大列，右侧 3 行） |
| full | 6（全部） | `tiled`（均匀平铺） |

## 暂停与恢复

spec 和 plan 阶段的 review 发现问题时，工作流会**自动暂停** loop 并通知用户。用户处理完后在总控 pane 输入 `continue` 即可恢复。

implement 阶段全自动运行，超过 3 轮修复无进展时也会暂停等待人工介入。

## 文件结构

```
eo-workflow/
├── SKILL.md          # 主编排指令（Claude 加载）
├── start-panes.sh    # Pane 启动脚本
└── README.md         # 本文件
```
