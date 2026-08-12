---
title: eo-board 看板现状
type: state
tags: [eo-board, cache, config, collaboration, aggregate, card, gates, journal]
created: 2026-07-24
updated: 2026-08-12
scope: 想了解看板能做什么、配置怎么生效时
status: active
source: cli/eo-board
summary: >
  eo-board 提供终端/HTML/本地服务三种只读看板；多项目聚合页是「change 流 ⇄ 概要卡」双视图首页，点卡/点行即下钻该项目泳道页；
  泳道 change 卡面有阶段徽标与 ≥3 轮警告，详情抽屉为五 tab（概览含 frontmatter / 清单 / 质量门当前状态 / 动态 journal 逆序 / 全文 mdBlock）；
  --serve 有每项目缓存，仓库无变化时轮询不重扫，有变化 3 秒内上板。
conclusions:
  - 配置缺必填字段不再静默兜底——报错并提示运行 /eo-project-init（协作者 clone 场景引导生成 local 覆盖）
  - 缓存对以下变化敏感：新 commit、任何 ref 增删移（含同 SHA 换分支）、change/backlog/roadmap 文件改动、跨日期边界
  - 看板严格只读：不写任何项目文件，数据源是 change.md frontmatter 与质量门报告，而非 Obsidian stub
  - 聚合页默认看到的是「哪个 change 在动」而不是「有哪些项目」；archived change 不进流，只在计数里可见
  - 泳道卡详情：五 tab 定位；质量门「当前状态」与卡面阶段/blocker 同源；journal 最新在上；全文迷你 markdown（链接仅 http/https/mailto）
  - 3 天无动静只降权不过滤--久未动的 draft 仍在流里，不会因为放久了而从视野消失
  - 多 worktree 并行同一 change：同 id 只出「最近活动」最新的一张卡；内容实质分叉的其余变体收进卡面「分叉×N」徽标与详情副本列表（可切换查看），一致副本合并无标记；状态严格低于 main worktree 的过期版本过滤不出卡也不计入 N（遗留 worktree 未回拉不污染）
  - 卡片类展示（泳道卡面 / 聚合行 / 详情概览）branch 与 worktree 分行显示；终端表格列维持连成一行
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

## 泳道页 change 卡（HTML / serve）

点开状态列上的 change 卡进入详情抽屉（backlog 卡详情形态未改；**终端摘要不投影** tab / journal / frontmatter 新面）。

### 卡面

- **AC / TODO 进度条**（正文 checkbox 现场计数）
- **阶段徽标**（如 `review P1×1`、`test ≈2 轮`）：只标「当前」质量门阶段，不把已完全通过的历史报告当当前
- **轮次警告**：任一质量门轮次 ≥ 3 时卡面挂 `card-warn` 样式——与是否有活动阶段**解耦**（archived / 已通过但历史轮次高时仍可警告）
- **blocker 标签**（⛔）：质量门未过或台账未决时的一句话卡点
- 其他标签：分支 worktree（卡片类分行显示：`⎇ branch` / `worktree_name` 各占一行；分叉时出卡也显标记）、分叉徽标（`分叉×N`，N = 未出卡的其余内容变体数）、commits、issue/PR、测试锁定短 sha 等

### 详情五 tab

| tab | 内容 |
|-----|------|
| **概览** | change.md 完整 YAML frontmatter 键值（缺省/空字段不占行）+ 派生信息（最近活动、worktree、commits…）+ 意图 §1 / 决策 |
| **清单** | 验收清单 §2 + TODO §3（轻档无 TODO 时有说明） |
| **质量门** | 顶部 **当前状态**（阶段、卡点、未决明细；无卡点显式「当前无卡点」）+ 各门报告速报与轮次；serve 热刷新时保留你当前选中的 tab |
| **动态** | `tmp/eo/loop/<change-id>/journal.md` 最近若干条窗口报告，**最新在上**；条目正文迷你 markdown 渲染；无 journal 时空态提示 |
| **全文** | 该 change.md 全文迷你 markdown 渲染（标题/表格/代码块/列表/checkbox/分割线/粗体/行内代码/安全链接） |

### 质量门「当前」口径（给人看）

- **阶段**：只展示仍未决的门（速报不通过、台账未决、FAIL 未过等）；**「有保留通过」不算完全通过**
- **未决明细**：以 finding 台账状态 **`open` / `fixed`** 为单一来源（复审核销前 fixed 仍算未决）；`verified` / `waived` / `superseded` **不**当当前卡点回退
- **blocker**：与卡面 ⛔ 同源；有未决 P0/P1 或明确不通过时可见

### 迷你 markdown 边界

- 先 HTML 转义再做白名单结构转换，**零第三方**依赖
- 链接：仅 `http` / `https` / `mailto` 生成可点 `href`；`javascript:` / `data:` 等只保留可见文字
- 能力不足处（如复杂嵌套粗体）作段落可读，不报错

## 聚合页：双视图首页与下钻（`--all --html` / `--all --serve`）

**默认视图「change 流」**:把所有注册项目的非 archived change 拉平成一条流,按最近动静倒序。每行看得见:项目徽标、`#seq slug`、状态、`tier·type`、summary(缺省回退标题)、TODO 与 AC 进度、非主 worktree 或分叉时的 `⎇ branch` / `worktree` 分行标记、质量门 blocker（有才显示）、最近动静。3 天内没动过的行降饱和并以分界线区隔--降权不过滤,久未动的 draft 仍在。流的上方每个项目一张摘要条卡(名字、目录、主分支、worktree 数、五状态计数、backlog 数、as-of),同样按 3 天规则降饱和。

**第二视图「概要卡」**：改版前的每项目一张卡，信息面不变。顶部卡区切换两视图，视图态记在 URL hash（`#/` = change 流、`#/cards` = 概要卡），刷新停在原视图。

**下钻**：项目条卡、change 行、概要卡都可点，直达该项目泳道页（内容与 `--project` 一致，含上节五 tab 详情），页头「← 返回首页」回默认 change 流，浏览器返回键按历史恢复进入前的视图。`--scan` 临时并入的未注册项目同样可点。

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
