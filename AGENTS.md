# Antigravity Rules & Directives for AAA AUTO

> 📖 **MANDATORY PROJECT REFERENCE**:
> Before executing ANY plan, modifying code, or starting a new session, **every AI agent must read [SESSION_BRIDGE.md](./SESSION_BRIDGE.md) and [PROJECT_BIBLE.md](./PROJECT_BIBLE.md)** for complete instant handover context, full system architecture, 8 active legitimate bots (MRG, ATF, Victor's Company, Kynex Network, DiggoMiner, PepeGram, AdxEarn AI, Chicken Land), 24h Render session collector workflows, and operational protocols. Whenever you build or modify features, you MUST update `PROJECT_BIBLE.md` and `CHANGELOG.md`.

---

## 1. 🛡️ Strict Project Isolation & Bot Boundary
- **No Cross-Project Contamination**: Never mix code, configurations, packages, or context from `/root/projects/AAA` or other projects into this workspace.
- **Separate Bot Isolation**: `@AAATelegramIdBot` (repository `AAA2743/AA`) is a completely distinct project and must never be touched, modified, or merged into `AAA_AUTO`.
- **Zero Ecosystem Mixing (Full Development Allowed, Zero Mixing)**: You CAN touch, improve, modify, deploy, and upgrade the User Bot (`@AAAPREMIUMAPPSbot`, ID `8167732110`), its webhook, and its mini app. However, you must NEVER mix the Admin Bot (`@myagyai`) and User Bot ecosystems: keep tokens, code, command handlers, channels, databases, and dashboards 100% strictly isolated.
- **Self-Contained**: Everything relating to this project must remain strictly within `/root/projects/AAA_AUTO`.
- **Clean Boundaries**: Never modify system or other workspace files unless explicitly requested.

---

## 2. 📝 Persistent Action Memory & Change Audit
- **Full Action Transparency**: Always maintain a clear record of:
  - **What was done**: Completed features, installed packages, and configuration updates.
  - **What is currently in progress**: The specific task being solved right now.
  - **What was modified or removed**: Explicitly state any file, function, or line of code that is deleted or refactored, along with the reason.
- **Project Changelog**: Maintain a clean, human-readable `CHANGELOG.md` in the repository tracking all major additions, edits, and deletions.
- **Walrus Memory Sync**: Proactively save key architectural decisions and user preferences to Walrus Memory so context is preserved permanently across restarts.

---

## 3. 🎨 Quality Standards & Open-Source UI Excellence
- **No Throwaway or Useless Apps**: Do not build generic, half-baked, or useless toy mockups. Build production-grade, intentional, and useful solutions.
- **Beautiful, Modern UI Reference**:
  - When designing interfaces or websites, reference modern, battle-tested open-source designs from GitHub and the open-source community (e.g., Tailwind CSS, shadcn/ui design patterns, modern clean component architecture).
  - Prioritize mobile responsiveness, sleek aesthetics, clean typography, and intuitive UX suitable for smartphone and desktop screens.

---

## 4. 📱 Zero Phone Load Directive (Samsung Galaxy A30)
- **Phone Exclusivity**: The Samsung Galaxy A30 is STRICTLY dedicated to running the Antigravity AI CLI for pair programming.
- **ZERO Bots on Phone**: NEVER run bots, daemon loops, supervisor loops, scrapers, queue pollers, or MTProto relay listeners on the phone under ANY circumstances.
- **100% Cloud-First**: All bot listeners, farming cycles, token refreshers, and MTProto logins MUST run 100% in the cloud (Cloudflare Workers, Render, Deno, Vercel).
- **Hard Resource Guardrail**: Terminate and prevent any background Python bot processes from running locally. Keep RAM and CPU entirely free for the AI coding session.
- **Git Checkpoints**: Always keep Git history clean and run checkpoints regularly so no progress is lost if the mobile session drops.

---

## 5. ☁️ Zero-Trust Ephemeral Infrastructure ("Never Trust VPS or Local")
- **Ephemeral Mindset & Zero-Trust VMs**: Always assume ANY VPS, ephemeral container (e.g. `api.instabox.sh`), or local PRoot container can die, expire, or get wiped at any moment without warning. Never store unbacked-up data solely on an ephemeral VM.
- **MANDATORY AUTOMATIC TELEGRAM BACKUP (DO NOT FORGET)**:
  - ALWAYS execute `python3 backup_manager.py` to stream disaster recovery archives directly to the Telegram vault channel (`@myagyai`) before and after any major sync, transfer, code edit, or deployment.
  - Never finish a major milestone or workspace migration without verifying that a fresh backup archive was successfully delivered to `@myagyai`.
- **Continuous Off-Machine Durability**:
  - Keep automated disaster recovery archives flowing to the Telegram vault (`@myagyai`) via `backup_manager.py`.
  - Replicate state, heartbeat sentinel, and telemetry across the 3-node Cloudflare Edge mesh.
  - Regularly sync critical architectural decisions and state to Walrus Memory.
  - Keep Git checkpoints clean, pushed to both `origin` and `standby_repo`, and documented in `CHANGELOG.md`.
- **1-Click Disaster Recovery**: Ensure the self-contained 1-click restore mechanism (`restore.sh` / Telegram one-liner) always works out-of-the-box anywhere.

---

## 6. 🔐 Zero Plaintext Secrets & Cloud Secret Isolation ("Strict Secret Hygiene")
- **Zero Plaintext Secrets**: NEVER expose, hardcode, or echo raw API keys, Telegram bot tokens, GitHub Personal Access Tokens (PATs), mnemonic seed phrases, private keys, database passwords, or auth headers in chat outputs, Git commit messages, command strings, or tracked repository files.
- **Clean Git Remotes & Credential Store**: Never embed auth tokens or PATs inside Git remote URLs (e.g. `https://<token>@github.com/...`). All Git remotes MUST use clean HTTPS URLs (`https://github.com/org/repo.git`), and authentication must be handled solely via local secure credential helper (`~/.git-credentials` with `chmod 600`), completely isolated from repository tracking.
- **Cloud-Native Secret Vaults**: All runtime secrets, API keys, and service tokens MUST be provisioned, stored, and accessed strictly through native cloud secret managers:
  - **Cloudflare Workers**: Cloudflare Worker Secrets & environment bindings (`wrangler secret put`, dashboard variables, or `env.*` bindings).
  - **Vercel**: Vercel Project Environment Variables (`vercel env add`, Project Settings > Environment Variables).
  - **Render**: Render Environment Variables (`os.getenv(...)` populated via Render service environment settings).
  - **Upstash Redis**: Authenticated HTTPS REST key-value storage with cloud-managed bearer tokens.
  - **Local Development / Node**: Local untracked `.env` file that is strictly `.gitignore`'d and NEVER committed, pushed, or printed in terminal logs.
- **Automatic Sanitization & Masking**: If logging or referencing sensitive entities in terminal output, status reports, or error logs, always mask or redact the token (e.g. `ghp_...`, `816...:AAE...`, `Bearer ***`).

---

## 7. 🤖 Strict Separation of Bot Ecosystems, Channels & Admin Dashboards ("Zero Ecosystem Mixing")
- **Independent Bot Identities & Responsibilities (Full Development Allowed, Zero Mixing)**:
  - Both the Admin Bot and User Bot can be actively maintained, improved, and deployed.
  - **Admin Bot (`@myagyai`, ID `8858823950`)**: Exclusively reserved for system administrators. Controls executive fleet operations, 20 MTProto account onboarding/linking, cloud farm orchestration, sentinel monitoring, disaster recovery backups, and cloud node health. Handled via `ADMIN_BOT_TOKEN` / `REPORT_BOT_TOKEN`.
  - **User Bot (`@AAAPREMIUMAPPSbot`, ID `8167732110`)**: Exclusively dedicated to public end-users. Powers community multi-pool mining, points economy, daily check-ins, rewarded ads, Stars VIP access, and public onboarding. Handled via `USER_BOT_TOKEN`.
  - **Zero Contamination**: Never mix user bot code, tokens, or handlers into admin operations, and never expose admin commands (`/farm`, `/fleet`, `/acc`, `/restore`, QR/PIN MTProto logins, server health, private account seeds) to the User Bot.
- **Strict Channel Separation (Zero Cross-Posting / Zero Leakage)**:
  - **Admin Channels & Vaults (Private/Administrative)**:
    - 🛡️ Disaster Recovery Vault Channel: `@myagyai` (`-1004453515167`)
    - 💳 Payouts & Daily Ledger Channel: `-1004402765950`
    - 🏢 Fleet Internal Supergroup: `-1003973231307` (*AAA T Wallet Supergroup*)
    - 🔔 Admin Notification Channel: `AAA Admin notification` (`-1004358687850` — Short, concise system & operational alert cards)
    - *Directive*: Strictly for system backups, encrypted disaster recovery archives, internal payout ledgers, and fleet health notifications. NEVER route, broadcast, or leak administrative data, encrypted archives, or internal fleet telemetry to user community channels.
  - **User Community Channels (Public/End-Users)**:
    - 📢 Official Announcements: `@AAAAutoMiner` (`-1003684868577`)
    - 💬 Community Mining Group: `@AAAAUTOMINING` (`-1004255751168`)
    - ⚡ Activity & Verification: `@AAA_ACTIVITY` (`-1004332544939`)
    - *Directive*: Exclusively for public community updates, user mining feeds, onboarding verification gates, and cross-channel community relays. NEVER send admin alerts, error traces, disaster recovery dumps, or account credentials to these channels.
- **Dual Independent Admin Dashboards (Never Conflate or Intermix)**:
  - **Executive Fleet Operations Console (`admin.html` / `/admin`)**:
    - Dedicated strictly to **Admin Bot (`@myagyai`) & Fleet Operators**.
    - Displays real-time status of the 20 MTProto fleet accounts, 9 farming pools, multi-cloud nodes (Render Standby Node 2, Cloudflare Edge Mesh), Redis key inspect/flush, and automated disaster recovery triggers.
    - Does NOT manage public end-users, ad impressions, or public community points.
  - **User Bot Admin Console (`user-admin.html` / `/user-admin`)**:
    - Dedicated strictly to **User Bot (`@AAAPREMIUMAPPSbot`) Community Management**.
    - Displays end-user community miners (`community_miners`), user points economy, daily check-in streaks, rewarded video ad impression metrics (`ad_impressions_log`), user account bindings, and Stars VIP subscriptions.
    - Does NOT expose private fleet MTProto sessions, private keys, wallet seeds, or executive fleet controls.
- **Database & State Namespace Isolation**:
  - Keep Redis/database keys cleanly separated: `fleet:*` is strictly for Admin Bot & Fleet operations; `user:*`, `points:*`, `community_miners`, and `ad_impressions_log` are strictly for User Bot.

---

## 8. 🎯 Zero Fake Data & Ground-Truth 8-Bot Policy ("Strict 8-Bot Integrity")
- **The 8 High-Conviction Fleet Bots**: The farming fleet exclusively operates across and monitors the **8 active legitimate bots**:
  1. ⚡ **MRG Miner** (`@mrgtoken_bot` / `app.mrgtoken.xyz` / `mrg.up.railway.app`)
  2. 🪙 **ATF Miner** (`@atfminers_bot` / `atfminers.asloni.online`)
  3. 🏢 **Victor's Company** (`@VictorsCompanybot` / `app.victors.company` / `server.victors.company`)
  4. 🌐 **Kynex Network** (`@Kynex_miningbot` / `kynex.top`)
  5. ⛏️ **DiggoMiner** (`@Diggominer_bot` / `diggo.linkpc.net`)
  6. 🐸 **PepeGram** (`@Pepe_gram_bot` / `app.miniempire.app`)
  7. 🤖 **AdxEarn AI** (`@AdxEarnAibot` / `api.adxearnai.xyz`)
  8. 🐔 **Chicken Land** (`@ChickenLandBot` / `app8968434282.tgcloud.ai`)
- **Zero Fake / Zero Dead Bot Querying**: Truly defunct or purged bots (`VyroDrop`, `Astra Airdrop`, `LeafEarn`, `PumpkinEarn`, `Stones`, `AI Lab`, `UltraWallet`, `FINVORA`, `ART`, `Apex`, `Ainovum`, `TRX Power`, `Bitcoin Cloud`, `Tensor`, `Ton Trader`, `USDT QUAD`, `TAC`, `Ominix`) are permanently purged from routine farming cycles, financial statements, and dashboard telemetry. Never report placeholder values, `0.0 ASTRA`, or simulated numbers. Every status must reflect a live, cryptographically signed API response.

---

## 9. 🔄 24-Hour WebApp Token Lifetime & Autonomous Cloud Refresher
- **Token Lifespan**: Telegram WebApp `initData` cryptographically expires after 24 hours (`auth_date` validation). Never allow tokens to age past 18 hours.
- **100% Cloud Token Refresher**: Token collection runs on Render Frankfurt Node 2 (`/collect-tokens`), extracting fresh WebApp hashes via MTProto and simultaneously synchronizing both `fleet:tokens:{uid}` and `miniapp_tokens` in Upstash Redis and Cloudflare KV.

---

## 10. 🌐 Strict Multi-Repository Privacy & Runner Architecture
- **Master Repositories (Strictly 100% PRIVATE)**: `AAA0002/ATL` and `AAA0002/my-agy-fleet-standby` contain core architecture, configurations, and internal scripts. They MUST remain private at all times.
- **Public Solver Runner (Unlimited Free Minutes)**: `AAA0002/cloud-fleet-solver` is strictly a public headless runner containing ZERO plaintext secrets, zero private keys, and zero sessions. It runs headless Patchright Chromium on GitHub Actions to solve Cloudflare Turnstile challenges and execute multi-bot farming with unlimited free minutes. All runtime secrets are delivered via GitHub Encrypted Secrets (`secrets.UPSTASH_TOKEN`, etc.).
- **Automatic Pass Relay**: Acquired passes (`victors:pass:{uid}`, `mrg:pass:{uid}`) are written to Upstash Redis and consumed by Render Standby Node 2 and Cloudflare edge mesh to autonomously execute shift claims and farming cycles.


