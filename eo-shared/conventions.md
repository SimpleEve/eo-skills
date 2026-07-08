# 横切约定（单一来源）

> 被全部 eo-* skill 引用：tmp 工件命名空间、commit 前缀、状态自动流转。

## 1. tmp 工件命名空间：tmp/eo/

所有 skill 的临时产物收进统一命名空间（项目仓库内 `tmp/eo/`，按域分子目录）：

```
tmp/eo/
├── handoff/<topic>.md          # 会话交接快照（eo-handoff）
├── fix/<date>-<slug>.md        # 深挖模式调查记录（eo-fix）
├── design/<date>-<topic>/      # 设计变体与预览 HTML（eo-design）
└── explain/<date>-<topic>.html # 一次性解释页（eo-recall）
```

纪律：

- **一切可丢弃**：任何 skill 不得把 tmp/eo/ 当信源引用。有长期价值的结论在产生时即沉淀到正式位置——根因 → change / lessons；design 选中结论 → DESIGN.md 决策日志；handoff 被下个会话消费后即弃。
- `tmp/eo/` 由 eo-project-init 写入 .gitignore。
- 文件名带日期或 topic 前缀；清理按 mtime，无登记表。`rm -rf tmp/eo` 即全量清理。

## 2. commit 前缀

| 场景 | 前缀 | 示例 |
|------|------|------|
| change 相关提交（implement 批次、archive 结算/meta） | `[<change-id>]` | `[014] 导出模块 Batch 1` |
| 直改模式：bug 小修 | `fix:` | `fix: 修正导出文件名日期格式` |
| 直改模式：UI/样式/文案 | `ui:` | `ui: 调整卡片间距` |

change-id 前缀是 eo-archive 归集 commit 区间的依据；`fix:`/`ui:` 前缀供 retro 统计直改流量。推荐「一次 change 一次 commit」；TODO 分批时允许一批一 commit，archive 至多补一个收尾 meta commit。

## 3. 状态自动流转

change 的 `status` 由 skill 在对话确认后自动写入，**用户永远不手改 frontmatter**：

```
draft ──(eo-change：用户对话确认)──▶ confirmed
      ──(eo-implement：首次执行)──▶ implementing
      ──(eo-review 通过)──▶ done
      ──(eo-archive：完成归档)──▶ archived（不可逆）
```

用户的确认动作发生在对话里（回复确认 / AskUserQuestion 选择），skill 负责落盘。
