---
title: eo-helper 单一交互入口 + eo-board --all 聚合形态 + 命令面收纳 Change 审查报告
change_id: eo-helper-entry
created: 2026-07-25
status: active
summary: >
  首轮全量审查通过，P0 为 0；缓存证据、薄壳退出码、配置前检、参数组合矩阵和 TODO 完成判据有 5 条 P1 待起草方裁决。
---

# eo-helper 单一交互入口 + eo-board --all 聚合形态 + 命令面收纳 Change 审查报告

> 关联：[change.md](change.md) ｜ 审查日期：2026-07-25 ｜ change status：draft
> 前提抽查基线：`6998899d55eba93a0e3a0335a4e013780c298796`（首轮审查时 HEAD；change.md 的 `base_commit` 尚为空）

## 审查总结

结论：通过，P0 为 0，可在确认后进入 implement。9 条 AC 均有可执行观察口径，7 条 TODO 全部映射到 AC，文件前提、聚合缓存复用、全局命令绕过 cwd 配置等核心断言也与当前代码相符；AC-9 正确标为人工项，实施完成后由 `eo-implement` 生成 `acceptance.md`，当前不要求起草期提前写死实现后的走查步骤。另有 5 条 P1 移交起草方裁决：最值得修的是把聚合缓存/单飞证据改成调用计数，把短命令退出码语义和 helper 不做配置前检的薄壳边界写清，并补齐 `--all` 与输出模式的参数组合矩阵。

## Finding 台账

<!-- 状态单一来源：本 skill 建条与核销（open→verified），修订方（/eo-change）填「处置」列。wont-fix 项后续任何轮次不得重报 -->

| ID | 级别 | 摘要 | 位置 | 状态 | 处置（修订方填） |
|----|------|------|------|------|------------------|
| P1-1 | P1 | 聚合缓存与单飞仅看 hit/miss 日志，缺少调用计数和跨槽并行的确定性证据 | AC-2、TODO-1、TODO-3 | fixed | fix：AC-2 验证改调用计数为准（stderr 仅辅助）；TODO-1 判据补 as-of 不重打断言；TODO-3 判据补计数断言（稳定键不增/同槽并发 +1/双槽并行各 +1） |
| P1-2 | P1 | “短命令回菜单”与“不吞错误码”缺少可同时执行的退出状态契约 | AC-5、TODO-4、§5.2 | fixed | fix：采纳「非零状态可见」路线——短命令非零码回显后仍回菜单，helper 菜单循环自身返回 0；长驻 exec 保留最终退出码；落 AC-5、TODO-4、§5.2 |
| P1-3 | P1 | helper 自行判断项目配置会复制既有 CLI 的配置发现与报错逻辑 | AC-6、TODO-4、§5.2 | fixed | fix：薄壳边界钉为「固定 argv 映射、不读配置不前检」，项目级选项原样转发、init 指引由底层 CLI 透传；落 AC-6、TODO-4、§5.2 |
| P1-4 | P1 | `--all` 与 html/serve/scan 等参数的合法组合矩阵未钉定 | TODO-2、TODO-3、§5.1 | fixed | fix：§5.1 新增组合矩阵（--all/--all --html [-o]/--all --serve [--port/--no-open] 合法；--scan 与三形态正交；--project、register/unregister 混用继续拒绝）；正反例进 TODO-3 判据、正例进 TODO-2 判据 |
| P1-5 | P1 | 多条 TODO 共同覆盖同一 AC 时，TODO-2/3/6 缺各自完成判据 | TODO-2、TODO-3、TODO-6 | fixed | fix：TODO-2 补聚合 HTML 静态断言、TODO-3 补 serve handler+计数+argparse 断言、TODO-6 补与三命令 --help 的参数集合核对 |
| P2-1 | P2 | 交互菜单的 EOF/Ctrl+C 退出行为未说明 | AC-6、§5.2 | fixed | fix：EOF/菜单态 Ctrl+C 与 q 同款干净退出（码 0 无 traceback），长驻接管后信号归底层；落 AC-6、§5.2 |

## P0 - 必须修订（阻塞 implement）

无。未发现 TODO↔AC 映射断裂、占位符、硬粒度超限、非法 type、不可验收 AC、推翻已钉设计判断或不成立的代码前提。

## P1 - 建议修订（移交起草方裁决，不阻塞）

### [P1-1] 缓存/单飞通过条件不够确定

