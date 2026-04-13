---
name: eo-archive
description: |
  变更归档技能。将已通过 review 的 change 的 Spec Delta 合并回模块 spec.md，完成变更闭环。

  USE FOR:
  - "归档 change" "archive" "合并 delta" "归档变更" "/eo-archive"
  - 任何需要把已实施、已审查通过的 change 合并回模块活文档的请求
---

# eo-archive — 变更归档

把已审查通过的 change 的 **Spec Delta** 机械合并回模块 `spec.md`，并更新索引、修改 change 状态。这是 change 生命周期的最后一步，也是保持 spec 常青的关键。

## 核心理念

1. **Delta 驱动**：只消费 change.md 的 `## 3 Spec Delta` 章节，不重新理解业务
2. **机械合并**：ADDED/MODIFIED/REMOVED 按声明直接落到 spec.md 对应章节
3. **冲突不硬吞**：若 Delta 与现有 spec 冲突（如 MODIFIED 的"旧描述"在 spec 中找不到），停下来让用户裁决
4. **一次性闭环**：归档后 change 状态变为 `archived`，不再允许修改

## 前置条件

- 用户给定 `<module-name>` 和 `<change-id>`（如 `/eo-archive inventory 015-add-sort`）
- `eo-doc/dev/<module-name>/spec.md` 存在
- `eo-doc/dev/<module-name>/changes/<change-id>/change.md` 存在且 `status: done`
- 对应的 `review.md` 存在且审查通过（无 P0/P1 剩余）
- 对应的 `test.md` 存在且通过（若 change 要求了测试）

若任一前置条件不满足 → 停止并告知用户原因。

## 工作流程

### 第一步：读取并验证

1. 读 `changes/<change-id>/change.md`，验证 `status: done`
2. 读 `changes/<change-id>/review.md`，确认结论为通过
3. 读 `changes/<change-id>/test.md`（若存在），确认通过
4. 读模块 `spec.md`，定位所有 Delta 涉及的章节

### 第二步：解析 Delta

从 `change.md` 的 `## 3 Spec Delta` 提取三类条目：
- **ADDED 列表**：每条含"能力名 + 描述 + spec 目标章节"
- **MODIFIED 列表**：每条含"能力名 + 旧描述 + 新描述 + spec §X.Y"
- **REMOVED 列表**：每条含"能力名 + spec §X.Y"

若 Delta 章节为空或格式不符 → 提示用户修复 change.md 后重跑。

### 第三步：冲突预检

**MODIFIED 项**：在 spec.md 对应章节搜索"旧描述"，若找不到（可能 spec 在这之间被其他 change 改过）→ 列出冲突项，让用户选择：
- 跳过该条
- 手动指定合并位置
- 终止归档

**REMOVED 项**：在 spec.md 对应章节搜索待删除内容，若找不到 → 同上处理。

**ADDED 项**：确认目标章节存在；若目标章节不存在，提示用户先修 change.md 或允许追加到章节末尾。

### 第四步：执行合并

对 spec.md 逐条应用 Delta：
- **ADDED**：在指定章节末尾追加新条目
- **MODIFIED**：定位旧描述，替换为新描述
- **REMOVED**：删除指定条目

所有合并操作用 Edit 工具逐条执行，保持 diff 清晰。

### 第五步：更新 spec.md 元信息

1. frontmatter `updated` 改为今天日期
2. 在 `## 9 关联变更`（或 `## 关联变更`）表末尾追加一行：
   ```
   | [<change-id>](changes/<change-id>/change.md) | YYYY-MM-DD | <change summary> |
   ```
3. 在 `## 10 变更记录` 追加一行：
   ```
   | YYYY-MM-DD | 归档 <change-id>: <一句话描述> | eo-archive |
   ```

### 第六步：更新 change.md

1. frontmatter `status` 从 `done` 改为 `archived`
2. `## 10 实施记录` 填入归档日期

### 第七步：更新索引

1. 更新 `eo-doc/dev/<module-name>/changes/INDEX.md`：找到对应行把 status 列改为 `archived`
2. 更新 `eo-doc/dev/INDEX.md`：若该模块条目需要刷新最近活动时间，同步

### 第八步：汇报结果 + 可选复检建议

向用户汇报：
- 合并的 Delta 条数（ADDED N / MODIFIED N / REMOVED N）
- spec.md 受影响的章节列表
- 冲突处理记录（若有）
- change 状态已改为 archived

**spec 复检建议**：根据本次 Delta 的规模和类型，在汇报末尾追加建议：

| 触发条件 | 建议文案 |
|---------|---------|
| MODIFIED ≥ 3 条 或 REMOVED ≥ 1 条 | 💡 本次 Delta 对 spec 做了 N 条 MODIFIED / M 条 REMOVED，建议跑一次 `/eo-spec-review <module-name>` 验证新基线仍然自洽 |
| 涉及 spec 章节 ≥ 3 个 | 💡 本次 Delta 触及 spec 的 N 个章节，建议跑一次 `/eo-spec-review` 确认跨章节一致性 |
| 仅少量 ADDED | 无需复检建议 |

**提示但不强制**：复检是可选的，用户决定是否跑。

---

## 冲突处理模板

当遇到无法自动合并的 Delta 时，向用户呈现：

```
⚠️ Delta 冲突：

[MODIFIED-2] 库存上限逻辑
  - 预期的旧描述（change.md 声明）：
    "玩家最多持有 100 件同类物品"
  - spec.md §3.4 当前实际内容：
    "玩家最多持有 120 件同类物品（v1.5 提升）"

可能原因：本 change 与之前某个 change 对 §3.4 有并发修改。

请选择：
  1. 跳过此条（Delta 不合并，由用户手动处理）
  2. 强制替换（用新描述覆盖当前实际内容）
  3. 终止归档
```

---

## 关键约束

- **只做合并，不做二次澄清**：归档阶段不问业务问题，所有澄清应在 change 阶段完成
- **冲突必须停下**：绝不自作主张解决冲突
- **归档不可逆**：archived 状态的 change 不再修改；若需修正，发起新的 change 来覆盖
- **Delta 完整性校验**：若 change.md 没写 Delta 或格式错误，直接拒绝归档
- **保持 diff 可读**：用 Edit 逐条合并，不要 Write 整文件覆盖 spec.md
