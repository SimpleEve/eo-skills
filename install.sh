#!/usr/bin/env sh

set -eu

usage() {
  cat <<'EOF'
用法:
  sh install.sh
  curl -fsSL https://raw.githubusercontent.com/SimpleEve/eo-skills/main/install.sh | sh

说明:
  把 eo-skills 仓库下所有 eo-* skill 软链到跨 agent 标准位 ~/.agents/skills，
  再在检测到的 agent skills 目录各建软链指向标准位:
  - ~/.claude/skills                (Claude Code)
  - ~/.codex/skills                 (Codex)
  - ~/.gemini/antigravity/skills    (Antigravity)
  与 skills CLI（npx skills add）落位同构；目标已有同名条目时跳过不覆盖。
  并把 cli/ 下的命令 (eo-helper 日常入口 + eo-board 看板 + eo-sync 同步核
  + eo-sync-obsidian/eo-sync-github 适配器) 链接进 EO_BIN_DIR (默认 ~/.local/bin，可覆盖)。
  这些 CLI 为 POSIX-only。
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "未知参数: $1（无 per-agent 旗标；未检测到的 agent 自动跳过）" >&2
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

# skill 目录可能是仓库根，也可能是仓库下的 skills/；cli/ 恒在仓库根
if [ "$(basename -- "$skills_dir")" = "skills" ]; then
  repo_root=$(dirname -- "$skills_dir")
else
  repo_root=$skills_dir
fi

shared_dir="$HOME/.agents/skills"

# eo-doc 是本仓库自身的 dogfood 文档（change 工件 + 项目手册），非分发内容
is_excluded() {
  case "$1" in
    eo-doc) return 0 ;;
    *) return 1 ;;
  esac
}

# 软链 $2 -> $1；目标已存在且有效则跳过，悬空软链则修复
link_one() {
  src=$1
  target=$2

  if [ -L "$target" ] && [ ! -e "$target" ]; then
    echo "修复悬空链接: $target"
    rm "$target"
  fi

  if [ -e "$target" ] || [ -L "$target" ]; then
    return 1
  fi

  ln -s "$src" "$target"
  return 0
}

link_into_shared() {
  found=0

  mkdir -p "$shared_dir"

  for skill_dir in "$skills_dir"/eo-*; do
    [ -d "$skill_dir" ] || continue
    skill_name=$(basename "$skill_dir")
    if is_excluded "$skill_name"; then
      continue
    fi

    found=1

    if link_one "$skill_dir" "${shared_dir}/${skill_name}"; then
      echo "[shared] 已链接 ${skill_name} -> ${shared_dir}/${skill_name}"
    else
      echo "[shared] 跳过 ${skill_name}，目标已存在: ${shared_dir}/${skill_name}"
    fi
  done

  if [ "$found" -eq 0 ]; then
    echo "未找到任何 eo-* skill 目录，请确认仓库结构正确: $skills_dir" >&2
    exit 1
  fi
}

link_agent() {
  agent_dir=$1
  agent_name=$2

  # 只给已安装的 agent 建链（按其配置目录是否存在判断）
  if [ ! -d "$HOME/$agent_dir" ]; then
    echo "[$agent_name] 未检测到 $HOME/${agent_dir}，跳过"
    return 0
  fi

  agent_skills_dir="$HOME/$agent_dir/skills"
  mkdir -p "$agent_skills_dir"

  for skill_dir in "$skills_dir"/eo-*; do
    [ -d "$skill_dir" ] || continue
    skill_name=$(basename "$skill_dir")
    if is_excluded "$skill_name"; then
      continue
    fi

    if link_one "${shared_dir}/${skill_name}" "${agent_skills_dir}/${skill_name}"; then
      echo "[$agent_name] 已链接 ${skill_name} -> ${agent_skills_dir}/${skill_name}"
    else
      echo "[$agent_name] 跳过 ${skill_name}，目标已存在: ${agent_skills_dir}/${skill_name}"
    fi
  done
}

link_one_cli() {
  cli_name=$1
  bin_dir=$2
  cli_src="$repo_root/cli/$cli_name"

  if [ ! -f "$cli_src" ]; then
    echo "[CLI] 未找到 cli/$cli_name，跳过（仓库版本过旧？）" >&2
    return 0
  fi

  target_path="$bin_dir/$cli_name"

  if [ -e "$target_path" ] || [ -L "$target_path" ]; then
    if [ "$(readlink "$target_path" 2>/dev/null || true)" = "$cli_src" ]; then
      echo "[CLI] $cli_name 已链接: $target_path"
    else
      echo "[CLI] 跳过 $cli_name，目标已存在且指向别处: $target_path"
    fi
  else
    ln -s "$cli_src" "$target_path"
    echo "[CLI] 已链接 $cli_name -> $target_path"
  fi
}

install_cli() {
  bin_dir=${EO_BIN_DIR:-"$HOME/.local/bin"}
  mkdir -p "$bin_dir"

  # eo-helper 日常入口；eo-board 只读看板；eo-sync 同步核 + 两个内置适配器（POSIX-only）
  for cli_name in eo-helper eo-board eo-sync eo-sync-obsidian eo-sync-github; do
    link_one_cli "$cli_name" "$bin_dir"
  done

  case ":$PATH:" in
    *":$bin_dir:"*) ;;
    *)
      echo "提示: $bin_dir 不在 PATH 中，把下面这行加进 shell 配置（如 ~/.zshrc）后重开终端:"
      echo "  export PATH=\"$bin_dir:\$PATH\""
      ;;
  esac
}

link_into_shared
link_agent ".claude" "Claude"
link_agent ".codex" "Codex"
link_agent ".gemini/antigravity" "Antigravity"

install_cli

echo "安装完成。"
echo "提示: 日常只需记一条命令——eo-helper，选数字即达看板与同步各入口。"
