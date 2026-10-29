# 🏛️ AAA AUTO — Master Architecture & Dashboards Ground Truth

> **AUTHORITATIVE GROUND-TRUTH SYSTEM REFERENCE**:
> This document provides an exhaustive, bug-free, zero-fake specification of the entire AAA AUTO (MY AGY AI) system, its bot ecosystems, exact dashboard boundaries, and operational invariants.
> **Master Navigation Hub**: See [MASTER_SYSTEM_DIRECTORY.md](./MASTER_SYSTEM_DIRECTORY.md) for the universal directory and cheat sheet.
> **Rule of Thumb**: Whenever debugging, inspecting, or enhancing features, follow this guide to guarantee 100% authentic data, zero simulated mockups, and strict ecosystem separation.

---

## 🎯 1. Executive System Topology & Dual Bot Separation

The architecture is divided into two 100% strictly isolated ecosystems (Rule 1 & 7: "Zero Ecosystem Mixing"):

```
                                  ┌──────────────────────────────────────────────────┐
                                  │             AAA AUTO MULTI-CLOUD ENGINE          │
                                  └─────────┬──────────────────────────────┬─────────┘
                                            │                              │
                     ┌──────────────────────┴────────┐    ┌────────────────┴──────────────────────┐
                     │                               │    │                                       │
                     ▼                               ▼    ▼                                       ▼
       ADMIN BOT (@myagyai, ID 8858823950)                      USER BOT (@AAAPREMIUMAPPSbot, ID 8167732110)
       ------------------------------------                     --------------------------------------------
       • Purpose: Executive fleet operations, 20 MTProto        • Purpose: Public multi-pool mining, points
         accounts, cloud node health, disaster recovery.          economy, daily check-ins, rewarded video ads.
       • Tokens: ADMIN_BOT_TOKEN / REPORT_BOT_TOKEN.            • Tokens: USER_BOT_TOKEN.
       • Private Channels: Vault (@myagyai), Payouts,           • Public Channels: Community Hub (@AAAAutoMiner),
         Supergroup (-1003973231307).                             Announcements (@AAAAUTOMINING), Activity.
       • Upstash Namespace: fleet:*                             • Upstash Namespace: ub_* (ub_user:*, ub_wallet:*)
       • Dedicated Dashboard: Executive Console (/admin)        • Dedicated Dashboards: User Miner (/miner),
                                                                  User Bot Admin (/user-admin), Ads Portal (/ads)
```

---

## 🖥️ 2. The Complete 4-Dashboard Roster (Roles, URLs & Files)

### 📊 Summary Table

| Dashboard # | Name & Purpose | Source File | Live Routes & URLs | Persistent TMA Menu Button | Audience |
|---|---|---|---|---|---|
| **Dashboard 1** | **User Mining Mini App**<br>Autonomous cloud mining interface, points, slots, 9 pools, non-custodial wallets. | [`public_ads/miner/index.html`](./public_ads/miner/index.html)<br>*(Mirrors: `public/index.html`, `public/app/index.html`)* | `https://restore-agy.agorameet.workers.dev/miner`<br>`https://agy-henna.vercel.app/miner` | Opened via `/start`, `/miner`, or chat buttons (NOT persistent menu) | Public End-Users |
| **Dashboard 2** | **User Bot Admin Console**<br>Management console for Commander Arif to manage community miners, points & ad metrics. | [`public_admin/user-admin.html`](./public_admin/user-admin.html)<br>*(Mirror: `public/user-admin.html`)* | `https://restore-agy.agorameet.workers.dev/user-admin`<br>`https://agy-aaa000.vercel.app/user-admin` | Admin PIN Gate (PIN: `2743` or `ADMIN_PIN`) | System Administrator (Commander Arif) |
| **Dashboard 3** | **Dedicated Ads Portal**<br>Rewarded video ad player with multi-network waterfall (HilltopAds, Clickadu, GigaPub). | [`public_ads/index.html`](./public_ads/index.html)<br>*(Mirrors: `public/ad/index.html`, `public/app/ad/index.html`)* | `https://atf-miner-app.pages.dev/`<br>`https://restore-agy.agorameet.workers.dev/ads` | **`🎬 Watch Ads`**<br>*(Bound as primary User Bot Chat Menu Button)* | Public End-Users (Monetization) |
| **Dashboard 4** | **Executive Fleet Dashboard**<br>Full fleet control: 20 MTProto accounts, 9 farming bots, multi-cloud node health. | [`public_admin/admin.html`](./public_admin/admin.html)<br>*(Mirror: `public/admin.html`)* | `https://agy-aaa000.vercel.app/admin`<br>`https://restore-agy.agorameet.workers.dev/admin` | **`👑 Fleet Dashboard`**<br>*(Bound as primary Admin Bot Chat Menu Button)* | Executive Fleet Operators |

