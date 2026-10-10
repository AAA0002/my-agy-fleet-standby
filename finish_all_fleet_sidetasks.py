#!/usr/bin/env python3
"""
finish_all_fleet_sidetasks.py
=============================================================================
COMPREHENSIVE MULTI-BOT FLEET SIDE-TASK HARVESTER & AUTOMATION ENGINE
=============================================================================
Sweeps and completes all available side-tasks, daily check-ins, social joins,
cooldown missions, wallet verifications, and referral commission claims across
all 18 accounts in the fleet for all 5 legitimate bots:
  1. MRG Miner (@mrg_miner_bot)
  2. ATF Miner (@atf_miner_bot)
  3. Victor's Company (@VictorsCompanybot)
  4. VyroDrop (@vyrodrop_bot)
  5. Kynex Network (@Kynex_miningbot)

Zero Phone Load (Rule 4): Runs once as a clean batch script in cloud/container,
exits cleanly, and persists updated tokens to Upstash Redis and Cloudflare Edge.
"""

import os
import sys
import json
import time
import random
import asyncio
import aiohttp
import re
import uuid
import logging
import urllib.parse
import urllib.request
from typing import Dict, Any, List

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("sidetask_sweeper")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Read environment variables
env = {}
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")

UPSTASH_URL = env.get("UPSTASH_URL") or env.get("UPSTASH_REDIS_REST_URL") or "https://relaxing-starfish-285827.upstash.io"
UPSTASH_TOKEN = env.get("UPSTASH_TOKEN") or env.get("UPSTASH_REDIS_REST_TOKEN") or "gQAAAAAABFyDAAIgcDI5MDYyYWZjNzYzNzk0ZmRjYjhmNTA4ZDI4ODlmODkzNw"
SECRET_KEY = env.get("SECRET_KEY") or "agy_cf_secret_7d36994e_2026"

CF_WORKERS = [
    "https://restore-agy.aaaai2.workers.dev",
    "https://restore-agy.aaa-bot.workers.dev",
    "https://restore-agy.aaa222.workers.dev",
    "https://restore-agy.agorameet.workers.dev",
    "https://restore-agy.aaaai.workers.dev"
]

MASTER_UID = "6727787768"
PRIMARY_TON_WALLET = "UQAWuK6X9s1fA0LzXGzM_81n1xL_T6_xY8Z_1x1x1x1x1x1"

# Load Accounts
accounts_path = os.path.join(BASE_DIR, "accounts.json")
with open(accounts_path, "r") as f:
    ACCOUNTS = json.load(f)

# Load TON Wallets
ton_wallets = {}
wallets_path = os.path.join(BASE_DIR, "fleet_ton_wallets.json")
if os.path.exists(wallets_path):
    try:
        with open(wallets_path, "r") as f:
            ton_wallets = json.load(f)
    except Exception:
        pass


