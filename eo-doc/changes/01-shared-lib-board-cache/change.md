---
id: shared-lib-board-cache
seq: 1
title: 抽取共享解析库并修复 eo-board local 合并与缓存
summary: cli 解析能力抽为共享库供 eo-sync 复用；eo-board 补 local 覆盖合并，--serve 加缓存
status: archived
tier: full
type: enhance
base_commit: 792522dc3d10117d6cf140e28c2ecd0e5bdf2f63
plan_revision: 1
fix_rounds: 1
fix_consumed: ["review#1"]
commits: ["9b3bc69", "72b1946", "5ac8d27", "5e81f33", "0c0219f", "9235e41"]
issue: ~
pr: ~
created: 2026-07-24
---

# 抽取共享解析库并修复 eo-board local 合并与缓存

## 速览

- **改什么**：把 frontmatter 解析 / change 扫描 / AC-TODO 计数 / git 封装 / 配置加载从 `cli/eo-board`（1925 行单文件）抽成共享库；顺手补上 eo-board 缺失的 `.eo-project.local.json` 合并，给 `--serve` 加每项目缓存
- **为什么**：C2（eo-sync 插件层）要复用同一套解析能力，本 change 是 P0 地基；同时 eo-board 当前无视 local 覆盖、`--serve` 每 3 秒轮询都全量重扫
- **行为差异**：之前 local 覆盖字段对看板不生效、serve 每次轮询全量重算（多 worktree + 多次 git 子进程）→ 之后 local 覆盖生效；仓库没动时轮询直接命中缓存，有改动后一个轮询周期内上板
- **怎么验**：AC 6 条（人工 0 条）；本仓跑 `eo-board` / `eo-board --serve` 对比抽取前后输出即可

## 1. 意图

eo-board 是当前唯一呈现层，其内部已经手写了一整套「文件契约消费」能力：frontmatter 简易 YAML 解析、change 目录扫描与 change.md 各节解析、AC/TODO checkbox 计数、git 子进程封装、`.eo-project.json` 定位与加载。C2 将落地的 eo-sync（投影插件层）需要完全相同的能力——不抽库则两处手写、双份腐烂。故本 change 先把这五域平移为共享模块（行为不变的内部重构子任务），并在同一次触碰中补齐 eo-board 两处用户可见增强：① 配置加载未做 `.eo-project.local.json` 顶层覆盖合并（skill 侧契约已定义，eo-board 未跟上）；② `--serve` 模式前端每 3 秒轮询 `/data.json`，后端每次请求都全量重扫全部 worktree + 全部 change + 多次 git 子进程调用。因含新增可见行为（local 覆盖生效、错误呈现、缓存性能），type 取 `enhance` 而非 refactor。

已钉决策（来自 brainstorm 捕获与 decisions，整体移交继承）：

- **变更前基线 = commit `792522d`**（前置工作已结算入库：`cli/eo-board` 1925 行单文件、install.sh 的 CLI 符号链接安装入口、skill 侧 local 合并契约三项均在该 commit 及其父提交中可追溯）；`base_commit` 依约仍由 eo-implement 首次执行时写入，且不得早于 `792522d`

