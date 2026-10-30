#!/usr/bin/env python3
"""
audit_fleet_live.py
=============================================================================
AAA AUTO / MY AGY AI — 100% AUTHENTIC LIVE GROUND-TRUTH FLEET AUDITOR
=============================================================================
Directly queries live bot backends and APIs per account across all 20 accounts
and all 9 legitimate mining pools (ATF, MRG, Victor's, Vyro, Kynex, Diggo, PepeGram, AdxEarn, Astra).
Zero blind trust, zero fake reports, 100% authentic ground-truth audit.
"""

import os
import sys
import json
import time
import asyncio
import aiohttp
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(BASE_DIR, ".env")
env = {}
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")

UPSTASH_URL = env.get("UPSTASH_URL") or env.get("UPSTASH_REDIS_REST_URL") or "https://internal-dodo-83852.upstash.io"
UPSTASH_TOKEN = env.get("UPSTASH_TOKEN") or env.get("UPSTASH_REDIS_REST_TOKEN") or ""

BROWSER_UA = "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36"

ASTRA_SB_KEY = __import__("base64").b64decode("ZXlKaGJHY2lPaUpJVXpJMU5pSXNJblI1Y0NJNklrcFhWQ0o5LmV5SnBjM01pT2lKemRYQmhZbUZ6WlNJc0luSmxaaUk2SW1KalluZHhibXRtZVhKd2FtaGpkR1Z6ZG01d0lpd2ljbTlzWlNJNkltRnViMjRpTENKcFlYUWlPakUzT1RBeE5UVTRNVGtzSW1WNGNDSTZNakV3TlRjek1UZ3hPWDAuNi10aVQtaFdjaklPUEFwWkpLejZRdlgzRUVxbkhfRk1IR1hscllRN2xRZw==").decode()

