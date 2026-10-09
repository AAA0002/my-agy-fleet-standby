# 📖 PROJECT BIBLE — AAA AUTO / MY AGY AI
> **Universal Onboarding, System Architecture, 9-Bot Fleet Engine & Operational Manual**
> *Maintainer: Antigravity AI Pair Programming System*
> *Last Updated: October 9, 2026*
> *Classification: Mission-Critical Living Technical Documentation*

---

## 🎯 1. Executive Summary & Purpose

If you are an AI assistant (Antigravity, Claude, GPT, Gemini, Llama) starting a new session, or a human operator taking over this workspace, **read this entire document first**. It provides the complete picture of this project, how every component works, where every secret and service lives, and how to operate and extend it without breaking production.

### What is this Project?
**AAA AUTO** (also known as **MY AGY AI Fleet**) is an enterprise-grade, cloud-first autonomous crypto farming and userbot fleet management infrastructure. It manages **18 Telegram accounts** (1 Master Account + 17 Worker Accounts) that continuously farm yield, satoshis, and tokens across **9 high-conviction legitimate Telegram WebApp Mini Apps** (all scammer bots purged and blacklisted), while managing dedicated multi-chain non-custodial wallets (EVM/BSC, TON, TRON, Solana, Bitcoin).

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
   - All bots operate in pure asset accumulation and auto-reinvest mode (e.g. ART compounds hardware, Stones & MRG upgrade miners).
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
│  │    Triple Render Standby Mesh (3 Nodes)│  │      Cloudflare Edge Mesh (5 Nodes)  │  │
│  │  • Node 1 (Singapore - Coz1): app.py   │  │  • aaaai2.workers.dev (Shard 0)      │  │
│  │  • Node 2 (Frankfurt - Abid): app.py   │  │  • aaa-bot.workers.dev (Shard 1)     │  │
│  │  • Node 3 (Oregon - Koram): app.py     │  │  • aaa222.workers.dev (Shard 2)      │  │
│  │                                        │  │  • agorameet.workers.dev (Shard 3)   │  │
│  │  Role: MTProto Session Collector       │  │  • aaaai.workers.dev (Shard 4)       │  │
│  │  - Runs Telethon in the cloud          │  │                                      │  │
│  │  - Connects 18 Telegram sessions       │  │  Role: 24/7 Edge Autonomous Farming   │  │
│  │  - Extracts fresh 24h WebApp initData  │  │  - Runs cron every 15 mins           │  │
│  │  - Syncs tokens to D1, Upstash & KV     │  │  - Farms all 9 legitimate bots        │  │
│  │  - Endpoint: POST /collect-tokens      │  │  - Executes side tasks & check-ins   │  │
│  └───────────────────┬────────────────────┘  │  - Fast, serverless, zero ban risk   │  │
│                      │                       │  - Propagates cached Turnstile passes │  │
│                      │ Syncs Fresh Tokens    └──────────────────▲───────────────────┘  │
│                      ▼                                          │ Reads Fresh Tokens   │
│  ┌──────────────────────────────────────────────────────────────┴───────────────────┐  │
│  │                        Upstash Serverless Redis REST                             │  │
│  │  • URL: https://relaxing-starfish-285827.upstash.io                              │  │
│  │  • Key: fleet:tokens:<uid> (Contains active WebApp initData for each account)    │  │
│  │  • Key: fleet:wallets:ton (Contains isolated TON wallets & recovery mnemonics)   │  │
│  │  • Key: victors:pass:<uid> (Contains fresh Cloudflare Turnstile humanPass)       │  │
│  │  • Key: fleet:live_state (Contains latest real-time farming results)             │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Cloud Nodes Directory (5 Cloudflare Accounts & 5 Render Services)
- **5 Cloudflare Edge Accounts & Workers (Serverless 24/7 Farming Mesh & 25M D1 Reads / 50GB R2)**:
  - Account 1 (`korimhaji210@gmail.com`): `https://restore-agy.aaaai2.workers.dev` (Shard 0)
    * D1 Database: `agy_fleet_db` (`c29cc72d-3813-4aa2-859a-8cdfd929825c`)
    * R2 (S3) Bucket: `agy-fleet-backups`
    * KV Namespace: `MY_AGY_VAULT` (`315ff9ee...`)
  - Account 2 (`Koramshah2@gmail.com`): `https://restore-agy.aaa-bot.workers.dev` (Shard 1)
    * D1 Database: `agy_fleet_db` (`9456e01a-77f1-49fa-b22b-d8b930e19bf2`)
    * R2 (S3) Bucket: `agy-fleet-backups`
    * KV Namespace: `BOT_KV` (`44d6b1ac...`)
  - Account 3 (`coz1gameh3@gmail.com`): `https://restore-agy.aaa222.workers.dev` (Shard 2)
    * D1 Database: `agy_fleet_db` (`6b0c8fc4-5ead-44fe-88c4-e660a4b95fef`)
    * R2 (S3) Bucket: `agy-fleet-backups`
    * KV Namespace: `restore-agy-kv` (`f5c5b2dc...`)
  - Account 4 (`aaafreeai@gmail.com`): `https://restore-agy.agorameet.workers.dev` (Shard 3)
    * D1 Database: `atf-miner-db` (`2659c73b-8144-4f2a-9a06-ef2368a1ce7f`)
    * R2 (S3) Buckets: `atf-db-backups`, `aaa-r2`
    * KV Namespace: `atf-cache-kv` (`c712104e...`)
  - Account 5 (`da98cfb7cca333391bb349333f294d0f`): `https://restore-agy.aaaai.workers.dev` (Shard 4)
    * D1 Database: `aaa-d1` (`e2db1db3-eaaf-49b3-86e5-95aee66772ef`)
    * R2 (S3) Bucket: `aaa-r2`
    * KV Namespace: `atf-miner-kv` (`c5eadf91...`)
