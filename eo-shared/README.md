# eo-shared — 共享规范（非 skill）

本目录**不是可触发的 skill**，是 eo-* 各 skill 引用的单一来源规范。带 SKILL.md 仅为让 skills CLI（`npx skills add`）把它随整套 skill 一起分发（skills CLI 只装带 SKILL.md 的目录，缺了它 `../eo-shared/` 引用会断链）；agent 侧请勿把它当独立 skill 触发。**必须整套安装**——单独拷贝某个 skill 目录会使其 `../eo-shared/` 引用断链。

| 文件 | 内容 | 主要消费方 |
|------|------|-----------|
| [questioning.md](questioning.md) | 提问纪律（预算、决策台账、封闭选择协议、反模式表） | eo-change / eo-brainstorming / eo-design |
| [goal-contract.md](goal-contract.md) | 七维目标契约的跨阶段语义、Proof 分层、Trade 优先级与 Unknown 权限 | eo-brainstorming / eo-loop |
| [ac-spec.md](ac-spec.md) | 验收清单（AC）规范：三级验证归属、重验证的环境纪律 | eo-change / eo-implement / eo-test / eo-review / eo-fix |
| [acceptance.md](acceptance.md) | 人工验收单：模板、软前门/唯一硬门生命周期、引导走查 | eo-implement（产）/ eo-review（提示）/ eo-archive（硬门） |
| [evidence.md](evidence.md) | 交付证据面：三段模板、类型预设与项目扩展、截图纪律、刷新与失效 | eo-implement（产）/ eo-fix（刷新）/ eo-archive（硬门+渲染）/ eo-loop（收尾渲染） |
| [reply-contract.md](reply-contract.md) | 长任务收尾回复契约（四条）单一来源与双生效通道 | eo-archive / eo-loop（硬步骤）/ eo-project-init（注入段） |
| [summary.md](summary.md) | 摘要契约：brief 字段写法（≤3 句三问）、生产时机与消费方、与 summary 的分工 | eo-implement / eo-fix（产）/ eo-archive（校）/ eo-loop（消费） |
| [granularity.md](granularity.md) | 粒度硬指标、trivial 判据、拆分决策表、风险信号清单（§5） | eo-change / eo-fix / eo-change-review / eo-brainstorming / eo-implement |
| [conventions.md](conventions.md) | 横切约定：tmp/eo/、commit 前缀、状态流转 | 主链各 skill |
| [board-github.md](board-github.md) | eo-sync 内置 Obsidian/GitHub 适配器的投影内容实现说明（opt-in） | eo-sync 内置适配器 / eo-archive 收口 / eo-project-init |
| [research.md](research.md) | 调研沉淀的格式、INDEX 与消费规则 | 任意调研产出方（产）/ eo-recall / eo-change（消费） |
| [lessons.md](lessons.md) | lessons 生产格式（结论前置 + trigger/summary 锚点）与消费流程（INDEX 匹配） | eo-project-record（产）/ eo-change / eo-implement / eo-test / eo-fix（消费） |

各 skill 以相对路径引用（`../eo-shared/<file>`，相对 skill 自身目录，软链与仓库内均可解析）。

**维护规则**：口径修改只改这里，禁止在任何 skill 内复制正文（v1 教训：「分段读 spec」规程复制进 3 个 skill 各自漂移）。上表「主要消费方」列仅供导览——**以各 skill 正文的实际引用为准**，此类反向名单不作同步维护承诺（供给方文件里不要再新建「被谁引用」清单）。
