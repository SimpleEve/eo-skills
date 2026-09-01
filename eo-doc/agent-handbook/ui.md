# 看板 UI 规范（Design Token 与原子组件）

看板 UI 由 `cli/eo-board` 单文件渲染（Python 零依赖，无构建、无外部资源）。项目板样式在 `PROJECT_CSS`，聚合首页样式在 `ALL_HTML_TEMPLATE` 内联 `<style id="aggStyle">`；两处的 `:root` 变量同值、手工同步。渲染层全貌见 `cli/eo-board`。

## 色彩 Token（light / dark 双套）

- 主题随 `prefers-color-scheme`；`:root[data-theme="light|dark"]` 是手动覆写入口（无 JS 切换器）
- 用色一律 `var(--*)` 引用；状态色成对：`--st-<状态>` 实色（文字/描边/圆点）+ `--st-<状态>-soft` 浅底

基础色：

| 变量 | light | dark | 用途 |
|------|-------|------|------|
| `--bg` | `#F2F4F7` | `#10141B` | 页面背景 |
| `--surface` | `#FFFFFF` | `#171C25` | 卡片/抽屉/浮层主面 |
| `--surface2` | `#F7F9FB` | `#1D2330` | 次级填充：tag 底、hover、信息格 |
| `--ink` | `#1B2432` | `#E6EAF1` | 主文字 |
| `--muted` | `#647084` | `#93A0B4` | 次级文字 |
| `--faint` | `#8B96A8` | `#6E7A8E` | 弱化文字与图标 |
| `--line` | `#E2E6ED` | `#242B38` | 描边与分隔线 |
| `--accent` | `#B4530A` | `#E08A3C` | 强调：链接、hover 描边、focus ring |
| `--accent-soft` | `#F6E8DC` | `#3A2717` | 强调浅底：定位圈、搜索 mark |
| `--warn` / `--warn-soft` | `#B0451E` / `#F9E9E2` | `#E37D53` / `#3A2018` | 警示（停滞/卡点/横幅）实色 + 浅底 |
| `--src-bg` | `#FBF4EC` | `#2A2118` | 数据来源标注底色（仅项目板） |
| `--shadow` | `0 12px 40px rgba(15,25,45,.18)` | `0 12px 40px rgba(0,0,0,.5)` | 浮层投影（仅项目板：抽屉/下拉/搜索面板） |

状态色 `--st-*`（实色 / 浅底）：

| 变量 | light | dark | 语义 |
|------|-------|------|------|
| `--st-backlog`(-soft) | `#4E7A5A` / `#E7F0E9` | `#7FAF8C` / `#1D2B22` | 待办池 |
| `--st-draft`(-soft) | `#6B7A90` / `#ECEFF4` | `#97A6BC` / `#222938` | 草稿 |
| `--st-confirmed`(-soft) | `#A87508` / `#F7EEDA` | `#D9A83E` / `#33290F` | 已确认 |
| `--st-implementing`(-soft) | `#2563B0` / `#E4EEF9` | `#6CA5E8` / `#1A2A40` | 实施中 |
| `--st-reviewed`(-soft) | `#0E8A74` / `#E0F2EE` | `#4CBFA6` / `#12312A` | 审查通过（兼表「完成/通过」） |
| `--st-archived`(-soft) | `#8A93A1` / `#EEF0F3` | `#7C8798` / `#20262F` | 已归档（兼表「静默」） |

JS 侧 `STATUS` 表把六状态绑到对应 cssVar，是「状态 → 颜色」的唯一映射。

## 字体 / 字号 / 圆角 / 间距 / 动效

