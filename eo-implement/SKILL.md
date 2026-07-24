---
name: eo-implement
description: |
  按 change.md 的 TODO 分批落地代码，批末验证对应 AC；也承接 test/review 反馈的修复循环。触发：实现 / 写代码 / implement / /eo-implement。
  NOT FOR: 口喷 bug 的定位与修复（走 /eo-fix）；变更起草（走 /eo-change）。
---

# eo-implement — 代码实现

按 change.md 实施代码。TODO 按 Batch 分组执行，**批末 checkpoint**：验证该批对应的 AC、勾选进度、汇报，再决定是否继续。

## 核心原则

1. **严格遵循 change**：按 §3 TODO 逐项实现；发现 change 有问题先告知用户，不自行改方案
2. **验收驱动**：AC（change.md §2）是完成判据——TODO 全勾 + **auto-light AC** 验证通过 = 实施完成；auto-heavy 归 /eo-test、manual 归人工验收单（三级归属见 [../eo-shared/ac-spec.md](../eo-shared/ac-spec.md)）
3. **最小变更**：只实现 change 要求的内容，不做额外"优化"
4. **修复循环不外溢**：test/review 反馈的缺陷在当前 change 内修复，不开新 change

## 前置条件

- **必须能找到 `.eo-project.json`**。同目录存在 `.eo-project.local.json` 时顶层字段覆盖合并（local 优先）。找不到 → 报错退出，提示运行 `/eo-project-init`
- 目标 `eo-doc/changes/<change-id>/change.md` 存在且 `status: confirmed` 或 `implementing`（**修复循环例外**：存在阻塞反馈时允许 `reviewed` 进入模式二——它会先按回退边置回 `implementing`）
- change 不存在 → 提示先执行 `/eo-change`；status: draft → 提示先在 /eo-change 完成确认
- frontmatter `tier: light` → 走**轻模式**（见下）；缺省/`full` → 模式一

## 工作流程

### 模式一：首次实施（按 Batch 执行）

1. **阅读上下文**
   - change.md（主输入：§1 意图与已钉决策、§2 AC、§3 TODO、条件节）
   - `eo-doc/agent-handbook/` 中相关代码地图（经 INDEX 定位），理解入口与既有模式
   - lessons 消费：按 [../eo-shared/lessons.md](../eo-shared/lessons.md) §1 扫 INDEX 匹配 trigger，命中读「规则」节带入
   - 涉及 UI 且仓库根有 `DESIGN.md` → 读入并遵守

2. **首次启动登记**
   - frontmatter 写入 `base_commit: <当前 HEAD>`（已有则不动）
   - `status: confirmed → implementing`（skill 自动改，不要求用户操作）——流转期零投影动作，看板由 archive 收口的 `eo-sync run` 或手动同步刷新

3. **确认执行范围**
   - 列出各 Batch 及 TODO 数，默认从第一个未完成 Batch 开始；用户可指定只跑某批
   - **同层并行批**（字母后缀，如 Batch 2a/2b）互不干扰，可乱序执行或只跑其一；本 skill 单会话内仍**串行**执行——跨 worker 并行派发归 /eo-loop（判据/隔离/合流见 [../eo-shared/granularity.md](../eo-shared/granularity.md) §6）

4. **批内逐项实现**
   - 按依赖顺序编码；每完成一个 TODO **立即在 change.md 勾选**——带「完成判据」的先跑判据再勾；无判据的（一对一映射）以常规绿灯（编译/lint/相关单测）为勾选门，其对应 AC 留待批末 checkpoint 验证
   - 写码时**注释零溯源**：change/TODO/AC/finding 等流程标记不进注释，也不写「为何正确」的叙事注释（[../eo-shared/conventions.md](../eo-shared/conventions.md) §2.6）
   - 遇到 change 未覆盖的技术细节：能从代码/handbook 自答的自答；真正的决策问用户（一次 1-2 问）；发现要改的是前序 change 已引入并生效的对外契约/行为 → 按 [../eo-shared/questioning.md](../eo-shared/questioning.md) §4「破坏性变更类问题」强制问直接替换还是保留兼容，**不得自答代入**，结论回补 change.md §1
   - 发现 TODO/AC 写漏：告知用户，经确认后就地补进 change.md（意图不变的精化），再继续；补的是 manual 项且验收单已生成 → 同步补验收项（未勾）

