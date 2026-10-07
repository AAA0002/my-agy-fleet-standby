# 📖 PROJECT BIBLE — AAA AUTO / MY AGY AI
> **Universal Onboarding, System Architecture, 16-Bot Fleet Engine & Operational Manual**
> *Maintainer: Antigravity AI Pair Programming System*
> *Last Updated: October 7, 2026*
> *Classification: Mission-Critical Living Technical Documentation*

---

## 🎯 1. Executive Summary & Purpose

If you are an AI assistant (Antigravity, Claude, GPT, Gemini, Llama) starting a new session, or a human operator taking over this workspace, **read this entire document first**. It provides the complete picture of this project, how every component works, where every secret and service lives, and how to operate and extend it without breaking production.

### What is this Project?
**AAA AUTO** (also known as **MY AGY AI Fleet**) is an enterprise-grade, cloud-first autonomous crypto farming and userbot fleet management infrastructure. It manages **18 Telegram accounts** (1 Master Account + 17 Worker Accounts) that continuously farm yield, satoshis, and tokens across **16 legitimate Telegram WebApp Mini Apps and MTProto bots**, while managing dedicated multi-chain non-custodial wallets (EVM/BSC, TON, TRON, Solana, Bitcoin).

### The Golden Directives (Non-Negotiable Rules)
1. **🛡️ Strict Project Isolation**: Everything relating to this project must remain strictly within this repository (`AAA0002/ATL`). **NEVER** touch, import, mix, or merge context from `@AAATelegramIdBot` (`AAA2743/AA`) or other external projects.
2. **📱 Zero Phone Load Directive (Samsung Galaxy A30)**:
   - The local Samsung Galaxy A30 running Ubuntu 26.04 PRoot is **EXCLUSIVELY dedicated to running the Antigravity AI CLI for pair programming**.
   - **NEVER** run bots, daemon loops, supervisor loops, scrapers, queue pollers, or MTProto relay listeners locally on the phone. Keep CPU and RAM 100% free for the coding session.
   - **100% of all mining, farming, token refreshers, and webhooks MUST run in the cloud** (Cloudflare Workers, Render, Upstash Redis).
3. **☁️ Zero-Trust Ephemeral Infrastructure**:
   - Assume any local machine, container, or VPS can die, expire, or get wiped at any moment.
   - Disaster recovery archives continuously flow to the Telegram vault (`@myagyai`) via `backup_manager.py`.
   - The 1-click restore mechanism (`restore.sh`) must always work out-of-the-box anywhere.
4. **🛑 Permanent Auto-Withdrawal Ban (100% Accumulation & Compounding Mode)**:
   - **NEVER trigger automatic withdrawals** from ANY bot under any circumstance.
   - Prevents wrong-address routing, sybil blacklisting, or draining into outdated/test wallets.
   - All bots operate in pure asset accumulation and auto-reinvest mode (e.g. USDT QUAD reinvests 100% into hashrate, ART compounds hardware, Stones & TAC upgrade miners).
5. **📝 Living Memory & Changelog**:
   - Whenever any file, function, bot, or architecture decision is modified, added, or removed, **always document it immediately** in `CHANGELOG.md` and update this `PROJECT_BIBLE.md`.

---

## 🌐 2. Cloud Infrastructure Topology

