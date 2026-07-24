---
title: 抽取共享解析库并修复 eo-board local 合并与缓存 Change 审查报告
change_id: shared-lib-board-cache
created: 2026-07-24
status: active
summary: >
  首轮全量审查发现审查基线缺少 eo-board 前置实现、缓存键未覆盖全部动态数据源两条 P0，当前不可进入 implement。
---

# 抽取共享解析库并修复 eo-board local 合并与缓存 Change 审查报告

> 关联：[change.md](change.md) ｜ 审查日期：2026-07-24 ｜ change status：draft

## 审查总结

本 change 的意图、C1 边界、5 条 TODO 对 6 条 AC 的覆盖关系和 Batch 拆分总体清楚，粒度也合规；但首轮审查基线 `f885f1c` 中没有方案声称已存在的 `cli/eo-board`，且缓存新鲜度键没有覆盖现有 `build_data` 的全部动态依赖。结论：❌ 需修订，当前不可进入 implement。P1 均移交起草方裁决，不阻塞 P0 核销。

## Finding 台账

<!-- 状态单一来源：本 skill 建条与核销（open→verified），修订方（/eo-change）填「处置」列。wont-fix 项后续任何轮次不得重报 -->

| ID | 级别 | 摘要 | 位置 | 状态 | 处置（修订方填） |
|----|------|------|------|------|------------------|
| P0-1 | P0 | 审查基线不存在待抽取的 eo-board 及其安装入口 | §1、§3、§4 | verified | 前置工作已由总控结算至 `792522d`（含 cli/eo-board、install.sh 安装入口、local 合并契约）；§1 已钉决策新增「变更前基线 = 792522d」行并约束 `base_commit` 不得早于它；AC-1 验证栏、TODO-1/2 完成判据、§4 install.sh 行全部改锚该 commit |
| P0-2 | P0 | 缓存键未覆盖日期、分支名和 `git log --all` 等真实输入 | §2 AC-6、§3 TODO-4/5、§5 | verified | §5 缓存设计改为依赖闭合表（逐项映射 build_data 动态输入→键成分：worktree 三元组含分支名、refs 指纹、当天日期、changes/backlog/roadmap mtime）；TODO-4 键组成同步扩展并加三类确定性用例（跨日/月、同 SHA 换分支、ref-only 更新）；AC-6 声明扩至 ref 更新与日期边界；§1 假设行同步 |
| P1-1 | P1 | `type: refactor` 与新增可见行为不符 | frontmatter、§1、§2 | verified | 采纳：frontmatter `type` 改 `enhance`，§1 补一句归类理由（抽库保留为内部重构子任务）；INDEX 与 stub 类型列同步 |
| P1-2 | P1 | 共享配置库的错误所有权未定义 | §3 TODO-1/3、§5 | verified | 采纳：§5 新增「错误所有权」节（库抛 `ConfigError` 不退进程，CLI 入口捕获格式化退出）；§1 假设行新增；TODO-1 完成判据加「库内无 sys.exit/die」，TODO-2 补入口捕获职责 |
| P1-3 | P1 | TODO 完成判据越过 auto-heavy 验证归属且缓存命中证据偏弱 | §2 AC-1/5/6、§3 TODO-2/5 | verified | 采纳：TODO-2 判据改为不起服务（终端/--html + build_data 直调 JSON 对照基线，serve 端到端归测试阶段）；TODO-5 判据改为 build_data 计数替身的 handler 级确定性检查；AC-1 验证栏改锚 792522d 基线并分流 serve 对照；AC-5 验证改调用计数断言、诊断行降为辅助 |

## P0 - 必须修订（阻塞 implement）

### [P0-1] 审查基线不存在待抽取的 eo-board 及其安装入口

