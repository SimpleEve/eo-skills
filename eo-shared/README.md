# eo-shared — 共享规范（非 skill）

本目录**不是可触发的 skill**（刻意没有 SKILL.md），是 eo-* 各 skill 引用的单一来源规范。install.sh 按 `eo-*` 通配把它和其他 skill 一起软链到各 agent 的 skills 目录，无 SKILL.md 的目录会被 agent 忽略，仅作为文件被引用。

| 文件 | 内容 | 被谁引用 |
|------|------|---------|
| [questioning.md](questioning.md) | 提问纪律（预算、决策台账、反模式表） | eo-change / eo-brainstorming / eo-design |
| [ac-spec.md](ac-spec.md) | 验收清单（AC）规范 | eo-change / eo-test / eo-review / eo-fix |
| [granularity.md](granularity.md) | 粒度硬指标、trivial 判据、拆分决策表 | eo-change / eo-fix / eo-change-review |
| [conventions.md](conventions.md) | 横切约定：tmp/eo/、commit 前缀、状态流转 | 全部 |
| [board-github.md](board-github.md) | 看板 stub 与 GitHub issue/PR 联动（opt-in） | eo-change / eo-implement / eo-review / eo-fix / eo-archive / eo-project-init |

各 skill 以相对路径引用（`../eo-shared/<file>`，相对 skill 自身目录，软链与仓库内均可解析）。

**维护规则**：口径修改只改这里，禁止在任何 skill 内复制正文（v1 教训：「分段读 spec」规程复制进 3 个 skill 各自漂移）。