---

## 🔍 3. In-Depth Dashboard Specifications

### 1️⃣ Dashboard 1: User Mining Mini App (`/miner`)
- **Primary Source**: [`public_ads/miner/index.html`](./public_ads/miner/index.html)
- **Embedded As**: `__USER_MINI_APP_HTML_JSON__` in `deploy_both_cf_workers.py`.
- **Core Authentic Features (Zero Fake Data)**:
  - **Real Points & Runway**: Real points balance (`stat-points`) and days of runway calculated as `Math.floor(points / daily_cost)` from `/api/user/profile`.
  - **Account Slots Tracking**: Real slots consumed vs allowed (`accs.length / totalSlots`) based on base slots + bonus ad slots.
  - **Daily Streak Cooldown**: 24h elapsed cooldown timer with dynamic button label: `Claim +100` or `Claimed (18h 40m)`.
  - **1-Click Multi-Pool Cloud Harvest**: Calls `/api/farm/all` to concurrently trigger cloud farming across all connected accounts.
  - **9 Verified Mining Protocols**: Individual cards displaying genuine connected accounts count (`mrgC`, `atfC`, `victorsC`, etc.).
  - **Non-Custodial Multi-Chain Wallets**: Real 5-chain non-custodial addresses (TON, EVM, TRON, Solana) generated deterministically and retrievable via `/wallets`.
  - **Real Crypto Market Rates**: Real Binance ticker rates (`💎 TON: $1.62 • 🟡 BNB: $750`) fetched directly from `/api/rates`.
  - **Zero-Asset Web Audio API**: Authentic synthesized UI audio (`playSound('click')`, `playSound('harvest')`, `playSound('reward')`).
  - **Silent 30-Second Background Sync**: Keeps balances and accounts updated automatically without manual page reloads.

### 2️⃣ Dashboard 2: User Bot Admin Console (`/user-admin`)
- **Primary Source**: [`public_admin/user-admin.html`](./public_admin/user-admin.html)
- **Embedded As**: `__USER_ADMIN_DASHBOARD_HTML_JSON__` in `deploy_both_cf_workers.py`.
- **Core Authentic Features**:
  - **Community Miners Roster**: Real-time listing of all registered users from Upstash Redis `ub_registered_users` and Turso LibSQL.
  - **Search & Multi-Filter Chips**: Filter by `All`, `Connected Accounts`, `With Wallets`, `Custom Payout`, `VIP Passes`, `Active`, `Paused`, `⚠️ Low Pts`, and `🚫 Banned`.
  - **Rewarded Ads Monetization Card**: Real metrics tracking total community rewarded ads watched, points distributed, active watchers, and 1-click link to the Ads Portal.
  - **Direct Telegram DM Action**: `DM ↗` link (`https://t.me/<username>`) on user cards to instantly reach users requiring session refresh or points top-ups.
  - **Points Grant & Deduction Engine**: Modal to credit or deduct points with preset chips (`+50`, `+100`, `+500`, `+1000`) or custom amounts.
  - **Broadcast Center**: Dispatch custom messages or pre-configured templates to specific cohorts (`no_account`, `revoked`, `all`, `active`) via `@AAAPREMIUMAPPSbot`.
  - **Autonomous Daily Deductions Sweep**: Trigger manual or automated 100 Pts/day sweeps with detailed deduction audit.

### 3️⃣ Dashboard 3: Dedicated Ads Portal (`/ads`)
- **Primary Source**: [`public_ads/index.html`](./public_ads/index.html)
- **Embedded As**: `__USER_ADS_HTML_JSON__` in `deploy_both_cf_workers.py`.
- **Core Authentic Features**:
  - **Waterfall Mediation Engine**: HilltopAds VAST 3.0, Clickadu, GigaPub, and Monetag SDKs.
  - **Persistent Menu Button**: The Telegram bot bottom-left menu button of `@AAAPREMIUMAPPSbot` is explicitly bound to `🎬 Watch Ads` pointing directly to this portal.
  - **Ad Credit Webhook**: Upon ad completion, calls `/api/user/claim-ad` with cryptographic verification to award `+20 Pts` to the user's profile.
  - **Preservation Invariant**: **NEVER modify or corrupt this portal with unrelated dashboard code**.

