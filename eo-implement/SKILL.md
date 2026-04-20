---
name: eo-implement
description: 根据 change.md 的 TODO 落地代码；也负责 change 生命周期内所有 bug 修复（fix 是 implement 的职责，不开新 change）。触发：实现 / 写代码 / implement / fix / 修 bug / /eo-implement。
---

# eo-implement — 代码实现

根据 change.md 实施代码，或根据 test/review 反馈修复缺陷。**fix 属于 implement 的职责范围**——change 的实施没有正确达成 spec 描述，就继续 implement 直到对齐，不引入新 change。

## 核心原则

1. **严格遵循 change**：按照 change.md `## 4 实施方案` 的 TODO 逐项实现
2. **架构一致**：遵循项目既有的架构、模块边界与依赖方向
3. **最小变更**：只实现 change 要求的内容，不做额外"优化"
4. **fix 不外溢**：所有 bug 修复都在当前 change 内循环（implement → test → review → implement fix），不开新 change

## 模板发现

启动时读 `eo-doc/templates/project-profile.md` 和 `implement-layers.md`（存在则启用分层执行，否则全量执行）。

## 前置条件

- **必须能找到 `.eo-project.json`**。找不到 → 报错退出，提示运行 `/eo-project-init`。`eo-doc/` 路径通过 `doc_root` 字段解析
- 目标 `eo-doc/dev/<module-name>/changes/<change-id>/change.md` 存在且 `status: approved` 或 `implementing`
- 对应模块的 `eo-doc/dev/<module-name>/spec.md` 可访问（作为基线参考）
- 若 change 不存在 → 提示用户先执行 `/eo-change`

## 工作流程

### 模式一：首次实施（按 change 的 TODO 实现）

1. **阅读上下文**
   - change.md（主输入）、模块 spec.md（基线参考）
   - 项目级背景文档（若存在）
   - 现有代码，理解命名规范与既有模式

2. **将 change 状态置为 implementing**
   - 将 change.md frontmatter 的 `status` 从 `approved` 改为 `implementing`（若尚未改）

3. **确认 TODO 范围**
   - 列出所有 TODO 及其 Part/层，向用户确认本次执行范围
   - 按依赖关系确定执行顺序

4. **逐项实现**
   - 按顺序编码
   - 每完成一个 TODO，运行相关验证
   - **立即在 change.md 将对应的 `- [ ]` 勾选为 `- [x]`**
   - 遇到 change 未覆盖的技术细节，向用户澄清后再继续

5. **偏差记录**
   - 默认不生成额外文档
   - 仅当实施过程偏离 change（方案临时变更、发现遗漏依赖、技术障碍绕行）时，创建 `changes/<change-id>/implement.md` 记录偏差
   - 偏差只写偏差本身，不重复 change 内容

6. **自查**
   - 代码可编译/可构建/可运行
   - 未破坏已有验证流程
   - 无明显安全风险

7. **完成标记**
   - 所有 TODO 勾选完成后，告知用户进入 `/eo-test`
   - 暂不把 change 状态改为 `done`——`done` 由 review 通过后才设置

### 模式二：fix 循环（根据 test/review 反馈修复）

**适用场景**：
- `test.md` 有 `❌ FAIL`
- `review.md` 有 P0/P1 issue
- 归档后发现实现不符合 spec 的缺陷（仍属于上一次 change 的实施补救，不开新 change）

**流程**：
1. 读对应反馈文档（`changes/<change-id>/test.md` 或 `review.md`）
2. 按优先级（P0 > P1 > P2）逐一修复
3. 每修复一个问题，运行对应验证
4. 修复完成后通知用户重新 `/eo-test` 或 `/eo-review`
5. **不引入新 change**：fix 是 implement 的内嵌职责
6. **不改 change.md §3**：fix 只调整代码，不改 change.md 的 §3（Delta 模式下的 ADDED/MODIFIED/REMOVED，或 bootstrap 模式下的实现范围）

### 分层执行（仅 implement-layers.md 存在时）

1. **层级选择**：列出所有 Part 及 TODO 数量，供用户选择执行范围（如"只实施 Server 的 TODO"）
2. **按层筛选**：按选定 Part 的 TODO 前缀筛选待执行项
3. **层切换检查**：切换层时
   - 确认前置层 TODO 已全部完成
   - 确认前置层的生成/导出脚本已执行（如有）
   - 加载 implement-layers.md 中该层的实施约束
4. **层内执行**：在该层范围内逐项实施，遵循该层特定约束
5. **跨层依赖**：当前 TODO 依赖其他层时，确认依赖已完成再执行

若无 implement-layers.md，忽略此段，全量执行。

## 偏差记录模板

见 [references/implement-deviation-template.md](references/implement-deviation-template.md)。

## 关键约束

- **不跳过 TODO**：按依赖顺序执行，不跳过前置依赖
- **不偏离 change**：如果发现 change 有问题，先告知用户，不要自行调整方案
- **不遗漏验证**：每个 TODO 的验收标准必须可验证
- **勾选进度**：完成 TODO 后必须在 change.md 中勾选
- **fix 不升格**：bug 修复是 implement 内嵌职责，**不以任何形式升格为新 change**
- **不改 §3**：即便 fix 期间发现 §3 写错了（Delta 或实现范围），也不在 implement 阶段改——上报用户手工处理；若属"spec 本身错了"则改为开 enhance change 承接
