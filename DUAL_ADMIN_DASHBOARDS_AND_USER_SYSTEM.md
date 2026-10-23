# 🛡️ Dual Dashboards, User Architecture & Session Management Manual

> **MANDATORY SYSTEM REFERENCE**:
> This document provides the complete, authoritative operational guide to the **Dual Independent Dashboards** (`/admin` vs `/user-admin`), the **User Bot Authentic Account Onboarding System**, the **MTProto Session Revocation Sentinel**, and the **Community Broadcast & Notification Engine**.
> *Classification: Mission-Critical Architectural Specification*
> *Rule 7 Directives: Zero Ecosystem Mixing • Zero Cross-Posting • Zero Contamination*

---

## 🗺️ 1. Executive Overview: Dual Independent Dashboards

To enforce **Rule 7 ("Zero Ecosystem Mixing")**, the system maintains two completely separated, independent admin consoles with distinct visual themes, dedicated database namespaces, separate bot identities, and isolated operational scopes.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 AAA AUTO INFRASTRUCTURE                                │
│                                                                                        │
│  ┌────────────────────────────────────────┐  ┌──────────────────────────────────────┐  │
│  │ 🏢 Executive Fleet Console (/admin)    │  │ 🤖 User Admin Console (/user-admin)   │  │
│  │                                        │  │                                      │  │
│  │  • Bot Identity: @myagyai (8858823950) │  │  • Bot Identity: @AAAPREMIUMAPPSbot   │  │
│  │  • Target: 20 Fleet Accounts (#1-#20)  │  │  • Target: Public Community Miners   │  │
│  │  • Database: Redis `fleet:*`           │  │  • Database: Turso user_accounts &   │  │
│  │              & accounts.json           │  │    user_wallets + Redis `ub_*`       │  │
│  │  • Features: Fleet Multi-Cloud Nodes,  │  │  • Features: 5-Chain User Wallets,   │  │
│  │    Sentinel Heartbeat, DR Vault Backup,│  │    Custom Payouts, Revoke Sentinel,  │  │
│  │    9-Pool Mining Execution             │  │    Broadcast Engine, Points Economy  │  │
│  │  • Theme: Dark Slate / Amber           │  │  • Theme: Deep Violet / Cyan         │  │
│  └────────────────────────────────────────┘  └──────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚖️ 2. Comprehensive Comparison Matrix

| Attribute | 🏢 Executive Fleet Console (`admin.html`) | 🤖 User Bot Admin Console (`user-admin.html`) |
| :--- | :--- | :--- |
| **Edge URL** | `https://restore-agy.agorameet.workers.dev/admin` | `https://restore-agy.agorameet.workers.dev/user-admin` |
| **Alternative Routes** | `/fleet`, `/console`, `/dashboard` | `/users-admin`, `/community-admin`, `/user-dash` |
| **Bot Association** | **Admin Bot (`@myagyai`)**, ID `8858823950` | **User Bot (`@AAAPREMIUMAPPSbot`)**, ID `8167732110` |
| **Token Handling** | `ADMIN_BOT_TOKEN` / `REPORT_BOT_TOKEN` | `USER_BOT_TOKEN` |
| **Managed Accounts** | **Accounts #1 to #20** (1 Master + 19 Workers) | **Public End-Users & Community Miners** |
| **Database Isolation** | `accounts.json`, Upstash `fleet:*` | Turso LibSQL `user_accounts`, `user_wallets`, Upstash `ub_*` |
| **Primary Scope** | Multi-node failover, disaster recovery, 20-account yield farming | Community user onboarding, wallet secrets, session revocations, broadcast notifications |
| **Channel Vaults** | 🛡️ `@myagyai` (`-1004453515167`), 💳 Ledger (`-1004402765950`) | 📢 `@AAAAutoMiner`, 💬 `@AAAAUTOMINING`, ⚡ `@AAA_ACTIVITY` |
| **Visual Identity** | Slate 950 background with Amber / Emerald accents | Deep Violet / Slate with Cyan / Purple accents & `@AAAPREMIUMAPPSbot` banner |

---

## 🚫 3. Deprecation & Complete Removal of "Telegram ID" Login

### Why Bare Numeric Telegram IDs Were Removed
- Third-party Telegram WebApp crypto bots (**MRG Miner, ATF Miner, Victor's Company, VyroDrop, Kynex Network, DiggoMiner, Astra Airdrop, PepeGram, AdxEarn AI**) enforce cryptographic signature verification:
  - **HMAC-SHA256 Signatures**: Each API call requires `initData` signed with the bot's secret key, valid for only a few hours.
  - **MTProto Sessions**: Autonomous background yield claims require an active Telegram MTProto session to sign webview authorizations.
- **The Problem with Numeric IDs**: A bare numeric Telegram ID (e.g. `6727787768`) cannot sign cryptographic tokens. Submitting a numeric ID led users to believe they were connected, but cloud farming workers encountered `401 Unauthorized` on every cycle.

### What Was Removed & What Replaced It
1. **Removed**:
   - The manual `input-raw-data` textarea in `public_ads/miner/index.html`.
   - The misleading instruction *"2. Telegram User ID: Or enter any numeric Telegram ID in the box above"*.
   - Backend acceptance of bare numeric IDs in `/api/user/account/add`.
2. **Implemented Authentic MTProto Device Onboarding**:
   - **📱 1-Tap QR Code Login (`tg://login?token=...`)**:
     * Uses Telethon on Render Node 2 (`/api/account/login/qr-start` with `is_user_bot: true`).
     * Displays a live QR code and provides a direct 1-tap link that opens Telegram's native device pairing dialog.
     * **Zero SMS codes required**; authorizes in under 2 seconds.
   - **📱 Phone Login (SMS / Official App OTP)**:
     * Dispatches an official 5-digit verification code directly from Telegram (`/api/account/login/send-code`).
     * Users verify in-app (`/api/account/login/verify-code`), generating an authentic Telethon session.
   - **Educational Helper**: If a user sends a bare numeric ID to `@AAAPREMIUMAPPSbot`, the bot explains why numeric IDs cannot sign transactions and offers direct buttons for 1-Tap QR Login and Phone Login.

---

## ⚠️ 4. MTProto Session Revocation Sentinel & User Notification

When a user connects their Telegram account to the User Bot, an MTProto session string is securely stored in Turso LibSQL table `user_accounts` and Upstash Redis. If the user later terminates the session via **Telegram Settings > Devices > Terminate Session**, the session becomes invalid.

### How Revocation is Handled
1. **Detection**:
   - Handled via Telethon's `client.is_user_authorized()`.
   - Catching `SessionRevokedError`, `UserDeactivatedError`, `AuthKeyUnregisteredError`, and `AuthKeyDuplicatedError`.
2. **Atomic Status Update**:
   - Turso LibSQL: `UPDATE user_accounts SET status = 'revoked' WHERE user_id = ?;`
   - Upstash Redis: `HSET ub_user:<uid> session_status "revoked"` and `prof["farming_active"] = false`.
3. **Immediate User Notification**:
   - The user immediately receives a dedicated alert from `@AAAPREMIUMAPPSbot`:
     ```
     ⚠️ Alert: Telegram Session Terminated / Revoked 🔴

     Your connected Telegram account session has expired or was terminated from Telegram Settings > Devices.

     Cloud auto-mining across all 9 bots has paused to protect your account.

     👉 Tap below to reconnect via 1-Tap QR Login or Phone Login to resume your 24/7 cloud earnings!
     ```
   - Inline keyboard with `[ 📱 1-Tap QR Login ]` and `[ 📱 Phone Login ]`.
4. **Admin Dashboard Visibility**:
   - In `user-admin.html`, the user card displays a prominent red badge: `🔴 Session Revoked / Disconnected`.
   - Administrators can filter by **Revoked** or trigger a manual scan across all user accounts using the **"Scan Revoked Sessions"** button (`/api/admin/session/check-all`).

---

## 📢 5. Community Broadcast & Notification Engine

The User Bot Admin Console includes an integrated **Broadcast & Alerts Engine** to send announcements and onboarding reminders directly inside [@AAAPREMIUMAPPSbot](https://t.me/AAAPREMIUMAPPSbot).

### Features
1. **Audience Filtering**:
   - `📱 Unconnected Users` (`no_account`): Targets community members who have registered but not yet connected an MTProto account.
   - `⚠️ Revoked Sessions` (`revoked`): Targets users whose device session expired or was revoked.
   - `👥 All Users` (`all`): Broadcasts to the entire community roster.
   - `🟢 Active Mining Users` (`active`): Broadcasts updates to active miners.
2. **Pre-Built Actionable Templates**:
   - **Upgrade Alert**: Informs users about the transition to 1-Tap QR & Phone login and explains why numeric IDs were retired.
   - **Session Reconnect**: Guides users to re-authorize revoked sessions.
   - **Daily Bonus**: Reminds users to claim their +100 daily streak points.
3. **Automatic Attached Buttons**:
   - Every broadcast automatically attaches:
     - `📱 1-Tap QR Login` (`ub_login_qr`)
     - `📱 Phone Login` (`ub_login_phone`)
     - `💎 My Wallets & Keys` (`ub_wallets`)
4. **Telegram Command Shortcut**:
   - Administrators can also broadcast directly from chat by sending `/notify_unconnected <optional message>` or `/broadcast all <message>` in [@AAAPREMIUMAPPSbot](https://t.me/AAAPREMIUMAPPSbot).

---

## 💎 6. Dedicated 5-Chain Non-Custodial Wallets & Custom Routing

Every connected user is provisioned a dedicated, isolated 5-chain wallet suite in Turso LibSQL table `user_wallets`:

1. **Chains Supported**:
   - **TON (v4r2)**: For Toncoin, Jettons, and pool reward claims.
   - **EVM (BSC / Arbitrum)**: For BEP-20 / Arbitrum tokens.
   - **TRON**: For TRX and USDT-TRC20.
   - **Solana**: For SOL and SPL tokens.
   - **Bitcoin**: Standard SegWit address for satoshi earnings.
2. **User Key Retrieval**:
   - Users can send `/wallets`, `/wallet`, or `/keys` in `@AAAPREMIUMAPPSbot` or tap **💎 My Wallets** to inspect their public addresses.
   - Tapping **🔐 View Recovery Keys** reveals their 24-word mnemonic and private keys in private chat with a non-custodial ownership notice.
3. **Custom Personal Payout Wallet Binding**:
   - Users can disconnect the default bot wallet and bind their personal wallet (Tonkeeper, MetaMask, Trust Wallet) via `/customwallet` or the Mini App.
   - Payouts route automatically to the user's custom address (`is_custom = 1`).

---

## 🗄️ 7. Database Isolation Reference

```sql
-- Turso LibSQL: Isolated User Accounts Table
CREATE TABLE IF NOT EXISTS user_accounts (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  chat_id TEXT NOT NULL,
  name TEXT,
  phone TEXT,
  session_string TEXT,
  status TEXT DEFAULT 'active',
  created_at INTEGER
);

-- Turso LibSQL: Isolated User Wallets Table
CREATE TABLE IF NOT EXISTS user_wallets (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  chat_id TEXT NOT NULL,
  chain TEXT NOT NULL,
  address TEXT NOT NULL,
  private_key TEXT,
  mnemonic TEXT,
  is_custom INTEGER DEFAULT 0,
  created_at INTEGER
);
```

- **Redis Key Isolation**:
  - `fleet:*` -> Reserved strictly for Admin Bot (`@myagyai`) & Fleet Accounts #1 to #20.
  - `ub_*` -> Reserved strictly for User Bot (`@AAAPREMIUMAPPSbot`):
    - `ub_registered_users`: Set of all community user IDs.
    - `ub_user:<uid>`: User profile (points, streak, ad metrics, accounts).
    - `ub_wallet:<uid>`: User multi-chain wallet suite.
    - `ub_custom_wallet:<uid>:<chain>`: User custom payout address.