def solve_atf_math(question_text: str) -> str:
    """Evaluates arithmetic questions like 'What is 12 + 15?' safely."""
    try:
        clean = re.sub(r"[^0-9\+\-\*\/\(\)\s]", "", question_text)
        parts = clean.split()
        if len(parts) >= 3:
            num1, op, num2 = parts[0], parts[1], parts[2]
            if op == "+": return str(int(num1) + int(num2))
            if op == "-": return str(int(num1) - int(num2))
            if op == "*": return str(int(num1) * int(num2))
            if op == "/": return str(int(num1) // int(num2))
    except Exception:
        pass
    return "0"


async def jitter(min_s: float = 0.5, max_s: float = 1.5):
    await asyncio.sleep(random.uniform(min_s, max_s))


# =============================================================================
# 1. TOKEN LOADER & CLOUD SYNC
# =============================================================================

async def fetch_all_tokens(session: aiohttp.ClientSession) -> Dict[str, Dict[str, str]]:
    """Loads tokens for all 18 accounts from Upstash Redis fleet:tokens:*."""
    tokens_db = {}
    up_h = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}
    
    # First, load from miniapp_tokens if available
    try:
        async with session.get(f"{UPSTASH_URL}/get/miniapp_tokens", headers=up_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
            if r.status == 200:
                d = await r.json()
                raw = d.get("result")
                while isinstance(raw, str):
                    raw = json.loads(raw)
                if isinstance(raw, dict):
                    tokens_db.update(raw)
    except Exception as e:
        logger.warning(f"Error loading miniapp_tokens: {e}")

    # Second, merge individual fleet:tokens:{uid}
    for acc in ACCOUNTS:
        uid = str(acc.get("user_id"))
        try:
            async with session.get(f"{UPSTASH_URL}/get/fleet:tokens:{uid}", headers=up_h, timeout=aiohttp.ClientTimeout(total=5)) as r:
                if r.status == 200:
                    d = await r.json()
                    raw = d.get("result")
                    if raw:
                        parsed = json.loads(raw) if isinstance(raw, str) else raw
                        if isinstance(parsed, dict):
                            existing = tokens_db.setdefault(uid, {})
                            existing.update(parsed)
        except Exception:
            pass

    return tokens_db


async def sync_token_to_cf(session: aiohttp.ClientSession, uid: str, token_dict: dict):
    """Syncs merged tokens to Cloudflare Worker edge nodes."""
    payload = {
        "account_id": str(uid),
        **token_dict
    }
    for cf_url in CF_WORKERS[:2]:
        try:
            async with session.post(
                f"{cf_url}/api/miniapp/tokens/sync",
                json=payload,
                headers={"Authorization": f"Bearer {SECRET_KEY}", "Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as r:
                pass
        except Exception:
            pass


# =============================================================================
# 2. INDIVIDUAL BOT SIDE-TASK HANDLERS
# =============================================================================

async def sweep_mrg_tasks(session: aiohttp.ClientSession, uid: str, name: str, m_init: str, acc: dict) -> Dict[str, Any]:
    """Sweeps MRG Miner tasks, level upgrades, and wallet bindings."""
    res = {"bot": "MRG Miner", "tasks_claimed": 0, "notes": [], "success": False}
    if not m_init:
        res["notes"].append("no_init_data")
        return res

    m_headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36 Telegram-Android/11.0.0",
        "Content-Type": "application/json",
        "Origin": "https://app.mrgtoken.xyz",
        "Referer": "https://app.mrgtoken.xyz/"
    }

    try:
        # 1. State lookup
        async with session.post("https://mrg.up.railway.app/api/user/me", json={"initData": m_init}, headers=m_headers, timeout=aiohttp.ClientTimeout(total=10)) as r:
            if r.status != 200:
                res["notes"].append(f"me_status_{r.status}")
                return res
            me_d = await r.json()

        res["success"] = True
        u_obj = me_d.get("user", {})
        cur_lvl = u_obj.get("peakLevel") or u_obj.get("manualUnlockedLevel") or 1
        in_bal = float(u_obj.get("inAppBalance", 0) or 0)
        res["balance"] = in_bal
        res["level"] = cur_lvl

        # 2. Bind TON Wallet
        is_ton_conn = u_obj.get("isTonConnected", False)
        target_ton_w = (acc.get("ton_wallet") or {}).get("address") or ton_wallets.get(uid, {}).get("address")
        if target_ton_w and not is_ton_conn:
            async with session.post("https://mrg.up.railway.app/api/user/connect-wallet", json={"initData": m_init, "address": target_ton_w, "balance": 0}, headers=m_headers, timeout=aiohttp.ClientTimeout(total=8)) as cr:
                if cr.status == 200:
                    res["notes"].append("ton_wallet_bound")

        # 3. Tasks Completion
        completed = set(me_d.get("completedTaskIds", []))
        tasks = me_d.get("tasks", [])
        for t in tasks:
            tid = t.get("taskId")
            if tid and tid not in completed:
                # Claim task
                await jitter(0.8, 1.8)
                async with session.post("https://mrg.up.railway.app/api/user/claim-task", json={"initData": m_init, "taskId": tid}, headers=m_headers, timeout=aiohttp.ClientTimeout(total=8)) as cl_resp:
                    cld = await cl_resp.json() if cl_resp.status == 200 else {}
                    if cld.get("success"):
                        res["tasks_claimed"] += 1
                        res["notes"].append(f"claimed_{tid}")
                    elif "wait" in json.dumps(cld).lower() or "second" in json.dumps(cld).lower():
                        await asyncio.sleep(15)
                        async with session.post("https://mrg.up.railway.app/api/user/claim-task", json={"initData": m_init, "taskId": tid}, headers=m_headers, timeout=aiohttp.ClientTimeout(total=8)) as r2:
                            cld2 = await r2.json() if r2.status == 200 else {}
                            if cld2.get("success"):
                                res["tasks_claimed"] += 1
                                res["notes"].append(f"claimed_wait_{tid}")

        # 4. Level Auto-Upgrade (if enough balance)
        if in_bal >= 100:
            def wp_calc(e):
                if e <= 0: return 0
                if e == 1: return 100
                if e <= 203: return round(100 + 9900 * (((e - 1) / 202.0) ** 1.8))
                return 10000
            lo, hi, target_lvl = 1, 203, cur_lvl
            while lo <= hi:
                mid = (lo + hi) // 2
                if in_bal >= wp_calc(mid):
                    target_lvl = mid
                    lo = mid + 1
                else:
                    hi = mid - 1
            if target_lvl > cur_lvl:
                async with session.post("https://mrg.up.railway.app/api/user/unlock-level", json={"initData": m_init, "level": target_lvl}, headers=m_headers, timeout=aiohttp.ClientTimeout(total=8)) as ul:
                    if ul.status == 200:
                        res["notes"].append(f"upgraded_lvl_{target_lvl}")
                        res["level"] = target_lvl

        # 5. Master Referral Commission
        if str(uid) == MASTER_UID:
            async with session.post("https://mrg.up.railway.app/api/user/claim-commission", json={"initData": m_init}, headers=m_headers, timeout=aiohttp.ClientTimeout(total=8)) as cr:
                if cr.status == 200:
                    res["notes"].append("master_commission_claimed")

    except Exception as e:
        res["notes"].append(f"err: {str(e)[:50]}")

    return res


async def sweep_atf_tasks(session: aiohttp.ClientSession, uid: str, name: str, atf_init: str, acc: dict) -> Dict[str, Any]:
    """Sweeps ATF Miner daily tasks, boost, math challenges, and team claims."""
    res = {"bot": "ATF Miner", "tasks_claimed": 0, "notes": [], "success": False}
    if not atf_init:
        res["notes"].append("no_init_data")
        return res

    atf_base = "https://atfminers.asloni.online/miner/index.php"
    atf_h = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36 Telegram-Android/11.0.0",
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://atfminers.asloni.online",
        "Referer": "https://atfminers.asloni.online/miner/index.html"
    }

    def payload(extra=None):
        p = {
            "initData": atf_init,
            "tg_id": int(uid),
            "username": acc.get("username", "") or "",
            "request_id": f"rq-{int(time.time()*1000)}-task",
            "device_id": f"dev-task-{uid}"
        }
        if str(uid) != MASTER_UID:
            p["ref"] = "6727787768"
        if extra:
            p.update(extra)
        return p

    try:
        # 1. Login
        async with session.post(f"{atf_base}?action=login&t={int(time.time()*1000)}", json=payload(), headers=atf_h, timeout=aiohttp.ClientTimeout(total=10)) as r:
            if r.status != 200:
                res["notes"].append(f"login_{r.status}")
                return res
            log_data = await r.json()

        res["success"] = True
        u_obj = log_data.get("user") if isinstance(log_data.get("user"), dict) else log_data
        lvl = u_obj.get("miner_level") or 1
        bal = float(u_obj.get("mined_balance") or 0.0)
        res["level"] = lvl
        res["balance"] = bal

        # 2. Daily claims & boosts
        await jitter(0.4, 0.9)
        async with session.post(f"{atf_base}?action=claim&t={int(time.time()*1000)}", json=payload(), headers=atf_h) as r: pass
        async with session.post(f"{atf_base}?action=claim_referrals&t={int(time.time()*1000)}", json=payload(), headers=atf_h) as r: pass
        async with session.post(f"{atf_base}?action=claim_team_wallet&t={int(time.time()*1000)}", json=payload(), headers=atf_h) as r: pass
        async with session.post(f"{atf_base}?action=activate_boost&t={int(time.time()*1000)}", json=payload(), headers=atf_h) as r: pass
        async with session.post(f"{atf_base}?action=record_daily_interaction&t={int(time.time()*1000)}", json=payload(), headers=atf_h) as r: pass

        # 3. Dedicated TON wallet sync
        ton_addr = (acc.get("ton_wallet") or {}).get("address") or ton_wallets.get(uid, {}).get("address")
        if ton_addr:
            async with session.post(f"{atf_base}?action=sync_wallet&t={int(time.time()*1000)}", json=payload({"wallet": ton_addr}), headers=atf_h) as r:
                res["notes"].append("wallet_synced")

        # 4. Solve Math Challenge & Start Mining
        try:
            async with session.post(f"{atf_base}?action=get_math_challenge&t={int(time.time()*1000)}", json=payload({"scope": "start_mine"}), headers=atf_h, timeout=aiohttp.ClientTimeout(total=8)) as mc:
                if mc.status == 200:
                    chd = await mc.json()
                    if chd.get("status") == "success" and chd.get("challenge_id"):
                        ans = solve_atf_math(chd.get("question", ""))
                        await jitter(1.5, 3.0)
                        async with session.post(f"{atf_base}?action=start_mine&t={int(time.time()*1000)}", json=payload({"math_challenge_id": chd["challenge_id"], "math_answer": ans}), headers=atf_h) as sm:
                            if sm.status == 200:
                                res["notes"].append("mining_restarted")
        except Exception:
            pass

        # 5. Cooldown & One-Time Tasks
        completed_tasks = set(log_data.get("user", {}).get("completed_tasks", []))
        task_cooldowns = log_data.get("task_cooldowns", {})
        now_sec = int(time.time())
        atf_tasks = [
            {"id": "telegram_join", "repeatable": False, "min_s": 10},
            {"id": "telegram_join_fa", "repeatable": False, "min_s": 10},
            {"id": "twitter_follow", "repeatable": False, "min_s": 10},
            {"id": "youtube_subscribe", "repeatable": False, "min_s": 10},
            {"id": "website_visit", "repeatable": True, "min_s": 10},
            {"id": "telegram_react_latest", "repeatable": True, "min_s": 20},
            {"id": "twitter_retweet", "repeatable": True, "min_s": 30},
            {"id": "youtube_like_comment", "repeatable": True, "min_s": 30}
        ]

        for t in atf_tasks:
            tid = t["id"]
            is_rep = t["repeatable"]
            cd = int(task_cooldowns.get(tid, 0) or 0)
            can_do = (tid not in completed_tasks) if not is_rep else (now_sec >= cd)
            if can_do:
                s_at = int(time.time()) - t["min_s"] - 5
                async with session.post(f"{atf_base}?action=start_task&t={int(time.time()*1000)}", json=payload({"task_id": tid, "client_started_at": s_at}), headers=atf_h) as st: pass
                await asyncio.sleep(1.2)
                async with session.post(f"{atf_base}?action=claim_task&t={int(time.time()*1000)}", json=payload({"task_id": tid, "client_started_at": s_at}), headers=atf_h) as cl:
                    if cl.status == 200:
                        cl_res = await cl.json()
                        if cl_res.get("status") == "success":
                            res["tasks_claimed"] += 1
                            res["notes"].append(f"task_{tid}")

    except Exception as e:
        res["notes"].append(f"err: {str(e)[:50]}")

    return res


async def sweep_victors_tasks(session: aiohttp.ClientSession, uid: str, name: str, vic_init: str, acc: dict) -> Dict[str, Any]:
    """Sweeps Victor's Company tasks, daily check-in, tutorial, wallet connect, and arcade."""
    res = {"bot": "Victor's Company", "tasks_claimed": 0, "notes": [], "success": False}
    if not vic_init:
        res["notes"].append("no_init_data")
        return res

    v_h = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36 Telegram-Android/11.0.0",
        "Authorization": f"tma {vic_init}",
        "Origin": "https://app.victors.company",
        "Referer": "https://app.victors.company/"
    }

    # Fetch cached Turnstile pass
    vic_pass = None
    try:
        async with session.get(f"{UPSTASH_URL}/get/victors:pass:{uid}", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=4)) as vr:
            if vr.status == 200:
                vd = await vr.json()
                raw_v = vd.get("result")
                if raw_v:
                    parsed_v = json.loads(raw_v) if isinstance(raw_v, str) else raw_v
                    vic_pass = parsed_v.get("humanPass") if isinstance(parsed_v, dict) else parsed_v
    except Exception:
        pass

    if vic_pass:
        v_h["x-human-pass"] = str(vic_pass)

    try:
        # 1. State lookup
        async with session.get("https://server.victors.company/api/me", headers=v_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
            if r.status != 200:
                res["notes"].append(f"me_status_{r.status} (pass: {bool(vic_pass)})")
                return res
            m_d = await r.json()

        res["success"] = True
        st = m_d.get("state", {}) if isinstance(m_d, dict) else {}
        me = st.get("user") or m_d.get("user") or m_d
        res["level"] = me.get("level", 1)
        res["balance"] = me.get("miningBalance", 0)

        # 2. Tutorial
        if not me.get("tutorialDone"):
            async with session.post("https://server.victors.company/api/me/tutorial", json={}, headers=v_h) as tr:
                if tr.status == 200: res["notes"].append("tutorial_done")

        # 3. Daily check-in
        async with session.post("https://server.victors.company/api/checkin", json={}, headers=v_h) as cr:
            if cr.status == 200: res["notes"].append("checkin_done")

        # 4. Connect TON wallet if needed
        ton_addr = (acc.get("ton_wallet") or {}).get("address") or ton_wallets.get(uid, {}).get("address")
        if ton_addr and not me.get("walletAddress"):
            async with session.post("https://server.victors.company/api/wallet/connect", json={"address": ton_addr}, headers=v_h) as wr:
                if wr.status == 200:
                    async with session.post("https://server.victors.company/api/tasks/claim", json={"taskId": "connect-wallet"}, headers=v_h) as twr:
                        if twr.status == 200: res["notes"].append("wallet_task_claimed")

        # 5. Discover & Claim tasks
        async with session.get("https://server.victors.company/api/tasks", headers=v_h, timeout=aiohttp.ClientTimeout(total=8)) as tr:
            if tr.status == 200:
                t_d = await tr.json()
                tasks = t_d.get("tasks", []) if isinstance(t_d, dict) else []
                for t in tasks:
                    if isinstance(t, dict):
                        tid = t.get("taskId") or t.get("id")
                        if tid and (t.get("status") == "open" or not t.get("claimed")):
                            await jitter(0.4, 0.9)
                            async with session.post("https://server.victors.company/api/tasks/claim", json={"taskId": tid}, headers=v_h) as tcr:
                                if tcr.status == 200:
                                    res["tasks_claimed"] += 1
                                    res["notes"].append(f"task_{tid}")

        # 6. Referral claims
        async with session.post("https://server.victors.company/api/referral/claim-bonus", json={}, headers=v_h) as rbr:
            if rbr.status == 200: res["notes"].append("ref_bonus_claimed")
        async with session.post("https://server.victors.company/api/referral/claim-commission", json={}, headers=v_h) as rcr:
            if rcr.status == 200: res["notes"].append("ref_commission_claimed")

        # 7. Deep Mine Arcade Expeditions
        try:
            import victors_arcade_solver
            arc_res = await victors_arcade_solver.solve_deep_mine_expeditions(session, v_h, name, max_runs=2)
            if arc_res.get("runs_played", 0) > 0:
                res["notes"].append(f"arcade_runs_{arc_res['runs_played']}_+{(arc_res.get('final_balance', 0) - arc_res.get('initial_balance', 0)):.0f}VIC")
        except Exception as e:
            pass

    except Exception as e:
        res["notes"].append(f"err: {str(e)[:50]}")

    return res


async def sweep_vyro_tasks(session: aiohttp.ClientSession, uid: str, name: str, vy_init: str, acc: dict) -> Dict[str, Any]:
    """Sweeps VyroDrop tasks, referral claims, and mining status."""
    res = {"bot": "VyroDrop", "tasks_claimed": 0, "notes": [], "success": False}
    if not vy_init:
        res["notes"].append("no_init_data")
        return res

    vy_h = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36 Telegram-Android/11.0.0",
        "Authorization": f"tma {vy_init}",
        "X-Vyro-UI-Contract": "claim-inactivity-v1",
        "X-Vyro-Market-Balances": "2",
        "X-Vyro-Dex": "1",
        "Referer": "https://vyro.run.place/"
    }

    try:
        # 1. Bootstrap
        async with session.get("https://vyro.run.place/api/bootstrap", headers=vy_h, timeout=aiohttp.ClientTimeout(total=8)) as r:
            if r.status != 200:
                res["notes"].append(f"bootstrap_{r.status}")
                return res
            b_d = await r.json()

        res["success"] = True
        m_obj = b_d.get("miner", {})
        res["level"] = m_obj.get("level", 1)
        res["speed"] = m_obj.get("currentSpeed", 0)

        # 2. Side Tasks
        t_headers = {**vy_h, "x-vyro-tasks-protocol": "2"}
        async with session.get("https://vyro.run.place/api/tasks?limit=8", headers=t_headers, timeout=aiohttp.ClientTimeout(total=8)) as tr:
            if tr.status == 200:
                t_d = await tr.json()
                tasks = t_d.get("tasks", []) if isinstance(t_d, dict) else []
                for t in tasks:
                    if isinstance(t, dict) and t.get("id") and t.get("state") != "CLAIMED":
                        tid = t["id"]
                        await jitter(0.4, 0.8)
                        async with session.post(f"https://vyro.run.place/api/tasks/{tid}/open", json={}, headers=t_headers) as o_r: pass
                        await jitter(0.8, 1.4)
                        async with session.post(f"https://vyro.run.place/api/tasks/{tid}/verify", json={}, headers=t_headers) as v_r:
                            if v_r.status == 200:
                                vd = await v_r.json()
                                if vd.get("task", {}).get("canClaim"):
                                    async with session.post(f"https://vyro.run.place/api/tasks/{tid}/claim", json={"idempotencyKey": str(uuid.uuid4())}, headers=t_headers) as c_r:
                                        if c_r.status in (200, 201):
                                            res["tasks_claimed"] += 1
                                            res["notes"].append(f"task_{tid}")

        # 3. Referral claims
        await jitter(0.4, 0.8)
        async with session.post("https://vyro.run.place/api/referrals/claim", json={"kind": "DIRECT", "idempotencyKey": str(uuid.uuid4())}, headers=vy_h) as dr:
            if dr.status in (200, 201): res["notes"].append("direct_ref_claimed")
        async with session.post("https://vyro.run.place/api/referrals/claim", json={"kind": "MINING", "idempotencyKey": str(uuid.uuid4())}, headers=vy_h) as mr:
            if mr.status in (200, 201): res["notes"].append("mining_ref_claimed")

    except Exception as e:
        res["notes"].append(f"err: {str(e)[:50]}")

    return res


