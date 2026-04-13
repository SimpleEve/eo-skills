# eo-skills

个人维护的 Claude Code / Codex skill 集合。本仓库按**用途分类**管理多个 eo- 前缀的 skill，每类独立演化、互不耦合。

## 分类总览

| 分类 | 用途 | 代表 skill |
|------|------|-----------|
| **开发工作流**（Development Workflow） | 驱动"模块活文档 + change Delta"的端到端开发流程 | `eo-module-init` / `eo-change` / `eo-change-review` / `eo-implement` / `eo-test` / `eo-review` / `eo-archive` / `eo-workflow` |
| **构思与选品**（Ideation） | 帮助用户从模糊想法收敛到可落地的方向 | `eo-brainstorming` / `eo-miniapp-ideation` |
| **项目管理**（Project Ops） | 项目看板、阶段、经验教训维护 | `eo-project-init` / `eo-project-update` / `eo-project-lesson` |
| **文档体系**（Docs） | 项目 `eo-doc/` 的统一维护入口 | `eo-doc-manager` |

> 本 README 重点讲 **开发工作流**。其它分类各自在自己的 skill 目录里说明，本页仅索引。

---

## 🛠 开发工作流（Development Workflow）

一套基于 **OpenSpec 风格 Delta 机制**的开发流水线：**模块（module）是一等公民**，每个模块都有一份活文档 `spec.md`；每次业务变更以 `change.md` 的形式独立归档，归档时由 `eo-archive` 把 change 的 Delta 机械合并回 spec。

### 设计理念

1. **模块是一等公民** — 所有开发产物都归属到 `eo-doc/dev/<module-name>/` 下
2. **spec 是活文档** — 不重写，只增量演化（ADDED / MODIFIED / REMOVED）
3. **change = proposal + plan** — 一份文档同时承载需求澄清、技术方案、TODO 拆解
4. **fix ≠ change** — bug 修复是 `eo-implement` 的内嵌职责，不开新 change、不产生 Delta
5. **change 无独立 review** — 作者自澄清即可发起；实施后的 `/eo-review` 是唯一正式审查

### 产物目录结构

```
eo-doc/dev/
└── <module-name>/              ← 一个业务模块 = 一个目录
    ├── spec.md                 ← 活文档：模块当前能力快照（工程视角）
    ├── spec-review.md          ← 仅模块初始化时一次性审查（可选）
    └── changes/
        ├── INDEX.md            ← 模块内 change 时间线
        └── <NNN-change-id>/    ← 数字前缀 + kebab-case（无 fix- 前缀）
            ├── change.md       ← Spec Delta + 技术方案 + TODO + AC
            ├── implement.md    ← 偏差记录（可选）
            ├── test.md         ← 测试报告
            └── review.md       ← 代码审查结论
```

> 玩法层业务文档仍放在 `eo-doc/doc/<module>.md`，`spec.md` 以薄引用方式指向它；`spec.md` 只承载工程视角（多层协作边界、跨模块依赖、change 时间线）。

### Skill 职责速查

| Skill | 触发时机 | 产出 | 可选 |
|-------|---------|------|------|
| `eo-module-init` | 新模块首次落地 | `spec.md` + `spec-review.md`（一次性） | — |
| `eo-spec` | 模块内部：撰写 spec | 被 `eo-module-init` 调用 | — |
| `eo-spec-review` | 模块初始化时**必须**；archive 后 Delta 大改时**可选** | `spec-review.md` | 复检可选 |
| `eo-change` | 已有模块的业务变更 | `changes/<NNN-xxx>/change.md` | — |
| `eo-change-review` | change draft 完成后，implement 前方案审查 | `change-review.md` | **✅ 可选** |
| `eo-implement` | 按 change.md TODO 实施（含 bug 修复循环） | 代码 + 可选 `implement.md` | — |
| `eo-test` | 运行测试 / 场景验证 | `test.md` | — |
| `eo-review` | 实施后的**代码**审查 | `review.md` | — |
| `eo-archive` | 代码审查通过后归档 | Delta 合并回 `spec.md` + 更新 INDEX | — |
| `eo-workflow` | 多 pane tmux 编排 | 自动派发 / 状态流转 | — |

### 三种 Review 的边界

