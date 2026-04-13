# Git Diff 驱动增量同步

## 触发方式

用户可能用以下方式触发：
- `/eo-doc-manager sync`
- "同步文档"、"sync docs"、"更新文档"
- "根据最近的改动同步文档"
- 提供具体 commit 范围："把这个 PR 的改动同步到文档"

## sync-cursor 机制

为确保 sync 不遗漏任何变更，使用 `eo-doc/.sync-cursor` 文件记录同步点。

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

### .sync-cursor 应加入 .gitignore

`.sync-cursor` 是本地状态文件，不应提交到仓库。init 时自动追加到 `.gitignore`。

## 完整流程

### Step 1: 获取变更范围

**默认行为**（基于 sync-cursor）：

```bash
# 1. 读取上次同步点
LAST_COMMIT=$(cat eo-doc/.sync-cursor | jq -r '.last_sync_commit')

# 2. 已提交的变更（从上次同步到 HEAD）
git diff ${LAST_COMMIT}..HEAD --name-only

# 3. 未提交的变更（工作区 + 暂存区）
git diff --name-only
git diff --cached --name-only

# 4. 合并去重
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
变更文件列表:
  src/lib/task-runtime/engine.ts       → task-runtime 模块
  src/lib/task-runtime/executors/...   → task-runtime 模块
  src/actions/sync.ts                  → actions/sync 模块
  src/components/TabContent.tsx        → UI 组件
  prisma/schema.prisma                 → 数据模型
```

### Step 3: 定位受影响文档

在 `eo-doc/` 下比对已有文档，按以下规则匹配：

1. **agent-handbook/**：检查文档的 `source` 字段是否包含变更文件路径
2. **doc/**：检查变更是否影响文档描述的业务规则或功能
3. **design/**：检查变更是否影响设计文档中功能的实现状态

```
受影响文档:
  eo-doc/agent-handbook/task-engine.md  ← src/lib/task-runtime/* 有变更
  eo-doc/doc/task-engine.md             ← 任务引擎业务行为可能变化
  eo-doc/design/task-engine-spec.md     ← impl_status 可能需更新
```

### Step 4: 评估变更影响

对每个受影响文档，读取 diff 详情判断影响级别：

| 变更类型 | 影响 | 操作 |
|----------|------|------|
| 新增导出/公开接口 | 高 | agent-handbook: 更新接口表 + doc: 更新功能描述 |
| 修改接口签名 | 高 | agent-handbook: 更新签名 + doc: 检查业务描述 |
| 新增功能模块 | 高 | agent-handbook: 创建新文档 + doc: 创建新文档 |
| 新增依赖关系 | 中 | agent-handbook: 更新依赖关系 |
| 新增/删除文件 | 中 | agent-handbook: 更新目录结构 |
| 业务规则变更 | 中 | doc: 更新规则描述 |
| 内部重构（接口不变） | 低 | 仅更新 `updated` 时间 |
| 注释/格式调整 | 无 | 跳过 |

### Step 5: 执行更新（三路同步）

**同时更新三个目标**：

#### 5a. 更新 agent-handbook/（代码架构）

对每篇受影响的 agent-handbook 文档：
1. 读取当前文档完整内容
2. 读取相关 diff 详情
3. 更新受影响的章节：入口结构、接口签名、依赖关系、使用示例
4. 更新 `updated` 时间
5. 若 summary/conclusions 受影响，同步更新

#### 5b. 更新 doc/（当前实现）

对每篇受影响的 doc 文档：
1. 读取当前文档完整内容
2. 结合 diff 判断业务行为变化
3. 更新受影响的章节：业务规则、状态流转、配置说明
4. 更新 `updated` 时间
5. 若 summary/conclusions 受影响，同步更新

#### 5c. 更新 design/ 实现状态

对每篇相关的 design 文档：
1. 读取「实现状态」表
2. 对比代码变更，判断哪些 feature 的状态需要更新
3. 更新状态值（planned → partial → implemented）
4. 重新计算 `impl_coverage`
5. 更新 frontmatter 中的 `impl_coverage`

### Step 6: 同步索引

更新所有受影响的 INDEX.md：
- 受影响目录的 INDEX.md
- 顶级 eo-doc/INDEX.md

### Step 7: 更新 sync-cursor

```json
{
  "last_sync_commit": "<当前 HEAD commit hash>",
  "last_sync_date": "YYYY-MM-DD",
  "sync_type": "sync"
}
```

### Step 8: 汇报变更

向用户展示同步结果：

```
文档同步完成（基于 abc1234..def5678 + 未提交变更）：

agent-handbook/ 更新:
  ✏️ agent-handbook/task-engine.md — 新增 retryTask 接口描述
  ➕ agent-handbook/notification.md — 新模块文档

doc/ 更新:
  ✏️ doc/task-engine.md — 更新任务重试规则描述

design/ 状态更新:
  📊 design/task-engine-spec.md — impl_coverage 2/5 → 3/5
    • 失败重试: planned → implemented

已跳过（内部重构，接口不变）:
  ⏭️ agent-handbook/utils.md

INDEX.md 已同步: agent-handbook/, doc/, design/, 顶级
sync-cursor 已更新: def5678 (2026-03-31)
```

## 批量同步注意事项

- 大量变更时，先展示影响分析，获得用户确认后再逐一更新
- 如果变更影响的模块还没有对应文档，提示用户是否创建
- 如果变更导致某个文档内容大幅过时（>50% 章节受影响），建议重写而非逐段修补
- doc/ 和 agent-handbook/ 同一模块的文档应同时创建或同时更新
