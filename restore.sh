#!/bin/bash
# =======================================================
# MY AGY AI - 1-Click Disaster Recovery & Fleet Bootstrapper
# Compatible with both Linux VPS (Ubuntu/Debian) & Android Termux
# =======================================================

set -e

echo "======================================================"
echo "  🚀 Restoring MY AGY AI Cloud Fleet & Antigravity"
echo "======================================================"

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

# 1. Detect environment and install packages
echo "📦 Checking system dependencies..."
if command -v pkg &> /dev/null; then
    echo "📱 Android Termux environment detected."
    pkg update -y && pkg install -y python tmux git unzip curl
elif command -v apt-get &> /dev/null; then
    echo "🖥️ Linux VPS environment detected."
    if [ "$(id -u)" -eq 0 ]; then
        apt-get update -y && apt-get install -y python3 python3-venv python3-pip tmux unzip curl
    else
        sudo apt-get update -y && sudo apt-get install -y python3 python3-venv python3-pip tmux unzip curl || true
    fi
fi

# 2. Restore Antigravity Session & OAuth Tokens
if [ -d "antigravity_session" ]; then
    echo "🔑 Restoring Antigravity session tokens & authorization..."
    mkdir -p "$HOME/.gemini/antigravity-cli"
    cp -rf antigravity_session/* "$HOME/.gemini/antigravity-cli/" 2>/dev/null || true
    chmod 600 "$HOME/.gemini/antigravity-cli/antigravity-oauth-token" 2>/dev/null || true
    echo "✅ Antigravity session restored! Authorization active."
fi

# 2.1 Restore Cloudflare Tunnel Configuration
if [ -d "cloudflared_config" ]; then
    echo "🌐 Restoring Cloudflare Tunnel configurations..."
    mkdir -p "$HOME/.cloudflared"
    cp -rf cloudflared_config/* "$HOME/.cloudflared/" 2>/dev/null || true
    chmod 600 "$HOME/.cloudflared"/*.json 2>/dev/null || true
    echo "✅ Cloudflare Tunnel config restored!"
fi

# 3. Ensure PATH includes ~/.local/bin
export PATH="$HOME/.local/bin:$PATH"
if [ -f "$HOME/.bashrc" ] && ! grep -q '\.local/bin' "$HOME/.bashrc"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

# 4. Install Antigravity CLI if missing
if ! command -v agy &> /dev/null; then
    echo "⚡ Downloading and installing Antigravity CLI..."
    curl -fsSL https://antigravity.google/cli/install.sh | bash || true
fi

# 5. Setup Python Virtual Environment for the Bot Fleet
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv 2>/dev/null || python -m venv venv 2>/dev/null || true
fi

# 6. Install Python requirements
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    if [ -f "venv/bin/pip" ]; then
        ./venv/bin/pip install -r requirements.txt
    else
        pip install --user -r requirements.txt 2>/dev/null || pip install -r requirements.txt
    fi
fi

# 7. Make all scripts executable
chmod +x bot_supervisor.sh start_userbot.sh stop_userbot.sh login_account.py phone_detector.py proxy_manager.py backup_manager.py restore.sh cloudflared_tunnel.sh 2>/dev/null || true

# 8. Start 24/7 background supervisor daemon in tmux
echo "⚡ Starting immortal 24/7 supervisor in tmux session: telegram_bot..."
./start_userbot.sh

echo "======================================================"
echo "  🎉 RESTORATION 100% COMPLETE!"
echo "  • Telegram Bot: Running 24/7 in tmux session: telegram_bot"
echo "  • Antigravity CLI: Ready to use ('agy')"
echo "  • Live Bot Logs: tail -f userbot.log"
echo "======================================================"
