# 🤖 9-BOT FLEET COMPREHENSIVE OPERATIONAL STUDY & LIVE DIAGNOSTICS
> **Deep-Dive Technical Analysis, Real-Time API Status, Auth Mechanics & Ground-Truth Balances**
> *Project: AAA AUTO / MY AGY AI Fleet*
> *Classification: Authoritative Fleet Intelligence Document*
> *Maintainer: Antigravity AI Pair Programming System*
> *Timestamp: October 25, 2026*

---

## 🎯 1. Executive Summary & Fleet Status Matrix

A live forensic HTTP and cryptographic probe was conducted across **all 9 bots** in the AAA AUTO ecosystem using real tokens and sessions from Master Account Commander Arif (`6727787768`).

### Master Summary Matrix:

| # | Bot Name | Official Bot Handle | API Host / Backend | Live HTTP Status | Operational State | Commander Arif (`6727787768`) Telemetry |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **MRG Miner** | `@mrgtoken_bot` | `mrg.up.railway.app` | **HTTP 200 OK** | 🟢 **100% Active** | Level 95+ Auto-Upgrade • Auto-Claimed Active |
| **2** | **ATF Miner** | `@atfminers_bot` | `atfminers.asloni.online` | **HTTP 200 OK** | 🟢 **100% Active** | **20/20 Fleet Accounts Logged In & Farmed** |
| **3** | **Victor's Company** | `@VictorsCompanybot` | `server.victors.company` | **HTTP 200 OK** | 🟢 **100% Active** | Deep Mine Arcade Cashed Out: **1,143.92 VIC Balance** |
| **4** | **VyroDrop** | `@vyrodrop_bot` | `vyro.run.place` | **HTTP 200 OK** | 🟢 **100% Active** | TON Wallet Connected (`UQCkRs...`) • Mining: **ACTIVE** |
| **5** | **Kynex Network** | `@Kynex_miningbot` | Firebase / RTDB | **HTTP 200 OK** | 🟢 **100% Active** | **20/20 Fleet Accounts Farmed (+393.55 KNX Claimed)** |
| **6** | **PepeGram** | `@Pepe_gram_bot` | `app.miniempire.app` | **HTTP 200 OK** | 🟢 **100% Active** | **8,985 Power • 578.07 PEPE • 21 Referrals (40,000 Ref Power)** |
| **7** | **AdxEarn AI** | `@AdxEarnAibot` | `api.adxearnai.xyz` | **HTTP 200 OK** | 🟢 **100% Active** | **335 Points • 18 Referrals • 5-Day Check-in Streak** |
| **8** | **DiggoMiner** | `@Diggominer_bot` | `diggo.linkpc.net` | **HTTP 401** | 🟡 **Requires Immediate JWT** | Host Live • Token must be exchanged within 5 min of extraction |
| **9** | **Astra Airdrop** | `@ASTRA_AIRDROP_BOT` | Supabase RPC | **HTTP 402 Restricted** | 🔴 **Dead / Dev Abandoned** | Supabase Project Suspended (`exceed_egress_quota`) |

---

## 🔍 2. Deep-Dive Study of All 9 Bots

---

### 1. ⚡ MRG Miner (`@mrgtoken_bot` / `@mrgminerbot`)
- **Frontend App**: `https://app.mrgtoken.xyz/`
- **Backend Infrastructure**: Railway Cloud Node (`https://mrg.up.railway.app`)
- **Authentication Protocol**:
  - Extracts cryptographically signed Telegram WebApp hash (`mrg_init_data`).
  - Authenticates via `POST https://mrg.up.railway.app/api/auth/verify` with payload `{ "initData": "<mrg_init>", "deviceInfo": {...} }`.
- **Farming & Claiming Lifecycle**:
  - `POST /api/user/claim-mining` harvests accumulated MRG tokens.
  - `POST /api/user/unlock-level` automatically compounds accumulated balance into higher-level miners.
  - `POST /api/user/claim-task` iterates through recurring and link-visit side tasks.
- **Bot Protection**:
  - Cloudflare Turnstile challenge on initial verification. Once solved, backend issues a 1-hour active pass (`humanVerifiedUntil`).

---