```
                  ┌──────────────────────────────────────────────┐
                  │          Samsung Galaxy A30 (Local)          │
                  │   Ubuntu 26.04 PRoot + Antigravity AI CLI    │
                  │  (Zero Bot Load - Pair Programming Only)     │
                  └──────────────────────┬───────────────────────┘
                                         │ Git Push / API Calls
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 CLOUD ARCHITECTURE                                     │
│                                                                                        │
│  ┌────────────────────────────────────────┐  ┌──────────────────────────────────────┐  │
│  │     Render Standby Cloud Containers    │  │      Cloudflare Edge Mesh (5 Nodes)  │  │
│  │  • Node 1 (Singapore): app.py          │  │  • aaaai2.workers.dev (Shard 0)      │  │
│  │  • Node 2 (Frankfurt): app.py          │  │  • aaa-bot.workers.dev (Shard 1)     │  │
│  │                                        │  │  • aaa222.workers.dev (Shard 2)      │  │
│  │  Role: MTProto Session Collector       │  │  • agorameet.workers.dev (Shard 3)   │  │
│  │  - Runs Telethon in the cloud          │  │  • aaaai.workers.dev (Shard 4)       │  │
│  │  - Connects 18 Telegram sessions       │  │                                      │  │
│  │  - Extracts fresh 24h WebApp initData  │  │  Role: 24/7 Edge Autonomous Farming   │  │
│  │  - Syncs tokens to Upstash & CF KV     │  │  - Runs cron every 15 mins           │  │
│  │  - Endpoint: POST /collect-tokens      │  │  - Farms all 16 bots via HTTP        │  │
│  └───────────────────┬────────────────────┘  │  - Executes side tasks & check-ins   │  │
│                      │                       │  - Fast, serverless, zero ban risk   │  │
│                      │ Syncs Fresh Tokens    └──────────────────▲───────────────────┘  │
│                      ▼                                          │ Reads Fresh Tokens   │
│  ┌──────────────────────────────────────────────────────────────┴───────────────────┐  │
│  │                        Upstash Serverless Redis REST                             │  │
│  │  • URL: https://relaxing-starfish-285827.upstash.io                              │  │
│  │  • Key: fleet:tokens:<uid> (Contains active WebApp initData for each account)    │  │
│  │  • Key: fleet:live_state (Contains latest real-time farming results)             │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Cloud Nodes Directory
- **Cloudflare Edge Nodes**:
  - Node 1: `https://restore-agy.aaaai2.workers.dev`
  - Node 2: `https://restore-agy.aaa-bot.workers.dev`
  - Node 3: `https://restore-agy.aaa222.workers.dev`
  - Node 4: `https://restore-agy.agorameet.workers.dev`
  - Node 5: `https://restore-agy.aaaai.workers.dev`
- **Render Standby Nodes**:
  - Node 1: `https://my-agy-fleet-standby.onrender.com` (Singapore)
  - Node 2: `https://my-agy-fleet-standby-node2.onrender.com` (Frankfurt)
  - GitHub Standby Deployment Repository: `AAA0002/my-agy-fleet-standby` (`app.py`)
- **Telegram Vaults**:
  - Admin & Backup Channel: `@myagyai` (Bot: `@myagyai`)
  - Secondary Bot: `@AAAPREMIUMAPPSbot`

---

## 🔄 3. The 24-Hour Session Lifecycle & Collector Flow

### Why does this architecture exist?
1. **The 24-Hour Expiration Rule**: All Telegram Mini Apps enforce an `auth_date` expiration timestamp inside `initData`. After 24 hours (86,400 seconds), bot backends reject API requests with `HTTP 401 Unauthorized` (`auth_date_too_old`).
2. **Cloudflare Limitation**: Cloudflare Workers run on V8 JavaScript serverless isolates and cannot establish raw MTProto binary TCP socket connections to Telegram Data Centers.
3. **The Solution**:
   - Render Standby (Python 3 + Telethon) acts as the **cloud MTProto session collector**.
   - Render uses the 18 Telegram Telethon session strings stored in `accounts.json` to connect to Telegram via MTProto.
   - For each bot, it calls `RequestWebViewRequest` or `RequestAppWebViewRequest` to obtain fresh WebApp URLs and extract fresh `initData`.
   - Render syncs these brand-new tokens into Upstash Redis (`fleet:tokens:<uid>`) and Cloudflare KV.
   - Cloudflare Workers Edge Mesh reads these fresh tokens and farms all 16 bots continuously every 15 minutes.

---

## 👥 4. Fleet Accounts & Multi-Chain Wallet System

The fleet consists of **18 Telegram accounts**:
- **Master Account**: UID `6727787768` (`Arif Hossain` / `@myagyai`). All worker referral links, commission sweeps, and team bonuses flow into this account.
- **Worker Accounts (17 Accounts)**: UIDs `8881914294`, `7648254021`, `8826375659`, `8450010161`, `8782429452`, `7734849205`, `8025472383`, `8851426148`, `8203342513`, `8190649727`, `7487048946`, `8741547543`, `8727040932`, `7749125802`, `7954290138`, `8975442879`, `8841038141`.

