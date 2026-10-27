#!/usr/bin/env python3
"""
finish_all_fleet_sidetasks.py
=============================================================================
COMPREHENSIVE MULTI-BOT FLEET SIDE-TASK HARVESTER & AUTOMATION ENGINE
=============================================================================
Sweeps and completes all available side-tasks, daily check-ins, social joins,
cooldown missions, wallet verifications, and referral commission claims across
all 20 accounts in the fleet for all 9 legitimate bots:
  1. MRG Miner (@mrg_miner_bot)
  2. ATF Miner (@atf_miner_bot)
  3. Victor's Company (@VictorsCompanybot)
  4. VyroDrop (@vyrodrop_bot)
  5. Kynex Network (@Kynex_miningbot)
  6. PepeGram (@pepe_mine_bot)
  7. AdxEarn AI (@AdxEarnAibot)
  8. DiggoMiner (@diggominer_bot)
  9. Chicken Land (@ChickenLandBot)

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
import hashlib
import hmac
import logging
import struct
import base64
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

UPSTASH_URL = env.get("UPSTASH_URL") or env.get("UPSTASH_REDIS_REST_URL") or "https://rich-emu-106119.upstash.io"
UPSTASH_TOKEN = env.get("UPSTASH_TOKEN") or env.get("UPSTASH_REDIS_REST_TOKEN") or ""
SECRET_KEY = env.get("SECRET_KEY") or env.get("CF_SECRET_KEY") or ""

CF_WORKERS = [
    "https://restore-agy.aaaai2.workers.dev",
    "https://restore-agy.aaa-bot.workers.dev",
    "https://restore-agy.aaa222.workers.dev",
    "https://restore-agy.agorameet.workers.dev",
    "https://restore-agy.aaaai.workers.dev"
]

MASTER_UID = "6727787768"
PRIMARY_TON_WALLET = "UQAWuK6X9s1fA0LzXGzM_81n1xL_T6_xY8Z_1x1x1x1x1x1"

# Load Accounts (with cloud backup fallback for Render/Cloud VMs)
ACCOUNTS = []
accounts_path = os.path.join(BASE_DIR, "accounts.json")
if os.path.exists(accounts_path):
    try:
        with open(accounts_path, "r") as f:
            ACCOUNTS = json.load(f)
    except Exception:
        pass

if not ACCOUNTS:
    import zipfile
    import io
    for cf_url in CF_WORKERS:
        try:
            req = urllib.request.Request(f"{cf_url}/backup.zip", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status == 200:
                    zip_bytes = resp.read()
                    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                        if "accounts.json" in zf.namelist():
                            ACCOUNTS = json.loads(zf.read("accounts.json").decode("utf-8"))
                            if ACCOUNTS:
                                break
        except Exception:
            pass

if not ACCOUNTS and UPSTASH_URL and UPSTASH_TOKEN:
    try:
        req = urllib.request.Request(f"{UPSTASH_URL}/get/fleet:accounts", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            res = data.get("result")
            if res:
                ACCOUNTS = json.loads(res) if isinstance(res, str) else res
    except Exception:
        pass

# Load TON Wallets
ton_wallets = {}
wallets_path = os.path.join(BASE_DIR, "fleet_ton_wallets.json")
if os.path.exists(wallets_path):
    try:
        with open(wallets_path, "r") as f:
            ton_wallets = json.load(f)
    except Exception:
        pass

if not ton_wallets and UPSTASH_URL and UPSTASH_TOKEN:
    try:
        req = urllib.request.Request(f"{UPSTASH_URL}/get/fleet:wallets:ton", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            d = json.loads(resp.read().decode())
            if d.get("result"):
                ton_wallets = json.loads(d["result"]) if isinstance(d["result"], str) else d["result"]
    except Exception:
        pass


def get_ton_wallet_address(acc: dict, uid: str) -> str:
    """Returns dedicated TON address for account with robust type conversion."""
    if acc and acc.get("ton_wallet") and acc["ton_wallet"].get("address"):
        return acc["ton_wallet"]["address"]
    s_uid = str(uid)
    w_entry = ton_wallets.get(s_uid)
    if not w_entry and s_uid.isdigit():
        w_entry = ton_wallets.get(int(s_uid))
    if isinstance(w_entry, dict) and w_entry.get("address"):
        return w_entry["address"]
    return ""


def create_mrg_ton_proof(wallet_entry: dict, nonce: str) -> dict:
    """Signs TonConnect 2.0 cryptographic proof for MRG Miner."""
    try:
        from nacl.signing import SigningKey
        from tonsdk.contract.wallet import Wallets, WalletVersionEnum
        words = wallet_entry["mnemonic"].split() if isinstance(wallet_entry["mnemonic"], str) else wallet_entry["mnemonic"]
        _, pub_k, priv_k, wallet_contract = Wallets.from_mnemonics(mnemonics=words, version=WalletVersionEnum.v4r2)
        state_init_res = wallet_contract.create_state_init()
        state_init_b64 = base64.b64encode(state_init_res["state_init"].to_boc(False)).decode("utf-8")
        t_addr = wallet_contract.address
        wc = t_addr.wc
        addr_hash = t_addr.hash_part
        raw_addr = f"{wc}:{addr_hash.hex()}"
        domain = "app.mrgtoken.xyz"
        domain_b = domain.encode("utf-8")
        ts_now = int(time.time())
        msg = b"ton-proof-item-v2/" + struct.pack(">i", wc) + addr_hash + struct.pack("<I", len(domain_b)) + domain_b + struct.pack("<Q", ts_now) + nonce.encode("utf-8")
        digest = hashlib.sha256(b"\xff\xff" + b"ton-connect" + hashlib.sha256(msg).digest()).digest()
        sig = SigningKey(priv_k[:32]).sign(digest).signature
        sig_b64 = base64.b64encode(sig).decode("utf-8")
        return {
            "address": raw_addr,
            "walletStateInit": state_init_b64,
            "proof": {
                "timestamp": ts_now,
                "domain": {"lengthBytes": len(domain_b), "value": domain},
                "signature": sig_b64,
                "payload": nonce
            }
        }
    except Exception as e:
        logger.debug(f"MRG proof creation error: {e}")
        return None


def solve_atf_math(question_text: str) -> str:
    """100% local, instant, deterministic arithmetic & challenge solver (0 network latency, 0 AI dependency)."""
    if not question_text:
        return "0"
    q_lower = question_text.lower().strip()

    if "days in a week" in q_lower or "days a week" in q_lower: return "7"
    if "hours in a day" in q_lower: return "24"
    if "minutes in an hour" in q_lower or "seconds in a minute" in q_lower: return "60"
    if "months in a year" in q_lower: return "12"
    if "days in a year" in q_lower: return "365"
    if "even or odd" in q_lower or "odd or even" in q_lower:
        m_num = re.search(r"\b(\d+)\b", q_lower)
        if m_num: return "even" if int(m_num.group(1)) % 2 == 0 else "odd"

    word_to_num = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
        "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
        "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
        "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
        "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
        "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
        "eighty": 80, "ninety": 90, "hundred": 100, "thousand": 1000
    }
    tokens = re.findall(r"[a-z0-9\+\-\*\/\%\=]+", q_lower)
    converted_tokens = []
    i = 0
    while i < len(tokens):
        w = tokens[i]
        if w in word_to_num:
            val = word_to_num[w]
            while i + 1 < len(tokens) and tokens[i+1] in word_to_num:
                next_val = word_to_num[tokens[i+1]]
                if next_val in (100, 1000):
                    val = val * next_val
                    i += 1
                elif val >= 20 and next_val < 10:
                    val += next_val
                    i += 1
                else:
                    break
            converted_tokens.append(str(val))
        elif w in ("plus", "add", "added", "+"): converted_tokens.append("+")
        elif w in ("minus", "subtract", "subtracted", "take", "-"): converted_tokens.append("-")
        elif w in ("times", "multiplied", "multiply", "*", "x"): converted_tokens.append("*")
        elif w in ("divided", "divide", "/"): converted_tokens.append("/")
        elif w in ("mod", "modulo", "remainder", "%"): converted_tokens.append("%")
        elif w.isdigit() or re.match(r"^\d+[\+\-\*\/\%]\d+$", w): converted_tokens.append(w)
        i += 1

    normalized = " ".join(converted_tokens)
    m = re.search(r"(\d+)\s*([\+\-\*\/\%])\s*(\d+)", normalized)
    if m:
        a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
        if op == "+": return str(a + b)
        if op == "-": return str(a - b)
        if op == "*": return str(a * b)
        if op == "/" and b != 0: return str(a // b)
        if op == "%" and b != 0: return str(a % b)

    nums = [int(n) for n in re.findall(r"\d+", normalized)]
    if nums:
        if ("half of" in q_lower or "half" in q_lower) and len(nums) == 1: return str(nums[0] // 2)
        if ("double of" in q_lower or "twice" in q_lower) and len(nums) == 1: return str(nums[0] * 2)
        if "square of" in q_lower and len(nums) == 1: return str(nums[0] * nums[0])
        if any(w in q_lower for w in ["larger", "greater", "bigger", "highest", "maximum", "max", "most"]): return str(max(nums))
        if any(w in q_lower for w in ["smaller", "less", "lowest", "minimum", "least", "min"]): return str(min(nums))

    if len(nums) >= 2:
        if any(op in q_lower for op in ["plus", "add", "sum", "total", "+"]): return str(nums[0] + nums[1])
        if any(op in q_lower for op in ["minus", "subtract", "difference", "take", "-"]): return str(nums[0] - nums[1])
        if any(op in q_lower for op in ["times", "multipl", "product", "*"]): return str(nums[0] * nums[1])
        if any(op in q_lower for op in ["divid", "quotient", "/"]): return str(nums[0] // nums[1]) if nums[1] != 0 else "0"

    return str(nums[0]) if nums else "0"


solve_challenge_deterministic = solve_atf_math


async def jitter(min_s: float = 0.5, max_s: float = 1.5):
    await asyncio.sleep(random.uniform(min_s, max_s))




# =============================================================================
# 1. TOKEN LOADER & CLOUD SYNC
# =============================================================================

async def fetch_all_tokens(session: aiohttp.ClientSession) -> Dict[str, Dict[str, str]]:
    """Loads tokens for all 20 accounts from Upstash Redis fleet:tokens:*."""
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

        # 2. Bind TON Wallet with TonConnect 2.0 Proof
        is_ton_conn = u_obj.get("isTonConnected", False)
        target_ton_w = get_ton_wallet_address(acc, uid)
        if target_ton_w and not is_ton_conn:
            w_entry = ton_wallets.get(str(uid)) or (acc.get("ton_wallet") if isinstance(acc.get("ton_wallet"), dict) else {})
            ton_proof_payload = None
            if w_entry and w_entry.get("mnemonic"):
                try:
                    async with session.post("https://mrg.up.railway.app/api/user/ton-proof-payload", json={"initData": m_init}, headers=m_headers, timeout=aiohttp.ClientTimeout(total=8)) as npr:
                        if npr.status == 200:
                            np_d = await npr.json()
                            nonce = np_d.get("payload") if isinstance(np_d, dict) else None
                            if nonce:
                                ton_proof_payload = create_mrg_ton_proof(w_entry, nonce)
                except Exception as p_err:
                    logger.debug(f"[{name}] MRG nonce fetch note: {p_err}")

            conn_body = {"initData": m_init, "address": target_ton_w, "balance": 0}
            if ton_proof_payload:
                conn_body["tonProof"] = ton_proof_payload

            async with session.post("https://mrg.up.railway.app/api/user/connect-wallet", json=conn_body, headers=m_headers, timeout=aiohttp.ClientTimeout(total=8)) as cr:
                if cr.status in (200, 201):
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

        # 4. Level Auto-Upgrade (if enough balance, including TON wallet balance)
        ton_holding = float(u_obj.get("tonWalletBalance", 0) or 0)
        total_mrg_bal = in_bal + ton_holding
        if total_mrg_bal >= 100:
            def wp_calc(e):
                if e <= 0: return 0
                if e == 1: return 100
                if e <= 203: return round(100 + 9900 * (((e - 1) / 202.0) ** 1.8))
                return 10000
            lo, hi, target_lvl = 1, 203, cur_lvl
            while lo <= hi:
                mid = (lo + hi) // 2
                if total_mrg_bal >= wp_calc(mid):
                    target_lvl = mid
                    lo = mid + 1
                else:
                    hi = mid - 1
            if target_lvl > cur_lvl:
                async with session.post("https://mrg.up.railway.app/api/user/unlock-level", json={"initData": m_init, "level": target_lvl}, headers=m_headers, timeout=aiohttp.ClientTimeout(total=8)) as ul:
                    if ul.status == 200:
                        res["notes"].append(f"upgraded_lvl_{target_lvl}")
                        res["level"] = target_lvl

        # 5. Master Referral Commission & One-Time Bonus
        if str(uid) == MASTER_UID:
            async with session.post("https://mrg.up.railway.app/api/user/claim-commission", json={"initData": m_init}, headers=m_headers, timeout=aiohttp.ClientTimeout(total=8)) as cr:
                if cr.status == 200:
                    res["notes"].append("master_commission_claimed")
            async with session.post("https://mrg.up.railway.app/api/user/claim-one-time-bonus", json={"initData": m_init}, headers=m_headers, timeout=aiohttp.ClientTimeout(total=8)) as br:
                if br.status == 200:
                    res["notes"].append("master_one_time_bonus_claimed")

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
            "request_id": f"rq-{uuid.uuid4()}",
            "device_id": f"dev-task-{uid}"
        }
        if str(uid) != MASTER_UID:
            p["ref"] = "6727787768"
        if extra:
            p.update(extra)
        return p

    try:
        # 1. Login & extract stateful session cookies (atf_tma_session, __Host-atf_fg_v1)
        async with session.post(f"{atf_base}?action=login&t={int(time.time()*1000)}", json=payload(), headers=atf_h, timeout=aiohttp.ClientTimeout(total=10)) as r:
            if r.status != 200:
                res["notes"].append(f"login_{r.status}")
                return res
            cookies = r.headers.getall("Set-Cookie", []) if hasattr(r.headers, "getall") else []
            if cookies:
                atf_h["Cookie"] = "; ".join([c.split(";")[0] for c in cookies])
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
        ton_addr = get_ton_wallet_address(acc, uid)
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
        cur_level = me.get("level", 0)
        res["level"] = cur_level
        res["balance"] = me.get("miningBalance", 0)

        # 2. Tutorial
        if not me.get("tutorialDone"):
            async with session.post("https://server.victors.company/api/me/tutorial", json={}, headers=v_h) as tr:
                if tr.status == 200: res["notes"].append("tutorial_done")

        # 3. Daily check-in
        async with session.post("https://server.victors.company/api/checkin", json={}, headers=v_h) as cr:
            if cr.status == 200: res["notes"].append("checkin_done")

        # 4. Level 1 Miner Unlock (Continuous +100 V/day passive yield)
        if cur_level < 1:
            try:
                async with session.post("https://server.victors.company/api/levels/unlock", json={"level": 1}, headers=v_h) as lr:
                    if lr.status in (200, 201):
                        res["notes"].append("miner_lvl1_unlocked")
            except Exception:
                pass

        # 5. Claim Accumulated Mining Balance
        try:
            async with session.post("https://server.victors.company/api/mining/claim", json={}, headers=v_h) as mr:
                if mr.status in (200, 201):
                    m_claim = await mr.json()
                    claimed_amt = m_claim.get("claimed", 0) if isinstance(m_claim, dict) else 0
                    if claimed_amt > 0:
                        res["notes"].append(f"mined_+{claimed_amt:.1f}VIC")
        except Exception:
            pass

        # 6. Connect TON wallet if needed (TonConnect 2.0 Proof-of-Ownership)
        ton_addr = get_ton_wallet_address(acc, uid)
        if ton_addr and (not me.get("walletAddress") or not me.get("walletOwned")):
            connected = False
            try:
                from victors_sb_solver import create_victors_ton_proof, load_fleet_ton_wallets
                tw = load_fleet_ton_wallets()
                w_entry = tw.get(str(uid)) or tw.get(int(uid) if uid.isdigit() else uid) or acc.get("ton_wallet")
                if w_entry and isinstance(w_entry, dict) and w_entry.get("mnemonic"):
                    async with session.get("https://server.victors.company/api/wallet/proof-payload", headers=v_h, timeout=aiohttp.ClientTimeout(total=8)) as npr:
                        if npr.status == 200:
                            np_d = await npr.json()
                            nonce = np_d.get("payload") if isinstance(np_d, dict) else None
                            if nonce:
                                proof_item, state_init_b64, pub_key_hex, friendly_addr = create_victors_ton_proof(w_entry, nonce)
                                if proof_item:
                                    conn_body = {
                                        "address": friendly_addr,
                                        "proof": proof_item,
                                        "stateInit": state_init_b64,
                                        "publicKey": pub_key_hex
                                    }
                                    async with session.post("https://server.victors.company/api/wallet/connect", json=conn_body, headers=v_h, timeout=aiohttp.ClientTimeout(total=8)) as cwr:
                                        if cwr.status in (200, 201):
                                             connected = True
                                             res["notes"].append("ton_wallet_proof_connected")
            except Exception as pe:
                logger.debug(f"[{name}] Victor's proof connect note: {pe}")

            if not connected:
                async with session.post("https://server.victors.company/api/wallet/connect", json={"address": ton_addr}, headers=v_h) as wr:
                    if wr.status == 200:
                        connected = True
                        res["notes"].append("ton_wallet_connected")

            if connected:
                async with session.post("https://server.victors.company/api/tasks/claim", json={"taskId": "connect-wallet"}, headers=v_h) as twr:
                    if twr.status == 200: res["notes"].append("wallet_task_claimed")

        # 7. Discover & Claim Jobs Board Tasks (with 4.2s link verification debounce)
        async with session.get("https://server.victors.company/api/tasks", headers=v_h, timeout=aiohttp.ClientTimeout(total=8)) as tr:
            if tr.status == 200:
                t_d = await tr.json()
                tasks = t_d.get("tasks", []) if isinstance(t_d, dict) else []
                for t in tasks:
                    if isinstance(t, dict):
                        tid = t.get("taskId") or t.get("id")
                        t_kind = t.get("kind", "")
                        if tid and (t.get("status") == "open" or not t.get("claimed")):
                            # Link-visit / partner-api tasks enforce 4.0s debounce before claim
                            if t_kind in ("link_visit", "telegram_channel", "partner_api") or t.get("url"):
                                await asyncio.sleep(4.2)
                            else:
                                await jitter(0.3, 0.6)
                            async with session.post("https://server.victors.company/api/tasks/claim", json={"taskId": tid}, headers=v_h) as tcr:
                                if tcr.status in (200, 201):
                                    res["tasks_claimed"] += 1
                                    res["notes"].append(f"task_{tid}")

        # 8. Referral claims (Hiring Bonus + Commission)
        if str(uid) == MASTER_UID or vic_pass:
            async with session.post("https://server.victors.company/api/referral/claim-bonus", json={}, headers=v_h) as rbr:
                if rbr.status == 200: res["notes"].append("ref_bonus_claimed")
            async with session.post("https://server.victors.company/api/referral/claim-commission", json={}, headers=v_h) as rcr:
                if rcr.status == 200: res["notes"].append("ref_commission_claimed")

        # 9. Deep Mine Arcade Expeditions & Arcade Mode Discovery
        try:
            import victors_arcade_solver
            arc_res = await victors_arcade_solver.solve_deep_mine_expeditions(session, v_h, name, max_runs=2)
            if arc_res.get("runs_played", 0) > 0:
                net_profit = arc_res.get("net_vic", 0.0)
                res["notes"].append(f"arcade_{arc_res['runs_played']}runs_{net_profit:+.1f}VIC")
        except Exception as e:
            logger.debug(f"[{name}] Victor's arcade solver note: {e}")

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


async def sweep_diggo_tasks(session: aiohttp.ClientSession, uid: str, name: str, d_init: str, acc: dict) -> Dict[str, Any]:
    """Sweeps DiggoMiner mining claim, referrals, and daily/social tasks."""
    res = {"bot": "DiggoMiner", "tasks_claimed": 0, "notes": [], "success": False}
    try:
        base_url = "https://diggo.linkpc.net"
        jwt_token = None
        st = {}

        # 0. Check cached JWT from acc object, token dict, or Upstash Redis
        jwt_token = acc.get("diggo_jwt") or (acc.get("tokens", {}).get("diggo_jwt") if isinstance(acc.get("tokens"), dict) else None)
        if not jwt_token and UPSTASH_URL and UPSTASH_TOKEN:
            try:
                async with session.get(f"{UPSTASH_URL}/get/fleet:tokens:{uid}", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=2)) as jr:
                    if jr.status == 200:
                        jd = await jr.json()
                        raw_res = jd.get("result")
                        if raw_res:
                            parsed_res = json.loads(raw_res) if isinstance(raw_res, str) else raw_res
                            if isinstance(parsed_res, dict) and parsed_res.get("diggo_jwt"):
                                jwt_token = parsed_res["diggo_jwt"]
            except Exception:
                pass
        if not jwt_token and UPSTASH_URL and UPSTASH_TOKEN:
            try:
                async with session.get(f"{UPSTASH_URL}/get/fleet:diggo:jwt:{uid}", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=2)) as jr:
                    if jr.status == 200:
                        jd = await jr.json()
                        if jd.get("result"):
                            jwt_token = str(jd["result"]).strip()
            except Exception:
                pass

        auth_headers = None
        if jwt_token:
            candidate_h = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {jwt_token}",
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 Telegram-Android/11.0.0",
                "Origin": base_url,
                "Referer": f"{base_url}/?tgWebAppStartParam=ref_4088138f11effe8eef4b86ff"
            }
            async with session.get(f"{base_url}/api/state", headers=candidate_h, timeout=aiohttp.ClientTimeout(total=5)) as pr:
                if pr.status == 200:
                    p_d = await pr.json()
                    if isinstance(p_d, dict) and p_d.get("state"):
                        st = p_d["state"]
                        auth_headers = candidate_h
                        res["success"] = True
                else:
                    jwt_token = None

        # 1. Auth (if no valid cached JWT)
        if not jwt_token or not auth_headers:
            if not d_init:
                res["notes"].append("no_init_data_and_no_jwt")
                return res

            if "%25" in d_init or "%3D" in d_init or "user%3D" in d_init:
                d_init = urllib.parse.unquote(d_init)
            init_headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 Telegram-Android/11.0.0",
                "Origin": base_url,
                "Referer": f"{base_url}/?tgWebAppStartParam=ref_4088138f11effe8eef4b86ff"
            }
            async with session.post(f"{base_url}/api/auth/telegram", json={"initData": d_init}, headers=init_headers, timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status != 200:
                    res["notes"].append(f"auth_status_{r.status}")
                    return res
                a_d = await r.json()

            jwt_token = a_d.get("token")
            if not jwt_token:
                res["notes"].append("no_token")
                return res

            res["success"] = True
            st = a_d.get("state", {})
            if UPSTASH_URL and UPSTASH_TOKEN and jwt_token:
                acc["diggo_jwt"] = jwt_token
                try:
                    await session.post(f"{UPSTASH_URL}/set/fleet:diggo:jwt:{uid}?ex=2592000", data=jwt_token, headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=2))
                    async with session.get(f"{UPSTASH_URL}/get/fleet:tokens:{uid}", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=2)) as gr:
                        if gr.status == 200:
                            curr_toks = {}
                            r_res = (await gr.json()).get("result")
                            if r_res:
                                curr_toks = json.loads(r_res) if isinstance(r_res, str) else r_res
                            if isinstance(curr_toks, dict):
                                curr_toks["diggo_jwt"] = jwt_token
                                await session.post(f"{UPSTASH_URL}/set/fleet:tokens:{uid}", data=json.dumps(curr_toks), headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=2))
                except Exception:
                    pass

            auth_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {jwt_token}",
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 Telegram-Android/11.0.0",
                "Origin": base_url,
                "Referer": f"{base_url}/?tgWebAppStartParam=ref_4088138f11effe8eef4b86ff"
            }

        # 2. Claim mining
        mining = st.get("mining") or {}
        if float(mining.get("pending", 0) or 0) > 0:
            await jitter(0.4, 0.8)
            async with session.post(f"{base_url}/api/claims/mining", json={}, headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())}) as cr:
                if cr.status in (200, 201):
                    c_d = await cr.json()
                    res["notes"].append(f"claimed_mined_{c_d.get('amount', 0):.2f}")

        # 3. Claim referrals
        await jitter(0.4, 0.8)
        async with session.post(f"{base_url}/api/referrals/claim", json={}, headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())}) as rr:
            if rr.status in (200, 201):
                res["notes"].append("ref_claimed")

        # 4. Daily Streak & Day Rewards
        day_rewards = st.get("dayRewards") or []
        for dr in day_rewards:
            if isinstance(dr, dict) and dr.get("status") == "available":
                d_num = dr.get("day")
                try:
                    async with session.post(f"{base_url}/api/streak/claim", json={"day": d_num}, headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())}) as sr:
                        if sr.status in (200, 201):
                            res["tasks_claimed"] += 1
                            res["notes"].append(f"streak_day_{d_num}")
                except Exception:
                    pass

        # 5. Sweep All Tasks (checkin, play, social, ads)
        tasks = st.get("tasks") or {}
        p_lvl = st.get("player", {}).get("level", 1)
        srv_now = st.get("serverNow") or (time.time() * 1000)

        # A. Check-in
        t_chk = tasks.get("checkin") or {}
        if t_chk.get("enabled") and not t_chk.get("claimed"):
            try:
                async with session.post(f"{base_url}/api/tasks/claim", json={"taskId": "checkin"}, headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())}) as tr:
                    if tr.status in (200, 201):
                        res["tasks_claimed"] += 1
                        res["notes"].append("task_checkin")
            except Exception:
                pass

        # B. Play / Level Milestone
        t_play = tasks.get("play") or {}
        if t_play.get("enabled") and not t_play.get("claimed"):
            req_lvl = t_play.get("targetLevel") or 1
            if p_lvl >= req_lvl or (t_play.get("progress", 0) >= t_play.get("total", 1)):
                try:
                    async with session.post(f"{base_url}/api/tasks/claim", json={"taskId": "play"}, headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())}) as tr:
                        if tr.status in (200, 201):
                            res["tasks_claimed"] += 1
                            res["notes"].append("task_play")
                except Exception:
                    pass

        # C. Telegram Channel Join
        t_tg = tasks.get("telegram") or {}
        if t_tg.get("enabled") and not t_tg.get("claimed"):
            try:
                await session.post(f"{base_url}/api/tasks/verify", json={"taskId": "telegram"}, headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())})
                async with session.post(f"{base_url}/api/tasks/claim", json={"taskId": "telegram"}, headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())}) as tr:
                    if tr.status in (200, 201):
                        res["tasks_claimed"] += 1
                        res["notes"].append("task_telegram")
            except Exception:
                pass

        # D. Social Tasks (community_react, x_follow, x_post)
        for tid in ["community_react", "x_follow", "x_post"]:
            t_obj = tasks.get(tid) or {}
            if t_obj.get("enabled") and not t_obj.get("claimed"):
                try:
                    conf = t_obj.get("confirmation")
                    att_id = conf.get("attemptId") if isinstance(conf, dict) else None
                    if not att_id:
                        async with session.post(f"{base_url}/api/tasks/social/start", json={"taskId": tid}, headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())}) as vs:
                            if vs.status == 200:
                                vd = await vs.json()
                                att = vd.get("attempt") or {}
                                att_id = att.get("attemptId")
                                confirm_at = att.get("confirmAt", 0)
                                wait_s = max(0.5, min(16.0, (confirm_at - srv_now) / 1000.0))
                                await asyncio.sleep(wait_s + 0.5)
                    if att_id:
                        await session.post(f"{base_url}/api/tasks/social/confirm", json={"taskId": tid, "attemptId": att_id, "confirmed": True}, headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())})
                        async with session.post(f"{base_url}/api/tasks/claim", json={"taskId": tid}, headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())}) as tr:
                            if tr.status in (200, 201):
                                res["tasks_claimed"] += 1
                                res["notes"].append(f"task_{tid}")
                except Exception:
                    pass

        # E. Rewarded Ad Task
        t_ad = tasks.get("ad") or {}
        if t_ad.get("enabled") and not t_ad.get("claimed") and (t_ad.get("quotaUsed", 0) < t_ad.get("quotaTotal", 4)):
            try:
                async with session.post(f"{base_url}/api/adsgram/start", json={}, headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())}) as ar:
                    if ar.status == 200:
                        ad_d = await ar.json()
                        ad_att_id = ad_d.get("attemptId")
                        if ad_att_id:
                            await asyncio.sleep(2.5)
                            await session.post(f"{base_url}/api/adsgram/complete", json={"attemptId": ad_att_id}, headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())})
                            async with session.post(f"{base_url}/api/tasks/claim", json={"taskId": "ad"}, headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())}) as cr:
                                if cr.status in (200, 201):
                                    res["tasks_claimed"] += 1
                                    res["notes"].append("task_ad")
            except Exception:
                pass

        # F. Solana Launch Campaign Tasks (quiz & pump)
        try:
            async with session.get(f"{base_url}/api/launch-tasks", headers=auth_headers, timeout=aiohttp.ClientTimeout(total=6)) as lr:
                if lr.status == 200:
                    ld = await lr.json()
                    if ld.get("enabled"):
                        quiz = ld.get("quiz", {})
                        pump = ld.get("pump", {})
                        if not quiz.get("claimed"):
                            async with session.post(f"{base_url}/api/launch-tasks/quiz", json={"answer": "ton_continues"}, headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())}, timeout=aiohttp.ClientTimeout(total=6)) as qr:
                                if qr.status == 200:
                                    res["tasks_claimed"] += 1
                                    res["notes"].append("launch_quiz_5_diggo")
                        if not pump.get("confirmed"):
                            await session.post(f"{base_url}/api/launch-tasks/pump/open", json={}, headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())}, timeout=aiohttp.ClientTimeout(total=5))
                            async with session.post(f"{base_url}/api/launch-tasks/pump/confirm", json={"confirmed": True}, headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())}, timeout=aiohttp.ClientTimeout(total=5)) as pr:
                                if pr.status == 200:
                                    res["tasks_claimed"] += 1
                                    res["notes"].append("launch_pump_confirmed")
        except Exception:
            pass

    except Exception as e:
        res["notes"].append(f"err: {str(e)[:50]}")

    return res


async def sweep_pepegram_tasks(session: aiohttp.ClientSession, uid: str, name: str, p_init: str, acc: dict) -> Dict[str, Any]:
    """Sweeps PepeGram mining claims, welcome bonuses, and available side-tasks."""
    res = {"bot": "PepeGram", "tasks_claimed": 0, "notes": [], "success": False}
    if not p_init:
        res["notes"].append("no_init_data")
        return res

    try:
        pepe_base = "https://app.miniempire.app/miniapp"
        pepe_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36",
            "Origin": "https://app.miniempire.app",
            "Referer": "https://app.miniempire.app/miniapp/index.html?tid=1449&lang=en"
        }

        # 1. Auth
        async with session.post(f"{pepe_base}/auth?tid=1449", json={"initData": p_init, "tid": 1449}, headers=pepe_headers, timeout=aiohttp.ClientTimeout(total=8)) as r:
            if r.status != 200:
                res["notes"].append(f"auth_status_{r.status}")
                return res
            auth_d = await r.json()

        if isinstance(auth_d, dict) and auth_d.get("error") == "user not registered":
            res["notes"].append("not_registered_in_bot")
            return res

        res["success"] = True
        u_data = auth_d.get("user") or {}
        res["balance"] = float(u_data.get("hashes", 0) or 0)
        res["level"] = int(u_data.get("power", 0) or 0)
        ends_at = int(u_data.get("hashes_production_ends_at", 0) or 0)

        # 2. Welcome bonus & Claim
        await jitter(0.4, 0.8)
        async with session.post(f"{pepe_base}/claim-welcome-bonus?tid=1449", json={"initData": p_init, "tid": 1449}, headers=pepe_headers) as wr:
            if wr.status in (200, 201):
                res["notes"].append("welcome_bonus_claimed")

        async with session.post(f"{pepe_base}/claim?tid=1449", json={"initData": p_init, "tid": 1449}, headers=pepe_headers) as clr:
            if clr.status in (200, 201):
                res["notes"].append("hashes_claimed")

        # 3. Mine tap
        await jitter(0.4, 0.8)
        async with session.post(f"{pepe_base}/tasks/mine?tid=1449", json={"initData": p_init, "tid": 1449}, headers=pepe_headers) as mr:
            if mr.status in (200, 201):
                res["notes"].append("mine_tapped")

        # 4. Production Start (6-Hour Mining Session & Referral Power Activation)
        now_ts = int(time.time())
        if now_ts >= ends_at:
            await jitter(0.4, 0.8)
            async with session.post(f"{pepe_base}/start-production?tid=1449", json={"initData": p_init, "tid": 1449}, headers=pepe_headers) as spr:
                if spr.status in (200, 201):
                    res["notes"].append("production_started")

        # 5. Free Power Boosts (Ad rolls & Slot spins)
        await jitter(0.3, 0.6)
        await session.post(f"{pepe_base}/tasks/ad-roll?tid=1449", json={"initData": p_init, "tid": 1449}, headers=pepe_headers)
        await session.post(f"{pepe_base}/tasks/ad-roll2?tid=1449", json={"initData": p_init, "tid": 1449}, headers=pepe_headers)
        await session.post(f"{pepe_base}/tasks/slot-spin?tid=1449", json={"initData": p_init, "tid": 1449}, headers=pepe_headers)

        # 6. Tasks claim
        await jitter(0.4, 0.8)
        async with session.get(f"{pepe_base}/tasks?initData={urllib.parse.quote(p_init)}&tid=1449", headers=pepe_headers) as tr:
            if tr.status == 200:
                t_d = await tr.json()
                for tk in (t_d.get("tasks", []) if isinstance(t_d, dict) else []):
                    tk_id = tk.get("id")
                    is_done = tk.get("completed")
                    is_eligible = tk.get("eligible")
                    if tk_id and not is_done and (not tk.get("pending") or is_eligible):
                        await jitter(0.4, 0.8)
                        async with session.post(f"{pepe_base}/tasks/claim?tid=1449", json={"initData": p_init, "tid": 1449, "task_id": tk_id, "taskId": tk_id}, headers=pepe_headers) as cr:
                            if cr.status in (200, 201):
                                res["tasks_claimed"] += 1
                                res["notes"].append(f"task_{tk_id}")

    except Exception as e:
        res["notes"].append(f"err: {str(e)[:50]}")

    return res


async def sweep_adxearn_tasks(session: aiohttp.ClientSession, uid: str, name: str, adx_init: str, acc: dict) -> Dict[str, Any]:
    """Sweeps AdxEarn AI check-in, farming claims, dynamic tasks, and milestones."""
    res = {"bot": "AdxEarn AI", "tasks_claimed": 0, "notes": [], "success": False}
    if not adx_init:
        res["notes"].append("no_init_data")
        return res

    try:
        adx_base = "https://api.adxearnai.xyz/api"
        adx_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36",
            "X-Telegram-Init-Data": adx_init
        }

        # 1. User Session
        fp = f"412x915|24|8|UTC|en-US|8|5|2.625|Mali-G78-{uid}"
        ref_param = None if str(uid) == MASTER_UID else "6727787768"
        async with session.post(f"{adx_base}/user/session", json={"ref": ref_param, "fp": fp}, headers=adx_headers, timeout=aiohttp.ClientTimeout(total=8)) as r:
            if r.status != 200:
                res["notes"].append(f"session_status_{r.status}")
                return res
            s_d = await r.json()

        res["success"] = True
        u_info = (s_d.get("user") if isinstance(s_d, dict) else {}) or {}
        res["balance"] = float(u_info.get("balance_points", 0) or 0)
        res["level"] = int(u_info.get("checkin_streak", 1) or 1)

        # 2. Daily Check-in
        await jitter(0.4, 0.8)
        async with session.post(f"{adx_base}/rewards/checkin", json={}, headers=adx_headers) as cr:
            if cr.status == 200:
                c_d = await cr.json()
                if c_d.get("success"):
                    res["tasks_claimed"] += 1
                    res["notes"].append(f"checkin_reward_{c_d.get('reward', 0)}")
            elif cr.status == 403:
                res["notes"].append("already_checked_in_today")

        # 3. Farming Claim & Start
        await jitter(0.4, 0.8)
        async with session.get(f"{adx_base}/farming/status", headers=adx_headers) as st_r:
            if st_r.status == 200:
                st_d = await st_r.json()
                if isinstance(st_d, dict):
                    if st_d.get("ready"):
                        await session.post(f"{adx_base}/farming/claim", json={}, headers=adx_headers)
                        res["notes"].append("farming_claimed")
                    if st_d.get("status") == "idle" or not st_d.get("startedAt"):
                        await session.post(f"{adx_base}/farming/start", json={}, headers=adx_headers)
                        res["notes"].append("farming_started")

        # 4. Farming Boost
        await jitter(0.3, 0.7)
        await session.post(f"{adx_base}/farming/boost", json={}, headers=adx_headers)

        # 5. Dynamic Tasks (Wait 16.0s for delayed tasks like 8 and 9)
        await jitter(0.4, 0.8)
        async with session.get(f"{adx_base}/rewards/tasks", headers=adx_headers) as tr:
            if tr.status == 200:
                td = await tr.json()
                started_tasks = []
                for tk in (td.get("tasks", []) if isinstance(td, dict) else []):
                    t_id = tk.get("id")
                    if t_id and not tk.get("completed") and not tk.get("claimed"):
                        try:
                            async with session.post(f"{adx_base}/rewards/task-start", json={"taskId": t_id}, headers=adx_headers) as s_resp:
                                if s_resp.status == 200:
                                    started_tasks.append(t_id)
                        except Exception:
                            pass
                if started_tasks:
                    await asyncio.sleep(16.0)
                    for t_id in started_tasks:
                        try:
                            async with session.post(f"{adx_base}/rewards/task-claim", json={"taskId": t_id}, headers=adx_headers) as cl:
                                if cl.status == 200:
                                    res["tasks_claimed"] += 1
                                    res["notes"].append(f"task_{t_id}")
                                elif cl.status == 403:
                                    c_err = await cl.json()
                                    if "already completed" in str(c_err.get("error", "")).lower():
                                        res["notes"].append(f"task_{t_id}_already_done")
                        except Exception:
                            pass

        # 6. Referral Milestones Claim
        if str(uid) == MASTER_UID:
            await session.post(f"{adx_base}/referrals/milestones/claim", json={}, headers=adx_headers)

    except Exception as e:
        res["notes"].append(f"err: {str(e)[:50]}")

    return res


async def sweep_chickenland_tasks(session: aiohttp.ClientSession, uid: str, name: str, c_init: str, acc: dict) -> Dict[str, Any]:
    """Sweeps Chicken Land daily check-in, captcha validation, eggs collection/selling, social tasks, hen buying, and ref rewards."""
    res = {"bot": "Chicken Land", "tasks_claimed": 0, "notes": [], "success": False}
    if not c_init:
        res["notes"].append("no_init_data")
        return res

    try:
        if c_init.startswith("TMA "):
            b64_token = c_init[4:].strip()
        elif "%3D" in c_init or "query_id=" in c_init or "user=" in c_init:
            decoded = urllib.parse.unquote(c_init) if "%3D" in c_init else c_init
            b64_token = base64.b64encode(decoded.encode("latin1")).decode("latin1")
        else:
            b64_token = c_init.strip()

        c_headers = {
            "Content-Type": "application/json",
            "Authorization": f"TMA {b64_token}",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36"
        }
        rpc_url = "https://app8968434282.tgcloud.ai/api/rpc"

        async def rpc(path: str, body: dict = None) -> dict:
            payload = {"method": "POST" if body is not None else "GET", "path": path, "body": body if body is not None else {}}
            async with session.post(rpc_url, json=payload, headers=c_headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                return await resp.json()

        # 1. Profile / Session
        ref_to_use = "12668"
        me_resp = await rpc("/api/me", {"ref": ref_to_use, "lang": "en"})
        if not me_resp.get("ok"):
            res["notes"].append(f"auth_failed_{me_resp.get('description', 'unknown')}")
            return res

        res["success"] = True
        u_info = me_resp.get("result", {}).get("user", {})
        res["balance"] = float(u_info.get("coins", 0))
        res["hens"] = int(u_info.get("hens", 0))
        res["rate"] = float(u_info.get("rate", 0))

        # 2. Captcha verification if needed
        if not u_info.get("human"):
            cap = await rpc("/api/captcha", {})
            if cap.get("ok") and cap.get("result", {}).get("kind") == "turnstile":
                await rpc("/api/human", {"fallback": True, "why": "unsupported"})
                await asyncio.sleep(0.5)
                cap2 = await rpc("/api/captcha", {})
                if cap2.get("ok") and cap2.get("result", {}).get("kind") == "pick":
                    items = cap2["result"].get("items", [])
                    tgt = cap2["result"].get("target", "")
                    if tgt in items:
                        await rpc("/api/human", {"pick": items.index(tgt)})

        # 3. Welcome bonus
        if not u_info.get("welcome"):
            w_res = await rpc("/api/welcome", {})
            if w_res.get("ok"):
                res["tasks_claimed"] += 1
                res["notes"].append("welcome_bonus_1000")

        # 4. Daily Checkin
        daily_res = await rpc("/api/task", {"id": "daily"})
        if daily_res.get("ok"):
            res["tasks_claimed"] += 1
            res["notes"].append("daily_checkin")

        # 5. Collect & Sell Eggs (only if basket has accumulated eggs)
        current_coins = float(u_info.get("coins", 0) or 0)
        if int(u_info.get("eggs", 0) or 0) > 0:
            sell_res = await rpc("/api/sell", {})
            if sell_res.get("ok"):
                eggs = sell_res.get("result", {}).get("eggs", 0)
                if eggs > 0:
                    res["notes"].append(f"eggs_sold_{eggs}")
                current_coins = float(sell_res.get("result", {}).get("user", {}).get("coins", current_coins))

        # 6. Tasks
        completed_tasks = set(u_info.get("tasks", []))
        for tid in ["channel", "payments", "dnews", "dpay", "dpromo", "c6"]:
            if tid not in completed_tasks:
                await rpc("/api/task/open", {"id": tid})
                await asyncio.sleep(0.5)
                t_claim = await rpc("/api/task", {"id": tid})
                if t_claim.get("ok"):
                    res["tasks_claimed"] += 1
                    res["notes"].append(f"task_{tid}")
                    if t_claim.get("result", {}).get("user"):
                        current_coins = float(t_claim["result"]["user"].get("coins", current_coins))

        # 7. Ref claim
        ref_claim = await rpc("/api/ref/claim", {})
        if ref_claim.get("ok") and ref_claim.get("result", {}).get("coins", 0) > 0:
            ref_amt = ref_claim["result"]["coins"]
            res["notes"].append(f"ref_coins_{ref_amt}")
            current_coins += ref_amt

        # 8. Buy hens if coins >= 1000
        if current_coins >= 1000:
            n_buy = int(current_coins // 1000)
            buy_res = await rpc("/api/buy", {"breed": "basic", "n": n_buy})
            if buy_res.get("ok"):
                res["notes"].append(f"hens_bought_{n_buy}")

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

        # 6. PepeGram
        pepe_res = await sweep_pepegram_tasks(session, uid, name, acc_toks.get("pepegram_init_data", ""), acc)
        account_report["results"]["pepegram"] = pepe_res

        # 7. AdxEarn AI
        adx_res = await sweep_adxearn_tasks(session, uid, name, acc_toks.get("adxearn_init_data", ""), acc)
        account_report["results"]["adxearn"] = adx_res

        # 8. DiggoMiner
        diggo_res = await sweep_diggo_tasks(session, uid, name, acc_toks.get("diggo_init_data", ""), acc_toks)
        account_report["results"]["diggo"] = diggo_res

        # 9. Chicken Land
        chicken_res = await sweep_chickenland_tasks(session, uid, name, acc_toks.get("chickenland_init_data", ""), acc)
        account_report["results"]["chickenland"] = chicken_res

        # Sync tokens to Cloudflare Workers if newly refreshed
        await sync_token_to_cf(session, uid, acc_toks)

        total_claimed = sum(r.get("tasks_claimed", 0) for r in account_report["results"].values())
        logger.info(f"✅ [{name}] Finished side-tasks! Claimed: {total_claimed} total tasks/rewards.")
        return account_report


async def main():
    logger.info("=============================================================================")
    logger.info("🎯 STARTING COMPLETE 9-BOT FLEET SIDE-TASK HARVEST (20 ACCOUNTS)")
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
        logger.info("\n" + "=" * 80)
        logger.info("📊 8-BOT FLEET ALL SIDE-TASKS HARVEST SUMMARY")
        logger.info("=" * 80)
        total_tasks = 0
        for rep in reports:
            acc_name = rep["account"]
            res = rep["results"]
            mrg_cl = res.get("mrg", {}).get("tasks_claimed", 0)
            atf_cl = res.get("atf", {}).get("tasks_claimed", 0)
            vic_cl = res.get("victors", {}).get("tasks_claimed", 0)
            vyr_cl = res.get("vyro", {}).get("tasks_claimed", 0)
            kyn_cl = res.get("kynex", {}).get("tasks_claimed", 0)
            pep_cl = res.get("pepegram", {}).get("tasks_claimed", 0)
            adx_cl = res.get("adxearn", {}).get("tasks_claimed", 0)
            dig_cl = res.get("diggo", {}).get("tasks_claimed", 0)
            acc_total = mrg_cl + atf_cl + vic_cl + vyr_cl + kyn_cl + pep_cl + adx_cl + dig_cl
            total_tasks += acc_total
            logger.info(f"• {acc_name:<25} | MRG:{mrg_cl} ATF:{atf_cl} VIC:{vic_cl} VYRO:{vyr_cl} KYN:{kyn_cl} PEP:{pep_cl} ADX:{adx_cl} DIG:{dig_cl} | Tot: {acc_total}")

        logger.info("=" * 80)
        logger.info(f"🏁 GRAND TOTAL SIDE-TASKS/REWARDS CLAIMED: {total_tasks}")
        logger.info("=============================================================================")


if __name__ == "__main__":
    asyncio.run(main())