async def sweep_kynex_tasks(session: aiohttp.ClientSession, uid: str, name: str, ky_init: str, acc: dict) -> Dict[str, Any]:
    """Sweeps Kynex Network daily checkin, sponsor channels, and rewarded ads."""
    res = {"bot": "Kynex Network", "tasks_claimed": 0, "notes": [], "success": False}
    if not ky_init:
        res["notes"].append("no_init_data")
        return res

    try:
        import kynex_miner
        is_owner = (str(uid) == MASTER_UID)
        farm_res = await kynex_miner.farm_kynex_account(session, ky_init, acc, is_master=is_owner)
        res["success"] = True
        res["balance"] = farm_res.get("balance", 0.0)
        res["level"] = farm_res.get("level", 1)
        res["mining_active"] = farm_res.get("mining_active", False)
        
        notes = farm_res.get("notes", [])
        claimed_tasks = [n for n in notes if "social_" in n or "ad_" in n or "daily_checkin" in n]
        res["tasks_claimed"] = len(claimed_tasks)
        res["notes"] = notes
    except Exception as e:
        res["notes"].append(f"err: {str(e)[:50]}")

    return res


# =============================================================================
# 3. MAIN RUNNER (18-ACCOUNT PARALLEL PIPELINE)
# =============================================================================