### Non-Custodial Multi-Chain Wallet Isolation
To prevent Sybil detection, anti-farming bans, and wallet clustering, each account is provisioned with **dedicated, isolated addresses** stored in JSON registries:
- `fleet_ton_wallets.json` — Dedicated TON (v4r2) non-custodial wallets.
- `fleet_evm_wallets.json` — Dedicated EVM / BSC (BEP20) non-custodial wallets.
- `fleet_tron_wallets.json` — Dedicated TRON (TRC20) non-custodial wallets.
- `fleet_solana_wallets.json` — Dedicated Solana non-custodial wallets.
- `fleet_btc_wallets.json` — Dedicated Bitcoin SegWit non-custodial wallets.

---

## 🤖 5. The Complete 16-Bot Fleet Catalog & Automation Matrix

| # | Bot Name | Telegram Handle | Backend URL / Host | Network | Core Farming Mechanism | Automated Side Tasks |
|---|---|---|---|---|---|---|
| **1** | **Stones Miners** | `@stonesminers_bot` | `https://app.stoneswithestand.my.id` | EVM / BSC | • `/api/claim`<br>• `/api/mining/start` | • Daily Check-in (`/api/task/complete`)<br>• Stone Breaker Minigame (Capped 50/50 STONES/day)<br>• Hashrate Boost Challenge (+0.5 TH/s)<br>• Dynamic task discovery from `/api/state`<br>• Dedicated EVM wallet binding |
| **2** | **MRG Miner** | `@mrg_miner_bot` | `https://mrg.up.railway.app` | TON | • `/api/user/claim-mining` | • Link tasks with 15s human dwell<br>• **Autonomous Level Upgrader**: Auto-unlocks levels up to **Level 203**<br>• Dedicated TON wallet connection (`/api/user/connect-wallet`)<br>• Master referral commission & team bonus claims |
| **3** | **ART Airdrop** | `@artairdrop_bot` | `https://art.tamimdev.dev` | TON | • `/api/user/claim-mining`<br>• `/api/user/start-mining` (8-hr) | • Daily High-Yield Ad watch (`/api/ads/claim`)<br>• **Hardware Buying**: Auto-buys Levels 2 through 8 hardware<br>• Dedicated TON wallet connection (Isolated per account)<br>• 100% Compounding Mode (auto-withdrawal disabled) |
| **4** | **AI Lab Robot** | `@ailabrobot_bot` | `https://api.ailab-agent.online` | USDT / Cloud | • `/api/v1/miner/claim`<br>• `/api/v1/miner/start` | • Partner task discovery & claims<br>• Daily check-in bonus<br>• Defensive empty-list error handling<br>• Safe accumulation mode (legacy cashout permanently eliminated) |
| **5** | **UltraWallet** | `@ultrawallet_bot` | `https://wallet.trxvault.top` | TRX / Cloud | • `/api/v1/mining/claim` | • Firebase custom token exchange via Google Identity Toolkit<br>• Daily check-in streak<br>• Staggered jitter rate-limit backoff (Asyncio Semaphore shield) |
| **6** | **Apex Mining** | `@apexminer_bot` | `https://apxn-miner-live.apxn-network.workers.dev` | APXN | • `/api/mining/claim`<br>• `/api/mining/restart` | • Daily check-in (`/api/checkin`)<br>• Ad boost & reward (`/api/ads/boost`, `/api/ads/reward`)<br>• Social & partner tasks (Telegram, Twitter, Discord) |
| **7** | **ATF Miner** | `@atf_miner_bot` | `https://atfminers.asloni.online` | TON | • `?action=claim`<br>• `?action=start_mine` | • **Automated Math Challenge Solver**: Solves arithmetic captcha<br>• Hashrate Boost (`?action=activate_boost`)<br>• 8x Cooldown Tasks (YouTube, Twitter, Channel joins)<br>• Dedicated TON wallet sync (`?action=sync_wallet`)<br>• Team wallet claims |
| **8** | **Ainovum AI** | `@ainovum_bot` | `https://ainovum.biz` | USDT BEP20 | • `/api/mining/start`<br>• `/api/mining/claim` | • Daily streak bonus (`/api/daily-bonus/claim`)<br>• Official channel bonus (`/api/channel-bonus/claim`)<br>• Mystery gift box open (`/api/gift-box/open`)<br>• 100% Asset accumulation mode (auto-withdraw disabled) |
| **9** | **TRX Power** | `@trxpowermining_bot` | `https://187.53.139.6.sslip.io/api` | TRON (TRX) | • `/api/mining/claim` | • Telegram WebApp v2.0.3 JWT authentication (`/auth/telegram`)<br>• Channel verification (`/api/user/verify-channels`)<br>• Channel task claim (`/api/tasks/channel/claim`)<br>• Dedicated TRON wallet connection (`/api/user/wallet`)<br>• Real-time stats audit |
| **10** | **Bitcoin Cloud** | `@Bitcoin_Cloud_Mining_bot` | MTProto Inline Callbacks | Bitcoin (BTC) | • Inline button `⛏ Mine` (`claim_mine`) | • Scheduled 4-hour anti-spam rate limiter<br>• Master account milestone satoshi rewards (`claim_task_3`, `4`, `5` once every 24h)<br>• Real BTC satoshis accumulated directly |
| **11** | **Tensor Mining** | `@tensormining_bot` | `https://flascoins.xyz` | ORCA Token | • 50-tap cloud batch (`/api/tap`) | • Full TMA Bearer handshake (`POST /api/auth`)<br>• Daily login reward (`/api/daily`)<br>• Dynamic partner tasks with dwell timers<br>• ORCA yield accumulation |
| **12** | **Ton Trader AI** | `@tontrader_bot` | `https://api.tontraderai.com` | TON | • Algorithmic yield claim (`/api/v1/finance/claim-yield`) | • Daily streak gift (`/api/v1/user/claim-daily-gift`)<br>• Mystery gift boxes (Opens up to 3 boxes via `/api/v1/user/claim-gift-box`) |
| **13** | **FINVORA Web3** | `@finvora_bot` | `https://finvora-production.up.railway.app` | GRAM / TON | • `/api/mining/claim` | • Instant bonus (`/api/bonus/instant`)<br>• Dedicated TON wallet connection (`/api/wallet/connect`) |
| **14** | **TurboGram V1** | `@turbogram_bot` | `https://turbo.tamimdev.dev` | GRAM / TON | • Balance & user state tracking (`/api/me`) | • Dynamic task discovery & completion (maintains **ACTIVE** referral tier)<br>• Dedicated TON wallet binding (`/api/me/wallet`) |
| **15** | **USDT QUAD** | `@usdtquadbot` | `https://ustdquad.up.railway.app` | USDT (BSC) | • Pending balance claim (`/claim-balance`) | • Hourly Hashrate Boost (+1 GH/s boost via `hourly_watch_ad`)<br>• Referral milestone rewards (`invite3` to `invite1000`)<br>• 100% Auto-reinvest into hashrate (`/reinvest-balance`) |
| **16** | **TAC Airdrop** | `@tacairdrop_bot` | `https://tacairdrop.xyz` | TAC / TON | • 8-hr continuous miner start & claim (`/api/mining/start`, `/api/mining/claim`) | • High-yield ad watches (up to 7 ads/day = **+105 TAC daily**)<br>• **Autonomous Sequential Miner Leveling**: Auto-upgrades miner up to **Level 148** based on holding balance<br>• Community & social tasks (`/api/tasks/complete`)<br>• Dedicated TON wallet connection<br>• Master referral & team wallet claims |

