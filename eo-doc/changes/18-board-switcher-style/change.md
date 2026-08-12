---
id: board-switcher-style
seq: 18
title: 项目切换器自绘下拉
summary: 原生 select 换自绘下拉，样式对齐看板设计语言，行为与跳转口径不变
status: confirmed
tier: light
type: enhance
base_commit: d7c6d328f95d8e9ffca030b427e94c505050e955
test_lock_commit: 7b1f42ed8012d2f156f9b7cbe185fe6e927861d1
commits: []
issue: ~
created: 2026-08-12
---

# 项目切换器自绘下拉

意图：#16 用原生 `<select>` 实现项目切换，触发器尚能融入顶栏，但展开的下拉列表是 OS 原生渲染（白底/系统字体），与看板暗黑定制 UI 明显脱节（用户原话「明显不符合整体 UI 设计风格，尤其是那个 dropdown list」）。换成自绘 button + listbox，复用现有设计令牌；跳转行为（serve `/p/<key>`、快照 hash）与数据口径不变。

## 2. 验收清单

- [ ] AC-1 触发器与展开列表全部自绘：面板用 `var(--surface)`/`--line` 暗色、圆角、hover/选中高亮，字体与顶栏 chip 一致；任何主题下不出现原生白底列表（人工:打开下拉过目观感）（人工观感，无锁定）
- [ ] AC-2 交互闭环：点击触发器展开/收起；点击面板外或 Esc 收起；方向键上下移动高亮、回车选中（验证：DOM 断言模拟键盘/点击流）（锁定：tests/test_board_switcher_style.py#test_lock_switcher_toggle_outside_and_escape_close · test_lock_arrow_keys_and_enter_select_navigate · test_lock_multi_project_uses_custom_listbox_not_native_select · test_lock_no_native_select_in_project_switch_markup）
- [ ] AC-3 选中项目即跳转，serve（`/p/<key>`）与静态快照（hash `#/p/<key>`）两种形态都生效；当前项目在列表中有选中标记（锁定：tests/test_board_switcher_style.py#test_lock_hash_href_navigation_for_snapshot_form · test_lock_current_project_marked_in_list · test_lock_arrow_keys_and_enter_select_navigate）
- [ ] AC-4 项目名含 HTML 特殊字符时列表安全渲染（不注入、不错位）（锁定：tests/test_board_switcher_style.py#test_lock_project_name_html_is_escaped）
- [ ] AC-5 无多项目数据时（单项目场景）保持原静态 chip，不出现禁用态下拉（锁定：tests/test_board_switcher_style.py#test_lock_single_project_stays_static_chip）
