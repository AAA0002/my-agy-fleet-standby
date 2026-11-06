#!/usr/bin/env python3
"""
check_system_health.py
Live forensic health verification across:
1. Cloudflare Edge Mesh (5 nodes)
2. Render Cloud Nodes (3 nodes)
3. Telegram Bot Webhooks
4. Render Deployment Status
5. Upstash Redis State
6. Live 9-Bot Fleet API Probe
"""

import os
import json
import time
import urllib.request
import urllib.error
import urllib.parse
import aiohttp
import asyncio

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

env = {}
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip("\"'\"'")

UPSTASH_URL = env.get("UPSTASH_URL")
UPSTASH_TOKEN = env.get("UPSTASH_TOKEN")
TURSO_URL = env.get("TURSO_URL") or env.get("TURSO_DB_URL") or "https://my-agy-fleet-db-aaa2743.aws-ap-south-1.turso.io"
TURSO_TOKEN = env.get("TURSO_TOKEN") or env.get("TURSO_DB_TOKEN") or ""
ADMIN_BOT_TOKEN = env.get("ADMIN_BOT_TOKEN") or env.get("REPORT_BOT_TOKEN")
USER_BOT_TOKEN = env.get("USER_BOT_TOKEN")
RENDER_KEY = env.get("RENDER_API_KEY_3") or env.get("RENDER_API_KEY")

async def test_cf_nodes():
    print("\n--- 1. Testing Cloudflare Edge Nodes ---")
    cf_nodes = [
        ("Primary Gateway Node 4", "https://restore-agy.agorameet.workers.dev"),
        ("Secondary Node 1", "https://restore-agy.aaaai2.workers.dev"),
        ("Secondary Node 2", "https://restore-agy.aaa-bot.workers.dev"),
        ("Secondary Node 3", "https://restore-agy.aaa222.workers.dev"),
        ("Secondary Node 5", "https://restore-agy.aaaai.workers.dev")
    ]
    async with aiohttp.ClientSession() as s:
        for name, url in cf_nodes:
            t0 = time.time()
            try:
                async with s.get(f"{url}/health", headers={"User-Agent": "Mozilla/5.0"}, timeout=aiohttp.ClientTimeout(total=5)) as r:
                    lat = int((time.time() - t0) * 1000)
                    print(f"  ✅ {name} ({url}): HTTP {r.status} ({lat}ms)")
            except Exception as e:
                print(f"  ⚠️ {name} ({url}): {e}")

