# 🌐 Domain, Email Routing & Proxy Harvester Hub

> 🚨 **STRICT SUBAGENT & PROJECT BOUNDARY DIRECTIVE**:
> This hub is dedicated **exclusively** to:
> 1. Managing DigitalPlat FreeDomain domain infrastructure (`agy.dpdns.org`).
> 2. Maintaining Cloudflare Catch-All Email Routing (`*@agy.dpdns.org` ➔ `aaa.support.a@gmail.com`).
> 3. Generating custom domain email aliases to register fresh Webshare free proxy accounts.
> 
> **STRICT ZERO-INTERFERENCE POLICY**:
> - **DO NOT INTERFERE** with the main AAA AUTO mining fleet (the 8 high-conviction farming bots: MRG, ATF, Victor's, Kynex, Diggo, PepeGram, AdxEarn AI, Chicken Land).
> - **DO NOT MODIFY** the core fleet automation scripts (`app.py`, `render_standby_app.py`, `mrg_turnstile_solver.py`, `victors_sb_solver.py`, `bot_registry.py`).
> - **DO NOT TOUCH** `@AAATelegramIdBot` (`AAA2743/AA`) or the User Bot (`@AAAPREMIUMAPPSbot`) production databases.
> - Stay strictly within this folder and operational scope.

---

## 🛠️ Architecture & Core Components

```
domain_email_proxy_hub/
├── README.md                      # This specification & operational guide
├── HANDOVER_BRIEF.md              # Instant handover brief for AI subagents/chats
├── digitalplat_dns_manager.py     # DigitalPlat API DNS manager for agy.dpdns.org
├── cloudflare_email_router.py     # Cloudflare Email Routing & Catch-All manager
└── webshare_proxy_harvester.py    # Multi-account Webshare proxy creator & harvester
```

---

## 🔑 Operational Credentials (Loaded from `.env`)

All credentials are automatically resolved from `/data/workspace/AAA_AUTO/.env`:
* **`DIGITALPLAT_API_KEY`**: Production token (`dp_live_...`) for `https://domain-api.digitalplat.org/api/v1`.
* **`CF_ZONE_EMAIL_TOKEN`**: Scoped Cloudflare API token (`cfut_...`) with Zone & Email Routing write access.
* **`GMAIL_ADDRESS`**: `aaa.support.a@gmail.com` (Target destination mailbox for all catch-all mail).
* **`GMAIL_APP_PASSWORD`**: Authenticated IMAP app password for automated token extraction.
* **`WEBSHARE_KEY_1` & `WEBSHARE_KEY_2`**: Active Webshare proxy keys.

---

## 🚀 Usage & Quick Commands

### 1. Verify DigitalPlat Domain & Injected MX Records
```bash
python3 domain_email_proxy_hub/digitalplat_dns_manager.py
```
* Queries `https://domain-api.digitalplat.org/api/v1/domains/agy.dpdns.org/dns/records`.
* Verifies Cloudflare MX (`route1`, `route2`, `route3`) and SPF TXT records are active.

### 2. Check Cloudflare Email Routing & Verification Status
```bash
python3 domain_email_proxy_hub/cloudflare_email_router.py
```
* Queries Cloudflare Zone `f668c3573777bb05a95eba5dc01ada32` (`agy.dpdns.org`).
* Checks destination address verification status and updates the Catch-All rule to Active.

### 3. Generate Alias & Expand Webshare Proxies
```bash
python3 domain_email_proxy_hub/webshare_proxy_harvester.py
```
* Generates fresh aliases (e.g. `proxy_a8f9z@agy.dpdns.org`).
* Listens on Gmail IMAP to auto-extract incoming confirmation links.