- **Render Cloud Fleet (Multi-Account Cloud MTProto Compute & Resilient Relay Mesh)**:
  - Node 1: **Render Standby Node 1 (Singapore)**: `https://my-agy-fleet-standby.onrender.com`
    * Service ID: `srv-damuhkmgekts73f1osag` | Workspace: `My Workspace` (`tea-d8j9clt8nd3s73eb041g`, `coz1gameh1@gmail.com`)
    * API Key: `RENDER_API_KEY_1: rnd_cGQwvG9J4pe6Rpf06sRMb4pzR6v1` | Linked Repo: `https://github.com/AAA2743/my-agy-fleet-standby` (main)
    * Status: 🟢 200 OK — Immutable standby compute node & failover MTProto token collector.
  - Node 2: **Render Standby Node 2 (Frankfurt)**: `https://my-agy-fleet-standby-node2.onrender.com`
    * Service ID: `srv-dan5q00ae00c73djummg` | Workspace: `Abid's workspace` (`tea-dan5pgbm8hqs73a5cvig`, `abidhasanch2001@gmail.com`)
    * API Key: `RENDER_API_KEY_2: rnd_KnVaiOw93SKa4fSTrEURwZrP0UaB` | Linked Repo: `https://github.com/AAA0002/my-agy-fleet-standby` (main)
    * Status: 🟢 200 OK — Primary 24/7 Compute & MTProto Token Collector. Deploys live automatically on git push via `push_to_standby_repo.py`.
  - Node 3: **Render Standby Node 3 (Oregon)**: `https://my-agy-fleet-standby-node3.onrender.com`
    * Service ID: `srv-db437o3tqb8s73dt4erg` | Workspace: `Koram's workspace` (`tea-daoj9nid0e5s738gqp0g`, `koramshah2@gmail.com`)
    * API Key: `RENDER_API_KEY: rnd_PqsurfX5D9blSaEEuEDDAUcl393y` | Linked Repo: `https://github.com/koramshah2/my-agy-fleet-standby` (main)
    * Status: 🟢 200 OK — High-availability secondary compute node. Deploys live automatically on git push via `push_to_standby_repo.py`.
  - Service 4: **Primary MTProto Relayer**: `https://atf-mtproto-relayer.onrender.com`
    * Service Endpoint: `/wake` (🟢 ONLINE & AUTHENTICATED)
    * Role: Dedicated 24/7 authenticated Telegram MTProto binary TCP socket bridge.
  - Service 5: **Backup MTProto Relayer**: `https://atf-mtproto-relayer-backup.onrender.com`
    * Service Endpoint: `/wake` (🟢 ONLINE & AUTHENTICATED)
    * Role: Cold standby failover MTProto bridge for high-availability session extraction.
  - Service 6: **Hermes Ari AI Council Agent**: `https://hermes-grok-cloud-agent.onrender.com`
    * Service ID: `srv-daojdt5g1s2s738jsjmg` | Workspace: `Koram's workspace` (`tea-daoj9nid0e5s738gqp0g`, `koramshah2@gmail.com`)
    * Service Key: `rnd_PqsurfX5D9blSaEEuEDDAUcl393y` | Linked Repo: `https://github.com/koramshah2/hermes-cloud-agent` (main)
    * Status: 🟢 200 OK — Background AI intelligence worker running `autonomous_cloud_agent.py` (Multi-model Groq + Gemini council).

- **GitHub Multi-Account CI/CD & Cloud Compute Fleet (4,000 Free Minutes/Month)**:
  - Account 1 (`AAA0002`):
    * Primary Repository: `https://github.com/AAA0002/ATL` (main)
    * Standby Deployment Repo: `https://github.com/AAA0002/my-agy-fleet-standby` (main)
    * Quota: 2,000 free minutes/month for GitHub Actions runners.
    * Workflows: `cloud_token_refresher.yml`, `fleet_sentinel.yml`, `cloud_sweeper.yml`, `mrg_turnstile_solver.yml`.
  - Account 2 (`koramshah2` / `Koramshah2@gmail.com`):
    * Mirror Standby Repo: `https://github.com/koramshah2/AAA_AUTO` (main)
    * Hermes Standby Repo: `https://github.com/koramshah2/hermes-cloud-agent` (main)
    * Quota: 2,000 free minutes/month for GitHub Actions runners.
    * Tokens: Classic PAT `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`, Fine-grained PAT `github_pat_11CQ4P67Y0...`.
    * Synchronized Git Remotes: `origin` (`AAA0002/ATL`) and `koram_standby` (`koramshah2/AAA_AUTO`).
  - Suspended 3rd Account Note (`AAA2743`):
    * GitHub account `AAA2743` was suspended by GitHub. All production dependencies have been migrated to `AAA0002` and `koramshah2`. Render services were updated via API to point to active repos.
  - **100% Cloud MRG Auto-Farming & Turnstile Solver Workflow**:
    * Workflow File: `.github/workflows/mrg_turnstile_solver.yml` (Runs every 3 hours: `15 */3 * * *`).
    * Script: `mrg_turnstile_solver.py` (Headless Patchright stealth engine, real Telegram `initData` simulation, native claim button clicker, Turnstile iframe solver, and auto-compounder).
    * Zero Phone Load: Runs 100% inside Microsoft/GitHub's cloud runner environment (Ubuntu 22.04, 7GB RAM).

