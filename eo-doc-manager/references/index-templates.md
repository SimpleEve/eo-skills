# INDEX.md 模板

`eo-doc/` 下**无顶级 INDEX.md**（CLAUDE.md 里的目录表即是一级索引）；每个子目录各自维护自己的 INDEX.md 作为二级索引。

## 目录级 INDEX.md

```markdown
# [分类名] Index

> Last updated: YYYY-MM-DD
> Total: N docs

| File | Title | Tags | Updated | Summary |
|------|-------|------|---------|---------|
| [filename.md](filename.md) | 标题 | `tag1` `tag2` | YYYY-MM-DD | 一句摘要 |
```

> 重构后 `eo-doc/` 仅保留 `agent-handbook/` / `state/` / `dev/` / `templates/`，统一使用上面的标准列。已无需 `impl_coverage` 特殊列（design/ 已迁出 eo-doc/）。

## 分组式 INDEX（10+ 篇时使用）

```markdown
# [分类名] Index

> Last updated: YYYY-MM-DD
> Total: N docs

## [子分类 A]

| File | Title | Tags | Updated | Summary |
|------|-------|------|---------|---------|
| [file1.md](file1.md) | 标题 | `tag` | YYYY-MM-DD | 摘要 |

## [子分类 B]

| File | Title | Tags | Updated | Summary |
|------|-------|------|---------|---------|
| [file2.md](file2.md) | 标题 | `tag` | YYYY-MM-DD | 摘要 |

## 已归档

| File | Title | Archived | Replacement |
|------|-------|----------|-------------|
| [old.md](old.md) | 旧版本 | YYYY-MM-DD | [new.md](new.md) |
```

## 维护规则

- 每次新增/修改/归档文档后，**同步更新受影响目录的 INDEX.md**
- 摘要列与文档 frontmatter 的 `summary` 字段保持一致
- 标签列与 frontmatter 的 `tags` 字段保持一致
- 按 `updated` 倒序排列（最近更新的在前）
- 单条目约 50 token，整个 INDEX 可一次性扫描
