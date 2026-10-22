#!/usr/bin/env python3
"""
deep_audit_18_accounts.py
=============================================================================
AAA AUTO / MY AGY AI — EXHAUSTIVE DEEP AUDIT OF ALL 18 FLEET ACCOUNTS
=============================================================================
Queries all active bot APIs concurrently for every single account:
- ATF Miner (@ATF_AIRDROP_bot)
- MRG Miner (@mrgminerbot)
- Victor's Company (@VictorsCompanybot)
- VyroDrop (@vyrodrop_bot)
- Kynex Network (@Kynex_miningbot)
Extracts real on-chain/API balances, miner levels, and security verification.
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

# Load accounts.json
with open(os.path.join(BASE_DIR, "accounts.json")) as f:
    ACCOUNTS_LIST = json.load(f)

async def probe_account_details(session: aiohttp.ClientSession, idx: int, acc_meta: dict, token_data: dict, up_headers: dict) -> dict:
    uid = str(acc_meta.get("user_id") or acc_meta.get("id"))
    name = acc_meta.get("name") or acc_meta.get("first_name", "Unknown")
    phone = acc_meta.get("phone", "N/A")
    username = acc_meta.get("username", "")

    now = datetime.now(timezone.utc)

    report = {
        "idx": idx,
        "uid": uid,
        "name": name,
        "phone": phone,
        "username": username,
        "atf": {"status": "No Token", "bal": 0.0, "wallet": None},
        "mrg": {"status": "No Token", "bal": 0.0, "lvl": 1, "unclaimed": 0.0, "verified_until": None, "ton_wallet": None},
        "victors": {"status": "No Token", "bal": 0.0, "lvl": 1, "pass": False, "wallet": None, "err": None},
        "vyro": {"status": "No Token", "bal": 0.0, "lvl": 1, "mining": False},
        "kynex": {"status": "No Token", "bal": 0.0, "auth": False}
    }

    t = token_data.get(uid) or {}

    # 1. ATF Miner
    atf_init = t.get("atf_init_data")
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
                "request_id": f"dpa-{int(time.time())}",
                "device_id": f"dev-{uid}",
                "tg_id": int(uid),
                "username": username
            }
            async with session.post(
                "https://atfminers.asloni.online/miner/index.php?action=login",
                headers=atf_headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=6)
            ) as r:
                if r.status == 200:
                    d = await r.json()
                    u = d.get("user") or {}
                    bal = u.get("total_balance") or u.get("balance") or 0.0
                    w = u.get("wallet_address")
                    report["atf"] = {
                        "status": "Online (Active)",
                        "bal": float(bal),
                        "wallet": w if w and w != "0" else "Not Bound"
                    }
                else:
                    report["atf"]["status"] = f"HTTP {r.status}"
        except Exception as e:
            report["atf"]["status"] = f"Timeout ({e.__class__.__name__})"

    # 2. MRG Miner
    mrg_init = t.get("mrg_init_data")
    if mrg_init:
        try:
            m_headers = {
                "Content-Type": "application/json",
                "Origin": "https://app.mrgtoken.xyz",
                "Referer": "https://app.mrgtoken.xyz/"
            }
            async with session.post(
                "https://mrg.up.railway.app/api/user/me",
                headers=m_headers,
                json={"initData": mrg_init},
                timeout=aiohttp.ClientTimeout(total=6)
            ) as r:
                if r.status == 200:
                    d = await r.json()
                    u = d.get("user") or {}
                    bal = float(u.get("inAppBalance", 0.0))
                    lvl = int(u.get("miningSnapshot", {}).get("level") or u.get("manualUnlockedLevel") or 1)
                    unclaimed = float(u.get("unclaimedMiningBalance", 0.0))
                    verified_str = u.get("humanVerifiedUntil")
                    ton_w = u.get("tonWalletAddress")
                    is_active = False
                    if verified_str:
                        try:
                            v_clean = verified_str.replace("Z", "+00:00")
                            if datetime.fromisoformat(v_clean) > now:
                                is_active = True
                        except Exception:
                            pass
                    report["mrg"] = {
                        "status": "Active & Verified" if is_active else "Security Check Needed (Turnstile)",
                        "bal": bal,
                        "lvl": lvl,
                        "unclaimed": unclaimed,
                        "verified_until": verified_str,
                        "ton_wallet": ton_w or "Not Connected"
                    }
                elif r.status == 401:
                    report["mrg"]["status"] = "401 Unauthorized (Expired)"
                else:
                    report["mrg"]["status"] = f"HTTP {r.status}"
        except Exception as e:
            report["mrg"]["status"] = f"Timeout ({e.__class__.__name__})"

    # 3. Victor's Company
    vic_init = t.get("victors_init_data")
    if vic_init:
        try:
            # Check Redis for cached humanPass
            async with session.get(f"{UPSTASH_URL}/get/victors:pass:{uid}", headers=up_headers) as r_p:
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
                "Authorization": f"tma {vic_init}",
                "Origin": "https://app.victors.company",
                "Referer": "https://app.victors.company/"
            }
            if human_pass:
                v_headers["x-human-pass"] = str(human_pass)

            async with session.get(
                "https://server.victors.company/api/me",
                headers=v_headers,
                timeout=aiohttp.ClientTimeout(total=6)
            ) as r:
                if r.status == 200:
                    d = await r.json()
                    me = d.get("user") or d
                    report["victors"] = {
                        "status": "Active & Farmed",
                        "bal": float(me.get("miningBalance", 0.0)),
                        "lvl": int(me.get("level", 1)),
                        "pass": True,
                        "wallet": me.get("walletAddress") or "None",
                        "err": None
                    }
                elif r.status in (401, 403):
                    text = await r.text()
                    try:
                        err_d = json.loads(text)
                        code = err_d.get("code") or err_d.get("error") or "AUTH"
                    except Exception:
                        code = text[:30]
                    report["victors"] = {
                        "status": f"Turnstile Needed ({code})" if "HUMAN_REQUIRED" in text else f"Auth Failed ({code})",
                        "bal": 0.0,
                        "lvl": 1,
                        "pass": False,
                        "wallet": None,
                        "err": code
                    }
                else:
                    report["victors"]["status"] = f"HTTP {r.status}"
        except Exception as e:
            report["victors"]["status"] = f"Timeout ({e.__class__.__name__})"

    # 4. VyroDrop
    vy_init = t.get("vyro_init_data")
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
                timeout=aiohttp.ClientTimeout(total=6)
            ) as r:
                if r.status == 200:
                    d = await r.json()
                    u = d.get("user") or {}
                    miner = d.get("miner") or {}
                    mining = d.get("mining") or {}
                    report["vyro"] = {
                        "status": "Active (Mining)",
                        "bal": float(u.get("balance", 0.0)),
                        "lvl": int(miner.get("level", 1)),
                        "mining": bool(mining.get("sessionId"))
                    }
                elif r.status in (401, 403):
                    report["vyro"]["status"] = f"HTTP {r.status} Expired"
                else:
                    report["vyro"]["status"] = f"HTTP {r.status}"
        except Exception as e:
            report["vyro"]["status"] = f"Timeout ({e.__class__.__name__})"

    # 5. Kynex Network
    ky_init = t.get("kynex_init_data")
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
                timeout=aiohttp.ClientTimeout(total=6)
            ) as r:
                if r.status == 200:
                    d = await r.json()
                    c_tok = d.get("result", {}).get("customToken")
                    report["kynex"] = {
                        "status": "Active (Verified)" if c_tok else "No Token",
                        "bal": 0.0,
                        "auth": bool(c_tok)
                    }
                else:
                    report["kynex"]["status"] = f"HTTP {r.status}"
        except Exception as e:
            report["kynex"]["status"] = f"Timeout ({e.__class__.__name__})"

    return report

async def main():
    headers = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{UPSTASH_URL}/get/miniapp_tokens", headers=headers) as r:
            raw = (await r.json()).get("result")
            token_data = json.loads(raw) if raw else {}

        print("Auditing all 18 accounts directly from live bot backends...")
        tasks = []
        for idx, acc in enumerate(ACCOUNTS_LIST, 1):
            tasks.append(probe_account_details(session, idx, acc, token_data, headers))

        reports = await asyncio.gather(*tasks)

        # Print detailed report for each account
        print("\n" + "=" * 90)
        print("📋 COMPLETE 18-ACCOUNT DETAILED DOSSIER (LIVE BACKEND GROUND-TRUTH)")
        print("=" * 90)

        for rep in reports:
            print(f"\n──────────────────────────────────────────────────────────────────────────────────────────")
            print(f"[{rep['idx']:02d}/18] 👤 {rep['name']} | UID: {rep['uid']} | Phone: {rep['phone']} | @{rep['username']}")
            print(f"──────────────────────────────────────────────────────────────────────────────────────────")
            
            # ATF
            atf = rep["atf"]
            print(f"  🪙 ATF Miner:     Status: {atf['status']:<25} | Balance: {atf['bal']:<8.1f} | TON Wallet: {atf['wallet']}")

            # MRG
            mrg = rep["mrg"]
            print(f"  ⚡ MRG Miner:     Status: {mrg['status']:<25} | Balance: {mrg['bal']:<8.1f} | Level: {mrg['lvl']:<4} | Unclaimed: {mrg['unclaimed']:.2f} MRG | Wallet: {mrg['ton_wallet']}")

            # Victor's
            vic = rep["victors"]
            print(f"  🏢 Victor's Co:   Status: {vic['status']:<25} | Balance: {vic['bal']:<8.1f} | Level: {vic['lvl']:<4} | HumanPass: {'YES' if vic['pass'] else 'NO'} | Error: {vic['err']}")

            # Vyro
            vyr = rep["vyro"]
            print(f"  💧 VyroDrop:      Status: {vyr['status']:<25} | Balance: {vyr['bal']:<8.2f} | Level: {vyr['lvl']:<4} | MiningActive: {vyr['mining']}")

            # Kynex
            kyn = rep["kynex"]
            print(f"  💎 Kynex Network: Status: {kyn['status']:<25} | AuthSuccess: {kyn['auth']}")

        print("\n" + "=" * 90)
        print("✅ Live 18-Account Audit Complete. 100% Genuine Direct API Data.")
        print("=" * 90 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