### 4️⃣ Dashboard 4: Executive Fleet Operations Console (`/admin`)
- **Primary Source**: [`public_admin/admin.html`](./public_admin/admin.html)
- **Embedded As**: `__ADMIN_DASHBOARD_HTML_JSON__` in `deploy_both_cf_workers.py`.
- **Core Authentic Features**:
  - **20 MTProto Accounts Live Telemetry**: Session status (`ACTIVE_ONLINE`, `NEEDS_CODE`, `REVOKED`) across all 20 fleet accounts.
  - **9 Farming Pools Orchestration**: Real-time stats across MRG, ATF, Victor's Company, VyroDrop, Kynex Network, Diggo, AdxEarn, Astra, PepeGram.
  - **Multi-Cloud Node Health**: Monitors Render Standby Node 2, Cloudflare Edge Mesh (5 nodes), and Deno Deploy.
  - **Disaster Recovery Controls**: 1-click trigger to stream encrypted backup archives to `@myagyai`.

---

## 🔐 4. Master Authentication, Lock & Biometric Passkey System

Both administrative dashboards (`/admin` and `/user-admin`) are fortified with an identical high-security cyber-fintech authentication gate:

### 1. 4-Digit Numeric PIN Pad (`2743`)
- **Standardized PIN**: `2743` (Commander Arif's master PIN).
- **Auto-Submission**: 4 glowing neon dots (`[0, 1, 2, 3]`) illuminate sequentially on keypad tap. Upon entering the 4th digit, the PIN is validated and submitted automatically.
- **Physical Keyboard Support**: Desktop operators can type `0-9` on their keyboard, `Backspace` to delete, and `Escape` to clear.
- **Dual Mode Toggle**: Operators can switch seamlessly between `"Switch to 4-Digit PIN Pad 🔢"` and `"Or use master password 🔏"`.

### 2. WebAuthn Biometric Passkeys (Fingerprints / Touch ID / Face ID)
- **Hardware-Bound Security**: FIDO2 asymmetric challenge-response via `/api/admin/auth/passkey-challenge` and `/api/admin/auth/verify-passkey`.
- **Multi-Device Credential Array**: Stored in Upstash Redis `admin_passkeys:6727787768` (Set) and Supabase `admin_auth`. Multiple phones, laptops, and desktop passkeys can be enrolled concurrently without overwriting existing devices.
- **Cache-Bypass**: Queries for `admin_passkey` and `admin_sess:` bypass the 15-minute worker cache (`maxAgeMs = 0`), ensuring immediate login usability across devices.
- **Header Status & Enrollment Prompt**: Active passkey status dot (🟢 active / 🟡 unlinked) on the header `👆 Passkey` button, with an automatic first-login banner prompt.

### 3. Inactivity Auto-Lock & 1-Tap Lock
- **1-Tap Lock Button (`🔒 Lock`)**: Present in both dashboard headers. Locks the interface immediately without clearing session credentials.
- **15-Minute Inactivity Auto-Lock**: Automatically locks the console after 15 minutes of idle time (`mousemove`, `keydown`, `touchstart`).
- **5-Minute Background Tab Auto-Lock**: Automatically locks if the tab is minimized or switched away for > 5 minutes via the Page Visibility API (`document.hidden`).
- **Dedicated Logout Button (`🚪 Logout`)**: Completely invalidates session tokens in Cloudflare Edge and local storage.

### 4. Zero-Asset Audio & Telegram Haptics
- **Web Audio API**: Synthetic audio oscillators (`playSound('click')`, `playSound('success')`, `playSound('error')`) provide immediate tactile feedback with 0 external network requests.
- **Haptics**: Leverages `Telegram.WebApp.HapticFeedback` for crisp mobile feedback.

---

## 🚫 5. "Zero Fake Things" Policy & Prohibited Patterns

To ensure complete production integrity, the following patterns are **STRICTLY PROHIBITED**:

1. **NO Hardcoded / Fake Tickers**:
   - ❌ **Prohibited**: Hardcoding random satoshi increments (e.g. `accumulatedSatoshis = 142850` with `Math.random() * 25`).
   - ✅ **Required**: Use genuine profile points and balances fetched from `/api/user/profile`.
2. **NO Fake Hashrate Claims**:
   - ❌ **Prohibited**: Fabricating static or random gigahash metrics (e.g. `128.4 GH/s`).
   - ✅ **Required**: Display authentic connected account counts and verified pool protocol statuses.
3. **NO Menu Button Hijacking**:
   - ❌ **Prohibited**: Overwriting the User Bot's `🎬 Watch Ads` menu button to point to `/miner` on `/start`.
   - ✅ **Required**: The User Bot chat menu button MUST remain permanently set to `🎬 Watch Ads` (`https://atf-miner-app.pages.dev/`).
4. **NO Ecosystem Cross-Contamination**:
   - ❌ **Prohibited**: Displaying fleet MTProto sessions, private keys, or admin commands inside User Bot dashboards.
   - ✅ **Required**: Keep `fleet:*` and `ub_*` completely separated in both code and storage.

---

## 🐞 6. Master Bug-Hunting & Sanity Verification Checklist

Execute this checklist whenever auditing the system or preparing for deployment:

### Step 1: Verify User Bot Menu Button
```bash
python3 -c "
import os, requests
from dotenv import load_dotenv
load_dotenv()
u_tok = os.getenv('USER_BOT_TOKEN')
r = requests.get(f'https://api.telegram.org/bot{u_tok}/getChatMenuButton')
data = r.json()
print('ChatMenuButton:', data)
assert data.get('result', {}).get('text') == '🎬 Watch Ads'
assert 'atf-miner-app.pages.dev' in data.get('result', {}).get('web_app', {}).get('url', '')
print('✅ Menu Button verified pointing to Ads Portal!')
"
```

### Step 2: Verify All 4 Live Dashboard Endpoints (HTTP 200)
```bash
# Dashboard 1: User Miner Dashboard
curl -s -o /dev/null -w "%{http_code}\n" "https://restore-agy.agorameet.workers.dev/miner"
# Dashboard 2: User Bot Admin Dashboard
curl -s -o /dev/null -w "%{http_code}\n" "https://restore-agy.agorameet.workers.dev/user-admin"
# Dashboard 3: Dedicated Ads Portal
curl -s -o /dev/null -w "%{http_code}\n" "https://restore-agy.agorameet.workers.dev/ads"
# Dashboard 4: Executive Fleet Dashboard
curl -s -o /dev/null -w "%{http_code}\n" "https://restore-agy.agorameet.workers.dev/admin"
```
*Expected Result*: All 4 return `200` (or 302 redirect for `/ads` to Vercel).

### Step 3: Verify Zero Fake Tickers in Miner Dashboard
```bash
python3 -c "
with open('public_ads/miner/index.html') as f:
    c = f.read()
assert 'startYieldTicker' not in c, 'Found prohibited fake yield ticker!'
assert 'accumulatedSatoshis' not in c, 'Found prohibited fake satoshis!'
assert 'Dual Currency Switcher' not in c, 'Found prohibited currency switcher!'
print('✅ Zero fake things in miner dashboard verified!')
"
```

### Step 4: Verify Mirror File Synchronization
```bash
diff public_ads/miner/index.html public/index.html
diff public_ads/miner/index.html public/app/index.html
diff public_admin/user-admin.html public/user-admin.html
```
*Expected Result*: 0 differences between master source and mirrors.

### Step 5: Verify Phone Cleanliness (Rule 4)
```bash
pgrep -f "python.*(bot|worker|farm|solve)" || echo "✅ Zero rogue bot processes on phone!"
```

### Step 6: Verify Telegram Backup Vault (Rule 5)
```bash
python3 backup_manager.py
```
*Expected Result*: `✅ Backup uploaded to https://t.me/myagyai and saved locally!`

---

## 📝 7. Key Code Locations & Handover Rules

- **Master System Directory**: [`MASTER_SYSTEM_DIRECTORY.md`](./MASTER_SYSTEM_DIRECTORY.md) (All-in-one index & quick reference).
- **Cloudflare Edge Worker Bundle**: [`deploy_both_cf_workers.py`](./deploy_both_cf_workers.py) (15,500+ lines).
- **User Dashboard Source**: [`public_ads/miner/index.html`](./public_ads/miner/index.html).
- **User Bot Admin Dashboard Source**: [`public_admin/user-admin.html`](./public_admin/user-admin.html).
- **Ads Portal Source**: [`public_ads/index.html`](./public_ads/index.html).
- **Executive Fleet Dashboard Source**: [`public_admin/admin.html`](./public_admin/admin.html).
- **Master Session Bridge**: [`SESSION_BRIDGE.md`](./SESSION_BRIDGE.md).
- **System Bible**: [`PROJECT_BIBLE.md`](./PROJECT_BIBLE.md).
- **Audit Changelog**: [`CHANGELOG.md`](./CHANGELOG.md).

> 💡 **Permanent Directive**: Whenever deploying changes, push simultaneously to `origin` (`AAA0002/ATL`) and `standby_repo` (`AAA0002/my-agy-fleet-standby`), stream a disaster recovery archive to `@myagyai`, and update `CHANGELOG.md`, `PROJECT_BIBLE.md`, and `SESSION_BRIDGE.md`.
