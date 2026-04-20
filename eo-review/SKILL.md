---
name: eo-review
description: |
  对已实施的代码做审查，产出 P0/P1/P2 分级报告（前提：代码已实现）。触发：review / 代码审查 / /eo-review。
  NOT FOR: spec 审查（/eo-spec-review）、change 方案审查（/eo-change-review，代码还没写时用）。
---

# eo-review — 代码审查

根据模块 spec 和 change 文档对**已实施的代码**进行审查，产出结构化的审查报告。

> **定位**：`eo-review` 只审代码。审查范围前移（审 spec / 审 change 方案）请用 `/eo-spec-review` / `/eo-change-review`。三种 review 关注点、上下文、产出物都不同，不要混用。
>
> | Skill | 审查对象 | 产出 |
> |-------|---------|------|
> | `/eo-spec-review` | 模块 spec.md | `spec-review.md` |
> | `/eo-change-review` | change.md（implement 前） | `change-review.md` |
> | **`/eo-review`**（本技能） | change 实施后的代码 | `review.md` |

## 核心原则

1. **对照文档审查**：严格依据模块 spec 和 change 文档检查功能完整性与正确性
2. **最佳实践审查**：检查代码质量、命名规范、架构合理性
3. **结构化产出**：按 P0/P1/P2 分级，明确区分问题类型
4. **固定产出**：输出到 `eo-doc/dev/<module-name>/changes/<change-id>/review.md`

## 模板发现

启动时读 `eo-doc/templates/project-profile.md` 和 `plan-layers.md`（存在则启用维度 6「跨层一致性」，否则跳过）。

## 前置条件

- **必须能找到 `.eo-project.json`**。找不到 → 报错退出，提示运行 `/eo-project-init`。`eo-doc/` 路径通过 `doc_root` 字段解析
- 模块活文档 `eo-doc/dev/<module-name>/spec.md` 和 change 文档 `eo-doc/dev/<module-name>/changes/<change-id>/change.md` 必须已存在
- **相关代码已实现**（即 `/eo-implement` 已经跑过至少一轮，change.md 的 TODO 至少部分被勾选）
- change.md `status` 应为 `implementing` 或 `done`（不应是 `draft` / `approved`）

### 前置拦截（硬性）

若启动时发现以下任一信号，**立即停止并纠偏**，不要开始审查：

| 信号 | 含义 | 正确路径 |
|------|------|---------|
| change.md `status: draft` | change 还没 approve，更没 implement | 走 `/eo-change-review` |
| change.md `status: approved` 但所有 TODO 未勾选 | 代码还没开工 | 走 `/eo-implement` 先实施 |
| 用户描述是"审查 change 方案" / "审方案" / "implement 之前再看看" | 用户想要的是方案审查 | 走 `/eo-change-review`（**不是本 skill**） |
| 用户描述是"change 重写后再看看有没有新问题" | 代码未变，只是 change.md 改了 | 走 `/eo-change-review` |

纠偏反馈模板：
> ⚠️ `/eo-review` 是**实施后的代码审查**，需要代码已经写出来。
> 你当前的情况是 `<信号描述>`——这一步应该走 `/eo-change-review`（方案审查）。
> 两者区别：
> - `/eo-change-review` 审 `change.md` 本身（Delta / TODO / AC 是否合规） — **implement 之前**
> - `/eo-review`（本 skill）审**代码** — implement / test 之后

## 工作流程

### 第一步：阅读上下文

1. 阅读 `eo-doc/dev/<module-name>/spec.md`（模块活文档基线）
2. 阅读 `eo-doc/dev/<module-name>/changes/<change-id>/change.md`（本次变更的 §3、实施方案、TODO、AC）
   - 从 frontmatter 读取 `change_type`：
     - `bootstrap` → §3 是认领的 spec 章节，审查时对照 spec 这些章节定义的能力检查代码实现
     - `feature` / `enhance` / `refactor` → §3 是 Delta，审查时对照 Delta 声明检查代码改动
3. 阅读项目级背景文档（如果存在）

### 第二步：模板发现与维度确定

1. **执行模板发现**（见上方），确定是否启用跨层审查维度
2. 检查 change 的 TODO 结构：
   - 若 change 采用层级 Part 结构且模板存在 → 在标准 5 个维度之外，增加**维度 6：跨层一致性**
   - 若 change 为默认 S/C/G 结构或无模板 → 保持标准 5 个维度

### 第三步：代码审查

按以下维度逐一审查：

#### 维度 1：功能完整性
- change 中每个 TODO 的验收标准是否已满足
- Spec 中每条验收标准（AC）是否已覆盖
- 是否有遗漏的边界场景

#### 维度 2：逻辑正确性
- 核心业务逻辑是否正确
- 异常处理是否完整
- 边界条件是否考虑
- 是否存在竞态条件、死锁、资源泄漏或生命周期问题

#### 维度 3：架构合规性
- 是否遵循项目既有的分层、模块边界和依赖方向
- 核心逻辑是否与 UI、CLI、Editor 工具、平台层实现保持合理隔离
- 模块职责是否单一，是否存在不合理的耦合

#### 维度 4：代码规范
- 命名是否清晰、一致
- 类型使用是否严格（有无不必要的 `any`、弱类型绕过等）
- 是否有重复代码可提取
- 公共 API 是否有必要的文档注释

#### 维度 5：安全与性能
- 是否存在常见安全漏洞（注入、越权、敏感信息暴露）
- 是否存在明显的性能瓶颈

#### 维度 6：跨层一致性（仅多层 Part 模式）

> 条件维度：仅当 `eo-doc/templates/plan-layers.md` 存在且 change 采用层级 Part 结构时启用。
> 审查依据：以 plan-layers.md 模板定义的层边界和 project-profile.md 的层间约束为标准。

- 各层之间的接口定义是否匹配（如 Proto 消息字段与 Server/Client 使用是否一致）
- 跨层数据流是否完整（请求→处理→响应→通知 链路无断裂）
- 各层状态同步是否可靠（如登录/重连时各层数据能否正确恢复）
- 是否存在层间假设不一致（一层假设另一层有某行为，但另一层未实现）
- 各层代码是否在模板定义的目录范围内（未越界修改其他层的代码）

### 第四步：撰写报告

按照下方固定模板撰写，写入 `eo-doc/dev/<module-name>/changes/<change-id>/review.md`。

## 固定模板

见 [references/review-template.md](references/review-template.md)。

## 关键约束

- **客观公正**：基于文档和最佳实践审查，不做主观偏好评判
- **问题定位精确**：必须给出具体的文件路径和行号
- **不直接改代码**：Review 只产出报告，修复工作由 `/eo-implement` 执行
- **分级清晰**：P0 仅限阻塞性问题，不要把小问题升级为 P0
