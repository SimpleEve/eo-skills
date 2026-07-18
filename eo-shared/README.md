# eo-shared — 共享规范（非 skill）

本目录**不是可触发的 skill**（刻意没有 SKILL.md），是 eo-* 各 skill 引用的单一来源规范。install.sh 按 `eo-*` 通配把它和其他 skill 一起软链到各 agent 的 skills 目录，无 SKILL.md 的目录仅作为文件被引用（已验证 Claude Code 忽略此类目录；Codex / Antigravity 按同规则处理，若某 runtime 异常请反馈）。**必须整套安装**——单独拷贝某个 skill 目录会使其 `../eo-shared/` 引用断链。

| 文件 | 内容 | 主要消费方 |
|------|------|-----------|
| [questioning.md](questioning.md) | 提问纪律（预算、决策台账、封闭选择协议、反模式表） | eo-change / eo-brainstorming / eo-design |
| [ac-spec.md](ac-spec.md) | 验收清单（AC）规范：三级验证归属、重验证的环境纪律 | eo-change / eo-implement / eo-test / eo-review / eo-fix |
| [acceptance.md](acceptance.md) | 人工验收单：模板、软前门/唯一硬门生命周期、引导走查 | eo-implement（产）/ eo-review（提示）/ eo-archive（硬门） |
| [granularity.md](granularity.md) | 粒度硬指标、trivial 判据、拆分决策表 | eo-change / eo-fix / eo-change-review / eo-brainstorming |
| [conventions.md](conventions.md) | 横切约定：tmp/eo/、commit 前缀、状态流转 | 主链各 skill |
| [board-github.md](board-github.md) | 看板 stub 与 GitHub issue/PR 联动（opt-in） | eo-change / eo-implement / eo-review / eo-fix / eo-archive / eo-project-init |
| [research.md](research.md) | 调研沉淀的格式、INDEX 与消费规则 | 任意调研产出方（产）/ eo-recall / eo-change（消费） |
| [lessons.md](lessons.md) | lessons 生产格式（结论前置 + trigger/summary 锚点）与消费流程（INDEX 匹配） | eo-project-record（产）/ eo-change / eo-implement / eo-test / eo-fix（消费） |

各 skill 以相对路径引用（`../eo-shared/<file>`，相对 skill 自身目录，软链与仓库内均可解析）。

**维护规则**：口径修改只改这里，禁止在任何 skill 内复制正文（v1 教训：「分段读 spec」规程复制进 3 个 skill 各自漂移）。上表「主要消费方」列仅供导览——**以各 skill 正文的实际引用为准**，此类反向名单不作同步维护承诺（供给方文件里不要再新建「被谁引用」清单）。
