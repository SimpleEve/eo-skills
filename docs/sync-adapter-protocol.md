# eo-sync 适配器协议 v1

`eo-sync` 是投影同步的插件化核；每个投影目标是一个独立可执行文件，核通过 **stdin/stdout JSON + 退出码** 的进程协议驱动它。内置适配器（Obsidian stub、GitHub issue/PR）与第三方适配器**同协议、同发现路径、无后门**——本文档即第三方接入的唯一契约，仅凭它就能独立写出一个适配器（`tests/fixtures/eo-sync-fixture` 是最小参考实现）。

## 发现与启用

- **发现**（有哪些）：核扫描 `PATH`，凡命名为 `eo-sync-<name>` 的可执行文件即一个适配器，`<name>` 为其名字。同名取 `PATH` 靠前者。
- **启用**（跑哪些）：只有合并配置（`.eo-project.json` + 可选 `.eo-project.local.json`）`sync` 段里 `enabled: true` 的适配器才会被执行。发现 ≠ 执行——这是第三方可执行文件的信任边界。`sync` 段以**键是否存在**判定：缺省（键不在）→ 回落 `board`/`github` 兼容映射；键存在（含空 `{}` 或显式 `null`）→ 段生效、`{}`/`null` 即零启用（绝不回落）；`sync` 为 object 以外类型 → 配置错误。
- **配置形态**：`"sync": { "<name>": { "enabled": true, ...适配器自定义参数 } }`。`sync` 段存在时完全以其为准；缺席时由存量 `board`/`github` 段等价映射（`board.enabled`→`obsidian`、`github.issue`/`pr`→`github`）。

## 触发点

同步只有三个触发点，对适配器完全透明（三者走同一 `run` 编排、同一协议、同一把锁）：

1. **archive 收口**：`/eo-archive` 归档时自动 `eo-sync run` 一次。
2. **手动**：任意时刻 `eo-sync run`（`--dry-run` 看提示性计划）。
3. **watch 自动档**：`eo-sync watch [--interval N] [--all | --project <path>]` 常驻轮询——每轮以 freshness 键短路（键不变零成本跳过），键变才进程内调用 `run` 编排；撞上进行中的手动/archive run（锁占用）跳过本轮下轮追平；`--all` 每轮重读用户级注册表 `${EO_HOME:-$HOME/.eo}/projects.json`。适配器无需感知 watch 的存在，也不得假设两次调用之间的间隔。

## 调用形态

```
eo-sync-<name> capabilities   < request.json   > response.json
eo-sync-<name> plan           < request.json   > response.json
eo-sync-<name> apply          < request.json   > response.json
```

- 动词由 **argv[1]** 给出，同时冗余出现在请求 JSON 的 `verb` 字段。
- 请求经 **stdin** 传入（UTF-8 JSON），响应写 **stdout**（UTF-8 JSON，单个对象）。
- **stderr 供人读**（错误详情、进度），核不解析。
- 每个请求/响应都带整数 `protocol_version`（见下）。

## 版本与演进

- 请求与响应均含 `"protocol_version": 1`（**主版本**）。
- **次版本演进通道 = 双方必须忽略未知字段**：核给适配器多传字段、适配器给核多返字段，对方一律忽略即前向兼容；只有破坏性改动（字段语义变更/移除/必填新增）才**递增主版本**。
- 核发现响应主版本 ≠ 自己支持的版本 → **跳过该适配器并告警**，不尝试解释（第三方不会因协议漂移被静默误用）。

## 三动词

### `capabilities`

声明自己能投影什么。请求除 `protocol_version`/`verb` 外无额外上下文。响应：

```json
{
  "protocol_version": 1,
  "name": "obsidian",
  "entities": ["change"],
  "projections": [
    { "id": "stub", "lifecycle_start": "draft", "ops": ["create", "update", "delete", "skip"] }
  ],
  "identity_fields": []
}
```

