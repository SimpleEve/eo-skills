---
id: eo-helper-entry
seq: 8
title: eo-helper 单一交互入口 + eo-board --all 聚合形态 + 命令面收纳
summary: 新增 eo-helper 数字菜单唯一入口；eo-board --all 补 --html/--serve；README 命令面收纳
status: archived
tier: full
type: feature
base_commit: 6998899d55eba93a0e3a0335a4e013780c298796
plan_revision: 1
fix_rounds: 2
fix_consumed: ["review#1", "acceptance#AC-9@14f7307"]
commits: ["8512f1c", "9c70a58", "14f7307", "dabaf0b", "5581b61", "c757368", "4233bce", "b57a106", "874a80d"]
issue: ~
pr: ~
created: 2026-07-25
---

# eo-helper 单一交互入口 + eo-board --all 聚合形态 + 命令面收纳

## 速览

- **改什么**：一条 `eo-helper` 数字菜单命令覆盖全部高频动作；多项目看板从终端行升级为一页网页（`--all --html/--serve`）；README 只教这一条命令
- **为什么**：命令面太复杂记不住——`eo-board`/`eo-sync` 两个 CLI 十来个旗标组合，用户拍板收纳成单一入口
- **行为差异**：之前——想看多项目只有终端表格，日常要背 `eo-board --all` / `eo-sync watch --all` 等一串命令 → 之后——只记 `eo-helper`，选数字即达（选项会回显底层命令，用熟了自然脱壳）；浏览器里一页看全部项目状态且 3 秒热刷新
- **怎么验**：AC 9 条（人工 1 条）；`sh install.sh` 后任意目录跑 `eo-helper` 直接试

## 1. 意图

来源：backlog 卡 `backlog/2026-07-25-eo-helper-single-entry.md`（用户 2026-07-25 拍板三点）。核心痛点是**命令面复杂度**：C1–C3 交付后 CLI 能力齐了，但入口碎——用户记不住旗标组合。三点一体：① 兑现 C3 遗留 OQ-1（`--all` 的 web 聚合形态，本 change 落地即予销号）；② `eo-helper` 数字菜单做唯一交互入口，**薄壳转发既有 CLI，不复制任何业务逻辑**；③ README 主推 eo-helper，全量 CLI 参数下沉 `docs/cli-reference.md`。

已钉决策（来自用户拍板 + 既有 decisions，不重问）：

- 聚合形态 → `eo-board --all` 补 `--html`/`--serve`，多项目一页看板；serve 复用既有每项目缓存槽与单飞（来源：用户拍板 ①，C3 OQ-1）
- 单一入口 → 新增 `eo-helper` 数字菜单 CLI，覆盖高频动作，选项即转发既有 CLI（薄壳），零第三方依赖（来源：用户拍板 ②）
- 命令面收纳 → README 主推 eo-helper；全量 CLI 参数下沉新文档 `docs/cli-reference.md`（来源：用户拍板 ③）
- eo-board 宪法四条不动摇 → 只读铁律 / 不做清单（零第三方依赖、无 SSE、无写操作）/ 性能靠缓存 / GitHub 仅可选旗标；聚合 serve 仍绑 127.0.0.1、沿用 3 秒轮询（来源：`decisions/2026-07-24-dashboard-deprecated-board-cli.md`）
- eo-helper 归属 → 独立单文件 CLI（`cli/eo-helper`），不并入 eo-board：它跨 board/sync 两域转发，塞进哪个都破坏单一职责；实现语言 Python stdlib，与既有 CLI 同款单文件手法（假设，用户未逐条确认）
- 菜单条目与交互形态 → 由 §5.2 裁决（任务指定裁决位）
- 用户文案术语 → 面向用户的文案（菜单/README/安装提示）不出现「投影」，改用「同步看板卡片」「看板自动跟手」类通俗表述；协议文档与内部规范（sync-adapter-protocol、eo-shared 等）保留「投影」术语不动（来源：用户对齐 2026-07-25）
- 聚合页视觉 → 沿用现有 eo-board HTML 设计语言，不出 variants 对比稿（来源：用户裁决 2026-07-25）

## 2. 验收清单

