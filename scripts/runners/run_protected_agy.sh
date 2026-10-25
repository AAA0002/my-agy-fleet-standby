#!/bin/bash
# =============================================================================
# PERSISTENT ANTIGRAVITY RUNNER WITH AUTOMATIC WAKELOCK & TMUX PROTECTION
# =============================================================================
# Prevents Android 11 / Samsung from killing Antigravity when screen locks
# or Termux goes to background.

# 1. Keep CPU awake via Termux WakeLock bridge
if [ -x /data/data/com.termux/files/usr/bin/termux-wake-lock ]; then
    /data/data/com.termux/files/usr/bin/termux-wake-lock 2>/dev/null
    echo "⚡ Termux wake lock held (CPU will not sleep)"
fi

# 2. Check if tmux session already exists
if tmux has-session -t agy 2>/dev/null; then
    echo "🔄 Existing Antigravity session found! Reconnecting..."
    exec tmux attach-session -t agy
else
    echo "🚀 Launching protected Antigravity session in tmux..."
    exec tmux new-session -s agy "/usr/local/bin/agy"
fi
