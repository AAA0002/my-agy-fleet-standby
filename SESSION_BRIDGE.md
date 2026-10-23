# 🌉 MASTER SESSION BRIDGE — CONTINUITY & CONTEXT HANDOVER

> **FOR NEW AI SESSIONS (ANTIGRAVITY, GEMINI, CLAUDE, GPT)**:
> This document is the master memory bridge for the **AAA AUTO** project.
> Read this document completely to achieve 100% full context, architectural rules, past actions, and active priorities instantly without any token bloat or loss of memory.
> **ALWAYS REMEMBER**: When building or modifying features, you MUST update `SESSION_BRIDGE.md`, `PROJECT_BIBLE.md`, and `CHANGELOG.md`.

---

## 🎯 1. Executive Identity & System Purpose

* **Project**: **AAA AUTO** (also known as **MY AGY AI Fleet**).
* **Workspace**: `/root/workspace` (PRoot / Phone) & `/data/workspace/AAA_AUTO` (Cloud VM).
* **Git Repository**: `AAA0002/ATL` (clean HTTPS remotes: `origin` and `standby_repo`).
* **Architecture**: 100% Cloud-First Autonomous Telegram Mini-App Mining & Multi-Chain Wallet Fleet.
* **Accounts**: **19 Telegram Accounts** (1 Master Account + 17 Static Worker Accounts + 1 Newly Onboarded Account #19 Adil H) farming in parallel.
* **Master System Memory Core**: See [FLEET_MEMORY_CORE.md](./FLEET_MEMORY_CORE.md) for complete system memory, account roster, and operational invariants.
* **5 Active Legitimate Fleet Bots**:
  1. **MRG Miner** (`@mrg_miner_bot`) — Cloudflare Turnstile Solver, Level 95+ Auto-Upgrade & auto-claim.
  2. **ATF Miner** (`@atf_miner_bot`) — Cloud hash compounding, balance tracking, automatic claim loop.
  3. **Victor's Company** (`@victorscompany_bot`) — HumanPass compounding, deep mining, wallet binding & Level 1 Miner hire.
  4. **VyroDrop** (`@vyrodrop_bot`) — Autonomous 0.05 VYRO/h Cloud Solver, TonConnect 2.0 wallet binding & mining start.
  5. **Kynex Network** (`@kynexnetwork_bot`) — 15-Min Energy Sweep & node farming.
  *(Complementary bots: DiggoMiner, Astra Airdrop, PepeGram, AdxEarn AI).*

---

## 🛡️ 2. Non-Negotiable Directives & Rules (NEVER BREAK)

1. **Rule 1 — Strict Bot & Project Boundary**:
   - Never touch `@AAATelegramIdBot` (`AAA2743/AA`).
   - **User Bot Strict Immutability ("DO NOT TOUCH USER BOT")**: The User Bot (`@AAAPREMIUMAPPSbot`, ID `8167732110`, webhook `atf-miner-worker.agorameet.workers.dev`) is exclusively for end-users and must **NEVER** be modified, redeployed, or tampered with. Admin operations stay strictly on `@myagyai` and admin channels.
2. **Rule 4 — Zero Phone Load Directive (Samsung Galaxy A30)**:
   - ZERO bots, ZERO daemon loops, and ZERO MTProto relay listeners run locally on the phone.
   - All bot listeners, farming cycles, token refreshers, and solving run 100% in the cloud (Cloudflare Workers, Render, GitHub Actions, Cloud VM).
3. **Rule 5 — Zero-Trust Ephemeral Infrastructure & Mandatory Telegram Backup**:
   - Always assume any VM (`api.instabox.sh`) or local container can expire or get wiped at any second.
   - **MANDATORY**: ALWAYS run `python3 backup_manager.py` before and after any code changes, deployments, or migrations to stream encrypted disaster recovery archives to the Telegram vault channel (`@myagyai`).
4. **Rule 6 — Strict Secret Hygiene**:
   - ZERO plaintext secrets in chat responses, terminal logs, or git commits. Credentials belong solely in local untracked `.env` (`chmod 600`) or native cloud secret vaults.

---

## 🔒 3. Strict Multi-Chain Wallet Immutability Architecture

> [!IMPORTANT]
> **CRITICAL RULE**: Our system ONLY creates new wallets for genuinely brand-new accounts, NEVER for old or existing accounts.

### Immutability & Resolution Rules:
1. **Search Priority**: When an account logs in or provisions:
   - Check `FLEET_STATIC_REGISTRY` (all 18 static accounts in `public_admin/fleet_wallets_data.json`).
   - Check chain-specific vaults (`fleet_ton_wallets.json`, `fleet_evm_wallets.json`, `fleet_tron_wallets.json`, `fleet_solana_wallets.json`, `fleet_btc_wallets.json`).
   - Check existing `accounts.json` and active cloud account sessions.
2. **Existing Account Match**: If matched by User ID, Phone number, or Account Index:
   - System **100% preserves** the existing authentic 5-chain wallets.
   - **NEVER** generates new private keys or overwrites existing addresses.
3. **Brand-New Account Provisioning**: Only when an account is confirmed 100% brand new:
   - Generates an isolated 5-chain non-custodial wallet suite:
     - **TON**: Standard BIP-39 mnemonic, v4r2 non-bounceable user-friendly address.
     - **EVM**: Dedicated secp256k1 private key for BSC (BEP-20) and Arbitrum.
     - **TRON**: Base58Check address (`T...`) derived from dedicated private key.
     - **Solana**: Ed25519 public key in Base58.
     - **Bitcoin**: Native SegWit (`bc1q...`) address.

### Multi-Document Automatic Archival:
Whenever a new account is onboarded, `save_and_archive_account_wallets` automatically updates:
1. `fleet_ton_wallets.json` — TON addresses and mnemonics.
2. `fleet_evm_wallets.json` — EVM addresses and private keys.
3. `fleet_tron_wallets.json` — TRON addresses and private keys.
4. `fleet_solana_wallets.json` — Solana addresses and private keys.
5. `fleet_btc_wallets.json` — Bitcoin addresses and private keys.
6. `public_admin/fleet_wallets_data.json` — Master public JSON registry.
7. `FLEET_WALLETS_SECRETS_MASTER_VAULT.txt` — Secure master secrets vault with mnemonics and keys for all accounts (strictly `.gitignore`'d).
8. `FLEET_ACCOUNTS_AND_WALLETS_DIRECTORY.md` — Publicly verifiable Markdown directory with sanitized keys.
9. `accounts.json` & Upstash Redis — Synchronized runtime session store.

---

## ⚡ 4. Bot Wallet Auto-Binding & Mining Activation

Certain farming bots require a connected wallet before mining will unlock or produce rewards:

| Bot Name | Wallet Network | API Handshake & Activation Flow |
| :--- | :--- | :--- |
| **Victor's Company** | TON / EVM | 1. Calls `POST /api/wallet/connect` with address.<br>2. Calls `POST /api/tasks/complete` with task ID `connect-wallet`.<br>3. Calls `POST /api/levels/unlock` for level 1 to hire Level 1 Miner. |
| **VyroDrop** | TON | 1. Signs or simulates TonConnect 2.0 challenge/proof.<br>2. Verifies wallet via `POST /api/auth/verify-wallet`.<br>3. Activates mining loop via `POST /api/mining/start`. |
| **MRG Miner** | TON | Binds target TON wallet address during onboarding handshake for automated earnings. |
| **ATF Miner** | TON | Syncs TON wallet to `atfminers.asloni.online/miner/index.php?action=sync_wallet`. |
| **Astra Airdrop** | TON | Calls Supabase RPC `astra_sync_wallet` with target address. |

---

## ☁️ 5. Cloud Infrastructure & Active Deployments

| Component | Provider / Endpoint | Purpose & Status |
| :--- | :--- | :--- |
| **Render Cloud Standby Node 2** | `https://my-agy-fleet-standby-node2.onrender.com` | Live & Verified (HTTP 200). Collects session links on-demand, syncs to Cloudflare KV, spins down to preserve free quota. |
| **Cloudflare Edge Mesh Node 1** | `https://restore-agy.aaaai2.workers.dev` | Live. Edge backup, pricing oracle, and telemetry. |
| **Cloudflare Edge Mesh Node 2** | `https://restore-agy.aaa-bot.workers.dev` | Live. Edge backup, pricing oracle, and telemetry. |
| **Cloudflare Edge Mesh Node 3** | `https://restore-agy.aaa222.workers.dev` | Live. Edge backup, pricing oracle, and telemetry. |
| **Cloudflare Edge Mesh Node 4** | `https://restore-agy.agorameet.workers.dev` | Live & Verified (HTTP 200). |
| **Cloudflare Edge Mesh Node 5** | `https://restore-agy.aaaai.workers.dev` | Live. Worker engine. |
| **GitHub Actions** | `.github/workflows/` | Cloudflare Turnstile automated solver and sweepers. |
| **Cloud VM** | `api.instabox.sh:2222` | Dedicated paired programming environment with 4 vCPUs, 8 GB RAM. |
| **Telegram Vault** | Channel `@myagyai` | 24/7 off-machine disaster recovery archive recipient. |

---

## 🔍 6. Solved Milestones & Past Actions Log

1. **MRG Turnstile Invisible Frame Fix**: Guarded against clicking initial 1x1 passive handshake placeholder frame.
2. **Server-Side 24h HumanPass Persistence**: Bound `POST /api/user/verify-human` before `POST /api/user/claim-mining`.
3. **Webshare Proxy Pool Integration**: 20 pooled proxies with 7-second pre-flight TLS probes against Turnstile.
4. **Cloud VM Pairing Preservation**: Transferred 647 MB SQLite history database to cloud VM at `api.instabox.sh:2222`.
5. **Victor's Company 0-Second Fresh Token Minting**: Telethon MTProto minting resolved stale `401 TG_AUTH` across all 18 accounts.
6. **GitHub Actions Green CI/CD**: Fixed f-string escaping; all solver runs verified successful.
7. **Real-Time Channel Departure/Rejoin Sentinel**: Built `chat_member` webhook listener; pauses mining on leave, resumes on rejoin.
8. **Client-Side Parser Parity**: 3-pass URL decoding across web apps.
9. **Short-Text Directive**: Condensed User Bot notifications.
10. **Telegram Login PIN Pad Bug Fix**:
    - Fixed `NameError: name 'uid' is not defined` when adding new accounts via Admin Bot PIN pad callback in `app.py`, `render_app_latest.py`, and `render_standby_app.py`.
11. **Strict Multi-Chain Wallet Immutability**:
    - Engineered `find_existing_account_wallets` ensuring existing accounts re-use authentic wallets with 100% immutability.
    - Brand-new accounts generate isolated 5-chain suites (TON v4r2, EVM BSC/Arb, TRON, Solana, Bitcoin).
12. **Multi-Document Automatic Archival & Secrets Master Vault**:
    - Initialized secure `FLEET_WALLETS_SECRETS_MASTER_VAULT.txt` containing mnemonics and private keys for all 18 accounts (strictly gitignored).
    - Generated public directory `FLEET_ACCOUNTS_AND_WALLETS_DIRECTORY.md`.
    - Auto-archival on every new account addition.
13. **Multi-Bot Wallet Auto-Binding**:
    - Implemented `bind_wallets_to_bots` and `bootstrap_account_mining` across Victor's Company, VyroDrop, MRG, ATF, Astra.
14. **Codebase-Wide Static Symbol Analysis & Zero-Defect Bug Elimination**:
    - Ran Python `symtable` scanner across all 73 project files and eliminated all unresolved symbols:
      * Fixed `REPORT_BOT_TOKEN = os.getenv("REPORT_BOT_TOKEN", "")` in `app.py`, `render_app_latest.py`, and `render_standby_app.py`.
      * Fixed `PRIMARY_TON_WALLET = "UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT"` in `app.py`, `render_app_latest.py`, and `render_standby_app.py`.
      * Fixed missing `import time` in `login_account.py`.
      * Validated 722 KB Cloudflare Edge Worker JS with Node.js (`node -c`, 0 errors).
15. **Telegram Login Expired/Revoked Code Recovery & 1-Tap QR Fallback**:
    - Diagnosed Telegram's anti-phishing scanner which revokes authorization codes if typed or shared in chat messages, or after 120s.
    - Replaced dead-end PIN Pad loop with an intelligent recovery screen presenting `[ 🔄 Request Fresh Code ]` and `[ 📱 1-Tap QR Login (Zero Code) ]`.
    - Fixed `btn_request_code_` for new accounts with multi-tier fallback (`memLoginFlow`, `login_flow:chatId`, `last_login_phone:chatId`).
    - Added `force_fresh: true` parameter support in `send-code` to bypass 75s debounce and disconnect stale clients.
    - Added 1-Tap QR Device Linking (`tg://login?token=...`) into PIN Pad and recovery screens.
    - Added chat OTP message auto-deletion to protect codes from Telegram chat scanners.

---

## 📂 7. Key File Index

- **Master System Bible**: [`PROJECT_BIBLE.md`](file:///data/workspace/AAA_AUTO/PROJECT_BIBLE.md) (Full technical architecture, 1300+ lines).
- **Audit Changelog**: [`CHANGELOG.md`](file:///data/workspace/AAA_AUTO/CHANGELOG.md) (All git commits and milestone logs).
- **Mandatory Directives**: [`AGENTS.md`](file:///data/workspace/AAA_AUTO/AGENTS.md) (Strict rules, boundaries, and operational protocols).
- **Session Bridge (This File)**: [`SESSION_BRIDGE.md`](file:///data/workspace/AAA_AUTO/SESSION_BRIDGE.md).
- **Disaster Recovery**: [`backup_manager.py`](file:///data/workspace/AAA_AUTO/backup_manager.py) (Telegram backup pipeline).
- **Standalone 1-Click Restore**: [`restore.sh`](file:///data/workspace/AAA_AUTO/restore.sh) (Restores full system anywhere).
- **Multi-Chain Wallet Provisioner**: [`fleet_wallet_provisioner.py`](file:///data/workspace/AAA_AUTO/fleet_wallet_provisioner.py).
- **Cloud Collector Services**:
  - [`render_standby_app.py`](file:///data/workspace/AAA_AUTO/render_standby_app.py)
  - [`render_app_latest.py`](file:///data/workspace/AAA_AUTO/render_app_latest.py)
  - [`app.py`](file:///data/workspace/AAA_AUTO/app.py)
- **Fleet Wallets & Master Vaults**:
  - `FLEET_WALLETS_SECRETS_MASTER_VAULT.txt` (Local master secrets vault with mnemonics/keys; strictly gitignored).
  - `FLEET_ACCOUNTS_AND_WALLETS_DIRECTORY.md` (Public markdown directory).
  - `public_admin/fleet_wallets_data.json` (Static registry).
  - `fleet_ton_wallets.json`, `fleet_evm_wallets.json`, `fleet_tron_wallets.json`, `fleet_solana_wallets.json`, `fleet_btc_wallets.json`.
  - `accounts.json` (18 fleet account sessions).

---

## 💾 8. Disaster Recovery Protocol

1. Before any git commit or deployment, run:
   ```bash
   python3 backup_manager.py
   ```
2. Verify encrypted zip is delivered to `@myagyai` with SHA256 checksum and file size.
3. Commit changes with clear, descriptive commit messages.
4. Push simultaneously to both remotes:
   ```bash
   git push origin main && git push standby_repo main
   ```
