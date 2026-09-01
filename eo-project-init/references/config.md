# eo-skills 配置约定

所有 eo-* skill 共享的路径与配置约定。本文档是**唯一权威来源**——其它 skill 引用本文，不重复定义。

## 用户级数据根 `~/.eo/`

`~/.eo/` 是整个 eo 生态（eo-skills + eo-platform 等）在单用户下共享的**用户级数据根**，避免配置与缓存散落各处。当前约定内容如下：

| 路径 | 性质 | 谁维护 |
|------|------|--------|
| `~/.eo/projects.json` | eo 生态项目注册表（`eo-board --all` / `eo-sync watch --all` 跨项目枚举） | `eo-board --register` / `--unregister` |
| `~/.eo/platform.db` | eo-platform 本地索引缓存（SQLite） | eo-platform |
| `~/.eo/logs/` | eo-platform 日志（按需） | eo-platform |
| `~/.eo/handbook-templates/<preset>/` | handbook 模板私有库（同名 preset 整套覆盖内置库） | 用户手工维护 |

根路径可通过环境变量 `EO_HOME` 覆盖（例如跑测试或多账号隔离时指向临时目录）。未设置时一律使用 `~/.eo/`。涉及该路径的内联命令一律写 `"${EO_HOME:-$HOME/.eo}"`。

## 两个配置文件

| 文件 | 作用域 | 谁维护 | 何时读 |
|------|--------|--------|--------|
| `<repo>/.eo-project.json` | 项目级·团队共享 | `eo-project-init` 生成，后续 skill 只读 | **所有 eo-* skill 启动时必读** |
| `<repo>/.eo-project.local.json` | 项目级·个人/机器覆盖（可选，**不提交**） | 协作者手工 / `eo-project-init` 协作者接入分支生成 | 与 `.eo-project.json` 同时读，顶层字段覆盖合并（local 优先） |

**合并结果**（`.eo-project.json` + 可选 local 覆盖）是**自包含**的——含所有需要的绝对路径，其它 skill 不需要再去读用户级文件。

## `<repo>/.eo-project.json` schema（项目级，必需）

