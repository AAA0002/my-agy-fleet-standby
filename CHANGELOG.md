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
- Updated `.gitignore` to strictly isolate and safeguard private keys, fleet tokens, and credential files.
- Applied executable permissions across shell and Python execution scripts.
- Initialized local Git repository with `.gitignore`.
- Configured project rules and isolation boundary in `AGENTS.md`.
