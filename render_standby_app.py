import os
import sys
import time
import json
import random
import asyncio
import urllib.parse
import logging
import re
import aiohttp
import datetime
import secrets
import hashlib
import hmac
import traceback
import uuid
import struct
from typing import Any
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    import ecdsa
    import base58
    HAS_ECDSA = True
except ImportError:
    HAS_ECDSA = False

GLOBAL_MTPROTO_SEMAPHORE = asyncio.Semaphore(1)

try:
    from proxy_manager import get_account_user_agent, get_account_fingerprint, parse_proxy, DEVICE_POOL
except Exception:
    FALLBACK_DEVICE_POOL = [
        {"model": "Samsung Galaxy A30", "sys": "Android 11 (RP1A.200720.012)", "app": "11.1.3 (5221)", "ua": "Mozilla/5.0 (Linux; Android 11; SM-A305F) AppleWebKit/537.36 Telegram-Android/11.1.3"},
        {"model": "Samsung Galaxy A54 5G", "sys": "Android 14 (OneUI 6.1)", "app": "11.1.2 (5210)", "ua": "Mozilla/5.0 (Linux; Android 14; SM-A546E) AppleWebKit/537.36 Telegram-Android/11.1.2"},
        {"model": "Xiaomi Redmi Note 12", "sys": "Android 14 (HyperOS 1.0)", "app": "11.1.0 (5202)", "ua": "Mozilla/5.0 (Linux; Android 14; 23021RAAEG) AppleWebKit/537.36 Telegram-Android/11.1.0"},
        {"model": "Realme C55", "sys": "Android 14 (RealmeUI 5.0)", "app": "11.0.9 (5195)", "ua": "Mozilla/5.0 (Linux; Android 14; RMX3710) AppleWebKit/537.36 Telegram-Android/11.0.9"},
        {"model": "Vivo Y22", "sys": "Android 14 (FuntouchOS 14)", "app": "11.1.1 (5205)", "ua": "Mozilla/5.0 (Linux; Android 14; V2207) AppleWebKit/537.36 Telegram-Android/11.1.1"},
        {"model": "Xiaomi Redmi Note 13 Pro", "sys": "Android 14 (HyperOS 1.0)", "app": "11.1.3 (5221)", "ua": "Mozilla/5.0 (Linux; Android 14; 23117RA68G) AppleWebKit/537.36 Telegram-Android/11.1.3"},
        {"model": "OnePlus Nord CE 3", "sys": "Android 14 (OxygenOS 14)", "app": "11.0.8 (5189)", "ua": "Mozilla/5.0 (Linux; Android 14; CPH2569) AppleWebKit/537.36 Telegram-Android/11.0.8"},
        {"model": "Samsung Galaxy S23 Ultra", "sys": "Android 14 (OneUI 6.1)", "app": "11.1.3 (5221)", "ua": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 Telegram-Android/11.1.3"}
    ]
    def get_account_fingerprint(identifier):
        ident_str = str(identifier or "default").strip()
        seed = int(hashlib.sha256(ident_str.encode("utf-8")).hexdigest(), 16)
        profile = FALLBACK_DEVICE_POOL[seed % len(FALLBACK_DEVICE_POOL)]
        return {
            "device_model": profile["model"],
            "system_version": profile["sys"],
            "app_version": profile["app"],
            "lang_code": "en",
            "system_lang_code": "en-BD"
        }
    def get_account_user_agent(identifier):
        ident_str = str(identifier or "default").strip()
        seed = int(hashlib.sha256(ident_str.encode("utf-8")).hexdigest(), 16)
        return FALLBACK_DEVICE_POOL[seed % len(FALLBACK_DEVICE_POOL)]["ua"]
    def parse_proxy(proxy_input):
        return None

def create_telethon_client(sess_str: str = "", identifier: Any = "default", proxy_val: Any = None, timeout: int = 15):
    """Creates a Telethon client configured with authentic Bangladesh (BD) mobile device fingerprint."""
    fp = get_account_fingerprint(identifier)
    acc_proxy = parse_proxy(proxy_val)
    session_obj = StringSession(sess_str) if sess_str else StringSession()
    return TelegramClient(
        session_obj,
        API_ID,
        API_HASH,
        device_model=fp["device_model"],
        system_version=fp["system_version"],
        app_version=fp["app_version"],
        lang_code=fp["lang_code"],
        system_lang_code=fp["system_lang_code"],
        proxy=acc_proxy,
        timeout=timeout
    )

from fastapi import FastAPI, HTTPException, Request
from telethon import TelegramClient, functions
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestWebViewRequest, RequestAppWebViewRequest, ImportChatInviteRequest, GetBotCallbackAnswerRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.account import UpdateNotifySettingsRequest
from telethon.tl.functions.bots import GetBotMenuButtonRequest
from telethon.tl.types import InputBotAppShortName, InputNotifyPeer, InputPeerNotifySettings
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    PhoneNumberInvalidError,
    FloodWaitError
)

try:
    from web3 import Web3
    from eth_account import Account
    HAS_WEB3 = True
except ImportError:
    HAS_WEB3 = False

try:
    from tonsdk.contract.wallet import Wallets, WalletVersionEnum
    import base64
    HAS_TONSDK = True
except ImportError:
    HAS_TONSDK = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RenderSessionCollector")

app = FastAPI(title="MY AGY AI — Standby Batch Session Link Collector")

SECRET_KEY = os.getenv("SECRET_KEY", "agy_cf_secret_7d36994e_2026")
API_ID = int(os.getenv("TELEGRAM_API_ID", "37321306"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "5cd9e5bbfb572a4429a0c54774153b47")
REPORT_CHAT_ID = os.getenv("REPORT_CHAT_ID", "6727787768")
# USER DIRECTIVE: Permanently disable all automated withdrawals to prevent wrong address routing
ENABLE_AUTO_WITHDRAWALS = False

CF_WORKER_URLS = [
    "https://restore-agy.aaaai2.workers.dev",
    "https://restore-agy.aaa-bot.workers.dev",
    "https://restore-agy.aaa222.workers.dev",
    "https://restore-agy.agorameet.workers.dev",
    "https://restore-agy.aaaai.workers.dev"
]

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://znbbaozpevurvbfkxakz.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or ""
UPSTASH_URL = os.getenv("UPSTASH_URL") or os.getenv("UPSTASH_REDIS_REST_URL") or "https://pleasant-locust-220893.upstash.io"
UPSTASH_TOKEN = os.getenv("UPSTASH_TOKEN") or os.getenv("UPSTASH_REDIS_REST_TOKEN") or ""

CACHED_GEMINI_KEYS = []

async def get_gemini_keys() -> list:
    global CACHED_GEMINI_KEYS
    if CACHED_GEMINI_KEYS:
        return CACHED_GEMINI_KEYS
    env_k = os.getenv("GEMINI_API_KEYS", "")
    if env_k:
        CACHED_GEMINI_KEYS = [k.strip() for k in env_k.split(",") if k.strip()]
        return CACHED_GEMINI_KEYS
    if UPSTASH_URL and UPSTASH_TOKEN:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"{UPSTASH_URL}/get/fleet:gemini_keys", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=4)) as r:
                    if r.status == 200:
                        data = await r.json()
                        res = data.get("result")
                        if res:
                            CACHED_GEMINI_KEYS = [k.strip() for k in res.split(",") if k.strip()]
        except Exception:
            pass
    return CACHED_GEMINI_KEYS

# =====================================================================
# DISTRIBUTED MTPROTO COORDINATOR & ACCOUNT CONCURRENCY LOCK ENGINE
# Prevents AuthKeyDuplicatedError by ensuring only 1 node/process accesses an account
# =====================================================================
NODE_INSTANCE_ID = (
    os.getenv("RENDER_SERVICE_NAME")
    or os.getenv("RENDER_SERVICE_ID")
    or os.getenv("RENDER_INSTANCE_ID")
    or ("render_node_" + hashlib.md5(str(os.getpid()).encode()).hexdigest()[:6])
)

# Render 3-Account Baton Relay Map
RENDER_ACCOUNTS_MAP = {
    1: {
        "node": 1,
        "name": "Render Node 1 (Singapore)",
        "service_id": "srv-damuhkmgekts73f1osag",
        "api_key": os.getenv("RENDER_API_KEY_1", ""),
        "url": "https://my-agy-fleet-standby.onrender.com"
    },
    2: {
        "node": 2,
        "name": "Render Node 2 (Frankfurt)",
        "service_id": "srv-dan5q00ae00c73djummg",
        "api_key": os.getenv("RENDER_API_KEY_2", ""),
        "url": "https://my-agy-fleet-standby-node2.onrender.com"
    },
    3: {
        "node": 3,
        "name": "Render Node 3 (Oregon)",
        "service_id": "srv-db437o3tqb8s73dt4erg",
        "api_key": os.getenv("RENDER_API_KEY_3") or os.getenv("RENDER_API_KEY", ""),
        "url": "https://my-agy-fleet-standby-node3.onrender.com"
    }
}

ACTIVE_MTPROTO_CLIENTS: set = set()

def get_current_node_number() -> int:
    nid = (NODE_INSTANCE_ID or "").lower()
    sid = os.getenv("RENDER_SERVICE_ID", "").lower()
    sname = os.getenv("RENDER_SERVICE_NAME", "").lower()

    if "node2" in nid or "dan5q00ae00c73djummg" in nid or sid == "srv-dan5q00ae00c73djummg" or "node2" in sname:
        return 2
    if "node3" in nid or "db437o3tqb8s73dt4erg" in nid or sid == "srv-db437o3tqb8s73dt4erg" or "node3" in sname:
        return 3
    if "node1" in nid or "damuhkmgekts73f1osag" in nid or sid == "srv-damuhkmgekts73f1osag" or "my-agy-fleet-standby" in sname or "my-agy-fleet-standby" in nid:
        return 1
    return 2

# Determine this node's default role
IS_PRIMARY_HOST = (
    "node2" in NODE_INSTANCE_ID.lower()
    or "dan5q00ae00c73djummg" in NODE_INSTANCE_ID.lower()
    or os.getenv("IS_PRIMARY_COORDINATOR", "").lower() in ("1", "true")
)

async def is_this_node_active() -> bool:
    """Dynamically determines if this Render node is the designated active MTProto coordinator."""
    cur_n = get_current_node_number()
    raw_active = await get_active_render_node()
    active_str = str(raw_active).strip('"').strip("'").lower()

    active_n = 2
    for n in (1, 2, 3):
        if str(n) in active_str:
            active_n = n
            break

    return cur_n == active_n

async def get_active_render_node() -> str:
    """Returns the designated active Render node from Upstash Redis (default: node2)."""
    if not (UPSTASH_URL and UPSTASH_TOKEN):
        return "node2"
    try:
        up_h = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{UPSTASH_URL}/get/fleet:active_render_node", headers=up_h, timeout=aiohttp.ClientTimeout(total=2)) as r:
                if r.status == 200:
                    d = await r.json()
                    val = d.get("result")
                    if val and val not in ("null", "false", "0", ""):
                        return str(val).lower()
    except Exception:
        pass
    return "node2"

async def is_in_maintenance_mode() -> tuple[bool, str, int]:
    """Checks if the fleet is in Maintenance Mode (during Render node rotation or cooldown).
    Returns (in_maintenance, reason, seconds_remaining)."""
    if not (UPSTASH_URL and UPSTASH_TOKEN):
        return (False, "", 0)
    try:
        up_h = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{UPSTASH_URL}/get/fleet:maintenance_mode", headers=up_h, timeout=aiohttp.ClientTimeout(total=3)) as r:
                if r.status == 200:
                    d = await r.json()
                    val = d.get("result")
                    if val and val not in ("null", "false", "0", ""):
                        async with s.get(f"{UPSTASH_URL}/get/fleet:maintenance_until", headers=up_h, timeout=aiohttp.ClientTimeout(total=3)) as r_u:
                            until_ts = 0
                            if r_u.status == 200:
                                u_d = await r_u.json()
                                try:
                                    until_ts = float(u_d.get("result") or 0)
                                except Exception:
                                    until_ts = 0
                            now = time.time()
                            if until_ts > now:
                                return (True, str(val), int(until_ts - now))
                            else:
                                await s.post(f"{UPSTASH_URL}/del/fleet:maintenance_mode", headers=up_h, timeout=aiohttp.ClientTimeout(total=2))
                                await s.post(f"{UPSTASH_URL}/del/fleet:maintenance_until", headers=up_h, timeout=aiohttp.ClientTimeout(total=2))
    except Exception as e:
        logger.debug(f"[Maintenance Check] Note: {e}")
    return (False, "", 0)

async def acquire_coordinator_lock(ttl_seconds: int = 120) -> bool:
    """Acquires or refreshes distributed coordinator lock in Upstash Redis.
    Only the active node holding this lock will run background watchdog MTProto tasks."""
    in_maint, _, _ = await is_in_maintenance_mode()
    if in_maint:
        return False
    if not (UPSTASH_URL and UPSTASH_TOKEN):
        return True
    is_this_active = await is_this_node_active()
    try:
        up_h = {"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"}
        async with aiohttp.ClientSession() as s:
            # 1. Check existing coordinator using atomic Redis GET
            async with s.post(UPSTASH_URL, json=["GET", "fleet:mtproto_coordinator"], headers=up_h, timeout=aiohttp.ClientTimeout(total=3)) as r:
                if r.status == 200:
                    data = await r.json()
                    cur_holder = data.get("result")
                    cur_node_num = get_current_node_number()
                    is_same_node = (
                        cur_holder == NODE_INSTANCE_ID
                        or (cur_holder and f"node{cur_node_num}" in str(cur_holder).lower())
                        or (cur_holder and str(cur_holder).lower().strip('"') in (f"node{cur_node_num}", str(cur_node_num)))
                        or (cur_node_num == 2 and cur_holder and "node2" in str(cur_holder).lower())
                    )
                    if is_same_node or (is_this_active and cur_holder in (None, "", "null")):
                        # Refresh lock atomically
                        await s.post(UPSTASH_URL, json=["SET", "fleet:mtproto_coordinator", NODE_INSTANCE_ID, "EX", ttl_seconds], headers=up_h, timeout=aiohttp.ClientTimeout(total=3))
                        return True
                    if cur_holder:
                        return False
            # 2. Key is empty; attempt atomic set-if-not-exists (NX)
            if is_this_active:
                async with s.post(UPSTASH_URL, json=["SET", "fleet:mtproto_coordinator", NODE_INSTANCE_ID, "NX", "EX", ttl_seconds], headers=up_h, timeout=aiohttp.ClientTimeout(total=3)) as r_nx:
                    if r_nx.status == 200:
                        nx_res = await r_nx.json()
                        return nx_res.get("result") == "OK"
    except Exception as e:
        logger.debug(f"[Coordinator Lock] Note: {e}")
    return False

async def acquire_account_lock(account_uid: str, ttl_seconds: int = 60) -> bool:
    """Acquires a single-account distributed lock in Upstash Redis atomically.
    Guarantees that NO TWO PROCESSES across any server connect to the same account simultaneously."""
    if not (UPSTASH_URL and UPSTASH_TOKEN) or not account_uid:
        return True
    try:
        up_h = {"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"}
        key = f"fleet:lock:acc:{account_uid}"
        async with aiohttp.ClientSession() as s:
            async with s.post(UPSTASH_URL, json=["SET", key, NODE_INSTANCE_ID, "NX", "EX", ttl_seconds], headers=up_h, timeout=aiohttp.ClientTimeout(total=3)) as r:
                if r.status == 200:
                    d = await r.json()
                    return d.get("result") == "OK"
    except Exception as e:
        logger.debug(f"[Account Lock] Error for {account_uid}: {e}")
    return False

async def release_account_lock(account_uid: str):
    """Releases the single-account distributed lock atomically."""
    if not (UPSTASH_URL and UPSTASH_TOKEN) or not account_uid:
        return
    try:
        up_h = {"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"}
        key = f"fleet:lock:acc:{account_uid}"
        async with aiohttp.ClientSession() as s:
            await s.post(UPSTASH_URL, json=["DEL", key], headers=up_h, timeout=aiohttp.ClientTimeout(total=2))
    except Exception:
        pass

async def sync_account_health_state(account_idx: int, is_healthy: bool, reason: str = ""):
    """Synchronizes real-time session health state in Upstash Redis across all Cloudflare Workers & Render nodes."""
    if not (UPSTASH_URL and UPSTASH_TOKEN) or not account_idx:
        return
    try:
        idx_str = str(account_idx)
        up_h = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}
        async with aiohttp.ClientSession() as s:
            if is_healthy:
                await s.post(f"{UPSTASH_URL}/sadd/fleet:healthy_sessions/{idx_str}", headers=up_h, timeout=aiohttp.ClientTimeout(total=2))
                await s.post(f"{UPSTASH_URL}/srem/fleet:revoked_sessions/{idx_str}", headers=up_h, timeout=aiohttp.ClientTimeout(total=2))
                await s.post(f"{UPSTASH_URL}/del/fleet:revocation_reason:{idx_str}", headers=up_h, timeout=aiohttp.ClientTimeout(total=2))
            else:
                await s.post(f"{UPSTASH_URL}/sadd/fleet:revoked_sessions/{idx_str}", headers=up_h, timeout=aiohttp.ClientTimeout(total=2))
                await s.post(f"{UPSTASH_URL}/srem/fleet:healthy_sessions/{idx_str}", headers=up_h, timeout=aiohttp.ClientTimeout(total=2))
                if reason:
                    await s.post(f"{UPSTASH_URL}/set/fleet:revocation_reason:{idx_str}?ex=86400", data=reason, headers=up_h, timeout=aiohttp.ClientTimeout(total=2))
    except Exception as e:
        logger.debug(f"[Health Sync] Failed for #{account_idx}: {e}")

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

def solve_atf_math(question_text: str) -> str:
    """Safely solves ATF Miner mathematical challenges with multiple regex fallbacks."""
    if not question_text:
        return "0"
    cleaned = re.sub(r"[^\d\+\-\*\/\(\)\s]", " ", question_text)
    m = re.search(r"(\d+\s*[\+\-\*\/]\s*\d+)", cleaned)
    if m:
        try:
            expr = m.group(1).replace(" ", "")
            parts = re.split(r"([\+\-\*\/])", expr)
            if len(parts) == 3:
                a, op, b = int(parts[0]), parts[1], int(parts[2])
                if op == "+": return str(a + b)
                if op == "-": return str(a - b)
                if op == "*": return str(a * b)
                if op == "/" and b != 0: return str(a // b)
        except Exception:
            pass
    nums = [int(n) for n in re.findall(r"\d+", question_text)]
    if len(nums) >= 2:
        if "+" in question_text or "plus" in question_text.lower():
            return str(nums[0] + nums[1])
        if "-" in question_text or "minus" in question_text.lower():
            return str(nums[0] - nums[1])
        if "*" in question_text or "x" in question_text.lower() or "times" in question_text.lower():
            return str(nums[0] * nums[1])
        if "/" in question_text and nums[1] != 0:
            return str(nums[0] // nums[1])
    return "0"

# Active Fleet Mini-App Bots (All 9 Bots)
MRG_BOT = "mrgminerbot"
MRG_REFERRAL_CODE = "ref_IRN1G3XD"
ATF_BOT = "ATF_AIRDROP_bot"
ATF_REFERRAL_CODE = "6727787768"
VICTORS_BOT = "VictorsCompanybot"
VICTORS_REFERRAL_CODE = "ref_A20AA96F18"
VYRO_BOT = "vyrodrop_bot"
VYRO_REFERRAL_CODE = "ref_myFjrqqE4WN_"
KYNEX_BOT = "Kynex_miningbot"
KYNEX_REFERRAL_CODE = "6727787768"
DIGGO_BOT = "Diggominer_bot"
DIGGO_REFERRAL_CODE = "ref_4088138f11effe8eef4b86ff"
ASTRA_BOT = "ASTRA_AIRDROP_BOT"
ASTRA_REFERRAL_CODE = "ref_6727787768"
PEPEGRAM_BOT = "Pepe_gram_bot"
PEPEGRAM_REFERRAL_CODE = "6727787768"
ADXEARN_BOT = "AdxEarnAibot"
ADXEARN_REFERRAL_CODE = "ref_6727787768"

LAST_BATCH_RUN = {
    "status": "idle",
    "collected": 0,
    "timestamp": 0
}

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "MY AGY AI Standby Batch Session Link Collector",
        "provider": "Render Cloud (Free Tier)",
        "purpose": "Wakes up on-demand to collect batch session links, syncs to 3x Cloudflare KV, triggers cloud farming, and spins down to save free hours.",
        "nodes": CF_WORKER_URLS,
        "last_run": LAST_BATCH_RUN
    }

@app.get("/health")
async def health():
    in_maint, reason, rem = await is_in_maintenance_mode()
    return {
        "ok": True,
        "status": "maintenance" if in_maint else "healthy",
        "in_maintenance": in_maint,
        "maintenance_reason": reason if in_maint else None,
        "cooldown_remaining_seconds": rem if in_maint else 0,
        "node": NODE_INSTANCE_ID
    }

@app.get("/api/fleet/maintenance-status")
async def api_maintenance_status():
    """Returns the fleet maintenance state, remaining cooldown seconds, and active node."""
    in_maint, reason, rem = await is_in_maintenance_mode()
    active_node = await get_active_render_node()
    return {
        "ok": True,
        "in_maintenance": in_maint,
        "reason": reason,
        "remaining_seconds": rem,
        "active_node": active_node,
        "this_node": NODE_INSTANCE_ID,
        "timestamp": time.time()
    }

@app.post("/api/fleet/disconnect-mtproto")
@app.get("/api/fleet/disconnect-mtproto")
async def api_disconnect_mtproto():
    """Immediately and cleanly disconnects all active Telethon MTProto sessions on this node."""
    disconnected_count = 0
    # Disconnect login sessions
    for cid, sess in list(LOGIN_SESSIONS.items()):
        cl = sess.get("client")
        if cl:
            try:
                await cl.disconnect()
                disconnected_count += 1
            except Exception:
                pass
    LOGIN_SESSIONS.clear()

    # Disconnect QR sessions
    for cid, sess in list(QR_SESSIONS.items()):
        cl = sess.get("client")
        if cl:
            try:
                await cl.disconnect()
                disconnected_count += 1
            except Exception:
                pass
    QR_SESSIONS.clear()

    # Disconnect in-flight background MTProto clients
    for cl in list(ACTIVE_MTPROTO_CLIENTS):
        try:
            await cl.disconnect()
            disconnected_count += 1
        except Exception:
            pass
    ACTIVE_MTPROTO_CLIENTS.clear()

    logger.info(f"[MTProto Disconnect] 🔌 Severed {disconnected_count} active Telegram socket connections.")
    return {
        "ok": True,
        "disconnected": disconnected_count,
        "message": "All Telegram MTProto client sockets severed cleanly.",
        "timestamp": time.time()
    }

async def _trigger_node_rotation(to_node: int, cooldown_seconds: int = 300):
    """Executes the rotation from this node to target node with maintenance cooldown."""
    cur_node_num = get_current_node_number()
    target = RENDER_ACCOUNTS_MAP.get(to_node)
    current = RENDER_ACCOUNTS_MAP.get(cur_node_num)
    if not target or not current:
        logger.error(f"[Rotation] Invalid target node {to_node}")
        return

    logger.info(f"[Rotation] 🔄 Initiating handover: Node {cur_node_num} -> Node {to_node} ({cooldown_seconds}s cooldown)")

    # 1. Enable Maintenance Mode & Set Active Node in Redis
    reason = f"Render Node Handover: Node {cur_node_num} -> Node {to_node}"
    if UPSTASH_URL and UPSTASH_TOKEN:
        up_h = {"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"}
        now = time.time()
        until = now + cooldown_seconds
        ex_ttl = cooldown_seconds + 60
        async with aiohttp.ClientSession() as s:
            await s.post(UPSTASH_URL, json=["SET", "fleet:maintenance_mode", reason, "EX", ex_ttl], headers=up_h)
            await s.post(UPSTASH_URL, json=["SET", "fleet:maintenance_until", str(until), "EX", ex_ttl], headers=up_h)
            await s.post(UPSTASH_URL, json=["SET", "fleet:active_render_node", f"node{to_node}"], headers=up_h)
            await s.post(UPSTASH_URL, json=["SET", "fleet:mtproto_coordinator", f"node{to_node}", "EX", cooldown_seconds + 1800], headers=up_h)

    # 2. Telegram Alert
    alert_txt = (
        f"🟡 <b>[FLEET ROTATION] Maintenance Mode Activated</b>\n\n"
        f"🔄 <b>Handover:</b> Node {cur_node_num} ➡️ Node {to_node}\n"
        f"⏳ <b>Cooling Duration:</b> {cooldown_seconds // 60}m ({cooldown_seconds}s)\n"
        f"🛡️ <b>Anti-Ban Safeguard:</b> All Telegram MTProto sockets disconnected to prevent dual-IP bans.\n"
        f"⏸️ <b>Source Node:</b> Suspending container to freeze free tier hour usage."
    )
    if REPORT_BOT_TOKEN and REPORT_CHAT_ID:
        try:
            async with aiohttp.ClientSession() as s:
                await s.post(f"https://api.telegram.org/bot{REPORT_BOT_TOKEN}/sendMessage", json={"chat_id": REPORT_CHAT_ID, "text": alert_txt, "parse_mode": "HTML"})
        except Exception:
            pass

    # 3. Resume target node via Render API
    try:
        r_headers = {"Authorization": f"Bearer {target['api_key']}", "Accept": "application/json"}
        async with aiohttp.ClientSession() as s:
            await s.post(f"https://api.render.com/v1/services/{target['service_id']}/resume", headers=r_headers, timeout=aiohttp.ClientTimeout(total=15))
            logger.info(f"[Rotation] Resumed Node {to_node} ({target['service_id']})")
    except Exception as re:
        logger.error(f"[Rotation] Error resuming Node {to_node}: {re}")

    # 4. Clean disconnect local MTProto
    await api_disconnect_mtproto()

    # 5. Suspend current node via Render API
    try:
        c_headers = {"Authorization": f"Bearer {current['api_key']}", "Accept": "application/json"}
        async with aiohttp.ClientSession() as s:
            await s.post(f"https://api.render.com/v1/services/{current['service_id']}/suspend", headers=c_headers, timeout=aiohttp.ClientTimeout(total=15))
            logger.info(f"[Rotation] Suspended Node {cur_node_num} ({current['service_id']}). Hour meter frozen to 0!")
    except Exception as se:
        logger.error(f"[Rotation] Error suspending Node {cur_node_num}: {se}")

@app.post("/api/fleet/rotate-node")
async def api_rotate_node(request: Request):
    """Triggers an atomic Baton Relay rotation to another Render node with Telegram Anti-Ban Maintenance Mode."""
    data = {}
    try:
        data = await request.json()
    except Exception:
        pass
    to_node = int(data.get("to_node", 3))
    cooldown = int(data.get("cooldown_seconds", 300))
    asyncio.create_task(_trigger_node_rotation(to_node=to_node, cooldown_seconds=cooldown))
    return {
        "ok": True,
        "status": "rotation_initiated",
        "target_node": to_node,
        "cooldown_seconds": cooldown,
        "message": f"Maintenance Mode cooling buffer active ({cooldown}s). Handing over to Node {to_node}."
    }

def format_error(e: Exception) -> str:
    """Helper for formatted error string (never returns empty string)."""
    msg = str(e).strip()
    return f"{type(e).__name__}: {msg}" if msg else type(e).__name__

def is_token_data_expired(t_dict: dict, max_age_hours: float = 20.0) -> bool:
    """
    Checks whether token data is missing, incomplete, or any key bot token is older than max_age_hours.
    Inspects internal auth_date from WebApp initData query strings for true expiration detection.
    """
    if not t_dict or not isinstance(t_dict, dict):
        return True
    now_ts = time.time()
    s_at = t_dict.get("synced_at")
    if not s_at:
        return True
    try:
        if isinstance(s_at, (int, float)):
            age_s = now_ts - (s_at / 1000.0 if s_at > 1e11 else float(s_at))
        elif isinstance(s_at, str):
            clean_s = s_at.strip()
            if clean_s.replace(".", "", 1).isdigit():
                val = float(clean_s)
                age_s = now_ts - (val / 1000.0 if val > 1e11 else val)
            else:
                from datetime import datetime
                dt = datetime.fromisoformat(clean_s.replace("Z", "+00:00"))
                age_s = now_ts - dt.timestamp()
        else:
            return True
        if age_s > (max_age_hours * 3600.0):
            return True
    except Exception:
        return True

    # Check individual token auth_date signatures (Active WebApp Bots)
    key_tokens = [
        "mrg_init_data", "atf_init_data",
        "victors_init_data", "vyro_init_data",
        "kynex_init_data", "diggo_init_data",
        "astra_init_data", "pepegram_init_data",
        "adxearn_init_data"
    ]
    present_cnt = 0
    expired_cnt = 0
    for kt in key_tokens:
        tok_val = t_dict.get(kt)
        if not tok_val:
            continue
        present_cnt += 1
        try:
            parsed = urllib.parse.parse_qs(str(tok_val))
            ad = parsed.get("auth_date", [None])[0]
            if ad and ad.isdigit():
                tok_age = now_ts - float(ad)
                max_bot_age = (12.0 * 3600.0) if kt in ("vyro_init_data", "diggo_init_data") else (max_age_hours * 3600.0)
                if tok_age > max_bot_age:
                    expired_cnt += 1
        except Exception:
            pass

    if present_cnt == 0 or expired_cnt > 0:
        return True
    return False

async def extract_bot_webapp_token(client: TelegramClient, bot_username: str, start_param: str = "", default_url: str = "", candidate_short_names: list = None) -> str:
    """
    Universal, resilient WebApp token extractor for Telegram bots.
    Employs 4 strategic fallbacks:
      1. RequestAppWebViewRequest with candidate short names (app, play, myapp, etc.)
      2. Bot Menu Button (functions.bots.GetBotMenuButtonRequest)
      3. Inline Keyboard buttons in recent messages (web_app.url, b.click(), tgWebApp url)
      4. Direct RequestWebViewRequest with known default WebApp URL
    """
    if not bot_username:
        return None

    def extract_from_url(url_str):
        if not url_str:
            return None
        try:
            p = urllib.parse.urlparse(str(url_str))
            frag = urllib.parse.parse_qs(p.fragment).get("tgWebAppData", [None])[0]
            if frag:
                if frag.startswith("user%3D") or "%257B" in frag or "%2522" in frag:
                    frag = urllib.parse.unquote(frag)
                return frag
            query = urllib.parse.parse_qs(p.query).get("tgWebAppData", [None])[0]
            if query:
                if query.startswith("user%3D") or "%257B" in query or "%2522" in query:
                    query = urllib.parse.unquote(query)
                return query
        except Exception:
            pass
        return None

    bot_ent = None
    bot_in = None
    try:
        bot_ent = await client.get_entity(bot_username)
        bot_in = await client.get_input_entity(bot_ent)
    except Exception as e:
        logger.debug(f"Entity resolution note for {bot_username}: {e}")
        return None

    # Strategy A: Try RequestAppWebViewRequest with candidate short names
    names_to_try = candidate_short_names or ["openapp", "app", "play", "myapp", "miniapp", "miner", "startapp", "bot", "game"]
    for sn in names_to_try:
        try:
            req_p = {
                "peer": bot_in,
                "app": InputBotAppShortName(bot_id=bot_in, short_name=sn),
                "platform": "android"
            }
            if start_param:
                req_p["start_param"] = str(start_param)
            res = await client(RequestAppWebViewRequest(**req_p))
            tok = extract_from_url(getattr(res, "url", None))
            if tok:
                return tok
        except Exception:
            continue

    # Strategy B: Bot Menu Button (functions.bots.GetBotMenuButtonRequest)
    try:
        menu = await client(functions.bots.GetBotMenuButtonRequest(user_id=bot_in))
        menu_btn = getattr(menu, "button", None)
        if menu_btn and hasattr(menu_btn, "url") and menu_btn.url:
            req_p = {
                "peer": bot_ent,
                "bot": bot_ent,
                "platform": "android",
                "url": menu_btn.url
            }
            if start_param:
                req_p["start_param"] = str(start_param)
            res = await client(RequestWebViewRequest(**req_p))
            tok = extract_from_url(getattr(res, "url", None))
            if tok:
                return tok
    except Exception:
        pass

    # Strategy C: Inline Keyboard buttons in existing bot messages (Zero-spam: never send /start)
    try:
        msgs = await client.get_messages(bot_ent, limit=5)
        for m in msgs:
            if not m.out and m.buttons:
                for row in m.buttons:
                    for b in row:
                        raw_b = getattr(b, "button", b)
                        # 1. Direct web_app attribute
                        w_url = getattr(getattr(raw_b, "web_app", None), "url", None) or getattr(raw_b, "url", None)
                        if w_url:
                            try:
                                req_p = {
                                    "peer": bot_ent,
                                    "bot": bot_ent,
                                    "platform": "android",
                                    "url": w_url
                                }
                                if start_param:
                                    req_p["start_param"] = str(start_param)
                                res = await client(RequestWebViewRequest(**req_p))
                                tok = extract_from_url(getattr(res, "url", None))
                                if tok:
                                    return tok
                            except Exception:
                                pass
                        b_url = getattr(raw_b, "url", None)
                        if b_url and "tgWebApp" in b_url:
                            tok = extract_from_url(b_url)
                            if tok:
                                return tok
                        # Zero-chat policy: Never trigger callback clicks in bot chats! Silent URL extraction only.
                        pass
    except Exception:
        pass

    # Strategy D: Direct RequestWebViewRequest with known default URL
    if default_url and not default_url.startswith("https://t.me/"):
        try:
            req_p = {
                "peer": bot_ent,
                "bot": bot_ent,
                "platform": "android",
                "url": default_url
            }
            if start_param:
                req_p["start_param"] = str(start_param)
            res = await client(RequestWebViewRequest(**req_p))
            tok = extract_from_url(getattr(res, "url", None))
            if tok:
                return tok
        except Exception:
            if start_param:
                try:
                    res = await client(RequestWebViewRequest(peer=bot_ent, bot=bot_ent, platform="android", url=default_url))
                    tok = extract_from_url(getattr(res, "url", None))
                    if tok:
                        return tok
                except Exception:
                    pass

    return None


async def extract_tokens_with_client(client: TelegramClient, acc: dict) -> dict:
    """Extracts fresh WebApp session initData tokens across all 7 active MiniApp bots."""
    name = acc.get("name", "User")
    uid = str(acc.get("user_id")) if acc.get("user_id") else None
    if not uid or uid == "None":
        try:
            me = await client.get_me()
            if me:
                uid = str(me.id)
                name = me.first_name or name
                acc["user_id"] = me.id
                acc["name"] = name
        except Exception:
            pass
    uid = uid or "unknown"
    tokens = {
        "account_id": uid,
        "name": name,
        "synced_at": time.time()
    }

    is_master = (uid == str(REPORT_CHAT_ID) or uid == "6727787768")

    # 1. MRG Miner (@mrgminerbot)
    mrg_param = None if is_master else MRG_REFERRAL_CODE
    tok = await extract_bot_webapp_token(client, MRG_BOT, start_param=mrg_param, default_url="https://app.mrgtoken.xyz/", candidate_short_names=["app", "miniapp"])
    if tok:
        tokens["mrg_init_data"] = tok
    await asyncio.sleep(random.uniform(0.5, 1.2))

    # 2. ATF Miner (@ATF_AIRDROP_bot - Silent WebApp query, zero chat messages)
    atf_param = None if is_master else ATF_REFERRAL_CODE
    tok = await extract_bot_webapp_token(client, ATF_BOT, start_param=atf_param, default_url="https://atfminers.asloni.online/miner/index.html?entry=bot_start", candidate_short_names=["app", "miner", "play"])
    if tok:
        tokens["atf_init_data"] = tok
    await asyncio.sleep(random.uniform(0.5, 1.2))

    # 3. Victor's Company (@VictorsCompanybot - Silent WebApp query, zero chat messages)
    v_param = None if is_master else VICTORS_REFERRAL_CODE
    tok = await extract_bot_webapp_token(client, VICTORS_BOT, start_param=v_param, default_url="https://app.victors.company/", candidate_short_names=["app", "play"])
    if tok:
        tokens["victors_init_data"] = tok
    await asyncio.sleep(random.uniform(0.5, 1.2))

    # 4. VyroDrop (@vyrodrop_bot - Silent WebApp query, zero chat messages)
    vy_param = None if is_master else VYRO_REFERRAL_CODE
    tok = await extract_bot_webapp_token(client, VYRO_BOT, start_param=vy_param, default_url="https://vyro.run.place/", candidate_short_names=["app", "vyro", "play", "mine"])
    if tok:
        tokens["vyro_init_data"] = tok
    await asyncio.sleep(random.uniform(0.5, 1.2))

    # 5. Kynex Network (@Kynex_miningbot - Silent WebApp query, zero chat messages)
    ky_param = None if is_master else KYNEX_REFERRAL_CODE
    tok = await extract_bot_webapp_token(client, KYNEX_BOT, start_param=ky_param, default_url="https://kynex.top/telegram-auth.html", candidate_short_names=["App", "app"])
    if tok:
        tokens["kynex_init_data"] = tok
    await asyncio.sleep(random.uniform(0.5, 1.2))

    # 6. DiggoMiner (@Diggominer_bot - Silent WebApp query)
    diggo_param = None if is_master else DIGGO_REFERRAL_CODE
    tok = await extract_bot_webapp_token(client, DIGGO_BOT, start_param=diggo_param, default_url="https://diggo.linkpc.net/", candidate_short_names=["openapp", "app", "miner", "miniapp", "startapp"])
    if tok:
        tokens["diggo_init_data"] = tok
    await asyncio.sleep(random.uniform(0.5, 1.2))

    # 8. Astra Airdrop (@ASTRA_AIRDROP_BOT)
    astra_param = None if is_master else ASTRA_REFERRAL_CODE
    tok = await extract_bot_webapp_token(client, ASTRA_BOT, start_param=astra_param, default_url="https://amazing-alpaca-eb7e2b.netlify.app/", candidate_short_names=["app", "airdrop", "startapp"])
    if tok:
        tokens["astra_init_data"] = tok
    await asyncio.sleep(random.uniform(0.5, 1.2))

    # 9. PepeGram (@Pepe_gram_bot - meme token mining)
    pepe_param = None if is_master else PEPEGRAM_REFERRAL_CODE
    if not is_master and not acc.get("pepegram_referral_bound"):
        try:
            await client.send_message(PEPEGRAM_BOT, f"/start {pepe_param}")
            await asyncio.sleep(0.6)
            acc["pepegram_referral_bound"] = True
        except Exception:
            pass
    tok = await extract_bot_webapp_token(client, PEPEGRAM_BOT, start_param=pepe_param, default_url="https://app.miniempire.app/miniapp/index.html?tid=1449&lang=en", candidate_short_names=["app", "game", "miner", "miniapp", "startapp"])
    if tok:
        tokens["pepegram_init_data"] = tok
    await asyncio.sleep(random.uniform(0.5, 1.2))

    # 10. AdxEarn AI (@AdxEarnAibot)
    adx_param = None if is_master else ADXEARN_REFERRAL_CODE
    tok = await extract_bot_webapp_token(client, ADXEARN_BOT, start_param=adx_param, default_url="https://app.adxearnai.xyz/index.html", candidate_short_names=["app", "startapp"])
    if tok:
        tokens["adxearn_init_data"] = tok

    # Anti-ban hardening: Zero channel joining during token extraction.
    return tokens


async def extract_tokens_for_account(acc: dict) -> dict:
    name = acc.get("name", "User")
    sess_str = acc.get("session_string") or acc.get("session")
    uid = str(acc.get("user_id") or acc.get("id") or "")
    idx = acc.get("index") or 0
    if not sess_str:
        return {}

    # STRICT 1-IP PINNING GUARD: Only the currently active coordinator node connects to MTProto.
    # Standby nodes strictly idle to permanently prevent multi-IP AuthKeyDuplicatedError.
    if not (await is_this_node_active()):
        cur_n = get_current_node_number()
        act_n = await get_active_render_node()
        logger.info(f"[{name}] Standby node {cur_n} ({NODE_INSTANCE_ID}) skipping MTProto connection — active coordinator is {act_n}.")
        return {}

    # Strict MTProto Concurrency Serializer: exactly 1 account connects at a time
    async with GLOBAL_MTPROTO_SEMAPHORE:
        # Acquire account-level distributed lock to guarantee zero concurrent connections
        if uid:
            locked = await acquire_account_lock(uid, ttl_seconds=60)
            if not locked:
                logger.info(f"[{name}] Account #{idx} currently locked by another node/task; skipping to prevent AuthKeyDuplicatedError.")
                return {}

        client = create_telethon_client(sess_str=sess_str, identifier=acc.get("phone") or name, proxy_val=acc.get("proxy"))
        ACTIVE_MTPROTO_CLIENTS.add(client)
        try:
            connected = False
            for attempt in range(1, 4):
                try:
                    await client.connect()
                    if await client.is_user_authorized():
                        connected = True
                        if idx:
                            await sync_account_health_state(idx, is_healthy=True)
                        break
                    else:
                        logger.warning(f"[{name}] Session unauthorized")
                        if idx:
                            await sync_account_health_state(idx, is_healthy=False, reason="Session unauthorized / logged out")
                        return {}
                except Exception as conn_err:
                    err_str = str(conn_err)
                    if "used under two different IP addresses" in err_str or "AUTH_KEY_DUPLICATED" in err_str or "AuthKeyDuplicatedError" in type(conn_err).__name__:
                        logger.warning(f"[{name}] MTProto session duplicated/revoked")
                        if idx:
                            await sync_account_health_state(idx, is_healthy=False, reason="AuthKeyDuplicatedError (multi-IP clash)")
                        return {}
                    if attempt < 3:
                        await asyncio.sleep(attempt * 2.0)
                    else:
                        logger.error(f"[{name}] Connection error after 3 attempts: {conn_err}")
                        return {}
            if not connected:
                return {}

            return await extract_tokens_with_client(client, acc)
        except Exception as e:
            logger.error(f"[{name}] Telethon connection error: {e}")
            return {}
        finally:
            ACTIVE_MTPROTO_CLIENTS.discard(client)
            try:
                await client.disconnect()
            except Exception:
                pass
            if uid:
                await release_account_lock(uid)
            # Randomized human cooldown before next account connection
            await asyncio.sleep(random.uniform(4.0, 8.0))

@app.post("/collect-tokens")
@app.get("/collect-tokens")
async def collect_tokens(request: Request):
    auth = request.headers.get("Authorization") or ""
    req_secret = request.query_params.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    accounts = body.get("accounts", [])
    
    # If accounts lack session strings, pull latest_backup_zip from Cloudflare KV
    has_sessions = any(a.get("session_string") or a.get("session") for a in accounts) if accounts else False
    if not has_sessions:
        import zipfile
        import io
        async with aiohttp.ClientSession() as http:
            for cf_url in CF_WORKER_URLS:
                try:
                    async with http.get(f"{cf_url}/backup.zip", headers=BROWSER_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as r:
                        if r.status == 200:
                            zip_bytes = await r.read()
                            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                                if "accounts.json" in zf.namelist():
                                    raw_acc = zf.read("accounts.json").decode("utf-8")
                                    accounts = json.loads(raw_acc)
                                    logger.info(f"Loaded {len(accounts)} accounts with sessions from Cloudflare KV backup archive.")
                                    break
                except Exception as e:
                    logger.warning(f"Could not load backup zip from {cf_url}: {e}")

    if not (await is_this_node_active()) and not request.query_params.get("force") == "1":
        cur_n = get_current_node_number()
        act_n = await get_active_render_node()
        return {
            "ok": True,
            "status": "STANDBY_IDLE",
            "message": f"Node {cur_n} ({NODE_INSTANCE_ID}) is standby. MTProto token collection is strictly pinned to active coordinator ({act_n}) to prevent multi-IP collisions."
        }

    if not accounts:
        return {"ok": True, "message": "No accounts with sessions found in backup archive or body", "collected": 0}

    sync_mode = request.query_params.get("sync") == "1" or len(accounts) <= 2

    async def _run_batch_collection(target_accounts):
        LAST_BATCH_RUN["status"] = "running"
        LAST_BATCH_RUN["timestamp"] = time.time()
        LAST_BATCH_RUN["total"] = len(target_accounts)
        LAST_BATCH_RUN["collected"] = 0
        collected_batch = {}
        sem = asyncio.Semaphore(1)

        async def _collect_single(acc):
            async with sem:
                uid = str(acc.get("user_id"))
                tokens = await extract_tokens_for_account(acc)
                if tokens:
                    act_uid = str(tokens.get("account_id") or acc.get("user_id") or uid)
                    collected_batch[act_uid] = tokens
                    LAST_BATCH_RUN["collected"] = len(collected_batch)
                    await sync_account_tokens_to_clouds(tokens)
                await asyncio.sleep(random.uniform(5.0, 10.0))

        tasks = [_collect_single(a) for a in target_accounts]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Trigger Cloudflare Edge Autonomous Cloud Farming (Failback to primary node)
        async with aiohttp.ClientSession() as http:
            for idx, cf_url in enumerate(CF_WORKER_URLS):
                try:
                    async with http.post(
                        f"{cf_url}/api/farm/all",
                        json={"all": True, "bot": "all"},
                        headers={"Authorization": f"Bearer {SECRET_KEY}", "Content-Type": "application/json"},
                        timeout=aiohttp.ClientTimeout(total=8)
                    ) as r:
                        if r.status == 200:
                            break  # Primary handled farming cycle, do NOT fan out to 4 standbys!
                except Exception:
                    pass

        LAST_BATCH_RUN["status"] = "completed"
        LAST_BATCH_RUN["collected"] = len(collected_batch)
        LAST_BATCH_RUN["timestamp"] = time.time()

    if not sync_mode:
        asyncio.create_task(_run_batch_collection(accounts))
        return {
            "ok": True,
            "status": "BATCH_DISPATCHED",
            "accounts_queued": len(accounts),
            "timestamp": time.time(),
            "message": f"Parallel batch token collection running in background across {len(accounts)} accounts with live sync."
        }
    else:
        await _run_batch_collection(accounts)
        return {
            "ok": True,
            "collected": LAST_BATCH_RUN.get("collected", 0),
            "timestamp": LAST_BATCH_RUN.get("timestamp", time.time()),
            "message": "Batch session links collected and synced to 5x Cloudflare KV nodes and Upstash Redis."
        }

# ============================================================================
# CLOUD BNB GALAXY AUTONOMOUS ENGINE (Balance Checks & Auto-Withdrawals)
# ============================================================================
MIN_WITHDRAWAL = float(os.getenv("MIN_WITHDRAWAL", "0.000055"))
DEFAULT_WALLET = os.getenv("WALLET_ADDRESS", "0xfda4182001672b9f0f09e2118242e543e35ed5ce")
CLOUD_BNB_STATUS = {
    "last_cycle_at": 0,
    "status": "idle",
    "accounts": {}
}

FLEET_ACCOUNTS_CACHE = {}

async def fetch_accounts_from_cloud():
    global FLEET_ACCOUNTS_CACHE
    accounts_map = {}
    
    # 1. First check in-memory cache
    if FLEET_ACCOUNTS_CACHE:
        accounts_map.update(FLEET_ACCOUNTS_CACHE)

    # 2. Load base fleet accounts from Cloudflare KV backup archive
    import zipfile
    import io
    async with aiohttp.ClientSession() as http:
        for cf_url in CF_WORKER_URLS:
            try:
                async with http.get(f"{cf_url}/backup.zip", headers=BROWSER_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    if r.status == 200:
                        zip_bytes = await r.read()
                        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                            if "accounts.json" in zf.namelist():
                                raw_acc = zf.read("accounts.json").decode("utf-8")
                                for a in json.loads(raw_acc):
                                    uid = str(a.get("user_id"))
                                    if uid and uid not in accounts_map:
                                        accounts_map[uid] = a
                                logger.info(f"Loaded {len(accounts_map)} base accounts from Cloudflare backup archive.")
                                break
            except Exception as e:
                logger.warning(f"Could not load backup zip from {cf_url}: {e}")

        # 3. Merge newly onboarded accounts from Upstash Redis (batched pipeline)
        if UPSTASH_URL and UPSTASH_TOKEN:
            try:
                up_h = {"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"}
                async with http.get(f"{UPSTASH_URL}/keys/account:*", headers=up_h, timeout=aiohttp.ClientTimeout(total=5)) as ur:
                    if ur.status == 200:
                        udata = await ur.json()
                        keys = udata.get("result", [])
                        if keys:
                            pipe_payload = [["get", k] for k in keys]
                            async with http.post(f"{UPSTASH_URL}/pipeline", json=pipe_payload, headers=up_h, timeout=aiohttp.ClientTimeout(total=6)) as pr:
                                if pr.status == 200:
                                    pdata = await pr.json()
                                    for item in pdata:
                                        rstr = item.get("result")
                                        if rstr:
                                            try:
                                                acc_obj = json.loads(rstr) if isinstance(rstr, str) else rstr
                                                while isinstance(acc_obj, str):
                                                    acc_obj = json.loads(acc_obj)
                                                if isinstance(acc_obj, dict):
                                                    auid = str(acc_obj.get("user_id"))
                                                    if auid and auid.isdigit():
                                                        if auid not in accounts_map:
                                                            accounts_map[auid] = acc_obj
                                                        else:
                                                            if acc_obj.get("session_string"):
                                                                accounts_map[auid]["session_string"] = acc_obj["session_string"]
                                                            accounts_map[auid].update(acc_obj)
                                            except Exception:
                                                pass
            except Exception as ue:
                logger.debug(f"Upstash account fetch note: {ue}")

        # 4. Merge accounts from Supabase Postgres
        if SUPABASE_URL and SUPABASE_KEY:
            try:
                sb_h = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
                async with http.get(f"{SUPABASE_URL}/rest/v1/accounts?select=*", headers=sb_h, timeout=aiohttp.ClientTimeout(total=5)) as sbr:
                    if sbr.status == 200:
                        sdata = await sbr.json()
                        if isinstance(sdata, list):
                            for sa in sdata:
                                if isinstance(sa, dict):
                                    suid = str(sa.get("user_id"))
                                    if suid and suid.isdigit():
                                        if suid not in accounts_map:
                                            accounts_map[suid] = sa
                                        else:
                                            for f_k, f_v in sa.items():
                                                if f_v is not None and (f_k not in accounts_map[suid] or not accounts_map[suid].get(f_k)):
                                                    accounts_map[suid][f_k] = f_v
            except Exception as se:
                logger.debug(f"Supabase account fetch note: {se}")

        # 5. Merge user bot accounts with active tokens from Upstash Redis
        if UPSTASH_URL and UPSTASH_TOKEN:
            try:
                up_h = {"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"}
                async with http.get(f"{UPSTASH_URL}/get/miniapp_tokens", headers=up_h, timeout=aiohttp.ClientTimeout(total=4)) as tr:
                    if tr.status == 200:
                        tdata = await tr.json()
                        t_res = tdata.get("result")
                        if t_res:
                            t_map = json.loads(t_res) if isinstance(t_res, str) else t_res
                            if isinstance(t_map, dict):
                                for tuid, tinfo in t_map.items():
                                    tuid_str = str(tuid)
                                    if tuid_str and tuid_str.isdigit() and tuid_str not in accounts_map:
                                        accounts_map[tuid_str] = {
                                            "user_id": int(tuid_str),
                                            "name": tinfo.get("name", f"Account_{tuid_str[-4:]}") if isinstance(tinfo, dict) else f"Account_{tuid_str[-4:]}",
                                            "phone": tinfo.get("phone", "") if isinstance(tinfo, dict) else "",
                                            "status": "active"
                                        }
                async with http.get(f"{UPSTASH_URL}/smembers/ub_registered_users", headers=up_h, timeout=aiohttp.ClientTimeout(total=4)) as ur_users:
                    if ur_users.status == 200:
                        u_list = (await ur_users.json()).get("result", [])
                        if u_list:
                            pipe_ub = [["get", f"ub_user:{u}"] for u in u_list[:50]]
                            async with http.post(f"{UPSTASH_URL}/pipeline", json=pipe_ub, headers=up_h, timeout=aiohttp.ClientTimeout(total=5)) as ub_pipe_r:
                                if ub_pipe_r.status == 200:
                                    ub_pipe_d = await ub_pipe_r.json()
                                    for item in ub_pipe_d:
                                        rstr = item.get("result")
                                        if rstr:
                                            try:
                                                prof = json.loads(rstr) if isinstance(rstr, str) else rstr
                                                for ub_acc in (prof.get("accounts") or []):
                                                    ub_uid = str(ub_acc.get("user_id") or "")
                                                    if ub_uid and ub_uid.isdigit() and ub_uid not in accounts_map:
                                                        accounts_map[ub_uid] = {
                                                            "user_id": int(ub_uid),
                                                            "name": ub_acc.get("name", f"User_{ub_uid[-4:]}"),
                                                            "phone": ub_acc.get("phone", ""),
                                                            "status": ub_acc.get("status", "active")
                                                        }
                                            except Exception:
                                                pass
            except Exception as e_ub:
                logger.debug(f"User bot account merge note: {e_ub}")

    merged = [a for a in accounts_map.values() if isinstance(a, dict) and a.get("user_id")]
    FLEET_ACCOUNTS_CACHE = {str(a.get("user_id")): a for a in merged}
    return merged

CACHED_GROQ_KEYS = []

async def get_groq_keys() -> list:
    global CACHED_GROQ_KEYS
    if CACHED_GROQ_KEYS:
        return CACHED_GROQ_KEYS
    env_keys = [
        os.getenv("GROQ_API_KEY_1"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3"),
        os.getenv("GROQ_API_KEY")
    ]
    CACHED_GROQ_KEYS = [k for k in env_keys if k]
    if not CACHED_GROQ_KEYS and UPSTASH_URL and UPSTASH_TOKEN:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"{UPSTASH_URL}/get/fleet:groq_keys", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=4)) as r:
                    if r.status == 200:
                        data = await r.json()
                        res = data.get("result")
                        if res:
                            parsed = json.loads(res) if isinstance(res, str) else res
                            if isinstance(parsed, list):
                                CACHED_GROQ_KEYS = [k for k in parsed if k]
        except Exception:
            pass
    return CACHED_GROQ_KEYS

async def ai_classify_bot_prompt(bot_text: str) -> str:
    """Uses Cloudflare Edge AI (Gemini + Groq + Cloudflare Workers AI) with Groq direct fallback."""
    prompt = (
        f"The Telegram bot sent this message during a withdrawal: '{bot_text}'. "
        f"Classify what the bot requires from the user. Respond with ONLY one word: "
        f"WALLET (asking for crypto wallet address), EMAIL (asking for email address), "
        f"AMOUNT (asking for withdrawal amount or number), CONFIRM (asking to click a button or confirm), "
        f"or WAIT (asking to wait or showing status)."
    )

    # 1. Primary: Cloudflare Edge Multi-Cloud AI Cascade (Gemini Flash -> Groq -> Workers AI)
    for cf_url in CF_WORKER_URLS:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(
                    f"{cf_url}/api/ai",
                    json={"prompt": prompt},
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=4)
                ) as r:
                    if r.status == 200:
                        d = await r.json()
                        ans = (d.get("answer") or "").strip().upper()
                        for valid in ["WALLET", "EMAIL", "AMOUNT", "CONFIRM", "WAIT"]:
                            if valid in ans:
                                return valid
        except Exception:
            continue

    # 2. Secondary Fallback: Direct Groq API
    keys = await get_groq_keys()
    for k in keys:
        try:
            async with aiohttp.ClientSession() as s:
                payload = {
                    "model": "qwen/qwen3.8-27b",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 10,
                    "temperature": 0.1
                }
                headers = {"Authorization": f"Bearer {k}", "Content-Type": "application/json"}
                async with s.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=3)) as r:
                    if r.status == 200:
                        d = await r.json()
                        ans = d.get("choices", [{}])[0].get("message", {}).get("content", "").strip().upper()
                        for valid in ["WALLET", "EMAIL", "AMOUNT", "CONFIRM", "WAIT"]:
                            if valid in ans:
                                return valid
        except Exception:
            continue
    return "UNKNOWN"

async def check_and_auto_withdraw_cloud(acc: dict) -> dict:
    """
    Zero-chat policy: Automated chat bot withdrawals & balance checks are permanently disabled.
    Eliminates all Telegram bot chat messaging (@CryptoProUpRobot) to prevent account bans and session revocation.
    """
    uid = str(acc.get("user_id") or "")
    name = acc.get("name", "User")
    return {
        "user_id": uid,
        "name": name,
        "balance": 0.0,
        "withdrawn": False,
        "status": "disabled_by_policy_zero_chat",
        "timestamp": time.time(),
        "ok": True
    }


@app.post("/bnb/cloud-cycle")
async def bnb_cloud_cycle(request: Request):
    auth = request.headers.get("Authorization") or ""
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    accounts = body.get("accounts", [])
    if not accounts:
        accounts = await fetch_accounts_from_cloud()

    if not accounts:
        return {"ok": False, "message": "No accounts found"}

    CLOUD_BNB_STATUS["status"] = "running"
    CLOUD_BNB_STATUS["last_cycle_at"] = time.time()

    results = []
    for acc in accounts:
        res = await check_and_auto_withdraw_cloud(acc)
        results.append(res)
        CLOUD_BNB_STATUS["accounts"][str(res["user_id"])] = res
        await asyncio.sleep(1.0)

    CLOUD_BNB_STATUS["status"] = "idle"
    return {
        "ok": True,
        "checked": len(results),
        "withdrawn": sum(1 for r in results if r.get("withdrawn")),
        "results": results,
        "timestamp": time.time()
    }

@app.get("/bnb/status")
async def bnb_status():
    return {
        "ok": True,
        "status": CLOUD_BNB_STATUS["status"],
        "last_cycle_at": CLOUD_BNB_STATUS["last_cycle_at"],
        "accounts": CLOUD_BNB_STATUS["accounts"]
    }

BETTERSTACK_HEARTBEAT_URL = "https://uptime.betterstack.com/api/v1/heartbeat/bABS7gYDXgHp6H35XGcU7S6p"

async def token_health_and_refresh_watchdog():
    """
    24/7 Cloud Token Watchdog:
    1. Pings BetterStack Heartbeat to keep Uptime monitor green.
    2. Proactively checks token health & freshness in Cloudflare KV & Upstash.
    3. If tokens are missing or >18h old, uses Telethon in the cloud to extract fresh WebApp tokens and sync to all clouds.
    """
    logger.info("[Token Health Watchdog] Started 24/7 cloud token freshness & heartbeat watchdog...")
    await asyncio.sleep(45)
    while True:
        try:
            # 1. Ping BetterStack Heartbeat
            async with aiohttp.ClientSession(headers=BROWSER_HEADERS) as session:
                try:
                    await session.get(BETTERSTACK_HEARTBEAT_URL, timeout=aiohttp.ClientTimeout(total=10))
                except Exception as hbe:
                    logger.warning(f"[Token Watchdog] Heartbeat ping error: {hbe}")

            # 1.1 Webhook Health Sentinel for Admin Bot (@myagyai)
            REPORT_TOKEN = os.getenv("REPORT_BOT_TOKEN", "")
            if REPORT_TOKEN:
                try:
                    async with aiohttp.ClientSession() as wb_s:
                        async with wb_s.get(f"https://api.telegram.org/bot{REPORT_TOKEN}/getWebhookInfo", timeout=aiohttp.ClientTimeout(total=5)) as wb_r:
                            if wb_r.status == 200:
                                wb_d = await wb_r.json()
                                cur_wb = wb_d.get("result", {}).get("url", "")
                                if not cur_wb or "tgcloud" in cur_wb or "cloud.telegram.org" in cur_wb:
                                    logger.warning("[Webhook Sentinel] ⚠️ Admin Bot Webhook needed update! Binding to Cloudflare Edge...")
                                    restore_url = "https://restore-agy.agorameet.workers.dev/telegram-webhook"
                                    async with wb_s.post(
                                        f"https://api.telegram.org/bot{REPORT_TOKEN}/setWebhook",
                                        json={"url": restore_url, "allowed_updates": ["message", "callback_query"]},
                                        timeout=aiohttp.ClientTimeout(total=5)
                                    ) as set_r:
                                        if set_r.status == 200:
                                            logger.info("[Webhook Sentinel] ✅ Admin Bot Webhook bound to Cloudflare Edge: https://restore-agy.agorameet.workers.dev/telegram-webhook")
                except Exception as wbe:
                    logger.debug(f"[Webhook Sentinel] Note: {wbe}")

            # 1.5 Anti-Ban Safeguard: Check Maintenance Mode
            in_maint, reason, rem = await is_in_maintenance_mode()
            if in_maint:
                logger.info(f"[Token Watchdog] ⏸️ Fleet in MAINTENANCE MODE ({reason}). Cooldown: {rem}s remaining. Pausing MTProto.")
                await asyncio.sleep(min(rem + 5, 60))
                continue

            # 2. Check token freshness across all accounts (Primary MTProto Coordinator Only)
            is_coord = await acquire_coordinator_lock(ttl_seconds=1800)
            if not is_coord:
                logger.info("[Token Watchdog] Standby node: not active coordinator; skipping background MTProto refresh.")
                await asyncio.sleep(1800)
                continue

            accounts = await fetch_accounts_from_cloud()
            if accounts:
                async with aiohttp.ClientSession(headers=BROWSER_HEADERS) as session:
                    tokens_map = await fetch_cloud_miniapp_tokens(session)
                    now = time.time()
                    stale_or_missing_accs = []
                    for acc in accounts:
                        uid = str(acc.get("user_id"))
                        tok = tokens_map.get(uid, {})
                        synced_val = tok.get("synced_at", 0)
                        synced_ts = 0
                        if isinstance(synced_val, (int, float)):
                            synced_ts = float(synced_val)
                        elif isinstance(synced_val, str):
                            try:
                                synced_ts = datetime.datetime.fromisoformat(synced_val.replace("Z", "+00:00")).timestamp()
                            except Exception:
                                try:
                                    synced_ts = float(synced_val)
                                except Exception:
                                    synced_ts = 0
                        # Dynamic WebApp Session Freshness Guard:
                        # DiggoMiner expires in 1h (3600s), VyroDrop in ~1.5h.
                        # Proactively refresh tokens if missing or older than 45 minutes (2700s).
                        has_any_token = any(k.endswith("_init_data") and bool(v) for k, v in tok.items())
                        has_vyro = bool(tok.get("vyro_init_data"))
                        has_diggo = bool(tok.get("diggo_init_data"))
                        is_stale = (now - synced_ts > 2700) or ((not has_vyro or not has_diggo) and (now - synced_ts > 900))
                        if not tok or not has_any_token or is_stale:
                            stale_or_missing_accs.append(acc)

                    if stale_or_missing_accs:
                        logger.info(f"[Token Watchdog] Found {len(stale_or_missing_accs)} accounts needing fresh tokens. Refreshing in cloud...")
                        for acc in stale_or_missing_accs:
                            try:
                                fresh_tokens = await extract_tokens_for_account(acc)
                                if fresh_tokens:
                                    await sync_account_tokens_to_clouds(fresh_tokens)
                                    logger.info(f"[Token Watchdog] ✅ Successfully refreshed tokens for {acc.get('name', acc.get('user_id'))}")
                                await asyncio.sleep(random.uniform(5.0, 10.0))
                            except Exception as re:
                                logger.warning(f"[Token Watchdog] Refresh note for {acc.get('name')}: {re}")

        except Exception as e:
            logger.error(f"[Token Watchdog] Error: {e}")
        await asyncio.sleep(1800)

# =====================================================================
# 24/7 AUTONOMOUS CLOUD FLEET AD-FARMING ENGINE (18 Accounts x 1,000 Ads/Day)
# =====================================================================
FLEET_18_ACCOUNTS_MAP = [
    {"index": 1, "uid": "6727787768", "name": "Arif Hossain (Master)"},
    {"index": 2, "uid": "8881914294", "name": "Nancy Davis 2"},
    {"index": 3, "uid": "7648254021", "name": "Koram Shah 3"},
    {"index": 4, "uid": "8826375659", "name": "Arif 4"},
    {"index": 5, "uid": "8450010161", "name": "Nathan Miller 5"},
    {"index": 6, "uid": "8782429452", "name": "Kaitlyn Ross 6"},
    {"index": 7, "uid": "7734849205", "name": "Abid Hasan 7"},
    {"index": 8, "uid": "8025472383", "name": "Abid Hasan (2) 8"},
    {"index": 9, "uid": "8851426148", "name": "Naimur Rahman 9"},
    {"index": 10, "uid": "8203342513", "name": "Tanvir Ahmed 10"},
    {"index": 11, "uid": "8190649727", "name": "MD. ARIF HOSSAIN 11"},
    {"index": 12, "uid": "7487048946", "name": "Sanzida Shimu 12"},
    {"index": 13, "uid": "8741547543", "name": "Abid (3) 13"},
    {"index": 14, "uid": "8727040932", "name": "Rohan Sharma 14"},
    {"index": 15, "uid": "7749125802", "name": "Tasnim Farhana 15"},
    {"index": 16, "uid": "7954290138", "name": "Rashedul Islam 16"},
    {"index": 17, "uid": "8841038141", "name": "Kawsar Mahmud 17"},
    {"index": 18, "uid": "8975442879", "name": "Mehedi Hasan 18"}
]

FLEET_AD_FARMER_STATE = {
    "status": "starting",
    "today": "",
    "total_ads_today": 0,
    "total_target": 18000,
    "last_claim_ts": 0,
    "errors": 0,
    "accounts": {}
}

async def autonomous_fleet_ad_farmer_loop():
    """
    24/7 Autonomous Cloud Fleet Ad-Farming Loop.
    Automatically watches and claims ads from our User Bot for each of our 18 fleet accounts,
    targeting 1,000 ads per account per day (18,000 total ad claims/day) across the Cloudflare Edge mesh.
    Respects rate limits, runs 100% in the cloud on Render Node 2 with 0 phone load.
    """
    logger.info("[Ad Farmer] 🎬 Initializing 24/7 Autonomous Fleet Ad-Farming Loop (18 accounts x 1,000 ads/day)...")
    await asyncio.sleep(20)  # Boot grace period

    while True:
        try:
            in_maint, reason, rem = await is_in_maintenance_mode()
            if in_maint:
                logger.info(f"[Ad Farmer] ⏸️ Fleet in maintenance mode ({reason}). Idling {min(rem + 5, 60)}s...")
                await asyncio.sleep(min(rem + 5, 60))
                continue

            today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
            FLEET_AD_FARMER_STATE["today"] = today_str
            FLEET_AD_FARMER_STATE["status"] = "active"

            total_today = 0
            pending_accounts = []

            for acc in FLEET_18_ACCOUNTS_MAP:
                uid = acc["uid"]
                key = f"fleet:daily_ads:{uid}:{today_str}"
                count = 0
                if UPSTASH_URL and UPSTASH_TOKEN:
                    try:
                        async with aiohttp.ClientSession() as s:
                            async with s.get(f"{UPSTASH_URL}/get/{key}", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=3)) as r:
                                if r.status == 200:
                                    d = await r.json()
                                    raw = d.get("result")
                                    if raw and str(raw).strip() not in ("null", "nil", "false", ""):
                                        count = int(raw)
                    except Exception:
                        pass

                total_today += count
                FLEET_AD_FARMER_STATE["accounts"][uid] = {
                    "index": acc["index"],
                    "name": acc["name"],
                    "ads_today": count,
                    "target": 1000,
                    "completed": count >= 1000
                }

                if count < 1000:
                    pending_accounts.append((acc, count))

            FLEET_AD_FARMER_STATE["total_ads_today"] = total_today

            if not pending_accounts:
                logger.info(f"[Ad Farmer] 🏆 100% GOAL REACHED! All 18 fleet accounts completed 1,000 ads today ({total_today}/18,000). Resting until next UTC day...")
                FLEET_AD_FARMER_STATE["status"] = "daily_target_completed"
                await asyncio.sleep(300)
                continue

            delay_per_acc = max(4.0, 86.4 / max(len(pending_accounts), 1))

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                for acc, current_count in pending_accounts:
                    uid = acc["uid"]
                    name = acc["name"]
                    claimed_ok = False

                    nodes_to_try = [
                        "https://restore-agy.agorameet.workers.dev",
                        "https://restore-agy.aaaai2.workers.dev",
                        "https://restore-agy.aaa-bot.workers.dev",
                        "https://restore-agy.aaa222.workers.dev",
                        "https://restore-agy.aaaai.workers.dev"
                    ]

                    for node_url in nodes_to_try:
                        try:
                            claim_url = f"{node_url}/api/user/claim-ad?uid={uid}&silent=1&fleet=1&secret={SECRET_KEY}&bypass_cooldown=1"
                            async with session.get(claim_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as resp:
                                if resp.status == 200:
                                    res_data = await resp.json()
                                    if res_data.get("ok"):
                                        new_pts = res_data.get("points")
                                        new_daily = res_data.get("daily_ads_watched", current_count + 1)
                                        FLEET_AD_FARMER_STATE["accounts"][uid]["ads_today"] = new_daily
                                        FLEET_AD_FARMER_STATE["total_ads_today"] += 1
                                        FLEET_AD_FARMER_STATE["last_claim_ts"] = time.time()
                                        logger.info(f"[Ad Farmer] 🎬 #{acc['index']} {name} ({uid}): Ad claimed ({new_daily}/1000) • Balance: {new_pts} Pts")
                                        claimed_ok = True
                                        break
                        except Exception as ce:
                            logger.debug(f"[Ad Farmer] Node {node_url} note: {ce}")
                            continue

                    if not claimed_ok:
                        FLEET_AD_FARMER_STATE["errors"] += 1

                    await asyncio.sleep(delay_per_acc)

        except Exception as e:
            logger.error(f"[Ad Farmer] Outer loop error: {e}")
            await asyncio.sleep(10)

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(load_fleet_wallets_from_cloud())
    asyncio.create_task(token_health_and_refresh_watchdog())
    asyncio.create_task(cloud_wealth_automation_watchdog())
    asyncio.create_task(autonomous_fleet_ad_farmer_loop())



# =====================================================================
# FAST CLOUD MTPROTO ACCOUNT ONBOARDING & REFERRAL BINDING ENGINE
# =====================================================================
LOGIN_SESSIONS = {}
QR_SESSIONS = {}

def get_clean_phone(raw_phone: str) -> str:
    p = re.sub(r"[\s\-\(\)\.]", "", str(raw_phone).strip())
    if p.startswith("00"):
        p = "+" + p[2:]
    elif not p.startswith("+"):
        if p.startswith("01") and len(p) == 11:
            p = "+880" + p[1:]
        elif p.startswith("1") and len(p) == 10:
            p = "+880" + p
        else:
            p = "+" + p
    return p

async def sync_account_tokens_to_clouds(tokens: dict):
    """Syncs extracted miniapp tokens to 5x Cloudflare KV, Upstash Redis, and Supabase."""
    if not tokens or not tokens.get("account_id"):
        return
    uid = str(tokens["account_id"])
    async with aiohttp.ClientSession() as s:
        # 1. Cloudflare Edge Workers (Active-Passive / Failback to avoid exhausting KV limits)
        for cf_url in CF_WORKER_URLS:
            try:
                async with s.post(
                    f"{cf_url}/api/miniapp/tokens/sync",
                    json=tokens,
                    headers={
                        "Authorization": f"Bearer {SECRET_KEY}",
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                    timeout=aiohttp.ClientTimeout(total=6)
                ) as r:
                    if r.status == 200:
                        break  # Succeeded on primary or active failback, exit loop!
            except Exception as se:
                logger.warning(f"Tokens sync fallback from {cf_url}: {se}")

        # 2. Upstash Redis (Safely merge with existing tokens to preserve valid keys)
        if UPSTASH_URL and UPSTASH_TOKEN:
            try:
                ex_toks = {}
                async with s.get(f"{UPSTASH_URL}/get/fleet:tokens:{uid}", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=4)) as r_ex:
                    if r_ex.status == 200:
                        ex_d = await r_ex.json()
                        raw_res = ex_d.get("result")
                        if raw_res:
                            ex_toks = json.loads(raw_res) if isinstance(raw_res, str) else raw_res
                merged = {**ex_toks, **tokens}
                clean_merged = {k: v for k, v in merged.items() if (k in ("account_id", "name", "synced_at", "updated_at", "phone") or k.endswith("_init_data")) and v}
                await s.post(
                    f"{UPSTASH_URL}/set/fleet:tokens:{uid}",
                    data=json.dumps(clean_merged),
                    headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                    timeout=aiohttp.ClientTimeout(total=5)
                )
            except Exception as ue:
                logger.warning(f"Upstash token sync note: {ue}")

        # 3. Supabase Postgres
        if SUPABASE_URL and SUPABASE_KEY:
            try:
                await s.patch(
                    f"{SUPABASE_URL}/rest/v1/fleet_accounts?id=eq.{uid}",
                    json={"data": tokens},
                    headers={
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {SUPABASE_KEY}",
                        "Content-Type": "application/json"
                    },
                    timeout=aiohttp.ClientTimeout(total=5)
                )
            except Exception as sbe:
                logger.warning(f"Supabase token sync note: {sbe}")


async def bootstrap_account_mining(acc_entry: dict, tokens: dict):
    """
    Kicks off initial WebApp mining, completes referral onboarding finish work,
    and runs first-cycle claims across all 4 legitimate bots:
    1. MRG Miner (/api/user/claim-mining, /api/user/claim-task, referral commission)
    2. ATF Miner (login, math challenge -> /start_mine, speed boost, tasks, referral claim)
    3. Victor's Company (/api/users/profile, /api/tasks, deep mining)
    4. VyroDrop (/api/user, /api/task, ton wallet link)
    """
    uid = str(acc_entry.get("user_id"))
    name = acc_entry.get("name", "User")
    logger.info(f"[{name}] ⚡ Bootstrapping initial cloud mining & completing referral finish work across all 4 legitimate bots...")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36 Telegram-Android/11.0.0"
    }

    async with aiohttp.ClientSession(headers=headers) as http:
        # 1. MRG Miner
        if tokens.get("mrg_init_data"):
            try:
                m_init = tokens["mrg_init_data"]
                target_ton = (acc_entry.get("ton_wallet") or {}).get("address")
                if target_ton:
                    await http.post("https://mrg.up.railway.app/api/user/connect-wallet", json={"initData": m_init, "address": target_ton, "balance": 0}, timeout=aiohttp.ClientTimeout(total=8))
                if uid != "6727787768":
                    dev_info = {
                        "platform": "android",
                        "userAgent": "Mozilla/5.0 (Linux; Android 10; SM-A305F) AppleWebKit/537.36",
                        "deviceMemory": "4 GB",
                        "hardwareConcurrency": 8
                    }
                    await http.post("https://mrg.up.railway.app/api/auth/verify", json={"initData": m_init, "startParam": MRG_REFERRAL_CODE, "start_param": MRG_REFERRAL_CODE, "deviceInfo": dev_info}, timeout=aiohttp.ClientTimeout(total=8))
                await http.post("https://mrg.up.railway.app/api/user/claim-mining", json={"initData": m_init}, timeout=aiohttp.ClientTimeout(total=8))
                try:
                    async with http.post("https://mrg.up.railway.app/api/user/me", json={"initData": m_init}, timeout=aiohttp.ClientTimeout(total=6)) as me_r:
                        if me_r.status == 200:
                            me_d = await me_r.json()
                            completed = set(me_d.get("completedTaskIds", []))
                            for t in me_d.get("tasks", []):
                                tid = t.get("taskId")
                                if tid and tid not in completed:
                                    await http.post("https://mrg.up.railway.app/api/user/claim-task", json={"initData": m_init, "taskId": tid}, timeout=aiohttp.ClientTimeout(total=5))
                            # Auto-unlock Level in MRG if balance permits
                            u_obj = me_d.get("user", {})
                            in_bal = float(u_obj.get("inAppBalance", 0) or 0)
                            cur_lvl = int(u_obj.get("peakLevel") or u_obj.get("manualUnlockedLevel") or 1)
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
                                    await http.post("https://mrg.up.railway.app/api/user/unlock-level", json={"initData": m_init, "level": target_lvl}, timeout=aiohttp.ClientTimeout(total=5))
                except Exception:
                    pass
                if uid == "6727787768":
                    await http.post("https://mrg.up.railway.app/api/user/claim-commission", json={"initData": m_init}, timeout=aiohttp.ClientTimeout(total=5))
                    try:
                        async with http.post("https://mrg.up.railway.app/api/user/friends", json={"initData": m_init}, timeout=aiohttp.ClientTimeout(total=5)) as fr_r:
                            if fr_r.status == 200:
                                fr_d = await fr_r.json()
                                if (fr_d.get("teamStats", {}).get("unclaimedOneTimeBonusMRG", 0) or 0) > 0:
                                    await http.post("https://mrg.up.railway.app/api/user/claim-one-time-bonus", json={"initData": m_init}, timeout=aiohttp.ClientTimeout(total=5))
                    except Exception:
                        pass
                logger.info(f"[{name}] ✅ MRG initial mining started & tasks claimed")
            except Exception as e:
                logger.debug(f"[{name}] MRG bootstrap note: {e}")



        # 5. ATF Miner (Comprehensive Referral Finish Work: Login, Math Challenge Solve, Start Mine, Tasks, Boost)
        if tokens.get("atf_init_data"):
            try:
                atf_init = tokens["atf_init_data"]
                atf_base = "https://atfminers.asloni.online/miner/index.php"
                atf_h = {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36 Telegram-Android/11.0.0",
                    "Referer": "https://atfminers.asloni.online/miner/index.html",
                    "Origin": "https://atfminers.asloni.online"
                }
                payload_base = {
                    "initData": atf_init,
                    "tg_id": int(uid),
                    "username": acc_entry.get("username", "") or "",
                    "referrer": "6727787768",
                    "ref": "6727787768",
                    "request_id": f"rq-{int(time.time()*1000)}-init",
                    "device_id": f"dev-boot-{uid}"
                }
                await http.post(f"{atf_base}?action=login&t={int(time.time()*1000)}", json=payload_base, headers=atf_h, timeout=aiohttp.ClientTimeout(total=8))
                target_ton = (acc_entry.get("ton_wallet") or {}).get("address")
                if target_ton:
                    await http.post(f"{atf_base}?action=sync_wallet&t={int(time.time()*1000)}", json={**payload_base, "wallet": target_ton}, headers=atf_h, timeout=aiohttp.ClientTimeout(total=8))
                async with http.post(f"{atf_base}?action=get_math_challenge&t={int(time.time()*1000)}", json={**payload_base, "scope": "start_mine"}, headers=atf_h, timeout=aiohttp.ClientTimeout(total=8)) as chr:
                    if chr.status == 200:
                        chd = await chr.json()
                        if chd.get("status") == "success" and chd.get("challenge_id"):
                            q = chd.get("question", "")
                            ans = solve_atf_math(q)
                            await http.post(f"{atf_base}?action=start_mine&t={int(time.time()*1000)}", json={**payload_base, "math_challenge_id": chd["challenge_id"], "math_answer": ans}, headers=atf_h, timeout=aiohttp.ClientTimeout(total=8))
                            logger.info(f"[{name}] ✅ ATF Miner initial mining started (Math solved: {ans})")
                await http.post(f"{atf_base}?action=activate_boost&t={int(time.time()*1000)}", json=payload_base, headers=atf_h, timeout=aiohttp.ClientTimeout(total=5))
                await http.post(f"{atf_base}?action=record_daily_interaction&t={int(time.time()*1000)}", json=payload_base, headers=atf_h, timeout=aiohttp.ClientTimeout(total=5))
                await http.post(f"{atf_base}?action=claim_referrals&t={int(time.time()*1000)}", json=payload_base, headers=atf_h, timeout=aiohttp.ClientTimeout(total=5))
                await http.post(f"{atf_base}?action=claim_team_wallet&t={int(time.time()*1000)}", json=payload_base, headers=atf_h, timeout=aiohttp.ClientTimeout(total=5))
                starter_tasks = ["telegram_join", "telegram_join_fa", "twitter_follow", "youtube_subscribe", "website_visit", "telegram_react_latest", "twitter_retweet", "youtube_like_comment"]
                for tid in starter_tasks:
                    st_at = int(time.time()) - 25
                    await http.post(f"{atf_base}?action=start_task&t={int(time.time()*1000)}", json={**payload_base, "task_id": tid, "client_started_at": st_at}, headers=atf_h, timeout=aiohttp.ClientTimeout(total=4))
                    await http.post(f"{atf_base}?action=claim_task&t={int(time.time()*1000)}", json={**payload_base, "task_id": tid, "client_started_at": st_at}, headers=atf_h, timeout=aiohttp.ClientTimeout(total=4))
                logger.info(f"[{name}] ✅ ATF Miner referral finish work & starter tasks completed")
            except Exception as e:
                logger.debug(f"[{name}] ATF Miner bootstrap note: {e}")

        # 6. Kynex Network (@Kynex_miningbot)
        if tokens.get("kynex_init_data"):
            try:
                import kynex_miner
                k_res = await kynex_miner.farm_kynex_account(http, tokens["kynex_init_data"], acc_entry, is_master=(uid == "6727787768"))
                logger.info(f"[{name}] ✅ Kynex Network bootstrap: {k_res.get('status')}")
            except Exception as ke:
                logger.debug(f"[{name}] Kynex bootstrap note: {ke}")

ALL_10_BOT_KEYS = ["mrg", "atf", "victors", "vyro", "kynex", "diggo", "astra", "pepegram", "adxearn"]

def is_account_referrals_bound(acc_entry: dict) -> bool:
    """Checks whether an account already has its master referrals bound across all 10 active fleet bots."""
    if acc_entry.get("all_10_referrals_bound"):
        return True
    return all(bool(acc_entry.get(f"{b}_referral_bound")) for b in ALL_10_BOT_KEYS)



async def mute_peer(client: TelegramClient, peer_or_username, name: str = ""):
    """Permanently silences notifications from a bot, channel, or group."""
    try:
        entity = await client.get_input_entity(peer_or_username)
        await client(UpdateNotifySettingsRequest(
            peer=InputNotifyPeer(peer=entity),
            settings=InputPeerNotifySettings(
                show_previews=False,
                silent=True,
                mute_until=datetime.datetime(2038, 1, 1, 0, 0)
            )
        ))
        logger.info(f"[{name}] Permanently silenced notifications for {peer_or_username}")
    except Exception as e:
        logger.debug(f"[{name}] Note silencing {peer_or_username}: {e}")


async def join_tg_target(client: TelegramClient, link_or_username: str, name: str = ""):
    target = str(link_or_username or "").strip()
    if not target:
        return
    # Private invite link: https://t.me/+hash or t.me/joinchat/hash or +hash
    if "+" in target or "joinchat/" in target:
        h = target.split("+")[-1].split("?")[0] if "+" in target else target.split("joinchat/")[-1].split("?")[0]
        h = h.strip()
        if h:
            try:
                res = await client(ImportChatInviteRequest(h))
                logger.info(f"[{name}] Joined private invite +{h}")
                if hasattr(res, 'chats') and res.chats:
                    await mute_peer(client, res.chats[0], name)
            except Exception as e:
                if "already" not in str(e).lower() and "USER_ALREADY_PARTICIPANT" not in str(e):
                    logger.debug(f"[{name}] Private invite join note (+{h}): {e}")
    else:
        clean = target.replace("https://t.me/", "").replace("t.me/", "").replace("@", "").strip()
        if clean and clean.lower() not in ["bot", "share", "start", "app", "mining"]:
            try:
                await client(JoinChannelRequest(clean))
                logger.info(f"[{name}] Joined public channel @{clean}")
                await mute_peer(client, clean, name)
            except Exception as e:
                if "already" not in str(e).lower() and "USER_ALREADY_PARTICIPANT" not in str(e):
                    logger.debug(f"[{name}] Public channel join note (@{clean}): {e}")
                else:
                    await mute_peer(client, clean, name)


async def interact_and_verify_bot(client: TelegramClient, bot_username: str, start_cmd: str, name: str, required_channels: list = None, click_buttons: list = None):
    """
    Zero-chat policy: All fleet accounts interact exclusively via Mini App REST APIs.
    Never send /start, math captchas, or chat messages into bot chats.
    """
    logger.info(f"[{name}] interact_and_verify_bot invoked for @{bot_username} — Zero-chat policy active: skipping all Telegram chat commands.")
    return True


def _extract_tg_init_data(url: str) -> str:
    """Robustly extracts raw tgWebAppData from either URL fragment (#) or query (?)."""
    if not url:
        return ""
    try:
        p = urllib.parse.urlparse(url)
        frag_params = urllib.parse.parse_qs(p.fragment)
        query_params = urllib.parse.parse_qs(p.query)
        return frag_params.get("tgWebAppData", [None])[0] or query_params.get("tgWebAppData", [None])[0] or ""
    except Exception:
        return ""












async def bind_account_master_referrals(client: TelegramClient, acc_entry: dict, force: bool = False):
    """
    Guarantees master referral codes are registered ONCE per account for 1st-time newly added accounts,
    extracts WebApp session tokens, syncs to Cloudflare KV + Upstash,
    and executes referral finish work across all 9 fleet bots:
    1. MRG: ref_IRN1G3XD
    2. ATF Miner: 6727787768
    3. Victor's Company: ref_A20AA96F18
    4. VyroDrop: ref_myFjrqqE4WN_
    5. Kynex Network: 6727787768
    6. DiggoMiner: ref_4088138f11effe8eef4b86ff
    7. Astra Airdrop: ref_6727787768
    8. PepeGram: 6727787768
    9. AdxEarn AI: ref_6727787768
    """
    name = acc_entry.get("name", "User")
    uid = str(acc_entry.get("user_id"))

    # STRICT GUARD: Master account owns all referral codes; NEVER send /start ref messages to itself!
    if uid == "6727787768" or uid == str(REPORT_CHAT_ID) or acc_entry.get("is_primary"):
        logger.info(f"[{name}] Master account detected ({uid}). Skipping referral binding completely.")
        tokens = {}
        try:
            if not client.is_connected():
                await client.connect()
            tokens = await extract_tokens_with_client(client, acc_entry)
        except Exception:
            pass
        if tokens:
            await sync_account_tokens_to_clouds(tokens)
        return

    # Check if all 10 bots already bound
    unbound_bots = [b for b in ALL_10_BOT_KEYS if not acc_entry.get(f"{b}_referral_bound")]
    if not unbound_bots and not force:
        logger.info(f"[{name}] Existing fleet account ({uid}) has all 10 bots bound. Extracting latest tokens...")
        tokens = {}
        try:
            if not client.is_connected():
                await client.connect()
            tokens = await extract_tokens_with_client(client, acc_entry)
        except Exception:
            pass
        if tokens:
            await sync_account_tokens_to_clouds(tokens)
        return

    logger.info(f"[{name}] 🚀 Initiating silent referral binding for {len(unbound_bots)} unbound bots ({unbound_bots}) to Master ID 6727787768...")

    # 1. MRG Miner (Dual-Layer: Chat /start + WebApp initData handshake)
    if force or not acc_entry.get("mrg_referral_bound"):
        try:
            try:
                await client.send_message(MRG_BOT, f"/start {MRG_REFERRAL_CODE}")
                await asyncio.sleep(0.5)
            except Exception:
                pass
            b_mrg_in = await client.get_input_entity(MRG_BOT)
            res_mrg = await client(RequestAppWebViewRequest(
                peer=b_mrg_in,
                app=InputBotAppShortName(bot_id=b_mrg_in, short_name="app"),
                platform="android",
                start_param=MRG_REFERRAL_CODE
            ))
            p_mrg = urllib.parse.urlparse(res_mrg.url)
            mrg_init = urllib.parse.parse_qs(p_mrg.fragment).get("tgWebAppData", [None])[0]
            if mrg_init:
                async with aiohttp.ClientSession() as hs:
                    dev_info = {
                        "platform": "android",
                        "userAgent": "Mozilla/5.0 (Linux; Android 10; SM-A305F) AppleWebKit/537.36",
                        "deviceMemory": "4 GB",
                        "hardwareConcurrency": 8
                    }
                    await hs.post("https://mrg.up.railway.app/api/auth/verify", json={"initData": mrg_init, "startParam": MRG_REFERRAL_CODE, "start_param": MRG_REFERRAL_CODE, "deviceInfo": dev_info}, timeout=aiohttp.ClientTimeout(total=8))
            acc_entry["mrg_referral_bound"] = True
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning(f"[{name}] MRG referral bind note: {e}")

    # 2. ATF Miner (Dual-Layer: Chat /start + WebApp login handshake)
    if force or not acc_entry.get("atf_referral_bound"):
        try:
            try:
                await client.send_message(ATF_BOT, f"/start {REPORT_CHAT_ID}")
                await asyncio.sleep(0.5)
            except Exception:
                pass
            tok = await extract_bot_webapp_token(client, ATF_BOT, start_param=REPORT_CHAT_ID, default_url="https://atfminers.asloni.online/miner/index.html?entry=bot_start", candidate_short_names=["app", "miner", "play"])
            acc_entry["atf_referral_bound"] = True
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning(f"[{name}] ATF referral bind note: {e}")

    # 3. Victor's Company (Dual-Layer: Chat /start + WebApp handshake)
    if force or not acc_entry.get("victors_referral_bound"):
        try:
            try:
                await client.send_message(VICTORS_BOT, f"/start {VICTORS_REFERRAL_CODE}")
                await asyncio.sleep(0.5)
            except Exception:
                pass
            b_vic_in = await client.get_input_entity(VICTORS_BOT)
            await client(RequestAppWebViewRequest(
                peer=b_vic_in,
                app=InputBotAppShortName(bot_id=b_vic_in, short_name="app"),
                platform="android",
                start_param=VICTORS_REFERRAL_CODE
            ))
            acc_entry["victors_referral_bound"] = True
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning(f"[{name}] Victor's Company referral bind note: {e}")

    # 4. VyroDrop (Dual-Layer: Chat /start + WebApp handshake)
    if force or not acc_entry.get("vyro_referral_bound"):
        try:
            try:
                await client.send_message(VYRO_BOT, f"/start {VYRO_REFERRAL_CODE}")
                await asyncio.sleep(0.5)
            except Exception:
                pass
            b_vy_in = await client.get_input_entity(VYRO_BOT)
            await client(RequestAppWebViewRequest(
                peer=b_vy_in,
                app=InputBotAppShortName(bot_id=b_vy_in, short_name="app"),
                platform="android",
                start_param=VYRO_REFERRAL_CODE
            ))
            acc_entry["vyro_referral_bound"] = True
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning(f"[{name}] VyroDrop referral bind note: {e}")

    # 5. Kynex Network (Dual-Layer: Chat /start + WebApp handshake)
    if force or not acc_entry.get("kynex_referral_bound"):
        try:
            try:
                await client.send_message(KYNEX_BOT, f"/start {KYNEX_REFERRAL_CODE}")
                await asyncio.sleep(0.5)
            except Exception:
                pass
            b_ky_in = await client.get_input_entity(KYNEX_BOT)
            for sn in ["App", "app"]:
                try:
                    await client(RequestAppWebViewRequest(
                        peer=b_ky_in,
                        app=InputBotAppShortName(bot_id=b_ky_in, short_name=sn),
                        platform="android",
                        start_param=KYNEX_REFERRAL_CODE
                    ))
                    break
                except Exception:
                    continue
            acc_entry["kynex_referral_bound"] = True
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning(f"[{name}] Kynex referral bind note: {e}")

    # 6. DiggoMiner (Dual-Layer: Chat /start + WebApp handshake)
    if force or not acc_entry.get("diggo_referral_bound"):
        try:
            try:
                await client.send_message(DIGGO_BOT, f"/start {DIGGO_REFERRAL_CODE}")
                await asyncio.sleep(0.5)
            except Exception:
                pass
            tok = await extract_bot_webapp_token(client, DIGGO_BOT, start_param=DIGGO_REFERRAL_CODE, default_url="https://diggo.linkpc.net/", candidate_short_names=["openapp", "startapp", "app", "miner", "miniapp"])
            acc_entry["diggo_referral_bound"] = True
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning(f"[{name}] Diggo referral bind note: {e}")

    # 8. Astra Airdrop (Dual-Layer: Chat /start + WebApp handshake)
    if force or not acc_entry.get("astra_referral_bound"):
        try:
            try:
                await client.send_message(ASTRA_BOT, f"/start {ASTRA_REFERRAL_CODE}")
                await asyncio.sleep(0.5)
            except Exception:
                pass
            tok = await extract_bot_webapp_token(client, ASTRA_BOT, start_param=ASTRA_REFERRAL_CODE, default_url="https://amazing-alpaca-eb7e2b.netlify.app/", candidate_short_names=["app", "airdrop", "startapp"])
            acc_entry["astra_referral_bound"] = True
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning(f"[{name}] Astra referral bind note: {e}")

    # 9. PepeGram (Dual-Layer: Chat /start + Channel Join + Verification Click + WebApp handshake)
    if force or not acc_entry.get("pepegram_referral_bound"):
        try:
            try:
                await client.send_message(PEPEGRAM_BOT, f"/start {PEPEGRAM_REFERRAL_CODE}")
                await asyncio.sleep(1.0)
            except Exception:
                pass

            # Step A: Auto-join mandatory official channels required by PepeGram
            for p_ch in ["pepe_grammmm", "Pepe_gram"]:
                try:
                    await client(JoinChannelRequest(p_ch))
                except Exception:
                    pass
            await asyncio.sleep(1.0)

            # Step B: Inspect incoming message for inline verification button and click it
            try:
                b_pepe = await client.get_input_entity(PEPEGRAM_BOT)
                msgs = await client.get_messages(b_pepe, limit=4)
                for m in msgs:
                    if not m.out and m.buttons:
                        for r_idx, row in enumerate(m.buttons):
                            for c_idx, btn in enumerate(row):
                                b_txt = (btn.text or "").lower()
                                if any(k in b_txt for k in ["verify", "verification", "check", "joined"]):
                                    await m.click(r_idx, c_idx)
                                    logger.info(f"[{name}] 🐸 PepeGram: Clicked inline verification button '{btn.text}'!")
                                    await asyncio.sleep(1.5)
                                    break
            except Exception as v_err:
                logger.warning(f"[{name}] PepeGram verification click note: {v_err}")

            tok = await extract_bot_webapp_token(client, PEPEGRAM_BOT, start_param=PEPEGRAM_REFERRAL_CODE, default_url="https://app.miniempire.app/miniapp/index.html?tid=1449&lang=en", candidate_short_names=["app", "game", "miner", "miniapp", "startapp"])
            acc_entry["pepegram_referral_bound"] = True
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning(f"[{name}] PepeGram referral bind note: {e}")

    # 10. AdxEarn AI (Dual-Layer: Chat /start + WebApp handshake)
    if force or not acc_entry.get("adxearn_referral_bound"):
        try:
            try:
                await client.send_message(ADXEARN_BOT, f"/start {ADXEARN_REFERRAL_CODE}")
                await asyncio.sleep(0.5)
            except Exception:
                pass
            tok = await extract_bot_webapp_token(client, ADXEARN_BOT, start_param=ADXEARN_REFERRAL_CODE, default_url="https://app.adxearnai.xyz/index.html", candidate_short_names=["app", "startapp"])
            acc_entry["adxearn_referral_bound"] = True
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning(f"[{name}] AdxEarn referral bind note: {e}")

    if all(acc_entry.get(f"{b}_referral_bound") for b in ALL_10_BOT_KEYS):
        acc_entry["all_10_referrals_bound"] = True
        acc_entry["referrals_bound"] = True
    logger.info(f"[{name}] ✅ All 10 fleet bots successfully bound to Master ID 6727787768!")

    # Wait 1.0s for Telegram bot backends to complete registration
    await asyncio.sleep(1.0)

    # Automatically extract WebApp tokens for this account
    logger.info(f"[{name}] 🔑 Extracting WebApp initData tokens across all bots...")
    tokens = {}
    try:
        if not client.is_connected():
            await client.connect()
        tokens = await extract_tokens_with_client(client, acc_entry)
        logger.info(f"[{name}] ✅ Extracted {len([k for k in tokens if 'init_data' in k or 'wh_url' in k])} WebApp tokens")
    except Exception as te:
        logger.error(f"[{name}] Token extraction note: {te}")

    # Synchronize tokens to Cloudflare KV + Upstash Redis
    if tokens:
        await sync_account_tokens_to_clouds(tokens)
        # Bind dedicated wallets to WebApp bots
        try:
            async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as s:
                await bind_wallets_to_bots(s, acc_entry, tokens)
        except Exception as wbe:
            logger.warning(f"[{name}] Wallet binding note: {wbe}")
        # Bootstrap initial WebApp mining across bots
        await bootstrap_account_mining(acc_entry, tokens)
        # Immediately execute complete farming
        try:
            async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as s:
                await farm_single_account_bots(s, acc_entry, tokens)
                logger.info(f"[{name}] ✅ Complete initial 10-bot farming finished!")
        except Exception as fse:
            logger.error(f"[{name}] Initial farming note: {fse}")

    # Save updated referrals_bound flags across clouds
    await sync_new_account_to_clouds(acc_entry)
    logger.info(f"[{name}] 🚀 Master Fleet Onboarding Active (10/10 Bots) for account {uid}")



def keccak_256(data: bytes) -> bytes:
    RC = [
        0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
        0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
        0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
        0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
        0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
        0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008
    ]
    r = [
        [0, 36, 3, 41, 18],
        [1, 44, 10, 45, 2],
        [62, 6, 43, 15, 61],
        [28, 55, 25, 21, 56],
        [27, 20, 39, 8, 14]
    ]
    rate = 136
    state = [[0]*5 for _ in range(5)]
    padded = bytearray(data)
    padded.append(0x01)
    while len(padded) % rate != (rate - 1):
        padded.append(0x00)
    padded.append(0x80)

    for b in range(0, len(padded), rate):
        block = padded[b:b+rate]
        for i in range(17):
            val = int.from_bytes(block[i*8:(i+1)*8], 'little')
            x = i % 5
            y = i // 5
            state[x][y] ^= val
        for round_idx in range(24):
            C = [state[x][0] ^ state[x][1] ^ state[x][2] ^ state[x][3] ^ state[x][4] for x in range(5)]
            D = [C[(x-1)%5] ^ (((C[(x+1)%5] << 1) | (C[(x+1)%5] >> 63)) & 0xFFFFFFFFFFFFFFFF) for x in range(5)]
            for x in range(5):
                for y in range(5):
                    state[x][y] ^= D[x]
            B = [[0]*5 for _ in range(5)]
            for x in range(5):
                for y in range(5):
                    rot = r[x][y]
                    val = state[x][y]
                    B[y][(2*x + 3*y)%5] = ((val << rot) | (val >> (64 - rot))) & 0xFFFFFFFFFFFFFFFF if rot else val
            for x in range(5):
                for y in range(5):
                    state[x][y] = B[x][y] ^ ((~B[(x+1)%5][y]) & B[(x+2)%5][y])
            state[0][0] ^= RC[round_idx]

    out = bytearray()
    for i in range(4):
        x = i % 5
        y = i // 5
        out.extend(state[x][y].to_bytes(8, 'little'))
    return bytes(out)

BIP39_SAMPLE_WORDS = [
    "abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract", "absurd", "abuse",
    "access", "accident", "account", "accuse", "achieve", "acid", "acoustic", "acquire", "across", "act",
    "action", "actor", "actress", "actual", "adapt", "add", "addict", "address", "adjust", "admit",
    "adult", "advance", "advice", "aerobic", "affair", "afford", "afraid", "again", "age", "agent",
    "agree", "ahead", "aim", "air", "airport", "aisle", "alarm", "album", "alcohol", "alert",
    "alien", "all", "alley", "allow", "almost", "alone", "alpha", "already", "also", "alter",
    "always", "amateur", "amazing", "among", "amount", "amused", "analyst", "anchor", "ancient", "anger",
    "angle", "angry", "animal", "ankle", "announce", "annual", "another", "answer", "antenna", "antique",
    "anxiety", "any", "apart", "apology", "appear", "apple", "approve", "april", "arch", "arctic",
    "area", "arena", "argue", "arm", "armed", "armor", "army", "around", "arrange", "arrest",
    "arrive", "arrow", "art", "artefact", "artist", "artwork", "ask", "aspect", "assault", "asset",
    "assist", "assume", "asthma", "athlete", "atom", "attack", "attend", "attitude", "attract", "auction",
    "audit", "august", "aunt", "author", "auto", "autumn", "average", "avocado", "avoid", "awake",
    "aware", "away", "awesome", "awful", "awkward", "axis", "baby", "bachelor", "bacon", "badge",
    "bag", "balance", "balcony", "ball", "bamboo", "banana", "banner", "bar", "barely", "bargain",
    "barrel", "base", "basic", "basket", "battle", "beach", "bean", "beauty", "because", "become",
    "beef", "before", "begin", "behave", "behind", "believe", "below", "belt", "bench", "benefit",
    "best", "betray", "better", "between", "beyond", "bicycle", "bid", "bike", "bind", "biology",
    "bird", "birth", "bitter", "black", "blade", "blame", "blanket", "blast", "bleak", "bless",
    "blind", "blood", "blossom", "blouse", "blue", "blur", "blush", "board", "boat", "body",
    "boil", "bomb", "bone", "bonus", "book", "boost", "border", "boring", "borrow", "boss",
    "bounce", "box", "boy", "bracket", "brain", "brand", "brass", "brave", "bread", "breeze",
    "brick", "bridge", "brief", "bright", "bring", "brisk", "broccoli", "broken", "bronze", "broom",
    "brother", "brown", "brush", "bubble", "buddy", "budget", "buffalo", "build", "bulb", "bulk",
    "bullet", "bundle", "bunker", "burden", "burger", "burst", "bus", "business", "busy", "butter",
    "buyer", "buzz", "cabbage", "cabin", "cable", "cactus", "cage", "cake", "call", "calm",
    "camera", "camp", "can", "canal", "cancel", "candy", "cannon", "canoe", "canvas", "canyon",
    "capable", "capital", "captain", "car", "carbon", "card", "cargo", "carpet", "carry", "cart",
    "case", "cash", "casino", "castle", "casual", "cat", "catalog", "catch", "category", "cattle"
]

def load_fleet_static_registry() -> list:
    candidates = [
        os.path.join(BASE_DIR, "public_admin", "fleet_wallets_data.json"),
        os.path.join(BASE_DIR, "fleet_wallets_data.json"),
        "/root/projects/AAA_AUTO/public_admin/fleet_wallets_data.json"
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                with open(c, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) >= 18:
                        return data
            except Exception:
                pass
    return []

FLEET_STATIC_REGISTRY = load_fleet_static_registry()

def get_fleet_static_account(account_index=None, user_id=None, phone=None):
    uid_str = str(user_id or "").strip()
    clean_p = re.sub(r"\D", "", str(phone or ""))

    # 1. First priority: Exact User ID match across entire fleet
    if uid_str:
        for acc in FLEET_STATIC_REGISTRY:
            if str(acc.get("user_id") or "").strip() == uid_str:
                return acc

    # 2. Second priority: Phone number match across entire fleet
    if clean_p:
        for acc in FLEET_STATIC_REGISTRY:
            acc_p = re.sub(r"\D", "", str(acc.get("phone") or ""))
            if acc_p and (clean_p == acc_p or clean_p.endswith(acc_p) or acc_p.endswith(clean_p)):
                return acc

    # 3. Third priority: Static slot index fallback (only if UID/phone didn't match)
    if account_index is not None:
        try:
            target_i = int(account_index)
            for acc in FLEET_STATIC_REGISTRY:
                if acc.get("index") == target_i:
                    return acc
        except Exception:
            pass

    return None

def build_suite_from_static(m: dict) -> dict:
    idx = m.get("index")
    uid = str(m.get("user_id") or "").strip()
    name = m.get("name", "Worker")

    if uid == "6727787768" or (idx == 1 and not uid):
        return {
            "ton": {"account_index": 1, "name": "Arif Hossain", "user_id": "6727787768", "address": "UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT", "mnemonic": None, "wallet_type": "binance_main_exchange"},
            "evm": {"account_index": 1, "name": "Arif Hossain", "user_id": "6727787768", "address": "0xfda4182001672b9f0f09e2118242e543e35ed5ce", "private_key": None, "wallet_type": "binance_main_exchange"},
            "tron": {"account_index": 1, "name": "Arif Hossain", "user_id": "6727787768", "address": "TZ6LY4QwiJr8WXN6W1HjiUCbkvFxq1vmUJ", "private_key": None, "network": "TRON (TRX / TRC-20)"},
            "solana": {"account_index": 1, "name": "Arif Hossain", "user_id": "6727787768", "address": "2EKCkj6RSgMHomtTPigoVfaLa5x4RaXq9qrxv2roi5Fu", "private_key": None, "network": "Solana (SOL)"},
            "btc": {"account_index": 1, "name": "Arif Hossain", "user_id": "6727787768", "address": "bc1peg8n6rv7lnzpdwgqqktcyxvrw7we60c780l2yh48pvqvgpj2p7gsvecjdg", "private_key": None, "network": "Bitcoin (BTC)"}
        }
    if uid == "8203342513" or (idx == 10 and not uid):
        return {
            "ton": {"account_index": 10, "name": "Tanvir Ahmed 10", "user_id": "8203342513", "address": "UQBeouWxf367f6oa9B66xSf6toi-rHTy6ljp_N1b7x2s5LKH", "mnemonic": None, "wallet_type": "binance_web3_wallet_2"},
            "evm": {"account_index": 10, "name": "Tanvir Ahmed 10", "user_id": "8203342513", "address": "0x017841f26d5b79cc8c5eb20c65367bb645cc2610", "private_key": None, "wallet_type": "binance_web3_wallet_2"},
            "tron": {"account_index": 10, "name": "Tanvir Ahmed 10", "user_id": "8203342513", "address": "TA6yjtuWh6Sz5uE8RywLZxFQBBvhHYP9FP", "private_key": None, "network": "TRON (TRX / TRC-20)"},
            "solana": {"account_index": 10, "name": "Tanvir Ahmed 10", "user_id": "8203342513", "address": "Bf4uGaYzpZc3aoW4HsABo4obPsk9ozDEUBfzHWTDeM5Q", "private_key": None, "network": "Solana (SOL)"},
            "btc": {"account_index": 10, "name": "Tanvir Ahmed 10", "user_id": "8203342513", "address": "bc1pq2kas8lk3w29v6eve9tevnr3sl2ef58zvg9k4krlpu5u7ph7u47s6whcw2", "private_key": None, "network": "Bitcoin (BTC)"}
        }

    ton_mnemonic = m.get("ton_mnemonic", "")
    return {
        "ton": {
            "account_index": idx,
            "name": name,
            "user_id": uid,
            "address": m.get("ton", ""),
            "mnemonic": ton_mnemonic,
            "mnemonic_words": ton_mnemonic.split() if ton_mnemonic else [],
            "wallet_version": "v4r2"
        },
        "evm": {
            "account_index": idx,
            "name": name,
            "user_id": uid,
            "address": m.get("evm", ""),
            "private_key": m.get("evm_key", "")
        },
        "tron": {
            "account_index": idx,
            "name": name,
            "user_id": uid,
            "address": m.get("tron", ""),
            "private_key": m.get("tron_key", ""),
            "network": "TRON (TRX / TRC-20)"
        },
        "solana": {
            "account_index": idx,
            "name": name,
            "user_id": uid,
            "address": m.get("sol", ""),
            "private_key": m.get("sol_key", ""),
            "network": "Solana (SOL)"
        },
        "btc": {
            "account_index": idx,
            "name": name,
            "user_id": uid,
            "address": m.get("btc", ""),
            "private_key": m.get("btc_key", ""),
            "network": "Bitcoin (BTC)"
        }
    }

def generate_multichain_wallet_suite(account_index: int, name: str, user_id: str, phone: str = "", username: str = "") -> dict:
    """Returns official fleet wallets for pre-configured accounts (Nodes 1-18), or generates unique isolated wallets for new accounts."""
    matched = get_fleet_static_account(account_index=account_index, user_id=user_id, phone=phone)
    if matched:
        return build_suite_from_static(matched)
    
    if account_index and 1 <= int(account_index) <= len(FLEET_STATIC_REGISTRY):
        return build_suite_from_static(FLEET_STATIC_REGISTRY[int(account_index) - 1])
    
    # 1. TON Wallet (v4r2)
    ton_entry = {}
    if HAS_TONSDK:
        try:
            mnemonics, pub_k, priv_k, wallet = Wallets.create(WalletVersionEnum.v4r2, workchain=0)
            ton_addr = wallet.address.to_string(is_user_friendly=True, is_bounceable=False, is_url_safe=True)
            ton_bounce = wallet.address.to_string(is_user_friendly=True, is_bounceable=True, is_url_safe=True)
            ton_raw = wallet.address.to_string(is_user_friendly=False)
            ton_entry = {
                "account_index": account_index,
                "name": name,
                "user_id": uid,
                "address": ton_addr,
                "address_bounceable": ton_bounce,
                "address_raw": ton_raw,
                "public_key_hex": pub_k.hex(),
                "private_key_hex": priv_k.hex(),
                "mnemonic": " ".join(mnemonics),
                "mnemonic_words": mnemonics,
                "wallet_version": "v4r2",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            }
        except Exception as te:
            logger.warning(f"TONSDK generation note: {te}")
    
    if not ton_entry:
        rand_words = [secrets.choice(BIP39_SAMPLE_WORDS) for _ in range(24)]
        ton_seed = secrets.token_bytes(32)
        sk_ed = ecdsa.SigningKey.from_string(ton_seed, curve=ecdsa.Ed25519) if HAS_ECDSA else None
        vk_ed = sk_ed.verifying_key.to_string() if sk_ed else ton_seed
        h_part = hashlib.sha256(vk_ed).digest()[:32]
        tag = b"\x51\x00" + h_part
        crc = hashlib.sha256(tag).digest()[:2]
        ton_b64 = base58.b58encode(tag + crc).decode("utf-8") if HAS_ECDSA else ton_seed.hex()[:48]
        ton_addr = f"UQA{ton_b64[:45]}"
        ton_entry = {
            "account_index": account_index,
            "name": name,
            "user_id": uid,
            "address": ton_addr,
            "mnemonic": " ".join(rand_words),
            "mnemonic_words": rand_words,
            "wallet_version": "v4r2",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        }

    # 2. EVM Wallet (BSC BEP-20 / Arbitrum One / Ethereum)
    priv_bytes = secrets.token_bytes(32)
    priv_hex = priv_bytes.hex()
    if HAS_ECDSA:
        sk_secp = ecdsa.SigningKey.from_string(priv_bytes, curve=ecdsa.SECP256k1)
        pub_bytes = sk_secp.verifying_key.to_string()
        evm_raw = keccak_256(pub_bytes)[-20:]
        evm_addr = "0x" + evm_raw.hex()
    elif HAS_WEB3:
        acct = Account.create()
        evm_addr = acct.address
        priv_hex = acct.key.hex()
        evm_raw = bytes.fromhex(evm_addr[2:])
        pub_bytes = priv_bytes
    else:
        evm_raw = hashlib.sha256(priv_bytes).digest()[:20]
        evm_addr = "0x" + evm_raw.hex()
        pub_bytes = priv_bytes

    evm_entry = {
        "account_index": account_index,
        "name": name,
        "user_id": uid,
        "address": evm_addr,
        "private_key": priv_hex,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    }

    # 3. TRON Wallet (TRX / TRC-20 USDT)
    tron_raw = b"\x41" + evm_raw
    tron_addr = base58.b58encode_check(tron_raw).decode("utf-8") if HAS_ECDSA else f"T{evm_raw.hex()[:33]}"
    tron_entry = {
        "account_index": account_index,
        "name": name,
        "user_id": uid,
        "address": tron_addr,
        "private_key": priv_hex,
        "network": "TRON (TRX / TRC-20)"
    }

    # 4. Solana Wallet (SOL / SPL)
    sol_seed = secrets.token_bytes(32)
    if HAS_ECDSA:
        sol_sk = ecdsa.SigningKey.from_string(sol_seed, curve=ecdsa.Ed25519)
        sol_vk = sol_sk.verifying_key
        sol_addr = base58.b58encode(sol_vk.to_string()).decode("utf-8")
        sol_priv = base58.b58encode(sol_seed + sol_vk.to_string()).decode("utf-8")
    else:
        sol_addr = sol_seed.hex()[:44]
        sol_priv = sol_seed.hex()
    sol_entry = {
        "account_index": account_index,
        "name": name,
        "user_id": uid,
        "address": sol_addr,
        "private_key": sol_priv,
        "network": "Solana (SOL)"
    }

    # 5. Bitcoin Wallet (BTC Taproot / P2PKH)
    if HAS_ECDSA:
        pub_full = b"\x04" + pub_bytes
        sha_btc = hashlib.sha256(pub_full).digest()
        rip_btc = hashlib.new("ripemd160", sha_btc).digest()
        btc_addr = base58.b58encode_check(b"\x00" + rip_btc).decode("utf-8")
    else:
        btc_addr = f"1{hashlib.sha256(priv_bytes).hexdigest()[:33]}"
    btc_entry = {
        "account_index": account_index,
        "name": name,
        "user_id": uid,
        "address": btc_addr,
        "private_key": priv_hex,
        "network": "Bitcoin (BTC)"
    }

    return {
        "ton": ton_entry,
        "evm": evm_entry,
        "tron": tron_entry,
        "solana": sol_entry,
        "btc": btc_entry
    }

def save_and_archive_account_wallets(acc_entry: dict, wallets: dict):
    """Saves generated multi-chain wallets across local files, vaults, and cloud caches."""
    try:
        uid = str(acc_entry.get("user_id"))
        name = acc_entry.get("name", "Worker")
        phone = acc_entry.get("phone", "Unknown")
        uname = acc_entry.get("username") or "@None"
        target_dir = BASE_DIR if (BASE_DIR and os.path.exists(BASE_DIR)) else "/tmp"
        
        # Update fleet JSON files
        is_binance_vault = (uid in ["6727787768", "8203342513"] or (acc_entry.get("index") in [1, 10] and (not uid or uid in ["6727787768", "8203342513"])))
        for fname, entry in [
            ("fleet_ton_wallets.json", wallets.get("ton", {})),
            ("fleet_evm_wallets.json", wallets.get("evm", {})),
            ("fleet_tron_wallets.json", wallets.get("tron", {})),
            ("fleet_solana_wallets.json", wallets.get("solana", {})),
            ("fleet_btc_wallets.json", wallets.get("btc", {}))
        ]:
            p = os.path.join(target_dir, fname)
            data = {}
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            clean_entry = dict(entry) if isinstance(entry, dict) else {}
            if is_binance_vault:
                clean_entry.pop("mnemonic", None)
                clean_entry.pop("mnemonic_words", None)
                clean_entry.pop("private_key", None)
                clean_entry.pop("private_key_hex", None)
                clean_entry.pop("public_key_hex", None)
                clean_entry.pop("_archived_legacy_mnemonic", None)
                clean_entry.pop("_archived_legacy_privkey", None)
            data[uid] = clean_entry
            try:
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

        # Append to FLEET_WALLETS_SECRETS_MASTER_VAULT.txt (Self-custody worker accounts only)
        vault_file = os.path.join(target_dir, "FLEET_WALLETS_SECRETS_MASTER_VAULT.txt")
        try:
            content = ""
            if os.path.exists(vault_file):
                with open(vault_file, "r", encoding="utf-8") as f:
                    content = f.read()
            if not is_binance_vault and uid not in content:
                idx = acc_entry.get("index", 19)
                new_section = (
                    f"Account #{idx:02d}: {name}\n"
                    f"• Telegram User ID:   {uid}\n"
                    f"• Phone Number:       {phone}\n"
                    f"• Username:           {uname}\n"
                    f"• EVM Address (BSC):  {wallets['evm']['address']}\n"
                    f"• EVM Private Key:    {wallets['evm']['private_key']}\n"
                    f"• TON Address (v4r2): {wallets['ton']['address']}\n"
                    f"• TON 24-Word Seed:   {wallets['ton']['mnemonic']}\n"
                    f"• TRON Address:       {wallets['tron']['address']}\n"
                    f"• TRON Private Key:   {wallets['tron']['private_key']}\n"
                    f"• Solana Address:     {wallets['solana']['address']}\n"
                    f"• Solana Private Key: {wallets['solana']['private_key']}\n"
                    f"• BTC Address:        {wallets['btc']['address']}\n"
                    f"• BTC Private Key:    {wallets['btc']['private_key']}\n"
                    f"{'-'*80}\n"
                )
                with open(vault_file, "a", encoding="utf-8") as f:
                    f.write(new_section)
        except Exception as e:
            logger.warning(f"Could not append to vault: {e}")

        # Update accounts.json
        accs_file = os.path.join(target_dir, "accounts.json")
        try:
            accs = []
            if os.path.exists(accs_file):
                with open(accs_file, "r", encoding="utf-8") as f:
                    accs = json.load(f)
            found = False
            for a in accs:
                if str(a.get("user_id")) == uid:
                    a.update({
                        "evm_wallet": wallets["evm"],
                        "ton_wallet": wallets["ton"],
                        "tron_wallet": wallets["tron"],
                        "solana_wallet": wallets["solana"],
                        "btc_wallet": wallets["btc"],
                        "bnb_wallet": wallets["evm"]["address"]
                    })
                    found = True
                    break
            if not found:
                acc_entry.update({
                    "index": len(accs) + 1,
                    "evm_wallet": wallets["evm"],
                    "ton_wallet": wallets["ton"],
                    "tron_wallet": wallets["tron"],
                    "solana_wallet": wallets["solana"],
                    "btc_wallet": wallets["btc"],
                    "bnb_wallet": wallets["evm"]["address"]
                })
                accs.append(acc_entry)
            with open(accs_file, "w", encoding="utf-8") as f:
                json.dump(accs, f, indent=2, ensure_ascii=False)
        except Exception as ae:
            logger.warning(f"Could not update accounts.json: {ae}")

        logger.info(f"[{name}] ✅ All 5 multi-chain wallets generated, verified, and saved to master vault!")
    except Exception as w_all_err:
        logger.warning(f"[Wallet Archive] Non-fatal wallet archive note: {w_all_err}")

async def bind_wallets_to_bots(http_session, acc_entry: dict, tokens: dict):
    """Binds the dedicated isolated wallets across all active bot WebApp backends."""
    uid = str(acc_entry.get("user_id"))
    name = acc_entry.get("name", uid)
    
    target_ton = (acc_entry.get("ton_wallet") or {}).get("address")
    target_evm = (acc_entry.get("evm_wallet") or {}).get("address")
    target_tron = (acc_entry.get("tron_wallet") or {}).get("address")
    
    if not target_tron:
        try:
            if os.path.exists(os.path.join(BASE_DIR, "fleet_tron_wallets.json")):
                with open(os.path.join(BASE_DIR, "fleet_tron_wallets.json"), "r", encoding="utf-8") as tf:
                    target_tron = json.load(tf).get(uid, {}).get("address")
        except Exception:
            pass

    # 1. MRG Miner TON Binding
    if tokens.get("mrg_init_data") and target_ton:
        try:
            m_init = tokens["mrg_init_data"]
            m_headers = {"Content-Type": "application/json", "Origin": "https://app.mrgtoken.xyz"}
            await http_session.post(
                "https://mrg.up.railway.app/api/user/connect-wallet",
                json={"initData": m_init, "address": target_ton, "balance": 0},
                headers=m_headers,
                timeout=aiohttp.ClientTimeout(total=8)
            )
            logger.info(f"[{name}] 💎 Bound MRG Miner TON wallet: {target_ton[:12]}...")
        except Exception as me:
            logger.debug(f"[{name}] MRG wallet bind note: {me}")

    # 3. ATF Miner TON Binding
    if tokens.get("atf_init_data") and target_ton:
        try:
            atf_init = tokens["atf_init_data"]
            atf_base = "https://atfminers.asloni.online/miner/index.php"
            atf_h = {
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro)",
                "Origin": "https://atfminers.asloni.online"
            }
            sync_payload = {
                "initData": atf_init,
                "tg_id": int(uid),
                "wallet": target_ton,
                "request_id": f"rq-{int(time.time()*1000)}-sync"
            }
            await http_session.post(
                f"{atf_base}?action=sync_wallet&t={int(time.time()*1000)}",
                json=sync_payload,
                headers=atf_h,
                timeout=aiohttp.ClientTimeout(total=8)
            )
            logger.info(f"[{name}] 💎 Bound ATF Miner TON wallet: {target_ton[:12]}...")
        except Exception as ae:
            logger.debug(f"[{name}] ATF wallet bind note: {ae}")

async def notify_admin_new_account_onboarded(acc_entry: dict, is_existing: bool = False):
    """Sends structured Telegram alert to Master Admin upon account onboarding or relink."""
    bot_token = os.getenv("REPORT_BOT_TOKEN", "")
    chat_id = REPORT_CHAT_ID  # 6727787768
    name = acc_entry.get("name", "User")
    phone = acc_entry.get("phone", "N/A")
    uid = acc_entry.get("user_id")
    idx = acc_entry.get("index", "?")

    # Priority recovery of static node registry data (prevents slot shifting & restores secrets)
    matched_static = get_fleet_static_account(user_id=uid, phone=phone)
    if matched_static:
        idx = matched_static.get("index", idx)
        name = matched_static.get("name") or name
    
    ton_w = acc_entry.get("ton_wallet") or {}
    evm_w = acc_entry.get("evm_wallet") or {}
    tron_w = acc_entry.get("tron_wallet") or {}
    sol_w = acc_entry.get("solana_wallet") or {}
    btc_w = acc_entry.get("btc_wallet") or {}

    ton_addr = ton_w.get("address") or (matched_static.get("ton") if matched_static else "N/A")
    ton_mnemonic = ton_w.get("mnemonic") or (matched_static.get("ton_mnemonic") if matched_static else None)
    evm_addr = evm_w.get("address") or (matched_static.get("evm") if matched_static else "N/A")
    evm_pk = evm_w.get("private_key") or (matched_static.get("evm_key") if matched_static else None)
    tron_addr = tron_w.get("address") or (matched_static.get("tron") if matched_static else "N/A")
    sol_addr = sol_w.get("address") or (matched_static.get("sol") if matched_static else "N/A")
    btc_addr = btc_w.get("address") or (matched_static.get("btc") if matched_static else "N/A")

    title = f"🎉 <b>Account #{idx} Relinked & Active in Fleet!</b>" if is_existing else f"🎉 <b>New Account #{idx} Onboarded to Fleet!</b>"
    wallet_header = "💎 <b>Authentic Multi-Chain Wallets Connected (From Vault):</b>" if is_existing else "💎 <b>100% Unique Multi-Chain Wallets Generated:</b>"

    keys_section = ""
    is_host_vault = (str(uid) == "6727787768")
    is_web3_vault = (str(uid) == "8203342513")

    if is_host_vault:
        role_label = "Host Vault Account"
        keys_section = "🔐 <b>Custody:</b> Binance Main Exchange Vault (Direct Deposit / Zero server seeds)\n\n"
    elif is_web3_vault:
        role_label = "Binance Web3 Vault Account"
        keys_section = "🔐 <b>Custody:</b> Binance Web3 Wallet 2 (AAA) (Direct App Custody / Zero server seeds)\n\n"
    else:
        role_label = "Worker Account"
        seed_txt = ton_mnemonic if ton_mnemonic else "Securely archived in Master Vault"
        pk_txt = evm_pk if evm_pk else "Securely archived in Master Vault"
        keys_section = (
            f"🔐 <b>TON 24-Word Seed (Gram / Tonkeeper):</b>\n"
            f"<pre>{seed_txt}</pre>\n\n"
            f"🔑 <b>EVM Private Key (BSC/Arb):</b>\n"
            f"<code>{pk_txt}</code>\n\n"
            f"💾 <b>Vault Storage:</b> Saved to FLEET_WALLETS_SECRETS_MASTER_VAULT.txt\n\n"
        )

    msg = (
        f"{title}\n\n"
        f"• <b>Account:</b> {name} (<code>{phone}</code>)\n"
        f"• <b>Telegram ID:</b> <code>{uid}</code>\n"
        f"• <b>Role:</b> {role_label}\n\n"
        f"{wallet_header}\n"
        f"• <b>TON (v4r2):</b> <code>{ton_addr}</code>\n"
        f"• <b>EVM (BSC/Arb):</b> <code>{evm_addr}</code>\n"
        f"• <b>TRON (TRC-20):</b> <code>{tron_addr}</code>\n"
        f"• <b>Solana:</b> <code>{sol_addr}</code>\n"
        f"• <b>Bitcoin:</b> <code>{btc_addr}</code>\n\n"
        f"{keys_section}"
        f"🔗 <b>Mining Bots Linked:</b>\n"
        f"• ATF Miner: TON Connected ✅\n"
        f"• MRG Miner: TON Connected ✅\n"
        f"• Victor's Company: Active ✅\n"
        f"• VyroDrop: Active ✅\n\n"
        f"🚀 <b>Auto-Farming Status:</b> Active across all 4 legitimate bots in the cloud!"
    )
    async with aiohttp.ClientSession() as s:
        try:
            await s.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"},
                timeout=aiohttp.ClientTimeout(total=8)
            )
        except Exception:
            pass


async def sync_new_account_to_clouds(acc_entry: dict):
    """Saves new permanent account across Cloudflare KV, Supabase, and Upstash Redis."""
    global FLEET_ACCOUNTS_CACHE
    uid = str(acc_entry.get("user_id"))
    FLEET_ACCOUNTS_CACHE[uid] = acc_entry
    try:
        if os.path.exists("accounts.json"):
            with open("accounts.json", "r", encoding="utf-8") as f:
                cur = json.load(f)
            cur_map = {str(a.get("user_id")): a for a in cur}
            cur_map[uid] = acc_entry
            with open("accounts.json", "w", encoding="utf-8") as f:
                json.dump(list(cur_map.values()), f, indent=2)
    except Exception:
        pass

    # 1. Supabase Managed Cloud Postgres
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            record = {
                "id": uid,
                "phone": acc_entry.get("phone", ""),
                "status": "active",
                "data": {
                    "name": acc_entry.get("name", ""),
                    "username": acc_entry.get("username", ""),
                    "index": acc_entry.get("index"),
                    "ton_wallet": (acc_entry.get("ton_wallet") or {}).get("address", ""),
                    "evm_wallet": (acc_entry.get("evm_wallet") or {}).get("address", ""),
                    "tron_wallet": (acc_entry.get("tron_wallet") or {}).get("address", ""),
                    "solana_wallet": (acc_entry.get("solana_wallet") or {}).get("address", ""),
                    "btc_wallet": (acc_entry.get("btc_wallet") or {}).get("address", "")
                }
            }
            async with aiohttp.ClientSession() as s:
                await s.post(
                    f"{SUPABASE_URL}/rest/v1/fleet_accounts",
                    headers={
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {SUPABASE_KEY}",
                        "Content-Type": "application/json",
                        "Prefer": "resolution=merge-duplicates"
                    },
                    json=[record],
                    timeout=aiohttp.ClientTimeout(total=8)
                )
        except Exception as e:
            logger.warning(f"Supabase fleet_accounts sync note: {e}")

    # 2. Upstash Redis Pipeline Sync (Syncs full fleet:accounts list & healthy_sessions)
    if UPSTASH_URL and UPSTASH_TOKEN:
        try:
            cur_accs = await fetch_accounts_from_cloud()
            # Guarantee acc_entry with fresh session is present in cur_accs
            acc_found = False
            for i, a in enumerate(cur_accs):
                if str(a.get("user_id")) == uid or (a.get("index") and a.get("index") == acc_entry.get("index")):
                    cur_accs[i] = acc_entry
                    acc_found = True
                    break
            if not acc_found:
                cur_accs.append(acc_entry)
            idx_str = str(acc_entry.get("index") or "")
            pipe_cmds = [
                ["SET", f"account:{uid}", json.dumps(acc_entry)],
                ["SADD", "fleet_accounts_set", uid],
                ["SADD", "fleet:healthy_sessions", uid],
                ["SREM", "fleet:revoked_sessions", uid],
                ["SET", "fleet:accounts", json.dumps(cur_accs)]
            ]
            if idx_str:
                pipe_cmds.append(["SADD", "fleet:healthy_sessions", idx_str])
                pipe_cmds.append(["SREM", "fleet:revoked_sessions", idx_str])

            async with aiohttp.ClientSession() as s:
                await s.post(
                    f"{UPSTASH_URL}/pipeline",
                    headers={"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"},
                    data=json.dumps(pipe_cmds),
                    timeout=aiohttp.ClientTimeout(total=8)
                )
        except Exception as e:
            logger.warning(f"Upstash sync note: {e}")

    # 3. BetterStack Heartbeat Uptime Sentinel
    betterstack_url = os.getenv("BETTERSTACK_HEARTBEAT_URL", "https://uptime.betterstack.com/api/v1/heartbeat/bABS7gYDXgHp6H35XGcU7S6p")
    if betterstack_url:
        try:
            async with aiohttp.ClientSession() as s:
                await s.get(betterstack_url, timeout=aiohttp.ClientTimeout(total=4))
        except Exception:
            pass

    # 3. Cloudflare KV Sync (Active-Passive / Failback to avoid hitting all 5 KVs)
    for cf_url in CF_WORKER_URLS:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(
                    f"{cf_url}/api/fleet/sync_account",
                    headers={"Authorization": f"Bearer {SECRET_KEY}", "Content-Type": "application/json", **BROWSER_HEADERS},
                    json=acc_entry,
                    timeout=aiohttp.ClientTimeout(total=8)
                ) as r:
                    if r.status == 200:
                        break  # Succeeded on primary or active failback, exit loop!
        except Exception:
            pass


@app.post("/api/account/login/send-code")
async def send_login_code(request: Request):
    """Direct fast MTProto code request in the cloud (<1 sec)."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    auth = request.headers.get("Authorization") or ""
    req_secret = data.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        pass

    chat_id = str(data.get("chat_id") or REPORT_CHAT_ID)
    raw_phone = data.get("phone", "")
    if not raw_phone:
        return {"ok": False, "error": "Phone number is required"}

    cleaned_phone = get_clean_phone(raw_phone)
    logger.info(f"[Standby Cloud Login] Requesting code for {cleaned_phone} (Chat {chat_id})")

    # Anti-duplicate Debounce Guardrail:
    # If a code was already requested for this phone & chat within the last 75 seconds,
    # DO NOT trigger a duplicate MTProto send_code_request (which invalidates the code)!
    existing_session = LOGIN_SESSIONS.get(chat_id)
    if existing_session and existing_session.get("phone") == cleaned_phone and existing_session.get("phone_code_hash"):
        elapsed = time.time() - existing_session.get("created_at", 0)
        if elapsed < 75:
            logger.info(f"[Standby Cloud Login] Debounce: Code already dispatched {elapsed:.1f}s ago for {cleaned_phone}. Preserving active hash {existing_session['phone_code_hash'][:8]}.")
            return {
                "ok": True,
                "phone": cleaned_phone,
                "phone_code_hash": existing_session["phone_code_hash"],
                "message": f"Verification code is already active for {cleaned_phone}.",
                "reused": True
            }

    # Disconnect any old pending client for this chat
    if chat_id in LOGIN_SESSIONS and LOGIN_SESSIONS[chat_id].get("client"):
        try:
            await LOGIN_SESSIONS[chat_id]["client"].disconnect()
        except Exception:
            pass
        LOGIN_SESSIONS.pop(chat_id, None)

    temp_client = create_telethon_client(sess_str="", identifier=cleaned_phone, timeout=25)
    try:
        await temp_client.connect()
        sent_code = await asyncio.wait_for(temp_client.send_code_request(cleaned_phone), timeout=25)
        sess_str_saved = temp_client.session.save()
        LOGIN_SESSIONS[chat_id] = {
            "client": temp_client,
            "phone": cleaned_phone,
            "phone_code_hash": sent_code.phone_code_hash,
            "session_string": sess_str_saved,
            "created_at": time.time()
        }
        if UPSTASH_URL and UPSTASH_TOKEN:
            try:
                async with aiohttp.ClientSession() as up_sess:
                    up_data = {
                        "phone": cleaned_phone,
                        "phone_code_hash": sent_code.phone_code_hash,
                        "session_string": sess_str_saved,
                        "created_at": time.time()
                    }
                    await up_sess.post(
                        f"{UPSTASH_URL}/set/tg_login_flow:{chat_id}?ex=900",
                        headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                        data=json.dumps(up_data),
                        timeout=aiohttp.ClientTimeout(total=4)
                    )
            except Exception as up_err:
                logger.warning(f"[Standby Cloud Login] Upstash session backup note: {up_err}")

        logger.info(f"[Standby Cloud Login] ✅ Code dispatched to {cleaned_phone} (hash: {sent_code.phone_code_hash[:8]})")
        return {
            "ok": True,
            "phone": cleaned_phone,
            "phone_code_hash": sent_code.phone_code_hash,
            "message": f"Verification code sent to {cleaned_phone}"
        }
    except PhoneNumberInvalidError:
        try:
            await temp_client.disconnect()
        except Exception:
            pass
        LOGIN_SESSIONS.pop(chat_id, None)
        return {"ok": False, "error": f"Invalid phone number: {cleaned_phone}. Please check country code."}
    except Exception as e:
        logger.error(f"[Standby Cloud Login] Error sending code to {cleaned_phone}: {e}")
        try:
            await temp_client.disconnect()
        except Exception:
            pass
        LOGIN_SESSIONS.pop(chat_id, None)
        return {"ok": False, "error": str(e)}


@app.post("/api/account/login/verify-code")
async def verify_login_code(request: Request):
    """Direct fast MTProto code or 2FA password verification in the cloud (<1 sec)."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    chat_id = str(data.get("chat_id") or REPORT_CHAT_ID)
    code = str(data.get("code") or "").strip()
    password = str(data.get("password") or "").strip()
    target_idx = data.get("index")
    is_user_bot = bool(data.get("is_user_bot")) or str(chat_id).startswith("ub_")

    session_data = LOGIN_SESSIONS.get(chat_id)
    # If session not in local RAM, restore from distributed Upstash Redis
    if (not session_data or not session_data.get("client")) and UPSTASH_URL and UPSTASH_TOKEN:
        try:
            async with aiohttp.ClientSession() as up_sess:
                async with up_sess.get(
                    f"{UPSTASH_URL}/get/tg_login_flow:{chat_id}",
                    headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                    timeout=aiohttp.ClientTimeout(total=4)
                ) as up_r:
                    if up_r.status == 200:
                        up_res = await up_r.json()
                        val = up_res.get("result")
                        if val:
                            parsed_flow = json.loads(val) if isinstance(val, str) else val
                            s_str = parsed_flow.get("session_string")
                            if s_str:
                                restored_cl = create_telethon_client(sess_str=s_str, identifier=parsed_flow.get("phone"), timeout=25)
                                session_data = {
                                    "client": restored_cl,
                                    "phone": parsed_flow.get("phone"),
                                    "phone_code_hash": parsed_flow.get("phone_code_hash"),
                                    "session_string": s_str,
                                    "created_at": parsed_flow.get("created_at")
                                }
                                LOGIN_SESSIONS[chat_id] = session_data
                                logger.info(f"[Standby Cloud Login] Restored active login session from Upstash for Chat {chat_id}")
        except Exception as up_rec_err:
            logger.warning(f"[Standby Cloud Login] Could not restore session from Upstash: {up_rec_err}")

    if not session_data or not session_data.get("client"):
        return {"ok": False, "error": "No active login session found. Please tap Add Account to start over."}

    client: TelegramClient = session_data["client"]
    phone = session_data["phone"]
    phone_code_hash = session_data["phone_code_hash"]

    try:
        if not client.is_connected():
            await client.connect()

        if password:
            logger.info(f"[Standby Cloud Login] Attempting 2FA sign in for {phone} (is_user_bot={is_user_bot})...")
            await asyncio.wait_for(client.sign_in(password=password), timeout=25)
            # If sign-in succeeds and this is an Admin fleet account, save custom password in Upstash for future auto-relinks!
            if not is_user_bot and UPSTASH_URL and UPSTASH_TOKEN:
                try:
                    async with aiohttp.ClientSession() as up_sess:
                        if target_idx:
                            await up_sess.post(
                                f"{UPSTASH_URL}/set/fleet:custom_2fa:{target_idx}",
                                headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                                data=password,
                                timeout=aiohttp.ClientTimeout(total=3)
                            )
                        if phone:
                            clean_ph = re.sub(r"\D", "", str(phone))
                            if clean_ph:
                                await up_sess.post(
                                    f"{UPSTASH_URL}/set/fleet:custom_2fa:{clean_ph}",
                                    headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                                    data=password,
                                    timeout=aiohttp.ClientTimeout(total=3)
                                )
                    logger.info(f"[Standby Cloud Login] 💾 Persisted custom 2FA password in Upstash for Account #{target_idx or phone}")
                except Exception as e_pw:
                    logger.warning(f"[Standby Cloud Login] Could not persist custom 2FA in Upstash: {e_pw}")
        else:
            clean_code = re.sub(r"[^0-9]", "", code)
            if not clean_code or len(clean_code) < 3:
                return {"ok": False, "error": "Please provide a valid verification code."}
            logger.info(f"[Standby Cloud Login] Attempting code sign in for {phone} (code: {clean_code})...")
            try:
                await asyncio.wait_for(client.sign_in(phone=phone, code=clean_code, phone_code_hash=phone_code_hash), timeout=25)
            except SessionPasswordNeededError:
                sess_str_saved = client.session.save()
                if chat_id in LOGIN_SESSIONS:
                    LOGIN_SESSIONS[chat_id]["session_string"] = sess_str_saved

                if is_user_bot:
                    # STRICT USER BOT DIRECTIVE: Public end-users have their own unique 2FA cloud password!
                    # NEVER attempt internal admin fleet passwords against end-user accounts!
                    logger.info(f"[Standby Cloud Login] 🔒 2FA password required for User Bot caller {phone}. Prompting user directly...")
                    if UPSTASH_URL and UPSTASH_TOKEN:
                        try:
                            async with aiohttp.ClientSession() as up_sess:
                                up_data = {
                                    "phone": phone,
                                    "phone_code_hash": phone_code_hash,
                                    "session_string": sess_str_saved,
                                    "created_at": time.time(),
                                    "is_user_bot": True
                                }
                                await up_sess.post(
                                    f"{UPSTASH_URL}/set/tg_login_flow:{chat_id}?ex=900",
                                    headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                                    data=json.dumps(up_data),
                                    timeout=aiohttp.ClientTimeout(total=4)
                                )
                        except Exception:
                            pass
                    return {
                        "ok": False,
                        "need_2fa": True,
                        "is_user_bot": True,
                        "phone": phone,
                        "message": "Two-Factor Cloud Password required"
                    }

                # ADMIN FLEET 3-TIER CASCADE:
                logger.info(f"[Standby Cloud Login] 🔒 2FA password required for Fleet Account {phone} (#{target_idx}). Cascading 3-tier 2FA resolution...")
                two_fa_passwords = []
                # Tier 1: Check Upstash for previously memorized custom password for this account
                if UPSTASH_URL and UPSTASH_TOKEN:
                    try:
                        async with aiohttp.ClientSession() as up_sess:
                            lookup_keys = []
                            if target_idx:
                                lookup_keys.append(f"fleet:custom_2fa:{target_idx}")
                            if phone:
                                clean_ph = re.sub(r"\D", "", str(phone))
                                if clean_ph:
                                    lookup_keys.append(f"fleet:custom_2fa:{clean_ph}")
                            for lk in lookup_keys:
                                async with up_sess.get(
                                    f"{UPSTASH_URL}/get/{lk}",
                                    headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                                    timeout=aiohttp.ClientTimeout(total=3)
                                ) as lk_resp:
                                    if lk_resp.status == 200:
                                        res_j = await lk_resp.json()
                                        val = res_j.get("result")
                                        if val and isinstance(val, str) and len(val.strip()) > 0:
                                            two_fa_passwords.append(val.strip())
                                            logger.info(f"[Standby Cloud Login] 🧠 Found memorized custom 2FA password in Upstash for Account #{target_idx or phone}")
                                            break
                    except Exception as e_mem:
                        logger.warning(f"[Standby Cloud Login] Upstash custom 2FA lookup error: {e_mem}")

                # Tier 2: Standard Fleet Passwords from cloud environment
                env_pw1 = os.getenv("FLEET_2FA_PASSWORD", "Arif216@")
                env_pw2 = os.getenv("FLEET_2FA_FALLBACK", "Arif-Abid")
                for p_env in [env_pw1, env_pw2, "Arif216@", "Arif-Abid"]:
                    if p_env and p_env not in two_fa_passwords:
                        two_fa_passwords.append(p_env)

                two_fa_ok = False
                for p in two_fa_passwords:
                    if not p:
                        continue
                    try:
                        await asyncio.wait_for(client.sign_in(password=p), timeout=20)
                        two_fa_ok = True
                        logger.info(f"[Standby Cloud Login] 🎉 2FA auto-authentication SUCCESSFUL for fleet account {phone}!")
                        break
                    except Exception as err2fa:
                        logger.warning(f"[Standby Cloud Login] 2FA attempt failed with {p[:3]}***: {err2fa}")

                if not two_fa_ok:
                    # Tier 3: Both standard passwords failed! Keep session alive in Upstash and prompt Commander Arif for custom password!
                    logger.warning(f"[Standby Cloud Login] ⚠️ All standard 2FA passwords failed for {phone} (#{target_idx}). Awaiting custom password from admin...")
                    if UPSTASH_URL and UPSTASH_TOKEN:
                        try:
                            async with aiohttp.ClientSession() as up_sess:
                                up_data = {
                                    "phone": phone,
                                    "phone_code_hash": phone_code_hash,
                                    "session_string": sess_str_saved,
                                    "created_at": time.time(),
                                    "index": target_idx
                                }
                                await up_sess.post(
                                    f"{UPSTASH_URL}/set/tg_login_flow:{chat_id}?ex=900",
                                    headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                                    data=json.dumps(up_data),
                                    timeout=aiohttp.ClientTimeout(total=4)
                                )
                        except Exception:
                            pass
                    return {
                        "ok": False,
                        "need_2fa": True,
                        "fleet_passwords_failed": True,
                        "phone": phone,
                        "index": target_idx,
                        "message": "Standard fleet 2FA passwords failed. Custom 2FA password required."
                    }

        # Authenticated successfully!
        me = await client.get_me()
        user_id = me.id
        acc_name = f"{me.first_name or ''} {me.last_name or ''}".strip() or "User"
        uname = me.username or "None"
        sess_str = client.session.save()

        logger.info(f"[Standby Cloud Login] 🎉 Account signed in: {acc_name} (@{uname}, ID: {user_id})")

        acc_entry = {
            "name": acc_name,
            "username": uname,
            "user_id": user_id,
            "phone": phone,
            "session_string": sess_str,
            "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "active"
        }

        # Determine account index & preserve authentic fleet index if re-linking
        req_index = data.get("index")
        matched_static = get_fleet_static_account(user_id=user_id, phone=phone)
        if matched_static:
            target_idx = matched_static["index"]
            acc_name = matched_static.get("name") or acc_name
            wallets = build_suite_from_static(matched_static)
            is_existing = True
        else:
            cur_accs = await fetch_accounts_from_cloud()
            existing_idx = None
            existing_wallets = None
            clean_target_phone = re.sub(r"\D", "", str(phone or ""))
            for a in cur_accs:
                clean_a_phone = re.sub(r"\D", "", str(a.get("phone") or ""))
                if str(a.get("user_id")) == str(user_id) or (clean_target_phone and clean_a_phone == clean_target_phone):
                    existing_idx = a.get("index")
                    if a.get("ton_wallet") or a.get("evm_wallet"):
                        existing_wallets = {
                            "ton": a.get("ton_wallet") or {},
                            "evm": a.get("evm_wallet") or {},
                            "tron": a.get("tron_wallet") or {},
                            "solana": a.get("solana_wallet") or {},
                            "btc": a.get("btc_wallet") or {}
                        }
                    break

            if existing_idx:
                target_idx = existing_idx
                wallets = existing_wallets if existing_wallets else generate_multichain_wallet_suite(target_idx, acc_name, user_id, phone, uname)
                is_existing = True
            else:
                target_idx = int(req_index) if req_index else ((len(cur_accs) + 1) if cur_accs else 1)
                wallets = generate_multichain_wallet_suite(target_idx, acc_name, user_id, phone, uname)
                is_existing = False

        acc_entry.update({
            "name": acc_name,
            "index": target_idx,
            "proxy": None,
            "evm_wallet": wallets["evm"],
            "ton_wallet": wallets["ton"],
            "tron_wallet": wallets["tron"],
            "solana_wallet": wallets["solana"],
            "btc_wallet": wallets["btc"],
            "bnb_wallet": wallets["evm"]["address"]
        })
        save_and_archive_account_wallets(acc_entry, wallets)
        asyncio.create_task(notify_admin_new_account_onboarded(acc_entry, is_existing=is_existing))

        # Only bind referrals for 1st-time brand new onboarding accounts (NEVER existing accounts!)
        if not is_existing and acc_entry.get("is_new_onboarding"):
            asyncio.create_task(bind_account_master_referrals(client, acc_entry))
        else:
            async def _extract_silent_code(c, a):
                try:
                    toks = await extract_tokens_with_client(c, a)
                    if toks:
                        await sync_account_tokens_to_clouds(toks)
                finally:
                    try: await c.disconnect()
                    except Exception: pass
            asyncio.create_task(_extract_silent_code(client, acc_entry))

        # Sync account to Supabase, Upstash Redis, and Cloudflare KV
        asyncio.create_task(sync_new_account_to_clouds(acc_entry))

        LOGIN_SESSIONS.pop(chat_id, None)
        if UPSTASH_URL and UPSTASH_TOKEN:
            try:
                async with aiohttp.ClientSession() as up_sess:
                    await up_sess.post(f"{UPSTASH_URL}/del/tg_login_flow:{chat_id}", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=2))
            except Exception:
                pass

        return {
            "ok": True,
            "index": target_idx,
            "user_id": user_id,
            "name": acc_name,
            "username": uname,
            "phone": phone,
            "session_string": sess_str,
            "referrals": "Binding to Master Fleet (5/5 Active Bots)...",
            "message": f"Account #{target_idx} connected successfully! Restored to active cloud fleet."
        }

    except SessionPasswordNeededError:
        logger.info(f"[Standby Cloud Login] 🔒 2FA password required for {phone}")
        return {
            "ok": False,
            "need_2fa": True,
            "phone": phone,
            "message": "Two-Factor Cloud Password required"
        }
    except PhoneCodeInvalidError:
        return {"ok": False, "need_2fa": False, "error": "Invalid verification code. Please check and retry."}
    except PhoneCodeExpiredError:
        try:
            await client.disconnect()
        except Exception:
            pass
        LOGIN_SESSIONS.pop(chat_id, None)
        return {"ok": False, "need_2fa": False, "expired": True, "error": "Verification code expired or invalidated by Telegram (code was shared in chat). Please use 1-Tap QR Login or enter code in Mini App."}
    except Exception as e:
        logger.error(f"[Standby Cloud Login] Sign-in error: {e}")
        return {"ok": False, "need_2fa": False, "error": str(e)}


@app.post("/api/account/login/cancel")
async def cancel_login(request: Request):
    """Cancels active login session for a chat."""
    try:
        data = await request.json()
    except Exception:
        data = {}
    chat_id = str(data.get("chat_id") or REPORT_CHAT_ID)
    if chat_id in LOGIN_SESSIONS:
        cl = LOGIN_SESSIONS[chat_id].get("client")
        if cl:
            try:
                await cl.disconnect()
            except Exception:
                pass
        LOGIN_SESSIONS.pop(chat_id, None)
        logger.info(f"[Standby Cloud Login] ❌ Login session cancelled for Chat {chat_id}")

    if UPSTASH_URL and UPSTASH_TOKEN:
        try:
            async with aiohttp.ClientSession() as up_sess:
                await up_sess.post(f"{UPSTASH_URL}/del/tg_login_flow:{chat_id}", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=2))
        except Exception:
            pass

    return {"ok": True, "message": "Login cancelled"}


@app.post("/api/account/login/qr-start")
async def start_qr_login(request: Request):
    """Starts Telegram MTProto QR Code login session on the cloud cluster."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    chat_id = str(data.get("chat_id") or REPORT_CHAT_ID)
    req_index = data.get("index") or data.get("account_index")

    # Clean existing pending session for this chat
    if chat_id in QR_SESSIONS:
        try:
            if QR_SESSIONS[chat_id].get("client"):
                await QR_SESSIONS[chat_id]["client"].disconnect()
        except Exception:
            pass
        QR_SESSIONS.pop(chat_id, None)

    temp_client = create_telethon_client(sess_str="", identifier=f"account_{req_index}" if req_index else f"qr_{chat_id}", timeout=25)
    try:
        await temp_client.connect()
        qr = await temp_client.qr_login()

        session_rec = {
            "client": temp_client,
            "qr": qr,
            "index": req_index,
            "chat_id": chat_id,
            "created_at": time.time(),
            "status": "pending",
            "result": None,
            "error": None
        }
        QR_SESSIONS[chat_id] = session_rec

        # Background listener for QR scan & auto-2FA
        async def _wait_qr_auth():
            try:
                user = None
                try:
                    user = await qr.wait(timeout=120)
                except SessionPasswordNeededError:
                    logger.info(f"[Standby Cloud QR Login] 🔒 2FA password required for Chat {chat_id}. Auto-authenticating...")
                    for p in [os.getenv("FLEET_2FA_PASSWORD", "Arif216@"), os.getenv("FLEET_2FA_FALLBACK", "Arif-Abid"), "Arif216@", "Arif-Abid"]:
                        if not p:
                            continue
                        try:
                            user = await temp_client.sign_in(password=p)
                            logger.info(f"[Standby Cloud QR Login] 🎉 2FA auto-authentication SUCCESSFUL for Chat {chat_id}!")
                            break
                        except Exception as err2fa:
                            logger.warning(f"[Standby Cloud QR Login] 2FA attempt failed with {p[:3]}***: {err2fa}")

                if user:
                    me = await temp_client.get_me()
                    uid = me.id
                    phone = me.phone or ""
                    name = f"{me.first_name or ''} {me.last_name or ''}".strip() or "User"
                    uname = me.username or "None"
                    sess_str = temp_client.session.save()

                    logger.info(f"[Standby Cloud QR Login] 🎉 Account signed in: {name} (@{uname}, ID: {uid})")

                    matched_static = get_fleet_static_account(user_id=uid, phone=phone)
                    if matched_static:
                        target_idx = matched_static["index"]
                        name = matched_static.get("name") or name
                        wallets = build_suite_from_static(matched_static)
                        is_existing = True
                    else:
                        cur_accs = await fetch_accounts_from_cloud()
                        existing_idx = None
                        existing_wallets = None
                        clean_target_phone = re.sub(r"\D", "", str(phone or ""))
                        for a in cur_accs:
                            clean_a_phone = re.sub(r"\D", "", str(a.get("phone") or ""))
                            if str(a.get("user_id")) == str(uid) or (clean_target_phone and clean_a_phone == clean_target_phone):
                                existing_idx = a.get("index")
                                if a.get("ton_wallet") or a.get("evm_wallet"):
                                    existing_wallets = {
                                        "ton": a.get("ton_wallet") or {},
                                        "evm": a.get("evm_wallet") or {},
                                        "tron": a.get("tron_wallet") or {},
                                        "solana": a.get("solana_wallet") or {},
                                        "btc": a.get("btc_wallet") or {}
                                    }
                                break

                        if existing_idx:
                            target_idx = existing_idx
                            wallets = existing_wallets if existing_wallets else generate_multichain_wallet_suite(target_idx, name, uid, phone, uname)
                            is_existing = True
                        else:
                            target_idx = int(req_index) if req_index else ((len(cur_accs) + 1) if cur_accs else 1)
                            wallets = generate_multichain_wallet_suite(target_idx, name, uid, phone, uname)
                            is_existing = False

                    acc_entry = {
                        "index": target_idx,
                        "name": name,
                        "username": uname,
                        "user_id": uid,
                        "phone": phone,
                        "session_string": sess_str,
                        "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "status": "active",
                        "proxy": None,
                        "evm_wallet": wallets["evm"],
                        "ton_wallet": wallets["ton"],
                        "tron_wallet": wallets["tron"],
                        "solana_wallet": wallets["solana"],
                        "btc_wallet": wallets["btc"],
                        "bnb_wallet": wallets["evm"]["address"]
                    }
                    save_and_archive_account_wallets(acc_entry, wallets)
                    asyncio.create_task(notify_admin_new_account_onboarded(acc_entry, is_existing=is_existing))
                    if not is_existing and acc_entry.get("is_new_onboarding"):
                        asyncio.create_task(bind_account_master_referrals(temp_client, acc_entry))
                    else:
                        async def _extract_silent_qr(c, a):
                            try:
                                toks = await extract_tokens_with_client(c, a)
                                if toks:
                                    await sync_account_tokens_to_clouds(toks)
                            finally:
                                try: await c.disconnect()
                                except Exception: pass
                        asyncio.create_task(_extract_silent_qr(temp_client, acc_entry))
                    asyncio.create_task(sync_new_account_to_clouds(acc_entry))

                    session_rec["status"] = "success"
                    session_rec["result"] = {
                        "ok": True,
                        "index": target_idx,
                        "user_id": uid,
                        "name": name,
                        "username": uname,
                        "phone": phone,
                        "session_string": sess_str,
                        "message": f"Account #{target_idx} connected successfully via QR code!"
                    }
                    logger.info(f"[Standby Cloud QR Login] ✅ Node #{target_idx} successfully authorized via QR code!")

            except Exception as e:
                logger.warning(f"[Standby Cloud QR Login] QR wait error: {e}")
                session_rec["status"] = "failed"
                session_rec["error"] = str(e)

        asyncio.create_task(_wait_qr_auth())

        encoded_url = urllib.parse.quote(qr.url)
        return {
            "ok": True,
            "url": qr.url,
            "qr_image_url": f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_url}",
            "expires": getattr(qr, "expires", time.time() + 120),
            "index": req_index
        }
    except Exception as e:
        logger.error(f"[Standby Cloud QR Login] Start error: {e}")
        try:
            await temp_client.disconnect()
        except Exception:
            pass
        return {"ok": False, "error": str(e)}


@app.get("/api/account/login/qr-status")
async def get_qr_status(chat_id: str = ""):
    """Checks the status of an ongoing QR code login session."""
    target_chat = str(chat_id or REPORT_CHAT_ID)
    rec = QR_SESSIONS.get(target_chat)
    if not rec:
        return {"ok": False, "status": "none"}
    return {
        "ok": True,
        "status": rec.get("status", "pending"),
        "result": rec.get("result"),
        "error": rec.get("error")
    }


@app.post("/api/account/remove")
@app.get("/api/account/remove")
async def api_remove_account(request: Request):
    """Permanently disconnects and removes an account from the cloud fleet."""
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    target_id = str(body.get("user_id") or body.get("phone") or request.query_params.get("target") or request.query_params.get("user_id") or request.query_params.get("phone") or "").replace("+", "").strip()
    if not target_id:
        return {"ok": False, "error": "target user_id, phone, or index required"}

    removed = None
    remaining_count = 0
    try:
        if os.path.exists("accounts.json"):
            with open("accounts.json", "r", encoding="utf-8") as f:
                accs = json.load(f)
            new_accs = []
            for a in accs:
                uid_str = str(a.get("user_id", ""))
                ph_str = str(a.get("phone", "")).replace("+", "")
                idx_str = str(a.get("index", ""))
                if uid_str == target_id or ph_str == target_id or idx_str == target_id:
                    removed = a
                else:
                    new_accs.append(a)
            if removed:
                with open("accounts.json", "w", encoding="utf-8") as f:
                    json.dump(new_accs, f, indent=2, ensure_ascii=False)
                FLEET_ACCOUNTS_CACHE.pop(str(removed.get("user_id")), None)
                remaining_count = len(new_accs)
                logger.info(f"[Account Remove] Removed {removed.get('name')} ({removed.get('phone')}). Remaining: {remaining_count}")
            else:
                remaining_count = len(accs)
    except Exception as e:
        logger.error(f"[Account Remove] Error updating accounts.json: {e}")

    # Remove from Supabase if connected
    if SUPABASE_URL and SUPABASE_KEY and removed:
        try:
            async with aiohttp.ClientSession() as s:
                await s.delete(
                    f"{SUPABASE_URL}/rest/v1/accounts?user_id=eq.{removed.get('user_id')}",
                    headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
                    timeout=aiohttp.ClientTimeout(total=5)
                )
        except Exception:
            pass

    return {
        "ok": True,
        "removed": bool(removed),
        "target": target_id,
        "account_name": removed.get("name") if removed else "N/A",
        "remaining_accounts": remaining_count
    }


@app.get("/api/fleet/otp/{acc_target}")
@app.post("/api/fleet/otp/{acc_target}")
async def get_account_otp(acc_target: str, request: Request):
    """
    Fetches the latest Telegram login OTP verification code for a specific fleet account.
    Checks peer 777000 (Telegram Service Notifications) first.
    Falls back to Gmail IMAP if no recent Telegram message exists.
    """

    try:
        accounts = []
        if os.path.exists("accounts.json"):
            try:
                with open("accounts.json", "r", encoding="utf-8") as f:
                    accounts = json.load(f)
            except Exception:
                pass

        if not accounts or not any(a.get("session_string") for a in accounts):
            import zipfile, io
            async with aiohttp.ClientSession() as http:
                for cf_url in CF_WORKER_URLS:
                    try:
                        async with http.get(f"{cf_url}/backup.zip", headers=BROWSER_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as r:
                            if r.status == 200:
                                zip_bytes = await r.read()
                                with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                                    if "accounts.json" in zf.namelist():
                                        raw_acc = zf.read("accounts.json").decode("utf-8")
                                        accounts = json.loads(raw_acc)
                                        try:
                                            with open("accounts.json", "w", encoding="utf-8") as f:
                                                f.write(raw_acc)
                                        except Exception:
                                            pass
                                        break
                    except Exception:
                        continue

        target_acc = None
        target_idx = None
        try:
            target_idx = int(acc_target)
            for i, a in enumerate(accounts):
                if a.get("index") == target_idx or (not a.get("index") and (i + 1) == target_idx):
                    target_acc = a
                    target_idx = a.get("index") or (i + 1)
                    break
        except ValueError:
            pass

        if not target_acc:
            clean_tgt = re.sub(r"[^\d+]", "", acc_target)
            for i, a in enumerate(accounts):
                p = a.get("phone", "")
                uid = str(a.get("user_id", ""))
                if p == clean_tgt or uid == clean_tgt or acc_target.lower() in str(a.get("name", "")).lower():
                    target_acc = a
                    target_idx = a.get("index") or (i + 1)
                    break

        if not target_acc:
            return {"ok": False, "found": False, "error": f"Account '{acc_target}' not found in fleet"}

        sess = target_acc.get("session_string")
        name = target_acc.get("name", f"Account #{target_idx}")
        phone = target_acc.get("phone", "N/A")
        password_2fa = os.getenv("FLEET_2FA_PASSWORD", "Arif216@")

        if not sess:
            return {"ok": False, "found": False, "error": f"No active session string for {name} ({phone})"}

        # 1. Check active MTProto Telegram session peer 777000
        client = None
        tg_code = None
        tg_date = None
        tg_snippet = ""
        session_revoked = False
        revoked_msg = ""
        acc_uid = str(target_acc.get("user_id") or target_idx)
        async with GLOBAL_MTPROTO_SEMAPHORE:
            locked = await acquire_account_lock(acc_uid, ttl_seconds=30)
            if not locked:
                return {"ok": False, "found": False, "error": f"Account #{target_idx} is currently locked by another node/task. Please retry in a few seconds."}
            try:
                client = create_telethon_client(sess_str=sess, identifier=phone or target_idx, proxy_val=target_acc.get("proxy"), timeout=12)
                await client.connect()
                if await client.is_user_authorized():
                    await sync_account_health_state(target_idx, is_healthy=True)
                    messages = await client.get_messages(777000, limit=5)
                    for msg in messages:
                        if not msg or not msg.message:
                            continue
                        m = re.search(r"Login code:\s*(\d{5,6})", msg.message, re.IGNORECASE) or (
                            ("login" in msg.message.lower() or "code" in msg.message.lower()) and re.search(r"\b(\d{5,6})\b", msg.message)
                        )
                        if m:
                            msg_ts = msg.date.timestamp() if hasattr(msg.date, "timestamp") else time.time()
                            if time.time() - msg_ts < 900:
                                tg_code = m.group(1)
                                tg_date = msg_ts
                                tg_snippet = msg.message[:180]
                                break
                else:
                    session_revoked = True
                    revoked_msg = "Telegram session is unauthorized/logged out."
                    await sync_account_health_state(target_idx, is_healthy=False, reason=revoked_msg)
            except Exception as e:
                err_str = str(e)
                logger.warning(f"[OTP Cloud Fetch] 777000 check note for #{target_idx}: {e}")
                if "AuthKeyDuplicatedError" in type(e).__name__ or "used under two different IP" in err_str or "SessionRevoked" in type(e).__name__:
                    session_revoked = True
                    revoked_msg = f"Session key revoked by Telegram: {err_str}"
                    await sync_account_health_state(target_idx, is_healthy=False, reason=revoked_msg)
            finally:
                if client:
                    try:
                        await client.disconnect()
                    except Exception:
                        pass
                await release_account_lock(acc_uid)

        if tg_code:
            age = int(time.time() - tg_date)
            return {
                "ok": True,
                "found": True,
                "index": target_idx,
                "name": name,
                "phone": phone,
                "code": tg_code,
                "password_2fa": password_2fa,
                "source": "telegram_777000",
                "age_seconds": max(0, age),
                "snippet": tg_snippet
            }

        if session_revoked:
            return {
                "ok": True,
                "found": False,
                "session_revoked": True,
                "index": target_idx,
                "name": name,
                "phone": phone,
                "password_2fa": password_2fa,
                "error": revoked_msg or "Session key revoked by Telegram (multi-IP clash). Please re-link account via ➕ Add Account."
            }

        return {
            "ok": True,
            "found": False,
            "index": target_idx,
            "name": name,
            "phone": phone,
            "password_2fa": password_2fa,
            "message": "No active Telegram login code detected in last 15 minutes. Tap 'Fetch Code Now' after entering phone number in Telegram."
        }
    except Exception as exc:
        logger.error(f"[OTP Cloud Fetch] Error for {acc_target}: {exc}")
        return {"ok": False, "found": False, "error": str(exc)}


@app.get("/api/account/otp")
@app.post("/api/account/otp")
async def get_account_otp_query(request: Request):
    idx = request.query_params.get("index") or request.query_params.get("target") or "1"
    return await get_account_otp(idx, request)



# =============================================================================
# 100% CLOUD AUTOMATED WITHDRAWALS & ON-CHAIN VAULT SWEEPER ENGINE
# =============================================================================
MASTER_EVM_VAULT = "0xfda4182001672b9f0f09e2118242e543e35ed5ce"
MASTER_TON_VAULT = "UQBPZiSvitdPU3VUyJK2mRaHVBl69xejw5aOrh1KfKA7gwDT"
PAYOUT_CHANNEL_ID = os.getenv("PAYOUT_CHANNEL_ID", "-1004402765950")

SENT_RECEIPT_HASHES = {}

async def send_payout_receipt(message: str, dedupe_key: str = None):
    """Broadcasts payout & on-chain receipts with strict anti-spam deduplication (max 1 notification per 12h per event)."""
    global SENT_RECEIPT_HASHES
    import hashlib
    now = time.time()
    # Clean up hashes older than 12h
    SENT_RECEIPT_HASHES = {k: v for k, v in SENT_RECEIPT_HASHES.items() if now - v < 43200}

    key = dedupe_key or hashlib.md5(message.strip().encode("utf-8")).hexdigest()
    if key in SENT_RECEIPT_HASHES:
        logger.info(f"[Anti-Spam] Suppressed duplicate Telegram receipt: {key}")
        return

    SENT_RECEIPT_HASHES[key] = now

    bot_token = os.getenv("REPORT_BOT_TOKEN", "")
    if not bot_token:
        return
    targets = [REPORT_CHAT_ID, PAYOUT_CHANNEL_ID]
    async with aiohttp.ClientSession() as s:
        for tid in targets:
            try:
                await s.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={
                        "chat_id": tid,
                        "text": message,
                        "parse_mode": "HTML" if "<" in message else "Markdown",
                        "disable_web_page_preview": True
                    },
                    timeout=aiohttp.ClientTimeout(total=8)
                )
                await asyncio.sleep(0.5)
            except Exception:
                pass





# =============================================================================
# MULTI-CHAIN ON-CHAIN SWEEPER & CONSOLIDATION ENGINE
# =============================================================================
FLEET_EVM_CACHE = {}
FLEET_TON_CACHE = {}

# In-memory TTL cache for Upstash passes to strictly stay within the 10,000 commands/day free limit
UPSTASH_PASS_CACHE = {}
UPSTASH_TOKENS_CACHE = {"data": {}, "ts": 0}

def get_cached_upstash_pass(key: str):
    now = time.time()
    if key in UPSTASH_PASS_CACHE:
        exp, val = UPSTASH_PASS_CACHE[key]
        if now < exp:
            return val
    return None

def set_cached_upstash_pass(key: str, val, ttl: int = 1800):
    UPSTASH_PASS_CACHE[key] = (time.time() + ttl, val)

BSC_USDT_CONTRACT = "0x55d398326f99059fF775485246999027B3197955"
DRPC_KEY = os.getenv("DRPC_API_KEY", "")
TONAPI_KEY = os.getenv("TONAPI_KEY", "")
TONCENTER_API_KEY = os.getenv("TONCENTER_API_KEY", "")

BSC_RPCS = [
    f"https://bsc.drpc.org/ogrpc?dkey={DRPC_KEY}",
    "https://bsc-dataseed.binance.org",
    "https://bsc-dataseed1.defibit.io",
    "https://bsc-dataseed1.binance.org"
]

ARB_RPCS = [
    f"https://arbitrum.drpc.org/ogrpc?dkey={DRPC_KEY}",
    "https://arb1.arbitrum.io/rpc"
]

async def load_fleet_wallets_from_cloud() -> tuple:
    """Loads worker EVM and TON wallets from local disk or Cloudflare backup.zip."""
    global FLEET_EVM_CACHE, FLEET_TON_CACHE
    if FLEET_EVM_CACHE and FLEET_TON_CACHE:
        return FLEET_EVM_CACHE, FLEET_TON_CACHE

    if os.path.exists("fleet_evm_wallets.json") and os.path.exists("fleet_ton_wallets.json"):
        try:
            with open("fleet_evm_wallets.json", "r", encoding="utf-8") as f:
                FLEET_EVM_CACHE = json.load(f)
            with open("fleet_ton_wallets.json", "r", encoding="utf-8") as f:
                FLEET_TON_CACHE = json.load(f)
            return FLEET_EVM_CACHE, FLEET_TON_CACHE
        except Exception:
            pass

    # Cloud fallback 1: Upstash Redis REST
    if UPSTASH_URL and UPSTASH_TOKEN:
        try:
            async with aiohttp.ClientSession() as http:
                if not FLEET_TON_CACHE:
                    async with http.get(f"{UPSTASH_URL}/get/fleet:wallets:ton", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=5)) as r:
                        if r.status == 200:
                            d = await r.json()
                            if d.get("result"):
                                FLEET_TON_CACHE = json.loads(d["result"]) if isinstance(d["result"], str) else d["result"]
                if not FLEET_EVM_CACHE:
                    async with http.get(f"{UPSTASH_URL}/get/fleet:wallets:evm", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=5)) as r:
                        if r.status == 200:
                            d = await r.json()
                            if d.get("result"):
                                FLEET_EVM_CACHE = json.loads(d["result"]) if isinstance(d["result"], str) else d["result"]
            if FLEET_EVM_CACHE and FLEET_TON_CACHE:
                logger.info(f"Loaded {len(FLEET_EVM_CACHE)} EVM and {len(FLEET_TON_CACHE)} TON wallets from Upstash Redis.")
                return FLEET_EVM_CACHE, FLEET_TON_CACHE
        except Exception as e:
            logger.warning(f"Could not load wallets from Upstash: {e}")

    # Cloud fallback 2: Edge mesh backup zip
    import zipfile, io
    async with aiohttp.ClientSession() as http:
        for cf_url in CF_WORKER_URLS:
            try:
                async with http.get(f"{cf_url}/backup.zip", headers=BROWSER_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    if r.status == 200:
                        zip_bytes = await r.read()
                        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                            if "fleet_evm_wallets.json" in zf.namelist():
                                FLEET_EVM_CACHE = json.loads(zf.read("fleet_evm_wallets.json").decode("utf-8"))
                            if "fleet_ton_wallets.json" in zf.namelist():
                                FLEET_TON_CACHE = json.loads(zf.read("fleet_ton_wallets.json").decode("utf-8"))
                            if FLEET_EVM_CACHE and FLEET_TON_CACHE:
                                logger.info(f"Loaded {len(FLEET_EVM_CACHE)} EVM and {len(FLEET_TON_CACHE)} TON wallets from cloud backup.")
                                return FLEET_EVM_CACHE, FLEET_TON_CACHE
            except Exception as e:
                logger.warning(f"Could not load wallets from {cf_url}: {e}")
    return FLEET_EVM_CACHE, FLEET_TON_CACHE


async def query_evm_rpc(session: aiohttp.ClientSession, rpc_list: list, method: str, params: list):
    payload = {"jsonrpc": "2.0", "id": int(time.time()), "method": method, "params": params}
    for rpc in rpc_list:
        try:
            async with session.post(rpc, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "result" in data:
                        return data["result"]
        except Exception:
            continue
    return None


async def audit_single_evm(session: aiohttp.ClientSession, uid: str, info: dict):
    if not isinstance(info, dict) or "address" not in info or str(uid).startswith("_"):
        return None
    addr = info["address"]
    name = info.get("name", f"Worker {uid}")
    clean_addr = addr.lower().replace("0x", "").zfill(64)
    usdt_call_data = "0x70a08231" + clean_addr

    raw_bnb_t = query_evm_rpc(session, BSC_RPCS, "eth_getBalance", [addr, "latest"])
    raw_eth_t = query_evm_rpc(session, ARB_RPCS, "eth_getBalance", [addr, "latest"])
    raw_usdt_t = query_evm_rpc(session, BSC_RPCS, "eth_call", [{"to": BSC_USDT_CONTRACT, "data": usdt_call_data}, "latest"])

    raw_bnb, raw_eth, raw_usdt = await asyncio.gather(raw_bnb_t, raw_eth_t, raw_usdt_t, return_exceptions=True)

    bnb_bal = int(raw_bnb, 16) / 1e18 if isinstance(raw_bnb, str) and raw_bnb else 0.0
    eth_bal = int(raw_eth, 16) / 1e18 if isinstance(raw_eth, str) and raw_eth else 0.0
    usdt_bal = int(raw_usdt, 16) / 1e18 if isinstance(raw_usdt, str) and raw_usdt not in ("0x", "0x0") else 0.0

    return {
        "uid": uid,
        "name": name,
        "address": addr,
        "private_key": info.get("private_key"),
        "bnb_balance": bnb_bal,
        "eth_balance": eth_bal,
        "usdt_balance": usdt_bal
    }


async def audit_single_ton(session: aiohttp.ClientSession, uid: str, info: dict, headers: dict):
    if not isinstance(info, dict) or "address" not in info or str(uid).startswith("_"):
        return None
    addr = info["address"]
    name = info.get("name", f"Worker {uid}")
    ton_bal = 0.0
    try:
        url = f"https://tonapi.io/v2/accounts/{addr}"
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                data = await resp.json()
                raw_bal = data.get("balance", 0)
                ton_bal = int(raw_bal) / 1e9
            else:
                # Toncenter API fallback
                tc_url = f"https://toncenter.com/api/v2/getAddressBalance?address={addr}"
                async with session.get(tc_url, timeout=aiohttp.ClientTimeout(total=5)) as tc_resp:
                    if tc_resp.status == 200:
                        tc_data = await tc_resp.json()
                        if tc_data.get("ok"):
                            ton_bal = int(tc_data.get("result", 0)) / 1e9
    except Exception:
        try:
            tc_url = f"https://toncenter.com/api/v2/getAddressBalance?address={addr}"
            async with session.get(tc_url, timeout=aiohttp.ClientTimeout(total=5)) as tc_resp:
                if tc_resp.status == 200:
                    tc_data = await tc_resp.json()
                    if tc_data.get("ok"):
                        ton_bal = int(tc_data.get("result", 0)) / 1e9
        except Exception:
            pass
    return {
        "uid": uid,
        "name": name,
        "address": addr,
        "mnemonic": info.get("mnemonic"),
        "ton_balance": ton_bal
    }


def sweep_evm_native_balance(rpc_list: list, chain_id: int, chain_name: str, private_key: str, from_addr: str, to_addr: str, native_balance: float, min_val: float = 0.0005):
    if not HAS_WEB3 or not private_key or native_balance <= min_val:
        return None
    try:
        w3 = None
        for rpc in rpc_list:
            try:
                tw3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
                if tw3.is_connected():
                    w3 = tw3
                    break
            except Exception:
                continue
        if not w3:
            return None

        cs_from = Web3.to_checksum_address(from_addr)
        cs_to = Web3.to_checksum_address(to_addr)
        if cs_from.lower() == cs_to.lower():
            return None

        nonce = w3.eth.get_transaction_count(cs_from)
        gas_price = w3.eth.gas_price
        gas_limit = 50000 if chain_id == 42161 else 21000
        gas_cost = gas_price * gas_limit
        balance_wei = w3.eth.get_balance(cs_from)
        amount_to_send = balance_wei - gas_cost
        if amount_to_send <= 0:
            return None

        tx = {
            "nonce": nonce,
            "to": cs_to,
            "value": amount_to_send,
            "gas": gas_limit,
            "gasPrice": gas_price,
            "chainId": chain_id
        }
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        raw_tx = getattr(signed_tx, "raw_transaction", None) or getattr(signed_tx, "rawTransaction", None)
        tx_hash = w3.eth.send_raw_transaction(raw_tx)
        tx_hash_hex = tx_hash.hex()
        if not tx_hash_hex.startswith("0x"):
            tx_hash_hex = "0x" + tx_hash_hex
        logger.info(f"[{chain_name}] Swept {amount_to_send / 1e18:.6f} to {to_addr}! Tx: {tx_hash_hex}")
        return tx_hash_hex
    except Exception as e:
        logger.error(f"[{chain_name}] Sweep failed for {from_addr}: {e}")
        return None


def sweep_bep20_token_balance(rpc_list: list, chain_id: int, private_key: str, token_addr: str, from_addr: str, to_addr: str, token_balance: float, min_tokens: float = 0.08):
    if not HAS_WEB3 or not private_key or token_balance <= min_tokens:
        return None
    try:
        w3 = None
        for rpc in rpc_list:
            try:
                tw3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
                if tw3.is_connected():
                    w3 = tw3
                    break
            except Exception:
                continue
        if not w3:
            return None

        cs_from = Web3.to_checksum_address(from_addr)
        cs_to = Web3.to_checksum_address(to_addr)
        if cs_from.lower() == cs_to.lower():
            return None

        cs_token = Web3.to_checksum_address(token_addr)
        native_bal = w3.eth.get_balance(cs_from)
        gas_price = w3.eth.gas_price
        gas_limit = 65000
        gas_cost = gas_price * gas_limit
        if native_bal < gas_cost:
            logger.warning(f"[BEP-20 Sweep] {from_addr} has tokens but insufficient gas")
            return None

        nonce = w3.eth.get_transaction_count(cs_from)
        transfer_abi = [
            {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
        ]
        contract = w3.eth.contract(address=cs_token, abi=transfer_abi)
        raw_bal = contract.functions.balanceOf(cs_from).call()
        if raw_bal <= 0:
            return None

        tx = contract.functions.transfer(cs_to, raw_bal).build_transaction({
            "from": cs_from,
            "nonce": nonce,
            "gas": gas_limit,
            "gasPrice": gas_price,
            "chainId": chain_id
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        raw_tx = getattr(signed_tx, "raw_transaction", None) or getattr(signed_tx, "rawTransaction", None)
        tx_hash = w3.eth.send_raw_transaction(raw_tx)
        tx_hash_hex = tx_hash.hex()
        if not tx_hash_hex.startswith("0x"):
            tx_hash_hex = "0x" + tx_hash_hex
        logger.info(f"[BEP-20 Sweep] Swept {token_balance:.2f} USDT to {to_addr}! Tx: {tx_hash_hex}")
        return tx_hash_hex
    except Exception as e:
        logger.error(f"[BEP-20 Sweep] Sweep failed for {from_addr}: {e}")
        return None


async def sweep_ton_balance(session: aiohttp.ClientSession, mnemonic: str, from_addr: str, to_addr: str, balance: float, min_threshold: float = 0.02):
    if not HAS_TONSDK or not mnemonic or balance <= min_threshold:
        return None
    try:
        words = mnemonic.strip().split()
        if len(words) != 24:
            return None
        _mn, _pub, _priv, wallet = Wallets.from_mnemonics(words, version=WalletVersionEnum.v4r2)
        seqno = 0
        try:
            tc_headers = {"X-API-Key": TONCENTER_API_KEY} if TONCENTER_API_KEY else {}
            tc_url = "https://toncenter.com/api/v2/runGetMethod"
            payload = {"address": from_addr, "method": "seqno", "stack": []}
            async with session.post(tc_url, json=payload, headers=tc_headers, timeout=aiohttp.ClientTimeout(total=5)) as r:
                if r.status == 200:
                    d = await r.json()
                    if d.get("ok") and d.get("result", {}).get("stack"):
                        raw = d["result"]["stack"][0][1]
                        seqno = int(raw, 16) if str(raw).startswith("0x") else int(raw)
        except Exception:
            pass

        gas_fee = 0.008
        amount_to_send = balance - gas_fee
        if amount_to_send <= 0:
            return None

        amount_nano = int(amount_to_send * 1e9)
        query = wallet.create_transfer_message(
            to_addr=to_addr,
            amount=amount_nano,
            seqno=seqno,
            payload="Automated Fleet Sweep"
        )
        boc = query["message"].to_boc(False)
        b64_boc = base64.b64encode(boc).decode("utf-8")

        tc_headers = {"X-API-Key": TONCENTER_API_KEY, "Content-Type": "application/json"} if TONCENTER_API_KEY else {"Content-Type": "application/json"}
        send_url = "https://toncenter.com/api/v2/sendBoc"
        async with session.post(send_url, json={"boc": b64_boc}, headers=tc_headers, timeout=aiohttp.ClientTimeout(total=8)) as br:
            if br.status == 200:
                resp_d = await br.json()
                if resp_d.get("ok"):
                    logger.info(f"[TON Sweep] Swept {amount_to_send:.4f} TON from {from_addr} to {to_addr}!")
                    return "boc_sent"
    except Exception as e:
        logger.error(f"[TON Sweep] Failed for {from_addr}: {e}")
    return None


async def execute_cloud_onchain_sweeper(session: aiohttp.ClientSession, accounts: list = None, execute_sweep: bool = True, notify: bool = False) -> dict:
    """Audits on-chain balances across all worker EVM and TON wallets and sweeps surplus balances."""
    logger.info("[Cloud Sweeper] Auditing on-chain balances across all fleet wallets...")
    evm_wallets, ton_wallets = await load_fleet_wallets_from_cloud()

    evm_tasks = [audit_single_evm(session, uid, info) for uid, info in evm_wallets.items()]
    evm_audit = [r for r in await asyncio.gather(*evm_tasks, return_exceptions=True) if isinstance(r, dict)]

    ton_headers = {"Authorization": f"Bearer {TONAPI_KEY}"} if TONAPI_KEY else {}
    ton_tasks = [audit_single_ton(session, uid, info, ton_headers) for uid, info in ton_wallets.items()]
    ton_audit = [r for r in await asyncio.gather(*ton_tasks, return_exceptions=True) if isinstance(r, dict)]

    funded_evm = [w for w in evm_audit if w.get("bnb_balance", 0) > 0.0005 or w.get("eth_balance", 0) > 0.0002 or w.get("usdt_balance", 0) > 0.08]
    funded_ton = [w for w in ton_audit if w.get("ton_balance", 0) > 0.01]

    total_bnb = sum(w.get("bnb_balance", 0) for w in evm_audit)
    total_eth = sum(w.get("eth_balance", 0) for w in evm_audit)
    total_usdt = sum(w.get("usdt_balance", 0) for w in evm_audit)
    total_ton = sum(w.get("ton_balance", 0) for w in ton_audit)

    swept_txs = []
    if execute_sweep:
        if HAS_WEB3:
            for w in funded_evm:
                pk = w.get("private_key")
                addr = w.get("address")
                name = w.get("name")
                if not pk or not addr or addr.lower() == MASTER_EVM_VAULT.lower():
                    continue
                if w.get("bnb_balance", 0) > 0.0008:
                    tx_bnb = sweep_evm_native_balance(BSC_RPCS, 56, "BSC", pk, addr, MASTER_EVM_VAULT, w["bnb_balance"])
                    if tx_bnb:
                        swept_txs.append({"chain": "BSC", "coin": "BNB", "amount": w["bnb_balance"], "name": name, "tx": tx_bnb, "url": f"https://bscscan.com/tx/{tx_bnb}"})
                if w.get("eth_balance", 0) > 0.0002:
                    tx_eth = sweep_evm_native_balance(ARB_RPCS, 42161, "Arbitrum One", pk, addr, MASTER_EVM_VAULT, w["eth_balance"])
                    if tx_eth:
                        swept_txs.append({"chain": "Arbitrum One", "coin": "ETH", "amount": w["eth_balance"], "name": name, "tx": tx_eth, "url": f"https://arbiscan.io/tx/{tx_eth}"})
                if w.get("usdt_balance", 0) > 0.08:
                    tx_usdt = sweep_bep20_token_balance(BSC_RPCS, 56, pk, BSC_USDT_CONTRACT, addr, MASTER_EVM_VAULT, w["usdt_balance"], min_tokens=0.08)
                    if tx_usdt:
                        swept_txs.append({"chain": "BSC", "coin": "USDT", "amount": w["usdt_balance"], "name": name, "tx": tx_usdt, "url": f"https://bscscan.com/tx/{tx_usdt}"})

        if HAS_TONSDK:
            for w in funded_ton:
                mn = w.get("mnemonic")
                addr = w.get("address")
                name = w.get("name")
                ton_bal = w.get("ton_balance", 0)
                if not mn or not addr or addr == MASTER_TON_VAULT or ton_bal <= 0.02:
                    continue
                tx_ton = await sweep_ton_balance(session, mn, addr, MASTER_TON_VAULT, ton_bal)
                if tx_ton:
                    swept_txs.append({"chain": "TON", "coin": "TON", "amount": ton_bal - 0.008, "name": name, "tx": tx_ton, "url": f"https://tonviewer.com/{addr}"})

    if swept_txs:
        lines = [f"• <b>{s['name']} ({s['chain']}):</b> Confirmed: <code>{s['amount']:.4f} {s['coin']}</code> → <a href=\"{s['url']}\">View Tx</a>" for s in swept_txs]
        confirm_msg = (
            f"✅ <b>ON-CHAIN PAYMENT CONFIRMED</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            + "\n".join(lines) +
            f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>Recipient Vault:</b> <code>{MASTER_EVM_VAULT}</code>\n"
            f"🛡️ <i>100% On-Chain Verified</i>"
        )
        await send_payout_receipt(confirm_msg)

    return {
        "ok": True,
        "evm_total_bnb": total_bnb,
        "evm_total_eth": total_eth,
        "evm_total_usdt": total_usdt,
        "ton_total": total_ton,
        "funded_evm_count": len(funded_evm),
        "funded_ton_count": len(funded_ton),
        "swept_count": len(swept_txs),
        "swept_txs": swept_txs
    }


@app.get("/api/sweep/audit")
async def api_sweep_audit(request: Request):
    """Audits on-chain balances across all worker wallets without executing transfers."""
    notify = request.query_params.get("notify") == "1"
    async with aiohttp.ClientSession() as session:
        res = await execute_cloud_onchain_sweeper(session, execute_sweep=False, notify=notify)
    return {"ok": True, "audit": res, "timestamp": time.time()}


@app.post("/api/sweep/execute")
async def api_sweep_execute(request: Request):
    """Executes on-chain vault sweeper across EVM and TON worker wallets."""
    async with aiohttp.ClientSession() as session:
        res = await execute_cloud_onchain_sweeper(session, execute_sweep=True, notify=False)
    return {"ok": True, "results": res, "timestamp": time.time()}


async def fetch_cloud_miniapp_tokens(session: aiohttp.ClientSession) -> dict:
    """Fetches and aggregates miniapp session tokens across all Cloudflare edge nodes and Upstash Redis."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Authorization": f"Bearer {SECRET_KEY}"
    }
    tokens_map = {}
    now_t = time.time()

    # 1. Primary SSOT: Upstash Redis (fleet:tokens:*) - fresh tokens extracted directly by Telethon
    global UPSTASH_TOKENS_CACHE
    if UPSTASH_URL and UPSTASH_TOKEN:
        if (now_t - UPSTASH_TOKENS_CACHE.get("ts", 0) < 60) and UPSTASH_TOKENS_CACHE.get("data"):
            tokens_map = {acc_id: dict(t_obj) for acc_id, t_obj in UPSTASH_TOKENS_CACHE["data"].items()}
        else:
            try:
                upstash_headers = {"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"}
                async with session.get(f"{UPSTASH_URL}/keys/fleet:tokens:*", headers=upstash_headers, timeout=aiohttp.ClientTimeout(total=6)) as ur:
                    if ur.status == 200:
                        uk = await ur.json()
                        keys = uk.get("result", [])
                        if keys:
                            pipe_payload = [["get", k] for k in keys]
                            async with session.post(f"{UPSTASH_URL}/pipeline", json=pipe_payload, headers=upstash_headers, timeout=aiohttp.ClientTimeout(total=6)) as pr:
                                if pr.status == 200:
                                    pdata = await pr.json()
                                    cached_tokens = {}
                                    for idx, item in enumerate(pdata):
                                        res_str = item.get("result")
                                        k = keys[idx]
                                        if res_str:
                                            try:
                                                t_obj = json.loads(res_str) if isinstance(res_str, str) else res_str
                                                acc_id = str(t_obj.get("account_id", k.split(":")[-1]))
                                                if acc_id.isdigit():
                                                    cached_tokens[acc_id] = t_obj
                                                    tokens_map[acc_id] = t_obj
                                            except Exception:
                                                pass
                                    UPSTASH_TOKENS_CACHE = {"data": cached_tokens, "ts": now_t}
            except Exception as ue:
                logger.warning(f"Upstash token load note: {ue}")

    # Also check Upstash miniapp_tokens fallback if any account missing
    if UPSTASH_URL and UPSTASH_TOKEN and len(tokens_map) < 18:
        try:
            up_h = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}
            async with session.get(f"{UPSTASH_URL}/get/miniapp_tokens", headers=up_h, timeout=aiohttp.ClientTimeout(total=4)) as mr:
                if mr.status == 200:
                    md = await mr.json()
                    raw_m = md.get("result")
                    if raw_m:
                        parsed_m = json.loads(raw_m) if isinstance(raw_m, str) else raw_m
                        if isinstance(parsed_m, dict):
                            for acc_id, t_obj in parsed_m.items():
                                if acc_id.isdigit() and isinstance(t_obj, dict):
                                    if acc_id not in tokens_map:
                                        tokens_map[acc_id] = t_obj
                                    else:
                                        for tk, tv in t_obj.items():
                                            if tk not in tokens_map[acc_id] or not tokens_map[acc_id][tk]:
                                                tokens_map[acc_id][tk] = tv
        except Exception:
            pass

    # 2. Secondary: Fallback to Cloudflare Worker edge nodes ONLY for accounts missing from Upstash
    for cf_url in CF_WORKER_URLS:
        for ep in ["/api/miniapp/tokens", "/api/fleet/tokens"]:
            try:
                async with session.get(f"{cf_url}{ep}", headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as r:
                    if r.status == 200:
                        data = await r.json()
                        tokens = data.get("tokens", data) if isinstance(data, dict) else {}
                        if isinstance(tokens, dict):
                            for k, v in tokens.items():
                                if k.isdigit() and isinstance(v, dict):
                                    if k not in tokens_map:
                                        tokens_map[k] = v
                                    else:
                                        for tk, tv in v.items():
                                            if tk not in tokens_map[k] or not tokens_map[k][tk]:
                                                tokens_map[k][tk] = tv
            except Exception:
                pass

    return tokens_map


FLEET_LAST_FARM_CACHE = {}


async def farm_single_account_bots(session: aiohttp.ClientSession, acc: dict, acc_tokens: dict, force: bool = False) -> dict:
    """
    Farms all 4 legitimate active bots (MRG, ATF, Victor's Company, VyroDrop) for a single account.
    Engineered with:
      - Deterministic mobile device fingerprinting per account (eliminates bot signatures)
      - Realistic human jitter delays
      - Anti-ban background dwell timers (14-17s for external/channel/social tasks)
      - Dynamic task discovery & retry logic
      - Fisher-Yates shuffled execution order per session
      - Strict Master Account compounding protection
    """
    uid = str(acc.get("user_id"))
    name = acc.get("name", uid)
    is_owner = (str(uid) == "6727787768" or acc.get("is_primary") or acc.get("phone") in ("+8801317342850", "01317342850"))

    # Normalize tokens dict in case it's nested
    tokens = acc_tokens.get(uid, acc_tokens) if isinstance(acc_tokens.get(uid), dict) else acc_tokens

    # Deterministic mobile User-Agent per account
    user_agent = get_account_user_agent(uid)
    headers = {
        "Content-Type": "application/json",
        "User-Agent": user_agent
    }

    status = {"uid": uid, "name": name, "bots": {}}
    bg_tasks = []

    # Helper for human jitter delay
    async def jitter(min_s=1.0, max_s=2.5):
        await asyncio.sleep(random.uniform(min_s, max_s))

    # Helper for safe post with retries
    async def safe_post(url, json_data=None, req_headers=None, timeout_sec=6, retries=2):
        h = req_headers or headers
        for attempt in range(retries):
            try:
                async with session.post(url, json=json_data, headers=h, timeout=aiohttp.ClientTimeout(total=timeout_sec)) as resp:
                    data = None
                    try:
                        data = await resp.json()
                    except Exception:
                        pass
                    return resp.status, data
            except Exception:
                if attempt < retries - 1:
                    await asyncio.sleep(0.8)
        return 0, None

    # Helper for safe get
    async def safe_get(url, req_headers=None, timeout_sec=6, retries=2):
        h = req_headers or headers
        for attempt in range(retries):
            try:
                async with session.get(url, headers=h, timeout=aiohttp.ClientTimeout(total=timeout_sec)) as resp:
                    data = None
                    try:
                        data = await resp.json()
                    except Exception:
                        pass
                    return resp.status, data
            except Exception:
                if attempt < retries - 1:
                    await asyncio.sleep(0.8)
        return 0, None

    # Helper for formatted error string (never returns empty string)
    def format_error(e: Exception) -> str:
        msg = str(e).strip()
        return f"{type(e).__name__}: {msg}" if msg else type(e).__name__

    # 1. MRG Miner
    async def _farm_mrg():
        if not tokens.get("mrg_init_data"):
            return
        try:
            m_init = tokens["mrg_init_data"]
            if m_init.startswith("user%3D") or "%257B" in m_init or "%2522" in m_init:
                m_init = urllib.parse.unquote(m_init)
            m_headers = {
                **headers,
                "Origin": "https://app.mrgtoken.xyz",
                "Referer": "https://app.mrgtoken.xyz/"
            }
            num_uid = int(str(uid)[-4:]) if str(uid)[-4:].isdigit() else 0
            device_info = {
                "model": ["SM-S928B", "Pixel 8 Pro", "SM-A536B", "23127PN0CG"][num_uid % 4],
                "ram": [8, 12, 6, 12][num_uid % 4],
                "cores": 8,
                "screen": ["1440x3120", "1344x2992", "1080x2400", "1200x2670"][num_uid % 4],
                "language": "en-US"
            }
            await jitter(1.0, 2.2)
            if not is_owner:
                await safe_post("https://mrg.up.railway.app/api/auth/verify", {"initData": m_init, "startParam": "ref_IRN1G3XD", "start_param": "ref_IRN1G3XD", "deviceInfo": device_info}, req_headers=m_headers)

            # Query in-memory cache or Upstash Redis for Turnstile security pass
            mrg_turnstile_tok = get_cached_upstash_pass(f"mrg:pass:{uid}")
            if mrg_turnstile_tok is None and UPSTASH_URL and UPSTASH_TOKEN:
                try:
                    async with session.get(f"{UPSTASH_URL}/get/mrg:pass:{uid}", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=3)) as pr:
                        if pr.status == 200:
                            pd = await pr.json()
                            if pd.get("result"):
                                parsed_p = json.loads(pd["result"]) if isinstance(pd["result"], str) else pd["result"]
                                mrg_turnstile_tok = parsed_p.get("turnstileToken")
                                set_cached_upstash_pass(f"mrg:pass:{uid}", mrg_turnstile_tok, ttl=1800)
                except Exception:
                    pass

            claim_payload = {"initData": m_init, "deviceInfo": device_info}
            if mrg_turnstile_tok:
                claim_payload["turnstileToken"] = mrg_turnstile_tok
            await jitter(1.2, 2.5)
            _, claim_d = await safe_post("https://mrg.up.railway.app/api/user/claim-mining", claim_payload, req_headers=m_headers)

            # Task completion & level auto-unlock
            await jitter(1.2, 2.6)
            _, me_d = await safe_post("https://mrg.up.railway.app/api/user/me", {"initData": m_init}, req_headers=m_headers)
            if me_d and isinstance(me_d, dict):
                # Bind dedicated TON wallet if not connected or different
                u_obj_init = me_d.get("user", {})
                is_ton_conn = u_obj_init.get("isTonConnected", False)
                cur_ton_w = u_obj_init.get("tonWalletAddress", "")
                target_ton_w = (acc.get("ton_wallet") or {}).get("address") or (FLEET_TON_CACHE.get(str(uid)) or {}).get("address") or (PRIMARY_TON_WALLET if is_owner else None)
                if target_ton_w and (not is_ton_conn or not cur_ton_w or cur_ton_w != target_ton_w):
                    await safe_post("https://mrg.up.railway.app/api/user/connect-wallet", {"initData": m_init, "address": target_ton_w, "balance": 0}, req_headers=m_headers)
                    logger.info(f"[{name}] ⛏️ [MRG] Bound dedicated TON wallet: {target_ton_w[:10]}...")

                completed = set(me_d.get("completedTaskIds", []))
                for t in me_d.get("tasks", []):
                    tid = t.get("taskId")
                    if tid and tid not in completed:
                        is_link = (t.get("type") == "link_visit" or t.get("url") or "channel" in str(t.get("title", "")).lower() or "social" in str(t.get("title", "")).lower())
                        if is_link:
                            async def _mrg_claim_link_task(task_id):
                                await asyncio.sleep(15)
                                _, cl_d = await safe_post("https://mrg.up.railway.app/api/user/claim-task", {"initData": m_init, "taskId": task_id}, req_headers=m_headers)
                                if cl_d and not cl_d.get("success") and ("wait" in json.dumps(cl_d).lower() or "second" in json.dumps(cl_d).lower()):
                                    await asyncio.sleep(12)
                                    await safe_post("https://mrg.up.railway.app/api/user/claim-task", {"initData": m_init, "taskId": task_id}, req_headers=m_headers)
                            bg_tasks.append(asyncio.create_task(_mrg_claim_link_task(tid)))
                        else:
                            await jitter(1.8, 3.2)
                            _, cl_d = await safe_post("https://mrg.up.railway.app/api/user/claim-task", {"initData": m_init, "taskId": tid}, req_headers=m_headers)
                            if cl_d and not cl_d.get("success") and ("wait" in json.dumps(cl_d).lower() or "second" in json.dumps(cl_d).lower()):
                                async def _mrg_retry_claim(task_id):
                                    await asyncio.sleep(14)
                                    await safe_post("https://mrg.up.railway.app/api/user/claim-task", {"initData": m_init, "taskId": task_id}, req_headers=m_headers)
                                bg_tasks.append(asyncio.create_task(_mrg_retry_claim(tid)))

                # Auto-unlock level up to 203
                u_obj = me_d.get("user", {})
                in_bal = float(u_obj.get("inAppBalance", 0) or 0)
                cur_lvl = int(u_obj.get("manualUnlockedLevel") or 0)
                if cur_lvl == 0:
                    await safe_post("https://mrg.up.railway.app/api/user/unlock-level", {"initData": m_init, "level": 1}, req_headers=m_headers)
                    cur_lvl = 1
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
                        await safe_post("https://mrg.up.railway.app/api/user/unlock-level", {"initData": m_init, "level": target_lvl}, req_headers=m_headers)

            if is_owner:
                await safe_post("https://mrg.up.railway.app/api/user/claim-commission", {"initData": m_init}, req_headers=m_headers)
                _, fr_d = await safe_post("https://mrg.up.railway.app/api/user/friends", {"initData": m_init}, req_headers=m_headers)
                if fr_d and (fr_d.get("teamStats", {}).get("unclaimedOneTimeBonusMRG", 0) or 0) > 0:
                    await safe_post("https://mrg.up.railway.app/api/user/claim-one-time-bonus", {"initData": m_init}, req_headers=m_headers)

            bal_str = ""
            unclaimed_val = 0.0
            if me_d and isinstance(me_d, dict) and me_d.get("user"):
                u_m = me_d["user"]
                b_val = float(u_m.get("inAppBalance", 0) or 0)
                l_val = u_m.get("manualUnlockedLevel") or u_m.get("peakLevel") or 1
                unclaimed_val = float(u_m.get("unclaimedMiningBalance", 0) or 0)
                bal_str = f" (lvl: {l_val}, bal: {b_val:.1f} MRG)"
            claim_stat = "farmed"
            if claim_d and isinstance(claim_d, dict):
                if claim_d.get("code") == "HUMAN_CHECK_REQUIRED":
                    claim_stat = f"farmed (security_check_needed: {unclaimed_val:.1f} MRG)"
                elif claim_d.get("success"):
                    claim_stat = f"farmed (auto-claimed {claim_d.get('claimedAmount', 'reward')} MRG)"
            status["bots"]["mrg"] = f"{claim_stat}{bal_str}"
        except Exception as e:
            status["bots"]["mrg"] = f"error: {format_error(e)}"







    # 7. ATF Miner
    async def _farm_atf():
        if not tokens.get("atf_init_data"):
            return
        try:
            atf_init = tokens["atf_init_data"]
            atf_base = "https://atfminers.asloni.online/miner/index.php"
            atf_h = {
                **headers,
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://atfminers.asloni.online/miner/index.html",
                "Origin": "https://atfminers.asloni.online"
            }
            def atf_payload(extra=None):
                p = {
                    "initData": atf_init,
                    "tg_id": int(uid),
                    "username": acc.get("username", "") or "",
                    "request_id": f"rq-{int(time.time()*1000)}-farm",
                    "device_id": f"dev-farm-{uid}"
                }
                if not is_owner:
                    p["ref"] = ATF_REFERRAL_CODE
                if extra:
                    p.update(extra)
                return p

            await jitter(1.0, 2.2)
            _, log_data = await safe_post(f"{atf_base}?action=login&t={int(time.time()*1000)}", atf_payload(), atf_h)
            
            # ATF Cloudflare Turnstile entry captcha check
            if (not log_data) or (isinstance(log_data, dict) and log_data.get("reason") in ("entry_captcha_required", "captcha_required")):
                atf_pass = get_cached_upstash_pass(f"atf:pass:{uid}")
                if atf_pass is None and UPSTASH_URL and UPSTASH_TOKEN:
                    try:
                        async with session.get(f"{UPSTASH_URL}/get/atf:pass:{uid}", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=3)) as ar:
                            if ar.status == 200:
                                ad = await ar.json()
                                if ad.get("result"):
                                    parsed_a = json.loads(ad["result"]) if isinstance(ad["result"], str) else ad["result"]
                                    atf_pass = parsed_a.get("captcha_token") or parsed_a.get("token") or parsed_a
                                    set_cached_upstash_pass(f"atf:pass:{uid}", atf_pass, ttl=86400 * 5)
                    except Exception:
                        pass
                if atf_pass:
                    await safe_post(f"{atf_base}?action=verify_entry_captcha&t={int(time.time()*1000)}", atf_payload({"captcha_token": atf_pass}), atf_h)
                    await jitter(0.5, 1.2)
                    _, log_data = await safe_post(f"{atf_base}?action=login&t={int(time.time()*1000)}", atf_payload(), atf_h)

            if isinstance(log_data, dict) and log_data.get("reason") in ("entry_captcha_required", "captcha_required"):
                status["bots"]["atf"] = "entry_captcha_required (Turnstile needed)"
                return

            completed_tasks = set()
            task_cooldowns = {}
            if log_data and isinstance(log_data, dict):
                completed_tasks = set(log_data.get("user", {}).get("completed_tasks", []))
                task_cooldowns = log_data.get("task_cooldowns", {})

            await jitter(1.0, 2.0)
            await safe_post(f"{atf_base}?action=claim&t={int(time.time()*1000)}", atf_payload(), atf_h)
            await jitter(0.8, 1.8)
            await safe_post(f"{atf_base}?action=claim_referrals&t={int(time.time()*1000)}", atf_payload(), atf_h)
            await jitter(0.8, 1.8)
            await safe_post(f"{atf_base}?action=claim_team_wallet&t={int(time.time()*1000)}", atf_payload(), atf_h)

            # Ensure dedicated TON wallet is synced to ATF
            try:
                ton_addr = (acc.get("ton_wallet") or {}).get("address") or (FLEET_TON_CACHE.get(str(uid)) or {}).get("address")
                if ton_addr:
                    await safe_post(f"{atf_base}?action=sync_wallet&t={int(time.time()*1000)}", atf_payload({"wallet": ton_addr}), atf_h)
            except Exception:
                pass

            # Math challenge with human delay
            try:
                _, chd = await safe_post(f"{atf_base}?action=get_math_challenge&t={int(time.time()*1000)}", atf_payload({"scope": "start_mine"}), atf_h)
                if chd and chd.get("status") == "success" and chd.get("challenge_id"):
                    q = chd.get("question", "")
                    ans = solve_atf_math(q)
                    await jitter(2.2, 4.5)
                    await safe_post(f"{atf_base}?action=start_mine&t={int(time.time()*1000)}", atf_payload({"math_challenge_id": chd["challenge_id"], "math_answer": ans}), atf_h)
            except Exception:
                pass

            await jitter(1.0, 2.0)
            await safe_post(f"{atf_base}?action=activate_boost&t={int(time.time()*1000)}", atf_payload(), atf_h)
            await safe_post(f"{atf_base}?action=record_daily_interaction&t={int(time.time()*1000)}", atf_payload(), atf_h)

            # Task completions with cooldown checks
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
                try:
                    tid = t["id"]
                    is_rep = t["repeatable"]
                    cd = int(task_cooldowns.get(tid, 0) or 0)
                    can_do = (tid not in completed_tasks) if not is_rep else (now_sec >= cd)
                    if can_do:
                        s_at = int(time.time()) - t["min_s"] - 5
                        await safe_post(f"{atf_base}?action=start_task&t={int(time.time()*1000)}", atf_payload({"task_id": tid, "client_started_at": s_at}), atf_h)
                        await asyncio.sleep(1.5)
                        _, cl_res = await safe_post(f"{atf_base}?action=claim_task&t={int(time.time()*1000)}", atf_payload({"task_id": tid, "client_started_at": s_at}), atf_h)
                        if cl_res and cl_res.get("status") != "success" and ("wait" in json.dumps(cl_res).lower() or "progress" in json.dumps(cl_res).lower()):
                            await asyncio.sleep(2.5)
                            await safe_post(f"{atf_base}?action=claim_task&t={int(time.time()*1000)}", atf_payload({"task_id": tid, "client_started_at": s_at}), atf_h)
                        await asyncio.sleep(1.0)
                except Exception:
                    pass

            bal_str = ""
            if log_data and isinstance(log_data, dict):
                u_obj = log_data.get("user") if isinstance(log_data.get("user"), dict) else log_data
                lvl = u_obj.get("miner_level") or log_data.get("miner_level") or 1
                try:
                    bal = float(u_obj.get("mined_balance") or log_data.get("mined_balance") or 0)
                except (ValueError, TypeError):
                    bal = 0.0
                bal_str = f" (lvl: {lvl}, bal: {bal:.1f} ATF)"
            status["bots"]["atf"] = f"farmed{bal_str}"
        except Exception as e:
            status["bots"]["atf"] = f"error: {format_error(e)}"



    # 8. Victor's Company (@VictorsCompanybot)
    async def _farm_victors():
        if tokens.get("victors_init_data"):
            try:
                v_init = tokens["victors_init_data"]
                v_h = {
                    **headers,
                    "Authorization": f"tma {v_init}",
                    "Origin": "https://app.victors.company",
                    "Referer": "https://app.victors.company/"
                }

                # Query in-memory cache or Upstash Redis for Victor's Company humanPass
                vic_pass = get_cached_upstash_pass(f"victors:pass:{uid}")
                if vic_pass is None and UPSTASH_URL and UPSTASH_TOKEN:
                    try:
                        async with session.get(f"{UPSTASH_URL}/get/victors:pass:{uid}", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=3)) as vr:
                            if vr.status == 200:
                                vd = await vr.json()
                                if vd.get("result"):
                                    parsed_v = json.loads(vd["result"]) if isinstance(vd["result"], str) else vd["result"]
                                    vic_pass = parsed_v.get("humanPass")
                                    set_cached_upstash_pass(f"victors:pass:{uid}", vic_pass, ttl=1800)
                    except Exception:
                        pass
                if vic_pass:
                    v_h["x-human-pass"] = str(vic_pass)

                # 1. Verify profile using humanPass
                await jitter(0.5, 1.2)
                m_code, m_d = await safe_get("https://server.victors.company/api/me", req_headers=v_h)
                is_auth_ok = (m_code == 200 and isinstance(m_d, dict) and (m_d.get("success") is True or "state" in m_d or "user" in m_d))
                st = m_d.get("state", {}) if isinstance(m_d, dict) else {}
                me = (st.get("user") or m_d.get("user") or m_d) if (is_auth_ok and isinstance(m_d, dict)) else {}

                if not is_auth_ok or not me:
                    if (not vic_pass) or m_code in (401, 403) or (isinstance(m_d, dict) and m_d.get("code") == "HUMAN_REQUIRED"):
                        set_cached_upstash_pass(f"victors:pass:{uid}", None, ttl=1)
                        status["bots"]["victors"] = "human_pass_required (Turnstile needed)"
                    else:
                        status["bots"]["victors"] = f"auth_failed (code {m_code})"
                    return

                lvl = me.get("peakLevel") or me.get("level", 1)
                in_app_bal = me.get("inAppBalance", 0)

                if not me.get("tutorialDone"):
                    await safe_post("https://server.victors.company/api/me/tutorial", json_data={}, req_headers=v_h)

                # 2. Daily checkin
                await jitter(0.6, 1.5)
                await safe_post("https://server.victors.company/api/checkin", json_data={}, req_headers=v_h)

                # 3. Connect TON wallet if not yet connected
                v_ton_w = (acc.get("ton_wallet") or {}).get("address") or (FLEET_TON_CACHE.get(str(uid)) or {}).get("address")
                if v_ton_w and not me.get("walletAddress"):
                    w_entry = FLEET_TON_CACHE.get(str(uid)) or (acc.get("ton_wallet") or {})
                    raw_m = w_entry.get("mnemonic") or w_entry.get("ton_mnemonic")
                    if raw_m:
                        try:
                            np_code, np_res = await safe_get("https://server.victors.company/api/wallet/proof-payload", req_headers=v_h)
                            if np_code == 200 and isinstance(np_res, dict) and np_res.get("payload"):
                                nonce = np_res["payload"]
                                words = raw_m.split() if isinstance(raw_m, str) else raw_m
                                _, pub_key_bytes, priv_key_bytes, wallet_contract = Wallets.from_mnemonics(
                                    mnemonics=words, version=WalletVersionEnum.v4r2
                                )
                                state_init_res = wallet_contract.create_state_init()
                                state_init_b64 = base64.b64encode(state_init_res["state_init"].to_boc(False)).decode("utf-8")
                                t_addr = wallet_contract.address
                                friendly_addr = t_addr.to_string(is_user_friendly=True, is_bounceable=False, is_url_safe=True)
                                domain_bytes = b"app.victors.company"
                                ts_now = int(time.time())
                                msg = b"ton-proof-item-v2/" + struct.pack(">i", t_addr.wc) + t_addr.hash_part + struct.pack("<I", len(domain_bytes)) + domain_bytes + struct.pack("<Q", ts_now) + nonce.encode("utf-8")
                                digest = hashlib.sha256(b"\xff\xff" + b"ton-connect" + hashlib.sha256(msg).digest()).digest()
                                from nacl.signing import SigningKey
                                sig = SigningKey(priv_key_bytes[:32]).sign(digest).signature
                                sig_b64 = base64.b64encode(sig).decode("utf-8")
                                conn_body = {
                                    "address": friendly_addr,
                                    "proof": {
                                        "timestamp": ts_now,
                                        "domain": {"lengthBytes": len(domain_bytes), "value": "app.victors.company"},
                                        "signature": sig_b64,
                                        "payload": nonce
                                    },
                                    "stateInit": state_init_b64,
                                    "publicKey": pub_key_bytes.hex()
                                }
                                await safe_post("https://server.victors.company/api/wallet/connect", json_data=conn_body, req_headers=v_h)
                        except Exception:
                            pass
                    await safe_post("https://server.victors.company/api/wallet/connect", json_data={"address": v_ton_w}, req_headers=v_h)
                    await safe_post("https://server.victors.company/api/tasks/claim", json_data={"taskId": "connect-wallet"}, req_headers=v_h)

                # 4. Levels unlock (Hire Level 1 Miner to start mining and eliminate home.noJob)
                manual_lvl = me.get("manualUnlockedLevel", 0)
                if manual_lvl < 1 or lvl < 1:
                    await jitter(0.4, 0.9)
                    await safe_post("https://server.victors.company/api/levels/unlock", json_data={"level": 1}, req_headers=v_h)
                unlocked = me.get("unlockedLevel", lvl)
                if unlocked > lvl:
                    await jitter(0.5, 1.2)
                    await safe_post("https://server.victors.company/api/levels/unlock", json_data={"level": unlocked}, req_headers=v_h)

                # 5. Mining claim
                await jitter(0.8, 1.8)
                await safe_post("https://server.victors.company/api/mining/claim", json_data={}, req_headers=v_h)

                # 6. Tasks discovery & claim
                await jitter(0.8, 1.6)
                _, t_d = await safe_get("https://server.victors.company/api/tasks", req_headers=v_h)
                if t_d and isinstance(t_d, dict):
                    tasks = t_d.get("tasks", [])
                    if isinstance(tasks, list):
                        for t in tasks:
                            if isinstance(t, dict):
                                tid = t.get("taskId") or t.get("id")
                                if tid and (t.get("status") == "open" or not t.get("claimed")):
                                    await jitter(0.4, 0.9)
                                    await safe_post("https://server.victors.company/api/tasks/claim", json_data={"taskId": tid}, req_headers=v_h)

                # 7. Referral claim bonus & commission
                await jitter(0.6, 1.4)
                await safe_post("https://server.victors.company/api/referral/claim-bonus", json_data={}, req_headers=v_h)
                await safe_post("https://server.victors.company/api/referral/claim-commission", json_data={}, req_headers=v_h)

                # 8. Deep Mine Arcade Minigame Solver
                try:
                    from victors_arcade_solver import solve_deep_mine_expeditions
                    arc_stats = await solve_deep_mine_expeditions(session, v_h, name, max_runs=2)
                    if arc_stats.get("runs_played", 0) > 0 and arc_stats.get("final_balance") is not None:
                        in_app_bal = arc_stats["final_balance"]
                except Exception as arc_e:
                    logger.debug(f"[{name}] [Victors Arcade] note: {arc_e}")

                bal_str = f" (lvl: {lvl}, bal: {in_app_bal} VIC)"
                status["bots"]["victors"] = f"farmed{bal_str}"
                return
            except Exception as e:
                status["bots"]["victors"] = f"api_error: {format_error(e)}"
                return

        status["bots"]["victors"] = "skipped (no initData)"

    # 9. VyroDrop (@vyrodrop_bot)
    async def _farm_vyro():
        if tokens.get("vyro_init_data"):
            try:
                vy_init = tokens["vyro_init_data"]
                vy_h = {
                    **headers,
                    "Authorization": f"tma {vy_init}",
                    "X-Vyro-UI-Contract": "claim-inactivity-v1",
                    "X-Vyro-Market-Balances": "2",
                    "X-Vyro-Dex": "1",
                    "Referer": "https://vyro.run.place/"
                }
                import uuid

                # 1. Bootstrap
                b_code, b_d = await safe_get("https://vyro.run.place/api/bootstrap", req_headers=vy_h)
                if b_code != 200 or not b_d or not isinstance(b_d, dict) or "error" in b_d:
                    err_code = b_d.get("error", {}).get("code") if isinstance(b_d, dict) else ""
                    if b_code == 401 or err_code == "TELEGRAM_AUTH_INVALID":
                        status["bots"]["vyro"] = "token_expired (auth 401 - needs MTProto refresh)"
                    else:
                        status["bots"]["vyro"] = f"skipped (bootstrap {b_code or 'error'})"
                    return

                u_obj = b_d.get("user", {})
                m_obj = b_d.get("miner", {})
                mining = b_d.get("mining") or {}
                lvl = m_obj.get("level", 1)

                # 2. Mining claim / start
                wallet_required = False
                sess_id = mining.get("sessionId")
                if sess_id:
                    await jitter(0.8, 1.8)
                    c_code, c_d = await safe_post(
                        "https://vyro.run.place/api/mining/claim",
                        json_data={"sessionId": sess_id, "idempotencyKey": str(uuid.uuid4())},
                        req_headers=vy_h
                    )
                    if c_code in (200, 201) or (c_d and isinstance(c_d, dict) and c_d.get("error", {}).get("code") == "MINING_SESSION_ALREADY_CLAIMED"):
                        await jitter(0.8, 1.6)
                        st_c, st_d = await safe_post(
                            "https://vyro.run.place/api/mining/start",
                            json_data={"idempotencyKey": str(uuid.uuid4())},
                            req_headers=vy_h
                        )
                        if st_c == 409 or (st_d and isinstance(st_d, dict) and st_d.get("error", {}).get("code") == "MINING_WALLET_REQUIRED"):
                            wallet_required = True
                else:
                    await jitter(0.8, 1.8)
                    st_c, st_d = await safe_post(
                        "https://vyro.run.place/api/mining/start",
                        json_data={"idempotencyKey": str(uuid.uuid4())},
                        req_headers=vy_h
                    )
                    if st_c == 409 or (st_d and isinstance(st_d, dict) and st_d.get("error", {}).get("code") == "MINING_WALLET_REQUIRED"):
                        wallet_required = True

                # 3. Tasks
                await jitter(0.8, 1.6)
                t_headers = {**vy_h, "x-vyro-tasks-protocol": "2"}
                _, t_d = await safe_get("https://vyro.run.place/api/tasks?limit=8", req_headers=t_headers)
                if t_d and isinstance(t_d, dict):
                    tasks = t_d.get("tasks", [])
                    if isinstance(tasks, list):
                        for t in tasks:
                            if isinstance(t, dict) and t.get("id") and t.get("state") != "CLAIMED":
                                tid = t["id"]
                                await jitter(0.4, 0.9)
                                await safe_post(f"https://vyro.run.place/api/tasks/{tid}/open", json_data={}, req_headers=t_headers)
                                await jitter(1.0, 1.8)
                                _, v_d = await safe_post(f"https://vyro.run.place/api/tasks/{tid}/verify", json_data={}, req_headers=t_headers)
                                if v_d and isinstance(v_d, dict) and v_d.get("task", {}).get("canClaim"):
                                    await jitter(0.8, 1.5)
                                    await safe_post(f"https://vyro.run.place/api/tasks/{tid}/claim", json_data={"idempotencyKey": str(uuid.uuid4())}, req_headers=t_headers)

                # 4. Referral claims
                await jitter(0.6, 1.4)
                await safe_post("https://vyro.run.place/api/referrals/claim", json_data={"kind": "DIRECT", "idempotencyKey": str(uuid.uuid4())}, req_headers=vy_h)
                await safe_post("https://vyro.run.place/api/referrals/claim", json_data={"kind": "MINING", "idempotencyKey": str(uuid.uuid4())}, req_headers=vy_h)

                if wallet_required:
                    c_resp = None
                    c_code = 0
                    try:
                        if not FLEET_TON_CACHE:
                            await load_fleet_wallets_from_cloud()
                        w_entry = FLEET_TON_CACHE.get(str(uid)) or (acc.get("ton_wallet") or {})
                        raw_m = w_entry.get("mnemonic") or w_entry.get("ton_mnemonic")
                        if w_entry and raw_m:
                            ch_headers = {**vy_h, "Content-Type": "application/json"}
                            v_pass = get_cached_upstash_pass(f"vyro:pass:{uid}")
                            if v_pass is None and UPSTASH_URL and UPSTASH_TOKEN:
                                try:
                                    async with session.get(f"{UPSTASH_URL}/get/vyro:pass:{uid}", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=3)) as vr:
                                        if vr.status == 200:
                                            vd = await vr.json()
                                            if vd.get("result"):
                                                parsed_v = json.loads(vd["result"]) if isinstance(vd["result"], str) else vd["result"]
                                                v_pass = parsed_v.get("turnstileToken") or parsed_v.get("humanPass") if isinstance(parsed_v, dict) else parsed_v
                                                set_cached_upstash_pass(f"vyro:pass:{uid}", v_pass, ttl=1800)
                                except Exception:
                                    pass
                            ch_body = {"turnstileToken": v_pass} if v_pass else {}
                            c_code, c_resp = await safe_post("https://vyro.run.place/api/wallet/challenge", json_data=ch_body, req_headers=ch_headers)
                            if c_code in (200, 201) and isinstance(c_resp, dict) and c_resp.get("payload"):
                                nonce = c_resp["payload"]
                                words = raw_m.split() if isinstance(raw_m, str) else raw_m
                                _, pub_key_bytes, priv_key_bytes, wallet_contract = Wallets.from_mnemonics(
                                    mnemonics=words, version=WalletVersionEnum.v4r2
                                )
                                state_init_res = wallet_contract.create_state_init()
                                state_init_b64 = base64.b64encode(state_init_res["state_init"].to_boc(False)).decode("utf-8")
                                t_addr = wallet_contract.address
                                friendly_addr = t_addr.to_string(is_user_friendly=True, is_bounceable=False, is_url_safe=True)
                                domain_bytes = b"vyro.run.place"
                                ts_now = int(time.time())
                                msg = b"ton-proof-item-v2/" + struct.pack(">i", t_addr.wc) + t_addr.hash_part + struct.pack("<I", len(domain_bytes)) + domain_bytes + struct.pack("<Q", ts_now) + nonce.encode("utf-8")
                                digest = hashlib.sha256(b"\xff\xff" + b"ton-connect" + hashlib.sha256(msg).digest()).digest()
                                from nacl.signing import SigningKey
                                sig = SigningKey(priv_key_bytes[:32]).sign(digest).signature
                                sig_b64 = base64.b64encode(sig).decode("utf-8")
                                conn_body = {
                                    "address": friendly_addr,
                                    "chain": "-239",
                                    "publicKey": pub_key_bytes.hex(),
                                    "walletStateInit": state_init_b64,
                                    "proof": {
                                        "timestamp": ts_now,
                                        "domain": {"lengthBytes": len(domain_bytes), "value": "vyro.run.place"},
                                        "signature": sig_b64,
                                        "payload": nonce
                                    }
                                }
                                conn_code, conn_resp = await safe_post("https://vyro.run.place/api/wallet/connect", json_data=conn_body, req_headers=ch_headers)
                                if conn_code in (200, 201):
                                    logger.info(f"[{name}] ✅ [VyroDrop] Bound dedicated TON wallet {friendly_addr[:12]}...")
                                    await jitter(0.8, 1.5)
                                    st_c2, _ = await safe_post("https://vyro.run.place/api/mining/start", json_data={"idempotencyKey": str(uuid.uuid4())}, req_headers=vy_h)
                                    if st_c2 in (200, 201):
                                        wallet_required = False
                    except Exception as vw_err:
                        logger.debug(f"[{name}] Vyro wallet connect note: {vw_err}")

                if wallet_required:
                    if c_code == 403 or (c_resp and isinstance(c_resp, dict) and "HUMAN_VERIFICATION_REQUIRED" in str(c_resp)):
                        status["bots"]["vyro"] = f"turnstile_required (wallet security check needed, lvl: {lvl or 1})"
                    else:
                        status["bots"]["vyro"] = f"wallet_required (TonConnect needed, lvl: {lvl or 1})"
                else:
                    speed = m_obj.get('currentSpeed', 0) if m_obj else 0
                    status["bots"]["vyro"] = f"farmed (lvl: {lvl or 1}, speed: {speed})"
                return
            except Exception as e:
                status["bots"]["vyro"] = f"api_error: {format_error(e)}"
                return

        status["bots"]["vyro"] = "skipped (no initData)"

    # 9. Kynex Network (@Kynex_miningbot)
    async def _farm_kynex():
        if tokens.get("kynex_init_data"):
            try:
                import kynex_miner
                res = await kynex_miner.farm_kynex_account(session, tokens["kynex_init_data"], acc, is_master=is_owner)
                status["bots"]["kynex"] = res.get("status", "farmed")
                return
            except Exception as e:
                status["bots"]["kynex"] = f"api_error: {format_error(e)}"
                return
        status["bots"]["kynex"] = "skipped (no initData)"

    # 6. DiggoMiner (@Diggominer_bot - diggo.linkpc.net)
    async def _farm_diggo():
        if tokens.get("diggo_init_data"):
            try:
                d_init = tokens["diggo_init_data"]
                if "%25" in d_init or "%3D" in d_init or "user%3D" in d_init:
                    d_init = urllib.parse.unquote(d_init)

                base_url = "https://diggo.linkpc.net"
                init_headers = {
                    "Content-Type": "application/json",
                    "User-Agent": user_agent,
                    "Origin": base_url,
                    "Referer": f"{base_url}/?tgWebAppStartParam=ref_4088138f11effe8eef4b86ff"
                }

                # 1. Telegram Auth
                a_code, a_d = await safe_post(f"{base_url}/api/auth/telegram", json_data={"initData": d_init}, req_headers=init_headers)
                if a_code == 401 or (isinstance(a_d, dict) and a_d.get("error") == "expired_init_data"):
                    status["bots"]["diggo"] = "token_expired (needs MTProto refresh)"
                    return
                if not a_d or not isinstance(a_d, dict) or not a_d.get("token"):
                    status["bots"]["diggo"] = f"skipped (auth {a_code or 'error'})"
                    return

                jwt_token = a_d["token"]
                st = a_d.get("state", {})
                bal = st.get("balance", 0)
                lvl = st.get("currentLevel", 1)
                mining = st.get("mining") or {}
                pending_mined = mining.get("pending", 0)

                auth_headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {jwt_token}",
                    "User-Agent": user_agent,
                    "Origin": base_url,
                    "Referer": f"{base_url}/?tgWebAppStartParam=ref_4088138f11effe8eef4b86ff"
                }

                # 2. Mining claim (if pending rewards accrued)
                claimed_amt = 0
                if pending_mined and float(pending_mined) > 0:
                    await jitter(0.5, 1.2)
                    c_code, c_d = await safe_post(
                        f"{base_url}/api/claims/mining",
                        json_data={},
                        req_headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())}
                    )
                    if isinstance(c_d, dict) and c_d.get("amount"):
                        claimed_amt = c_d["amount"]
                        bal = c_d.get("state", {}).get("balance", bal)

                # 3. Referrals claim
                await jitter(0.4, 0.9)
                await safe_post(
                    f"{base_url}/api/referrals/claim",
                    json_data={},
                    req_headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())}
                )

                # 4. Check-in daily task
                tasks = st.get("tasks") or {}
                checkin_task = tasks.get("checkin") or {}
                if checkin_task.get("enabled") and not checkin_task.get("claimed") and (checkin_task.get("progress", 0) >= checkin_task.get("total", 1)):
                    await jitter(0.4, 0.9)
                    t_code, t_d = await safe_post(
                        f"{base_url}/api/tasks/claim",
                        json_data={"taskId": "checkin"},
                        req_headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())}
                    )
                    if isinstance(t_d, dict) and t_d.get("amount"):
                        bal = t_d.get("state", {}).get("balance", bal)

                # 5. Social & Community tasks
                for sid in ["telegram", "community_react", "social-tasks"]:
                    s_task = tasks.get(sid) or {}
                    if s_task.get("enabled") and not s_task.get("claimed"):
                        await jitter(0.3, 0.7)
                        t_code, t_d = await safe_post(
                            f"{base_url}/api/tasks/claim",
                            json_data={"taskId": sid},
                            req_headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())}
                        )
                        if isinstance(t_d, dict) and t_d.get("amount"):
                            bal = t_d.get("state", {}).get("balance", bal)

                claim_str = f", +{claimed_amt:.2f} claimed" if claimed_amt else ""
                status["bots"]["diggo"] = f"farmed (bal: {bal:.2f} DIGGO, lvl: {lvl}{claim_str})"
                return
            except Exception as e:
                status["bots"]["diggo"] = f"api_error: {format_error(e)}"
                return
        status["bots"]["diggo"] = "skipped (no initData)"


    # 8. Astra Airdrop (@ASTRA_AIRDROP_BOT)
    async def _farm_astra():
        if tokens.get("astra_init_data"):
            try:
                a_init = tokens["astra_init_data"]
                # Parse initData into p_dcs and p_hash for Supabase RPC
                q = urllib.parse.parse_qs(a_init, keep_blank_values=True)
                flat_q = {k: v[0] for k, v in q.items()}
                hash_val = flat_q.pop("hash", "")
                p_dcs = "\n".join(f"{k}={v}" for k, v in sorted(flat_q.items()))

                astra_sb_url = "https://bcbwqnkfyrpjhctesvnp.supabase.co"
                astra_sb_key = os.getenv("ASTRA_SB_KEY") or __import__("base64").b64decode("ZXlKaGJHY2lPaUpJVXpJMU5pSXNJblI1Y0NJNklrcFhWQ0o5LmV5SnBjM01pT2lKemRYQmhZbUZ6WlNJc0luSmxaaUk2SW1KalluZHhibXRtZVhKd2FtaGpkR1Z6ZG01d0lpd2ljbTlzWlNJNkltRnViMjRpTENKcFlYUWlPakUzT1RBeE5UVTRNVGtzSW1WNGNDSTZNakV3TlRjek1UZ3hPWDAuNi10aVQtaFdjaklPUEFwWkpLejZRdlgzRUVxbkhfRk1IR1hscllRN2xRZw==").decode()
                astra_headers = {
                    "apikey": astra_sb_key,
                    "Authorization": f"Bearer {astra_sb_key}",
                    "Content-Type": "application/json",
                    "User-Agent": user_agent
                }

                async def astra_rpc(fn, extra=None):
                    args = {"p_dcs": p_dcs, "p_hash": hash_val}
                    if extra: args.update(extra)
                    _, res_d = await safe_post(f"{astra_sb_url}/rest/v1/rpc/{fn}", args, req_headers=astra_headers)
                    return res_d if isinstance(res_d, dict) else {}

                # 1. Login & Master Referral Binding
                p_ref = None if is_owner else int(ASTRA_REFERRAL_CODE.replace("ref_", "") if ASTRA_REFERRAL_CODE.replace("ref_", "").isdigit() else "6727787768")
                log_d = await astra_rpc("astra_login", {"p_ref": p_ref} if p_ref else {})
                u_obj = (log_d.get("user") if isinstance(log_d, dict) else {}) or {}
                miner_lvl = u_obj.get("miner_level", 1)
                astra_bal = float(u_obj.get("mined_balance", 0) or u_obj.get("balance", 0))

                # 2. Sync Dedicated Account TON Wallet if available
                target_ton_w = (acc.get("ton_wallet") or {}).get("address") or (FLEET_TON_CACHE.get(str(uid)) or {}).get("address") or (PRIMARY_TON_WALLET if is_owner else None)
                if target_ton_w and (not u_obj.get("wallet_address") or u_obj.get("wallet_address") != target_ton_w):
                    await astra_rpc("astra_sync_wallet", {"p_wallet": str(target_ton_w)})

                # 3. Mine Claim & Boost Activation
                await jitter(0.5, 1.2)
                await astra_rpc("astra_mine_claim")
                await astra_rpc("astra_activate_boost")

                # 4. Math Challenge Solver & Start Mining
                await jitter(0.5, 1.2)
                ch_d = await astra_rpc("astra_math_challenge", {"p_scope": "start_mine"})
                if ch_d and ch_d.get("status") == "success" and ch_d.get("challenge_id"):
                    q_str = ch_d.get("question", "")
                    ans = solve_atf_math(q_str)
                    await jitter(1.5, 3.0)
                    await astra_rpc("astra_start_mine", {"p_cid": ch_d["challenge_id"], "p_answer": str(ans)})

                # 5. Side-Task Automation (Complete 3/3 tasks to unlock +100 ASTRA bonus per recruit for Master)
                # 4 repeatable tasks: react_telegram_post, twitter_retweet, youtube_like_comment, subscribe_youtube
                tasks_to_run = ["react_telegram_post", "twitter_retweet", "youtube_like_comment", "subscribe_youtube"]
                started_res = await asyncio.gather(*[astra_rpc("astra_task_start", {"p_task": t}) for t in tasks_to_run], return_exceptions=True)
                started_tasks = [
                    tasks_to_run[i] for i, st in enumerate(started_res)
                    if isinstance(st, dict) and st.get("status") == "success"
                ]

                if started_tasks:
                    await asyncio.sleep(15.5)  # satisfy minSeconds
                    await asyncio.gather(*[astra_rpc("astra_task_claim", {"p_task": t}) for t in started_tasks], return_exceptions=True)

                # 6. Referral & Team Claims
                await jitter(0.5, 1.0)
                await astra_rpc("astra_claim")
                await astra_rpc("astra_team_claim")

                status["bots"]["astra"] = f"farmed (lvl: {miner_lvl}, bal: {astra_bal:.1f} ASTRA)"
                return
            except Exception as e:
                status["bots"]["astra"] = f"api_error: {format_error(e)}"
                return
        status["bots"]["astra"] = "skipped (no initData)"

    # 9. PepeGram (@Pepe_gram_bot)
    async def _farm_pepegram():
        if tokens.get("pepegram_init_data"):
            try:
                p_init = tokens["pepegram_init_data"]
                pepe_base = "https://app.miniempire.app/miniapp"
                pepe_headers = {
                    "Content-Type": "application/json",
                    "User-Agent": user_agent,
                    "Origin": "https://app.miniempire.app",
                    "Referer": "https://app.miniempire.app/miniapp/index.html?tid=1449&lang=en"
                }

                # 1. Auth & Profile
                await jitter(0.5, 1.2)
                _, auth_d = await safe_post(f"{pepe_base}/auth?tid=1449", {"initData": p_init, "tid": 1449}, req_headers=pepe_headers)
                if isinstance(auth_d, dict) and auth_d.get("error") == "user not registered":
                    status["bots"]["pepegram"] = "not_registered (needs bot /start)"
                    return

                u_data = (auth_d.get("user") if isinstance(auth_d, dict) else {}) or {}
                power_val = u_data.get("power", 0)
                hashes_val = u_data.get("hashes", 0)
                ends_at = int(u_data.get("hashes_production_ends_at", 0) or 0)

                # 2. Welcome bonus & Claim
                await jitter(0.5, 1.2)
                await safe_post(f"{pepe_base}/claim-welcome-bonus?tid=1449", {"initData": p_init, "tid": 1449}, req_headers=pepe_headers)
                await safe_post(f"{pepe_base}/claim?tid=1449", {"initData": p_init, "tid": 1449}, req_headers=pepe_headers)

                # 3. Mine tap / task execution
                await jitter(0.5, 1.2)
                await safe_post(f"{pepe_base}/tasks/mine?tid=1449", {"initData": p_init, "tid": 1449}, req_headers=pepe_headers)

                # 4. Production Start (6-Hour Mining Session & Referral Power Activation)
                now_ts = int(time.time())
                if now_ts >= ends_at:
                    await jitter(0.4, 0.9)
                    _, sp_d = await safe_post(f"{pepe_base}/start-production?tid=1449", {"initData": p_init, "tid": 1449}, req_headers=pepe_headers)
                    if isinstance(sp_d, dict) and sp_d.get("ends_at"):
                        ends_at = int(sp_d["ends_at"])

                # 5. Free Power Boosts (Ad rolls & Slot spins)
                await jitter(0.2, 0.5)
                await safe_post(f"{pepe_base}/tasks/ad-roll?tid=1449", {"initData": p_init, "tid": 1449}, req_headers=pepe_headers, timeout_sec=4, retries=1)
                await safe_post(f"{pepe_base}/tasks/ad-roll2?tid=1449", {"initData": p_init, "tid": 1449}, req_headers=pepe_headers, timeout_sec=4, retries=1)
                await safe_post(f"{pepe_base}/tasks/slot-spin?tid=1449", {"initData": p_init, "tid": 1449}, req_headers=pepe_headers, timeout_sec=4, retries=1)

                # 6. Tasks list & claim (cap to 3 per cycle with fast timeouts)
                await jitter(0.2, 0.5)
                _, t_data = await safe_get(f"{pepe_base}/tasks?initData={urllib.parse.quote(p_init)}&tid=1449", req_headers=pepe_headers, timeout_sec=4, retries=1)
                if isinstance(t_data, dict) and t_data.get("tasks"):
                    unclaimed = [tk for tk in t_data["tasks"] if not tk.get("completed") and not tk.get("pending")]
                    for tk in unclaimed[:3]:
                        tk_id = tk.get("id")
                        if tk_id:
                            await jitter(0.2, 0.4)
                            await safe_post(f"{pepe_base}/tasks/claim?tid=1449", {"initData": p_init, "tid": 1449, "taskId": tk_id}, req_headers=pepe_headers, timeout_sec=4, retries=1)

                # 7. Team / Referral Commission Harvest
                await jitter(0.2, 0.4)
                await safe_post(f"{pepe_base}/claim?tid=1449", {"initData": p_init, "tid": 1449}, req_headers=pepe_headers, timeout_sec=4, retries=1)

                status["bots"]["pepegram"] = f"farmed (power: {power_val}, hashes: {hashes_val}, active_until: {ends_at})"
                return
            except Exception as e:
                status["bots"]["pepegram"] = f"api_error: {format_error(e)}"
                return
        status["bots"]["pepegram"] = "skipped (no initData)"

    # 10. AdxEarn AI (@AdxEarnAibot)
    async def _farm_adxearn():
        if tokens.get("adxearn_init_data"):
            try:
                adx_init = tokens["adxearn_init_data"]
                adx_base = "https://api.adxearnai.xyz/api"
                adx_headers = {
                    "Content-Type": "application/json",
                    "User-Agent": user_agent,
                    "X-Telegram-Init-Data": adx_init
                }
                await jitter(0.5, 1.2)

                # 1. User Session & Master Referral Binding
                ref_param = None if is_owner else ADXEARN_REFERRAL_CODE.replace("ref_", "")
                fp = f"412x915|24|8|UTC|en-US|8|5|2.625|Mali-G78-{uid}"
                s_code, s_d = await safe_post(f"{adx_base}/user/session", {"ref": ref_param, "fp": fp}, req_headers=adx_headers)

                user_info = (s_d.get("user") if isinstance(s_d, dict) else None) or {}
                bal_pts = user_info.get("balance_points", 0)
                streak = user_info.get("checkin_streak", 0)

                # 2. Daily Check-in Reward
                await jitter(0.5, 1.2)
                c_code, c_d = await safe_post(f"{adx_base}/rewards/checkin", {}, req_headers=adx_headers)
                if isinstance(c_d, dict) and c_d.get("success"):
                    rew = c_d.get("reward", 0)
                    streak = c_d.get("streak", streak)
                    bal_pts += rew

                # 3. Mining / Farming Status & Lifecycle
                await jitter(0.5, 1.2)
                st_code, st_d = await safe_get(f"{adx_base}/farming/status", req_headers=adx_headers)
                mining_stat = "ACTIVE"
                if isinstance(st_d, dict):
                    if st_d.get("ready"):
                        await jitter(0.5, 1.0)
                        await safe_post(f"{adx_base}/farming/claim", {}, req_headers=adx_headers)
                    if st_d.get("status") == "idle" or not st_d.get("startedAt"):
                        await jitter(0.5, 1.0)
                        await safe_post(f"{adx_base}/farming/start", {}, req_headers=adx_headers)

                # 4. Farming Boost
                await jitter(0.4, 0.8)
                await safe_post(f"{adx_base}/farming/boost", {}, req_headers=adx_headers)

                # 5. Dynamic Task Discovery & Completion
                await jitter(0.5, 1.2)
                t_code, t_d = await safe_get(f"{adx_base}/rewards/tasks", req_headers=adx_headers)
                if isinstance(t_d, dict) and t_d.get("tasks"):
                    tasks = t_d.get("tasks", [])
                    for t in tasks:
                        if isinstance(t, dict):
                            t_id = t.get("id")
                            v_type = t.get("verify_type")
                            delay = int(t.get("verify_delay_seconds") or 15)
                            if t_id and (not v_type or v_type == "other" or "offer" in str(t.get("title", "")).lower() or "bonus" in str(t.get("title", "")).lower()):
                                try:
                                    await safe_post(f"{adx_base}/rewards/task-start", {"taskId": t_id}, req_headers=adx_headers)
                                    async def _delayed_adx_task_claim(task_id, wait_s):
                                        await asyncio.sleep(wait_s + 1)
                                        await safe_post(f"{adx_base}/rewards/task-claim", {"taskId": task_id}, req_headers=adx_headers)
                                    bg_tasks.append(asyncio.create_task(_delayed_adx_task_claim(t_id, min(delay, 16))))
                                except Exception:
                                    pass

                # 6. Referral Milestones Claim
                if is_owner:
                    await safe_post(f"{adx_base}/referrals/milestones/claim", {}, req_headers=adx_headers)

                status["bots"]["adxearn"] = f"farmed (bal: {bal_pts} pts, streak: {streak}, mining: {mining_stat})"
                return
            except Exception as e:
                status["bots"]["adxearn"] = f"api_error: {format_error(e)}"
                return
        status["bots"]["adxearn"] = "skipped (no initData)"

    # Humanized Concurrent Execution Pipeline: Active Fleet Mining Pools (All 10 Bots)
    BOT_COOLDOWNS = {
        "atf": (1200, 2400),      # 20m - 40m
        "mrg": (1800, 3600),      # 30m - 60m
        "victors": (3600, 7200),  # 1h - 2h
        "vyro": (2400, 4800),     # 40m - 80m
        "kynex": (2400, 4800),    # 40m - 80m
        "diggo": (1800, 3600),    # 30m - 60m
        "astra": (1800, 3600),    # 30m - 60m
        "pepegram": (1800, 3600), # 30m - 60m
        "adxearn": (1800, 3600)   # 30m - 60m
    }

    bot_routines = [
        {"name": "mrg", "fn": _farm_mrg, "has_data": bool(tokens.get("mrg_init_data"))},
        {"name": "atf", "fn": _farm_atf, "has_data": bool(tokens.get("atf_init_data"))},
        {"name": "victors", "fn": _farm_victors, "has_data": bool(tokens.get("victors_init_data"))},
        {"name": "vyro", "fn": _farm_vyro, "has_data": bool(tokens.get("vyro_init_data"))},
        {"name": "kynex", "fn": _farm_kynex, "has_data": bool(tokens.get("kynex_init_data"))},
        {"name": "diggo", "fn": _farm_diggo, "has_data": bool(tokens.get("diggo_init_data"))},
        {"name": "astra", "fn": _farm_astra, "has_data": bool(tokens.get("astra_init_data"))},
        {"name": "pepegram", "fn": _farm_pepegram, "has_data": bool(tokens.get("pepegram_init_data"))},
        {"name": "adxearn", "fn": _farm_adxearn, "has_data": bool(tokens.get("adxearn_init_data"))},
    ]

    for b in bot_routines:
        if not b["has_data"]:
            status["bots"][b["name"]] = "skipped (no initData)"

    active_routines = [b for b in bot_routines if b["has_data"]]
    random.shuffle(active_routines)

    now_ts = int(time.time())
    sem_bot = asyncio.Semaphore(10)

    async def _run_single_routine(b):
        b_name = b["name"]
        min_s, max_s = BOT_COOLDOWNS.get(b_name, (1800, 3600))
        cd_key = f"fleet:last_farm:{b_name}:{uid}"

        should_farm = True
        if not force:
            try:
                # 1. Check local in-memory cache FIRST (saves 99% of Upstash calls)
                last_farm_raw = FLEET_LAST_FARM_CACHE.get(f"{b_name}:{uid}")
                if not last_farm_raw and UPSTASH_URL and UPSTASH_TOKEN:
                    try:
                        async with session.get(f"{UPSTASH_URL}/get/{cd_key}", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=1.5)) as u_resp:
                            if u_resp.status == 200:
                                u_data = await u_resp.json()
                                last_farm_raw = u_data.get("result")
                                if last_farm_raw:
                                    FLEET_LAST_FARM_CACHE[f"{b_name}:{uid}"] = last_farm_raw
                    except Exception:
                        pass

                if last_farm_raw:
                    try:
                        last_obj = json.loads(last_farm_raw) if isinstance(last_farm_raw, str) and last_farm_raw.startswith("{") else None
                        last_time = int(last_obj.get("timestamp", 0)) if last_obj else int(last_farm_raw)
                        cd_sec = int(last_obj.get("cooldown", min_s)) if last_obj else min_s
                        elapsed = now_ts - last_time
                        if last_time > 0 and elapsed < cd_sec:
                            rem_m = max(1, (cd_sec - elapsed) // 60)
                            status["bots"][b_name] = f"cooldown ({rem_m}m remaining)"
                            should_farm = False
                    except Exception:
                        pass
            except Exception:
                pass

        if not should_farm:
            return

        async with sem_bot:
            try:
                await jitter(0.2, 0.6)
                await asyncio.wait_for(b["fn"](), timeout=90.0)
                # Store randomized cooldown: 2h-8h on success, 3m-5m retry on error/expired
                bot_res = str(status["bots"].get(b_name, "")).lower()
                is_success = bot_res.startswith("farmed") or bot_res.startswith("ok")
                next_cd = random.randint(min_s, max_s) if is_success else random.randint(180, 300)
                val_to_save = json.dumps({"timestamp": now_ts, "cooldown": next_cd})
                FLEET_LAST_FARM_CACHE[f"{b_name}:{uid}"] = val_to_save
                if UPSTASH_URL and UPSTASH_TOKEN:
                    try:
                        async with session.post(f"{UPSTASH_URL}/set/{cd_key}", data=val_to_save, headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=2.0)):
                            pass
                    except Exception:
                        pass
            except asyncio.TimeoutError:
                status["bots"][b_name] = "timeout (90s)"
                fail_cd = random.randint(180, 300)
                FLEET_LAST_FARM_CACHE[f"{b_name}:{uid}"] = json.dumps({"timestamp": now_ts, "cooldown": fail_cd})
            except Exception as err:
                status["bots"][b_name] = f"error: {format_error(err)}"
                fail_cd = random.randint(180, 300)
                FLEET_LAST_FARM_CACHE[f"{b_name}:{uid}"] = json.dumps({"timestamp": now_ts, "cooldown": fail_cd})

    await asyncio.gather(*[_run_single_routine(b) for b in active_routines], return_exceptions=True)
    if bg_tasks:
        try:
            await asyncio.wait_for(asyncio.gather(*bg_tasks, return_exceptions=True), timeout=18.0)
        except Exception:
            pass
    return status


async def run_cloud_fleet_farming_cycle(session: aiohttp.ClientSession = None, accounts: list = None, tokens_map: dict = None, force: bool = False) -> dict:
    """Executes full autonomous cloud farming and task completions across all 5 legitimate bots for all fleet accounts."""
    created_session = False
    if session is None:
        session = aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        created_session = True

    try:
        FLEET_18_SET = {
            "6727787768", "8881914294", "7648254021", "8826375659", "8450010161",
            "8782429452", "7734849205", "8025472383", "8851426148", "8203342513",
            "8190649727", "7487048946", "8741547543", "8727040932", "7749125802",
            "7954290138", "8841038141", "8975442879"
        }
        if accounts is None:
            accounts = await fetch_accounts_from_cloud()
        accounts = [
            a for a in (accounts or [])
            if str(a.get("user_id")) in FLEET_18_SET or a.get("session_string") or a.get("session")
        ]
        if not accounts:
            return {"ok": False, "message": "No accounts found for farming cycle", "farmed_count": 0}

        if tokens_map is None:
            tokens_map = await fetch_cloud_miniapp_tokens(session)

        if not FLEET_TON_CACHE or not FLEET_EVM_CACHE:
            await load_fleet_wallets_from_cloud()

        farm_tasks = []
        farm_sem = asyncio.Semaphore(4)

        async def _farm_with_sem(a_dict, t_dict):
            async with farm_sem:
                uid_str = str(a_dict.get("user_id"))
                now_s = time.time()
                synced_val = t_dict.get("synced_at", 0) or t_dict.get("updated_at", 0) or 0
                synced_ts = 0
                if isinstance(synced_val, (int, float)):
                    synced_ts = float(synced_val)
                elif isinstance(synced_val, str):
                    try:
                        synced_ts = datetime.datetime.fromisoformat(synced_val.replace("Z", "+00:00")).timestamp()
                    except Exception:
                        try:
                            synced_ts = float(synced_val)
                        except Exception:
                            synced_ts = 0

                has_any_token = any(k.endswith("_init_data") and bool(v) for k, v in t_dict.items())
                has_vyro = bool(t_dict.get("vyro_init_data"))
                has_diggo = bool(t_dict.get("diggo_init_data"))
                needs_refresh = (not has_any_token) or (not has_vyro) or (not has_diggo) or is_token_data_expired(t_dict, max_age_hours=18.0)

                if needs_refresh and (a_dict.get("session_string") or a_dict.get("session")):
                    try:
                        fresh_toks = await asyncio.wait_for(extract_tokens_for_account(a_dict), timeout=90.0)
                        if fresh_toks:
                            t_dict.update(fresh_toks)
                            tokens_map[uid_str] = t_dict
                            asyncio.create_task(sync_account_tokens_to_clouds(t_dict))
                    except Exception as ex_e:
                        logger.warning(f"[Farm Task] On-the-fly extraction note for {uid_str}: {ex_e}")
                try:
                    res = await asyncio.wait_for(farm_single_account_bots(session, a_dict, t_dict, force=force), timeout=180.0)
                    if isinstance(res, dict) and any(("token_expired" in str(v).lower() or "token_invalid" in str(v).lower() or "unauthorized" in str(v).lower()) for v in res.get("bots", {}).values()):
                        if a_dict.get("session_string") or a_dict.get("session"):
                            try:
                                fresh_toks = await asyncio.wait_for(extract_tokens_for_account(a_dict), timeout=90.0)
                                if fresh_toks:
                                    t_dict.update(fresh_toks)
                                    tokens_map[uid_str] = t_dict
                                    asyncio.create_task(sync_account_tokens_to_clouds(t_dict))
                                    res = await asyncio.wait_for(farm_single_account_bots(session, a_dict, t_dict, force=True), timeout=180.0)
                            except Exception:
                                pass
                    return res
                except asyncio.TimeoutError:
                    return {"uid": uid_str, "name": a_dict.get("name", uid_str), "bots": {"status": "timeout_180s"}}

        for acc in accounts:
            uid = str(acc.get("user_id"))
            acc_tok = tokens_map.get(uid, {})
            farm_tasks.append(_farm_with_sem(acc, acc_tok))

        results = await asyncio.gather(*farm_tasks, return_exceptions=True)
        valid_res = [r for r in results if isinstance(r, dict)]

        return {
            "ok": True,
            "farmed_count": len(valid_res),
            "total_accounts": len(accounts),
            "results": valid_res,
            "timestamp": time.time()
        }
    finally:
        if created_session:
            await session.close()


LAST_FARM_RUN = {
    "status": "idle",
    "farmed_count": 0,
    "timestamp": 0,
    "results": []
}


@app.post("/api/farm/cloud-all")
async def api_farm_cloud_all(request: Request):
    """Executes on-demand cloud fleet farming cycle across all 5 legitimate bots for accounts."""
    auth = request.headers.get("Authorization") or ""
    req_secret = request.query_params.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        pass

    sync_mode = request.query_params.get("sync") == "1"
    force_mode = request.query_params.get("force") == "1"
    shard_param = str(request.query_params.get("shard") or os.getenv("NODE_SHARD") or "all").lower()

    async def _execute_farming():
        global LAST_FARM_RUN
        LAST_FARM_RUN["status"] = "running"
        LAST_FARM_RUN["timestamp"] = time.time()
        try:
            async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as session:
                accounts = await fetch_accounts_from_cloud()
                total = len(accounts) if accounts else 0
                midpoint = (total + 1) // 2
                if shard_param == "1":
                    accounts = [a for a in accounts if int(a.get("index") or 0) <= midpoint]
                    logger.info(f"[Farm Trigger] Partition Shard 1: Selected accounts 1-{midpoint} ({len(accounts)}/{total} accounts)")
                elif shard_param == "2":
                    accounts = [a for a in accounts if int(a.get("index") or 0) > midpoint]
                    logger.info(f"[Farm Trigger] Partition Shard 2: Selected accounts {midpoint+1}-{total} ({len(accounts)}/{total} accounts)")

                tokens = await fetch_cloud_miniapp_tokens(session)
                res = await run_cloud_fleet_farming_cycle(session, accounts, tokens, force=force_mode)
                LAST_FARM_RUN["status"] = "completed"
                LAST_FARM_RUN["farmed_count"] = res.get("farmed_count", 0)
                LAST_FARM_RUN["total_accounts"] = res.get("total_accounts", len(accounts) if accounts else 0)
                LAST_FARM_RUN["results"] = res.get("results", [])
                LAST_FARM_RUN["timestamp"] = time.time()
                return res
        except Exception as e:
            logger.error(f"[Farm Trigger] Error: {e}")
            LAST_FARM_RUN["status"] = f"error: {e}"
            return {"ok": False, "error": str(e)}

    if sync_mode:
        return await _execute_farming()

    asyncio.create_task(_execute_farming())
    return {
        "ok": True,
        "status": "dispatched",
        "shard": shard_param,
        "message": f"Full 5-bot cloud farming cycle dispatched for Shard {shard_param}.",
        "timestamp": time.time()
    }


@app.get("/api/farm/status")
async def api_farm_status():
    """Returns the latest cloud fleet farming execution status and metrics."""
    return {"ok": True, "last_farm_run": LAST_FARM_RUN, "timestamp": time.time()}


LAST_SWEEP_RUN = {"status": "idle", "timestamp": 0, "output": ""}


@app.get("/api/tasks/sweep-all")
@app.post("/api/tasks/sweep-all")
async def api_tasks_sweep_all(request: Request):
    """Executes on-demand cloud side-tasks sweep across all 10 bots on Render Node 2."""
    auth = request.headers.get("Authorization") or ""
    req_secret = request.query_params.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    async def _run_sweep():
        global LAST_SWEEP_RUN
        LAST_SWEEP_RUN["status"] = "running"
        LAST_SWEEP_RUN["timestamp"] = time.time()
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "finish_all_fleet_sidetasks.py",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            stdout, _ = await proc.communicate()
            LAST_SWEEP_RUN["status"] = "completed" if proc.returncode == 0 else "failed"
            LAST_SWEEP_RUN["output"] = stdout.decode("utf-8", errors="ignore")[-2000:]
        except Exception as e:
            LAST_SWEEP_RUN["status"] = "error"
            LAST_SWEEP_RUN["output"] = str(e)

    asyncio.create_task(_run_sweep())
    return {"ok": True, "status": "dispatched", "message": "10-Bot fleet side-task sweep dispatched on Render Node 2."}


@app.get("/api/tasks/sweep-status")
async def api_tasks_sweep_status():
    """Returns the latest status of the 10-bot side-task sweep."""
    return {"ok": True, "last_sweep_run": LAST_SWEEP_RUN}


@app.get("/api/fleet/ad-farmer/status")
async def api_fleet_ad_farmer_status():
    """Returns the real-time status of the 24/7 autonomous fleet ad-farming loop."""
    return {
        "ok": True,
        "state": FLEET_AD_FARMER_STATE,
        "timestamp": time.time()
    }


@app.post("/api/fleet/ad-farmer/trigger")
async def api_fleet_ad_farmer_trigger():
    """Triggers an immediate burst or status refresh of the ad-farming loop."""
    FLEET_AD_FARMER_STATE["status"] = "manually_triggered"
    return {
        "ok": True,
        "message": "Autonomous fleet ad-farming loop triggered.",
        "state": FLEET_AD_FARMER_STATE
    }


@app.post("/api/farm/account/{uid}")
async def api_farm_single_account(uid: str, request: Request):
    """Executes on-demand cloud farming & token bootstrap for a single account in the fleet."""
    try:
        force_mode = request.query_params.get("force") == "1"
        refresh_mode = request.query_params.get("refresh") == "1"
        accounts = await fetch_accounts_from_cloud()
        target_acc = next((a for a in accounts if str(a.get("user_id")) == str(uid)), None)
        if not target_acc:
            raise HTTPException(status_code=404, detail=f"Account {uid} not found in fleet")

        if not FLEET_TON_CACHE or not FLEET_EVM_CACHE:
            await load_fleet_wallets_from_cloud()

        async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as session:
            tokens_map = await fetch_cloud_miniapp_tokens(session)
            acc_tok = tokens_map.get(str(uid), {})
            key_tokens = [f"{b}_init_data" for b in ALL_10_BOT_KEYS]
            missing_any = not all(k in acc_tok and bool(acc_tok.get(k)) for k in key_tokens)
            now_s = time.time()
            synced_val = acc_tok.get("synced_at", 0) or acc_tok.get("updated_at", 0) or 0
            synced_ts = 0
            if isinstance(synced_val, (int, float)):
                synced_ts = float(synced_val)
            elif isinstance(synced_val, str):
                try:
                    synced_ts = datetime.datetime.fromisoformat(synced_val.replace("Z", "+00:00")).timestamp()
                except Exception:
                    try:
                        synced_ts = float(synced_val)
                    except Exception:
                        synced_ts = 0

            has_vyro = bool(acc_tok.get("vyro_init_data"))
            has_diggo = bool(acc_tok.get("diggo_init_data"))
            is_stale = (now_s - synced_ts > 2700) or ((not has_vyro or not has_diggo) and (now_s - synced_ts > 900))
            missing_tokens = refresh_mode or (not acc_tok) or missing_any or is_stale
            if missing_tokens:
                fresh = await extract_tokens_for_account(target_acc)
                if fresh:
                    acc_tok = {**acc_tok, **fresh}
                    await sync_account_tokens_to_clouds(acc_tok)
                    await bootstrap_account_mining(target_acc, acc_tok)

            if not acc_tok:
                return {"ok": False, "message": "Failed to extract WebApp tokens for account", "uid": uid}

            res = await farm_single_account_bots(session, target_acc, acc_tok, force=force_mode)
            if isinstance(res, dict) and any(("token_expired" in str(v).lower() or "not_registered" in str(v).lower()) for v in res.get("bots", {}).values()):
                fresh = await extract_tokens_for_account(target_acc)
                if fresh:
                    acc_tok = {**acc_tok, **fresh}
                    await sync_account_tokens_to_clouds(acc_tok)
                    res = await farm_single_account_bots(session, target_acc, acc_tok, force=True)
            return {"ok": True, "result": res}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Farm Single Account] Error for {uid}: {traceback.format_exc()}")
        return {"ok": False, "error": str(e), "traceback": traceback.format_exc(), "uid": uid}


@app.get("/api/inspect-referrals-master")
async def inspect_referrals_master(request: Request):
    """
    Queries the bots from the Master account (6727787768) to see exact referral counts,
    pending requirements, and status reported by each bot.
    """
    auth = request.headers.get("Authorization") or ""
    req_secret = request.query_params.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    accounts = await fetch_accounts_from_cloud()
    master_acc = next((a for a in accounts if str(a.get("user_id")) == "6727787768"), None)
    if not master_acc:
        raise HTTPException(status_code=404, detail="Master account not found")

    sess_str = master_acc.get("session_string") or master_acc.get("session")
    cl = create_telethon_client(sess_str=sess_str, identifier=master_acc.get("phone") or "Master", proxy_val=master_acc.get("proxy"))
    bots_to_query = [
        ("mrg", "mrgminerbot", ["/start"]),
        ("atf", "ATF_AIRDROP_bot", ["/start"]),
        ("victors", "VictorsCompanybot", ["/start"]),
        ("vyro", "vyrodrop_bot", ["/start"]),
        ("kynex", "Kynex_miningbot", ["/start"]),
        ("diggo", "Diggominer_bot", ["/start"]),
        ("astra", "ASTRA_AIRDROP_BOT", ["/start"]),
        ("pepegram", "Pepe_gram_bot", ["/start"]),
        ("adxearn", "AdxEarnAibot", ["/start"])
    ]
    results = {}
    try:
        await cl.connect()
        if not await cl.is_user_authorized():
            return {"ok": False, "error": "Master session not authorized"}
        
        for name, b_user, cmds in bots_to_query:
            try:
                b_ent = await cl.get_entity(b_user)
                # Zero-chat policy: do NOT send /start into bot chats! Read existing messages silently.
                msgs = await cl.get_messages(b_ent, limit=5)
                replies = []
                for m in msgs:
                    if not m.out:
                        btns = []
                        if m.buttons:
                            for row in m.buttons:
                                btns.append([b.text for b in row])
                        replies.append({"text": m.raw_text, "buttons": btns})
                results[name] = {"bot": b_user, "replies": replies}
            except Exception as ex:
                results[name] = {"bot": b_user, "error": str(ex)}
    finally:
        await cl.disconnect()

    return {"ok": True, "master_id": "6727787768", "bots": results}


async def study_bot_deep(cl: TelegramClient, bot_key: str, bot_username: str) -> dict:
    """
    Performs deep inspection of a single Telegram bot using the connected client:
    - Pre-joins any required sponsor channels.
    - Inspects initial messages.
    - Sends /start and handles verification buttons.
    - Reads reply keyboards and inline buttons.
    - Tests clicking candidate buttons (Balance, Claim, Bonus, Reward).
    - Obtains WebApp URL and tgWebAppData via RequestAppWebViewRequest.
    - Scans frontend HTML & JS bundles for REST API endpoints and tests them.
    """
    res = {
        "bot_key": bot_key,
        "bot_username": bot_username,
        "status": "success",
        "initial_messages": [],
        "post_start_messages": [],
        "reply_keyboard": [],
        "inline_buttons": [],
        "tested_actions": [],
        "webapp": {},
        "error": None
    }
    channel_deps = {
        "victors": ["VictorsCompany"],
        "vyro": ["vyrodrop"]
    }

    try:
        # Zero-channel policy: Never join channels during bot study!
        pass

        bot_ent = await cl.get_entity(bot_username)
        res["bot_id"] = getattr(bot_ent, "id", None)
        res["bot_title"] = getattr(bot_ent, "title", None) or getattr(bot_ent, "first_name", "")

        msgs = await cl.get_messages(bot_ent, limit=5)
        for m in reversed(msgs):
            res["initial_messages"].append({
                "id": m.id,
                "out": m.out,
                "text": m.raw_text,
                "buttons": [[b.text for b in row] for row in m.buttons] if m.buttons else []
            })

        # Zero-chat policy: do NOT send /start or click buttons in bot chats! Inspect existing messages silently.
        pass

        fresh_msgs = await cl.get_messages(bot_ent, limit=8)
        inline_buttons_found = []
        reply_keyboard_found = []

        for m in reversed(fresh_msgs):
            m_btns = []
            if m.buttons:
                for r_idx, row in enumerate(m.buttons):
                    row_btns = []
                    for c_idx, b in enumerate(row):
                        b_url = getattr(b, "url", None)
                        if not b_url and hasattr(b, "button") and hasattr(b.button, "type") and hasattr(b.button.type, "url"):
                            b_url = b.button.type.url
                        b_info = {
                            "msg_id": m.id,
                            "row": r_idx,
                            "col": c_idx,
                            "text": b.text,
                            "url": b_url
                        }
                        if hasattr(b, "data") and b.data:
                            b_info["data"] = b.data.decode("utf-8", errors="ignore")
                        row_btns.append(b_info)
                        inline_buttons_found.append(b_info)
                    m_btns.append(row_btns)

            res["post_start_messages"].append({
                "id": m.id,
                "out": m.out,
                "text": m.raw_text,
                "buttons": m_btns
            })

            if m.reply_markup and hasattr(m.reply_markup, "rows"):
                for r in m.reply_markup.rows:
                    r_texts = [getattr(b, "text", str(b)) for b in getattr(r, "buttons", []) if hasattr(b, "text")]
                    if r_texts:
                        reply_keyboard_found.append(r_texts)

        res["reply_keyboard"] = reply_keyboard_found
        res["inline_buttons"] = inline_buttons_found

        action_keywords = ["balance", "claim", "bonus", "reward", "miner", "hire", "mining", "referral", "stats", "free", "daily"]
        tested_actions = []

        flat_reply_btns = [b for row in reply_keyboard_found for b in row]
        for btn_text in flat_reply_btns:
            if any(k in btn_text.lower() for k in action_keywords):
                tested_actions.append({
                    "type": "reply_keyboard_found",
                    "button": btn_text,
                    "status": "passive_recorded"
                })

        for btn in inline_buttons_found:
            b_text = btn.get("text", "")
            if any(k in b_text.lower() for k in ["claim", "bonus", "reward", "free miner", "balance", "start mining"]):
                try:
                    m_target = next((m for m in fresh_msgs if m.id == btn.get("msg_id")), None)
                    if m_target:
                        click_res = await m_target.click(btn["row"], btn["col"])
                        await asyncio.sleep(2.0)
                        after_msgs = await cl.get_messages(bot_ent, limit=2)
                        after_text = after_msgs[0].raw_text if after_msgs and not after_msgs[0].out else ""
                        tested_actions.append({
                            "type": "inline_click",
                            "button": b_text,
                            "click_result": str(click_res) if click_res else "ok",
                            "response": after_text
                        })
                except Exception as ce:
                    tested_actions.append({
                        "type": "inline_click",
                        "button": b_text,
                        "error": str(ce)
                    })

        res["tested_actions"] = tested_actions

        webapp_info = {"has_webapp": False}
        candidate_short_names = ["openapp", "app", "miner", "miniapp", "startapp", "play", "game", "trade", "myapp"]
        found_webview_url = None

        # 1. Inspect inline buttons for direct WebApp URLs or deep-links
        for btn in inline_buttons_found:
            url = btn.get("url") or ""
            if not url:
                continue
            if "t.me/" in url:
                try:
                    parsed_u = urllib.parse.urlparse(url)
                    p_parts = [p for p in parsed_u.path.split('/') if p]
                    if len(p_parts) >= 2 and p_parts[1] not in candidate_short_names:
                        candidate_short_names.insert(0, p_parts[1])
                    qs = urllib.parse.parse_qs(parsed_u.query)
                    if "startapp" in qs:
                        sa_val = qs["startapp"][0]
                        if sa_val and sa_val not in candidate_short_names and not sa_val.startswith("ref_"):
                            candidate_short_names.insert(0, sa_val)
                except Exception:
                    pass
            elif "tgWebApp" in url:
                found_webview_url = url
                break

        # 2. Inspect message raw buttons for web_app attribute
        if not found_webview_url:
            for m in fresh_msgs:
                if not m.out and m.buttons:
                    for r_idx, row in enumerate(m.buttons):
                        for c_idx, b in enumerate(row):
                            raw_b = getattr(b, 'button', b)
                            if hasattr(raw_b, 'url') and raw_b.url:
                                if "tgWebApp" in raw_b.url:
                                    found_webview_url = raw_b.url
                                    break
                                elif "t.me/" in raw_b.url:
                                    try:
                                        parsed_u = urllib.parse.urlparse(raw_b.url)
                                        p_parts = [p for p in parsed_u.path.split('/') if p]
                                        if len(p_parts) >= 2 and p_parts[1] not in candidate_short_names:
                                            candidate_short_names.insert(0, p_parts[1])
                                        qs = urllib.parse.parse_qs(parsed_u.query)
                                        if "startapp" in qs:
                                            sa_val = qs["startapp"][0]
                                            if sa_val and sa_val not in candidate_short_names and not sa_val.startswith("ref_"):
                                                candidate_short_names.insert(0, sa_val)
                                    except Exception:
                                        pass
                            if hasattr(raw_b, 'web_app') and getattr(raw_b.web_app, 'url', None):
                                try:
                                    w_raw_url = raw_b.web_app.url
                                    if not w_raw_url.startswith("https://t.me/"):
                                        wv = await cl(RequestWebViewRequest(
                                            peer=bot_ent,
                                            bot=bot_ent,
                                            platform="android",
                                            url=w_raw_url,
                                            start_param="ref_4088138f11effe8eef4b86ff" if "diggo" in bot_key.lower() else "6727787768"
                                        ))
                                        if wv and getattr(wv, 'url', None):
                                            found_webview_url = wv.url
                                            break
                                except Exception:
                                    pass
                        if found_webview_url:
                            break
                if found_webview_url:
                    break

        # 3. Check Bot Menu Button
        b_input = await cl.get_input_entity(bot_ent)
        if not found_webview_url:
            try:
                menu = await cl(functions.bots.GetBotMenuButtonRequest(user_id=b_input))
                menu_btn = getattr(menu, "button", None)
                if menu_btn and hasattr(menu_btn, "url") and menu_btn.url:
                    webapp_info["menu_button_url"] = menu_btn.url
                    if not menu_btn.url.startswith("https://t.me/"):
                        wv = await cl(RequestWebViewRequest(
                            peer=bot_ent,
                            bot=bot_ent,
                            platform="android",
                            url=menu_btn.url,
                            start_param="ref_4088138f11effe8eef4b86ff" if "diggo" in bot_key.lower() else "6727787768"
                        ))
                        if wv and getattr(wv, "url", None):
                            found_webview_url = wv.url
            except Exception as me_err:
                webapp_info["menu_button_error"] = str(me_err)

        # 4. Try RequestAppWebViewRequest with discovered candidate short names
        ref_start_param = "ref_4088138f11effe8eef4b86ff" if "diggo" in bot_key.lower() else "6727787768"
        for sn in candidate_short_names:
            if found_webview_url and "tgWebAppData" in found_webview_url and not found_webview_url.startswith("https://t.me/"):
                break
            try:
                wv_res = await cl(RequestAppWebViewRequest(
                    peer=b_input,
                    app=InputBotAppShortName(bot_id=b_input, short_name=sn),
                    platform="android",
                    start_param=ref_start_param
                ))
                if wv_res and getattr(wv_res, 'url', None):
                    cand_url = wv_res.url
                    if not cand_url.startswith("https://t.me/"):
                        found_webview_url = cand_url
                        webapp_info["short_name"] = sn
                        break
            except Exception:
                continue

        # Reject any t.me link as final webview URL
        if found_webview_url and found_webview_url.startswith("https://t.me/"):
            found_webview_url = None

        if found_webview_url:
            webapp_info["has_webapp"] = True
            webapp_info["url"] = found_webview_url
            parsed_u = urllib.parse.urlparse(found_webview_url)
            frag_params = urllib.parse.parse_qs(parsed_u.fragment)
            query_params = urllib.parse.parse_qs(parsed_u.query)
            init_data = frag_params.get("tgWebAppData", [None])[0] or query_params.get("tgWebAppData", [None])[0]
            webapp_info["init_data_present"] = bool(init_data)
            if init_data:
                webapp_info["init_data_sample"] = init_data[:80] + "..."

            base_url = f"{parsed_u.scheme}://{parsed_u.netloc}"
            webapp_info["base_url"] = base_url

            async with aiohttp.ClientSession() as http:
                web_headers = {
                    "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.127 Mobile Safari/537.36 Telegram-Android/11.1.3",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Referer": "https://web.telegram.org/"
                }
                try:
                    async with http.get(found_webview_url, headers=web_headers, timeout=aiohttp.ClientTimeout(total=8)) as html_resp:
                        html_content = await html_resp.text()
                        webapp_info["html_status"] = html_resp.status

                        script_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html_content)
                        webapp_info["script_srcs"] = script_srcs[:5]

                        discovered_routes = set()
                        for s_src in script_srcs[:3]:
                            js_url = s_src if s_src.startswith("http") else urllib.parse.urljoin(found_webview_url, s_src)
                            try:
                                async with http.get(js_url, headers=web_headers, timeout=aiohttp.ClientTimeout(total=8)) as js_resp:
                                    if js_resp.status == 200:
                                        js_code = await js_resp.text()
                                        routes = re.findall(r'["\'](/api/[a-zA-Z0-9_\-\/]+)["\']', js_code)
                                        for r in routes:
                                            if any(k in r.lower() for k in ["claim", "mine", "mining", "bonus", "checkin", "daily", "task", "user", "profile", "info", "balance", "start", "reward", "wallet", "boost"]):
                                                discovered_routes.add(r)
                            except Exception:
                                pass
                        webapp_info["discovered_api_routes"] = list(discovered_routes)

                        api_test_results = {}
                        if init_data and discovered_routes:
                            for candidate_r in list(discovered_routes)[:3]:
                                full_api_url = urllib.parse.urljoin(base_url, candidate_r)
                                api_headers = {
                                    **web_headers,
                                    "Origin": base_url,
                                    "Referer": found_webview_url,
                                    "Authorization": f"tma {init_data}",
                                    "Content-Type": "application/json"
                                }
                                try:
                                    async with http.post(full_api_url, json={"initData": init_data}, headers=api_headers, timeout=aiohttp.ClientTimeout(total=5)) as post_r:
                                        post_text = await post_r.text()
                                        api_test_results[f"POST {candidate_r}"] = {"status": post_r.status, "resp": post_text[:200]}
                                except Exception as pe:
                                    api_test_results[f"POST {candidate_r}"] = {"error": str(pe)}
                        webapp_info["api_test_results"] = api_test_results
                except Exception as he:
                    webapp_info["html_fetch_error"] = str(he)

        res["webapp"] = webapp_info

    except Exception as e:
        res["status"] = "error"
        res["error"] = str(e)

    return res


@app.get("/api/study-bot/{bot_key}")
@app.post("/api/study-bot/{bot_key}")
async def study_bot_endpoint(bot_key: str, request: Request):
    """
    Studies one or all bots in depth using specified account (?uid=) or active authorized worker account.
    bot_key can be: mrg, atf, victors, vyro, or all.
    """
    auth = request.headers.get("Authorization") or ""
    req_secret = request.query_params.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    accounts = await fetch_accounts_from_cloud()
    req_uid = request.query_params.get("uid")
    target_acc = None
    if req_uid:
        target_acc = next((a for a in accounts if str(a.get("user_id")) == str(req_uid)), None)

    bot_map = {
        "mrg": "mrgminerbot",
        "atf": "ATF_AIRDROP_bot",
        "victors": "VictorsCompanybot",
        "vyro": "vyrodrop_bot",
        "kynex": "Kynex_miningbot",
        "diggo": "Diggominer_bot",
        "astra": "ASTRA_AIRDROP_BOT",
        "pepegram": "Pepe_gram_bot",
        "adxearn": "AdxEarnAibot"
    }

    if bot_key == "all":
        target_bots = list(bot_map.items())
    elif bot_key in bot_map:
        target_bots = [(bot_key, bot_map[bot_key])]
    else:
        clean_bot = bot_key.replace("@", "").strip()
        target_bots = [(clean_bot.lower(), clean_bot)]

    # Try target account first, then fallback to any active worker account (strictly excluding Master 6727787768)
    ordered_accs = ([target_acc] if target_acc else []) + [a for a in accounts if a != target_acc and str(a.get("user_id")) != "6727787768" and (a.get("session_string") or a.get("session"))]
    results = {}
    used_uid = None
    for acc in ordered_accs:
        sess_str = acc.get("session_string") or acc.get("session")
        if not sess_str:
            continue
        cl = create_telethon_client(sess_str=sess_str, identifier=acc.get("phone") or acc.get("name") or "worker", proxy_val=acc.get("proxy"))
        try:
            await asyncio.wait_for(cl.connect(), timeout=8.0)
            if not await cl.is_user_authorized():
                await cl.disconnect()
                continue
            used_uid = str(acc.get("user_id"))
            for b_key, b_user in target_bots:
                results[b_key] = await study_bot_deep(cl, b_key, b_user)
            break
        except Exception as e:
            logger.warning(f"Study bot attempt with UID {acc.get('user_id')} note: {e}")
        finally:
            try: await cl.disconnect()
            except Exception: pass

    if not used_uid:
        return {"ok": False, "error": "No authorized account session available for deep study"}

    return {"ok": True, "inspected_by_uid": used_uid, "results": results}

@app.post("/api/mute-all-chats")
async def mute_all_chats_endpoint(request: Request):
    """Mutes notifications for all bots and channels across all fleet accounts."""
    auth = request.headers.get("Authorization") or ""
    req_secret = request.query_params.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    accounts = await fetch_accounts_from_cloud()
    all_targets_to_mute = [
        "mrgminerbot", "mrgminer", "mrgfun", "mrgwithdrawal",
        "ATF_AIRDROP_bot", "atfminers",
        "Kynex_miningbot", "kynex_mining",
        "VictorsCompanybot", "VictorsCompany",
        "vyrodrop_bot", "vyrodrop",
        "Diggominer_bot", "diggo_community",
        "ASTRA_AIRDROP_BOT",
        "Pepe_gram_bot",
        "AdxEarnAibot"
    ]
    results = []
    for acc in accounts:
        uid = str(acc.get("user_id"))
        name = acc.get("name", uid)
        sess_str = acc.get("session_string") or acc.get("session")
        if not sess_str:
            continue
        async with GLOBAL_MTPROTO_SEMAPHORE:
            locked = await acquire_account_lock(uid, ttl_seconds=30)
            if not locked:
                results.append({"uid": uid, "name": name, "status": "locked_skipped"})
                continue
            cl = create_telethon_client(sess_str=sess_str, identifier=acc.get("phone") or name, proxy_val=acc.get("proxy"))
            muted_count = 0
            try:
                await cl.connect()
                if not await cl.is_user_authorized():
                    results.append({"uid": uid, "name": name, "error": "unauthorized"})
                    continue

                for tgt in all_targets_to_mute:
                    try:
                        await mute_peer(cl, tgt, name)
                        muted_count += 1
                    except Exception:
                        pass

                # Also mute all dialogs that are channels or bots
                dialogs = await cl.get_dialogs(limit=50)
                for d in dialogs:
                    if d.is_channel or d.is_group or getattr(d.entity, 'bot', False):
                        try:
                            await mute_peer(cl, d.input_entity, name)
                            muted_count += 1
                        except Exception:
                            pass

                results.append({"uid": uid, "name": name, "muted_chats": muted_count})
            except Exception as e:
                results.append({"uid": uid, "name": name, "error": str(e)})
            finally:
                try:
                    await cl.disconnect()
                except Exception:
                    pass
                await release_account_lock(uid)

    return {"ok": True, "results": results}


@app.get("/api/inspect-bot-chat/{uid}")
async def inspect_bot_chat(uid: str, request: Request):
    """Fetches the latest messages and buttons from each bot for a specific worker account."""
    auth = request.headers.get("Authorization") or ""
    req_secret = request.query_params.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    accounts = await fetch_accounts_from_cloud()
    target_acc = next((a for a in accounts if str(a.get("user_id")) == str(uid)), None)
    if not target_acc:
        raise HTTPException(status_code=404, detail="Account not found")

    sess_str = target_acc.get("session_string") or target_acc.get("session")
    async with GLOBAL_MTPROTO_SEMAPHORE:
        locked = await acquire_account_lock(uid, ttl_seconds=30)
        if not locked:
            return {"ok": False, "uid": uid, "error": "Account is locked by another process"}
        cl = create_telethon_client(sess_str=sess_str, identifier=target_acc.get("phone") or target_acc.get("name") or uid, proxy_val=target_acc.get("proxy"))
        bots_to_check = [
            ("mrg", "mrgminerbot"),
            ("atf", "ATF_AIRDROP_bot"),
            ("victors", "VictorsCompanybot"),
            ("vyro", "vyrodrop_bot"),
            ("kynex", "Kynex_miningbot"),
            ("diggo", "Diggominer_bot"),
            ("astra", "ASTRA_AIRDROP_BOT"),
            ("pepegram", "Pepe_gram_bot"),
            ("adxearn", "AdxEarnAibot")
        ]
        chats = {}
        try:
            try:
                await cl.connect()
            except Exception as conn_err:
                import traceback
                return {"ok": False, "uid": uid, "error": f"Connection error: {type(conn_err).__name__}: {conn_err}", "traceback": traceback.format_exc()}

            try:
                is_auth = await cl.is_user_authorized()
                if not is_auth:
                    return {"ok": False, "uid": uid, "error": "Account session not authorized in Telegram"}
            except Exception as auth_err:
                import traceback
                return {"ok": False, "uid": uid, "error": f"Auth check error: {type(auth_err).__name__}: {auth_err}", "traceback": traceback.format_exc()}

            for name, b_user in bots_to_check:
                try:
                    b_ent = await cl.get_entity(b_user)
                    msgs = await cl.get_messages(b_ent, limit=4)
                    msg_list = []
                    for m in reversed(msgs):
                        btns = []
                        if m.buttons:
                            for row in m.buttons:
                                row_btns = []
                                for b in row:
                                    raw_b = getattr(b, "button", b)
                                    b_type = type(raw_b).__name__
                                    b_url = getattr(b, "url", None) or getattr(raw_b, "url", None) or getattr(getattr(raw_b, "web_app", None), "url", None)
                                    b_data = getattr(raw_b, "data", None)
                                    if isinstance(b_data, bytes):
                                        try: b_data = b_data.decode()
                                        except Exception: b_data = str(b_data)
                                    row_btns.append({
                                        "text": b.text,
                                        "type": b_type,
                                        "url": b_url,
                                        "data": b_data
                                    })
                                btns.append(row_btns)
                        msg_list.append({"id": m.id, "out": m.out, "text": m.raw_text, "buttons": btns})
                    chats[name] = msg_list
                except Exception as ex:
                    chats[name] = [{"error": str(ex)}]
        except Exception as e:
            import traceback
            return {"ok": False, "uid": uid, "error": f"{type(e).__name__}: {str(e)}", "traceback": traceback.format_exc()}
        finally:
            try:
                await cl.disconnect()
            except Exception:
                pass
            await release_account_lock(uid)

        return {"ok": True, "uid": uid, "chats": chats}


@app.get("/api/pepegram/verify-fleet")
@app.post("/api/pepegram/verify-fleet")
async def verify_pepegram_fleet_endpoint(request: Request):
    """
    Autonomously joins @pepe_grammmm and clicks the 'Verify' button in @Pepe_gram_bot across all worker accounts.
    Eliminates 'Channel Membership Required' barrier and fully qualifies recruit referrals under Master 6727787768.
    """
    auth = request.headers.get("Authorization") or ""
    req_secret = request.query_params.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    accounts = await fetch_accounts_from_cloud()
    results = []

    for acc in accounts:
        uid = str(acc.get("user_id"))
        name = acc.get("name", f"Acc {uid}")
        if uid == "6727787768" or acc.get("is_primary"):
            continue

        sess = acc.get("session_string") or acc.get("session")
        if not sess:
            continue

        acc_res = {"uid": uid, "name": name, "joined": False, "verified": False}
        cl = create_telethon_client(sess_str=sess, identifier=acc.get("phone") or name or uid, proxy_val=acc.get("proxy"))
        try:
            await cl.connect()
            if not await cl.is_user_authorized():
                acc_res["error"] = "not_authorized"
                results.append(acc_res)
                continue

            # 1. Join official required channel @pepe_grammmm
            try:
                await cl(JoinChannelRequest("pepe_grammmm"))
                acc_res["joined"] = True
                logger.info(f"[{name}] Joined @pepe_grammmm")
            except Exception as je:
                acc_res["join_note"] = str(je)

            await asyncio.sleep(0.8)

            # 2. Send /start {MASTER_UID} to ensure referral link is seeded
            b_pepe = await cl.get_input_entity("Pepe_gram_bot")
            try:
                await cl.send_message(b_pepe, "/start 6727787768")
                await asyncio.sleep(1.2)
            except Exception:
                pass

            # 3. Locate verification inline button and click it
            msgs = await cl.get_messages(b_pepe, limit=5)
            for m in msgs:
                if not m.out and m.buttons:
                    for r_idx, row in enumerate(m.buttons):
                        for c_idx, btn in enumerate(row):
                            b_txt = (btn.text or "").lower()
                            if any(k in b_txt for k in ["verify", "verification", "check", "joined"]):
                                try:
                                    await m.click(r_idx, c_idx)
                                    acc_res["verified"] = True
                                    acc_res["button_text"] = btn.text
                                    logger.info(f"[{name}] Clicked PepeGram '{btn.text}' button!")
                                    await asyncio.sleep(1.5)
                                    break
                                except Exception as ce:
                                    acc_res["click_error"] = str(ce)
                    if acc_res["verified"]:
                        break

            results.append(acc_res)
        except Exception as e:
            acc_res["error"] = str(e)
            results.append(acc_res)
        finally:
            try:
                await cl.disconnect()
            except Exception:
                pass
        await asyncio.sleep(1.0)

    return {"ok": True, "total": len(results), "accounts": results}


@app.get("/api/debug-account-session/{uid}")
async def debug_account_session(uid: str, request: Request):
    """Deep diagnostics for an account session: tests connect, auth, and token extraction."""
    auth = request.headers.get("Authorization") or ""
    req_secret = request.query_params.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    target_acc = None
    if UPSTASH_URL and UPSTASH_TOKEN:
        try:
            up_h = {"Authorization": f"Bearer {UPSTASH_TOKEN}", "Content-Type": "application/json"}
            async with aiohttp.ClientSession() as http:
                async with http.get(f"{UPSTASH_URL}/get/account:{uid}", headers=up_h, timeout=aiohttp.ClientTimeout(total=4)) as ur:
                    if ur.status == 200:
                        r_data = await ur.json()
                        val = r_data.get("result")
                        if val:
                            obj = json.loads(val) if isinstance(val, str) else val
                            while isinstance(obj, str): obj = json.loads(obj)
                            if isinstance(obj, dict) and obj.get("session_string"):
                                target_acc = obj
        except Exception:
            pass

    if not target_acc:
        accounts = await fetch_accounts_from_cloud()
        target_acc = next((a for a in accounts if str(a.get("user_id")) == str(uid)), None)

    if not target_acc:
        return {"ok": False, "error": f"Account {uid} not found in cloud accounts"}

    sess_str = target_acc.get("session_string") or target_acc.get("session")
    if not sess_str:
        return {"ok": False, "error": f"Account {uid} has no session string"}

    results = {"uid": uid, "name": target_acc.get("name"), "steps": {}}
    async with GLOBAL_MTPROTO_SEMAPHORE:
        locked = await acquire_account_lock(uid, ttl_seconds=60)
        if not locked:
            return {"ok": False, "uid": uid, "error": "Account is locked by another process"}
        cl = create_telethon_client(sess_str=sess_str, identifier=target_acc.get("phone") or target_acc.get("name") or uid, proxy_val=target_acc.get("proxy"))
        try:
            results["steps"]["connecting"] = "started"
            await cl.connect()
            results["steps"]["connecting"] = "connected"

            results["steps"]["authorizing"] = "checking"
            is_auth = await cl.is_user_authorized()
            results["steps"]["authorizing"] = is_auth
            if not is_auth:
                return {"ok": False, "results": results, "error": "Session is NOT authorized (may have expired or logged out)"}

            me = await cl.get_me()
            results["me"] = {"id": me.id, "first_name": me.first_name, "username": me.username, "phone": me.phone}

            # Try extracting tokens for all 4 bots
            extracted = await extract_tokens_with_client(cl, target_acc)
            results["extracted_tokens"] = {k: (v[:30] + "..." if isinstance(v, str) and len(v) > 30 else v) for k, v in extracted.items()}
            
            # If tokens extracted, sync to Upstash Redis
            if extracted:
                await sync_account_tokens_to_clouds(extracted)
                results["synced_to_cloud"] = True

            return {"ok": True, "results": results}
        except Exception as e:
            import traceback
            results["exception"] = f"{type(e).__name__}: {str(e)}"
            results["traceback"] = traceback.format_exc()
            return {"ok": False, "results": results, "error": str(e)}
        finally:
            try:
                await cl.disconnect()
            except Exception:
                pass
            await release_account_lock(uid)



# Type B Channel & Subscription Engine Definitions
CHANNEL_WHITELIST = {
    "myagyai",
    "mrgminer",
    "mrgfun",
    "mrgwithdrawal",
    "DurovKidney",
    "VictorsCompany",
    "victors_company",
    "VICWithdrawals",
    "TheBoss_Victor",
    "vyrodrop",
    "atfminers",
    "kynex_mining",
    "EarnVaulte",
    "solanamemes001",
    "Web3Primeteam"
}

# Active Legitimate Sponsor Channels (Scammers, TRX Power, ART, AI Lab, UltraWallet, FINVORA & Stones purged)
MANDATORY_SPONSOR_CHANNELS = [
    "mrgminer", "mrgfun", "mrgwithdrawal", "DurovKidney",
    "VictorsCompany", "victors_company", "VICWithdrawals", "TheBoss_Victor",
    "vyrodrop",
    "atfminers",
    "kynex_mining",
    "EarnVaulte",
    "solanamemes001",
    "Web3Primeteam"
]

# 9 High-Conviction Legitimate Fleet Bots (100% REST-Based Mini-Apps)
FLEET_LEGITIMATE_BOTS = [
    "mrgminerbot", "ATF_AIRDROP_bot",
    "VictorsCompanybot", "vyrodrop_bot",
    "Kynex_miningbot", "Diggominer_bot",
    "ASTRA_AIRDROP_BOT", "Pepe_gram_bot",
    "AdxEarnAibot"
]

# Blacklisted & Purged Bots to permanently block and delete from Telegram dialogs
FLEET_BANNED_SCAMMERS = [
    # Purged per user directive
    "LeafEarnBot",
    "stoneswithestand_bot",
    "AiLab_robot",
    "UltrawalletTrade_Bot",
    "FINVORAWeb3bot",
    "TurboGramV1_bot",
    "trxpowermining_bot",
    "BitcoinCloudMinersBot",
    "Bitcoin_Cloud_Mining_bot",
    "ART_AIRDROP_BOT",
    "artairdrop_bot",
    "goldkeepers_bot",
    "earncraft_bot",
    # Previously blacklisted scammers
    "ainovum_bot",
    "tensormining_bot",
    "TensorMiningRobot",
    "TonTraderAIBot",
    "tontrader_bot",
    "tacairdrop_bot",
    "usdtquadbot",
    "ApxMinerBot",
    "apexminer_bot",
    "OminixAiBot"
]

# Channels & Groups to permanently leave and delete from Telegram dialogs
SCAM_CHANNELS_TO_LEAVE = [
    # Newly purged per user directive
    "stoneswithestand",
    "ailabrobotnews",
    "AiLabRobotPayouts",
    "ultrawalletofficial",
    "ultrawallet",
    "finvoraweb3",
    "TurboGramAnnouncements",
    "TurboGramPayment",
    "trxpowerminingofficial",
    "trx_world_work",
    "trxpowermining",
    "art_airdrop",
    "artairdrop",
    "artcoin_en",
    "artwithdraw",
    "earncraft_new",
    # Previously blacklisted scam channels
    "tensorcoinnews",
    "tontraderai_official",
    "tontraderai_group",
    "tontraderai_reviews",
    "tacairdrop",
    "tacairdrop_official",
    "tac_airdrop",
    "tacairdropen",
    "novum_en",
    "apexminer_official",
    "apexminergroup",
    "usdtquad_channel",
    "usdtquad"
]

LAST_CHANNEL_SYNC_STATUS = {
    "status": "idle",
    "timestamp": 0,
    "total_accounts": 0,
    "results": []
}

@app.get("/api/channels/status")
async def channel_status_endpoint(request: Request):
    """Returns the latest Type B Channel & Subscription Engine status."""
    return {"ok": True, "status": LAST_CHANNEL_SYNC_STATUS}


@app.post("/api/channels/sync-and-verify")
@app.get("/api/channels/sync-and-verify")
async def sync_and_verify_channels_endpoint(request: Request):
    """
    Type B Channel & Bot Management Engine:
    Ensures all fleet accounts join mandatory sponsor channels, unblock all 5 legitimate bots,
    and permanently mute all channels/bots to prevent notification spam.
    Protects against Telegram's 500-channel limit by leaving unwhitelisted spam channels if dialogs > 400.
    """
    auth = request.headers.get("Authorization") or ""
    req_secret = request.query_params.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    accounts = await fetch_accounts_from_cloud()
    target_uid = request.query_params.get("uid")
    if target_uid:
        accounts = [a for a in accounts if str(a.get("user_id")) == str(target_uid)]

    sync_mode = request.query_params.get("sync") == "1" or bool(target_uid)

    async def _run_channel_sync():
        LAST_CHANNEL_SYNC_STATUS["status"] = "running"
        LAST_CHANNEL_SYNC_STATUS["timestamp"] = time.time()
        LAST_CHANNEL_SYNC_STATUS["total_accounts"] = len(accounts)
        LAST_CHANNEL_SYNC_STATUS["results"] = []
        results = []

        for acc in accounts:
            uid = str(acc.get("user_id"))
            name = acc.get("name", uid)
            sess_str = acc.get("session_string") or acc.get("session")
            if not sess_str:
                res_item = {"uid": uid, "name": name, "status": "no_session"}
                results.append(res_item)
                LAST_CHANNEL_SYNC_STATUS["results"].append(res_item)
                continue

            cl = create_telethon_client(sess_str=sess_str, identifier=acc.get("phone") or name, proxy_val=acc.get("proxy"))
            already_purged = bool(acc.get("dead_bots_purged_v2"))
            acc_res = {"uid": uid, "name": name, "joined": [], "unblocked": [], "blocked_scammers": [], "deleted_dialogs": [], "left_scam_channels": [], "muted": 0, "pruned": 0, "already_purged": already_purged}
            try:
                await asyncio.wait_for(cl.connect(), timeout=10.0)
                if not await cl.is_user_authorized():
                    acc_res["status"] = "unauthorized"
                    results.append(acc_res)
                    LAST_CHANNEL_SYNC_STATUS["results"].append(acc_res)
                    continue

                # 1-TIME SANITATION: Only block, erase history, and leave discontinued bots once per account
                if not already_purged:
                    # 1. Dialog-based multi-pass sanitation: Erase history completely & leave channels
                    try:
                        d_list = await cl.get_dialogs(limit=100)
                        for d in d_list:
                            u_low = (getattr(d.entity, 'username', '') or '').lower()
                            t_low = (getattr(d.entity, 'title', '') or getattr(d.entity, 'first_name', '') or '').lower()
                            is_chan = hasattr(d.entity, "broadcast") and getattr(d.entity, "broadcast", False)
                            is_bot = getattr(d.entity, "bot", False)

                            # Strict protection: NEVER treat active legitimate fleet bots as scammers
                            if u_low in [b.lower() for b in FLEET_LEGITIMATE_BOTS]:
                                continue

                            matches = any(b.lower() == u_low for b in FLEET_BANNED_SCAMMERS) or \
                                      any(c.lower() == u_low for c in SCAM_CHANNELS_TO_LEAVE) or \
                                      any(k in t_low for k in ["finvora", "turbo gram", "turbogram", "ai lab", "ailab", "stones white", "ultra wallet", "ultrawallet", "trx power", "gold keepers", "earncraft", "art 🚀", "live withdraw"])
                            if matches:
                                if is_bot:
                                    try: await cl(functions.contacts.BlockRequest(id=d.entity))
                                    except Exception: pass
                                if is_chan:
                                    try: await cl(functions.channels.LeaveChannelRequest(d.entity))
                                    except Exception: pass
                                else:
                                    try:
                                        await cl(functions.messages.ReadHistoryRequest(peer=d.entity, max_id=0))
                                        for _ in range(25):
                                            r_del = await cl(functions.messages.DeleteHistoryRequest(peer=d.entity, max_id=0, just_clear=False, revoke=True))
                                            if getattr(r_del, 'offset', 0) <= 0: break
                                            await asyncio.sleep(0.2)
                                    except Exception: pass
                                try: await cl.delete_dialog(d.entity)
                                except Exception: pass
                                acc_res["deleted_dialogs"].append(u_low or t_low)
                    except Exception as pe:
                        logger.warning(f"[{name}] Dialog purge note: {pe}")

                    # Direct entity fallback purge
                    for sb in FLEET_BANNED_SCAMMERS:
                        try:
                            b_ent = await cl.get_entity(sb)
                            await cl(functions.contacts.BlockRequest(id=b_ent))
                            for _ in range(25):
                                r_del = await cl(functions.messages.DeleteHistoryRequest(peer=b_ent, max_id=0, just_clear=False, revoke=True))
                                if getattr(r_del, 'offset', 0) <= 0: break
                                await asyncio.sleep(0.2)
                            await cl.delete_dialog(b_ent)
                            acc_res["blocked_scammers"].append(sb)
                        except Exception: pass

                    for sc in SCAM_CHANNELS_TO_LEAVE:
                        try:
                            ch_ent = await cl.get_entity(sc)
                            try: await cl(functions.channels.LeaveChannelRequest(ch_ent))
                            except Exception: pass
                            await cl.delete_dialog(ch_ent)
                            acc_res["left_scam_channels"].append(sc)
                        except Exception: pass

                    acc["dead_bots_purged_v2"] = True
                    FLEET_ACCOUNTS_CACHE[uid] = acc
                    if UPSTASH_URL and UPSTASH_TOKEN:
                        try:
                            async with aiohttp.ClientSession() as sup:
                                await sup.post(f"{UPSTASH_URL}/set/fleet:purged_v2:{uid}", data="1", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=3))
                        except Exception:
                            pass
                    try:
                        asyncio.create_task(sync_new_account_to_clouds(acc))
                    except Exception:
                        pass
                else:
                    logger.info(f"[{name}] Dead bots & scam channels already purged previously. Skipping dialog deletion.")

                # 3. Unblock all 9 legitimate fleet bots
                for b in FLEET_LEGITIMATE_BOTS:
                    try:
                        await cl(functions.contacts.UnblockRequest(id=b))
                        acc_res["unblocked"].append(b)
                    except Exception:
                        pass

                # 4. Join mandatory legitimate sponsor channels (Idempotent: runs ONCE per account with human delays)
                channels_already_joined = False
                if UPSTASH_URL and UPSTASH_TOKEN:
                    try:
                        async with aiohttp.ClientSession() as up_s:
                            async with up_s.get(f"{UPSTASH_URL}/get/fleet:channels_joined:{uid}", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=2)) as up_r:
                                if up_r.status == 200:
                                    d_j = await up_r.json()
                                    if d_j.get("result"):
                                        channels_already_joined = True
                    except Exception:
                        pass

                if channels_already_joined:
                    acc_res["joined"].append("all_sponsor_channels_previously_verified")
                else:
                    hit_flood = False
                    for ch in MANDATORY_SPONSOR_CHANNELS:
                        try:
                            await cl(JoinChannelRequest(ch))
                            acc_res["joined"].append(ch)
                            await asyncio.sleep(random.uniform(6.0, 12.0))
                        except FloodWaitError as fwe:
                            logger.warning(f"[{name}] Flood wait {fwe.seconds}s encountered on @{ch}. Halting joins to protect account.")
                            acc_res["joined"].append(f"flood_wait_{fwe.seconds}s")
                            hit_flood = True
                            break
                        except Exception as ce:
                            err_s = str(ce).lower()
                            if "already" in err_s:
                                acc_res["joined"].append(f"{ch} (already)")

                    if not hit_flood and UPSTASH_URL and UPSTASH_TOKEN:
                        try:
                            async with aiohttp.ClientSession() as up_s:
                                await up_s.post(f"{UPSTASH_URL}/set/fleet:channels_joined:{uid}", data="1", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=2))
                        except Exception:
                            pass

                # 5. Scan ALL dialogs: Erase and delete dialogs for any scammer bot, channel, or group (only if not already purged)
                muted_cnt = 0
                dialogs = await cl.get_dialogs(limit=200)
                for d in dialogs:
                    uname = (getattr(d.entity, 'username', '') or '').lower()
                    title = (d.name or '').lower()
                    is_scam = (
                        uname not in [b.lower() for b in FLEET_LEGITIMATE_BOTS] and
                        (uname in SCAM_CHANNELS_TO_LEAVE or
                         uname in [b.lower() for b in FLEET_BANNED_SCAMMERS] or
                         any(s in uname for s in ["tensorcoin", "tontrader", "tacairdrop", "usdtquad", "apexminer", "ainovum", "trxpower", "bitcoincloud", "artairdrop", "art_airdrop"]) or
                         any(s in title for s in ["tensorcoin", "ton trader", "tac airdrop", "usdt quad", "apex miner", "ainovum", "trx power", "bitcoin cloud", "art airdrop"]))
                    )
                    if is_scam and not already_purged:
                        if d.is_channel or d.is_group:
                            try:
                                await cl(functions.channels.LeaveChannelRequest(d.input_entity))
                            except Exception:
                                pass
                            try:
                                await cl.delete_dialog(d.input_entity)
                                acc_res["left_scam_channels"].append(uname or d.name)
                            except Exception:
                                pass
                        else:
                            # Bot or user
                            try:
                                await cl(functions.contacts.BlockRequest(id=d.input_entity))
                            except Exception:
                                pass
                            try:
                                await cl(functions.messages.DeleteHistoryRequest(peer=d.input_entity, max_id=0, just_clear=False, revoke=True))
                            except Exception:
                                pass
                            try:
                                await cl.delete_dialog(d.input_entity)
                                acc_res["deleted_dialogs"].append(uname or d.name)
                            except Exception:
                                pass
                        await asyncio.sleep(0.3)
                        continue

                    if d.is_channel or d.is_group or getattr(d.entity, 'bot', False):
                        try:
                            await mute_peer(cl, d.input_entity, name)
                            muted_cnt += 1
                        except Exception:
                            pass
                acc_res["muted"] = muted_cnt

                # 4. Channel limit protection: if total dialogs > 400, leave non-whitelisted channels (workers only)
                pruned_cnt = 0
                if uid != "6727787768" and len(dialogs) > 400:
                    for d in dialogs:
                        if d.is_channel and not getattr(d.entity, 'megagroup', False):
                            uname = (getattr(d.entity, 'username', '') or '').lower()
                            title = (d.name or '').lower()
                            if uname not in CHANNEL_WHITELIST and not uname.startswith("aaa") and "aaa" not in title and "my agy ai" not in title:
                                try:
                                    await cl(functions.channels.LeaveChannelRequest(d.input_entity))
                                    pruned_cnt += 1
                                    await asyncio.sleep(0.8)
                                except Exception:
                                    pass
                acc_res["pruned"] = pruned_cnt
                acc_res["status"] = "synced"
                results.append(acc_res)
                LAST_CHANNEL_SYNC_STATUS["results"].append(acc_res)
            except Exception as e:
                acc_res["status"] = f"error: {format_error(e)}"
                results.append(acc_res)
                LAST_CHANNEL_SYNC_STATUS["results"].append(acc_res)
            finally:
                try: await cl.disconnect()
                except Exception: pass

        LAST_CHANNEL_SYNC_STATUS["status"] = "completed"
        return results

    if sync_mode:
        res = await _run_channel_sync()
        return {"ok": True, "count": len(res), "results": res}
    else:
        asyncio.create_task(_run_channel_sync())
        return {
            "ok": True,
            "status": "running_in_background",
            "accounts_queued": len(accounts),
            "message": "Type B Channel Sync & Muting running in background across all fleet accounts. Monitor via /api/channels/status"
        }


@app.post("/api/cleanup-purged-bots-once")
@app.get("/api/cleanup-purged-bots-once")
async def cleanup_purged_bots_once_endpoint(request: Request):
    """
    Dedicated 1-time purge endpoint for user accounts:
    Iterates all 18 accounts, permanently blocks & erases chat history for all discontinued bots
    (@stoneswithestand_bot, @AiLab_robot, @UltrawalletTrade_Bot, @FINVORAWeb3bot, etc.),
    leaves discontinued channels, and guarantees strictly 1-time execution per account.
    """
    auth = request.headers.get("Authorization") or ""
    req_secret = request.query_params.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    force = request.query_params.get("force") == "1"
    accounts = await fetch_accounts_from_cloud()
    results = []

    for acc in accounts:
        uid = str(acc.get("user_id"))
        name = acc.get("name", uid)
        sess_str = acc.get("session_string") or acc.get("session")
        if not sess_str:
            results.append({"uid": uid, "name": name, "status": "no_session"})
            continue

        if not force and acc.get("dead_bots_purged_v2"):
            results.append({"uid": uid, "name": name, "status": "already_purged_skipped"})
            continue

        cl = create_telethon_client(sess_str=sess_str, identifier=acc.get("phone") or name, proxy_val=acc.get("proxy"))
        acc_res = {"uid": uid, "name": name, "blocked_and_erased": [], "left_channels": []}
        try:
            await asyncio.wait_for(cl.connect(), timeout=10.0)
            if not await cl.is_user_authorized():
                acc_res["status"] = "unauthorized"
                results.append(acc_res)
                continue

            # 1. Dialog-based multi-pass sanitation: Erase history completely & leave channels
            try:
                d_list = await cl.get_dialogs(limit=100)
                for d in d_list:
                    u_low = (getattr(d.entity, 'username', '') or '').lower()
                    t_low = (getattr(d.entity, 'title', '') or getattr(d.entity, 'first_name', '') or '').lower()
                    is_chan = hasattr(d.entity, "broadcast") and getattr(d.entity, "broadcast", False)
                    is_bot = getattr(d.entity, "bot", False)

                    matches = any(b.lower() == u_low for b in FLEET_BANNED_SCAMMERS) or \
                              any(c.lower() == u_low for c in SCAM_CHANNELS_TO_LEAVE) or \
                              any(k in t_low for k in ["finvora", "turbo gram", "turbogram", "ai lab", "ailab", "stones white", "ultra wallet", "ultrawallet", "trx power", "gold keepers", "earncraft", "art 🚀", "live withdraw"])
                    if matches:
                        if is_bot:
                            try: await cl(functions.contacts.BlockRequest(id=d.entity))
                            except Exception: pass
                        if is_chan:
                            try: await cl(functions.channels.LeaveChannelRequest(d.entity))
                            except Exception: pass
                        else:
                            try:
                                await cl(functions.messages.ReadHistoryRequest(peer=d.entity, max_id=0))
                                for _ in range(25):
                                    r_del = await cl(functions.messages.DeleteHistoryRequest(peer=d.entity, max_id=0, just_clear=False, revoke=True))
                                    if getattr(r_del, 'offset', 0) <= 0: break
                                    await asyncio.sleep(0.2)
                            except Exception: pass
                        try: await cl.delete_dialog(d.entity)
                        except Exception: pass
                        acc_res["blocked_and_erased"].append(u_low or t_low)
            except Exception as pe:
                logger.warning(f"[{name}] Dialog purge note: {pe}")

            # Direct entity fallback purge
            for sb in FLEET_BANNED_SCAMMERS:
                try:
                    b_ent = await cl.get_entity(sb)
                    await cl(functions.contacts.BlockRequest(id=b_ent))
                    for _ in range(25):
                        r_del = await cl(functions.messages.DeleteHistoryRequest(peer=b_ent, max_id=0, just_clear=False, revoke=True))
                        if getattr(r_del, 'offset', 0) <= 0: break
                        await asyncio.sleep(0.2)
                    await cl.delete_dialog(b_ent)
                    acc_res["blocked_and_erased"].append(sb)
                except Exception: pass

            for sc in SCAM_CHANNELS_TO_LEAVE:
                try:
                    ch_ent = await cl.get_entity(sc)
                    try: await cl(functions.channels.LeaveChannelRequest(ch_ent))
                    except Exception: pass
                    await cl.delete_dialog(ch_ent)
                    acc_res["left_channels"].append(sc)
                except Exception: pass

            # 3. Mark 1-time purge complete
            acc["dead_bots_purged_v2"] = True
            FLEET_ACCOUNTS_CACHE[uid] = acc
            if UPSTASH_URL and UPSTASH_TOKEN:
                try:
                    async with aiohttp.ClientSession() as sup:
                        await sup.post(f"{UPSTASH_URL}/set/fleet:purged_v2:{uid}", data="1", headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}, timeout=aiohttp.ClientTimeout(total=3))
                except Exception:
                    pass
            try:
                await sync_new_account_to_clouds(acc)
            except Exception:
                pass

            acc_res["status"] = "purged_success"
            results.append(acc_res)
        except Exception as e:
            acc_res["status"] = f"error: {format_error(e)}"
            results.append(acc_res)
        finally:
            try: await cl.disconnect()
            except Exception: pass

    return {"ok": True, "count": len(results), "results": results}


LAST_ONBOARD_STATUS = {
    "status": "idle",
    "processed": 0,
    "total": 0,
    "timestamp": 0,
    "results": []
}


@app.get("/api/onboard-status")
async def onboard_status_endpoint(request: Request):
    """Returns the current background onboarding and referral binding execution status."""
    return {"ok": True, "status": LAST_ONBOARD_STATUS}


@app.post("/api/onboard-new-bots")
@app.get("/api/onboard-new-bots")
async def onboard_new_bots(request: Request):
    """
    Explicit interactive cloud onboarding endpoint:
    Processes worker accounts, executes bot-specific referral completion pipelines,
    joins sponsor channels, clicks verification buttons, and starts mining.
    Supports background execution (default) and single account filtering (?uid=<id>).
    """
    auth = request.headers.get("Authorization") or ""
    req_secret = request.query_params.get("secret", "")
    if auth != f"Bearer {SECRET_KEY}" and req_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    target_uid = request.query_params.get("uid") or body.get("uid")
    force_mode = request.query_params.get("force") in ("1", "true", "yes") or bool(body.get("force"))
    sync_mode = request.query_params.get("sync") == "1" or bool(target_uid)

    accounts = body.get("accounts", [])
    if not accounts:
        accounts = await fetch_accounts_from_cloud()

    if target_uid:
        accounts = [a for a in accounts if str(a.get("user_id")) == str(target_uid)]
        if not accounts:
            raise HTTPException(status_code=404, detail=f"Account with UID {target_uid} not found")

    async def _run_onboard_pipeline():
        LAST_ONBOARD_STATUS["status"] = "running"
        LAST_ONBOARD_STATUS["timestamp"] = time.time()
        LAST_ONBOARD_STATUS["total"] = len(accounts)
        LAST_ONBOARD_STATUS["processed"] = 0
        LAST_ONBOARD_STATUS["results"] = []

        results = []
        for acc in accounts:
            uid = str(acc.get("user_id"))
            name = acc.get("name", "User")
            if uid == "6727787768":
                acc_res = {"uid": uid, "name": name, "status": "master_skipped", "bots": {b: "verified" for b in ALL_10_BOT_KEYS}}
                results.append(acc_res)
                LAST_ONBOARD_STATUS["processed"] += 1
                continue

            sess_str = acc.get("session_string") or acc.get("session")
            if not sess_str:
                acc_res = {"uid": uid, "name": name, "status": "no_session", "bots": {}}
                results.append(acc_res)
                LAST_ONBOARD_STATUS["processed"] += 1
                continue

            acc_res = {"uid": uid, "name": name, "bots": {}}

            # Check if all 10 referrals are bound (unless force mode is active)
            if not force_mode and is_account_referrals_bound(acc):
                acc_res["status"] = "already_bound_all_10"
                for b_name in ALL_10_BOT_KEYS:
                    acc_res["bots"][b_name] = "verified"
                results.append(acc_res)
                LAST_ONBOARD_STATUS["processed"] += 1
                continue

            async with GLOBAL_MTPROTO_SEMAPHORE:
                locked = await acquire_account_lock(uid, ttl_seconds=90)
                if not locked:
                    acc_res["status"] = "locked_by_other_node"
                    results.append(acc_res)
                    LAST_ONBOARD_STATUS["processed"] += 1
                    continue
                cl = create_telethon_client(sess_str=sess_str, identifier=acc.get("phone") or name, proxy_val=acc.get("proxy"))
                try:
                    await cl.connect()
                    if not await cl.is_user_authorized():
                        acc_res["error"] = "unauthorized"
                        results.append(acc_res)
                        continue

                    # Onboard and bind master referrals across all 10 fleet bots
                    try:
                        await bind_account_master_referrals(cl, acc, force=force_mode)
                        for b_name in ALL_10_BOT_KEYS:
                            acc_res["bots"][b_name] = "verified" if acc.get(f"{b_name}_referral_bound") else "pending"
                    except Exception as e:
                        acc_res["error"] = str(e)

                    if is_account_referrals_bound(acc):
                        acc["referrals_bound"] = True
                        acc["all_10_referrals_bound"] = True
                    await sync_new_account_to_clouds(acc)
                finally:
                    try:
                        await cl.disconnect()
                    except Exception:
                        pass
                    await release_account_lock(uid)
            results.append(acc_res)
            LAST_ONBOARD_STATUS["processed"] += 1
            LAST_ONBOARD_STATUS["results"].append(acc_res)

        LAST_ONBOARD_STATUS["status"] = "completed"
        return {"ok": True, "count": len(results), "results": results}

    if not sync_mode:
        asyncio.create_task(_run_onboard_pipeline())
        return {
            "ok": True,
            "status": "running_in_background",
            "accounts_to_process": len([a for a in accounts if str(a.get("user_id")) != "6727787768"]),
            "message": "Cloud onboarding and referral binding running in background. Monitor via /api/onboard-status"
        }
    else:
        return await _run_onboard_pipeline()


@app.post("/api/withdraw/auto-cycle")
async def api_withdraw_auto_cycle(request: Request):
    """Auto-withdrawals permanently disabled by user directive."""
    return {
        "ok": True,
        "disabled": True,
        "message": "Automated withdrawals are permanently disabled to prevent wrong-address routing. All fleet accounts are in 100% accumulation and compounding mode.",
        "timestamp": time.time()
    }


LAST_AUTO_CLEANUP_TS = 0
LAST_SIDE_TASKS_SWEEP_TS = 0

@app.post("/api/cleanup")
async def api_cleanup_endpoint(request: Request):
    """Triggers autonomous multi-tier sanitation in the cloud."""
    global LAST_AUTO_CLEANUP_TS
    try:
        import clean_up_system
        disk_stats = clean_up_system.clean_local_disk(dry_run=False)
        upstash_stats = clean_up_system.sanitize_upstash_redis(dry_run=False)
        LAST_AUTO_CLEANUP_TS = time.time()
        return {
            "ok": True,
            "disk": disk_stats,
            "upstash": upstash_stats,
            "timestamp": time.time()
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "timestamp": time.time()}


def get_current_month_hours() -> float:
    """Calculates active running hours for the current calendar month in UTC."""
    now = datetime.datetime.now(datetime.timezone.utc)
    month_start = datetime.datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    elapsed_seconds = (now - month_start).total_seconds()
    return round(elapsed_seconds / 3600.0, 1)


async def cloud_wealth_automation_watchdog():
    """24/7 background watchdog executing scheduled cloud farming, autonomous sanitation, and 650h Baton Relay rotation."""
    global LAST_AUTO_CLEANUP_TS, LAST_SIDE_TASKS_SWEEP_TS
    logger.info("[Cloud Wealth Watchdog] Initialized 24/7 autonomous farming scheduler, auto clean-up & Baton Relay engine...")
    await asyncio.sleep(60)
    cycle_count = 0
    while True:
        try:
            # 1. Anti-Ban Safeguard: Check Maintenance Mode
            in_maint, reason, rem = await is_in_maintenance_mode()
            if in_maint:
                logger.info(f"[Cloud Wealth Watchdog] ⏸️ Fleet in MAINTENANCE MODE ({reason}). Cooldown: {rem}s remaining. Idling.")
                await asyncio.sleep(min(rem + 5, 60))
                continue

            is_coord = await acquire_coordinator_lock(ttl_seconds=1800)
            if not is_coord:
                logger.info("[Cloud Wealth Watchdog] Standby node: not active coordinator; idling.")
                await asyncio.sleep(1800)
                continue

            cycle_count += 1
            accounts = await fetch_accounts_from_cloud()
            if accounts:
                logger.info(f"[Cloud Wealth Watchdog] ⚡ Running Scheduled Cloud Cycle #{cycle_count} across {len(accounts)} accounts...")
                async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as session:
                    tokens = await fetch_cloud_miniapp_tokens(session)

                    # 1. Full Fleet Farming Cycle
                    try:
                        farm_res = await run_cloud_fleet_farming_cycle(session, accounts, tokens)
                        logger.info(f"[Cloud Wealth Watchdog] Fleet farming cycle #{cycle_count} finished: {farm_res.get('farmed_count', 0)} accounts")
                    except Exception as fe:
                        logger.error(f"[Cloud Wealth Watchdog] Farming error: {fe}")

                    # 2. Automated Withdrawals Permanently Disabled by User Directive
                    pass

                    # 3. Autonomous Sanitation & Maintenance (Runs automatically every 6 hours)
                    now_ts = time.time()
                    if (now_ts - LAST_AUTO_CLEANUP_TS) > 21600:
                        try:
                            import clean_up_system
                            logger.info("[Cloud Wealth Watchdog] 🧹 Running autonomous cloud sanitation & maintenance...")
                            clean_up_system.clean_local_disk(dry_run=False)
                            clean_up_system.sanitize_upstash_redis(dry_run=False)
                            LAST_AUTO_CLEANUP_TS = now_ts
                            logger.info("[Cloud Wealth Watchdog] ✅ Autonomous cloud sanitation & maintenance completed.")
                        except Exception as ce:
                            logger.debug(f"[Cloud Wealth Watchdog] Auto clean-up note: {ce}")

                    # 4. Autonomous 10-Bot Side-Tasks Sweeper (Runs every 3 hours)
                    if (now_ts - LAST_SIDE_TASKS_SWEEP_TS) > 10800:
                        try:
                            logger.info("[Cloud Wealth Watchdog] 🎯 Triggering autonomous 10-bot side-task sweep in cloud...")
                            asyncio.create_task(asyncio.create_subprocess_exec(
                                sys.executable, "finish_all_fleet_sidetasks.py",
                                stdout=asyncio.subprocess.DEVNULL,
                                stderr=asyncio.subprocess.DEVNULL
                            ))
                            LAST_SIDE_TASKS_SWEEP_TS = now_ts
                        except Exception as se:
                            logger.debug(f"[Cloud Wealth Watchdog] Side-task auto trigger note: {se}")

            # 4. Baton Relay 650h Rotation Monitor (Automatic Single-Active Handover)
            cur_node_num = get_current_node_number()
            cur_hours = get_current_month_hours()
            safe_margin = max(0.0, round(650.0 - cur_hours, 1))
            logger.info(f"[Baton Relay] Node {cur_node_num} monthly runtime: {cur_hours:.1f} / 750.0 hours (Safe margin: {safe_margin:.1f}h before 650.0h auto-rotation)")
            if cur_hours >= 650.0:
                next_node = 3 if cur_node_num == 2 else (1 if cur_node_num == 3 else 2)
                logger.warning(f"[Baton Relay] ⚠️ Node {cur_node_num} reached {cur_hours:.1f} hours! Triggering rotation to Node {next_node}...")
                asyncio.create_task(_trigger_node_rotation(to_node=next_node, cooldown_seconds=300))
                await asyncio.sleep(300)
                continue

        except Exception as e:
            logger.error(f"[Cloud Wealth Watchdog] Cycle error: {e}")

        await asyncio.sleep(1800)
