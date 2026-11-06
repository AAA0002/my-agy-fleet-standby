#!/bin/bash
# ==============================================================================
# AAA AUTO Smart Session Resume & Remote Control Daemon Setup
# Compatible with: Linux VPS, Instabox VM, Cloudflare Nodes, and Android Termux
# ==============================================================================

set -e

echo "=============================================================="
echo "  🚀 Installing AAA Smart Session Resume & Remote Control"
echo "=============================================================="

USER_HOME="${HOME:-/data/home}"
BIN_DIR="$USER_HOME/.local/bin"
mkdir -p "$BIN_DIR"

# 1. Detect Environment (Termux vs Linux VPS)
IS_TERMUX=false
if [ -n "$TERMUX_VERSION" ] || [ "$(uname -o 2>/dev/null)" = "Android" ] || [ -f "/system/bin/app_process" ]; then
    IS_TERMUX=true
    echo "📱 Android Termux / Mobile environment detected."
    TERMUX_BIN="/data/data/com.termux/files/usr/bin"
    [ -d "$TERMUX_BIN" ] && BIN_DIR="$TERMUX_BIN"
else
    echo "🖥️ Linux VPS / Cloud VM environment detected ($(uname -m))."
fi

# 2. Configure Lag-Free Mobile TMUX (~/.tmux.conf)
echo "⚡ Configuring lag-free mobile TMUX (~/.tmux.conf)..."
cat << 'TMUX_CONF' > "$USER_HOME/.tmux.conf"
# ==============================================================================
# AAA AUTO Mobile & Termux Optimized TMUX Configuration
# ZERO Touch Lag | Dual Prefix (Ctrl-a / Ctrl-b) | Effortless Detach & Auto-Resize
# ==============================================================================

# Dual Prefix: Support both Ctrl-b and Ctrl-a (Ctrl-a is 10x easier on mobile)
set -g prefix C-b
set -g prefix2 C-a
bind C-a send-prefix -2

# Disable mouse completely - prevents Termux touches from sending laggy escape codes
set -g mouse off

# 0ms escape delay for instant keystrokes and arrows
set -s escape-time 0
set -sg escape-time 0
set -g repeat-time 0

# Terminal geometry & colors
set -g default-terminal "xterm-256color"
set -ga terminal-overrides ",xterm-256color:Tc"
set -g history-limit 20000

# Aggressive window resizing for mobile screens (Samsung Galaxy A30)
setw -g aggressive-resize on
set -g window-size latest
set -g focus-events on
set-hook -g client-attached 'resize-window -A'

# Window numbering
set -g base-index 1
setw -g pane-base-index 1
set -g renumber-windows on

# Minimal, clean status bar with clear exit/detach instructions
set -g status on
set -g status-interval 10
set -g status-style bg=black,fg=cyan
set -g status-left "#[fg=green,bold]⚡ [AGY] #[default]"
set -g status-right "#[fg=colour245]Detach: #[fg=green,bold]Alt+d #[fg=colour245]or #[fg=yellow,bold]Ctrl+a d #[fg=colour240]| #[fg=cyan]%H:%M"
set -g status-left-length 20
set -g status-right-length 55

# Clean disconnect and persistence (Never die on process exit)
set-option -g destroy-unattached off
set-option -g detach-on-destroy off
set -g visual-bell off
set -g bell-action none

# ==============================================================================
# MOBILE & TERMUX EXIT / DETACH SHORTCUTS (NO CHORD STRUGGLES)
# ==============================================================================

# 1. Instant 1-Key Detach (No prefix needed!)
# Press Alt+d or Alt+q on Termux extra keys row to instantly detach safely
bind -n M-d detach-client
bind -n M-q detach-client

# 2. Standard Prefix Detach (Press Ctrl+a then d, or Ctrl+b then d)
bind d detach-client
bind q detach-client

# 3. Clean Session Exit / Kill
# Press Ctrl+a then K to completely kill the session cleanly
bind K confirm-before -p "Kill session #S? (y/n)" kill-session
bind X confirm-before -p "Kill session #S? (y/n)" kill-session

# 4. Reload configuration on the fly
bind r source-file ~/.tmux.conf \; display-message "Tmux config reloaded!"
TMUX_CONF

# Reload tmux server if already running
tmux source-file "$USER_HOME/.tmux.conf" 2>/dev/null || true

# 3. Create Smart Entrypoint Script (agy-entry)
echo "⚡ Installing agy-entry smart session switcher..."
cat << 'ENTRY_SCRIPT' > "$BIN_DIR/agy-entry"
#!/bin/bash
# ==============================================================================
# AAA AUTO Smart Antigravity Session & Remote Control Entrypoint
# Zero Lag | Auto-Session Resume | Mobile-First Resilience (Samsung Galaxy A30)
# ==============================================================================

# 1. Locate true compiled agy binary
REAL_AGY="/data/home/.local/bin/agy"
if [ ! -x "$REAL_AGY" ]; then
    REAL_AGY="$(which agy 2>/dev/null)"
fi

# 2. Ensure Antigravity Remote Control Daemon (aaa-hub-vm) is active
if command -v systemctl >/dev/null 2>&1; then
    if ! systemctl --user is-active antigravity-cli-daemon.service >/dev/null 2>&1; then
        systemctl --user restart antigravity-cli-daemon.service >/dev/null 2>&1 || true
    fi
else
    if ! pgrep -f "agy remote-control serve" >/dev/null 2>&1; then
        nohup "$REAL_AGY" remote-control serve >/dev/null 2>&1 &
    fi
