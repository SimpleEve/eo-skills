---
id: registry-board-watch
seq: 3
title: 项目注册表 + eo-board 多项目聚合 + eo-sync watch
summary: 新建 ~/.eo/projects.json 生态注册表；eo-board 多项目聚合与下钻；eo-sync watch 自动追平投影
status: implementing
tier: full
type: feature
base_commit: 85ad4fccba8c983e4c104b8c78b00b00a14ca9c7
plan_revision: 1
fix_rounds: 0
fix_consumed: []
commits: []
issue: ~
pr: ~
created: 2026-07-25
---

# 项目注册表 + eo-board 多项目聚合 + eo-sync watch

## 速览

- **改什么**：一张用户级项目注册表（`~/.eo/projects.json`）+ 跨项目看板一屏总览 + 投影自动追平守护
- **为什么**：多项目现状只能逐个 cd 进去看；看板 stub 在流转期全程滞后，要等归档或手动 run 才跳变
- **行为差异**：之前——每个项目单独进目录跑 `eo-board`，change 状态流转后看板不更新，须记得手动 `eo-sync run` → 之后——任意目录 `eo-board --all` 一屏看全部项目并可下钻；`eo-sync watch` 常驻后状态流转在一个轮询间隔内自动上板
- **怎么验**：AC 11 条（人工 0 条）；init 一个临时项目看注册表 + 挂起 watch 改一个 change 状态直接试

## 1. 意图

两张 backlog 卡合并实施（`backlog/2026-07-24-projects-registry-multi-board.md` 建议的 C3 范围 + `backlog/2026-07-25-eo-sync-watch.md` 明确「建议并入 C3 一个 change 吃掉」）：

1. **生态级项目注册表**：多项目枚举的必要前提。`~/.eo/projects.json` 由 `eo-project-init` 成功时顺手注册、`eo-board` 手工 register/unregister 维护、扫描兜底为辅；eo-board 多项目与 eo-sync `--all` 共用同一张表。
2. **eo-board 多项目聚合**：每项目一行状态机计数 + as-of 新鲜度戳 + 下钻，在四条宪法内实现（只读 / 不做清单 / 缓存 / GitHub 可选旗标）。
3. **eo-sync watch 自动档**（OQ-2 翻案获准）：呈现层自费的 pull——freshness 键短路轮询、键变才 run、复用 flock、`--all` 枚举注册表；第一版终端常驻。

三块都叠加在已归档交付的 change #1（eo_lib + board 缓存）与 change #2（eo-sync 投影核）之上，**纯增量，不重写**。

已钉决策（继承自 decisions 与 brainstorm，不重问）：

- 呈现层归属 → eo-dashboard 废弃、activity 观测彻底放弃；cli/eo-board 唯一呈现层，单/多项目一体（来源：`decisions/2026-07-24-dashboard-deprecated-board-cli.md`，brainstorm #10）
- eo-board 宪法四条 → ① 只读铁律（绝不写项目文件）② 不做清单（无 SSE/无观测/无写操作/零第三方依赖）③ 性能靠缓存不靠架构 ④ GitHub 实时状态仅可选旗标（来源：同上，brainstorm #11）
- 注册表 → 新建 `~/.eo/projects.json`（不复用 dashboard 遗留 workbench.json）；init 成功顺手注册；register/unregister 手工维护；扫描兜底为辅；board 与 sync 共用（来源：同上，brainstorm #12）
- watch 全部参数 → `eo-sync watch [--interval N] [--all | --project <path>]`；每轮以 eo_lib freshness 键短路，键不变零成本跳过，键变才 run；复用既有文件锁，撞手动/archive run 跳过本轮；`--all` 枚举注册表、不要求在项目根运行；第一版终端常驻，launchd 守护化留待真实需求（来源：`decisions/2026-07-25-eo-sync-watch-auto-tier.md`）
- 六个流程 skill 零投影负担不动摇 → watch 是呈现侧自己的后台进程，写路径不为呈现层付费（来源：同上）
- 纯增量假设 → 不改 `eo-sync run/adapters`、eo-board 既有单项目三形态、eo_lib 既有 API 的任何现有**语义**，只新增旗标/子命令/模块；唯一例外是 `bookkeeping_path()` 内部改为消费 eo_lib 新增的 repo identity API（行为等价重构，hash8 输出不变，交叉测试锁定）（假设，依据宪法与「叠加不重写」边界，用户未逐条确认）
- 注册表写入不算破只读铁律 → 铁律管的是项目仓库文件；注册表是用户级生态文件，且仅由显式 register/init 动作写入（依据：决策 #12 明文授予 eo-board register/unregister）

## 2. 验收清单