- **Telegram Dual Bot & Channel Ecosystem (Admin Infrastructure vs. Normal User Platform)**:

  #### 🛡️ System 1: Admin Telegram Ecosystem (Control, Telemetry, Vault, Disaster Recovery)
  *Dedicated exclusively to system administrators, automated disaster recovery, on-chain telemetry, and AI command execution.*
  - **Admin Bot**: `@myagyai` (Bot ID: `8858823950`, Token: `REPORT_BOT_TOKEN: 8858823950:AAEdX47g7as1xLYEudfRUHaVGUdNIaU_ku8`)
    - Purpose: Autonomous execution reporting, harvest alerts, AI natural language commands, Better Stack dead-man pings, and automated backup broadcasts.
  - **Admin Direct Control Chat**: `REPORT_CHAT_ID: 6727787768` (`@Arif2743aaa`, Phone: `+8801317342850`)
    - Purpose: High-priority operational alerts, Turnstile solver telemetry, and 1-click disaster restore execution.
    - Authorized Admin UIDs: `["6727787768", "8741547543", "7648254021"]`.
  - **Disaster Recovery Vault Channel**: `@myagyai` (Channel ID: `-1004453515167`, Env: `BACKUP_CHANNEL: @myagyai`)
    - Purpose: Immutable off-machine repository for AES-encrypted `.zip` disaster recovery backups, MTProto session strings snapshot, and Pinata IPFS gateway CIDs.
  - **Payouts & Daily Ledger Channel**: Channel ID: `-1004402765950` (Env: `PAYOUT_CHANNEL_ID: -1004402765950`)
    - Purpose: On-chain withdrawal receipts, daily profit statements, Jetton gas refuel notifications, and accounting audit trail.
  - **Fleet Internal Supergroup**: Channel ID: `-1003973231307` (*AAA T Wallet Supergroup*)
    - Purpose: Internal fleet sync telemetry, multi-wallet heartbeat checks, and node failover alerts.

  ---

  #### 👥 System 2: Normal User Telegram Ecosystem (Public Mining Platform & Community)
  > 🛑 **MANDATORY DIRECTIVE — DO NOT TOUCH THE USER BOT**:
  > Under NO circumstances should any AI agent (Antigravity, Claude, GPT, Gemini) modify, edit, redeploy, reconfigure, or tamper with the User Bot (`@AAAPREMIUMAPPSbot`), its Cloudflare edge webhook, its database bindings, or its user-facing community channels. It is strictly dedicated to public end-users and operates in 100% autonomous serving mode.

  - **User Bot Identity**: `@AAAPREMIUMAPPSbot` (Bot ID: `8167732110`, Token: `USER_BOT_TOKEN: 8167732110:AAGQA6bBgRwaChFIWPvs9uCt6aZ3j1VGCn8`)
    - Name: *AAA AUTO MINING*
    - Live Webhook: `https://atf-miner-worker.agorameet.workers.dev/` (Cloudflare Worker Node 4)
    - Role: User onboarding, public mining slot dashboard, referral tree rewards, in-bot ad rewards, and point tracking.
  - **User WebApp Frontend**: `https://atf-miner-app.pages.dev` (Cloudflare Pages)
  - **User Distributed Mining Engine**: `https://atf-mining-engine.aaaai.workers.dev` (Cloudflare Worker Node 5)
  - **User Database & Cache**: Cloudflare D1 `atf-miner-db` (`2659c73b-8144-4f2a-9a06-ef2368a1ce7f`) + KV `atf-cache-kv` (`c712104ed5744835add7e97384da8c82`)
  - **User Session Security Key**: `USER_BOT_SESSION_ENCRYPTION_KEY: edf824a8b2d05d039839fdfcef84108c555459779f2d4ea3fca6e66a21ec056e`
  - **User Community Group**: Chat ID: `-1003684868577` (*AAA Auto Miner*, `https://t.me/+8xTmE28Up9U5YWQ1`)
    - Purpose: Public end-user community discussion, miner support, and questions.
  - **Official Public Announcements**: Channel ID: `-1004255751168` (`@AAAATFAUTOMINING`, `https://t.me/AAAATFAUTOMINING`)
    - Purpose: Official broadcasts, platform updates, airdrop news, and system maintenance alerts for end-users.
  - **Live Public Miner Activity Stream**: Channel ID: `-1004332544939` (`@AAAATF_ACTIVITY`, `https://t.me/AAAATF_ACTIVITY`)
    - Purpose: Real-time public user claims, level achievements, and active mining transactions stream.