- eo-board 四条宪法 → 本方案全程合宪：只读铁律（缓存只是派生数据的进程内副本）；不做清单（零第三方依赖，仅标准库；不加 SSE——前端 3 秒轮询保留，改的是后端不再每次重算；无写操作）；性能靠缓存不靠架构（HEAD + mtime 判新鲜度）；GitHub 仅可选旗标不受影响（来源：`decisions/2026-07-24-dashboard-deprecated-board-cli.md`）
- `.eo-project.local.json` 顶层字段覆盖合并、local 优先、必填校验看合并结果（来源：brainstorm 关键决策 #1，已在 skill 侧落地，本 change 让 eo-board 对齐）
- 共享库的下游消费方是未来 eo-sync（C2）→ 抽取边界据此定：eo-sync 会消费的进库（解析/扫描/计数/git/配置），纯呈现职责（门禁判定、终端/HTML 渲染、HTTP 服务）留在 eo-board（来源：`decisions/2026-07-24-sync-plugin-layer.md`）
- 本 change 为 C1（P0 地基），C2/C3 依赖其共享库（来源：brainstorm 决策与分流表）
- 共享库落位 `cli/eo_lib/` Python 包；eo-board 以 `Path(__file__).resolve()` 定位真实文件所在仓库后导入，install.sh 的符号链接安装方式不变（假设，用户未逐条确认；备选见 §8 OQ-1）
- 缓存为进程内存缓存、不落盘；新鲜度键在宪法「HEAD + changes 目录 mtime」基础上扩展为闭合 `build_data` 全部动态输入的依赖集合：backlog / roadmap 数据源 mtime、worktree (路径, 分支名, HEAD) 三元组集合、refs 指纹（覆盖「本月直改」统计的 `git log --all` 输入）、当天日期（覆盖停滞天数等日期派生字段）——vault 模式下 backlog/roadmap 在仓库外且日期/refs 不体现在 HEAD 上，不纳入则 `--serve` 对它们永久陈旧（假设，用户未逐条确认；依赖清单见 §5）
- 共享层错误所有权：库不终止进程——配置/解析失败抛携带文件路径与原因的 `ConfigError`，由 CLI 入口（eo-board，将来 eo-sync）捕获、格式化 stderr 并退出（假设，用户未逐条确认）

## 2. 验收清单

- [x] AC-1 抽取后行为不变：同一仓库状态下，eo-board 终端 / `--html` / `--serve` 三形态输出与抽取前一致（验证：基线取自 `792522d`——临时 worktree 上运行终端 / `--html` 形态并直接调 `build_data` 采样 JSON，抽取后 diff 逐字段等价（生成时间类字段除外）；`--serve` 数据面与 `/data.json` 同源自 `build_data`，起服务的端到端对照由测试阶段以同法比较）
- [x] AC-2 共享库可独立复用：不经 eo-board，直接 `python3 -c "import ..."` 即可调用五域能力——frontmatter 解析、change 目录扫描、AC/TODO 计数、git 封装、配置加载（验证：对本仓跑一段冒烟脚本，各域返回结构化结果）
- [x] AC-3 local 覆盖生效：仓库存在 `.eo-project.local.json` 时，eo-board 按顶层字段覆盖后的合并结果工作（如 local 覆盖 `project_root` 后，backlog/roadmap 从新位置读取）；无 local 文件时行为与现在完全一致（验证：临时写一个覆盖 `project_root` 的 local 文件跑终端形态，观察 backlog 数据源变化，验后删除复原）
- [x] AC-4 local 解析失败可见：`.eo-project.local.json` 存在但 JSON 非法时，用户看到指明该文件与原因的报错并退出（与主配置解析失败同口径），而非静默忽略或裸 traceback
- [x] AC-5 缓存命中：`--serve` 运行中仓库无变化时，后续 `/data.json` 轮询由缓存直接应答、不再全量重扫（验证：以 `build_data` 调用计数断言——同状态连续两次请求，第二次不触发全量扫描（计数不增）；stderr 的 hit/miss 诊断行仅作辅助观察，不作为通过依据）
- [x] AC-6 缓存新鲜：`--serve` 运行中出现新 commit、任何 ref 更新（含同 SHA 分支切换）、change.md / backlog 卡 / roadmap.md 改动，或跨过日期边界后，一个轮询周期（3 秒）内数据即反映变化（停滞天数、本月直改等派生字段同步刷新），无需重启服务（验证：serve 运行中手改某 change.md 的 status，浏览器 3-6 秒内看到卡片移列；日期/refs 类失效由确定性用例覆盖，见 TODO-4 完成判据）

## 3. TODO

