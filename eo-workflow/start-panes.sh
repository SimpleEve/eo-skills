#!/usr/bin/env bash
# eo-workflow pane 启动脚本
# 用法: bash start-panes.sh <phase> [--with-review]
# phase: module-init | change | implement | archive | full
# --with-review: change / full 阶段额外启动 review pane 承载 eo-change-review

set -euo pipefail

PHASE="${1:?用法: start-panes.sh <phase> (module-init|change|implement|archive|full) [--with-review]}"
WITH_REVIEW=0
if [[ "${2:-}" == "--with-review" ]]; then
  WITH_REVIEW=1
fi
SESSION="$(tmux display-message -p '#{session_name}')"
CWD="$(pwd)"

# ─── Agent 启动命令（可按需修改 model 和 reasoning effort）───────────────
CLAUDE_CMD="cd \"$CWD\" && claude --dangerously-skip-permissions"
CODEX_IMPLEMENT="cd \"$CWD\" && codex --dangerously-bypass-approvals-and-sandbox -m gpt-5.4 -c model_reasoning_effort=\"medium\""
CODEX_REVIEW="cd \"$CWD\" && codex --dangerously-bypass-approvals-and-sandbox -m gpt-5.4 -c model_reasoning_effort=\"xhigh\""
CODEX_TEST="cd \"$CWD\" && codex --dangerously-bypass-approvals-and-sandbox -m gpt-5.4 -c model_reasoning_effort=\"low\""

# ─── 辅助函数 ─────────────────────────────────────────────────────────────

create_pane() {
  local label="$1"
  local agent_cmd="$2"

  if tmux-bridge resolve "$label" >/dev/null 2>&1; then
    echo "⏭  pane '$label' 已存在，跳过"
    return
  fi

  local pane_id
  pane_id="$(tmux split-window -h -t "$SESSION" -c "$CWD" -P -F '#{pane_id}')"

  tmux-bridge name "$pane_id" "$label" >/dev/null 2>&1 || true
  tmux select-pane -t "$pane_id" -T "$label"

  tmux send-keys -t "$pane_id" -l -- "$agent_cmd"
  tmux send-keys -t "$pane_id" Enter

  echo "✅  created pane '$label' ($pane_id)"
}

# ─── 按 phase 创建 pane ──────────────────────────────────────────────────
# module-init: 作者在 spec pane 用 /eo-module-init（含 spec + spec-review），review pane 用于 spec-review
# change:      作者在 change pane 用 /eo-change，不需要独立 review pane（change 自澄清）
# implement:   implement / test / review 三 pane 循环
# archive:     单 pane，主 orchestrator 直接触发 /eo-archive
# full:        全流程

case "$PHASE" in
  module-init)
    create_pane spec    "$CLAUDE_CMD"
    create_pane review  "$CODEX_REVIEW"
    ;;
  change)
    create_pane change  "$CLAUDE_CMD"
    if [[ $WITH_REVIEW -eq 1 ]]; then
      create_pane review  "$CODEX_REVIEW"
    fi
    ;;
  implement)
    create_pane implement "$CODEX_IMPLEMENT"
    create_pane test      "$CODEX_TEST"
    create_pane review    "$CODEX_REVIEW"
    ;;
  archive)
    # archive 由主 orchestrator 直接执行，不需要额外 pane
    ;;
  full)
    create_pane spec      "$CLAUDE_CMD"
    create_pane change    "$CLAUDE_CMD"
    create_pane implement "$CODEX_IMPLEMENT"
    create_pane test      "$CODEX_TEST"
    create_pane review    "$CODEX_REVIEW"
    ;;
  *)
    echo "❌ 未知阶段: $PHASE（可选: module-init | change | implement | archive | full）" >&2
    exit 1
    ;;
esac

# ─── 应用布局 ─────────────────────────────────────────────────────────────

case "$PHASE" in
  module-init)
    tmux select-layout -t "$SESSION" even-horizontal
    ;;
  implement)
    tmux select-layout -t "$SESSION" main-vertical
    ;;
  full)
    tmux select-layout -t "$SESSION" tiled
    ;;
esac

sleep 3
echo "🚀 pane 就绪 ($PHASE)"
