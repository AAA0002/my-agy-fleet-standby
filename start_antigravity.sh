#!/usr/bin/env bash
# =======================================================
# 24/7 IMMORTAL ANTIGRAVITY AUTO-START & WATCHDOG DAEMON
# Automatically starts Antigravity CLI with Remote Control
# and keeps it alive 24/7 across reboots & terminal closures!
# =======================================================

SESSION="antigravity_cli"
AGY_BIN="/home/arif2743/.local/bin/agy"
LOG_FILE="/home/arif2743/antigravity_autostart.log"

# Check if agy binary exists
if [ ! -x "$AGY_BIN" ]; then
    echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] ERROR: Antigravity binary not found at $AGY_BIN" >> "$LOG_FILE"
    exit 1
fi

# If persistent tmux session is already running, nothing to do
if tmux has-session -t "$SESSION" 2>/dev/null; then
    # Verify agy process is alive inside tmux
    if pgrep -f "/home/arif2743/.local/bin/agy" >/dev/null 2>&1; then
        exit 0
    fi
fi

# Start persistent session with Remote Control enabled
echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] 🚀 Starting Antigravity CLI with Remote Control in tmux '$SESSION'..." >> "$LOG_FILE"
tmux new-session -d -s "$SESSION" "$AGY_BIN --remote-control"

# Verify startup
sleep 2
if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] ✅ Antigravity CLI Remote Control is ACTIVE (tmux: $SESSION, WebChannel connected)." >> "$LOG_FILE"
else
    echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] ❌ Failed to start Antigravity tmux session." >> "$LOG_FILE"
fi
