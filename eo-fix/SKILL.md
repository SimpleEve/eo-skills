---
name: eo-fix
description: |
  发现 bug 但不确定是代码写错了、change 方案写偏了，还是 spec 基线本身就错了时，先用此 skill 做诊断路由。用 INDEX + frontmatter (tags/summary) 轻量定位相关 spec / change / state，再三方对比事实，给出「直接 fix」vs「追加 change」的建议。触发：修 bug / 不知道是实现错还是方案错 / 到底该 fix 还是开 change / /eo-fix。
  NOT FOR: 已经定位清楚的实现 bug（直接走 /eo-implement）；明确的业务变更（走 /eo-change）。
---

# eo-fix — Bug 发现后的诊断路由

用户发现一个"行为不对"，但说不清楚是**代码实现错了**、**change 方案错了**、还是**spec 基线错了**。本 skill 只做三件事：

1. **轻量定位**：不全文 grep `eo-doc/`，靠 INDEX + frontmatter (tags/summary) 锁定候选 spec / change / state
2. **三方对比**：凑齐 F-spec / F-change / F-code 三份事实再下结论
3. **分叉建议**：告诉用户走哪条路（`/eo-implement` fix / 内联改 change / 开 enhance change），不亲自改文件

## 前置

**必须能找到 `.eo-project.json`**。找不到 → 报错退出，提示运行 `/eo-project-init`。`eo-doc/` 路径通过 `doc_root` 字段解析。

## 定位（相对于其他 skill）

| skill | 职责 | 本 skill 何时把球踢给它 |
|-------|------|------------------------|
| `/eo-fix` | **诊断路由**：不知道错在哪一层时先判断 | — |
| `/eo-implement`（fix 模式）| 在当前 change 内循环修代码，不开新 change | 诊断为"代码没对齐" |
| `/eo-change-review` | change.md 方案审查 | change §3 小修订后复审 |
| `/eo-change` | 对已有模块发起新变更（含 enhance）| 诊断为"spec 基线就错了，是业务变更" |
| `/eo-flow fix` | 把 fix 甩给 tmux 另一 pane 的 codex | 用户走多 pane 工作流时备选 |

**fix 不开新 change** 是 `eo-implement` 的硬规则。本 skill 的价值正是判断这条硬规则是否适用——若是 spec 错了，那就不是 fix，是 enhance。

## 核心原则

1. **先索引后全文**：禁止 `grep -r` spec/change 正文；用 INDEX 的表格摘要 + frontmatter 的 `tags`/`summary` 缩小候选集，锁定后再读正文对应小节
2. **三方齐备才下结论**：spec / change / code 任一缺失都只能说"倾向"，不能说"是"
3. **不动手改**：只出诊断 + 建议；改文件/改代码的动作由用户拍板后派给对应 skill
4. **证据不足就追问**：宁可多问一轮，也不要硬猜

## 工作流程

### 第一步：搜集现象

向用户确认以下三项（用户描述里已含则跳过对应条）：

- **期望行为**：按哪份文档 / 哪次对话，它本该是什么样？
- **实际行为**：当前表现 + 重现步骤？
- **触及范围**：猜测涉及哪个模块 / 哪个功能？（粗略词即可，不强求精确）

### 第二步：轻量定位（Token 高效）

**绝不全局 grep spec/change/代码正文**。严格按下列三层逐步收敛：

1. **模块层**：读 `eo-doc/dev/INDEX.md`
   - 按关键词匹配 `Title` / `Tags` / `Summary` 列，找出 1–3 个候选模块
   - 候选 > 3 → 向用户追问缩小范围，不要硬挑

2. **模块内候选**：对每个候选模块
   - 读 `eo-doc/dev/<module>/spec.md` 的 **frontmatter**（`tags` / `summary` / `status`），**不读正文**
   - 读 `eo-doc/dev/<module>/changes/INDEX.md` 全表（每行含 change-id / type / status / 日期 / 摘要）
   - 按"与现象最相关"挑 1–2 个候选 change

3. **state 交叉对照**（可选）：若存在 `eo-doc/state/INDEX.md`
   - 按关键词匹配，挑一篇描述该功能"实际做了什么"的 state 文档作为第三方对照

输出定位摘要：

```
候选定位：
  - module: <module-name>   spec tags=[...]  summary=...
  - change: <NNN-xxx>        type=enhance    status=archived   summary=...
  - state:  <state-file>     （可选）
```

若定位失败（无匹配 / 用户否认）→ 向用户追问更多线索，不要硬猜。

### 第三步：读事实（锁定后才读正文）

对锁定的候选，**只读与现象相关的小节**，不要通读：

- **spec.md**：读 §3（功能需求，尤其 §3.3 核心行为 / §3.4 业务规则）+ §6（AC）里对应小节
- **change.md**：读 §3（Delta 或 bootstrap 实现范围）+ §5（AC）+ §4.3 里相关 TODO
- **代码**：按 change.md §2.3 / §4.3 的"涉及文件"列表定位实际实现的函数/行

凑齐三组事实：

| 记号 | 含义 |
|------|------|
| **F-spec** | spec 声明的应有行为 |
| **F-change** | change 对 spec 做了什么 Delta（或 bootstrap 认领了哪段） |
| **F-code** | 代码实际行为 |

### 第四步：诊断分叉

按下表判断根因：

