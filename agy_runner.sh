#!/usr/bin/env bash
# =======================================================
# 24/7 IMMORTAL ANTIGRAVITY CLI RUNNER (TMUX WRAPPER)
# Keeps Antigravity running 24/7 even when Termux closes!
# Automatically connects Google Cloud Remote Control V2!
# =======================================================

SESSION="antigravity_cli"
AGY_BIN="/home/arif2743/.local/bin/agy"

# If already inside a tmux window, execute agy directly with remote control
if [ -n "$TMUX" ]; then
    exec "$AGY_BIN" --remote-control "$@"
fi

# If persistent tmux session exists, reattach cleanly
if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "⚡ Re-attaching to your 24/7 persistent Antigravity session (immune to Termux closure)..."
    echo "📡 Remote Control is active & connected to Google Cloud WebChannel."
    exec tmux attach-session -t "$SESSION"
else
    echo "🚀 Starting new 24/7 persistent Antigravity session in tmux with Remote Control..."
    exec tmux new-session -s "$SESSION" "$AGY_BIN --remote-control" "$@"
fi
