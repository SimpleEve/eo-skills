#!/usr/bin/env sh

set -eu

usage() {
  cat <<'EOF'
用法:
  sh install.sh
  curl -fsSL https://raw.githubusercontent.com/SimpleEve/eo-skills/main/install.sh | sh
  sh install.sh --claude-only
  sh install.sh --codex-only
  sh install.sh --antigravity-only

说明:
  默认同时把 eo-skills 仓库下所有 eo-* skill 软链到:
  - ~/.claude/skills          (Claude Code)
  - ~/.agents/skills          (Codex)
  - ~/.gemini/antigravity/skills  (Antigravity)
EOF
}

install_claude=1
install_codex=1
install_antigravity=1

while [ "$#" -gt 0 ]; do
  case "$1" in
    --claude-only)
      install_codex=0
      install_antigravity=0
      ;;
    --codex-only)
      install_claude=0
      install_antigravity=0
      ;;
    --antigravity-only)
      install_claude=0
      install_codex=0
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
  CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd || pwd
)

repo_url=${EO_SKILLS_REPO_URL:-https://github.com/SimpleEve/eo-skills.git}
cache_dir=${EO_SKILLS_REPO_DIR:-"$HOME/.eo-skills/repo"}

has_skill_dirs() {
  scan_dir=$1

  for skill_dir in "$scan_dir"/eo-*; do
    [ -d "$skill_dir" ] || continue
    return 0
  done

  return 1
}

resolve_skills_dir() {
  source_dir=$1

  if has_skill_dirs "$source_dir/skills"; then
    printf '%s\n' "$source_dir/skills"
    return 0
  fi

  if has_skill_dirs "$source_dir"; then
    printf '%s\n' "$source_dir"
    return 0
  fi

  return 1
}

ensure_cached_repo() {
  if ! command -v git >/dev/null 2>&1; then
    echo "远程安装需要 git：请先安装 git，或 clone 仓库后在仓库根目录运行 sh install.sh。" >&2
    exit 1
  fi

  if [ -d "$cache_dir/.git" ]; then
    if [ -n "$(git -C "$cache_dir" status --porcelain)" ]; then
      echo "缓存仓库有未提交改动，已停止更新: $cache_dir" >&2
      echo "请处理该目录，或设置 EO_SKILLS_REPO_DIR 指向新的缓存目录后重试。" >&2
      exit 1
    fi

    echo "更新 eo-skills 缓存仓库: $cache_dir"
    git -C "$cache_dir" fetch --depth=1 origin main
    git -C "$cache_dir" checkout -q -B main origin/main
  else
    mkdir -p "$(dirname -- "$cache_dir")"

    if [ -e "$cache_dir" ]; then
      echo "缓存路径已存在但不是 git 仓库: $cache_dir" >&2
      echo "请移走该路径，或设置 EO_SKILLS_REPO_DIR 指向新的缓存目录后重试。" >&2
      exit 1
    fi

    echo "克隆 eo-skills 到缓存仓库: $cache_dir"
    git clone --depth=1 "$repo_url" "$cache_dir"
  fi
}

if skills_dir=$(resolve_skills_dir "$script_dir"); then
  :
else
  ensure_cached_repo

  if ! skills_dir=$(resolve_skills_dir "$cache_dir"); then
    echo "未找到任何 eo-* skill 目录，请确认仓库结构正确: $cache_dir" >&2
    exit 1
  fi
fi

link_skills() {
  target_dir=$1
  target_name=$2
  found=0

  mkdir -p "$target_dir"

  for skill_dir in "$skills_dir"/eo-*; do
    [ -d "$skill_dir" ] || continue
    found=1
    skill_name=$(basename "$skill_dir")
    target_path="${target_dir}/${skill_name}"

    if [ -e "$target_path" ] || [ -L "$target_path" ]; then
      echo "[${target_name}] 跳过 ${skill_name}，目标已存在: ${target_path}"
      continue
    fi

    ln -s "$skill_dir" "$target_path"
    echo "[${target_name}] 已链接 ${skill_name} -> ${target_path}"
  done

  if [ "$found" -eq 0 ]; then
    echo "未找到任何 eo-* skill 目录，请确认仓库结构正确: $skills_dir" >&2
    exit 1
  fi
}

if [ "$install_claude" -eq 1 ]; then
  link_skills "$HOME/.claude/skills" "Claude"
fi

if [ "$install_codex" -eq 1 ]; then
  link_skills "$HOME/.agents/skills" "Codex"
fi

if [ "$install_antigravity" -eq 1 ]; then
  link_skills "$HOME/.gemini/antigravity/skills" "Antigravity"
fi

echo "安装完成。"
echo "提示: eo-flow 依赖 tmux + smux 提供的 tmux-bridge；如果只用单 agent 流，可以先不装。"
