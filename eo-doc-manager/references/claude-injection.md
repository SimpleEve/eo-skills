# CLAUDE.md 注入规则

`eo-doc-manager` 的 `init` 和 `re-sync` 会向项目根目录的 `CLAUDE.md` 注入文档体系说明，让 AI 在每次会话启动时知道文档结构和如何使用。

`eo-project-init` 另外注入 `<!-- eo-project:start -->` 段落（项目管理侧说明），两者互不干扰。

## 注入标记

```markdown
<!-- eo-doc:start -->
...（注入内容）...
<!-- eo-doc:end -->
```

## 注入模板

```markdown
<!-- eo-doc:start -->
## eo-doc 文档体系（代码侧）

代码侧文档根目录 `eo-doc/`。**本表即目录索引**——按任务类型读对应**子目录 INDEX**；不要一次性读完。

**涉及代码时**：`agent-handbook/INDEX.md` 是必读的**代码地图指南**（先扫 INDEX 定位模块，再按需读具体模块详情，**不要通读**）。

| 目录 | 用途 | 何时读 |
|------|------|--------|
| [agent-handbook/](eo-doc/agent-handbook/INDEX.md) | 代码架构、模块入口、接口索引 | **看/改代码前必读 INDEX**，按需深入模块 |
| [state/](eo-doc/state/INDEX.md) | 业务规则、状态流转、系统现状 | 了解功能"现在是什么样" |
| [dev/](eo-doc/dev/INDEX.md) | 功能开发文档（spec/change/review） | 查变更进度 |
| [templates/](eo-doc/templates/) | 项目定制模板（eo-* 技能扩展点） | eo-* 技能启动时自动读取 |

> 项目管理侧（roadmap / decisions / lessons / 原始 PRD 与设计）见 `.eo-project.json` 的 `project_root` 字段。
<!-- eo-doc:end -->
```

> 若 `state/` 尚未创建（init 后首次 sync 前），对应行可省略或标注「待生成」。

## 注入流程

### 场景 1：CLAUDE.md 不存在

1. 在项目根目录创建 CLAUDE.md
2. 写入：
   ```markdown
   # CLAUDE.md

   本文档为 AI Agent 提供项目全局上下文。

   <!-- eo-doc:start -->
   ...（注入模板）...
   <!-- eo-doc:end -->
   ```

### 场景 2：CLAUDE.md 存在，无 `<!-- eo-doc:start -->` 标记

1. 读取现有 CLAUDE.md 全文
2. 询问用户：注入到文件末尾 or 用户指定位置
3. 默认追加到文件末尾（保持两空行间隔）
4. 添加 `<!-- eo-doc:start -->` / `<!-- eo-doc:end -->` 标记包裹注入内容

### 场景 3：CLAUDE.md 存在，已有 `<!-- eo-doc:start -->` 标记

1. 定位 `<!-- eo-doc:start -->` 到 `<!-- eo-doc:end -->` 之间的内容
2. **完全替换**为新的注入模板（不做局部 merge）
3. 保留标记外的其他内容不变

## 注入内容要点

### 为什么 agent-handbook 特殊对待

- `agent-handbook/INDEX.md` 是**代码地图指南**，不是通读材料
- 正确用法：**先扫 INDEX 定位相关模块 → 按需读具体模块文档 → 再到代码**
- 错误用法：把 INDEX 当目录浏览全部模块文档

### 为什么不加"先读 eo-doc/INDEX.md"

- 无顶级 INDEX.md（CLAUDE.md 里的表就是一级索引）
- 避免 CLAUDE → 顶级 INDEX → 子 INDEX 三跳

## 验证

注入完成后：
- [ ] CLAUDE.md 存在且可读
- [ ] `<!-- eo-doc:start -->` 和 `<!-- eo-doc:end -->` 成对出现
- [ ] 表格渲染正常（列数一致）
- [ ] 所有链接指向真实存在的子目录 INDEX.md（state/ 未建时可标注待生成）
