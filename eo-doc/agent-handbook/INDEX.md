# Agent Handbook — 代码地图索引

> 先扫本 INDEX 定位模块，再按需读具体模块详情，不要通读。

| 模块 | 入口 | 一句话 |
|------|------|--------|
| [cli-eo-lib.md](cli-eo-lib.md) | `cli/eo_lib/` | 五域共享解析库（配置+local 合并/git/frontmatter/change 扫描/freshness 键 + 公开 tree_max_mtime），ConfigError 错误所有权，eo-board 与未来 eo-sync 共用 |
| [cli-eo-sync.md](cli-eo-sync.md) | `cli/eo-sync*` | 投影同步核+双内置适配器：协议 v1、持锁编排、fail-safe 孤儿删除、identity_fields 保序回写 |
| [cli-eo-helper.md](cli-eo-helper.md) | `cli/eo-helper` | 数字菜单薄壳唯一入口：固定 argv 映射选前回显、短命令 subprocess 回菜单、serve/watch os.exec 接管、非 TTY 对照表退出 |
| [cli-eo-board.md](cli-eo-board.md) | `cli/eo-board` | 零依赖单文件只读看板，三形态（终端/--html/--serve），serve 每项目单飞缓存；聚合页双视图 + route_key 下钻路由，泳道页资产 serve 与快照共用一套 |

> 本仓库的「产品本体」是各 `eo-*/SKILL.md`（自描述，不入 handbook）；handbook 只覆盖可执行代码（`cli/`、`tests/`、`install.sh`）。
>
> 不挂模块的测试：`tests/test_sot_default_caliber.py` 是 SoT 默认口径（init 缺省推荐 local + 管理侧随仓库提交）的文档静态断言套件，守护 `eo-project-init/SKILL.md`、`references/config.md`、`docs/GUIDE.md`、`README.md` 四文件口径一致。`tests/test_sync_consolidation_caliber.py` 同型，守护 sync 段收编口径（init 停写 board/github 旧段、1.5 迁移、文档 legacy 标注）于 `eo-project-init/SKILL.md`、`references/config.md`、`eo-shared/board-github.md`、`docs/GUIDE.md`，并断言本仓 `.eo-project.json` 狗粮迁移等价与 change 区间 `cli/` 零 diff。