- [ ] AC-1 跑 `/eo-project-init`（首次创建或更新既有配置两个成功出口）时顺手注册：注册成功则项目出现在 `~/.eo/projects.json` 且任意目录 `eo-board --all` 可见；注册失败时 init 仍成功完成，但输出明确告警与手工补注册指引（`eo-board --register`），补注册后同样可见（验证：临时目录 init 后查注册表与聚合视图；将注册表目录置为不可写再 init 一次看告警与指引）
- [x] AC-2 用户能用 `eo-board --register [path]` / `--unregister [path]` 手工维护注册表（缺省 path 为当前目录）；对同一项目重复 register（含从另一 worktree）不产生重复条目
- [ ] AC-3 `eo-board --all` 每注册项目一行：项目名 + 各状态 change 计数 + backlog 数 + as-of 新鲜度戳（验证：≥2 个注册项目下运行，核对行内容与时间戳）
- [ ] AC-4 用户在任意目录 `eo-board --project <路径|注册名>` 直接看到该项目的单项目视图，无需 cd；注册名命中多个项目时报歧义并列出候选路径、要求改用路径（不静默取第一项）（验证：在 $HOME 下用注册名跑一次；注册两个同名项目后再按名跑一次看歧义提示）
- [ ] AC-5 未注册项目可被扫描兜底纳入：`eo-board --all --scan <父目录>` 把含 `.eo-project.json` 的一层子目录并入本次聚合并提示可注册，但不写注册表（验证：跑完后核对 projects.json 未变）
- [ ] AC-6 `eo-sync watch` 常驻期间，change 状态流转后至多一个轮询间隔（默认 10s）内投影追平——看板 stub 卡状态更新（验证：watch 挂起时手改一个 change 的 status，观察 stub 卡）
- [ ] AC-7 项目无变化时 watch 不执行同步（freshness 键短路，短路轮无输出）；每次实际同步在 stderr 打一行诊断；watch 自身 run 产生的回写不引发下一轮再次同步；run 部分失败（个别适配器出错）的轮次同样记基线——项目无新变化时下一轮回到静默，不对持续性故障忙循环重试（验证：静置数轮确认 stderr 静默；一次流转只出现一次 run 诊断；构造一个必失败适配器观察仅告警一轮后恢复静默）
- [ ] AC-8 watch 撞上进行中的手动/archive 同步（锁占用）时跳过本轮不崩溃，下一轮自动追平（验证：人为持锁一轮后释放）
- [ ] AC-9 异常路径：`--all` 在注册表缺失/为空时明确提示如何注册；注册表内路径失效或配置非法时，`eo-board --all` 该行显示错误、`eo-sync watch --all` 告警并跳过该项目，其余项目均不受影响；watch 常驻期间同一故障项目按错误指纹只告警一次（不逐轮刷屏），故障修复后自动重新纳入同步且抑制记录清除（验证：注册一个不存在的路径后各跑一次；watch 下静置数轮确认告警不重复，修复路径后观察该项目恢复追平）
- [ ] AC-10 `docs/GUIDE.md` 与 `docs/sync-adapter-protocol.md` 载明 watch 触发点与多项目用法，与 §5 裁决一致（验证：读两文档相应小节）
- [ ] AC-11 `eo-sync watch --project <路径>` 可在任意目录运行、只追平该项目；`eo-sync watch --all` 一轮内追平全部有效注册项目，且 watch 运行期间新注册的项目自下一轮起被纳入（验证：两个注册项目下跑 `--all` 观察各自 stub 追平；watch 挂起期间注册第三个项目，观察下一轮被纳入）

## 3. TODO

### Batch 1（MVP：注册表资产）

- [x] TODO-1 新增 eo_lib 注册表模块与共用仓库身份 API：`gitio` 增规范化 repo identity 函数（realpath 归一化的 git common dir 绝对路径），registry 去重与 eo-sync `bookkeeping_path()` 改为同源消费；registry.py 提供 schema v1（见 §5.1）、load/save（原子写、`EO_HOME` 覆盖、顶层与条目级未知字段保留）、register/unregister（identity 去重、非 git 退化 realpath）（文件：新增: cli/eo_lib/registry.py、tests/test_eo_lib_registry.py；修改: cli/eo_lib/gitio.py、cli/eo-sync；对应 AC-1、AC-2；完成判据：单测绿——幂等注册 / 主与 linked worktree 去重且 registry identity 与簿记 hash8 交叉一致 / 原子写且替换失败不破坏旧文件 / EO_HOME 隔离 / 未知字段两级 round-trip 保留 / 损坏 JSON 容错 / 同名项目共存）
- [x] TODO-2 eo-board 新增 `--register [PATH]` / `--unregister [PATH]` 旗标（入互斥 mode 组，缺省 PATH=cwd，结果一行输出；unregister 未命中给明确提示；register 撞既有注册名时成功但提示同名共存）（文件：修改: cli/eo-board；对应 AC-2；完成判据：register→unregister 往返后注册表复原）
- [x] TODO-3 eo-project-init 两处成功出口（首次创建与更新/修复既有配置）都加「顺手注册」步骤：执行 `eo-board --register`，失败不阻塞 init，但必须输出告警与手工补注册指引（文件：修改: eo-project-init/SKILL.md；对应 AC-1；完成判据：两出口均含注册步骤与降级告警措辞，与 AC-1 口径一致）

