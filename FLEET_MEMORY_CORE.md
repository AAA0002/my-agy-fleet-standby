# 🧠 FLEET MEMORY CORE — AAA AUTO & MY AGY AI
> **MANDATORY PERSISTENT MEMORY ARCHIVE**
> *Created: October 2026 | Last Synced: 2026-10-23*
> **Every AI agent, developer, and automated process MUST read this document to understand system invariants, active account roster, wallet architecture, and operational protocols.**

---

## 1. 🛡️ Absolute Core Invariants & Safety Directives

### 1.1 Strict Account Immutability & Anti-Overwrite Protocol
- **Slots #1 to #18 are Permanently Reserved**: Accounts 1 through 18 are static, legitimate accounts. They must NEVER be overwritten, shifted, renumbered, or replaced by any new account.
- **New Account Indexing Rule**: Any brand-new account onboarded to the fleet MUST be assigned an index greater than 18 (e.g. Account #19, #20, #21...).
- **Strict Identity Matching (No Blind Index Hijacking)**:
  - An account is matched as an *existing account* ONLY if its Telegram `user_id` matches OR its clean `phone` number matches.
  - An account must **NEVER** be matched purely by index number when `user_id` or `phone` is provided. If `user_id` and `phone` do not match any existing record, it is strictly treated as a **100% Brand-New Account**.
- **Dynamic Fleet Merge**: Cloudflare Worker (`getFleetAccounts()`) merges the 18 static default accounts and automatically appends all dynamic accounts (19+) so the roster displays `Accounts Roster (N)` dynamically.

### 1.2 Zero Phone Load Directive (Samsung Galaxy A30)
- The phone is strictly for running the Antigravity pair-programming CLI.
- **ZERO bots, loops, or scrapers run locally**. 100% of MTProto sessions, farming loops, token refreshers, and wallet signers run in the cloud (Cloudflare Workers & Render Node 2).

### 1.3 Strict Separation of Bot Ecosystems, Channels & Dual Admin Dashboards ("Zero Ecosystem Mixing")
- **Independent Bot Ecosystems**:
  - **Admin Bot (`@myagyai`, ID `8858823950`)**: Exclusively reserved for system administrators. Controls executive fleet operations, 20 MTProto account onboarding/linking, cloud farm orchestration, sentinel monitoring, disaster recovery backups, and cloud node health. Handled via `ADMIN_BOT_TOKEN` / `REPORT_BOT_TOKEN`.
  - **User Bot (`@AAAPREMIUMAPPSbot`, ID `8167732110`)**: Exclusively dedicated to public end-users. Powers community multi-pool mining, points economy, daily check-ins, rewarded ads, Stars VIP access, and public onboarding. Handled via `USER_BOT_TOKEN`.
  - **Zero Contamination**: Admin commands (`/farm`, `/fleet`, `/acc`, `/restore`, QR/PIN MTProto logins) must NEVER be exposed to the User Bot; user flows must NEVER be mixed with admin operations.
- **Strict Channel Separation (Zero Cross-Posting / Zero Leakage)**:
  - **Admin Channels & Vaults (Private/Administrative)**:
    - 🛡️ Disaster Recovery Vault Channel: `@myagyai` (`-1004453515167`)
    - 💳 Payouts & Daily Ledger Channel: `-1004402765950`
    - 🏢 Fleet Internal Supergroup: `-1003973231307` (*AAA T Wallet Supergroup*)
    - *Policy*: Exclusively for system backups, encrypted disaster recovery archives, internal payout ledgers, and fleet telemetry. NEVER route or leak administrative data to user community channels.
  - **User Community Channels (Public/End-Users)**:
    - 📢 Official Announcements: `@AAAAutoMiner` (`-1003684868577`)
    - 💬 Community Mining Group: `@AAAAUTOMINING` (`-1004255751168`)
    - ⚡ Activity & Verification: `@AAA_ACTIVITY` (`-1004332544939`)
    - *Policy*: Exclusively for public announcements, user mining feeds, onboarding verification gates, and cross-channel community relays. NEVER send admin alerts, error traces, disaster recovery dumps, or account credentials to these channels.
- **Dual Independent Admin Dashboards (Never Conflate or Intermix)**:
  - **Executive Fleet Operations Console (`public_admin/admin.html` at `/admin`)**:
    - Dedicated strictly to **Admin Bot (`@myagyai`) & Fleet Operators**.
    - Displays real-time status of the 20 MTProto fleet accounts, 9 farming pools, multi-cloud nodes (Render Standby Node 2, Cloudflare Edge Mesh), Redis key inspect/flush, and automated disaster recovery triggers.
    - Does NOT manage public end-users, ad impressions, or public community points.
  - **User Bot Admin Console (`public_admin/user-admin.html` at `/user-admin`)**:
    - Dedicated strictly to **User Bot (`@AAAPREMIUMAPPSbot`) Community Management**.
    - Displays end-user community miners (`community_miners`), user points economy, daily check-in streaks, rewarded video ad impression metrics (`ad_impressions_log`), user account bindings, and Stars VIP subscriptions.
    - Does NOT expose private fleet MTProto sessions, private keys, wallet seeds, or executive fleet controls.
- **Database & State Namespace Isolation**:
  - Keep Redis/database keys cleanly separated: `fleet:*` is strictly for Admin Bot & Fleet operations; `user:*`, `points:*`, `community_miners`, and `ad_impressions_log` are strictly for User Bot.


---

## 2. 👥 Active Accounts Roster (23 Accounts)

| Index | Name | Username | Telegram ID | Phone | Custody Type | Primary Wallet | Status |
| :---: | :--- | :--- | :---: | :---: | :--- | :--- | :---: |
| **01** | **Arif Hossain (Master)** 👑 | `@Arif2743aaa` | `6727787768` | `+8801317342850` | Binance Main Exchange Vault | TON: `UQBPZiS...gwDT` | 🟢 Active |
| **02** | Koram Shah | `@Koram_Shah` | `7648254021` | `+8801790208077` | Isolated 24-Word Seed | TON: `UQC8xeC...pp-1` | 🟢 Active |
| **03** | Arif | `@Arif2743_a` | `8826375659` | `+8801575842094` | Isolated 24-Word Seed | TON: `UQAOfjJ...oPBD` | 🟢 Active |
| **04** | Nadim | `@nathan_miller7` | `8450010161` | `+14302084365` | Isolated 24-Word Seed | TON: `UQBrmX4...MOBQ` | 🟢 Active |
| **05** | Kaitlyn | `@kaitlyn_ross7` | `8782429452` | `+8801867539837` | Isolated 24-Word Seed | TON: `UQAid8o...jk9q` | 🟢 Active |
| **06** | Abid Hasan (1) | `@Abidhasan222` | `7734849205` | `+8801718056423` | Isolated 24-Word Seed | TON: `UQAtcq_...fVXU` | 🟢 Active |
| **07** | Abid Hasan (2) | `@None` | `8025472383` | `+8801797795624` | Isolated 24-Word Seed | TON: `UQCIPXA...LydV` | 🟢 Active |
| **08** | Naimur Rahman | `@naimur_rhmn7` | `8851426148` | `+8801727651288` | Isolated 24-Word Seed | TON: `UQDF-a-...cweI` | 🟢 Active |
| **09** | Tanvir Ahmed | `@tanvir_ahmed785` | `8203342513` | `+8801729892810` | Isolated 24-Word Seed | TON: `UQBeouW...5LKH` | 🟢 Active |
| **10** | MD Arif Hossain | `@aaamah222` | `8190649727` | `+8801571089931` | Isolated 24-Word Seed | TON: `UQBgy3I...VHrB` | 🟢 Active |
| **11** | Sanzida Shimu | `@SanzidaShimu` | `7487048946` | `+8801774578536` | Isolated 24-Word Seed | TON: `UQBOdyZ...BMQo` | 🟢 Active |
| **12** | Abid (3) | `@Abid_300` | `8741547543` | `+8801838268380` | Isolated 24-Word Seed | TON: `UQAy5w8...fDkN` | 🟢 Active |
| **13** | Rohan Sharma | `@rohan_sharma7` | `8727040932` | `+918930504750` | Isolated 24-Word Seed | TON: `UQCbqkS...UsLo` | 🟢 Active |
| **14** | Tasnim Farhana | `@tasnim_farhana7` | `7749125802` | `+8801906045479` | Isolated 24-Word Seed | TON: `UQBhpe9...kcaR` | 🟢 Active |
| **15** | Rashedul Islam | `@rashedul_islam7` | `7954290138` | `+8801304151082` | Isolated 24-Word Seed | TON: `UQANs0f...0gYH` | 🟢 Active |
| **16** | Kawsar Mahmud | `@kawsar_mahmud7` | `8841038141` | `+8801879273559` | Isolated 24-Word Seed | TON: `UQCDqle...dY5j` | 🟢 Active |
| **17** | Mehedi Hasan | `@mehedi_hasan783` | `8975442879` | `+8801839716506` | Isolated 24-Word Seed | TON: `UQBcHzN...49fL` | 🟢 Active |
| **18** | Adil H | `@AdilHassain` | `8937908003` | `+8801804723069` | Isolated 24-Word Seed | TON: `UQCrEZr...Aw8D` | 🟢 Active |
| **19** | Asaduzzaman Sarker | `@Asaduzzamansarkar` | `8609131528` | `+8801312863569` | Isolated 24-Word Seed | TON: `UQCdmqN...g0DE` | 🟢 Active |
| **20** | AAA201 | `@AAA201AAA` | `8669217201` | `+8801913962342` | Isolated 24-Word Seed | TON: `UQDH-Fr...n_jw` | 🟢 Active |
| **21** | AAA 22 | `@aaa022a` | `9272631973` | `+8801732100769` | Isolated 24-Word Seed | TON: `UQDNmNk...EHGJ` | 🟢 Active |
| **22** | Abid Hasan (4) | `@aaa023aa` | `9106746905` | `+8801788601627` | Isolated 24-Word Seed | TON: `UQAvTw1...akWI` | 🟢 Active |
| **23** | AAA 24 | `@aaa024a` | `8972499908` | `+8801794783852` | Isolated 24-Word Seed | TON: `UQDxJ5R...idIN` | 🟢 Active |

---

## 3. 💎 Multi-Chain Wallet Generation & Vault Storage

### 3.1 Wallet Generation Rules
1. **Existing Accounts (1-18)**: Use immutable pre-configured keys from `FLEET_STATIC_REGISTRY` / `public_admin/fleet_wallets_data.json`.
2. **Brand-New Accounts (19+)**: Generate a dedicated, isolated 5-chain wallet suite:
   - **TON (v4r2)**: Generated with 24 BIP-39 mnemonic words via `tonsdk`.
   - **EVM (BSC / Arbitrum / ETH)**: 256-bit ECDSA secp256k1 key with `0x` address.
   - **TRON (TRC-20 USDT / TRX)**: Base58Check address derived from EVM public key.
   - **Solana (SOL / SPL)**: Ed25519 keypair encoded in base58.
   - **Bitcoin (BTC)**: P2PKH / Taproot address derived from private key.

### 3.2 Vault Storage Locations
Every generated wallet and its private keys are archived in:
1. `FLEET_WALLETS_SECRETS_MASTER_VAULT.txt` (Local text vault for disaster recovery)
2. `FLEET_ACCOUNTS_AND_WALLETS_DIRECTORY.md` (Human-readable Markdown directory)
3. `public_admin/fleet_wallets_data.json` & `fleet_wallets_data.json` (Structured JSON registry)
4. `fleet_ton_wallets.json`, `fleet_evm_wallets.json`, etc.
5. Upstash Redis: `fleet:wallets_vault:{uid}` and `fleet:wallets_vault:index_{idx}`
6. Cloudflare KV & Supabase Postgres
7. **Telegram Disaster Alert**: Sent directly to Commander Arif (`6727787768`) via `REPORT_BOT_TOKEN` upon onboarding.

---

## 4. 🤖 9 Mining Pools & Automated Wallet Binding

When a new account connects, the system immediately binds its dedicated wallets and unlocks mining:

1. **ATF Miner (`@AAAPREMIUMAPPSbot`)**:
   - TON wallet synced via `sync_wallet` API.
   - Math challenge automatically solved (`solve_atf_math`).
   - Speed boost activated and 8 starter tasks claimed.
2. **MRG Miner (`@mrgminerbot`)**:
   - TON wallet bound via `/api/user/connect-wallet`.
   - Initial claim executed and peak level unlocked.
3. **Victor's Company (`@victorscompanybot`)**:
   - TON wallet connected via `/api/wallet/connect`.
   - Task `connect-wallet` claimed.
   - **Level 1 Miner Unlocked** (`/api/levels/unlock`) so mining runs 24/7 without `home.noJob` error.
4. **VyroDrop (`@vyrodropbot`)**:
   - TonConnect challenge requested and signed via Ed25519 TON private key.
   - `/api/mining/start` executed with unique idempotency key.
5. **Astra Airdrop (`@AstraAirdrop_bot`)**:
   - TON wallet synced via Supabase RPC `astra_sync_wallet`.
6. **PepeGram (`@PepeGramMiningBot`)**:
   - Auto-verified and active in cloud farm loop.
7. **AdxEarn AI (`@adxearnbot`)**:
   - 24/7 autonomous daily claims running in cloud loop.
8. **Diggo Miner (`@DiggoMiningBot`)**:
   - 30-day JWT cached and mining cycles active.
9. **Kynex Network (`@kynexnetworkbot`)**:
   - Session data bound and auto-farm active.

---

## 5. 📱 Anti-Revocation Telegram Login Protocol

- **The Telegram Revocation Trap**: When Telegram sends a verification code, if the user types or shares that code in a chat message, Telegram's security system revokes and expires it within seconds.
- **The Solution (On-Screen PIN Pad)**:
  - The Cloudflare Worker displays an inline keypad (`buildPinPadKeyboard`) with digits `0-9`, `⌫ Del`, and `✅ Verify`.
  - Tapping buttons sends callback queries (`pin_digit_X`), keeping the chat completely clean of text codes.
  - Upon the 5th digit, the worker automatically auto-applies the 2FA password (from Cloud Vault or memorized custom password) and authenticates on Render Node 2.
- **1-Tap QR Login**:
  - Available as a fast zero-SMS fallback. User scans QR from Telegram Settings > Devices > Link Desktop Device.

---

## 6. ☁️ Multi-Cloud Infrastructure & Handover Mesh

```
                     ┌────────────────────────────────┐
                     │   Telegram User / Admin Chat   │
                     └───────────────┬────────────────┘
                                     │ Webhook / Callbacks
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │        Cloudflare Edge Worker Mesh (Node 4)            │
        │      https://restore-agy.agorameet.workers.dev         │
        └───────────────┬────────────────────────┬───────────────┘
                        │                        │
         Distributed KV │ Upstash Redis          │ Proxy MTProto / API
                        ▼                        ▼
        ┌────────────────────────┐      ┌────────────────────────┐
        │  Upstash Redis REST    │      │  Render Standby Node 2 │
        │  (fleet:accounts, etc) │      │  (Frankfurt Container) │
        └────────────────────────┘      └────────────────────────┘
```

- **Cloudflare Edge**: Node 4 (`restore-agy.agorameet.workers.dev`) handles all webhook routing, PIN pad state, dynamic account rosters, and admin callbacks.
- **Render Standby Node 3 (Oregon)**: `https://my-agy-fleet-standby-node3.onrender.com` runs Telethon MTProto client for cloud logins, token extraction, and 24/7 background mining.
- **GitHub Sync**: `python3 push_to_standby_repo.py` synchronizes `app.py` to `AAA0002/my-agy-fleet-standby` and triggers auto-deploy on Render Node 3.
- **Cloudflare Sync**: `python3 deploy_both_cf_workers.py` deploys the worker script and syncs bot menus.
- **Disaster Recovery**: `python3 backup_manager.py` creates complete disaster recovery archives and streams them to Telegram (`@myagyai`).

---

## 7. 🗄️ Master Fleet Infrastructure & Cloud Assets Registry (147 Keys)

### 7.1 Multi-Cloud Compute & Serverless Edge
- **Cloudflare Workers (5 Accounts / Nodes)**: Node 1 (`aaaai2`), Node 2 (`aaa-bot`), Node 3 (`aaa222`), Node 4 (`agorameet` - Primary Active Webhook), Node 5 (`aaaai`). Plus Secondary & UserBot accounts.
- **Cloudflare Pages**: `https://atf-miner-app.pages.dev/` (Dedicated Ads Portal).
- **Cloudflare Cache API (`caches.default`)**: Zero-cost, infinite read/write RAM cache bypassing KV limits.
- **Render (3 Service Nodes)**: Node 1 Singapore (`srv-d9n...`), Node 2 Frankfurt (`srv-dan...`), Node 3 Oregon (`srv-db437o3tqb8s73dt4erg` - Active Coordinator).
- **Deno Deploy**: `https://my-agy-fleet-deno.aaa222.deno.net` (Deno edge mesh sentinel).
- **Vercel Edge**: `https://agy-aaa000.vercel.app` (Serverless Node).
- **Puzl Kubernetes Cloud**: `https://k8s.eu-finland-1.clusters.puzl.cloud` (Namespace: `root-bhwgczyd9lu5uusfyg7xkvdcu491oh1y6f1lf8pdfzo3z`).
- **UbiCloud VMs**: Open Cloud compute runners via `UBICLOUD_PAT_ID`.
- **CircleCI**: Free automated cloud pipeline runners (`CIRCLECI_TOKEN`).
- **GitHub Actions**: Public runner `cloud-fleet-solver` for unlimited free Turnstile solving.

### 7.2 Multi-Database, Caching & Decentralized Storage
- **Turso LibSQL**: `https://my-agy-fleet-db-aaa2743.aws-ap-south-1.turso.io` (Table `kv_mesh`, 25,000,000 operations/month free tier).
- **Upstash Redis**: Dual-store clusters (`UPSTASH_URL`, `UPSTASH_STANDBY_URL`, `UPSTASH_API_KEY_JMF`, `UPSTASH_API_KEY_AAAFREEAI`).
- **Supabase PostgreSQL**: Database, REST API, Auth & Storage (`SUPABASE_URL`).
- **Qdrant Vector Cloud**: 3 distinct Qdrant clusters configured in `QDRANT_KEYS` for semantic memory and AI embeddings.
- **Layerbase**: Configured in `LAYERBASE_KEYS`.
- **Pinata IPFS**: Decentralized pinning for immutable wallet and system snapshots (`PINATA_JWT`).
- **Cloudflare D1 & KV**: `CF_D1_DATABASE_ID_USERBOT`, `CF_KV_CACHE_ID_USERBOT`, `CF_KV_MINER_ID_SECONDARY`.

### 7.3 Web3, RPC Nodes & On-Chain Gateways
- **TON Blockchain**: `TONAPI_KEY` (TonAPI) + `TONCENTER_API_KEY` (Toncenter high-speed indexing).
- **EVM (BSC / Arbitrum / Ethereum)**: `DRPC_BSC_RPC`, `DRPC_ARBITRUM_RPC` (dRPC decentralized nodes) + `BINANCE_OFFICIAL_RPC` + `ALCHEMY_ETH_RPC` (Alchemy) + `ETHERSCAN_API_KEY`.
- **TRON Blockchain**: Native TRC-20 derivation and balance tracking.
- **Solana Blockchain**: Ed25519 base58 key derivation.
- **Bitcoin Blockchain**: P2PKH / Taproot derivation.

### 7.4 Network, Proxies & Observability
- **Webshare Rotating Proxy Pool**: 7 verified Webshare accounts (`WEBSHARE_KEY_1` to `WEBSHARE_KEY_7`), expanding pool to 70 rotating proxies.
- **IPInfo API**: Geolocation verification & IP hygiene (`IPINFO_TOKEN`).
- **Cron-Job.org**: Automated scheduling (`CRONJOB_API_KEY`), 10 jobs registered (Keep-Alive, Farm, Token Harvester).
- **BetterStack**: Uptime heartbeat monitoring (`BETTERSTACK_HEARTBEAT_URL`).
- **Sentry**: Real-time error tracking and telemetry (`SENTRY_DSN`).
- **Hookdeck**: Webhook reliability queue (`HOOKDECK_API_KEY`).
- **Walrus Memory**: Autonomous persistent agent memory key (`WALRUS_MEMORY_KEY`).
- **DigitalPlat & Cloudflare Email Routing**: Custom domain email forwarding & Google App Password automation.

---
*End of Memory Core. Keep this file updated whenever accounts, pools, or architecture evolve.*
