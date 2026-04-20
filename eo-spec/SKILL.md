---
name: eo-spec
description: |
  为新模块撰写活文档 spec.md 作为后续 change 的基线。通常由 /eo-module-init 触发。触发：写 spec / 需求分析 / 模块规格 / /eo-spec。
  NOT FOR: 修改已有模块（走 /eo-change，通过 Delta 演化 spec）。
---

# eo-spec — 模块需求规格（活文档）

将模块的模糊需求意图转化为清晰、无歧义的 **spec 活文档**，存放于 `eo-doc/dev/<module-name>/spec.md`。

## 前置

**必须能找到 `.eo-project.json`**。找不到 → 报错退出，提示运行 `/eo-project-init`。`eo-doc/` 路径通过 `doc_root` 字段解析。

## 定位（重要）

- **只用于新模块首次建立**：spec 是模块的"当前能力快照 + 持续演化基线"
- **不用于已有模块的修改**：已有模块的变更走 `/eo-change`，通过 Delta 增量演化 spec
- 通常由 `/eo-module-init` 作为其一个步骤调用；独立调用时也只处理新模块

## 核心原则

1. **不猜测**：遇到任何模糊点必须向用户提问澄清，绝不自行假设
2. **不模糊**：每个需求边界必须确定，In Scope / Out of Scope 必须明确列出
3. **不写代码**：绝不写任何代码，包括伪代码。只用自然语言描述需求行为
4. **活文档属性**：spec 不是一次性产物，会随后续 change 的 Delta 合并持续演化
5. **固定产出**：输出到 `eo-doc/dev/<module-name>/spec.md`

## 模板发现

启动时读 `eo-doc/templates/project-profile.md` 和 `spec-layers.md`（存在则启用多层章节，否则使用纯单层模板）。

## 工作流程

### 第一步：理解与澄清

1. 阅读用户给出的需求描述
2. 阅读项目级背景文档（PRD、roadmap；如存在）
3. **执行模板发现**
4. **扫描 `eo-doc/dev/` 下已有的模块**（读取各 spec.md 的 frontmatter），避免重复或冲突
5. 列出所有不确定的点，逐一向用户澄清
6. 反复澄清直到无任何歧义

### 第二步：撰写 Spec

1. 确定 `module-name`（小写英文 kebab-case，如 `inventory` / `transport-queue`）
2. 创建目录 `eo-doc/dev/<module-name>/`（如不存在）
3. 按下方固定模板写入 `eo-doc/dev/<module-name>/spec.md`

### 第三步：用户确认

1. 将产出交给用户确认，根据反馈修订到满意
2. 用户确认后，将 frontmatter 的 `status` 从 `draft` 更新为 `confirmed`

### 第四步：更新索引

更新 `eo-doc/dev/INDEX.md`，添加模块条目。

## 固定模板

见 [references/spec-template.md](references/spec-template.md)。

## 流程图 / 架构图（活文档）

- **§1.4 模块架构图**：必画。即使模块很简单，也画一张单节点图占位，后续 change 会演化它
- **§3.5 核心流程图 / 状态图**：涉及用户操作流程、状态流转、多角色交互时**必画**；纯计算/查询型模块写"无"
- 图类型选择、命名、样式规范统一遵循 [eo-doc-manager/references/mermaid.md](../eo-doc-manager/references/mermaid.md)
- spec 阶段的图描述**当前稳定态**，不带 `:::new/:::changed` 标注（那是 change 的事）

## 关键约束

- **绝不写代码**：包括伪代码、代码片段、接口定义。这些属于 eo-change 阶段的职责
- **绝不猜测**：宁可多问一轮，也不要用"可能"、"大概"、"应该"这类词
- **一个 module 一个 spec**：不要在一个 spec 里塞多个不相关的模块
- **module-name 命名规则**：小写英文 kebab-case（如 `inventory` / `transport-queue`）
- **状态流转**：用户确认后必须更新 `status: draft` → `status: confirmed`
- **与 eo-change 的分工**：spec 只建一次基线；后续所有修改走 change 的 Delta
