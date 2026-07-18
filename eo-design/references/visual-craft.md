# 视觉工艺手册：正向规则 + 黑名单 + 自检门

> eo-design 各模式生成 HTML 前后使用。核心标准：**「人类设计师会不会羞于在这上面署名？」**——会，就重做。只有黑名单救不了平庸：先按正向规则立观点，再用黑名单兜底。

## 0. 治疗强度分诊（动手前先判）

页面唯一任务是「完成操作」还是「留下印象」？

- **utilitarian**（工具界面 / dashboard / 表单 / 文档）：打磨层级、密度与可扫读性——摘要先于细节、状态用颜色+形态双编码（pill/徽标/severity 条）、可交互的看起来可交互；**不上浮夸 hero、不堆装饰**
- **editorial**（落地页 / 营销页 / 展示页）：必须有强观点，按 §1 承诺方向
- DESIGN.md 的「装饰级别」已定档时按它执行

## 1. 方向承诺（editorial 页面 / init 提案 / 每个变体）

- **先承诺一个说得出名字的方向**再动手（极简冷峻 / 杂志编辑感 / 复古未来 / 工业感 / art deco / 柔和粉彩 / brutalist / 奢侈品排版…），之后所有决策服务于它
- **Signature**：一句话写下「这一版靠什么被记住」（init 模式即 memorable-thing 的视觉兑现）
- init 提案的方向承诺作用于品牌/系统层；具体页面强度仍按 §0 分诊——utilitarian surface 的 Signature 允许是「信息效率 / 可信度」，不强求视觉高峰
- **胆量花在一个地方**：一处做到最猛（一个夸张的标题字号 / 一块出格的色面 / 一种非常规布局），其余全部压安静；到处都猛 = 到处都不猛
- 交付前**摘掉一件首饰**：删一个不服务 Signature 的装饰
- 强度靠 intentionality 不靠 intensity：说不出理由的效果不加

## 2. 字体

- 按角色配 2-3 款（≤3）：Display（克制用于大标题）+ Body + 可选 Data/Code
- Display 候选：Fraunces / Instrument Serif / Satoshi / General Sans / Clash Grotesk / Bricolage Grotesque
- Body 候选：Instrument Sans / DM Sans / Geist / Plus Jakarta Sans / Source Sans 3 / Outfit
- Data/Code 候选：JetBrains Mono / IBM Plex Mono / Geist Mono
- **CJK 分支**（中文为主的项目）：Display 候选：思源宋体 Noto Serif SC / 霞鹜文楷 LXGW WenKai；Body 候选：思源黑体 Noto Sans SC / MiSans / HarmonyOS Sans SC；中西混排 fallback 链西文在前、CJK 在后；CJK 字重档位少，禁伪粗体（faux bold）
- **收敛陷阱**（未经 DESIGN.md 明确选择不用）：Inter / Roboto / Arial / Helvetica / Open Sans / Lato / Montserrat / Poppins / **Space Grotesk**（它正是「Inter 的安全替代」这个陷阱本身）；`system-ui` 当主字体 = 放弃排版的信号
- 排印硬数字：type scale 比例 1.25 或 1.333；正文行高 1.5×、标题 1.15-1.25×；每行 45-75 字符（拉丁）/ 22-38 汉字（CJK）；正文 ≥16px、caption ≥12px；≥2 个字重；数字列 `tabular-nums`（大号 hero 数字除外，用比例字形）；标题 `text-wrap: balance`；全大写标签加 letter-spacing、拉丁小写不加（CJK 正文可加 0.02-0.05em）

## 3. 颜色

- **命名色板**：4-6 个 base 色各起名字（说不出名字 = 没想清楚职责）；中性阶 / 语义色 / 暗色映射是派生 token，不计入 4-6 但同样须具名
- 一个主导色 + 一处锐利强调；均匀用力的胆怯色板不如「主导 + 锐利」
- 中性灰**带一点主色色相**：纯中灰读起来像没考虑过，偏色相的灰读起来像选过
- 硬数字：非灰色 ≤12；正文对比 ≥4.5:1、大字 ≥3:1
- 暗色模式：表面用 elevation 分层（越浮越亮）而非简单反明度；正文近白（约 #E0E0E0）非纯白；主色去饱和 10-20%；与亮色模式同等用心
- 语义色（success/warn/error）独立于强调色；不得只靠红绿区分状态

## 4. 布局与间距

- 间距走刻度（4/8px 基准，如 2/4/8/16/24/32/48/64），禁刻度外魔法数
- flex/grid + `gap` 排版，不用逐元素 margin 堆间距
- 嵌套圆角：内 radius = 外 radius − 间隙
- 宽内容（表格/代码块/图）各自 `overflow-x: auto`，body 永不横向滚动
- 全居中是默认款；不对称、重叠、打破网格是观点（editorial 下优先考虑）

