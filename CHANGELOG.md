# Changelog - AAA AUTO

All notable changes, architectural decisions, and modifications for the `AAA AUTO` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]
### Added
- Restored automation codebase from backup into `/root/projects/AAA_AUTO`:
  - Telegram userbot core (`userbot_refresher.py`, `login_account.py`, `phone_detector.py`, `proxy_manager.py`, `backup_manager.py`).
  - Process supervisors and lifecycle scripts (`bot_supervisor.sh`, `start_userbot.sh`, `stop_userbot.sh`, `restore.sh`).
  - Monitoring & metrics engines (`bep20_onchain_watcher.py`, `multichain_onchain_watcher.py`, `daily_profit_reporter.py`, `batch_atf_miner.py`, `refresh_fleet_tokens.py`, `update_dashboard_compact.py`).
  - Tunnel and deployment helpers (`cloudflared_tunnel.sh`, `deploy_both_cf_workers.py`, `my_agy_bot.service`).
  - Python dependency definitions (`requirements.txt`).
- Added Rule 5 ("Zero-Trust Ephemeral Infrastructure") to `AGENTS.md`, cementing the core principle to never rely on volatile VPS or local storage.
- Fully installed all Python dependencies from `requirements.txt` (`Telethon`, `phonenumbers`, `pyaes`, `sentry-sdk`, `aiohttp`, etc.).
- Launched 24/7 immortal supervisor daemon (`bot_supervisor.sh`) inside persistent `tmux` session `telegram_bot`.
- Verified live Multi-Account userbot fleet resumption across 13 accounts with 3-node Cloudflare edge synchronization.
- Updated `README.md` with full architectural breakdown, component inventory, and operational guidelines.
- Fixed hardcoded VPS path in `update_dashboard_compact.py` to use dynamic project directory resolution.
- Updated `.gitignore` to strictly isolate and safeguard private keys, fleet tokens, and credential files.
- Applied executable permissions across shell and Python execution scripts.
- Initialized local Git repository with `.gitignore`.
- Configured project rules and isolation boundary in `AGENTS.md`.
