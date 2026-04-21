---
name: eo-flow
description: |
  单点 handoff：把 eo-* 任务（review/test/implement/change-review/spec-review）甩给 tmux 里的 codex pane 执行，回包后决定"甩回去修"或"暂停问用户"。触发：eo-flow / 甩给 codex / /eo-flow。
  NOT FOR: 完整流水线（用 /eo-workflow）。
---

# eo-flow — Claude ↔ Codex 一次性 handoff

## 前置

**必须能找到 `.eo-project.json`**。找不到 → 报错退出，提示运行 `/eo-project-init`。codex pane 中执行的下游 skill 自己也会检查。

## 定位

- `/eo-workflow` = 多 pane 全流程编排（cron / 状态机 / 自动流转）——重
- `/eo-flow` = **单点 handoff**：「当前上下文这件事，甩给 codex，我等你回来决策」——轻

不是 pipeline，只负责一个动作。

## action 映射表（写死）

| action | codex skill | effort | pane label |
|--------|-------------|--------|-----------|
| `review` | `$eo-review` | high | `review-$P` |
| `test` | `$eo-test` | medium | `test-$P` |
| `implement` | `$eo-implement` | high | `impl-$P` |
| `spec-review` | `$eo-spec-review` | high | `review-$P` |
| `change-review` | `$eo-change-review` | high | `review-$P` |
| `fix` | `$eo-implement`（附反馈） | high | `impl-$P` |

⚠️ **`fix` 只用于 `review → 代码修订` 这一条路径**。`spec-review` / `change-review` 的修订是文档修订（改 `spec.md` / `change.md`），不派发 codex，本 pane 内联改（见第 4 步分叉）。

`$P` = 项目短名，从 `git rev-parse --show-toplevel` 或 CWD basename 取，超 12 字符截断，且只保留 `[a-zA-Z0-9_-]`（避免特殊字符破坏 tmux-bridge 解析）。多项目挂同 tmux session 时，label 带作用域（`review-rabbit` vs `review-kitten`）自然不冲突。

## Codex 调用关键事实

1. **skill 前缀是 `$` 不是 `/`**：`$eo-review <path>` / `$eo-implement <path>`。任何时候不能弄反。
2. **启动命令必须带 `--dangerously-bypass-approvals-and-sandbox`**，否则每步卡权限：
   ```
   codex --dangerously-bypass-approvals-and-sandbox -m gpt-5.4 -c model_reasoning_effort="<effort>"
   ```
3. **effort 是启动参数，不能中途切**——所以**按 action 分 pane**（`impl-$P` / `test-$P` / `review-$P` 各自固定一档），label 就是 effort 隔离边界。

## 执行思路（不是流程脚本）

### 1. 识别目标

从上下文推断要 handoff 的目标（最近在聊的 change.md / spec.md / TODO 勾选区域）。推不出来再问用户一次。

### 2. 找 / 起 codex pane（自动）

`tmux-bridge list` 找匹配 label 的 pane：
- 已存在 → 用
- 不存在 → **自动 split 新 pane**（不问用户），跑上面的 codex 启动命令
- 存在但进程挂了 → `send-keys` 重发启动命令（不 kill pane）

建完 `tmux select-layout -t <window> tiled` 均匀重排，避免新 pane 被挤成缝。

⚠️ **关键坑：所有 tmux 操作必须显式 `-t` 锚到 `$TMUX_PANE`**。不带 `-t` 的 `tmux display-message` / `split-window` 解析到的是"当前 client 的 active window"——ghostty / iTerm 多开窗口挂同 session 时，用户聚焦在别的 tab，新 pane 就会建到别人 tab 里。`$TMUX_PANE` 是 tmux 注入到每个 pane 的环境变量，永远指向运行代码的那个 pane。

```bash
SELF_PANE="${TMUX_PANE:?not inside tmux}"
WINDOW="$(tmux display-message -p -t "$SELF_PANE" '#{window_id}')"
# split-window / select-layout 全部 -t "$WINDOW"
# split 后校验 tmux display-message -p -t "$PANE_ID" '#{window_id}' == "$WINDOW"，偏了就 kill-pane 回滚
```

