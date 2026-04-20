# Git Diff 驱动增量同步

## 触发方式

- `/eo-doc-manager sync`
- "同步文档"、"sync docs"、"更新文档"
- "根据最近的改动同步文档"
- 指定范围："把这个 PR 的改动同步到文档"

## sync-cursor 机制

使用 `<doc_root>/.sync-cursor` 记录同步点（`doc_root` 来自 `.eo-project.json`，通常是 `eo-doc/`）。

### 文件格式

```json
{
  "last_sync_commit": "abc1234def5678",
  "last_sync_date": "2026-03-31",
  "sync_type": "sync"
}
```

### 工作原理

1. **首次 sync**：若 `.sync-cursor` 不存在，提示用户选择起点（某个 commit / 分支基点 / 全部历史）
2. **后续 sync**：读取 `last_sync_commit`，从该点到当前 HEAD 的变更 + 未提交变更
3. **sync 完成后**：将当前 HEAD 写入 `.sync-cursor`
4. **用户指定范围时**：优先使用用户指定的范围，但仍更新 `.sync-cursor`

`.sync-cursor` 是本地状态文件，init 时自动追加到 `.gitignore`。

## 完整流程

### Step 1: 获取变更范围

**默认行为**（基于 sync-cursor）：

```bash
LAST_COMMIT=$(cat <doc_root>/.sync-cursor | jq -r '.last_sync_commit')
git diff ${LAST_COMMIT}..HEAD --name-only
git diff --name-only
git diff --cached --name-only
```

**用户指定范围时**：

| 场景 | 命令 |
|------|------|
| 指定 commit 范围 | `git diff <from>..<to> --name-only` |
| 与某分支对比 | `git diff main --name-only` |
| 指定时间段 | `git log --since="2026-03-01" --name-only --pretty=format:""` |

### Step 2: 归类变更文件

将变更文件按模块/目录归类：

```
src/lib/task-runtime/engine.ts       → task-runtime 模块
src/lib/task-runtime/executors/...   → task-runtime 模块
src/actions/sync.ts                  → actions/sync 模块
```

### Step 3: 定位受影响文档

在 `<doc_root>/` 下比对已有文档：

1. **agent-handbook/**：检查 `source` 字段是否包含变更文件路径
2. **state/**：检查变更是否影响文档描述的业务规则或功能
   - 若 state/ 不存在 → 首次 sync 时 lazy 建目录并生成首批文档

```
受影响文档:
  eo-doc/agent-handbook/task-engine.md  ← src/lib/task-runtime/* 有变更
  eo-doc/state/task-engine.md           ← 任务引擎业务行为可能变化
```

### Step 4: 评估变更影响

对每个受影响文档，读取 diff 详情判断影响级别：

| 变更类型 | 影响 | 操作 |
|----------|------|------|
| 新增导出/公开接口 | 高 | agent-handbook: 更新接口表 + state: 更新功能描述 |
| 修改接口签名 | 高 | agent-handbook: 更新签名 + state: 检查业务描述 |
| 新增功能模块 | 高 | agent-handbook: 创建新文档 + state: 创建新文档 |
| 新增依赖关系 | 中 | agent-handbook: 更新依赖关系 |
| 新增/删除文件 | 中 | agent-handbook: 更新目录结构 |
| 业务规则变更 | 中 | state: 更新规则描述 |
| 内部重构（接口不变） | 低 | 仅更新 `updated` 时间 |
| 注释/格式调整 | 无 | 跳过 |

### Step 5: 执行更新（两路同步）

**同时更新两个目标**：

#### 5a. 更新 agent-handbook/

对每篇受影响的文档：
1. 读取当前文档完整内容
2. 读取相关 diff 详情
3. 更新受影响的章节：入口结构、接口签名、依赖关系、使用示例
4. 更新 `updated` 时间
5. 若 summary/conclusions 受影响，同步更新

#### 5b. 更新 state/

对每篇受影响的文档：
1. 读取当前文档完整内容
2. 结合 diff 判断业务行为变化
3. 更新受影响的章节：业务规则、状态流转、配置说明
4. 更新 `updated` 时间
5. 若 summary/conclusions 受影响，同步更新

若 state/ 尚不存在，本次 sync 首次 lazy 建目录，按业务模块清单生成首批文档（遵守 re-sync 的 state 生成规范）。

### Step 6: 同步索引

更新所有受影响子目录的 INDEX.md。

### Step 7: 更新 sync-cursor

```json
{
  "last_sync_commit": "<当前 HEAD commit hash>",
  "last_sync_date": "YYYY-MM-DD",
  "sync_type": "sync"
}
```

### Step 8: 汇报变更

```
文档同步完成（基于 abc1234..def5678 + 未提交变更）：

agent-handbook/ 更新:
  ✏️ agent-handbook/task-engine.md — 新增 retryTask 接口描述
  ➕ agent-handbook/notification.md — 新模块文档

state/ 更新:
  ✏️ state/task-engine.md — 更新任务重试规则描述

已跳过（内部重构，接口不变）:
  ⏭️ agent-handbook/utils.md

INDEX.md 已同步: agent-handbook/, state/
sync-cursor 已更新: def5678 (2026-03-31)
```

## 批量同步注意事项

- 大量变更时，先展示影响分析，获得用户确认后再逐一更新
- 如果变更影响的模块还没有对应文档，提示用户是否创建
- 如果变更导致某个文档内容大幅过时（>50% 章节受影响），建议重写而非逐段修补
- state/ 和 agent-handbook/ 同一模块的文档应同时创建或同时更新
