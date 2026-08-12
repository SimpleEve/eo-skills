# CLI 参考（eo-helper / eo-board / eo-sync）

三个终端命令的全量参数参考。日常入口是 `eo-helper`（一条命令覆盖高频动作）；本文供需要原生命令与深层旗标时查阅。完整性基准是各命令的 `--help` 输出——两边如有出入，以 `--help` 为准并欢迎修订本文。

- 适配器协议（第三方接入 `eo-sync-<name>`）：[sync-adapter-protocol.md](sync-adapter-protocol.md)
- v1 → v2 迁移：[migration-v1-to-v2.md](migration-v1-to-v2.md)
- 用法详解与设计权衡：[GUIDE.md](GUIDE.md)

---

## eo-helper —— 日常入口（数字菜单）

任意目录运行 `eo-helper`，得到数字菜单；选数字后**先回显将执行的底层命令再执行**——用熟了自然过渡到原生命令。

```
$ eo-helper
eo-helper · eo-skills 日常入口（选数字，q 退出）
  1) 全局实时看板            → eo-board --serve
  2) 注册本项目到多项目看板  → eo-board --register
  3) 同步看板卡片（跑一次）  → eo-sync run
  4) 看板自动跟手（常驻）    → eo-sync watch --all
  5) 全局终端速览            → eo-board
```

| 参数 | 说明 |
|------|------|
| （无参数） | 进入交互菜单；stdin 非 TTY（脚本/管道）时打印菜单↔命令对照表后直接退出，不挂起、不拉起子进程 |
| `-h`, `--help` | 打印菜单↔命令对照表后退出 |

行为约定：

- **薄壳转发**：只维护固定的「编号 → argv」映射，不读项目配置、不做前检；底层命令的输出与报错原样透传（在无 `.eo-project.json` 的目录选项目级条目，看到的就是底层 CLI 自己的报错与 init 指引）
- **短命令**（2/3/5）前台执行完回菜单，子进程非零退出时回显一行退出码（如 `↑ eo-sync run 退出码 1`）
- **长驻命令**（1/4）直接替换进程接管前台，Ctrl+C 行为与直接运行底层命令完全一致
- 菜单态按 `q` / Ctrl+D / Ctrl+C 均干净退出（退出码 0）
- 底层 CLI 不在 PATH 时提示先跑 `sh install.sh`

---

## eo-board —— 只读看板

从 `.eo-project.json` 出发，汇总多 worktree 的 change / backlog / roadmap。**绝不写项目仓库文件**（唯一写例外是用户级注册表 `${EO_HOME:-$HOME/.eo}/projects.json`，且仅在显式 `--register`/`--unregister` 时写）。

### 形态

| 形态 | 命令 | 说明 |
|------|------|------|
| 终端摘要 | `eo-board` | 全局项目聚合：五状态计数 + backlog 数 + as-of 新鲜度戳 |
| 静态快照 | `eo-board --html [-o PATH]` | 全局双视图首页 + 项目下钻，自包含 HTML，缺省写系统 tmp 目录并自动开浏览器 |
| 实时服务 | `eo-board --serve [--port N]` | 全局双视图首页 + 项目下钻；仅绑 127.0.0.1，3 秒热刷新，带每项目缓存 |
| 下钻 | 页内点击 / `eo-board --project <路径\|注册名>` | 聚合页任意项目条卡、change 行、概要卡点击直达该项目泳道页；命令行等价形态三态通用，无需 cd |

### 全量旗标

| 旗标 | 适用 | 说明 |
|------|------|------|
| `-h`, `--help` | — | 显示帮助并退出 |
| `--html` | 全局 dashboard | 生成自包含静态 HTML 快照 |
| `--serve` | 全局 dashboard | 启动本地只读 HTTP 服务（仅绑 127.0.0.1） |
| `--all` | 已退役 | 直接报错并提示去掉旗标；全局 dashboard 已是默认形态 |
| `--project <路径\|注册名>` | 单项目直达 | 下钻指定项目；注册名命中多个时报歧义并列候选 |
| `--scan <父目录>` | 全局 dashboard | 把含 `.eo-project.json` 的一层子目录临时并入聚合（不写注册表），三形态皆可组合 |
| `--register [PATH]` | 注册表维护 | 把项目注册进用户级注册表（缺省 PATH=当前目录；同仓 worktree 幂等） |
| `--unregister [PATH]` | 注册表维护 | 从注册表移除项目（缺省 PATH=当前目录） |
| `-o PATH`, `--output PATH` | `--html` | 指定输出文件路径（默认写系统 tmp 目录） |
| `--port PORT` | `--serve` | 监听端口（默认 7333） |
| `--no-open` | `--html` / `--serve` | 生成/启动后不自动打开浏览器 |

