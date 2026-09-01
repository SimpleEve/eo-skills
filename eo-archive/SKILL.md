---
name: eo-archive
description: |
  归档 change：过四问验收门、结算工作区为 commit、冻结 change 目录。触发：归档 change / archive / /eo-archive。
---

# eo-archive — 变更归档

归档的本质：**把世界结算成 commit，冻结 change 目录为审计历史**。change 目录归档后整体冻结，**不合并回任何文档**。

## 核心理念

1. **四问核对是唯一硬门**：change.md §2 逐条过——自动项有证据、人工项验收单已勾、阻塞项不通过禁止归档；豁免必须显式记录
2. **冻结不可逆**：`status: archived` 之后 change 目录只读；后续问题按性质走 /eo-fix 或新 change
3. **commit 区间只是审计**：归集的区间写入 frontmatter 备查

## 前置条件

- **必须能找到 `.eo-project.json`**。同目录存在 `.eo-project.local.json` 时顶层字段覆盖合并（local 优先）。找不到 → 报错退出，提示运行 `/eo-project-init`
- 目标 `eo-doc/changes/<change-id>/change.md` 存在且 `status: implementing` 或 `reviewed`（存量 `done` 视同 reviewed，顺手改写）
  - draft/confirmed → 指出当前环节，回 /eo-change 或 /eo-implement；已 archived 直接告知

## 工作流程（四层）

### 第一层：四问核对门（唯一硬门）

1. **工作区无本 change 的未提交交付改动**（业务代码或测试）。有 → 先结算成 `[<change-id>]` commit 再继续
2. **§2 逐条核对**：
   - **自动项**：须有验证证据——implement 自验速报 / eo-test 报告（若挂了该闸门）/ 当前重跑。无证据 → 当前重跑补齐，或与用户确认豁免
   - **人工项**（「人工:」标记）：规范见 [../eo-shared/acceptance.md](../eo-shared/acceptance.md)——非空则 `acceptance.md` 必须存在且与集合一一对应（缺项/孤儿/重复 = 校验失败）；逐项核对勾选与异常行（用户勾的直接有效；agent 代勾必须带确认记录，缺记录按未勾）；验收基线之后存在改变人工项行为的 `[<change-id>]` 提交 → 受影响项按未勾（判不清 → 全部按未勾）
   - **阻塞项不通过/未验** → 禁止归档，按封闭选择协议（[../eo-shared/questioning.md](../eo-shared/questioning.md) §4）三选一：**补齐**（推荐——回 /eo-fix 循环内分支或 implement 修复；「不通过」= 修复循环输入，status 置回 implementing）/ **显式豁免**（§6 记录 + 验收单同项标豁免，双记录同 AC 编号）/ **终止归档**
   - **非阻塞项不通过** → 记 backlog 继续，不挡归档
3. **信号闸门核验**：§6 记录了命中信号且未豁免 → 对应闸门报告（test.md / review.md / change-review.md）须存在且结论通过；缺失或结论不通过 → 提示用户补跑或显式豁免（豁免补记 §6）
4. **brief 与最终交付一致**：校对 frontmatter `brief`，不符就地改写（口径见 [../eo-shared/summary.md](../eo-shared/summary.md)）
5. **交付证据面核对**：`evidence.md` 存在且「入口与环境 / 过程证据 / 怎么验」三段非空（规范见 [../eo-shared/evidence.md](../eo-shared/evidence.md)）。缺失或必备段为空 = 校验失败 → 按封闭选择协议（[../eo-shared/questioning.md](../eo-shared/questioning.md) §4）三选一：**补齐**（回 implement 或 /eo-fix 循环内分支）/ **显式豁免**（§6 记录）/ **终止归档**——不静默放行
6. **归档前先发交付汇报，与确认提问同条消息发出**（封闭选择，跨会话最终复核）：
   - 交付汇报 = **回复契约四条**（[../eo-shared/reply-contract.md](../eo-shared/reply-contract.md)：做了什么 / 为什么这么做 / 主要产出 / 遇到的问题与解法）+ **证据面渲染**（引 evidence.md 的入口地址、截图指针、验收指引——引用不重建）+ 核对结果汇总一句
   - 汇报之后才是封闭选择确认项；尚有未勾人工项 → 主动提议「带我验收」逐项走查；核对通过后同步勾 change.md 的人工 AC