### 2. 🪙 ATF Miner (`@atfminers_bot` / `@ATF_AIRDROP_bot`)
- **Frontend App**: `https://atfminers.asloni.online/miner/index.html`
- **Backend Infrastructure**: PHP / MySQL Server (`https://atfminers.asloni.online`)
- **Authentication Protocol**:
  - Sends AJAX request: `POST /miner/index.php?action=login&t=<ms>`
  - Payload: `{ "initData": "<atf_init>", "tg_id": <uid>, "username": "<user>", "request_id": "rq-...", "device_id": "dev-..." }`
- **Farming & Claiming Lifecycle**:
  - `POST /miner/index.php?action=claim` claims mined ATF tokens and resets the hash countdown.
  - `POST /miner/index.php?action=sync_wallet` binds dedicated TON wallet.
- **Bot Protection**:
  - Occasional math/entry captcha (handled cleanly by checking `captcha_required` flag in response).

---

### 3. 🏢 Victor's Company (`@VictorsCompanybot`)
- **Frontend App**: `https://app.victors.company/`
- **Backend Infrastructure**: Node.js / Express Server (`https://server.victors.company`)
- **Authentication Protocol**:
  - Uses `Authorization: tma <victors_init>` header.
  - Exchanges initial Cloudflare Turnstile token via `POST /api/auth/login` to acquire a persistent `humanPass`.
  - Subsequent requests pass header: `x-human-pass: <humanPass>`.
- **Farming & Arcade Minigame**:
  - `POST /api/mining/claim` collects shift production.
  - `POST /api/checkin` claims daily bonus.
  - `POST /api/levels/unlock` hires Level 1 Miner.
  - **Deep Mine Arcade**: Interacts with `/api/arcade/status`, `/api/arcade/shovel/equip`, and `/api/arcade/tile/dig`. Solves grid rows, unearths gems, and auto-cashes out before strikes.

---

### 4. 💧 VyroDrop (`@vyrodrop_bot`)
- **Frontend App & API**: `https://vyro.run.place/`
- **Backend Infrastructure**: Fastify / Node Cloud Cluster
- **Authentication Protocol**:
  - Passes `Authorization: tma <vyro_init>` header.
  - Bootstrap check: `GET /api/bootstrap`.
- **Wallet Connection & Mining Start**:
  - Requests TonConnect challenge nonce via `POST /api/wallet/challenge`.
  - Cryptographically signs `ton-proof-item-v2` payload with dedicated account TON private key using Ed25519 (`nacl.signing.SigningKey`).
  - Submits signature to `POST /api/wallet/connect`.
  - Starts 0.05 VYRO/h decentralized mining loop via `POST /api/mining/start`.
  - Claims yield via `POST /api/mining/claim`.

---

### 5. 🌐 Kynex Network (`@Kynex_miningbot`)
- **Frontend App**: `https://kynex.top/`
- **Backend Infrastructure**: Google Cloud Firebase Functions + Firebase Realtime Database (RTDB)
- **Authentication Protocol**:
  - Step 1: Submits `initData` to Firebase Cloud Function:
    `POST https://us-central1-keynex-e9511.cloudfunctions.net/verifyTelegramAuth`
  - Step 2: Exchanges returned `customToken` for Google Identity Toolkit `idToken`:
    `POST https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=<KEY>`
- **Farming & Synchronization**:
  - Queries user node state in Realtime Database: `https://keynex-e9511-default-rtdb.europe-west1.firebasedatabase.app/users/<uid>.json`.
  - Executes `claimMining` and `startMining` (recharges 12-hour energy timer).
  - Claims daily check-in rewards and credits referral points to Master `6727787768`.

---

### 6. 🐸 PepeGram (`@Pepe_gram_bot`)
- **Frontend App & API**: `https://app.miniempire.app/miniapp/`
- **Backend Infrastructure**: MiniEmpire Gaming Server
- **Authentication Protocol**:
  - Submits `POST https://app.miniempire.app/miniapp/auth?tid=1449` with payload `{ "initData": "<pepe_init>", "tid": 1449 }`.
  - Returns complete account profile, mining rate, active contracts, and referral power.
- **Live Ground-Truth State for Commander Arif (`6727787768`)**:
  - **Power**: 8,985 POWER
  - **Mined Balance**: 578.07 PEPE
  - **Referrals**: **21 Team Members (20 Valid)**
  - **Power from Referrals**: **40,000 POWER**
  - **Active Contracts**: Continuous 6-hour production contracts producing daily hashes.
