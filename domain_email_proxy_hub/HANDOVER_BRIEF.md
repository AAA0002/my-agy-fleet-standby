# 📋 Handover Brief: Domain, Catch-All Email & Proxy Subagent

**Role**: Domain, Email Routing & Proxy Specialist  
**Workspace**: `/data/workspace/AAA_AUTO/domain_email_proxy_hub/`  
**Isolation Rule**: Strictly self-contained. Never modify core fleet farming scripts or other project workspaces.

---

### 1. Active Infrastructure State
* **Domain Registered**: `agy.dpdns.org` (DigitalPlat FreeDomain, valid through 2027-10-29).
* **Authoritative DNS**: DigitalPlat Cloud DNS (`dns1.digitalplat.org`, `dns2.digitalplat.org`).
* **Cloudflare Email Routing Zone**: `f668c3573777bb05a95eba5dc01ada32` (`agy.dpdns.org`).
* **Injected DNS Records on DigitalPlat**:
  - `MX @ -> 50 route1.mx.cloudflare.net.`
  - `MX @ -> 44 route2.mx.cloudflare.net.`
  - `MX @ -> 95 route3.mx.cloudflare.net.`
  - `TXT @ -> "v=spf1 include:_spf.mx.cloudflare.net ~all"`
* **Target Forwarding Mailbox**: `aaa.support.a@gmail.com`
* **Catch-All Rule**: Forward `*@agy.dpdns.org` ➔ `aaa.support.a@gmail.com`

---

### 2. Available Automated Tools
1. `digitalplat_dns_manager.py`: Full CRUD on DigitalPlat DNS records via `https://domain-api.digitalplat.org/api/v1`.
2. `cloudflare_email_router.py`: Cloudflare Email Routing rules, destination address management, and IMAP verification.
3. `webshare_proxy_harvester.py`: Alias generation (`*@agy.dpdns.org`), Webshare account expansion, and proxy pool synchronization.

---

### 3. Immediate Mission Tasks
1. Complete destination email verification by visiting Cloudflare confirmation link or verifying with token.
2. Confirm that Catch-All rule forwards test messages sent to `test@agy.dpdns.org` into `aaa.support.a@gmail.com`.
3. Use generated catch-all email aliases to register additional Webshare accounts, extracting confirmation links from Gmail to expand the free proxy roster past 20.
4. Report updated proxy roster to root `.env` (`WEBSHARE_KEY_3`, etc.) without touching any core farming loop.
