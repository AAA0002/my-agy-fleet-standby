# MY AGY AI — Autonomous Multi-Bot Cloud Fleet Engine

Production multi-chain cloud automation system combining **Telegram MTProto userbots**, **Cloudflare 24/7 Edge Gateways**, and **Render Fallback Compute**.

---

## 🏗️ Architecture

```
                  ┌─────────────────────────────────┐
                  │    Telegram Users & Webhooks    │
                  └────────────────┬────────────────┘
                                   │ HTTPS
                                   ▼
        ┌─────────────────────────────────────────────────────┐
        │        CLOUDFLARE WORKERS (The 24/7 Edge Brain)     │
        │ • Dual-Node High Availability:                      │
        │   - Node 1: https://restore-agy.aaaai2.workers.dev  │
        │   - Node 2: https://restore-agy.aaa-bot.workers.dev │
        │ • 0ms cold starts, 100% cloud uptime                │
        │ • Mini-App 24h Token Vault in Cloudflare KV         │
        │ • Real-time Binance Price Oracle (/api/rates)       │
        │ • Workers AI (Llama 3.2 3B Instruct) (/ai)          │
        │ • Dual-node auto failover & dead-man sentinel       │
        └──────────────────────────┬──────────────────────────┘
                                   │ Cloud Sync
                                   ▼
        ┌─────────────────────────────────────────────────────┐
        │         LINUX CLOUD VPS (The Cloud Muscle)          │
        │ • Telethon MTProto Engine (userbot_refresher.py)    │
        │ • 13 Multi-Chain Accounts                           │
        │ • Goal #1: BNB Galaxy (10 daily tasks & auto-WD)    │
        │ • Tier-1 US Headers & human interaction delays      │
        │ • On-chain BEP-20 Watcher & BscScan verification    │
        └──────────────────────────┬──────────────────────────┘
                                   │ Hot Standby
                                   ▼
        ┌─────────────────────────────────────────────────────┐
        │             RENDER CLOUD RUNNER (Fallback)          │
        │ • Autonomous standby environment via Render API     │
        └─────────────────────────────────────────────────────┘
```

---

## 🚀 Key Modules

* `userbot_refresher.py`: Core MTProto Telethon engine managing 13 fleet accounts.
* `deploy_both_cf_workers.py`: Dual-account Cloudflare Edge deployer & synchronizer.
* `bep20_onchain_watcher.py`: Real-time BSC RPC monitor for incoming deposits to `0xfda4182001672b9f0f09e2118242e543e35ed5ce`.
* `daily_profit_reporter.py`: Automated 00:00 UTC financial accounting report.
* `custom_bot_registry.json`: Extensible plug-and-play earning bot registry.

---

## 🔒 Security & Privacy

* Sensitive files (`.env`, `accounts.json`, `*.session`) are strictly ignored via `.gitignore` and kept on secure cloud nodes.
* Dual receipts route to **[AAA T Wallet Payouts](https://t.me/+oN8uefSRYWUyM2Fl)** and Admin DM.