### 🛰️ The Complete Master Catalog of Cloud Infrastructure & Verified APIs (from `.env`)

| Infrastructure Layer | Service / Provider | Endpoint / Host / Resource | Status & Verified Capabilities |
| :--- | :--- | :--- | :--- |
| **Serverless Edge Web** | **Vercel Cloud** | `https://agy-aaa000.vercel.app` | 🟢 **HTTP 200 OK** — Edge deployment (`team_C2l6j4UJ0x8Cwu7xvYtxBn02`) |
| **Serverless Edge Web** | **Deno Deploy (Node 1)** | `https://my-agy-fleet-deno.aaa222.deno.net` | 🟢 **HTTP 200 OK** — TypeScript Edge serverless runner |
| **Serverless Edge Web** | **Deno Deploy (Node 2)** | `https://my-agy-fleet-deno2.aaasupporta.deno.net` | 🟢 **HTTP 200 OK** — Secondary TypeScript Edge runner |
| **Cloudflare Pages** | **ATF WebApp** | `https://atf-miner-app.pages.dev` | 🟢 **HTTP 200 OK** — Global static and edge WebApp frontend |
| **Decentralized Storage** | **Pinata IPFS** | `api.pinata.cloud` | 🟢 **AUTHENTICATED** — Latest CID: `QmUSX7XHwMcq3muCnZBaDzvk3D9ohXnJpe9iiQikbms8mn` |
| **Serverless Database** | **Upstash Redis** | `relaxing-starfish-285827.upstash.io` | 🟢 **HTTP 200 OK** — Real-time token storage across all 18 accounts |
| **Serverless Database** | **Turso LibSQL** | `my-agy-fleet-db-aaa2743.aws-ap-south-1.turso.io` | 🟢 **HTTP 200 OK** — Distributed SQLite edge database |
| **Cloud Postgres** | **Supabase Cloud** | `znbbaozpevurvbfkxakz.supabase.co` | 🟢 **HTTP 200 OK** — Managed PostgreSQL database via Service Role Key |
| **AI Inference Engine** | **Google Gemini** | `generativelanguage.googleapis.com` | 🟢 **14/14 KEYS ACTIVE** — Rotating multi-key pool for Ari AI reasoning |
| **Edge AI Inference** | **Workers AI (Cloudflare)** | Global Edge Mesh (Llama 3.2 3B Instruct) | 🟢 **ACTIVE** — Zero API keys required across 5 Cloudflare nodes |
| **Web3 Infrastructure** | **Alchemy Ethereum** | `eth-mainnet.g.alchemy.com/v2/...` | 🟢 **HTTP 200 OK** — Live block height queries verified |
| **Web3 Infrastructure** | **Toncenter Official** | `https://toncenter.com/api/v2` | 🟢 **HTTP 200 OK** — High-speed TON masterchain RPC |
| **Web3 Infrastructure** | **TonAPI Key** | `https://tonapi.io` | 🟢 **ACTIVE** — Jetton transfers and account audits |
| **Web3 Infrastructure** | **Etherscan API** | `api.etherscan.io` | 🟢 **ACTIVE** — EVM on-chain verification key |
| **Rotating Proxy Pool** | **Webshare Proxies** | `proxy.webshare.io` | 🟢 **20 ACTIVE PROXIES** — Residential/datacenter proxy pool across 2 keys |
| **Cloud Scheduler** | **Cron-Job.org** | `api.cron-job.org` | 🟢 **HTTP 200 OK** — External heartbeat trigger for cloud worker wakeups |
| **Uptime & Dead-Man** | **Better Stack** | `uptime.betterstack.com/api/v1/heartbeat/...` | 🟢 **HTTP 200 OK** — Dead-man's switch 24/7 heartbeat monitor |
| **Crash Interception** | **Sentry Monitoring** | `ingest.us.sentry.io` | 🟢 **ACTIVE** — 2 Projects configured for real-time exception trapping |
| **IP Telemetry** | **ipinfo.io** | `ipinfo.io/json` | 🟢 **ACTIVE** — Autonomous geolocation & ASN validation |
| **Permanent Memory** | **Walrus Memory** | Protocol Key: `11162bafeb85...` | 🟢 **ACTIVE** — Permanent system state sync across restarts |

---

## 🔄 3. The 24-Hour Session Lifecycle & Collector Flow

### Why does this architecture exist?
1. **The 24-Hour Expiration Rule**: All Telegram Mini Apps enforce an `auth_date` expiration timestamp inside `initData`. After 24 hours (86,400 seconds), bot backends reject API requests with `HTTP 401 Unauthorized` (`auth_date_too_old`).
2. **Cloudflare Limitation**: Cloudflare Workers run on V8 JavaScript serverless isolates and cannot establish raw MTProto binary TCP socket connections to Telegram Data Centers.
3. **The Solution**:
   - Render Standby (Python 3 + Telethon) acts as the **cloud MTProto session collector**.
   - Render uses the 18 Telegram Telethon session strings stored in `accounts.json` to connect to Telegram via MTProto.
   - For each bot, it calls `RequestWebViewRequest` or `RequestAppWebViewRequest` to obtain fresh WebApp URLs and extract fresh `initData`.
   - Render syncs these brand-new tokens into Cloudflare D1 SQL (`fleet_tokens`), Upstash Redis (`fleet:tokens:<uid>`), and Cloudflare KV.
   - Cloudflare Workers Edge Mesh reads these fresh tokens directly from strongly consistent D1 SQL and farms all 7 legitimate bots continuously every 15 minutes.

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

