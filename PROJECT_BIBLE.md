# 📖 PROJECT BIBLE — AAA AUTO / MY AGY AI
> **Universal Onboarding, System Architecture, 5-Bot Fleet Engine & Operational Manual**
> *Maintainer: Antigravity AI Pair Programming System*
> *Last Updated: October 12, 2026*
> *Classification: Mission-Critical Living Technical Documentation*

---

## 🎯 1. Executive Summary & Purpose

If you are an AI assistant (Antigravity, Claude, GPT, Gemini, Llama) starting a new session, or a human operator taking over this workspace, **read this entire document first**. It provides the complete picture of this project, how every component works, where every secret and service lives, and how to operate and extend it without breaking production.

### What is this Project?
**AAA AUTO** (also known as **MY AGY AI Fleet**) is an enterprise-grade, cloud-first autonomous crypto farming and userbot fleet management infrastructure. It manages **18 Telegram accounts** (1 Master Account + 17 Worker Accounts) that continuously farm yield, satoshis, and tokens across **5 high-conviction legitimate Telegram WebApp Mini Apps** (MRG Miner, ATF Miner, Victor's Company, VyroDrop, Kynex Network — all scammer and discontinued bots purged and blacklisted), while managing dedicated multi-chain non-custodial wallets (EVM/BSC, TON, TRON, Solana, Bitcoin).

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
   - All bots operate in pure asset accumulation and auto-reinvest mode (e.g. MRG upgrades miners, ATF compounds hash, Victor's compounds passes).
5. **📝 Living Memory & Changelog**:
   - Whenever any file, function, bot, or architecture decision is modified, added, or removed, **always document it immediately** in `CHANGELOG.md` and update this `PROJECT_BIBLE.md`.
6. **🔇 Absolute Zero-Chat Policy for Fleet Accounts**:
   - All 18 fleet accounts interact exclusively through **Telegram Mini App REST APIs** (authenticating with signed `tgWebAppData` extracted silently via `RequestAppWebViewRequest`).
   - **NEVER send `/start`, `/start <ref>`, `mine`, or text messages into Telegram bot chats**. Bot chats must remain 100% silent and clean.
   - Referral binding is handled strictly via `start_param` in `RequestAppWebViewRequest` or directly in REST API authentication handshakes (e.g. MRG `/api/auth/verify`, ATF `action=login` `ref` parameter).

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
│  │  • Node 2 (Frankfurt): Shard 1 (Acc 1-9│  │  • aaaai2.workers.dev (Shard 0)      │  │
│  │    + Primary MTProto Auth & OTP Gateway│  │  • aaa-bot.workers.dev (Shard 1)     │  │
│  │  • Node 3 (Oregon): Shard 2 (Acc 10-18)│  │  • aaa222.workers.dev (Shard 2)      │  │
│  │    + Failover MTProto Gateway          │  │  • agorameet.workers.dev (Shard 3)   │  │
│  │  • Node 1 (Singapore): Standby Archive │  │  • aaaai.workers.dev (Shard 4)       │  │
│  │                                        │  │                                      │  │
│  │  Role: Parallel MTProto & Farming Shard│  │  Role: 24/7 Edge Autonomous Farming   │  │
│  │  - Partitioned Shard 1 (1-9) & 2 (10-18│  │  - Runs cron every 15 mins           │  │
│  │  - Cuts memory, CPU & MTProto load 50% │  │  - Farms all 5 legitimate bots        │  │
│  │  - Debounced anti-duplicate code retry │  │  - Executes side tasks & check-ins   │  │
│  │  - Extracts fresh 24h WebApp initData  │  │  - Fast, serverless, zero ban risk   │  │
│  │  - Syncs tokens to D1, Upstash & KV     │  │  - Propagates cached Turnstile passes │  │
│  │  - Endpoint: POST /collect-tokens      │  │                                      │  │
│  └───────────────────┬────────────────────┘  └──────────────────▲───────────────────┘  │
│                      ▼                                          │ Reads Fresh Tokens   │
│  ┌──────────────────────────────────────────────────────────────┴───────────────────┐  │
│  │                        Upstash Serverless Redis REST                             │  │
│  │  • URL: https://pleasant-locust-220893.upstash.io                                │  │
│  │  • Key: fleet:tokens:<uid> (Contains active WebApp initData for each account)    │  │
│  │  • Key: fleet:wallets:ton (Contains isolated TON wallets & recovery mnemonics)   │  │
│  │  • Key: victors:pass:<uid> (Contains fresh Cloudflare Turnstile humanPass)       │  │
│  │  • Key: fleet:live_state (Contains latest real-time farming results)             │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Cloud Nodes Directory (5 Cloudflare Accounts & 5 Render Accounts / 6 Services)
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
  - **Active-Passive / Failover Edge Architecture (Zero Daily KV Write Quota Exhaustion)**:
    * **Node 1 (Primary: `aaaai2.workers.dev`)**: The ONLY node provisioned with the 15-minute Edge Cron trigger (`*/15 * * * *`). Handles primary cron farming cycles, D1 logs, and periodic state updates.
    * **Nodes 2, 3, 4, 5 (Passive Standby / Failover)**: Crons disabled (`[]` empty list). Early exit in `scheduled()` (`if (CURRENT_SUBDOMAIN !== "aaaai2") return;`). Generates 0 scheduled operations and 0 KV writes. If Node 1 is ever offline, any standby can be promoted to primary instantly.
    * **Zero KV Ephemeral Caching**: `/api/rates` cached in module-scope memory (`memRatesCache`) with CDN `max-age=120`, eliminating KV writes for Binance rates. Sibling upload fan-out replication removed; standbys proxy `/backup.zip` on demand without local KV storage.
    * **Resilient Login State Machine**: `login_flow:${chatId}` uses in-memory `memLoginFlow` Map and Upstash Redis first, ensuring user login flows never fail when Cloudflare KV quotas are hit.
- **Cloudflare Workers Edge Admin Bot Hosting (100% Cloudflare Edge — NOT Telegram Serverless)**:
  - **MANDATORY POLICY**: The Admin Bot (`@myagyai`, ID `8858823950`) webhook is hosted **100% permanently on Cloudflare Workers Edge**, NOT Telegram Serverless (`tgcloud.ai`).
  - **Live Webhook URL**: `https://restore-agy.aaaai2.workers.dev/telegram-webhook`
  - **Verification**: Verified with Telegram Bot API `getWebhookInfo` (`ip_address: "188.114.96.0"` (Cloudflare), `pending_update_count: 0`).
  - **Why Telegram Serverless (`tgcloud.ai`) Was Retired for Bot Webhooks**:
    * `tgcloud.ai` is an experimental beta runtime. During container cold restarts or edge scale-downs, Telegram automatically wiped the bot's webhook to `""` (blank).
    * This caused the Admin Bot to go completely silent and fail to respond to commands like `🔄 Refresh Menu`, `/start`, `/farm`, or OTP requests.
    * Cloudflare Workers Edge provides 100% uptime SLA, globally distributed V8 isolates, instant sub-50ms response times, and never drops webhooks.
  - **Auxiliary Mini App**: The static WebApp interface `https://app8858823950.tgcloud.ai/` remains accessible as an optional client UI, but all bot logic, webhook routing, callback handling, and command processing execute strictly on Cloudflare Workers Edge (`deploy_both_cf_workers.py`).
  - **Interactive Features on Cloudflare Edge**:
    * Full button-based menus, OTP extraction (`/otp`), wallet inspection (`/wallets`, `/wallet <1-18>`), AI Copilot (`/deepseek`, `/llama`, `/ai`, `/image`), multi-node farming triggers (`/farm`), Turnstile dispatch, and Render standby relay control.
    * Added explicit support for inline keyboard button `🔄 Refresh Menu` returning the full private console dashboard.


- **Render Cloud Fleet (The 3 Official Accounts — 600-650h Baton Relay & Anti-Ban Maintenance Mode)**:
  - **Account 1: Node 1 (Singapore)**: `https://my-agy-fleet-standby.onrender.com`
    * Service ID: `srv-damuhkmgekts73f1osag` | Workspace: `My Workspace` (`tea-d8j9clt8nd3s73eb041g`, `coz1gameh1@gmail.com`)
    * API Key: `RENDER_API_KEY_1: rnd_cGQwvG9J4pe6Rpf06sRMb4pzR6v1` | Linked Repo: `https://github.com/AAA0002/my-agy-fleet-standby` (main)
    * Status: ⏸️ **Suspended** (0 hours consumed / cold standby). Protected user service `temp-mail-bot` (`srv-d8j9n867r5hc73dlqvgg`) is blacklisted and permanently isolated.
  - **Account 2: Node 2 (Frankfurt)**: `https://my-agy-fleet-standby-node2.onrender.com`
    * Service ID: `srv-dan5q00ae00c73djummg` | Workspace: `Abid's workspace` (`tea-dan5pgbm8hqs73a5cvig`, `abidhasanch2001@gmail.com`)
    * API Key: `RENDER_API_KEY_2: rnd_KnVaiOw93SKa4fSTrEURwZrP0UaB` | Linked Repo: `https://github.com/AAA0002/my-agy-fleet-standby` (main)
    * Status: 🟢 **ACTIVE & ONLINE** — Designated Primary MTProto Coordinator.
  - **Account 3: Node 3 (Oregon)**: `https://my-agy-fleet-standby-node3.onrender.com`
    * Service ID: `srv-db437o3tqb8s73dt4erg` | Workspace: `Koram's workspace` (`tea-daoj9nid0e5s738gqp0g`, `koramshah2@gmail.com`)
    * API Key: `RENDER_API_KEY_3: rnd_PqsurfX5D9blSaEEuEDDAUcl393y` | Linked Repo: `https://github.com/koramshah2/my-agy-fleet-standby` (main)
    * Status: ⏸️ **Suspended** (0 hours consumed / cold standby failover).
  - **🔄 600–650 Hour Baton Relay Handover Protocol**:
    * Render free tier grants 750 hours/month per account (1 calendar month = 744 hours).
    * When a service is suspended via `POST /v1/services/{id}/suspend`, its hour meter freezes to 0.
    * Active node tracks its monthly uptime in Upstash Redis (`fleet:uptime_hours:node{id}:{YYYY-MM}`).
    * At **620 hours** (~Day 25/26), the active node automatically triggers a clean Baton Relay rotation to the next node in the ring (`Node 2 -> Node 3 -> Node 1 -> Node 2`).
    * On the 1st of every month, Render automatically resets free tier hours to 750, ensuring infinite zero-cost runtime.
  - **🛡️ Telegram Anti-Ban Maintenance Mode & Graceful Disconnect**:
    * **Root Cause of Session Bans (`AuthKeyDuplicatedError`)**: Connecting to Telegram from two different cloud IPs simultaneously triggers immediate Telegram account revocation.
    * **Dynamic Coordinator Auto-Detection**: Replaced static import-time checks with dynamic `is_this_node_active()` and canonical node ID mapping (`get_current_node_number()`), allowing whichever node is designated active in Upstash Redis (`fleet:active_render_node`) to seamlessly take over MTProto connections while standby nodes remain silent.
    * **Maintenance Mode (5-Minute Cooling Buffer)**:
      1. Rotation triggers `fleet:maintenance_mode = true` and `fleet:maintenance_until` (300 seconds) in Redis.
      2. Telegram Admin Bot alert dispatched to `@myagyai`.
      3. Destination node is resumed via Render API (`POST /v1/services/{new_id}/resume`) and polled for healthy status (up to 120s max). If destination fails to boot, rotation safely aborts and keeps source node active.
      4. Source node severs all MTProto sockets cleanly (`POST /api/fleet/disconnect-mtproto`, including in-flight `ACTIVE_MTPROTO_CLIENTS`).
      5. Source node suspends itself (`POST /v1/services/{old_id}/suspend`) -> container stops, hours stop.
      6. System enforces 5-minute cooldown where NO MTProto connections are made, allowing Telegram datacenter servers to completely flush old socket states and NAT bindings.
      7. Maintenance Mode expires, new node promotes itself to active coordinator, and normal farming resumes on a clean single IP.
  - **🌐 Dedicated Relayers & Auxiliary AI Services**:
    * Primary MTProto Relayer: `https://atf-mtproto-relayer.onrender.com/wake` (🟢 ONLINE & AUTHENTICATED)
    * Backup MTProto Relayer: `https://atf-mtproto-relayer-backup.onrender.com/wake` (🟢 ONLINE & AUTHENTICATED)
    * Hermes Ari AI Council Agent: `https://hermes-grok-cloud-agent.onrender.com` (🟢 ONLINE, Koram account, Groq AI Council)

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
  - **100% Cloud MTProto Token Refresher & Auto-Farming Pipeline**:
    * Workflow File: `.github/workflows/cloud_token_refresher.yml` (Runs every 2 hours: `0 */2 * * *`).
    * Script: `refresh_cloud_tokens.py` (Connects MTProto in cloud, harvests fresh 24h WebApp `initData`, syncs to 5x Cloudflare Nodes and Upstash Redis).
    * Auto-Dispatch Pipeline: Automatically triggers `.github/workflows/mrg_turnstile_solver.yml` and Render Standby multi-node farming upon completion.
  - **100% Cloud Multi-Bot Turnstile Solver & Auto-Farming Workflow**:
    * Workflow File: `.github/workflows/mrg_turnstile_solver.yml` (Runs every 4 hours: `0 */4 * * *`, ensuring Victor's Company and MRG human passes stay perpetually fresh before their 6–8h expiration).
    * Timeout: 40 minutes (`timeout-minutes: 40`), preventing premature cancellation across 18 fleet accounts.
    * Script: `mrg_turnstile_solver.py` (Patchright Chromium stealth engine, Turnstile script loader race guard, dual-action targeted iframe element and frame locator clicks on `#challenge-stage, .ctp-checkbox-label, .mark`, real Telegram `initData` simulation, TonConnect 2.0 wallet onboarding, Turnstile iframe solver, and full reward auto-compounder).
    * Zero Phone Load: Runs 100% inside GitHub's cloud runner environment (Ubuntu 24.04, 7GB RAM).

- **Retired Telegram Serverless Platform (`tgcloud.ai` - Deprecated for Bot Webhooks)**:
  - Mini App Static Mirror: `https://app8858823950.tgcloud.ai/` (static UI frontend only).
  - **Status**: Retired & replaced by Cloudflare Workers Edge (`https://restore-agy.aaaai2.workers.dev/telegram-webhook`) for all bot webhooks and backend execution.
  - Reason: `tgcloud.ai` wiped webhooks during cold restarts. Cloudflare Edge provides 100% stability, never clears webhooks, and has zero cold-start delay.

- **Telegram Dual Bot & Channel Ecosystem (Admin Infrastructure vs. Normal User Platform)**:

  #### 🛡️ System 1: Admin Telegram Ecosystem (Control, Telemetry, Vault, Disaster Recovery)
  *Dedicated exclusively to system administrators, automated disaster recovery, on-chain telemetry, and AI command execution.*
  - **Admin Bot**: `@myagyai` (Bot ID: `8858823950`, Token: `REPORT_BOT_TOKEN: 8858823950:AAEdX47g7as1xLYEudfRUHaVGUdNIaU_ku8`)
    - Purpose: Autonomous execution reporting, harvest alerts, multi-model AI copilot, Better Stack dead-man pings, and automated backup broadcasts.
    - **Serverless Cloud AI Mesh**:
      * `/deepseek <prompt>`: DeepSeek R1 32B reasoning on Cloudflare Edge GPUs.
      * `/llama <prompt>`: Meta Llama 3.2 rapid edge copilot.
      * `/image <prompt>` / `/draw <prompt>`: Stable Diffusion XL binary photo generator with direct Telegram photo upload.
      * `/ai <prompt>`: Google Gemini 3.8 Flash with 5-key dynamic rotation & instant Llama edge fallback.
      * `/mrg`, `/atf`, `/victors`, `/vyro`, `/kynex`: Dedicated telemetry & command centers for all 5 legitimate active bots.
      * `/models`: Directory of active edge AI models.
    - **Executive Fleet Operations Console (`/admin`)**:
      * Live URL: `https://restore-agy.aaaai2.workers.dev/admin` (embedded across all 5 Cloudflare Worker nodes).
      * Features: All 18 accounts, Multi-Model Ari AI Studio, Dedicated OTP & Relogin Center (#1-18), Multi-Chain Treasury, 5-Node Edge Mesh latency matrix, Obsidian Dark & Clean Light theme.
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
| **Serverless Database** | **Upstash Redis** | `pleasant-locust-220893.upstash.io` | 🟢 **HTTP 200 OK** — Brand new active database (10k fresh commands/day) |
| **Serverless Database** | **Turso LibSQL** | `my-agy-fleet-db-aaa2743.aws-ap-south-1.turso.io` | 🟢 **HTTP 200 OK** — Distributed SQLite edge database |
| **Cloud Postgres** | **Supabase Cloud** | `znbbaozpevurvbfkxakz.supabase.co` | 🟢 **HTTP 200 OK** — Managed PostgreSQL database via Service Role Key |
| **Cloud Database** | **Layerbase Cloud** | `api.layerbase.com` | 🟢 **ACTIVE** — 6 Managed database instances (QuestDB, InfluxDB, Weaviate) |
| **Vector Database** | **Qdrant Cloud** | `cloud.qdrant.io` | 🟢 **MANAGEMENT KEYS ACTIVE** — Semantic memory and embedding clusters |
| **CI/CD Cloud Compute** | **CircleCI Cloud** | `circleci.com` | 🟢 **1-YEAR TOKEN ACTIVE** — Cloud automation runner (`aaa.support.a@gmail.com`) |
| **Cloud Compute** | **Ubicloud** | `console.ubicloud.com` | 🟢 **PAT ACTIVE** — Cloud VM & Postgres compute (`pat-akn22db4...`) |
| **Kubernetes Cluster** | **Puzl Cloud K8s** | `k8s.eu-finland-1.clusters.puzl.cloud` | 🟢 **CONFIG ACTIVE** — Finland European Kubernetes cluster context |
| **AI Inference Engine** | **Google Gemini** | `generativelanguage.googleapis.com` | 🟢 **14/14 KEYS ACTIVE** — Rotating multi-key pool for Ari AI reasoning |
| **Edge AI Inference** | **Workers AI (Cloudflare)** | Global Edge Mesh (Llama 3.2 3B Instruct) | 🟢 **ACTIVE** — Zero API keys required across 5 Cloudflare nodes |
| **Web3 Infrastructure** | **Alchemy Ethereum** | `eth-mainnet.g.alchemy.com/v2/...` | 🟢 **HTTP 200 OK** — Live block height queries verified |
| **Web3 Infrastructure** | **Toncenter Official** | `https://toncenter.com/api/v2` | 🟢 **HTTP 200 OK** — High-speed TON masterchain RPC |
| **Web3 Infrastructure** | **TonAPI Key** | `https://tonapi.io` | 🟢 **ACTIVE** — Jetton transfers and account audits |
| **Web3 Infrastructure** | **Etherscan API** | `api.etherscan.io` | 🟢 **ACTIVE** — EVM on-chain verification key |
| **Rotating Proxy Pool** | **Webshare Proxies** | `proxy.webshare.io` | 🟢 **20 ACTIVE PROXIES** — Residential/datacenter proxy pool across 2 keys |
| **Cloud Scheduler** | **Cron-Job.org** | `api.cron-job.org` | 🟢 **ACTIVE (8 JOBS)** — Keep-alives for Render Node 1/2/3 & Deno; 30m autonomous cloud farming sweeps on Node 2 (8614058) & Node 3 (8614059) |
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
   - Cloudflare Workers Edge Mesh and Render Standby execute farming via an intelligent **Humanistic Per-Bot Cadence Engine**:
     * **ATF Miner**: 2.0h – 3.0h (7,200s – 10,800s, avg 2.5h) — matches 2-hour task refresh cycle.
     * **MRG Miner**: 3.0h – 4.0h (10,800s – 14,400s, avg 3.5h) — matches 3-4h hashrate claim cycle.
     * **Victor's Company**: 4.0h – 5.0h (14,400s – 18,000s, avg 4.5h) — matches arcade energy & offline earnings accumulation.
     * **VyroDrop**: 4.0h – 6.0h (14,400s – 21,600s, avg 5.0h) — matches mining session duration.
     * **Kynex Network**: 6.0h – 8.0h (21,600s – 28,800s, avg 7.0h) — matches 12h energy bar replenishment.
     * **Zero Chat Spam Rule**: Tokens are queried 100% silently via `RequestAppWebViewRequest`. ZERO `/start` or `mine` messages are sent into Telegram bot chats. Master Account (`6727787768`) is guarded against self-referrals.

---

## 👥 4. Fleet Accounts & Multi-Chain Wallet System

The fleet consists of **18 Telegram accounts**:
- **Master Account**: UID `6727787768` (`Arif Hossain` / `@Arif2743aaa` / `@myagyai`). All worker referral links, commission sweeps, and team bonuses flow into this account.
- **Worker Accounts (17 Accounts)**: UIDs `8881914294`, `7648254021`, `8826375659`, `8450010161`, `8782429452`, `7734849205`, `8025472383`, `8851426148`, `8203342513`, `8190649727`, `7487048946`, `8741547543`, `8727040932`, `7749125802`, `7954290138`, `8975442879`, `8841038141`.

### 👥 The 18 Fleet Accounts Roster & Ownership Classification
To protect against automated Telegram Sybil bans and wipe away seller artifacts, all purchased accounts have been renamed with completely natural, human names and authentic usernames:
- **Personal Accounts (8 Accounts — 100% Preserved & Immutable)**:
  1. `Arif Hossain` (`+8801317342850`, `@Arif2743aaa`, UID `6727787768`) — Primary Master Account
  2. `Koram Shah` (`+8801790208077`, `@Koram_Shah`, UID `7648254021`) — Account #3
  3. `Arif` (`+8801575842094`, `@Arif2743_a`, UID `8826375659`) — Account #4
  4. `MD. ARIF HOSSAIN` (`+8801571089931`, `@aaamah222`, UID `8190649727`) — Account #11
  5. `Abid Hasan` (`+8801718056423`, `@Abidhasan222`, UID `7734849205`) — Account #7
  6. `Abid Hasan` (`+8801797795624`, UID `8025472383`) — Account #8
  7. `Abid` (`+8801838268380`, `@Abid_300`, UID `8741547543`) — Account #13
  8. `Sanzida Shimu` (`+8801774578536`, `@Sanzidashimu`, UID `7487048946`) — Account #12
- **Purchased Worker Accounts (10 Accounts — Hardened With Numbered Natural Names & Wallet Parity)**:
  9. `Nancy Davis 2` (`+8801943805617`, `@nancydavis_24`, UID `8881914294`) — Account #2
  10. `Nathan Miller 5` (`+14302084365`, `@nathan_miller7`, UID `8450010161`) — Account #5
  11. `Kaitlyn Ross 6` (`+8801867539837`, `@kaitlyn_ross7`, UID `8782429452`) — Account #6
  12. `Naimur Rahman 9` (`+8801727651288`, `@naimur_rhmn7`, UID `8851426148`) — Account #9
  13. `Tanvir Ahmed 10` (`+8801729892810`, `@tanvir_ahmed785`, UID `8203342513`) — Account #10
  14. `Rohan Sharma 14` (`+918930504750`, `@rohan_sharma7`, UID `8727040932`) — Account #14
  15. `Tasnim Farhana 15` (`+8801906045479`, `@tasnim_farhana7`, UID `7749125802`) — Account #15
  16. `Rashedul Islam 16` (`+8801304151082`, `@rashedul_islam7`, UID `7954290138`) — Account #16
  17. `Kawsar Mahmud 17` (`+8801879273559`, `@kawsar_mahmud7`, UID `8841038141`) — Account #17
  18. `Mehedi Hasan 18` (`+8801839716506`, `@mehedi_hasan783`, UID `8975442879`) — Account #18

### Non-Custodial Multi-Chain Wallet Isolation
To prevent Sybil detection, anti-farming bans, and wallet clustering, each account is provisioned with **dedicated, isolated addresses** stored in JSON registries:
- `fleet_ton_wallets.json` — Dedicated TON (v4r2) non-custodial wallets.
- `fleet_evm_wallets.json` — Dedicated EVM / BSC (BEP20) non-custodial wallets.
- `fleet_tron_wallets.json` — Dedicated TRON (TRC20) non-custodial wallets.
- `fleet_solana_wallets.json` — Dedicated Solana non-custodial wallets.
- `fleet_btc_wallets.json` — Dedicated Bitcoin SegWit non-custodial wallets.

---

### 🤖 5. The Complete 5-Bot Fleet Catalog & Automation Matrix

| # | Type | Bot Name | Telegram Handle | Backend URL / Host | Network | Core Farming Mechanism | Automated Side Tasks |
|---|---|---|---|---|---|---|---|
| **1** | **Type A** | **MRG Miner** | `@mrg_miner_bot` | `https://mrg.up.railway.app` | TON | • `/api/user/claim-mining`<br>• **Telemetry:** `farmed (lvl: {lvl}, bal: {bal} MRG)` | • Link tasks with 15s human dwell<br>• **Autonomous Level Upgrader**: Auto-unlocks levels up to **Level 95+** (synchronized with `manualUnlockedLevel`)<br>• **Cryptographic TON Connect 2.0 Proof**: Full Ed25519 wallet ownership verification bound across all 18 accounts (`isTonConnected: True`)<br>• Accurate claim telemetry distinguishing human check challenge from completed claims<br>• Master referral commission & team bonus claims |
| **2** | **Type A** | **ATF Miner** | `@atf_miner_bot` | `https://atfminers.asloni.online` | TON | • `?action=claim`<br>• `?action=start_mine`<br>• **Telemetry:** `farmed (lvl: {lvl}, bal: {bal} ATF)` | • **Automated Math Challenge Solver**: Solves arithmetic captcha<br>• Hashrate Boost (`?action=activate_boost`)<br>• 8x Cooldown Tasks (YouTube, Twitter, Channel joins)<br>• Dedicated TON wallet sync (`?action=sync_wallet`)<br>• Team wallet claims |
| **3** | **Type A** | **Victor's Company** | `@VictorsCompanybot` | `https://server.victors.company/api` | TON / GameFi | • `/api/mining/claim`<br>• `/api/arcade/mine/start` + `dig` + `end`<br>• **Telemetry:** `farmed (lvl: {lvl}, bal: {bal})` | • **Cloudflare Turnstile Protected**: SiteKey `0x4AAAAAAFD0KRgPRFVwDvgn`<br>• Solved via 100% Cloud Xvfb Headful Browser (`mrg_turnstile_solver.py`)<br>• Submits `turnstileToken` to `POST /api/auth/login` with `startParam: ref_A20AA96F18` -> returns `humanPass`<br>• **Mandatory Header**: All subsequent API calls require `x-human-pass: <humanPass>`<br>• **Recruit Qualification**: Sub-accounts connect dedicated TON wallet (`POST /api/wallet/connect`) and claim task `connect-wallet` (`POST /api/tasks/claim`). This unlocks Level 1 Miner (+100 V/day) and qualifies recruit!<br>• **Master Bonus Sweep**: Master sweeps recruitment hiring bonus (+100 V per recruit) via `POST /api/referral/claim-bonus` and mining commissions via `POST /api/referral/claim-commission`<br>• Daily check-in (`/api/checkin`) & tutorial completion (`/api/me/tutorial`)<br>• ⚠️ **Paywall Audit**: Frontend requires 0.05 TON transfer to treasury `UQD4t3lRBgtAg7U_dYlTAIYjqIPXRT6zHqAvoGgqTvYYWnRv` before withdrawals |
| **4** | **Type A** | **VyroDrop** | `@vyrodrop_bot` | `https://vyro.run.place/api` | VYRO / DEX | • `/api/mining/claim`<br>• `/api/mining/start`<br>• **Telemetry:** `farmed (lvl: {lvl}, speed: {spd})` | • Referral binding to `ref_myFjrqqE4WN_` (`referrerUserId: 738aee88-2e37-4a70-8b3b-dd1819395130`)<br>• **Wallet Requirement**: `/api/mining/start` requires connected TON wallet (`409 MINING_WALLET_REQUIRED`). Referrals do not activate until invited account connects TON wallet and starts first mining session.<br>• **Wallet Onboarding Turnstile**: SiteKey `0x4AAAAAAFMSnxZaI2W86NOg` (`action: wallet_onboarding`) solved via 100% Cloud Xvfb Headful Browser<br>• **TonConnect 2.0 Proof**: Signs challenge with dedicated TON keypair from `fleet_ton_wallets.json` and submits to `/api/wallet/connect`<br>• Automatic mining cycle start (`/api/mining/start`) and yield claims (`/api/mining/claim`)<br>• **Master Sweep**: Master Account claims referral commissions via `POST /api/referrals/claim` |
| **5** | **Type A** | **Kynex Network** | `@Kynex_miningbot` | `https://us-central1-keynex-e9511.cloudfunctions.net` | Firebase / KNX | • `verifyTelegramAuth`<br>• `startMining` / `claimMining`<br>• **Telemetry:** `farmed (bal: {bal} KNX, lvl: {lvl}, mining: ACTIVE)` | • **Firebase Cloud Functions Backend**: Callable endpoints on `us-central1` + Realtime Database (`europe-west1`)<br>• **Master Referral Binding**: Master account `6727787768`; worker accounts bind under `6727787768`<br>• **Starter Onboarding**: Sets starter profile in RTDB with genuine defaults (`miningPower: 12.85`, `energy: 100`, `energySeconds: 43200`)<br>• **Automated Energy Management**: Monitors energy balance (12h capacity); auto-refills when depleted<br>• **Mandatory Sponsor Channels**: Auto-joins and claims tasks `kynex_mining`, `EarnVaulte`, `solanamemes001`, `Web3Primeteam` (+1,800 KNX)<br>• **Automated Watch Ads Rewards**: Auto-claims daily rewarded ad tasks (`claimTasksAdReward`, +2,200 KNX daily)<br>• **Daily Streak Check-in**: Claims daily login bonus (`claimDailyCheckin`, +50 KNX daily) |

---

### 🔌 Plug-and-Farm Architecture (`bot_registry.py`)
To prevent repetitive manual interventions and code rewrites when onboarding new bots:
1. **Single Source of Truth (SSOT)**: All bots are declared centrally in `bot_registry.py`. Each entry defines `bot_username`, `master_ref_code`, `app_url`, `token_key`, `short_names`, `api_base`, `sponsor_channels`, and `requires_turnstile`.
2. **Zero-Touch Onboarding**: Adding any new bot in the future requires only one dictionary entry in `bot_registry.py`. The cloud token refresher (`refresh_cloud_tokens.py`), referral binder (`login_account.py`), and 24/7 cloud auto-farming engines automatically ingest new bots dynamically.
3. **Automated New Account Referral Binding (`bind_referrals`)**:
   Whenever a new Telegram account is added to the fleet, `login_account.bind_referrals` runs automatically:
   - `@mrgminerbot`: sends `/start ref_IRN1G3XD`, opens WebApp, and binds the account's TON wallet.
   - `@ATF_AIRDROP_bot`: sends `/start 6727787768`, binds wallet, solves initial math challenge, and starts mining.
   - `@VictorsCompanybot`: sends `/start ref_A20AA96F18`, initializes WebApp, binds TON wallet (+100 VIC recruit bonus credited to Master).
   - `@vyrodrop_bot`: sends `/start ref_myFjrqqE4WN_`, activates WebApp, and connects TonConnect 2.0 wallet.
   - `@Kynex_miningbot`: sends `/start 6727787768`, activates WebApp, initializes Realtime DB starter profile, binds referral, and kicks off mining.
   - Sets `all_5_referrals_bound: true` and syncs the new account state across Upstash Redis and Cloudflare KV with zero manual interaction.

---

### 🚫 Complete Eradication of Scammer & Removed Bots & Channels (October 8–9, 2026)
Following operator directive and verified evidence of fraudulent schemes or obsolescence, **15 bots and all their associated channels/groups were permanently purged from all fleet code routines, blacklisted, blocked, dialogs erased with revoke=True across all 18 accounts, and all related channels/groups abandoned**:

1. **Stones Miners** (`@stonesminers_bot` / `@stoneswithestand_bot` / channels: `@stoneswithestand`): Purged permanently per operator directive; all token extraction, routine farming, captcha solver scripts/templates (`stones_captcha_solver.py`, `stones_captcha_templates.json`, `batch_stones_withdraw.py`), and whitelist channels removed.
2. **AI Lab Robot** (`@AiLab_robot` / channels: `@ailabrobotnews`): Purged permanently per operator directive; all token extraction, routine farming, and whitelist channels removed.
3. **UltraWallet** (`@UltrawalletTrade_Bot` / channels: `@ultrawalletofficial`, `@ultrawallet`): Purged permanently per operator directive; Firebase and task loops eradicated.
4. **FINVORA Web3** (`@FINVORAWeb3bot` / channels: `@finvoraweb3`): Purged permanently per operator directive; Railway WebApp and bonus routines deleted.
5. **Ainovum AI** (`@ainovum_bot` / channels: `@novum_en`, `@ainovum_channel`): Fraudulent non-paying backend with fake yield claims.
6. **Tensor Mining Robot** (`@tensormining_bot`, `TensorMiningRobot` / channel: `https://t.me/TensorCoinNews`): Unbacked fake ORCA token, sybil baiting.
7. **Ton Trader AI** (`@TonTraderAIBot`, `@tontrader_bot` / channels: `@tontraderai_official`, `@tontraderai_group`): Fake algorithmic yield simulation.
8. **TAC Airdrop** (`@tacairdrop_bot` / channels: `@tacairdrop`, `@tacairdrop_official`, `@tac_airdrop`): Fake mining contract, deceptive advertising.
9. **USDT QUAD** (`@usdtquadbot` / channel: `@usdtquad_channel`): Fraudulent cloud hashrate simulation, fake investment scheme.
10. **Apex Mining** (`@ApxMinerBot`, `@apexminer_bot` / channels: `@ApexMiner_Official`, `@ApexMinerGroup`): Unbacked token, suspicious anti-sybil bait.
11. **Ominix AI** (`@OminixAiBot`): Phishing & credential harvester (previously reported to Telegram Anti-Scam).
12. **ART Airdrop** (`@ART_AIRDROP_BOT`, `@artairdrop_bot` / channels: `@ART_AIRDROP`, `@artairdrop`): Fake yield simulation with artificial paywalls.
13. **TRX Power Mining** (`@trxpowermining_bot` / channels: `@trxpowerminingOfficial`, `@TRX_WORLD_WORK`, `@trxpowermining`): Unregulated fake cloud hashing Ponzi.
14. **Bitcoin Cloud Miners** (`@BitcoinCloudMinersBot`, `@Bitcoin_Cloud_Mining_bot` / channels: private links): Fake cloud mining tap bot.
15. **TurboGram V1** (`@TurboGramV1_bot` / channels: `@TurboGramAnnouncements`, `@TurboGramPayment`): Permanently purged and blacklisted, dialog history revoked and erased across all 18 accounts.

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
   - All 5 legitimate bots farm strictly via high-performance REST APIs. Token extraction is decoupled and handled exclusively by `/collect-tokens` in dedicated background batches.
4. **Empirical Fleet Results (Live October 10, 2026)**:
   - **Farmed Accounts**: **18 / 18 (100% Success)**.
   - **Farmed Bots per Account**: **5/5 legitimate bots active per account**.
   - **Total Active Bot Actions**: Complete coverage across all 18 accounts in under 30 seconds.

---

## ⚡ 6.2 Dual-Type Bot Architecture, Channel Engine & Dialog Purge Protocol (October 10, 2026)

### 1. The Dual-Type Bot & Channel Architecture
The fleet's 5 active high-conviction legitimate bots and channels are fundamentally divided into two technical architectures:

#### Type A: WebApp Mini-Apps / REST Bots (5 Genuine Bots)
- **Bots Included**: MRG Miner (`@mrg_miner_bot` / `@mrgminerbot`), ATF Miner (`@atf_miner_bot` / `@ATF_AIRDROP_bot`), Victor's Company (`@VictorsCompanybot`), VyroDrop (`@vyrodrop_bot`), Kynex Network (`@Kynex_miningbot`).
- **Mechanism**:
  - Authenticated via Telegram WebApp `initData` (HMAC SHA-256 query string signed by Telegram bot tokens) or Bearer JWT tokens.
  - Executed 100% via asynchronous HTTP REST calls with zero MTProto connection overhead.
  - Multi-account parallelized via `asyncio.Semaphore(3)` with per-bot rate-limiting and exponential backoff.
  - Pure cloud execution across Render Standby Node 2 and Cloudflare Workers 5-node mesh.

#### Type B: MTProto Dialog Purge, Token Collector & Sponsor Channel Sentinel Engine
- **Core Operations**:
  1. **Strict 1-Time Userbot Account Sanitation Protocol**:
     - *Operator Directive*: Sanitation (blocking discontinued bots, deleting conversation histories with `revoke=True`, and leaving discontinued channels) must execute **EXACTLY ONCE** per account, never repeated in routine farming cycles.
     - *Implementation*: Guarded by `acc.get("dead_bots_purged_v2")` and Upstash Redis key `fleet:purged_v2:<uid> = 1`. Once processed, subsequent cycles permanently skip the intensive dialog deletion flow, preventing Telegram API FloodWait penalties.
     - *Purged Bot Targets*: `@stoneswithestand_bot`, `@AiLab_robot`, `@UltrawalletTrade_Bot`, `@FINVORAWeb3bot`, `@TurboGramV1_bot`, `@trxpowermining_bot`, and all legacy scammers.
     - *Purged Channel Targets*: `stoneswithestand`, `ailabrobotnews`, `ultrawalletofficial`, `ultrawallet`, `finvoraweb3`, `TurboGramAnnouncements`, `trxpowerminingofficial`, etc.
  2. **Automated Sponsor Channel & Community Subscription Engine**:
     - Automatically joins and verifies all legitimate sponsor channels:
       `mrgminer`, `mrgfun`, `VictorsCompany`, `vyrodrop`, `atfminers`.
     - **Unblock Sentinel**: Automatically unblocks the 5 legitimate fleet bots across all accounts.
     - **Mute Sentinel**: Automatically mutes notifications across all channels, supergroups, and bots (`UpdateNotifySettingsRequest`) to ensure 0 notification noise.
     - **Telegram 500-Channel Cap Guard**: Audits total dialogs and prunes non-essential spam if dialog count exceeds 400.
     - **Cloud Endpoints**: `POST/GET /api/channels/sync-and-verify`, `POST/GET /api/cleanup-purged-bots-once`, and `GET /api/channels/status` on Render Standby Node 2.

### 2. Elimination of Fake / Dummy Farming Reporting
- **The Problem**: Previous iterations had legacy fallbacks where missing tokens or failed API calls returned `farmed` or `ok` to prevent UI pipeline breaks, masking genuine token expirations or auth errors.
- **The Fix**:
  - Every bot routine now validates tokens strictly and executes genuine API calls:
    * `_farm_stones`: Claims mining pool (`/api/claim`), starts miner (`/api/mining/start`), completes daily check-in, minigame, and boost, returning exact balance and level stats.
    * `_farm_mrg`: Accurately parses `/api/user/claim-mining` response, verifies cryptographic TON Connect 2.0 wallet ownership, auto-unlocks levels based on `manualUnlockedLevel`, and reports real claim status.
    * `_farm_atf`: Solves arithmetic math captcha dynamically, activates speed boost, claims referral yield and team wallet, and cycles cooldown tasks.
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
  - **🌐 Webshare Rotating Proxy Mesh**: Authenticates via Webshare API (`WEBSHARE_KEY_1`: `1r347t4h8dwfkpoa4ifmmyajvmu3oxyn2guzs5k0`) to bypass Cloudflare 503 WAF blocks on Microsoft Azure runner datacenter IPs.
  - **🛡️ Anti-Tamper & Native Initialization**: Avoids tampering with `window.turnstile` using custom getters/setters (which triggered Cloudflare's client-side anti-tamper detection). Uses Playwright native request/response interceptors (`page.on('response')`, `page.on('request')`) and DOM polling (`window.turnstile.getResponse()`) to safely extract tokens.
  - **MRG Miner**: Solves SiteKey `0x4AAAAAAFI-XXL7bFNbLU_J` on `app.mrgtoken.xyz`, refreshes `humanVerifiedUntil`, and claims mining rewards.
  - **Victor's Company**: Solves SiteKey `0x4AAAAAAFD0KRgPRFVwDvgn` on `app.victors.company` using Android Chrome mobile stealth context (`viewport: 430x932`). Fixes the "only runs inside Telegram / mobile" lockout by strictly URL-encoding `v_init` into the URL hash (`#tgWebAppData={encoded}&tgWebAppPlatform=android&tgWebAppVersion=8.0...`), pre-populating `sessionStorage.initParams`, and establishing property getters on `window.Telegram.WebApp` to prevent script overwrite. Filters out expired sessions via rapid 0.2s pre-flight probe (`POST /api/auth/login` expecting `403 HUMAN_REQUIRED`). Features Cloud Virtual Phone streaming via `noVNC` over Cloudflare Tunnel (`cloudflared`) and automated checkbox locator auto-clicking. Completes `POST /api/auth/login` with `turnstileToken` and `startParam: ref_A20AA96F18`, retrieves `humanPass`, and saves it to Upstash Redis (`victors:pass:{uid}`). Executes the full recruitment qualification pipeline: requests challenge nonce from `/api/wallet/proof-payload`, cryptographically signs TonConnect 2.0 binary proof (`ton-proof-item-v2` with domain `app.victors.company`) using account's dedicated TON Ed25519 key, links wallet (`POST /api/wallet/connect` with `{address, proof, stateInit, publicKey}` achieving `walletOwned: true`), completes onboarding tutorial (`/api/me/tutorial`), claims daily streak (`/api/checkin`), claims free social tasks (+15 VIC), claims mining yields (`/api/mining/claim`), and sweeps Master referral hiring bonuses (+100 V per recruit) and commissions.
  - **VyroDrop**: Executes 2-step challenge protocol: navigates directly to `/profile/wallet`, queries `POST https://vyro.run.place/api/wallet/challenge` for dynamic server `cdata`, renders SiteKey `0x4AAAAAAFMSnxZaI2W86NOg` (`action: wallet_onboarding`, exact camelCase `cData: e.cdata`), clicks Turnstile iframe, retrieves `turnstileToken`, fetches nonce, signs TonConnect 2.0 proof with account's private key, connects wallet (`/api/wallet/connect`), starts mining (`/api/mining/start`), and unlocks Master recruitment rewards (`/api/referrals/claim`).
  - **💼 Cloud-Resilient Wallets**: Both TON and EVM wallets are synced to Upstash Redis (`fleet:wallets:ton`, `fleet:wallets:evm`), ensuring Render Standby Nodes and GitHub Actions have instant access without depending on local disk files.
  - **Zero Phone Load**: 100% cloud execution running every 3 hours (`.github/workflows/mrg_turnstile_solver.yml`). 0 local processes on Samsung Galaxy A30.

### 3. Strict Master Account Self-Referral Immunity
- Rejection was prevented across `refresh_cloud_tokens.py`, `render_standby_app.py`, and `render_app_latest.py`:
  - When `acc_uid == REPORT_CHAT_ID` (`6727787768`), bots receive `start_param=None` instead of their own referral codes.
  - Workers (Accounts 2–18) continue to submit master referral codes (`VICTORS_REF: ref_A20AA96F18`, `VYRO_REF: ref_myFjrqqE4WN_`).

---

## ⛏️ 6.4 Victor's Company Deep Mine Arcade Minigame Engine & Mathematical Solver (October 9, 2026)

### 1. Reverse-Engineered Arcade Protocol (`/api/arcade/mine/*`)
- **Grid Architecture**: 9 columns x 40 rows (`width: 9`, `depth: 40`, total 360 blocks).
- **Gear Costs & Stats**:
  - `shovel`: Cost 25 VIC, Power 1, Energy 25, Hearts 3.
  - `pickaxe`: Cost 44 VIC, Power 2, Energy 30, Hearts 3.
  - `drill`: Cost 55 VIC, Power 3, Energy 32, Hearts 3.
- **Safe Row Discovery (`Ue.safeRows = 2`)**:
  - Rows `y = 0` and `y = 1` have strictly ZERO hazards (`hazard = 0`). No rockfall, no gas, no lava.
  - Row `y = 0` is reachable directly from the surface; Row `y = 1` is reachable once the block directly above (`x, 0`) is opened.
- **Block Costs & Loot Hints**:
  - Soft dirt costs 1 energy; boulders cost 2 energy.
  - The server returns bitmask `hint`: bit 0 (`hint & 1`) indicates loot sparkle (+1.1 to +4.5 VIC).
- **Payout & Refund Mechanics**:
  - `bagCap = 1.15` (max 28.75 VIC bag for shovel), `refundRate = 0.9` (90% unused energy refunded).
  - Payout on completion: `paid = bag + refund`. If player busts (`hearts <= 0`), server wipes 100% of bag and refund (`bustKeep = 0`).
  - Cash-out (`POST /api/arcade/mine/end`) guarantees 100% bag retention + 90% energy refund credited directly to `inAppBalance`.

### 2. Autonomous Safe Solver Implementation (`victors_arcade_solver.py`)
- Digs only reachable blocks in safe rows (0 and 1), prioritizing loot sparkle soft dirt (1 energy) over boulders.
- Handles server auto-conclusion when energy reaches 0 (returning `result` in `/api/arcade/mine/dig`), or calls `/api/arcade/mine/end` when safe rows are exhausted or bag reaches cap (~28.5 VIC).
- **Live Production Results**:
  - Verified on Nancy (`8881914294`): completed 14 digs, collected 18.9 VIC in loot, cashed out with +3.70 VIC NET PROFIT (balance jumped from 40.23 to 43.93 VIC).
  - Verified on Arif (`8826375659`): completed 18 digs, collected 15.4 VIC in loot with zero damage taken.
- **Fleet Task Claim Breakthrough**:
  - All 16 accounts joined `@victors_company`, `@VICWithdrawals`, and `@TheBoss_Victor` via cloud MTProto refresher (GitHub Actions Run `37933864463`).
  - Claimed all 4 sponsor tasks across all 11 authenticated sub-accounts, elevating balances from ~20.15 to ~40.25 VIC (11/11 accounts qualified for Deep Mine).
- **Cloud Farming Integration**: Integrated into `render_app_latest.py`, `render_standby_app.py`, and `victors_sb_solver.py` for continuous 24/7 cloud execution (Zero Phone Load, Rule 4).

---

## 🛡️ 6.5 Free-Tier Quota Engineering & Infrastructure Safeguards (October 9, 2026)

To permanently resolve resource exhaustion across free cloud tiers without paying recurring fees or triggering rate-limit lockouts, the architecture enforces strict mathematical quotas:

### 1. GitHub Actions Minutes Budget (<1,410 min/mo out of 2,000 min/mo Free Quota)
- **Problem**: Default workflows previously ran on aggressive 3-hour or 6-hour crons, consuming ~4,860 minutes/month and exhausting the free 2,000-minute monthly limit.
- **Resolution**: Re-engineered workflow schedules in `.github/workflows/`:
  * `mrg_turnstile_solver.yml`: Reduced from `15 */3 * * *` to `15 */12 * * *` (~600 min/mo).
  * `victors_sb_solver.yml`: Reduced from `30 */3 * * *` to `30 */12 * * *` (~360 min/mo).
  * `cloud_token_refresher.yml`: `0 */12 * * *` (~180 min/mo).
  * `fleet_sentinel.yml`: `0 */12 * * *` (~120 min/mo).
  * `cloud_sweeper.yml`: Reduced from `0 */6 * * *` to daily `0 18 * * *` (~150 min/mo).
  * `victors_cloud_phone_tunnel.yml`: Strict `workflow_dispatch` on-demand execution (0 scheduled minutes).
- **Total Consumption**: **~1,410 minutes/month** (70.5% of free quota, preserving 590 cushion minutes for manual runs).

### 2. Cloudflare KV Write Protection (<36 writes/day out of 1,000 writes/day Free Quota)
- **Problem**: `refresh_cloud_tokens.py` formerly looped over all 5 Cloudflare Worker endpoints in parallel, writing tokens to all nodes on every sync (90 writes per run), rapidly burning the 1,000/day free limit.
- **Resolution**: Implemented single-node primary write with automatic failover break. As soon as the primary Cloudflare Worker confirms KV write (`status in (200, 201)`), the loop breaks immediately.
- **Total Consumption**: **~36 writes/day** (<4% of the 1,000 daily free limit).

### 3. Upstash Redis Command Optimization (<1,200 commands/day out of 10,000/day Free Quota)
- **Problem**: Frequent hourly queries for Turnstile passes (`mrg:pass:{uid}`, `victors:pass:{uid}`) and individual N+1 GET requests for `account:*` and `fleet:tokens:*` threatened the 10,000 commands/day free cap.
- **Resolution**:
  * **In-Memory TTL Cache (`UPSTASH_PASS_CACHE`)**: Added a 30-minute in-memory cache for security passes in `render_app_latest.py` and `render_standby_app.py`, eliminating duplicate Upstash queries during farming cycles.
  * **Batched REST Pipeline (`/pipeline`)**: Replaced hourly N+1 GET loops for accounts and fleet tokens with single atomic `/pipeline` requests (`[["get", k] for k in keys]`).
- **Total Consumption**: Reduced from >3,500 commands/day to **<1,200 commands/day** (12% of the 10,000 daily free quota).

### 4. Render Multi-Account Standby Mesh (2,250 Total Free Hours/Month)
- **Problem**: Render free services provide 750 free hours/month per account (sufficient for exactly 1 continuously running service).
- **Resolution**: Partitioned standby nodes across distinct Render accounts:
  * Node 1 (Singapore): Account 1 (`RENDER_API_KEY_1`, 750h quota).
  * Node 2 (Frankfurt): Koram Account (`RENDER_API_KEY_2`, 750h quota).
  * Node 3 (Oregon): Koram Account (`RENDER_API_KEY_3`, 750h quota).
- **Result**: Complete redundancy with zero risk of mid-month shutdown due to exhausted hours.

---

## 🧹 6.6 Autonomous Multi-Tier Sanitation & Maintenance Engine (October 9, 2026)

To prevent resource leakages, unbounded database list growth, and local disk ballooning on ephemeral and mobile environments, the fleet runs an autonomous multi-tier clean-up system ([`clean_up_system.py`](file:///root/workspace/clean_up_system.py)):

### 1. Tier 1: Local Disk & Ephemeral Workspace Sanitation
- **Bytecode Pruning**: Recursively removes all `__pycache__`, `*.pyc`, and `.pytest_cache` while skipping large vendor directories (`.git`, `.gemini`, `node_modules`).
- **Backup Retention Policy**: Retains only the 2 most recent `my_agy_ai_backup_*.zip` archives locally (all archives are durably mirrored to the Telegram vault `@myagyai`), pruning older archives to conserve disk space.
- **Log Rotation**: Automatically rotates and truncates log files $>2$ MB, keeping the most recent 1,500 lines.
- **Temporary Scrap Cleaning**: Purges headless browser scraps (`/tmp/*chrome*`, `/tmp/*xvfb*`, `/tmp/*selenium*`).

### 2. Tier 2: Process Sanitation & Mobile Resource Guardrail (Rule 4)
- Enforces the **Zero Phone Load Directive** on the Samsung Galaxy A30:
  - Scans active OS processes.
  - Automatically terminates any rogue background bot or scraper processes (`render_app`, `mrg_turnstile_solver`, `victors_sb_solver`, `batch_atf_miner`, `bot_supervisor.sh`).
  - Guarantees 0 CPU/RAM overhead on the phone for Antigravity AI pair programming.

### 3. Tier 3: Upstash Redis Serverless Quota & Storage Hygiene
- **Transaction List Capping**: Automatically executes `LTRIM fleet:payouts 0 99` to cap the payout history to the 100 most recent items, preventing unbounded Redis memory growth.
- **Stale Pass Pruning**: Audits security pass keys (`*:pass:*`) and purges entries older than 48 hours via atomic `/pipeline` batching.

### 4. Tier 4: GitHub Actions CI/CD History Pruning
- Queries GitHub Actions runs and automatically deletes completed/canceled workflow runs older than 7 days via the GitHub REST API (`DELETE /repos/{repo}/actions/runs/{run_id}`).
- Keeps repository run history lean and protects organization storage limits.

### 5. Automated Execution & Operator Controls
- **Automated Sentinel**: Integrated into `.github/workflows/fleet_sentinel.yml` running every 12 hours.
- **Telegram Serverless Cockpit**: Integrated into `@My_Router_AI_bot` (`/cleanup` command and inline clean button).
- **Manual CLI Execution**: `python3 clean_up_system.py [--dry-run|--disk-only|--cloud-only|--proc-only]`.

---

## 🛠️ 7. Operator & AI Cheat Sheet

Here are the exact commands to run for everyday operations:

### 1. Check Fleet Farming Status
Query the Cloudflare Edge Gateway for real-time status across all 18 accounts:
```bash
curl -s https://restore-agy.aaaai2.workers.dev/api/farm/status | jq .
```

### 2. Trigger Immediate Cloud Farm
Trigger an immediate harvest across all 5 legitimate bots on Cloudflare Workers:
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

### 9. Render-First Architecture & Free-Tier GitHub Actions Quota Protocol
To strictly preserve GitHub Actions free-tier quotas (2,000 minutes/month cap for free users), all continuous 24/7 background workloads are offloaded to **Render Standby Mesh** and **Cron-Job.org** (100% free, 0 minute meter):
- **Continuous 24/7 Multi-Bot Farming**: Handled 100% by Render Node 2 (Frankfurt) and Node 3 (Oregon) via POST `/api/farm/cloud-all` triggered every 15 minutes by Cron-Job.org (`8614058` & `8614059`). Consumes **0** GitHub Actions minutes.
- **Continuous MTProto Token Harvesting**: Handled 100% by Render Node 2 (Frankfurt) via POST `/collect-tokens` triggered every 4 hours by Cron-Job.org (`8614259`). Consumes **0** GitHub Actions minutes.
- **Conserved GitHub Actions Scheduling**:
  * `mrg_turnstile_solver.yml`: Reduced to **twice daily** (`0 3,15 * * *` = ~300 min/mo total).
  * `cloud_token_refresher.yml`: Reduced to **once daily** (`0 4 * * *` = ~90 min/mo total). Auto-dispatch removed.
  * `fleet_sentinel.yml`: Reduced to **once daily** (`0 8 * * *` = ~60 min/mo total).
  * `victors_sb_solver.yml`: Schedule disabled (workflow_dispatch only).
  * **Total Monthly GitHub Actions Consumption**: **~450 minutes/month** (only ~22% of the free 2,000-minute quota, leaving >75% buffer).
- **Killercoda Decommissioned**: Fragile 60-minute Killercoda sessions removed in favor of permanent, stable Render and Cloudflare infrastructure.

---

## 🔐 8. Distributed Cloud Secrets Vault & Automated IMAP Engine

To ensure zero-trust off-machine durability and seamless authentication automation:

### 1. Distributed Secret Replicas Across 4 Cloud Tiers
* **Cloudflare D1 SQL**: Table `fleet_vault_secrets` on Node 1 (`c29cc72d-3813-4aa2-859a-8cdfd929825c`). Stores `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `FLEET_2FA_PASSWORD`, `FLEET_2FA_FALLBACK`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, and `RECOVERY_EMAIL`.
* **Supabase Managed Postgres**: Record `id='system_fleet_vault'` in `fleet_accounts` table. Replicated across APAC edge with instant REST accessibility.
* **Render Environment Mesh**: Synchronized via Render API (`PUT /v1/services/{id}/env-vars`) across all 3 active services (`my-agy-fleet-standby`, `my-agy-fleet-standby-node2`, `my-agy-fleet-standby-node3`).
* **Local Master `.env`**: Complete local reference for Termux pair programming tools.

### 2. Google App Password & IMAP Verification Engine (`auto_bind_login_emails.py`)
* Google App Password (`kuqevwndvabevefx` for `aaa.support.a@gmail.com`) allows hands-free MTProto verification code extraction via Python standard `imaplib`.
* **Login Email vs. 2FA Recovery Email**:
  - **2FA Recovery Email**: Set via `account.UpdatePasswordSettingsRequest`. 100% active on all 10 purchased accounts with password `Arif216@` and recovery `aaa.support.a@gmail.com`.
  - **Login Email (OTP)**: Bound via `account.SendVerifyEmailCodeRequest` + `account.VerifyEmailRequest`. Account #14 and #16 bound to `aaa.support.a+14@gmail.com` and `aaa.support.a+16@gmail.com`.

### 3. Telegram Admin Bot Relogin & OTP Hub (`@myagyai`)
To facilitate seamless login on new devices (e.g., after phone resets) without SIM cards or SMS:
* **Endpoint (`GET /api/fleet/otp/{target}`)**: Hosted on Render Standby Node 2 & Node 3.
  - Queries Telegram official service notification messages (`peer=777000`: `Login code: XXXXX`) directly from active cloud MTProto sessions.
  - Falls back to Gmail IMAP inbox extraction (`aaa.support.a@gmail.com`) if Telegram sends the code via email.
  - Returns account name, phone number, formatted copyable `code`, 2FA password (`Arif216@`), source, and age in seconds.
* **Telegram Admin Bot UI**:
  - `🔑 OTP & Relogin` button in persistent reply keyboard and inline keyboards.
  - Interactive Dynamic Grid Picker (`btn_otp_menu`) with real-time badges: `👑` (Master Host), `🟢` (Active), `🔴` (Needs Re-link).
  - 1-by-1 Wizard (`btn_otp_get_1` through `btn_otp_get_18`) with *🔄 Fetch Code Now*, *⚡ 1-Tap Re-link*, and *⏭️ Next / Skip*.
  - Text commands `/otp <number>`, `/recover`, `/sessions`, `/audit`, and `/acc <id>`.
  - 1-tap copyable Markdown `<code>` blocks for phone, login code, and 2FA password.

### 4. Dynamic Session Health Synchronization & Active-Passive Edge Failback
* **Dynamic Health State Machine**: Managed dynamically via Upstash Redis sets (`fleet:healthy_sessions` and `fleet:revoked_sessions`) with 60s in-memory edge caching.
* **1-Tap Re-link Auto-Promotion (`onAccountRelinkSuccess`)**: When an account session is re-linked via MTProto, its index is dynamically promoted from `revoked` to `healthy` across all edge nodes, immediately updating the OTP grid, fleet roster, and inspection screens.
* **Resilient Multi-Layer Account Removal**: Deletions are mirrored across module RAM cache (`memDeletedAccounts`), Upstash Redis (`fleet:deleted_accounts`), and Cloudflare KV (`fleet_deleted_accounts`), ensuring that hitting Cloudflare KV daily free quotas never causes removed accounts to reappear or screens to stall.
* **Render-to-Edge Failback Routing**: All outbound calls from Render nodes to Cloudflare Workers query Node 1 (`aaaai2.workers.dev`) first, immediately breaking upon receiving a 200 OK response. Standby nodes (Nodes 2-5) produce 0 scheduled KV writes and maintain cold zero-cost standby posture.

---

## 🔒 9. Living Changelog Protocol

Whenever you perform work in this repository:
1. **Never delete existing working features** without explicit user request or confirmed scam decommissioning.
2. **Commit with clean conventional commits**: `git commit -m "feat/fix/perf: description"`.
3. **Keep `CHANGELOG.md` updated** with every major addition, modification, and bug fix.
4. **Keep `PROJECT_BIBLE.md` updated** whenever a bot is added, an endpoint changes, or a new cloud service is provisioned.
5. **Push git checkpoints** to `AAA0002/ATL` (`main`) and create a fresh backup in `@myagyai`.

---

## 💼 10. Web3 Multi-Chain Non-Custodial Real Wallet Architecture & Zero-Emoji Institutional UI Standards

### 1. Real Non-Custodial Multi-Chain Wallet Engine
* **Official Credentials Binding**: Strictly bound to the official 18 accounts documented in `FLEET_MULTICHAIN_WALLETS_DASHBOARD.md` (assembled into `public_admin/fleet_wallets_data.json`). Node #01 is bound to Binance Main Exchange Vault; Node #10 is bound to Binance Web3 Wallet 2 (AAA); Nodes #02-#09 and #11-#18 are bound to dedicated self-custody suites.
* **Static Fleet Registry Precedence (`fleet_wallet_provisioner.py`)**:
  - `FLEET_STATIC_REGISTRY` loaded directly from `fleet_wallets_data.json`.
  - When accounts relink or onboard (e.g. Node 5 Nathan Miller 5, `+14302084365`), user ID and phone number take precedence over modal request parameters (`req_index`).
  - Pre-configured accounts (Nodes 1-18) **NEVER** have random synthetic keys generated; their permanent authentic keys and node indices are strictly preserved.
* **16-Account Fleet Seed Manager & Quick Mobile Importer Wizard (`admin.html`)**:
  - Eliminates the burden of typing 384 words (16 accounts × 24 words) on a mobile phone keyboard.
  - **18-Account Quick-Jump Pills**: Horizontal scroll bar with 1-tap selectors for all 18 accounts (color-coded amber for Binance Vaults #1 & #10, and cyan for the 16 self-custody accounts).
  - **Dedicated Binance Vault Cards**: Node #1 displays Binance Central Reserve Vault with mandatory memo (`103525143`); Node #10 displays Binance Web3 MPC Vault.
  - Numbered 3-column 24-word grid with 1-tap "Copy 24 Words" (clean space-separated) and "Numbered" export.
  - 1-Tap "Open in Tonkeeper" deeplink and 1-Tap "Copy EVM Key".
  - Bulk Export Utilities: 1-Click "Copy 16 Seeds", 1-Click "Download TXT Backup", 1-Click "Download JSON Vault".
* **Fleet Account Detail Modal Wallet & Seed Shortcut (`admin.html`)**:
  - Tapping any account card in the Fleet list instantly shows its TON and BSC addresses, custody type, and provides a direct `[ 🔑 View 24-Word Seed in Seed Manager ]` button.
* **Telegram Bot `/wallet <1-18>` Dynamic Inspection Engine (`deploy_both_cf_workers.py`)**:
  - `/wallets`: Returns executive summary of both Binance vaults and the 16 self-custody accounts.
  - `/wallet <1-18>` (e.g. `/wallet 5`): Immediately delivers that account's multi-chain addresses, EVM key in `<code>`, and for worker accounts, the 24-word recovery phrase in `<pre>` for 1-tap copying.
* **Telegram Alert Secret Phrase & Key Delivery (`render_standby_app.py`)**:
  - `notify_admin_new_account_onboarded(acc_entry, is_existing)` delivers the complete 24-word recovery phrase formatted in `<pre>` for 1-tap copying on mobile, plus the EVM private key.
  - Confirms automatic archival to `FLEET_WALLETS_SECRETS_MASTER_VAULT.txt`.
* **Zero Fake Mock Tokens & Live Multi-Chain RPC Queries**:
  - Purged all fake token mock balances (`notBal`, `dogsBal`, `mrgBal`, `usdtBscBal`, `usdtTronBal`, `solBal`).
  - Browser directly queries 5 public RPCs:
    * TON Center RPC (`https://toncenter.com/api/v2/getAddressInformation?address={addr}`)
    * BSC JSON-RPC (`https://bsc-dataseed.binance.org` -> `eth_getBalance`)
    * TronGrid API (`https://api.trongrid.io/v1/accounts/{addr}`)
    * Solana RPC (`https://api.mainnet-beta.solana.com` -> `getBalance`)
    * Mempool Space API (`https://mempool.space/api/address/{addr}`)
    * Binance Live Price Tickers (`TONUSDT`, `BNBUSDT`, `BTCUSDT`, `TRXUSDT`, `SOLUSDT`)
* **1-Tap Tonkeeper Mobile Transaction Signing**:
  - Universal deeplink `https://app.tonkeeper.com/transfer/{addr}?amount={nanotons}&text={memo}` pre-fills recipient address, amount in nanotons, and transfer memo.
  - Tonkeeper opens directly on mobile, loads the active 24-word account, and prompts the user to sign with one tap. Zero server custody.

### 2. Zero-Emoji Institutional UI Standards
* **Institutional Vector SVG Standards**: 100% elimination of all emoji pictographs across Admin Console (`public_admin/admin.html`) and Standalone Login Portal (`public_admin/login.html`).
* **SVG Vector Assets**: High-precision vector icons for TON, BSC, TRON, Solana, Bitcoin, USDT, USDC, ATF, MRG, NOT, DOGS, lock, key, badgeCheck, and server telemetry.
* **High-Contrast Dark Theme & Responsive Architecture**: Built with Tailwind CSS and React 18, optimized for mobile devices (Samsung Galaxy A30) and desktop screens.

### 3. Dedicated Admin Authentication & Standalone Login Portal
* **Edge Password Hash Fix**: Corrected variable definition order in `deploy_both_cf_workers.py` line 2473 (`hexHash` buffer computation before validation), resolving `hexHash is not defined` error.
* **Client-Side SHA-256 Fallback**: Integrated offline SHA-256 validation (`Arif-Abid` / `Arif216@` / master hash) directly into `AdminAuthGate`.
* **Multi-Cloud Dedicated Deployments**:
  - Primary Admin Console: `https://agy-aaa000.vercel.app/admin` & `https://aaa-free-ai.vercel.app/admin`
  - Standalone Login Portal: `https://agy-aaa000.vercel.app/login` & `https://aaa-free-ai.vercel.app/login`
  - Cloudflare Pages Mirrors: `https://aaa-admin-portal.pages.dev/admin` & `https://aaa-admin-portal.pages.dev/login`

### 4. AAA Telegram — Premium Mini App UI Design System (`public_admin/index.html`)
* **Product Mission**: Distinctive, polished commercial Telegram Mini App web product launched directly via Telegram bot for multi-account and MTProto session lifecycle management.
* **Aesthetic Standard**:
  - **Premium Light Theme**: Pure white surfaces (`#FFFFFF`), pale blue canvas (`#F4F8FC`), deep navy typography (`#0E1E38`), and Telegram-blue primary accents (`#2481CC`).
  - **100% Vector SVGs**: Zero emoji icons used in UI components.
  - **Mobile-First In-App Browser Optimization**: Uses `window.Telegram.WebApp` with header color `#F4F8FC`, background `#F4F8FC`, full viewport expansion, and synchronized native back button.
* **11-Screen Complete Specification & Advanced Features**:
  1. **Page 1 — Welcome**: Wordmark, abstract layered floating device graphic with radial glow, headline *"All your Telegram accounts. One place."*, *"Connect Telegram"* primary button, and privacy disclaimer.
  2. **Page 2 — Telegram Account Login**: Back control, step indicator, segmented control for **Phone Number** vs **QR Code** login modes, crisp SVG QR Code scan preview with step-by-step connection guide, country selector (`🇧🇩 Bangladesh +880`), phone input, validation messaging, and Terms/Privacy links.
  3. **Page 3 — Login Code**: Step 2 of 3, paper airplane verification icon, 6 individual auto-advancing OTP digit boxes with auto-paste support, live countdown timer (`04:32`), and resend link.
  4. **Page 4 — Two-Step Verification (2FA)**: Step 3 of 3, lock badge, password input with vector eye visibility toggle, and *"Forgot password?"* link.
  5. **Page 5 — Main Dashboard**: Header lockup (wordmark, avatar initials "AH", settings cog), greeting *"Good morning, Arif Hasan"*, overview card (Connected pill, 18 connected accounts, 6 active sessions), 3 quick-action cards (Accounts, Sessions, Settings), and Recent Activity feed.
  6. **Page 6 — My Accounts**: Top bar, *"+ Add Account"* CTA, live search input (filter by name, phone, or handle), quick filter tabs (All 18, Connected, Master Host), account cards with initials, masked phone number, connection status pill, and chevron. Preloaded with the complete 18-account production fleet roster.
  7. **Subpage — Account Details**: Large avatar header, account attributes list, *"Switch Account"*, and *"Remove Account"* with confirmation modal dialog.
  8. **Page 7 — Session Management (Sessions)**: Live search input (filter by device, platform, IP), status filter tabs (All, Active, Disconnected), device cards (Samsung SM-A305F, Chrome Windows, Linux Ubuntu, iPhone 15 Pro, Firefox Linux, Samsung Galaxy S23) with status pills and last active times.
  9. **Page 8 — Session Details**: Device status header, specifications card (Account name, Platform, App Version, Device Model, IP, Location, Authorization Time, Last Activity), and red *"Terminate Session"* CTA with confirmation modal.
  10. **Page 9 — Activity**: Category filter tabs (All, Logins, Sessions, Security), chronological event rows with vector icons, descriptions, and timestamps.
  11. **Page 10 — Settings**: Grouped list rows for Appearance (Light/Dark/System themes), Preferences (Language, Notifications), Security and Privacy (Security info, Session management, Privacy info, **1-Click JSON Session Vault Export**), and About (App version 1.0.0, Support, Terms).
  12. **Page 11 — Empty, Loading & Error Screens Modal**: Showcases all 8 production states (No accounts connected, No sessions available, Logging in spinner, Invalid verification code, Expired authorization, Network error, Account disconnected, Successful authorization).
* **Live Production URLs**:
  - `https://agy-aaa000.vercel.app/`
  - `https://aaa-free-ai.vercel.app/`

### 5. Admin Bot Redesign & De-duplication Protocol (`deploy_both_cf_workers.py`)
* **Bot Handle & Token**: `@myagyai` (`8858823950:AAEdX47g7as1xLYEudfRUHaVGUdNIaU_ku8`)
* **Live Edge Webhook**: `https://restore-agy.aaaai2.workers.dev/telegram-webhook` (Primary Gateway on Cloudflare Workers)
* **Single-Message Philosophy**:
  - Zero duplicate double-messages on `/start` or `/menu`. The bot replies with a single authoritative Markdown console.
  - Zero duplicate buttons between inline keyboard and persistent reply keyboard.
  - In-place message edits via `editMessageText` for all submenus (`btn_accounts`, `btn_session_audit`, `btn_otp_menu`, `btn_wallets`, `btn_mesh`).
  - Every submenu features a universal `[ 🔙 Back to Main Menu ]` button (`btn_back_main`) that reverts the message cleanly.
* **Direct WebApp Integration**:
  - Primary button: `📱 AAA Telegram App` (launches `https://agy-aaa000.vercel.app/`)
  - Secondary button: `👑 Fleet Console` (launches `https://agy-aaa000.vercel.app/admin`)
  - Dedicated `/app` command for instant 1-tap direct launch.
* **Scam Bot Elimination**:
  - Permanently purged all menu items, text prompts, and buttons for decommissioned scam bots (`Stones`, `AI Lab`, `UltraWallet`, `FINVORA`, `ART`, `Apex`, `BNB Galaxy`).
  - Bot and fleet strictly standardized on the **5 active legitimate bots**:
    1. **MRG Miner** (`@MRG_miner_bot`)
    2. **ATF Miner** (`@atf_miner_bot`)
    3. **Victor's Company** (`@VictorsCompanybot`)
    4. **VyroDrop** (`@vyrodrop_bot`)
    5. **Kynex Network** (`@Kynex_miningbot`)



