# ⚡ AUTONOMOUS CLOUD SOLVER & MULTI-BOT FARMING ARCHITECTURE
> **Authoritative Specification: Decoupled Turnstile Solving, High-Speed REST Harvesting & Multi-Cloud Mesh Execution**
> *Project: AAA AUTO / MY AGY AI Fleet*
> *Classification: Mission-Critical Living Technical Documentation*
> *Maintainer: Antigravity AI Pair Programming System*
> *Last Updated: October 25, 2026*

---

## 🎯 1. Executive Summary & Purpose

The **Autonomous Cloud Solver & Multi-Bot Farming Engine** is the execution backbone of the **AAA AUTO** fleet. It manages **20 authorized Telegram accounts** (1 Master Account + 19 Worker Accounts) farming in parallel across the **5 active legitimate Mini App bots** with 100% cloud autonomy, 0 phone resource utilization (Zero Phone Load Directive on Samsung Galaxy A30), and zero fake reporting (Ground-Truth 5-Bot Integrity).

### Architectural Breakthrough: Two-Phase Decoupled Architecture
Historically, running browser automation across 20 accounts sequentially introduced massive latency (35–45 minutes per run), risking runner timeouts, proxy exhaustion, and thread starvation. The modernized architecture implements a **high-speed decoupled two-phase solver model**:

1. **Phase 1: Rapid REST Pre-Flight & Instant Multi-Bot Harvesting**:
   Audits all 20 accounts across Victor's Company, VyroDrop, ATF Miner, and MRG Miner via sub-second REST endpoints. Accounts with active passes (`victors:pass:{uid}`, connected Vyro wallets, active ATF sessions, active MRG passes) have their rewards, checkins, shift claims, and tasks processed instantly via REST in **< 30 seconds total** without launching a browser.
2. **Phase 2: Targeted Browser Solving**:
   Decouples Chromium from the main loop; launches Patchright Chromium stealth strictly for the subset of accounts that genuinely require Turnstile passes or onboarding challenges. If zero accounts need solving, the browser is completely bypassed.
3. **Phase 3: Deep Mine Arcade Expeditions**:
   Automates Victor's Company Deep Mine arcade minigame (`victors_arcade_solver.py`) over asynchronous HTTP sessions for all active accounts.
4. **Phase 4: Kynex Network Mining & RTDB Synchronization**:
   Executes Firebase Cloud Functions callable auth (`verifyTelegramAuth`) and Identity Toolkit token exchange for Kynex Network (`kynex_miner.py`).

---

## 🗺️ 2. System Architecture & Component Diagram

```mermaid
flowchart TD
    subgraph Multi_Cloud_Runner ["Cloud Execution Layer"]
        GHA["GitHub Actions Runner<br/>(cloud-fleet-solver)<br/>Unlimited Free Minutes"]
        Render["Render Frankfurt Node 2<br/>FastAPI Server /app.py<br/>/collect-tokens"]
        CF["Cloudflare Edge Mesh<br/>(5 Edge Worker Nodes)<br/>30-Min Cron Triggers"]
    end

    subgraph Central_State ["State Bus & Pass Relay"]
        Upstash[("Upstash Redis<br/>fleet:tokens:{uid}<br/>victors:pass:{uid}<br/>mrg:pass:{uid}<br/>vyro:pass:{uid}")]
        KV[("Cloudflare KV<br/>miniapp_tokens")]
    end

    subgraph Two_Phase_Engine ["mrg_turnstile_solver.py"]
        P1["Phase 1: REST Pre-Flight<br/>• Victor's cached pass audit<br/>• VyroDrop bootstrap check<br/>• ATF session verification<br/>• Instant reward harvest"]
        P2{"Browser Needed?"}
        P2_Yes["Phase 2: Targeted Browser<br/>• Patchright Stealth<br/>• Android Client Hints<br/>• Hardware CDP Mouse Clicks<br/>• Callback interception"]
        P2_No["Bypass Chromium<br/>(Zero Browser Overhead)"]
        P3["Phase 3: Victor's Arcade<br/>• Deep Mine Expeditions<br/>• Shift claims"]
        P4["Phase 4: Kynex Miner<br/>• Firebase callable auth<br/>• RTDB sync & energy claim"]
    end

    subgraph Target_Bots ["Strict Ground-Truth 5 Bots"]
        B1["⚡ MRG Miner (@mrgtoken_bot)"]
        B2["🪙 ATF Miner (@atfminers_bot)"]
        B3["🏢 Victor's Company (@VictorsCompanybot)"]
        B4["💧 VyroDrop (@vyrodrop_bot)"]
        B5["🌐 Kynex Network (@Kynex_miningbot)"]
    end

    GHA --> Two_Phase_Engine
    Render -->|"Sync fresh tokens"| Central_State
    CF -->|"Read passes & farm"| Central_State
    Two_Phase_Engine -->|"Read/Write Passes"| Upstash
    Two_Phase_Engine --> P1
    P1 --> P2
    P2 -->|Yes| P2_Yes
    P2 -->|No| P2_No
    P2_Yes --> P3
    P2_No --> P3
    P3 --> P4
    P1 --> Target_Bots
    P2_Yes --> Target_Bots
    P3 --> B3
    P4 --> B5
```