5. **批末 checkpoint（STOP and VALIDATE）**
   - 验证该批对应的 **auto-light AC**：按 §2 的验证口径（「验证」栏，省略时按声明本身）逐条执行，通过则勾选。**跑为主，写为例外**——优先以既有绿灯（编译 / lint / 已有测试）与一次性冒烟命令作勾选证据，仅当验证口径无法用一次性手段满足时才新写测试文件；回归资产的系统性沉淀归 /eo-test（审计 + 补缺，批末落下的测试它不重写）
   - **auto-heavy AC 不跑、不勾、不代验**（需起服务 / 多环境组合 / 点击流；判不准按 heavy）——重验证收敛到 /eo-test 一次跑完，**implement 不起环境**；汇报里列为「待 test」
   - **manual 类（「人工:」标记）不代勾**，留给完成时的人工验收门
   - 提交本批代码：commit message 带 `[<change-id>]` 前缀（见 [../eo-shared/conventions.md](../eo-shared/conventions.md)；推荐一次 change 一次 commit，分批时一批一 commit）
   - （可选自检）对本批 diff 的**新增注释行**扫溯源 token（`P[012]-\d`、`AC-\d`、`TODO-\d`、当前 change slug）——提示不门禁，命中列出人工判定，按 §2.6 清理
   - **合流 checkpoint**（仅并行层）：本批是同层并行批（字母后缀）的最后一批时，加跑一次合流校验（[../eo-shared/granularity.md](../eo-shared/granularity.md) §6）——合并结果常规绿灯 + 该层各批对应 AC 复核；单会话串行执行时即该层 AC 验证的汇总，不重复起验证
   - 汇报：本批完成的 TODO / 勾掉的 AC / **待 test 的 heavy AC** / 验证结果，询问「继续下一批 / 停」

6. **全部完成 → 生成人工验收单（软门，不阻塞）**
   - TODO 全勾、auto-light AC 全部验证通过后，若存在 **manual 类 AC**（「人工:」标记），按 [../eo-shared/acceptance.md](../eo-shared/acceptance.md) 生成 `acceptance.md`（操作步骤写实现后才确定的入口/路径/数据），速报：

     ```
     ✅ 轻验证通过 <n>/<n>（<测试/回归摘要一句>）
     ⏳ 待 test 的重验证项：<h> 条（<AC 编号>）；无 heavy 项省略此行
     📋 人工验收单已生成（<m> 条人工项）：<acceptance.md 路径>
        现在验或归档前验都行；对我说「带我验收」可逐项走查。
     建议下一步：<eo-test / eo-review 择一>
     ```

     **下一步二选一，无固定默认**，按本 change 的风险面判：行为面广、heavy AC 多、主要风险是「跑不跑得通」→ 先 `/eo-test`；逻辑密集、边界多（算法 / 数据处理 / 协议解析），主要风险是「想没想到」→ 先 `/eo-review`（读码为主、不起环境，缺陷早暴露，且 test 不会因随后的修复而白跑）。

     **不阻塞等待表态**（人工验收的唯一硬门在 /eo-archive）；用户此刻就确认的项照常代勾（勾的备注 = 用户结论）；用户指出问题 → 回本 skill 修复循环。**无 manual 项的 change 不生成验收单、不打扰**
   - `status` 保持 `implementing`——`reviewed` 由 review 通过后设置

### 模式二：修复循环（test/review/acceptance 反馈）

**适用**：`test.md` 有 ❌ FAIL，`review.md` 有 P0/P1，或 `acceptance.md` 有「不通过」项。status 为 `reviewed` 时（产出阻塞结果的 skill 正常已按回退边置回；没置则此刻补）→ 先置回 `implementing`。**轻档反馈**（显式 light test/review 的 tmp 报告、用户口头打回、独立复核不通过）也走本模式——只执行第 2-4、6 步（无台账无计数，跳过 0/1/5/7）。

0. **触发集判定与熔断检查**（修复动手前，全档专属）
   - 触发集 = 各失败反馈的稳定标识（`review#<轮次>` / `test#<轮次>` / `acceptance#<AC编号>@<验收基线sha>`）中**未出现在 frontmatter `fix_consumed`** 的部分；报告所属 revision < 当前 `plan_revision` 的反馈（回炉已作废）**不构成触发集**
   - 触发集为空 → 跨会话续修上一轮，**不计数**，直接进第 1 步
   - 触发集非空且 `fix_rounds`（缺省 0）已 ≥ 3 → **停，不开始修复**，用户三选一：
     a) **豁免一轮**：放行本轮，change.md 末尾记「熔断豁免：第 N 轮，<日期>」；下一个新触发集重新过闸。用户明确要求永久关闭 → 记「熔断：用户显式关闭，<日期>」，此后不再拦
     b) **卡点检查**：走下方子流程，按根因结论定出口
     c) **回炉**：转 /eo-change 回炉子流程（方案实质修订 + 重新确认）
   - 通过（或豁免）→ `fix_rounds` +1、触发集并入 `fix_consumed`（字段语义见 [../eo-shared/conventions.md](../eo-shared/conventions.md) §3）
