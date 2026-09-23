# AAA AUTO / MY AGY AI Automation Fleet

Autonomous task automation, multi-account Telegram fleet orchestration, and decentralized on-chain telemetry engine.

---

## 🏗️ System Architecture

### 1. Telegram Userbot Fleet & Automation Core
- **`userbot_refresher.py`**: Telethon-based multi-account runner automating mini-apps, webview tokens, airdrops, and channel interactions with proxy rotation.
- **`login_account.py`**: Interactive CLI for authenticating accounts into `accounts.json` with phone number normalization and string sessions.
- **`phone_detector.py`**: Multi-region phone detector and country flag resolver.
- **`proxy_manager.py`**: Per-account proxy assignment, fingerprint spoofing, and latency verification.
- **`batch_atf_miner.py`**: Autonomous mining and math captcha solver across fleet accounts.
- **`refresh_fleet_tokens.py`**: Background token and session renewal engine.

### 2. 24/7 Immortal Process Supervision
- **`bot_supervisor.sh`**: Robust background daemon ensuring zero downtime, automatic log rotation (`userbot.log` and `supervisor.log`), and PID-lock safeguards.
- **`start_userbot.sh`**: Spawns supervisor daemon inside detached `tmux` session (`telegram_bot`).
- **`stop_userbot.sh`**: Gracefully terminates running bot and supervisor instances.
- **`my_agy_bot.service`**: Systemd unit definition for host-level autostart.

### 3. On-Chain Financial Telemetry & Accounting
- **`multichain_onchain_watcher.py`**: Real-time vault watcher querying decentralized JSON-RPC nodes directly for BSC (BEP-20 BNB), Arbitrum One, and TON blockchain.
- **`bep20_onchain_watcher.py`**: Dedicated Binance Smart Chain transaction listener.
- **`daily_profit_reporter.py`**: Automated 00:00 UTC financial ledger calculating yields, Binance API fiat conversions (USD / BDT), and ledger disbursements.

### 4. Edge Mesh, Cloud Backup & Disaster Recovery
- **`backup_manager.py`**: Archives core code, sessions, and configurations, dispatching 1-click restore payloads to Telegram vault channels.
- **`restore.sh`**: 1-click self-contained disaster recovery bootstrapper.
- **`deploy_both_cf_workers.py`**: Cloudflare Workers edge mesh (3 redundant nodes) handling backup storage, dead-man sentinel, telemetry APIs, and Workers AI.
- **`cloudflared_tunnel.sh`**: Secure ingress tunnel without exposing public ports.

---

## 🔒 Security & Privacy Directives
- Sensitive configuration files (`.env`, `accounts.json`, `fleet_*.json`, `*.state.json`, `.cloudflare_credentials`) are strictly excluded from version control via `.gitignore`.
- Full project isolation maintained within `/root/projects/AAA_AUTO`.
- Changes and architectural updates audited in [CHANGELOG.md](./CHANGELOG.md).