---

## ⚡ 3. The 4 Phases of Execution

### Phase 1: Rapid REST Pre-Flight & Instant Harvesting
Before spawning any browser instance or Xvfb display, the runner evaluates the live state of all 20 accounts:

- **Victor's Company (`check_and_farm_victors_rest`)**:
  - Queries Upstash Redis for `victors:pass:{uid}`.
  - Tests pass validity via `GET https://server.victors.company/api/me` with `x-human-pass` header.
  - If valid (HTTP 200), claims mining (`/mining/claim`), daily check-in (`/checkin`), tutorial completion (`/me/tutorial`), level 1 miner unlock (`/levels/unlock`), and referral commission.
  - Returns `(handled=True, needs_browser=False)`.
- **VyroDrop (`check_and_farm_vyro_rest`)**:
  - Queries `GET https://vyro.run.place/api/bootstrap`.
  - If wallet is already connected, claims accumulated mining rewards (`/mining/claim`), starts mining if idle (`/mining/start`), and claims referral rewards.
  - If wallet connection challenge does not require Turnstile, creates TonConnect 2.0 cryptographic proof using dedicated TON seed and connects via REST.
  - Returns `(handled=True, needs_browser=False)`.
- **ATF Miner (`check_and_farm_atf_rest`)**:
  - Sends login probe to `https://atfminers.asloni.online/miner/index.php?action=login`.
  - If HTTP 200 without `entry_captcha_required`, auto-claims mining yield via `action=claim`.
  - Returns `(handled=True, needs_browser=False)`.
- **MRG Miner (`check_account_status`)**:
  - Queries `POST https://mrg.up.railway.app/api/user/status`.
  - Reads `humanVerifiedUntil` timestamp. If active, queues for direct REST claiming in Phase 3.

### Phase 2: Targeted Stealth Browser Solving (Patchright + Xvfb)
Only accounts whose tokens returned `needs_browser_solve = True` enter Phase 2.
Accounts are prioritized so that **Master Account (`6727787768`) is always solved first**.

#### Anti-Fingerprinting Stealth Measures:
1. **Linux armv8l Platform Override**: Headless Linux runners on Azure/GitHub Actions present `navigator.platform == 'Linux x86_64'`, while mobile User-Agents claim Android. Cloudflare Turnstile flags this discrepancy as a bot signal. The solver injects:
   ```javascript
   Object.defineProperty(navigator, 'platform', { get: () => 'Linux armv8l' });
   Object.defineProperty(navigator, 'userAgentData', {
       get: () => ({
           brands: [{ brand: 'Chromium', version: '130' }, { brand: 'Google Chrome', version: '130' }],
           mobile: true,
           platform: 'Android'
       })
   });
   ```
2. **Explicit WebApp Query Parameters**: Injects matching `tgWebAppPlatform=android&tgWebAppVersion=8.0` parameters into URL hashes and session storage.
3. **Turnstile Hooking**: Overrides `window.turnstile.render` to capture the resulting token immediately upon resolution, bypassing DOM polling delays.
4. **Hardware CDP Mouse Clicks**: Calculates exact bounding box coordinates of the Cloudflare challenge iframe (`box["x"] + 32.0`, `box["y"] + height / 2.0`) and simulates natural human curve mouse movements (`steps=6` to `steps=8`).
5. **Pass Persistence**: Saves acquired tokens to Redis (`victors:pass:{uid}`, `mrg:pass:{uid}`, `vyro:pass:{uid}`) so subsequent runs reuse active passes via REST.