1. **读取反馈（读取协议）**：同会话反馈已在上下文 → **不重读报告文件**；跨会话 → 只读报告的台账 + 末尾速报，按 `open` 项的最近轮**定点读**对应轮次详情节，不通读全文
2. 按 P0 > P1 > P2 逐一修复；修复代码**注释零溯源**——finding/AC/TODO 标记与「为何正确」的辩护不进注释（[../eo-shared/conventions.md](../eo-shared/conventions.md) §2.6）
3. **双向取证，取最低成本层**：每个缺陷**先复现失败、修后在同层验通过**——「改完看起来对了」不算证据。复现在**能复现它的最低成本层**做：纯逻辑用单测 / `node -e` 等价复刻（秒级），接口契约用一次请求，**确属集成 / UI 态才起环境**。不要每改一行就重新 build + 起环境
4. 涉及的 **auto-light AC 就地重验**；**auto-heavy 的复验归 /eo-test**（收口时一次跑完，不在修复循环里反复起环境）；被本次修复弄脏的**已勾** AC 按 [../eo-shared/ac-spec.md](../eo-shared/ac-spec.md)「勾变脏即取消」处理；修复改变了人工项的入口/行为 → 按 [../eo-shared/acceptance.md](../eo-shared/acceptance.md)「失效与重置」更新对应验收项（步骤刷新、取消勾选并注明原因、刷新验收基线）
5. **回写台账**：每个缺陷修复并同层验通过后，把对应报告台账行置 `fixed` 并填修复 commit——`verified` 由复审方核销，本 skill 不写
6. 修复提交带 `[<change-id>]` 前缀
7. 完成后提示重新 `/eo-test` 或 `/eo-review`
8. 修复不开新 change；发现根源是方案/需求问题 → 停下告知用户，转 /eo-change **回炉子流程**（实质修订 + 重新确认；意图不变的口径精化不必全量回炉，就地补 AC 即可）

#### 卡点检查子流程（熔断三选一选 b 时执行）

spawn 一个**新鲜上下文 subagent**（执行者自述不作数——修了 3 轮的 agent 是判断自己为何修不好的最差人选），输入按 manifest 给，**禁止默认通读报告全史**：

- 当前 revision 的 change.md 全文
- test.md / review.md 的台账 + 末尾速报 + open/fixed 项定点详情
- change-review.md 当前结论、acceptance.md 不通过项、implement.md 偏差记录（各自存在时）
- `[<change-id>]` 提交列表与涉及文件的 scoped diff、本 change 相关的未提交脏 diff

产出四分类根因 + 建议出口：

| 根因 | 出口 |
|------|------|
| change 方案/架构不合理 | 转 /eo-change 回炉子流程 |
| AC 口径漂移（各轮按不同理解打回） | 回 /eo-change 钉死口径（意图不变的精化，不必全量回炉） |
| 纯实施质量问题 | 方向没错，建议豁免一轮继续修 |
| 测试基建/环境假失败 | 修基建；台账根因列标 `environment`，结论注明假失败轮数供用户裁决（计数不自动回退） |

结论一行写入 change.md 末尾：`卡点检查：<根因>，<日期>，第 N 轮`。**失败关闭**：subagent 起不了（槽位/工具不可用）→ 不得用执行者自述替代，记「卡点检查未执行」，用户在「稍后重试 / 直接回炉 / 单轮豁免」中裁决。

### 轻模式（tier: light）

替代模式一的 Batch 结构；test/review 反馈的修复仍走模式二。

1. **上下文与登记**：读 change.md（意图 + AC）、handbook INDEX 命中篇目、lessons 命中项（[../eo-shared/lessons.md](../eo-shared/lessons.md) §1）；涉及 UI 且仓库根有 `DESIGN.md` → 读入并遵守。写 `base_commit`、`status → implementing`（流转期零投影）
2. **测试锁定**（按 AC 性质分流）：
   - 新增/变更行为的 auto AC → 落成失败测试，确认**因断言失败**（而非报错/导入错误）
   - 「行为不变」类（characterization）→ 基线即绿合法，**不强制先红**，但须注明覆盖了哪些现有行为
   - 可静态判定的负向约束 → 锁成 lint/静态检查命令
   - AC 零 auto → 跳过本步（完成门只走独立复核 + manual）
   - 项目无测试基建 → 停，问用户：转全档，或接受无锁定轻档（在 change.md 注明，完成门只剩复核 + manual）

   锁定内容单独 commit（`[<change-id>]` 前缀），commit hash 写入 frontmatter `test_lock_commit`；AC 行回填「锁定：<测试文件>#<用例>」。**出现 auto-heavy 验证需求（起服务/多环境/点击流）→ 停，报扩档**。观感类不落测试，保持书面