### Batch 1（MVP：抽库，行为不变）
- [x] TODO-1 新建 `cli/eo_lib/` 共享包，从 eo-board 平移五域实现：`config.py`（`find_project_config`/`load_project_config`）、`gitio.py`（`run_git`/`list_worktrees`）、`frontmatter.py`（`split_frontmatter`/`parse_yaml_subset`/`parse_yaml_scalar`/`unquote`）、`changes.py`（`split_body_sections`/`parse_ac_section`/`parse_todo_section`/`parse_oq_section`/`parse_change_file`/`scan_all_changes` 及 AC-TODO 计数）；平移时错误所有权同步落地——`config.py` 不再调用 `die()`，改抛携带路径与原因的 `ConfigError`，由调用方 CLI 入口捕获退出（文件：新增: cli/eo_lib/__init__.py、cli/eo_lib/config.py、cli/eo_lib/gitio.py、cli/eo_lib/frontmatter.py、cli/eo_lib/changes.py；对应 AC-1、AC-2；完成判据：包不依赖 eo-board 可独立 import，五域函数签名与语义同 `792522d` 版实现等价，库内无任何 `sys.exit`/`die` 调用）
- [x] TODO-2 `cli/eo-board` 改为消费共享包：删除被平移的实现，头部加符号链接安全的导入引导（`Path(__file__).resolve()` 定位真实仓库内 `cli/` 后 import）；board 专属逻辑（gates 门禁判定、backlog/roadmap 聚合、渲染、HTTP 服务）留在原文件，并在入口捕获 `ConfigError` 格式化退出（文件：修改: cli/eo-board；对应 AC-1；完成判据：不起服务——终端 / `--html` 形态输出及 `build_data` 直调 JSON 与 `792522d` 基线 diff 等价，经符号链接调用亦正常；`--serve` 端到端对照归测试阶段）

### Batch 2a（local 合并）
- [x] TODO-3 `config.py` 实现 `.eo-project.local.json` 顶层字段覆盖合并（local 优先，合并后再做缺省填充；local 存在但 JSON 非法 → 与主配置同口径报错退出），eo-board 经共享包自动获得（文件：修改: cli/eo_lib/config.py；对应 AC-3、AC-4）

### Batch 2b（--serve 缓存）
- [x] TODO-4 共享包新增新鲜度键计算，闭合 `build_data` 全部动态输入：各 worktree (路径, 分支名, HEAD sha) 三元组、refs 指纹（`git for-each-ref` 输出摘要，覆盖 `git log --all` 的「本月直改」统计输入）、当天日期（覆盖停滞天数 / 当月边界等日期派生字段）、`<doc_root>/changes/` 目录树 max-mtime、backlog / roadmap 数据源 mtime，产出可比较的键（文件：新增: cli/eo_lib/freshness.py；对应 AC-5、AC-6；完成判据：同状态两次计算键相等；三类确定性用例各证键变化——① 跨日/跨月（mock 日期）② 同 SHA 切换分支 ③ 仅 ref 更新（如新建 tag/分支、worktree 集合不变）；另 changes/backlog/roadmap 任一源改动后键变化）
- [x] TODO-5 `--serve` 请求处理接入每项目进程内缓存：`/data.json` 与 `/` 请求先算新鲜度键，命中返回缓存的 build_data 结果，miss 才重扫并更新缓存；hit/miss 各在 stderr 记一行诊断（文件：修改: cli/eo-board；对应 AC-5、AC-6；完成判据：不起 HTTP 服务——对缓存层/handler 以 `build_data` 计数替身做确定性检查：同键第二次取数不进入 `build_data`，键变化后重新进入；起服务的端到端断言归测试阶段）

## 4. 涉及文件

- `install.sh` — 无需改动（连带确认项）：`792522d` 已含 CLI 符号链接安装逻辑，安装仍是 `cli/eo-board` 单链接，共享包随仓库就位，由 TODO-2 的真实路径引导解析；AC-1 验证含经符号链接调用

