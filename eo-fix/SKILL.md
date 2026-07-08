---
name: eo-fix
description: |
  bug 口喷入口：轻量定位 + 三方对比（AC ↔ state ↔ 代码）+ 直接修复；原因不明的难缠 bug 自动升级深挖模式；实为需求变更时转 /eo-change。触发：修 bug / 有个 bug / 行为不对 / fix / /eo-fix。
  NOT FOR: 明确的业务变更（走 /eo-change）；implement-test-review 循环内的反馈修复（归 /eo-implement 模式二）。
---

# eo-fix — Bug 修复

用户口喷一个「行为不对」，本 skill 负责走完全程：**定位原因 → 判定归属 → 直接修复 → 验证**。只有「这其实是需求变更」才把球踢出去。

## 核心原则

1. **先索引后全文**：禁止全局 grep；用 changes/INDEX.md、state/INDEX.md、agent-handbook/INDEX.md 的表格摘要 + frontmatter（tags/summary）收敛候选，锁定后只读相关小节
2. **三方对比**：F-ac（期望行为）/ F-state（文档记载的现状）/ F-code（实现事实）凑齐再下结论；证据不足只说「倾向」并追问
3. **直接修复**：判定为实现 bug 就地修，不倒手给其他 skill
4. **深挖有门**：常规手段定位不了才升级深挖模式，升级必须向用户宣告

## 前置

**必须能找到 `.eo-project.json`**。找不到 → 报错退出，提示运行 `/eo-project-init`。

## 工作流程

### 第一步：搜集现象

确认三项（用户描述已含则不重复问）：期望行为（按哪个说法它本该怎样）、实际行为（表现 + 复现步骤）、猜测范围（粗略词即可）。同时检索 `<project_root>/lessons/`——同类坑踩过的直接引用结论。

### 第二步：轻量定位

1. 读 `eo-doc/changes/INDEX.md`：按关键词匹配摘要，锁定相关 change——**活跃（非 archived）优先**，其次最近 archived
2. 读 `eo-doc/state/INDEX.md`（存在时）：挑一篇描述该功能现状的文档
3. 读 `eo-doc/agent-handbook/INDEX.md`：定位实现代码的入口文件
4. 候选 >3 或全无匹配 → 追问用户，不硬挑

### 第三步：三方事实

| 记号 | 来源 | 缺位时 |
|------|------|--------|
| **F-ac** | 相关 change 的 §2 验收清单（+ §1 已钉决策） | 无相关 change → 以用户口述的期望行为为准，并注明「无书面 AC」 |
| **F-state** | state/ 对应篇目的规则/流程描述 | state 未建 → 跳过此方 |
| **F-code** | 按 handbook 定位的实现（只读相关函数/行） | — |

### 第四步：路由判定（修复前）

| 观察 | 判定 | 动作 |
|------|------|------|
| F-code ≠ F-ac（或明显缺陷：崩溃、数据错、显而易见的逻辑错） | **实现 bug** | 进第五步直接修复 |
| F-ac 本身写漏/写偏，且 change 未 archived | **AC 写漏** | 告知用户，确认后先补 change.md §2/§3，再进第五步修 |
| 期望行为变了 / 涉事 change 已 archived 且改动非平凡 | **需求变更** | 停手，建议 `/eo-change`（把已收集的现象与结论带过去） |
| F-state ≠ F-code | **文档陈旧** | 顺手提示跑 `/eo-doc-manager sync`，以代码为准重判 |
| 原因无法定位 / 无法稳定复现 | **难缠 bug** | 升级深挖模式（第六步） |

**修复范围判断**（进第五步前）：预估改动若不再是 trivial 量级（判据见 [../eo-shared/granularity.md](../eo-shared/granularity.md) §2，如需要方案权衡、动对外接口）→ 停手建议开 change，不硬修。

### 第五步：执行修复

1. 修改代码，最小变更
2. **验证**：用户给的复现步骤转成回归验证，跑通；相关 AC（若有）重新核对
3. **落点**：
   - 有相关**活跃 change** → 修复计入该 change：勾选涉及的 TODO/AC，commit 带 `[<change-id>]` 前缀；联动钩子刷新 stub（[../eo-shared/board-github.md](../eo-shared/board-github.md)，未开启跳过）
   - 无活跃 change → 直改落地：commit 带 `fix:` 前缀（见 [../eo-shared/conventions.md](../eo-shared/conventions.md)），由 doc-manager 的下次 sync 兜底归档；顺带报告 cursor 落后量，超过 10 个 commit 建议顺手跑 `/eo-doc-manager sync`

### 第六步：深挖模式（自动升级）

触发即向用户宣告：**「常规定位失败，进入深挖模式：会临时插桩/加日志/git bisect，结束后还原现场。」**

1. 读 [references/investigation.md](references/investigation.md)，按四阶段执行（固定复现 → 假设清单 → 二分排除 → 验证还原）
2. 调查记录写 `tmp/eo/fix/<date>-<slug>.md`（可丢弃工件，见 conventions.md）
3. 根因确认后**回到第四步路由表**定归属，再走第五步修复
4. 根因有普适教训 → 提议用户跑 `/eo-project-lesson` 沉淀（调查记录本身不是沉淀）

### 第七步：收尾速报

```
修复完成：<一句话根因>
- 改动：<file:line 级别的简述>
- 验证：<复现步骤回归结果 / AC 核对结果>
- 落点：计入 <change-id> / 直改（fix: commit <hash>）
- （深挖时）调查记录：tmp/eo/fix/<file>；建议沉淀 lesson：<是/否>
```

## 关键约束

| 约束 | 说明 |
|------|------|
| 禁全局 grep | 定位只走 INDEX + frontmatter 收敛 |
| 三方齐备才下结论 | 任一缺位只说「倾向」；证据不足追问，不乱猜 |
| 修复范围守界 | 超出 trivial 量级 / 需要方案权衡 → 建议开 change，不硬修 |
| 深挖必宣告、必还原 | 插桩/日志/bisect 结束后全部还原；调查记录只进 tmp/eo/fix/ |
| 需求变更不伪装成 fix | 期望行为本身变了就是 /eo-change 的事，哪怕改动很小 |
| 与 implement 的分工 | test/review 反馈的修复归 /eo-implement 模式二；本 skill 是流程外的口喷入口 |

## 典型场景

**场景 1 · 实现 bug**：「导出 CSV 字段顺序乱了」→ 定位 change `012`，F-ac 说顺序 [A,B,C,D]，F-code 是 [A,C,B,D] → 直接修，`012` 活跃则勾 AC 计入，否则 `fix:` 直改。

**场景 2 · AC 写漏**：「重试只在网络错误触发，超时不触发」→ F-ac 只写了网络错误（漏超时），change 未归档 → 确认后补 AC-3「超时同样重试」+ 对应 TODO，再修代码。

**场景 3 · 需求变更伪装**：「积分过期改成 90 天了，现在还是 30 天」→ 三方自洽都是 30 天 → 这是业务变更，转 /eo-change（带上下文），本 skill 不动代码。

**场景 4 · 难缠 bug**：「偶发卡死，复现不稳定」→ 三方对比无果 → 宣告进入深挖 → 固定复现 → 假设清单 → bisect 锁定引入点 → 回路由表：实现 bug → 修复 + 还原插桩 + 建议沉淀 lesson。
