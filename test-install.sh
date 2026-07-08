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
  sh test-install.sh swap      # 【推荐·免登录】全局软链临时指向本仓库(可逆,manifest 记录原状)
  sh test-install.sh restore   # 还原全局到 swap 之前的状态
  sh test-install.sh setup     # 【备选】独立配置目录(CLAUDE_CONFIG_DIR,需 /login 一次)
  sh test-install.sh remove    # 删除独立配置目录
  sh test-install.sh status    # 查看当前状态

swap 模式说明:
  - 同名 skill 的全局链接改指本仓库;v2 已删除的 v1 skill 链接改名停车(.v1-parked)
  - 窗口期内所有项目的新会话都是 v2;restore 一条命令秒级还原
EOF
}

[ "$#" -ge 1 ] || { usage >&2; exit 1; }

case "$1" in
  swap)
    gskills="$HOME/.claude/skills"
    manifest="$EO_HOME/v2-swap-manifest.txt"
    if [ -f "$manifest" ]; then echo "已处于 swap 状态 (manifest 存在): $manifest" >&2; exit 1; fi
    mkdir -p "$EO_HOME"; : > "$manifest"
    swapped=0; parked=0; added=0
    # 1) 本仓库有的 skill: 全局链接改指本仓库(记录原 target); 全局没有的直接新增
    for skill_dir in "$src"/eo-*; do
      [ -d "$skill_dir" ] || continue
      name=$(basename "$skill_dir")
      gpath="$gskills/$name"
      if [ -L "$gpath" ]; then
        echo "RELINK $name $(readlink "$gpath")" >> "$manifest"
        rm "$gpath"; ln -s "$skill_dir" "$gpath"; swapped=$((swapped+1))
      elif [ ! -e "$gpath" ]; then
        echo "ADDED $name -" >> "$manifest"
        ln -s "$skill_dir" "$gpath"; added=$((added+1))
      else
        echo "跳过 ${name} (全局是实体目录, 不敢动)" >&2
      fi
    done
    # 2) 全局有、本仓库没有的 eo-* 链接(v1 独有): 改名停车
    for gpath in "$gskills"/eo-*; do
      [ -L "$gpath" ] || continue
      name=$(basename "$gpath")
      case "$name" in *.v1-parked) continue;; esac
      if [ ! -d "$src/$name" ]; then
        echo "PARKED $name $(readlink "$gpath")" >> "$manifest"
        mv "$gpath" "$gpath.v1-parked"; parked=$((parked+1))
      fi
    done
    echo "swap 完成: 改指 ${swapped} 个 / 新增 ${added} 个 / 停车 ${parked} 个 (v1 独有)"
    echo "全局现为 v2 → $src ; 还原: sh test-install.sh restore"
    ;;
  restore)
    gskills="$HOME/.claude/skills"
    manifest="$EO_HOME/v2-swap-manifest.txt"
    [ -f "$manifest" ] || { echo "无 swap manifest, 无需还原。" >&2; exit 1; }
    while IFS=" " read -r op name target; do
      gpath="$gskills/$name"
      case "$op" in
        RELINK) rm -f "$gpath"; ln -s "$target" "$gpath";;
        ADDED)  rm -f "$gpath";;
        PARKED) rm -f "$gpath"; mv "$gpath.v1-parked" "$gpath" 2>/dev/null || ln -s "$target" "$gpath";;
      esac
    done < "$manifest"
    rm "$manifest"
    echo "已还原全局 skills 到 swap 之前的状态。"
    ;;
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
    if [ -f "$EO_HOME/v2-swap-manifest.txt" ]; then
      echo "swap 状态: 生效中 (全局 → $src); 还原: sh test-install.sh restore"
    else
      echo "swap 状态: 未启用"
    fi
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
