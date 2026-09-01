# 维护协议

## changes/INDEX.md 整理

1. 列出 `changes/` 下全部子目录，与 INDEX.md 条目比对：
   - 孤儿条目（指向已删除目录）→ 删除该行
   - 漏收目录 → 读其 change.md frontmatter 补行
2. 状态/摘要列与各 change.md frontmatter 保持一致（以 frontmatter 为准）
3. seq 列顺手查重：重号 → created 晚者让号（见 [../../eo-shared/conventions.md](../../eo-shared/conventions.md) §2）
4. 单条目保持约 50 token，整个 INDEX 可一次性扫描

## templates/ 管理

- 模板由项目按需自建（如项目类型画像 `project-profile.md`），本 skill 不自动生成内容
- 模板内容完全来自用户输入；templates/ 无 INDEX，无需同步索引

## 验证

- [ ] INDEX 条目与目录一一对应
- [ ] 所有交叉引用指向真实存在的文件