| Skill | 审查对象 | 问的核心问题 | 强制 / 可选 |
|-------|---------|-------------|------------|
| `/eo-spec-review` | 模块 `spec.md`（活文档基线） | **需求**对不对？业务自洽吗？ | module-init 时强制；后续可选 |
| `/eo-change-review` | 某个 change 的 `change.md` | **方案**对不对？Delta 和实施方案一致吗？ | 全程可选（高风险建议走） |
| `/eo-review` | change 实施后的代码 | **代码**对不对？实现 vs AC？ | 每个 change 强制 |

关注点、上下文、回退动作完全不同，**不要混用**。

### 典型流程

```
新模块：    /eo-module-init       →  spec.md（含 spec-review 一次性）
            │                         status: confirmed
            ▼
业务变更：  /eo-change            →  changes/NNN-xxx/change.md（status: draft）
            │
            ▼  （可选）
方案审查：  /eo-change-review     →  change-review.md
            │                         P0/P1 → 回 eo-change 修
            ▼
approve：  （用户改 status: approved）
            │
            ▼
实施：      /eo-implement         →  代码 + 勾选 TODO
            │                         （bug 修复循环在此完成，不开新 change）
            ▼
测试：      /eo-test              →  test.md
            │
            ▼  （失败 → 回 implement）
代码审查：  /eo-review            →  review.md
            │                         P0/P1 → 回 implement 修
            ▼
归档：      /eo-archive           →  Delta 合并回 spec.md
            │                         status: archived
            ▼  （可选）
spec 复检：/eo-spec-review        →  若 Delta 触及章节多 / MODIFIED-REMOVED 多
                                     archive 会主动提示
```

**实施期 bug：** 留在 `/eo-implement` 内循环修，不走归档、不开新 change。

**归档后发现缺陷：**
- "实现不符合 spec" → 继续走 `/eo-implement` 补丁式实施
- "spec 本身要改" → 开新的 `enhance` 类型 change

### 关键约束

| 约束 | 说明 |
|------|------|
| `change-id` 命名 | `NNN-kebab-name`（3 位数字前缀，按模块内递增）；**拒绝 `fix-` 前缀** |
| `change_type` 枚举 | `feature` / `enhance` / `refactor`（**无 `fix`**） |
| 每个 change 必须产出 Delta | §3 至少一条 ADDED / MODIFIED / REMOVED |
| 单次聚焦 | 一个 change 只做一件事；混入多个改动请拆分 |
| 状态流转 | `draft → approved → implementing → done → archived` |
| spec 只由 archive 修改 | change 期间不直接改 `spec.md` |

### `/eo-workflow` 多 Agent 编排

面向 tmux 多窗格自动化：

```
/eo-workflow <phase> <module-name> [change-id] [loop-interval] [--with-review]
```

| Phase | 所需 pane | 行为 |
|-------|-----------|------|
| `module-init` | spec, review | 用户编写 spec → 自动派发 spec-review → P0/P1 则暂停待修 |
| `change` | change（默认）或 change + review（`--with-review`） | 用户与 `/eo-change` 交互澄清；启用 `--with-review` 时 draft 完成后自动派发 `/eo-change-review` |
| `implement` | implement, test, review | 全自动 implement→test→review 循环，失败回 implement 修复 |
| `archive` | （无） | 主 pane 直接执行 `/eo-archive` |
| `full` | 全部 | 上述阶段按顺序串联；`--with-review` 同样作用于 change 子阶段 |

`--with-review` 开关：在 `change` / `full` phase 插入 change-review 子阶段，让 change draft 完成后先过一轮方案审查再进 implement。默认关闭。

详情见 `eo-workflow/SKILL.md`。

---

## 📚 其它分类（索引）

以下 skill 各自独立演化，不属于开发流水线：

- **`eo-brainstorming`** — 发散 / 对抗 / 拆解 / 方向决策
- **`eo-miniapp-ideation`** — 微信小程序需求挖掘与 MVP 构思
- **`eo-project-init` / `eo-project-update` / `eo-project-lesson`** — 项目看板与阶段管理（基于 `.eo-project.json` 关联 vault）
- **`eo-doc-manager`** — `eo-doc/` 文档体系的统一维护入口

---

## 安装与使用

所有 skill 遵循 Claude Code skill 规范：

```
<skill-name>/
└── SKILL.md    ← frontmatter 声明 name / description，正文为执行说明
```

全局安装位置：`~/.claude/skills/<skill-name>/`（也可通过软链到本仓库管理）。

在 Claude Code 中通过 `/<skill-name>` 触发，例如：

```
/eo-change           # 发起一次模块变更
/eo-implement <change-path>
/eo-workflow implement my-module 001-add-queue
```

## License

See [LICENSE](LICENSE).
