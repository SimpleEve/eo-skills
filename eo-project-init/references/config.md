# eo-skills 配置约定

所有 eo-* skill 共享的路径与模式约定。本文档是**唯一权威来源**——其它 skill 引用本文，不重复定义。

## 用户级数据根 `~/.eo/`

`~/.eo/` 是整个 eo 生态（eo-skills + eo-platform 等）在单用户下共享的**用户级数据根**，避免配置与缓存散落各处。当前约定内容如下：

| 路径 | 性质 | 谁维护 |
|------|------|--------|
| `~/.eo/config.json` | eo-skills 全局配置（旧 `~/.eo-skills.json` 的继任者） | 用户手工 / `eo-project-init` 首次运行时引导生成 |
| `~/.eo/platform.db` | eo-platform 本地索引缓存（SQLite） | eo-platform |
| `~/.eo/logs/` | eo-platform 日志（按需） | eo-platform |

根路径可通过环境变量 `EO_HOME` 覆盖（例如跑测试或多账号隔离时指向临时目录）。未设置时一律使用 `~/.eo/`。

**自动迁移**：若 `~/.eo-skills.json` 存在且 `~/.eo/config.json` 不存在，`eo-project-init` 启动时**静默执行一次**：

```bash
mkdir -p ~/.eo
mv ~/.eo-skills.json ~/.eo/config.json
```

迁移后在终端打印一行提示，之后不再检查旧路径。已完成迁移的机器或新机器，只读 `~/.eo/config.json`。

## 两个配置文件

| 文件 | 作用域 | 谁维护 | 何时读 |
|------|--------|--------|--------|
| `~/.eo/config.json` | 用户级 | 用户手工 / `eo-project-init` 首次运行时引导生成 | **仅 `eo-project-init` 读**（作为新项目的默认值）。eo-platform 等平台级进程可选只读消费（不写）。 |
| `<repo>/.eo-project.json` | 项目级 | `eo-project-init` 生成，后续 skill 只读 | **所有 eo-* skill 启动时必读** |

`.eo-project.json` 是**自包含**的——写入所有需要的绝对路径，其它 skill 不需要再去读用户级文件。

## `~/.eo/config.json` schema（用户级，可选）

```json
{
  "vault_root": "/Users/xxx/EveOS",
  "projects_subdir": "30-我的项目",
  "kanban_path": "00-Wiki/项目看板.md",
  "create_symlink": true,
  "default_mode": "vault"
}
```

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `vault_root` | string | — | vault 根路径（绝对）。不配 → 默认 `local` 模式 |
| `projects_subdir` | string | `"projects"` | vault 下的项目子目录（vault 模式才用到） |
| `kanban_path` | string \| null | `null` | 项目看板路径（**相对 `vault_root`**）。`null` → 不维护看板 |
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
  "kanban_path": "/Users/xxx/EveOS/00-Wiki/项目看板.md"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `project_name` | string | ✅ | 项目显示名 |
| `mode` | `"vault"` \| `"local"` | ✅ | 运行模式 |
| `project_root` | string（绝对路径） | ✅ | **项目管理侧根**。vault 模式=vault 项目目录；local 模式=`<repo>/.eo-project` |
| `doc_root` | string（相对 repo root） | ✅ | **代码侧根**，默认 `"eo-doc"` |
| `kanban_path` | string（绝对路径） \| null | ❌ | 看板绝对路径；缺省/`null` = 不维护看板 |

**设计约束**：
- `project_root` 永远是绝对路径。vault 模式不依赖软链——软链只是给用户查看方便，skill 一律走 `project_root`。
- `.eo-project.json` 本身**提交到仓库**（团队共享配置）。

## 运行模式对比

| 方面 | `vault` 模式 | `local` 模式 |
|------|-----------|-----------|
| 触发条件 | `~/.eo/config.json` 里有 `vault_root`，且用户选 vault | 反之 |
| `project_root` 落在哪 | `<vault_root>/<projects_subdir>/<project_name>/` | `<repo>/.eo-project/` |
| 是否建软链 | 默认建 `<repo>/<doc_root>/vault` → `<project_root>`（整个 vault 项目目录单点挂进来；`create_symlink` 控制） | 不建 |
| 是否维护看板 | 看 `kanban_path` 是否配置 | 始终不维护 |
| `.eo-project/`（local 模式目录）入 git | — | **默认进 `.gitignore`** |

## Skill 启动时的配置解析流程

**除 `eo-project-init` 外的所有 eo-* skill 启动时：**

1. 从 cwd 向上查找 `.eo-project.json`（到文件系统根为止）
2. 找不到 → 报错并退出：
   ```
   ❌ 未找到 .eo-project.json
   请先运行 /eo-project-init 初始化项目。
   ```
3. 找到 → 解析其内容，后续一律用其中的路径（**不读 `~/.eo/config.json`**）

**`eo-project-init` 的启动行为更特殊**：
1. **迁移检查**：若 `~/.eo-skills.json` 存在且 `~/.eo/config.json` 不存在 → 自动迁移（`mkdir -p ~/.eo && mv ~/.eo-skills.json ~/.eo/config.json`），打印一行提示。
2. 先看 cwd 是否已有 `.eo-project.json`（已初始化过）。
3. 未初始化时，读 `~/.eo/config.json` 拿默认值，提示用户确认/覆盖。
4. 用户级文件不存在 → 进入首次引导流程（见 `eo-project-init/SKILL.md`）。

## 目录结构参考

### 代码侧（仓库内 `<doc_root>/`，默认 `eo-doc/`）

`eo-doc-manager init` 建最小骨架：

```
eo-doc/
├── agent-handbook/   # 必建，代码架构（AI）
├── dev/              # 必建，spec/change/review 流
├── templates/        # 必建（空），eo-* 扩展点
└── state/            # 按需，系统当前状态描述（sync 时首建）
```

**已移除**：`design/`、`doc/`、`research/`、`knowledgebase/`（`doc/` 语义迁到 `state/`；其余三者搬到项目管理侧或暂时移除）。

### 项目管理侧（`project_root/`）

`eo-project-init` 建最小骨架：

```
<project_root>/
├── roadmap.md     # 必建
├── log.md         # 必建
├── backlog.md     # 必建（待办池 + 未接入的未来规划）
├── phases/        # 按需，roadmap 拆解后生成
├── decisions/     # 按需，首次记录决策时建
├── lessons/       # 按需，首次记录经验时建（**项目级**，替代全局 _lessons/）
├── brainstorm/    # 按需，eo-brainstorming 首次产出时建
└── docs/          # 按需，原始 PRD / 设计 / 规划
```

vault 模式下（`create_symlink: true` 时），在代码侧建整目录软链：
- `<repo>/<doc_root>/vault` → `<project_root>`

**方向说明**：Obsidian 侧是**源**，整个项目目录作为一个软链点挂到代码侧 `<doc_root>/vault/` 下。**单点整挂**，不是按子目录一个个软链——后者在 vault 侧新建 `docs/` / `phases/` 等子目录时还要回代码侧补软链，不自动。