### 聚合页两视图与下钻路由（`--html` / `--serve`）

- **change 流（默认视图）**：跨项目全部非 archived change 按最近活动倒序一条流——项目徽标、`#seq slug`、状态、`tier·type`、summary、TODO/AC 进度、非主 worktree 的 `⎇branch@worktree`、质量门 blocker、最近动静；3 天内无动静的行降权并以分界线区隔（不过滤，只降权）。顶部每项目一张摘要条卡（名字、目录、主分支、worktree 数、五状态计数、backlog 数、as-of）。
- **概要卡（第二视图）**：改版前的每项目一张卡，信息面不变且升级为可点。顶部卡区切换两视图，视图态记在 URL hash（`#/` = change 流、`#/cards` = 概要卡），刷新后停在原视图。
- **下钻**：条卡 / change 行 / 概要卡点击进入项目泳道页，页头项目名是可切换全部可下钻项目的下拉，同时保留「← 返回首页」；浏览器返回键按历史恢复。路由标识 `route_key = <URL 编码项目名>~<项目根路径 hash8>`——同名项目、注册名与配置名不一致、CJK 名、cwd/`--scan` 临时并入的未注册项目都各有稳定键。
  - `--serve`：`/`（首页）、`/p/<route_key>`（泳道页）、`/data.json`（聚合数据）、`/p/<route_key>/data.json`（单项目数据）；未知或失效的 key 返回含回首页链接的指引页。
  - `--html`：同一套 key 走 hash 路由（`#/`、`#/cards`、`#/p/<route_key>`），全部项目泳道数据内嵌单文件，离线零网络请求。

不合法组合（会直接报错）：任何 `--all` 调用、`--scan --project`、`--register`/`--unregister` 混用 `--project`/`--scan`/`-o`、`-o` 用在非 `--html` 模式、`--port` 用在非 `--serve` 模式、`--no-open` 用在非 `--html`/`--serve` 模式。

### 示例

```bash
eo-board                          # 全局终端摘要
eo-board --html -o board.html     # 全局快照到指定路径
eo-board --serve --port 7400      # 换端口起全局实时看板
eo-board --scan ~/projects        # 未注册项目临时扫进来看
eo-board --project my-app         # 按注册名下钻
eo-board --register               # 注册当前项目
```

---

## eo-sync —— 同步看板卡片 / GitHub issue·PR

把 change 状态单向同步到外部呈现目标（Obsidian 看板卡、GitHub issue/PR）。插件化：发现 PATH 上的 `eo-sync-<name>` 适配器，持锁编排一次单向同步；**本地 markdown 是唯一真相源**。目标经 `.eo-project.json` 的 `sync` 段逐项目开启。

> 协议与内部文档（如 [sync-adapter-protocol.md](sync-adapter-protocol.md)）中该机制称「投影」，是同一件事。

### 子命令

| 子命令 | 说明 |
|--------|------|
| `eo-sync run` | 执行一次同步（幂等，跑几遍都无副作用） |
| `eo-sync adapters` | 列出 PATH 上发现的适配器与其 capabilities |
| `eo-sync watch` | 常驻轮询：freshness 键变才 run，键不变零成本跳过 |

### `eo-sync run` 旗标

| 旗标 | 说明 |
|------|------|
| `-h`, `--help` | 显示帮助并退出 |
| `--dry-run` | 只输出提示性计划，全程零写入、不取锁 |
| `--change ID` | 只同步指定 change id |
| `--target NAME` | 只跑指定适配器 |

### `eo-sync watch` 旗标

| 旗标 | 说明 |
|------|------|
| `-h`, `--help` | 显示帮助并退出 |
| `--interval N` | 轮询间隔秒数（默认 10，下限 1） |
| `--all` | 追平注册表全部项目（每轮重读注册表，无需在项目内运行；与 `--project` 互斥） |
| `--project PATH` | 只追平指定路径的项目（无需 cd） |

同一作用域只允许一个 watch 实例（`--all` 撞 `--all`、同仓 `--project` 互撞会报错退出）。

### 示例

```bash
eo-sync adapters              # 看有哪些同步目标、哪些已启用
eo-sync run --dry-run         # 只看计划，不写任何东西
eo-sync run                   # 手动同步一次
eo-sync run --change my-feat  # 只同步一个 change
eo-sync watch --all           # 常驻：所有注册项目状态一变即自动追平
eo-sync watch --interval 5    # 本项目 5 秒一轮
```
