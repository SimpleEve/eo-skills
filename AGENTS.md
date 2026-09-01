# AGENTS.md

本文档为 AI Agent 提供项目全局上下文。

<!-- eo-project:start -->
## EO-Project

本项目已接入 eo-skills。项目管理侧（roadmap / backlog 卡片 / decisions / lessons 等）位置从 `.eo-project.json` 的 `project_root` 字段解析（同目录存在 `.eo-project.local.json` 时顶层字段覆盖，local 优先），下文记作 `<project_root>`。

- 代码侧文档：`eo-doc/`

### 项目记录入口

仅当**用户明确表达**要记录时响应（不做关键词嗅探，避免误触发）：

- 用户明确说「加个待办 / 记到 backlog / 以后做」→ 调用 `/eo-backlog` 写卡到 `<project_root>/backlog/`
- 用户明确说「把这个决策记下来」→ 调用 `/eo-project-record` 写入 `<project_root>/decisions/`
- 用户明确说「记一条经验 / 踩坑记录一下」→ 调用 `/eo-project-record` 写入 `<project_root>/lessons/`

对话中出现疑似待办/决策/教训但用户未明说时，**至多在当前话题收尾处轻提一句**「要不要记入 backlog/decisions/lessons？」，不打断进行中的工作。
<!-- eo-project:end -->

<!-- eo-reply-contract:start -->
## 回复契约（长任务收尾）

长开发任务收尾时，用一段人话向用户汇报，四条各一句：

1. **做了什么**——行为变化，不是 diff 清单
2. **为什么这么做**——关键决策与理由，被否掉的方案一并点名
3. **主要产出**——文件 / 功能 / 命令，用户去哪看、怎么验
4. **遇到的问题与解法**——没有就明说「无」

受众分两层：对开发者讲接口与路径，对需求方讲行为与结果。一句一事，不铺陈过程。
<!-- eo-reply-contract:end -->

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