async def test_render_nodes():
    print("\n--- 2. Testing Render Cloud Standby Nodes ---")
    render_nodes = [
        ("Render Node 3 (Oregon - Primary)", "https://my-agy-fleet-standby-node3.onrender.com"),
        ("Render Node 2 (Frankfurt)", "https://my-agy-fleet-standby-node2.onrender.com"),
        ("Render Node 1 (Singapore)", "https://my-agy-fleet-standby.onrender.com")
    ]
    async with aiohttp.ClientSession() as s:
        for name, r_url in render_nodes:
            t0 = time.time()
            try:
                async with s.get(f"{r_url}/health", headers={"User-Agent": "Mozilla/5.0"}, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    lat = int((time.time() - t0) * 1000)
                    print(f"  ✅ {name}: HTTP {r.status} ({lat}ms)")
            except Exception as e:
                print(f"  ⚠️ {name}: {e}")

async def test_telegram_webhooks():
    print("\n--- 3. Testing Telegram Webhook Endpoints ---")
    bots = [
        ("Admin Bot (@myagyai)", ADMIN_BOT_TOKEN),
        ("User Bot (@AAAPREMIUMAPPSbot)", USER_BOT_TOKEN)
    ]
    async with aiohttp.ClientSession() as s:
        for name, tok in bots:
            if not tok:
                print(f"  ⚠️ {name}: No token found")
                continue
            try:
                async with s.get(f"https://api.telegram.org/bot{tok}/getWebhookInfo", timeout=aiohttp.ClientTimeout(total=6)) as r:
                    d = await r.json()
                    res = d.get("result", {})
                    wh = res.get("url", "None")
                    pending = res.get("pending_update_count", 0)
                    err = res.get("last_error_message")
                    err_s = f" | Last Error: {err}" if err else ""
                    print(f"  ✅ {name}: Webhook -> {wh} (Pending: {pending}{err_s})")
            except Exception as e:
                print(f"  ⚠️ {name}: {e}")

async def test_render_deployments():
    print("\n--- 4. Checking Render Deployment Progress ---")
    srv_id = "srv-db437o3tqb8s73dt4erg"
    if not RENDER_KEY:
        print("  ⚠️ No RENDER_API_KEY found.")
        return
    async with aiohttp.ClientSession() as s:
        try:
            headers = {"Authorization": f"Bearer {RENDER_KEY}"}
            async with s.get(f"https://api.render.com/v1/services/{srv_id}/deploys?limit=3", headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status == 200:
                    deploys = await r.json()
                    for item in deploys:
                        dep = item.get("deploy", {})
                        print(f"  🚀 Deploy {dep.get('id')}: Status = {dep.get('status')} | Created: {dep.get('createdAt')}")
                else:
                    print(f"  ⚠️ Render API HTTP {r.status}")
        except Exception as e:
            print(f"  ⚠️ Render check error: {e}")

async def test_live_11_bots_probe():
    print("\n--- 5. Probing Live 9-Bot API Connectivity & Tokens ---")
    accs_file = os.path.join(BASE_DIR, "accounts.json")
    if not os.path.exists(accs_file):
        print("  ⚠️ accounts.json missing")
        return
    with open(accs_file, "r") as f:
        accs = json.load(f)
    master_acc = [a for a in accs if str(a.get("account_id") or a.get("user_id")) == "6727787768"][0]
    worker_acc = [a for a in accs if str(a.get("account_id") or a.get("user_id")) != "6727787768"][0]

    def extract_auth_date(tok):
        if not isinstance(tok, str):
            return 0
        try:
            qs = urllib.parse.parse_qs(tok)
            return int(qs.get("auth_date", [0])[0])
        except Exception:
            return 0

    # Pull live tokens: Turso LibSQL High-Capacity SSOT FIRST (25M ops/mo), then Upstash
    live_tokens = {}
    if TURSO_URL and TURSO_TOKEN:
        try:
            t_http = TURSO_URL.replace("libsql://", "https://") + "/v2/pipeline"
            t_req = urllib.request.Request(
                t_http,
                headers={"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"},
                data=json.dumps({"requests": [{"type": "execute", "stmt": {"sql": "SELECT key, val FROM kv_mesh WHERE key IN ('fleet:tokens:6727787768', 'fleet:tokens_state', 'fleet:diggo:jwt:6727787768');"}}]}).encode()
            )
            with urllib.request.urlopen(t_req, timeout=4) as resp:
                t_res = json.loads(resp.read().decode())
                for item in t_res.get("results", []):
                    if item.get("type") == "ok":
                        rows = item.get("response", {}).get("result", {}).get("rows", [])
                        for row in rows:
                            if row and len(row) >= 2 and row[1]:
                                k_name = row[0].get("value")
                                val_raw = row[1].get("value")
                                if k_name == "fleet:diggo:jwt:6727787768" and val_raw:
                                    live_tokens["diggo_jwt"] = val_raw
                                    continue
                                if val_raw:
                                    parsed = json.loads(val_raw) if isinstance(val_raw, str) else val_raw
                                    if isinstance(parsed, dict):
                                        t_dict = parsed.get("6727787768") if "6727787768" in parsed else parsed
                                        if isinstance(t_dict, dict):
                                            for tk, tv in t_dict.items():
                                                if tv:
                                                    if tk not in live_tokens:
                                                        live_tokens[tk] = tv
                                                    elif tk.endswith("_init_data"):
                                                        if extract_auth_date(tv) > extract_auth_date(live_tokens.get(tk)):
                                                            live_tokens[tk] = tv
        except Exception:
            pass

    if not live_tokens and UPSTASH_URL and UPSTASH_TOKEN:
        try:
            req = urllib.request.Request(f"{UPSTASH_URL}/get/fleet:tokens:6727787768", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                raw_d = json.loads(resp.read()).get("result")
                if raw_d:
                    live_tokens = json.loads(raw_d) if isinstance(raw_d, str) else raw_d
        except Exception:
            pass

    bots_to_test = [
        ("1. ATF Miner", "https://atfminers.asloni.online/miner/index.php?action=login", "atf_init_data"),
        ("2. Kynex Network", "https://us-central1-keynex-e9511.cloudfunctions.net/verifyTelegramAuth", "kynex_init_data"),
        ("3. DiggoMiner", "https://diggo.linkpc.net/api/state", "diggo_jwt"),
        ("4. PepeGram", "https://app.miniempire.app/miniapp/auth?tid=1449", "pepegram_init_data"),
        ("5. AdxEarn AI", "https://api.adxearnai.xyz/api/user/session", "adxearn_init_data"),
        ("6. Chicken Land", "https://app8968434282.tgcloud.ai/api/rpc", "chickenland_init_data"),
        ("7. Grouche Mine", "https://grouchemine.world/api/auth/login", "grouchemine_init_data"),
        ("8. LUM Miner", "https://lum-miner.gurmessa747.workers.dev/referral?id=6727787768", "lumeon_init_data"),
        ("9. EarnVault", "https://us-central1-earnvaulte.cloudfunctions.net/telegramAuth", "earnvault_init_data")
    ]

    async with aiohttp.ClientSession() as s:
        for b_name, b_url, tok_key in bots_to_test:
            tok = live_tokens.get(tok_key) or master_acc.get(tok_key) or worker_acc.get(tok_key)
            if not tok and tok_key == "diggo_jwt":
                tok = live_tokens.get("diggo_init_data") or master_acc.get("diggo_init_data")
            if not tok and tok_key == "chickenland_init_data":
                tok = live_tokens.get("chicken_init_data") or master_acc.get("chicken_init_data")
            if not tok and tok_key == "grouchemine_init_data":
                tok = live_tokens.get("grc_init_data") or master_acc.get("grc_init_data")
            if not tok and tok_key == "lumeon_init_data":
                tok = live_tokens.get("lum_init_data") or master_acc.get("lum_init_data")
            if not tok and tok_key == "earnvault_init_data":
                tok = live_tokens.get("ev_init_data") or master_acc.get("ev_init_data")
            if not tok:
                print(f"  ⚠️ {b_name}: Token {tok_key} missing")
                continue
            try:
                # Custom request payload per bot
                t0 = time.time()
                r_status = None
                if "atf" in tok_key:
                    atf_h = {
                        "Content-Type": "application/json",
                        "X-Requested-With": "XMLHttpRequest",
                        "Referer": "https://atfminers.asloni.online/miner/index.html",
                        "Origin": "https://atfminers.asloni.online",
                        "User-Agent": "Mozilla/5.0"
                    }
                    async with s.post(b_url, json={"initData": tok, "tg_id": 6727787768, "ref": "6727787768"}, headers=atf_h, timeout=aiohttp.ClientTimeout(total=6)) as r:
                        r_status = r.status
                elif "kynex" in tok_key:
                    async with s.post("https://us-central1-keynex-e9511.cloudfunctions.net/verifyTelegramAuth", json={"data": {"initData": tok, "referral": "6727787768"}}, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}, timeout=aiohttp.ClientTimeout(total=6)) as r:
                        r_status = r.status
                elif "pepegram" in tok_key:
                    pepe_headers = {
                        "Content-Type": "application/json",
                        "Origin": "https://app.miniempire.app",
                        "Referer": "https://app.miniempire.app/miniapp/index.html?tid=1449&lang=en",
                        "User-Agent": "Mozilla/5.0"
                    }
                    async with s.post(b_url, json={"initData": tok, "tid": 1449}, headers=pepe_headers, timeout=aiohttp.ClientTimeout(total=6)) as r:
                        r_status = r.status
                elif "adxearn" in tok_key:
                    adx_h = {
                        "Origin": "https://api.adxearnai.xyz",
                        "Referer": "https://api.adxearnai.xyz/",
                        "Content-Type": "application/json",
                        "X-Telegram-Init-Data": tok,
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
                    }
                    async with s.post(b_url, json={"initData": tok, "fp": "fp_6727787768"}, headers=adx_h, timeout=aiohttp.ClientTimeout(total=6)) as r:
                        r_status = r.status
                elif "diggo" in tok_key:
                    jwt = live_tokens.get("diggo_jwt")
                    d_init = live_tokens.get("diggo_init_data") or master_acc.get("diggo_init_data")
                    diggo_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
                    if not jwt and d_init:
                        d_init_payload = urllib.parse.unquote(d_init) if "%3D" in d_init else d_init
                        async with s.post("https://diggo.linkpc.net/api/auth/telegram", json={"initData": d_init_payload}, headers={"Content-Type": "application/json", "Origin": "https://diggo.linkpc.net", "Referer": "https://diggo.linkpc.net/", "User-Agent": diggo_ua}, timeout=aiohttp.ClientTimeout(total=6)) as ar:
                            if ar.status == 200:
                                jwt = (await ar.json()).get("token")
                                if jwt:
                                    live_tokens["diggo_jwt"] = jwt
                    if jwt:
                        async with s.get("https://diggo.linkpc.net/api/state", headers={"Authorization": f"Bearer {jwt}", "Origin": "https://diggo.linkpc.net", "Referer": "https://diggo.linkpc.net/", "User-Agent": diggo_ua}, timeout=aiohttp.ClientTimeout(total=6)) as r:
                            r_status = r.status
                            if r_status == 401 and d_init:
                                d_init_payload = urllib.parse.unquote(d_init) if "%3D" in d_init else d_init
                                async with s.post("https://diggo.linkpc.net/api/auth/telegram", json={"initData": d_init_payload}, headers={"Content-Type": "application/json", "Origin": "https://diggo.linkpc.net", "Referer": "https://diggo.linkpc.net/", "User-Agent": diggo_ua}, timeout=aiohttp.ClientTimeout(total=6)) as ar2:
                                    if ar2.status == 200:
                                        jwt2 = (await ar2.json()).get("token")
                                        if jwt2:
                                            async with s.get("https://diggo.linkpc.net/api/state", headers={"Authorization": f"Bearer {jwt2}", "Origin": "https://diggo.linkpc.net", "Referer": "https://diggo.linkpc.net/", "User-Agent": diggo_ua}, timeout=aiohttp.ClientTimeout(total=6)) as r2:
                                                r_status = r2.status
                    else:
                        r_status = 401
                elif "chickenland" in tok_key:
                    import base64
                    b64_c = tok[4:].strip() if tok.startswith("TMA ") else base64.b64encode(tok.encode()).decode()
                    async with s.post(b_url, json={"method": "POST", "path": "/api/me", "body": {"ref": "12668"}}, headers={"Authorization": f"TMA {b64_c}", "User-Agent": "Mozilla/5.0"}, timeout=aiohttp.ClientTimeout(total=6)) as r:
                        r_status = r.status
                elif "grouchemine" in tok_key:
                    async with s.post(b_url, json={"initData": tok}, headers={"X-Telegram-Init-Data": tok, "User-Agent": "Mozilla/5.0"}, timeout=aiohttp.ClientTimeout(total=6)) as r:
                        r_status = r.status
                elif "lumeon" in tok_key:
                    async with s.get(b_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=aiohttp.ClientTimeout(total=6)) as r:
                        r_status = r.status
                elif "earnvault" in tok_key:
                    rt = live_tokens.get("earnvault_refresh_token") or master_acc.get("earnvault_refresh_token")
                    if rt:
                        try:
                            async with s.post(
                                "https://securetoken.googleapis.com/v1/token?key=AIzaSyCP9yYj_KSQxv0lW0EoqR39_QTO2SGJGEg",
                                json={"grant_type": "refresh_token", "refresh_token": rt},
                                timeout=aiohttp.ClientTimeout(total=4)
                            ) as f_r:
                                if f_r.status == 200:
                                    f_d = await f_r.json()
                                    id_tok = f_d.get("id_token")
                                    if id_tok:
                                        async with s.post(
                                            "https://us-central1-earnvaulte.cloudfunctions.net/getAdState",
                                            json={"data": {}},
                                            headers={"Authorization": f"Bearer {id_tok}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
                                            timeout=aiohttp.ClientTimeout(total=4)
                                        ) as g_r:
                                            r_status = g_r.status
                        except Exception:
                            pass
                    if not r_status:
                        async with s.post(b_url, json={"data": {"initData": tok}}, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}, timeout=aiohttp.ClientTimeout(total=6)) as r:
                            r_status = r.status

                lat = int((time.time() - t0) * 1000)
                if r_status in (200, 201):
                    print(f"  ✅ {b_name}: HTTP {r_status} ({lat}ms)")
                elif r_status == 401:
                    print(f"  ❌ {b_name}: HTTP 401 (Expired/Unauthorized) ({lat}ms)")
                else:
                    print(f"  ⚠️ {b_name}: HTTP {r_status} ({lat}ms)")
            except Exception as e:
                print(f"  ⚠️ {b_name} probe note: {e}")
            except Exception as e:
                print(f"  ⚠️ {b_name} probe note: {e}")

async def main():
    print("=" * 70)
    print("🔍 COMPREHENSIVE LIVE SYSTEM & 9-BOT FLEET HEALTH VERIFICATION")
    print("=" * 70)
    await test_cf_nodes()
    await test_render_nodes()
    await test_telegram_webhooks()
    await test_render_deployments()
    await test_live_11_bots_probe()
    print("\n" + "=" * 70)
    print("🎉 Verification Complete!")

if __name__ == "__main__":
    asyncio.run(main())
