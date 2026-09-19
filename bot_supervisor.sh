#!/usr/bin/env bash
# =======================================================
# 24/7 IMMORTAL SUPERVISOR FOR TELEGRAM USERBOT & AI BOT
# =======================================================

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$BASE_DIR/venv/bin/python" ]; then
    PYTHON_BIN="$BASE_DIR/venv/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON_BIN="$(command -v python3)"
else
    PYTHON_BIN="python"
fi
BOT_SCRIPT="$BASE_DIR/userbot_refresher.py"
SUPERVISOR_LOG="$BASE_DIR/supervisor.log"
BOT_LOG="$BASE_DIR/userbot.log"
LOCK_FILE="$BASE_DIR/supervisor.lock"
PID_FILE="$BASE_DIR/userbot.pid"

# Single-instance guarantee using supervisor.pid
SUPERVISOR_PID_FILE="$BASE_DIR/supervisor.pid"
if [ -f "$SUPERVISOR_PID_FILE" ]; then
    OLD_PID=$(cat "$SUPERVISOR_PID_FILE" 2>/dev/null)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        STAT=$(ps -p "$OLD_PID" -o stat= 2>/dev/null | tr -d ' ')
        if [ -n "$STAT" ] && [[ "$STAT" != *"Z"* ]]; then
            echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] Supervisor instance already running (PID: $OLD_PID). Exiting duplicate." >> "$SUPERVISOR_LOG"
            exit 0
        fi
    fi
fi

echo "$$" > "$SUPERVISOR_PID_FILE"

# Ignore HUP so closing Termux or SSH never affects this supervisor
trap '' HUP

echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] === Immortal Supervisor started (PID: $$) ===" >> "$SUPERVISOR_LOG"

while true; do
    # Rotate logs safely using copytruncate to prevent disk bloat (Lean 2GB VPS settings)
    for LOG_ITEM in "$BOT_LOG:2097152" "$SUPERVISOR_LOG:1048576" "$BASE_DIR/cloudflared.log:1048576"; do
        TARGET_FILE="${LOG_ITEM%%:*}"
        MAX_BYTES="${LOG_ITEM##*:}"
        if [ -f "$TARGET_FILE" ]; then
            F_SIZE=$(stat -c%s "$TARGET_FILE" 2>/dev/null || echo 0)
            if [ "$F_SIZE" -gt "$MAX_BYTES" ]; then
                cp "$TARGET_FILE" "${TARGET_FILE}.old" 2>/dev/null || true
                : > "$TARGET_FILE"
                echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] Auto-rotated large log: $(basename "$TARGET_FILE") ($((F_SIZE / 1024)) KB)" >> "$SUPERVISOR_LOG"
            fi
        fi
    done

    # Auto-prune .old files if free disk space is under 400MB
    AVAIL_KB=$(df -k "$BASE_DIR" 2>/dev/null | awk 'NR==2 {print $4}')
    if [ -n "$AVAIL_KB" ] && [ "$AVAIL_KB" -lt 409600 ]; then
        rm -f "$BASE_DIR"/*.old 2>/dev/null || true
    fi

    # Enforce strict 2-archive limit and clean temp pycache (2GB VPS protection)
    ZIP_COUNT=$(ls -1 "$BASE_DIR"/my_agy_ai_backup_*.zip 2>/dev/null | wc -l)
    if [ "$ZIP_COUNT" -gt 2 ]; then
        ls -1t "$BASE_DIR"/my_agy_ai_backup_*.zip | tail -n +3 | xargs -r rm -f 2>/dev/null || true
    fi

    # Auto-prune __pycache__, bytecode, stale temp files, and oversized tmux logs
    find "$BASE_DIR" -maxdepth 2 -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$BASE_DIR" -maxdepth 2 -type f \( -name "*.tmp*" -o -name "*.temp*" \) -mmin +30 -delete 2>/dev/null || true
    find "$BASE_DIR" -maxdepth 2 -type f -name "*.pyc" -delete 2>/dev/null || true
    find "$BASE_DIR" -maxdepth 1 -type f -name "tmux-*.log" -size +1M -delete 2>/dev/null || true
    find /tmp -maxdepth 1 -user "$(whoami)" -type f -mmin +720 -delete 2>/dev/null || true

    # Check if userbot_refresher.py is running and not a zombie
    IS_RUNNING=0
    LIVE_PIDS=$(pgrep -f "$BOT_SCRIPT" 2>/dev/null || true)
    for P in $LIVE_PIDS; do
        P_STAT=$(ps -p "$P" -o stat= 2>/dev/null | tr -d ' ')
        if [ -n "$P_STAT" ] && [[ "$P_STAT" != *"Z"* ]]; then
            IS_RUNNING=1
            echo "$P" > "$PID_FILE"
            break
        fi
    done

    if [ "$IS_RUNNING" -eq 0 ]; then
        echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] [HEAL] Userbot is down! Reviving process..." >> "$SUPERVISOR_LOG"
        
        # Launch userbot
        "$PYTHON_BIN" "$BOT_SCRIPT" >> "$BOT_LOG" 2>&1 &
        BOT_PID=$!
        echo "$BOT_PID" > "$PID_FILE"
        echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] [OK] Userbot launched with PID $BOT_PID" >> "$SUPERVISOR_LOG"
        
        # Brief pause to allow the bot to initialize
        sleep 5
    fi


    # Cloudflare Zero-Trust Tunnel Auto-Revival Watchdog
    if [ -f "$BASE_DIR/cloudflared_tunnel.sh" ] && ! pgrep -f "cloudflared tunnel" > /dev/null 2>&1; then
        bash "$BASE_DIR/cloudflared_tunnel.sh" start > /dev/null 2>&1 || true
    fi

    # Heartbeat interval
    sleep 15
done