### 第二层：工作区结算

1. `git status` 检查工作区
2. **属于本 change 的未提交改动** → 提交，message 带 `[<change-id>]` 前缀（见 [../eo-shared/conventions.md](../eo-shared/conventions.md)）
3. **无关脏改动** → 留在工作区不动
4. 两类混在同一文件无法分离 → 停下问用户如何拆分

### 第三层：冻结元数据并提交

1. 从 `base_commit..HEAD` 按 `[<change-id>]` 前缀归集本 change 的提交；单 commit 直取，多 commit 列出请用户确认；存在无前缀夹杂提交时请用户圈定
2. 写入 frontmatter：`commits: [<区间>]`（仅审计用）、`status: archived`（不可逆）
3. 更新 `eo-doc/changes/INDEX.md` 对应行，顺手对 seq 列查重（重号 → created 晚者让号，见 [../eo-shared/conventions.md](../eo-shared/conventions.md) §2）
4. 以上文档改动提交入库——可与第二层合为同一个 commit（推荐一次 change 一次 commit）；implement 已按批提交时，这就是一个小的收尾 meta commit

### 第四层：收尾

1. **投影同步**：调用 `eo-sync run` 一次（内置 obsidian/github 适配器按启用配置执行——stub 投影 `status: archived`（**tags 与文件位置不动**：`eo-change` tag 是看板过滤锚点）、issue 兜底关闭、PR 按 `github.pr` 策略仅对 archived 生成；未启用目标跳过，机制见 [../eo-shared/board-github.md](../eo-shared/board-github.md)）。本次 run 产生身份字段回写（典型：PR URL、迟到的 issue 号）时，**立即追加第二个收尾 commit** `[<change-id>] sync 身份回写`（无回写则零额外 commit）——归档完成时工作区无未提交 SoT。本次 run 创建/更新了 PR → 回写 commit 后追加 `git push` 同一分支一次（追加推送自动进入 PR，合并后 SoT 含幂等键）；push 失败告警不阻塞归档（幂等键已在本地 SoT，随后续任意 push 传播）。sync 本身失败降级为告警不阻塞归档（投影可随时手动 `eo-sync run` 补上）
   - **冻结语义**：归档后 change 目录冻结，**唯一允许的后续写入 = eo-sync 身份字段回写**（PR URL 只可能在 archived 后产生）；此后手动 run 若补写身份字段，作为工作区常规变更随下次提交走，不自动提交
2. **state 联动（配置驱动）**：合并配置 `state.enabled: true` → 调用 `/eo-doc-manager sync`（cursor..HEAD 增量再生现状篇，完成推进游标；archive 只是该机制的两个触发点之一，同步语义以 doc-manager 为单一来源，本 skill 不复述）。sync 失败降级为告警不阻塞归档——游标未推进，手动重跑 sync 即续上。未启用 → 零动作
3. **值得留的教训/决策**：本 change 踩过的坑、定下的取舍，够 [../eo-shared/lessons.md](../eo-shared/lessons.md) / eo-project-record 门槛的，提议沉淀（用户点头才写）
4. 对话速报（不写额外文件）：

```
归档完成：<change-id>
- 四问核对：自动项 <n>/<n> 有证据；人工项 <m>/<m> 已勾；豁免 N 项（已记 §6）
- commit 区间：<...>（N 个提交）
```

## 关键约束

| 约束 | 说明 |
|------|------|
| 不反写任何文档 | change 内容不合并回任何文件；归档即冻结为审计历史 |
| 四问门禁 | 阻塞项未过必须走「补齐 / 显式豁免 / 终止」三选一，不得静默放行；非阻塞项记 backlog 可放行 |
| 证据面硬门 | evidence.md 缺失或三段有空 = 校验失败，三选一不静默放行 |
| 交付汇报硬步骤 | 确认提问前必发交付汇报（回复契约四条 + 证据面渲染），与确认同条消息；不得只发一句汇总 |
| 信号闸门核验 | 命中且未豁免的闸门报告缺失或结论不通过 → 提示补跑或豁免，不静默放行 |
| 归档不可逆 | archived 后不回退 status；后续问题走 /eo-fix 或新 change |
| 区间仅审计 | commit 区间只写 frontmatter 备查 |
| 一次一个 | 一次归档一个 change；多个待归档时逐个走完四层 |
