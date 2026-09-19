#!/usr/bin/env bash
# =======================================================
# 24/7 IMMORTAL ANTIGRAVITY CLI RUNNER (TMUX WRAPPER)
# Keeps Antigravity running 24/7 even when Termux closes!
# =======================================================

SESSION="antigravity_cli"
AGY_BIN="/home/arif2743/.local/bin/agy"

# If already inside a tmux window, execute agy directly
if [ -n "$TMUX" ]; then
    exec "$AGY_BIN" "$@"
fi

# If persistent tmux session exists, reattach cleanly
if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "⚡ Re-attaching to your 24/7 persistent Antigravity session (immune to Termux closure)..."
    exec tmux attach-session -t "$SESSION"
else
    echo "🚀 Starting new 24/7 persistent Antigravity session in tmux..."
    exec tmux new-session -s "$SESSION" "$AGY_BIN" "$@"
fi
