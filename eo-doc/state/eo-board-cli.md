---
title: eo-board 看板现状
type: state
tags: [eo-board, cache, config, collaboration, aggregate]
created: 2026-07-24
updated: 2026-07-27
scope: 想了解看板能做什么、配置怎么生效时
status: active
source: cli/eo-board
summary: >
  eo-board 提供终端/HTML/本地服务三种只读看板；多项目聚合页是「change 流 ⇄ 概要卡」双视图首页，点卡/点行即下钻该项目泳道页；
  配置支持 .eo-project.local.json 个人覆盖（顶层字段、local 优先、必填看合并结果）；
  --serve 有每项目缓存，仓库无变化时轮询不重扫，有变化 3 秒内上板。
conclusions:
  - 配置缺必填字段不再静默兜底——报错并提示运行 /eo-project-init（协作者 clone 场景引导生成 local 覆盖）
  - 缓存对以下变化敏感：新 commit、任何 ref 增删移（含同 SHA 换分支）、change/backlog/roadmap 文件改动、跨日期边界
  - 看板严格只读：不写任何项目文件，数据源是 change.md frontmatter 而非 Obsidian stub
  - 聚合页默认看到的是「哪个 change 在动」而不是「有哪些项目」；archived change 不进流，只在计数里可见
  - 3 天无动静只降权不过滤——久未动的 draft 仍在流里，不会因为放久了而从视野消失
---

## 使用方式

| 命令 | 行为 |
|------|------|
| `eo-board` | 终端摘要：状态分列 + backlog + 警告 + 统计 |
| `eo-board --html [-o 路径]` | 自包含静态 HTML 快照，自动开浏览器 |
| `eo-board --serve` | 本地只读服务（127.0.0.1:7333），页面每 3 秒热刷新 |
| `eo-board --all [--html|--serve] [--scan 父目录]` | 多项目总览：终端行 / 一页网页快照 / 实时聚合页（后两者为双视图首页 + 可点下钻，见下节） |
| `eo-helper` | 数字菜单唯一入口：以上高频动作全覆盖（选前回显底层命令） |
| `eo-board --project <路径\|名>` | 任意目录下钻单项目视图（与聚合页里点进去看到的是同一个泳道页） |
| `eo-board --register / --unregister` | 维护 ~/.eo/projects.json 注册表 |

## 聚合页：双视图首页与下钻（`--all --html` / `--all --serve`）

**默认视图「change 流」**：把所有注册项目的非 archived change 拉平成一条流，按最近动静倒序。每行看得见：项目徽标、`#seq slug`、状态、`tier·type`、summary（缺省回退标题）、TODO 与 AC 进度、非主 worktree 时的 `⎇branch@worktree`、质量门 blocker（有才显示）、最近动静。3 天内没动过的行降饱和并以分界线区隔——降权不过滤，久未动的 draft 仍在。流的上方每个项目一张摘要条卡（名字、目录、主分支、worktree 数、五状态计数、backlog 数、as-of），同样按 3 天规则降饱和。

**第二视图「概要卡」**：改版前的每项目一张卡，信息面不变。顶部卡区切换两视图，视图态记在 URL hash（`#/` = change 流、`#/cards` = 概要卡），刷新停在原视图。

**下钻**：项目条卡、change 行、概要卡都可点，直达该项目泳道页（内容与 `--project` 一致），页头「← 返回首页」回默认 change 流，浏览器返回键按历史恢复进入前的视图。`--scan` 临时并入的未注册项目同样可点。

- 项目由稳定键区分（可读名 + 项目根路径哈希），同名项目、注册名与配置名不一致、中文名都各有各的地址，不会串门
- `--serve` 下路由是 `/p/<key>`，路由表逐请求重建：serve 挂着时新注册的项目立刻能点进去，不用重启；访问失效或未知地址给一张列出当前可下钻项目的指引页，不是崩溃或空白
- `--html` 快照把各项目泳道数据一并内嵌单文件，用 hash 路由切同样三种视图，离线打开全程零网络请求

**活跃判定**：项目与 change 的「最近动静」取 commit 时间与 `changes/`、`backlog/` 文件 mtime 的最大值——未提交的编辑也算动静，改完文件不必先 commit 就能浮到流顶。活跃窗口 3 天。

## 配置解析规则

1. 从当前目录向上找 `.eo-project.json`
2. 同目录存在 `.eo-project.local.json` → 顶层字段覆盖合并（local 优先）
3. 合并结果校验必填：`project_name` / `mode`（vault|local）/ `project_root`（绝对路径）/ `doc_root`（相对路径）；缺失或非法 → 明确报错 + `/eo-project-init` 指引，不展示空看板

## 缓存行为（--serve）

- 仓库无变化：轮询命中缓存直接应答（stderr 有 hit 诊断行）
- 有变化：一个轮询周期（3 秒）内页面反映新数据；并发请求同槽只重建一次（单飞），多项目槽互不阻塞
- 单次运行形态（终端 / --html）不使用缓存，永远全量扫描
- 聚合页首页与下钻泳道页共用同一批项目缓存槽：从首页点进某个项目，用的是首页刚建好的那份数据，不会为下钻再扫一遍
