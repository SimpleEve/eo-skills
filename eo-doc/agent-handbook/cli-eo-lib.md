---
title: cli/eo_lib 共享解析库
type: agent
tags: [cli, shared-lib, config, frontmatter, freshness]
created: 2026-07-24
updated: 2026-07-25
scope: 改动 cli/ 下任何消费 change/backlog/配置文件契约的代码时
status: active
source: cli/eo_lib/
summary: >
  eo-board 与未来 eo-sync 共用的五域解析库（零第三方依赖，仅标准库）：
  配置加载（含 .eo-project.local.json 覆盖合并与必填校验）、git 封装、frontmatter 解析、change 扫描计数、缓存新鲜度键。
conclusions:
  - 库不拥有进程生命周期：一律抛 ConfigError（含路径与原因），禁止 sys.exit/die——退出责任在 CLI 入口
  - 必填校验以合并结果为准（project_name/mode/project_root/doc_root + mode 枚举 + 路径约束），无静默缺省填充
  - project_root 相对值读取时归一化（解析得出已存在目录才放行 + 告警），下游拿到的恒为绝对路径；解析不到则 fail-closed 不猜
  - freshness 键必须闭合 build_data 全部动态输入；新增动态输入须同步扩展键（模块 docstring 载明契约）
---

供 CLI 侧消费「文件契约」（change.md frontmatter、.eo-project.json、backlog 卡）的共享实现。抽取自 eo-board（change #1，基线 792522d），API 语义与原实现等价。

## 模块与入口

| 模块 | 关键函数 | 职责 |
|------|---------|------|
| `config.py`（111 行） | `find_project_config(start)` / `load_project_config(path)` / `ConfigError` | 向上定位 `.eo-project.json`；同目录 `.eo-project.local.json` 顶层字段覆盖合并（local 优先）→ `_validate_merged` 必填校验 → 标准化。`_normalize_project_root`：相对 `project_root`（v1 遗留软链形态）按 repo root 解析 + realpath，得已存在目录才放行并 stderr 告警；解析不出（含成环软链的 RuntimeError、NUL 路径的 ValueError）一律 fail-closed；绝对路径分支零变化 |
| `gitio.py` | `run_git` / `list_worktrees` / `list_worktrees_status`（降级感知枚举，供快照完整性判定） | git 子进程封装（15s 超时、失败返空串）；worktree 枚举（porcelain 解析 + 分支名覆盖） |
| `frontmatter.py` | `split_frontmatter` / `parse_yaml_subset` / `parse_yaml_scalar` / `unquote` / `upsert_frontmatter_fields`（保序回写：已存字段原地换值、新字段 frontmatter 尾插） | 手写 YAML 子集（容错、BOM、行内注释、`[a,b]` 列表；不支持多行值/嵌套对象） |
| `changes.py`（249 行） | `parse_change_file` / `scan_all_changes` / `parse_ac_section` / `parse_todo_section` / `parse_oq_section` / `count_ac` / `count_todo` | change.md 各节解析与多 worktree 扫描（同 id 取状态最高者、seq 撞号告警） |
| `registry.py` | `load_registry` / `register` / `unregister` / `entry_path` | 生态项目注册表 `${EO_HOME:-$HOME/.eo}/projects.json`：schema v1、原子写、未知字段保留、损坏报错不清空；去重键=`gitio.repo_identity()`（与 eo-sync 簿记 hash8 同源单一 API） |
| `freshness.py`（69 行） | `compute_freshness_key(cfg)` | 缓存新鲜度键：当天日期 + worktree(路径,分支,HEAD) 三元组集 + `for-each-ref` sha256 指纹 + changes 树 max-mtime + backlog/roadmap mtime |

## 使用约束

- 导入方式：消费方以 `Path(__file__).resolve()` 定位真实 `cli/` 目录后 `from eo_lib import ...`（符号链接安装与仓库直跑双路径成立，见 cli/eo-board 头部）
- 错误所有权：库内抛 `ConfigError`，CLI 入口捕获、格式化 stderr、非零退出并附 `/eo-project-init` 指引
- 测试：`tests/test_eo_board_cache.py` 覆盖 freshness 键确定性用例（跨日/月、同 SHA 换分支、ref-only 更新）与缓存单飞；`tests/test_eo_lib_project_root.py` 覆盖 project_root 归一化（相对/软链解析放行、绝对零变化、成环软链与目标消失 fail-closed）与既有校验矩阵 characterization

## 来源

- [cli/eo_lib/](../../cli/eo_lib/) — 实现本体
- [changes/01-shared-lib-board-cache/](../changes/01-shared-lib-board-cache/change.md) — 抽取边界与已钉决策（审计历史）
