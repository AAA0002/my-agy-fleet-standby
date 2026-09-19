#!/usr/bin/env bash
# =======================================================
# START SCRIPT - 24/7 PERMANENT CLOUD RUNNER
# =======================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION_NAME="telegram_bot"
SUPERVISOR="$DIR/bot_supervisor.sh"

# Clean up stale dead PID files if old processes died
for PID_CHECK in "$DIR/supervisor.pid" "$DIR/userbot.pid"; do
    if [ -f "$PID_CHECK" ]; then
        OLD_P=$(cat "$PID_CHECK" 2>/dev/null)
        if [ -n "$OLD_P" ]; then
            P_STAT=$(ps -p "$OLD_P" -o stat= 2>/dev/null | tr -d ' ')
            if [ -z "$P_STAT" ] || [[ "$P_STAT" == *"Z"* ]]; then
                rm -f "$PID_CHECK"
            fi
        fi
    fi
done

# Check if tmux session already exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Telegram Bot supervisor is already running in persistent tmux session '$SESSION_NAME'."
    ps -ef | grep -E "tmux|bot_supervisor|userbot_refresher" | grep -v grep
    exit 0
fi

echo "Starting 24/7 Immortal Supervisor Daemon in persistent tmux session '$SESSION_NAME'..."
tmux new-session -d -s "$SESSION_NAME" "bash $SUPERVISOR"

# Verification loop (up to 6 seconds)
TMUX_ACTIVE=0
for i in {1..6}; do
    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        TMUX_ACTIVE=1
        break
    fi
    sleep 1
done

echo "=== Verification ==="
if [ "$TMUX_ACTIVE" -eq 1 ]; then
    echo "✅ Supervisor daemon is ACTIVE in detached tmux (100% immune to Termux or phone disconnect)."
else
    echo "❌ Failed to start tmux session."
fi

# Check for live non-zombie userbot
USERBOT_LIVE=0
LIVE_PIDS=$(pgrep -f "userbot_refresher.py" 2>/dev/null || true)
for P in $LIVE_PIDS; do
    P_STAT=$(ps -p "$P" -o stat= 2>/dev/null | tr -d ' ')
    if [ -n "$P_STAT" ] && [[ "$P_STAT" != *"Z"* ]]; then
        USERBOT_LIVE=1
        break
    fi
done

if [ "$USERBOT_LIVE" -eq 1 ]; then
    echo "✅ Telegram Userbot & AI Assistant are ACTIVE and running."
else
    echo "⏳ Userbot is initializing..."
fi

echo ""
echo "Processes running in cloud background:"
ps -ef | grep -E "tmux|bot_supervisor|userbot_refresher" | grep -v grep

