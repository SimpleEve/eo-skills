# eo-skills 使用说明（面向用户）

> 这篇回答一个问题：**装好之后，我每天到底敲什么？**
> 概念与设计权衡见 [GUIDE.md](GUIDE.md)，交互式导览见 [how-it-works.html](how-it-works.html)。

---

## 0. 一分钟总览

eo-skills 有两类东西：

| 类别 | 有哪些 | 在哪用 |
|------|--------|--------|
| **Skill**（对话里喊） | `/eo-change`、`/eo-fix`、`/eo-implement`…… | Claude Code / Codex 会话里 |
| **CLI**（终端里敲） | `eo-board`（看板）、`eo-sync`（投影同步） | 任意终端 |

日常心智模型：**对话里干活，终端里看板**。你在会话里口喷需求和 bug，流程 skill 负责留痕；`eo-board` 让你随时看到所有项目进展，`eo-sync watch` 让 Obsidian 看板自动跟手。

---

## 1. 安装与升级

```bash
git clone https://github.com/SimpleEve/eo-skills.git ~/code/eo-skills
cd ~/code/eo-skills && sh install.sh
```

- skill 以**软链**装进 `~/.claude/skills/` 等目录——以后 `git pull` 即升级，无需重装
- CLI（`eo-board`、`eo-sync`、`eo-sync-obsidian`、`eo-sync-github`）链接进 `~/.local/bin`（可用 `EO_BIN_DIR` 覆盖）；确保该目录在 `PATH` 里
- CLI 为 POSIX-only（macOS / Linux；Windows 请在 WSL 里用）
- 已装过的重跑 `sh install.sh` 是幂等补齐

## 2. 每个项目做一次：初始化

在项目目录的 Claude Code 会话里：

```
/eo-project-init
```

它会问一个关键问题——**项目管理侧（roadmap / backlog / 决策 / 教训）放哪**：

- **local 模式**（缺省推荐）：放仓库内 `.eo-project/`，**随仓库提交**——协作者 clone 即得完整项目记忆
- **vault 模式**：放你的 Obsidian vault，跨项目统一浏览（重度 Obsidian 用户选这个）

init 成功会顺手把项目登记进 `~/.eo/projects.json`（多项目看板靠它）；注册失败不影响 init，稍后 `eo-board --register` 补上即可。

**协作者接入**：clone 了别人已初始化的仓库？直接重跑 `/eo-project-init`——它检测到配置里的路径不适用你的机器时，会引导生成 `.eo-project.local.json`（个人覆盖，不提交），不动团队共享配置。

## 3. 日常：三条路

| 你想干嘛 | 敲什么 | 会发生什么 |
|---------|--------|-----------|
| 小改动（挪按钮/改文案） | 直接让 agent 改 | 不开流程，改完 commit 完事 |
| 加功能/增强/重构 | `/eo-change 加一个批量导出` | 产出验收清单（AC）→ 你确认 → `/eo-implement` 落地 → test/review → `/eo-archive` 归档 |
| 报 bug | `/eo-fix 导出的文件名不对` | 定位直接修，不问东问西 |

不确定选哪条？直接喊 `/eo-change`——够小它会主动说「不值得开 change，直接改」。想把一串环节托管着自动循环推进，喊 `/eo-loop`。

## 4. 看板：eo-board

### 单项目（在项目目录里）

```bash
eo-board            # 终端摘要：change 各状态分列 + backlog + 警告
eo-board --html     # 自包含 HTML 快照，自动开浏览器
eo-board --serve    # 本地实时看板 http://127.0.0.1:7333（3 秒热刷新，有缓存不费机器）
```

### 多项目（任意目录）

```bash
eo-board --all                    # 每个注册项目一行：状态计数 + backlog 数 + 数据新鲜度
eo-board --project 兔村游戏        # 按注册名（或路径）下钻单项目视图，不用 cd
eo-board --all --scan ~/projects  # 没注册的项目也临时扫进来看（不写注册表）
```

### 注册表维护

```bash
eo-board --register     # 把当前项目登记进 ~/.eo/projects.json（init 会自动做）
eo-board --unregister   # 移除登记
```

eo-board 是**只读**的——它永远不写你的项目文件。

## 5. 投影同步：eo-sync

change 的状态要「投影」到外部才看得见：Obsidian 看板卡片、GitHub issue/PR。投影统一由 `eo-sync` 执行：

```bash
eo-sync adapters        # 看有哪些投影目标、哪些已启用
eo-sync run --dry-run   # 只看计划，不写任何东西
eo-sync run             # 执行投影（幂等，跑几遍都无副作用）
```

**什么时候需要手动跑？** 基本不需要——`/eo-archive` 归档时自动跑一次；平时挂上 watch 就全自动：

```bash
eo-sync watch --all           # 常驻：所有注册项目，状态一变 10 秒内追平（推荐挂一个终端里）
eo-sync watch --interval 5    # 只盯当前项目，5 秒间隔
```

watch 没变化时零成本静默（靠新鲜度键短路），**同一作用域只开一个**（重复启动会报错并告知持有者）。Obsidian 用户：挂上 `watch --all`，你的 Bases 看板从此自动跟手。

### 配置（.eo-project.json 的 `sync` 段）

init 的联动问答会写好；手工样例：

```json
"sync": {
  "obsidian": { "enabled": true, "stub_dir": "board" },
  "github":   { "enabled": true, "issue": true, "pr": "auto" }
}
```

- **obsidian**：change 投影成 vault `board/` 的 stub 卡（Bases 看板消费）
- **github**：confirmed 起建 issue、archive 时按策略建 PR（AC 全勾才 `Closes`）
- 老项目的 `board`/`github` 旧段不用改——自动等价映射
- 想接 Notion/飞书？投影是插件化的：PATH 上放一个 `eo-sync-<name>` 可执行 + 配置启用即可，协议见 [sync-adapter-protocol.md](sync-adapter-protocol.md)

## 6. 常见问题

**Q：看板卡片怎么不动了？**
状态流转期间不再实时写卡（这是设计：写路径不为呈现层付费）。挂 `eo-sync watch --all` 即恢复秒级跟手；或任意时刻 `eo-sync run` 手动追平；归档时总会自动同步一次。

**Q：投影删错了怎么办？**
投影是派生数据，`eo-sync run` 随时全量重建；且孤儿清理只在「快照可证完整」时执行，扫描有任何异常都会保守跳过。

**Q：多人协作，配置里全是别人的路径？**
重跑 `/eo-project-init`，机器相关字段会进你自己的 `.eo-project.local.json`（不提交）。

**Q：老项目报「project_root 必须是绝对路径」？**
v1 时代的配置可能把 `project_root` 写成了软链相对路径（如 `eo-doc/vault`）。临时解法：手工改成绝对的 vault 路径。读取时自动归一化软链引用的兼容修复在排期中。

**Q：数据都在哪，删了工具会丢东西吗？**
一切真相都在 markdown 文件里（仓库内 `eo-doc/` + 管理侧目录）。CLI 只读或只写投影/注册表（`~/.eo/` 下），卸载工具不损失任何数据。