- 类型：前提不成立
- 位置：change.md §1 第 23、30、38 行；§3 TODO-1/2/5；§4
- 描述：`base_commit` 缺省时首轮按当前 HEAD `f885f1c` 审查。`git cat-file -e f885f1c:cli/eo-board` 返回 128，`git status --short -- cli/eo-board install.sh` 显示 `?? cli/eo-board`、` M install.sh`；HEAD 版 `install.sh` 也没有 CLI 安装逻辑。方案所述 1925 行单文件、符号链接安装及 skill 侧 local 合并契约都只存在于未提交工作区，不是可追溯的变更前事实。
- 影响：TODO-2/5 的“修改”对象和 TODO-1 的抽取源无法从基线复现，AC-1 也无法以 `base_commit` 生成可信的抽取前对照；实施会把未结算前置改动误当成既有系统。
- 建议：先把引入 `cli/eo-board`、CLI 安装入口及 local 配置契约的前置工作结算到一个明确 commit，再让本 change 的 `base_commit` 指向该 commit；若这些内容本就应归本 change，则需把相应 TODO 改为“新增”并重写 AC-1 的基线策略。处置后按新基线复审。

### [P0-2] 缓存键没有覆盖 `build_data` 的全部动态输入

- 类型：前提不成立
- 位置：change.md §2 AC-6；§3 TODO-4/5；§5“缓存设计”
- 描述：方案把新鲜度键限定为 worktree HEAD、changes/backlog/roadmap mtime 和 worktree 路径集合，但当前 `build_data` 还依赖日期、worktree 分支名以及 `git log --all`。`cli/eo-board:413-418` 用 `date.today()` 计算停滞天数，`:672-677` 用当天月份与 `git log --all` 计算“本月直改”，`:861-863` 直接输出分支名。跨日/跨月、同 SHA 分支切换、非 worktree ref 更新时，拟定键都可保持不变而输出已经应当变化。
- 影响：缓存会稳定命中陈旧数据，违反 AC-6 的“缓存新鲜”与 refactor 的行为保持口径；这不是实现细节取舍，而是新鲜度判定前提不成立。
- 建议：在 §5 和 TODO-4 中先闭合 `build_data` 的依赖集合：至少纳入日期边界、worktree 分支身份、影响 `git log --all` 的 refs 指纹，或反向收窄 `build_data` 使其只依赖既定键；完成判据增加跨日/月、同 SHA 换分支、ref-only 更新三类确定性用例。

## P1 - 建议修订（移交起草方裁决，不阻塞）

### [P1-1] `type: refactor` 与新增可见行为不符

- 类型：类型错配
- 位置：change.md frontmatter、§1、§2 AC-3～AC-6
- 描述：本项目类型契约中 `refactor` 要求用户可见行为不变；本 change 明确新增 local 覆盖、错误呈现、缓存诊断和性能行为。
- 建议：改为 `type: enhance`；共享库抽取仍可作为 enhance 内的内部重构子任务保留。

### [P1-2] 共享配置库的错误所有权未定义

- 类型：技术方案边界不完整
- 位置：change.md §3 TODO-1/3、§5
- 描述：当前 `load_project_config` 在 `cli/eo-board:53-74` 直接调用 board 级 `die()` 终止进程；TODO-1 又要求共享包不依赖 eo-board、可独立复用，但方案没有定义异常类型、退出责任或错误格式所有者。
- 建议：钉定共享层抛出携带路径与原因的 `ConfigError`，由 eo-board/未来 eo-sync 的 CLI 入口负责格式化并退出；同步更新 TODO-1/3 与 AC-4 的责任边界。

### [P1-3] TODO 完成判据与 auto-heavy 验证归属混线

- 类型：验证归属不一致
- 位置：change.md §2 AC-1/5/6、§3 TODO-2/5
- 描述：`--serve`、连续 HTTP 请求和浏览器轮询属于 auto-heavy，只应由 `/eo-test` 执行；但 TODO-2/5 把这些动作写成 implement 阶段的完成门。AC-1 还要求“抽取前”生成 serve 基线，而 AC-5 允许只看 hit 日志或主观耗时，既与阶段归属冲突，也不能稳定证明未发生全量扫描。
- 建议：TODO 完成判据改成不起服务的导入、函数级和 handler 级确定性检查；由 `/eo-test` 在 `base_commit` 临时 worktree 与当前实现之间比较三形态，并用调用计数/替身断言第二次请求没有进入全量扫描，避免仅凭日志或“显著下降”判断。

