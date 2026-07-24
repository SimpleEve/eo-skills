---
name: eo-archive
description: |
  归档 change：结算工作区为 commit、冻结 change 目录、触发文档同步（doc-manager sync）。按档分流准入：全档需 review 通过，轻档凭完成门留痕。触发：归档 change / archive / /eo-archive。
  NOT FOR: 未过准入门的 change（全档先走 /eo-review；轻档先过 eo-implement 轻模式完成门）；文档同步本身的细节（归 /eo-doc-manager）。
---

# eo-archive — 变更归档

归档的本质：**把世界结算成 commit，然后按 commit 更新文档**。change 目录归档后整体冻结为审计历史，**不合并回任何文档**——活文档（state/ + agent-handbook/）由 doc-manager 以代码为唯一信源维护，本 skill 只是它的触发点之一。

## 核心理念

1. **零同步逻辑**：本 skill 不拥有任何文档同步细节，第四层是对 `/eo-doc-manager sync` 的内嵌调用（加载并执行其流程）
2. **AC 是归档门**：验收清单全勾才能归档，人工项经 acceptance.md 逐项核验（唯一硬门在此）；豁免必须显式记录
3. **冻结不可逆**：`status: archived` 之后 change 目录只读；后续问题按性质走 /eo-fix 或新 change
4. **commit 区间只是审计**：归集的区间写入 frontmatter 备查，不决定同步范围（同步永远是 cursor..HEAD）

## 前置条件

- **必须能找到 `.eo-project.json`**。同目录存在 `.eo-project.local.json` 时顶层字段覆盖合并（local 优先）。找不到 → 报错退出，提示运行 `/eo-project-init`
- 目标 `eo-doc/changes/<change-id>/change.md` 存在且 `status: reviewed`（存量 `done` 视同 reviewed，顺手改写；`tier: light` 为 `implementing`，见下条）
- **归档两档同源于本 skill**：`tier: light` 走第一层的**轻档门**（无 review/test 台账，门槛改为完成门留痕校验）；eo-implement 轻模式收口即内嵌调用本 skill——主控 / implement / 用户任一上下文触发皆可，门槛校验不因入口而减免

## 工作流程（五层）

### 第一层：前置校验（按档分流）

**全档（tier 缺省/full）**：

1. `status: reviewed`（不是 → 指出当前所处环节：draft/confirmed 回 /eo-change 或 /eo-implement；implementing 回 /eo-implement；已 archived 直接告知）
2. **报告当前结论门**（读末尾速报 + 台账，不通读正文——正文是历史快照）：
   - **工作区无本 change 的未提交实施改动**（有 → 先结算成 `[<change-id>]` commit 再回 /eo-review——未经审查的实施改动不得借第二层结算绕过下一条）
   - `review.md` 存在且末尾速报结论为通过（P0/P1 已清零），且其**最新轮基线 commit == 本 change 最后一个 `[<change-id>]` 实施提交**——修过码必须重新 review，旧结论不作数（不符 → 回 /eo-review 复审）
   - `test.md` 存在时末尾速报必须为通过（test 不强制基线新鲜度——重验证一次跑完的取舍；触及 heavy AC 的修复由模式二收尾提示重跑）；台账不得有 `open`/`fixed` 的**阻塞项**（= review 台账 P0/P1、test 台账级别「阻塞」行；`waived`/`superseded`/P2 不算）——有 → 回 /eo-implement 模式二修复或重跑对应验证核销
3. **验收清单全勾 + 人工验收硬门**（规范见 [../eo-shared/acceptance.md](../eo-shared/acceptance.md)）：
   - 从 change.md §2 解析 manual AC 集合（「人工:」标记）——**非空则 `acceptance.md` 必须存在且与集合一一对应**（缺项/孤儿/重复 = 校验失败）；空集则只查普通 AC 全勾
   - 逐项核对勾选与异常行：用户勾的「通过」直接有效（勾选权归用户）；agent 代勾必须带确认记录（日期 +「原话」），缺记录按未勾处理
   - 验收基线之后存在改变人工项行为的 `[<change-id>]` 提交 → 受影响项按未勾（判不清 → 全部按未勾）
   - **未勾的 auto-heavy AC**（重验证项，勾选权归 /eo-test 不归 implement——跳过 eo-test 时它们必然未勾）→ 提示跑 `/eo-test` 补验；与下方未勾项同处置，**不得静默放行**
   - **归档前把已勾项汇总一句请用户一键确认**（封闭选择，跨会话最终复核）；尚有未勾项 → 主动提议「带我验收」逐项走查；核对通过后同步勾 manual AC
   - 存在不通过/待验/未勾项 → 按封闭选择协议（[../eo-shared/questioning.md](../eo-shared/questioning.md) §4）三选一：**补齐**（推荐——回 /eo-implement 修复，或回 /eo-test 补验重验证项；「不通过」= 修复循环输入，status 置回 implementing）/ 显式豁免（§8 + 验收单同项标豁免，双记录同 AC 编号）/ 终止归档

**轻档（tier: light）**——无 review/test 台账，门槛改为**完成门留痕校验**（证据只认工件留痕与重跑，执行者自述不作数）：