### Batch 2a（eo-board 多项目）

- [ ] TODO-4 `--all` 聚合终端视图：枚举注册表、线程池并发扫描各项目（复用 `build_data`）、每项目一行计数 + as-of 戳、失效项目行内报错不中断、注册表缺失/空的引导提示（文件：修改: cli/eo-board、tests/test_eo_board_cache.py；对应 AC-1 的 `--all` 可见性半边、AC-3、AC-9 的 board 半边；完成判据：AC-3 行内容单测 + 失效项目行内报错用例绿）
- [ ] TODO-5 下钻与扫描兜底：`--project <路径|注册名>`（注册名查表解析为路径，命中多项报歧义并列候选路径；等价于在该目录运行，三形态通用）+ `--all --scan <父目录>`（一层枚举临时并集，不写注册表，提示可 `--register` 收编）（文件：修改: cli/eo-board、tests/test_eo_board_cache.py；对应 AC-4、AC-5）

### Batch 2b（eo-sync watch）

- [ ] TODO-6 `watch` 子命令：轮询语义按 §5.3（首轮必 run、键短路、四态结果矩阵与基线更新、锁占跳过、告警抑制与恢复、`--all` 每轮重读注册表、`--project` 显式作用域、SIGINT/SIGTERM 干净退出）；main 的 cwd 配置解析对 `watch --all` / `watch --project` 放行（文件：修改: cli/eo-sync、tests/test_eo_sync.py；对应 AC-6、AC-7、AC-8、AC-9 的 watch 半边、AC-11；完成判据：四态矩阵逐格有单测（0/1 记基线、2/异常不记且重试）+ 告警抑制与恢复用例绿）

### Batch 3（文档口径）

- [ ] TODO-7 文档口径同步：GUIDE.md 增多项目与 watch 用法小节；docs/sync-adapter-protocol.md 触发点段补 watch 自动档（文件：修改: docs/GUIDE.md、docs/sync-adapter-protocol.md；对应 AC-10）

> Batch 2a / 2b 文件集不相交（board+其测试 vs sync+其测试）、互不消费对方产出，仅共同依赖 Batch 1 的注册表模块——可并行。Batch 3 待 2a/2b 合流后串行（文档要引用两边落定的 CLI 形态）。

## 5. 技术方案

三块开放细节的裁决（触发：新增持久化结构 + 常驻进程语义需在编码前钉死）：

### 5.1 注册表 schema（`${EO_HOME:-$HOME/.eo}/projects.json`）

```json
{
  "version": 1,
  "projects": [
    { "name": "eo-skills",
      "path": "/Users/xx/projects/eo-skills",
      "registered_at": "2026-07-25" }
  ]
}
```

- `path` = 含 `.eo-project.json` 的目录绝对路径（realpath 归一化）；`name` 冗余自该项目配置的 `project_name`，仅供显示与 `--project <注册名>` 解析——**真相在各项目配置**，聚合时以实际加载结果为准，不一致时以加载结果显示并告警
- **去重键 = 规范化 repo identity（单一实现）**：`eo_lib/gitio.py` 新增规范化函数（git common dir → 绝对路径 realpath 归一化），registry 去重与 eo-sync `bookkeeping_path()` 的 hash8 **同函数消费**——「同源」由单一 API 保证而非两份等价实现，附主/linked worktree 下 registry identity 与簿记 hash8 的交叉测试；同一仓库任意 worktree 重复 register 视为同一项目、幂等更新 `name`/`registered_at`；非 git 目录退化为 realpath 判等
- **`name` 不是唯一键**：不同仓库合法同名（register 成功但提示同名共存）；按注册名解析命中多项时报歧义并列出候选路径、要求改用路径，绝不静默取第一项
- 写入：临时文件 + rename 原子落盘（与 eo-sync 簿记同款，替换失败不破坏旧文件）；读入时**顶层与项目条目两级**未知字段原样保留（前向兼容）；文件缺失视为空表，损坏 JSON 明确报错不静默清空
- 位置尊重 `EO_HOME`（shell 文档一律写 `${EO_HOME:-$HOME/.eo}`，Python 实现 `os.environ.get("EO_HOME")` 回落 `Path.home() / ".eo"`，与簿记一致，测试隔离同款手法）；读写实现收进 `cli/eo_lib/registry.py`，board / sync / init 三消费方共用，不各写一份

