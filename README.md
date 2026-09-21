# MY AGY AI — Autonomous Multi-Bot Cloud Fleet Engine

Production multi-chain cloud automation system combining **Telegram MTProto automation**, **Cloudflare 3x Edge Gateways**, **GitHub Actions Cloud Token Refreshers**, and **Render Cloud AI Compute**.

---

## 🏗️ Architecture

```
                  ┌────────────────────────────────────────────────────────┐
                  │          Telegram Users, Mini Apps & Webhooks          │
                  └───────────────────────────┬────────────────────────────┘
                                              │ HTTPS
                                              ▼
        ┌──────────────────────────────────────────────────────────────────────────┐
        │                  CLOUDFLARE WORKERS (The 24/7 Edge Brain)                │
        │ • Triple-Node High Availability (3x Sharded Mesh):                       │
        │   - Node 1: https://restore-agy.aaaai2.workers.dev                       │
        │   - Node 2: https://restore-agy.aaa-bot.workers.dev                      │
        │   - Node 3: https://restore-agy.aaa222.workers.dev                       │
        │ • 0ms cold starts, 100% serverless cloud uptime                          │
        │ • Mini-App 24h Token Vault in Cloudflare KV                              │
        │ • Real-time Crypto Rates Oracle (/api/rates)                             │
        │ • R2 Disaster Recovery Storage: agy-fleet-backups (/backup.zip)          │
        │ • Autonomous Edge Farming: 15-min cron triggers across 13 accounts       │
        │ • D1 Serverless SQL Telemetry Database (fleet_logs)                      │
        └─────────────────────────────────────┬────────────────────────────────────┘
                                              │ 
                       ┌──────────────────────┴──────────────────────┐
                       ▼                                             ▼
        ┌───────────────────────────────┐             ┌─────────────────────────────┐
        │   GITHUB ACTIONS (Cloud MT)   │             │   RENDER CLOUD RUNNER (Ari) │
        │ • cloud_token_refresher.yml   │             │ • hermes-grok-cloud-agent   │
        │ • Every 12h automated MTProto │             │ • Google Gemini (14 keys)   │
        │ • Zero VPS reliance           │             │ • Groq LPU (3 keys)         │
        │ • Syncs tokens to CF KV & R2  │             │ • 24/7 Keepalive via cron   │
        └───────────────────────────────┘             └─────────────────────────────┘
```

---

## 🎯 Project Core Directives & Memory

* **Zero-VPS Reliance:** The fleet is 100% cloud-driven. If any VPS or local machine stops, GitHub Actions, Cloudflare edge workers, and Cron-Job.org continue autonomous farming and bot interactions.
* **ATF Miner Policy:** **Farming and Accumulation ONLY** (No withdrawals).
* **Strictly Free Tier:** $0 across Cloudflare, Upstash, GitHub, Render, Deno, Vercel, and Google Gemini.
* **Dashboard Theme:** Light theme by default, clean, responsive React 18 Mini App at `/dashboard`.

---

## 📬 Dedicated Telegram Channels & Vaults

* **Admin Direct Chat:** `6727787768` (`@Arif2743aaa`) — Interactive admin control & natural AI chat.
* **Private Payouts Channel:** `-1004402765950` (`PAYOUT_CHANNEL_ID`) — Withdrawal receipts, deposit verifications, accounting.
* **Disaster Recovery Backup Channel:** `-1004453515167` (`@myagyai`) — Full `.zip` archives with 1-click restore commands.
* **Community Supergroup:** `-1003973231307` (`AAA_T_WALLET_GROUP`) — Community alerts and fleet announcements.

---

## 💼 Vault & Settlement Wallets

* **BEP-20 (BNB, USDT):** `0xfda4182001672b9f0f09e2118242e543e35ed5ce`
* **Arbitrum One (STONES):** `0xfda4182001672b9f0f09e2118242e543e35ed5ce`
* **TON (Account 1 Main / Binance):** `UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT`
* **TON Workers (Accounts #2–13):** 12 isolated non-custodial v4r2 wallets in `fleet_ton_wallets.json`.

---

## 🤖 Active Earning Fleet (13 Accounts across 10 Bots)

1. **BNB Galaxy** (`@CryptoProUpRobot`): 10 daily ad tasks, instant BEP-20 auto-withdrawal to vault.
2. **Stones Miners** (`@stoneswithestand_bot`): Mining, treasure hunt, OCR captcha solver, auto-withdraw 500 STONES to Arbitrum.
3. **MRG Miner** (`@mrgminerbot`): Mining claims, reaction tasks, TH/s hash rate scaling.
4. **ART Airdrop** (`@ART_AIRDROP_BOT`): 8-hour mining cycles, task claims, level priority up to Level 8.
5. **AI Lab Robot** (`@AiLab_robot`): Hash exchanges, 20 task claims, USDT conversions.
6. **UltraWallet** (`@UltrawalletTrade_Bot`): Daily check-in streak, 10/h mining cycle renewal.
7. **Apex Miner** (`@ApxMinerBot`): Mined points collection and tracking.
8. **ATF Miner** (`@ATF_AIRDROP_bot`): **FARMING & ACCUMULATION ONLY (NO WITHDRAWALS)**.
9. **Ainovum** (`@ainovum_bot`): Mining collections, auto-withdraw USDT >= 0.1 to BEP-20 vault.
10. **MiningGRAM** (`@MiningGRAM_Bot`): Trickle claims and miner state verification.

---

## ⚙️ Cron-Job.org Cloud Scheduler Inventory

All 7 cloud keepalives active:
* `Ari AI Agent Keep-Alive (Render)` (Job `#8484430`) — Every 10m
* `Render Node 1 (Singapore) Keep-Alive` (Job `#8472437`) — Every 10m
* `Render Node 2 (Frankfurt) Keep-Alive` (Job `#8472438`) — Every 10m
* `Cloudflare Edge 3x Mesh Sentinel & Health` (Job `#8472440`) — Every 15m
* `Deno Deploy Edge Sentinel Keep-Alive` (Job `#8472538`) — Every 10m
* `Vercel Edge Cloud Node Keep-Alive` (Job `#8472711`) — Every 10m
* `Autonomous 6h Session Link Collector` (Job `#8472441`) — Every 6h