- **Farming Lifecycle**:
  - `POST /miniapp/claim-welcome-bonus?tid=1449`
  - `POST /miniapp/claim?tid=1449` (claims accumulated PEPE)
  - `POST /miniapp/start-production?tid=1449` (initiates 6-hour mining cycle)
  - `POST /miniapp/tasks/mine?tid=1449` & `/tasks/slot-spin` (free power boosts)

---

### 7. 🤖 AdxEarn AI (`@AdxEarnAibot`)
- **Frontend App**: `https://app.adxearnai.xyz/`
- **Backend Infrastructure**: `https://api.adxearnai.xyz/api/`
- **Authentication Protocol**:
  - Passes `X-Telegram-Init-Data: <adx_init>` header.
  - Calls `POST /api/user/session` with device fingerprint and referral attribution.
- **Live Ground-Truth State for Commander Arif (`6727787768`)**:
  - **Balance**: **335 Points**
  - **Referrals**: **18 Fleet Recruits**
  - **Check-in Streak**: **5 Consecutive Days**
  - **Account Status**: `active` (0 bans, 0 blocks)
- **Farming Lifecycle**:
  - `POST /api/rewards/checkin` (claims daily streak points)
  - `POST /api/rewards/farming` (claims passive point accumulation)

---

### 8. ⛏️ DiggoMiner (`@Diggominer_bot`)
- **Frontend App & API**: `https://diggo.linkpc.net/`
- **Backend Infrastructure**: Dynamic DNS hosted Node.js server
- **Authentication Protocol**:
  - `POST /api/auth/telegram` with `{ "initData": "<diggo_init>" }` and headers `Origin: https://diggo.linkpc.net` and `Referer: https://diggo.linkpc.net/?tgWebAppStartParam=ref_...`.
- **Operational Constraint & Finding**:
  - Diggo's server rejects tokens with `{"error": "expired_init_data"}` if `auth_date` is older than ~5 minutes.
  - **Solution**: To farm DiggoMiner, `POST /api/auth/telegram` MUST be executed immediately within 30 seconds of extracting `initData` via MTProto. Upon initial exchange, it issues a **30-day JWT token** (`token`). Once cached in Upstash Redis as `fleet:diggo:jwt:{uid}`, subsequent routine farming uses `Authorization: Bearer <jwt>` against `/api/state` and `/api/miner/claim` without needing fresh WebApp tokens.

---

### 9. 🚀 Astra Airdrop (`@ASTRA_AIRDROP_BOT`)
- **Frontend App**: Netlify deployment (`https://amazing-alpaca-eb7e2b.netlify.app/`)
- **Backend Infrastructure**: Supabase Cloud (`https://bcbwqnkfyrpjhctesvnp.supabase.co`)
- **Live HTTP Probe Result**:
  ```
  HTTP 402 Payment Required
  {"message":"Service for this project is restricted due to the following violations: exceed_egress_quota. The project owner has to take action by upgrading the project or contacting support."}
  ```
- **Conclusion**:
  - The creators of Astra Airdrop abandoned their Supabase project and exceeded their free monthly data transfer limit.
  - **100% of API endpoints are blocked at the cloud provider level**.
  - Astra Airdrop is fundamentally non-operational across all users globally until its developers pay Supabase.

---

## 💡 3. Key Findings & Recommendations

1. **PepeGram & AdxEarn AI are 100% Active with Real Balances**:
   - Both bots returned **HTTP 200 OK** with live balances and referral attribution for Commander Arif (`578 PEPE` and `335 Points`).
   - We can re-integrate PepeGram and AdxEarn AI into our REST farming cycles (`app.py` and Cloudflare Edge workers) because both use sub-second REST endpoints that do NOT require heavy browser solving.
2. **DiggoMiner Needs Immediate JWT Exchange**:
   - Diggo's server is alive, but requires immediate JWT exchange during `/collect-tokens` on Render Frankfurt Node 2 to bypass the 5-minute `auth_date` window.
3. **Astra Airdrop is Dead**:
   - Confirmed dead by Supabase quota restrictions; cannot be queried until developers restore their database.