*(Note: Scam bot `@OminixAiBot` was formally reported to Telegram Anti-Scam, blocked on all 18 accounts, and purged from all codebases).*

---

## ⚡ 6. Fleet-Wide Parity & Anti-Throttling Architecture

### Why Did Worker Accounts Previously Fail While Master Succeeded?
During fleet operations, an investigation revealed why some bots worked on the master account but failed on worker accounts:
1. **Concurrent Request Throttling (HTTP 429)**:
   - When all 18 accounts hit bot APIs at the exact same millisecond, third-party edge gateways (notably Cloudflare rate limits on UltraWallet and others) throttled requests.
   - Because Account 1 was first in line, it succeeded, while Accounts 2–18 received HTTP 429 ("Too many requests").
   - **Solution Implemented**: An `asyncio.Semaphore(2)` was added with randomized jitter delays (`1.2s`–`2.8s`) between account dispatches and 3-attempt exponential backoff retry loops.
2. **Shared / Colliding Wallet Addresses (Anti-Sybil Flags)**:
   - ART and others previously used the master wallet for worker accounts, causing anti-sybil filtering on backends.
   - **Solution Implemented**: Full wallet isolation across all 18 accounts using master dictionaries `FLEET_TON_WALLETS` and `FLEET_TRON_WALLETS` provisioned in both Cloudflare Edge and Render.