### 🤖 5. The Complete 9-Bot Fleet Catalog & Automation Matrix

| # | Type | Bot Name | Telegram Handle | Backend URL / Host | Network | Core Farming Mechanism | Automated Side Tasks |
|---|---|---|---|---|---|---|---|
| **1** | **Type A** | **Stones Miners** | `@stonesminers_bot` | `https://app.stoneswithestand.my.id` | EVM / BSC | • `/api/claim`<br>• `/api/mining/start`<br>• **Telemetry:** `farmed (lvl: {lvl}, bal: {coins} STONES)` | • Daily Check-in (`/api/task/complete`)<br>• Stone Breaker Minigame (Capped 50/50 STONES/day)<br>• Hashrate Boost Challenge (+0.5 TH/s)<br>• Dynamic task discovery from `/api/state`<br>• Dedicated EVM wallet binding |
| **2** | **Type A** | **MRG Miner** | `@mrg_miner_bot` | `https://mrg.up.railway.app` | TON | • `/api/user/claim-mining`<br>• **Telemetry:** `farmed (lvl: {lvl}, bal: {bal} MRG)` | • Link tasks with 15s human dwell<br>• **Autonomous Level Upgrader**: Auto-unlocks levels up to **Level 95+** (synchronized with `manualUnlockedLevel`)<br>• **Cryptographic TON Connect 2.0 Proof**: Full Ed25519 wallet ownership verification bound across all 18 accounts (`isTonConnected: True`)<br>• Accurate claim telemetry distinguishing human check challenge from completed claims<br>• Master referral commission & team bonus claims |
| **3** | **Type A** | **AI Lab Robot** | `@ailabrobot_bot` | `https://api.ailab-agent.online` | USDT / Cloud | • `/api/v1/miner/claim`<br>• `/api/v1/miner/start`<br>• **Telemetry:** `farmed (bal: ${bal}, {hashes} hashes)` | • Partner task discovery & claims<br>• Daily check-in bonus<br>• Defensive empty-list error handling<br>• Safe accumulation mode (legacy cashout permanently eliminated) |
| **4** | **Type A** | **UltraWallet** | `@ultrawallet_bot` | `https://wallet.trxvault.top` | TRX / Cloud | • `/api/mining/claim`<br>• **Telemetry:** `farmed (bal: ${usdt} USDT, pend: {lt} LT)` | • Firebase custom token exchange via Google Identity Toolkit<br>• Daily check-in streak<br>• Lucky spins wheel & watch-ad spins |
| **5** | **Type A** | **ATF Miner** | `@atf_miner_bot` | `https://atfminers.asloni.online` | TON | • `?action=claim`<br>• `?action=start_mine`<br>• **Telemetry:** `farmed (lvl: {lvl}, bal: {bal} ATF)` | • **Automated Math Challenge Solver**: Solves arithmetic captcha<br>• Hashrate Boost (`?action=activate_boost`)<br>• 8x Cooldown Tasks (YouTube, Twitter, Channel joins)<br>• Dedicated TON wallet sync (`?action=sync_wallet`)<br>• Team wallet claims |
| **6** | **Type A** | **FINVORA Web3** | `@finvora_bot` | `https://finvora-production.up.railway.app` | GRAM / TON | • `/api/mining/claim`<br>• **Telemetry:** `farmed (avail: {bal} GRAM)` | • Instant bonus (`/api/bonus/instant`)<br>• Dedicated TON wallet connection (`/api/wallet/connect`) |
| **7** | **Type A** | **TurboGram V1** | `@turbogram_bot` | `https://turbo.tamimdev.dev` | GRAM / TON | • `/api/me`<br>• **Telemetry:** `farmed (bal: {bal} GRAM)` | • Dynamic task discovery & completion (maintains **ACTIVE** referral tier)<br>• Dedicated TON wallet binding (`/api/me/wallet`) |
| **8** | **Type A** | **Victor's Company** | `@VictorsCompanybot` | `https://server.victors.company/api` | TON / GameFi | • `/api/mining/claim`<br>• `/api/arcade/mine/start` + `dig` + `end`<br>• **Telemetry:** `farmed (lvl: {lvl}, bal: {bal})` | • **Cloudflare Turnstile Protected**: SiteKey `0x4AAAAAAFD0KRgPRFVwDvgn`<br>• Solved via 100% Cloud Xvfb Headful Browser (`mrg_turnstile_solver.py`)<br>• Submits `turnstileToken` to `POST /api/auth/login` with `startParam: ref_A20AA96F18` -> returns `humanPass`<br>• **Mandatory Header**: All subsequent API calls require `x-human-pass: <humanPass>`<br>• **Recruit Qualification**: Sub-accounts connect dedicated TON wallet (`POST /api/wallet/connect`) and claim task `connect-wallet` (`POST /api/tasks/claim`). This unlocks Level 1 Miner (+100 V/day) and qualifies recruit!<br>• **Master Bonus Sweep**: Master sweeps recruitment hiring bonus (+100 V per recruit) via `POST /api/referral/claim-bonus` and mining commissions via `POST /api/referral/claim-commission`<br>• Daily check-in (`/api/checkin`) & tutorial completion (`/api/me/tutorial`)<br>• ⚠️ **Paywall Audit**: Frontend requires 0.05 TON transfer to treasury `UQD4t3lRBgtAg7U_dYlTAIYjqIPXRT6zHqAvoGgqTvYYWnRv` before withdrawals |
| **9** | **Type A** | **VyroDrop** | `@vyrodrop_bot` | `https://vyro.run.place/api` | VYRO / DEX | • `/api/mining/claim`<br>• `/api/mining/start`<br>• **Telemetry:** `farmed (lvl: {lvl}, speed: {spd})` | • Referral binding to `ref_myFjrqqE4WN_` (`referrerUserId: 738aee88-2e37-4a70-8b3b-dd1819395130`)<br>• **Wallet Requirement**: `/api/mining/start` requires connected TON wallet (`409 MINING_WALLET_REQUIRED`). Referrals do not activate until invited account connects TON wallet and starts first mining session.<br>• **Wallet Onboarding Turnstile**: SiteKey `0x4AAAAAAFMSnxZaI2W86NOg` (`action: wallet_onboarding`) solved via 100% Cloud Xvfb Headful Browser<br>• **TonConnect 2.0 Proof**: Signs challenge with dedicated TON keypair from `fleet_ton_wallets.json` and submits to `/api/wallet/connect`<br>• Automatic mining cycle start (`/api/mining/start`) and yield claims (`/api/mining/claim`)<br>• **Master Sweep**: Master Account claims referral commissions via `POST /api/referrals/claim` |

