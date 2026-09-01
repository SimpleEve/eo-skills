# Commit 规范

单一来源：eo-shared/conventions.md §2.5。以下含本仓 git log 的观察归纳。

## 成文前缀（conventions.md §2.5）

| 场景 | 前缀 | 例 |
|------|------|-----|
| change 相关提交（测试锁定 / implement 批次 / archive 结算） | `[<slug>]` | `[board-fork-collapse] 同 id 折叠单卡` |
| 直改：bug 小修 | `fix:` | `fix: 统一看板 review 未决计数` |
| 直改：UI / 样式 / 文案 | `ui:` | `ui: 顶栏新增可见搜索入口` |

- 正文中文短句，一句话说清改了什么
- seq 绝不进 commit message；slug 随首个 commit 落地后不改名
- 前缀不因活跃 change 改向：trivial 直改仍走 `fix:` / `ui:`

## 观察到但未入表的前缀

- `doc sync：<说明>（区间锚点）`：文档同步提交
- `doc <说明>`：文档类直改

**何时读**：每次提交前选前缀。
