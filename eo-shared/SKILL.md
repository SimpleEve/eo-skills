---
name: eo-shared
description: |
  共享规范库（非独立 skill，勿直接触发）：eo-* 各 skill 以 ../eo-shared/<file> 引用的单一来源规范（提问纪律、粒度判据、AC 规范、commit 纪律等）。
  NOT FOR: 直接调用本目录；它只作为引用目标随整套 eo-skills 一起分发。
---

# eo-shared — 共享规范库

本目录**不是可直接触发的 skill**，是 eo-* 各 skill 引用的单一来源规范。带 SKILL.md 仅为让 skills CLI（`npx skills add`）把它随整套 skill 一起分发——各 skill 以 `../eo-shared/<file>` 相对路径引用，**必须整套安装**，单独拷贝某个 skill 目录会断链。
