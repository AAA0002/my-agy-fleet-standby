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

## 2. 👥 Active Accounts Roster (19+ Accounts)

| Index | Name | Username | Telegram ID | Phone | Custody Type | Primary Wallet | Status |
| :---: | :--- | :--- | :---: | :---: | :--- | :--- | :---: |
| **01** | **Arif Hossain (Master)** 👑 | `@Arif2743aaa` | `6727787768` | `+8801317342850` | Binance Main Exchange Vault | TON: `UQBPZiS...gwDT` (Memo: 103525143) | 🟢 Active |
| **02** | Nancy Davis 2 | `None` | `8881914294` | `+8801943805617` | Isolated 24-Word Seed | TON: `UQA0aO4...hsP` | 🟢 Active |
| **03** | Koram Shah | `None` | `7648254021` | `+8801790208077` | Isolated 24-Word Seed | TON: `UQDQ1e7...6G9` | 🟢 Active |
| **04** | Arif 4 | `None` | `8826375659` | `+8801575842094` | Isolated 24-Word Seed | TON: `UQBqM7d...R0E` | 🟢 Active |
| **05** | Nathan Miller 5 | `None` | `8450010161` | `+14302084365` | Isolated 24-Word Seed | TON: `UQDYD4Y...aO_` | 🟢 Active |
| **06** | Kaitlyn Ross 6 | `None` | `8782429452` | `+8801867539837` | Isolated 24-Word Seed | TON: `UQD3m0A...6gX` | 🟢 Active |
| **07** | Abid Hasan 7 | `None` | `7734849205` | `+8801718056423` | Isolated 24-Word Seed | TON: `UQDgq1_...r0k` | 🟢 Active |
| **08** | Abid Hasan (2) 8 | `None` | `8025472383` | `+8801797795624` | Isolated 24-Word Seed | TON: `UQC6jU_...aE2` | 🟢 Active |
| **09** | Naimur Rahman 9 | `None` | `8851426148` | `+8801727651288` | Isolated 24-Word Seed | TON: `UQA4H_G...t5c` | 🟢 Active |
| **10** | **Tanvir Ahmed 10** ⭐ | `@TanvirAhmed10` | `8203342513` | `+8801729892810` | Binance Web3 Wallet 2 (AAA) | TON: `UQBeouW...LKH` | 🟢 Active |
| **11** | MD. ARIF HOSSAIN 11 | `None` | `8190649727` | `+8801571089931` | Isolated 24-Word Seed | TON: `UQA_VwI...Jd0` | 🟢 Active |
| **12** | Sanzida Shimu 12 | `None` | `7487048946` | `+8801774578536` | Isolated 24-Word Seed | TON: `UQCvTzJ...1u_` | 🟢 Active |
| **13** | Abid (3) 13 | `None` | `8741547543` | `+8801838268380` | Isolated 24-Word Seed | TON: `UQDwT-3...xK-` | 🟢 Active |
| **14** | Rohan Sharma 14 | `None` | `8727040932` | `+918930504750` | Isolated 24-Word Seed | TON: `UQCfJ0X...r8K` | 🟢 Active |
| **15** | Tasnim Farhana 15 | `None` | `7749125802` | `+8801906045479` | Isolated 24-Word Seed | TON: `UQAxL-2...4hV` | 🟢 Active |
| **16** | Rashedul Islam 16 | `None` | `7954290138` | `+8801304151082` | Isolated 24-Word Seed | TON: `UQDGZ6E...yYx` | 🟢 Active |
| **17** | Kawsar Mahmud 17 | `None` | `8841038141` | `+8801879273559` | Isolated 24-Word Seed | TON: `UQDjL-9...8bZ` | 🟢 Active |
| **18** | Mehedi Hasan 18 | `None` | `8975442879` | `+8801839716506` | Isolated 24-Word Seed | TON: `UQBcHzN...49fL` | 🟢 Active |
| **19** | **Adil H** | `@AdilHassain` | `8937908003` | `+8801804723069` | Isolated 24-Word Seed | TON: `UQCrEZr...w8D` | 🟢 Active |

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
- **Render Standby Node 2**: `https://my-agy-fleet-standby-node2.onrender.com` runs Telethon MTProto client for cloud logins, token extraction, and 24/7 background mining.
- **GitHub Sync**: `python3 push_to_standby_repo.py` synchronizes `render_standby_app.py` as `app.py` to `AAA0002/my-agy-fleet-standby` and triggers auto-deploy on Render Node 2.
- **Cloudflare Sync**: `python3 deploy_both_cf_workers.py` deploys the worker script and syncs bot menus.
- **Disaster Recovery**: `python3 backup_manager.py` creates complete disaster recovery archives and streams them to Telegram (`@myagyai`).

---
*End of Memory Core. Keep this file updated whenever accounts, pools, or architecture evolve.*