fi

# 3. If user passes explicit maintenance or non-interactive subcommands, pass through
if [ "$#" -gt 0 ] && [ "$1" != "-c" ] && [ "$1" != "--continue" ]; then
    case "$1" in
        mcp|plugin|plugins|update|models|agent|agents|remote-control|changelog|help|acp)
            exec "$REAL_AGY" "$@"
            ;;
    esac
fi

# 4. Handle execution when ALREADY inside a tmux pane
if [ -n "$TMUX" ]; then
    [ -d "/data/workspace/AAA_AUTO" ] && cd "/data/workspace/AAA_AUTO" || cd "$HOME"
    
    # Check if another agy process is already active in background or another pane
    AGY_PID="$(pgrep -f "agy.*--continue" 2>/dev/null | grep -v "$$" | head -n 1)"
    if [ -n "$AGY_PID" ]; then
        echo "⚡ Antigravity AI is already running in this tmux session (PID: $AGY_PID)."
        echo "👉 If you see the prompt below, just type your prompt directly."
        echo "👉 If you want to restart afresh, run: tmux kill-session -t agy && agy"
        exit 0
    fi

    # Not currently running in this pane, start it immediately
    exec "$REAL_AGY" --continue "$@"
fi

# 5. When connecting from OUTSIDE tmux (e.g. fresh SSH from phone Termux):
[ -d "/data/workspace/AAA_AUTO" ] && cd "/data/workspace/AAA_AUTO" || cd "$HOME"

if tmux has-session -t agy 2>/dev/null; then
    # Detach any stale/zombie background clients and attach with active mobile dimensions
    exec tmux attach-session -d -t agy
else
    # Create persistent, mobile-optimized session
    exec tmux new-session -s agy "bash -c 'exec $REAL_AGY --continue; exec bash'"
fi
ENTRY_SCRIPT
chmod +x "$BIN_DIR/agy-entry"

# Also symlink / copy to /usr/local/bin if root/sudo available
if [ "$(id -u)" -eq 0 ]; then
    cp -f "$BIN_DIR/agy-entry" /usr/local/bin/agy-entry 2>/dev/null || true
    chmod +x /usr/local/bin/agy-entry 2>/dev/null || true
elif command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
    sudo cp -f "$BIN_DIR/agy-entry" /usr/local/bin/agy-entry 2>/dev/null || true
    sudo chmod +x /usr/local/bin/agy-entry 2>/dev/null || true
fi

# 4. Configure Remote Control Daemon
INSTANCE_NAME="aaa-hub-$(hostname 2>/dev/null || echo 'node')"
echo "⚡ Checking Remote Control daemon for instance: $INSTANCE_NAME..."
if command -v systemctl >/dev/null 2>&1; then
    if agy remote-control status 2>&1 | grep -q "active"; then
        echo "✅ Remote Control daemon is already active."
    else
        agy remote-control start --name "$INSTANCE_NAME" 2>/dev/null || true
        echo "✅ Remote Control daemon started via systemd."
    fi
else
    if $IS_TERMUX; then
        echo "📱 Phone detected (Samsung A30). Stopping any local remote-control to enforce Zero Phone Load..."
        agy remote-control stop 2>/dev/null || true
        pkill -f "agy remote-control" 2>/dev/null || true
        echo "✅ Phone remote-control stopped. Remote control runs exclusively on Cloud VM."
    else
        # Non-systemd Linux fallback
        if ! pgrep -f "agy remote-control serve" >/dev/null 2>&1; then
            nohup agy remote-control serve >/dev/null 2>&1 &
            echo "✅ Remote Control background daemon started (PID: $!)."
        else
            echo "✅ Remote Control background daemon already running."
        fi
    fi
fi

# 5. Update ~/.bashrc Aliases & Profile
BASHRC="$USER_HOME/.bashrc"
touch "$BASHRC"

# Clean old duplicate aliases
sed -i '/alias agy=/d' "$BASHRC" 2>/dev/null || true
sed -i '/alias agy-direct=/d' "$BASHRC" 2>/dev/null || true
sed -i '/alias agy-remote=/d' "$BASHRC" 2>/dev/null || true
sed -i '/alias resume-session=/d' "$BASHRC" 2>/dev/null || true
sed -i '/alias new-session=/d' "$BASHRC" 2>/dev/null || true
sed -i '/alias agy-attach=/d' "$BASHRC" 2>/dev/null || true

cat << 'BASHRC_SNIPPET' >> "$BASHRC"

# AAA AUTO Smart Session Resume & Remote Control
alias agy='agy-entry'
alias agy-direct='/data/home/.local/bin/agy'
alias agy-remote='agy remote-control status'
alias resume-session='agy-entry'
alias new-session='agy-entry'
alias agy-attach='tmux attach -d -t agy 2>/dev/null || tmux attach'
alias agy-fix='agy remote-control start && tmux attach -d -t agy'
alias agy-restart='tmux kill-session -t agy 2>/dev/null; agy'
BASHRC_SNIPPET

echo "=============================================================="
echo "  🎉 SMART SESSION RESUME & REMOTE CONTROL INSTALLED!"
echo "  • Run 'agy'        -> Instantly resume active session"
echo "  • Run 'agy-direct' -> Run native CLI without tmux"
echo "  • Remote Control   -> Active at https://antigravity.google.com"
echo "  • Touch Lag        -> 100% Eliminated (mouse off)"
echo "=============================================================="