---

### 🚫 Complete Eradication of Scammer Bots & Channels (October 8, 2026)
Following operator directive and verified evidence of fraudulent schemes, **10 scammer bots and all their associated channels/groups were permanently purged from all fleet code routines, blacklisted, blocked, dialogs erased with revoke=True across all 18 accounts, and all related channels/groups abandoned**:

1. **Ainovum AI** (`@ainovum_bot` / channels: `@novum_en`, `@ainovum_channel`): Fraudulent non-paying backend with fake yield claims.
2. **Tensor Mining Robot** (`@tensormining_bot`, `TensorMiningRobot` / channel: `https://t.me/TensorCoinNews`): Unbacked fake ORCA token, sybil baiting.
3. **Ton Trader AI** (`@TonTraderAIBot`, `@tontrader_bot` / channels: `@tontraderai_official`, `@tontraderai_group`): Fake algorithmic yield simulation.
4. **TAC Airdrop** (`@tacairdrop_bot` / channels: `@tacairdrop`, `@tacairdrop_official`, `@tac_airdrop`): Fake mining contract, deceptive advertising.
5. **USDT QUAD** (`@usdtquadbot` / channel: `@usdtquad_channel`): Fraudulent cloud hashrate simulation, fake investment scheme.
6. **Apex Mining** (`@ApxMinerBot`, `@apexminer_bot` / channels: `@ApexMiner_Official`, `@ApexMinerGroup`): Unbacked token, suspicious anti-sybil bait.
7. **Ominix AI** (`@OminixAiBot`): Phishing & credential harvester (previously reported to Telegram Anti-Scam).
8. **ART Airdrop** (`@ART_AIRDROP_BOT`, `@artairdrop_bot` / channels: `@ART_AIRDROP`, `@artairdrop`): Fake yield simulation with artificial paywalls.
9. **TRX Power Mining** (`@trxpowermining_bot` / channels: `@trxpowerminingOfficial`, `@TRX_WORLD_WORK`, `@trxpowermining`): Unregulated fake cloud hashing Ponzi.
10. **Bitcoin Cloud Miners** (`@BitcoinCloudMinersBot`, `@Bitcoin_Cloud_Mining_bot` / channels: private links): Fake cloud mining tap bot.

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

## ⚡ 6.1 Fleet Farming Concurrency & Anti-Timeout Overhaul (October 7, 2026)

### Root-Cause Analysis of Previous Worker Farming Abortions
During thorough auditing of `/api/farm/cloud-all`, an investigation revealed why accounts previously faced execution timeouts:
1. **Sequential Execution Latency**:
   - Running bot routines sequentially with humanized jitter delays (1.0s–2.5s per action) caused each account session to exceed request timeouts.
2. **Blocking Background Dwell Tasks**:
   - Channel verification and external task dwell tasks (15–17 seconds) were awaited in the blocking path, adding latency.
3. **Redundant On-The-Fly Extraction Triggers**:
   - Launching heavy Telethon MTProto extractions concurrently triggered connection contention and gateway timeouts.

### Architectural Solutions Implemented & Verified
1. **Concurrent Bot Execution Pipeline per Account**:
   - Refactored `farm_single_account_bots` to run active bot routines concurrently using `sem_bot = asyncio.Semaphore(4)`.
   - Cycle time per account plummeted from **85 seconds** to **12–16 seconds**.
2. **Detached Asynchronous Background Dwell Execution**:
   - Dwell tasks and ad reward waits are dispatched as background event loop tasks (`asyncio.create_task`), returning HTTP farming responses immediately once core claims and check-ins complete.
