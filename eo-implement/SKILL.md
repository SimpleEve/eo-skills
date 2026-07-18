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

- **必须能找到 `.eo-project.json`**。找不到 → 报错退出，提示运行 `/eo-project-init`
- 目标 `eo-doc/changes/<change-id>/change.md` 存在且 `status: confirmed` 或 `implementing`
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
   - `status: confirmed → implementing`（skill 自动改，不要求用户操作）；联动钩子刷新 stub（[../eo-shared/board-github.md](../eo-shared/board-github.md)，未开启跳过）

3. **确认执行范围**
   - 列出各 Batch 及 TODO 数，默认从第一个未完成 Batch 开始；用户可指定只跑某批

4. **批内逐项实现**
   - 按依赖顺序编码；每完成一个 TODO **立即在 change.md 勾选**——带「完成判据」的先跑判据再勾；无判据的（一对一映射）以常规绿灯（编译/lint/相关单测）为勾选门，其对应 AC 留待批末 checkpoint 验证
   - 遇到 change 未覆盖的技术细节：能从代码/handbook 自答的自答；真正的决策问用户（一次 1-2 问）
   - 发现 TODO/AC 写漏：告知用户，经确认后就地补进 change.md（意图不变的精化），再继续；补的是 manual 项且验收单已生成 → 同步补验收项（未勾）

5. **批末 checkpoint（STOP and VALIDATE）**
   - 验证该批对应的 **auto-light AC**：按 §2 的验证口径（「验证」栏，省略时按声明本身）逐条执行，通过则勾选
   - **auto-heavy AC 不跑、不勾、不代验**（需起服务 / 多环境组合 / 点击流；判不准按 heavy）——重验证收敛到 /eo-test 一次跑完，**implement 不起环境**；汇报里列为「待 test」
   - **manual 类（「人工:」标记）不代勾**，留给完成时的人工验收门
   - 提交本批代码：commit message 带 `[<change-id>]` 前缀（见 [../eo-shared/conventions.md](../eo-shared/conventions.md)；推荐一次 change 一次 commit，分批时一批一 commit）
   - 联动钩子：刷新看板 stub 进度（[../eo-shared/board-github.md](../eo-shared/board-github.md)，未开启跳过）
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

### 模式二：修复循环（test/review 反馈）

**适用**：`test.md` 有 ❌ FAIL，`review.md` 有 P0/P1，或 `acceptance.md` 有「不通过」项（人工验收打回；此时 status 为 `reviewed` → 先置回 `implementing` 并联动 stub）。

1. 读对应反馈文档，按 P0 > P1 > P2 逐一修复
2. **双向取证，取最低成本层**：每个缺陷**先复现失败、修后在同层验通过**——「改完看起来对了」不算证据。复现在**能复现它的最低成本层**做：纯逻辑用单测 / `node -e` 等价复刻（秒级），接口契约用一次请求，**确属集成 / UI 态才起环境**。不要每改一行就重新 build + 起环境
3. 涉及的 **auto-light AC 就地重验**；**auto-heavy 的复验归 /eo-test**（收口时一次跑完，不在修复循环里反复起环境）；被本次修复弄脏的**已勾** AC 按 [../eo-shared/ac-spec.md](../eo-shared/ac-spec.md)「勾变脏即取消」处理；修复改变了人工项的入口/行为 → 按 [../eo-shared/acceptance.md](../eo-shared/acceptance.md)「失效与重置」更新对应验收项（步骤刷新、取消勾选并注明原因、刷新验收基线）
4. 修复提交带 `[<change-id>]` 前缀
5. 完成后提示重新 `/eo-test` 或 `/eo-review`
6. 修复不开新 change；发现问题根源是需求变更 → 停下告知用户，建议走 /eo-change

### 轻模式（tier: light）

替代模式一的 Batch 结构；test/review 反馈的修复仍走模式二。

1. **上下文与登记**：读 change.md（意图 + AC）、handbook INDEX 命中篇目、lessons 命中项（[../eo-shared/lessons.md](../eo-shared/lessons.md) §1）；涉及 UI 且仓库根有 `DESIGN.md` → 读入并遵守。写 `base_commit`、`status → implementing`、刷新 stub
2. **测试锁定**（按 AC 性质分流）：
   - 新增/变更行为的 auto AC → 落成失败测试，确认**因断言失败**（而非报错/导入错误）
   - 「行为不变」类（characterization）→ 基线即绿合法，**不强制先红**，但须注明覆盖了哪些现有行为
   - 可静态判定的负向约束 → 锁成 lint/静态检查命令
   - AC 零 auto → 跳过本步（完成门只走独立复核 + manual）
   - 项目无测试基建 → 停，问用户：转全档，或接受无锁定轻档（在 change.md 注明，完成门只剩复核 + manual）

   锁定内容单独 commit（`[<change-id>]` 前缀），commit hash 写入 frontmatter `test_lock_commit`；AC 行回填「锁定：<测试文件>#<用例>」。**出现 auto-heavy 验证需求（起服务/多环境/点击流）→ 停，报扩档**。观感类不落测试，保持书面