## P2 - 可选优化

无。

## AC 质量检查

| AC | 用户视角 | 可验证 | 技术无关 | 备注 |
|----|---------|--------|---------|------|
| AC-1 | ✅ | ⚠️ | ✅ | 行为不变口径存在，但基线不可追溯且 heavy 验证归属未闭合 |
| AC-2 | ⚠️ | ✅ | ⚠️ | 以共享库消费者为视角可接受，属于内部 API 契约 |
| AC-3 | ✅ | ✅ | ✅ | 正常与无 local 边界均覆盖 |
| AC-4 | ✅ | ✅ | ✅ | 异常路径明确且可观察 |
| AC-5 | ⚠️ | ⚠️ | ⚠️ | 目标偏内部实现；日志/主观耗时不能稳定证明跳过扫描 |
| AC-6 | ✅ | ✅ | ✅ | 3 秒口径明确，但方案漏掉现有时间/ref 动态输入 |

异常路径由 AC-4 覆盖；refactor 的行为保持口径由 AC-1 覆盖。当前主要问题不是 AC 悬空，而是基线与缓存依赖模型不成立。

## TODO↔AC 映射检查

| TODO | 对应 AC | 状态 |
|------|---------|------|
| TODO-1 | AC-1、AC-2 | ✅ 映射成立 |
| TODO-2 | AC-1 | ⚠️ 映射成立，但受 P0-1 / P1-3 影响 |
| TODO-3 | AC-3、AC-4 | ✅ 映射成立 |
| TODO-4 | AC-5、AC-6 | ❌ 目标映射成立，但方案无法满足新鲜度前提（P0-2） |
| TODO-5 | AC-5、AC-6 | ⚠️ 受 P0-2 / P1-3 影响 |

每条 AC 均至少被一条 TODO 覆盖，没有越界 TODO 或悬空 AC。

## 粒度检查

TODO 数：5（软标 3-7 / 硬标 10）｜ 全文：90 行（软标 500 / 硬标 700）｜ 结论：合规。

Batch 1 可形成抽库 MVP；Batch 2a 文件集为 `config.py`，Batch 2b 文件集为 `freshness.py` + `eo-board`，文件不相交，且都只依赖已完成的 Batch 1，没有彼此的生产者-消费者关系，并行标注成立。

## 前提真实性抽查（维度 7）

| 断言 | 基线 | 证据 | 判定 |
|------|------|------|------|
| TODO-1 新增 `cli/eo_lib/*` 的父模块与抽取源已存在 | `base_commit`=`f885f1c` | `git cat-file -e f885f1c:cli/eo-board` → exit 128；工作区仅有 `?? cli/eo-board` | ❌ 不成立（P0-1） |
| TODO-2 修改 `cli/eo-board`，对象存在且函数形态匹配 | `base_commit`=`f885f1c` | HEAD 无该路径；工作区文件才有 `find_project_config` 等 14 个目标函数 | ❌ 不成立（P0-1） |
| TODO-3 修改 Batch 1 新增的 `config.py` | 本 change 批间依赖 | TODO-1 明确先新增 `cli/eo_lib/config.py`，Batch 2a 后消费 | ✅ 成立 |
| TODO-4 新增 `freshness.py`，无命名冲突 | HEAD + 未提交 diff | `find cli -maxdepth 2` 仅见 `cli/eo-board`，不存在 `eo_lib/freshness.py` | ✅ 成立，但受 P0-1 父模块基线影响 |
| TODO-5 修改 serve 请求处理，对象形态匹配 | `base_commit`=`f885f1c` | HEAD 无该路径；工作区 `cli/eo-board:1831-1840` 才有 `/` 与 `/data.json` 每次调用 `build_data` 的 handler | ❌ 不成立（P0-1） |
| eo-board 当前未合并 `.eo-project.local.json` | HEAD + 未提交 diff | 工作区 `cli/eo-board:53-69` 只读取主配置并直接填默认值 | ✅ 成立 |
| serve 当前每个数据请求都全量重建 | HEAD + 未提交 diff | 工作区 `cli/eo-board:1831-1840` 的 `/`、`/data.json` 均直接调用 `build_data` | ✅ 成立 |
| HEAD + mtime + worktree 路径集合足以判定 `build_data` 新鲜度 | 当前兼容性 | `cli/eo-board:413-418`、`:672-677`、`:861-863` 另依赖日期、all refs 与分支名 | ❌ 不成立（P0-2） |