## 5. 技术方案

触发：新增共享库边界（新架构模式）+ 缓存策略。

**抽取边界**（判据：eo-sync 会消费的进库，纯呈现留 board）：

| 域 | 入库 | 留 eo-board |
|----|------|------------|
| 配置 | find/load + local 合并 | board/github 段的开关消费 |
| git | run_git、list_worktrees | 各 change 的 git 统计聚合（compute_change_git_stats 依赖呈现语境，暂留，C2 需要时再上移） |
| frontmatter | 全部（简易 YAML 子集） | — |
| change 扫描 | change.md 解析、目录扫描、AC/TODO/OQ 计数 | 门禁判定（gates）、报告轮次估算 |
| 呈现 | — | 终端/HTML 渲染、HTTP 服务、backlog/roadmap 扫描（C3 多项目化时再议是否上移） |

**导入方式**：eo-board 保持无扩展名单入口可执行文件；头部以 `sys.path.insert(0, str(Path(__file__).resolve().parent))` 定位真实 `cli/` 目录后 `from eo_lib import ...`——符号链接安装（install.sh 现状）与仓库内直跑两条路径都成立，零安装步骤。

**缓存设计**：每项目一个进程内缓存槽（键 → build_data 结果）。新鲜度键必须闭合 `792522d` 版 `build_data` 的**全部动态输入**，逐项对应：

| build_data 依赖 | 键成分 |
|----------------|--------|
| 各 worktree 的 change 扫描 | worktree (路径, 分支名, HEAD sha) 三元组集合（分支名单列——同 SHA 换分支时输出的 branch 字段会变） |
| changes 目录内容（含 test/review 等工件与 mtime 派生的末次活动） | `changes/` 目录树聚合 max-mtime |
| backlog / roadmap（vault 模式在仓库外） | 对应目录/文件 mtime |
| 「本月直改」统计（`git log --all`） | refs 指纹（`git for-each-ref` 输出摘要——任何 ref 增删移都改变指纹） |
| 停滞天数、当月边界等日期派生字段 | 当天日期（跨日即失效） |

键计算只做 stat 与少量轻量 git 调用（for-each-ref + 各 worktree HEAD/分支查询；相对全量重扫的多轮子进程 + 全文解析，成本仍低一个量级以上）。后续若 `build_data` 引入新动态输入，键成分须同步扩展——此不变量随抽库落为 `freshness.py` 模块注释级契约。不落盘：落盘缓存引入失效与清理复杂度，serve 常驻进程内存已覆盖收益场景；单次 `--terminal`/`--html` 运行天然全量扫，不受影响。

**错误所有权**：共享层（`eo_lib`）不拥有进程生命周期——一律抛携带文件路径与原因的 `ConfigError`（及后续需要时的同族异常），不调用 `die()`/`sys.exit`；CLI 入口（eo-board，将来 eo-sync）捕获后格式化 stderr 并以非零码退出。AC-4 的用户可见口径由 eo-board 入口层保证。

**宪法合规自查**：仅标准库（零第三方依赖）✓；只读（缓存是派生数据副本，无任何写回）✓；无 SSE/推送（前端 3 秒轮询机制不变，优化在后端命中）✓；GitHub 旗标逻辑不触碰 ✓。

## 8. 开放问题

- OQ-1 共享包形态按最简假设起草（`cli/eo_lib/` 仓库内包 + 路径引导导入）；若 C2 落地时 eo-sync 适配器需要独立分发/安装形态，包位置与导入方式届时重估（defer 原因：真实第二消费者出现前无从裁决，避免过度设计）
- OQ-2 缓存新鲜度是否要对用户可见（如 `data.json` 附 as-of 时间戳字段）——本 change 只做 stderr 诊断行，前端可见新鲜度留待 C3 多项目化（每项目一行 as-of）统一设计（defer 原因：C3 已有该需求条目，此处先做不改输出契约的最小实现）
