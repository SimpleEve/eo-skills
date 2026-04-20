---
name: eo-workflow
description: 在 tmux 多窗格中编排 eo-* 技能流水线（module-init / change / implement / archive），跨 pane 自动派发和状态轮询。触发：eo-workflow / 启动工作流 / 全流程 / /eo-workflow。
---

# eo-workflow — 多 Agent 编排工作流

在 tmux 多窗格中编排新工作流的 skill 流水线。通过 tmux-bridge 跨 pane 通信，配合 CronCreate 做定时轮询，实现 module-init / change / implement / archive 的自动派发、状态监控和结果流转。

## 前置

**必须能找到 `.eo-project.json`**。找不到 → 报错退出，提示运行 `/eo-project-init`。子 pane 中执行的每个 eo-* skill 自己也会检查，但本 skill 启动时先校验以快速失败。

## 新工作流速览

```
模块不存在 → /eo-module-init（含 spec + spec-review 一次性审查）
模块已存在 + 业务变更 → /eo-change → /eo-implement → /eo-test → /eo-review → /eo-archive
实施期 bug fix → /eo-implement（不开新 change，不走 archive）
```

## 参数

```
/eo-workflow <phase> <module-name> [change-id] [loop-interval] [--with-review]
```

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `phase` | 是 | `module-init` / `change` / `implement` / `archive` / `full` | `implement` |
| `module-name` | 是 | `eo-doc/dev/` 下的模块名（kebab-case） | `transport` |
| `change-id` | implement/archive 必填 | 模块内 change 目录名（如 `001-add-queue`） | `001-add-queue` |
| `loop-interval` | 否 | 监控轮询间隔，默认 `3m` | `5m` |
| `--with-review` | 否 | 在 `change` / `full` phase 启用 change-review 子阶段（change draft 完成后自动派发 `/eo-change-review`） | `--with-review` |

派生变量：
- `MODULE_ROOT` = `eo-doc/dev/<module-name>/`
- `CHANGE_ROOT` = `eo-doc/dev/<module-name>/changes/<change-id>/`
- `LOOP_CRON` = interval 转 cron（如 `3m` → `*/3 * * * *`）

## 执行流程

### 1. 前置校验

| Phase | 校验 |
|-------|------|
| module-init | `MODULE_ROOT` 不存在 |
| change | `MODULE_ROOT/spec.md` 存在且 `status: confirmed` |
| implement | `CHANGE_ROOT/change.md` 存在且 `status: approved` 或 `implementing` |
| archive | `CHANGE_ROOT/change.md` 存在且 `status: done`；`review.md` 存在且通过 |
| full | `module-name` 有效 |

### 2. 启动 Pane

```bash
bash ~/.claude/skills/eo-workflow/start-panes.sh <phase>
```

各阶段所需 pane（除 main/orchestrator）：

| Phase | Pane |
|-------|------|
| module-init | spec, review |
| change | change |
| implement | implement, test, review |
| archive | （无，主 orchestrator 直接执行） |
| full | spec, change, implement, test, review |

### 3. 识别 Agent 类型

从 `tmux-bridge list` 的 **PROCESS** 列判断：
- 含 `codex` → Codex → 前缀 `$`
- 含 `claude` 或其他 → Claude → 前缀 `/`

### 4. 设置 Loop 并首次触发

1. CronCreate 监控 job（LOOP_CRON, recurring: true）
2. 立即执行首轮操作

---

## 指令发送标准流程

对所有 pane 统一用 `tmux-bridge type`（不用 `message`）：

```bash
tmux-bridge read <label> 20
tmux-bridge type <label> "<command>"
tmux-bridge read <label> 5
tmux-bridge keys <label> Enter
```

### Review Pane 上下文清理

full 模式下 review pane 被 spec-review / code-review 两个阶段复用。切换阶段前发 `/clear`：

```bash
tmux-bridge read review 5
tmux-bridge type review "/clear"
tmux-bridge read review 5
tmux-bridge keys review Enter
```