- [x] AC-1 用户跑 `eo-board --all --html` 得到自包含聚合快照：每个注册项目一个区块（状态计数 + backlog 数 + as-of 戳），失效/非法条目行内显示错误不缺席不中断；`-o` 指定输出路径与单项目 `--html` 语义一致（验证：≥2 个注册项目 + 1 条坏路径条目下生成并打开）
- [x] AC-2 用户跑 `eo-board --all --serve` 得到多项目一页看板，某项目 change 状态流转后页面在轮询间隔内自动刷新；数据无变化的重复请求命中缓存（stderr hit 诊断），同项目并发请求只触发一次重扫（验证：挂 serve 后手改一个 change 的 status 观察页面；缓存/单飞以 `build_data` 调用计数断言为准——稳定键重复请求计数不增、同槽并发只增 1，stderr hit/miss 仅作辅助观察）
- [x] AC-3 serve 挂起期间新注册的项目无需重启即出现在聚合页（每轮重读注册表）；注册表缺失/为空时页面显示注册指引而非空页或报错（验证：serve 挂起时在新项目目录 `eo-board --register` 后刷新页面）
- [x] AC-4 用户在任意目录运行 `eo-helper` 看到数字菜单（条目清单见 §5.2），选数字后**先回显将执行的底层命令再执行**，用户可据此渐进学会原生命令
- [x] AC-5 转发不复制逻辑：底层命令的输出与报错原样透传；短命令（同步一次/终端速览等）结束后回到菜单，失败时非零退出状态明确回显（非零状态可见，不静默）；长驻命令（serve/watch）接管前台且 Ctrl+C 行为与直接运行一致
- [x] AC-6 异常路径：stdin 非 TTY 时 `eo-helper` 打印菜单↔命令对照表后直接退出（不挂起等输入）；输入非法编号提示重选；菜单态按 Ctrl+D（EOF）/Ctrl+C 与 `q` 同款干净退出（无 traceback）；在无 `.eo-project.json` 的目录选项目级条目时原样转发、用户看到的是底层 CLI 自己的报错与 init 指引（helper 不自检配置），全局选项（多项目看板/看板自动跟手）照常可用（验证：`echo | eo-helper` 看对照表退出；在 $HOME 下逐项试）
- [x] AC-7 `sh install.sh` 后 `eo-helper` 在 PATH 可用，安装完成提示以 eo-helper 为主推入口（验证：临时前缀安装后 `command -v eo-helper`）
- [x] AC-8 README 用 `eo-helper` 一条命令讲完看板与同步入口，原全量 CLI 旗标细节移入 `docs/cli-reference.md` 且 README 给出链接；cli-reference 覆盖 eo-board/eo-sync/eo-helper 三命令全部参数（验证：README 正文 grep 不到 `--scan`/`--interval` 等深层旗标，也 grep 不到「投影」表述——该术语只留在协议与内部文档；对照 `--help` 核 cli-reference 完整性）
- [x] AC-9 README 重构后新用户视角通读顺畅——只需记 `eo-helper` 一条命令即可跑通「初始化后看板+同步」日常（人工:通读 README 安装→第一次使用→看板一节 → 过目认可）（确认：用户重验依赖节清理后通读通过，原话「通过，直接归档」· 2026-07-26 · 基线 b57a106）

## 3. TODO

### Batch 1（MVP：eo-board --all 聚合形态）

- [x] TODO-1 聚合数据层重构：`_aggregate_row` 的数据获取改为可注入（单次运行直连 `build_data`；serve 走 `get_board_data_cached` 缓存槽+单飞），as-of 戳随数据产生时刻走（缓存命中时保持构建时刻不重打）；新增 `build_all_data()` 产出结构化聚合 JSON（rows/reg_count/scanned_count），终端渲染改为消费它（文件：修改: cli/eo-board、tests/test_eo_board_cache.py；对应 AC-1、AC-2；完成判据：既有 `--all` 终端行为回归绿 + 注入两种 getter 的单测绿 + 缓存命中行 as-of 保持缓存构建时刻不按请求时刻重打的断言绿）
- [x] TODO-2 `--all --html`：聚合 HTML 模板（自包含、JSON 注入 + 前端渲染，与单项目同款手法）+ `cmd_all` 分派 `--html`（`-o`/缺省 tmp 路径语义与单项目一致）（文件：修改: cli/eo-board、tests/test_eo_board_cache.py；对应 AC-1；完成判据：聚合 HTML 静态断言绿——每项目区块、坏条目行内错误、`-o` 与缺省路径两分支——加 `--all --html` argparse 正例）
- [x] TODO-3 `--all --serve`：复用 `ThreadingHTTPServer` 起聚合服务（`/` 聚合页 + `/data.json` 聚合数据），每次数据请求重读注册表、逐项目走缓存槽（跨槽并行）、坏条目行内错误、空注册表返回指引页；前端 3 秒轮询 hash 比对热刷新沿用（文件：修改: cli/eo-board、tests/test_eo_board_cache.py；对应 AC-2、AC-3；完成判据：serve handler 断言绿——每请求重读注册表、坏条目行、空注册表指引——加 `build_data` 调用计数断言（稳定键重复请求不增、同槽 N 路并发仅 +1、双槽并行各 +1）与 §5.1 组合矩阵的 argparse 正反例）

