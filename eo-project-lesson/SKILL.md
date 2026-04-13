---
name: eo-project-lesson
description: "捕获项目经验教训，写入 _lessons/ 集中存放。全局 skill，可在代码仓库中通过 .eo-project.json 定位项目目录。当用户说'踩坑了'、'记录经验'、'教训'、'lesson learned'时触发。"
---

# eo-project-lesson

## 功能

捕获项目中的经验教训（踩坑、最佳实践、意外收获），写入 `30-我的项目/_lessons/` 集中存放，并更新项目看板的经验教训计数。

## 输入

用户提供：
- **经验内容**：发生了什么、学到了什么
- **项目名称**（可选）：如在代码仓库中，通过 `.eo-project.json` 自动关联

## 定位项目目录

### 场景 A：在 vault 目录内

直接访问 `30-我的项目/<项目名>/`。

### 场景 B：在代码仓库内

读取当前目录或父目录的 `.eo-project.json`：

```json
{
  "project_name": "项目名",
  "project_vault": "/absolute/path/to/vault/30-我的项目/项目名"
}
```

如果找不到 `.eo-project.json`，提示用户：
1. 指定项目名（如果能确认是哪个项目）
2. 或运行 `eo-project-init` 生成配置

## 执行步骤

### 1. 定位项目

- 在 vault 内：用户指定或从上下文推断
- 在代码仓库：读取 `.eo-project.json` 获取 `project_name` 和 `project_vault`

### 2. 提炼经验教训

从用户输入中提取：
- **标题**：一句话概括
- **类别**：`pitfall`（踩坑）/ `best-practice`（最佳实践）/ `surprise`（意外发现）
- **项目**：关联项目名
- **阶段**：当前活跃 phase（自动读取）
- **内容**：发生了什么 + 学到了什么 + 下次怎么做

### 3. 创建经验文件

在 `30-我的项目/_lessons/` 创建文件：

命名：`{YYYY-MM-DD}-{项目名}-{简述}.md`

```markdown
---
type: lesson
category: "pitfall" | "best-practice" | "surprise"
project: "项目名"
phase: "phase-N-阶段名"
date: YYYY-MM-DD
tags: []
---

# {标题}

## 发生了什么

{背景和经过}

## 学到了什么

{核心教训}

## 下次怎么做

{可操作的改进方案}
```

### 4. 更新项目看板

在 `00-Wiki/项目看板.md` 对应项目条目中，更新经验教训计数。

### 5. 追加项目日志

在项目的 `log.md` 追加记录。

### 6. 输出摘要

展示：
- 经验文件路径
- 经验摘要
- 当前项目累计经验数

## 输出

- 经验文件：`30-我的项目/_lessons/{date}-{project}-{slug}.md`
- 看板更新：经验教训计数
- 项目日志：追加记录

## 约束

- 经验文件一旦创建不可修改，只能新建补充
- 所有经验集中在 `_lessons/` 目录，通过 `project` 字段关联项目
- 所有链接使用最短路径 `[[文件名]]`
- 能推断的字段自动填充，不强制用户提供所有信息
- 在代码仓库侧操作时，必须通过 `.eo-project.json` 定位，不猜路径
- 如果 `project_vault` 路径不可达，报错并提示检查配置