| 字段 | 含义 |
|------|------|
| `name` | 适配器名（应与 `eo-sync-<name>` 后缀一致，仅供自述） |
| `entities` | 支持的实体，v1 只有 `"change"` |
| `projections[].id` | 投影 id（如 stub / issue / pr / note） |
| `projections[].lifecycle_start` | 该投影从哪个 change 状态起开始存在：`"draft"` / `"confirmed"` / `"archived"`。核不据此预过滤，**由适配器自行在 plan 内遵守**；本字段供 `eo-sync adapters` 展示与文档对齐 |
| `projections[].ops` | 可能产出的动作子集，取自 `create`/`update`/`delete`/`skip` |
| `identity_fields` | **拥有回写权的 change frontmatter 字段名**列表（幂等键）。无回写则空列表 `[]`。约束见「回写」 |

### `plan`（纯函数，禁止任何写入）

计算「本地 → 投影」的差异，产出动作清单。**不得写入任何介质**（既不写目标平台，也不写簿记，也不写仓库文件）；可读取自己的目标介质用于差异比对/漂移检测。请求：

```json
{
  "protocol_version": 1,
  "verb": "plan",
  "context": { "project_name": "...", "project_root": "/abs/...", "doc_root": "eo-doc", "repo_root": "/abs/..." },
  "changes": [ { /* change 快照，见下 */ } ],
  "bookkeeping": { /* 本适配器的簿记命名空间，见「簿记」 */ },
  "params": { /* 配置里该适配器的启用参数（已去掉 enabled 键） */ },
  "snapshot_complete": true
}
```

- **`snapshot_complete`**（布尔，fail-safe）：本次 `changes` 是否为**可证完整**的全集。核只在同时满足「无选择性过滤（`--change`）+ 扫描/消歧零告警（无解析失败·撞号·内容分叉）+ worktree 枚举未降级」时才置 `true`；**任一不满足即 `false`**。适配器**禁止**在 `false` 时从「簿记有、快照无」推导 `delete`——那可能是被过滤/降级/告警漏掉的 change，据缺席删除即数据破坏。仅 `true`（全量、无降级）时缺席才等于放弃、可计划孤儿删除。**字段缺省时按 `false`（不完整）处理**——未显式声明完整性的核不得触发删除，这是 fail-safe 的默认。

响应：

```json
{
  "protocol_version": 1,
  "actions": [
    { "op": "create|update|delete|skip", "projection": "stub", "change_id": "batch-export", "reason": "首次投影", "payload": { } }
  ],
  "drift": [ "issue #42 已被人在 GitHub 关闭但 change 未 archived" ]
}
```

- `op` ∈ `create`/`update`/`delete`/`skip`；`reason` 为人读原因（进 dry-run 输出）；`payload` 是适配器留给自己 apply 阶段的自定义载荷。
- `drift` 是漂移**告警文本**列表（严格单向：只报不回写），可为空。
- **结构校验**：核在进入编排前按动词逐层校验响应最小结构——`actions` 须为列表、每个 action 的 `op` ∈ 枚举且 `change_id`/`projection` 为字符串；`writeback` 须为 `{change_id: {字段: 标量}}`、`results`/`bookkeeping`/`drift` 类型须合法。结构合法但 schema 非法（如 `actions: "x"`、`writeback: []`、对象值当标量）→ 按**该适配器失败**隔离、继续其它目标、run 总退出码 1；未知字段仍按 v1 规则忽略。

### `apply`

落地 plan 的动作，写自己的目标介质，返回结果 + 幂等键回写 + 更新后的簿记。请求：

```json
{
  "protocol_version": 1,
  "verb": "apply",
  "context": { "..." },
  "actions": [ { /* 同 plan 响应里的 action */ } ],
  "bookkeeping": { /* 本适配器命名空间 */ },
  "params": { }
}
```

响应：

```json
{
  "protocol_version": 1,
  "results": [ { "change_id": "batch-export", "op": "create", "ok": true } ],
  "writeback": { "batch-export": { "issue": 42 } },
  "bookkeeping": { "batch-export": { "content_hash": "…", "synced_status": "confirmed", "synced_at": "2026-07-25" } },
  "drift": []
}
```