### 5.2 eo-board 多项目视图形态

- **v1 聚合仅终端形态**：`eo-board --all` 每注册项目一行——项目名、状态机计数（draft/confirmed/implementing/reviewed，archived 计总数不展开）、backlog 数、as-of 戳；`--html/--serve` 的多项目聚合不做，登记 OQ-1（需求驱动，宪法②防扩张）
- **as-of 戳** = 该项目本次 `build_data` 完成时刻（多项目并发扫描，各行独立戳）；单次运行不落缓存，与现状单项目行为一致（宪法③的缓存只在 `--serve` 生效，本 change 不动它）
- **下钻** = `--project <路径|注册名>`：只是把配置解析起点从 cwd 换成指定项目，复用既有单项目渲染，因此对终端/`--html`/`--serve` 三形态天然通用；注册名歧义规则见 §5.1（多命中报歧义列候选）
- **扫描兜底为辅**：`--scan <父目录>` 仅一层深度、仅本次聚合临时并集、绝不写注册表（写入只走显式 register / init）；输出尾部提示未注册项可 `--register` 收编
- 宪法核对：全程只读项目文件 ✓；无新依赖/无服务化 ✓；GitHub 数据继续走既有可选旗标路径，聚合行不引入实时查询 ✓

### 5.3 watch 轮询语义

- `eo-sync watch [--interval N] [--all | --project <path>]`：`--interval` 缺省 **10 秒**（下限 1）；缺省作用域 = cwd 所在项目；`--all` 每轮**重读**注册表（新注册项目下一轮即纳入），不要求 cwd 在任何项目内
- **每轮每项目**：`compute_freshness_key(cfg)` 与该项目上一基线比对——相同 → 跳过（短路，零 stderr 输出）；不同 → 进程内调用既有 run 编排（不 spawn 子进程），stderr 打一行诊断（项目 + 时刻）
- **首轮无基线视为键已变**：启动即对作用域内每项目 run 一次，追平停摆期间积压
- **四态结果矩阵**（基线更新 / 重试 / 输出，逐格可测）：

  | run 结果 | 基线 | 下一轮（项目无新变化时） | stderr |
  |----------|------|--------------------------|--------|
  | 0 全成 | run 后**重算**键记为基线（吸收 identity 回写的 mtime 变化，防自触发循环） | 短路静默 | 一行 run 诊断（项目 + 时刻） |
  | 1 部分失败 | 同上记基线（run 幂等、适配器级失败自带告警，防对持续性故障忙循环） | 短路静默 | run 诊断 + run 自带的适配器告警 |
  | 2 锁占用 | **不更新** | 自动重试 | 一行跳过提示 |
  | 异常（配置失效/加载抛错等） | **不更新** | 自动重试（受告警抑制约束） | 按抑制规则告警 |

- **告警抑制**：进程内按（项目, 错误指纹）记忆，同一故障常驻期间只告警一次，不逐轮刷屏；该项目一旦成功加载并完成一次 run（退出 0/1），清除其全部抑制记录、恢复正常纳入——瞬时失败不会被永久吞掉，恢复后如再故障可重新告警
- **锁**：复用 `acquire_lock` 的 flock 语义；撞上手动/archive run → 本轮跳过该项目，不崩溃不等待
- **常驻形态**：前台进程，SIGINT/SIGTERM 干净退出（释放持有中的锁）；launchd/systemd 守护化后置（已钉）
- **单项目故障隔离**：`--all` 下某项目配置缺失/非法 → 按上述抑制规则告警并跳过，循环与其余项目不受影响
- **main 分派放行**：`watch --all` / `watch --project` 不要求 cwd 在项目内（现 `main()` 在分派前无条件从 cwd 找配置，需对这两种作用域改为按 §5.3 逐项目解析）；裸 `watch` 仍沿用 cwd 解析与既有报错

## 8. 开放问题

- OQ-1 `--html` / `--serve` 的多项目聚合形态（defer 原因：v1 终端先行已覆盖总览刚需，web 聚合等真实使用信号，避免宪法②所防的重量回长）
- OQ-2 `--scan` 是否需要递归深度 >1 与忽略规则（defer 原因：扫描定位是兜底为辅，一层深度先跑，真实目录结构不满足再议）