AC-2 把“稳定请求命中缓存”和“同项目并发只重扫一次”列为验收结果，但验证栏只要求观察 stderr 的 hit/miss；TODO-1 的完成判据也只写“注入两种 getter”，TODO-3 没有进一步锁定调用次数。当前 `cli/eo-board:1474-1493` 的真实机制是按 `config_path` 分槽、锁内重算键和二次查表；本轮 8 线程同槽探针得到 `build_data` 调用 1 次，两槽并发各调用 1 次且总耗时约等于单次构建，前提成立，但方案没有把这份一致性变成回归门。建议用临时 fixture + `build_data` 调用计数锁定：稳定键顺序请求计数不增、同槽 N 路并发计数只增 1、两槽构建可重叠且各增 1；stderr 继续只作辅助观察。另断言缓存命中行的 as-of 取缓存数据的 `generated_at`，不按请求时刻重打。

### [P1-2] 短命令的退出码语义自相牵制

§5.2 同时要求 3/4/6/7 号短命令由 subprocess 执行后回到菜单，以及薄壳“不吞错误码”。短命令进程结束后 helper 仍存活，调用方此时拿不到那个子进程作为 helper 的最终退出码；若立刻以相同非零码退出 helper，又违反“结束后回菜单”。建议二选一写成可测契约：要么短命令 stdio 原样直通、非零码明确回显后仍回菜单，并把“不吞错误码”改成“非零状态可见”；要么短命令失败即让 helper 以同码退出。长驻命令继续 `exec`，天然保留信号和最终退出码。

### [P1-3] 项目配置前检不应进入 helper

AC-6/TODO-4 写“当前目录无配置时项目级选项给 init 指引”，容易诱导 helper 自己查 `.eo-project.json`；这会复制底层 CLI 的配置发现规则，并可能把项目子目录误判为无配置。真实 `eo-board:1796-1809` 与 `eo-sync:1031-1045` 已负责向上找配置、合并 local 覆盖并输出 init/修复指引，而 `eo-board --all` 与 `eo-sync watch --all` 又分别在 `eo-board:1789-1794`、`eo-sync:1031-1033` 绕过 cwd 配置。建议把薄壳边界钉成“helper 只维护固定 argv 映射，不读配置；项目级选项也直接转发，由底层 CLI 原样给指引”，并用项目子目录与 `$HOME` 两个 fixture 锁定。

### [P1-4] `--all` 参数组合缺少完整语法裁决

当前 parser 把 `--all` 与 `--html`/`--serve` 放在同一个互斥组，实际运行两种新组合都以退出码 2 报“不允许同时使用”；TODO-2/3 虽写了分派新形态，却没有说明调整后的合法/非法组合。建议在 §5.1 钉一张最小矩阵：允许 `--all`、`--all --html [-o]`、`--all --serve [--port/--no-open]`；继续拒绝 `--all --project` 及 register/unregister 与输出模式混用；并明确既有 `--scan` 是支持静态/serve 聚合、仅支持终端，还是与 web 组合时报明确错误。TODO-2/3 同步加入 argparse 正反例测试。

### [P1-5] 共同覆盖 AC 的 TODO 缺分项完成门

粒度规范要求多条 TODO 对同一 AC 时逐条写完成判据。当前 AC-1 由 TODO-1/2 共同覆盖、AC-2 由 TODO-1/3 共同覆盖、AC-8 由 TODO-6/7 共同覆盖，但 TODO-2、TODO-3、TODO-6 没有各自完成判据。建议分别补聚合 HTML 静态断言、聚合 serve handler/缓存并发断言、cli-reference 对三条 `--help` 的参数集合核对；不要把整条 AC 的最终验收重复抄入 TODO。

## P2 - 可选优化

### [P2-1] 菜单提示符的 EOF/Ctrl+C 行为

非 TTY 降级已经清楚地限定为“stdin 非 TTY → 打印对照表、退出 0、绝不拉起子进程”，方向合格；但交互 TTY 下按 Ctrl+D 会触发 EOF，菜单态 Ctrl+C 也未定义。建议与 `q` 一样干净退出，避免 Python traceback；长驻子命令接管后的 Ctrl+C 仍完全归底层 CLI。

## AC 质量检查

