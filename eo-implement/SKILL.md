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
2. **验收驱动**：AC（change.md §2）是完成判据——TODO 全勾且 AC 全部可验证通过才算实施完成
3. **最小变更**：只实现 change 要求的内容，不做额外"优化"
4. **修复循环不外溢**：test/review 反馈的缺陷在当前 change 内修复，不开新 change

## 前置条件

- **必须能找到 `.eo-project.json`**。找不到 → 报错退出，提示运行 `/eo-project-init`
- 目标 `eo-doc/changes/<change-id>/change.md` 存在且 `status: confirmed` 或 `implementing`
- change 不存在 → 提示先执行 `/eo-change`；status: draft → 提示先在 /eo-change 完成确认

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
   - 按依赖顺序编码；每完成一个 TODO 运行其「完成判据」，**立即在 change.md 勾选**
   - 遇到 change 未覆盖的技术细节：能从代码/handbook 自答的自答；真正的决策问用户（一次 1-2 问）
   - 发现 TODO/AC 写漏：告知用户，经确认后就地补进 change.md（意图不变的精化），再继续

5. **批末 checkpoint（STOP and VALIDATE）**
   - 验证该批对应的 AC：按 §2 的「验证」栏逐条执行，通过则勾选 AC
   - 提交本批代码：commit message 带 `[<change-id>]` 前缀（见 [../eo-shared/conventions.md](../eo-shared/conventions.md)；推荐一次 change 一次 commit，分批时一批一 commit）
   - 联动钩子：刷新看板 stub 进度（[../eo-shared/board-github.md](../eo-shared/board-github.md)，未开启跳过）
   - 汇报：本批完成的 TODO / 勾掉的 AC / 验证结果，询问「继续下一批 / 停」

6. **全部完成**
   - TODO 全勾 + AC 全部验证通过 → 告知用户进入 `/eo-test`
   - `status` 保持 `implementing`——`done` 由 review 通过后设置

### 模式二：修复循环（test/review 反馈）

**适用**：`test.md` 有 ❌ FAIL，或 `review.md` 有 P0/P1。

1. 读对应反馈文档，按 P0 > P1 > P2 逐一修复
2. 每修一个跑对应验证；涉及的 AC 重新验证
3. 修复提交带 `[<change-id>]` 前缀
4. 完成后提示重新 `/eo-test` 或 `/eo-review`
5. 修复不开新 change；发现问题根源是需求变更 → 停下告知用户，建议走 /eo-change

### 偏差记录

默认不生成额外文档。仅当实施偏离 change（方案临时变更、发现遗漏依赖、技术障碍绕行）时，创建 `changes/<change-id>/implement.md` 只记偏差本身。模板见 [references/implement-deviation-template.md](references/implement-deviation-template.md)。

## 关键约束

- **不跳过 TODO**、不跳过批末 AC 验证
- **勾选即时**：TODO/AC 完成立即在 change.md 勾选，不攒批
- **commit 前缀**：所有实施提交带 `[<change-id>]`（archive 靠它归集区间）
- **status 自动流转**：confirmed→implementing 由本 skill 写入；done 由 review 通过后写入
- **修复循环不升格**：test/review 反馈的缺陷不以任何形式开新 change
- **不偏离 change**：方案问题上报用户；就地补 AC/TODO 仅限意图不变的精化
