---
title: 抽取共享解析库并修复 eo-board local 合并与缓存代码审查报告
change_id: shared-lib-board-cache
tags: [eo-board, shared-lib, cache]
created: 2026-07-24
updated: 2026-07-24
status: active
summary: >
  首轮审查未发现 P0，但缓存 miss 缺少单飞保护、合并配置缺少必填校验，共有 2 条 P1，暂不能置 reviewed。
---

# 抽取共享解析库并修复 eo-board local 合并与缓存 代码审查报告

> 关联 Change：[change.md](change.md)（检查表：其 §2 验收清单）
> 首轮审查日期：2026-07-24 ｜ 审查范围：基线 `792522d`；实施提交 `9b3bc69`、`72b1946`、`5ac8d27`；`cli/eo-board`、`cli/eo_lib/`
> ⚠️ 首轮之后正文各节为历史快照——当前状态以「Finding 台账」与末尾「速报」为准

## Finding 台账

| ID | 级别 | 摘要 | 位置 | 状态 | 根因 | 首见/最近轮 | 基线/修复 commit |
|----|------|------|------|------|------|-------------|------------------|
| P1-1 | P1 | cache miss 重建未受单飞保护，并发请求会重复全量扫描 | `cli/eo-board:1455` | fixed | implementation | 1/1 | `5ac8d27` / `5e81f33` |
| P1-2 | P1 | local 合并后未校验必填配置，缺配置会静默展示空看板 | `cli/eo_lib/config.py:35` | fixed | implementation | 1/1 | `5ac8d27` / `5e81f33` |

## 审查总结（首轮快照）

五域抽取与 `792522d` 基线保持等价，符号链接导入、local 浅合并、非法 JSON 的 `ConfigError` 所有权均已落地；新鲜度键也静态覆盖了当前 `build_data` 的 worktree、refs、日期、changes、backlog 与 roadmap 输入。当前仍有两条 P1：线程锁只保护字典读写，不能阻止同键并发重建；配置加载没有执行项目契约要求的合并后必填校验。按本 change 的收敛标准，状态保持 `implementing`。

## P0 - 必须修复（阻塞性问题）

无。

## P1 - 建议修复（重要但不阻塞）

### [P1-1] cache miss 重建未受单飞保护

- **类型**：潜在 Bug / 性能问题
- **位置**：`cli/eo-board:1455`
- **描述**：`_BOARD_CACHE_LOCK` 只覆盖第一次查表与最后写表，锁在 `build_data` 前已经释放。`ThreadingHTTPServer` 下两个同项目、同新鲜度键的并发 miss 会同时穿透并各跑一次全量扫描；确定性双线程探针得到 `build_count=2`，两个请求均打印 miss。若两次请求观察到不同键，较晚结束的旧构建还可覆盖较新的缓存槽，造成后续额外 miss。
- **影响**：多标签页或并发轮询时，最昂贵的扫描与 git 子进程仍会重复执行，缓存无法稳定兑现其性能目标。
- **建议**：按项目槽实现 single-flight（每槽 lock/condition 或 in-flight future）；拿到构建权后再次检查键，只允许一个线程为同键执行 `build_data`，同时避免用全局锁串行阻塞不同项目。

### [P1-2] 合并配置缺少必填校验

- **类型**：逻辑错误 / 错误边界缺失
- **位置**：`cli/eo_lib/config.py:35`
- **描述**：主配置与 local 浅合并后，函数直接给 `mode` 填 `"local"`、允许 `project_root=None` 并返回，没有按共享配置契约校验合并结果。用仅含 `project_name`/`doc_root`、缺少 local 文件的协作者配置运行时，eo-board 以退出码 0 展示一个空 local 看板，而不是抛 `ConfigError` 并提示运行 `/eo-project-init`。这与 [配置约定](../../../eo-project-init/references/config.md) 的必填字段及启动流程不符，也违背 change §1 的已钉决策。
- **影响**：协作者缺失机器配置时会看到“空项目”这一假成功；未来 eo-sync 复用该公共入口后也会继承错误路径。
- **建议**：浅合并完成后、构造标准化配置前校验 `project_name`、`mode`、`project_root`、`doc_root`，并检查 mode 枚举、路径类型与绝对/相对约束；缺失或非法时抛带配置路径和具体字段原因的 `ConfigError`，由 CLI 补充 `/eo-project-init` 指引。

## P2 - 可选优化（锦上添花）

无。

## 验收标准覆盖检查

| AC 编号 | 描述 | 状态 |
|---------|------|------|
| AC-1 | 抽取后三形态行为不变 | ✅ 通过：同一当前仓库状态下，基线/现版 `build_data`、终端渲染、HTML 渲染在归一化生成时间后逐字段相等；现有符号链接入口可运行。serve 端到端仍归 `/eo-test` |
| AC-2 | 共享库可独立复用 | ✅ 通过：`from cli.eo_lib import ...` 可直接调用配置、git、frontmatter、change 扫描、AC/TODO 计数五域，返回结构化结果且库内无 `sys.exit`/`die` |
| AC-3 | local 顶层覆盖生效 | ✅ 通过：临时项目中 local `project_root` 成功改换 backlog 数据源，对象字段按顶层整体覆盖；无 local 时保持基线等价 |
| AC-4 | local 解析失败可见 | ✅ 通过：非法 local 返回码 1，stderr 含 `.eo-project.local.json` 完整路径与 JSON 原因，无 traceback |
| AC-5 | 缓存命中 | — 本轮不核：按任务约束归 `/eo-test` |
| AC-6 | 缓存新鲜 | — 本轮不核：按任务约束归 `/eo-test` |

## TODO 完成度检查

| TODO | 描述 | 状态 |
|------|------|------|
| TODO-1 | 五域抽入 `cli/eo_lib/` | ✅ 完成：抽取实现与基线等价，公共包可独立导入 |
| TODO-2 | eo-board 消费共享包并捕获 ConfigError | ✅ 完成：board 专属职责保留，符号链接导入与错误格式化成立 |
| TODO-3 | local 浅合并与非法 JSON 错误 | ⚠️ 部分完成：AC-3/4 已覆盖，但合并结果必填校验缺失，见 P1-2 |
| TODO-4 | 新鲜度键闭合动态输入 | ✅ 静态实现完成：列明的六类输入均进入键；行为验收仍归 `/eo-test` |
| TODO-5 | serve 接入每项目缓存 | ⚠️ 部分完成：顺序命中路径存在，但并发 miss 未单飞，见 P1-1 |

## 验证证据

- `792522d` 基线与 `5ac8d27` 现版：`build_data_equal=True`、`terminal_equal=True`、`html_equal=True`（归一化 `generated_at`）。
- 共享包五域冒烟：配置、frontmatter、git、worktree、change 扫描、AC/TODO 计数均返回预期结构，warnings 为空。
- local 临时项目：覆盖后只显示 local backlog；非法 local 返回码 1 且错误口径正确。
- 并发缓存探针：固定同一 freshness key，同时发起两个线程，`build_data` 被调用 2 次，复现 P1-1。
- `python3 -m compileall -q cli/eo_lib cli/eo-board` 通过。

## 速报

结论：有保留通过（P1 2 条）［第 1 轮 · revision 1 · 基线 `5ac8d27`］
P1（应修）：
1. cache miss 重建未受单飞保护，并发请求会重复全量扫描 — `cli/eo-board:1455`
2. local 合并后未校验必填配置，缺配置会静默展示空看板 — `cli/eo_lib/config.py:35`
下一步：回 `/eo-implement` 模式二修复后复审；AC-5/6 仍待 `/eo-test`，change status 保持 `implementing`。
