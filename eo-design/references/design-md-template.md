# DESIGN.md 模板与约束注入

## DESIGN.md 模板（仓库根，目标 <90 行）

单文件承载「token + rationale + 决策日志」。**不含组件规格**——组件级细节属于实现，DESIGN.md 只钉系统级决策。

```markdown
# DESIGN.md — <项目名> 设计系统

> 本文件是项目设计真相源。任何视觉/UI 决策前先读它；偏离需用户批准并记入 Decisions Log。

## Product Context
- 产品：<一句话> ｜ 用户：<谁> ｜ 类型：<Web 应用 / 工具站 / 营销页…>
- Memorable thing：<用户第一眼要记住的那件事>

## Aesthetic Direction
- 方向名：<如「工程手账」>；装饰级别：<克制/适中/浓郁>；情绪：<3 个形容词>
- 参考：<站点/风格锚点，可选>

## Typography
| 角色 | 字体 | 理由 |
|------|------|------|
| Display | <font> | <一句> |
| Body | <font> | <一句> |
| Code/Data | <font> | <一句> |
- 加载策略：<系统栈 / 字体服务 link>；字号阶梯：<12/14/16/20/24/32px…>

## Color
- 策略：<一句，如「暖中性底 + 单强调色」>
- Primary：`#xxxxxx`；中性阶：`#...` ×N；语义色：success `#` / warn `#` / error `#`
- 暗色模式：<策略一句话>

## Spacing & Layout
- 基准：<4px/8px>；刻度：<4/8/12/16/24/32…>；密度：<紧凑/舒适>
- 网格/最大宽度：<如 1200px 居中>；圆角分级：<2/6/12px 用途>

## Motion
- 策略：<克制，仅状态反馈>；缓动：<ease-out>；时长：<120/200/300ms 分档>

## Decisions Log
| 日期 | 决策 | 理由 |
|------|------|------|
| YYYY-MM-DD | <初始系统确立 / 后续微决策> | <一句> |
```

Decisions Log **只追加不改写**——包括「light 模式强调色用 600 档因为 500 太亮」这类微决策，它们是防止反复横跳的记忆。

## 约束注入（agent 配置文件）

写完/更新 DESIGN.md 后，向项目的 agent 配置文件（CLAUDE.md，探测顺序与 eo-project 注入一致）幂等注入以下段落（`<!-- eo-design:start/end -->` 标记定位，重复执行整段替换）：

```markdown
<!-- eo-design:start -->
## Design System

本项目设计真相源为根目录 [DESIGN.md](DESIGN.md)：

- 任何视觉/UI 决策（新页面、组件、样式调整）**之前必须读 DESIGN.md**
- 不得未经用户批准偏离其 token（字体/色板/间距刻度/圆角/动效）；批准的偏离记入其 Decisions Log
- 发现现有实现不符合 DESIGN.md 时，标记出来（不静默将错就错）
<!-- eo-design:end -->
```

注入流程与验证同 `eo-doc-manager/references/claude-injection.md` 的三场景规则（不存在则创建、无标记则追加、有标记则整段替换）。