---

## Phase: module-init（交互式）

由用户在 spec pane 中直接操作，orchestrator 负责派发 spec-review。

### 首次操作

通知用户：
> spec pane 已就绪，请在 spec pane 中使用 `/eo-module-init <module-name>` 初始化模块。
> 完成后将 spec.md 的 status 改为 `confirmed`，我会自动派发 spec-review。

### Cron 监控逻辑

1. 读 `MODULE_ROOT/spec.md` frontmatter → status 非 `confirmed` → 不操作
2. status `confirmed` + review pane 空闲 + `spec-review.md` 不存在 → 派发 `<prefix>eo-spec-review MODULE_ROOT/spec.md` 到 review pane
3. review 完成 + `spec-review.md` 存在 → 读审查结论：
   - 无 P0/P1 → CronDelete + 通知 "✅ 模块基线建立完成"
   - 有 P0/P1 → 暂停 loop（CronDelete），通知用户去 spec pane 修复，等 `continue`

### 恢复机制

用户输入 `continue` 后：删除旧 `spec-review.md` → 重新 CronCreate 同一监控 prompt

---

## Phase: change（交互式）

由用户在 change pane 中直接和 eo-change 协作澄清。**默认不做自动审查**（change 自澄清）；启用 `--with-review` 时，draft 完成后会自动派发 `/eo-change-review` 到 review pane。

### 启动 Pane

- 默认：只需 `change` pane
- `--with-review`：需要 `change` + `review` pane

### 首次操作

默认：
> change pane 已就绪，请在 change pane 中使用 `/eo-change`，目标模块 `<module-name>`。
> 完成后将 change.md 的 status 改为 `approved`，然后启动 `/eo-workflow implement <module-name> <change-id>`。

带 `--with-review`：
> change pane 已就绪，请在 change pane 中使用 `/eo-change`，目标模块 `<module-name>`。
> change.md 写完后保持 `status: draft`，我会自动派发 `/eo-change-review` 到 review pane 做方案审查。
> change-review 通过后，你再将 status 改为 `approved` 进入 implement。

### Cron 监控逻辑

**默认模式：**
1. 扫描 `MODULE_ROOT/changes/` 下所有 change 的 frontmatter
2. 发现 `status: approved` 的 change → 通知用户可进入 implement 阶段
3. 不自动派发任何审查

**`--with-review` 模式：**
1. 扫描 `MODULE_ROOT/changes/` 下 `status: draft` 的 change
2. 发现 change.md 写完且 `change-review.md` 不存在 + review pane 空闲 → 派发 `<prefix>eo-change-review CHANGE_ROOT/change.md` 到 review pane
3. change-review 完成 + `change-review.md` 存在 → 读结论：
   - 无 P0/P1 → 通知用户可将 status 改为 `approved` 进入 implement
   - 有 P0/P1 → 暂停 loop 通知用户去 change pane 修订，修订后等 `continue`
4. `status: approved` → 通知用户可进入 implement
5. 恢复机制：用户输入 `continue` 后删除旧 `change-review.md` 并重新 CronCreate 同一监控 prompt

---

## Phase: implement（全自动）

implement 阶段完全自动化，在 implement / test / review 三 pane 间流转。

### 首次操作

派发 `<prefix>eo-implement CHANGE_ROOT/change.md` 到 implement pane。将 change.md status 从 `approved` 改为 `implementing`。

### Cron 监控逻辑（状态机）

**规则 1：implement 完成 + test 未开始本轮**
→ 派发 `<prefix>eo-test CHANGE_ROOT/change.md` 到 test pane

**规则 2：test 完成 → 读 `CHANGE_ROOT/test.md`**
- 有失败 → 派发 implement 修复：`<prefix>eo-implement CHANGE_ROOT/change.md 根据 CHANGE_ROOT/test.md 的测试结果修复所有失败`
- 全通过 → 派发 `<prefix>eo-review CHANGE_ROOT/change.md` 到 review pane