- `results[]`（**必填**）：逐动作结果，每项须含 `change_id` 与 `op`；含 `"error"` 非空的项被核视为该适配器本次**存在失败**（计入 run 总退出码）。
- `writeback`（**必填**）：见「回写」。**无回写也须显式给空对象 `{}`**，不得省略键。
- `bookkeeping`（**必填**）：**整个命名空间的新值**（核原样持久化，不做合并）。见「簿记」。
- **必填契约（v1）**：`apply` 响应缺 `results` / `writeback` / `bookkeeping` 任一键即协议违规——核按该适配器失败隔离（其余目标照常、run 退出码 1），绝不把缺字段当空成功；`plan` 响应同理必含 `actions`，每个 action 必含 `op`/`change_id`/`projection`。

## change 快照字段

`plan` 的 `changes[]` 每项由核从 `scan_all_changes` 生成，字段稳定如下：

| 字段 | 说明 |
|------|------|
| `id` | change slug（幂等去重、投影文件名的锚） |
| `seq` | 显示别名（#N），可为 null |
| `title` / `summary` / `status` / `tier` / `type` / `created` | change frontmatter 同名字段 |
| `base_commit` | 首次实施登记的 HEAD |
| `issue` / `pr` | 已回写的平台身份字段（可为 null；**同轮内**身份字段适配器回写后，核刷新快照，纯投影适配器随即读到新值） |
| `identities` | change frontmatter 里**仅标量**字段的映射（列表/对象如 `commits`/`fix_consumed` 一律排除——身份值按协议 v1 只允许标量）。含第三方身份字段如 `page_id`。适配器据此把自己声明的身份字段**读回**——旁车簿记丢失/重建后仍能从 SoT 定位已创建对象，而非当作新对象重建。通用平台身份的读路径，不偏袒内置字段 |
| `intent` | §1 意图正文（供 issue body 等） |
| `ac` | §2 验收项列表 `[{code,done,text,manual,note}]` |
| `todo` | §3 TODO 分批 `[{batch, items:[{code,done,text}]}]` |
| `ac_done`/`ac_total`/`todo_done`/`todo_total` | 勾选计数 |
| `rel_path` | change.md 相对其所在 worktree 根的路径（stub 正文用） |
| `branch` | upsert 时的分支；在默认分支时核已置 null（适配器据此省略） |

## 退出码

**适配器进程**：`0` 成功，非 `0` 失败（stderr 供人读）。核对失败适配器：跳过、告警、计入 run 失败。

**`eo-sync run` 总退出码**：

| 码 | 含义 |
|----|------|
| `0` | 全部成功 |
| `1` | 存在适配器/动作失败（其余目标已完成，部分成功详情见输出） |
| `2` | 锁占用退出（另一个 run 正持锁，本次干净退出、无副作用） |
| 非 0 | 配置错误（`ConfigError`）沿用非零路径 |

## 回写（核执行校验与落盘，适配器只声明与返回）

平台身份（issue 号 / PR URL / Notion `page_id` 等）由适配器在 `apply` 的 `writeback` 里返回，**核**负责校验与写回 change frontmatter（SoT）。适配器**永不自己写仓库文件**。

**校验规则**（任一不过 → 拒绝该条回写并告警，其余照常）：

- 字段必须 ∈ 该适配器 `capabilities.identity_fields`；未声明/未知字段拒绝。
- 键名须匹配 `^[a-z][a-z0-9_]*$`，且**不得为 change 生命周期保留键**：`id` `seq` `title` `summary` `status` `tier` `type` `base_commit` `plan_revision` `fix_rounds` `fix_consumed` `commits` `created`。声明保留键作身份字段的适配器在 run 启动即被整体拒绝。
- 两个启用适配器声明**同名身份字段** → 二者同样 fail-closed（核无法判定归属，一并拒绝）。
- 目标字段已有**不同非空值** → 不覆盖、告警（平台身份只写空位，幂等键一经写入不变）。
- `null` 值忽略（严格单向下不删除身份）。

**保序回写**（核用 `eo_lib.upsert_frontmatter_fields`，不依赖预改模板）：

