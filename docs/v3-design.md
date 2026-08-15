# eo-skills v3 设计：默认信任，信号升级

> 2026-08-15 定稿。替代 v2 的「三档渐进式严谨」主线；v2-design.md 保留作历史。
> 三项方向决策（用户拍板）：① 三站主路 + 可选闸门，不物理合并 skill；② 测试默认自验，风险信号触发独立 tester；③ 四问即 change 骨架。

## 1. 诊断（v2 的重量从哪来）

1. **不信任被编码成了文件协议**：独立 tester 上下文、writer matrix、append-only 轮次台账、证据新鲜度证明（S..H、I⊆R）——为「跨会话失忆 + 自证不可信」设计的审计框架，每个 change 都被当审计对象。
2. **流程路由硬编码**：每个 skill 结尾写死下一棒，速报必填字段、终态措辞三选一。路由应是「状态 + 风险信号算出的建议」，不是管道。
3. **change 文档以工程为中心**：AC 规范、TODO 文件栏前缀、Batch 并行组都是写给 implementer 的；给用户的只有「速览」一节，还是 AC 的二手翻译。四问在 goal-contract 七维里早有（Why/Outcome/Proof/Bounds），但只作内部 lens，从未成为文档脊柱。
4. **skill 文本自身重**：核心 5 个 skill 各 12–26KB，触发即吃上下文。

## 2. 目标形态

```
默认主路（三站）：
  /eo-change ──→ /eo-implement ──→ /eo-archive
   四问骨架       实施+自验          唯一硬门

可选闸门（风险信号命中 或 用户点名，才出现）：
  /eo-change-review · /eo-test（独立 tester）· /eo-review
```

默认值翻转：从「默认怀疑、审计留痕」翻成「默认信任、风险触发升级」。

### 2.1 风险信号清单（取代 light/full 判档）

命中任一 → change 确认时**建议**挂对应闸门，用户一个词豁免（豁免记 change.md 一节）：

| 信号 | 建议闸门 |
|------|---------|
| 不可逆操作（删数据 / schema 变更 / 破坏性 API） | change-review + 独立 test |
| 权限 / 资金 / 安全边界 | change-review + 独立 test + review |
| 外部契约（第三方 API、平台规则） | change-review |
| AC ≥5 或触及 ≥3 个共享模块 | change-review 或 review（择一） |
| 用户显式要求 | 点谁谁上 |

granularity.md §5 判档退役；§1 粒度数值保留（超硬标仍拒绝确认，防的是 change 太大，不是档位）。

### 2.2 change 文档：四问即骨架

```markdown
## §1 解决什么问题
为谁解决什么问题，为什么现在做。（Why，1-3 句人话）

## §2 完成后我应该看到什么
每条 = 演示脚本口吻的可观察结果 + 验收归属 + 阻断标注：
- [自动] 打开 X 做 Y，应看到 Z（阻塞）
- [人工] …（非阻塞）

## §3 谁验收、按什么标准
自动项：跑什么命令/看什么输出；人工项：指向验收单（acceptance.md 不变）。

## §4 不通过怎么办
阻塞项不过 → 禁止归档，回 implement 或回炉；非阻塞项不过 → 记 backlog 继续。

## §5 技术备注（折叠，implementer 视角）
TODO / Batch / 文件面。不再是文档主角。
```

- AC 规范（ac-spec.md）改写为「用户口吻 + 谁验 + 阻塞标注」三要素；auto/manual 标注保留（archive 门需要）。
- 速览节取消（§2 就是人读投影）；探针对齐保留（写完亮 §1+§2 给用户否一次）。
- 已钉决策并入 §1；条件节（§4-§8 旧模板）瘦身为一节「风险与开放问题」，有则写。

### 2.3 status 模型

`draft / confirmed / implementing / reviewed / archived` 字符串**不动**（eo-board / eo-sync 代码消费它们，改枚举 = 代码变更，不在本轮范围）。语义变化：

- `draft → confirmed`：对话确认即转，不变。
- `reviewed`：从必经站降级为**可选**——只有跑了 /eo-review 才置；archive 不再以它为前提。
- archive 的前提改为四问核对（见 2.4）。