高风险抽样覆盖：变更前抽取源、符号链接安装前提、缓存兼容性；机械核验覆盖了全部 5 条 TODO 的新增/修改对象。

## 结构完整性

| 节 | 状态 | 备注 |
|----|------|------|
| 速览 | ✅ | 用户可见差异与 §1/§2 基本一致 |
| §1 意图 + 已钉决策 | ❌ | C1 边界清楚，但变更前基线不成立 |
| §2 验收清单 | ⚠️ | 覆盖正常/异常/边界；heavy 验证归属需收敛 |
| §3 TODO（Batch） | ❌ | 映射和并行拆分成立，但缓存键方案与修改对象基线存在 P0 |
| 条件节 §4-§8 | ⚠️ | §4/§5/§8 触发合理，§6/§7 无触发；§5 依赖模型需补齐 |

## 复审记录（第 2 轮 · 全量 · 2026-07-24）

- 模式判定：自动升级全量。命中两条机械信号：§1 已钉决策新增基线、缓存依赖闭合和错误所有权；AC-1/5/6 发生语义性改写。
- 核销 P0-1：verified。`git cat-file -e 792522d:cli/eo-board` 成功，基线文件为 1925 行；同一基线的 `install.sh` 含 CLI 符号链接入口，skill 侧 local 合并契约可追溯。§1、AC-1、TODO-1/2、§4 均统一锚定 `792522d`。
- 核销 P0-2：verified。§5 已把 worktree 路径/分支/HEAD、refs 指纹、当天日期和 changes/backlog/roadmap mtime 与 `build_data` 输入逐项对应；TODO-4 与 AC-6 覆盖跨日/月、同 SHA 换分支和 ref-only 更新。
- 核销 P1-1：verified。frontmatter 与 INDEX 均改为 `type: enhance`，§1 明确抽库只是内部重构子任务。
- 核销 P1-2：verified。§1、TODO-1/2 与 §5 一致规定共享层抛 `ConfigError`、CLI 入口负责格式化与退出。
- 核销 P1-3：verified。TODO-2/5 的完成门均改为不起服务的确定性检查；`--serve` 端到端对照留给测试阶段，AC-5 以 `build_data` 调用计数为通过依据。
- 全量复核：6 条 AC 均可验证且含异常路径；5 条 TODO 与 AC 双向覆盖，无占位符或循环依赖；Batch 2a/2b 文件集不相交且无逻辑依赖；全文 105 行、TODO 5 条，粒度合规；§4/§5/§8 触发合理，§6/§7 无触发。
- 新增 finding：无。
- 未决：无。结论：通过。

## 速报

结论：通过（P0 0 条）［第 2 轮 · 全量］
P0（阻塞 implement）：无
P1（移交起草方裁决，不阻塞循环）：无（上一轮 3 条均已 verified）
P2（可后置）：无
下一步：`/eo-implement eo-doc/changes/01-shared-lib-board-cache/change.md`（status 仍为 draft，先回 /eo-change 对话确认）。未决 P1：无。注意：`/eo-review` 是代码审查，要在 implement 之后，现在还不轮到它。
