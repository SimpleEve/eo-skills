# 维护协议

## 更新工作流

### 新增内容

1. 确定目标分类（`design/`、`doc/`、`agent-handbook/`、`research/`、`knowledgebase/`）
2. 检查已有 INDEX.md 中是否有相关文档
3. 若已有相关文档：
   - 合并后仍 < 500 行且同一主题 → 合并到已有文档
   - 属于独立子主题 → 创建新文档
4. 设置 `updated` 为当前日期
5. 更新目录级 INDEX.md 对应条目（或新增行）
6. 更新顶级 INDEX.md

### 修改已有内容

1. 完整读取当前文档
2. 应用修改，保持结构
3. 更新 `updated` 为当前日期
4. 若修改影响了 `summary` 或 `conclusions`，同步更新两者
5. 若 INDEX.md 摘要列发生变化，同步更新（目录级 + 顶级）
6. 检查修改后是否超出 500 行阈值

### 批量导入

一次导入多篇文档时：

1. 先通读所有输入材料
2. 识别全部输入中的主题聚类
3. 按分流规则判断每段内容归属（可能跨目录）
4. 检查已有结构是否有冲突/重叠
5. 向用户展示文件规划：
   ```
   导入计划（6 篇文档）：
   → eo-doc/design/task-engine-spec.md（新建）
   → eo-doc/doc/task-engine.md（新建）
   → eo-doc/agent-handbook/task-engine.md（新建）
   → eo-doc/research/competitor-a.md（新建）
   → eo-doc/knowledgebase/oauth-guide.md（新建）
   → eo-doc/doc/auth.md（更新，与已有合并）

   INDEX.md 更新：所有受影响目录 + 顶级
   ```
6. 用户确认后执行

## design ↔ doc 一致性检查

**每次 sync/re-sync 后必须执行。**

### 检查流程

1. 遍历 `eo-doc/design/` 下所有 active 文档
2. 读取每篇文档的「实现状态」表
3. 对比 `eo-doc/doc/` 中的实际内容：
   - design 说"已实现"，但 doc 中没有对应描述 → **标记为需要核实**
   - design 说"未实现"，但 doc 中已有对应描述 → **更新为 implemented**
   - design 说"部分实现"，检查 doc 描述的完整度 → **更新或保持**
4. 重新计算 `impl_coverage` 并更新 frontmatter
5. 若有状态变更，同步顶级 INDEX.md 的 impl_coverage 列

### 差异处理规则

| 情况 | 操作 |
|------|------|
| design feature 对应的代码已实现，doc 已记录 | 标记 `✅ implemented`，添加 doc_ref 链接 |
| design feature 对应的代码已实现，doc 未记录 | 标记 `✅ implemented`，在 doc 中补充记录 |
| design feature 代码部分实现 | 标记 `🔶 partial`，备注缺失部分 |
| design feature 代码未实现 | 保持 `📋 planned` |
| doc 记录了 design 中没有的功能 | 提示用户：是否需要补充 design 文档？ |

## 一致性检查清单

每次创建/更新操作后执行：

### 标签一致性
- 无近义重复标签：`auth` vs `authentication` → 选定一个
- 无过于宽泛的标签：`development` → 太模糊
- 跨目录同一概念使用相同标签

### 交叉引用完整性
- 文档中所有 `[链接](path.md)` 指向真实存在的文件
- design↔doc↔agent-handbook 三方交叉引用完整
- 若被引用文档发生拆分/重命名，更新所有引用

### INDEX.md 同步
- 目录内每个 `.md` 文件（INDEX.md 除外）都有对应索引条目
- 无孤立索引条目指向已删除的文件
- 目录级 INDEX.md 条目与顶级 INDEX.md 一致
- design 文档在顶级 INDEX.md 中显示 impl_coverage

### doc 与 agent-handbook 同源
- 每个 doc/ 中描述的模块，在 agent-handbook/ 中有对应文档
- 两者描述的功能范围一致（doc 用业务语言，agent-handbook 用代码语言）
- 若 doc 新增了模块描述，检查 agent-handbook 是否需要同步新增

## 臃肿检测清单

每次操作后检查被修改的文档：

| 检查项 | 阈值 | 处理 |
|--------|------|------|
| 行数 | > 500 | 建议拆分 |
| 标签数 | > 5 | 审查范围，可能需要拆分 |
| 章节数 | > 8 个 `##` | 考虑按章节组拆分 |
| 摘要准确性 | 摘要与内容不符 | 重写摘要 |
| 结论时效性 | 结论已过时 | 更新结论 |

## 归档

内容过时时：
1. frontmatter 设置 `status: archived`
2. 顶部加说明：`> 已于 YYYY-MM-DD 归档。当前版本见 [replacement.md](replacement.md)。`
3. 在目录级 INDEX.md 中移至 `## 已归档` 分组
4. 在顶级 INDEX.md 中移除或标注
5. **不删除**——归档文档仍可作为历史参考
