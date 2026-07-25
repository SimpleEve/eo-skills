---
title: eo-helper 单一交互入口 + eo-board --all 聚合形态 + 命令面收纳代码审查报告
change_id: eo-helper-entry
tags: [eo-helper, eo-board, cli, review]
created: 2026-07-25
updated: 2026-07-25
status: active
summary: >
  首轮代码审查发现 2 条 P1：特殊数字输入会让 helper traceback，
  eo-board 的输出模式修饰旗标未完整执行组合约束；P0 为 0。
---

# eo-helper 单一交互入口 + eo-board --all 聚合形态 + 命令面收纳 代码审查报告

> 关联 Change：[change.md](change.md)（检查表：其 §2 验收清单）
> 首轮审查日期：2026-07-25 ｜ 实施区间：`8512f1c..5581b61` ｜ 方案基线：`6998899`
> 审查范围：`cli/eo-helper`、`cli/eo-board`、`install.sh`、README/CLI 文档及对应测试
> 首轮之后正文各节为历史快照；当前状态以「Finding 台账」与末尾「速报」为准。

## Finding 台账

<!-- 状态单一来源；轮次编号全文件单调递增（跨 revision 不清零）。写入权：
     eo-review 建条与核销；eo-implement 回写 fixed + 修复 commit；用户可裁决 waived。 -->

| ID | 级别 | 摘要 | 位置 | 状态 | 根因 | 首见/最近轮 | 基线/修复 commit |
|----|------|------|------|------|------|-------------|------------------|
| P1-1 | P1 | `isdigit()` 与 `int()` 接受域不同，特殊数字输入会直接 traceback | `cli/eo-helper:87` | fixed | implementation | 1/1 | `5581b61` / `c757368` |
| P1-2 | P1 | `--port`/`--no-open` 的适用模式未校验，非法组合被静默接受 | `cli/eo-board:2111` | fixed | implementation | 1/1 | `5581b61` / `c757368` |
| P2-1 | P2 | 跨缓存槽并行测试只断言调用数，没有证明两个构建实际重叠 | `tests/test_eo_board_cache.py:583` | fixed | implementation | 1/1 | `5581b61` / `c757368` |

## 审查总结（首轮快照）

整体架构方向正确：helper 只持有固定 argv 映射，短命令使用继承 stdio 的
`subprocess.run`，长驻命令使用 `os.execvp`；聚合 serve 每次重读注册表，
逐项目复用既有缓存槽和单飞锁，跨槽由线程池并行，静态 HTML 不走缓存。
独立执行全套 199 项测试全部通过，聚合状态刷新、缓存命中、跨槽重叠、
非 TTY、真实 PTY 下的 EOF/Ctrl+C、长驻 exec 和临时安装也均验证通过。

当前不能流转 `reviewed`：菜单的非法输入分支存在可复现 traceback，且
argparse 仍会接受并忽略与当前输出模式无关的修饰旗标。两项均应回
`/eo-implement` 模式二修复后再做定向复审。

## P0 - 必须修复（阻塞性问题）

无。

## P1 - 建议修复（重要但不阻塞运行）

### [P1-1] 特殊数字输入绕过非法编号分支并触发 traceback

- **类型**：潜在 Bug / AC 覆盖缺口
- **位置**：`cli/eo-helper:87`
- **描述**：代码先以 `choice.isdigit()` 判定，再直接执行 `int(choice)`。
  两者接受域并不相同，例如 `²`.isdigit() 为真，但 `int("²")` 抛
  `ValueError`。真实 PTY 输入 `²` 后 helper 退出码为 1，输出 traceback，
  没有提示重选。
- **影响**：粘贴或输入 Unicode 数字样式、超长纯数字串时，菜单会崩溃，
  违反 AC-6「非法编号提示重选」和无 traceback 的异常路径契约。
- **建议**：只解析一次并捕获转换失败，再统一走非法编号提示；补充至少
  一个 `isdigit()` 为真但 `int()` 失败的回归样例，并覆盖超长数字串。

### [P1-2] 输出模式修饰旗标未执行完整组合约束

- **类型**：CLI 契约 / 逻辑正确性
- **位置**：`cli/eo-board:2111`、`cli/eo-board:2120`、
  `docs/cli-reference.md:69`
- **描述**：帮助和 cli-reference 都声明 `--port` 仅适用于 `--serve`，
  `--no-open` 仅适用于 `--html`/`--serve`，但 `main()` 只校验了
  `-o`、`--scan`、`--project` 及注册动作的部分组合。实跑
  `eo-board --all --html --port 7444 -o /tmp/a.html --no-open`、
  `eo-board --all --port 7444`、`eo-board --register --no-open`
  均以 0 退出，相关旗标被静默忽略。
