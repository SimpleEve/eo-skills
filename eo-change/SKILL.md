---
name: eo-change
description: |
  发起变更，产出四问骨架的 change 工件（解决什么问题 / 完成后看到什么 / 谁验收 / 不通过怎么办）。触发：新增 / 加功能 / 增强 / 重构 / change / /eo-change。
  NOT FOR: bug 修复（走 /eo-fix）；trivial 小改（本 skill 会主动短路成直改，不产生工件）。
---

# eo-change — 发起变更

发起一次变更。change 是**过程工件**：起草期承载澄清与拆解，实施期承载进度，归档即冻结为审计历史——**不合并回任何文档**。

## 核心理念

1. **四问骨架**：change.md 的第一受众是用户。§1 解决什么问题、§2 完成后我应该看到什么、§3 谁验收按什么标准、§4 不通过怎么办——工程细节折叠进 §5 技术备注
2. **验收驱动**：AC（§2）先于 TODO 产出，是 implement 的完成判据、archive 的验收门、fix 的期望行为锚点
3. **默认信任，信号升级**：主路只有 change → implement → archive 三站；命中风险信号才建议挂闸门（change-review / test / review），清单与纪律见 [../eo-shared/granularity.md](../eo-shared/granularity.md) §5
4. **量化粒度**：超软标建议拆、超硬标拒绝确认，指标数值以 granularity.md §1 为准
5. **提问有预算**：事实自查、决策上抛——规则见 [../eo-shared/questioning.md](../eo-shared/questioning.md)
6. **状态自动流转**：用户在对话里确认，skill 落盘 status，用户永不手改 frontmatter

## 前置条件

- **必须能找到 `.eo-project.json`**（cwd 或父目录）。同目录存在 `.eo-project.local.json` 时顶层字段覆盖合并（local 优先）。找不到 → 报错退出，提示运行 `/eo-project-init`。`eo-doc/` 路径由 `doc_root` 解析
- `eo-doc/changes/` 不存在时 lazy 创建（含 INDEX.md 骨架）

## 工作流程

### 第一步：意图理解

1. 读用户的变更描述。**若来自 /eo-brainstorming 捕获出口**：直接继承其已钉决策与 change 草案，跳过已钉项的一切重复提问，从第四步续起。**若来源是某张 backlog 卡**：继承卡片的 title/说明/标签作为意图输入，记下卡片路径待确认后归档。**若来源是外部 GitHub issue**：继承其正文作意图输入，记下 issue 号待落盘回写 `issue:`（eo-sync 靠回写号去重）
2. **trivial → 主动短路**：按 [../eo-shared/granularity.md](../eo-shared/granularity.md) §2 判据，满足即告知用户「这不值得开 change，直接改」，按直改模式执行（改 → 验证 → `fix:`/`ui:` 前缀 commit；注释零溯源，见 [../eo-shared/conventions.md](../eo-shared/conventions.md) §2.6），本流程终止
3. **方向未定 → 建议升级**：「这个方向本身还没定，建议先 /eo-brainstorming 把决策钉了再回来」；用户坚持则继续，澄清预算放宽到 5+
4. **update vs new**：若变更明显是某个未归档 change 的意图精化 → 提议就地更新那个 change 而非新开（决策表见 granularity.md §3）

### 第二步：事实自查（静默执行）

提问之前先自答：

1. 定位相关现状与实现：`.codegraph/` 索引存在则 `codegraph explore` 优先召回；不存在则按目录收敛 + 源码直读相关段落
2. 读 `eo-doc/changes/INDEX.md` 最近 3 条（演化方向，避免重复/冲突）
3. **lessons 消费**：按 [../eo-shared/lessons.md](../eo-shared/lessons.md) §1 扫 INDEX 匹配 trigger/tags，命中 ≤3 条读其「规则」节带入起草；采纳的在 §1 已钉决策标注来源
4. 涉及外部世界 → 按 [../eo-shared/research.md](../eo-shared/research.md) 消费规则查 `<project_root>/research/`
5. 涉及 UI 且仓库根有 `DESIGN.md` → 读入作为默认设计约束
6. 能从以上信源回答的问题，**禁止问用户**

### 第三步：预算内澄清

按 [../eo-shared/questioning.md](../eo-shared/questioning.md) 全文执行：预算配比、每轮 1-2 问、封闭选择按其 §4 协议（带推荐项）、视觉/UI 方向类问题必带「画 HTML 对比页」选项、疲劳信号立即降级用默认。defer 上限 3 条，落入 §6 开放问题。

### 第四步：风险信号扫描与播报

过一遍 [../eo-shared/granularity.md](../eo-shared/granularity.md) §5 信号清单，**显式播报命中/未命中及理由**；命中 → 建议挂对应闸门，用户一个词豁免（豁免记 §6）。判不准按命中处理。

### 第五步：产出 §2 验收清单（先于 TODO）

按 [../eo-shared/ac-spec.md](../eo-shared/ac-spec.md) 撰写：演示脚本口吻、归属与阻塞标注、覆盖异常路径。**AC 定不下来说明澄清还没到位，回第三步。**

### 第六步：TODO 拆解与分批（§5 技术备注）

