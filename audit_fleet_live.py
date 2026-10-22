#!/usr/bin/env python3
"""
audit_fleet_live.py
=============================================================================
AAA AUTO / MY AGY AI — 100% AUTHENTIC LIVE GROUND-TRUTH FLEET AUDITOR
=============================================================================
Directly queries live bot backends and APIs per account.
Zero blind trust, zero fake reports, 100% authentic ground-truth audit.
Verifies real balances, active mining states, and Cloudflare Turnstile requirements.
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

UPSTASH_URL = env.get("UPSTASH_URL") or env.get("UPSTASH_REDIS_REST_URL") or "https://pleasant-locust-220893.upstash.io"
UPSTASH_TOKEN = env.get("UPSTASH_TOKEN") or env.get("UPSTASH_REDIS_REST_TOKEN") or ""

BROWSER_UA = "Mozilla/5.0 (Linux; Android 10; SM-A305F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36"

async def audit_single_account(session: aiohttp.ClientSession, uid: str, acc: dict, headers: dict) -> dict:
    name = (acc.get("name") or "User")[:15]
    now = datetime.now(timezone.utc)
    res = {
        "uid": uid,
        "name": name,
        "atf": "⚪ Idle",
        "mrg": "⚪ Idle",
        "victors": "⚪ Idle",
        "vyro": "⚪ Idle",
        "kynex": "⚪ Idle"
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
                else:
                    res["atf"] = f"🔴 {r.status}"
        except Exception:
            res["atf"] = "🔴 Timeout"
    else:
        res["atf"] = "⚪ No Tok"

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
                            # e.g. 2026-10-22T08:00:51.812Z
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
    else:
        res["mrg"] = "⚪ No Tok"

    # 3. Victor's Company
    v_init = acc.get("victors_init_data")
    if v_init:
        try:
            # Check if cached human pass exists in Redis
            async with session.get(f"{UPSTASH_URL}/get/victors:pass:{uid}", headers=headers) as r_p:
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
    else:
        res["victors"] = "⚪ No Tok"

    # 4. VyroDrop
    vy_init = acc.get("vyro_init_data")
    if vy_init:
        try:
            vy_headers = {
                "Content-Type": "application/json",
                "Authorization": f"tma {vy_init}",
                "X-Vyro-UI-Contract": "claim-inactivity-v1",
                "X-Vyro-Market-Balances": "2",
                "X-Vyro-Dex": "1",
                "Referer": "https://vyro.run.place/"
            }
            async with session.get(
                "https://vyro.run.place/api/bootstrap",
                headers=vy_headers,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as r:
                if r.status == 200:
                    d = await r.json()
                    u = d.get("user") or {}
                    miner = d.get("miner") or {}
                    lvl = miner.get("level", 1)
                    bal = u.get("balance", 0)
                    res["vyro"] = f"🟢 L{lvl} {float(bal):.2f}"
                elif r.status == 401 or r.status == 403:
                    res["vyro"] = f"🔴 {r.status} Exp"
                else:
                    res["vyro"] = f"🔴 {r.status}"
        except Exception:
            res["vyro"] = "🔴 Timeout"
    else:
        res["vyro"] = "⚪ No Tok"

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
                elif r.status == 401 or r.status == 403:
                    res["kynex"] = f"🔴 {r.status}"
                else:
                    res["kynex"] = f"🔴 {r.status}"
        except Exception:
            res["kynex"] = "🔴 Timeout"
    else:
        res["kynex"] = "⚪ No Tok"

    return res

async def audit_all_accounts():
    headers = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        # Load miniapp_tokens directly from Redis
        async with session.get(f"{UPSTASH_URL}/get/miniapp_tokens", headers=headers) as r:
            if r.status != 200:
                print(f"Error fetching miniapp_tokens: HTTP {r.status}")
                return
            d = await r.json()
            raw = d.get("result")
            tokens = json.loads(raw) if raw else {}

        print(f"\n==========================================================================================")
        print(f"🚀 LIVE GROUND-TRUTH FLEET AUDITOR (5 ACTIVE LEGITIMATE BOTS • ZERO FAKE DATA)")
        print(f"==========================================================================================")
        print(f"{'Idx':<4} {'Name':<16} {'UID':<12} {'ATF Miner':<14} {'MRG Miner':<15} {'Victor\'s':<14} {'VyroDrop':<14} {'Kynex':<10}")
        print(f"------------------------------------------------------------------------------------------")

        tasks = []
        for uid, acc in tokens.items():
            tasks.append(audit_single_account(session, str(uid), acc, headers))

        results = await asyncio.gather(*tasks)

        # Summary counters
        stats = {
            "atf": {"ok": 0, "warn": 0, "err": 0},
            "mrg": {"ok": 0, "warn": 0, "err": 0},
            "victors": {"ok": 0, "warn": 0, "err": 0},
            "vyro": {"ok": 0, "warn": 0, "err": 0},
            "kynex": {"ok": 0, "warn": 0, "err": 0}
        }

        for idx, res in enumerate(results, 1):
            for b in ["atf", "mrg", "victors", "vyro", "kynex"]:
                val = res[b]
                if "🟢" in val:
                    stats[b]["ok"] += 1
                elif "🟡" in val:
                    stats[b]["warn"] += 1
                else:
                    stats[b]["err"] += 1

            print(f"{idx:<4} {res['name']:<16} {res['uid']:<12} {res['atf']:<14} {res['mrg']:<15} {res['victors']:<14} {res['vyro']:<14} {res['kynex']:<10}")

        print(f"------------------------------------------------------------------------------------------")
        print(f"📊 FLEET SUMMARY ({len(results)} Accounts Tested Against Live Backends):")
        print(f"• 🪙 ATF Miner:     🟢 {stats['atf']['ok']} Online | 🔴 {stats['atf']['err']} Offline")
        print(f"• ⚡ MRG Miner:     🟢 {stats['mrg']['ok']} Active | 🟡 {stats['mrg']['warn']} Turnstile Required | 🔴 {stats['mrg']['err']} Expired")
        print(f"• 🏢 Victor's Co:   🟢 {stats['victors']['ok']} Active | 🟡 {stats['victors']['warn']} Turnstile Required | 🔴 {stats['victors']['err']} Expired")
        print(f"• 💧 VyroDrop:      🟢 {stats['vyro']['ok']} Active | 🔴 {stats['vyro']['err']} Offline")
        print(f"• 💎 Kynex Network: 🟢 {stats['kynex']['ok']} Active | 🔴 {stats['kynex']['err']} Offline")
        print(f"==========================================================================================\n")

if __name__ == "__main__":
    asyncio.run(audit_all_accounts())
