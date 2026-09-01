# 三层架构与 SKILL 写作纪律

## 三层

1. **skill 层**（`eo-*/SKILL.md`）：prompt 产品本体，agent 运行时触发
2. **契约层**（`eo-shared/`）：跨 skill 口径单一来源；非 skill（无 SKILL.md）
3. **可执行层**（`cli/`）：skill 调用的终端 CLI，Python 3 标准库零第三方依赖

## 契约纪律

- 口径修改只改 eo-shared；禁止在任何 skill 内复制正文
- skill 以相对路径引用 `../eo-shared/<file>`；必须整套安装（skills CLI 或 install.sh 均整套分发，落位 `~/.agents/skills/` 单源 + 各 agent 目录软链），单独拷贝即断链

## SKILL 写作纪律

- 只写现行口径：无兼容说明、无出处、无设计理由（依据沉淀在 docs/ 与 research/）
- 每字金贵：SKILL 进运行时上下文，token 即成本

**何时读**：新增或修改 skill、改 eo-shared 口径、动 cli 与 skill 接线时。
