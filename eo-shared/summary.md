# 摘要契约（跨阶段共享语义）

> 目标：change 的验收导向摘要一处产出、两处渲染——写进 change.md frontmatter，渲染到 eo-loop 窗口汇报与看板。

## 与 summary 的分工

`summary` 是一句话意图（≤50 字），changes/INDEX 摘要列与看板卡面的单一来源；`brief` 是验收导向摘要，供用户据此判断「做完了什么、去哪验」。两者各司其职，不互相改写。

## brief 字段

change.md frontmatter 的 `brief`：≤3 句，面向非技术读者，依次回答三问——

1. **做了什么**：用户可见的变化，不写技术实现
2. **在哪能看到**：入口、页面或命令
3. **怎么验收**：对照 §2 AC 的走查路径

写不出时宁缺毋滥——留空（`brief: ~`），不凑字、不抄 summary。

## 生产时机

| 节点 | 动作 |
|------|------|
| eo-implement | 批末自验后更新 |
| eo-fix | 收尾记账时顺带更新（有相关活跃 change 时） |
| eo-archive | 归档前校对「brief 与最终交付一致」，不符就地改写 |

## 消费方

- **eo-loop 窗口汇报首段**：观测点（节点边界）原样引用 brief；总控只引用，不代写、不改写
- **看板**：详情概览对 change.md frontmatter 全键透传，brief 随字段自动显示
