# eo-skills 配置约定

所有 eo-* skill 共享的路径与模式约定。本文档是**唯一权威来源**——其它 skill 引用本文，不重复定义。

## 用户级数据根 `~/.eo/`

`~/.eo/` 是整个 eo 生态（eo-skills + eo-platform 等）在单用户下共享的**用户级数据根**，避免配置与缓存散落各处。当前约定内容如下：

| 路径 | 性质 | 谁维护 |
|------|------|--------|
| `~/.eo/config.json` | eo-skills 全局配置（旧 `~/.eo-skills.json` 的继任者） | 用户手工 / `eo-project-init` 首次运行时引导生成 |
| `~/.eo/platform.db` | eo-platform 本地索引缓存（SQLite） | eo-platform |
| `~/.eo/logs/` | eo-platform 日志（按需） | eo-platform |

根路径可通过环境变量 `EO_HOME` 覆盖（例如跑测试或多账号隔离时指向临时目录）。未设置时一律使用 `~/.eo/`。涉及该路径的内联命令一律写 `"${EO_HOME:-$HOME/.eo}"`。

**自动迁移**：若 `~/.eo-skills.json` 存在且 `~/.eo/config.json` 不存在，`eo-project-init` 启动时**静默执行一次**：

```bash
EO_HOME="${EO_HOME:-$HOME/.eo}"
mkdir -p "$EO_HOME"
mv ~/.eo-skills.json "$EO_HOME/config.json"
```

迁移后在终端打印一行提示，之后不再检查旧路径。已完成迁移的机器或新机器，只读 `$EO_HOME/config.json`。

## 三个配置文件

| 文件 | 作用域 | 谁维护 | 何时读 |
|------|--------|--------|--------|
| `~/.eo/config.json` | 用户级 | 用户手工 / `eo-project-init` 首次运行时引导生成 | **仅 `eo-project-init` 读**（作为新项目的默认值）。eo-platform 等平台级进程可选只读消费（不写）。 |
| `<repo>/.eo-project.json` | 项目级·团队共享 | `eo-project-init` 生成，后续 skill 只读 | **所有 eo-* skill 启动时必读** |
| `<repo>/.eo-project.local.json` | 项目级·个人/机器覆盖（可选，**不提交**） | 协作者手工 / `eo-project-init` 协作者接入分支生成 | 与 `.eo-project.json` 同时读，顶层字段覆盖合并（local 优先） |

**合并结果**（`.eo-project.json` + 可选 local 覆盖）是**自包含**的——含所有需要的绝对路径，其它 skill 不需要再去读用户级文件。

## `~/.eo/config.json` schema（用户级，可选）

```json
{
  "vault_root": "/Users/xxx/EveOS",
  "projects_subdir": "30-我的项目",
  "create_symlink": true,
  "default_mode": "vault"
}
```

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `vault_root` | string | — | vault 根路径（绝对）。不配 → 默认 `local` 模式 |
| `projects_subdir` | string | `"projects"` | vault 下的项目子目录（vault 模式才用到） |
| `create_symlink` | bool | `true` | vault 模式下是否在代码仓库建 `<repo>/<doc_root>/vault` 软链指向 `<project_root>` |
| `default_mode` | `"vault"` \| `"local"` | 由 `vault_root` 推断 | 新项目默认模式；配了 `vault_root` → `vault`，否则 `local` |

**整个文件可选**。完全不存在时等同于「纯本地模式，永不碰 vault」。

## `<repo>/.eo-project.json` schema（项目级，必需）

