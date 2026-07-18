---
name: eo-design
description: |
  项目设计能力，真相源为仓库根 DESIGN.md。触发：定设计系统 / 出几版视觉方案对比 / 做高保真页面 / 设计审计 / 配色 / 字体 / design / /eo-design。
  NOT FOR: 具体功能的变更起草（走 /eo-change）；纯文案修改。
---

# eo-design — 设计系统与高保真预览

以仓库根 `DESIGN.md` 为**项目级设计真相源**的四模式技能。姿态是**设计顾问，不是表单向导**：主动提出完整连贯的提案让用户挑剔，而不是逐项让用户填空。

## 模式路由

| 模式 | 触发 | 职责 |
|------|------|------|
| `init` | 设计系统 / 从头定设计 / DESIGN.md 不存在时的默认 | 0→1 建立设计系统 → DESIGN.md + 约束注入 |
| `variants` | 出几版看看 / 对比方案 / 某屏幕的视觉发散 | 多变体 HTML 对比 → 结论进 DESIGN.md 决策日志 |
| `apply` | 落地 / 做成页面 / 生产级实现 | 选中方向 → 生产级 HTML/组件 |
| `audit` | 检查设计一致性 / 设计审计 | 实现 vs DESIGN.md 的偏差报告 |

无法判断时问一句。`variants`/`apply`/`audit` 在 DESIGN.md 不存在时提示先跑 `init`（用户可拒绝，则以当次对话约定为准并提示结论不会被沉淀约束）。

## 通用规则（四模式共用）

- **DESIGN.md 优先级最高**：存在即为默认约束，高于任何临时发挥与从 mockup 反推的值；偏离必须经用户批准并记入 Decisions Log
- **上游 brief 握手**：上游材料（brainstorming 记录的「设计 brief」节 / 所服务 change 的 change.md §1）只用于**预填五维**（给谁 / 核心任务 / 现状 / 所处流程 / 边界情况）——已钉项不重问，缺维照常采集；无可读引用（给不出路径）一律按无上游处理；方向说不清 → 按各模式的上下文门槛升级 /eo-brainstorming，不硬着头皮设计
- **预览一律自包含 HTML**：内联全部 CSS/JS、不依赖外部服务；候选字体可用字体服务 link 标签加载。质量要求见 [references/visual-craft.md](references/visual-craft.md)
- **真实内容**：用产品真实文案/数据渲染，禁 lorem ipsum
- **工件位置**：过程产物 `tmp/eo/design/<date>-<topic>/`（可丢弃，见 [../eo-shared/conventions.md](../eo-shared/conventions.md)）；服务某个 change 的定稿另存 `eo-doc/changes/<id>/design/`
- **提问纪律**：遵循 [../eo-shared/questioning.md](../eo-shared/questioning.md)；封闭选择按其 §4 协议带推荐项

## init — 建立设计系统

1. **预填充（静默）**：读 README / CLAUDE.md / 已有 DESIGN.md / `eo-doc/state/`，能推断的（产品是什么、给谁用、项目类型）不问
2. **一个合并问题**：把预填充结论摆出来让用户确认/纠正，**外加一个必问项**——「你希望用户第一眼记住这个产品的什么？一句话」（memorable-thing：之后所有设计决策服务于它）
3. **上下文门槛（硬性）**：至此「产品是什么 / 给谁用 / memorable-thing / 本次设计边界」仍有 ≥2 项说不清（「说不清」= 既无仓库证据、用户也答不出可执行结论；不适用维度标 N/A 不计入）→ 停止出提案，建议先 /eo-brainstorming 钉方向（其记录的「设计 brief」节回来即预填）；用户拒绝升级 → 当场最小 brief（五维合并问，计入 questioning.md §2 预算），2 轮封顶，未答项按合理默认推进并显式标注「（假设）」
4. **竞品视觉调研（可选）**：用户同意且环境可联网时，搜 3-5 个同类产品提炼品类共识与差异化机会；不可用或用户跳过 → 直接下一步，不阻塞
5. **一次性完整提案（SAFE/RISK 拆分）**：给出覆盖 Aesthetic / Typography / Color / Spacing / Layout / Motion 的连贯系统，每项带一句 rationale；结构为「2-3 个跟随品类惯例的安全选择 + 至少 2 个刻意冒险（各说得失）」，核心问题问「**在哪里冒险**」而不是逐项选菜单
6. **HTML 预览页**：候选字体样张 + 色板 + 组件示例（按钮/卡片/表单/告警）+ 1-2 个用真实内容渲染的页面 mockup + 明暗模式切换，写入 `tmp/eo/design/<date>-init/`，请用户在浏览器确认；反馈迭代（每轮改预览页，不重开）
7. **落地**：按 [references/design-md-template.md](references/design-md-template.md) 写仓库根 `DESIGN.md`（目标 <90 行）；执行同文件中的**约束注入**（CLAUDE.md 的 `<!-- eo-design:start/end -->` 段，幂等替换）
8. 速报：DESIGN.md 路径 + 关键决策一句话清单 + 注入状态