**规则 3：review 完成 → 读 `CHANGE_ROOT/review.md`**
- 有 P1+ 问题 → 派发 implement 修复：`<prefix>eo-implement CHANGE_ROOT/change.md 根据 CHANGE_ROOT/review.md 的审查意见修复所有问题`
- 通过（"LGTM"/"可合入"/"通过" 且无 P0/P1）→ 将 change.md status 改为 `done` → CronDelete + 通知 "✅ 实施、测试、审查全部通过，可进入 /eo-workflow archive"

**规则 4：任一 pane 运行中** → 不操作

**安全阀**：超过 3 轮 implement-fix 循环无进展 → 暂停通知用户人工介入

### implement fix 完成后的流转

- 上一轮 test 失败修复 → 重新派发 test
- 上一轮 review 问题修复 → 重新派发 review
- **fix 不创建新 change**：所有 fix 都在当前 change.md 内迭代

---

## Phase: archive（一次性）

orchestrator 主 pane 直接执行 `/eo-archive <module-name> <change-id>`，无需额外 pane。

### 执行逻辑

1. 校验 `change.md status: done` + `review.md` 通过
2. 调用 eo-archive（或由 main pane 的 agent 执行）
3. 读 change.md 的 Spec Delta → 合并到 `MODULE_ROOT/spec.md`
4. 更新 `changes/INDEX.md` 和 `eo-doc/dev/INDEX.md`
5. 将 change.md status 改为 `archived`
6. 通知 "✅ 归档完成，Delta 已合并回模块 spec"

若遇到 Delta 冲突 → 停止并要求用户裁决

---

## Phase: full（全流程）

依次执行 module-init（若需要）→ change → implement → archive。

### 阶段转换

**module-init → change：**
1. spec-review 通过
2. Edit 工具将 `spec.md` status 改为 `confirmed`
3. 向 review pane 发 `/clear`
4. CronDelete module-init cron → CronCreate change cron
5. 通知用户去 change pane 触发 `/eo-change`

**change → implement：**
1. change.md status 从 draft 改为 approved（由用户确认后触发）
2. CronDelete change cron → CronCreate implement cron
3. 向 implement pane 发送 `<prefix>eo-implement CHANGE_ROOT/change.md`

**implement → archive：**
1. review 通过
2. change.md status 改为 done
3. CronDelete implement cron
4. 主 orchestrator 执行 `/eo-archive <module-name> <change-id>`
5. 归档成功 → 流程结束

---

## Pane 状态检测

通过 `tmux-bridge read <label> 30` 判断：

| 信号 | 含义 |
|------|------|
| Codex `›` / Claude `❯` 提示符无活跃输出 | 空闲 |
| `Working (Nm Ns • esc to interrupt)` | 运行中 |
| "已完成"/"done"/"completed"/"applied" | 任务完成 |

### Review/Test 结果判断

**Review 类**（spec-review.md / change-review.md / review.md）：
- 有 P0/P1 issue → 未通过
- 结论含 "通过"/"LGTM"/"可合入" 且无 P0/P1 → 通过

**Test**（test.md）：
- 有 "❌"/"FAIL"/"失败" → 有失败
- 全部 "✅"/"pass" → 全通过

---

## 文档路径速查

| 阶段 | skill | 产出文档 |
|------|-------|---------|
| module-init | eo-module-init | `eo-doc/dev/<module>/spec.md` |
| spec-review | eo-spec-review | `eo-doc/dev/<module>/spec-review.md` |
| change | eo-change | `eo-doc/dev/<module>/changes/<change-id>/change.md` |
| change-review（可选） | eo-change-review | `changes/<change-id>/change-review.md` |
| implement | eo-implement | 代码 + 可选 `changes/<change-id>/implement.md`（偏差） |
| test | eo-test | `changes/<change-id>/test.md` |
| review（代码） | eo-review | `changes/<change-id>/review.md` |
| archive | eo-archive | 合并回 `<module>/spec.md` + 状态变更 |