async def process_account(session: aiohttp.ClientSession, acc: dict, tokens_db: dict, sem: asyncio.Semaphore) -> Dict[str, Any]:
    async with sem:
        uid = str(acc.get("user_id"))
        name = acc.get("name", f"Account_{uid}")
        is_owner = (uid == MASTER_UID)
        acc_toks = tokens_db.get(uid, {})

        logger.info(f"🚀 Sweeping side-tasks for {name} ({uid})...")
        account_report = {
            "account": f"{name} ({uid})",
            "is_master": is_owner,
            "results": {}
        }

        # 1. MRG Miner
        mrg_res = await sweep_mrg_tasks(session, uid, name, acc_toks.get("mrg_init_data", ""), acc)
        account_report["results"]["mrg"] = mrg_res

        # 2. ATF Miner
        atf_res = await sweep_atf_tasks(session, uid, name, acc_toks.get("atf_init_data", ""), acc)
        account_report["results"]["atf"] = atf_res

        # 3. Victor's Company
        vic_res = await sweep_victors_tasks(session, uid, name, acc_toks.get("victors_init_data", ""), acc)
        account_report["results"]["victors"] = vic_res

        # 4. VyroDrop
        vyro_res = await sweep_vyro_tasks(session, uid, name, acc_toks.get("vyro_init_data", ""), acc)
        account_report["results"]["vyro"] = vyro_res

        # 5. Kynex Network
        kynex_res = await sweep_kynex_tasks(session, uid, name, acc_toks.get("kynex_init_data", ""), acc)
        account_report["results"]["kynex"] = kynex_res

        # Sync tokens to Cloudflare Workers if newly refreshed
        await sync_token_to_cf(session, uid, acc_toks)

        total_claimed = sum(r.get("tasks_claimed", 0) for r in account_report["results"].values())
        logger.info(f"✅ [{name}] Finished side-tasks! Claimed: {total_claimed} total tasks/rewards.")
        return account_report