| 观察 | 根因 | 建议路径 |
|------|------|---------|
| F-code ≠ F-change（代码没按 change §3/§5 实现）| **实现没对齐** | `/eo-implement` fix 循环（或 `/eo-flow fix`）；**不开新 change** |
| F-change ≠ F-spec 且 change 未 archived（`status` ∈ `approved`/`implementing`/`done`）| **change 方案写偏了** | 内联改 change.md §3/§5 → `/eo-change-review` → 重跑 `/eo-implement` |
| F-change ≠ F-spec 且 change **已 archived** | **已归档 change 的实施不符 spec** | 仍属 implement 补丁循环：`/eo-implement` fix；**不开新 change** |
| F-spec 声明的业务意图与用户当前真实需求不一致 | **spec 基线错了（其实是业务变更）** | `/eo-change <module>` 开 `enhance` change |
| F-spec / F-change / F-code 三方自洽，但用户说"现在不该这样" | 新需求伪装成 bug | 同上：`/eo-change` 开 `enhance` |
| 现象不可复现 / 三方事实凑不齐 | 证据不足 | 追问用户；不下结论 |

**关键判据**（用户原话语义线索）：

- "实现得不对" / "跟 AC 不符" / "明明写了却没做" → 倾向**实现错**
- "方案漏了 xxx" / "change 写偏了" / "应该还要 …" → 倾向 **change 方案错**
- "需求变了" / "现在我想要…" / "当初没考虑到" → 倾向 **spec 错（=业务变更）**

### 第五步：输出诊断报告

给用户一份**短报告**（不要长篇），结构如下：

```
## 诊断：<一句话结论>

### 证据
- F-spec（<module>/spec.md §X.Y）:   ...
- F-change（<NNN-xxx>/change.md §3）: ...
- F-code（<file:line>）:              ...

### 不一致项
- [x] F-code ≠ F-change
- [ ] F-change ≠ F-spec
- [ ] F-spec 本身错

### 建议路径
→ /eo-implement <change-path>（或 /eo-flow fix，若用多 pane 工作流）

### 备选
若你认为真正问题在 spec（业务变更），走 /eo-change <module> 开 enhance。
```

**停手，等用户拍板**。不自动派发。

### 第六步：用户确认后转交

- 用户认同"实现错" → 提示 `/eo-implement <change-path>` 或 `/eo-flow fix`
- 用户认同"change 方案错"且未归档 → 提示**本 pane 内联改 change.md**，改完跑 `/eo-change-review`（不走 `/eo-review`——代码还没改）
- 用户认同"spec 错 / 业务变更" → 提示 `/eo-change <module>` 开 enhance（不走 implement fix 循环）

## 关键约束

| 约束 | 说明 |
|------|------|
| 先索引后全文 | 禁止全局 `grep` spec/change 正文；用 INDEX + frontmatter `tags`/`summary` 收敛候选集 |
| 候选 > 3 就追问 | 模块层匹配出 4+ 候选时不要硬挑，先问用户 |
| 三方齐备才下结论 | F-spec / F-change / F-code 任一缺失只能说"倾向"，不能说"是" |
| 不动手改 | 只做诊断 + 建议，不改 spec / change / code |
| 不自动开新 change | 只在"spec 错了且属业务变更"时建议 `/eo-change` enhance；fix 不升格是 `/eo-implement` 的硬规则 |
| change-review 对应 change-review | 内联改完 change.md 后复审用 `/eo-change-review`（方案审查），**不是** `/eo-review`（代码审查） |
| 证据不足就问 | 现象说不清 / 候选太多 → 追问用户，不乱猜 |

## 典型场景

### 场景 1：代码 bug（最常见）

> 用户："导出 CSV 时字段顺序乱了。"

- 定位 → `export` 模块
- F-spec（spec §3.2）：字段顺序 [A, B, C, D]
- F-change（`012-xxx` §3）：Delta 没动字段顺序
- F-code：实际顺序 [A, C, B, D]
- → **实现没对齐**。建议 `/eo-implement <012-xxx>` 或 `/eo-flow fix`

### 场景 2：change 方案写偏

> 用户："这个功能说是要加重试，但只在网络错误触发，超时不触发。"

- F-spec（spec §3.3）：重试覆盖「网络错误 + 超时」
- F-change（`007-retry` §3 ADDED）：只写了"网络错误重试"（漏了超时）
- F-code：按 change 实现的，仅网络错误触发
- → **change §3 写漏了一个条件**。若 `007-retry` 未归档 → 内联改 change.md §3 → `/eo-change-review` → `/eo-implement`

### 场景 3：spec 错了（业务变更伪装）

> 用户："现在规定积分过期 90 天，不是 30 天。"

- F-spec（spec §3.4）：声明的就是 30 天
- F-change + F-code：全按 30 天实现，三方自洽
- → **spec 基线不符合现在的业务**——这是业务变更。建议 `/eo-change <module>` 开 `enhance`（把 30 改 90）

## 与其它 skill 的关系

- `/eo-implement`：本 skill 诊断为"代码错"后把球交给它（fix 循环不开新 change）
- `/eo-change`：本 skill 诊断为"spec 错 / 业务变更"后交给它（开 enhance）
- `/eo-change-review`：内联改完 change.md 后用它复审
- `/eo-flow fix`：多 pane 工作流时的代码 fix 派发入口（等价 `/eo-implement`）
- `/eo-review`：不相关。`/eo-review` 是代码审查，本 skill 不走这条路径
