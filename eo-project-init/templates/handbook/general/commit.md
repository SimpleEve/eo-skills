# Commit 规范

单一来源：eo-shared/conventions.md §2.5。

## 成文前缀（conventions.md §2.5）

| 场景 | 前缀 | 例 |
|------|------|-----|
| change 相关提交（测试锁定 / implement 批次 / archive 结算） | `[<slug>]` | `[<slug>] <一句话说清改了什么>` |
| 直改：bug 小修 | `fix:` | `fix: <一句话>` |
| 直改：UI / 样式 / 文案 | `ui:` | `ui: <一句话>` |

- 正文中文短句，一句话说清改了什么
- seq 绝不进 commit message；slug 随首个 commit 落地后不改名
- 前缀不因活跃 change 改向：trivial 直改仍走 `fix:` / `ui:`

## 观察到但未入表的前缀

- 待补（从本仓 `git log` 归纳）

**何时读**：每次提交前选前缀。