```json
{
  "project_name": "my-project",
  "mode": "local",
  "project_root": "/Users/xxx/my-project/.eo-project",
  "doc_root": "eo-doc",
  "kanban_path": null,
  "sync": {
    "obsidian": { "enabled": true, "stub_dir": "board" },
    "github":   { "enabled": false }
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `project_name` | string | ✅ | 项目显示名 |
| `mode` | `"local"` | ✅ | 运行模式 |
| `project_root` | string（绝对路径） | ✅ | **项目管理侧根**，= `<repo>/.eo-project` 的绝对路径。写成相对路径时（存量形态）读取层按 repo root 解析并解软链后放行 + 告警，见下「读取层归一化」 |
| `doc_root` | string（相对 repo root） | ✅ | **代码侧根**，默认 `"eo-doc"` |
| `kanban_path` | null | ❌ | 一律 `null`；存量值被所有 skill 忽略。项目级总览 = Bases 聚合各项目 roadmap.md frontmatter |
| `board.enabled` | bool | ❌（默认 `false`） | **存量字段**（新配置不再生成，仅兼容映射消费；首选写 `sync.obsidian.enabled`）。change 看板投影开关。开启后 `eo-sync`（obsidian 适配器）把 stub 卡片投影到 `<project_root>/board/`，见 `eo-shared/board-github.md` 与下文 `sync` 段 |
| `board.stub_dir` | string | ❌（默认 `"board"`） | **存量字段**（首选 `sync.obsidian.stub_dir`）。stub 目录名（相对 `project_root`） |
| `github.issue` | bool | ❌（默认 `false`） | **存量字段**（首选 `sync.github.issue`）。change ↔ GitHub issue 联动开关 |
| `github.pr` | `"auto"` \| `"always"` \| `"never"` | ❌（默认 `"never"`） | **存量字段**（首选 `sync.github.pr`）。archive 时的 PR 策略：`auto` = 在非默认分支且有 remote 时自动建 PR |
| `sync` | object \| null | ❌ | **首选**（init 新配置写本段，存量 `board`/`github` 仅存量兼容）。`eo-sync` 适配器启用制。**键存在性决定是否回落**：缺省（键不在）→ 由 `board`/`github` 兼容映射派生；键存在（含空 `{}` 或显式 `null`）→ 完全以其为准、绝不回落，其中 `{}`/`null` = 显式零目标；object 以外的类型（数字/字符串等）→ 配置错误。schema 见下 |
| `state` | object | ❌ | state 现状文档层启用制。键缺失 = 未表态（init 走问答）；`{"enabled": true}` 启用，`{"enabled": false}` 显式关闭不再询问。schema 见下 |

缺省 `board` / `github` 字段 = 全部关闭（存量项目兼容映射照常生效；新配置不含这两段）。

### `sync` 段（eo-sync 适配器启用制）

`eo-sync` 的投影目标由 `sync` 段显式启用——**发现 ≠ 执行**：PATH 上的 `eo-sync-*` 可执行文件负责「有哪些」，`sync` 段负责「启用哪些 + 参数」（这也是第三方可执行文件的信任边界）。

```json
{
  "sync": {
    "obsidian": { "enabled": true, "stub_dir": "board" },
    "github":   { "enabled": true, "issue": true, "pr": "auto" },
    "notion":   { "enabled": false, "database_id": "..." }
  }
}
```

| 键 | 说明 |
|----|------|
| `sync.<name>.enabled` | bool，仅 `true` 的适配器会被 `eo-sync run` 执行 |
| `sync.<name>.<其它>` | 该适配器的自定义参数，`enabled` 之外的键原样透传给适配器 |

**兼容映射**：以**键是否存在**判定（非「值是否非空」）——合并配置**无** `sync` 键时由存量 `board` / `github` 段等价派生启用集（`board.enabled`→`obsidian`、`github.issue`/`pr`→`github`）；`sync` 键**存在**（含空 `{}` 或显式 `null`）则完全以其为准、不与 `board`/`github` 深合并，其中 `{}`/`null` 是用户显式选择的零目标（绝不回落存量段）；`sync` 值为 object 以外的类型 → 配置校验失败（不静默降级）。存量项目无需改配置即按等价映射生效。Init 新配置只写 `sync` 段，重跑 init（1.5 分支）对仅有旧段的项目提示并代写等价 `sync` 段（旧段保留不删）。协议契约见 [../../docs/sync-adapter-protocol.md](../../docs/sync-adapter-protocol.md)。
### `state` 段（state 现状文档层）

`eo-doc/state/` 现状篇（业务现状活文档，代码为唯一信源）是否启用，由 `state` 段显式表达：

```json
{ "state": { "enabled": true } }
```

- 键缺失 = 未表态——init（首建与 1.5 分支）按封闭选择协议问一次，结论落本段
- `enabled: true`：`/eo-doc-manager sync` 按 cursor 增量再生 `state/` 现状篇（`eo-doc/.sync-cursor` 记录游标）；archive 收口自动联动
- `enabled: false`：显式关闭，不再询问；存量 `state/` 目录冻结留存（不删除）
- `enabled` 非 bool 或 `state` 值为 object 以外类型 → 配置校验失败
- 团队共享字段（文档层偏好是团队口径），不进 `.eo-project.local.json` 的机器相关覆盖清单

**设计约束**：
- `project_root` **生成时**永远写绝对路径，skill 一律走 `project_root`。
- **读取层归一化**（存量兼容）：合并结果的 `project_root` 是相对路径时（存量常写成软链相对路径），读取层按 repo root 解析并解软链，得到已存在的目录即放行并在 stderr 告警一行；解析不到已存在目录则仍按配置校验失败处理（不猜、不静默放行）。下游拿到的 `project_root` 恒为绝对路径，消费方无需感知。重跑 `/eo-project-init` 会把它回写成绝对路径（落点按 local 优先规则）。
- `.eo-project.json` 本身**提交到仓库**（团队共享配置）；`.eo-project.local.json` **不提交**（`eo-project-init` 默认写入 `.gitignore`）。
- 必填校验以**合并结果**为准——单个文件不要求自包含。

## `<repo>/.eo-project.local.json`（项目级个人覆盖，可选）

**动机**：`.eo-project.json` 提交进仓库，但 `project_root`（绝对路径）、`mode`、`sync` 因人/机器而异——协作者 clone 后拿到的是别人机器上的路径。local 文件承载这些机器相关字段，共享文件只留团队口径。

**规则**：

- 与 `.eo-project.json` **同目录**；schema 相同，**所有字段可选**。
- **顶层浅合并**，local 优先：local 出现的顶层字段整段覆盖共享文件的同名字段（`sync` 及 存量 `board` / `github` 是对象也**整段覆盖**，不做深合并）。
- 团队仓库的 `.eo-project.json` 可只保留共享字段（`project_name` / `doc_root`），机器相关字段（`project_root` / `mode` / `sync`）由每人的 local 文件提供。
- **字段写回**（如 sync 段后开补齐，见 `eo-shared/board-github.md`）：该顶层字段已存在于 local 文件 → 写 local（写共享文件会被覆盖屏蔽）；否则写 `.eo-project.json`。

## Skill 启动时的配置解析流程

**除 `eo-project-init` 外的所有 eo-* skill 启动时：**

1. 从 cwd 向上查找 `.eo-project.json`（到文件系统根为止）
2. 找不到 → 报错并退出：
   ```
   ❌ 未找到 .eo-project.json
   请先运行 /eo-project-init 初始化项目。
   ```
3. 找到 → 解析其内容；**同目录存在 `.eo-project.local.json` 时先做顶层字段覆盖合并（local 优先）**，后续一律用合并结果中的路径（**不读用户级文件**）
4. 合并结果缺必填字段（`project_root` / `mode` 等）→ 报错并提示运行 `/eo-project-init`（协作者 clone 场景见其「协作者接入」分支）

**`eo-project-init` 的启动行为更特殊**：
1. 先看 cwd 向上是否已有 `.eo-project.json`（已初始化过 → 走「1.5 更新/修复分支」）。
2. 未初始化 → 进入首次创建流程（见 `eo-project-init/SKILL.md`）。

## 目录结构参考

### 代码侧（仓库内 `<doc_root>/`，默认 `eo-doc/`）

`eo-doc-manager init` 建最小骨架：

```
eo-doc/
├── changes/          # 必建，change 工件流
├── agent-handbook/   # 可选，Agent 操作手册（篇目含 INDEX.md）
└── templates/        # 必建（空），eo-* 扩展点
```

### 项目管理侧（`project_root/`）

`eo-project-init` 建最小骨架：

```
<project_root>/
├── roadmap.md     # 必建（frontmatter 含 status/phase/summary，Bases 项目总览按此聚合）
├── backlog/       # 按需，待办/灵感卡片（每条一文件，status: backlog 上看板；archive/ 存归档卡）
├── phases/        # 按需，roadmap 拆解后生成
├── decisions/     # 按需，首次记录决策时建
├── lessons/       # 按需，首次记录经验时建（**项目级**，替代全局 _lessons/）
├── brainstorm/    # 按需，eo-brainstorming 首次产出时建
├── board/         # 按需，change 看板 stub（sync.obsidian（或存量 board.enabled）启用时由 eo-sync 投影维护）
├── research/      # 按需，调研沉淀（带 INDEX + frontmatter；eo-recall / eo-change 事实自查消费）
└── docs/          # 按需，原始 PRD / 设计 / 规划
```

`.eo-project/`（即 `project_root`）**缺省随仓库提交**——管理侧是协作者最需要的项目记忆；用户明确不想提交时才追加进 `.gitignore`。
