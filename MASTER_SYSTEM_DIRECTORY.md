# 🧭 AAA AUTO / MY AGY AI — Master System Directory & Operational Navigation Hub

> **AUTHORITATIVE MASTER SYSTEM DIRECTORY & LIVING OPERATIONAL INDEX**:
> This document is the **Single Source of Truth (SSOT)** for Commander Arif and any AI agent (Antigravity, Gemini, Claude, GPT). It documents every single dashboard, bot, credential, authentication protocol, biometric/passkey lock, 20-account fleet roster, 9-pool mining engine, API route, database table, and disaster recovery workflow across the entire AAA AUTO infrastructure.
> **Rule of Thumb**: Before modifying, deploying, or debugging any part of the system, consult this index to instantly locate files, credentials, routes, and operational rules.

---

## 📑 Table of Contents

1. [⚡ Executive Quick-Reference Cheat Sheet](#-1-executive-quick-reference-cheat-sheet)
2. [🔐 Master Authentication, Lock & Biometric Passkey Architecture](#-2-master-authentication-lock--biometric-passkey-architecture)
3. [🖥️ The Complete 4-Dashboard Roster & Technical Specifications](#-3-the-complete-4-dashboard-roster--technical-specifications)
4. [🤖 Dual Bot Ecosystems ("Zero Ecosystem Mixing" Architecture)](#-4-dual-bot-ecosystems-zero-ecosystem-mixing-architecture)
5. [👥 20 Telegram Accounts Fleet Directory & Master Registry](#-5-20-telegram-accounts-fleet-directory--master-registry)
6. [⛏️ 9 Active Fleet Mining Protocols & Auto-Binding Handshakes](#-6-9-active-fleet-mining-protocols--auto-binding-handshakes)
7. [🌐 Multi-Cloud Infrastructure & Edge Mesh Topology](#-7-multi-cloud-infrastructure--edge-mesh-topology)
8. [📡 Comprehensive Master REST API Route Directory](#-8-comprehensive-master-rest-api-route-directory)
9. [💾 Operational Runbook & Automated Disaster Recovery](#-9-operational-runbook--automated-disaster-recovery)
10. [📁 Repository File System Map ("Where Everything Lives")](#-10-repository-file-system-map-where-everything-lives)

---

## ⚡ 1. Executive Quick-Reference Cheat Sheet

| Parameter | Value / Identifier | Notes |
|:---|:---|:---|
| **System Commander** | **Arif** (`6727787768` / `@Arif2743aaa`) | Sole administrative owner of the fleet and master vaults |
| **Admin Master PIN** | **`2743`** | Standardized 4-digit numeric PIN for both admin dashboards |
| **PIN SHA-256 Hash** | `4d5f60d62b859ce230607dc271d27378a876b60c24c5de0832f2df98c0b46b9b` | Verified in Cloudflare Workers edge auth logic |
| **Biometric Passkeys** | Upstash Redis `admin_passkeys:6727787768` | Multi-device WebAuthn passkey set (Fingerprint/TouchID/FaceID) |
| **Admin Bot** | **`@myagyai`** (ID: `8858823950`) | Executive fleet operations, 20 MTProto accounts, cloud sentinel |
| **User Bot** | **`@AAAPREMIUMAPPSbot`** (ID: `8167732110`) | Public community mining, rewarded video ads, points economy |
| **TON Master Vault** | `UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT` | Executive on-chain treasury ([Tonviewer](https://tonviewer.com/UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT)) |
| **EVM Master Vault** | `0x7856d39352e8045610e7c53d0e9a56eefbf19b5c` | BNB Chain (BEP-20) & Arbitrum treasury |
| **Primary Edge Gateway** | `https://restore-agy.agorameet.workers.dev` | Cloudflare Edge Mesh Node 4 (Frankfurt/Global) |
| **Active Fleet Accounts** | **20 Accounts** (1 Master + 19 Workers) | 100% cloud-farmed across 8 verified pools |
| **Active Mining Pools** | **8 Protocols (Strict 8-Bot Integrity)** | MRG Miner, ATF Miner, Victor's Company, VyroDrop, Kynex Network, DiggoMiner, PepeGram, AdxEarn AI |
| **Zero Phone Load** | **Samsung Galaxy A30** | STRICTLY pair-programming CLI. Zero local bots or daemons. |

### 📢 Telegram Channels Directory (Strictly Isolated)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        TELEGRAM CHANNELS SEPARATION BOUNDARY                           │
├───────────────────────────────────────────┬────────────────────────────────────────────┤
│ 🛡️ ADMINISTRATIVE & VAULT CHANNELS        │ 📢 PUBLIC COMMUNITY & MINING CHANNELS      │
│ (Private to Admin Bot @myagyai)           │ (Public to User Bot @AAAPREMIUMAPPSbot)    │
├───────────────────────────────────────────┼────────────────────────────────────────────┤
│ • DR Vault Channel: @myagyai              │ • Announcements: @AAAAutoMiner             │
│   (ID: -1004453515167)                    │   (ID: -1003684868577)                     │
│ • Payouts & Daily Ledger:                 │ • Community Mining Hub: @AAAAUTOMINING     │
│   (ID: -1004402765950)                    │   (ID: -1004255751168)                     │
│ • Fleet Internal Supergroup:              │ • Activity & Verification: @AAA_ACTIVITY   │
│   (ID: -1003973231307)                    │   (ID: -1004332544939)                     │
└───────────────────────────────────────────┴────────────────────────────────────────────┘
```

---

## 🔐 2. Master Authentication, Lock & Biometric Passkey Architecture

Both the Executive Fleet Operations Console (`/admin`) and User Bot Admin Console (`/user-admin`) share a hardened cyber-fintech security gate.

```
       ┌──────────────────────────────────────────────────────────┐
       │              CYBER-FINTECH SECURITY GATE                 │
       │   [ 🔒 ENTER SECURITY PIN ] or [ 👆 BIOMETRIC PASSKEY ]  │
       └────────────┬─────────────────────────────┬───────────────┘
                    │                             │
          ┌─────────▼─────────┐         ┌─────────▼─────────┐
          │  4-DIGIT PIN 2743 │         │ WEBAUTHN PASSKEY  │
          │  Auto-Submit Pad  │         │ Fingerprint/Touch │
          └─────────┬─────────┘         └─────────┬─────────┘
                    │                             │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
          ┌───────────────────────────────────────────────┐
          │  Cloudflare Edge Token: admin_sess:<hash>     │
          │  • Instant 1-Tap Lock (preserves token)       │
          │  • 15-Minute Inactivity Auto-Lock             │
          │  • 5-Minute Background Tab Auto-Lock          │
          │  • 1-Click Logout (purges token)              │
          └───────────────────────────────────────────────┘
```

### 🔢 1. 4-Digit Numeric PIN Pad System
- **Master PIN**: `2743` (Commander Arif's signature administrative code).
- **Interactive UI**: 3x4 Cyber-Fintech Numeric Keypad (`1-9`, `👆 Passkey`, `0`, `⌫ Delete`).
- **4 Glowing Indicator Dots**: As digits are entered, dots light up cyan/neon. Upon the 4th digit, the PIN is validated and submitted automatically.
- **Physical Keyboard Support**: Desktop operators can type `0-9` directly on their keyboard. `Backspace` deletes the last digit, and `Escape` clears all entered digits.
- **Alternative Password Mode**: Operators can click `"Or use master password 🔏"` to switch between the numeric pad and a standard text password input field.

### 👆 2. WebAuthn Biometric Passkeys (Fingerprint / Touch ID / Face ID)
- **FIDO2 / WebAuthn Standard**: Provides hardware-bound asymmetric cryptographic authentication.
- **Authentication Handshake**:
  1. Frontend requests random challenge: `GET /api/admin/auth/passkey-challenge`.
  2. Browser invokes device biometric prompt via `navigator.credentials.get({ publicKey: ... })`.
  3. Signature payload is verified against registered public keys: `POST /api/admin/auth/verify-passkey`.
  4. Returns signed session bearer token.
- **Multi-Device Credential Array**:
  - Upstash Redis key: `admin_passkeys:6727787768` (Set of registered credentials).
  - Enables enrolling multiple physical devices simultaneously (e.g. Android phone, MacBook Touch ID, Windows PC).
  - Synchronized with Supabase `admin_auth` table.
- **Bypass Cache Lag**: Upstash Redis queries for `admin_passkey` and `admin_sess:` bypass the 15-minute in-memory worker cache (`maxAgeMs = 0`), ensuring newly enrolled devices work immediately.
- **Header Status Dot & First-Login Prompt**:
  - The `👆 Passkey` button in the dashboard header displays a live status dot: 🟢 green if the device has an enrolled passkey, 🟡 yellow if unlinked.
  - A first-login banner politely invites Commander Arif to enroll biometric passkeys on newly detected devices with 1-click.

### ⏱️ 3. Auto-Lock & Session Lifecycle
- **Instant 1-Tap `🔒 Lock` Button**: Located in the top header bar of both consoles. Locks the screen immediately without terminating or dropping active session state.
- **15-Minute Inactivity Auto-Lock**: Monitors mouse movement, touch events, keyboard input, and scrolling. If inactive for > 15 minutes, locks the console automatically.
- **5-Minute Background Tab Auto-Lock**: Utilizes the HTML5 Page Visibility API (`document.hidden` / `visibilitychange`). If the operator switches to another app or minimizes the browser for > 5 minutes, the console locks automatically to prevent unauthorized access.
- **Dedicated `🚪 Logout` Button**: Terminates the session token on Cloudflare Edge, wipes local storage tokens, and redirects back to the initial login state.

### 🎵 4. Zero-Asset Web Audio API Synthesizer & Haptics
- **100% Synthetic Sound**: Uses the browser's native `AudioContext` oscillator with zero external audio assets or network requests:
  - `playSound('click')`: 800Hz gentle sine pulse (20ms) for tactile keypad taps.
  - `playSound('success')`: Ascending C-E-G triad fanfare (120ms) for successful logins and actions.
  - `playSound('error')`: 150Hz harsh sawtooth buzz (150ms) for incorrect PIN attempts.
  - `playSound('harvest')` / `playSound('reward')`: Smooth arpeggiated chime for mining sweeps.
- **Telegram Haptic Feedback**: Triggers native device vibration via `Telegram.WebApp.HapticFeedback.notificationOccurred('success' | 'error' | 'warning')`.

---

## 🖥️ 3. The Complete 4-Dashboard Roster & Technical Specifications

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             THE 4 AUTHORITATIVE DASHBOARDS                             │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1️⃣ User Mining Mini App: /miner (public_ads/miner/index.html)                          │
│    • Public end-users • Autonomous cloud mining • 9 pools • Non-custodial wallets      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 2️⃣ User Bot Admin Console: /user-admin (public_admin/user-admin.html)                  │
│    • Commander Arif • Community miners roster • Points economy • Rewarded ads metrics  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 3️⃣ Dedicated Ads Monetization Portal: /ads (public_ads/index.html)                     │
│    • Public end-users • Waterfall rewarded ads • Persistent User Bot menu button       │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 4️⃣ Executive Fleet Operations Console: /admin (public_admin/admin.html)                │
│    • Executive operators • 20 MTProto accounts • 9 pools engine • DR backup triggers   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1️⃣ Dashboard 1: User Mining Mini App (`/miner`)
- **Live URLs**:
  - `https://restore-agy.agorameet.workers.dev/miner`
  - `https://agy-henna.vercel.app/miner`
- **Source File**: [`public_ads/miner/index.html`](file:///data/workspace/AAA_AUTO/public_ads/miner/index.html) (160 KB)
- **Mirrors**: [`public/index.html`](file:///data/workspace/AAA_AUTO/public/index.html), [`public/app/index.html`](file:///data/workspace/AAA_AUTO/public/app/index.html)
- **Embedded In Edge Worker**: `__USER_MINI_APP_HTML_JSON__` in `deploy_both_cf_workers.py`.
- **Target Audience**: Public Telegram end-users of `@AAAPREMIUMAPPSbot`.
- **Core Features**:
  - **Authentic Points & Runway**: Real-time points balance and daily runway calculation based on connected accounts (`Math.floor(points / daily_cost)`).
  - **Account Slots Tracking**: Live meter displaying connected slots vs max slots (base slots + bonus ad slots).
  - **7-Day Streak Stepper**: Interactive visual milestone stepper with live cooldown timer and dynamic claim bonuses (`+100` to `+500` Pts).
  - **1-Click Multi-Pool Harvest**: Concurrently triggers cloud mining passes across all 9 pools via `/api/farm/all`.
  - **8 Verified Protocol Cards**: Real connected accounts counters (`mrgC`, `atfC`, `victorsC`, `vyroC`, `kynexC`, `diggoC`, `adxC`, `pepeC`) with reward token chips (`Earn TON`, `Earn ATF`, `Earn VYRO`, etc.).
  - **Non-Custodial Cloud Vaults**: Multi-chain wallet suite (TON, EVM/BSC, TRON, SOL) with high-resolution deposit QR modal and direct block explorer links (Tonviewer, BscScan, Tronscan, Solscan).
  - **Authentic Binance Crypto Oracle**: Fetches live ticker prices directly from `/api/rates`.
  - **Zero-Fake Guarantee**: Zero simulated satoshi counters or fabricated gigahash tickers.
  - **Silent 30-Second Background Sync**: Automatically refreshes data without page reloads.

### 2️⃣ Dashboard 2: User Bot Admin Console (`/user-admin`)
- **Live URLs**:
  - `https://restore-agy.agorameet.workers.dev/user-admin`
  - `https://agy-aaa000.vercel.app/user-admin`
- **Source File**: [`public_admin/user-admin.html`](file:///data/workspace/AAA_AUTO/public_admin/user-admin.html) (114 KB)
- **Mirror**: [`public/user-admin.html`](file:///data/workspace/AAA_AUTO/public/user-admin.html)
- **Embedded In Edge Worker**: `__USER_ADMIN_DASHBOARD_HTML_JSON__` in `deploy_both_cf_workers.py`.
- **Target Audience**: Commander Arif (User Bot Community Administrator).
- **Authentication**: PIN `2743` or WebAuthn Biometric Passkey.
- **Core Features**:
  - **Community Miners Roster**: Real-time listing of all community users queried from Upstash Redis `ub_registered_users` and Turso LibSQL.
  - **Multi-Filter Chips**: Filter by `All`, `Connected Accounts`, `With Wallets`, `Custom Payout`, `VIP Passes`, `Active`, `Paused`, `⚠️ Low Pts`, and `🚫 Banned`.
  - **Rewarded Ads Monetization Card**: Live metrics tracking total community rewarded ads watched, points distributed (+20 Pts/ad), and active watchers.
  - **Direct Telegram DM Action**: 1-click `DM ↗` links (`https://t.me/<username>`) on user cards to reach users requiring session refresh or points top-ups.
  - **Points Grant & Deduction Modal**: Credit or deduct points with preset chips (`+50`, `+200`, `+500`, `-50`) or custom amounts.
  - **Broadcast Center**: Dispatch custom announcements with templates, line counter, and live Telegram character limit checker (`X / 4096 chars`).
  - **Economy Sweeper**: Trigger manual or automated 100 Pts/day sweeps with detailed deduction audit.
  - **JSON Export**: 1-click button to download the entire community miners database snapshot.

### 3️⃣ Dashboard 3: Dedicated Ads Monetization Portal (`/ads`)
- **Live URLs**:
  - `https://agy-henna.vercel.app/` (Primary Hosted Vercel App)
  - `https://restore-agy.agorameet.workers.dev/ads` (Edge worker redirect)
- **Source File**: [`public_ads/index.html`](file:///data/workspace/AAA_AUTO/public_ads/index.html) (121 KB)
- **Embedded In Edge Worker**: `__USER_ADS_HTML_JSON__` in `deploy_both_cf_workers.py`.
- **Target Audience**: Public Telegram end-users (Monetization & Slot Unlocks).
- **Core Features**:
  - **Waterfall Ad Mediation Engine**: HilltopAds VAST 3.0, Clickadu, GigaPub, and Monetag SDKs.
  - **Persistent Menu Button Binding**: The bottom-left Telegram chat menu button of `@AAAPREMIUMAPPSbot` is permanently bound to **`🎬 Watch Ads`** pointing directly to `https://agy-henna.vercel.app/`.
  - **Cryptographic Credit Webhook**: Upon ad completion, calls `/api/user/claim-ad` with cryptographic verification to award `+20 Pts` to the user profile.
  - **Preservation Invariant**: **100% UNTOUCHED**. Never overwrite this portal with unrelated dashboard code.

### 4️⃣ Dashboard 4: Executive Fleet Operations Console (`/admin`)
- **Live URLs**:
  - `https://restore-agy.agorameet.workers.dev/admin`
  - `https://agy-aaa000.vercel.app/admin`
- **Source File**: [`public_admin/admin.html`](file:///data/workspace/AAA_AUTO/public_admin/admin.html) (118 KB)
- **Mirror**: [`public/admin.html`](file:///data/workspace/AAA_AUTO/public/admin.html)
- **Embedded In Edge Worker**: `__ADMIN_DASHBOARD_HTML_JSON__` in `deploy_both_cf_workers.py`.
- **Target Audience**: Commander Arif & Executive Fleet Operators.
- **Authentication**: PIN `2743` or WebAuthn Biometric Passkey.
- **Core Features**:
  - **20 MTProto Accounts Live Telemetry**: Live session health (`ACTIVE_ONLINE`, `NEEDS_CODE`, `REVOKED`) across all 20 fleet accounts.
  - **Executive Treasury Watcher**: Tracks on-chain TON Executive Master Vault (`UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT`) and Binance BEP-20 Master Vault with live Tonviewer and BscScan links.
  - **20-Account 5-Chain Wallet Directory**: Integrated wallet directory with chain filter selector pills (`ALL`, `TON`, `EVM`, `TRON`, `SOL`, `BTC`), search filter, fast copy, and explorer links.
  - **9 Farming Pools Cloud Orchestrator**: Real-time status and 1-click cloud trigger across all 9 farming protocols.
  - **Multi-Cloud Node Health**: Real-time round-trip latency testing for all 5 Cloudflare edge nodes and Render Standby Node 2.
  - **Upstash Redis Key Inspector**: Search, inspect, and safely manage Redis keys.
  - **Disaster Recovery Controls**: 1-click trigger to stream encrypted backup archives directly to `@myagyai`.

---

## 🤖 4. Dual Bot Ecosystems ("Zero Ecosystem Mixing" Architecture)

The system operates two completely independent bot identities. In accordance with **Rules 1 & 7**, code, tokens, command handlers, channels, databases, and dashboards are strictly segregated:

```
┌──────────────────────────────────────────────┬──────────────────────────────────────────────┐
│       👑 ADMIN BOT (@myagyai)                │       🤖 USER BOT (@AAAPREMIUMAPPSbot)       │
├──────────────────────────────────────────────┼──────────────────────────────────────────────┤
│ • Bot ID: 8858823950                         │ • Bot ID: 8167732110                         │
│ • Tokens: ADMIN_BOT_TOKEN / REPORT_BOT_TOKEN │ • Tokens: USER_BOT_TOKEN                     │
│ • Primary Audience: Commander Arif (Admin)   │ • Primary Audience: Public Telegram Users    │
│ • Database Namespace: fleet:* & accounts.json│ • Database Namespace: ub_*, Turso LibSQL     │
│ • Chat Menu Button: 👑 Fleet Dashboard       │ • Chat Menu Button: 🎬 Watch Ads             │
│   (https://...workers.dev/admin)             │   (https://agy-henna.vercel.app/)            │
│ • Webhook URL: /api/admin/bot/webhook        │ • Webhook URL: /api/user/bot/webhook         │
│ • Private Vaults: Channel @myagyai           │ • Community Channels: @AAAAutoMiner,         │
│   Supergroup -1003973231307, Payouts         │   @AAAAUTOMINING, @AAA_ACTIVITY              │
│ • Dedicated Console: /admin                  │ • Dedicated Console: /user-admin & /miner    │
└──────────────────────────────────────────────┴──────────────────────────────────────────────┘
```

### 📋 Complete Telegram Bot Commands Reference

#### Admin Bot Commands (`@myagyai`)
- `/start` — Welcomes Commander Arif and displays the executive fleet control panel.
- `/fleet` or `/status` — Displays real-time operational status of all 20 accounts and 9 mining pools.
- `/farm` — Triggers an immediate cloud farming pass across all active pools.
- `/wallets` — Summarizes aggregate balances across TON, EVM, TRON, SOL, and BTC vaults.
- `/nodes` — Checks round-trip health of Cloudflare Edge nodes and Render Standby Node 2.
- `/backup` — Triggers an encrypted disaster recovery backup archive to channel `@myagyai`.
- `/restore` — Outputs the 1-click restore command for instant VM bootstrapping.
- `/acc <id>` — Inspects session telemetry, phone number, and wallet addresses for account #`id`.

#### User Bot Commands (`@AAAPREMIUMAPPSbot`)
- `/start` — Launches user onboarding, assigns non-custodial wallets, and displays the WebApp launcher.
- `/miner` — Opens the User Mining Mini App (`/miner`) inside Telegram.
- `/account` — Displays user points balance, runway days, active accounts, and bonus ad slots.
- `/wallets` or `/keys` — Displays the user's dedicated non-custodial 5-chain wallet addresses and recovery keys.
- `/customwallet <address>` — Binds a personal external TON or EVM wallet for automated payout routing.
- `/checkin` — Claims the daily streak points reward (+100 to +500 Pts).
- `/quests` — Displays community channel join quests for bonus points.
- `/help` — Displays the community mining guide and FAQ.

---

## 👥 5. 20 Telegram Accounts Fleet Directory & Master Registry

The fleet manages **20 authenticated Telegram accounts** operating concurrently in the cloud.

### 📜 Master Accounts Roster

| Account # | Telegram User ID | Account Name / Label | Assigned Proxy | Primary TON Wallet (v4r2) |
|:---:|:---:|:---:|:---:|:---|
| **#1** | `6727787768` | **Arif (Master)** | Direct / Pooled | `UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT` |
| **#2** | `7058204212` | Worker Account 02 | Webshare US | `EQB4Z...` (See Vault) |
| **#3** | `7184920145` | Worker Account 03 | Webshare US | `EQC8x...` (See Vault) |
| **#4** | `7201948210` | Worker Account 04 | Webshare DE | `EQD1a...` (See Vault) |
| **#5** | `7349102847` | Worker Account 05 | Webshare UK | `EQAf3...` (See Vault) |
| **#6** | `7410293841` | Worker Account 06 | Webshare NL | `EQB7u...` (See Vault) |
| **#7** | `7529104820` | Worker Account 07 | Webshare FR | `EQC9m...` (See Vault) |
| **#8** | `7610293845` | Worker Account 08 | Webshare US | `EQD2p...` (See Vault) |
| **#9** | `7739102841` | Worker Account 09 | Webshare CA | `EQA4k...` (See Vault) |
| **#10** | `7810293849` | Worker Account 10 | Webshare US | `EQB6j...` (See Vault) |
| **#11** | `7920192843` | Worker Account 11 | Webshare DE | `EQC1v...` (See Vault) |
| **#12** | `8019284710` | Worker Account 12 | Webshare UK | `EQD8w...` (See Vault) |
| **#13** | `8120394821` | Worker Account 13 | Webshare NL | `EQA3z...` (See Vault) |
| **#14** | `8239102845` | Worker Account 14 | Webshare FR | `EQB5x...` (See Vault) |
| **#15** | `8340192847` | Worker Account 15 | Webshare US | `EQC7c...` (See Vault) |
| **#16** | `8451029381` | Worker Account 16 | Webshare CA | `EQD4b...` (See Vault) |
| **#17** | `8562019284` | Worker Account 17 | Webshare US | `EQA1n...` (See Vault) |
| **#18** | `8673102945` | Worker Account 18 | Webshare DE | `EQB9m...` (See Vault) |
| **#19** | `8937908003` | **Adil H** | Webshare UK | Dedicated 5-Chain Suite (Generated) |
| **#20** | `8609131528` | **Asaduzzaman Sarker** | Webshare NL | Dedicated 5-Chain Suite (Generated) |

> 🔒 **Master Wallet Immutability Rule**: Our system **ONLY** creates new wallets for genuinely brand-new accounts, NEVER for old or existing accounts. When an existing account reconnects, its authentic wallet suite is preserved with 100% immutability.

### 🗄️ Master Secrets Storage Files (Local & Isolated)
- `FLEET_WALLETS_SECRETS_MASTER_VAULT.txt` — Secure master secrets vault with mnemonics and private keys for all accounts (strictly `.gitignore`'d).
- `FLEET_ACCOUNTS_AND_WALLETS_DIRECTORY.md` — Public markdown directory with sanitized addresses.
- `public_admin/fleet_wallets_data.json` — Static wallet registry powering the admin dashboard.
- `fleet_ton_wallets.json`, `fleet_evm_wallets.json`, `fleet_tron_wallets.json`, `fleet_solana_wallets.json`, `fleet_btc_wallets.json` — Chain-specific JSON vaults.
- `accounts.json` — Telethon MTProto session strings for all 20 accounts.

---

## ⛏️ 6. 9 Active Fleet Mining Protocols & Auto-Binding Handshakes

All discontinued, scammer, or dead bots (LeafEarn, PumpkinEarn) have been permanently purged. The 9 active protocols are:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               9 ACTIVE MINING PROTOCOLS                                │
├────┬──────────────────┬────────────────────────┬───────────────────────────────────────┤
│ #  │ Protocol Name    │ Bot Handle             │ Solving & Handshake Mechanism         │
├────┼──────────────────┼────────────────────────┼───────────────────────────────────────┤
│ 1  │ MRG Miner        │ @mrgminerbot           │ Single-Click Turnstile, TonConnect 2  │
│ 2  │ ATF Miner        │ @ATF_AIRDROP_bot       │ Deterministic Math Solver, TON Sync   │
│ 3  │ Victor's Company │ @VictorsCompanybot     │ MTProto Minting, Level 1 Unlock       │
│ 4  │ VyroDrop         │ @vyrodrop_bot          │ Autonomous 0.05 VYRO/h, TonConnect 2  │
│ 5  │ Kynex Network    │ @Kynex_miningbot       │ 15-Min Energy Sweep, Firebase Tokens  │
│ 6  │ DiggoMiner       │ @Diggominer_bot        │ 30-Day JWT Fallback, Auto-Claim       │
│ 7  │ PepeGram         │ @Pepe_gram_bot         │ 6-Hour Production, Slot Spin Loop     │
│ 8  │ AdxEarn AI       │ @AdxEarnAibot          │ Daily Streaks & Dynamic Task Sweeps   │
└────┴──────────────────┴────────────────────────┴───────────────────────────────────────┘
```

### ⚙️ Handshake & Auto-Binding Details

1. **MRG Miner (`@mrgminerbot`)**:
   - **Solving**: Solves Cloudflare Turnstile with single-click Chrome DevTools Protocol (`mrg_turnstile_solver.py`).
   - **TonConnect 2.0**: Signs cryptographic Ed25519 proofs over dynamic nonces to bind TON wallets (`app.mrgtoken.xyz`).
   - **Miner Upgrades**: Automatically auto-upgrades mining rigs to Level 95+ and auto-claims satoshis.
2. **ATF Miner (`@ATF_AIRDROP_bot`)**:
   - **Solving**: Local deterministic math solver (`solve_atf_math`) solves arithmetic expressions and word operators in < 0.01ms.
   - **Auto-Sync**: Automatically syncs the account's TON address to `atfminers.asloni.online/miner/index.php?action=sync_wallet`.
3. **Victor's Company (`@VictorsCompanybot`)**:
   - **0-Second Fresh Token Minting**: Telethon MTProto engine mints fresh WebApp authorization tokens on demand to prevent `401 TG_AUTH`.
   - **Level 1 Miner Unlock**: Dispatches `POST /api/levels/unlock {"level": 1}` to hire Level 1 Miner and avoid `home.noJob`.
   - **Pass Compounding**: Automatically claims daily HumanPass and reinvests in mining passes.
4. **VyroDrop (`@vyrodrop_bot`)**:
   - **TonConnect 2.0 Handshake**: Simulates TonConnect 2.0 proof handshake via `POST /api/auth/verify-wallet`.
   - **Autonomous 0.05 VYRO/h Loop**: Automatically activates mining cycle via `POST /api/mining/start`.
5. **Kynex Network (`@Kynex_miningbot`)**:
   - **Auth**: Exchanges `initData` with Firebase auth token via `verifyTelegramAuth`.
   - **Energy Sweep**: Automatically triggers 15-minute energy sweeps and node claim cycles.
6. **DiggoMiner (`@Diggominer_bot`)**:
   - **30-Day JWT Fallback**: Exchanges Telegram session with long-lived JWT token; auto-claims mined tokens and Solana launch tasks.
7. **PepeGram (`@Pepe_gram_bot`)**:
   - **Autonomous Loop**: Claims daily PEPE rewards, starts 6-hour production, spins free slot, and claims team commissions.
8. **AdxEarn AI (`@AdxEarnAibot`)**:
   - **Dynamic Tasks & Streaks**: Autonomous check-in streak, farming boost, and dynamic task sweeping.

---

## 🌐 7. Multi-Cloud Infrastructure & Edge Mesh Topology

The system runs entirely in the cloud across high-availability edge nodes, ephemeral compute workers, and persistent key-value meshes.

```
                              ┌─────────────────────────────────────────┐
                              │     CLOUDFLARE EDGE MESH GATEWAYS       │
                              │     Node 4: restore-agy.agorameet       │
                              │     Node 1: restore-agy.aaaai2          │
                              │     Node 2: restore-agy.aaa-bot         │
                              │     Node 3: restore-agy.aaa222          │
                              │     Node 5: restore-agy.aaaai           │
                              └───────┬─────────────────────────┬───────┘
                                      │                         │
            ┌─────────────────────────┴─────────┐     ┌─────────┴────────────────────────┐
            │                                   │     │                                  │
            ▼                                   ▼     ▼                                  ▼
┌───────────────────────┐           ┌───────────────────────┐           ┌───────────────────────┐
│     RENDER NODE 2     │           │   UPSTASH REDIS MESH  │           │     TURSO LIBSQL      │
│  (Frankfurt Standby)  │           │   (Encrypted Key/Val) │           │   (Distributed SQL)   │
│  • Session Collector  │           │   • fleet:* (Admin)   │           │   • user_accounts     │
│  • Turnstile Solvers  │           │   • ub_* (User Bot)   │           │   • user_wallets      │
│  • Ad-Farming Sweeps  │           │   • admin_passkeys    │           │   • ad_impressions    │
└───────────────────────┘           └───────────────────────┘           └───────────────────────┘
```

### 🛰️ Infrastructure Roster
1. **Primary Cloudflare Edge Gateway (Node 4)**:
   - URL: `https://restore-agy.agorameet.workers.dev`
   - Role: Master API router, dashboard server, WebAuthn passkey verifier, Workers AI challenge solver.
2. **Cloudflare Edge Redundant Mesh (Nodes 1, 2, 3, 5)**:
   - Fallback nodes providing geo-distributed failover, price feeds, and health telemetry.
3. **Render Cloud Standby Node 2**:
   - URL: `https://my-agy-fleet-standby-node2.onrender.com`
   - Role: Collects session links on-demand, executes MTProto pairing, spins down automatically to preserve free quota on `koramshah2@gmail.com`.
4. **Upstash Redis**:
   - Namespaces: `fleet:*` (Admin fleet state, accounts), `ub_*` (User Bot profiles, daily streaks), `admin_passkeys:6727787768` (WebAuthn credentials).
5. **Turso LibSQL**:
   - Tables: `user_accounts` (User MTProto sessions), `user_wallets` (User non-custodial wallets), `user_points` (Ledger), `ad_impressions_log` (Rewarded ad audits).
6. **GitHub Actions (Standby Mirror)**:
   - Repository: `AAA0002/my-agy-fleet-standby` (Public mirror receiving **unlimited free runner minutes**).
   - Workflow: `.github/workflows/fleet_sentinel.yml` running multi-cloud health sweeps.

---

## 📡 8. Comprehensive Master REST API Route Directory

All endpoints are hosted on the primary Cloudflare Edge Gateway (`https://restore-agy.agorameet.workers.dev`):

### 👤 Public User Endpoints
- `GET /miner` — Serves the User Mining Mini App HTML.
- `GET /ads` — Redirects to the Dedicated Ads Monetization Portal (`https://agy-henna.vercel.app/`).
- `GET /api/user/profile?initData=...` — Returns user points, runway, connected accounts count, and slots.
- `POST /api/user/claim-daily` — Claims daily streak bonus (+100 to +500 Pts).
- `POST /api/user/claim-ad` — Cryptographically verifies rewarded ad completion and awards +20 Pts.
- `POST /api/user/claim-quest` — Claims points for joining official community channels (+50 Pts each).
- `GET /api/user/wallets?initData=...` — Retrieves user's 5-chain non-custodial wallet addresses and keys.
- `POST /api/user/wallet/custom` — Binds personal TON or EVM payout address.
- `POST /api/farm/all` — Triggers cloud harvest across all 9 pools concurrently.
- `GET /api/rates` — Live crypto market rates (TON, BNB, BTC, ETH, SOL) from Binance.
- `POST /api/user/account/add` — Adds an account session (1-Tap Telegram link, QR login, or Phone SMS).

### 🔒 Admin Security & Passkey Endpoints
- `POST /api/admin/auth/login` — Verifies PIN `2743` (or SHA-256 hash) and returns bearer token.
- `GET /api/admin/auth/passkey-challenge` — Generates a WebAuthn challenge for biometric authentication.
- `POST /api/admin/auth/verify-passkey` — Verifies device biometric signature and issues session token.
- `POST /api/admin/auth/register-passkey` — Enrolls a new biometric device passkey into `admin_passkeys:6727787768`.
- `GET /api/admin/auth/status` — Checks current passkey enrollment status (enrolled count, active devices).
- `POST /api/admin/auth/logout` — Terminates and purges the active session token.

### 🤖 User Bot Admin Endpoints (`/user-admin`)
- `GET /api/admin/users?secret=2743` — Returns full list of community miners with pagination and filters.
- `POST /api/admin/user/points` — Credits or deducts points from a community user profile.
- `POST /api/admin/user/ban` — Toggles ban status for a suspected sybil user.
- `POST /api/admin/broadcast` — Dispatches targeted broadcast messages to community cohorts via `@AAAPREMIUMAPPSbot`.
- `POST /api/admin/economy/sweep` — Triggers 100 Pts/day cloud sweep with detailed deduction audit.
- `GET /api/admin/metrics/ads` — Returns aggregate rewarded ad impressions and point distribution metrics.

### 🏢 Executive Fleet Endpoints (`/admin`)
- `GET /api/fleet/status?secret=2743` — Real-time telemetry for all 20 accounts and 9 farming pools.
- `GET /api/fleet/wallets?secret=2743` — Returns complete 20-account 5-chain wallet directory.
- `POST /api/fleet/farm` — Triggers an immediate cloud farming pass across the 20 accounts.
- `GET /api/nodes/health` — Returns round-trip latency for all 5 Cloudflare nodes and Render Node 2.
- `POST /api/fleet/backup` — Triggers encrypted disaster recovery backup archive to `@myagyai`.

---

## 💾 9. Operational Runbook & Automated Disaster Recovery

### 🛡️ Rule 5: Mandatory Telegram Backup Pipeline
Whenever modifying code, deploying updates, or transferring workspace states, execute:
```bash
python3 backup_manager.py
```
- **What it does**: Gathers core code, Telethon sessions, configurations, and wallet registries, encrypts them into an archive, calculates SHA-256 checksums, and uploads them directly to Telegram vault channel `@myagyai` (`-1004453515167`).
- **Verification**: Ensure the output ends with:
  `✅ Backup uploaded to https://t.me/myagyai and saved locally!`

### 🚀 Standalone 1-Click Disaster Recovery Restore
If an ephemeral VM dies or you are setting up a brand-new cloud container, restore everything with one command:
```bash
bash restore.sh
```
Or execute the 1-line curl bootstrapper from Telegram vault `@myagyai`.

### 🔄 Dual-Remote Git Synchronization
Always push code simultaneously to both the primary repository and the standby unlimited-runners mirror:
```bash
git push origin main && git push standby_repo main
```

---

## 📁 10. Repository File System Map ("Where Everything Lives")

```
/data/workspace/AAA_AUTO/
├── MASTER_SYSTEM_DIRECTORY.md          # 🧭 THIS DOCUMENT — Master system index & navigation hub
├── DASHBOARDS_AND_SYSTEM_GROUND_TRUTH.md # 🏛️ 4-Dashboard specification & zero-fake policy
├── PROJECT_BIBLE.md                     # 📖 Universal architecture bible & 8-bot engine manual
├── SESSION_BRIDGE.md                    # 🌉 Continuity handover & past action history
├── FLEET_MEMORY_CORE.md                 # 🧠 20-Account memory & operational invariants
├── FLEET_ACCOUNTS_AND_WALLETS_DIRECTORY.md # 💳 20-Account 5-chain non-custodial wallet directory
├── DUAL_ADMIN_DASHBOARDS_AND_USER_SYSTEM.md # 🛡️ Guide to dual consoles (/admin vs /user-admin)
├── CHANGELOG.md                         # 📝 Permanent historical changelog
├── AGENTS.md                            # 📜 Mandatory developer rules & non-negotiable directives
│
├── public_ads/                          # 🎬 DASHBOARDS SOURCE DIRECTORY
│   ├── index.html                       # 3️⃣ Dedicated Ads Monetization Portal (/ads) [UNTOUCHED]
│   └── miner/
│       └── index.html                   # 1️⃣ User Mining Mini App (/miner)
│
├── public_admin/                        # 🏢 ADMIN CONSOLES SOURCE DIRECTORY
│   ├── admin.html                       # 4️⃣ Executive Fleet Operations Console (/admin)
│   ├── user-admin.html                  # 2️⃣ User Bot Admin Console (/user-admin)
│   └── fleet_wallets_data.json          # 20-Account non-custodial wallet JSON registry
│
├── public/                              # 🌐 MIRROR ASSETS FOR EDGE WORKER PACKAGING
│   ├── index.html                       # Mirror of public_ads/miner/index.html
│   ├── admin.html                       # Mirror of public_admin/admin.html
│   ├── user-admin.html                  # Mirror of public_admin/user-admin.html
│   └── app/index.html                   # Mirror of public_ads/miner/index.html
│
├── deploy_both_cf_workers.py            # ⚡ Master Cloudflare Edge Worker bundle compiler & deployer
├── backup_manager.py                    # 🛡️ Disaster recovery backup pipeline (uploads to @myagyai)
├── restore.sh                           # 🚀 Standalone 1-click system restore bootstrapper
├── multichain_onchain_watcher.py        # 💎 Multi-chain on-chain vault balance watcher
├── daily_profit_reporter.py             # 📊 Daily 00:00 UTC profit & ledger reporting engine
├── mrg_turnstile_solver.py              # 🤖 Cloudflare Turnstile single-click solver
├── victors_sb_solver.py                 # 🤖 Victor's Company automated challenge solver
├── batch_atf_miner.py                   # 🤖 ATF Miner autonomous loop & math solver
├── audit_bots_and_sidetasks.py          # 🔍 Comprehensive 8-bot fleet audit suite
└── accounts.json                        # 🔒 20 Fleet Telethon session strings (isolated/gitignored)
```

---

> 💡 **Permanent Directive for All AI Agents**:
> When you are asked to inspect, enhance, or deploy anything in AAA AUTO, always consult this directory first. Keep this file updated whenever new features, routes, credentials, or dashboard mechanics are added. Maintain zero fake data, enforce zero ecosystem mixing, ensure zero phone load, and stream disaster recovery backups to `@myagyai`!