### Phase 3: Victor's Company Arcade Expeditions (`victors_arcade_solver.py`)
For all accounts with verified passes:
- Queries active arcade status: `GET https://server.victors.company/api/arcade/status`.
- Automatically solves and dispatches **Deep Mine Arcade minigame expeditions**.
- Claims game rewards, compounding points into account balance.

### Phase 4: Kynex Network Auto-Farming (`kynex_miner.py`)
For all accounts with `kynex_init_data`:
- Step 1: Submits `initData` to `https://us-central1-keynex-e9511.cloudfunctions.net/verifyTelegramAuth`.
- Step 2: Exchanges returned `customToken` for a Google Identity Toolkit `idToken` via `https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken`.
- Step 3: Synchronizes Realtime Database (`keynex-e9511-default-rtdb.europe-west1.firebasedatabase.app`), claims mining cycle (`claimMining`), restarts mining node (`startMining`), and claims daily check-in.

---

## 🎯 4. Ground-Truth 5-Bot Operational Specifications

| Bot Name | Official Handle | Mini App API Host | Key Actions & Endpoints | Pass / Session Key |
| :--- | :--- | :--- | :--- | :--- |
| **MRG Miner** | `@mrgtoken_bot` | `mrg.up.railway.app` | `/api/user/status`<br>`/api/user/claim-reward`<br>`/api/user/verify-human`<br>`/api/user/unlock-level` | `mrg:pass:{uid}`<br>(1h Turnstile pass) |
| **ATF Miner** | `@atfminers_bot` | `atfminers.asloni.online` | `/miner/index.php?action=login`<br>`/miner/index.php?action=claim`<br>`/miner/index.php?action=sync_wallet` | `fleet:last_farm:atf:{uid}` |
| **Victor's Company** | `@VictorsCompanybot` | `server.victors.company` | `/api/auth/login`<br>`/api/me`<br>`/api/mining/claim`<br>`/api/tasks/claim`<br>`/api/arcade/status` | `victors:pass:{uid}`<br>(Persistent humanPass) |
| **VyroDrop** | `@vyrodrop_bot` | `vyro.run.place` | `/api/bootstrap`<br>`/api/wallet/challenge`<br>`/api/wallet/connect`<br>`/api/mining/start`<br>`/api/mining/claim` | `vyro:pass:{uid}`<br>(TonConnect session) |
| **Kynex Network** | `@Kynex_miningbot` | `us-central1-keynex-e9511.cloudfunctions.net` | `/verifyTelegramAuth`<br>`signInWithCustomToken`<br>RTDB profile sync | `fleet:last_farm:kynex:{uid}` |

### Legacy Purge List (Zero Querying Policy)
The following defunct or scam bots are **PERMANENTLY PURGED** from code, queries, and reports:
- ❌ **DiggoMiner** (`@Diggominer_bot` / `diggo.linkpc.net`) — Defunct / dead backend.
- ❌ **Astra Airdrop** (`@ASTRA_AIRDROP_BOT` / Netlify) — Defunct / dead Supabase backend.
- ❌ **PepeGram** (`@Pepe_gram_bot`) — Defunct meme bot.
- ❌ **AdxEarn AI** (`@AdxEarnAibot`) — Defunct / offline.
- ❌ **LeafEarn** (`@LeafEarnBot`) — Defunct.
- ❌ **PumpkinEarn** (`@PumpkinEarnBot`) — Defunct.

---

## 🌐 5. Multi-Repository Architecture & Cloud Runner Topology

### Repository Boundary Model
1. **`AAA0002/ATL` (Private Master)**:
   - Contains core infrastructure, full source code, private wallets, configuration registries, and internal deployment tools.
   - Strictly 100% PRIVATE. Never made public.
2. **`AAA0002/my-agy-fleet-standby` (Private Standby)**:
   - Full mirrored disaster recovery clone of `ATL`.
   - Synchronized automatically on every commit.
3. **`AAA0002/cloud-fleet-solver` (Public Runner)**:
   - Dedicated headless Patchright Chromium task runner.
   - **Zero Plaintext Secrets**: Contains ZERO sessions, zero private keys, and zero account mnemonics.
   - Public repository status unlocks **unlimited free GitHub Actions minutes**.
   - All runtime credentials are provided via GitHub Encrypted Secrets (`secrets.UPSTASH_TOKEN`, etc.).
   - Executes on a **6-hour cron schedule** (`0 */6 * * *`).

