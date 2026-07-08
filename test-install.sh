#!/usr/bin/env sh
# 试用安装：把本仓库（通常是开发中的 worktree）的 eo-* skill 软链到某个项目的
# 项目级 skills 目录（<project>/.claude/skills/），不触碰全局 ~/.claude/skills。
# Claude Code 同名 skill 项目级优先，因此该项目内 v2 会覆盖全局 v1。
# 软链指向本仓库，改动即时生效——调整满意后再正式提交/推送。

set -eu

usage() {
  cat <<'EOF'
用法:
  sh test-install.sh <project-path>            # 安装到指定项目
  sh test-install.sh <project-path> --remove   # 从该项目移除（只删指向本仓库的链接）

说明:
  - 只写 <project>/.claude/skills/，全局 skills 不受影响
  - 自动把链接路径加入项目 .gitignore（幂等）
  - v2 已删除的 skill（eo-spec 等）仍存在于全局 v1，本脚本不处理；
    v2 文档不会引导到它们，试用时避免手动调用即可
EOF
}

[ "$#" -ge 1 ] || { usage >&2; exit 1; }
case "$1" in -h|--help) usage; exit 0;; esac

project=$(CDPATH= cd -- "$1" && pwd)
shift
mode="install"
[ "${1:-}" = "--remove" ] && mode="remove"

src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target="$project/.claude/skills"

if [ "$mode" = "remove" ]; then
  removed=0
  for link in "$target"/eo-*; do
    [ -L "$link" ] || continue
    dest=$(readlink "$link")
    case "$dest" in
      "$src"/*) rm "$link"; removed=$((removed+1)); echo "已移除 $(basename "$link")";;
      *) echo "跳过 $(basename "$link") (不指向本仓库)";;
    esac
  done
  echo "完成：移除 $removed 个链接。全局 skills 未受影响。"
  exit 0
fi

mkdir -p "$target"
linked=0; skipped=0
for skill_dir in "$src"/eo-*; do
  [ -d "$skill_dir" ] || continue
  name=$(basename "$skill_dir")
  path="$target/$name"
  if [ -e "$path" ] || [ -L "$path" ]; then
    echo "跳过 ${name} (目标已存在: ${path})"; skipped=$((skipped+1)); continue
  fi
  ln -s "$skill_dir" "$path"
  linked=$((linked+1))
done

# .gitignore 幂等追加（试用链接不入库）
gi="$project/.gitignore"
marker="# eo-skills test-install (trial links, do not commit)"
if ! { [ -f "$gi" ] && grep -qF "$marker" "$gi"; }; then
  { echo ""; echo "$marker"; echo ".claude/skills/eo-*"; } >> "$gi"
  echo "已追加 .gitignore 规则: .claude/skills/eo-*"
fi

echo ""
echo "完成: 链接 ${linked} 个 (跳过 ${skipped}) → ${target}"
echo "来源: $src"
echo "提示: 同名 skill 项目级优先于全局；在该项目的 Claude Code 会话中即用 v2。"
echo "      本仓库的任何改动即时生效。试用结束: sh test-install.sh $project --remove"
