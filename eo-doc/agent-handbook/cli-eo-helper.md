---
title: cli/eo-helper 单一交互入口
type: agent
tags: [cli, helper, menu, ux]
created: 2026-07-26
updated: 2026-07-26
scope: 改动菜单条目、命令转发语义时
status: active
source: cli/eo-helper
summary: >
  数字菜单薄壳：7 条固定 argv 映射（看板/注册/同步/watch），选前回显底层命令（菜单即教学）；
  不复制业务逻辑、错误码透传。
conclusions:
  - 薄壳边界：不解析业务输出、不加旗标翻译、不吞错误码；底层 CLI 缺失给 install.sh 指引
  - 短命令 subprocess 前台执行后回菜单；serve/watch 用 os.exec 替换进程（信号语义与直跑一致，不留守护壳）
  - 非 TTY 打印菜单↔命令对照表 rc0 即退；输入校验只认 ASCII 数字（²/全角/中文数字一律非法提示）
---

菜单条目与转发映射见 `cli/eo-helper` 头部常量表；测试 `tests/test_eo_helper.py` + `tests/test_eo_helper_pty.py`（真实 PTY 会话矩阵）。

## 来源
- [cli-eo-board.md](cli-eo-board.md) / [cli-eo-sync.md](cli-eo-sync.md) — 被转发的两个 CLI
- [../../docs/cli-reference.md](../../docs/cli-reference.md) — 全量旗标参考（--help 为基准）