3. **Missing Auth / Registration Handshakes on Workers**:
   - Bots like TRX Power Mining required a Telegram WebApp JWT handshake (`POST /auth/telegram`) before calling `/api/mining/claim`.
   - Tensor Mining required `POST /api/auth` with `Authorization: tma <initData>` prior to tapping.
   - USDT QUAD required an explicit `/register` call with referral `28373302`.
   - **Solution Implemented**: Full auth, verification, and registration lifecycle handshakes are now executed for all worker accounts across both Cloudflare Edge Workers and Render Standby.
4. **Permanent Auto-Withdrawal Ban**:
   - All auto-cashouts (including legacy AI Lab addresses) have been completely eliminated. All accounts strictly compound and accumulate hashpower/tokens.

---

## 🛠️ 7. Operator & AI Cheat Sheet

Here are the exact commands to run for everyday operations:

### 1. Check Fleet Farming Status
Query the Cloudflare Edge Gateway for real-time status across all 18 accounts:
```bash
curl -s https://restore-agy.aaaai2.workers.dev/api/farm/status | jq .
```

### 2. Trigger Immediate Cloud Farm
Trigger an immediate harvest across all 16 bots on Cloudflare Workers:
```bash
curl -s -X POST https://restore-agy.aaaai2.workers.dev/api/farm/all \
  -H "Authorization: Bearer agy_cf_secret_7d36994e_2026" \
  -H "Content-Type: application/json" \
  -d '{"all": true, "bot": "all"}'
```

### 3. Refresh 24-Hour WebApp Tokens via Render
Trigger Render Standby to connect via Telethon MTProto in the cloud and refresh tokens:
```bash
# Refresh Master Account
python3 -c '
import json, requests
with open("accounts.json") as f:
    accs = json.load(f)
master = [a for a in accs if str(a.get("user_id")) == "6727787768"]
r = requests.post("https://my-agy-fleet-standby.onrender.com/collect-tokens",
  headers={"Authorization": "Bearer agy_cf_secret_7d36994e_2026"}, json={"accounts": master})
print(r.json())
'
```

### 4. Run Comprehensive Audit on Core Farming & Side Tasks
Run the live audit tool to check yields and side tasks across Master and Worker accounts:
```bash
python3 audit_bots_and_sidetasks.py
```

### 5. Deploy Updated Standby Code to Render
After modifying `render_standby_app.py`, push it to the deployment repo so Render auto-deploys:
```bash
python3 push_to_standby_repo.py
```

### 6. Deploy Updated Edge Code to Cloudflare Mesh
Deploy the 5-node worker engine across Cloudflare:
```bash
python3 deploy_both_cf_workers.py
```

### 7. Run Disaster Recovery Backup to Telegram Vault
Push an encrypted disaster recovery snapshot to `@myagyai`:
```bash
python3 backup_manager.py
```

### 8. Verify Zero Phone Load
Always verify 0 background Python bot daemons are running locally on the phone:
```bash
ps aux | grep python
```
*(Should only show one-shot commands, never continuous daemons or pollers).*

---

## 🔒 8. Living Changelog Protocol

Whenever you perform work in this repository:
1. **Never delete existing working features** without explicit user request or confirmed scam decommissioning.
2. **Commit with clean conventional commits**: `git commit -m "feat/fix/perf: description"`.
3. **Keep `CHANGELOG.md` updated** with every major addition, modification, and bug fix.
4. **Keep `PROJECT_BIBLE.md` updated** whenever a bot is added, an endpoint changes, or a new cloud service is provisioned.
5. **Push git checkpoints** to `AAA0002/ATL` (`main`) and create a fresh backup in `@myagyai`.
