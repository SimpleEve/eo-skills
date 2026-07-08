#!/usr/bin/env sh
# 试用安装：为「开发中的本仓库」构建一套独立的 Claude Code 配置目录（试用配置），
# 其 skills/ 软链到本仓库的 eo-*。用 CLAUDE_CONFIG_DIR 启动即可在任意项目试用 v2，
# 全局 ~/.claude 零接触、无同名冲突；本仓库的改动即时生效，满意后再正式提交推送。
#
# 注：不用「项目级 .claude/skills」方案——Claude Code 同名 skill 的优先级是
# personal > project（官方文档），项目级会被全局 v1 覆盖；skillOverrides "off"
# 又是按名字整体隐藏（实测两级同灭）。独立配置目录是唯一干净的隔离面。

set -eu

EO_HOME="${EO_HOME:-$HOME/.eo}"
trial="$EO_HOME/v2-trial-config"
src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

usage() {
  cat <<EOF
用法:
  sh test-install.sh setup     # 构建试用配置目录（幂等）
  sh test-install.sh remove    # 删除试用配置目录
  sh test-install.sh status    # 查看当前状态

试用方式（setup 后，在任意项目目录）:
  CLAUDE_CONFIG_DIR="$trial" claude
建议加别名:
  alias claude-v2='CLAUDE_CONFIG_DIR="$trial" claude'
EOF
}

[ "$#" -ge 1 ] || { usage >&2; exit 1; }

case "$1" in
  setup)
    mkdir -p "$trial/skills"
    linked=0; skipped=0
    for skill_dir in "$src"/eo-*; do
      [ -d "$skill_dir" ] || continue
      name=$(basename "$skill_dir")
      path="$trial/skills/$name"
      if [ -e "$path" ] || [ -L "$path" ]; then skipped=$((skipped+1)); continue; fi
      ln -s "$skill_dir" "$path"
      linked=$((linked+1))
    done
    # 带上全局设置与记忆（副本，改动不回写全局）
    for f in settings.json CLAUDE.md; do
      if [ -f "$HOME/.claude/$f" ] && [ ! -f "$trial/$f" ]; then
        cp "$HOME/.claude/$f" "$trial/$f"
        echo "已复制全局 ${f} (副本, 独立演化)"
      fi
    done
    # 跳过 onboarding 向导（不复制凭据——首次启动需 /login 一次，token 之后常驻试用配置）
    if [ -f "$HOME/.claude.json" ] && [ ! -f "$trial/.claude.json" ]; then
      python3 - <<PYEOF 2>/dev/null || true
import json
d=json.load(open("$HOME/.claude.json"))
keep={k:d[k] for k in ("hasCompletedOnboarding","theme") if k in d}
json.dump(keep,open("$trial/.claude.json","w"))
PYEOF
    fi
    echo "完成: 链接 ${linked} 个 skill (跳过 ${skipped}) → $trial/skills"
    echo "来源: $src (改动即时生效)"
    echo ""
    echo "启动试用会话（任意项目目录下）:"
    echo "  CLAUDE_CONFIG_DIR=\"$trial\" claude"
    echo "建议别名: alias claude-v2='CLAUDE_CONFIG_DIR=\"$trial\" claude'"
    echo "注意: 凭据按配置目录隔离, 首次启动需 /login 一次 (仅此一次)"
    ;;
  remove)
    rm -rf "$trial"
    echo "已删除 $trial。全局 ~/.claude 从未被触碰。"
    ;;
  status)
    if [ -d "$trial/skills" ]; then
      echo "试用配置: $trial"
      echo "skills: $(ls "$trial/skills" | wc -l | tr -d ' ') 个 → 指向 $(readlink "$trial/skills/eo-change" 2>/dev/null | sed 's|/eo-change$||' || echo '?')"
    else
      echo "未安装。运行: sh test-install.sh setup"
    fi
    ;;
  -h|--help) usage ;;
  *) usage >&2; exit 1 ;;
esac