### Batch 2（eo-helper 单一入口）

- [x] TODO-4 新增 `cli/eo-helper`：数字菜单循环（条目与交互按 §5.2），选项回显底层命令后转发；短命令 subprocess 前台执行完回菜单（非零退出状态回显）、长驻命令 `os.exec*` 接管进程；非 TTY 打印对照表退出、菜单态 EOF/Ctrl+C 干净退出；只维护固定 argv 映射、不读项目配置不做前检（项目级报错与 init 指引全部由底层 CLI 透传）；Python stdlib 单文件零第三方依赖（文件：新增: cli/eo-helper、tests/test_eo_helper.py；对应 AC-4、AC-5、AC-6）
- [x] TODO-5 安装接线：install.sh 的 cli 安装列表加 `eo-helper`，安装完成提示改为主推 `eo-helper`（文件：修改: install.sh；对应 AC-7）

### Batch 3（命令面收纳）

- [x] TODO-6 新增 `docs/cli-reference.md`：eo-board / eo-sync / eo-helper 三命令全量参数与示例下沉于此（含 `--scan`、`--interval`、`--port`、注册表维护等深层旗标），并链接既有协议/迁移文档（文件：新增: docs/cli-reference.md；对应 AC-8；完成判据：cli-reference 旗标集合与三命令 `--help` 输出机械核对一致、无缺漏）
- [x] TODO-7 README 收纳重构：原「看板与投影：两个 CLI」一节改为「看板与同步」——eo-helper 主推 + 极简速查（几条最常用原生命令）+ 链接 cli-reference；「第一次使用」与安装提示同步改口径；面向用户文案全部去「投影」术语（协议文档不动）；docs/GUIDE.md 相应入口段落同步（文件：修改: README.md、docs/GUIDE.md；对应 AC-8、AC-9；完成判据：README 正文无深层旗标残留且无「投影」表述，GUIDE 入口段与 README 口径一致）

> 批间串行：Batch 2 的菜单条目转发 Batch 1 新增的 `--all --serve`（消费其 CLI 形态，构成逻辑依赖）；Batch 3 文档要引用两边落定的最终形态。不标并行组。

## 5. 技术方案

触发：新交互形态（菜单）+ 聚合 serve 架构需编码前钉死；菜单条目与交互形态按任务指定在本节裁决。

### 5.1 `--all` 聚合的 HTML/serve 架构

- **一页 = 概览页**：每项目一个卡片区块（项目名、五状态计数、backlog 数、as-of、错误行内展示），信息面与终端 `--all` 对齐、视觉升级；**不内嵌单项目完整看板**（页面内下钻 defer，见 OQ-1）——下钻继续用 `eo-board --project`
- **视觉已钉**：聚合页沿用现有 eo-board HTML 的设计语言（配色/排版/组件手法同款延伸），不出 variants 对比稿（用户裁决 2026-07-25）
- **参数组合矩阵**（P1-4 裁决）：合法——`--all`（终端）、`--all --html [-o PATH]`、`--all --serve [--port N] [--no-open]`；`--scan <父目录>` 与三形态正交组合皆合法（它只是数据源并集：注册表之外临时并入一层子目录，serve 下与注册表同步每轮重枚举）；继续拒绝——`--all --project`、`--register`/`--unregister` 与任何输出模式混用、`-o` 在非 `--html` 下使用（沿用既有报错）；正反例进 TODO-3 的 argparse 测试
- **serve 复用既有缓存**：聚合 handler 每次 `/data.json` 请求重读注册表（新注册项目即时纳入，呼应 watch 的每轮重读语义），逐项目调 `get_board_data_cached`——槽键仍是各项目 config_path，同槽单飞、跨槽并行，全部既有机制零改动；聚合层自身不再加第二层缓存（槽层已挡住重扫成本）
- **单次运行（`--html`）不走缓存**：与单项目现状一致，天然全量扫
- **宪法核对**：只读 ✓；零第三方依赖（stdlib http.server + 内嵌 JS）✓；仅绑 127.0.0.1 ✓；无 SSE（沿用 3 秒轮询）✓