```json
{
  "project_name": "my-project",
  "mode": "vault",
  "project_root": "/Users/xxx/EveOS/30-我的项目/my-project",
  "doc_root": "eo-doc",
  "kanban_path": null,
  "board": { "enabled": false },
  "github": { "issue": false, "pr": "never" }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `project_name` | string | ✅ | 项目显示名 |
| `mode` | `"vault"` \| `"local"` | ✅ | 运行模式 |
| `project_root` | string（绝对路径） | ✅ | **项目管理侧根**。vault 模式=vault 项目目录；local 模式=`<repo>/.eo-project` |
| `doc_root` | string（相对 repo root） | ✅ | **代码侧根**，默认 `"eo-doc"` |
| `kanban_path` | null | ❌ | **已废弃**（旧手工看板体系退役）。新配置一律 `null`；存量值被所有 skill 忽略。项目级总览 = Bases 聚合各项目 roadmap.md frontmatter |
| `board.enabled` | bool | ❌（默认 `false`） | change 看板投影开关（vault 模式才有意义）。开启后 `eo-sync`（obsidian 适配器）把 stub 卡片投影到 `<project_root>/board/`，见 `eo-shared/board-github.md` 与上文 `sync` 段 |
| `board.stub_dir` | string | ❌（默认 `"board"`） | stub 目录名（相对 `project_root`） |
| `github.issue` | bool | ❌（默认 `false`） | change ↔ GitHub issue 联动开关 |
| `github.pr` | `"auto"` \| `"always"` \| `"never"` | ❌（默认 `"never"`） | archive 时的 PR 策略：`auto` = 在非默认分支且有 remote 时自动建 PR |
| `sync` | object \| null | ❌ | `eo-sync` 适配器启用制。**键存在性决定是否回落**：缺省（键不在）→ 由 `board`/`github` 兼容映射派生；键存在（含空 `{}` 或显式 `null`）→ 完全以其为准、绝不回落，其中 `{}`/`null` = 显式零目标；object 以外的类型（数字/字符串等）→ 配置错误。schema 见下 |

缺省 `board` / `github` 字段 = 全部关闭（向后兼容 v1 生成的配置）。

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

**兼容映射**：以**键是否存在**判定（非「值是否非空」）——合并配置**无** `sync` 键时由存量 `board` / `github` 段等价派生启用集（`board.enabled`→`obsidian`、`github.issue`/`pr`→`github`）；`sync` 键**存在**（含空 `{}` 或显式 `null`）则完全以其为准、不与 `board`/`github` 深合并，其中 `{}`/`null` 是用户显式选择的零目标（绝不回落存量段）；`sync` 值为 object 以外的类型 → 配置校验失败（不静默降级）。存量项目无需改配置即按等价映射生效。正式收编（init 停写旧段 + 存量迁移）时机见 change `sync-plugin-layer` 的 OQ-1。协议契约见 [../../docs/sync-adapter-protocol.md](../../docs/sync-adapter-protocol.md)。

**设计约束**：
- `project_root` 永远是绝对路径。vault 模式不依赖软链——软链只是给用户查看方便，skill 一律走 `project_root`。
- `.eo-project.json` 本身**提交到仓库**（团队共享配置）；`.eo-project.local.json` **不提交**（`eo-project-init` 默认写入 `.gitignore`）。
- 必填校验以**合并结果**为准——单个文件不要求自包含。

## `<repo>/.eo-project.local.json`（项目级个人覆盖，可选）

**动机**：`.eo-project.json` 提交进仓库，但 `project_root`（绝对路径）、`mode`、`board` 因人/机器而异——协作者 clone 后拿到的是别人的 vault 路径。local 文件承载这些机器相关字段，共享文件只留团队口径。

**规则**：

- 与 `.eo-project.json` **同目录**；schema 相同，**所有字段可选**。
- **顶层浅合并**，local 优先：local 出现的顶层字段整段覆盖共享文件的同名字段（`board` / `github` 是对象也**整段覆盖**，不做深合并）。
- 团队仓库的 `.eo-project.json` 可只保留共享字段（`project_name` / `doc_root` / `github`），机器相关字段（`project_root` / `mode` / `board`）由每人的 local 文件提供。
- **字段写回**（如 board/github 后开补齐，见 `eo-shared/board-github.md`）：该顶层字段已存在于 local 文件 → 写 local（写共享文件会被覆盖屏蔽）；否则写 `.eo-project.json`。

## 运行模式对比

| 方面 | `vault` 模式 | `local` 模式 |
|------|-----------|-----------|
| 触发条件 | `~/.eo/config.json` 里有 `vault_root`，且用户选 vault | 反之 |
| `project_root` 落在哪 | `<vault_root>/<projects_subdir>/<project_name>/` | `<repo>/.eo-project/` |
| 是否建软链 | 默认建 `<repo>/<doc_root>/vault` → `<project_root>`（整个 vault 项目目录单点挂进来；`create_symlink` 控制） | 不建 |
| `.eo-project/`（local 模式目录）入 git | — | **默认进 `.gitignore`** |

## Skill 启动时的配置解析流程

**除 `eo-project-init` 外的所有 eo-* skill 启动时：**

1. 从 cwd 向上查找 `.eo-project.json`（到文件系统根为止）
2. 找不到 → 报错并退出：
   ```
   ❌ 未找到 .eo-project.json
   请先运行 /eo-project-init 初始化项目。
   ```
3. 找到 → 解析其内容；**同目录存在 `.eo-project.local.json` 时先做顶层字段覆盖合并（local 优先）**，后续一律用合并结果中的路径（**不读 `~/.eo/config.json`**）
4. 合并结果缺必填字段（`project_root` / `mode` 等）→ 报错并提示运行 `/eo-project-init`（协作者 clone 场景见其「协作者接入」分支）

**`eo-project-init` 的启动行为更特殊**：
1. **迁移检查**：若 `~/.eo-skills.json` 存在且用户级配置不存在 → 自动迁移到 `"${EO_HOME:-$HOME/.eo}"/config.json`，打印一行提示。
2. 先看 cwd 是否已有 `.eo-project.json`（已初始化过）。
3. 未初始化时，读 `~/.eo/config.json` 拿默认值，提示用户确认/覆盖。
4. 用户级文件不存在 → 进入首次引导流程（见 `eo-project-init/SKILL.md`）。

## 目录结构参考

### 代码侧（仓库内 `<doc_root>/`，默认 `eo-doc/`）

`eo-doc-manager init` 建最小骨架：

```
eo-doc/
├── agent-handbook/   # 必建，代码架构（AI）
├── changes/          # 必建，change 工件流
├── templates/        # 必建（空），eo-* 扩展点
└── state/            # 按需，系统当前状态描述（sync 时首建）
```

**已移除（不再规划）**：`design/`、`doc/`、`research/`、`knowledgebase/`——`doc/` 语义迁到 `state/`；design 迁项目管理侧 `docs/`；调研沉淀归项目管理侧 `research/`；通用领域术语归 `state/glossary.md`。若将来知识规模大到检索吃力，升级路径是索引层而非目录（backlog 有远期条目）。

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
├── board/         # 按需，change 看板 stub（board.enabled/sync.obsidian 时由 eo-sync 投影维护）
├── research/      # 按需，调研沉淀（带 INDEX + frontmatter；eo-recall / eo-change 事实自查消费）
└── docs/          # 按需，原始 PRD / 设计 / 规划
```

vault 模式下（`create_symlink: true` 时），在代码侧建整目录软链：
- `<repo>/<doc_root>/vault` → `<project_root>`

**方向说明**：Obsidian 侧是**源**，整个项目目录作为一个软链点挂到代码侧 `<doc_root>/vault/` 下。**单点整挂**，不是按子目录一个个软链——后者在 vault 侧新建 `docs/` / `phases/` 等子目录时还要回代码侧补软链，不自动。