- **影响**：参数拼错时 CLI 给出成功假象，用户可能误以为端口或打开策略
  已生效；新增的 `--all` 三形态矩阵没有被完整落实。
- **建议**：显式校验 `--port`/`--no-open` 的模式依赖，并把非 serve
  携带 `--port`、非 html/serve 携带 `--no-open`、注册动作携带两者加入
  argparse 反例矩阵；默认端口与用户显式传参需能区分。

## P2 - 可选优化

### [P2-1] 跨槽并行缺少能防串行退化的确定性断言

`tests/test_eo_board_cache.py:583-584` 在并发请求后只断言总调用数为 2。
如果未来把两个项目改成串行构建，该测试仍会通过。当前实现经独立探针确认
两个 300ms 构建存在约 363ms 重叠，代码行为正确；建议测试用
`max_inflight`、Barrier 或事件握手直接断言两个不同槽同时进入构建，
避免依赖脆弱的耗时阈值。

## 验收标准覆盖检查

| AC 编号 | 审查结论 | 证据摘要 |
|---------|----------|----------|
| AC-1 | 通过 | 聚合 HTML 含多项目区块、坏条目行内错误和两种输出路径；相关测试通过 |
| AC-2 | 通过 | 状态改写后下一次 `/data.json` 返回新计数；稳定键命中缓存，同槽单飞，跨槽实际重叠 |
| AC-3 | 通过 | handler 每请求调用 `build_all_data()` 重读注册表；动态注册和空表指引测试通过 |
| AC-4 | 通过 | 七项固定映射、先回显再转发和任意目录运行路径均成立 |
| AC-5 | 通过 | 短命令继承 stdio 并显示非零码；长驻命令真实 exec 后 PID 内命令已替换 |
| AC-6 | 部分通过 | 非 TTY、EOF、Ctrl+C、无配置透传均通过；特殊数字输入见 P1-1 |
| AC-7 | 通过 | 隔离 HOME/EO_BIN_DIR 安装后 eo-helper 软链与主推提示正确 |
| AC-8 | 通过 | 三命令 help 旗标集合全部能在 cli-reference 中找到；README 收纳与术语扫描通过 |
| AC-9 | 人工项，不核 | 保持未勾；本轮不代替用户判断 README 通读体验 |

## TODO 完成度检查

| TODO | 审查结论 | 说明 |
|------|----------|------|
| TODO-1 | 完成 | 聚合数据结构、getter 注入和缓存 as-of 语义成立 |
| TODO-2 | 完成 | `--all --html` 两种输出路径、自包含数据与错误行成立 |
| TODO-3 | 部分完成 | serve、动态注册表、缓存和扫描组合成立；参数矩阵缺 P1-2 |
| TODO-4 | 部分完成 | 薄壳分流和透传成立；非法输入处理缺 P1-1 |
| TODO-5 | 完成 | install.sh 已接线 eo-helper，隔离安装冒烟通过 |
| TODO-6 | 完成 | cli-reference 覆盖 eo-helper/eo-board/eo-sync 全量旗标 |
| TODO-7 | 完成 | README/GUIDE 已收纳命令面；AC-9 体验判断仍归用户 |

## 独立验证

- `python3 -m unittest discover -s tests -p 'test_*.py' -v`：199 项通过，耗时 61.679s。
- `python3 -m compileall -q cli tests`：通过。
- `git diff --check 6998899..5581b61`：通过。
- 临时 EO_HOME 聚合 serve：change 从 draft 改 reviewed 后，下一请求计数从
  `{"draft": 1}` 变为 `{"reviewed": 1}`。
- 真实 PTY：EOF/Ctrl+C 均退出 0 且无 traceback；选择实时看板后进程命令
  已从 eo-helper 替换为 eo-board；无配置目录的短命令原样显示底层 init 指引和退出码 1。
- 反例探针：真实 PTY 输入 `²` 得到 `ValueError` traceback，进程退出 1。

## 速报

结论：有保留通过（P1 2 条）［第 1 轮 · revision 1 · 基线 `5581b61`］
P1（应修）：
1. 特殊数字输入会绕过非法编号提示并让 helper traceback - `cli/eo-helper:87`
2. `--port`/`--no-open` 与输出模式的组合约束未落实 - `cli/eo-board:2111`
P2（可后置）：
3. 跨缓存槽并行测试没有直接证明构建重叠 - `tests/test_eo_board_cache.py:583`
下一步：回 `/eo-implement` 模式二修复 P1 后定向复审；AC-9 继续保留给用户人工验收。
