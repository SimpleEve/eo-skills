# 目录职责边界

| 路径 | 职责 | 入库 |
|------|------|------|
| `eo-*/SKILL.md` | 产品本体：各 skill 的 prompt 定义，自描述 | 是 |
| `eo-shared/` | 跨 skill 口径单一来源（非 skill，无 SKILL.md） | 是 |
| `cli/` | 可执行层：eo-board / eo-helper / eo-sync + 适配器 + eo_lib | 是 |
| `tests/` | unittest 套件（零第三方依赖）；`*_caliber.py` 是文档口径静态断言 | 是 |
| `docs/` | 设计稿与使用指南（GUIDE / v*-design / cli-reference / 协议） | 是 |
| `research/` | 仓内调研（产品方向，带 INDEX.md） | 是 |
| `eo-doc/` | 代码侧文档体系（changes / state / agent-handbook / templates） | 是 |
| `tmp/eo/` | 运行时工件 | 否，可随时 `rm -rf` |
| `tasks/` | 会话级草稿 | 否 |
| `.codegraph/` | codegraph 索引 | 否 |

- 管理侧（roadmap / backlog / decisions / lessons / brainstorm / 管理侧 research）不在仓内：在 `.eo-project.json` 的 `project_root`（本仓为 Obsidian vault，经 `eo-doc/vault` 软链访问）
- 测试跑法：`python3 -m unittest discover -s tests`

**何时读**：新文件不知道放哪、或判断某内容该不该入库时。
