#!/usr/bin/env sh

set -eu

usage() {
  cat <<'EOF'
用法:
  sh install.sh
  sh install.sh --claude-only
  sh install.sh --codex-only

说明:
  默认同时把当前仓库下所有 eo-* skill 软链到:
  - ~/.claude/skills
  - ~/.agents/skills
EOF
}

install_claude=1
install_codex=1

while [ "$#" -gt 0 ]; do
  case "$1" in
    --claude-only)
      install_codex=0
      ;;
    --codex-only)
      install_claude=0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "未知参数: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

script_dir=$(
  CDPATH= cd -- "$(dirname -- "$0")" && pwd
)

link_skills() {
  target_dir=$1
  target_name=$2
  found=0

  mkdir -p "$target_dir"

  for skill_dir in "$script_dir"/eo-*; do
    [ -d "$skill_dir" ] || continue
    found=1
    skill_name=$(basename "$skill_dir")
    target_path="$target_dir/$skill_name"

    if [ -e "$target_path" ] || [ -L "$target_path" ]; then
      echo "[$target_name] 跳过 $skill_name，目标已存在: $target_path"
      continue
    fi

    ln -s "$skill_dir" "$target_path"
    echo "[$target_name] 已链接 $skill_name -> $target_path"
  done

  if [ "$found" -eq 0 ]; then
    echo "未找到任何 eo-* skill 目录，请确认脚本位于仓库根目录。" >&2
    exit 1
  fi
}

if [ "$install_claude" -eq 1 ]; then
  link_skills "$HOME/.claude/skills" "Claude"
fi

if [ "$install_codex" -eq 1 ]; then
  link_skills "$HOME/.agents/skills" "Codex"
fi

echo "安装完成。"
echo "提示: eo-flow 依赖 tmux + smux 提供的 tmux-bridge；如果只用单 agent 流，可以先不装。"