## variants — 多变体发散

1. **建立 brief**：按通用规则的上游握手预填五维（含所服务 change 的相关 state/ 篇目），缺维在 2 轮封顶内补问（可标 N/A）；无上游 → 全量五维采集；连「该做什么屏幕 / 解决什么问题」都未定 → 建议先 /eo-brainstorming
2. **性质声明（已有 DESIGN.md 时必做）**：本轮是「系统内探索」（只在 DESIGN.md 未锁定的维度分道）还是「系统变更实验」（生成前明确列出拟突破的 token）；后者的选中结论须经用户批准偏离后方可沉淀
3. **文字概念先行**：先出 N 个（默认 3）纯文字设计概念让用户筛——**反趋同硬要求**见 visual-craft.md（像三个不同团队的方案，不是同一方案的三种浓度）；一次封闭选择确认要做的概念即生成，不在文字阶段多轮拉锯
4. 逐概念生成自包含 HTML 变体（runtime 支持子 agent 时每变体一个并行生成、各自过 visual-craft.md 自检后回收；失败的重试 1 次，仍败 → 对比页标注缺失项并问用户是否补齐，全部失败 → 报错停止；不支持子 agent 则串行）+ 一张对比索引页（并排 iframe/链接），写入 `tmp/eo/design/<date>-<topic>/`
5. **对比页即选择器**：请用户看页拍板，不得退回口头 A/B/C 描述式问偏好；反馈按「每变体：保留 / 淘汰 / 杂交（注明取哪个维度：布局/配色/字体/密度）」结构化收集，迭代直接改对比页（不重开），直到选定
6. **沉淀（分支硬规则）**：有 DESIGN.md → 选中结论追加 Decisions Log（决策列写「<屏幕>: 选 <概念>（淘汰方向一句带过）」；系统变更实验须已获批准）；无 DESIGN.md（用户拒建）→ **不写任何持久文档**，速报显式声明「结论仅当次有效、未沉淀」；服务 change 的定稿复制到 `eo-doc/changes/<id>/design/`，defer/未选方向记入该 change 的开放问题
7. 速报：选中方向 + 沉淀状态（已入 Decisions Log / 仅当次有效）

## apply — 生产级落地

1. 输入路由：来自 variants 的选中稿 / DESIGN.md 直接驱动 / 用户自由描述
2. **设计计划先行（按档位）**：整页/新 surface → 按 visual-craft.md「设计计划」节全量列出（命名色板 / 分角色字体 / 布局概念 1-2 句 / Signature）；组件级小改 → 只列受影响 token + 状态差异，允许结论「无自由视觉维度」（此时跳过通用默认检查）；列完对照 brief 复审，「给任意同类页面都会这么写」的部分改掉再动手
3. 生成生产级自包含 HTML/组件：DESIGN.md token 优先；语义化结构；响应式；明暗模式；过 visual-craft.md 黑名单与交付前核对后才交付
4. 三种视口宽度自查（移动/平板/桌面），修到无横向滚动、无布局破碎；交互/可达性自查：键盘焦点可见、触达目标 ≥44px、disabled/loading/empty/error 状态齐全（utilitarian 页面必查）
5. 产物位置由用途定：change 相关 → `eo-doc/changes/<id>/design/`；探索性 → `tmp/eo/design/`
6. 速报：产物路径 + 遵循/偏离 DESIGN.md 的说明（偏离需已获批准并记 Decisions Log）

## audit — 一致性审计

1. 对指定页面/组件的实现，从**渲染结果**（截图或运行中的页面）而非源码提取实际使用的字体/色值/间距/圆角
2. 逐项对照 DESIGN.md，产出偏差清单：P0（明显违背，如色板外颜色、字体错用）/ P1（token 不一致，如间距刻度外的魔法数）/ P2（可改进）
3. 只报告不动手；修复建议标注对应 DESIGN.md 条目
4. **对话速报**（硬性，缺速报=流程未完成）：

```
结论：一致 / 偏差 N 项（P0 x / P1 y / P2 z）
P0：1. <一句话> — <位置>
下一步：<修复建议归属：直改（ui:）/ 开 change>
（详单见 <报告路径，写 tmp/eo/design/<date>-audit/report.md>）
```

## 关键约束

- **落盘白名单**：本 skill 的全部写入仅限——仓库根 `DESIGN.md`、agent 配置文件的 `eo-design` 注入段、`tmp/eo/design/`、`eo-doc/changes/<id>/design/`；此外一律不写（含 `.base` 文件与任何其他项目文档）
- **Decisions Log 只追加不改写**（日期｜决策｜理由）
- **联网调研永远可选**，跳过不阻塞任何模式
- 偏离 DESIGN.md = 用户批准 + 记 Decisions Log，两者缺一不可
