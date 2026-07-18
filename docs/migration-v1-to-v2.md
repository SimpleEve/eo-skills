# v1 → v2 迁移指南

面向已在项目中使用 eo-skills v1 的用户。v2 是破坏性升级，核心变化一句话：**spec 归为 change，归档不再反写文档——活文档（state / agent-handbook）由 doc-manager 以代码为唯一信源维护**。

## 破坏性变更清单

| 变化 | v1 | v2 |
|------|----|----|
| 模块与 spec | `eo-doc/dev/<module>/spec.md` 活文档基线 | **移除**。期望行为的载体是 change 的验收清单（AC） |
| change 位置 | `eo-doc/dev/<module>/changes/` 模块内编号 | `eo-doc/changes/` 项目级扁平目录，目录名 `<NN>-<slug>/`（seq 补零前缀便于 `ls` 排序、找进行中的）；**身份仍是 slug**（commit 前缀/issue 用它，撞号只 `git mv` 目录、不碰 commit），frontmatter `seq` 为显示序号（#N，撞号自愈）；存量数字前缀 id 冻结兼容 |
| change 模板 | 9 章（Delta / S-C-G / 层级 Part） | 必填 3 节（意图 / AC / TODO 分批）+ 条件 5 节（含涉及文件） |
| 归档 | Delta 机械合并回 spec.md | 结算 commit → 触发 doc-manager sync → 冻结 change |
| status 流转 | 用户手改 frontmatter（approved 等） | skill 自动流转：draft → confirmed → implementing → reviewed → archived（曾短暂命名 `done`，读到视同 reviewed） |
| bug 修复 | eo-fix 只诊断，implement 修 | **eo-fix 直接修复**（含深挖模式）；implement 只管 test/review 反馈循环 |
| 小改动 | 也要开 change | trivial 直改模式（判据见 eo-shared/granularity.md），cursor sync 兜底 |
| 移除的 skill | — | eo-workflow、eo-spec、eo-spec-review、eo-module-init、eo-project-update |
| 项目记录 | eo-project-lesson（仅教训） | **eo-project-record**（教训 + 决策统一入口，各带 INDEX） |
| 项目看板 | kanban_path 手工看板（init 注册/update 刷新/lesson 计数） | **退役**。change 级观测 → board stub + Bases；项目级总览 → Bases 聚合各项目 roadmap.md frontmatter |
| log.md | 必建，update/lesson 追加 | 移除必建（时间线由 changes/INDEX + git log 承担；存量 log.md 保留不再写入） |
| backlog | 扁平 `backlog.md` 追加条目 | **卡片化**：`backlog/` 每条一文件（`status: backlog` 上项目看板）；采纳/放弃归档到 `backlog/archive/`（status + tag 切换 + adopted_by 关联）；旧扁平文件打散后留存 |
| 新增 | — | eo-design（DESIGN.md）、eo-shared/（共享规范） |
| 临时文件 | `tmp/<topic>-handoff.md` 等散放 | 统一 `tmp/eo/<域>/`（handoff / fix / design） |

## 迁移步骤（存量 v1 项目）

> **推荐走自动路径**：在项目里重跑 `/eo-project-init`——其更新/修复分支会检测 v1 痕迹并自动引导下列第 2-6、8、9 步（可执行版见 `eo-project-init/references/migrate-v1.md`）。手动只需第 1 步（更新安装）与第 7 步（可选 design）。以下为完整手动版备查。

1. **更新安装**：重跑 install 脚本（软链模式下拉取新版仓库即生效）。新目录 `eo-shared/`、`eo-design/` 会被自动链接；已删除的四个 skill 需手动清理残留软链：
   ```bash
   rm -f ~/.claude/skills/{eo-workflow,eo-spec,eo-spec-review,eo-module-init,eo-project-update,eo-project-lesson} \
         ~/.agents/skills/{eo-workflow,eo-spec,eo-spec-review,eo-module-init,eo-project-update,eo-project-lesson} \
         ~/.gemini/antigravity/skills/{eo-workflow,eo-spec,eo-spec-review,eo-module-init,eo-project-update,eo-project-lesson}
   ```
2. **冻结存量 spec**：给每个 `eo-doc/dev/<module>/spec.md` 与 `spec-history.md` 的 frontmatter 加 `status: frozen`。它们保留作历史参考，v2 的任何 skill 不再读写。
3. **建立项目级 changes/**：创建 `eo-doc/changes/INDEX.md`，`seq` 从所有模块现存最大号 +1 续起（新 change 目录名 = seq 补零前缀 + slug，如 `15-batch-export/`；commit 前缀只用 slug）。存量模块内的 changes/ 目录原地保留（历史），INDEX 中可加一行指向旧位置。
4. **在途 change 走完余下生命周期**：implement/test/review 照走；**归档按 v2 执行**（不合并 Delta，直接结算 commit + sync + 冻结）。
5. **更新注入段**：重跑 `/eo-project-init`（幂等）——刷新 CLAUDE.md 的 eo-doc 目录表（dev → changes）、行为钩子新口径、`tmp/eo/` 进 .gitignore。
6. **首次 sync**：跑 `/eo-doc-manager sync`。若此前从未建过 state/，会 lazy 生成首批文档；此后 state + agent-handbook 就是「系统现在是什么样」的唯一口径。
7. （可选）`/eo-design init` 建立 DESIGN.md。
8. **项目管理侧迁移**：`kanban_path` 字段从此被忽略（旧手工看板文件可归档删除，如 00-Wiki/项目看板.md）；roadmap.md frontmatter 补 `status/phase/summary` 三字段后可被 Bases 聚合成项目总览；记录入口统一为 `/eo-project-record`（旧 lesson/update 软链已在步骤 1 一并清理）。
9. **backlog 打散**：旧扁平 `backlog.md`（或 backlog/todo.md）的未完成条目按 `/eo-backlog` 的 migrate 动作打散为卡片（created 取原日期、行内 #tag 转 frontmatter tags），自动出现在项目看板 backlog 列；已完成/放弃条目与原文件留存作档。

## 语义速查（旧习惯 → 新做法）

- 「先 module-init 再 change」→ 直接 `/eo-change`（新项目冷启动可先 `/eo-brainstorming` 拆首批 bootstrap change）
- 「改 status: approved」→ 不用了，对话里确认即可
- 「归档后跑 spec-review 复检」→ 不存在了；文档质量由 doc-manager 的一致性抽查（每 5 次 sync）兜底
- 「这个 bug 该 fix 还是开 change？」→ 都口喷给 `/eo-fix`，它自己判
- 「小样式调整开个 change」→ 不用，直接改，commit 带 `ui:` 前缀