### 5.2 eo-helper 菜单条目与交互形态（裁决）

```
$ eo-helper
eo-helper · eo-skills 日常入口（选数字，q 退出）
  1) 本项目实时看板       → eo-board --serve
  2) 所有项目一页看板     → eo-board --all --serve
  3) 注册本项目到多项目看板 → eo-board --register
  4) 同步看板卡片（跑一次）  → eo-sync run
  5) 看板自动跟手（常驻）   → eo-sync watch --all
  6) 终端速览：本项目      → eo-board
  7) 终端速览：所有项目    → eo-board --all
```

- **菜单文案术语**：面向用户条目不用「投影」（4/5 号如上表），与 README 收纳口径一致；内部实现与协议文档保留术语
- **回显即教学**：每次选择先打一行 `→ 正在执行：<底层命令>` 再执行，菜单右列常驻显示映射——薄壳同时是命令面的学习路径
- **短命令回菜单，非零状态可见**（P1-2 裁决）：3/4/6/7 用 subprocess 前台执行（stdio 直通），结束后回菜单；子进程非零退出时回菜单前明确回显一行退出状态（如 `↑ eo-sync run 退出码 1`）——「不吞错误码」的契约即「非零状态可见」，helper 自身菜单循环正常退出返回 0；1/2/5 用 `os.exec*` 替换进程（信号/Ctrl+C/最终退出码与直接运行完全一致，helper 不留守护壳）
- **非 TTY 守卫与菜单态退出**：stdin 非 TTY 时打印上表（菜单↔命令对照）后退出码 0，绝不阻塞脚本/管道、不拉起子进程；交互态下 EOF（Ctrl+D）与菜单态 Ctrl+C 一律与 `q` 同款干净退出（退出码 0，无 traceback）；长驻子命令接管后的信号行为完全归底层 CLI
- **薄壳边界**（P1-3 裁决）：helper 只维护固定 argv 映射，**不读项目配置、不做配置前检**——项目级选项在无配置目录也原样转发，`.eo-project.json` 的发现、local 合并与 init/修复指引全部由底层 CLI 负责并原样透传（既有 eo-board/eo-sync 均已内置该指引）；不解析业务输出、不加旗标翻译；底层 CLI 不在 PATH 时给 install.sh 指引；skill 侧动作（如 /eo-project-init）不进菜单（仅在指引文案中提及）

### 5.3 命令面收纳口径

- README 原「看板与投影：两个 CLI」一节改名「看板与同步」并收缩为「一条命令：eo-helper」+ 3-5 行最常用原生命令速查 + cli-reference 链接；FAQ 保留但口径同步
- **术语口径**：README/菜单/安装提示等面向用户文案不出现「投影」——改说「同步看板卡片」「看板自动跟手」类通俗表述；`docs/sync-adapter-protocol.md` 等协议文档与内部规范保留「投影」术语不动（用户对齐 2026-07-25）
- `docs/cli-reference.md` 结构：每命令一节（概述→形态→全量旗标表→示例），以 `--help` 输出为完整性基准；README/GUIDE 深层旗标一律链接至此不重复

## 8. 开放问题

- OQ-1 聚合页内点击下钻单项目完整看板（defer 原因：概览页 + `--project` 已覆盖刚需，页面内路由属重量回长，等真实使用信号——C3 OQ-1 的收敛姿势同款）
- OQ-2 eo-helper 菜单是否需要用户级自定义（隐藏/追加条目）（defer 原因：先固定七项验证入口收纳是否成立，自定义等真实诉求）