3. **实施**：自拆 TODO（对话内列出，**不写入 change.md**）；**禁改测试文件**——确需改（AC 本身写错）→ 停手上报，用户确认改 AC 后重锁再继续；注释零溯源（conventions §2.6）
4. **完成门**（全过才算完）：
   - 锁定测试全绿 + lint/typecheck 绿
   - **独立复核**：spawn 一个新鲜上下文 subagent，输入 = change.md + `test_lock_commit..HEAD` 完整 diff（含测试文件改动历史）+（UI 时）DESIGN.md，核对「AC 逐条被真实覆盖？锁定后测试是否被弱化/删除/篡改？有无过拟合 / 硬编码特判 / 绕过验证？diff 里有无 AC 之外的多余实现（镀金）？注释有无流程溯源标注 / 叙事辩护（conventions §2.6）？」——执行者自述不作数。结论一行写入 change.md 末尾（`独立复核：通过/不通过，<日期>，基线 <short-sha>`）；发现问题 → 修复后重跑完成门
   - manual 项（「人工:」）逐项请用户确认，**代勾必须附确认记录**（AC 行后「确认：<用户原话要点>，<日期>，基线 <short-sha>」，规范见 [../eo-shared/ac-spec.md](../eo-shared/ac-spec.md)）；manual 项 >2 条是扩档信号
5. **收口（完成门通过后立即执行，不得延迟）**：内嵌调用 `/eo-archive` 走**轻档门**（读其 SKILL.md 照做：留痕校验 → 结算 → 元数据冻结 → 显式 doc sync → GitHub 联动 → stub 终态；完成门刚跑过且其后无新提交的锁定测试绿灯可复用）——归档步骤以 eo-archive 为唯一信源，本 skill 不复述。值得留的决策按 eo-project-record 门槛落 decisions/。**不产 test.md / review.md**
6. **扩档**（任一信号：影响面圈不住 / 两次以上跑偏 / AC 超 5 条装不下 / auto-heavy 出现 / manual 项 >2）：停手告知用户，转 /eo-change「扩档子流程」——tier 改 full、已完成工作映射为已勾 TODO、用户再确认（风险触发的建议跑全量 change-review）；然后回本 skill 模式一从首个未完成 Batch 续走。`test_lock_commit` 与已锁定测试保留，文件不挪、commit 前缀不变

### 偏差记录

默认不生成额外文档。仅当实施偏离 change（方案临时变更、发现遗漏依赖、技术障碍绕行）时，创建 `changes/<change-id>/implement.md` 只记偏差本身。模板见 [references/implement-deviation-template.md](references/implement-deviation-template.md)。

## 关键约束

- **不跳过 TODO**、不跳过批末 AC 验证
- **并行批纪律**：同层批（字母后缀）的跨 worker 并行只发生在 eo-loop 派发的隔离 worktree 里，本 skill 内串行执行；层末合流 checkpoint 必跑（granularity §6）
- **重验证不在 implement 跑**：auto-heavy AC（起服务 / 多环境组合 / 点击流）归 /eo-test——implement 不起环境、不跑环境矩阵、不代勾 heavy 项；判不准 light/heavy 按 heavy 处理
- **批末跑为主，写为例外**：全档批末验证优先用既有绿灯与一次性冒烟作证据，不为过批末门系统性编写测试——回归资产的沉淀归 /eo-test（轻模式的测试锁定不受此限，它是轻档唯一证据门）
- **修复循环双向取证**：先复现失败再修，且复现取最低成本层——起环境是最后手段，不是默认
- **勾选即时**：TODO/AC 完成立即在 change.md 勾选，不攒批
- **commit 前缀**：所有实施提交带 `[<change-id>]`（archive 靠它归集区间）
- **注释纪律**：一切流程溯源标注（change 编号/slug、TODO/AC、finding P0-x/P1-x、FAIL-x、批次号）**严禁**进代码注释（溯源走 commit 前缀）；注释只写代码表达不了的约束、一两行为限，不写「为何正确」的辩护，见 [../eo-shared/conventions.md](../eo-shared/conventions.md) §2.6
- **熔断纪律**：`fix_rounds`/`fix_consumed` 由模式二第 0 步维护——触发集空不计数、到限必停三选一、回炉确认后归零；台账回写只置 `fixed`（verified 归复审方）
- **轻/全档计数边界**：轻档不用 `fix_rounds`/报告台账——其熔断 = 两次以上跑偏即扩档（granularity §5 扩档信号）；显式 light review/test 的 tmp 报告不触发计数；扩档转 full 确认后模式二计数从 0 起
- **status 自动流转**：confirmed→implementing 由本 skill 写入；reviewed 由 review 通过后写入；轻档 archived 由收口内嵌调用的 eo-archive（轻档门）写入
- **轻模式纪律**：TODO 不写入 change.md、禁改测试文件、完成门必过独立复核；扩档信号出现即停手报告
- **修复循环不升格**：test/review 反馈的缺陷不以任何形式开新 change
- **不偏离 change**：方案问题上报用户；就地补 AC/TODO 仅限意图不变的精化