| AC | 用户视角 | 可验证 | 技术无关 | 备注 |
|----|---------|--------|---------|------|
| AC-1 | 是 | 是 | 是 | 多项目、坏条目、输出路径均有操作和观察点 |
| AC-2 | 部分 | 是 | 部分 | 热刷新可直接观察；缓存/单飞证据建议改调用计数（P1-1） |
| AC-3 | 是 | 是 | 是 | 运行中新注册与空注册表两条边界清楚 |
| AC-4 | 是 | 是 | 是 | 任意目录、菜单、先回显后执行均可直接试 |
| AC-5 | 是 | 是 | 部分 | stdio/信号可对照直跑；短命令退出码待澄清（P1-2） |
| AC-6 | 是 | 是 | 是 | 非 TTY、非法编号、无项目配置与全局选项均有预期；helper 前检边界见 P1-3 |
| AC-7 | 是 | 是 | 是 | `EO_BIN_DIR` 临时前缀可隔离安装验证 |
| AC-8 | 是 | 是 | 部分 | README grep 与 `--help` 参数集合可机械核对 |
| AC-9 | 是 | 是 | 是 | “人工:”标记正确，通读路径落到现有安装/第一次使用/看板章节 |

异常/边界由 AC-1、AC-3、AC-6 承担。AC-9 是唯一人工项；按 `eo-shared/acceptance.md`，具体入口、操作步骤和验收基线应在实现完成后生成到 `acceptance.md`，当前方案不缺提前工件。

## TODO↔AC 映射检查

| TODO | 对应 AC | 状态 |
|------|---------|------|
| TODO-1 | AC-1、AC-2 | 通过：结构化聚合数据与 getter 注入覆盖两形态共同地基；确定性缓存证据见 P1-1 |
| TODO-2 | AC-1 | 通过：聚合 HTML、输出路径和自包含渲染直接对应；完成判据见 P1-5 |
| TODO-3 | AC-2、AC-3 | 通过：聚合 serve、动态注册表、缓存槽和坏条目隔离均覆盖；完成判据见 P1-1/P1-5 |
| TODO-4 | AC-4、AC-5、AC-6 | 通过：菜单、转发、非 TTY 与异常路径均有落点；薄壳边界见 P1-2/P1-3 |
| TODO-5 | AC-7 | 通过：安装列表与完成提示一对一映射 |
| TODO-6 | AC-8 | 通过：全量 CLI 参数文档有独立文件落点；完成判据见 P1-5 |
| TODO-7 | AC-8、AC-9 | 通过：README/GUIDE 收纳和人工通读一并覆盖 |

每条 AC 至少有一条 TODO 覆盖，每条 TODO 也都能映射到 §1 意图，没有悬空 AC 或越界 TODO。

## TODO 机械前提核验

| TODO | 操作与对象 | 基线结果 |
|------|------------|----------|
| TODO-1 | 修改 `cli/eo-board`、`tests/test_eo_board_cache.py` | 两对象存在；`_aggregate_row`、`build_data`、`get_board_data_cached` 形态相符 |
| TODO-2 | 修改 `cli/eo-board`、`tests/test_eo_board_cache.py` | 两对象存在；现有单项目 `render_html`/`cmd_html` 可作语义参照，parser 组合需 P1-4 明确 |
| TODO-3 | 修改 `cli/eo-board`、`tests/test_eo_board_cache.py` | 两对象存在；已有 `ThreadingHTTPServer`、`/`、`/data.json`、3 秒轮询和每槽单飞 |
| TODO-4 | 新增 `cli/eo-helper`、`tests/test_eo_helper.py` | 父目录与单文件 CLI/test 惯例存在，两个目标名均无冲突 |
| TODO-5 | 修改 `install.sh` | 对象存在；`install_cli()` 当前用固定 CLI 列表逐个软链 |
| TODO-6 | 新增 `docs/cli-reference.md` | `docs/` 父目录存在，目标名无冲突 |
| TODO-7 | 修改 `README.md`、`docs/GUIDE.md` | 两对象存在；AC-9 指定的 README 三段标题当前均存在 |

## 粒度检查

TODO 数：7（理想 3-7 / 硬上限 10）｜ 全文：111 行（软标 200-500 / 硬上限 700）｜ 结论：合规。

三个 Batch 均为纯数字串行批；Batch 2 消费 Batch 1 新增的 CLI 形态，Batch 3 再引用前两批最终命令面，依赖说明与实际文件关系一致。该 change 同时新增 web 聚合、入口薄壳和文档收纳，但三者都服务“只记 eo-helper”这一用户意图，且存在明确生产者-消费者链，不建议拆分。

## 核心边界一致性