### Multi-Cloud Execution Roles
- **Render Frankfurt Node 2 (`my-agy-fleet-standby-node2.onrender.com`)**:
  - Primary cloud server running `app.py`.
  - Executes `/collect-tokens` to extract fresh WebApp hashes from Telethon sessions without phone load.
- **Render Oregon Node 3 (`my-agy-fleet-standby-node3.onrender.com`)**:
  - Standby failover node.
- **Cloudflare Edge Mesh (`restore-agy.*.workers.dev`)**:
  - 5 distributed edge workers running cron farming triggers every 30 minutes.
  - Consumes active passes stored in Upstash Redis to claim rewards.

---

## 🔒 6. Token Lifecycle & Autonomous Failover Protocol

```mermaid
stateDiagram-v2
    [*] --> FreshTokens : Render Node 2 /collect-tokens
    FreshTokens --> ActiveFarming : Age < 12 Hours
    ActiveFarming --> WarningThreshold : Age >= 12 Hours
    WarningThreshold --> AutonomousFailover : Council detects stale tokens
    AutonomousFailover --> RenderCollection : Trigger /collect-tokens on Frankfurt Node 2
    RenderCollection --> FreshTokens : Redis & KV updated
    WarningThreshold --> Expired : Age >= 24 Hours (Crypto Signature Invalid)
    Expired --> EmergencyAlert : Telegram Vault Alert
```

1. **Cryptographic Validity**: Telegram WebApp `initData` is signed using HMAC-SHA256 with the bot token. It includes an `auth_date` timestamp. Most bot backends reject tokens with `auth_date` older than 24 hours.
2. **12-Hour Autonomous Failover**: `autonomous_cloud_agent.py` monitors token age via Redis key `fleet:tokens_updated_at`. When age exceeds 12 hours, the Ari AI Council automatically triggers `/collect-tokens` on Render Node 2 before tokens expire.
3. **Emergency Fallback**: If Node 2 Frankfurt fails to respond within 45 seconds, the system automatically falls back to Node 3 Oregon.

---

## 🛠️ 7. Operational Runbook & Maintenance

### Triggering Manual Cloud Farm Cycle via GitHub Actions
```bash
gh workflow run turnstile_solver.yml --repo AAA0002/cloud-fleet-solver
```

### Checking Active Cloud Runner Execution
```bash
gh run list --repo AAA0002/cloud-fleet-solver --limit 5
gh run view <RUN_ID> --repo AAA0002/cloud-fleet-solver --log
```

### Triggering Cloud Token Refresh on Render Node 2
```bash
curl -X POST "https://my-agy-fleet-standby-node2.onrender.com/collect-tokens" \
  -H "Authorization: Bearer agy_cf_secret_7d36994e_2026" \
  -H "Content-Type: application/json" \
  -d '{"source": "ManualTrigger"}'
```

### Mandatory Disaster Recovery Backup (Before & After Changes)
```bash
python3 backup_manager.py
```
*Always verify delivery to Telegram Vault `@myagyai` (`-1004453515167`).*

---

## 📋 8. Audit & Resolution History

| Issue Detected | Root Cause | Architectural Resolution |
| :--- | :--- | :--- |
| **Victor's Arcade Crash** | Missing `import aiohttp` in `mrg_turnstile_solver.py` | Added top-level `import aiohttp` |
| **Turnstile HTTP 403 on Azure** | Platform mismatch (`Linux x86_64` vs Android UA) | Injected matching `navigator.platform = 'Linux armv8l'` client hints |
| **Long Runner Duration (35+ min)** | Sequential Chromium launch across 20 accounts | Engineered Phase 1 REST pre-flight; Chromium launched strictly for passless accounts |
| **Proxy 402 Payment Required** | Webshare proxy bandwidth exhausted | Added `USE_BROWSER_PROXY: "0"` fallback on cloud runners |
| **Dead Bot Lag in Token Extractor** | `app.py` querying Diggo, Astra, PepeGram, AdxEarn | Purged dead bot routines from `extract_tokens_with_client` |
| **Referrals Never Bound Bug** | `ALL_10_BOT_KEYS` checked defunct bots | Aligned `ALL_10_BOT_KEYS` strictly to the 5 active legitimate bots |
| **Double-Encoded JSON in Redis** | `json=json.dumps(payload)` in `autonomous_cloud_agent.py` | Changed to `data=json.dumps(payload)` with Content-Type header |