- 每条 TODO 三要素（描述/文件/对应 AC），逐条映射 AC；**禁止占位符**
- 按 Batch 分组，**Batch 1 = MVP**：跑完即可独立验证其对应 AC；每批结束有可验证的东西，避免按层切批
- **并行组**：互不干扰的批（文件集不相交 + 无逻辑依赖，判据见 granularity.md §6）拆成同层并行批，字母后缀标注（`Batch 2a` / `Batch 2b`）；判不准不标，串行是安全缺省
- 不写具体函数体；接口签名/数据结构可以描述
- 触碰对外契约/已生效行为 → 按 questioning.md §4「破坏性变更类问题」强制问清直接替换还是保留兼容，结论钉入 §1

### 第七步：粒度自检（自动校验）

对照 granularity.md §1：数 TODO、`wc -l` 全文。超软标建议按 AC 分组拆成 change 序列（第一个 = MVP）；超硬标**拒绝进入确认**，必须拆。序列内后续 change 依赖前序产出的在 INDEX 摘要列标「依赖 #N」（granularity.md §6），无标注 = 串行。

### 第八步：写入 change.md + 探针对齐

1. **确定 change-id**（slug 即身份，规则见 conventions.md §2）：查重（本地 + `git ls-tree` 兜底）；分配 `seq` = 现有最大号 +1，目录 `<NN>-<slug>/`
2. 按 [references/change-template.md](references/change-template.md) 写入 `change.md`（`status: draft`）
3. **探针对齐**：对话里亮出 §1 + §2（不甩文件路径让用户通读；要细节再展开）——探针的成功标准是**尽快暴露分歧**，不是通过评审。用户否 → 就地改再亮一次
4. **用户确认后 skill 自动置 `status: confirmed`**；来源是 backlog 卡的按 [../eo-backlog/SKILL.md](../eo-backlog/SKILL.md) archive 动作归档该卡（adopted + 关联本 change-id）。流转期零投影动作——看板 draft 卡在首次 `eo-sync run` 时出现

### 第九步：更新索引 + 提示后续

更新 `eo-doc/changes/INDEX.md`，顺手对 seq 列查重（重号 → created 晚者让号，机械动作见 conventions.md §2），顺手防蒸发（30 天未动的未归档条目列一行提醒）。后续提示按信号扫描结果：

> change 已就绪（confirmed）。
> - 信号：未命中 / 命中 <信号> → 建议先跑 </eo-change-review 等>（说「跳过」即豁免，记 §6）
> - 下一步：`/eo-implement <change-path>`

## 回炉子流程（方案实质修订）

回炉 ≠ 修 bug——是「方案本身要改」。前提：status 为 `implementing`（`reviewed` 的先按回退边置回，见 conventions.md §3）。

1. **边界检查**：先过 granularity.md §3 更新 vs 新开决策表——意图本质变化 / 与原范围重叠 <50% / 原 change 可独立收尾 → **新开 change**，不回炉
2. **status → `draft`**，修订 §1-§5（含已钉决策的重钉）
3. **勾选失效处理**：新旧 AC 逐条映射——语义不变的保留勾选注「回炉前完成」；语义受影响的取消勾选注「回炉待复验」；人工项按 [../eo-shared/acceptance.md](../eo-shared/acceptance.md)「失效与重置」处理
4. **报告作废**：已存在的 test.md / review.md / change-review.md 结论随方案作废——在文件顶部加一行 `> 方案回炉（<日期>），本报告结论作废`；下次调用对应闸门时覆盖重写
5. **索引**：INDEX 行状态回 draft
6. **确认收口**：交用户重新确认 → `status: confirmed`，然后回 /eo-implement 从首个未勾 Batch 续走

**回炉与就地精化的边界**：措辞微调、意图不变的就地补 AC（implement 流程内确认后补写）不算回炉——不回 draft、不动勾选、不走本子流程。

## changes/INDEX.md 模板

```markdown
# 变更时间线

| # | change | 类型 | 状态 | 日期 | 摘要 |
|---|--------|------|------|------|------|
| 14 | [batch-export](14-batch-export/change.md) | feature | confirmed | YYYY-MM-DD | 一句话（= frontmatter summary） |
```

存量 INDEX 含「档」列→ 首次更新时顺手整表去掉该列，各行的档值不保留。

## 关键约束

- **AC 先于 TODO**；每条 TODO 必须映射到 AC
- **四问是骨架**：§1-§4 必填且用户口吻；§5 技术备注不抢主角；确认时亮 §1+§2
- **并行组只标互不干扰**（判据见 granularity.md §6）：判不准不标，串行是安全缺省
- **粒度硬上限拒绝确认**（数值见 granularity.md §1）
- **风险信号必播报**：命中/未命中与理由都在确认时说清；豁免记 §6
- **回炉只走回炉子流程**：先过更新 vs 新开边界；勾选失效逐条处理
- **无 `fix` 类型**；bug 走 /eo-fix
- **status 由 skill 流转**（见 [../eo-shared/conventions.md](../eo-shared/conventions.md)），用户不手改
- **change 阶段不写代码**；归档不反写（change 目录冻结为审计历史）
