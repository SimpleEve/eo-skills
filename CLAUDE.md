# CLAUDE.md

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

<!-- eo-doc:start -->
## eo-doc 文档体系（代码侧）

代码侧文档根目录 `eo-doc/`。**本表即目录索引**——按任务类型读对应**子目录 INDEX**；不要一次性读完。

**涉及代码时**：`agent-handbook/INDEX.md` 是必读的**代码地图指南**（先扫 INDEX 定位模块，再按需读具体模块详情，**不要通读**）。

| 目录 | 用途 | 何时读 |
|------|------|--------|
| [agent-handbook/](eo-doc/agent-handbook/INDEX.md) | 代码架构、模块入口、接口索引 | **看/改代码前必读 INDEX**，按需深入模块 |
| state/ | 业务规则、状态流转、系统现状（待首次 sync 生成） | 了解功能"现在是什么样" |
| [changes/](eo-doc/changes/INDEX.md) | change 工件流（change/review/test） | 查变更进度 |
| [templates/](eo-doc/templates/) | 项目定制模板（eo-* 技能扩展点） | eo-* 技能启动时自动读取 |

> 项目管理侧（roadmap / decisions / lessons / 原始 PRD 与设计）见 `.eo-project.json`（同目录如有 `.eo-project.local.json` 则字段覆盖，local 优先）的 `project_root` 字段。
<!-- eo-doc:end -->