async def main():
    logger.info("=============================================================================")
    logger.info("🎯 STARTING COMPLETE 5-BOT FLEET SIDE-TASK HARVEST (18 ACCOUNTS)")
    logger.info("=============================================================================")

    conn = aiohttp.TCPConnector(limit=25, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=conn) as session:
        tokens_db = await fetch_all_tokens(session)
        logger.info(f"Loaded tokens for {len(tokens_db)} accounts from Upstash Redis.")

        # Semaphore of 3 to avoid hammering APIs while maintaining fast speed
        sem = asyncio.Semaphore(3)
        tasks = [process_account(session, acc, tokens_db, sem) for acc in ACCOUNTS]
        reports = await asyncio.gather(*tasks)

        # Print Summary
        logger.info("\n" + "=" * 70)
        logger.info("📊 FLEET SIDE-TASK HARVEST SUMMARY")
        logger.info("=" * 70)
        total_tasks = 0
        for rep in reports:
            acc_name = rep["account"]
            res = rep["results"]
            mrg_cl = res.get("mrg", {}).get("tasks_claimed", 0)
            atf_cl = res.get("atf", {}).get("tasks_claimed", 0)
            vic_cl = res.get("victors", {}).get("tasks_claimed", 0)
            vyr_cl = res.get("vyro", {}).get("tasks_claimed", 0)
            kyn_cl = res.get("kynex", {}).get("tasks_claimed", 0)
            acc_total = mrg_cl + atf_cl + vic_cl + vyr_cl + kyn_cl
            total_tasks += acc_total
            logger.info(f"• {acc_name:<30} | MRG: {mrg_cl} | ATF: {atf_cl} | VIC: {vic_cl} | VYRO: {vyr_cl} | KYN: {kyn_cl} | Total: {acc_total}")

        logger.info("=" * 70)
        logger.info(f"🏁 GRAND TOTAL SIDE-TASKS/REWARDS CLAIMED: {total_tasks}")
        logger.info("=============================================================================")


if __name__ == "__main__":
    asyncio.run(main())