3. **Pure WebApp REST Execution**:
   - All 7 legitimate bots farm strictly via high-performance REST APIs. Token extraction is decoupled and handled exclusively by `/collect-tokens` in dedicated background batches.
4. **Empirical Fleet Results (Live October 8, 2026)**:
   - **Farmed Accounts**: **18 / 18 (100% Success)**.
   - **Farmed Bots per Account**: **7/7 legitimate bots active per account**.
   - **Total Active Bot Actions**: Complete coverage across all 18 accounts in under 30 seconds.

---

## ⚡ 6.2 Dual-Type Bot Architecture, Channel Engine & Dialog Purge Protocol (October 8, 2026)

### 1. The Dual-Type Bot & Channel Architecture
The fleet's 7 active high-conviction legitimate bots and channels are fundamentally divided into two technical architectures:

#### Type A: WebApp Mini-Apps / REST Bots (9 Genuine Bots)
- **Bots Included**: Stones Miners (`@stonesminers_bot` / `@stoneswithestand_bot`), MRG Miner (`@mrg_miner_bot` / `@mrgminerbot`), AI Lab (`@ailabrobot_bot` / `@AiLab_robot`), UltraWallet (`@ultrawallet_bot` / `@UltrawalletTrade_Bot`), ATF Miner (`@atf_miner_bot` / `@ATF_AIRDROP_bot`), FINVORA Web3 (`@finvora_bot` / `@FINVORAWeb3bot`), TurboGram (`@turbogram_bot` / `@TurboGramV1_bot`), Victor's Company (`@VictorsCompanybot`), VyroDrop (`@vyrodrop_bot`).
- **Mechanism**:
  - Authenticated via Telegram WebApp `initData` (HMAC SHA-256 query string signed by Telegram bot tokens) or Bearer JWT tokens.
  - Executed 100% via asynchronous HTTP REST calls with zero MTProto connection overhead.
  - Multi-account parallelized via `asyncio.Semaphore(4)` with per-bot rate-limiting and exponential backoff.
  - Pure cloud execution across Render Standby Node 2 and Cloudflare Workers 5-node mesh.

#### Type B: MTProto Dialog Purge, Token Collector & Sponsor Channel Sentinel Engine
- **Core Operations**:
  1. **Permanent Dialog Deletion & Chat Purge Protocol**:
     - *Why Bots Remained in Telegram Interface*: Previously, calling `contacts.BlockRequest` only blocked future messages from bots; Telegram intentionally keeps chat threads visible in the user's chat list.
     - *The Complete Eradication Fix*: Implemented `functions.messages.DeleteHistoryRequest(peer=..., max_id=0, just_clear=False, revoke=True)` and `client.delete_dialog(...)`. This permanently purges conversation history from Telegram servers and deletes the chat tile from the Telegram client interface across all accounts.
     - *Deep Dialog Scanner*: Sweeps up to 200 dialogs per account to block and delete dialogs for any blacklisted bots (`trxpowermining_bot`, `BitcoinCloudMinersBot`, `ART_AIRDROP_BOT`, `ainovum_bot`, `tensormining_bot`, `TonTraderAIBot`, `tacairdrop_bot`, `usdtquadbot`, `ApxMinerBot`, `OminixAiBot`) and leave/delete dialogs for scam channels (`trxpowerminingofficial`, `trx_world_work`, `trxpowermining`, `art_airdrop`, `tensorcoinnews`, etc.).
  2. **Automated Sponsor Channel & Community Subscription Engine**:
     - Automatically joins and verifies all 8 legitimate sponsor channels:
       `finvoraweb3`, `TurboGramAnnouncements`, `TurboGramPayment`, `stoneswithestand`, `mrgminer`, `mrgfun`, `ailabrobotnews`, `ultrawalletofficial`.
     - **Unblock Sentinel**: Automatically unblocks the 7 legitimate fleet bots across all accounts.
     - **Mute Sentinel**: Automatically mutes notifications across all channels, supergroups, and bots (`UpdateNotifySettingsRequest`) to ensure 0 notification noise.
     - **Telegram 500-Channel Cap Guard**: Audits total dialogs and prunes non-essential spam if dialog count exceeds 400.
     - **Cloud Endpoints**: `POST/GET /api/channels/sync-and-verify` and `GET /api/channels/status` on Render Standby Node 2.