| 边界 | 判定 | 说明 |
|------|------|------|
| eo-helper 只转发、不复制业务逻辑 | 基本一致 | 固定 argv + stdio/exec 路线正确；退出码和配置前检仍需 P1-2/P1-3 收紧 |
| `--all --serve` 复用单项目缓存/单飞 | 一致 | 当前缓存按 `config_path` 分槽、同槽单飞、跨槽并行；方案明确逐项目复用且不加聚合二级缓存 |
| 单次 `--all --html` 不走缓存 | 一致 | 与现有 terminal/html 全量构建边界相同 |
| 每轮重读注册表 | 一致 | 不缓存聚合层，可让运行中新注册项目进入下一次 `/data.json` |
| eo-board 四条约束 | 一致 | 仍为只读项目文件、stdlib、127.0.0.1、3 秒轮询，无 SSE/写交互/GitHub 强依赖 |
| AC-9 人工验收路径 | 一致 | 人工判断仅针对 README 通读体验；验收单在 implement 后生成、archive 时为硬门 |
| 非 TTY 降级 | 一致 | stdin 非 TTY 直接打印固定映射并退出 0，不读输入、不执行子命令 |

§8 有 2 条 defer，未超过 3 条上限；都未偷渡进 TODO。未触发 §4、§6、§7：实现与测试文件均已列入 TODO，无流程图、无新外部依赖、无不可逆操作。

## 前提真实性抽查（维度 7）

| 断言 | 基线 | 证据 | 判定 |
|------|------|------|------|
| 既有每项目缓存槽与同槽单飞可直接供聚合 serve 复用 | `6998899d` | `cli/eo-board:1458-1493` 以 config path 分槽并在槽锁内重算键、二次查表；8 线程同槽探针仅 1 次构建 | 成立 |
| 不同项目缓存槽可并行构建，聚合层无需第二层缓存 | `6998899d` + 当前兼容性探针 | `cli/eo-board:1480-1492` 的 build lock 按 slot 建立；两槽各 80ms 构建并发完成约 85ms、各调用 1 次 | 成立 |
| 当前 `--all` 只有终端形态，新组合需要改 parser 与分派 | `6998899d` | `cli/eo-board:1760-1767` 把 html/serve/all 置于同一互斥组；实跑 `--all --html`、`--all --serve` 均退出 2 | 成立；组合矩阵见 P1-4 |
| 全局菜单项可以在任意目录原样转发，项目级错误可由底层 CLI 负责 | `6998899d` | `cli/eo-board:1789-1809` 在 all 分派后才解析 cwd；`cli/eo-sync:1031-1045` 对 watch all/project 同样先放行，项目级分支已有 init 指引 | 成立；helper 不应复制前检，见 P1-3 |
| 用户拍板的三点与本 change 范围一致 | 当前管理侧工件 | backlog `2026-07-25-eo-helper-single-entry.md:9` 明列 web 聚合、数字菜单和 README 收纳；accepted decision 的只读/零依赖/缓存边界见 `2026-07-24-dashboard-deprecated-board-cli.md:22-30` | 成立 |

## 结构完整性

| 节 | 状态 | 备注 |
|----|------|------|
| 速览 | 通过 | 三项行为差异与 §1/§2 一致，人工数量正确 |
| §1 意图 + 已钉设计判断 | 通过 | 来源工件与现有 board/sync 边界相符 |
| §2 验收清单 | 通过 | 9 条均可操作；P1 为证据强度/边界精化，不构成 P0 |
| §3 TODO（Batch） | 通过 | 映射完整、无占位符、批间依赖自洽；分项完成判据见 P1-5 |
| 条件节 §4-§8 | 通过 | §5 触发合理，§8 defer 数量合规；其余条件未触发 |

## 速报

结论：通过（P0 0 条）［第 1 轮 · 全量］

P0（阻塞 implement）：
1. 无未决 P0。

P1（移交起草方裁决，不阻塞循环）：
2. 缓存/单飞证据应改为调用计数并锁定跨槽并行 — change.md AC-2、TODO-1/3
3. 短命令回菜单与错误码透传需统一契约 — change.md AC-5、§5.2
4. helper 不应复制项目配置发现与 init 报错逻辑 — change.md AC-6、§5.2
5. `--all` 与 html/serve/scan 的合法组合矩阵需钉定 — change.md §5.1
6. TODO-2/3/6 应补共同覆盖 AC 时的分项完成判据 — change.md §3

P2（可后置）：
7. 菜单态 EOF/Ctrl+C 建议按 q 干净退出。

下一步：`/eo-implement eo-doc/changes/08-eo-helper-entry/change.md`（status 仍为 draft，先回 /eo-change 对话确认）。未决 P1 已入台账，由起草方裁决：采纳的回 /eo-change 顺手修（不触发复审），不采纳的标 wont-fix 附理由。注意：`/eo-review` 是代码审查，要在 implement 之后，现在还不轮到它。