### 2.4 archive：唯一硬门 = 四问核对

1. §2 每条阻塞项有证据（自动测试过 / 用户已勾）或显式豁免；
2. 人工项验收单一一对应（现有逻辑保留）；
3. 豁免清单向用户播报一遍，一键确认；
4. 收口：lessons 捕获（有坑才记）、doc sync、board 投影。

「不通过是否禁止继续」在 change 里由阻塞标注回答，在 archive 由这道门执行。

### 2.5 工件模型

- 默认产出：change.md（四问）+ 对话速报 + git 历史。
- test.md / review.md / change-review.md：只在对应闸门实际被调用时产出**简版**（结论 + 未决清单 + 失败定位）。轮次追加协议、台账 writer matrix、证据新鲜度证明全部删除——同一 change 再次被审就覆盖重写报告，历史由 git 兜。
- fix 的打地鼠信号、全链审查、熔断：**不动**（card-platform 实战换来）。

### 2.6 eo-loop

瘦身为「主路导航 + 信号检测」：默认按三站推进；检测到风险信号或打地鼠信号时停下给建议；不再强制编排 test/review 进循环。

## 3. 不动的部分

recall、lessons、board（含 eo-sync/eo-board 代码）、questioning.md 提问协议、acceptance.md 验收单、eo-fix 主体、goal-contract.md 七维（保留为内部 lens，加一句「change 的对外投影 = 四问」）、eo-brainstorming / eo-design / eo-handoff / eo-backlog / eo-project-record / eo-doc-manager / eo-project-init。

## 4. 执行清单（skill 文本改写，非代码，不开 change）

| # | 文件 | 动作 |
|---|------|------|
| 1 | eo-shared/granularity.md | §5 判档 → 风险信号清单；其余保留 |
| 2 | eo-shared/ac-spec.md | AC 三要素用户口吻化 + 阻塞标注 |
| 3 | eo-shared/conventions.md | §3：reviewed 变可选、archive 前提改写；status 枚举不动 |
| 4 | eo-shared/goal-contract.md | 加「四问 = change 对外投影」一句 |
| 5 | eo-change/SKILL.md + references/change-template.md | 四问骨架；删档位分流；扩档/回炉瘦身（回炉 = 方案实质改 → 重新确认，删计数器字段纪律） |
| 6 | eo-implement/SKILL.md | 默认自验；信号触发才建议独立 test/review；轻模式 lock 依赖删除；完成门保留为「自验清单 + 对话速报」 |
| 7 | eo-test/SKILL.md | 定位改「按需独立 tester」；lock 模式退役；报告简版覆盖式 |
| 8 | eo-review/SKILL.md | 按需；不再写 status；报告简版覆盖式；维度 7 证据失效审计删除（谁调用谁负责基线） |
| 9 | eo-change-review/SKILL.md | 信号触发或点名；删轮次上限/增量核销协议，单轮报告 |
| 10 | eo-archive/SKILL.md | 硬门 = 四问核对（2.4） |
| 11 | eo-loop/SKILL.md | 瘦身（2.6） |
| 12 | eo-fix/SKILL.md | 仅修 status/引用口径，主体不动 |
| 13 | README.md / docs/GUIDE.md | 同步新主路 |
| 14 | eo-doc/（本仓自身文档） | 改完后跑 doc-manager sync |

## 5. 迁移

无在途 change（18 个全 archived），无转换负担。存量归档工件冻结不改。frontmatter 计数器字段（`plan_revision`/`fix_rounds`/`fix_consumed`/`test_lock_commit`）停止写入，已归档的不清理。

## 6. 风险与回退

- **风险**：删掉独立验证后，高风险 change 漏检概率上升。对冲：信号清单 + archive 硬门 + 用户随时可点名闸门。信号漏判是最大软肋——change 确认时必须显式播报「命中/未命中信号及理由」，把漏判暴露给用户。
- **回退**：全部改动是 skill 文本，git 可回滚；v2-design.md 与归档工件不动。
