# 🌉 MASTER SESSION BRIDGE — CONTINUITY & CONTEXT HANDOVER

> **FOR NEW AI SESSIONS (GEMINI, ANTIGRAVITY, CLAUDE, GPT)**:
> This document bridges the previous 63,300-step master session (`ab0db110-aa04-4d2f-808c-08e45816f8cd`) to your new clean session.
> Read this document completely to achieve 100% full context, architecture knowledge, current project state, and active priorities in seconds without any token bloat or latency.

---

## 🎯 1. Executive Identity & System Purpose

* **Project**: **AAA AUTO** (also known as **MY AGY AI Fleet**).
* **Workspace**: `/root/workspace` (PRoot / Phone) & `/data/workspace/AAA_AUTO` (Cloud VM).
* **Git Repository**: `AAA0002/ATL` (clean HTTPS remotes: `origin` and `standby_repo`).
* **Architecture**: 100% Cloud-First Autonomous Telegram Mini-App Mining & Multi-Chain Wallet Fleet.
* **Accounts**: **18 Telegram Accounts** (1 Master Account + 17 Worker Accounts) farming in parallel.
* **9 Active Legitimate Fleet Bots**:
  1. **MRG Miner** (`@mrg_miner_bot`) — Level 95+ Auto-Upgrade & Turnstile Solver.
  2. **ATF Miner** (`@atf_miner_bot`) — Cloud hash compounding, balance tracking.
  3. **Victor's Company** (`@victorscompany_bot`) — HumanPass compounding and deep mining.
  4. **VyroDrop** (`@vyrodrop_bot`) — Autonomous 0.05 VYRO/h Cloud Solver.
  5. **Kynex Network** (`@kynexnetwork_bot`) — 15-Min Energy Sweep & node farming.
  6. **DiggoMiner** (`@diggominer_bot`) — 30-Day JWT Session Mining.
  7. **Astra Airdrop** (`@AstraAirdropBot`) — Supabase RPC & Boosts.
  8. **PepeGram** (`@pepe_mine_bot`) — 6h Hash Production Loop.
  9. **AdxEarn AI** (`@AdxEarnAibot`) — Daily Ads & Point Farming.
  *(All scammer/unneeded bots like LeafEarn, PumpkinEarn, etc., permanently purged).*

---

## 🛡️ 2. Non-Negotiable Rules & Directives (NEVER BREAK)

1. **Rule 1 — Strict Bot & Project Isolation**:
   - Never touch `@AAATelegramIdBot` (`AAA2743/AA`).
   - **User Bot Strict Immutability ("DO NOT TOUCH USER BOT")**: The User Bot (`@AAAPREMIUMAPPSbot`, ID `8167732110`, webhook `atf-miner-worker.agorameet.workers.dev`) is exclusively for end-users and must **NEVER** be modified, redeployed, or tampered with. Admin operations stay strictly on `@myagyai`.
2. **Rule 4 — Zero Phone Load Directive (Samsung Galaxy A30)**:
   - ZERO bots, ZERO daemon loops, and ZERO MTProto relay listeners run locally on the phone.
   - All bot listeners, farming cycles, token refreshers, and solving run 100% in the cloud (Cloudflare Workers, Render, GitHub Actions, Cloud VM).
3. **Rule 5 — Zero-Trust Ephemeral Infrastructure & Mandatory Telegram Backup**:
   - Always assume any VM (`api.instabox.sh`) or local container can expire or get wiped at any second.
   - **MANDATORY**: ALWAYS run `python3 backup_manager.py` before and after any code changes, deployments, or migrations to stream encrypted disaster recovery archives to the Telegram vault channel (`@myagyai`).
4. **Rule 6 — Strict Secret Hygiene**:
   - ZERO plaintext secrets in chat responses, terminal logs, or git commits. Credentials belong solely in local untracked `.env` (`chmod 600`) or native cloud secret vaults.

---

## ☁️ 3. Cloud Infrastructure & Active Deployments

| Component | Provider / Location | Purpose & Status |
| :--- | :--- | :--- |
| **Render Cloud Node 2** | `https://my-agy-fleet-standby-node2.onrender.com` | Live. Wakes on-demand for batch session link collection, syncs to Cloudflare KV, triggers cloud farming, spins down to save free hours. |
| **Cloudflare Edge Mesh** | 5 Worker nodes (`restore-agy.aaaai2.workers.dev`, etc.) | High-availability 24/7 endpoint mesh & session link fallback. |
| **GitHub Actions** | Workflows in `.github/workflows/` | Runs `mrg_turnstile_solver.yml` (Patchright + Webshare proxies) and `multi_chain_sweeper.yml`. |
| **Cloud VM** | `api.instabox.sh:2222` (`ibssh_um2ztzz4r64whg4mp4fvgs2o3i`) | 4 vCPUs, 8 GB RAM, 20 GB disk. Dedicated Antigravity CLI paired programming environment. |
| **Telegram Vault** | Channel `@myagyai` | 24/7 off-machine disaster recovery archive recipient. |

