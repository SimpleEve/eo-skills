# Agent Handbook — 项目操作手册

规范性、方向性：细节判断交运行时；非 SSOT（代码为准）；不挂自动同步。
先扫本表定位篇目，按需读，不通读。

| 篇目 | 一句话 | 何时读 |
|------|--------|--------|
| [worktree.md](worktree.md) | 多 worktree 并行：看板折叠/分叉口径 + codegraph 索引按目录隔离 | 开 worktree 并行开发前；看板出现分叉徽标时 |
| [commit.md](commit.md) | commit 前缀：`[<slug>]` / `fix:` / `ui:` + 观察到的 doc 系前缀 | 每次提交前选前缀 |
| [comments.md](comments.md) | 注释纪律：代码为真相源、顺手清理过时注释 | 编辑任何代码前 |
| [directory.md](directory.md) | 仓内顶层目录职责边界与入库口径 | 新文件不知道放哪、判断该不该入库时 |
| [architecture.md](architecture.md) | skill / eo-shared / cli 三层分工 + SKILL 写作纪律 | 改 skill 或 eo-shared 前 |
| [ui.md](ui.md) | 看板 UI：Design Token（light/dark 双套 CSS 变量 + `--st-*` 状态色）与原子组件清单 | 动看板样式、新增组件或颜色前 |

## 待补

- lint 规范：待补（本仓无 lint 配置）