## 5. 动效

- 一次编排好的入场（staggered `animation-delay`）胜过零散微交互
- 多余动画会强化「AI 生成感」；尊重 `prefers-reduced-motion`
- 预览页只用纯 CSS 动效

## 6. 文案即设计材料

- 真实内容：产品真实文案/数据；禁 lorem ipsum、禁 "Item 1/2/3" 式占位
- 站在用户侧命名（「通知」不是「webhook 配置」）；按钮说清会发生什么；错误信息 = 哪儿错了 + 怎么修
- 编号（01/02/03）、eyebrow、分割线这类结构装置只在内容真是序列/分层时用

## 7. 设计计划（apply 硬门，按档位）

写代码前先列，列完对照 brief 复审：

1. **整页 / 新 surface**：命名色板（4-6 base 各带名）｜分角色字体｜布局概念 1-2 句｜Signature 一句｜editorial 页面另加一句 asset 策略（真实产品图 / 插画 / 纯排版，选哪个、为什么）
2. **组件级小改**：只列受影响 token + 状态差异；结论可以是「无自由视觉维度」，此时跳过第 3 条
3. **通用默认检查**：凡「给任意同类页面都会这么写」的部分，改掉并记一句改了什么
4. token 与 DESIGN.md 冲突时 DESIGN.md 赢（偏离须批准 + 记 Decisions Log）

## 8. 预览页质量（init / variants 的 HTML）

- **预览页本身必须漂亮**——它是本技能品味的信号。排版、留白、层级不敷衍
- 自包含：CSS/JS 内联；候选字体可用字体服务 `<link>` 加载并给系统栈兜底
- 明暗模式切换（顶部小开关即可）；三视口不破版（移动 375 / 平板 768 / 桌面 1280）
- 对比索引页：多变体时给一张并排入口页，每个变体标注概念名 + 一句定位

## 9. 反趋同（variants 的文字概念阶段）

**失败判据：两个变体互换标题文案后没人察觉差别，就是同一方案的三种浓度，不是三个方案。**

- 每个变体各自过 §1 方向承诺——三个变体 = 三个说得出名字的方向
- 变体间至少在两个系统维度上分道（布局范式 / 密度 / 色彩策略 / 字体气质 / 装饰级别），不是只换主色
- 已有 DESIGN.md 时，分道范围受 variants 性质声明约束：系统内探索只动未锁维度；要动已锁 token = 系统变更实验，须显式声明并经批准才可沉淀
- 每个概念写清：一句定位 + 它赌的是什么（哪类用户/场景会明显更爱它）+ 放弃了什么
- 像三个不同设计团队交稿，而不是同一团队的保守/标准/激进档

## 10. AI slop 黑名单（所有交付前自检）

出现即重做。**豁免条款：用户点名要或 DESIGN.md 明确选择的照做——用户原话永远赢；只是自由维度不花在默认款上**：

- 紫色系渐变按钮/头图（白底紫→蓝渐变 hero 是重灾区）、玻璃拟态滥用
- 「三列卡片 + 彩圈图标 + 粗标题 + 两行描述」特性网格——最易识别的 AI 布局
- 暖奶油底（#F4F1EA 系）+ 衬线大标题 + 赤陶强调；近黑底 + 一抹酸绿/朱红——两套「AI 高级感」预制菜
- 默认 Inter/Roboto/Space Grotesk 全场通吃且无字号层级设计
- emoji 当图标/分节符铺满界面；每个卡片都圆角+阴影+渐变边框；圆角卡片加强调色竖条
- 空洞营销词填充（"Powerful. Simple. Fast."）代替真实产品信息
- 什么都居中；到处同一号大圆角
- 深色模式 = 纯黑底 + 原色不调整
- 动效堆砌：入场全体 fade-in-up、hover 全体放大
- 结构装置（编号/eyebrow）用在非序列内容上

## 11. 交付前核对

- [ ] 治疗强度判对（utilitarian 没过度设计 / editorial 有 Signature）
- [ ] token 全部来自 DESIGN.md（或已批准偏离并记 Decisions Log；无 DESIGN.md 场景：已显式声明「仅当次有效、未沉淀」）
- [ ] 排印/颜色硬数字过（行宽 45-75 字符 / 22-38 汉字、正文 ≥16px、对比 ≥4.5:1）
- [ ] 三视口截图无破版、无横向滚动；明暗两模式都过目
- [ ] 交互/可达性：键盘焦点可见、触达目标 ≥44px、disabled/loading/empty/error 状态齐全（utilitarian 必查）
- [ ] 黑名单逐条扫过；摘掉了一件首饰
- [ ] 「羞于署名」自问通过
