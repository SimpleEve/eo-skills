---
title: eo-board 看板现状
type: state
tags: [eo-board, cache, config, collaboration]
created: 2026-07-24
updated: 2026-07-24
scope: 想了解看板能做什么、配置怎么生效时
status: active
source: cli/eo-board
summary: >
  eo-board 提供终端/HTML/本地服务三种只读看板；配置支持 .eo-project.local.json 个人覆盖（顶层字段、local 优先、必填看合并结果）；
  --serve 有每项目缓存，仓库无变化时轮询不重扫，有变化 3 秒内上板。
conclusions:
  - 配置缺必填字段不再静默兜底——报错并提示运行 /eo-project-init（协作者 clone 场景引导生成 local 覆盖）
  - 缓存对以下变化敏感：新 commit、任何 ref 增删移（含同 SHA 换分支）、change/backlog/roadmap 文件改动、跨日期边界
  - 看板严格只读：不写任何项目文件，数据源是 change.md frontmatter 而非 Obsidian stub
---

## 使用方式

| 命令 | 行为 |
|------|------|
| `eo-board` | 终端摘要：状态分列 + backlog + 警告 + 统计 |
| `eo-board --html [-o 路径]` | 自包含静态 HTML 快照，自动开浏览器 |
| `eo-board --serve` | 本地只读服务（127.0.0.1:7333），页面每 3 秒热刷新 |

## 配置解析规则

1. 从当前目录向上找 `.eo-project.json`
2. 同目录存在 `.eo-project.local.json` → 顶层字段覆盖合并（local 优先）
3. 合并结果校验必填：`project_name` / `mode`（vault|local）/ `project_root`（绝对路径）/ `doc_root`（相对路径）；缺失或非法 → 明确报错 + `/eo-project-init` 指引，不展示空看板

## 缓存行为（--serve）

- 仓库无变化：轮询命中缓存直接应答（stderr 有 hit 诊断行）
- 有变化：一个轮询周期（3 秒）内页面反映新数据；并发请求同槽只重建一次（单飞），多项目槽互不阻塞
- 单次运行形态（终端 / --html）不使用缓存，永远全量扫描