1. `status: implementing`（draft/confirmed → 回 /eo-implement 轻模式；已 archived 直接告知）
2. **工作区无本 change 的未提交实施改动**（有 → 先结算成 `[<change-id>]` commit；结算后独立复核基线必然过期，由下一条拦回——不得跳过下条放行）
3. **独立复核留痕新鲜**：change.md 末尾存在「独立复核：通过」行，且其基线 short-sha == 本 change 最后一个 `[<change-id>]` 实施提交（缺失 / 不通过 / 基线过期 → 回 /eo-implement 重跑完成门）
4. **锁定测试绿**：frontmatter 有 `test_lock_commit` → 重跑锁定测试确认全绿（implement 收口内嵌调用时，完成门刚跑过且其后无新提交 → 可复用该绿灯不重跑）；无锁定轻档（change.md 已注明）→ 跳过本条
5. **AC 全勾 + manual 确认留痕**：manual 项（「人工:」）代勾必须带 AC 行确认记录（「确认：原话要点 + 日期 + 基线 sha」，规范见 [../eo-shared/ac-spec.md](../eo-shared/ac-spec.md)）；存在未勾/缺记录项 → 三选一：补齐（回 /eo-implement）/ 显式豁免（AC 行标豁免 + 原话 + 日期）/ 终止归档

以下第二~五层两档共用，差异点在层内标注。

### 第二层：工作区结算

cursor 基于 commit，sync 只能看见已提交内容，因此先结算：

1. `git status` 检查工作区
2. **属于本 change 的未提交改动** → 提交，message 带 `[<change-id>]` 前缀（见 [../eo-shared/conventions.md](../eo-shared/conventions.md)）
3. **无关脏改动** → 留在工作区不动（后续 sync 默认「只取已提交增量」不会碰它们）
4. 两类混在同一文件无法分离 → 停下问用户如何拆分

### 第三层：冻结元数据并提交

1. 从 `base_commit..HEAD` 按 `[<change-id>]` 前缀归集本 change 的提交；单 commit 直取，多 commit 列出请用户确认；存在无前缀夹杂提交时请用户圈定
2. 写入 frontmatter：`commits: [<区间>]`（仅审计用）、`status: archived`（不可逆）
3. 更新 `eo-doc/changes/INDEX.md` 对应行（轻档档列写 light），顺手对 seq 列查重（重号 → created 晚者让号，见 [../eo-shared/conventions.md](../eo-shared/conventions.md) §2）
4. 以上文档改动提交入库——可与第二层合为同一个 commit（推荐一次 change 一次 commit）；implement 已按批提交时，这就是一个小的收尾 meta commit

### 第四层：文档同步（内嵌调用）

执行 `/eo-doc-manager sync` 的完整流程（读其 SKILL.md 与 references 照做）：cursor..HEAD 增量更新 state/ + agent-handbook/，完成后 cursor 推进到 HEAD。

- 把 change.md 路径作为业务语境提示带入（帮助 sync 理解「为什么改」）；**信源永远是代码**，不按 change 说的写、按代码是的写
- 同步范围覆盖第二/三层的提交与期间累积的直改提交，一并吸收
- 若 sync 中途失败：change 已冻结、cursor 未推进——直接手动重跑 `/eo-doc-manager sync` 续上，不需要回滚归档
- 例外：本 change 的 diff 不触碰代码路径（纯文档/流程工件）→ 可跳过本层并说明，cursor 不动（期间累积的直改增量留待下次任意 sync 收割）

### 第五层：收尾

1. 联动钩子：按 [../eo-shared/board-github.md](../eo-shared/board-github.md) 执行——stub 最终 upsert（仅置 `status: archived`，**tags 与文件位置不动**：`eo-change` tag 是看板过滤锚点）、issue 兜底关闭、PR 创建（按 `github.pr` 策略；对应开关未开启则跳过）
2. 对话速报（不写额外文件）：

```
归档完成：<change-id>
- commit 区间：<...>（N 个提交）
- 文档同步：state/ 更新 X 篇、agent-handbook/ 更新 Y 篇（跳过 Z 篇）
- AC：全勾 / 豁免 N 项（已记 §8）
- 后续建议：<doc-manager 若提示一致性校验到期，转达；否则省略此行>
```

## 关键约束

| 约束 | 说明 |
|------|------|
| 不反写任何文档 | change 内容不合并回 state/handbook/其他文件；活文档更新只经由第四层的 sync |
| 零同步逻辑 | 第四层是内嵌调用 /eo-doc-manager，本文件不复述其任何步骤 |
| AC 门禁 | 未全勾必须走「补齐 / 显式豁免 / 终止」三选一，不得静默放行 |
| 归档不可逆 | archived 后不回退 status；后续问题走 /eo-fix 或新 change |
| 区间 ≠ 范围 | commit 区间只写 frontmatter 审计；同步范围永远是 cursor..HEAD |
| 一次一个 | 一次归档一个 change；多个待归档时逐个走完五层 |
| 两档同源 | 轻档只换第一层准入门（完成门留痕），第二~五层与全档共用；implement 轻模式收口 = 内嵌调用本 skill，门槛不因入口减免 |