**Label 设置必须校验**：`tmux-bridge name` 会静默失败。建完立即 `tmux-bridge resolve <label>` 反查，返回值 ≠ `$PANE_ID` 就当作失败处理。先 resolve 再 split——已有同 label 的 pane 直接复用，别重复创建。

label 只准 `[a-zA-Z0-9_-]`，括号/空格/中文会让 tmux-bridge 解析崩。

例外：用户明确说过"不要新开 pane"才回退到"提示用户自起"。

### 3. 派发指令（必须注入回包合约）

**核心约束：eo-* skill 本身不懂 smux**（它们要能在没 tmux 的机器上独立跑），所以"通知另一个 pane 回包"这件事必须由 eo-flow 在**每次派发的附言里**手动注入。别去改 eo-* skill 的 SKILL.md 加回包逻辑，那是职责混乱。

派发前拿本 pane 标识（**绝不硬编码 `"claude"`**，用户可能同时开多个 claude pane）：

```bash
CALLBACK="$(tmux-bridge id)"   # %N 形式的 pane-id
```

附言末尾字面追加（不翻译）——**三步必须全执行，少一步就卡在对方输入框里没提交**：

```
【回包合约】完成后依次执行（缺一不可）：
1) tmux-bridge read <CALLBACK> 5
2) tmux-bridge message <CALLBACK> "done: <action> @ <目标> → <产出文件>"
3) tmux-bridge keys <CALLBACK> Enter
第 3 步的 Enter 是提交键——漏掉就只是把字打到对方 prompt 里不会触发回调。这三步必须是 shell 里最后动作，否则视为未完成。
```

走 `/smux` 的 read-act-read 四段把这整条指令发到 codex pane，然后**立刻告知用户**派了什么、在等哪个 pane 的回包。停手。

### 4. 收到回包后决策分叉

codex 按合约会回 `[tmux-bridge from:... ] done: ...` 到本 pane。**必须读产出文件**（不要只看回包字面）：

| action | 读什么 |
|--------|-------|
| review / spec-review / change-review | 对应 `*-review.md` |
| test | `test.md` |
| implement / fix | `git diff` + change.md 的 TODO 勾选 + 可选 `implement.md` |

**分叉判据**（先按上游 action 选路径，再按问题性质选档位）：

**路径选择**（fix 的载体取决于上游 action）：

| 上游 action | 客观修订走哪 | 为什么 |
|------------|-------------|-------|
| `review` | 甩 `$eo-implement`（`/eo-flow fix`，异步 codex） | 改代码，量大、需执行环境 |
| `change-review` | **本 pane 内联改 `change.md`** | 文档修订，量小；且 `$eo-implement` 不消费 `change-review.md` |
| `spec-review` | **本 pane 内联改 `spec.md`** | 同上；`$eo-spec` 是新建流程，不适合小幅修订 |

内联改之前，先标出有决策空间的条目（命名、抽象粒度、策略选择）给用户确认，纯字面/规范校订直接改。改完告知用户"已内联修订 X 条，另 Y 条待你定"。

**档位选择**（在上游路径之上，决定自动 or 停手）：

- **自动修**（按上面路径走）：明确 P0 bug、测试失败、AC 未覆盖、规范违反——客观、有标准答案的。
- **暂停问用户**：架构取舍、接口命名、跨模块影响、需要改 spec / change §3、同一问题反复 2 轮没收敛。
- **通过可合**：零 P0/P1 或仅 P2 → 告知用户进入**对应 action 的下一步**（见下表，**不要无脑建议 `/eo-archive`**）：

  | 刚跑完的 action | 通过后的下一步（提示给用户） |
  |----------------|------------------------------|
  | `spec-review` | 用户把 `spec.md` 的 `status` 改为 `confirmed` → 进入 `/eo-change` 或 `/eo-module-init` 后续流程 |
  | `change-review` | 用户把 `change.md` 的 `status` 改为 `approved` → `/eo-flow implement`（或直接 `/eo-implement`） |
  | `implement` | `/eo-flow test`（或 `/eo-test`） |
  | `test` | `/eo-flow review`（或 `/eo-review`） |
  | `review` | `/eo-archive <module> <change-id>` ← **只有这里才是归档入口** |
  | `fix` | 按 fix 前的上下文回到原 action 复审（例：review 触发的 fix → 再跑 `/eo-flow review`） |

  关键区分：`eo-archive` 只消费"实施后代码审查（`review.md`）通过"的 change，不消费 `change-review.md`。change-review 是方案级审查，通过后代码还没写，不能归档。

