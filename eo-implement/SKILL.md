---
name: eo-implement
description: |
  按 change.md 的 TODO 分批落地代码，批末自验对应 AC。触发：实现 / 写代码 / implement / /eo-implement。
  NOT FOR: bug 与反馈修复（口喷 bug 与 test/review/acceptance 循环内反馈一律走 /eo-fix）；变更起草（走 /eo-change）。
---

# eo-implement — 代码实现

按 change.md 实施代码。TODO 按 Batch 分组执行，**批末 checkpoint**：自验该批对应的 AC、勾选进度、汇报，再决定是否继续。v3 起**测试是普通工程实践**——需要就写，遵循项目既有测试约定；不再有独立 tester 前置锁定。

## 核心原则

1. **严格遵循 change**：按 §5 TODO 逐项实现；发现 change 有问题先告知用户，不自行改方案
2. **验收驱动**：AC（change.md §2）是完成判据——TODO 全勾 + 自动 AC 自验通过 = 实施完成；人工项归验收单（[../eo-shared/acceptance.md](../eo-shared/acceptance.md)）
3. **最小变更**：只实现 change 要求的内容，不做额外"优化"
4. **自验留证**：自动 AC 逐条按验证口径执行，命令 + 关键输出留在对话速报

## 前置条件

- **必须能找到 `.eo-project.json`**。同目录存在 `.eo-project.local.json` 时顶层字段覆盖合并（local 优先）。找不到 → 报错退出，提示运行 `/eo-project-init`
- 目标 `eo-doc/changes/<change-id>/change.md` 存在且 `status: confirmed` 或 `implementing`（`reviewed` 状态下的阻塞反馈修复归 /eo-fix 循环内分支——它会先按回退边置回 `implementing`）
- change 不存在 → 提示先执行 `/eo-change`；status: draft → 提示先在 /eo-change 完成确认

## 工作流程

1. **阅读上下文**
   - change.md（主输入：§1 意图与已钉决策、§2 AC、§5 TODO、§6 风险）
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
   - 按依赖顺序编码；每完成一个 TODO **立即在 change.md 勾选**——勾选门 = 常规绿灯（编译/lint/相关测试）
   - 测试随写：逻辑密集、边界多、会被后续变更反复触碰的验证点落成测试文件（遵循项目既有目录与命名约定）；其余靠一次性执行证据。写测试不是流程义务，是工程判断
   - 写码时**注释零溯源**：change/TODO/AC/finding 等流程标记不进注释，也不写「为何正确」的叙事注释（[../eo-shared/conventions.md](../eo-shared/conventions.md) §2.6）
   - 遇到 change 未覆盖的技术细节：能从代码/handbook 自答的自答；真正的决策问用户（一次 1-2 问）；发现要改的是前序 change 已引入并生效的对外契约/行为 → 按 [../eo-shared/questioning.md](../eo-shared/questioning.md) §4「破坏性变更类问题」强制问直接替换还是保留兼容，**不得自答代入**，结论回补 change.md §1
   - 发现 TODO/AC 写漏：告知用户，经确认后就地补进 change.md（意图不变的精化），再继续；补的是人工项且验收单已生成 → 同步补验收项（未勾）

5. **批末 checkpoint（STOP and VALIDATE）**
   - 自验该批对应的**自动 AC**：按 §2/§3 的验证口径逐条执行（需要起环境的照起，环境纪律见 [../eo-shared/ac-spec.md](../eo-shared/ac-spec.md)「起环境的纪律」——探测复用、按环境组合分组跑），通过则勾选，证据留在汇报里
   - **UI 变化留截图**：本批涉及 UI 变化时，自验当下把关键界面截图存进 change 目录 `shots/`（`<批号>-<场景>.png`），纪律见 [../eo-shared/evidence.md](../eo-shared/evidence.md)「截图纪律」
   - **人工项（「人工:」标记）不代勾**，留给验收单
   - 提交本批代码：commit message 带 `[<change-id>]` 前缀（推荐一次 change 一次 commit，分批时一批一 commit）
   - **提交前注释自检（必做）**：对本批 diff 的新增注释行扫溯源 token（`AC-\d`、`TODO-\d`、当前 change slug）——命中按 conventions §2.6 语义判定，确属溯源标注/叙事辩护的清理后再提交
   - **合流 checkpoint**（仅并行层）：本批是同层并行批的最后一批时，加跑合流校验（granularity §6）——合并结果常规绿灯 + 该层各批对应 AC 复核
   - 汇报：本批完成的 TODO / 勾掉的 AC（附一句证据）/ 未过项，询问「继续下一批 / 停」

6. **全部完成 → 生成交付证据面（必产）+ 人工验收单（软门，不阻塞）**
   - TODO 全勾、自动 AC 全部自验通过后，**无论有无人工项**都按 [../eo-shared/evidence.md](../eo-shared/evidence.md) 生成 `evidence.md`（三段：入口与环境 / 过程证据 / 怎么验；先查项目 `eo-doc/templates/evidence-*.md` 预设，命中优先；无可观察面的最薄形态三段各一行）。自验起过的环境按 ac-spec 纪律不主动停——把可访问地址与状态写进「入口与环境」段
   - 若存在**人工 AC**，按 [../eo-shared/acceptance.md](../eo-shared/acceptance.md) 生成 `acceptance.md`（操作步骤写实现后才确定的入口/路径/数据），速报：

     ```
     ✅ 自验通过 <n>/<n>（<测试/回归摘要一句>）
     🧾 交付证据面：<evidence.md 路径>（入口：<URL/命令，无则「无」>）
     📋 人工验收单已生成（<m> 条人工项）：<acceptance.md 路径>
        现在验或归档前验都行；对我说「带我验收」可逐项走查。
     建议下一步：<默认 /eo-archive；命中信号且未豁免 → 对应闸门（/eo-test 或 /eo-review）>
     ```

     无人工项时速报去掉 📋 行。**不阻塞等待表态**（人工验收的唯一硬门在 /eo-archive）；用户此刻就确认的项照常按验收单规则处理；用户指出问题 → 转 /eo-fix 循环内分支
   - `status` 保持 `implementing`——`reviewed` 只在实际跑了 /eo-review 并通过时由它设置

### 偏差记录

默认不生成额外文档。仅当实施偏离 change（方案临时变更、发现遗漏依赖、技术障碍绕行）时，创建 `changes/<change-id>/implement.md` 只记偏差本身。模板见 [references/implement-deviation-template.md](references/implement-deviation-template.md)。

## 关键约束

- **不跳过 TODO**、不跳过批末 AC 自验
- **并行批纪律**：同层批（字母后缀）的跨 worker 并行只发生在 eo-loop 派发的隔离 worktree 里，本 skill 内串行执行；层末合流 checkpoint 必跑（granularity §6）
- **勾选即时**：TODO/AC 完成立即在 change.md 勾选，不攒批
- **commit 前缀**：所有实施提交带 `[<change-id>]`（archive 靠它归集区间）
- **注释纪律**：一切流程溯源标注严禁进代码注释（溯源走 commit 前缀）；注释只写代码表达不了的约束、一两行为限，见 conventions §2.6
- **status 自动流转**：confirmed→implementing 由本 skill 写入；reviewed 由 /eo-review（如被调用）通过后写入；archived 由 /eo-archive 写入
- **不偏离 change**：方案问题上报用户；就地补 AC/TODO 仅限意图不变的精化
