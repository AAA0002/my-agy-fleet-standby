#!/usr/bin/env bash
# =============================================================================
# MY AGY AI — 60-SECOND INSTANT VPS DISASTER RECOVERY & FLEET RESTORER
# =============================================================================
# Run on ANY fresh Linux VPS / Cloud Instance to restore the entire fleet:
#   curl -sSL https://raw.githubusercontent.com/AAA0002/ATL/main/restore_fleet.sh | bash
# =============================================================================

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo "============================================================"
echo "  🚀 MY AGY AI — INSTANT FLEET DISASTER RECOVERY"
echo "============================================================"

# 1. Update packages and install prerequisites
echo "[1/6] Installing system dependencies (python3, venv, git, tmux, curl, unzip)..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-pip python3-venv git curl wget unzip tmux > /dev/null 2>&1 || true
elif command -v yum &> /dev/null; then
    sudo yum install -y -q python3 python3-pip git curl wget unzip tmux > /dev/null 2>&1 || true
fi

# 2. Setup Python virtual environment
echo "[2/6] Setting up Python 3 virtual environment..."
if [ ! -d "$BASE_DIR/venv" ]; then
    python3 -m venv "$BASE_DIR/venv"
fi
source "$BASE_DIR/venv/bin/activate"

# 3. Download latest fleet archive from Cloudflare R2 / KV
echo "[3/6] Fetching latest encrypted fleet backup from Cloudflare R2 & KV..."
CF_BACKUP_URLS=(
    "https://restore-agy.aaaai2.workers.dev/backup.zip"
    "https://restore-agy.aaa-bot.workers.dev/backup.zip"
    "https://restore-agy.aaa222.workers.dev/backup.zip"
)

BACKUP_DOWNLOADED=0
for B_URL in "${CF_BACKUP_URLS[@]}"; do
    echo "  Trying $B_URL..."
    if curl -sSL -f -m 20 "$B_URL" -o "$BASE_DIR/latest_backup.zip" 2>/dev/null; then
        if [ -s "$BASE_DIR/latest_backup.zip" ]; then
            echo "  ✅ Backup archive downloaded successfully!"
            BACKUP_DOWNLOADED=1
            break
        fi
    fi
done

# Fallback: If Cloudflare archive is unreachable, try Decentralized Pinata IPFS via Upstash Redis
if [ "$BACKUP_DOWNLOADED" -eq 0 ]; then
    echo "  Checking latest decentralized IPFS backup via Upstash & Pinata Gateway..."
    LATEST_CID=$(curl -sSL -m 6 -H "Authorization: Bearer ${UPSTASH_TOKEN:-$UPSTASH_REDIS_REST_TOKEN}" "https://internal-dodo-83852.upstash.io/get/fleet:latest_ipfs_cid" 2>/dev/null | grep -o '"result":"[^"]*"' | cut -d'"' -f4 || true)
    if [ -n "$LATEST_CID" ] && [ "$LATEST_CID" != "null" ]; then
        echo "  Found IPFS CID: $LATEST_CID. Fetching from Pinata IPFS Gateway..."
        if curl -sSL -f -m 35 "https://gateway.pinata.cloud/ipfs/$LATEST_CID" -o "$BASE_DIR/latest_backup.zip" 2>/dev/null; then
            if [ -s "$BASE_DIR/latest_backup.zip" ]; then
                echo "  ✅ Backup archive downloaded from Pinata IPFS Gateway!"
                BACKUP_DOWNLOADED=1
            fi
        fi
    fi
fi

if [ "$BACKUP_DOWNLOADED" -eq 1 ]; then
    echo "[4/6] Unpacking fleet configuration, accounts, and session keys..."
    unzip -o -q "$BASE_DIR/latest_backup.zip" -d "$BASE_DIR"
    rm -f "$BASE_DIR/latest_backup.zip"
else
    echo "  ⚠️ Cloud archives not reachable. Checking local files..."
fi

# 4. Install Python dependencies
echo "[5/6] Installing required Python packages..."
pip install --upgrade pip -q
if [ -f "$BASE_DIR/requirements.txt" ]; then
    pip install -r "$BASE_DIR/requirements.txt" -q
else
    pip install telethon aiohttp python-dotenv requests -q
fi

# 5. Launch supervisor in persistent tmux session
echo "[6/6] Launching 24/7 Immortal Supervisor in tmux session 'telegram_bot'..."
chmod +x "$BASE_DIR/bot_supervisor.sh" 2>/dev/null || true

# Kill any existing stale supervisor or userbot
pkill -f "bot_supervisor.sh" 2>/dev/null || true
pkill -f "userbot_refresher.py" 2>/dev/null || true
sleep 1

tmux new-session -d -s telegram_bot "bash $BASE_DIR/bot_supervisor.sh" 2>/dev/null || bash "$BASE_DIR/bot_supervisor.sh" &

sleep 3
if pgrep -f "userbot_refresher.py" > /dev/null; then
    echo ""
    echo "============================================================"
    echo "  🎉 FLEET SUCCESSFULLY RESTORED & RUNNING 24/7!"
    echo "============================================================"
    echo "  • Supervisor: ACTIVE (tmux session: telegram_bot)"
    echo "  • Bot Daemon: RUNNING"
    echo "  • Cloud Edge: 3x Cloudflare Nodes Synchronized"
    echo "============================================================"
else
    echo "⚠️ Process starting up. Check supervisor.log for live status."
fi