- 字体栈有变量：`--sans` 正文（系统栈），`--mono` 一切编号、元信息、按钮小字
- 字号无变量：body 14.5px/1.55；组件内 10–22.5px 硬编码但分档稳定（卡题 14、抽屉题 17.5、统计数 22.5、tag/chip 10.5–11.5）
- 圆角无变量但全局一致：3–4px 小件（chip/tag/code）、6px 信息盒、8px 卡片与面板、12px 搜索面板、999px 胶囊
- 间距无变量：flex/grid gap 硬编码（卡间 10、列间 14、卡内 padding 11px 13px 12px）
- 局部变量模式：组件留缺口（`--col-color` 列色、`--bar-color` 进度条色），调用方行内 style 注入
- 动效 0.15–0.22s ease，均配 `prefers-reduced-motion` 兜底；断点仅聚合页列表（1023/799/479px）

## 原子组件（项目板）

| 组件 | class / 渲染函数 | 用法约束 |
|------|------------------|----------|
| 状态列 | `.col` + `--col-color` · `buildBoard()` | 列头 2px 描边吃 `--col-color`；`.collapsed` 竖排折叠 |
| change 卡 | `.card` · `changeCard()` | 整卡 `role="button"` 可点；`.dim` 归档淡显、`.card-warn` 质量门警示 |
| backlog 卡 | `.card` + `.bl-*` · `backlogCard()` | 与 change 卡同壳，内部件不同 |
| 状态胶囊 | `.st-pill` · `stPill()` | 上色唯一通道：`--st-X-soft` 底 + `--st-X` 字，行内 var() 注入 |
| chip | `.chip` | 顶栏元信息键值（key + `<b>` 值）；`.serve-live` 表自动刷新中 |
| 徽标 tag | `.tag` | 卡脚事实标记；变体 `.ok/.warn/.lock/.branch/.stage` 全走状态色对 |
| 粒度标 | `.tier.full` / `.tier.light` | full 用 implementing 色对，light 仅素描边 |
| 进度条 | `.prog-row > .bar` | 颜色经 `--bar-color` 行内注入，缺省 `--st-implementing` |
| 详情抽屉 | `.drawer` + `.backdrop` · `openDetail()` | fixed 右滑入，宽 `min(920px, 94vw)` |
| 抽屉页签 | `.detail-tab` / `.detail-pane` · `bindDetailTabs()` | active 态 accent 底线 |
| 自绘下拉 | `.project-switch-*` · `bindProjectSwitcher()` | combobox/listbox/option 全套 aria，勿换原生 select |
| 定位搜索 | `.search-backdrop` / `.search-panel` · `openSearch()` | ⌘K 或 / 唤起；命中高亮用 `mark` + accent 色对 |
| 统计条 | `.stat` | 数字一律 mono + tabular-nums |
| 警示横幅 | `.warn-banner` | 页级警示唯一形式（无 toast 组件） |
| 来源标注 | `.src` / `.src-toggle` | 默认隐藏，`.show-src` 总开关；三档徽标 `.badge.a/.b/.c` 固定 reviewed/implementing/warn 色 |
| markdown 容器 | `.md-block` | 详情正文统一容器，内部 h/p/ul/code/table 样式已定义 |
| 勾选清单 | `.cklist` / `.ck` | AC 项；done 态用 reviewed 实色 |

聚合首页复用同一组变量与 `.pill`；自有件 `.proj` 项目卡、`.row` change 行、`.viewswitch`、`.count`（`.pill` 另有 `.live/.quiet/.unreg` 变体），口径与上表一致。

## 规范

1. 新 UI 先查上两节：能复用既有变量与组件类就不写新样式。
2. 新增颜色先进变量：`PROJECT_CSS` 与 `aggStyle` 两套 `:root`（各含媒体查询与 data-theme，共四份）同值同步；禁写死色值。
3. 状态相关着色只走 `--st-*` 实色 + `-soft` 浅底，成对新增并在 `STATUS` 表登记映射。
4. 组件需要配色缺口时按 `--col-color` / `--bar-color` 模式加局部变量行内注入，不改组件类本身。
5. 保持零依赖：不引外部 CSS/JS 框架与字体文件；新动效必须配 `prefers-reduced-motion` 兜底。

**何时读**：动看板样式、新增看板组件或颜色前。
