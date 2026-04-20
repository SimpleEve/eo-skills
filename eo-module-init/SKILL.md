---
name: eo-module-init
description: |
  为全新模块建立 spec 活文档并完成首次 spec-review，打好后续所有 change 的基线。触发：新建模块 / module init / 新模块 / /eo-module-init。
  NOT FOR: 修改已有模块（走 /eo-change）。
---

# eo-module-init — 模块初始化

为某个全新模块建立 `eo-doc/dev/<module-name>/spec.md` 活文档，过一次 spec-review 把基线质量把牢。**此 skill 一个模块只走一次**，后续所有修改通过 `/eo-change` 增量演化。

## 核心理念

1. **模块是一等公民**：独立目录 + 活文档 spec.md + changes/ 时间线
2. **基线质量**：只有模块首次建立时强制走 spec-review，后续增量 change 不再单独 review spec
3. **不含实施**：此 skill 只产出模块文档骨架，不写代码，不建 change

## 前置条件

- **必须能找到 `.eo-project.json`**。找不到 → 报错退出，提示运行 `/eo-project-init`。`eo-doc/` 路径通过 `doc_root` 字段解析
- 用户给定 `module-name`（小写 kebab-case，如 `inventory` / `transport-queue`）
- `eo-doc/dev/<module-name>/` 目录**不存在**（若存在则提示冲突，建议走 `/eo-change`）

## 工作流程

### 第一步：冲突检查

1. 检查 `eo-doc/dev/<module-name>/` 是否存在
2. 若存在：告知用户"该模块已存在，若要修改请走 `/eo-change`"，终止
3. 若不存在：继续

### 第二步：调用 eo-spec 写模块活文档

直接进入 **eo-spec 流程**（读其 SKILL.md 执行），产出位于 `eo-doc/dev/<module-name>/spec.md` 的模块 spec。

注意：
- 术语统一为 `module-name`（不是 spec-name）
- spec 定位是"模块当前能力快照 + 持续活文档"，而非"一次性功能规格"
- 模板里的"关联变更"表初始为空，后续由 eo-archive 维护

### 第三步：用户确认 → status: confirmed

用户确认 spec 无误后，将 frontmatter 的 `status` 从 `draft` 改为 `confirmed`。

### 第四步：触发 eo-spec-review

直接进入 **eo-spec-review 流程**（读其 SKILL.md 执行），对 `<module-name>/spec.md` 做系统性审查，产出 `<module-name>/spec-review.md`。

### 第五步：根据 review 结果迭代

- **无 P0/P1** → 通过，继续下一步
- **有 P0/P1** → 提示用户修订 `spec.md`，修订后删除 `spec-review.md` 重跑第四步
- 循环直到通过

### 第六步：建立 changes/ 骨架

1. 创建 `eo-doc/dev/<module-name>/changes/` 空目录
2. 创建 `eo-doc/dev/<module-name>/changes/INDEX.md`，写入表头：

```markdown
# <module-name> 变更时间线

| 编号 | 标题 | 类型 | 状态 | 日期 | 摘要 |
|------|------|------|------|------|------|
```

### 第七步：更新全局索引

更新 `eo-doc/dev/INDEX.md`，添加该模块条目。

### 第八步：提示后续流程

告知用户：
> 模块 `<module-name>` 初始化完成（spec 已就绪、code 未实现）。
>
> **首批实现 — 用 `bootstrap` 类型 change**：
> 1. 通读 `spec.md`，把"§3 核心行为"等能力章节按合理粒度拆成 1-N 个 bootstrap change（每个认领一部分章节，互不重叠）
> 2. 对每个 bootstrap：`/eo-change`（选 `change_type: bootstrap`，§3 写"实现范围"而不是 Delta）→ `/eo-implement` → `/eo-test` → `/eo-review` → `/eo-archive`
> 3. 全部 bootstrap 归档完毕 = spec 全量落地为代码
>
> **后续演化 — 用 `feature` / `enhance` / `refactor`**：
> 当代码已存在、需要新增/修改/重构能力时，按对应类型发 change，§3 写 Delta（ADDED/MODIFIED/REMOVED）。
>
> 后续不要再跑 `/eo-module-init` 或单独 `/eo-spec`。

---

## 关键约束

- **一次性**：一个模块只走一次 module-init
- **强制 spec-review**：模块基线必须过 review，不可跳过
- **不产出 change / 代码**：此 skill 只负责建立模块骨架
- **module-name 命名**：小写 kebab-case（如 `hero` / `inventory` / `transport-queue`）
- **与 eo-change 的分工**：
  - 模块不存在 → eo-module-init
  - 模块已存在 → eo-change（哪怕是"大改 spec"，也走 refactor 类型的 change）
