#!/usr/bin/env bash
# deploy_tgcloud.sh
# Deploys AAA Admin Bot to Telegram Serverless infrastructure

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/tgcloud_admin_bot"

if [ ! -d "$PROJECT_DIR" ]; then
  echo "❌ Project directory $PROJECT_DIR not found."
  exit 1
fi

TOKEN="$1"
if [ -z "$TOKEN" ]; then
  # Check if in .env
  if [ -f "$SCRIPT_DIR/.env" ]; then
    TOKEN=$(grep -E "^TGCLOUD_TOKEN=" "$SCRIPT_DIR/.env" | cut -d '=' -f2- | tr -d '"' | tr -d "'")
  fi
fi

if [ -n "$TOKEN" ]; then
  echo "🔑 Setting Telegram Serverless Access Token..."
  mkdir -p "$PROJECT_DIR/.tgcloud"
  cat <<EOF > "$PROJECT_DIR/.tgcloud/credentials"
{
  "token": "$TOKEN"
}
EOF
  chmod 600 "$PROJECT_DIR/.tgcloud/credentials"
fi

cd "$PROJECT_DIR"

echo "📡 Checking Telegram Serverless status..."
npx tgcloud status

if [ -z "$TOKEN" ] && [ ! -f ".tgcloud/credentials" ]; then
  echo ""
  echo "⚠️ Telegram Serverless Access Token required!"
  echo "Steps to get your token from @BotFather:"
  echo "1. Open Telegram -> @BotFather -> /mybots"
  echo "2. Select @myagyai (or your bot) -> Tap 'Serverless'"
  echo "3. Turn Serverless ON -> Tap 'CLI Access' -> 'Access token'"
  echo "4. Run: ./deploy_tgcloud.sh 'app<id>:<secret>'"
  exit 0
fi

echo "🚀 Deploying modules to Telegram Serverless cloud..."
npx tgcloud push

echo "📦 Applying database schema migrations..."
npx tgcloud migrate

echo "✅ Telegram Serverless Admin Bot deployed successfully!"
