# 全量重建（re-sync）

## 触发方式

- `/eo-doc-manager re-sync`
- "重建文档"、"全量同步"、"re-sync"

## 与 sync 的区别

| | sync | re-sync |
|---|------|---------|
| 数据源 | git diff（增量） | 全量源码扫描 |
| 依赖 sync-cursor | 是 | 否（完成后重置 cursor） |
| 重建 state/ | 增量更新 | 清空后重新生成 |
| 重建 agent-handbook/ | 增量更新 | 清空后重新生成 |
| 适用场景 | 日常同步 | 文档与代码严重脱节、首次批量生成 |

## 完整流程

> **代码优先原则**适用于 re-sync。state/ 和 agent-handbook/ 的内容从源码生成，不从已有文档迁移。已有文档仅作为"人工业务背景"的参考源。详见 SKILL.md「代码优先原则」。

### Step 1: 扫描项目源码

遍历项目全部源代码，建立模块清单：
- 分析项目根目录结构，识别源码目录、入口文件和模块边界
- 读取关键源文件，提取公开接口、类型定义、导出
- 映射模块间依赖关系（import/require 分析）

### Step 2: 重建 agent-handbook/

1. 备份现有 agent-handbook/ 文档（保留在内存中作参考）
2. **基于 Step 1 的模块清单，按模块生成文档**：每个业务模块独立一篇，文件名与模块目录名对应（如 `src/lib/opportunities/` → `opportunities.md`）。参考 [splitting.md](splitting.md) 的拆分模式和禁止模式
3. **禁止生成横切面汇总文档**（如 directory-map、module-boundaries、persistence-architecture）。架构信息必须分散到对应模块文档中
4. 仅允许 `overview.md`（技术栈+目录结构速查）和 `entrypoints.md`（页面/API/Action 索引）作为辅助入口
5. 从旧文档中仅提取"代码无法推断的人工补充内容"（如使用注意事项、历史决策原因）
6. 技术内容（接口签名、目录结构、依赖关系）一律以源码为准，不复用旧文档
7. 更新 agent-handbook/INDEX.md

### Step 3: 重建 state/

**严格遵守 SKILL.md「state/ 写作规范」。核心要点：**

1. 备份现有 state/ 文档（若 state/ 不存在，则为首次生成，直接 lazy 建）
2. **枚举业务模块清单**（非技术模块）：业务/产品/策划视角的功能单元。子系统内有多种显著不同的子类型时，每个子类型独立一篇
3. 与用户确认模块清单后再动笔；粒度不对时宁可重新枚举也不要硬写
4. **每篇按统一结构骨架写**：概述 / 核心玩法（或核心流程）/ 规则与参数 / 与其他模块的交互 / 当前未实现 TODO
5. **规格说明体风格**：业务语言、不贴代码路径/类名/文件名/代码片段；允许引用配置表名和字段名作为规则锚点
6. **基于代码实际行为**提取规则、数值、时序、优先级、边界条件；一律以源码为准
7. 从旧文档中仅提取"代码无法推断的业务背景描述"（为什么这样设计、历史决策原因）
8. 更新 state/INDEX.md

### Step 4: 重置 sync-cursor

将 `<doc_root>/.sync-cursor` 更新为当前 HEAD，为后续增量 sync 建立新基线：

```json
{
  "last_sync_commit": "<当前 HEAD commit hash>",
  "last_sync_date": "YYYY-MM-DD",
  "sync_type": "re-sync"
}
```

### Step 5: 汇报结果

```
文档全量重建完成：

agent-handbook/ (重建):
  📄 agent-handbook/task-engine.md
  📄 agent-handbook/data-layer.md
  📄 agent-handbook/overview.md
  共 N 篇

state/ (重建):
  📄 state/task-engine.md
  📄 state/content-monitoring.md
  共 N 篇

sync-cursor 已重置: abc1234 (2026-03-31)
```

## 注意事项

- re-sync 前向用户确认，因为会清空并重建 state/ 和 agent-handbook/
- 重建时尽量保留已有文档中的人工补充内容
- 若已有文档包含代码无法推断的业务背景描述，保留这些内容
- re-sync 完成后，后续 sync 从新基线开始增量