3. **实施**：自拆 TODO（对话内列出，**不写入 change.md**）；**禁改测试文件**——确需改（AC 本身写错）→ 停手上报，用户确认改 AC 后重锁再继续
4. **完成门**（全过才算完）：
   - 锁定测试全绿 + lint/typecheck 绿
   - **独立复核**：spawn 一个新鲜上下文 subagent，输入 = change.md + `test_lock_commit..HEAD` 完整 diff（含测试文件改动历史）+（UI 时）DESIGN.md，核对「AC 逐条被真实覆盖？锁定后测试是否被弱化/删除/篡改？有无过拟合 / 硬编码特判 / 绕过验证？」——执行者自述不作数。结论一行写入 change.md 末尾（`独立复核：通过/不通过，<日期>，基线 <short-sha>`）；发现问题 → 修复后重跑完成门
   - manual 项（「人工:」）逐项请用户确认，**代勾必须附确认记录**（AC 行后「确认：<用户原话要点>，<日期>，基线 <short-sha>」，规范见 [../eo-shared/ac-spec.md](../eo-shared/ac-spec.md)）；manual 项 >2 条是扩档信号
5. **收口（finalizer，顺序执行，不得减免）**：
   ① **结算**：确认全部实施变更已提交（`[<change-id>]` 前缀），工作区无本 change 残留
   ② **元数据**：自检 AC 勾选终态（每个 manual 勾有确认记录、独立复核记录存在，缺任一 → 不得归档）→ frontmatter 写 `commits`（`[<change-id>]` 前缀提交区间）、`status → archived` → INDEX 行终态（档列 light）+ seq 查重自愈 → 以上文档变更作一个收尾 meta commit
   ③ **显式触发 `/eo-doc-manager sync`**（cursor sync 无自动触发，不能指望兜底）；本 change 的 diff 不触碰代码路径时可跳过并说明
   ④ GitHub 联动开启时：按 [../eo-shared/board-github.md](../eo-shared/board-github.md) 执行 push/PR 与 issue body 终态刷新；**关 issue 放最后**
   ⑤ stub 终态 upsert；值得留的决策按 eo-project-record 门槛落 decisions/。**不产 test.md / review.md**
6. **扩档**（任一信号：影响面圈不住 / 两次以上跑偏 / AC 超 5 条装不下 / auto-heavy 出现 / manual 项 >2）：停手告知用户，转 /eo-change「扩档子流程」——tier 改 full、已完成工作映射为已勾 TODO、用户再确认（风险触发的建议跑全量 change-review）；然后回本 skill 模式一从首个未完成 Batch 续走。`test_lock_commit` 与已锁定测试保留，文件不挪、commit 前缀不变

### 偏差记录

默认不生成额外文档。仅当实施偏离 change（方案临时变更、发现遗漏依赖、技术障碍绕行）时，创建 `changes/<change-id>/implement.md` 只记偏差本身。模板见 [references/implement-deviation-template.md](references/implement-deviation-template.md)。

## 关键约束

- **不跳过 TODO**、不跳过批末 AC 验证
- **重验证不在 implement 跑**：auto-heavy AC（起服务 / 多环境组合 / 点击流）归 /eo-test——implement 不起环境、不跑环境矩阵、不代勾 heavy 项；判不准 light/heavy 按 heavy 处理
- **修复循环双向取证**：先复现失败再修，且复现取最低成本层——起环境是最后手段，不是默认
- **勾选即时**：TODO/AC 完成立即在 change.md 勾选，不攒批
- **commit 前缀**：所有实施提交带 `[<change-id>]`（archive 靠它归集区间）
- **status 自动流转**：confirmed→implementing 由本 skill 写入；reviewed 由 review 通过后写入；轻档 archived 由轻模式收口写入
- **轻模式纪律**：TODO 不写入 change.md、禁改测试文件、完成门必过独立复核；扩档信号出现即停手报告
- **修复循环不升格**：test/review 反馈的缺陷不以任何形式开新 change
- **不偏离 change**：方案问题上报用户；就地补 AC/TODO 仅限意图不变的精化
