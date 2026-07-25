# Agent Handbook — 代码地图索引

> 先扫本 INDEX 定位模块，再按需读具体模块详情，不要通读。

| 模块 | 入口 | 一句话 |
|------|------|--------|
| [cli-eo-lib.md](cli-eo-lib.md) | `cli/eo_lib/` | 五域共享解析库（配置+local 合并/git/frontmatter/change 扫描/freshness 键），ConfigError 错误所有权，eo-board 与未来 eo-sync 共用 |
| [cli-eo-sync.md](cli-eo-sync.md) | `cli/eo-sync*` | 投影同步核+双内置适配器：协议 v1、持锁编排、fail-safe 孤儿删除、identity_fields 保序回写 |
| [cli-eo-board.md](cli-eo-board.md) | `cli/eo-board` | 零依赖单文件只读看板，三形态（终端/--html/--serve），serve 每项目单飞缓存 |

> 本仓库的「产品本体」是各 `eo-*/SKILL.md`（自描述，不入 handbook）；handbook 只覆盖可执行代码（`cli/`、`tests/`、`install.sh`）。