---

## 🔍 4. Recent Solved Milestones (What Was Just Done)

1. **MRG Turnstile Invisible Frame Fix**:
   - Cloudflare Turnstile renders an initial 1x1 placeholder frame (`0.3, 4.5`) during passive TLS handshake.
   - Fixed premature clicking bug: Added guardrail `box["width"] >= 200 and box["height"] >= 45`. Passive attestation completes naturally without instance destruction.
2. **Server-Side 24h Human Verification Pass Persistence**:
   - Added direct call to `POST /api/user/verify-human` immediately before `POST /api/user/claim-mining` across `render_standby_app.py`, `render_app_latest.py`, and `app.py`.
   - Locks in full 24h verification validity on MRG backend servers.
3. **Webshare Proxy Pool Integration**:
   - Pooled `WEBSHARE_KEY_1` and `WEBSHARE_KEY_2` (20 proxies total) with 7-second pre-flight HTTPS probes against Cloudflare Turnstile endpoints.
4. **Cloud VM Transition & Session Preservation**:
   - Provisioned 4-core cloud VM at `api.instabox.sh:2222`.
   - Transferred and preserved full 647 MB SQLite database of the previous session (`ab0db110-aa04-4d2f-808c-08e45816f8cd.db`).
   - Configured global python virtualenv with all dependencies.
5. **Victor's Company Fleet Audit & 0-Second Fresh Token Minting**:
   - Resolved 9-day stale `initData` causing `401 TG_AUTH` across all accounts.
   - Built and ran `extract_victors_fresh.py` via Telethon MTProto: minted 100% fresh 0-second `initData` for all 18 accounts.
   - Probed Victor's `/auth/login` across all 18 accounts: 100% returned `403 HUMAN_REQUIRED` (0% session expired).
   - Master account `6727787768` has `start_param=None` (preventing self-referral loop); all 17 sub-accounts bound to `ref_A20AA96F18`.
6. **GitHub Actions Turnstile Solver & CI/CD Pipeline Green**:
   - Fixed Python f-string escaping in `window.turnstile.render` hook inside `mrg_turnstile_solver.py`.
   - Verified GitHub Actions runs (Runs `39633362685`, `39634493201`, `39713197934`) all completed with `✓ SUCCESS`. Zero quota or minute exhaustion.


---

## 📂 5. Key File Index

- **Master System Bible**: [`PROJECT_BIBLE.md`](file:///root/workspace/PROJECT_BIBLE.md) (Full technical architecture, 1300+ lines).
- **Audit Changelog**: [`CHANGELOG.md`](file:///root/workspace/CHANGELOG.md) (All git commits and milestone logs).
- **Mandatory Directives**: [`AGENTS.md`](file:///root/workspace/AGENTS.md) (Strict rules, boundaries, and operational protocols).
- **Disaster Recovery**: [`backup_manager.py`](file:///root/workspace/backup_manager.py) (Telegram backup pipeline).
- **Standalone 1-Click Restore**: [`restore.sh`](file:///root/workspace/restore.sh) (Restores full system anywhere).
- **Cloud Collector Services**:
  - [`render_standby_app.py`](file:///root/workspace/render_standby_app.py)
  - [`render_app_latest.py`](file:///root/workspace/render_app_latest.py)
  - [`app.py`](file:///root/workspace/app.py)
- **Fleet Wallets & Data**:
  - `fleet_ton_wallets.json` (18 TON non-custodial wallets)
  - `fleet_evm_wallets.json` (18 EVM non-custodial wallets)
  - `accounts.json` (18 fleet account sessions)

---

## 🗄️ 6. Location of Previous Session History (Reference Only)

If you ever need deep granular logs or transcripts from the previous session:
- **Session ID**: `ab0db110-aa04-4d2f-808c-08e45816f8cd`
- **Database File**: `/data/home/.gemini/antigravity-cli/conversations/ab0db110-aa04-4d2f-808c-08e45816f8cd.db` (Phone & VM)
- **Brain Artifacts**: `/data/home/.gemini/antigravity-cli/brain/ab0db110-aa04-4d2f-808c-08e45816f8cd/`
- **Transcripts**: `transcript.jsonl` and `transcript_full.jsonl` in `.system_generated/logs/`
- **Telegram Vault**: Disaster recovery archives delivered directly to [@myagyai](https://t.me/myagyai).

---

> **Ready for Action**: You now have 100% full context. Assist the user with speed, precision, and adherence to the Golden Directives!