- 目标字段已存在（含值为 `~`）→ 原地替换冒号后的值，**保留该行行内注释**与缩进。
- 字段不存在（第三方身份字段如 `page_id` 默认不在模板中）→ 以 `<key>: <值>` 单行标量**追加在 frontmatter 关闭 `---` 之前**；锚点与模板内容无关，任何 change 文件通用。
- 其余行的顺序、格式、注释一律原样保留。

**多 worktree 落点消歧**（同 id 多份候选）：核先取状态最高者；同状态多份时优先「发起 run 的 worktree」内那份；发起处无该 change 且各候选内容一致 → 任取；内容分叉 → **fail-closed**（跳过该 change 回写并列出候选路径告警，绝不把枚举顺序当回写目标）。

## 簿记

核为每个适配器维护一个独立命名空间，随 `plan`/`apply` 请求传入、随 `apply` 响应整体覆盖回收。核只做持久化，不解释其内容——适配器可在自己命名空间存任意扩展键（如 Notion 的增量 checkpoint）。

- **存放**：`"${EO_HOME:-$HOME/.eo}"/sync-state/<project_name>-<hash8>.json`（`hash8` = git common dir 绝对路径 SHA-256 前 8 位，全 worktree 共享同一份、天然「一仓库一份」；测试用 `EO_HOME` 重定向隔离）。**仓库外、单份共享**，不进 SoT。
- **顶层结构**：`{"version": 1, "adapters": {"<name>": { /* 该适配器命名空间 */ }}}`。
- **推荐的每-change 记账形状**（内置适配器约定，非强制）：`{"<change-id>": {"content_hash": "…", "synced_status": "…", "synced_at": "…"}}`——`content_hash` 用于内容去重（未变 → skip），命名空间键集用于删除检测（**仅当 `snapshot_complete` 为真**：簿记有、全量快照无 → 目标被放弃 → delete；部分快照下缺席不得推导删除）。

## 并发与锁

- 非 dry-run 的 `run` 在**扫描之前取锁**，持锁完成 scan → plan → apply → 回写 → 簿记原子落盘后释放；权威计划只在锁内生成。
- `--dry-run` 只读不取锁，输出明示为**提示性计划**（落地以持锁重算为准）。
- 锁实现：POSIX `fcntl.flock` 独占簿记同名 `.lock` 文件；**v1 明示 POSIX-only**（Windows 用 WSL）。后到进程抢锁失败 → 打印持有者 `pid`+时间戳后以退出码 `2` 退出（不排队，稍后重跑）。陈锁（时间戳超 10 分钟且 pid 不存活）自动清理后重试一次。

## 第三方接入指南

1. 放一个可执行 `eo-sync-<name>`（任意语言，能读 stdin/写 stdout/给退出码即可）到 `PATH`。
2. 实现三动词：`capabilities` 声明投影与身份字段；`plan` 纯计算差异；`apply` 写目标介质并返回 `writeback`/`bookkeeping`。
3. 在配置 `sync.<name>.enabled = true` 启用，`eo-sync adapters` 应能列出其 capabilities，`eo-sync run` 会把它纳入。
4. 遵守：`plan` 零写入；未知字段忽略（前向兼容）；身份字段只写空位；stderr 供人读。

### Notion 适配器契约要点（v1 只定契约不实现）

供将来实现者对齐，也示范非内置身份字段如何承载：

- **粒度**：一个 change ↔ 一行 Notion database row；`projections: [{id:"row", lifecycle_start:"confirmed", ...}]`。
- **身份字段**：`identity_fields: ["page_id"]`——首次 apply 创建 row 后把 `page_id` 经 `writeback` 交核回写 change frontmatter（`page_id` 不在模板中，走「追加在 `---` 前」路径）。
- **限速**：Notion API 有速率限制，`apply` 内自建**令牌桶**平滑请求，`results` 里对被限速跳过的动作标注，供下轮补齐。
- **增量**：在自己的簿记命名空间存 `checkpoint`（上次同步游标）+ 每行 `content_hash`；`plan` 靠 hash 比对只对变化行产出 `update`，靠 checkpoint 支持大库分页续传。