async def audit_single_account(session: aiohttp.ClientSession, uid: str, acc: dict, headers: dict, idx: int = 1) -> dict:
    name = (acc.get("name") or "User")[:15]
    now = datetime.now(timezone.utc)
    res = {
        "idx": idx,
        "uid": uid,
        "name": name,
        "atf": "⚪ NoTok",
        "mrg": "⚪ NoTok",
        "victors": "⚪ NoTok",
        "vyro": "⚪ NoTok",
        "kynex": "⚪ NoTok",
        "diggo": "⚪ NoTok",
        "pepe": "⚪ NoTok",
        "adx": "⚪ NoTok",
        "astra": "⚪ NoTok"
    }

    # 1. ATF Miner
    atf_init = acc.get("atf_init_data")
    if atf_init:
        try:
            atf_headers = {
                "User-Agent": BROWSER_UA,
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://atfminers.asloni.online/miner/index.html",
                "Origin": "https://atfminers.asloni.online"
            }
            payload = {
                "initData": atf_init,
                "request_id": f"aud-{int(time.time())}",
                "device_id": f"dev-{uid}",
                "tg_id": int(uid),
                "username": acc.get("username", "")
            }
            async with session.post(
                "https://atfminers.asloni.online/miner/index.php?action=login",
                headers=atf_headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as r:
                if r.status == 200:
                    d = await r.json()
                    u = d.get("user") or {}
                    bal = u.get("total_balance") or u.get("balance") or 0
                    res["atf"] = f"🟢 {float(bal):.1f}"
                elif r.status == 401:
                    try:
                        d = await r.json()
                        reason = d.get("reason", "")
                        if "auth_date" in reason or "old" in reason or "expired" in reason:
                            res["atf"] = "🔴 Exp (24h)"
                        else:
                            res["atf"] = "🔴 401 Auth"
                    except Exception:
                        res["atf"] = "🔴 401 Exp"
                else:
                    res["atf"] = f"🔴 {r.status}"
        except Exception:
            res["atf"] = "🔴 Timeout"

    # 2. MRG Miner
    m_init = acc.get("mrg_init_data")
    if m_init:
        try:
            m_headers = {
                "Content-Type": "application/json",
                "Origin": "https://app.mrgtoken.xyz",
                "Referer": "https://app.mrgtoken.xyz/"
            }
            async with session.post(
                "https://mrg.up.railway.app/api/user/me",
                headers=m_headers,
                json={"initData": m_init},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as r:
                if r.status == 200:
                    d = await r.json()
                    u = d.get("user") or {}
                    bal = u.get("inAppBalance", 0)
                    lvl = u.get("miningSnapshot", {}).get("level") or u.get("manualUnlockedLevel") or 1
                    verified_until_str = u.get("humanVerifiedUntil")
                    is_active = False
                    if verified_until_str:
                        try:
                            clean_str = verified_until_str.replace("Z", "+00:00")
                            v_dt = datetime.fromisoformat(clean_str)
                            if v_dt > now:
                                is_active = True
                        except Exception:
                            pass
                    if is_active:
                        res["mrg"] = f"🟢 L{lvl} {float(bal):.0f}"
                    else:
                        res["mrg"] = f"🟡 SecReq {float(bal):.0f}"
                elif r.status == 401:
                    res["mrg"] = "🔴 401 Exp"
                else:
                    res["mrg"] = f"🔴 {r.status}"
        except Exception:
            res["mrg"] = "🔴 Timeout"

    # 3. Victor's Company
    v_init = acc.get("victors_init_data")
    if v_init:
        try:
            async with session.get(f"{UPSTASH_URL}/get/victors:pass:{uid}", headers=headers, timeout=aiohttp.ClientTimeout(total=3)) as r_p:
                p_raw = (await r_p.json()).get("result")
                human_pass = None
                if p_raw:
                    try:
                        p_obj = json.loads(p_raw) if isinstance(p_raw, str) else p_raw
                        human_pass = p_obj.get("humanPass") if isinstance(p_obj, dict) else p_obj
                    except Exception:
                        human_pass = p_raw

            v_headers = {
                "Content-Type": "application/json",
                "Authorization": f"tma {v_init}",
                "Origin": "https://app.victors.company",
                "Referer": "https://app.victors.company/"
            }
            if human_pass:
                v_headers["x-human-pass"] = str(human_pass)

            async with session.get(
                "https://server.victors.company/api/me",
                headers=v_headers,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as r:
                if r.status == 200:
                    d = await r.json()
                    me = d.get("user") or d
                    lvl = me.get("level", 1)
                    bal = me.get("miningBalance", 0)
                    res["victors"] = f"🟢 L{lvl} {float(bal):.0f}"
                elif r.status == 401 or r.status == 403:
                    body = await r.text()
                    if "HUMAN_REQUIRED" in body:
                        res["victors"] = "🟡 Turnstile"
                    elif "TG_AUTH" in body or "expired" in body.lower():
                        res["victors"] = "🔴 401 Exp"
                    else:
                        res["victors"] = "🔴 401 Auth"
                else:
                    res["victors"] = f"🔴 {r.status}"
        except Exception:
            res["victors"] = "🔴 Timeout"

    # 4. VyroDrop
    vy_init = acc.get("vyro_init_data")
    if vy_init:
        try:
            vy_headers = {
                "Content-Type": "application/json",
                "Authorization": f"tma {vy_init}",
                "X-Vyro-UI-Contract": "claim-inactivity-v1",
                "Referer": "https://vyro.run.place/"
            }
            async with session.get(
                "https://vyro.run.place/api/bootstrap",
                headers=vy_headers,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as r:
                if r.status == 200:
                    d = await r.json()
                    miner = d.get("miner") or {}
                    lvl = miner.get("level", 1)
                    res["vyro"] = f"🟢 L{lvl}"
                elif r.status in (401, 403):
                    res["vyro"] = f"🔴 {r.status} Exp"
                else:
                    res["vyro"] = f"🔴 {r.status}"
        except Exception:
            res["vyro"] = "🔴 Timeout"

    # 5. Kynex Network
    ky_init = acc.get("kynex_init_data")
    if ky_init:
        try:
            ky_headers = {
                "Content-Type": "application/json",
                "Origin": "https://kynex.top",
                "Referer": "https://kynex.top/telegram-auth.html"
            }
            async with session.post(
                "https://us-central1-keynex-e9511.cloudfunctions.net/verifyTelegramAuth",
                headers=ky_headers,
                json={"data": {"initData": ky_init}},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as r:
                if r.status == 200:
                    d = await r.json()
                    res["kynex"] = "🟢 Active" if d.get("result", {}).get("customToken") else "🔴 NoTok"
                elif r.status in (401, 403):
                    res["kynex"] = f"🔴 {r.status}"
                else:
                    res["kynex"] = f"🔴 {r.status}"
        except Exception:
            res["kynex"] = "🔴 Timeout"

    # 6. DiggoMiner
    try:
        jwt_tok = None
        async with session.get(f"{UPSTASH_URL}/get/fleet:diggo:jwt:{uid}", headers=headers, timeout=aiohttp.ClientTimeout(total=3)) as jr:
            if jr.status == 200:
                jd = await jr.json()
                if jd.get("result"):
                    jwt_tok = str(jd["result"]).strip()
        if jwt_tok:
            d_headers = {"Authorization": f"Bearer {jwt_tok}", "User-Agent": BROWSER_UA}
            async with session.get("https://diggo.linkpc.net/api/state", headers=d_headers, timeout=aiohttp.ClientTimeout(total=5)) as r:
                if r.status == 200:
                    st_data = await r.json()
                    st = st_data.get("state") or {}
                    bal = st.get("balance", 0)
                    res["diggo"] = f"🟢 {float(bal):.0f}"
                elif r.status in (401, 403):
                    res["diggo"] = f"🔴 {r.status} Exp"
                else:
                    res["diggo"] = f"🔴 {r.status}"
        else:
            res["diggo"] = "⚪ No Tok"
    except Exception:
        res["diggo"] = "🔴 Timeout"

    # 7. PepeGram
    pepe_init = acc.get("pepegram_init_data")
    if pepe_init:
        try:
            pepe_headers = {"Content-Type": "application/json", "User-Agent": BROWSER_UA, "Origin": "https://app.miniempire.app"}
            async with session.post(
                "https://app.miniempire.app/miniapp/auth?tid=1449",
                headers=pepe_headers,
                json={"initData": pepe_init, "tid": 1449},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as r:
                if r.status == 200:
                    d = await r.json()
                    u = d.get("user") or {}
                    power = u.get("power", 0)
                    res["pepe"] = f"🟢 P{power}"
                elif r.status in (401, 403):
                    res["pepe"] = f"🔴 {r.status}"
                else:
                    res["pepe"] = f"🔴 {r.status}"
        except Exception:
            res["pepe"] = "🔴 Timeout"

    # 8. AdxEarn AI
    adx_init = acc.get("adxearn_init_data")
    if adx_init:
        try:
            adx_headers = {"Content-Type": "application/json", "X-Telegram-Init-Data": adx_init, "User-Agent": BROWSER_UA}
            async with session.post(
                "https://api.adxearnai.xyz/api/user/session",
                headers=adx_headers,
                json={"fp": "412x915|24|8"},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as r:
                if r.status == 200:
                    d = await r.json()
                    pts = d.get("user", {}).get("balance_points", 0)
                    res["adx"] = f"🟢 {pts}pts"
                elif r.status in (401, 403):
                    res["adx"] = f"🔴 {r.status}"
                else:
                    res["adx"] = f"🔴 {r.status}"
        except Exception:
            res["adx"] = "🔴 Timeout"

    # 9. Astra Airdrop
    astra_init = acc.get("astra_init_data")
    if astra_init:
        try:
            q = urllib.parse.parse_qs(astra_init, keep_blank_values=True)
            flat_q = {k: v[0] for k, v in q.items()}
            hash_val = flat_q.pop("hash", "")
            p_dcs = "\n".join(f"{k}={v}" for k, v in sorted(flat_q.items()))
            sb_url = "https://bcbwqnkfyrpjhctesvnp.supabase.co"
            async with session.post(
                f"{sb_url}/rest/v1/rpc/astra_login",
                json={"p_dcs": p_dcs, "p_hash": hash_val},
                headers={"apikey": ASTRA_SB_KEY, "Authorization": f"Bearer {ASTRA_SB_KEY}"},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as r:
                if r.status == 200:
                    d = await r.json()
                    bal = d.get("user", {}).get("mined_balance", 0)
                    res["astra"] = f"🟢 {float(bal):.1f}"
                elif r.status == 402:
                    res["astra"] = "🟡 Egress"
                elif r.status in (401, 403):
                    res["astra"] = f"🔴 {r.status}"
                else:
                    res["astra"] = f"🔴 {r.status}"
        except Exception:
            res["astra"] = "🔴 Timeout"

    return res

async def audit_all_accounts():
    headers = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        # 1. Load canonical accounts list
        accounts = []
        try:
            async with session.get(f"{UPSTASH_URL}/get/fleet:accounts", headers=headers) as r:
                if r.status == 200:
                    raw = (await r.json()).get("result")
                    accounts = json.loads(raw) if raw else []
        except Exception:
            pass

        if not accounts and os.path.exists(os.path.join(BASE_DIR, "accounts.json")):
            with open(os.path.join(BASE_DIR, "accounts.json")) as f:
                accounts = json.load(f)

        accounts.sort(key=lambda x: int(x.get("index", 999)))

        # 2. Load miniapp_tokens from fleet_miniapp_tokens, miniapp_tokens & individual fleet:tokens:*
        tokens_map = {}
        try:
            async with session.get(f"{UPSTASH_URL}/get/fleet_miniapp_tokens", headers=headers) as r:
                if r.status == 200:
                    raw = (await r.json()).get("result")
                    if raw:
                        tokens_map.update(json.loads(raw) if isinstance(raw, str) else raw)
            async with session.get(f"{UPSTASH_URL}/get/miniapp_tokens", headers=headers) as r:
                if r.status == 200:
                    raw = (await r.json()).get("result")
                    if raw:
                        for k, v in (json.loads(raw) if isinstance(raw, str) else raw).items():
                            if k not in tokens_map:
                                tokens_map[k] = v
                            else:
                                tokens_map[k].update(v)
            async with session.get(f"{UPSTASH_URL}/keys/fleet:tokens:*", headers=headers) as r:
                if r.status == 200:
                    k_list = (await r.json()).get("result", [])
                    if k_list:
                        pipe_payload = [["get", k] for k in k_list]
                        async with session.post(f"{UPSTASH_URL}/pipeline", json=pipe_payload, headers=headers) as pr:
                            if pr.status == 200:
                                p_res = await pr.json()
                                for item in p_res:
                                    res_str = item.get("result")
                                    if res_str:
                                        t_item = json.loads(res_str) if isinstance(res_str, str) else res_str
                                        u_id = str(t_item.get("account_id") or "")
                                        if u_id:
                                            if u_id not in tokens_map:
                                                tokens_map[u_id] = t_item
                                            else:
                                                tokens_map[u_id].update(t_item)
        except Exception:
            pass

        print("\n" + "="*124)
        print("🚀 LIVE GROUND-TRUTH FLEET AUDITOR (ALL 20 ACCOUNTS • ALL 9 ACTIVE LEGITIMATE MINING POOLS)")
        print("="*124)
        print(f"{'Idx':<4} {'Name':<15} {'UID':<11} {'ATF':<9} {'MRG':<12} {'Victor':<11} {'Vyro':<9} {'Kynex':<9} {'Diggo':<9} {'Pepe':<9} {'Adx':<9} {'Astra':<9}")
        print("-" * 124)

        tasks = []
        for acc in accounts:
            uid = str(acc.get("user_id"))
            idx = int(acc.get("index", 1))
            acc_tok = tokens_map.get(uid, {})
            # Merge account record with tokens
            merged = {**acc, **acc_tok}
            tasks.append(audit_single_account(session, uid, merged, headers, idx=idx))

        results = await asyncio.gather(*tasks)

        pools = ["atf", "mrg", "victors", "vyro", "kynex", "diggo", "pepe", "adx", "astra"]
        stats = {b: {"ok": 0, "warn": 0, "err": 0} for b in pools}

        for res in results:
            for b in pools:
                val = res[b]
                if "🟢" in val:
                    stats[b]["ok"] += 1
                elif "🟡" in val:
                    stats[b]["warn"] += 1
                else:
                    stats[b]["err"] += 1

            print(f"{res['idx']:<4} {res['name']:<15} {res['uid']:<11} {res['atf']:<9} {res['mrg']:<12} {res['victors']:<11} {res['vyro']:<9} {res['kynex']:<9} {res['diggo']:<9} {res['pepe']:<9} {res['adx']:<9} {res['astra']:<9}")

        print("-" * 124)
        print(f"📊 FLEET SUMMARY ({len(results)} Accounts Tested Against Live Cloud Backends):")
        print(f"• 🪙 ATF Miner:     🟢 {stats['atf']['ok']} Online | 🔴 {stats['atf']['err']} Offline")
        print(f"• ⚡ MRG Miner:     🟢 {stats['mrg']['ok']} Active | 🟡 {stats['mrg']['warn']} Turnstile Required | 🔴 {stats['mrg']['err']} Expired")
        print(f"• 🏢 Victor's Co:   🟢 {stats['victors']['ok']} Active | 🟡 {stats['victors']['warn']} Turnstile Required | 🔴 {stats['victors']['err']} Expired")
        print(f"• 💧 VyroDrop:      🟢 {stats['vyro']['ok']} Active | 🔴 {stats['vyro']['err']} Offline")
        print(f"• 💎 Kynex Network: 🟢 {stats['kynex']['ok']} Active | 🔴 {stats['kynex']['err']} Offline")
        print(f"• ⛏️ DiggoMiner:    🟢 {stats['diggo']['ok']} Active | 🔴 {stats['diggo']['err']} Offline")
        print(f"• 🐸 PepeGram:      🟢 {stats['pepe']['ok']} Active | 🔴 {stats['pepe']['err']} Offline")
        print(f"• 📈 AdxEarn AI:    🟢 {stats['adx']['ok']} Active | 🔴 {stats['adx']['err']} Offline")
        print(f"• 🪐 Astra Airdrop: 🟢 {stats['astra']['ok']} Active | 🟡 {stats['astra']['warn']} Restricted (Egress Quota) | 🔴 {stats['astra']['err']} Offline")
        print("=" * 124 + "\n")

if __name__ == "__main__":
    asyncio.run(audit_all_accounts())