超时未回包（≥10 分钟）：`tmux-bridge read <codex-pane> 40` 看状态——进程还在就继续等；已 idle 但文件落稿了说明 codex 漏发 message，手动读产出决策并告知用户。

### 5. 何时停

- 用户说"停 / 我来看看"
- 同一问题反复 2 轮未收敛（Claude 和 codex 判断打架）
- codex pane 报错 / 卡住——不自作主张救援

## 关键约束

| 约束 | 说明 |
|------|------|
| `$` vs `/` | Codex 用 `$eo-*`，Claude 用 `/eo-*`，不能混 |
| effort 不可中途切 | 按 action 分 pane，每 pane 固定一档，label 是边界 |
| bypass 必带 | codex 启动必须 `--dangerously-bypass-approvals-and-sandbox` |
| 不抢活 | Claude 不在本 pane 执行 `$eo-*`，只派发 + 决策 |
| 不杀 pane | 只建不杀；进程挂了 `send-keys` 重发启动命令 |
| 锚 `$TMUX_PANE` | 所有 tmux 操作显式 `-t`，否则多终端挂同 session 会 split 到别人 tab |
| label 格式受限 + 必校验 | label 只准 `[a-zA-Z0-9_-]`（dash-kebab），括号/空格/中文会让 tmux-bridge 静默失败；建完立即 `tmux-bridge resolve` 反查验证 |
| 回包合约必注入 | 每次派发附言末尾带**三步**回包：`read` → `message` → `keys Enter`。**漏 Enter 就卡在对方输入框**。`CALLBACK` 从 `tmux-bridge id` 取，**不硬编码 `"claude"`** |
| 合约在 eo-flow 不在 eo-* | 不改 `~/.claude/skills/eo-*/SKILL.md` 加回包逻辑，eo-* 要能脱离 smux 独立跑 |
| fix 不开新 change | 这是 `$eo-implement` 自己的硬规则 |
| fix 载体随上游 | `review → fix` 甩 `$eo-implement`（代码）；`spec-review` / `change-review` 的修订**本 pane 内联改**文档，不派 codex。默认行为，别反向派发 |
| 读产出再决策 | 不光看 tmux 回包字面，必须读 `review.md` / `test.md` |
| 争议停手 | 架构/接口/跨模块/反复修不过 → 停下问用户 |

## 示例：review → 发现 P0 → 自动 fix → 再 review

```
用户: /eo-flow review
Claude:
  1. 定位 change = eo-doc/dev/transport/changes/002-offline-sync/change.md
  2. 找 review-rabbit pane → 无 → split 新 pane 跑 codex high
  3. CALLBACK=$(tmux-bridge id)  # %40
  4. 发 "$eo-review <change.md> 【回包合约】完成后 tmux-bridge message %40 ..."
  5. 告知用户"已派 review，等回包"
  ─ 收到回包 ─
  6. 读 review.md → 有 P0（测试失败）+ P1（命名）→ 客观问题，自动 fix
  7. 找 impl(rabbit) pane → split 新 pane 跑 codex high
  8. 发 "$eo-implement <change.md> 根据 review.md 的 P0/P1 全部修复 【回包合约】..."
  9. 回包后重新发 /eo-flow review（同 pane 复用）
  10. review 零 P0/P1 → 告知用户 "可 /eo-archive"
```

假设第 6 步 review 发现的是"Agent 层跨层访问 UI 状态"（架构问题），则跳过 7-9，停下问用户：

> P1 架构问题（Agent 跨层）不是改两行能搞定，需要你定：调分层 or 开 enhance change 改 spec？

## 与其它 skill 的关系

- `/smux`：tmux-bridge 通信基建，本 skill 完全依赖
- `/eo-workflow`：完整流水线编排（本 skill 不做流程）
- `/eo-change` / `/eo-implement` / `/eo-review` 等：本 skill 不替代它们，只是远程调用（`$` 前缀在 codex 端执行）
