# Handbook 模板机制

`eo-doc/agent-handbook/` 的篇目内容从模板生成：一套模板 = 一个 preset 目录，init 按项目信号匹配候选，用户确认后合并生成。handbook 定位：规范性、方向性、非 SSOT（代码为准）、不挂自动同步。

## 两个库

| 库 | 位置 | 来源 |
|----|------|------|
| 内置库 | `eo-project-init/templates/handbook/<preset>/` | 随整套 skill 软链分发 |
| 私有库 | `"${EO_HOME:-$HOME/.eo}/handbook-templates/<preset>/"` | 用户手工维护 |

同名 preset **私有库整套覆盖内置库**（按 preset 粒度替换，不做文件级合并）。

## 一套 preset 的结构

```
<preset>/
├── manifest.md   # frontmatter 声明适用信号与简介
├── INDEX.md      # handbook 索引（篇目表 + 待补区）
└── <篇目>.md     # 篇目文件组
```

`manifest.md` frontmatter：

```yaml
---
name: general             # preset 名，与目录名一致
summary: 一句话简介        # 封闭选择时展示给用户
signals: []               # 适用信号：相对仓库根的文件路径或 glob 列表
---
```

- signals 逐条在仓库根探测：文件路径存在、或 glob 有匹配，任一命中即该 preset 成为候选
- **空 signals 不参与命中**，仅在无其他候选时作为缺省候选

## 匹配与生成

**已有项目**（生成 = 匹配合并，不是裸 copy）：

1. 五面扫描（lint/commit 配置、`git log` 归纳的 commit 规律、目录结构、架构分工、UI token 用法）产出实证
2. 取两个库的 preset 集合（同名取私有库版本），按 signals 命中候选
3. 按封闭选择协议确认用哪套（含「不用模板」——纯按实证落盘）
4. 合并生成：实证 > 模板 > 待补——模板篇目为底，扫描实证覆盖冲突项，扫描不到依据的标「待补」；已配置文件化的只落一行指针（指向配置文件）
5. worktree 协作与 codegraph 使用两篇逐个询问授权后才写入（comments 注释纪律随 preset 默认生成；AGENTS.md 注入段有其硬入口指针）

**空项目**：无实证可扫；询问项目类型，选定 preset 纯 copy（「待补」占位随项目成形后补齐）。