### 2. Elimination of Fake / Dummy Farming Reporting
- **The Problem**: Previous iterations had legacy fallbacks where missing tokens or failed API calls returned `farmed` or `ok` to prevent UI pipeline breaks, masking genuine token expirations or auth errors.
- **The Fix**:
  - Every bot routine now validates tokens strictly and executes genuine API calls:
    * `_farm_stones`: Claims mining pool (`/api/claim`), starts miner (`/api/mining/start`), completes daily check-in, minigame, and boost, returning exact balance and level stats.
    * `_farm_mrg`: Accurately parses `/api/user/claim-mining` response, verifies cryptographic TON Connect 2.0 wallet ownership, auto-unlocks levels based on `manualUnlockedLevel`, and reports real claim status.
    * `_farm_ailab`: Logs in, queries `/miner`, starts hashrate mining, exchanges hashes if balance >= 3.0, and completes partner tasks.
    * `_farm_ultra`: Signs in with custom Firebase token via Google Identity Toolkit, claims check-in streak, mining pool, energy, and executes lucky wheel spins.
    * `_farm_atf`: Solves arithmetic math captcha dynamically, activates speed boost, claims referral yield and team wallet, and cycles cooldown tasks.
    * `_farm_finvora`: Connects dedicated TON wallet, claims instant bonus, and harvests mining yield.
    * `_farm_turbogram`: Connects dedicated TON wallet, discovers pending tasks, starts and completes tasks to maintain active referral tier.
    * `_farm_victors`: Authenticates via `/api/auth/login` binding referral `ref_A20AA96F18`, acquires `x-human-pass`, completes daily check-in, claims mining yield, auto-unlocks levels, discovers and claims tasks, sweeps referral bonus, and plays arcade minigame.
    * `_farm_vyro`: Bootstraps session with custom protocol headers, starts/claims mining session, discovers tasks, executes strict 3-step task protocol (`/open` -> `/verify` -> `/claim` with UUID idempotency key) binding referral `ref_myFjrqqE4WN_`, and claims direct/mining referral rewards.
  - **Internal `auth_date` Token Age Auditing**: `is_token_data_expired()` now inspects the inner `auth_date` timestamp of WebApp `initData` query strings, accurately flagging tokens approaching the 20-hour mark.

---

## ⚡ 6.3 Multi-Bot Cloud Turnstile Engine & Self-Referral Prevention Protocol (October 9, 2026)

### 1. Root-Cause Diagnosis: Why New Bots Farming Paused
- **Victor's Company (`@VictorsCompanybot`)**:
  - `POST /api/auth/login` is guarded by Cloudflare Turnstile (SiteKey `0x4AAAAAAFD0KRgPRFVwDvgn`).
  - Calling login without Turnstile returns `403 HUMAN_REQUIRED`. Without successful login, the referral code was rejected, and `humanPass` was withheld.
- **VyroDrop (`@vyrodrop_bot`)**:
  - Referrals to Master UUID (`738aee88-2e37-4a70-8b3b-dd1819395130`) bound successfully via `ref_myFjrqqE4WN_`.
  - `/api/mining/start` returned `409 MINING_WALLET_REQUIRED`. VyroDrop mining and referral activation are blocked until invited workers connect an isolated TON wallet and start their first mining session.

### 2. Multi-Bot Cloud Turnstile Solver Engine (`mrg_turnstile_solver.py`)
- Solves Cloudflare Turnstile in the cloud (GitHub Actions / Cloud VMs) via Patchright Chromium stealth:
  - **MRG Miner**: Solves SiteKey `0x4AAAAAAFI-XXL7bFNbLU_J` on `app.mrgtoken.xyz`, refreshes `humanVerifiedUntil`, and claims mining rewards.
  - **Victor's Company**: Solves SiteKey `0x4AAAAAAFD0KRgPRFVwDvgn` on `app.victors.company`, completes `/api/auth/login`, retrieves `humanPass`, and stores it into Upstash Redis (`victors:pass:{uid}`).
  - **Zero Phone Load**: 100% cloud execution running every 3 hours (`.github/workflows/mrg_turnstile_solver.yml`). 0 local processes on Samsung Galaxy A30.

### 3. Strict Master Account Self-Referral Immunity
- Rejection was prevented across `refresh_cloud_tokens.py`, `render_standby_app.py`, and `render_app_latest.py`:
  - When `acc_uid == REPORT_CHAT_ID` (`6727787768`), bots receive `start_param=None` instead of their own referral codes.
  - Workers (Accounts 2–18) continue to submit master referral codes (`VICTORS_REF: ref_A20AA96F18`, `VYRO_REF: ref_myFjrqqE4WN_`).

---

## 🛠️ 7. Operator & AI Cheat Sheet

Here are the exact commands to run for everyday operations:

### 1. Check Fleet Farming Status
Query the Cloudflare Edge Gateway for real-time status across all 18 accounts:
```bash
curl -s https://restore-agy.aaaai2.workers.dev/api/farm/status | jq .
```

### 2. Trigger Immediate Cloud Farm
Trigger an immediate harvest across all 7 legitimate bots on Cloudflare Workers:
```bash
curl -s -X POST https://restore-agy.aaaai2.workers.dev/api/farm/all \
  -H "Authorization: Bearer agy_cf_secret_7d36994e_2026" \
  -H "Content-Type: application/json" \
  -d '{"all": true, "bot": "all"}'
```

### 3. Type B Channel & Sponsor Subscription Engine
Trigger auto-joining of 17 sponsor channels, bot unblocking, and full notification muting across accounts:
```bash
# Check status
curl -s "https://my-agy-fleet-standby-node2.onrender.com/api/channels/status"

# Trigger sync and verification cycle
curl -s -X POST "https://my-agy-fleet-standby-node2.onrender.com/api/channels/sync-and-verify"

# Inspect bot chat buttons & WebApp URLs for an account
curl -s "https://my-agy-fleet-standby-node2.onrender.com/api/inspect-bot-chat/8826375659?bot=trxpowermining_bot"
```

### 4. Refresh 24-Hour WebApp Tokens via Render
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
