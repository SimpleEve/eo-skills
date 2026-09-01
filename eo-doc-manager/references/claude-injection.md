# CLAUDE.md 注入规则

`eo-doc-manager` 的 `init` 会向项目根目录的 agent 配置文件注入文档体系说明，让 AI 在每次会话启动时知道 `eo-doc/` 的结构。

`eo-project-init` 另外注入 `<!-- eo-project:start -->`（项目管理侧说明）与 `<!-- eo-reply-contract:start -->`（长任务收尾回复契约）两个段落，三者互不干扰。

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

代码侧文档根目录 `eo-doc/`。

| 目录 | 用途 | 何时读 |
|------|------|--------|
| [changes/](eo-doc/changes/INDEX.md) | change 工件流（change/review/test） | 查变更进度 |
| [agent-handbook/](eo-doc/agent-handbook/INDEX.md) | 项目操作手册（commit/注释/worktree/架构/目录/UI 规范） | 做对应操作前读对应篇；不存在则无此约束 |
| [templates/](eo-doc/templates/) | 项目定制模板（eo-* 技能扩展点） | eo-* 技能启动时自动读取 |
> **注释纪律（硬入口）**：编辑任何代码前，`eo-doc/agent-handbook/comments.md` 存在则必读并遵循——它约束一切代码改动，含不经 eo 流程的直改。

> 项目管理侧（roadmap / decisions / lessons / 原始 PRD 与设计）见 `.eo-project.json`（同目录如有 `.eo-project.local.json` 则字段覆盖，local 优先）的 `project_root` 字段。
<!-- eo-doc:end -->
```

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
2. 按封闭选择协议（[../../eo-shared/questioning.md](../../eo-shared/questioning.md) §4）问：注入到文件末尾（推荐）or 用户指定位置
3. 默认追加到文件末尾（保持两空行间隔）
4. 添加 `<!-- eo-doc:start -->` / `<!-- eo-doc:end -->` 标记包裹注入内容

### 场景 3：CLAUDE.md 存在，已有 `<!-- eo-doc:start -->` 标记

1. 定位 `<!-- eo-doc:start -->` 到 `<!-- eo-doc:end -->` 之间的内容
2. **完全替换**为新的注入模板（不做局部 merge）
3. 保留标记外的其他内容不变

## 验证

注入完成后：
- [ ] CLAUDE.md 存在且可读
- [ ] `<!-- eo-doc:start -->` 和 `<!-- eo-doc:end -->` 成对出现
- [ ] 表格渲染正常（列数一致）
- [ ] 所有链接指向真实存在的目录/INDEX.md
